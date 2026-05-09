import numpy as np
import pandas as pd
import os
import pickle
from config import Config

# TensorFlow imports (akan error jika tidak ada, tapi kita handle)
TF_AVAILABLE = False
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    print("[WARNING] TensorFlow / sklearn tidak terinstall. LSTM akan menggunakan fallback naive.")

class LSTMPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.lookback = Config.LSTM_LOOKBACK
        self.feature_cols = ['open', 'high', 'low', 'close', 'volume']
        if Config.USE_LSTM and TF_AVAILABLE:
            self._load_or_build_model()
    
    def _load_or_build_model(self):
        model_path = Config.LSTM_MODEL_PATH
        scaler_path = model_path.replace('.h5', '_scaler.pkl')
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.model = load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("[LSTM] Model dan scaler loaded from disk.")
                return
            except Exception as e:
                print(f"[LSTM] Gagal load model: {e}")
        print("[LSTM] Membangun model baru (belum trained).")
        self.model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.lookback, len(self.feature_cols))),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        self.scaler = MinMaxScaler()
        self.model.save(model_path)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
    
    def _prepare_data(self, df):
        if not all(col in df.columns for col in self.feature_cols):
            data = df['close'].values.reshape(-1, 1)
        else:
            data = df[self.feature_cols].values
        scaled = self.scaler.fit_transform(data)
        X, y = [], []
        for i in range(self.lookback, len(scaled)):
            X.append(scaled[i-self.lookback:i])
            y.append(scaled[i, 3])  # close column index = 3
        return np.array(X), np.array(y)
    
    def train_model(self, df_list, epochs=20, batch_size=32, validation_split=0.1):
        if not TF_AVAILABLE or self.model is None:
            print("[LSTM] Training skipped: TensorFlow not available.")
            return
        combined = pd.concat(df_list, ignore_index=True)
        if len(combined) < self.lookback + 10:
            print("[LSTM] Data insufficient for training.")
            return
        X, y = self._prepare_data(combined)
        if len(X) == 0:
            return
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size,
                       validation_split=validation_split,
                       callbacks=[early_stop], verbose=0)
        self.model.save(Config.LSTM_MODEL_PATH)
        with open(Config.LSTM_MODEL_PATH.replace('.h5', '_scaler.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)
        print("[LSTM] Training completed and model saved.")
    
    def predict_next_price(self, df):
        if df is None or len(df) < self.lookback:
            return None
        if not TF_AVAILABLE or self.model is None:
            close = df['close'].values[-self.lookback:]
            x = np.arange(len(close))
            z = np.polyfit(x, close, 1)
            pred = z[0] * (len(close)) + z[1]
            return float(pred)
        latest = df.iloc[-self.lookback:].copy()
        if not all(col in latest.columns for col in self.feature_cols):
            data = latest['close'].values.reshape(-1, 1)
            if not hasattr(self.scaler, 'data_min_'):
                self.scaler.fit(data)
            scaled = self.scaler.transform(data)
        else:
            data = latest[self.feature_cols].values
            scaled = self.scaler.transform(data)
        X_pred = scaled.reshape(1, self.lookback, data.shape[1])
        pred_scaled = self.model.predict(X_pred, verbose=0)[0][0]
        if hasattr(self.scaler, 'data_min_'):
            close_min = self.scaler.data_min_[3]
            close_max = self.scaler.data_max_[3]
            pred_price = pred_scaled * (close_max - close_min) + close_min
        else:
            pred_price = pred_scaled
        return float(pred_price)

ai_predictor = LSTMPredictor()

def periodic_training():
    import pandas as pd
    import glob
    files = glob.glob("history/*.csv")
    if files:
        dfs = [pd.read_csv(f) for f in files[-10:]]
        if dfs:
            ai_predictor.train_model(dfs, epochs=10)
