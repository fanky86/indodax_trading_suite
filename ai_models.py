# ai_models.py
import numpy as np
import pandas as pd
import os
from config import Config

# Fallback jika tensorflow tidak ada
TF_AVAILABLE = False
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TF_AVAILABLE = True
except ImportError:
    print("[INFO] TensorFlow tidak terinstall, LSTM akan menggunakan prediksi naive.")

class LSTMPredictor:
    def __init__(self):
        self.model = None
        if Config.USE_LSTM and TF_AVAILABLE:
            self._load_or_build_model()
    
    def _load_or_build_model(self):
        if os.path.exists(Config.LSTM_MODEL_PATH):
            try:
                self.model = load_model(Config.LSTM_MODEL_PATH)
                print("[LSTM] Model loaded from disk.")
                return
            except:
                pass
        print("[LSTM] Membangun model baru (belum trained).")
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(Config.LSTM_LOOKBACK, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        self.model.save(Config.LSTM_MODEL_PATH)
    
    def predict_next_price(self, df: pd.DataFrame) -> float:
        if df is None or len(df) < Config.LSTM_LOOKBACK:
            return None
        
        close = df['close'].astype(float).values[-Config.LSTM_LOOKBACK:]
        
        # Fallback jika LSTM tidak tersedia
        if not TF_AVAILABLE or self.model is None:
            # Prediksi naive: regresi linear sederhana
            x = np.arange(len(close))
            z = np.polyfit(x, close, 1)
            pred = z[0] * (len(close)) + z[1]
            return float(pred)
        
        # Normalisasi
        min_c = close.min()
        max_c = close.max()
        if max_c - min_c < 1e-8:
            return close[-1]
        norm = (close - min_c) / (max_c - min_c)
        X = norm.reshape(1, Config.LSTM_LOOKBACK, 1)
        pred_norm = self.model.predict(X, verbose=0)[0][0]
        pred_price = pred_norm * (max_c - min_c) + min_c
        return float(pred_price)
    
    def train_model(self, df_list):
        """Fungsi opsional untuk training ulang (dipanggil periodik)"""
        if not TF_AVAILABLE or self.model is None:
            return
        # implementasi training jika diperlukan
        pass

ai_predictor = LSTMPredictor()
