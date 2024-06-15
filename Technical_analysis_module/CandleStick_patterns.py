from Data_env.Data_cleaning import data_cleaning
import datetime as dt
import pandas as pd
import numpy as np


class CandleSticks(data_cleaning):

    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.df_c_c = self.get_futures_data()

    def hammer(self,):

        self.df_c["hammer"] = (((self.df_c["High"] - self.df_c["Low"]) > 3 * (self.df_c["Open"] - self.df_c["Close"])) & \
                        ((self.df_c["Close"] - self.df_c["Low"]) / (.001 + self.df_c["High"] - self.df_c["Low"]) > 0.6) & \
                        ((self.df_c["Open"] - self.df_c["Low"]) / (.001 + self.df_c["High"] - self.df_c["Low"]) > 0.6)) & \
                       (abs(self.df_c["Close"] - self.df_c["Open"]) > 0.1 * (self.df_c["High"] - self.df_c["Low"]))
        return self.df_c

    def shooting_star(self,):

        self.df_c["sstar"] = (((self.df_c["High"] - self.df_c["Low"]) > 3 * (self.df_c["Open"] - self.df_c["Close"])) & \
                       ((self.df_c["High"] - self.df_c["Close"]) / (.001 + self.df_c["High"] - self.df_c["Low"]) > 0.6) & \
                       ((self.df_c["High"] - self.df_c["Open"]) / (.001 + self.df_c["High"] - self.df_c["Low"]) > 0.6)) & \
                      (abs(self.df_c["Close"] - self.df_c["Open"]) > 0.1 * (self.df_c["High"] - self.df_c["Low"]))
        return self.df_c


    def doji(self,):
        avg_doji = abs(self.df_c["Close"] - self.df_c["Open"]).median()
        self.df_c["doji"] = abs(self.df_c["Close"] - self.df_c["Open"]) <= (0.05 * avg_doji)
        return self.df_c

    def maru_bozu(self,):
        """returns dataframe with maru bozu candle column"""
        avg_candle_size = abs(self.df_c["Close"] - self.df_c["Open"]).median()
        self.df_c["h-c"] = self.df_c["High"] - self.df_c["Close"]
        self.df_c["l-o"] = self.df_c["Low"] - self.df_c["Open"]
        self.df_c["h-o"] = self.df_c["High"] - self.df_c["Open"]
        self.df_c["l-c"] = self.df_c["Low"] - self.df_c["Close"]
        self.df_c["maru_bozu"] = np.where((self.df_c["Close"] - self.df_c["Open"] > 2 * avg_candle_size) & \
                                   (self.df_c[["h-c", "l-o"]].max(axis=1) < 0.005 * avg_candle_size), "maru_bozu_green",
                                   np.where((self.df_c["Open"] - self.df_c["Close"] > 2 * avg_candle_size) & \
                                            (abs(self.df_c[["h-o", "l-c"]]).max(axis=1) < 0.005 * avg_candle_size),
                                            "maru_bozu_red", False))
        self.df_c.drop(["h-c", "l-o", "h-o", "l-c"], axis=1, inplace=True)
        return self.df_c
