"""
SymbolResolver — resolves live option symbols for each trade leg.

Strike selection supports three modes (set per leg in runner LEGS):
  strike_offset : int    — ATM ± N points
  strike_pct    : float  — spot × pct  (e.g. 0.98 → 2% OTM put)
  strike_delta  : float  — closest delta  (CE: 0–1, PE: −1–0)

Expiry can be set via (in order of priority):
  expiry_date : "YYYY-MM-DD"  — exact date
  expiry_term : "1W" | "2W" | "1M" | "2M"  — term structure
  (default)   → next weekly expiry for the instrument
"""

import datetime
import calendar
import math
import holidays
import models.black_scholes as bs


class SymbolResolver:

    def __init__(self, fyers, underlying: str, exchange: str = "NSE",
                 strike_rounding: int = 100,
                 expiry_date: str = None,
                 expiry_term: str = None):
        self.fyers          = fyers
        self.underlying     = underlying       # e.g. "NSE:BANKNIFTY-INDEX"
        self.exchange       = exchange
        self.strike_rounding = strike_rounding
        self.india_holidays  = holidays.country_holidays("IN")
        self.base_name       = underlying.split(":")[1].split("-")[0]

        # Fixed expiry date (highest priority)
        if expiry_date is not None:
            self._fixed_expiry = (
                datetime.date.fromisoformat(expiry_date)
                if isinstance(expiry_date, str) else expiry_date
            )
        else:
            self._fixed_expiry = None

        # Term-structure expiry (used when expiry_date is None)
        self._expiry_term = expiry_term   # e.g. "1W", "2W", "1M"

    # ------------------------------------------------------------------
    # Public API — resolve symbols for all legs
    # ------------------------------------------------------------------

    def resolve_legs(self, legs: list) -> list:
        """
        Return a list of dicts:
          {"symbol": str, "option_type": str, "side": int, "entry": 0.0, "ltp": 0.0}

        One dict per leg in the order supplied.
        """
        ltp    = self._get_underlying_ltp()
        expiry = self._compute_expiry()
        atm    = self._round_strike(ltp)
        iv     = self._get_atm_iv(ltp, atm, expiry)

        print(f"\n[Symbol] Underlying LTP : {ltp:.2f}")
        print(f"[Symbol] ATM strike     : {atm}")
        print(f"[Symbol] Expiry         : {expiry}")
        print(f"[Symbol] ATM IV (approx): {iv*100:.1f}%\n" if iv else "")

        resolved = []
        for leg in legs:
            opt_type = leg["option_type"]
            strike   = self._compute_strike(leg, ltp, atm, expiry, iv)
            symbol   = self._build_symbol(opt_type, strike, expiry)
            side_lbl = "SELL" if leg["side"] == -1 else "BUY"
            print(f"[Symbol] {side_lbl} {opt_type} K={strike} → {symbol}")
            resolved.append({
                "symbol":      symbol,
                "option_type": opt_type,
                "side":        leg["side"],
                "entry":       0.0,
                "ltp":         0.0,
            })

        self._verify([r["symbol"] for r in resolved])
        return resolved

    # ------------------------------------------------------------------
    # Strike computation
    # ------------------------------------------------------------------

    def _compute_strike(self, leg, ltp, atm, expiry, iv):
        opt_type = leg["option_type"]

        if "strike_pct" in leg:
            raw = ltp * leg["strike_pct"]
            return self._round_strike(raw)

        elif "strike_delta" in leg:
            target_delta = leg["strike_delta"]
            T = self._time_to_expiry(expiry)
            if iv and T > 0:
                return self._find_delta_strike(opt_type, target_delta, ltp, expiry, iv, T)
            print(f"[Symbol] Warning: cannot compute delta strike (no IV/T); using ATM")
            return atm

        else:
            offset = leg.get("strike_offset", 0)
            return atm + offset

    def _find_delta_strike(self, option_type, target_delta, ltp, expiry, iv, T):
        """Fetch option chain and find the strike with the closest delta."""
        r = 0.065

        # Try Fyers option chain — may already contain delta
        try:
            resp = self.fyers.optionchain({
                "symbol": self.underlying, "strikecount": 20, "timestamp": ""
            })
            if resp.get("s") == "ok":
                chain = resp["data"].get("optionsChain", [])
                best_k, best_diff = None, float("inf")
                for row in chain:
                    k   = row.get("strikePrice", 0)
                    key = "CE" if option_type == "CE" else "PE"
                    # Try Fyers-provided delta first
                    fyers_delta = row.get(key, {}).get("delta")
                    if fyers_delta is not None:
                        d = float(fyers_delta)
                    else:
                        d = bs.delta(ltp, k, T, r, iv, option_type)
                    diff = abs(d - target_delta)
                    if diff < best_diff:
                        best_diff, best_k = diff, k
                if best_k:
                    return best_k
        except Exception:
            pass

        # Fallback: scan ±20 strikes in multiples of rounding
        best_k, best_diff = self._round_strike(ltp), float("inf")
        for step in range(-20, 21):
            k    = self._round_strike(ltp) + step * self.strike_rounding
            d    = bs.delta(ltp, k, T, r, iv, option_type)
            diff = abs(d - target_delta)
            if diff < best_diff:
                best_diff, best_k = diff, k
        return best_k

    # ------------------------------------------------------------------
    # Expiry computation
    # ------------------------------------------------------------------

    def _compute_expiry(self) -> datetime.date:
        if self._fixed_expiry is not None:
            return self._fixed_expiry
        if self._expiry_term:
            return self._expiry_from_term(self._expiry_term)
        # Default: next weekly expiry
        return self._expiry_from_term("1W")

    def _expiry_from_term(self, term: str) -> datetime.date:
        """
        Parse "NW" or "NM" and return the N-th weekly/monthly expiry from today.

        Examples: "1W" → next weekly, "2W" → one after that, "1M" → next monthly.
        """
        n      = int(term[:-1])
        period = term[-1].upper()

        if period == "W":
            # BANKNIFTY → Wednesday (2), NIFTY → Thursday (3)
            target_dow = 2 if "BANKNIFTY" in self.base_name else 3
            today      = datetime.date.today()
            days_ahead = (target_dow - today.weekday()) % 7
            if days_ahead == 0 and datetime.datetime.now().hour >= 15:
                days_ahead = 7
            expiry = today + datetime.timedelta(days=days_ahead)
            while expiry in self.india_holidays:
                expiry -= datetime.timedelta(days=1)
            # Advance n-1 more weeks
            for _ in range(n - 1):
                expiry += datetime.timedelta(weeks=1)
                while expiry in self.india_holidays:
                    expiry -= datetime.timedelta(days=1)
            return expiry

        else:  # "M"
            today    = datetime.date.today()
            month    = today.month
            year     = today.year
            found    = []
            while len(found) < n:
                exp = self._last_thursday(year, month)
                if exp >= today:
                    found.append(exp)
                month += 1
                if month > 12:
                    month, year = 1, year + 1
            return found[n - 1]

    def _last_thursday(self, year: int, month: int) -> datetime.date:
        last_day  = calendar.monthrange(year, month)[1]
        last_date = datetime.date(year, month, last_day)
        while last_date.weekday() != 3:   # Thursday = 3
            last_date -= datetime.timedelta(days=1)
        while last_date in self.india_holidays:
            last_date -= datetime.timedelta(days=1)
        return last_date

    def _time_to_expiry(self, expiry: datetime.date) -> float:
        today = datetime.date.today()
        days  = max((expiry - today).days, 0)
        return max(days / 365.0, 1 / 365.0)

    # ------------------------------------------------------------------
    # ATM IV for delta computation
    # ------------------------------------------------------------------

    def _get_atm_iv(self, ltp, atm, expiry):
        """Compute ATM IV from live option quotes (used for delta-based selection)."""
        T = self._time_to_expiry(expiry)
        if T <= 0:
            return None
        r = 0.065

        try:
            ce_sym = self._build_symbol("CE", atm, expiry)
            pe_sym = self._build_symbol("PE", atm, expiry)
            resp   = self.fyers.quotes({"symbols": f"{ce_sym},{pe_sym}"})
            if resp.get("s") != "ok":
                return None

            ivs = []
            for item in resp.get("d", []):
                sym   = item.get("n", "")
                mkt   = item.get("v", {}).get("lp", 0.0)
                opt   = "CE" if sym.endswith("CE") else "PE"
                iv    = bs.implied_vol(mkt, ltp, atm, T, r, opt)
                if not math.isnan(iv):
                    ivs.append(iv)
            return sum(ivs) / len(ivs) if ivs else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Symbol construction and verification
    # ------------------------------------------------------------------

    def _build_symbol(self, option_type: str, strike: int,
                      expiry: datetime.date) -> str:
        # Fyers weekly format: NSE:BANKNIFTY25MAY07 44000CE
        expiry_tag = expiry.strftime("%y%b%d").upper()
        return f"{self.exchange}:{self.base_name}{expiry_tag}{strike}{option_type}"

    def _verify(self, symbols: list):
        resp = self.fyers.quotes({"symbols": ",".join(symbols)})
        if resp.get("s") != "ok":
            raise RuntimeError(
                f"Symbol verification failed: {resp}\nSymbols: {symbols}"
            )
        print("[Symbol] All symbols verified OK.")

    def _get_underlying_ltp(self) -> float:
        resp = self.fyers.quotes({"symbols": self.underlying})
        if resp.get("s") != "ok":
            raise RuntimeError(f"Quotes failed for {self.underlying}: {resp}")
        return resp["d"][0]["v"]["lp"]

    def _round_strike(self, price: float) -> int:
        return int(round(price / self.strike_rounding) * self.strike_rounding)

    # ------------------------------------------------------------------
    # Legacy API (kept for compatibility)
    # ------------------------------------------------------------------

    def build_option_symbols(self):
        """Resolve ATM CE + PE — kept for any code still calling the old API."""
        atm_legs = [
            {"option_type": "CE", "strike_offset": 0, "side": -1},
            {"option_type": "PE", "strike_offset": 0, "side": -1},
        ]
        resolved = self.resolve_legs(atm_legs)
        expiry   = self._compute_expiry()
        ltp      = self._get_underlying_ltp()
        atm      = self._round_strike(ltp)
        return resolved[0]["symbol"], resolved[1]["symbol"], atm, expiry
