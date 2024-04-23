from Data_env.Data_loading import data_load
import pandas as pd
import string
import datetime as dt

class data_cleaning():

    def __init__(self,path:string,ticker:string):
        self.path = path
        self.ticker = ticker
    def get_data(self):
        df = data_load(path=self.path)
        if df.empty:
            print("No Data found in "+self.path)
        else:
            df.insert(0, "Timestamp", df["Date"] + " " + df["Time"])
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d/%m/%Y %H:%M:%S")
            df.drop('Date', inplace=True, axis=1)
            df.drop('Time', inplace=True, axis=1)
            return df
    def get_ticker(self):
        df = self.get_data()
        df = df[df["Ticker"].apply(lambda a: a[0:len(self.ticker)]==self.ticker)]
        if df.empty:
            print(self.ticker+" data unavailable")
        else:
            return df

    def get_ticker_call_data(self):
        try:
            df = self.get_ticker()
            ticker_calls = df[df["Ticker"].apply(lambda a: a.strip()[-2:] == "CE")]
            if ticker_calls.empty:
                # Because of data issue
                ticker_calls = df[df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "CE")]
            return ticker_calls
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None

    def get_ticker_put_data(self):
        try:
            df = self.get_ticker()
            ticker_puts = df[df["Ticker"].apply(lambda a: a.strip()[-2:] == "PE")]
            if ticker_puts.empty:
                # Because of data issue
                ticker_puts = df[df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "PE")]
            return ticker_puts
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None
    def get_futures_data(self):
        try:
            df = self.get_ticker()
            ticker_fut = df[df["Ticker"].apply(lambda a: a.strip()[-2:] == "-I")]
            if ticker_fut.empty:
                # Because of data issue
                ticker_fut = df[df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "-I")]
            return ticker_fut
        except KeyError as e:
            print(self.ticker+"'s future's data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None








