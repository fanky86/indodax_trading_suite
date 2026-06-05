# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ---------- INDODAX API (isi dengan milik Anda) ----------
    INDODAX_API_KEY = os.getenv("INDODAX_API_KEY")
    INDODAX_SECRET_KEY = os.getenv("INDODAX_SECRET_KEY")
    INDODAX_BASE_URL = "https://indodax.com"

    # config.py (tambahkan di bagian CONFIG)
    INDODAX_WS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5NDY2MTg0MTV9.UR1lBM6Eqh0yWz-PVirw1uPCxe60FdchR8eNVdsskeo"   # Ganti dengan token asli

    # ---------- TRADING SETTINGS ----------
    MAX_OPEN_POSITIONS = 3
    MINIMUM_ORDER_IDR = 10000
    MAX_POSITION_SIZE_IDR = 10000
    REAL_TRADING = True
    ALLOW_REAL_ORDER = True          # Set True jika API key sudah benar & siap trading
    SCALPING_MODE = True
    TRAILING_STOP_PCT = 1.5           # Trailing stop 1.5%
    TAKE_PROFIT_PCT = 3
    COOLDOWN_SECONDS = 300
    
    # ---------- DETECTOR THRESHOLD ----------
    WHALE_THRESHOLD_USDT = 5000       # Transaksi > 5k USDT
    PUMP_THRESHOLD_PCT = 5.0          # Kenaikan >5% dalam 1 menit
    
    # ---------- SCANNER ----------
    TIMEFRAMES = ["1m", "5m", "15m", "1h"]
    REFRESH_INTERVAL = 60             # detik antar scan
    
    # ---------- TELEGRAM ----------
    TELEGRAM_ENABLED = True
    TELEGRAM_BOT_TOKEN = "8640703551:AAFZgiOQ0C0ct7Tuhegx9zIlegqVJIbtVWc"
    TELEGRAM_CHAT_ID = "7211121595"
    
    # ---------- WEB DASHBOARD ----------
    DASHBOARD_PORT = 5001
    ENABLE_DASHBOARD = True
    
    # ---------- LSTM ----------
    USE_LSTM = True                   # Akan fallback jika tensorflow tidak ada
    LSTM_MODEL_PATH = "lstm_model.keras"
    LSTM_LOOKBACK = 60
