# websocket_stream.py
import websocket
import json
import time
import requests
from colorama import Fore

from config import Config
from detectors import whale_pump_detector
from data_fetcher import get_all_pairs

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

def get_top_volume_pairs(limit=30):
    try:
        all_pairs = get_all_pairs()
        tickers = {}
        for pair in all_pairs[:100]:
            try:
                symbol = pair.replace('_', '')
                url = f"https://indodax.com/api/ticker/{symbol}"
                resp = requests.get(url, timeout=5).json()
                vol = float(resp.get('ticker', {}).get('vol_idr', 0))
                tickers[pair] = vol
            except:
                tickers[pair] = 0
        sorted_pairs = sorted(tickers.items(), key=lambda x: x[1], reverse=True)
        top_pairs = [p[0] for p in sorted_pairs[:limit]]
        print(Fore.GREEN + f"[WS] Top {len(top_pairs)} pairs by volume: {top_pairs[:5]}...")
        return top_pairs
    except Exception as e:
        print(Fore.RED + f"[WS] Gagal get top pairs: {e}, fallback ke 30 random")
        return get_all_pairs()[:30]

def on_open(ws):
    print(Fore.GREEN + "[WS] Connected to Indodax WebSocket")
    # Auth payload: hanya params.token dan id (tanpa method)
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
                        subscribe_top_pairs(ws)
                        continue
            # Trade stream (format sesuai dokumentasi)
            if isinstance(data, dict) and "result" in data:
                result = data["result"]
                if isinstance(result, dict) and "channel" in result and "trade-activity" in result["channel"]:
                    trade_list = result.get("data", {}).get("data", [])
                    for trade in trade_list:
                        try:
                            raw_pair = trade[0]
                            price = float(trade[4])
                            amount = float(trade[6])  # coin amount
                            pair = raw_pair
                            if pair.endswith("idr"):
                                pair = pair[:-3] + "_idr"
                            elif pair.endswith("usdt"):
                                pair = pair[:-4] + "_usdt"
                            whale_pump_detector.on_trade(pair, price, amount)
                            if _callback:
                                _callback(pair, price, amount)
                        except:
                            pass
    except Exception as e:
        print(Fore.RED + f"[WS GENERAL ERROR] {e}")

def subscribe_top_pairs(ws):
    try:
        print(Fore.YELLOW + "[WS] Getting top volume pairs...")
        pairs = get_top_volume_pairs(limit=30)
        if not pairs:
            pairs = get_all_pairs()[:30]
        # Subscribe dengan format "channels" (array) yang benar
        channels = [f"market:trade-activity-{p.replace('_', '')}" for p in pairs]
        payload = {
            "method": 1,
            "params": {"channels": channels},   # ← PERBAIKAN: gunakan array channels
            "id": int(time.time() * 1000)
        }
        ws.send(json.dumps(payload))
        print(Fore.GREEN + f"[WS] Subscribed to {len(channels)} channels")
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
    ws = websocket.WebSocketApp(WS_URL,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()
