# data_fetcher.py
import requests
import pandas as pd
import time

def get_all_pairs():
    """Ambil semua pasangan IDR dan USDT dari Indodax"""
    try:
        data = requests.get("https://indodax.com/api/pairs", timeout=10).json()
        pairs = [p['ticker_id'] for p in data if '_idr' in p['ticker_id'] or '_usdt' in p['ticker_id']]
        print(f"[✓] Mendapatkan {len(pairs)} pasangan")
        return pairs
    except Exception as e:
        print(f"[!] Gagal ambil pairs: {e}")
        return []

def get_candles(pair, timeframe='1h'):
    """
    Mengambil data candlestick dari Indodax via endpoint publik
    timeframe: 1m,5m,15m,1h,4h,1d
    """
    # Konversi timeframe ke resolution (menit)
    res_map = {'1m':1, '5m':5, '15m':15, '1h':60, '4h':240, '1d':1440}
    resolution = res_map.get(timeframe, 60)
    
    # Ubah format pair: btc_idr -> btcidr (hilangkan underscore)
    symbol = pair.replace('_', '')
    
    # Timestamp sekarang dan 90 hari lalu
    to = int(time.time())
    from_ts = to - (90 * 24 * 3600)
    
    url = f"https://indodax.com/tradingview/history?symbol={symbol}&resolution={resolution}&from={from_ts}&to={to}"
    
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        
        # Validasi apakah data candlestick ada
        if not data.get('c') or len(data['c']) < 30:
            return None
        
        df = pd.DataFrame({
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v']
        }).astype(float)
        
        return df
    except Exception as e:
        # Error tidak perlu print berulang-ulang (cukup sekali)
        return None
