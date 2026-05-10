# =========================================
# data_fetcher.py
# SMART MARKET FETCHER FINAL
# =========================================

import ccxt
import pandas as pd
import time

from colorama import Fore


# =========================================
# BLACKLIST PAIRS
# =========================================

BLACKLIST = {

    "ab_idr",
    "att_idr",
    "cht_idr",
    "cbg_idr"
}


# =========================================
# TICKER CACHE
# =========================================

TICKER_CACHE = {}

LAST_TICKER_UPDATE = 0


# =========================================
# SINGLE TICKER CACHE
# =========================================

SINGLE_TICKER_CACHE = {}

LAST_SINGLE_UPDATE = {}


# =========================================
# CANDLE CACHE
# =========================================

CANDLE_CACHE = {}

LAST_CANDLE_UPDATE = {}


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
# GET TICKERS CACHE
# =========================================

def get_cached_tickers():

    global TICKER_CACHE
    global LAST_TICKER_UPDATE

    now = time.time()

    # cache 10 detik
    if (
        now - LAST_TICKER_UPDATE < 10
        and
        TICKER_CACHE
    ):

        return TICKER_CACHE

    for _ in range(3):

        try:

            TICKER_CACHE = (
                exchange.fetch_tickers()
            )

            LAST_TICKER_UPDATE = now

            return TICKER_CACHE

        except Exception as e:

            print(
                Fore.RED +
                f"[CACHE ERROR] {e}"
            )

            time.sleep(1)

    return TICKER_CACHE


# =========================================
# GET ALL PAIRS
# =========================================

def get_all_pairs(

    min_volume_idr=5_000_000,

    max_spread=5,

    top=30

):

    try:

        tickers = get_cached_tickers()

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

                bid = float(
                    ticker.get("bid") or 0
                )

                ask = float(
                    ticker.get("ask") or 0
                )

                last = float(
                    ticker.get("last") or 0
                )

                # skip micin
                if last < 1:
                    continue

                # volume IDR/USDT
                quote_volume = float(
                    ticker.get("quoteVolume") or 0
                )

                # invalid market
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

                # volatility %
                change = abs(

                    float(

                        ticker.get("percentage")

                        or

                        ticker.get("change")

                        or 0
                    )
                )

                # filter volume
                if quote_volume < min_volume_idr:
                    continue

                # filter spread
                if spread > max_spread:
                    continue

                # skip market kurang aktif
                # if change < 0.3:
                   # continue

                # format pair
                formatted = (
                    s.replace("/", "_")
                )

                # blacklist
                if formatted in BLACKLIST:
                    continue

                # =================================
                # SCORING
                # =================================

                score = 0

                # volume score
                if quote_volume > 5_000_000_000:
                    score += 3

                elif quote_volume > 1_000_000_000:
                    score += 2

                # spread score
                if spread < 0.3:
                    score += 2

                elif spread < 0.8:
                    score += 1

                # volatility score
                if change > 3:
                    score += 2

                elif change > 1:
                    score += 1

                valid_pairs.append({

                    "pair": formatted,

                    "volume": quote_volume,

                    "spread": spread,

                    "price": last,

                    "change": change,

                    "score": score
                })

            except:
                continue

        # =====================================
        # SORT BY SCORE + VOLUME
        # =====================================

        valid_pairs = sorted(

            valid_pairs,

            key=lambda x: (
                x["score"],
                x["volume"]
            ),

            reverse=True
        )

        # LIMIT
        valid_pairs = valid_pairs[:top]

        pairs = [

            x["pair"]

            for x in valid_pairs
        ]

        # =====================================
        # DEBUG OUTPUT
        # =====================================

        print(
            Fore.GREEN +
            f"\n[✓] Smart pairs loaded: "
            f"{len(pairs)}"
        )

        print(
            Fore.CYAN +
            "\n=== TOP PAIRS ==="
        )

        for p in valid_pairs[:10]:

            print(

                Fore.YELLOW +

                f"{p['pair']} | "

                f"Score={p['score']} | "

                f"Spread={round(p['spread'], 2)}% | "

                f"Change={round(p['change'], 2)}% | "

                f"Vol={round(p['volume'])}"
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

        now = time.time()

        cache_key = f"{pair}_{timeframe}"

        # =====================================
        # CACHE TIMER
        # =====================================

        cache_time = 15

        if timeframe == "1h":
            cache_time = 60

        elif timeframe == "15m":
            cache_time = 30

        elif timeframe == "5m":
            cache_time = 15

        # =====================================
        # RETURN CACHE
        # =====================================

        if cache_key in LAST_CANDLE_UPDATE:

            if (

                now
                -
                LAST_CANDLE_UPDATE[cache_key]

                < cache_time

            ):

                return CANDLE_CACHE.get(
                    cache_key
                )

        # =====================================
        # FETCH
        # =====================================

        symbol = (
            pair
            .replace("_", "/")
            .upper()
        )

        time.sleep(0.1)

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

        # =====================================
        # SAVE CACHE
        # =====================================

        CANDLE_CACHE[cache_key] = df

        LAST_CANDLE_UPDATE[cache_key] = now

        return df

    except Exception:

        return None


# =========================================
# GET TICKER
# =========================================

def get_ticker(pair):

    try:

        now = time.time()

        # cache 5 detik
        if pair in LAST_SINGLE_UPDATE:

            if (
                now - LAST_SINGLE_UPDATE[pair]
                < 5
            ):

                return SINGLE_TICKER_CACHE.get(
                    pair
                )

        symbol = (

            pair

            .replace("_", "/")

            .upper()
        )

        ticker = exchange.fetch_ticker(
            symbol
        )

        data = {

            "last": ticker.get("last"),

            "bid": ticker.get("bid"),

            "ask": ticker.get("ask"),

            "volume": ticker.get("quoteVolume")
        }

        SINGLE_TICKER_CACHE[pair] = data

        LAST_SINGLE_UPDATE[pair] = now

        return data

    except Exception:

        return SINGLE_TICKER_CACHE.get(pair)


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

    if df is not None:

        print(df.tail())

    else:

        print("No candle data")

    print("\n=== TICKER ===\n")

    print(
        get_ticker("btc_idr")
    )
