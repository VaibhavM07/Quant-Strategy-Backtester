from Data_env.Data_cleaning import data_cleaning
from Data_env.get_expiry import get_expiry
data = data_cleaning(path=r"/Users/vaibhavmishra/Documents/GitHub/Backtesting/Sample data",ticker="RELIANCE")
# print(data.get_futures_data())
exp = get_expiry(df=data.get_ticker())
print(exp.monthly())
# print(data.get_option_put_data())