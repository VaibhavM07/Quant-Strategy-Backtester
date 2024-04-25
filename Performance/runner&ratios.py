import pandas as pd 
import numpy as np 
from Performance import Backtesting_metrics
class strat_run(Backtesting_metrics):
    def __init__(self,initial_capital:int,risk_free_rate:float = 5,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        for i in range(len(self.tradlog)):
            if i == 0:
                self.tradlog.loc[:, 'Equity'].iloc[i] = self.initial_capital + self.tradlog['PnL Including Slippage'].iloc[i]
                self.tradlog.loc[:, 'Rate Of Return'].iloc[i] = (self.tradlog['PnL Including Slippage'].iloc[
                                                                 i] / self.initial_capital) * 100
            else:
                self.tradlog.loc[:, 'Equity'].iloc[i] = self.tradlog['Equity'].iloc[i - 1] + \
                                                    self.tradlog['PnL Including Slippage'].iloc[i]
                self.tradlog.loc[:, 'Rate Of Return'].iloc[i] = (self.tradlog['PnL Including Slippage'].iloc[i] /
                                                             self.tradlog['Equity'].iloc[i - 1]) * 100
        
    def sharpe_ratio(self):
        self.avg_ror = self.tradelog['Rate Of Return'].mean() * len(self.tradelog) - self.risk_free_rate
        sigma = self.tradelog['Rate Of Return'].std() * np.sqrt(len(self.tradelog))
        sharpe_ratio = self.avg_ror / sigma
        return ("Sharpe Ratio:", round(sharpe_ratio, 2))
    def sortino_ratio(self):
        self.sharpe_ratio()
        downside_sigma = self.tradelog[self.tradelog['Rate Of Return'] < 0]['Rate Of Return'].std() * np.sqrt(len(self.tradelog))
        sortino_ratio = self.avg_ror / downside_sigma

        print("Sortino Ratio:", round(sortino_ratio, 2))




        
        
        