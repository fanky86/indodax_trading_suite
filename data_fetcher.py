# data_fetcher.py

import requests
import pandas as pd
import time
from typing import Optional


def get_all_pairs():
    """Mengambil semua pasangan IDR & USDT dari Indodax"""
    try:
        resp = requests.get(
            "https://indodax.com/api/pairs",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        data = resp.json()

        pairs = []

        for item in data:
            ticker = item.get("ticker_id", "")

            if "_idr" in ticker or "_usdt" in ticker:
                pairs.append(ticker)

        return pairs

    except Exception as e:
        print(f"Error get_all_pairs: {e}")
        return []


def get_candles(pair: str, timeframe: str = "1h") -> Optional[pd.DataFrame]:
    """
    timeframe: 1m,5m,15m,1h,4h,1d
    """

    resolution_map = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "1h": "60",
        "4h": "240",
        "1d": "1D"
    }

    interval = resolution_map.get(timeframe, "60")

    # btc_idr -> BTCIDR
    symbol = pair.replace("_", "").upper()

    from_timestamp = int(time.time()) - (86400 * 30)
    to_timestamp = int(time.time())

    url = (
        f"https://indodax.com/tradingview/history_v2"
        f"?symbol={symbol}"
        f"&tf={interval}"
        f"&from={from_timestamp}"
        f"&to={to_timestamp}"
    )

    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        )

        if resp.status_code != 200:
            print(f"HTTP Error {resp.status_code} for {pair}")
            return None

        data = resp.json()

        if "c" not in data or not data["c"]:
            print(f"No candle data for {pair}")
            return None

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(data["t"], unit="s"),
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "close": data["c"],
            "volume": data["v"]
        })

        numeric_cols = ["open", "high", "low", "close", "volume"]

        df[numeric_cols] = df[numeric_cols].astype(float)

        return df

    except Exception as e:
        print(f"Error fetching {pair} {timeframe}: {e}")

        try:
            print(resp.text[:300])
        except:
            pass

        return None
