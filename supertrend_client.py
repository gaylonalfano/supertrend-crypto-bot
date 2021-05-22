"""
Gonna see if I can turn this into a Supertrend Client that can be
accessed and used within a FastAPI endpoint function
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
import typing as T
import pandas as pd
import ccxt

# Show max rows in DF
# pd.set_option("display.max_rows", None)


class Supertrend:
    exchange = ccxt.binance()

    def __init__(self, symbols, timeframe, limit):
        self.symbols: T.List[str] = symbols
        self.timeframe: str = timeframe
        self.limit: int = limit

    # Q: Do I set defaults to Class instance variables? ie symbol = self.symbols[0]?
    def fetch_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> pd.DataFrame:
        """Fetch symbol data on schedule from binance and return dataframe"""
        # 1. Grab our data using class variable
        # open high low close data
        bars = self.exchange.fetch_ohlcv(
            symbol=symbol, timeframe=timeframe, limit=limit
        )

        # Create a DF but only with completed timestamps (ie exclude last row)
        data = pd.DataFrame(
            bars[:-1], columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Make timestamp easier to read
        data.timestamp = pd.to_datetime(
            data.timestamp, unit="ms"
        )  # 2021-05-11 23:00:00

        # print(data.head())
        return data

    # 2. Perform some calculations to get the upper_band and lower_band
    def compute_true_range(self, data: pd.DataFrame):
        # NOTE We could use ta library but we're computing manually

        # 2.1 Compute True Range: max((h-l)|(abs(h-prev_close))|(abs(l-prev_close)))
        # Add a 'previous_close' column that shifts 'close' down one for side-by-side
        data["previous_close"] = data.close.shift(1)
        data["high-low"] = data.high - data.low
        data["high-previous_close"] = abs(data.high - data.previous_close)
        data["low-previous_close"] = abs(data.low - data.previous_close)

        # Compute the True Range by finding the max() of the three columns
        # NOTE Using .max(axis=1) to compute ACROSS columns
        true_value = data[
            ["high-low", "high-previous_close", "low-previous_close"]
        ].max(axis=1)

        # Store in new 'tr' column
        # data["tr"] = true_value

        # Return the computed true_value
        return true_value

    def compute_average_true_range(self, data: pd.DataFrame, period: int):
        """Compute ATR on dataframe argument"""
        # Compute the corresponding true_value for this data
        data["tr"] = self.compute_true_range(data)

        # Now use tr to compute atr
        average_true_range = data["tr"].rolling(period).mean()

        # Store in new 'atr' column
        # data["atr"] = average_true_range

        # Return the computed atr
        return average_true_range

    def compute_basic_upper_band(self, data: pd.DataFrame, multiplier: int = 3):
        """Compute basic upper band = ((high + low) / 2) + (multiplier * atr)"""
        basic_upper_band = ((data.high + data.low) / 2) + (multiplier * data.atr)
        # data["basic_upper_band"] = basic_upper_band
        return basic_upper_band

    def compute_basic_lower_band(self, data: pd.DataFrame, multiplier: int = 3):
        """Compute basic lower band = ((high + low) / 2) - (multiplier * atr)"""
        basic_lower_band = ((data.high + data.low) / 2) - (multiplier * data.atr)
        # data["basic_lower_band"] = basic_lower_band
        return basic_lower_band

    def compute_trend_and_final_bands(self, data: pd.DataFrame):
        """
        FINAL UPPER BAND CALCULATION:
        if((Current basic upper band < Previous final upper band)
        and (Previous close < Previous final lower band))
        then (Current basic lower band)
        else (Previous final lower band)

        FINAL LOWER BAND CALCULATION:
        if((Current basic lower band > Previous final lower band)
        and (Previous close < Previous final lower band))
        then (Current basic lower band)
        else (Previous final lower band)
        """
        # ==== Compute in_uptrend and final bands - LARRY's SOLUTION
        # Initialize the in_uptrend column to True
        # NOTE Must initialize these columns of it errors
        data["in_uptrend"] = True
        # Initialize final bands columns as well
        # Q: But this is no different the BASIC bands...
        # A: It's OK since we update as we iterate
        data["final_upper_band"] = data.basic_upper_band
        data["final_lower_band"] = data.basic_lower_band

        # Loop through dataframe (similar to my compute_final_lower_band() attempt)
        # TODO May be a more efficient method with .apply(), etc.
        for current_index in range(1, len(data.index)):
            previous_index = current_index - 1

            if (
                data.loc[current_index, "close"]
                > data.loc[previous_index, "final_upper_band"]
            ):
                # UP trend
                data.loc[current_index, "in_uptrend"] = True
            elif (
                data.loc[current_index, "close"]
                < data.loc[previous_index, "final_lower_band"]
            ):
                # DOWN trend
                data.loc[current_index, "in_uptrend"] = False
            else:
                # It's somewhere in the middle so the trend remains
                data.loc[current_index, "in_uptrend"] = data.loc[
                    previous_index, "in_uptrend"
                ]

                # Next, need to update the FINAL bands
                # Compute the current final LOWER band
                # In an UP trend (i.e., in_uptrend = True)
                if (
                    data.loc[current_index, "in_uptrend"]
                    and data.loc[current_index, "basic_lower_band"]
                    < data.loc[previous_index, "final_lower_band"]
                ):
                    # FLATTEN the current final lower band (keep same as previous)
                    data.loc[current_index, "final_lower_band"] = data.loc[
                        previous_index, "final_lower_band"
                    ]

                # Compute the current final UPPER band
                # In a DOWN trend (i.e., in_uptrend = False)
                if (
                    not data.loc[current_index, "in_uptrend"]
                    and data.loc[current_index, "basic_upper_band"]
                    > data.loc[previous_index, "final_upper_band"]
                ):
                    # FLATTEN the current final upper band (keep same as previous)
                    data.loc[current_index, "final_upper_band"] = data.loc[
                        previous_index, "final_upper_band"
                    ]

    def find_buy_sell_timestamps(self, data: pd.DataFrame):
        """Appends new column to dataframe specifying buy or sell timestamps"""
        # Q: Initialize columns?
        # A: Doesn't seem to work...
        # data["buy"] = None
        # data["sell"] = None
        # Q: How to compare previous row value with current row value?
        # A: Compare previous row value with current row using eq() and shift()
        # NOTE I need NOT equal to so it returns True so using ne() instead
        # NOTE Larry used indices to check:
        # last_row_index = len(df.index) - 1 ; previous_row_index = last_row_index - 1
        # Then: if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]...
        data["match"] = data.in_uptrend.ne(data.in_uptrend.shift())

        # FIXME Want to get the dates and the trade recommendation when trend swap
        def is_buy_or_sell(row):
            if row["match"] is True and row["in_uptrend"] is True:
                # Buy
                # data["buy"] = True
                # data["sell"] = False
                return "Buy"
            elif row["match"] is True and row["in_uptrend"] is False:
                # Sell
                # data["buy"] = False
                # data["sell"] = True
                return "Sell"
            # else:
            #     data["buy"] = None
            #     data["sell"] = None

        data["trade"] = data.apply(is_buy_or_sell, axis=1)
        # Or, data.apply(lambda r: is_buy(r), axis=1)

        # Now let's extract any/all buys and sells
        buy_mask = data["trade"] == "Buy"
        sell_mask = data["trade"] == "Sell"
        # NOTE Don't have to do any fancy loops just use the masks!
        # FIXME Need to remove the 0 index for buys
        buys = data[buy_mask].iloc[1:, :]
        sells = data[sell_mask]
        # Timestamps only
        # NOTE Return a Series with just .loc[] or raw value with .loc[].iloc[0]
        # buys = data.loc[buy_mask, "timestamp"]
        # sells = data.loc[sell_mask, "timestamp"]
        # buys = [data.loc[buy_mask, "timestamp"] for i in data.in]

    def supertrend(
        self,
        data: pd.DataFrame,
        period: int = 7,
        multiplier: int = 3,
    ):
        """Compute the supertrend"""
        # Q: Where to update dataframe? Here directly or within helpers?
        # Option 1: Update here directly
        # 1. Compute our atr so we can then compute the upper/lower bands
        data["atr"] = self.compute_average_true_range(data, period)

        # 2. Compute our basic bands and add to dataframe
        data["basic_upper_band"] = self.compute_basic_upper_band(data, multiplier)
        data["basic_lower_band"] = self.compute_basic_lower_band(data, multiplier)

        # 3. ==== FIXME Compute in_uptrend and final bands -- MY ATTEMPT
        # Q: Do I update dataframe within helper or within this function?
        # Option 1: Update dataframe directly here
        # data["in_uptrend"] = compute_final_lower_band(data)
        # Option 2: Update dataframe within helper function
        # compute_final_lower_band(data)
        # Option 3: Dunno... TODO
        # Q: Could consider list comprehension?
        # result = [f(x, y) for x, y in zip(df['col1'], df['col2'])]

        # ==== Compute in_uptrend and final bands - LARRY's SOLUTION
        # NOTE This helper adds cols in_uptrend and final bands columns
        self.compute_trend_and_final_bands(data)

        # 4 Grab all Buy/Sell timestamps (i.e., when in_uptrend toggles)
        # NOTE Compare previous row value with current row using eq() and shift()
        self.find_buy_sell_timestamps(data)

        # 5. Return the updated dataframe
        return data
