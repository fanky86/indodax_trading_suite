# trading_engine.py
from config import Config
from utils import place_order, send_telegram, log_to_csv
from colorama import Fore
import time

class TradingEngine:
    def __init__(self):
        self.open_positions = {}

    def open_position(self, pair: str, side: str, entry_price: float, amount: float):
        if not Config.ALLOW_REAL_ORDER:
            print(Fore.CYAN + f"[SIM] OPEN {side.upper()} {pair} {amount:.6f} @ {entry_price}")
            self._add_position(pair, side, entry_price, amount)
            return
        resp = place_order(pair, side, entry_price, amount)
        if resp and resp.get('success'):
            self._add_position(pair, side, entry_price, amount)
            send_telegram(f"✅ OPEN {side.upper()} {pair} @ {entry_price} | amount {amount:.6f}")
        else:
            print(Fore.RED + f"Order failed: {resp}")

    def _add_position(self, pair, side, entry, amount):
        self.open_positions[pair] = {
            'side': side,
            'entry_price': entry,
            'amount': amount,
            'highest': entry,
            'trailing_stop_pct': Config.TRAILING_STOP_PCT,
            'open_time': time.time()
        }

    def close_position(self, pair: str, current_price: float, reason: str = ""):
        if pair not in self.open_positions:
            return
        pos = self.open_positions.pop(pair)
        side = 'sell' if pos['side'] == 'buy' else 'buy'
        if Config.ALLOW_REAL_ORDER:
            place_order(pair, side, current_price, pos['amount'])
            send_telegram(f"🔒 CLOSE {pair} @ {current_price} ({reason})")
        else:
            print(Fore.YELLOW + f"[SIM] CLOSE {pair} @ {current_price} ({reason})")
        log_to_csv({
            'pair': pair,
            'side': pos['side'],
            'entry': pos['entry_price'],
            'exit': current_price,
            'pnl_pct': (current_price - pos['entry_price']) / pos['entry_price'] * 100,
            'reason': reason,
            'time': time.time()
        })

    def update_trailing_stop(self, pair: str, current_price: float):
        if pair not in self.open_positions:
            return
        pos = self.open_positions[pair]
        if current_price > pos['highest']:
            pos['highest'] = current_price
        stop_price = pos['highest'] * (1 - pos['trailing_stop_pct'] / 100)
        if current_price <= stop_price:
            self.close_position(pair, current_price, "TRAILING STOP")

    def check_scalping_signal(self, signals_dict):
        if not Config.SCALPING_MODE:
            return None
        tf1m = signals_dict.get('1m', {})
        if tf1m.get('signal') in ['STRONG BUY', 'BUY']:
            entry = tf1m['price']
            tp = entry * 1.01
            sl = entry * 0.995
            return {'action': 'buy', 'entry': entry, 'tp': tp, 'sl': sl}
        if tf1m.get('signal') in ['STRONG SELL', 'SELL']:
            entry = tf1m['price']
            tp = entry * 0.99
            sl = entry * 1.005
            return {'action': 'sell', 'entry': entry, 'tp': tp, 'sl': sl}
        return None

trading_engine = TradingEngine()
