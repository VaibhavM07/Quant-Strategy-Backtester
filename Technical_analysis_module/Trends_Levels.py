from Data_env.Data_cleaning import data_cleaning
from Technical_analysis_module.CandleStick_patterns import CandleSticks
import datetime as dt
import pandas as pd
import numpy as np


class Trends_Levels(CandleSticks):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.df_t = self.get_futures_data()

    def levels(self):
        ##calc suo,res,pivot for each tick

        high = round(self.df_t["High"], 2)
        low = round(self.df_t["Low"], 2)
        close = round(self.df_t["Close"], 2)
        pivot = round((high + low + close) / 3, 2)
        r1 = round((2 * pivot - low), 2)
        r2 = round((pivot + (high - low)), 2)
        r3 = round((high + 2 * (pivot - low)), 2)
        s1 = round((2 * pivot - high), 2)
        s2 = round((pivot - (high - low)), 2)
        s3 = round((low - 2 * (high - pivot)), 2)
        levels_df_t = pd.DataFrame({
            "p": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3
        })
        return levels_df_t

    def trend(self, n: int = 5):
        ##assess the trend by analyzing each candle
        self.df_t["up"] = np.where(self.df_t["Low"] >= self.df_t["Low"].shift(1), 1, 0)
        self.df_t["dn"] = np.where(self.df_t["High"] <= self.df_t["High"].shift(1), 1, 0)

        uptrend_count = 0
        downtrend_count = 0

        for i in range(len(self.df_t)):
            if i >= n:
                if self.df_t["Close"].iloc[i] > self.df_t["Open"].iloc[i]:
                    uptrend_count += self.df_t["up"].iloc[i - n + 1: i + 1].sum()
                elif self.df_t["Open"].iloc[i] > self.df_t["Close"].iloc[i]:
                    downtrend_count += self.df_t["dn"].iloc[i - n + 1: i + 1].sum()

        if uptrend_count >= 0.7 * n: ##70% candles shoudl be green
            return "uptrend"
        elif downtrend_count >= 0.7 * n:  ##70% candles shoudl be red
            return "downtrend"
        else:
            return None

    def res_sup(self):
        ##calc nearest supp/res for each candle
        levels_df_t = self.levels()

        if 'min_sup_idx' not in self.df_t.columns:
            self.df_t['min_sup_idx'] = None
        if 'max_res_idx' not in self.df_t.columns:
            self.df_t['max_res_idx'] = None

        for i in range(len(levels_df_t)):
            level = ((self.df_t["Close"].iloc[i] + self.df_t["Open"].iloc[i]) / 2 + (
                    self.df_t["High"].iloc[i] + self.df_t["Low"].iloc[i]) / 2) / 2    ##calc avg p(central tendency of price rnage)
            distances = levels_df_t.iloc[i]-level  #distancefrom avg

            self.df_t["min_sup_idx"].iloc[i] = distances.idxmin()#min_sup from avg p
            self.df_t["max_res_idx"].iloc[i] = distances.idxmax()#max_res from avg p
        return self.df_t








