from Data_env.Get_expiry import get_expiry
import pandas as pd
import string
"""target_strike -ve will do down from ATM and +ve for going up from ATM"""
class Strike_selection():
    def __init__(self,call_put: str,futures: pd.DataFrame = None,calls: pd.DataFrame = None,puts: pd.DataFrame = None,target_strikes: list[int] = None):
        self.df_s = futures
        self.calls = calls
        self.puts = puts
        self.call_put = call_put
        self.target_strikes  = target_strikes
        self.strike = int(self.df_s["Open"].iloc[0].round(-2))
        self.custom_Calls = pd.DataFrame()
        self.custom_Puts = pd.DataFrame()

    def get_ATM_strike(self):
        if self.call_put == "CALL":
            call_strike = str(self.strike)+"CE.NFO"
            ATM_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-11:] == call_strike)]
            if ATM_call.empty:
                call_strike = str(self.strike) + "CE"
                ATM_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-7:] == call_strike)]
            return ATM_call

        elif self.call_put == "PUT":
            put_strike = str(self.strike)+"PE.NFO"
            ATM_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[-11:] == put_strike)]
            if ATM_put.empty:
                put_strike = str(self.strike) + "PE"
                ATM_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[-7:] == put_strike)]
            return ATM_put

    def custom_strike(self):
        for target_strike in self.target_strikes:
            custom_str = int(self.df_s["Open"].iloc[0].round(-2))+target_strike
            if self.call_put == "CALL":
                call_strike = str(custom_str)+"CE.NFO"
                custom_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-11:] == call_strike)]
                if custom_call.empty:
                    call_strike = str(self.strike) + "CE"
                    custom_call = self.calls[self.calls['Ticker'].apply(lambda a: a.strip()[-7:] == call_strike)]
                    self.custom_Calls = pd.concat([self.custom_Calls,custom_call])

            elif self.call_put == "PUT":
                put_strike = str(self.strike)+"PE.NFO"
                custom_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[11:] == put_strike)]
                if custom_put.empty:
                    put_strike = str(self.strike) + "PE"
                    custom_put = self.puts[self.puts['Ticker'].apply(lambda a: a.strip()[7:] == put_strike)]
                    self.custom_Puts = pd.concat([self.custom_Puts, custom_put])
        return self.custom_Calls,self.custom_Puts


