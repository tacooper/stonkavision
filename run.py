#!/usr/bin/python3

import argparse
import pandas
import pandas_datareader.data as pdr
import yfinance
from columns import Column

def main():
    # parse all arguments from command line
    print("")
    args = parse_args()

    # override PDR to get Yahoo Finance data faster
    yfinance.pdr_override()

    # retrieve data for closing price of latest market date
    print("Downloading stock closing price...")
    stock_price = pdr.get_data_yahoo(args.symbol)["Close"][-1]

    # get Yahoo Finance data for stock ticker
    print("Downloading stock data...")
    ticker = yfinance.Ticker(args.symbol)

    # download stock options and build data frame
    data_frame = build_stock_options_data(ticker, args.expiry_dates)

    # remove unnecessary columns from data frame
    data_frame = data_frame.drop(columns = ["contractSize", "contractSymbol", "currency", "lastTradeDate"])

    # add custom columns with calculated values to data frame
    data_frame.insert(3, "distanceOTM", stock_price - data_frame["strike"])
    data_frame.insert(4, "percentOTM", data_frame["distanceOTM"] / stock_price * 100)
    data_frame["value"] = data_frame["openInterest"] * data_frame["lastPrice"] * 100

    # filter options with no value
    data_frame = data_frame[data_frame["value"] > 0]
    data_frame = data_frame[data_frame["lastPrice"] > 0.10]
    data_frame = data_frame[data_frame["inTheMoney"] == False]

    # sort data frame rows by expiry date
    data_frame.sort_values(inplace=True, by=Column.EXPIRY_DATE.value, ascending=True)
    data_frame.reset_index(inplace=True, drop=True)

    # display data frame
    print(data_frame)

def build_stock_options_data(ticker, num_expiry_dates):
    # create data frame for storing put options
    data_frame = pandas.DataFrame()

    # sort expiry dates by closest to current date
    option_dates = sorted(ticker.options)
    total_expiry_dates = len(option_dates)
    if num_expiry_dates == 0:
        num_expiry_dates = total_expiry_dates
    print("Downloading stock options for [{} / {}] expiry dates...".format(num_expiry_dates, total_expiry_dates))

    date_count = 0
    for expiry_date in option_dates:
        # only download stock options for total number of expiry dates
        date_count += 1
        if date_count > num_expiry_dates:
            break
        else:
            print("    Building option data for {} expiry date...".format(expiry_date))

            # get set of call/put options for each expiration date
            option = ticker.option_chain(expiry_date)

            # insert expiration date into first column
            option.puts.insert(0, Column.EXPIRY_DATE.value, expiry_date)

            # add put options to data frame
            data_frame = data_frame.append(option.puts)

    print("Skipped option data for remaining expiry dates: {}".format(option_dates[num_expiry_dates:]))
    print("")

    return data_frame

def parse_args():
    # define all arguments to parse from command line
    parser = argparse.ArgumentParser(description="Get options chain data for a single stock.")
    parser.add_argument("-d", "--expiry_dates", default=0, type=int,
        help="Number of expiry dates in options chain (0 = all).")
    parser.add_argument("-s", "--symbol", required=True, help="Stock ticker symbol.")

    return parser.parse_args()

if __name__ == "__main__":
    main()
