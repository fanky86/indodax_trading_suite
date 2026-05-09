# websocket_stream.py

import websocket
import json
import time

from colorama import Fore

from config import Config
from detectors import whale_pump_detector

try:
    from realtime_store import add_trade
except:

    def add_trade(
        pair,
        price,
        amount
    ):
        pass


WS_URL = (
    "wss://ws3.indodax.com/ws/"
)

_callback = None


VALID_WS_PAIRS = [

    "btcidr",
    "ethidr",
    "solidr",
    "xrpidr",
    "dogeidr",

    "adaidr",
    "pepeidr",
    "shibidr",
    "avaxidr",
    "trxidr",

    "btcusdt",
    "ethusdt"
]


def parse_multi_json(
    data_str
):

    results = []

    decoder = (
        json.JSONDecoder()
    )

    idx = 0

    data_str = (
        data_str.strip()
    )

    while idx < len(data_str):

        try:

            obj, end = (
                decoder.raw_decode(
                    data_str,
                    idx
                )
            )

            results.append(obj)

            idx = end

            while (

                idx < len(data_str)

                and

                data_str[idx]
                in
                ' \n\r\t'
            ):

                idx += 1

        except:
            break

    return results


def on_open(ws):

    print(

        Fore.GREEN +

        "[WS] Connected"
    )

    auth_payload = {

        "params": {

            "token":

            Config
            .INDODAX_WS_TOKEN
        },

        "id": 1
    }

    ws.send(

        json.dumps(
            auth_payload
        )
    )

    print(

        Fore.CYAN +

        "[WS] Auth sent"
    )


def on_message(
    ws,
    message
):

    global _callback

    try:

        if isinstance(
            message,
            bytes
        ):

            message = (
                message.decode(
                    "utf-8"
                )
            )

        parsed = (
            parse_multi_json(
                message
            )
        )

        for data in parsed:

            # =====================
            # AUTH
            # =====================

            if (

                isinstance(
                    data,
                    dict
                )

                and

                "result" in data
            ):

                result = (
                    data["result"]
                )

                if isinstance(
                    result,
                    dict
                ):

                    client_id = (

                        result.get(
                            "client"
                        )

                        or

                        result.get(
                            "client_id"
                        )
                    )

                    if client_id:

                        print(

                            Fore.GREEN +

                            "[WS] Auth OK"
                        )

                        subscribe_all_pairs(
                            ws
                        )

                        continue

            # =====================
            # TRADE STREAM
            # =====================

            if (

                isinstance(
                    data,
                    dict
                )

                and

                "result" in data
            ):

                result = (
                    data["result"]
                )

                if (

                    isinstance(
                        result,
                        dict
                    )

                    and

                    "channel"
                    in
                    result
                ):

                    channel = (
                        result.get(
                            "channel",
                            ""
                        )
                    )

                    if (

                        "trade-activity"
                        in
                        channel
                    ):

                        trades = (

                            result
                            .get(
                                "data",
                                {}
                            )
                            .get(
                                "data",
                                []
                            )
                        )

                        for trade in trades:

                            try:

                                raw_pair = (
                                    trade[0]
                                )

                                price = (
                                    float(
                                        trade[4]
                                    )
                                )

                                amount = (
                                    float(
                                        trade[6]
                                    )
                                )

                                pair = (
                                    raw_pair
                                )

                                if pair.endswith(
                                    "idr"
                                ):

                                    pair = (

                                        pair[:-3]

                                        +

                                        "_idr"
                                    )

                                elif pair.endswith(
                                    "usdt"
                                ):

                                    pair = (

                                        pair[:-4]

                                        +

                                        "_usdt"
                                    )

                                add_trade(

                                    pair,

                                    price,

                                    amount
                                )

                                whale_pump_detector.on_trade(

                                    pair,

                                    price,

                                    amount
                                )

                                if _callback:

                                    _callback(

                                        pair,

                                        price,

                                        amount
                                    )

                            except:
                                pass

    except Exception as e:

        print(

            Fore.RED +

            f"[WS ERROR] {e}"
        )


def subscribe_all_pairs(
    ws
):

    print(

        Fore.YELLOW +

        "[WS] Subscribing..."
    )

    subscribed = 0

    for symbol in VALID_WS_PAIRS:

        try:

            channel = (

                "market:"
                "trade-activity-"
                f"{symbol}"
            )

            payload = {

                "method": 1,

                "params": {

                    "channel":
                    channel
                },

                "id": int(

                    time.time()
                    * 1000
                )
            }

            ws.send(

                json.dumps(
                    payload
                )
            )

            subscribed += 1

            print(

                Fore.CYAN +

                "[WS] "

                f"{subscribed}/"

                f"{len(VALID_WS_PAIRS)} "

                f"{symbol}"
            )

            time.sleep(0.2)

        except Exception as e:

            print(

                Fore.RED +

                f"[SUB ERROR] {e}"
            )

    print(

        Fore.GREEN +

        "[WS] Total "

        f"{subscribed}"
    )


def on_error(
    ws,
    error
):

    print(

        Fore.RED +

        f"[WS ERROR] {error}"
    )


def on_close(

    ws,

    close_status_code,

    close_msg
):

    print(

        Fore.YELLOW +

        "[WS CLOSED]"
    )

    time.sleep(5)

    start_websocket(
        _callback
    )


def start_websocket(
    callback=None
):

    global _callback

    _callback = callback

    while True:

        try:

            ws = (
                websocket
                .WebSocketApp(

                    WS_URL,

                    on_open=on_open,

                    on_message=on_message,

                    on_error=on_error,

                    on_close=on_close
                )
            )

            ws.run_forever(

                ping_interval=20,

                ping_timeout=10
            )

        except Exception as e:

            print(

                Fore.RED +

                f"[WS CRASH] {e}"
            )

        print(

            Fore.YELLOW +

            "[WS] reconnect..."
        )

        time.sleep(5)
