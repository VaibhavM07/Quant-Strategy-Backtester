"""
NIFTY Short Straddle  — see runners/README.md for parameter docs
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODE            = "backtest"        # "backtest" | "live"

TICKER          = "NIFTY"
EXPIRY_TYPE     = "MONTHLY"         # backtest only: "CURRENT_WEEK" | "MONTHLY"
CSV_TICKER      = None
STRIKE_ROUNDING = 50

LEGS = [
    {"option_type": "CE", "strike_delta":  0.25, "side": -1},
    {"option_type": "PE", "strike_delta": -0.25, "side": -1},
]

ENTRY_TIME      = "09:30:00"
EXIT_TIME       = "15:15:00"
QUANTITY        = 50
STOP_LOSS       = 1.20
TAKE_PROFIT     = 0.50   # capture 50% of premium; None = no target

DATA_PATH       = r"/Users/vaibhavmishra/NSE Data/ALL NSE DATA/NSE F&O year 20112015&2019-2020/NSE F&O"
INITIAL_CAPITAL = 100_000

UNDERLYING      = "NSE:NIFTY50-INDEX"
EXPIRY_DATE     = None
EXPIRY_TERM     = None

# ──────────────────────────────────────────────────────────────────────

if MODE == "backtest":
    from engine.backtest_engine import BacktestEngine
    engine = BacktestEngine(
        path=DATA_PATH, ticker=TICKER, csv_ticker=CSV_TICKER,
        legs=LEGS, entry_time=ENTRY_TIME, exit_time=EXIT_TIME,
        quantity=QUANTITY, stop_loss_multiplier=STOP_LOSS,
        initial_capital=INITIAL_CAPITAL, strike_rounding=STRIKE_ROUNDING,
        expiry_type=EXPIRY_TYPE,
    )
    print("\n" + engine.run().to_string(index=False))

elif MODE == "live":
    from engine.live_engine import LiveEngine
    LiveEngine(
        underlying=UNDERLYING, legs=LEGS,
        entry_time=ENTRY_TIME, exit_time=EXIT_TIME,
        quantity=QUANTITY, stop_loss_multiplier=STOP_LOSS,
        take_profit=TAKE_PROFIT,
        strike_rounding=STRIKE_ROUNDING,
        expiry_date=EXPIRY_DATE, expiry_term=EXPIRY_TERM,
    ).run()

else:
    raise ValueError(f"Unknown MODE '{MODE}'.")
