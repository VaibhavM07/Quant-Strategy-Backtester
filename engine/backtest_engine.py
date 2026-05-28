"""
Generic options backtest engine.

All trade details come from the strategy config — no strategy-specific logic here.

LEGS format:
    LEGS = [
        {"option_type": "CE", "strike_offset": 0,   "side": -1},
        {"option_type": "PE", "strike_offset": 0,   "side": -1},
        {"option_type": "CE", "strike_delta": 0.10, "side":  1},
    ]

QUANTITY and STOP_LOSS accept either a fixed value or a callable:

    QUANTITY   = 25                          # fixed
    QUANTITY   = lambda net_prem: int(10_000 / (abs(net_prem) * 0.20))  # dynamic

    STOP_LOSS  = 1.20                        # multiplier — exit at 20% loss of premium
    STOP_LOSS  = lambda net_prem: 5_000.0   # fixed rupee loss limit per lot
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from Data_env.Data_cleaning import data_cleaning
from Data_env.Data_cleaning import _leg_col_key
from Performance.runner_and_ratios import runner


def _resolve(val, *args):
    """Call val with args if callable, else return val as-is."""
    return val(*args) if callable(val) else val


class BacktestEngine:

    def __init__(self,
                 path: str,
                 ticker: str,
                 legs: list,
                 entry_time: str,
                 exit_time: str,
                 quantity,
                 stop_loss_multiplier,
                 initial_capital: int,
                 strike_rounding: int = 100,
                 csv_ticker: str = None,
                 expiry_type: str = "CURRENT_WEEK"):
        self.path                 = path
        self.ticker               = ticker
        self.csv_ticker           = csv_ticker or ticker
        self.legs                 = legs
        self.entry_time           = entry_time
        self.exit_time            = exit_time
        self.quantity             = quantity             # int or callable(net_premium) -> int
        self.stop_loss_multiplier = stop_loss_multiplier # float or callable(net_premium) -> float rupee limit
        self.initial_capital      = initial_capital
        self.strike_rounding      = strike_rounding
        self.expiry_type          = expiry_type

    def run(self) -> pd.DataFrame:
        qty_label = "dynamic" if callable(self.quantity) else str(self.quantity)
        sl_label  = "dynamic" if callable(self.stop_loss_multiplier) else f"{self.stop_loss_multiplier}x"
        sides = " / ".join(
            f"{'SELL' if l['side'] == -1 else 'BUY'} "
            f"{l['option_type']}({l.get('strike_offset', 0):+d})"
            for l in self.legs
        )
        print(f"\n[Backtest] {self.ticker}  {sides}")
        print(f"           {self.entry_time} → {self.exit_time}  "
              f"SL: {sl_label}  Qty: {qty_label}\n")

        dc = data_cleaning(
            expiry_type=self.expiry_type,
            path=self.path,
            ticker=self.csv_ticker,
            legs=self.legs,
            strike_rounding=self.strike_rounding,
        )
        trade_universe, _ = dc.get_filtered_data()

        if trade_universe.empty:
            raise RuntimeError("No data loaded — check DATA_PATH and TICKER settings.")

        dates_str = trade_universe["Timestamp"].dt.date.astype(str)
        trade_universe = trade_universe[
            trade_universe["Timestamp"] >= pd.to_datetime(dates_str + " " + self.entry_time)
        ]
        trade_universe = trade_universe[
            trade_universe["Timestamp"] < pd.to_datetime(
                trade_universe["Timestamp"].dt.date.astype(str) + " " + self.exit_time
            )
        ].copy()

        tradelog = self._run_strategy(trade_universe)

        # Resolve quantity for performance reporting (use first-day net premium as estimate)
        report_qty = self.quantity
        if callable(report_qty):
            # Use a representative quantity — the median across days
            import statistics
            day_quantities = tradelog.get("_resolved_qty", pd.Series([25]))
            report_qty = int(statistics.median(day_quantities.dropna()))

        perf = runner(
            initial_capital=self.initial_capital,
            risk_free_rate=1,
            tradelog=tradelog.drop(columns=["_resolved_qty"], errors="ignore"),
            quantity=report_qty,
        )
        return perf.report()

    def _run_strategy(self, trade_universe: pd.DataFrame) -> pd.DataFrame:
        df = trade_universe.copy()
        df['_date'] = df['Timestamp'].dt.date
        records = []

        for _, day in df.groupby('_date'):
            day = day.reset_index(drop=True)
            entry_row = day.iloc[0]

            entry_prices = {
                _leg_col_key(leg): entry_row[f"{_leg_col_key(leg)}_Open"]
                for leg in self.legs
            }

            net_premium = sum(
                (-leg["side"]) * entry_prices[_leg_col_key(leg)]
                for leg in self.legs
            )

            # Resolve quantity and SL — supports plain values or callables
            qty = _resolve(self.quantity, net_premium)
            sl_raw = _resolve(self.stop_loss_multiplier, net_premium)

            # sl_raw: if > 2 treat as rupee limit, else treat as multiplier
            if callable(self.stop_loss_multiplier):
                sl_per_unit = sl_raw / max(qty, 1)   # callable returns total rupee limit
            else:
                sl_per_unit = abs(net_premium) * (sl_raw - 1)

            pnl_series = sum(
                (-leg["side"]) * (
                    entry_prices[_leg_col_key(leg)]
                    - day[f"{_leg_col_key(leg)}_Open"]
                )
                for leg in self.legs
            )
            sl_rows = day[pnl_series < -sl_per_unit]

            exit_row = sl_rows.iloc[0] if not sl_rows.empty else day.iloc[-1]
            sl_exit  = 1 if not sl_rows.empty else 0

            for leg in self.legs:
                key = _leg_col_key(leg)
                records.append({
                    'Ticker':          entry_row[f'{key}_Ticker'],
                    'Side':            leg["side"],
                    'Strike Offset':   leg.get("strike_offset", 0),
                    'Entry Time':      entry_row['Timestamp'],
                    'Entry Price':     entry_prices[key],
                    'Stop Loss Exit':  sl_exit,
                    'Exit Time':       exit_row['Timestamp'],
                    'Exit Price':      exit_row[f'{key}_Open'],
                    '_resolved_qty':   qty,
                })

        return pd.DataFrame(records)
