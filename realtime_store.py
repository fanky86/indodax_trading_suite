# realtime_store.py

import pandas as pd
from collections import defaultdict
from datetime import datetime


# =========================================
# STORAGE
# =========================================

market_data = defaultdict(list)


# =========================================
# ADD TRADE
# =========================================

def add_trade(
    pair,
    price,
    volume
):

    try:

        candle = {

            "timestamp": datetime.now(),

            "open": float(price),

            "high": float(price),

            "low": float(price),

            "close": float(price),

            "volume": float(volume)
        }

        market_data[pair].append(
            candle
        )

        # limit memory
        if len(market_data[pair]) > 1000:

            market_data[pair] = (
                market_data[pair][-1000:]
            )

    except Exception:
        pass


# =========================================
# GET DATAFRAME
# =========================================

def get_realtime_df(pair):

    try:

        if pair not in market_data:
            return None

        data = market_data[pair]

        if len(data) < 30:
            return None

        df = pd.DataFrame(data)

        return df

    except Exception:

        return None
