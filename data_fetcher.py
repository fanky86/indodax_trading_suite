# data_fetcher.py

import ccxt
import pandas as pd
import time
from colorama import Fore


# =========================================
# INIT EXCHANGE
# =========================================

exchange = ccxt.indodax({

    "enableRateLimit": True,

    "rateLimit": 1500,

    "timeout": 20000,

    "options": {
        "defaultType": "spot"
    }
})


# =========================================
# GET ALL PAIRS
# =========================================

def get_all_pairs():

    try:

        markets = exchange.load_markets()

        pairs = []

        for symbol in markets.keys():

            s = symbol.lower()

            if (
                "/idr" in s
                or
                "/usdt" in s
            ):

                # BTC/IDR -> btc_idr
                formatted = (
                    s.replace("/", "_")
                )

                pairs.append(formatted)

        print(
            Fore.GREEN +
            f"[✓] Mendapatkan "
            f"{len(pairs)} pasangan via CCXT"
        )

        return pairs

    except Exception as e:

        print(
            Fore.RED +
            f"[PAIR ERROR] {e}"
        )

        return []


# =========================================
# GET CANDLES
# =========================================

def get_candles(
    pair,
    timeframe='1h',
    limit=200
):

    try:

        # btc_idr -> BTC/IDR
        symbol = (
            pair
            .replace("_", "/")
            .upper()
        )

        ohlcv = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

        if (
            not ohlcv
            or
            len(ohlcv) < 30
        ):

            return None

        df = pd.DataFrame(

            ohlcv,

            columns=[

                'timestamp',

                'open',

                'high',

                'low',

                'close',

                'volume'
            ]
        )

        # timestamp
        df['timestamp'] = pd.to_datetime(
            df['timestamp'],
            unit='ms'
        )

        # numeric
        numeric_cols = [

            'open',

            'high',

            'low',

            'close',

            'volume'
        ]

        df[numeric_cols] = (
            df[numeric_cols]
            .astype(float)
        )

        # cleanup
        df = (
            df
            .dropna()
            .reset_index(drop=True)
        )

        return df

    except Exception:

        return None


# =========================================
# GET TICKER
# =========================================

def get_ticker(pair):

    try:

        symbol = (
            pair
            .replace("_", "/")
            .upper()
        )

        ticker = exchange.fetch_ticker(
            symbol
        )

        return {

            "last": ticker.get("last"),

            "bid": ticker.get("bid"),

            "ask": ticker.get("ask"),

            "volume": ticker.get("baseVolume")
        }

    except Exception:

        return None


# =========================================
# TEST
# =========================================

if __name__ == "__main__":

    print("\n=== LOAD PAIRS ===\n")

    pairs = get_all_pairs()

    print(
        pairs[:10]
    )

    print("\n=== BTC CANDLE ===\n")

    df = get_candles(
        "btc_idr",
        "1h"
    )

    print(df.tail())

    print("\n=== TICKER ===\n")

    print(
        get_ticker("btc_idr")
    )
