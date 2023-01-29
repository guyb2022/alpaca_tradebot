from accounts_api import AlpacaAccount
import time
from datetime import datetime, timedelta

if __name__ == "__main__":
    
    alpaca = AlpacaAccount('NVDA')
    alpaca.csv_handling(
            "bars.csv",
            columns_list=["time", "open", "high", "low", "close",
                          "volume", "tic", "exchange", "vwap"],
    )
    n = 200
    while True:
        end = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        start = (datetime.strptime(end, "%Y-%m-%d %H:%M:%S") -\
                 timedelta(minutes=n)).strftime("%Y-%m-%d %H:%M:%S")
        # check is trading hours
        if alpaca.market_is_open():
            print("market is open")
            # collect 200 last bars into bars.csv
            hist_sf = alpaca.get_history_data(start, end)
            hist_sf.to_csv('bars.csv')
            # stream live data
            last_price_bar = alpaca.stream.subscribe_bars(alpaca.trade_bars, alpaca.symbol)
            alpaca.run_connection()
            # run the agent to predict action

            if alpaca.is_done():
                break


    # acc.print_account()
    # # ticker, qty, type, side:
    # acc.submit_order('NVDA', '10', 'market', 'buy')
    # acc.print_account()
    # alpaca_trader = Alpaca('AAPL')
    # print("------------   starting agent  --------------")
    # print("Acount property: ")
    # alpaca_trader.print_property()
    # print("Acount positions: ")
    # alpaca_trader.print_positions()
    ## alpaca_trader.get_historical_data('1H')
    ## trader.update_df()
    ## print(trader.df.head())