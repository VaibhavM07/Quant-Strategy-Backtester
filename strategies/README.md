# Runners — Strategy Configuration Guide

Each file in this folder is a complete strategy. To create a new strategy, copy any runner and change the parameters. No engine code needs to be touched.

---

## MODE

```python
MODE = "backtest"   # or "live"
```

Switching to `"live"` uses the same LEGS definition to place real orders via Fyers.

---

## LEGS — Defining the Trade

Each leg is a dict with three keys:

| Key | Description |
|-----|-------------|
| `option_type` | `"CE"` or `"PE"` |
| `side` | `-1` = sell, `1` = buy |
| strike selector | one of the three methods below |

### Strike Selection Methods

**1. `strike_offset` (int) — points from ATM**

```python
{"option_type": "CE", "strike_offset":    0, "side": -1}  # ATM
{"option_type": "CE", "strike_offset":  200, "side": -1}  # ATM + 200
{"option_type": "PE", "strike_offset": -200, "side":  1}  # ATM - 200
```

**2. `strike_pct` (float) — percentage of spot price**

```python
{"option_type": "CE", "strike_pct": 1.02, "side": -1}  # 2% OTM call
{"option_type": "PE", "strike_pct": 0.98, "side": -1}  # 2% OTM put
{"option_type": "CE", "strike_pct": 1.00, "side": -1}  # ATM
```

**3. `strike_delta` (float) — closest Black-Scholes delta**

```python
{"option_type": "CE", "strike_delta":  0.50, "side": -1}  # ATM call (delta 0.5)
{"option_type": "CE", "strike_delta":  0.25, "side": -1}  # 25-delta call
{"option_type": "PE", "strike_delta": -0.25, "side": -1}  # 25-delta put
{"option_type": "PE", "strike_delta": -0.50, "side": -1}  # ATM put
```

CE delta range: 0.0 → 1.0 (higher = deeper ITM)
PE delta range: −1.0 → 0.0 (more negative = deeper ITM)

### Strategy Examples

```python
# Short straddle — sell ATM CE + PE
LEGS = [
    {"option_type": "CE", "strike_offset": 0, "side": -1},
    {"option_type": "PE", "strike_offset": 0, "side": -1},
]

# Short strangle — sell OTM CE + PE by delta
LEGS = [
    {"option_type": "CE", "strike_delta":  0.25, "side": -1},
    {"option_type": "PE", "strike_delta": -0.25, "side": -1},
]

# Bull put spread — credit spread, bullish
LEGS = [
    {"option_type": "PE", "strike_offset":  200, "side": -1},  # sell ITM PE
    {"option_type": "PE", "strike_offset": -200, "side":  1},  # buy OTM PE
]

# Iron condor — sell inner, buy outer
LEGS = [
    {"option_type": "CE", "strike_delta":  0.25, "side": -1},
    {"option_type": "PE", "strike_delta": -0.25, "side": -1},
    {"option_type": "CE", "strike_delta":  0.10, "side":  1},
    {"option_type": "PE", "strike_delta": -0.10, "side":  1},
]
```

---

## Expiry (Live Only)

Use **one** of the two parameters (leave the other as `None`). If both are `None`, defaults to the next weekly expiry.

### `EXPIRY_DATE` — exact date

```python
EXPIRY_DATE = "2025-06-04"   # ISO format YYYY-MM-DD
EXPIRY_TERM = None
```

Takes highest priority. Use when you want to pin a specific contract.

### `EXPIRY_TERM` — term structure

```python
EXPIRY_DATE = None
EXPIRY_TERM = "1W"   # next weekly expiry
```

| Value | Meaning |
|-------|---------|
| `"1W"` | Next weekly expiry (this week's Wednesday for BANKNIFTY, Thursday for NIFTY) |
| `"2W"` | The weekly expiry one week after that |
| `"1M"` | Next monthly expiry (last Thursday of the month) |
| `"2M"` | The monthly expiry one month after that |

> EXPIRY_TERM is evaluated fresh each day at runtime, so the contract rolls automatically.

---

## Expiry Type (Backtest Only)

```python
EXPIRY_TYPE = "CURRENT_WEEK"   # weekly options (BANKNIFTY)
EXPIRY_TYPE = "MONTHLY"        # monthly options (NIFTY pre-2019, or any monthly strategy)
```

---

## STRIKE_ROUNDING

```python
STRIKE_ROUNDING = 100   # BANKNIFTY — strikes in multiples of 100
STRIKE_ROUNDING = 50    # NIFTY     — strikes in multiples of 50
```

Used to round ATM and percentage-based strikes to the nearest valid strike.

---

## Custom Logic — Callables

`QUANTITY`, `STOP_LOSS`, and `TAKE_PROFIT` each accept either a **fixed value or a function**. The engine calls the function at entry time (after resolving live prices) with the relevant context. This lets you implement any logic — dynamic sizing, fixed rupee SL, VIX-based targets — entirely in the strategy file, without touching the engine.

### Callable signatures

```python
# QUANTITY(net_premium) -> int
# net_premium: sum of premium collected/paid across all legs, per lot

# STOP_LOSS(net_premium, quantity) -> float   ← returns rupee loss limit (positive)
# TAKE_PROFIT(net_premium, quantity) -> float  ← returns rupee profit target (positive)
```

### Examples

```python
# Risk-based sizing: risk 1% of capital per trade
CAPITAL = 5_00_000

def QUANTITY(net_premium):
    risk = CAPITAL * 0.01
    return max(1, int(risk / (abs(net_premium) * 0.20)))

STOP_LOSS   = 1.20    # still works as a multiplier alongside a callable QUANTITY
TAKE_PROFIT = 0.50    # still works as a fraction


# Fixed rupee limits — ignore premium size entirely
QUANTITY    = 25
STOP_LOSS   = lambda net_prem, qty: 8_000.0   # always exit at ₹8,000 loss
TAKE_PROFIT = lambda net_prem, qty: 5_000.0   # always target ₹5,000 profit


# No take profit — hold until time exit or SL
TAKE_PROFIT = None
```

The backtest engine uses the same `QUANTITY` and `STOP_LOSS` callables, so you can validate sizing logic historically before going live.

---

## Other Parameters

| Parameter | Description |
|-----------|-------------|
| `TICKER` | Index name as it appears in your CSV files (e.g. `"BANKNIFTY"`) |
| `CSV_TICKER` | Override if your data provider uses a different string. `None` → uses `TICKER` |
| `UNDERLYING` | Fyers symbol for live LTP feed (e.g. `"NSE:BANKNIFTY-INDEX"`) |
| `ENTRY_TIME` | `"HH:MM:SS"` — when to enter each day |
| `EXIT_TIME` | `"HH:MM:SS"` — time exit (also used as daily cutoff) |
| `QUANTITY` | Lots per leg — fixed int or callable `(net_premium) -> int` |
| `STOP_LOSS` | `1.20` = 20% of premium as loss limit, or callable `(net_prem, qty) -> float` (rupees) |
| `TAKE_PROFIT` | `0.50` = capture 50% of premium, callable `(net_prem, qty) -> float`, or `None` |
| `DATA_PATH` | Path to root of CSV data. Point to a single year folder or parent of all years |
| `INITIAL_CAPITAL` | Starting capital for backtest P&L calculations |

---

## Available Runners

| File | Strategy | Direction |
|------|----------|-----------|
| `banknifty_short_straddle.py` | Sell ATM CE + PE | Delta-neutral |
| `nifty_short_straddle.py` | Sell ATM CE + PE (NIFTY) | Delta-neutral |
| `banknifty_bull_put_spread.py` | Sell ITM PE / Buy OTM PE | Bullish credit |
| `banknifty_bear_put_spread.py` | Buy ITM PE / Sell OTM PE | Bearish debit |
| `banknifty_bull_call_spread.py` | Buy ATM CE / Sell OTM CE | Bullish debit |
| `banknifty_bear_call_spread.py` | Sell ITM CE / Buy OTM CE | Bearish credit |
