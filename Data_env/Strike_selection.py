from Data_env.get_expiry import get_expiry
import pandas as pd
import string

"""Moneyness -ve will do down from ATM and +ve for going up from ATM"""
class Strike_selection(get_expiry):
    def __init__(self,Moneyness:int=None,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.df_s = self.get_futures_data()
        self.calls = self.get_ticker_call_data()
        self.puts = self.get_ticker_put_data()
        self.Moneyness  = Moneyness
        self.strike = int(self.df_s["Open"].iloc[0].round(-2))

    def get_ATM_strike(self,call_put):
        if call_put == "CALL":
            call_strike = str(self.strike)+"CE.NFO"
            ATM_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-11:] == call_strike)]
            if ATM_call.empty:
                call_strike = str(self.strike) + "CE"
                ATM_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-7:] == call_strike)]
            return ATM_call

        elif call_put == "PUT":
            put_strike = str(self.strike)+"PE.NFO"
            ATM_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[-11:] == put_strike)]
            if ATM_put.empty:
                put_strike = str(self.strike) + "PE"
                ATM_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[-7:] == put_strike)]
            return ATM_put

    def custom_strike(self,call_put):
        custom_str = int(self.df_s["Open"].iloc[0].round(-2))+self.Moneyness
        if call_put == "CALL":
            call_strike = str(custom_str)+"CE.NFO"
            custom_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-11:] == call_strike)]
            if custom_call.empty:
                call_strike = str(self.strike) + "CE"
                custom_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-7:] == call_strike)]
            return custom_call

        elif call_put == "PUT":
            put_strike = str(self.strike)+"PE.NFO"
            custom_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[11:] == put_strike)]
            if custom_put.empty:
                put_strike = str(self.strike) + "PE"
                custom_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[7:] == put_strike)]
            return custom_put


