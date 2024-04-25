import pandas as pd 
import numpy as np 
from Performance.Backtesting_metrics import Backtesting_metrics


class runner(Backtesting_metrics):


    def __init__(self, initial_capital: int, risk_free_rate: float = 5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tradelog = self.tradelog
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.tradelog['Equity'] = 0  #Equity is capital plus pnl
        self.tradelog['Rate Of Return'] = 0

        for i in range(len(self.tradelog)):
            if i == 0:
                self.tradelog.loc[i, 'Equity'] = int(self.initial_capital + self.tradelog.loc[i, 'PnL Including Slippage'])
                self.tradelog.loc[i, 'Rate Of Return'] = round(self.tradelog.loc[
                                                              i, 'PnL Including Slippage'] / self.initial_capital*100 ,2)
            else:
                self.tradelog.loc[i, 'Equity'] = int(
                    self.tradelog.loc[i - 1, 'Equity'] + self.tradelog.loc[i, 'PnL Including Slippage'])
                self.tradelog.loc[i, 'Rate Of Return'] = (self.tradelog.loc[i, 'PnL Including Slippage'] /
                                                          self.tradelog.loc[i - 1, 'Equity']) * 100
    def sharpe_ratio(self):
        self.avg_ror = self.tradelog['Rate Of Return'].mean() * len(self.tradelog) - self.risk_free_rate
        sigma = self.tradelog['Rate Of Return'].std() * np.sqrt(len(self.tradelog))
        sharpe_ratio = self.avg_ror / sigma
        return (round(sharpe_ratio, 2))
    def sortino_ratio(self):
        self.sharpe_ratio()
        downside_sigma = self.tradelog[self.tradelog['Rate Of Return'] < 0]['Rate Of Return'].std() * np.sqrt(len(self.tradelog))
        sortino_ratio = self.avg_ror / downside_sigma
        return(round(sortino_ratio, 2))

    def max_drawdown(self):
        self.tradelog['Drawdown'] = self.tradelog['PnL Including Slippage Cumulative Sum'] - self.tradelog[
            'PnL Including Slippage Cumulative Sum'].cummax()
        max_drawdown = self.tradelog['Drawdown'].min()
        max_drawdown_percent = (max_drawdown /
                                self.tradelog[self.tradelog['Drawdown'] == self.tradelog['Drawdown'].min()]['Equity'].iloc[0]) * 100

        return (round(max_drawdown, 2),
                round(max_drawdown_percent, 2))

    def CAGR(self):
        number_of_trading_days_for_this_backtest = (
                    self.tradelog.iloc[-1]['Entry Time'].date() - self.tradelog.iloc[0]['Entry Time'].date()).days
        number_of_trading_days_for_this_backtest = int(number_of_trading_days_for_this_backtest)
        cagr = (((self.tradelog.iloc[-1]['Equity'] / self.initial_capital) ** (
                    1 / (number_of_trading_days_for_this_backtest / 365))) - 1) * 100
        return round(cagr, 2)

    def report(self):
        report = pd.DataFrame()

        report["Metrics"] = ["Total Trades", "Profitable Trades", "Loss-Making Trades", "Win Rate",
                             "Avg Profit per Trade",
                             "Avg Loss per Trade", "Risk Reward Ratio",
                             "Sharpe Ratio",
                             "Sortino Ratio", "Max Drawdown", "Max Drawdown Percentage", "CAGR",]

        report["Values"] = [
            len(self.tradelog),
            self.win_rate()[0],
            self.win_rate()[1],
            self.win_rate()[2],
            self.avg_pnl_per_trade()[0],
            self.avg_pnl_per_trade()[1],
            self.ris_reward(),
            self.sharpe_ratio(),
            self.sortino_ratio(),
            self.max_drawdown()[0],
            self.max_drawdown()[1],
            self.CAGR()
        ]

        return report




        
        
        