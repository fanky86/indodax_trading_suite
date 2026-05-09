# detectors.py
from collections import deque
from config import Config
from utils import send_telegram
from colorama import Fore

class WhalePumpDetector:
    def __init__(self):
        self.recent_trades = deque(maxlen=100)
        self.last_price = {}
    
    def on_trade(self, pair: str, price: float, volume: float):
        usdt_value = price * volume
        if usdt_value > Config.WHALE_THRESHOLD_USDT:
            msg = f"🐋 WHALE ALERT: {pair} | {usdt_value:,.0f} USDT @ {price}"
            send_telegram(msg)
            print(Fore.MAGENTA + msg)
        
        if pair in self.last_price:
            prev = self.last_price[pair]
            pct_change = (price - prev) / prev * 100
            if pct_change > Config.PUMP_THRESHOLD_PCT:
                msg = f"🚀 PUMP DETECTED: {pair} +{pct_change:.1f}% in last trade"
                send_telegram(msg)
                print(Fore.RED + msg)
        self.last_price[pair] = price

def detect_futures_pairs():
    """Mendeteksi pair futures (biasanya f_ prefix)"""
    import requests
    try:
        data = requests.get("https://indodax.com/api/pairs").json()
        futures = [p['ticker_id'] for p in data if p['ticker_id'].startswith('f_')]
        return futures
    except:
        return []

whale_pump_detector = WhalePumpDetector()
