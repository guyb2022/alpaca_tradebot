import requests, json
import pandas as pd
import numpy as np
from config import *
from talib import STOCHRSI, MFI
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import TimeInForce
from config import *
from alpaca.trading.client import TradingClient


class Alpaca:
    def __init__(self, symbol):
        self.api_key = API_KEY
        self.api_secret_key = SECRET_KEY
        self.base_url = APCA_API_BASE_URL
        self.trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
        self.account = self.trading_client.get_account()
        self.initial_balance = 100000
        self.df = pd.DataFrame()
        self.symbol = symbol

    def print_property(self):
        # Getting account information and printing it
        client = self.trading_client.get_account()
        print(f"cash: {client.cash} -- portfolio value: {client.portfolio_value}\n")

        # for property_name, value in client:
        #     print(f"\"{property_name}\": {value}")

    def submit_order(self, qty, side):
        # Setting parameters for our buy order
        market_order_data = MarketOrderRequest(symbol=self.symbol,
                                               qty=qty,
                                               side=side,
                                               time_in_force=TimeInForce.GTC
                                               )
        self.trading_client.submit_order(market_order_data)

    def print_positions(self):
        positions = self.trading_client.get_all_positions()
        for position in positions:
            # qty, cost_basis, market_value, unrealized_intraday_pl, change_today, current_price
            # unrealized_pl, unrealized_plpc,
            print(f"qty: {position.qty}")
            print(f"cost basis: {position.cost_basis}")
            print(f"market value: {position.market_value}")
            print(f"unrealized intraday pl: {position.unrealized_intraday_pl}")
            print(f"change today: {position.change_today}")
            print(f"current price: {position.current_price}")
            print(f"unrealized pl: {position.unrealized_pl}")
            print(f"unrealized plpc: {position.unrealized_plpc}")



    def get_historical_data(self, interval):
        url = f'{self.base_url}/v1/bars/{interval}?symbols={self.symbol}&limit=30'
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret_key
        }
        r = requests.get(url, headers=headers)
        data = r.json()
        if r.status_code != 200:
            print("Error: The request was unsuccessful.")
        else:
            data = json.loads(r.content)
            print(data)
        print(r.status_code)
        print(r.json())
        self.df = pd.DataFrame(data[self.symbol])
        self.df.index = pd.to_datetime(self.df.t, unit='s')
        self.df = self.df[['o', 'h', 'l', 'c', 'v']]
        self.df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    def update_indicators(self):
        self.df['RSI'] = STOCHRSI(self.df['Close'].values, timeperiod=14)
        self.df['MFI'] = MFI(self.df['High'].values, self.df['Low'].values, self.df['Close'].values, self.df['Volume'].values, timeperiod=14)
        self.df['MA5'] = self.df['Close'].rolling(window=5).mean()
        self.df['MA50'] = self.df['Close'].rolling(window=50).mean()
        self.df['MA200'] = self.df['Close'].rolling(window=200).mean()

    def update_df(self):
        url = f'{self.base_url}/v1/last/stocks/{self.symbol}'
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret_key
        }
        r = requests.get(url, headers=headers)
        data = r.json()
        new_price = {'Open': data['last']['o'],
                     'High': data['last']['h'],
                     'Low': data['last']['l'],
                     'Close': data['last']['c'],
                     'Volume': data['last']['v']}
        new_price_df = pd.DataFrame(new_price, index=[data['last']['t']])
        self.df = self.df.append(new_price_df)
        self.update_indicators()