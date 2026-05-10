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

def get_all_pairs(

    min_volume_idr=50_000_000,
    max_spread=1.5,
    top=30

):

    try:

        tickers = exchange.fetch_tickers()

        valid_pairs = []

        for symbol, ticker in tickers.items():

            s = symbol.lower()

            # hanya IDR / USDT
            if (
                "/idr" not in s
                and
                "/usdt" not in s
            ):
                continue

            try:

                bid = float(ticker.get("bid") or 0)
                ask = float(ticker.get("ask") or 0)
                last = float(ticker.get("last") or 0)

                # volume quote
                quote_volume = float(
                    ticker.get("quoteVolume") or 0
                )

                # skip invalid
                if (
                    bid <= 0
                    or ask <= 0
                    or last <= 0
                ):
                    continue

                # spread %
                spread = (
                    (ask - bid) / bid
                ) * 100

                # filter volume
                if quote_volume < min_volume_idr:
                    continue

                # filter spread
                if spread > max_spread:
                    continue

                formatted = (
                    s.replace("/", "_")
                )

                valid_pairs.append({

                    "pair": formatted,

                    "volume": quote_volume,

                    "spread": spread,

                    "price": last
                })

            except:
                continue

        # SORT BY VOLUME
        valid_pairs = sorted(

            valid_pairs,

            key=lambda x: x["volume"],

            reverse=True
        )

        # LIMIT
        valid_pairs = valid_pairs[:top]

        pairs = [
            x["pair"]
            for x in valid_pairs
        ]

        print(
            Fore.GREEN +
            f"[✓] Smart pairs loaded: "
            f"{len(pairs)}"
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

            "volume": ticker.get("quoteVolume")
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
