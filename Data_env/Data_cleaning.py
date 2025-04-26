import pandas as pd
import string
import glob
import warnings
warnings.filterwarnings('ignore')
from Data_env.Get_expiry import get_expiry
from Data_env.Strike_selection import Strike_selection
import tqdm


class data_cleaning():

    def __init__(self,expiry_type,path:string,ticker:string,custom_strikes:list[int] = None):
        self.path = path
        self.ticker = ticker
        self.expiry_type = expiry_type
        self.custom_strikes = custom_strikes
        self.filtered_call = pd.DataFrame()
        self.filtered_put = pd.DataFrame()
        self.trade_uni= pd.DataFrame()
        self.futures=  pd.DataFrame()

    def data_load(self,file) -> pd.DataFrame:

        local_df = pd.read_csv(file)
        if local_df.empty:
            print("No Data found in "+self.path)
        else:
            local_df.insert(0, "Timestamp", local_df["Date"] + " " + local_df["Time"])
            local_df["Timestamp"] = pd.to_datetime(local_df["Timestamp"], format="%d/%m/%Y %H:%M:%S")
            local_df = local_df.sort_values(by="Timestamp")
            local_df["Ticker"] = local_df["Ticker"].apply(str)
            local_df.drop('Date', inplace=True, axis=1)
            local_df.drop('Time', inplace=True, axis=1)
            local_df = local_df[local_df["Ticker"].apply(lambda a: a[0:len(self.ticker)]==self.ticker)]
            if self.expiry_type == "CURRENT_WEEK":
                expiry = get_expiry(futures=self.get_futures_data(local_df=local_df)).current_weekly()
            elif self.expiry_type == "MONTHLY":
                expiry = get_expiry(futures=self.get_futures_data(local_df=local_df)).monthly()
            else:
                raise Exception(f"{self.expiry_type} does not exist")

            future = self.get_futures_data(local_df=local_df)
            calls = self.get_ticker_call_data(local_df=local_df)
            puts = self.get_ticker_put_data(local_df = local_df)
            if self.custom_strikes:

                calls = Strike_selection(call_put="CALL",futures=future,calls=calls,puts=puts,target_strikes=self.custom_strikes).custom_strike()[0]
                puts = Strike_selection(call_put="PUT", futures=future, calls=calls, puts=puts,
                                         target_strikes=self.custom_strikes).custom_strike()[1]
            else:
                calls = Strike_selection(call_put="CALL", futures=future, calls=calls, puts=puts,
                                         target_strikes=self.custom_strikes).get_ATM_strike()
                puts = Strike_selection(call_put="PUT", futures=future, calls=calls, puts=puts,
                                        target_strikes=self.custom_strikes).get_ATM_strike()
            for i in range(len(expiry)):
                calls = pd.concat([self.filtered_call, calls[calls["Ticker"].apply(
                    lambda a: a.strip()[:len(self.ticker) + len(expiry[i])] == str(
                        self.ticker + expiry[i]))]])
                calls = calls.sort_values(by=["Timestamp"], ascending=True)
                calls.columns = ["Timestamp", "CE_Ticker", "CE_Open", "CE_High", "CE_Low", "CE_Close","CE_Volume","CE_Open_Interest"]

                puts = pd.concat([self.filtered_put, puts[puts["Ticker"].apply(
                    lambda a: a.strip()[:len(self.ticker) + len(expiry[i])] == str(
                        self.ticker + expiry[i]))]])
                puts = puts.sort_values(by=["Timestamp"], ascending=True)
                puts.columns = ["Timestamp", "PE_Ticker", "PE_Open", "PE_High", "PE_Low", "PE_Close","PE_Volume","PE_Open_Interest"]
        trade_universe = pd.merge(calls, puts, on="Timestamp")

        return trade_universe,future
    def get_ticker_call_data(self,local_df):
        try:
            ticker_calls = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "CE")]
            if ticker_calls.empty:
                # Because of data issue
                ticker_calls = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "CE")]
            return ticker_calls
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None

    def get_ticker_put_data(self,local_df):
        try:
            ticker_puts = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "PE")]
            if ticker_puts.empty:
                # Because of data issue
                ticker_puts = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "PE")]
            return ticker_puts
        except KeyError as e:
            print(self.ticker+"'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None
    def get_futures_data(self,local_df):
        try:
            ticker_fut = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "-I")]
            if ticker_fut.empty:
                # Because of data issue
                ticker_fut = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "-I")]
            return ticker_fut
        except KeyError as e:
            print(self.ticker+"'s future's data unavailable")
            return None
        except Exception as e:
            print("Error : {}".format(e))
            return None

    def get_filtered_data(self):
        print("TRADE UNIVERSE CREATED")
        folder = glob.glob(self.path)
        for file in folder:
            files = glob.glob(file + "/*.csv")
        for file in tqdm.tqdm(files):
            self.trade_uni = pd.concat([self.trade_uni,self.data_load(file=file)[0]])
            self.futures  = pd.concat([self.futures,self.data_load(file=file)[1]])
            if self.trade_uni.empty or self.futures.empty:
                print(f"Skipping file {file} because it's empty.")
        return self.trade_uni,self.futures







