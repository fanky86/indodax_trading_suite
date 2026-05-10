# =========================================
# trading_engine.py
# SMART AUTO TRADING ENGINE FINAL SAFE
# =========================================

import time
import threading

from colorama import Fore

from config import Config

from utils import (

    place_order,

    get_balance,

    cancel_order,

    send_telegram,

    log_to_csv
)


class TradingEngine:

    def __init__(self):

        self.open_positions = {}

        self.cooldowns = {}

        self.daily_loss = 0

        # DEADMAN SWITCH
        self.last_heartbeat = time.time()

    # =====================================
    # HEARTBEAT
    # =====================================

    def heartbeat(self):

        self.last_heartbeat = time.time()

    # =====================================
    # DEADMAN SWITCH MONITOR
    # =====================================

    def deadman_switch_monitor(self):

        while True:

            try:

                elapsed = (
                    time.time()
                    -
                    self.last_heartbeat
                )

                # bot freeze
                if elapsed > 120:

                    print(
                        Fore.RED +
                        "[DEADMAN SWITCH] "
                        "Bot timeout detected!"
                    )

                    send_telegram(

                        "⚠️ DEADMAN SWITCH ACTIVE\n"

                        "Bot timeout detected.\n"

                        "Cancelling all open orders..."
                    )

                    # cancel semua posisi
                    for pair in list(

                        self.open_positions.keys()
                    ):

                        pos = (
                            self.open_positions[pair]
                        )

                        try:

                            order_id = pos.get(
                                "order_id"
                            )

                            side = pos.get(
                                "side"
                            )

                            if order_id:

                                result = cancel_order(

                                    pair,

                                    order_id,

                                    side
                                )

                                print(
                                    Fore.YELLOW +
                                    f"[CANCELLED] {pair}"
                                )

                                print(result)

                        except Exception as e:

                            print(
                                Fore.RED +
                                f"Cancel error: {e}"
                            )

                    self.last_heartbeat = (
                        time.time()
                    )

                time.sleep(10)

            except Exception as e:

                print(
                    Fore.RED +
                    f"Deadman monitor error: {e}"
                )

                time.sleep(5)

    # =====================================
    # OPEN POSITION
    # =====================================

    def open_position(

        self,

        pair: str,

        side: str,

        price: float,

        amount: float
    ):

        try:

            self.heartbeat()

            # =================================
            # MAX DAILY LOSS
            # =================================

            if self.daily_loss <= -5:

                print(
                    Fore.RED +
                    "[STOP] Daily loss limit reached"
                )

                return

            # =================================
            # DRY RUN MODE
            # =================================

            if not Config.REAL_TRADING:

                print(

                    Fore.YELLOW +

                    f"[DRY RUN] "

                    f"{side.upper()} "

                    f"{pair}"
                )

                return

            # =================================
            # COOLDOWN
            # =================================

            now = time.time()

            if pair in self.cooldowns:

                elapsed = (
                    now -
                    self.cooldowns[pair]
                )

                # cooldown 15 menit
                if elapsed < 900:

                    print(
                        Fore.YELLOW +
                        f"[COOLDOWN] {pair}"
                    )

                    return

            # =================================
            # ANTI DUPLICATE
            # =================================

            if pair in self.open_positions:

                print(
                    Fore.YELLOW +
                    f"[SKIP] {pair} "
                    "already open"
                )

                return

            # =================================
            # MAX POSITIONS
            # =================================

            if (

                len(self.open_positions)

                >=

                Config.MAX_OPEN_POSITIONS
            ):

                print(
                    Fore.YELLOW +
                    "[LIMIT] "
                    "Max positions reached"
                )

                return

            # =================================
            # MINIMUM ORDER
            # =================================

            if amount < Config.MINIMUM_ORDER_IDR:

                print(
                    Fore.YELLOW +
                    "[SKIP] "
                    "Order too small"
                )

                return

            # =================================
            # CHECK BALANCE
            # =================================

            balance = get_balance()

            if not balance:

                print(
                    Fore.RED +
                    "[ERROR] "
                    "Cannot get balance"
                )

                return

            idr_balance = float(
                balance.get("idr", 0)
            )

            if side.lower() == "buy":

                if idr_balance < amount:

                    print(
                        Fore.RED +
                        "[ERROR] "
                        "Insufficient IDR balance"
                    )

                    return

            # =================================
            # ORDER LOG
            # =================================

            print(

                Fore.CYAN +

                f"[ORDER] "

                f"{side.upper()} "

                f"{pair} "

                f"Price={price} "

                f"Amount={amount}"
            )

            # =================================
            # PLACE ORDER
            # =================================

            result = place_order(

                pair,

                side,

                price,

                amount
            )

            if not result:

                print(
                    Fore.RED +
                    "[ERROR] Order failed"
                )

                return

            print(result)

            # =================================
            # SUCCESS
            # =================================

            if result.get("success") == 1:

                order_data = result.get(
                    "return",
                    {}
                )

                order_id = order_data.get(

                    "order_id",

                    str(time.time())
                )

                self.open_positions[pair] = {

                    "side": side,

                    "entry": price,

                    "amount": amount,

                    "order_id": order_id,

                    "timestamp": time.time(),

                    "highest": price,

                    "lowest": price
                }

                self.cooldowns[pair] = (
                    time.time()
                )

                print(

                    Fore.GREEN +

                    f"[SUCCESS] "

                    f"OPEN {pair}"
                )

                send_telegram(

                    f"🔥 OPEN POSITION\n"

                    f"Pair: {pair}\n"

                    f"Side: {side}\n"

                    f"Price: {price}\n"

                    f"Amount: {amount}"
                )

                log_to_csv(

                    "trade_log.csv",

                    {

                        "time": time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),

                        "pair": pair,

                        "side": side,

                        "price": price,

                        "amount": amount,

                        "status": "OPEN"
                    }
                )

            else:

                print(
                    Fore.RED +
                    f"[FAILED] {result}"
                )

        except Exception as e:

            print(
                Fore.RED +
                f"Open position error: {e}"
            )

    # =====================================
    # CLOSE POSITION
    # =====================================

    def close_position(

        self,

        pair: str,

        price: float
    ):

        try:

            self.heartbeat()

            if pair not in self.open_positions:
                return

            pos = self.open_positions[pair]

            side = pos["side"]

            amount = pos["amount"]

            close_side = (

                "sell"

                if side == "buy"

                else "buy"
            )

            result = place_order(

                pair,

                close_side,

                price,

                amount
            )

            if (

                result

                and

                result.get("success") == 1
            ):

                pnl = (

                    (
                        price
                        -
                        pos["entry"]
                    )

                    /

                    pos["entry"]

                ) * 100

                # update daily loss
                self.daily_loss += pnl

                print(

                    Fore.GREEN +

                    f"[CLOSE] "

                    f"{pair} "

                    f"PNL={pnl:.2f}%"
                )

                send_telegram(

                    f"✅ CLOSE POSITION\n"

                    f"{pair}\n"

                    f"PNL={pnl:.2f}%"
                )

                log_to_csv(

                    "trade_log.csv",

                    {

                        "time": time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),

                        "pair": pair,

                        "side": close_side,

                        "price": price,

                        "amount": amount,

                        "pnl": pnl,

                        "status": "CLOSE"
                    }
                )

                del self.open_positions[pair]

        except Exception as e:

            print(
                Fore.RED +
                f"Close position error: {e}"
            )

    # =====================================
    # TRAILING STOP
    # =====================================

    def update_trailing_stop(

        self,

        pair: str,

        current_price: float
    ):

        try:

            if pair not in self.open_positions:
                return

            pos = self.open_positions[pair]

            # update highest
            if current_price > pos["highest"]:

                pos["highest"] = current_price

            highest = pos["highest"]

            # trailing stop
            stop_price = highest * (

                1 -
                Config.TRAILING_STOP_PCT / 100
            )

            if current_price <= stop_price:

                print(
                    Fore.YELLOW +
                    f"[TRAILING STOP] {pair}"
                )

                self.close_position(
                    pair,
                    current_price
                )

        except Exception as e:

            print(
                Fore.RED +
                f"Trailing stop error: {e}"
            )

    # =====================================
    # TAKE PROFIT / STOP LOSS
    # =====================================

    def check_risk_management(

        self,

        pair: str,

        current_price: float
    ):

        try:

            if pair not in self.open_positions:
                return

            pos = self.open_positions[pair]

            entry = pos["entry"]

            pnl = (

                (
                    current_price
                    -
                    entry
                )

                /

                entry

            ) * 100

            # TAKE PROFIT
            if pnl >= Config.TAKE_PROFIT_PCT:

                print(
                    Fore.GREEN +
                    f"[TAKE PROFIT] {pair}"
                )

                self.close_position(
                    pair,
                    current_price
                )

            # STOP LOSS
            elif pnl <= -Config.STOP_LOSS_PCT:

                print(
                    Fore.RED +
                    f"[STOP LOSS] {pair}"
                )

                self.close_position(
                    pair,
                    current_price
                )

        except Exception as e:

            print(
                Fore.RED +
                f"Risk management error: {e}"
            )

    # =====================================
    # SCALPING SIGNAL
    # =====================================

    def check_scalping_signal(
        self,
        signals: dict
    ):

        try:

            tf_1m = signals.get("1m")

            tf_5m = signals.get("5m")

            tf_15m = signals.get("15m")

            if (
                not tf_1m
                or
                not tf_5m
                or
                not tf_15m
            ):

                return None

            # =================================
            # BTC MARKET WEAK
            # =================================

            if (

                tf_15m["trend"]

                !=

                "BULLISH"
            ):

                return None

            # =================================
            # STRONG BUY
            # =================================

            if (

                tf_1m["signal"]

                ==

                "STRONG BUY"

                and

                tf_5m["signal"]

                ==

                "STRONG BUY"

                and

                tf_15m["signal"]

                in [

                    "BUY",

                    "STRONG BUY"
                ]

                and

                tf_15m["confidence"]

                >= 70

                and

                tf_15m["rsi"] < 75
            ):

                return {

                    "action": "buy",

                    "entry": tf_1m["price"]
                }

            # =================================
            # STRONG SELL
            # =================================

            if (

                tf_1m["signal"]

                ==

                "STRONG SELL"

                and

                tf_5m["signal"]

                ==

                "STRONG SELL"

                and

                tf_15m["signal"]

                in [

                    "SELL",

                    "STRONG SELL"
                ]

                and

                tf_15m["confidence"]

                >= 70
            ):

                return {

                    "action": "sell",

                    "entry": tf_1m["price"]
                }

            return None

        except Exception as e:

            print(

                Fore.RED +

                f"Scalping signal error: {e}"
            )

            return None


# =========================================
# SINGLETON
# =========================================

trading_engine = TradingEngine()
