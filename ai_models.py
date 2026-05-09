# ai_models.py

import numpy as np
from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Dense,
    LSTM,
    Input
)

from config import Config


class AIPredictor:

    def __init__(self):

        self.scaler = MinMaxScaler(
            feature_range=(0, 1)
        )

        self.model = self.build_model()

    # =====================================
    # BUILD MODEL
    # =====================================

    def build_model(self):

        model = Sequential([

            Input(
                shape=(Config.LSTM_LOOKBACK, 1)
            ),

            LSTM(
                50,
                return_sequences=True
            ),

            LSTM(50),

            Dense(1)
        ])

        model.compile(
            optimizer='adam',
            loss='mse'
        )

        return model

    # =====================================
    # PREDICT
    # =====================================

    def predict_next_price(
        self,
        df
    ):

        try:

            closes = (
                df['close']
                .values
                .reshape(-1, 1)
            )

            # minimal candle
            if (
                len(closes)
                <
                Config.LSTM_LOOKBACK
            ):

                return None

            # =================================
            # FIT SCALER
            # =================================

            self.scaler.fit(
                closes
            )

            scaled_data = (
                self.scaler.transform(
                    closes
                )
            )

            # ambil last sequence
            X = []

            X.append(

                scaled_data[
                    -Config.LSTM_LOOKBACK:
                ]
            )

            X = np.array(X)

            # reshape
            X = X.reshape(

                X.shape[0],

                X.shape[1],

                1
            )

            # predict
            pred_scaled = (
                self.model.predict(
                    X,
                    verbose=0
                )
            )

            # inverse scale
            prediction = (
                self.scaler
                .inverse_transform(
                    pred_scaled
                )
            )

            return float(
                prediction[0][0]
            )

        except Exception as e:

            print(
                f"[LSTM ERROR] {e}"
            )

            return None


# singleton
ai_predictor = AIPredictor()
