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
        ##calc suo,res,pivot for each tick

        high = round(self.df["High"], 2)
        low = round(self.df["Low"], 2)
        close = round(self.df["Close"], 2)
        pivot = round((high + low + close) / 3, 2)
        r1 = round((2 * pivot - low), 2)
        r2 = round((pivot + (high - low)), 2)
        r3 = round((high + 2 * (pivot - low)), 2)
        s1 = round((2 * pivot - high), 2)
        s2 = round((pivot - (high - low)), 2)
        s3 = round((low - 2 * (high - pivot)), 2)
        levels_df = pd.DataFrame({
            "p": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3
        })
        return levels_df

    def trend(self, n: int = 5):
        ##assess the trend by analyzing each candle
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

        if uptrend_count >= 0.7 * n: ##70% candles shoudl be green
            return "uptrend"
        elif downtrend_count >= 0.7 * n:  ##70% candles shoudl be red
            return "downtrend"
        else:
            return None

    def res_sup(self):
        ##calc nearest supp/res for each candle
        levels_df = self.levels()

        if 'min_sup_idx' not in self.df.columns:
            self.df['min_sup_idx'] = None
        if 'max_res_idx' not in self.df.columns:
            self.df['max_res_idx'] = None

        for i in range(len(levels_df)):
            level = ((self.df["Close"].iloc[i] + self.df["Open"].iloc[i]) / 2 + (
                    self.df["High"].iloc[i] + self.df["Low"].iloc[i]) / 2) / 2    ##calc avg p(central tendency of price rnage)
            distances = levels_df.iloc[i]-level  #distancefrom avg

            self.df["min_sup_idx"].iloc[i] = distances.idxmin()#min_sup from avg p
            self.df["max_res_idx"].iloc[i] = distances.idxmax()#max_res from avg p
        return self.df








