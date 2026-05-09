# trading_engine.py

import time
from colorama import Fore
from config import Config
from utils import (
    place_order,
    get_balance,
    send_telegram,
    log_to_csv
)


class TradingEngine:

    def __init__(self):

        self.open_positions = {}

    def open_position(
        self,
        pair: str,
        side: str,
        price: float,
        amount: float
    ):

        try:

            # =========================
            # VALIDASI
            # =========================

            if not Config.REAL_TRADING:

                print(
                    Fore.YELLOW +
                    f"[DRY RUN] {side.upper()} {pair}"
                )

                return

            # anti duplicate
            if pair in self.open_positions:

                print(
                    Fore.YELLOW +
                    f"[SKIP] {pair} sudah ada posisi"
                )

                return

            # max posisi
            if len(self.open_positions) >= Config.MAX_OPEN_POSITIONS:

                print(
                    Fore.YELLOW +
                    "[LIMIT] Max open positions reached"
                )

                return

            # minimum order
            if amount < Config.MINIMUM_ORDER_IDR:

                print(
                    Fore.YELLOW +
                    "[SKIP] Order terlalu kecil"
                )

                return

            # =========================
            # CHECK BALANCE
            # =========================

            balance = get_balance()

            if not balance:

                print(
                    Fore.RED +
                    "[ERROR] Tidak bisa cek balance"
                )

                return

            idr_balance = float(
                balance.get("idr", 0)
            )

            # BUY check saldo
            if side.lower() == "buy":

                if idr_balance < amount:

                    print(
                        Fore.RED +
                        "[ERROR] Saldo IDR tidak cukup"
                    )

                    return

            # =========================
            # PLACE ORDER
            # =========================

            print(
                Fore.CYAN +
                f"[ORDER] {side.upper()} "
                f"{pair} "
                f"Price={price} "
                f"Amount={amount}"
            )

            result = place_order(
                pair=pair,
                side=side,
                price=price,
                amount=amount
            )

            if not result:

                print(
                    Fore.RED +
                    "[ERROR] Order gagal"
                )

                return

            # =========================
            # CHECK RESPONSE
            # =========================

            if result.get("success") == 1:

                order_data = result.get("return", {})

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

                print(
                    Fore.GREEN +
                    f"[SUCCESS] OPEN {pair}"
                )

                # Telegram
                send_telegram(
                    f"🔥 OPEN POSITION\n"
                    f"Pair: {pair}\n"
                    f"Side: {side}\n"
                    f"Price: {price}\n"
                    f"Amount: {amount}"
                )

                # CSV log
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

    def close_position(
        self,
        pair: str,
        price: float
    ):

        try:

            if pair not in self.open_positions:
                return

            pos = self.open_positions[pair]

            side = pos["side"]

            amount = pos["amount"]

            # close logic
            close_side = (
                "sell"
                if side == "buy"
                else "buy"
            )

            result = place_order(
                pair=pair,
                side=close_side,
                price=price,
                amount=amount
            )

            if result and result.get("success") == 1:

                pnl = (
                    (
                        price - pos["entry"]
                    ) / pos["entry"]
                ) * 100

                print(
                    Fore.GREEN +
                    f"[CLOSE] {pair} "
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

    def update_trailing_stop(
        self,
        pair: str,
        current_price: float
    ):

        try:

            if pair not in self.open_positions:
                return

            pos = self.open_positions[pair]

            entry = pos["entry"]

            # update highest
            if current_price > pos["highest"]:

                pos["highest"] = current_price

            highest = pos["highest"]

            # trailing %
            trailing_percent = 2

            stop_price = highest * (
                1 - trailing_percent / 100
            )

            # kena trailing stop
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

    def check_scalping_signal(
        self,
        signals: dict
    ):

        try:

            tf_1m = signals.get("1m")

            tf_5m = signals.get("5m")

            if not tf_1m or not tf_5m:
                return None

            if (
                tf_1m["signal"] in
                ["BUY", "STRONG BUY"]

                and

                tf_5m["signal"] in
                ["BUY", "STRONG BUY"]
            ):

                return {
                    "action": "buy",
                    "entry": tf_1m["price"]
                }

            if (
                tf_1m["signal"] in
                ["SELL", "STRONG SELL"]

                and

                tf_5m["signal"] in
                ["SELL", "STRONG SELL"]
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


# singleton
trading_engine = TradingEngine()
