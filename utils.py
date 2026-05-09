# utils.py
import requests
import hmac
import hashlib
import time
from datetime import datetime
from colorama import Fore
from config import Config

def send_telegram(message: str):
    if not Config.TELEGRAM_ENABLED:
        return
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": Config.TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(Fore.RED + f"Telegram error: {e}")

def indodax_signed_request(endpoint: str, params: dict = None):
    """Melakukan request ke private API Indodax"""
    if not Config.INDODAX_API_KEY or "ISI_API_KEY" in Config.INDODAX_API_KEY:
        print(Fore.YELLOW + "[WARNING] API key belum diisi, real order disabled.")
        return None
    if params is None:
        params = {}
    params['timestamp'] = int(time.time() * 1000)
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sign = hmac.new(Config.INDODAX_SECRET_KEY.encode('utf-8'),
                    param_str.encode('utf-8'),
                    hashlib.sha512).hexdigest()
    headers = {"Key": Config.INDODAX_API_KEY, "Sign": sign}
    url = f"{Config.INDODAX_BASE_URL}/{endpoint}"
    try:
        resp = requests.post(url, data=params, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        print(Fore.RED + f"Signed request error: {e}")
        return None

def get_balance(coin='usdt'):
    res = indodax_signed_request('getInfo')
    if res and 'return' in res and 'balance' in res['return']:
        return float(res['return']['balance'].get(coin, 0))
    return 0.0

def place_order(pair: str, order_type: str, price: float, amount: float):
    """order_type: 'buy' atau 'sell'"""
    if not Config.ALLOW_REAL_ORDER:
        print(Fore.CYAN + f"[SIMULASI] {order_type.upper()} {amount:.8f} {pair} @ {price}")
        return {"success": True, "simulate": True}
    params = {
        "pair": pair,
        "type": order_type,
        "price": str(price),
        "amount": str(amount)
    }
    return indodax_signed_request('trade', params)

def log_to_csv(data: dict, filename: str = "trading_log.csv"):
    import csv
    import os
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
