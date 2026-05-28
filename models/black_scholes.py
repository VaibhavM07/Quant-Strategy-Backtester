"""
Black-Scholes option pricing and Greeks.

Usage
-----
import models.black_scholes as bs

iv  = bs.implied_vol(market_price=120, S=44000, K=44000, T=0.05, r=0.06, option_type="CE")
grk = bs.greeks(S=44000, K=44000, T=0.05, r=0.06, sigma=iv, option_type="CE")
# grk → {"price": ..., "delta": ..., "gamma": ..., "vega": ..., "theta": ..., "rho": ..., "iv": ...}

Parameters
----------
S     : float  — underlying spot price
K     : float  — strike price
T     : float  — time to expiry in years (e.g. 7/365 for 7 days)
r     : float  — annual risk-free rate as a decimal (e.g. 0.065 for 6.5%)
sigma : float  — annual implied volatility as a decimal (e.g. 0.20 for 20%)
option_type : "CE" | "PE"

Greeks returned per standard conventions
-----------------------------------------
delta : ∂V/∂S            (CE: 0–1, PE: −1–0)
gamma : ∂²V/∂S²          (always positive)
vega  : ∂V/∂σ            (per 1% change in IV, in ₹)
theta : ∂V/∂t            (per calendar day, in ₹, always negative for long)
rho   : ∂V/∂r            (per 1% change in rate, in ₹)
"""

import math
import numpy as np

# ---------------------------------------------------------------------------
# Try fast scipy erf; fall back to pure-Python approximation
# ---------------------------------------------------------------------------
try:
    from scipy.stats import norm as _norm
    _cdf  = _norm.cdf
    _pdf  = _norm.pdf
    from scipy.optimize import brentq as _brentq
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False
    def _cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    def _pdf(x):
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Core internals
# ---------------------------------------------------------------------------

def _d1d2(S, K, T, r, sigma):
    ln_sk = math.log(S / K)
    sqrt_T = math.sqrt(T)
    d1 = (ln_sk + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


# ---------------------------------------------------------------------------
# Price
# ---------------------------------------------------------------------------

def price(S: float, K: float, T: float, r: float, sigma: float,
          option_type: str = "CE") -> float:
    """Theoretical Black-Scholes option price."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(0.0, (S - K) if option_type == "CE" else (K - S))
        return intrinsic
    d1, d2 = _d1d2(S, K, T, r, sigma)
    disc = math.exp(-r * T)
    if option_type == "CE":
        return S * _cdf(d1) - K * disc * _cdf(d2)
    else:
        return K * disc * _cdf(-d2) - S * _cdf(-d1)


# ---------------------------------------------------------------------------
# Greeks
# ---------------------------------------------------------------------------

def delta(S: float, K: float, T: float, r: float, sigma: float,
          option_type: str = "CE") -> float:
    """Delta — sensitivity of option price to ₹1 move in underlying."""
    if T <= 0:
        return 1.0 if (option_type == "CE" and S > K) else (0.0 if option_type == "CE" else -1.0)
    d1, _ = _d1d2(S, K, T, r, sigma)
    return _cdf(d1) if option_type == "CE" else _cdf(d1) - 1.0


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Gamma — rate of change of delta per ₹1 move in underlying."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, sigma)
    return _pdf(d1) / (S * sigma * math.sqrt(T))


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vega — option price change per 1% rise in IV (in ₹)."""
    if T <= 0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, sigma)
    return S * _pdf(d1) * math.sqrt(T) * 0.01   # scaled to 1% IV move


def theta(S: float, K: float, T: float, r: float, sigma: float,
          option_type: str = "CE") -> float:
    """Theta — option price decay per calendar day (in ₹, negative for long)."""
    if T <= 0:
        return 0.0
    d1, d2 = _d1d2(S, K, T, r, sigma)
    decay = -S * _pdf(d1) * sigma / (2.0 * math.sqrt(T))
    disc  = math.exp(-r * T)
    if option_type == "CE":
        return (decay - r * K * disc * _cdf(d2)) / 365.0
    else:
        return (decay + r * K * disc * _cdf(-d2)) / 365.0


def rho(S: float, K: float, T: float, r: float, sigma: float,
        option_type: str = "CE") -> float:
    """Rho — option price change per 1% rise in risk-free rate (in ₹)."""
    if T <= 0:
        return 0.0
    _, d2 = _d1d2(S, K, T, r, sigma)
    disc  = math.exp(-r * T)
    if option_type == "CE":
        return K * T * disc * _cdf(d2) * 0.01
    else:
        return -K * T * disc * _cdf(-d2) * 0.01


# ---------------------------------------------------------------------------
# Implied volatility
# ---------------------------------------------------------------------------

def implied_vol(market_price: float, S: float, K: float, T: float,
                r: float, option_type: str = "CE",
                lo: float = 1e-4, hi: float = 10.0) -> float:
    """
    Implied volatility via Brent's method (scipy) or bisection fallback.

    Returns float in [lo, hi], or np.nan if the market price is outside
    the no-arbitrage bounds.
    """
    if T <= 0:
        return float("nan")
    intrinsic = max(0.0, (S - K) if option_type == "CE" else (K - S))
    if market_price <= intrinsic or market_price <= 0:
        return float("nan")

    def objective(sigma):
        return price(S, K, T, r, sigma, option_type) - market_price

    # Bracket check
    if objective(lo) * objective(hi) > 0:
        return float("nan")

    if _HAS_SCIPY:
        try:
            return _brentq(objective, lo, hi, xtol=1e-6, maxiter=200)
        except Exception:
            return float("nan")
    else:
        # Pure-Python bisection
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if objective(mid) < 0:
                lo = mid
            else:
                hi = mid
            if (hi - lo) < 1e-6:
                break
        return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# Convenience: all greeks at once
# ---------------------------------------------------------------------------

def greeks(S: float, K: float, T: float, r: float, sigma: float,
           option_type: str = "CE") -> dict:
    """Return a dict of all greeks and theoretical price."""
    return {
        "price":  round(price(S, K, T, r, sigma, option_type), 4),
        "delta":  round(delta(S, K, T, r, sigma, option_type), 4),
        "gamma":  round(gamma(S, K, T, r, sigma), 6),
        "vega":   round(vega(S, K, T, r, sigma), 4),
        "theta":  round(theta(S, K, T, r, sigma, option_type), 4),
        "rho":    round(rho(S, K, T, r, sigma, option_type), 4),
        "iv":     round(sigma * 100, 2),          # as percentage
    }
