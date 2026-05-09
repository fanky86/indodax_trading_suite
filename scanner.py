# scanner.py

from data_fetcher import (
    get_candles
)

from indicators import (
    calculate_indicators
)

from smart_money import (
    detect_order_blocks,
    recognize_candlestick_patterns
)

from ai_models import (
    ai_predictor
)

from config import Config


def scan_pair(pair):

    result = {}

    # =========================
    # BTC FILTER
    # =========================

    btc_df = get_candles(
        "btc_idr",
        "1h"
    )

    btc_bullish = True

    if btc_df is not None:

        btc_ind = (
            calculate_indicators(
                btc_df
            )
        )

        if btc_ind["trend"] != "BULLISH":

            btc_bullish = False

    # =========================
    # MAIN LOOP
    # =========================

    for tf in Config.TIMEFRAMES:

        try:

            df = get_candles(
                pair,
                tf
            )

            if (

                df is None

                or

                len(df) < 100
            ):

                continue

            # =====================
            # INDICATORS
            # =====================

            ind = (
                calculate_indicators(
                    df
                )
            )

            patterns = (
                recognize_candlestick_patterns(
                    df
                )
            )

            smc = (
                detect_order_blocks(
                    df
                )
            )

            # =====================
            # AI PREDICTION
            # =====================

            lstm_pred = (
                ai_predictor
                .predict_next_price(df)
            )

            # =====================
            # SCORE SYSTEM
            # =====================

            score = 0

            # RSI

            if ind["rsi"] < 30:

                score += 3

            elif ind["rsi"] < 40:

                score += 1

            elif ind["rsi"] > 70:

                score -= 3

            elif ind["rsi"] > 60:

                score -= 1

            # TREND

            if ind["trend"] == "BULLISH":

                score += 2

            else:

                score -= 2

            # MACD

            if (

                ind["macd"]

                >

                ind["macd_signal"]
            ):

                score += 2

            else:

                score -= 2

            # VOLUME

            if ind["vol_surge"]:

                score += 1

            # BTC FILTER

            if btc_bullish:

                score += 2

            else:

                score -= 2

            # AI

            if lstm_pred:

                current = (
                    ind["last_price"]
                )

                if (

                    lstm_pred

                    >

                    current * 1.01
                ):

                    score += 2

                elif (

                    lstm_pred

                    <

                    current * 0.99
                ):

                    score -= 2

            # PATTERN

            bullish_patterns = [

                "HAMMER",

                "ENGULFING_BULL"
            ]

            bearish_patterns = [

                "SHOOTING_STAR",

                "ENGULFING_BEAR"
            ]

            for p in patterns:

                if p in bullish_patterns:

                    score += 1

                elif p in bearish_patterns:

                    score -= 1

            # =====================
            # CONFIDENCE
            # =====================

            confidence = min(

                100,

                abs(score) * 10
            )

            # =====================
            # SIGNAL
            # =====================

            if score >= 8:

                signal = (
                    "STRONG BUY"
                )

            elif score >= 4:

                signal = "BUY"

            elif score <= -8:

                signal = (
                    "STRONG SELL"
                )

            elif score <= -4:

                signal = "SELL"

            else:

                signal = "HOLD"

            # =====================
            # DEBUG
            # =====================

            print(

                f"{pair} {tf} | "

                f"RSI="
                f"{ind['rsi']:.2f} | "

                f"Score="
                f"{score:.2f} | "

                f"Confidence="
                f"{confidence}% | "

                f"Signal="
                f"{signal}"
            )

            # =====================
            # RESULT
            # =====================

            result[tf] = {

                "price":

                round(
                    ind["last_price"],
                    4
                ),

                "rsi":

                round(
                    ind["rsi"],
                    2
                ),

                "trend":

                ind["trend"],

                "score":

                round(
                    score,
                    2
                ),

                "confidence":

                confidence,

                "signal":

                signal,

                "patterns":

                patterns,

                "support":

                smc["support"],

                "resistance":

                smc["resistance"],

                "lstm_pred":

                round(
                    lstm_pred,
                    4
                )

                if lstm_pred

                else None
            }

        except Exception as e:

            print(

                f"[SCAN ERROR] "

                f"{pair} "

                f"{tf}: {e}"
            )

    return result
