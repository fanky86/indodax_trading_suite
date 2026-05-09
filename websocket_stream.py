# websocket_stream.py

import websocket
import json
import time
from colorama import Fore

from config import Config
from detectors import whale_pump_detector
from data_fetcher import get_all_pairs
from realtime_store import add_trade


# =========================================
# CONFIG
# =========================================

WS_URL = "wss://ws3.indodax.com/ws/"

_callback = None


# =========================================
# MULTI JSON PARSER
# =========================================

def parse_multi_json(data_str):

    """
    Parse multiple JSON objects
    from websocket packet
    """

    results = []

    decoder = json.JSONDecoder()

    idx = 0

    data_str = data_str.strip()

    while idx < len(data_str):

        try:

            obj, end = decoder.raw_decode(
                data_str,
                idx
            )

            results.append(obj)

            idx = end

            # skip whitespace
            while (

                idx < len(data_str)

                and

                data_str[idx] in

                ' \n\r\t'
            ):

                idx += 1

        except json.JSONDecodeError as e:

            print(

                Fore.RED +

                f"[WS PARSE ERROR] "

                f"{e}"
            )

            break

    return results


# =========================================
# ON OPEN
# =========================================

def on_open(ws):

    print(

        Fore.GREEN +

        "[WS] Connected to "
        "Indodax WebSocket"
    )

    auth_payload = {

        "id": 1,

        "method": "public/auth",

        "params": {

            "token":
            Config.INDODAX_WS_TOKEN
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

    global _callback

    try:

        # bytes -> string
        if isinstance(message, bytes):

            message = message.decode(
                "utf-8"
            )

        # parse multi json
        parsed_objects = (
            parse_multi_json(message)
        )

        for data in parsed_objects:

            # =================================
            # AUTH SUCCESS
            # =================================

            if (
                isinstance(data, dict)
                and
                data.get("result")
            ):

                result = data["result"]

                if isinstance(result, dict):

                    client_id = (

                        result.get(
                            "client_id"
                        )

                        or

                        result.get(
                            "client"
                        )
                    )

                    if client_id:

                        print(

                            Fore.GREEN +

                            f"[WS] Authenticated! "

                            f"Client ID: "

                            f"{client_id}"
                        )

                        subscribe_all_pairs(ws)

                        continue

            # =================================
            # TRADE DATA
            # =================================

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
                    "trade-activity"
                    in
                    channel

                    and

                    trade_data
                ):

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

                    # =================================
                    # REALTIME CACHE
                    # =================================

                    add_trade(

                        pair,

                        price,

                        amount
                    )

                    # =================================
                    # WHALE DETECTOR
                    # =================================

                    whale_pump_detector.on_trade(

                        pair,

                        price,

                        amount
                    )

                    # =================================
                    # CALLBACK
                    # =================================

                    if _callback:

                        _callback(

                            pair,

                            price,

                            amount
                        )

    except Exception as e:

        print(

            Fore.RED +

            f"[WS GENERAL ERROR] {e}"
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

                symbol = pair.replace(
                    "_",
                    ""
                )

                channel = (
                    f"market:trade-activity-{symbol}"
                )

                payload = {

                    "id": int(
                        time.time() * 1000
                    ),

                    "method":
                    "public/subscribe",

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

                if subscribed % 50 == 0:

                    print(

                        Fore.CYAN +

                        f"[WS] Subscribed "

                        f"{subscribed}/"

                        f"{len(pairs)}"
                    )

                # anti flood
                time.sleep(0.02)

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

        "[WS CLOSED] "

        "reconnecting in 5s..."
    )

    time.sleep(5)

    start_websocket(_callback)


# =========================================
# START
# =========================================

def start_websocket(callback=None):

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
