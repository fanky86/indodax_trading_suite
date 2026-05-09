# indicators.py
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands

def calculate_indicators(df: pd.DataFrame):
    close = df['close'].astype(float)
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    volume = df['volume'].astype(float)
    
    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]
    macd = MACD(close)
    macd_line = macd.macd().iloc[-1]
    macd_signal = macd.macd_signal().iloc[-1]
    bb = BollingerBands(close)
    bb_upper = bb.bollinger_hband().iloc[-1]
    bb_lower = bb.bollinger_lband().iloc[-1]
    
    avg_volume = volume.tail(20).mean()
    vol_surge = volume.iloc[-1] > avg_volume * 1.5
    
    trend = "BULLISH" if ema20 > ema50 else "BEARISH"
    last_price = float(close.iloc[-1])
    
    return {
        'rsi': float(rsi),
        'ema20': float(ema20),
        'ema50': float(ema50),
        'macd': float(macd_line),
        'macd_signal': float(macd_signal),
        'bb_upper': float(bb_upper),
        'bb_lower': float(bb_lower),
        'vol_surge': bool(vol_surge),
        'trend': trend,
        'last_price': last_price
    }
