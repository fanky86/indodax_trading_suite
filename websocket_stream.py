# websocket_stream.py

import websocket
import json
import time
import threading
from colorama import Fore

from config import Config
from detectors import whale_pump_detector
from data_fetcher import get_all_pairs


WS_URL = "wss://ws3.indodax.com/ws/"


# =========================================
# ON OPEN
# =========================================

def on_open(ws):

    print(
        Fore.GREEN +
        "[WS] Connected to Indodax WebSocket"
    )

    # AUTH
    auth_payload = {

        "id": 1,

        "method": "public/auth",

        "params": {

            "token": Config.INDODAX_WS_TOKEN
        }
    }

    ws.send(
        json.dumps(auth_payload)
    )

    print(
        Fore.CYAN +
        "[WS] Auth request sent"
    )


# =========================================
# ON MESSAGE
# =========================================

def on_message(ws, message):

    try:

        data = json.loads(message)

        # print(data)

        # auth success
        if (
            isinstance(data, dict)
            and
            data.get("result")
        ):

            result = data["result"]

            if (
                isinstance(result, dict)
                and
                result.get("client_id")
            ):

                print(
                    Fore.GREEN +
                    f"[WS] Authenticated! "
                    f"Client ID: "
                    f"{result['client_id']}"
                )

                subscribe_all_pairs(ws)

                return

        # realtime trade
        if (
            isinstance(data, dict)
            and
            "params" in data
        ):

            params = data["params"]

            channel = params.get(
                "channel",
                ""
            )

            trade_data = params.get(
                "data",
                {}
            )

            if (
                "trade-activity" in channel
                and
                trade_data
            ):

                # market:trade-activity-btcidr
                raw_pair = (
                    channel
                    .split("-")[-1]
                )

                # btcidr -> btc_idr
                pair = raw_pair

                if pair.endswith("idr"):

                    pair = (
                        pair[:-3]
                        + "_idr"
                    )

                elif pair.endswith("usdt"):

                    pair = (
                        pair[:-4]
                        + "_usdt"
                    )

                price = float(
                    trade_data.get(
                        "price",
                        0
                    )
                )

                amount = float(
                    trade_data.get(
                        "amount",
                        0
                    )
                )

                whale_pump_detector.on_trade(
                    pair,
                    price,
                    amount
                )

    except Exception as e:

        print(
            Fore.RED +
            f"[WS ERROR] {e}"
        )


# =========================================
# SUBSCRIBE ALL PAIRS
# =========================================

def subscribe_all_pairs(ws):

    try:

        print(
            Fore.YELLOW +
            "[WS] Loading pairs..."
        )

        pairs = get_all_pairs()

        subscribed = 0

        for pair in pairs:

            try:

                # btc_idr -> btcidr
                symbol = pair.replace(
                    "_",
                    ""
                )

                channel = (
                    f"market:trade-activity-{symbol}"
                )

                payload = {

                    "id": int(time.time()),

                    "method": "public/subscribe",

                    "params": {

                        "channels": [
                            channel
                        ]
                    }
                }

                ws.send(
                    json.dumps(payload)
                )

                subscribed += 1

                print(
                    Fore.CYAN +
                    f"[WS] Subscribed: "
                    f"{channel}"
                )

                # anti spam rate limit
                time.sleep(0.05)

            except Exception:
                pass

        print(
            Fore.GREEN +
            f"[WS] Total subscribed: "
            f"{subscribed}"
        )

    except Exception as e:

        print(
            Fore.RED +
            f"[WS SUB ERROR] {e}"
        )


# =========================================
# ERROR
# =========================================

def on_error(ws, error):

    print(
        Fore.RED +
        f"[WS ERROR] {error}"
    )


# =========================================
# CLOSE
# =========================================

def on_close(
    ws,
    close_status_code,
    close_msg
):

    print(
        Fore.YELLOW +
        "[WS CLOSED] reconnecting..."
    )

    time.sleep(5)

    start_websocket()


# =========================================
# START
# =========================================

def start_websocket():

    ws = websocket.WebSocketApp(

        WS_URL,

        on_open=on_open,

        on_message=on_message,

        on_error=on_error,

        on_close=on_close
    )

    ws.run_forever()
