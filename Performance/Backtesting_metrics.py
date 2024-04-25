import pandas as pd
import numpy as np

class Backtesting_metrics():

    def __init__(self,lot_size,tradelog :pd.DataFrame):
        self.tradelog = tradelog
        self.lot_size = lot_size

    def PnL(self):
        self.tradelog['PnL'] = self.lot_size * (self.tradelog['Entry Price'] - self.tradelog['Exit Price'])
        self.tradelog['PnL Cumulative Sum'] = self.tradelog['PnL'].cumsum()
        return self.tradelog

    def PnL_inc_slippage(self):
        #slippage is deducted, as selling at a lower price is a loss
        self.tradlog['Entry Including Slippage'] = self.tradlog['Entry Price'] - (self.tradlog['Entry Price'] * 0.001)
        #slippage is added, as buying at a higher price is a loss
        self.tradlog['Exit Including Slippage'] = self.tradlog['Exit Price'] + (self.tradlog['Exit Price'] * 0.001)

        #pnlaccounting for slippages
        self.tradlog['PnL Including Slippage'] = self.lot_size * (
                    self.tradlog['Entry Including Slippage'] - self.tradlog['Exit Including Slippage']) - 100

        # Adding up the slippage accounted pnl and ploting it
        self.tradlog['PnL Including Slippage Cumulative Sum'] = self.tradlog['PnL Including Slippage'].cumsum()

        return self.tradelog

    def win_rate(self):
        profitable_trades = len(self.tradlog[self.tradlog['PnL Including Slippage'] > 0])
        lossmaking_trades = len(self.tradlog) - profitable_trades
        win_rate = profitable_trades / len(self.tradlog)

        print("Number of Profitable Trades:", profitable_trades)
        print("Number of Loss-Making Trades:", lossmaking_trades)
        print("Win Rate:", round(win_rate, 2))




