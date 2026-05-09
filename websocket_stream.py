import websocket
import json
import threading
import time
from detectors import whale_pump_detector
from colorama import Fore


def on_message(ws, message):
    try:
        data = json.loads(message)

        print(f"[WS] {data}")

        # Format trade
        if 'pair' in data and 'price' in data:

            pair = data['pair']

            # btcidr -> btc_idr
            if '_' not in pair:

                if pair.endswith('idr'):
                    pair = pair.replace('idr', '_idr')

                elif pair.endswith('usdt'):
                    pair = pair.replace('usdt', '_usdt')

            price = float(data['price'])
            volume = float(data.get('volume', 0))

            whale_pump_detector.on_trade(pair, price, volume)

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


def on_open(ws):

    print(Fore.GREEN + "WebSocket connected!")

    subscribe_message = {
        "sub": "market.btcidr.trade"
    }

    ws.send(json.dumps(subscribe_message))


def start_websocket(callback=None):

    # Endpoint websocket baru
    ws_url = "wss://socket.indodax.com/ws"

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    if callback:
        on_message.callback = callback

    ws.run_forever()
