import pandas as pd
import numpy as np
from Data_env import (Data_cleaning,get_expiry,Strike_selection)
from Performance import(runner_and_ratios)


class short_straddle:

    def __init__(self, path, ticker, Entry_time, Exit_time, quantity, tradelog: pd.DataFrame):
        self.path = path
        self.ticker = ticker
        self.Entry_time = Entry_time
        self.Exit_time = Exit_time
        self.tradelog = tradelog
        self.quantity = quantity

    def atm_option_data(self):
        self.call_universe = pd.DataFrame()
        self.put_universe = pd.DataFrame()
        option_data = Strike_selection.Strike_selection(path=self.path, ticker=self.ticker)
        self.calls = option_data.get_ATM_strike(call_put="CALL")
        self.puts = option_data.get_ATM_strike(call_put="PUT")
        self.expiry = option_data.current_weekly()
        for i in range(len(self.expiry)):
            self.call_universe = pd.concat([self.call_universe, self.calls[self.calls["Ticker"].apply(
                lambda a: a.strip()[:len(self.ticker) + len(self.expiry[i])] == str(self.ticker + self.expiry[i]))]])
            self.put_universe = pd.concat([self.put_universe, self.puts[self.puts["Ticker"].apply(
                lambda a: a.strip()[:len(self.ticker) + len(self.expiry[i])] == str(self.ticker + self.expiry[i]))]])

        self.call_universe = self.call_universe.sort_values(by=["Timestamp", "Volume"], ascending=[True, False])
        self.call_universe = self.call_universe[~self.call_universe.duplicated(subset="Timestamp", keep="first")]
        self.call_universe.columns = ["Timestamp", "CE_Ticker", "CE_Open", "CE_High", "CE_Low", "CE_Close", "CE_Volume",
                                      "CE_Open_Interest"]

        self.put_universe = self.put_universe.sort_values(by=["Timestamp", "Volume"], ascending=[True, False])
        self.put_universe = self.put_universe[~self.put_universe.duplicated(subset="Timestamp", keep="first")]
        self.put_universe.columns = ["Timestamp", "PE_Ticker", "PE_Open", "PE_High", "PE_Low", "PE_Close", "PE_Volume",
                                     "PE_Open_Interest"]

        self.trade_universe = pd.merge(self.call_universe, self.put_universe, on="Timestamp")

        self.trade_universe = self.trade_universe[self.trade_universe["Timestamp"] >= pd.to_datetime(
            self.trade_universe["Timestamp"].dt.date.astype(str) + " " + self.Entry_time)]
        self.trade_universe = self.trade_universe[self.trade_universe["Timestamp"] < pd.to_datetime(
            self.trade_universe["Timestamp"].dt.date.astype(str) + " " + self.Exit_time)]

        return self.trade_universe

    def trade_logic(self):
        trade_active = False
        entry_time = None
        entry_price = None

        for index, row in self.trade_universe.iterrows():
            current_time = row['Timestamp']

            if trade_active:
                # Exit the trade at the end of the day or around 3:15 PM
                if current_time.date() > entry_time.date() or current_time.time() >= pd.to_datetime(self.Exit_time).time():
                    self.exit_trade(current_time)
                    trade_active = False
                    continue

                stop_loss_price = (entry_price * 1.20)
                if (row['CE_Open'] + row['PE_Open']) > stop_loss_price:
                    self.exit_trade(current_time)
                    trade_active = False
                    continue

            if not trade_active:
                CE_ticker = row['CE_Ticker']
                PE_ticker = row['PE_Ticker']
                entry_time = current_time
                entry_price = row['CE_Open'] + row['PE_Open']

                stop_loss_price = entry_price * 1.20

                self.tradelog = pd.concat([self.tradelog, pd.DataFrame([{
                    'Ticker': CE_ticker, 'Entry Time': entry_time, 'Entry Price': row['CE_Open'],
                    'Stop Loss Exit': None, 'Exit Time': None, 'Exit Price': None
                }, {
                    'Ticker': PE_ticker, 'Entry Time': entry_time, 'Entry Price': row['PE_Open'],
                    'Stop Loss Exit': None, 'Exit Time': None, 'Exit Price': None
                }])], ignore_index=True)

                trade_active = True

        if trade_active:
            self.exit_trade(self.trade_universe['Timestamp'].iloc[-1])

        return self.tradelog

    def exit_trade(self, current_time):
        # Ensure that only valid indices are accessed
        try:
            index = self.trade_universe[self.trade_universe['Timestamp'] == current_time].index[0]
            if index < len(self.trade_universe):
                self.tradelog.loc[len(self.tradelog) - 2, 'Exit Time'] = current_time
                self.tradelog.loc[len(self.tradelog) - 2, 'Exit Price'] = self.trade_universe['CE_Open'].iloc[index]
                self.tradelog.loc[len(self.tradelog) - 1, 'Exit Time'] = current_time
                self.tradelog.loc[len(self.tradelog) - 1, 'Exit Price'] = self.trade_universe['PE_Open'].iloc[index]
                self.tradelog.loc[len(self.tradelog) - 2, 'Stop Loss Exit'] = 1 if (self.trade_universe['CE_Open'].iloc[index] + self.trade_universe['PE_Open'].iloc[index]) > (self.tradelog['Entry Price'].iloc[-2] + self.tradelog['Entry Price'].iloc[-1]) * 1.20 else 0
                self.tradelog.loc[len(self.tradelog) - 1, 'Stop Loss Exit'] = self.tradelog.loc[len(self.tradelog) - 2, 'Stop Loss Exit']
            else:
                print(f"Index {index} is out of bounds for trade_universe with length {len(self.trade_universe)}.")
        except IndexError as e:
            print(f"Index error at position {index}: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


    def performace(self):
        performace = runner_and_ratios.runner(initial_capital=100000,risk_free_rate=1,tradelog=self.tradelog,quantity=self.quantity)
        self.report = performace.report()
        return self.report



if __name__ == "__main__":
    path = r"/Users/vaibhavmishra/NSE Data/ALL NSE DATA/NSE F&O year 20112015&2019-2020/NSE F&O/2019"
    ticker = "BANKNIFTY"
    obj1 = short_straddle(path=path,ticker=ticker,Entry_time="09:29:59",Exit_time="15:15:00",quantity = 25,tradelog=pd.DataFrame(columns = ['Ticker', 'Entry Time', 'Entry Price', 'Stop Loss Exit', 'Exit Time', 'Exit Price']))
    obj1.atm_option_data()
    obj1.trade_logic()
    print(obj1.performace())
