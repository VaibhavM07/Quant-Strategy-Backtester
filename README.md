# Options Backtesting & Live Trading Framework

A generic, config-driven framework for backtesting and live trading Indian index options (BANKNIFTY, NIFTY) via Fyers API.

---

## Quick Start

```bash
# 1. Set your data path and parameters in a runner file
# 2. Run it
python strategies/banknifty_short_straddle.py
```

Switch `MODE = "backtest"` to `MODE = "live"` in the runner to go live.

---

## Project Structure

```
strategies/                    ← Strategy configs — one file per strategy
engine/
    backtest_engine.py      ← Generic backtest engine (runs any LEGS config)
    live_engine.py          ← Generic live engine (Fyers orders, WS monitoring, SL)
Live_trade_engine/
    config.py               ← Fyers API credentials (CLIENT_ID, SECRET_KEY only)
    Login_module.py         ← OAuth login + token caching
    symbol_module.py        ← Resolves option symbols from legs config
    execute_trade_module.py ← Places orders via Fyers (basket + single fallback)
    Get_postion_module.py   ← Fetches open positions from Fyers
Data_env/
    Data_cleaning.py        ← Loads and merges raw CSV data into trade universe
    Strike_selection.py     ← Selects strikes by offset / % of spot / delta
    Get_expiry.py           ← Parses expiry strings from CSV ticker names
models/
    black_scholes.py        ← BS pricing, greeks (delta/gamma/vega/theta/rho), IV solver
Performance/
    Backtesting_metrics.py  ← P&L, slippage, per-trade metrics
    runner_and_ratios.py    ← Sharpe, max drawdown, win rate, full report
    Plots.py                ← Equity curve and drawdown charts
Sample data/                ← Sample CSVs for testing (Jan 2019 BANKNIFTY)
```

---

## How It Works

### Backtest Flow

```
Strategy file (LEGS, timing, SL, data path)
    → BacktestEngine
        → Data_cleaning  (loads CSVs, selects strikes, merges legs by timestamp)
        → _run_strategy  (vectorised: entry at ENTRY_TIME, SL check each candle, exit)
        → runner_and_ratios  (Sharpe, CAGR, max DD, win rate, full report)
```

**Data format**: 1-minute OHLCV CSVs from Globaldatafeeds. Folder structure expected:
```
NSE F&O/
    2019/
        01/
            GFDLNFO_01012019.csv
            ...
        02/
        ...
    2020/
    ...
```
The engine walks all nested folders recursively. Point `DATA_PATH` at the root year folder or the parent of all years.

**Caching**: On first run the engine processes all CSVs and saves a parquet cache. Subsequent runs load the parquet directly (10–20× faster). Delete the `.parquet` files to force a rebuild.

### Live Flow

```
Strategy file (LEGS, timing, SL, underlying, expiry)
    → LiveEngine
        → Login_module   (OAuth, token cached to JSON)
        → symbol_module  (resolves live option symbols from LEGS config)
        → _OptionRunner
            → enter_position  (basket order via Fyers)
            → WebSocket       (streams LTP for all legs)
            → _check_exit     (SL or time exit → basket close)
```

---

## Data Requirements

- Raw CSVs from Globaldatafeeds (or compatible format)
- Columns: `Date, Time, Ticker, Open, High, Low, Close, Volume, Open Interest`
- Date formats supported: `DD/MM/YYYY` (newer) and `DD-MM-YY` (older files)
- Futures rows identified by ticker ending in `-I` (e.g. `BANKNIFTY-I`)
- Options rows identified by ticker ending in `CE` or `PE`

---

## Adding a New Strategy

1. Copy any file from `strategies/`
2. Rename it (e.g. `strategies/banknifty_iron_condor.py`)
3. Edit `LEGS`, `ENTRY_TIME`, `EXIT_TIME`, `STOP_LOSS`, `QUANTITY`
4. Run it

See `strategies/README.md` for full documentation of all parameters.

---

## Credentials Setup (Live Only)

Edit `Live_trade_engine/config.py`:

```python
CLIENT_ID  = "YOUR_APP_ID"      # e.g. "EGD02YUYIM-100"
SECRET_KEY = "YOUR_SECRET_KEY"
```

On first run you will be prompted to complete OAuth in a browser. The access token is cached in `access_token.json` and reused until it expires.

---

## Dependencies

```bash
pip install pandas pyarrow fyers-apiv3 holidays scipy numpy
```
