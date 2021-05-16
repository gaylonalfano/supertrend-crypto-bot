import streamlit as st
import pandas as pd
import ccxt
import ta
import config
from ta.volatility import BollingerBands, AverageTrueRange


# print(dir(ccxt))
# print(ccxt.exchanges)

# PUBLIC information
exchange = ccxt.binanceus()
# exchange = ccxt.coinbasepro()

# PRIVATE Connecting to exchange with private keys
# print(exchange.requiredCredentials)
# exchange.binanceus({"apiKey": config.API_KEY})
# print(config.BINANCE_API_KEY)


markets = exchange.load_markets()
# st.write(markets)

# NOTE Some ticker symbols are different names on different exchanges
# ticker = exchange.fetch_ticker("ZEN/USD")
# print(ticker)

# Candles/Bars (can add limit=)
ohlc = exchange.fetch_ohlcv("ETH/USDT", timeframe="1m", limit=40)
# st.write(ohlc)
# st.table(ohlc)

# Convert to Pandas DataFrame
df = pd.DataFrame(ohlc, columns=["timestamp", "open", "high", "low", "close", "volume"])
# print(df)
# st.dataframe(df)
# st.write(df["close"])
# st.write(type(df["close"]))  # Series
# st.write(df["close"].loc[-20:])
# st.write(df[-20:])
# close_series = df["close"]
close_series = df.loc[:, "close"]
# st.write(close_series.shape[0])

# for candle in ohlc:
#     st.write(candle)

# 2. Create new BollingerBands indicator (moving avg +/- 2 std)
# NOTE This needs a pd.Series of close values
bb_indicator = BollingerBands(close_series)
# Now can use built-in methods of the class
upper_band = bb_indicator.bollinger_hband()
lower_band = bb_indicator.bollinger_lband()
moving_average = bb_indicator.bollinger_mavg()
df["upper_band"] = upper_band
df["lower_band"] = lower_band
df["moving_average"] = moving_average
# st.dataframe(df)


# 3. Create new AverageTrueRange indicator (high, low, close)
# https://youtu.be/s3KIV-WaNuQ?list=PLvzuUVysUFOv5XEPHeqefgyHZcDfLxH-W&t=1061
atr_indicator = AverageTrueRange(df.high, df.low, df.close)

average_true_range = atr_indicator.average_true_range()
df["average_true_range"] = average_true_range
st.dataframe(df)
