from Data_env.Data_cleaning import data_cleaning
import pandas as pd
import numpy as np

class Indicators(data_cleaning):

    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.df_i = self.get_futures_data()

    def ema(self,observation_window:int=9,ma:int=10):
        self.df_i[str(ma)+"EMA"] = self.df_i["Close"].ewm(span=ma, min_periods=observation_window).mean()
        self.df_i.dropna(inplace=True)
        return self.df_i
    def macd(self,fast_length:int = 12,slow_length:int =26,signal_smoothing:int = 9):

        self.df_i["MA_fast"] = self.df_i["Close"].rolling(fast_length).mean()
        self.df_i["MA_slow"] = self.df_i["Close"].rolling(slow_length).mean()
        self.df_i["MACD"] = self.df_i["MA_fast"] - self.df_i["MA_slow"]
        self.df_i["signal"] = self.df_i["MACD"].rolling(signal_smoothing).mean()
        self.df_i.dropna(inplace=True)
        return self.self.df_i

    def bollinger_bands(self, length:int =20, stdDev:int = 2):
        # here s is the number of standard dev
        self.df_i["MA"] = self.df_i["Close"].ewm(span=length, min_periods=length).mean()
        self.df_i["BB_up"] = self.df_i["MA"] + stdDev * self.df_i["Close"].rolling(length).std(ddof=0)
        self.df_i["BB_down"] = self.df_i["MA"] - stdDev * self.df_i["Close"].rolling(length).std(ddof=0)
        self.df_i["BB_width"] = self.df_i["BB_up"] - self.df_i["BB_down"]
        self.df_i.dropna(inplace=True)
        return self.df_i

    def pivot(self,):
        self.df_i['PP'] = (self.df_i['High'] + self.df_i['Low'] + self.df_i['Close']) / 3
        self.df_i['R1'] = 2 * self.df_i['PP'] - self.df_i['Low']
        self.df_i['S1'] = 2 * self.df_i['PP'] - self.df_i['High']
        self.df_i['R2'] = self.df_i['PP'] + (self.df_i['High'] - self.df_i['Low'])
        self.df_i['S2'] = self.df_i['PP'] - (self.df_i['High'] - self.df_i['Low'])
        self.df_i['R3'] = self.df_i['PP'] + 2 * (self.df_i['High'] - self.df_i['Low'])
        self.df_i['S3'] = self.df_i['PP'] - 2 * (self.df_i['High'] - self.df_i['Low'])
        return self.df_i

    def stocastic(self,):
        self.df_i['14-high'] = self.df_i['High'].rolling(14).max()
        self.df_i['14-low'] = self.df_i['Low'].rolling(14).min()
        self.df_i['%K'] = (self.df_i['Close'] - self.df_i['14-low']) * 100 / (self.df_i['14-high'] - self.df_i['14-low'])
        self.df_i['%D'] = self.df_i['%K'].rolling(3).mean()
        self.df_i['%K'] = self.df_i['%K'].apply(lambda a: round(a, 2))
        self.df_i['%D'] = self.df_i['%D'].apply(lambda a: round(a, 2))
        self.df_i.drop('14-low', axis=1, inplace=True)
        self.df_i.drop('14-high', axis=1, inplace=True)
        return self.df_i

    def Supertrend(self, atr_period:int = 10, multiplier:int = 3):

        high = self.df_i['High']
        low = self.df_i['Low']
        close = self.df_i['Close']

        #atr
        price_diffs = [high - low,
                       high - close.shift(),
                       close.shift() - low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        # default atr calculation in supertrend indicator
        atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean()

        hl2 = (high + low) / 2
        # upperband and lowerband calculation
        final_upperband = upperband = hl2 + (multiplier * atr)
        final_lowerband = lowerband = hl2 - (multiplier * atr)

        # initialize Supertrend column to true
        supertrend = pd.Series(True, index=self.df_i.index)

        for i in range(1, len(self.df_i.index)):
            curr, prev = i, i - 1

            # if current close price crosses above upperband
            if close.iloc[curr] > final_upperband.iloc[prev]:
                supertrend.iloc[curr] = True
            # if current close price crosses below lowerband
            elif close.iloc[curr] < final_lowerband.iloc[prev]:
                supertrend.iloc[curr] = False
            # else, the trend continues
            else:
                supertrend.iloc[curr] = supertrend.iloc[prev]

                # adjustment to the final bands
                if supertrend.iloc[curr] == True and final_lowerband.iloc[curr] < final_lowerband.iloc[prev]:
                    final_lowerband.iloc[curr] = final_lowerband.iloc[prev]
                if supertrend.iloc[curr] == False and final_upperband.iloc[curr] > final_upperband.iloc[prev]:
                    final_upperband.iloc[curr] = final_upperband.iloc[prev]

            # remove bands according to the trend direction
            if supertrend.iloc[curr] == True:
                final_upperband.iloc[curr] = np.nan
            else:
                final_lowerband.iloc[curr] = np.nan

        return pd.DataFrame({
            'Supertrend' + str(atr_period): supertrend,
            'Final Lowerband' + str(atr_period): final_lowerband,
            'Final Upperband' + str(atr_period): final_upperband
        }, index=self.df_i.index)