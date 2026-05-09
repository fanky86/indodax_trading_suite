import ccxt
import pandas as pd

exchange = ccxt.indodax({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def get_all_pairs():
    try:
        markets = exchange.load_markets()
        pairs = [symbol for symbol in markets if '_idr' in symbol or '_usdt' in symbol]
        print(f"[DEBUG] Dapat {len(pairs)} pairs")
        return pairs
    except Exception as e:
        print(f"Error get pairs: {e}")
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
        print(f"Error fetching {pair} {timeframe}: {e}")
        return None
