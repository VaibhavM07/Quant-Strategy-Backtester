import pandas as pd
import numpy as np


class Backtesting_metrics():

    def __init__(self, quantity, tradelog: pd.DataFrame, slippage: float = 0.001):
        self.tradelog = tradelog
        self.quantity = quantity
        self.slippage = slippage

        # Side: -1 = short (sell), 1 = long (buy). Defaults to -1 for backward compat.
        side = self.tradelog.get('Side', pd.Series(-1, index=self.tradelog.index))

        entry = self.tradelog['Entry Price']
        exit_ = self.tradelog['Exit Price']

        # Slippage is adverse in both directions:
        #   sell (short): receive less on entry, pay more on exit (buy back)
        #   buy  (long):  pay more on entry, receive less on exit (sell)
        entry_slip = np.where(side == -1, entry * (1 - slippage), entry * (1 + slippage))
        exit_slip  = np.where(side == -1, exit_ * (1 + slippage), exit_ * (1 - slippage))

        self.tradelog['Entry Including Slippage'] = entry_slip
        self.tradelog['Exit Including Slippage']  = exit_slip

        # Direction-aware P&L: (-side) * (entry_slip - exit_slip)
        #   short (side=-1): entry_slip - exit_slip  → profit when exit < entry
        #   long  (side= 1): exit_slip - entry_slip  → profit when exit > entry
        self.tradelog['PnL Including Slippage'] = (
            self.quantity * (-side) * (entry_slip - exit_slip) - 100
        )
        self.tradelog['PnL Including Slippage Cumulative Sum'] = (
            self.tradelog['PnL Including Slippage'].cumsum()
        )

    def PnL(self):
        side = self.tradelog.get('Side', pd.Series(-1, index=self.tradelog.index))
        self.tradelog['PnL'] = (
            self.quantity * (-side) *
            (self.tradelog['Entry Price'] - self.tradelog['Exit Price'])
        )
        self.tradelog['PnL Cumulative Sum'] = self.tradelog['PnL'].cumsum()
        return self.tradelog

    def win_rate(self):
        self.profitable_trades = len(self.tradelog[self.tradelog['PnL Including Slippage'] > 0])
        self.lossmaking_trades = len(self.tradelog) - self.profitable_trades
        self.win_ratee = self.profitable_trades / len(self.tradelog)
        return self.profitable_trades, self.lossmaking_trades, round(self.win_ratee, 2)

    def avg_pnl_per_trade(self):
        self.avg_profit = self.tradelog[self.tradelog['PnL Including Slippage'] > 0]['PnL Including Slippage'].mean()
        self.avg_loss   = self.tradelog[self.tradelog['PnL Including Slippage'] < 0]['PnL Including Slippage'].mean()
        return round(self.avg_profit, 2), round(self.avg_loss, 2)

    def ris_reward(self):
        self.avg_pnl_per_trade()
        self.risk_reward = abs(self.avg_profit / self.avg_loss)
        return round(self.risk_reward, 2)
