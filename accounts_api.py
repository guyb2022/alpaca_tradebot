import config, requests
import alpaca_trade_api as trader_api
from alpaca_trade_api.rest import REST, TimeFrame
import pandas as pd
import numpy as np
from statistics import mode
from alpaca_trade_api.stream import Stream
from datetime import datetime,timedelta
from anyio import current_time
import logging
import os
import time
import nest_asyncio
nest_asyncio.apply()
import talib as talib

API_KEY = config.API_KEY
SECRET_KEY = config.SECRET_KEY
BASE_URL = config.BASE_URL
WS_URL = config.WS_URL

class AlpacaAccount:
    def __init__(self, symbol):
        self.API_KEY = config.API_KEY
        self.API_SECRET = config.SECRET_KEY
        self.BASE_URL = config.BASE_URL
        self.api = REST(config.API_KEY,
                        config.SECRET_KEY,
                        config.BASE_URL)
        self.symbol = symbol
        self.df = pd.DataFrame()
        self.stream = Stream(API_KEY,
                             SECRET_KEY,
                             BASE_URL,
                             raw_data=False,
                             data_feed='iex')
        self.ORDER_URL = config.ORDER_URL
        self.account = self.api.get_account()

    async def trade_bars(self, bars):
        # handle all the trade/data manipulation
        temp_df = pd.DataFrame(
            columns=["Date", "Open", "High", "Low", "Close", "Volume", "Vwap"]
        )
        present_time = datetime.utcfromtimestamp(bars.timestamp/10**9).strftime("%Y-%m-%d %H:%M:%S")
        temp_df["Date"] = [present_time]
        temp_df["Open"] = [bars.open]
        temp_df["High"] = [bars.high]
        temp_df["Low"] = [bars.low]
        temp_df["Close"] = [bars.close]
        temp_df["Volume"] = [bars.volume]
        temp_df["Vwap"] = [bars.vwap]

        file_name = "bars.csv"
        columns_list = ["Date", "Open", "High", "Low", "Close", "Volume", "Vwap"]
        self.csv_handling(file_name, columns_list)

        trade_temp_df = pd.read_csv(file_name)
        trade_temp_df = pd.concat([trade_temp_df, temp_df], ignore_index=True)

        trade_temp_df.to_csv(file_name, index=False)

        # Calculate relevant indicators
        indicators = self.calculate_indicators(trade_temp_df)
        # Get new columns from indicators dataframe
        trade_temp_df['MA_5'] = indicators['MA_5']
        trade_temp_df['MA_20'] = indicators['MA_20']
        trade_temp_df['MA_200'] = indicators['MA_200']
        trade_temp_df['EMA_21'] = indicators['EMA_21']
        trade_temp_df['RSI'] = indicators['RSI']
        trade_temp_df['Stoch_K'] = indicators['Stoch_K']
        trade_temp_df['Stoch_D'] = indicators['Stoch_D']
        trade_temp_df['BB_Upper'] = indicators['BB_Upper']
        trade_temp_df['BB_Middle'] = indicators['BB_Middle']
        trade_temp_df['BB_Lower'] = indicators['BB_Lower']
        trade_temp_df['ATR'] = indicators['ATR']
        trade_temp_df['OBV'] = indicators['OBV']
        trade_temp_df['CMF'] = indicators['CMF']
        trade_temp_df['MACD'] = indicators['MACD']
        trade_temp_df['MACD_Signal'] = indicators['MACD_Signal']
        trade_temp_df['MACD_Hist'] = indicators['MACD_Hist']
        trade_temp_df['ROC'] = indicators['ROC']
        trade_temp_df['HT_Trendline'] = indicators['HT_Trendline']
        trade_temp_df['Elliott_Waves'] = indicators['Elliott_Waves']

        last_row = trade_temp_df.iloc[-1]
        trade_temp_df = trade_temp_df.iloc[:-1]
        print(last_row)
        return last_row

    def calculate_indicators(self, df):
        # Create a copy of the dataframe
        df = df.copy()
        # Moving Average
        df['MA_5'] = talib.SMA(df['Close'], timeperiod=5)
        df['MA_20'] = talib.SMA(df['Close'], timeperiod=20)
        df['MA_200'] = talib.SMA(df['Close'], timeperiod=200)
        # Exponential Moving Average
        df['EMA_21'] = talib.EMA(df['Close'], timeperiod=21)
        # Relative Strength Index
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
        # Stochastic Oscillator
        df['Stoch_K'], df['Stoch_D'] = talib.STOCH(df['High'],
                                                   df['Low'], df['Close'],
                                                   fastk_period=14, slowk_period=3,
                                                   slowd_period=3)
        # Bollinger Bands
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = talib.BBANDS(df['Close'],
                                                                       timeperiod=14)
        # Average True Range
        df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
        # On-Balance Volume
        df['OBV'] = talib.OBV(df['Close'], df['Volume'])
        # Chaikin Money Flow
        df['CMF'] = talib.CMF(df['High'], df['Low'], df['Close'], df['Volume'],
                              timeperiod=14)
        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(df['Close'],
                                                                    fastperiod=12,
                                                                    slowperiod=26,
                                                                    signalperiod=9)
        # ROC
        df['ROC'] = talib.ROC(df['Close'], timeperiod=14)
        # Hilbert Transform
        df['HT_Trendline'] = talib.HT_TRENDLINE(df['Close'])
        # Elliott Waves
        df['Elliott_Waves'] = talib.HT_TRENDMODE(df['Close'])
        return df

    def csv_handling(self, file_name: str, columns_list: list):
        if os.path.exists(file_name):
            try:
                trade_temp_df = pd.read_csv(file_name)
            except:
                print("The file doesn't exist, creating it")
                trade_temp_df = pd.DataFrame(columns=columns_list)
                trade_temp_df.to_csv(file_name)
            if trade_temp_df.empty:
                trade_temp_df = pd.DataFrame(columns=columns_list)
                trade_temp_df.to_csv(file_name)
            else:
                pass
        else:
            trade_temp_df = pd.DataFrame(columns=columns_list)
            trade_temp_df.to_csv(file_name)

    def run_connection(self):
        try:
            self.stream.run()
        except KeyboardInterrupt:
            print("Interrupted execution by the user")
            loop.run_until_complete(self.stream.stop_ws())
            exit(0)
        except Exception as e:
            print(f'Exception from websocket connection: {e}')
        finally:
            print('Trying to re-establish connection')
            time.sleep(3)
            self.run_connection()

    def get_history_data(self, start,end):
        ## Check if n=200 satisfy the equestion
        return self.api.get_bars(self.symbol, TimeFrame.Minute, start, end, limit=200).df

    def print_account(self):
        # print(f"account_number: {self.account_number} -- cash: {self.cash} --- "
        #       f"equity: {self.equity}")
        print(self.account)

    def submit_order(self, ticker, qty, type, side):
        data = {
            'symbol': ticker,
            'qty': qty,
            'type': type,
            'side': side,
            'time_in_force': 'day'
        }
        # r = requests.post(config.ORDER_URL, json=data, headers=config.HEADERS)
        self.order = self.api.submit_order(data)
        print(self.order)

    def get_positions(self):
        portfolio_position = self.api.get_position(self.symbol)
        print(portfolio_position)
        return portfolio_position

    def get_all_positions(self):
        portfolio = self.api.list_positions()
        # Print the quantity of shares for each position.
        for position in portfolio:
            print("{} shares of {}".format(position.qty, position.symbol))

    def close_all_position(self):
        self.api.close_all_positions()

    def is_done(self):
        # cash = self.api.get_account()['cash']
        # units = self.api.get_position(self.symbol)['qty'].values
        # price = self.df.iloc[]['close']
        # if cash < price & units < 0:
        #     return True
        return False

    def market_is_open(self):
        return self.api.get_clock().is_open