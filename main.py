import threading
import time
from colorama import Fore, init
from config import Config
from data_fetcher import get_all_pairs
from scanner import scan_pair
from trading_engine import trading_engine
from detectors import detect_futures_pairs, whale_pump_detector
from websocket_stream import start_websocket
from web_dashboard import run_dashboard, update_dashboard
from utils import send_telegram

init(autoreset=True)

def scanning_loop():
    print(Fore.GREEN + "[Main] Scanner loop started")
    while True:
        try:
            pairs = get_all_pairs()
            futures = detect_futures_pairs()
            if futures:
                print(Fore.YELLOW + f"[Futures Detected] {futures}")
            
            for pair in pairs[:30]:
                try:
                    signals = scan_pair(pair)
                    if not signals:
                        continue
                    
                    # Cetak hasil sinyal ke console
                    main_signal = signals.get('1h', {})
                    if main_signal.get('signal') != 'HOLD':
                        print(Fore.CYAN + f"\n🔥 {pair} | {main_signal.get('signal')} | Score: {main_signal.get('score')} | Price: {main_signal.get('price')} | RSI: {main_signal.get('rsi')}")
                        for tf, data in signals.items():
                            if data.get('signal') != 'HOLD' and tf != '1h':
                                print(f"   {tf}: {data['signal']} (score {data['score']})")
                    
                    # Ambil sinyal dari timeframe 1h sebagai utama
                    price = main_signal.get('price', 0)
                    signal = main_signal.get('signal', 'HOLD')
                    rsi = main_signal.get('rsi', 0)
                    
                    # Update dashboard
                    update_dashboard(pair, price, signal, rsi)
                    
                    # Auto trading (sama seperti sebelumnya)
                    if signal in ['STRONG BUY', 'BUY'] and pair not in trading_engine.open_positions:
                        amount = Config.MAX_POSITION_SIZE_USDT / price if price > 0 else 0
                        if amount > 0:
                            trading_engine.open_position(pair, 'buy', price, amount)
                    
                    scalp_action = trading_engine.check_scalping_signal(signals)
                    if scalp_action and pair not in trading_engine.open_positions:
                        amount = Config.MAX_POSITION_SIZE_USDT / scalp_action['entry']
                        trading_engine.open_position(pair, scalp_action['action'], scalp_action['entry'], amount)
                    
                    # Update trailing stop
                    for pos_pair in list(trading_engine.open_positions.keys()):
                        from data_fetcher import get_candles
                        df = get_candles(pos_pair, '1m')
                        if df is not None:
                            current = df['close'].iloc[-1]
                            trading_engine.update_trailing_stop(pos_pair, current)
                    
                except Exception as e:
                    print(Fore.RED + f"Error scanning {pair}: {e}")
            
            print(Fore.BLUE + f"[Scan] Selesai, next dalam {Config.REFRESH_INTERVAL} detik")
            time.sleep(Config.REFRESH_INTERVAL)
        except Exception as e:
            print(Fore.RED + f"Loop error: {e}")
            time.sleep(5)

def websocket_callback(pair, price, volume):
    """Meneruskan data dari WebSocket ke dashboard & detector"""
    update_dashboard(pair, price, 'LIVE', 0)

def start_websocket_thread():
    try:
        start_websocket(callback=websocket_callback)
    except Exception as e:
        print(Fore.RED + f"WebSocket thread gagal: {e}")

if __name__ == '__main__':
    print(Fore.CYAN + """
    ╔══════════════════════════════════════════════════╗
    ║     INDODAX FULL AI TRADING SUITE (REAL)         ║
    ║  LSTM | Auto Order | Whale/Pump | Web Dashboard  ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Start scanner loop di thread terpisah
    scanner_thread = threading.Thread(target=scanning_loop, daemon=True)
    scanner_thread.start()
    
    # Start WebSocket realtime (jika gagal, tidak menghentikan program)
    try:
        # WebSocket sementara dinonaktifkan
        # ws_thread = threading.Thread(target=start_websocket_thread, daemon=True)
        # ws_thread.start()
        print(Fore.YELLOW + "[INFO] WebSocket dinonaktifkan, gunakan scanner periodik saja")
    except Exception as e:
        print(Fore.RED + f"Tidak bisa start WebSocket: {e}")
    
    # Start web dashboard
    if Config.ENABLE_DASHBOARD:
        print(Fore.GREEN + f"Dashboard running at http://localhost:{Config.DASHBOARD_PORT}")
        run_dashboard()
    else:
        while True:
            time.sleep(1)
