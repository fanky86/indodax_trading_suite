# config.py
import os

class Config:
    # ---------- INDODAX API (isi dengan milik Anda) ----------
    INDODAX_API_KEY = os.getenv("INDODAX_API_KEY", "PIUNZQLD-YQJWUP2Y-ONXQKXAZ-RGO05AIX-XBRQNS8N")
    INDODAX_SECRET_KEY = os.getenv("INDODAX_SECRET_KEY", "82822911b3c91daebc2486abab12936576e42320764c7ac4f37289bf50ecd71f78137dab1cc76fc3")
    INDODAX_BASE_URL = "https://indodax.com/api"
    
    # ---------- TRADING SETTINGS ----------
    ALLOW_REAL_ORDER = False          # Set True jika API key sudah benar & siap trading
    MAX_POSITION_SIZE_USDT = 20.0     # Maksimal order per posisi (dalam USDT)
    SCALPING_MODE = True
    TRAILING_STOP_PCT = 1.5           # Trailing stop 1.5%
    
    # ---------- DETECTOR THRESHOLD ----------
    WHALE_THRESHOLD_USDT = 5000       # Transaksi > 5k USDT
    PUMP_THRESHOLD_PCT = 5.0          # Kenaikan >5% dalam 1 menit
    
    # ---------- SCANNER ----------
    TIMEFRAMES = ["1m", "5m", "15m", "1h"]
    REFRESH_INTERVAL = 60             # detik antar scan
    
    # ---------- TELEGRAM ----------
    TELEGRAM_ENABLED = False
    TELEGRAM_BOT_TOKEN = "ISI_BOT_TOKEN"
    TELEGRAM_CHAT_ID = "ISI_CHAT_ID"
    
    # ---------- WEB DASHBOARD ----------
    DASHBOARD_PORT = 5000
    ENABLE_DASHBOARD = True
    
    # ---------- LSTM ----------
    USE_LSTM = True                   # Akan fallback jika tensorflow tidak ada
    LSTM_MODEL_PATH = "lstm_model.h5"
    LSTM_LOOKBACK = 60
