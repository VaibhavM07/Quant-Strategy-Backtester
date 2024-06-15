# from Data_env.Data_cleaning import data_cleaning
# from Data_env.get_expiry import get_expiry
# from Data_env.Strike_selection import Strike_selection
# from Technical_analysis_module.Indicators import Indicators
# from Technical_analysis_module.CandleStick_patterns import CandleSticks
# from Technical_analysis_module.Trends_Levels import Trends_Levels
from Performance.Backtesting_metrics import Backtesting_metrics
from Performance.runner_and_ratios import runner
import pandas as pd
import numpy as np
path=r"/Users/vaibhavmishra/Documents/GitHub/Backtesting/Sample data"
ticker="BANKNIFTY"


tradelog = pd.DataFrame(columns=['Ticker', 'Entry Time', 'Entry Price', 'Stop Loss Exit', 'Exit Time', 'Exit Price'])

# Generate random data
num_rows = 10
tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'FB']
entry_times = pd.date_range(start='2024-01-01', periods=num_rows, freq='D')
entry_prices = np.random.uniform(100, 500, num_rows)
stop_loss_exits = np.random.uniform(80, 150, num_rows)
exit_times = pd.date_range(start='2024-01-01', periods=num_rows, freq='D')
exit_prices = np.random.uniform(100, 500, num_rows)

# Fill DataFrame with random data
tradelog['Ticker'] = np.random.choice(tickers, num_rows)
tradelog['Entry Time'] = entry_times
tradelog['Entry Price'] = entry_prices
tradelog['Stop Loss Exit'] = stop_loss_exits
tradelog['Exit Time'] = exit_times
tradelog['Exit Price'] = exit_prices
print(tradelog)
# data = data_cleaning(path=path,ticker=ticker)
# print(data.get_futures_data())
# print(data.get_futures_data())
# exp = get_expiry(path=path,ticker=ticker)
# print(exp.weekly())
# strike  = Strike_selection(Moneyness=-100,path=path,ticker=ticker)
# print(strike.custom_strike())

ind = runner(tradelog=tradelog,initial_capital=10000,risk_free_rate=5,quantity=100)

# ind.tradelog = ind.tradelog

# print(ind.T(call_put="CALL"))
print(ind.report())
# print(ind.levels())
# print(exp.weekly())
# # print(data.get_option_put_data())