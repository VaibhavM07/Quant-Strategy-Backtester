from Data_env.Data_cleaning import data_cleaning
import datetime as dt
import pandas as pd
import numpy as np


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


    def doji(self,):
        avg_doji = abs(self.df["Close"] - self.df["Open"]).median()
        self.df["doji"] = abs(self.df["Close"] - self.df["Open"]) <= (0.05 * avg_doji)
        return self.df

    def maru_bozu(self,):
        """returns dataframe with maru bozu candle column"""
        avg_candle_size = abs(self.df["Close"] - self.df["Open"]).median()
        self.df["h-c"] = self.df["High"] - self.df["Close"]
        self.df["l-o"] = self.df["Low"] - self.df["Open"]
        self.df["h-o"] = self.df["High"] - self.df["Open"]
        self.df["l-c"] = self.df["Low"] - self.df["Close"]
        self.df["maru_bozu"] = np.where((self.df["Close"] - self.df["Open"] > 2 * avg_candle_size) & \
                                   (self.df[["h-c", "l-o"]].max(axis=1) < 0.005 * avg_candle_size), "maru_bozu_green",
                                   np.where((self.df["Open"] - self.df["Close"] > 2 * avg_candle_size) & \
                                            (abs(self.df[["h-o", "l-c"]]).max(axis=1) < 0.005 * avg_candle_size),
                                            "maru_bozu_red", False))
        self.df.drop(["h-c", "l-o", "h-o", "l-c"], axis=1, inplace=True)
        return self.df
