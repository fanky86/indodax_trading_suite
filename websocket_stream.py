# websocket_stream.py
import websocket
import json
import time
import threading
from colorama import Fore
from detectors import whale_pump_detector
from config import Config

WS_URL = "wss://ws3.indodax.com/ws/"
TOKEN = Config.INDODAX_WS_TOKEN  # ambil dari config

# Global variable untuk callback (dari main.py)
_callback = None

def on_open(ws):
    print(Fore.GREEN + "[WS] Connected to Indodax WebSocket")
    
    # Jika token tersedia, kirim autentikasi
    if TOKEN and TOKEN != "ISI_TOKEN_STATIC_ANDA":
        auth_msg = {
            "id": 1,
            "method": "public/auth",
            "params": {"token": TOKEN}
        }
        ws.send(json.dumps(auth_msg))
        print(Fore.CYAN + "[WS] Auth sent")
        time.sleep(1)
    else:
        print(Fore.YELLOW + "[WS] No token, skipping auth (might still work for public channels)")
    
    # Subscribe ke channel trade BTC/IDR (bisa ditambah pair lain)
    subscribe_msg = {
        "id": 2,
        "method": "public/subscribe",
        "params": {
            "channels": [
                "market:btcidr:trade",
                "market:ethidr:trade",
                "market:usdtidr:trade"
            ]
        }
    }
    ws.send(json.dumps(subscribe_msg))
    print(Fore.YELLOW + f"[WS] Subscribed to trade channels")

def on_message(ws, message):
    global _callback
    try:
        data = json.loads(message)
        # Untuk debugging (optional, bisa dihapus jika terlalu ramai)
        # print(Fore.BLUE + f"[WS MESSAGE] {data}")
        
        # Jika pesan berisi data trade
        if isinstance(data, dict):
            # Handle subscription result (abaikan)
            if "result" in data:
                return
            
            # Format pesan dari Indodax: {"params": {"data": {"price": ..., "amount": ...}}}
            if "params" in data and "data" in data["params"]:
                trade = data["params"]["data"]
                # Tentukan pair dari channel? Bisa disimpan saat subscribe, untuk sederhana kita hardcode dulu
                # Karena kita subscribe multiple channel, kita perlu tahu pair asal. 
                # Alternatif: parsing channel dari field lain. Untuk kemudahan, kita asumsikan semua trade adalah btc_idr.
                # Atau kita bisa simpan mapping channel->pair saat subscribe.
                # Untuk solusi lengkap, kita akan gunakan informasi channel yang mungkin ada di data.
                # Tapi karena tidak ada, kita tebak dari harga? Lebih baik kita parsing dari field "channel" jika ada.
                # Di sini saya akan gunakan simple: jika ada data, asumsikan btc_idr.
                pair = "btc_idr"   # default
                # Coba cari channel name
                if "channel" in data.get("params", {}):
                    ch = data["params"]["channel"]
                    if "ethidr" in ch:
                        pair = "eth_idr"
                    elif "usdtidr" in ch:
                        pair = "usdt_idr"
                    else:
                        pair = "btc_idr"
                
                price = float(trade.get("price", 0))
                volume = float(trade.get("amount", 0))
                
                # Kirim ke detector whale/pump
                whale_pump_detector.on_trade(pair, price, volume)
                
                # Panggil callback jika ada (dari main untuk update dashboard)
                if _callback:
                    _callback(pair, price, volume)
                    
    except Exception as e:
        print(Fore.RED + f"[WS] Error parsing message: {e}")

def on_error(ws, error):
    print(Fore.RED + f"[WS] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(Fore.YELLOW + "[WS] Closed, reconnecting in 5 seconds...")
    time.sleep(5)
    start_websocket(_callback)  # reconnect dengan callback yang sama

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
