from Data_env.Data_cleaning import data_cleaning
import datetime as dt
import pandas as pd


class CandleSticks(data_cleaning):

    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.df = self.get_futures_data()

    def hammer(self,):

        self.df["hammer"] = (((self.df["High"] - self.df["Low"]) > 3 * (self.df["Open"] - self.df["Close"])) & \
                        ((self.df["Close"] - self.df["Low"]) / (.001 + self.df["High"] - self.df["Low"]) > 0.6) & \
                        ((self.df["Open"] - self.df["Low"]) / (.001 + self.df["High"] - self.df["Low"]) > 0.6)) & \
                       (abs(self.df["Close"] - self.df["Open"]) > 0.1 * (self.df["High"] - self.df["Low"]))
        return self.df

    def shooting_star(self,):

        self.df["sstar"] = (((self.df["High"] - self.df["Low"]) > 3 * (self.df["Open"] - self.df["Close"])) & \
                       ((self.df["High"] - self.df["Close"]) / (.001 + self.df["High"] - self.df["Low"]) > 0.6) & \
                       ((self.df["High"] - self.df["Open"]) / (.001 + self.df["High"] - self.df["Low"]) > 0.6)) & \
                      (abs(self.df["Close"] - self.df["Open"]) > 0.1 * (self.df["High"] - self.df["Low"]))
        return self.df