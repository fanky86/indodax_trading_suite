# data_fetcher.py
import requests
import pandas as pd
from typing import Optional

def get_all_pairs():
    """Mengambil semua pasangan IDR & USDT dari Indodax"""
    try:
        data = requests.get("https://indodax.com/api/pairs").json()
        pairs = []
        for item in data:
            ticker = item['ticker_id']
            if '_idr' in ticker or '_usdt' in ticker:
                pairs.append(ticker)
        return pairs
    except:
        return []

def get_candles(pair: str, timeframe: str = "1h") -> Optional[pd.DataFrame]:
    """
    timeframe: 1m,5m,15m,1h,4h,1d
    """
    resolution_map = {
        "1m": 1, "5m": 5, "15m": 15,
        "1h": 60, "4h": 240, "1d": 1440
    }
    resolution = resolution_map.get(timeframe, 60)
    url = f"https://indodax.com/tradingview/history_v2?symbol={pair.upper()}&resolution={resolution}&from=0&to=9999999999"
    try:
        resp = requests.get(url, timeout=10).json()
        if 'c' not in resp or not resp['c']:
            return None
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(resp['t'], unit='s'),
            'open': resp['o'],
            'high': resp['h'],
            'low': resp['l'],
            'close': resp['c'],
            'volume': resp['v']
        }).astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {pair} {timeframe}: {e}")
        return None
