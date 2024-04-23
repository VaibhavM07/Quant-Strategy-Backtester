from Data_env.Data_cleaning import data_cleaning
from Technical_analysis_module.CandleStick_patterns import CandleSticks
import datetime as dt
import pandas as pd
import numpy as np


class Trends_Levels(CandleSticks):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.df = self.get_futures_data()

    def levels(self):

        #ivot point and support/resistance levels"
        high = round(self.df["High"], 2)
        low = round(self.df["Low"], 2)
        close = round(self.df["Close"], 2)
        self.df["pivot"] = round((high + low + close) / 3, 2)
        self.df["r1"] = round((2 * self.df["pivot"]  - low), 2)
        self.df["r2"] = round((self.df["pivot"]  + (high - low)), 2)
        self.df["r3"] = round((high + 2 * (self.df["pivot"]  - low)), 2)
        self.df["s1"] = round((2 * self.df["pivot"]  - high), 2)
        self.df["s2"] = round((self.df["pivot"]  - (high - low)), 2)
        self.df["s3"] = round((low - 2 * (high - self.df["pivot"] )), 2)
        return self.df

    def trend(self, n: int = 5):
        # Function to assess the trend by analyzing each candle
        self.df["up"] = np.where(self.df["Low"] >= self.df["Low"].shift(1), 1, 0)
        self.df["dn"] = np.where(self.df["High"] <= self.df["High"].shift(1), 1, 0)

        uptrend_count = 0
        downtrend_count = 0

        for i in range(len(self.df)):
            if i >= n:
                if self.df["Close"].iloc[i] > self.df["Open"].iloc[i]:
                    uptrend_count += self.df["up"].iloc[i - n + 1: i + 1].sum()
                elif self.df["Open"].iloc[i] > self.df["Close"].iloc[i]:
                    downtrend_count += self.df["dn"].iloc[i - n + 1: i + 1].sum()

        if uptrend_count >= 0.7 * n:
            return "uptrend"
        elif downtrend_count >= 0.7 * n:
            return "downtrend"
        else:
            return None



