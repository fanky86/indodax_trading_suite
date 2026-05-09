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
        if ind['rsi'] < 30:
            score += 2
        elif ind['rsi'] > 70:
            score -= 2
        if ind['trend'] == 'BULLISH':
            score += 2
        else:
            score -= 2
        if ind['macd'] > ind['macd_signal']:
            score += 2
        else:
            score -= 2
        if ind['vol_surge']:
            score += 1
        if lstm_pred and lstm_pred > ind['last_price'] * 1.01:
            score += 1.5
        elif lstm_pred and lstm_pred < ind['last_price'] * 0.99:
            score -= 1.5

        if score >= 5:
            signal = "STRONG BUY"
        elif score >= 3:
            signal = "BUY"
        elif score <= -5:
            signal = "STRONG SELL"
        elif score <= -3:
            signal = "SELL"
        else:
            signal = "HOLD"

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
