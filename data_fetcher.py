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

    timeframe_map = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "1h": "60",
        "4h": "240",
        "1d": "1440"
    }

    tf = timeframe_map.get(timeframe, "60")

    symbol = pair.lower()

    url = (
        f"https://indodax.com/tradingview/history?"
        f"symbol={symbol}"
        f"&resolution={tf}"
        f"&from=0"
        f"&to={int(time.time())}"
    )

    try:

        resp = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        print(f"[DEBUG] {url}")
        print(f"[DEBUG] STATUS {resp.status_code}")
        print(f"[DEBUG] RESP {resp.text[:200]}")

        data = resp.json()

        if not data:
            return None

        if "s" in data and data["s"] == "no_data":
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
            print(resp.text[:500])
        except:
            pass

        return None
