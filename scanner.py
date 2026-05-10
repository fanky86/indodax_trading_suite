# =========================================
# scanner.py
# SMART AI SCANNER FINAL
# =========================================

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


# =========================================
# MAIN SCANNER
# =========================================

def scan_pair(pair):

    result = {}

    # =====================================
    # BTC MARKET FILTER
    # =====================================

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

    # =====================================
    # MULTI TIMEFRAME LOOP
    # =====================================

    for tf in Config.TIMEFRAMES:

        try:

            df = get_candles(
                pair,
                tf
            )

            # minimum candle
            if (

                df is None

                or

                len(df) < 100
            ):

                continue

            # =================================
            # INDICATORS
            # =================================

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

            # =================================
            # AI PREDICTION
            # =================================

            lstm_pred = (
                ai_predictor
                .predict_next_price(df)
            )

            # =================================
            # SCORE SYSTEM
            # =================================

            score = 0

            # =================================
            # RSI
            # =================================

            rsi = ind["rsi"]

            # bullish momentum
            if 50 <= rsi <= 70:

                score += 3

            # oversold bounce
            elif 30 <= rsi < 50:

                score += 2

            # extreme oversold
            elif rsi < 30:

                score += 4

            # strong bullish trend
            elif 70 < rsi <= 80:

                score += 1

            # too overbought
            elif rsi > 80:

                score -= 2

            # =================================
            # TREND
            # =================================

            if ind["trend"] == "BULLISH":

                score += 3

            else:

                score -= 1

            # =================================
            # MACD
            # =================================

            if (

                ind["macd"]

                >

                ind["macd_signal"]
            ):

                score += 3

            else:

                score -= 1

            # =================================
            # VOLUME SURGE
            # =================================

            if ind["vol_surge"]:

                score += 2

            # =================================
            # BTC MARKET FILTER
            # =================================

            if btc_bullish:

                score += 2

            else:

                score -= 1

            # =================================
            # AI PREDICTION
            # =================================

            if lstm_pred:

                current = (
                    ind["last_price"]
                )

                # bullish prediction
                if (

                    lstm_pred

                    >

                    current * 1.01
                ):

                    score += 3

                # bearish prediction
                elif (

                    lstm_pred

                    <

                    current * 0.99
                ):

                    score -= 2

            # =================================
            # CANDLE PATTERNS
            # =================================

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

                    score += 2

                elif p in bearish_patterns:

                    score -= 2

            # =================================
            # EXTRA MOMENTUM
            # =================================

            try:

                momentum = (

                    (
                        df['close'].iloc[-1]

                        -

                        df['close'].iloc[-5]
                    )

                    /

                    df['close'].iloc[-5]

                ) * 100

                if momentum > 3:

                    score += 3

                elif momentum > 1:

                    score += 2

                elif momentum < -3:

                    score -= 3

            except:

                pass

            # =================================
            # CONFIDENCE
            # =================================

            confidence = min(

                100,

                abs(score) * 8
            )

            # =================================
            # SIGNAL
            # =================================

            if score >= 10:

                signal = (
                    "STRONG BUY"
                )

            elif score >= 6:

                signal = (
                    "BUY"
                )

            elif score <= -10:

                signal = (
                    "STRONG SELL"
                )

            elif score <= -6:

                signal = (
                    "SELL"
                )

            else:

                signal = (
                    "HOLD"
                )

            # =================================
            # DEBUG OUTPUT
            # =================================

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

            # =================================
            # RESULT
            # =================================

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
