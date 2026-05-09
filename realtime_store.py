# realtime_store.py

import pandas as pd
from collections import defaultdict
from datetime import datetime


# realtime candles
market_data = defaultdict(list)


def add_trade(
    pair,
    price,
    volume
):

    now = datetime.now()

    candle = {

        "timestamp": now,

        "open": price,

        "high": price,

        "low": price,

        "close": price,

        "volume": volume
    }

    market_data[pair].append(candle)

    # limit memory
    if len(market_data[pair]) > 500:

        market_data[pair] = (
            market_data[pair][-500:]
        )


def get_realtime_df(pair):

    if pair not in market_data:
        return None

    data = market_data[pair]

    if len(data) < 30:
        return None

    df = pd.DataFrame(data)

    return df
