# data_fetcher.py
import ccxt
import pandas as pd
import requests
import time

exchange = ccxt.indodax({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def get_all_pairs():
    """Ambil semua pair IDR dan USDT"""
    try:
        markets = exchange.load_markets()
        pairs = [symbol for symbol in markets if '_idr' in symbol or '_usdt' in symbol]
        if pairs:
            print(f"[✓] Mendapatkan {len(pairs)} pasangan via ccxt")
            return pairs
    except Exception as e:
        print(f"[!] ccxt error: {e}, fallback ke API langsung...")
    
    # Fallback: API langsung Indodax
    try:
        data = requests.get("https://indodax.com/api/pairs", timeout=10).json()
        pairs = [p['ticker_id'] for p in data if '_idr' in p['ticker_id'] or '_usdt' in p['ticker_id']]
        print(f"[✓] Mendapatkan {len(pairs)} pasangan via API langsung")
        return pairs
    except Exception as e:
        print(f"[!] Gagal total: {e}")
        return []

def get_candles(pair, timeframe='1h'):
    tf_map = {'1m':'1m','5m':'5m','15m':'15m','1h':'1h','4h':'4h','1d':'1d'}
    tf = tf_map.get(timeframe, '1h')
    try:
        ohlcv = exchange.fetch_ohlcv(pair, tf, limit=200)
        if not ohlcv:
            return None
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.astype(float)
        return df
    except Exception as e:
        # Jangan print error setiap kali (bisa spam)
        return None
