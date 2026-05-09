# =========================================
# scanner.py
# =========================================

from data_fetcher import get_candles
from realtime_store import get_realtime_df
from indicators import calculate_indicators
from smart_money import (
    detect_order_blocks,
    recognize_candlestick_patterns
)
from ai_models import ai_predictor
from config import Config


def scan_pair(pair: str):

    result = {}

    for tf in Config.TIMEFRAMES:

        # realtime first
        df = get_realtime_df(pair)

        # fallback API
        if df is None:

            df = get_candles(
                pair,
                tf
            )

        if df is None:

            continue

        if len(df) < 30:

            continue

        try:

            ind = calculate_indicators(df)

            patterns = (
                recognize_candlestick_patterns(df)
            )

            smc = detect_order_blocks(df)

            lstm_pred = (
                ai_predictor.predict_next_price(df)
            )

            # =================================
            # SCORE
            # =================================

            score = 0.0

            confidence = 0

            # RSI
            if ind['rsi'] < 30:

                score += 2.5
                confidence += 20

            elif ind['rsi'] < 40:

                score += 1
                confidence += 10

            elif ind['rsi'] > 70:

                score -= 2.5

            elif ind['rsi'] > 60:

                score -= 1

            # Trend
            if ind['trend'] == 'BULLISH':

                score += 2
                confidence += 20

            else:

                score -= 2

            # MACD
            if ind['macd'] > ind['macd_signal']:

                score += 1.5
                confidence += 20

            else:

                score -= 1.5

            # Volume surge
            if ind['vol_surge']:

                score += 1
                confidence += 10

            # AI prediction
            if lstm_pred:

                if (
                    lstm_pred >
                    ind['last_price'] * 1.005
                ):

                    score += 2
                    confidence += 20

                elif (
                    lstm_pred <
                    ind['last_price'] * 0.995
                ):

                    score -= 2

            # =================================
            # SIGNAL
            # =================================

            if score >= 4:

                signal = "STRONG BUY"

            elif score >= 1.5:

                signal = "BUY"

            elif score <= -4:

                signal = "STRONG SELL"

            elif score <= -1.5:

                signal = "SELL"

            else:

                signal = "HOLD"

            print(

                f"{pair} {tf} | "

                f"RSI={ind['rsi']:.2f} | "

                f"Score={score:.2f} | "

                f"Confidence={confidence}% | "

                f"Signal={signal}"
            )

            result[tf] = {

                'price': round(
                    ind['last_price'],
                    4
                ),

                'rsi': round(
                    ind['rsi'],
                    2
                ),

                'trend': ind['trend'],

                'score': round(
                    score,
                    2
                ),

                'confidence': confidence,

                'signal': signal,

                'patterns': patterns,

                'support': smc['support'],

                'resistance': smc['resistance'],

                'lstm_pred': (
                    round(lstm_pred, 4)
                    if lstm_pred
                    else None
                )
            }

        except Exception as e:

            print(
                f"[SCAN ERROR] "
                f"{pair} {tf}: {e}"
            )

    return result
