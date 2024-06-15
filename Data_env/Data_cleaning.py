from Data_env.Data_loading import data_load
import pandas as pd
import string
import datetime as dt
import glob
import warnings
warnings.filterwarnings('ignore')

class data_cleaning():

    def __init__(self,path:string,ticker:string):
        self.path = path
        self.ticker = ticker
        self.df = data_load(path=self.path)
        if self.df.empty:
            print("No Data found in "+self.path)
        else:
            self.df.insert(0, "Timestamp", self.df["Date"] + " " + self.df["Time"])
            self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], format="%d/%m/%Y %H:%M:%S")
            self.df = self.df.sort_values(by="Timestamp")
            self.df["Ticker"] = self.df["Ticker"].apply(str)
            self.df.drop('Date', inplace=True, axis=1)
            self.df.drop('Time', inplace=True, axis=1)
            self.df = self.df[self.df["Ticker"].apply(lambda a: a[0:len(self.ticker)]==self.ticker)]


    def get_ticker_call_data(self):
        try:
            ticker_calls = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-2:] == "CE")]
            if ticker_calls.empty:
                # Because of data issue
                ticker_calls = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "CE")]
            return ticker_calls
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None

    def get_ticker_put_data(self):
        try:
            ticker_puts = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-2:] == "PE")]
            if ticker_puts.empty:
                # Because of data issue
                ticker_puts = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "PE")]
            return ticker_puts
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None
    def get_futures_data(self):
        try:
            ticker_fut = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-2:] == "-I")]
            if ticker_fut.empty:
                # Because of data issue
                ticker_fut = self.df[self.df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "-I")]
            return ticker_fut
        except KeyError as e:
            print(self.ticker+"'s future's data unavailable")
            return None
        except Exception as e:
            print("Error : {}".format(e))
            return None








