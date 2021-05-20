"""
NOTES:
- Buy or Sell indicators whenever the closing price is above/below
the corresponding final band.
- Formulas from https://www.tradingfuel.com/supertrend-indicator-formula-and-calculation/
- A hard design decision was whether to update the dataframe within each helper
function, OR only return the values and ONLY WITHIN the supertrend() function
do we then update the dataframe. So far going with this but it's hard to reference
columns that do not exist in the original dataframe...
- Larry actually overwrites the basic bands columns with the final bands values.
This threw me off a bit as my in_uptrend calc was never accurate as I was comparing
to the basic bands instead of final bands.
- BUG? On timestamps where it swaps in_uptrend T/F, that current final band value doesn't
update. Have to wait to NEXT timestamp to see the final bands update.
Check out 9/5/20 timestamp: https://youtu.be/21tLM3XrU9I?list=PLvzuUVysUFOv5XEPHeqefgyHZcDfLxH-W&t=1133
The CFUB is 515.52 but should be PFUB value of 511.2350 (I think)
- I could consider looping over a list of cryptos and running supertrend() on each
"""
import time
import datetime
import schedule
import streamlit as st
import pandas as pd
import ccxt
import config

# Show max rows in DF
# pd.set_option("display.max_rows", None)

# FIXME Get the Kraken connection working.
st.write("API_KEY: ", config.KRAKEN_API_KEY)
st.write("API_KEY_DESC: ", config.KRAKEN_API_KEY_DESCRIPTION)
st.write("PRIVATE_KEY: ", config.KRAKEN_PRIVATE_KEY)
st.write("API_SECRET: ", config.KRAKEN_API_SECRET)

# exchange = ccxt.kraken(
#     {"apiKey": config.KRAKEN_API_KEY, "secret": config.KRAKEN_PRIVATE_KEY}
# )

# # TODO Test out kraken exchange connection
# # print(exchange.fetch_balance())
# st.write(exchange.fetch_balance())

# def fetch_data(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
#     """Fetch symbol data on schedule from kraken and return dataframe"""
#     # 1. Grab our data
#     exchange = ccxt.kraken(
#         {"apiKey": config.KRAKEN_API_KEY, "secret": config.KRAKEN_PRIVATE_KEY}
#     )

#     # TODO Test out kraken exchange connection
#     print(exchange.fetch_balance())

#     # open high low close data
#     bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

#     # Create a DF but only with completed timestamps (ie exclude last row)
#     data = pd.DataFrame(
#         bars[:-1], columns=["timestamp", "open", "high", "low", "close", "volume"]
#     )

#     # Make timestamp easier to read
#     data.timestamp = pd.to_datetime(data.timestamp, unit="ms")  # 2021-05-11 23:00:00

#     # print(data.head())
#     return data


# # 2. Perform some calculations to get the upper_band and lower_band
# def compute_true_range(data: pd.DataFrame):
#     # NOTE We could use ta library but we're computing manually

#     # 2.1 Compute True Range: max((h-l)|(abs(h-prev_close))|(abs(l-prev_close)))
#     # Add a 'previous_close' column that shifts 'close' down one for side-by-side
#     data["previous_close"] = data.close.shift(1)
#     data["high-low"] = data.high - data.low
#     data["high-previous_close"] = abs(data.high - data.previous_close)
#     data["low-previous_close"] = abs(data.low - data.previous_close)

#     # Compute the True Range by finding the max() of the three columns
#     # NOTE Using .max(axis=1) to compute ACROSS columns
#     true_value = data[["high-low", "high-previous_close", "low-previous_close"]].max(
#         axis=1
#     )

#     # Store in new 'tr' column
#     # data["tr"] = true_value

#     # Return the computed true_value
#     return true_value


# def compute_average_true_range(data: pd.DataFrame, period: int):
#     """Compute ATR on dataframe argument"""
#     # Compute the corresponding true_value for this data
#     data["tr"] = compute_true_range(data)

#     # Now use tr to compute atr
#     average_true_range = data["tr"].rolling(period).mean()

#     # Store in new 'atr' column
#     # data["atr"] = average_true_range

#     # Return the computed atr
#     return average_true_range


# def compute_basic_upper_band(data: pd.DataFrame, multiplier: int = 3):
#     """Compute basic upper band = ((high + low) / 2) + (multiplier * atr)"""
#     basic_upper_band = ((data.high + data.low) / 2) + (multiplier * data.atr)
#     # data["basic_upper_band"] = basic_upper_band
#     return basic_upper_band


# def compute_basic_lower_band(data: pd.DataFrame, multiplier: int = 3):
#     """Compute basic lower band = ((high + low) / 2) - (multiplier * atr)"""
#     basic_lower_band = ((data.high + data.low) / 2) - (multiplier * data.atr)
#     # data["basic_lower_band"] = basic_lower_band
#     return basic_lower_band


# # def compute_in_uptrend(
# #     data: pd.DataFrame, current_index: int = 1, previous_index: int = 0
# # ):
# #     # FIXME
# #     # Initialize "in_uptrend" column value
# #     # data.loc[current_index, "in_uptrend"] = True
# #     # st.write(
# #     #     data.loc[current_index, "close"] > data.loc[previous_index, "basic_upper_band"]
# #     # )
# #     if data.loc[current_index, "close"] > data.loc[previous_index, "basic_upper_band"]:
# #         # data.loc[current_index, "in_uptrend"] = True
# #         return True
# #     elif (
# #         data.loc[current_index, "close"] < data.loc[previous_index, "basic_lower_band"]
# #     ):
# #         # data.loc[current_index, "in_uptrend"] = False
# #         return False
# #     else:
# #         data.loc[current_index, "in_uptrend"] = data.loc[previous_index, "in_uptrend"]

# # Trying a different approach
# # def first_number_greater_than_second_number(a, b):
# #     return True if a > b else False

# # data["in_uptrend"] = data.apply(
# #     first_number_greater_than_second_number(
# #         data.loc[current_index, "close"],
# #         data.loc[previous_index, "basic_lower_band"],
# #     ),
# #     axis=0,
# # )

# # st.subheader("compute_in_uptrend")
# # st.dataframe(data)

# # return data


# def compute_final_upper_band(data: pd.DataFrame):
#     """
#     FINAL UPPER BAND CALCULATION:
#     if((Current basic upper band < Previous final upper band)
#     and (Previous close < Previous final lower band))
#     then (Current basic lower band)
#     else (Previous final lower band)
#     """
#     # Q: How to track current/previous state?
#     # Use .apply()?
#     # current_index = 1
#     # previous_index = current_index - 1

#     # current_basic_upper_band = df['ba']
#     pass


# def compute_final_lower_band(data: pd.DataFrame):
#     """
#     FINAL LOWER BAND CALCULATION:
#     if((Current basic lower band > Previous final lower band)
#     and (Previous close < Previous final lower band))
#     then (Current basic lower band)
#     else (Previous final lower band)
#     """
#     # Initiliaze the in_uptrend value-BROKE
#     # data["in_uptrend"] = True
#     # data["in_uptrend"] = compute_in_uptrend(data)
#     # data["previous_basic_upper_band"] = "hi"
#     data["previous_basic_upper_band"] = data.basic_upper_band.shift(1)
#     data["previous_basic_lower_band"] = data.basic_lower_band.shift(1)
#     data["cc_gt_pbub"] = data.close > data.previous_basic_upper_band
#     data["cc_lt_pblb"] = data.close < data.previous_basic_lower_band
#     # if data.cc_gt_pbub is True:
#     #     data["in_uptrend"] = True
#     # elif data.cc_lt_pblb is True:
#     #     data["in_uptrend"] = False

#     # Need to loop through the dataframe and track current/previous
#     # NOTE Get number of rows using len(df.index) or data.shape[0]
#     # for current_index in range(1, len(data.index)):
#     #     # print(current)
#     #     # st.write(current)
#     #     # 1. Track the previous_index as well for comparisons
#     #     previous_index = current_index - 1

#     #     # 2. Compute whether in_uptrend
#     #     # WITH compute_in_uptrend() helper
#     #     # data.loc[current_index, "in_uptrend"] = compute_in_uptrend(
#     #     #     data, current_index, previous_index
#     #     # )
#     #     # WITHOUT compute_in_uptrend() helper
#     #     # Q: How to reference the previous in_uptrend value without the
#     #     # existing in_uptrend column to reference?
#     #     # Q: Should I use .apply() or list comprehension?
#     #     # E.g. result = [f(x, y) for x, y in zip(df['col1'], df['col2'])]
#     #     # if (
#     #     #     data.loc[current_index, "close"]
#     #     #     > data.loc[previous_index, "basic_upper_band"]
#     #     # ):
#     #     #     # Q: Do I update dataframe here or within main supertrend()?
#     #     #     # data.loc[current_index, "in_uptrend"] = True
#     #     #     return True
#     #     # elif (
#     #     #     data.loc[current_index, "close"]
#     #     #     < data.loc[previous_index, "basic_lower_band"]
#     #     # ):
#     #     #     # data.loc[current_index, "in_uptrend"] = False
#     #     #     return False
#     #     # else:
#     #     #     # Q: How to reference the previous in_uptrend value without the
#     #     #     # existing in_uptrend column to reference?
#     #     #     data.loc[current_index, "in_uptrend"] = data.loc[
#     #     #         previous_index, "in_uptrend"
#     #     #     ]
#     #     #     return (
#     #     #         data.loc[previous_index, "close"]
#     #     #         > data.loc[previous_index - 1, "basic_upper_band"]
#     #     #     )
#     #     # === Trying .apply() with lambda
#     #     # NOTE I have to initialize the column up to for this to work
#     #     # data["previous_basic_upper_band"][current_index] = data.loc[
#     #     #     previous_index, "basic_upper_band"
#     #     # ]
#     #     # NOTE OR, I don't initialize column up top but instead call shift()
#     #     data["previous_basic_upper_band"] = data.basic_upper_band.shift(1)
#     #     data["previous_basic_lower_band"] = data.basic_lower_band.shift(1)
#     #     data["cc_gt_pbub"] = data.close > data.previous_basic_upper_band
#     #     data["cc_lt_pblb"] = data.close < data.previous_basic_lower_band

#     #     # data["cc_lt_pblb"] = (
#     #     #     data.loc[current_index, "close"]
#     #     #     < data.loc[previous_index, "basic_lower_band"]
#     #     # )

#     #     # 3. Store/update the in_uptrend in dataframe
#     #     # NOTE Must use .loc[] to set value or Error
#     #     # data.loc[current_index, "in_uptrend"] = in_uptrend

#     #     # 4. Compute the final_lower_band and store
#     #     # Check the trend
#     #     # if in_uptrend and data.loc[previous_index, "close"] < data.loc[previous_index, "basic_lower_band"]:
#     #     #     data.loc[current_index, "final_lower_band"] = data.loc[current_index, "basic_lower_band"]
#     #     # else:
#     #     #     data.loc[current_index, "final_lower_band"] = data.loc[previous_index, "final_lower_band"]


# def compute_trend_and_final_bands(data: pd.DataFrame):
#     """
#     FINAL UPPER BAND CALCULATION:
#     if((Current basic upper band < Previous final upper band)
#     and (Previous close < Previous final lower band))
#     then (Current basic lower band)
#     else (Previous final lower band)

#     FINAL LOWER BAND CALCULATION:
#     if((Current basic lower band > Previous final lower band)
#     and (Previous close < Previous final lower band))
#     then (Current basic lower band)
#     else (Previous final lower band)
#     """
#     # ==== Compute in_uptrend and final bands - LARRY's SOLUTION
#     # Initialize the in_uptrend column to True
#     # NOTE Must initialize these columns of it errors
#     data["in_uptrend"] = True
#     # Initialize final bands columns as well
#     # Q: But this is no different the BASIC bands...
#     # A: It's OK since we update as we iterate
#     data["final_upper_band"] = data.basic_upper_band
#     data["final_lower_band"] = data.basic_lower_band

#     # Loop through dataframe (similar to my compute_final_lower_band() attempt)
#     # TODO May be a more efficient method with .apply(), etc.
#     for current_index in range(1, len(data.index)):
#         previous_index = current_index - 1

#         if (
#             data.loc[current_index, "close"]
#             > data.loc[previous_index, "final_upper_band"]
#         ):
#             # UP trend
#             data.loc[current_index, "in_uptrend"] = True
#         elif (
#             data.loc[current_index, "close"]
#             < data.loc[previous_index, "final_lower_band"]
#         ):
#             # DOWN trend
#             data.loc[current_index, "in_uptrend"] = False
#         else:
#             # It's somewhere in the middle so the trend remains
#             data.loc[current_index, "in_uptrend"] = data.loc[
#                 previous_index, "in_uptrend"
#             ]

#             # Next, need to update the FINAL bands
#             # Compute the current final LOWER band
#             # In an UP trend (i.e., in_uptrend = True)
#             if (
#                 data.loc[current_index, "in_uptrend"]
#                 and data.loc[current_index, "basic_lower_band"]
#                 < data.loc[previous_index, "final_lower_band"]
#             ):
#                 # FLATTEN the current final lower band (keep same as previous)
#                 data.loc[current_index, "final_lower_band"] = data.loc[
#                     previous_index, "final_lower_band"
#                 ]

#             # Compute the current final UPPER band
#             # In a DOWN trend (i.e., in_uptrend = False)
#             if (
#                 not data.loc[current_index, "in_uptrend"]
#                 and data.loc[current_index, "basic_upper_band"]
#                 > data.loc[previous_index, "final_upper_band"]
#             ):
#                 # FLATTEN the current final upper band (keep same as previous)
#                 data.loc[current_index, "final_upper_band"] = data.loc[
#                     previous_index, "final_upper_band"
#                 ]


# def find_buy_sell_timestamps(data: pd.DataFrame, show_buy_sell_timestamps: bool = True):
#     """Appends new column to dataframe specifying buy or sell timestamps"""
#     # Q: Initialize columns?
#     # A: Doesn't seem to work...
#     # data["buy"] = None
#     # data["sell"] = None
#     # Q: How to compare previous row value with current row value?
#     # A: Compare previous row value with current row using eq() and shift()
#     # NOTE I need NOT equal to so it returns True so using ne() instead
#     # NOTE Larry used indices to check:
#     # last_row_index = len(df.index) - 1 ; previous_row_index = last_row_index - 1
#     # Then: if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]...
#     data["match"] = data.in_uptrend.ne(data.in_uptrend.shift())

#     # FIXME Want to get the dates and the trade recommendation when trend swap
#     def is_buy_or_sell(row):
#         if row["match"] is True and row["in_uptrend"] is True:
#             # Buy
#             # data["buy"] = True
#             # data["sell"] = False
#             return "Buy"
#         elif row["match"] is True and row["in_uptrend"] is False:
#             # Sell
#             # data["buy"] = False
#             # data["sell"] = True
#             return "Sell"
#         # else:
#         #     data["buy"] = None
#         #     data["sell"] = None

#     data["trade"] = data.apply(is_buy_or_sell, axis=1)
#     # Or, data.apply(lambda r: is_buy(r), axis=1)

#     # Now let's extract any/all buys and sells
#     buy_mask = data["trade"] == "Buy"
#     sell_mask = data["trade"] == "Sell"
#     # NOTE Don't have to do any fancy loops just use the masks!
#     # FIXME Need to remove the 0 index for buys
#     buys = data[buy_mask].iloc[1:, :]
#     sells = data[sell_mask]
#     # Timestamps only
#     # NOTE Return a Series with just .loc[] or raw value with .loc[].iloc[0]
#     # buys = data.loc[buy_mask, "timestamp"]
#     # sells = data.loc[sell_mask, "timestamp"]
#     # buys = [data.loc[buy_mask, "timestamp"] for i in data.in]
#     if show_buy_sell_timestamps is True:
#         st.write("buys: ", buys)
#         st.write("sells: ", sells)


# def supertrend(
#     data: pd.DataFrame,
#     period: int = 7,
#     multiplier: int = 3,
#     show_buy_sell_timestamps: bool = True,
# ):
#     """Compute the supertrend"""
#     # Q: Where to update dataframe? Here directly or within helpers?
#     # Option 1: Update here directly
#     # 1. Compute our atr so we can then compute the upper/lower bands
#     data["atr"] = compute_average_true_range(data, period)

#     # 2. Compute our basic bands and add to dataframe
#     data["basic_upper_band"] = compute_basic_upper_band(data, multiplier)
#     data["basic_lower_band"] = compute_basic_lower_band(data, multiplier)

#     # 3. ==== FIXME Compute in_uptrend and final bands -- MY ATTEMPT
#     # Q: Do I update dataframe within helper or within this function?
#     # Option 1: Update dataframe directly here
#     # data["in_uptrend"] = compute_final_lower_band(data)
#     # Option 2: Update dataframe within helper function
#     # compute_final_lower_band(data)
#     # Option 3: Dunno... TODO
#     # Q: Could consider list comprehension?
#     # result = [f(x, y) for x, y in zip(df['col1'], df['col2'])]

#     # ==== Compute in_uptrend and final bands - LARRY's SOLUTION
#     # NOTE This helper adds cols in_uptrend and final bands columns
#     compute_trend_and_final_bands(data)

#     # 4 Grab all Buy/Sell timestamps (i.e., when in_uptrend toggles)
#     # NOTE Compare previous row value with current row using eq() and shift()
#     find_buy_sell_timestamps(data, show_buy_sell_timestamps)

#     # 5. Return the updated dataframe
#     return data

#     # Option 2: Update dataframe within helpers instead (so just run)
#     # Error - This is all NaN bc not updated the dataframe
#     # compute_average_true_range(data, period)
#     # compute_basic_upper_band(data, multiplier)
#     # compute_basic_lower_band(data, multiplier)

#     # return data


# # 1. Select our data
# st.title("Supertrend")
# available_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
# # NOTE Could provide default symbol but it will autorun. Leaving empty for now.
# # selected_symbols = st.multiselect("Select the symbol(s): ", options=available_symbols, default=None)
# # schedule_frequency = st.slider("Re-run frequency (seconds):", 10, 300, 10)
# # TODO Could consider making checkbox to toggle displaying buy/sell timestamp


# # 2. Fetch data, build dataframes, and store df for each symbol
# # Q: Do I wrap all this into a run_bot function?
# # Q: Do I need to await the fetch_data() and make this async?
# def run_bot(symbols):
#     """Main program function to fetch data and compute supertrend"""
#     for symbol in symbols:
#         st.subheader(f"{symbol} Supertrend")

#         st.write(
#             f"Fetching data for {symbol} at {datetime.datetime.now(datetime.timezone.utc)}"
#         )
#         print(
#             f"Fetching data for {symbol} at {datetime.datetime.now(datetime.timezone.utc)}"
#         )
#         df = fetch_data(symbol=symbol, timeframe="1m", limit=100)

#         # 3. Perform supertrend calculation
#         supertrend_data = supertrend(df)

#         # 4. Display results
#         st.dataframe(supertrend_data)

#         # 5. Execute the buy/sell order via ccxt ('trade' column)
#         # NOTE Need a global in_position bool because we don't want to
#         # order again and again once it flips.
#         # execute_order(supertrend)

#     # 5. Cancel the schedule Job (run once basically)
#     # return schedule.CancelJob


# # 3. Run this main() on a schedule frequency based on st slider
# # print(schedule.jobs)
# # Run once without scheduler
# run_bot(symbols=["ETH/USDT"])


# # FIXME Frequency doesn't seem to be working...
# # schedule.every(schedule_frequency).seconds.do(main, symbols=symbols)
# # schedule.every(30).seconds.do(main)
# # schedule.every().minutes.do(main)
# # schedule.every(10).seconds.do(fetch_data, symbol="ETH/USDT", timeframe="1m", limit=10)
# # schedule.every(20).seconds.do(run_bot, symbols=["ETH/USDT"])  # WORKS!
# # schedule.every(20).seconds.do(run_bot, symbols=symbols)  # Runs ETH 3 times BTC once...
# # WITHOUT using the st.multiselect, so passing symbols manually:
# # schedule.every(20).seconds.do(run_bot, symbols=["BTC/USDT"])

# # Clear all scheduler jobs in case of redundancies
# schedule.clear()

# # while True:
# #     schedule.run_pending()
# #     print("Scheduler jobs: ", schedule.jobs)  # List[Job]
# #     time.sleep(1)
