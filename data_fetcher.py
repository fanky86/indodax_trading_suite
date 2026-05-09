# data_fetcher.py
import requests
import pandas as pd
import time
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
    Indodax menggunakan symbol tanpa underscore, contoh: btc_idr -> btc_idr? Ternyata harus 'btcidr'
    """
    resolution_map = {
        "1m": 1, "5m": 5, "15m": 15,
        "1h": 60, "4h": 240, "1d": 1440
    }
    resolution = resolution_map.get(timeframe, 60)
    
    # Ubah pair dari "btc_idr" menjadi "btcidr" (hilangkan underscore)
    symbol = pair.replace('_', '')
    
    to_timestamp = int(time.time())
    url = f"https://indodax.com/tradingview/history?symbol={symbol}&resolution={resolution}&from=0&to={to_timestamp}"
    
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = resp.json()
        if 'c' not in data or not data['c']:
            return None
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(data['t'], unit='s'),
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v']
        }).astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {pair} {timeframe}: {e}")
        return None
