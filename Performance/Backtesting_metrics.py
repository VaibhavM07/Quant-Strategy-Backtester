import pandas as pd
import numpy as np

class Backtesting_metrics():

    def __init__(self, quantity, tradelog: pd.DataFrame,slippage:float = 0.001):
        self.tradelog = tradelog
        self.quantity = quantity
        self.slippage = slippage
        self.tradelog['Entry Including Slippage'] = self.tradelog['Entry Price'] - (self.tradelog['Entry Price'] * self.slippage)
        self.tradelog['Exit Including Slippage'] = self.tradelog['Exit Price'] + (self.tradelog['Exit Price'] * self.slippage)
        self.tradelog['PnL Including Slippage'] = self.quantity* (self.tradelog['Entry Including Slippage'] - self.tradelog['Exit Including Slippage']) - 100
        self.tradelog['PnL Including Slippage Cumulative Sum'] = self.tradelog['PnL Including Slippage'].cumsum()


    def PnL(self):
        self.tradelog['PnL'] = self.lot_size * (self.tradelog['Entry Price'] - self.tradelog['Exit Price'])
        self.tradelog['PnL Cumulative Sum'] = self.tradelog['PnL'].cumsum()
        return self.tradelog

    def win_rate(self):
        self.profitable_trades = len(self.tradelog[self.tradelog['PnL Including Slippage'] > 0])
        self.lossmaking_trades = len(self.tradelog) - self.profitable_trades
        self.win_ratee = self.profitable_trades / len(self.tradelog)

        return self.profitable_trades,self.lossmaking_trades,round(self.win_ratee, 2)

    def avg_pnl_per_trade(self):
        self.avg_profit = self.tradelog[self.tradelog['PnL Including Slippage'] > 0]['PnL Including Slippage'].mean()
        self.avg_loss = self.tradelog[self.tradelog['PnL Including Slippage'] < 0]['PnL Including Slippage'].mean()

        return (round(self.avg_profit, 2),
                round(self.avg_loss, 2))

    def ris_reward(self):
        self.avg_pnl_per_trade()
        self.risk_reward = abs(self.avg_profit / self.avg_loss)
        return (round(self.risk_reward, 2))
