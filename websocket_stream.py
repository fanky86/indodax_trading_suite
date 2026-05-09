# websocket_stream.py
import websocket
import json
import time
import threading
from colorama import Fore
from detectors import whale_pump_detector
from config import Config

# Gunakan token statis yang benar dari dokumentasi
# Gunakan ini untuk production:
STATIC_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5NDY2MTg0MTV9.UR1lBM6Eqh0yWz-PVirw1uPCxe60FdchR8eNVdsskeo"

# Atau jika ingin mencoba di demo, gunakan token ini:
# STATIC_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.OqWmyrtOvp_DvIdBnOgU9gyXhURkEOtu8brZtvwjYAw"

WS_URL = "wss://ws3.indodax.com/ws/"  # Ganti ke "wss://ws.demo-indodax.com/ws/" untuk demo

# Global variable untuk callback (dari main.py)
_callback = None

def on_open(ws):
    print(Fore.GREEN + "[WS] Connected to Indodax WebSocket")
    
    # Kirim request autentikasi sesuai dokumentasi (tanpa method field)
    auth_msg = {
        "params": {"token": STATIC_TOKEN},
        "id": 1
    }
    ws.send(json.dumps(auth_msg))
    print(Fore.CYAN + "[WS] Auth request sent")
    # Beri waktu untuk proses autentikasi
    time.sleep(1)

def on_message(ws, message):
    global _callback
    try:
        data = json.loads(message)
        
        # Tangani response auth
        if "result" in data and "client" in data["result"]:
            print(Fore.GREEN + f"[WS] Authenticated! Client ID: {data['result']['client']}")
            # Setelah auth berhasil, subscribe ke channel
            subscribe_to_channels(ws)
            return
        
        # Parse data trade activity
        if "result" in data and "channel" in data["result"] and "data" in data["result"]:
            channel = data["result"]["channel"]
            # Format channel yang di-subscribe: "market:trade-activity-btcidr"
            if channel.startswith("market:trade-activity-"):
                trade_data = data["result"]["data"]["data"]
                for trade in trade_data:
                    # Format trade array: [pair, timestamp, sequence, side, price, idr_volume, btc_volume]
                    pair_raw = trade[0]  # "btcidr"
                    price = float(trade[4])
                    volume = float(trade[5])
                    
                    # Ubah format pair dari "btcidr" menjadi "btc_idr"
                    if '_' not in pair_raw:
                        if 'idr' in pair_raw:
                            pair = pair_raw.replace('idr', '_idr')
                        elif 'usdt' in pair_raw:
                            pair = pair_raw.replace('usdt', '_usdt')
                        else:
                            pair = pair_raw
                    
                    # Kirim ke detector whale/pump
                    whale_pump_detector.on_trade(pair, price, volume)
                    
                    # Panggil callback jika ada
                    if _callback:
                        _callback(pair, price, volume)
            
    except Exception as e:
        print(Fore.RED + f"[WS] Error parsing message: {e}")

def subscribe_to_channels(ws):
    """Berlangganan ke channel trade activity untuk pasangan yang diinginkan"""
    print(Fore.YELLOW + "[WS] Subscribing to trade channels...")
    
    # Daftar pasangan yang ingin dipantau
    pairs_to_subscribe = ["btcidr", "ethidr", "usdtidr"]
    
    for pair in pairs_to_subscribe:
        subscribe_msg = {
            "method": 1,  # method 1 untuk subscribe
            "params": {"channel": f"market:trade-activity-{pair}"},
            "id": 2  # id unik untuk request ini
        }
        ws.send(json.dumps(subscribe_msg))
        print(Fore.YELLOW + f"[WS] Subscribed to market:trade-activity-{pair}")

def on_error(ws, error):
    print(Fore.RED + f"[WS] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(Fore.YELLOW + "[WS] Closed, reconnecting in 5 seconds...")
    time.sleep(5)
    start_websocket(_callback)

def start_websocket(callback=None):
    """Callback akan dipanggil dengan (pair, price, volume) setiap ada trade"""
    global _callback
    _callback = callback
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
