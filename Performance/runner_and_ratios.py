import pandas as pd
import numpy as np
from Performance.Backtesting_metrics import Backtesting_metrics


class runner(Backtesting_metrics):

    def __init__(self, initial_capital: int, risk_free_rate: float = 5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tradelog = self.tradelog.dropna().reset_index(drop=True)
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate

        # ── Vectorized equity curve (was O(n) row-by-row loc loop) ────────
        pnl = self.tradelog['PnL Including Slippage']
        self.tradelog['Equity'] = (self.initial_capital + pnl.cumsum()).astype(int)

        # RoR_i = PnL_i / Equity_{i-1}; first trade divides by initial_capital
        prev_equity = self.tradelog['Equity'].shift(1).fillna(self.initial_capital)
        self.tradelog['Rate Of Return'] = (pnl / prev_equity * 100).round(2)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _trades_per_year(self) -> float:
        """Annualisation factor based on actual backtest length."""
        n_days = (
            self.tradelog.iloc[-1]['Entry Time'].date()
            - self.tradelog.iloc[0]['Entry Time'].date()
        ).days
        n_years = n_days / 365 if n_days > 0 else 1.0
        return len(self.tradelog) / n_years

    # ── Ratios ────────────────────────────────────────────────────────────

    def sharpe_ratio(self) -> float:
        tpy = self._trades_per_year()
        mean_r = self.tradelog['Rate Of Return'].mean()
        std_r  = self.tradelog['Rate Of Return'].std()

        annualised_return = mean_r * tpy
        annualised_std    = std_r  * np.sqrt(tpy)

        # Store for reuse in sortino
        self.avg_ror = annualised_return - self.risk_free_rate

        if annualised_std == 0:
            return 0.0
        return round(self.avg_ror / annualised_std, 2)

    def sortino_ratio(self) -> float:
        self.sharpe_ratio()          # sets self.avg_ror
        tpy = self._trades_per_year()
        downside_std = (
            self.tradelog[self.tradelog['Rate Of Return'] < 0]['Rate Of Return'].std()
            * np.sqrt(tpy)
        )
        if downside_std == 0:
            return 0.0
        return round(self.avg_ror / downside_std, 2)

    def max_drawdown(self):
        self.tradelog['Drawdown'] = (
            self.tradelog['PnL Including Slippage Cumulative Sum']
            - self.tradelog['PnL Including Slippage Cumulative Sum'].cummax()
        )
        mdd = self.tradelog['Drawdown'].min()
        mdd_row = self.tradelog[self.tradelog['Drawdown'] == mdd]['Equity'].iloc[0]
        mdd_pct = (mdd / mdd_row) * 100 if mdd_row != 0 else 0.0
        return round(mdd, 2), round(mdd_pct, 2)

    def CAGR(self) -> float:
        n_days = (
            self.tradelog.iloc[-1]['Entry Time'].date()
            - self.tradelog.iloc[0]['Entry Time'].date()
        ).days
        if n_days == 0:
            return 0.0
        cagr = (self.tradelog.iloc[-1]['Equity'] / self.initial_capital) ** (365 / n_days) - 1
        return round(cagr * 100, 2)

    # ── Report ────────────────────────────────────────────────────────────

    def report(self) -> pd.DataFrame:
        report = pd.DataFrame()
        report["Metrics"] = [
            "Total Trades", "Profitable Trades", "Loss-Making Trades", "Win Rate",
            "Avg Profit per Trade", "Avg Loss per Trade", "Risk Reward Ratio",
            "Sharpe Ratio", "Sortino Ratio",
            "Max Drawdown", "Max Drawdown %", "CAGR (%)",
        ]
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
            self.CAGR(),
        ]
        return report
