# websocket_stream.py (final)

import websocket
import json
import time
from colorama import Fore

from config import Config
from detectors import whale_pump_detector
from data_fetcher import get_all_pairs

# Optional realtime store (abaikan jika tidak ada)
try:
    from realtime_store import add_trade
except ImportError:
    def add_trade(pair, price, amount):
        pass  # dummy function

WS_URL = "wss://ws3.indodax.com/ws/"
_callback = None

def parse_multi_json(data_str):
    results = []
    decoder = json.JSONDecoder()
    idx = 0
    data_str = data_str.strip()
    while idx < len(data_str):
        try:
            obj, end = decoder.raw_decode(data_str, idx)
            results.append(obj)
            idx = end
            while idx < len(data_str) and data_str[idx] in ' \n\r\t':
                idx += 1
        except json.JSONDecodeError:
            break
    return results

def on_open(ws):
    print(Fore.GREEN + "[WS] Connected to Indodax WebSocket")
    auth_payload = {"params": {"token": Config.INDODAX_WS_TOKEN}, "id": 1}
    ws.send(json.dumps(auth_payload))
    print(Fore.CYAN + "[WS] Auth request sent")

def on_message(ws, message):
    global _callback
    try:
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        parsed = parse_multi_json(message)
        for data in parsed:
            # Auth success
            if isinstance(data, dict) and "result" in data:
                result = data["result"]
                if isinstance(result, dict):
                    client_id = result.get("client") or result.get("client_id")
                    if client_id:
                        print(Fore.GREEN + f"[WS] Authenticated! Client ID: {client_id}")
                        subscribe_all_pairs(ws)
                        continue
            # Trade stream (format Indodax: {"result":{"channel":"...","data":{"data":[...]}}})
            if isinstance(data, dict) and "result" in data:
                result = data["result"]
                if isinstance(result, dict) and "channel" in result and "trade-activity" in result["channel"]:
                    trade_list = result.get("data", {}).get("data", [])
                    for trade in trade_list:
                        try:
                            raw_pair = trade[0]   # e.g. "btcidr"
                            price = float(trade[4])
                            amount = float(trade[6])  # coin amount
                            pair = raw_pair
                            if pair.endswith("idr"):
                                pair = pair[:-3] + "_idr"
                            elif pair.endswith("usdt"):
                                pair = pair[:-4] + "_usdt"
                            add_trade(pair, price, amount)
                            whale_pump_detector.on_trade(pair, price, amount)
                            if _callback:
                                _callback(pair, price, amount)
                        except Exception:
                            pass
    except Exception as e:
        print(Fore.RED + f"[WS GENERAL ERROR] {e}")

def subscribe_all_pairs(ws):
    try:
        print(Fore.YELLOW + "[WS] Loading pairs...")
        pairs = get_all_pairs()
        subscribed = 0
        for pair in pairs:
            try:
                symbol = pair.replace("_", "")
                channel = f"market:trade-activity-{symbol}"
                payload = {"method": 1, "params": {"channel": channel}, "id": int(time.time() * 1000)}
                ws.send(json.dumps(payload))
                subscribed += 1
                if subscribed % 50 == 0:
                    print(Fore.CYAN + f"[WS] Subscribed {subscribed}/{len(pairs)}")
                time.sleep(0.02)
            except Exception:
                pass
        print(Fore.GREEN + f"[WS] Total subscribed: {subscribed}")
    except Exception as e:
        print(Fore.RED + f"[WS SUB ERROR] {e}")

def on_error(ws, error):
    print(Fore.RED + f"[WS ERROR] {error}")

def on_close(ws, close_status_code, close_msg):
    print(Fore.YELLOW + "[WS CLOSED] reconnecting in 5s...")
    time.sleep(5)
    start_websocket(_callback)

def start_websocket(callback=None):
    global _callback
    _callback = callback
    ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever()
