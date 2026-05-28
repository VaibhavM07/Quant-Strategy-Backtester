"""
Strike selection for historical (backtest) data.

Supports three methods per leg:

  strike_offset : int    — ATM ± N points   (e.g. 0 = ATM, 200 = ATM+200)
  strike_pct    : float  — spot × pct, rounded  (e.g. 0.98 = 2% OTM put)
  strike_delta  : float  — closest strike to target delta
                           CE delta is positive (e.g. 0.50 = ATM, 0.25 = 25-delta)
                           PE delta is negative (e.g. -0.25 = 25-delta put)

For delta-based selection the module computes implied vol from the ATM
option price (Black-Scholes) and then scans all available strikes.
T (time-to-expiry in years) must be supplied for delta/IV to work.
"""

import re
import math
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models.black_scholes as bs


class Strike_selection:

    def __init__(self, futures: pd.DataFrame, calls: pd.DataFrame,
                 puts: pd.DataFrame, strike_rounding: int = 100,
                 T: float = None, r: float = 0.065):
        """
        Parameters
        ----------
        futures        : DataFrame containing the futures OHLC rows for this file.
        calls / puts   : raw CE / PE rows (all strikes available in the file).
        strike_rounding: nearest-strike interval (100 for BANKNIFTY, 50 for NIFTY).
        T              : time to expiry in years — needed for delta-based selection.
        r              : risk-free rate (default 6.5%).
        """
        self.calls          = calls
        self.puts           = puts
        self.strike_rounding = strike_rounding
        self.T              = T
        self.r              = r

        raw         = futures["Open"].iloc[0]
        self.spot   = float(raw)
        self.atm    = int(round(raw / strike_rounding) * strike_rounding)
        self._iv    = None   # computed lazily from ATM option prices

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_strike_data(self, leg: dict) -> pd.DataFrame:
        """
        Return the DataFrame rows for the leg's target strike.

        leg must contain 'option_type' and exactly one of:
          strike_offset, strike_pct, strike_delta
        """
        opt_type = leg["option_type"]

        if "strike_pct" in leg:
            raw_strike = self.spot * leg["strike_pct"]
            target = int(round(raw_strike / self.strike_rounding) * self.strike_rounding)

        elif "strike_delta" in leg:
            target = self._delta_strike(opt_type, leg["strike_delta"])

        else:
            offset = leg.get("strike_offset", 0)
            target = self.atm + offset

        return self._fetch(opt_type, target)

    # ------------------------------------------------------------------
    # Delta-based strike selection
    # ------------------------------------------------------------------

    def _delta_strike(self, option_type: str, target_delta: float) -> int:
        iv = self._get_iv()
        T  = self.T

        if iv is None or T is None or T <= 0:
            return self.atm   # safe fallback

        strikes = self._available_strikes(option_type)
        if not strikes:
            return self.atm

        best_strike = self.atm
        best_diff   = float("inf")

        for k in strikes:
            try:
                d    = bs.delta(self.spot, k, T, self.r, iv, option_type)
                diff = abs(d - target_delta)
                if diff < best_diff:
                    best_diff   = diff
                    best_strike = k
            except Exception:
                continue

        return best_strike

    def _get_iv(self):
        """Compute ATM implied vol from CE and PE ATM prices (average)."""
        if self._iv is not None:
            return self._iv
        if self.T is None or self.T <= 0:
            return None

        ivs = []
        for opt_type in ("CE", "PE"):
            rows = self._fetch(opt_type, self.atm)
            if rows.empty:
                continue
            mkt_price = float(rows["Open"].iloc[0])
            iv = bs.implied_vol(mkt_price, self.spot, self.atm, self.T,
                                self.r, opt_type)
            if not math.isnan(iv):
                ivs.append(iv)

        self._iv = float(np.mean(ivs)) if ivs else None
        return self._iv

    def _available_strikes(self, option_type: str) -> list[int]:
        """Parse all unique strike values from ticker strings."""
        data   = self.calls if option_type == "CE" else self.puts
        suffix = option_type
        strikes = set()
        for ticker in data["Ticker"].dropna().unique():
            m = re.search(r"(\d{4,6})" + suffix, ticker)
            if m:
                strikes.add(int(m.group(1)))
        return sorted(strikes)

    # ------------------------------------------------------------------
    # Low-level fetch by absolute strike
    # ------------------------------------------------------------------

    def _fetch(self, option_type: str, strike: int) -> pd.DataFrame:
        data       = self.calls if option_type == "CE" else self.puts
        suffix     = f"{strike}{option_type}"
        suffix_nfo = f"{suffix}.NFO"
        result = data[data["Ticker"].apply(lambda a: a.strip().endswith(suffix_nfo))]
        if result.empty:
            result = data[data["Ticker"].apply(lambda a: a.strip().endswith(suffix))]
        return result
