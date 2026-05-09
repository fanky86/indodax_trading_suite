# detectors.py
from collections import deque
from config import Config
from utils import send_telegram
from colorama import Fore

class WhalePumpDetector:
    def __init__(self):
        self.recent_trades = deque(maxlen=100)
        self.last_price = {}
        self.idr_to_usdt_rate = 16000.0  # default, akan diupdate dari usdt_idr

    def update_idr_rate(self, price_usdt_idr):
        if price_usdt_idr > 0:
            self.idr_to_usdt_rate = price_usdt_idr

    def on_trade(self, pair: str, price: float, volume: float):
        if '_idr' in pair:
            # volume adalah nilai transaksi dalam IDR
            value_usdt = volume / self.idr_to_usdt_rate
            value_display = f"{volume:,.0f} IDR (~{value_usdt:,.0f} USDT)"
        else:
            # pair USDT atau lainnya, asumsikan volume = jumlah koin
            value_usdt = price * volume
            value_display = f"{value_usdt:,.0f} USDT"

        if value_usdt > Config.WHALE_THRESHOLD_USDT:
            msg = f"🐋 WHALE ALERT: {pair} | {value_display} @ {price:,.2f}"
            send_telegram(msg)
            print(Fore.MAGENTA + msg)

        if pair in self.last_price:
            prev = self.last_price[pair]
            if prev > 0:
                pct_change = (price - prev) / prev * 100
                if pct_change > Config.PUMP_THRESHOLD_PCT:
                    msg = f"🚀 PUMP DETECTED: {pair} +{pct_change:.1f}% in last trade"
                    send_telegram(msg)
                    print(Fore.RED + msg)
        self.last_price[pair] = price

def detect_futures_pairs():
    import requests
    try:
        data = requests.get("https://indodax.com/api/pairs").json()
        futures = [p['ticker_id'] for p in data if p['ticker_id'].startswith('f_')]
        return futures
    except:
        return []

def update_usdt_idr_rate():
    import requests
    try:
        ticker = requests.get("https://indodax.com/api/ticker/usdt_idr").json()
        price = float(ticker['ticker']['last'])
        whale_pump_detector.update_idr_rate(price)
        return price
    except:
        return whale_pump_detector.idr_to_usdt_rate

whale_pump_detector = WhalePumpDetector()
