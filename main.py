# =========================================
# MAIN.PY (UPGRADE SMART AUTO TRADING)
# =========================================

import threading
import time

from colorama import (
    Fore,
    init
)

from config import Config

from data_fetcher import (
    get_all_pairs,
    get_ticker
)

from scanner import scan_pair

from trading_engine import (
    trading_engine
)

from websocket_stream import (
    start_websocket
)

from web_dashboard import (
    run_dashboard,
    update_dashboard
)

from utils import (
    send_telegram
)

init(autoreset=True)


# =========================================
# WEBSOCKET CALLBACK
# =========================================

def websocket_callback(
    pair,
    price,
    volume
):

    update_dashboard(

        pair,

        price,

        "LIVE",

        0
    )


# =========================================
# WEBSOCKET THREAD
# =========================================

def start_websocket_thread():

    try:

        start_websocket(
            callback=websocket_callback
        )

    except Exception as e:

        print(
            Fore.RED +
            f"[WS THREAD ERROR] {e}"
        )


# =========================================
# MAIN SCANNER LOOP
# =========================================

def scanning_loop():

    print(
        Fore.GREEN +
        "[MAIN] Scanner loop started"
    )

    while True:

        try:

            # =================================
            # LOAD PAIRS
            # =================================

            pairs = get_all_pairs()

            # =================================
            # BTC MARKET FILTER
            # =================================

            btc_signal = scan_pair(
                "btc_idr"
            )

            btc_main = btc_signal.get(
                "1h",
                {}
            )

            btc_market_bearish = (

                btc_main.get(
                    "signal"
                )

                in

                [

                    "SELL",

                    "STRONG SELL"
                ]
            )

            print(

                Fore.YELLOW +

                f"[BTC MARKET] "

                f"{btc_main.get('signal')}"
            )

            # =================================
            # LOOP ALL PAIRS
            # =================================

            for pair in pairs[:200]:

                try:

                    signals = scan_pair(pair)

                    if not signals:

                        continue

                    main_signal = signals.get(
                        "1h",
                        {}
                    )

                    signal = main_signal.get(
                        "signal",
                        "HOLD"
                    )

                    confidence = main_signal.get(
                        "confidence",
                        0
                    )

                    price = main_signal.get(
                        "price",
                        0
                    )

                    rsi = main_signal.get(
                        "rsi",
                        0
                    )

                    # =================================
                    # UPDATE DASHBOARD
                    # =================================

                    update_dashboard(

                        pair,

                        price,

                        signal,

                        rsi
                    )

                    # =================================
                    # DEBUG SIGNAL
                    # =================================

                    if signal != "HOLD":

                        print(

                            Fore.CYAN +

                            f"\n🔥 {pair} | "

                            f"{signal} | "

                            f"Conf={confidence}% | "

                            f"RSI={rsi} | "

                            f"Price={price}"
                        )

                    # =================================
                    # BTC FILTER
                    # =================================

                    if btc_market_bearish:

                        print(

                            Fore.YELLOW +

                            "[FILTER] BTC bearish"
                        )

                        continue

                    # =================================
                    # RSI FILTER
                    # =================================

                    if rsi > 80:

                        print(

                            Fore.YELLOW +

                            "[FILTER] RSI too high"
                        )

                        continue

                    # =================================
                    # VOLATILITY FILTER
                    # =================================

                    support = main_signal.get(
                        "support",
                        price
                    )

                    resistance = main_signal.get(
                        "resistance",
                        price
                    )

                    volatility = (

                        abs(
                            resistance - support
                        )

                        / price
                    ) * 100

                    if volatility < 1:

                        print(

                            Fore.YELLOW +

                            "[FILTER] Low volatility"
                        )

                        continue

                    # =================================
                    # SPREAD FILTER
                    # =================================

                    ticker = get_ticker(pair)

                    if ticker:

                        bid = ticker.get(
                            "bid",
                            0
                        )

                        ask = ticker.get(
                            "ask",
                            0
                        )

                        if bid and ask:

                            spread = (

                                (ask - bid)

                                / ask
                            ) * 100

                            if spread > 1:

                                print(

                                    Fore.YELLOW +

                                    "[FILTER] Spread too high"
                                )

                                continue

                    # =================================
                    # MULTI TF CONFIRMATION
                    # =================================

                    buy_count = 0

                    for tf in [

                        "1m",

                        "5m",

                        "15m"
                    ]:

                        tf_signal = signals.get(
                            tf,
                            {}
                        )

                        if tf_signal.get(
                            "signal"
                        ) in [

                            "BUY",

                            "STRONG BUY"
                        ]:

                            buy_count += 1

                    # =================================
                    # POSITION SIZE
                    # =================================

                    if confidence >= 90:

                        amount = 50000

                    elif confidence >= 80:

                        amount = 25000

                    else:

                        amount = 10000

                    # =================================
                    # AUTO BUY
                    # =================================

                    if (

                        signal == "STRONG BUY"

                        and

                        confidence >= 70

                        and

                        buy_count >= 2

                        and

                        pair not in trading_engine.open_positions
                    ):

                        print(

                            Fore.GREEN +

                            f"[AUTO BUY] {pair}"
                        )

                        trading_engine.open_position(

                            pair=pair,

                            side="buy",

                            price=price,

                            amount=amount
                        )

                        send_telegram(

                            f"🔥 AUTO BUY\n"

                            f"Pair: {pair}\n"

                            f"Price: {price}\n"

                            f"Confidence: {confidence}%"
                        )

                    # =================================
                    # AUTO SELL
                    # =================================

                    if (

                        pair

                        in

                        trading_engine.open_positions
                    ):

                        if signal in [

                            "SELL",

                            "STRONG SELL"
                        ]:

                            print(

                                Fore.RED +

                                f"[AUTO SELL] {pair}"
                            )

                            trading_engine.close_position(

                                pair,

                                price
                            )

                            send_telegram(

                                f"❌ AUTO SELL\n"

                                f"Pair: {pair}\n"

                                f"Price: {price}"
                            )

                    # =================================
                    # TRAILING STOP UPDATE
                    # =================================

                    for pos_pair in list(

                        trading_engine
                        .open_positions
                        .keys()
                    ):

                        ticker = get_ticker(
                            pos_pair
                        )

                        if ticker:

                            current_price = ticker.get(
                                "last",
                                0
                            )

                            trading_engine.update_trailing_stop(

                                pos_pair,

                                current_price
                            )

                except Exception as e:

                    print(

                        Fore.RED +

                        f"[PAIR ERROR] "

                        f"{pair}: {e}"
                    )

            # =================================
            # LOOP DELAY
            # =================================

            print(

                Fore.BLUE +

                f"\n[SCAN DONE] "

                f"Next scan "

                f"{Config.REFRESH_INTERVAL}s"
            )

            time.sleep(
                Config.REFRESH_INTERVAL
            )

        except Exception as e:

            print(

                Fore.RED +

                f"[MAIN LOOP ERROR] {e}"
            )

            time.sleep(5)


# =========================================
# START
# =========================================

if __name__ == "__main__":
    try:
        os.system("git pull")
    except:
        pass

    print(

        Fore.CYAN +

        """
╔══════════════════════════════════════════╗
║      SMART AI TRADING ENGINE            ║
║  FULL REALTIME | AI | AUTO TRADING      ║
╚══════════════════════════════════════════╝
"""
    )

    # scanner
    scanner_thread = threading.Thread(

        target=scanning_loop,

        daemon=True
    )

    scanner_thread.start()

    # websocket
    ws_thread = threading.Thread(

        target=start_websocket_thread,

        daemon=True
    )

    ws_thread.start()

    print(

        Fore.GREEN +

        "[INFO] WebSocket realtime aktif"
    )

    # dashboard
    if Config.ENABLE_DASHBOARD:

        print(

            Fore.GREEN +

            f"Dashboard: "

            f"http://localhost:{Config.DASHBOARD_PORT}"
        )

        run_dashboard()

    else:

        while True:

            time.sleep(1)
