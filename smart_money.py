# smart_money.py
import pandas as pd
import numpy as np

def detect_order_blocks(df: pd.DataFrame, window=5):
    """Deteksi support/resistance berdasarkan swing high/low"""
    highs = df['high'].astype(float).values
    lows = df['low'].astype(float).values
    
    swing_highs = []
    for i in range(window, len(highs)-window):
        if all(highs[i] >= highs[i-window:i]) and all(highs[i] >= highs[i+1:i+window+1]):
            swing_highs.append(highs[i])
    
    swing_lows = []
    for i in range(window, len(lows)-window):
        if all(lows[i] <= lows[i-window:i]) and all(lows[i] <= lows[i+1:i+window+1]):
            swing_lows.append(lows[i])
    
    resistance = swing_highs[-1] if swing_highs else None
    support = swing_lows[-1] if swing_lows else None
    
    return {
        'resistance': resistance,
        'support': support,
        'order_block_bullish': support,
        'order_block_bearish': resistance
    }

def recognize_candlestick_patterns(df: pd.DataFrame):
    patterns = []
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(last['close'] - last['open'])
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']
    
    # Doji
    if body <= (last['high'] - last['low']) * 0.1:
        patterns.append("DOJI")
    # Hammer
    if lower_wick > body * 2 and upper_wick < body * 0.5 and last['close'] > last['open']:
        patterns.append("HAMMER")
    # Engulfing
    if (last['close'] > last['open'] and prev['close'] < prev['open'] and
        last['close'] > prev['open'] and last['open'] < prev['close']):
        patterns.append("BULLISH_ENGULFING")
    if (last['close'] < last['open'] and prev['close'] > prev['open'] and
        last['close'] < prev['open'] and last['open'] > prev['close']):
        patterns.append("BEARISH_ENGULFING")
    
    return patterns
