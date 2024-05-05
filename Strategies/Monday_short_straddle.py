import pandas as pd
import numpy as np
from Data_env import (Data_cleaning,get_expiry,Strike_selection)
from Performance import(runner_and_ratios)


class short_straddle():

    def __init__(self,path,ticker,Entry_time,Exit_time,quantity,tradelog:pd.DataFrame):
        self.path = path
        self.ticker = ticker
        self.Entry_time = Entry_time
        self.Exit_time = Exit_time
        self.tradelog = tradelog
        self.quantity =quantity

    def atm_option_data(self):
        self.call_universe = pd.DataFrame()
        self.put_universe = pd.DataFrame()
        option_data = Strike_selection.Strike_selection(path=self.path, ticker=self.ticker)
        self.calls = option_data.get_ATM_strike(call_put="CALL")
        self.puts = option_data.get_ATM_strike(call_put="PUT")
        self.expiry = option_data.current_weekly()
        for i in range(len(self.expiry)):
            self.call_universe = pd.concat([self.call_universe, self.calls[self.calls["Ticker"].apply(
                lambda a: a.strip()[:len(ticker) + len(self.expiry[i])] == str(ticker + self.expiry[i]))]])
            self.put_universe = pd.concat([self.put_universe, self.puts[self.puts["Ticker"].apply(
                lambda a: a.strip()[:len(ticker) + len(self.expiry[i])] == str(ticker + self.expiry[i]))]])

        self.call_universe = self.call_universe.sort_values(by=["Timestamp", "Volume"], ascending=[True, False])
        self.call_universe = self.call_universe[~self.call_universe.duplicated(subset="Timestamp", keep="first")]
        self.call_universe.columns= ["Timestamp", "CE_Ticker", "CE_Open", "CE_High", "CE_Low", "CE_Close", "CE_Volume",
                             "CE_Open_Interest"]

        self.put_universe = self.put_universe.sort_values(by=["Timestamp", "Volume"], ascending=[True, False])
        self.put_universe = self.put_universe[~self.put_universe.duplicated(subset="Timestamp", keep="first")]
        self.put_universe.columns= ["Timestamp", "PE_Ticker", "PE_Open", "PE_High", "PE_Low", "PE_Close", "PE_Volume",
                             "PE_Open_Interest"]

        self.trade_universe = pd.merge(self.call_universe, self.put_universe, on="Timestamp", suffixes=('', ''))


        self.trade_universe = self.trade_universe[self.trade_universe["Timestamp"] >= pd.to_datetime(
            self.trade_universe["Timestamp"].dt.date.astype(str) + " " + self.Entry_time)]
        self.trade_universe = self.trade_universe[self.trade_universe["Timestamp"] < pd.to_datetime(
            self.trade_universe["Timestamp"].dt.date.astype(str) + " " + self.Exit_time)]

        return self.trade_universe
    
    def trade_logic(self):
        self.CE_ticker = self.trade_universe['CE_Ticker'].iloc[0]
        self.PE_ticker = self.trade_universe['PE_Ticker'].iloc[0]
        self.CE_Entry_time = self.PE_Entry_time = self.trade_universe['Timestamp'].iloc[0]
        self.CE_Entry_price = self.trade_universe['CE_Open'].iloc[0]
        self.PE_Entry_price = self.trade_universe['PE_Open'].iloc[0]

        self.stop_loss_price = (self.CE_Entry_price + self.PE_Entry_price) * ((20 + 100) / 100)
        self.stop_loss = self.trade_universe[(self.trade_universe['CE_Open'] + self.trade_universe['PE_Open']) > self.stop_loss_price]

        if self.stop_loss.empty:
            self.stop_loss_exit = 0
            self.CE_Exit_time = self.PE_Exit_time = self.trade_universe['Timestamp'].iloc[-1]
            self.CE_Exit_price = self.trade_universe['CE_Open'].iloc[-1]
            self.PE_Exit_price = self.trade_universe['PE_Open'].iloc[-1]
        else:
            self.stop_loss_exit = 1
            self.CE_Exit_time = self.PE_Exit_time = self.stop_loss['Timestamp'].iloc[0]
            self.CE_Exit_price = self.stop_loss['CE_Open'].iloc[0]
            self.PE_Exit_price = self.stop_loss['PE_Open'].iloc[0]

        self.tradelog.loc[len(self.tradelog)] = [self.CE_ticker, self.CE_Entry_time, self.CE_Entry_price, self.stop_loss_exit, self.CE_Exit_time,
                                       self.CE_Exit_price]
        self.tradelog.loc[len(self.tradelog)] = [self.PE_ticker, self.PE_Entry_time, self.PE_Entry_price, self.stop_loss_exit, self.PE_Exit_time,
                                       self.PE_Exit_price]

        if self.stop_loss_exit:
            if self.CE_Exit_price > self.CE_Entry_price and self.PE_Exit_price < self.PE_Entry_price:
                leg = "PE"
            elif self.CE_Exit_price < self.CE_Entry_price and self.PE_Exit_price > self.PE_Entry_price:
                leg = "CE"
            else:
                print("Error in Leg Entry. Logic Malfunction")

            self.leg_ticker = self.trade_universe[leg + "_Ticker"].iloc[0]
            self.leg_entry_time = self.stop_loss["Timestamp"].iloc[0]
            self.leg_entry_price = self.stop_loss[leg + "_Open"].iloc[0]

            self.leg_stop_loss_price = self.leg_entry_price * ((100 + 20) / 100)
            self.leg_stop_loss = self.trade_universe[self.trade_universe["Timestamp"] > self.leg_entry_time]
            self.leg_stop_loss = self.leg_stop_loss[self.leg_stop_loss[leg + '_Open'] > self.leg_stop_loss_price]


            if self.leg_stop_loss.empty:
                self.leg_stop_loss_exit = 0
                self.leg_exit_time = self.trade_universe["Timestamp"].iloc[-1]
                self.leg_exit_price = self.trade_universe[leg + "_Open"].iloc[-1]
            else:
                self.leg_stop_loss_exit = 1
                self.leg_exit_time = self.leg_stop_loss["Timestamp"].iloc[0]
                self.leg_exit_price = self.leg_stop_loss[leg + "_Open"].iloc[0]

            self.tradelog.loc[len(self.tradelog)] = [self.leg_ticker, self.leg_entry_time, self.leg_entry_price, self.leg_stop_loss_exit,
                                           self.leg_exit_time, self.leg_exit_price]

        return self.tradelog

    def performace(self):
        performace = runner_and_ratios.runner(initial_capital=100000,risk_free_rate=1,tradelog=self.tradelog,quantity=self.quantity)
        self.report = performace.report()
        return self.report



if __name__ == "__main__":
    path = r"/Users/vaibhavmishra/GitHub/Backtesting/Sample data/"
    ticker = "BANKNIFTY"
    obj1 = short_straddle(path=path,ticker=ticker,Entry_time="09:29:59",Exit_time="15:15:00",quantity = 25,tradelog=pd.DataFrame(columns = ['Ticker', 'Entry Time', 'Entry Price', 'Stop Loss Exit', 'Exit Time', 'Exit Price']))
    obj1.atm_option_data()
    obj1.trade_logic()
    obj1.performace()
