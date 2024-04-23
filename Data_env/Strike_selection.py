from Data_env.Data_cleaning import data_cleaning
import pandas as pd
import string

"""Moneyness -ve will do down from ATM and +ve for going up from ATM"""
class Strike_selection(data_cleaning):
    def __init__(self,Moneyness:int=None,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.df = self.get_futures_data()
        self.Moneyness  = Moneyness

    def get_ATM_strike(self):
        strike = int(self.df["Open"].iloc[0].round(-2))
        return strike
    def custom_strike(self):
        ATM_strike = self.get_ATM_strike()
        return ATM_strike+self.Moneyness

