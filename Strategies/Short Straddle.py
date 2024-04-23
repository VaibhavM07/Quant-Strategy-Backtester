from Data_env.Data_cleaning import data_cleaning
from Data_env.get_expiry import get_expiry
from Data_env.Strike_selection import Strike_selection

path=r"/Users/vaibhavmishra/Documents/GitHub/Backtesting/Sample data"
ticker="RELIANCE"
# data = data_cleaning(path=path,ticker=ticker)
# df = data.get_futures_data()
# print(data.get_futures_data())
exp = get_expiry(path=path,ticker=ticker)
strike  = Strike_selection(Moneyness=-100,path=path,ticker=ticker)
print(strike.custom_strike())
# print(exp.weekly())
# # print(data.get_option_put_data())