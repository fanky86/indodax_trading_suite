# websocket_stream.py
import websocket
import json
import threading
import time
from detectors import whale_pump_detector
from colorama import Fore

def on_message(ws, message):
    try:
        data = json.loads(message)
        # Format pesan Indodax: {"pair":"btcidr","price":xxx,"volume":xxx}
        if 'pair' in data and 'price' in data:
            pair = data['pair']
            price = float(data['price'])
            volume = float(data.get('volume', 0))
            whale_pump_detector.on_trade(pair, price, volume)
            # bisa juga kirim ke dashboard via global variable atau callback
            if hasattr(on_message, 'callback'):
                on_message.callback(pair, price, volume)
    except Exception as e:
        print(Fore.RED + f"WS parse error: {e}")

def on_error(ws, error):
    print(Fore.RED + f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(Fore.YELLOW + "WebSocket closed, reconnecting in 5s...")
    time.sleep(5)
    start_websocket()

def start_websocket(callback=None):
    """
    callback function signature: callback(pair, price, volume)
    """
    ws_url = "wss://ws.indodax.com/trade"   # Endpoint publik Indodax
    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    if callback:
        on_message.callback = callback
    ws.run_forever()
