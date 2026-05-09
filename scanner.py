# scanner.py

from data_fetcher import get_candles
from indicators import calculate_indicators
from smart_money import detect_order_blocks, recognize_candlestick_patterns
from ai_models import ai_predictor
from config import Config


def scan_pair(pair: str) -> dict:

    result = {}

    for tf in Config.TIMEFRAMES:

        df = get_candles(pair, tf)

        if df is None or len(df) < 50:
            continue

        ind = calculate_indicators(df)

        patterns = recognize_candlestick_patterns(df)

        smc = detect_order_blocks(df)

        lstm_pred = ai_predictor.predict_next_price(df)

        score = 0.0

        # RSI
        if ind['rsi'] < 30:
            score += 2.5

        elif ind['rsi'] < 40:
            score += 1

        elif ind['rsi'] > 70:
            score -= 2.5

        elif ind['rsi'] > 60:
            score -= 1

        # Trend
        if ind['trend'] == 'BULLISH':
            score += 2
        else:
            score -= 2

        # MACD
        if ind['macd'] > ind['macd_signal']:
            score += 1.5
        else:
            score -= 1.5

        # Volume surge
        if ind['vol_surge']:
            score += 1

        # AI prediction
        if lstm_pred:

            if lstm_pred > ind['last_price'] * 1.005:
                score += 2

            elif lstm_pred < ind['last_price'] * 0.995:
                score -= 2

        # Signal generation
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

        # DEBUG
        print(
            f"{pair} {tf} | "
            f"RSI={ind['rsi']:.2f} | "
            f"Trend={ind['trend']} | "
            f"MACD={ind['macd']:.4f} | "
            f"Score={score:.2f} | "
            f"Signal={signal}"
        )

        result[tf] = {
            'price': round(ind['last_price'], 4),
            'rsi': round(ind['rsi'], 2),
            'trend': ind['trend'],
            'score': round(score, 2),
            'signal': signal,
            'patterns': patterns,
            'support': smc['support'],
            'resistance': smc['resistance'],
            'lstm_pred': round(lstm_pred, 4) if lstm_pred else None
        }

    return result
