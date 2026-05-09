# websocket_stream.py

import websocket
import json
import time
from colorama import Fore

from realtime_store import add_trade
from detectors import whale_pump_detector
from data_fetcher import get_all_pairs
from config import Config


# =========================================
# CONFIG
# =========================================

WS_URL = "wss://ws3.indodax.com/ws/"

STATIC_TOKEN = Config.INDODAX_WS_TOKEN

_callback = None


# =========================================
# ON OPEN
# =========================================

def on_open(ws):

    print(
        Fore.GREEN +
        "[WS] Connected to Indodax"
    )

    # AUTH
    auth_msg = {

        "params": {
            "token": STATIC_TOKEN
        },

        "id": 1
    }

    ws.send(
        json.dumps(auth_msg)
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

        data = json.loads(message)

        # DEBUG
        # print(data)

        # =====================================
        # AUTH SUCCESS
        # =====================================

        if (
            "result" in data
            and
            isinstance(data["result"], dict)
        ):

            result = data["result"]

            if "client" in result:

                print(
                    Fore.GREEN +
                    f"[WS] Authenticated! "
                    f"Client ID: "
                    f"{result['client']}"
                )

                subscribe_all_pairs(ws)

                return

        # =====================================
        # TRADE STREAM
        # =====================================

        if (
            "result" in data
            and
            isinstance(data["result"], dict)
        ):

            result = data["result"]

            if (
                "channel" in result
                and
                "data" in result
            ):

                channel = result["channel"]

                # market:trade-activity-btcidr
                if channel.startswith(
                    "market:trade-activity-"
                ):

                    raw_data = (
                        result["data"]
                        .get("data", [])
                    )

                    for trade in raw_data:

                        try:

                            # FORMAT:
                            # [pair, timestamp, seq, side, price, idr_volume, coin_volume]

                            pair_raw = trade[0]

                            price = float(
                                trade[4]
                            )

                            # pakai coin volume
                            coin_volume = float(
                                trade[6]
                            )

                            # btcidr -> btc_idr
                            pair = pair_raw

                            if (
                                "_"
                                not in pair
                            ):

                                if pair.endswith(
                                    "idr"
                                ):

                                    pair = (
                                        pair[:-3]
                                        + "_idr"
                                    )

                                elif pair.endswith(
                                    "usdt"
                                ):

                                    pair = (
                                        pair[:-4]
                                        + "_usdt"
                                    )

                            # =================================
                            # REALTIME STORE
                            # =================================

                            add_trade(
                                pair,
                                price,
                                coin_volume
                            )

                            # =================================
                            # WHALE DETECTOR
                            # =================================

                            whale_pump_detector.on_trade(
                                pair,
                                price,
                                coin_volume
                            )

                            # =================================
                            # CALLBACK
                            # =================================

                            if _callback:

                                _callback(
                                    pair,
                                    price,
                                    coin_volume
                                )

                        except Exception:
                            pass

    except Exception as e:

        print(
            Fore.RED +
            f"[WS PARSE ERROR] {e}"
        )


# =========================================
# SUBSCRIBE ALL PAIRS
# =========================================

def subscribe_all_pairs(ws):

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

            subscribe_msg = {

                "method": 1,

                "params": {
                    "channel": channel
                },

                "id": int(time.time())
            }

            ws.send(
                json.dumps(
                    subscribe_msg
                )
            )

            subscribed += 1

            print(
                Fore.CYAN +
                f"[WS] Subscribed: "
                f"{channel}"
            )

            # anti spam rate limit
            time.sleep(0.03)

        except Exception:
            pass

    print(
        Fore.GREEN +
        f"[WS] Total subscribed: "
        f"{subscribed}"
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
        "Reconnect in 5s..."
    )

    time.sleep(5)

    start_websocket(
        _callback
    )


# =========================================
# START
# =========================================

def start_websocket(
    callback=None
):

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
