import os
import hashlib
import datetime
import pandas as pd
import string
import glob
import warnings
warnings.filterwarnings('ignore')
from Data_env.Get_expiry import get_expiry
from Data_env.Strike_selection import Strike_selection
import tqdm


# ---------------------------------------------------------------------------
# Leg column key — unique string identifier for one leg's data columns
# ---------------------------------------------------------------------------

def _leg_col_key(leg: dict) -> str:
    """
    Return a short, deterministic column prefix for a leg.

    CE, offset=0       → "CE_0"
    CE, offset=200     → "CE_200"
    CE, offset=-200    → "CE_n200"
    CE, pct=1.02       → "CE_pct102"
    CE, delta=0.25     → "CE_d25"
    PE, delta=-0.25    → "PE_dn25"
    """
    opt = leg["option_type"]
    if "strike_pct" in leg:
        pct_int = int(round(leg["strike_pct"] * 100))
        return f"{opt}_pct{pct_int}"
    elif "strike_delta" in leg:
        d     = leg["strike_delta"]
        sign  = "n" if d < 0 else ""
        d_int = int(abs(d) * 100)
        return f"{opt}_d{sign}{d_int}"
    else:
        offset = leg.get("strike_offset", 0)
        sign   = "n" if offset < 0 else ""
        return f"{opt}_{sign}{abs(offset)}"


def _expiry_str_to_date(exp_str: str, reference_date: datetime.date) -> datetime.date:
    """Convert expiry string like '05JAN' → date, inferring year from reference_date."""
    day   = int(exp_str[:2])
    month = datetime.datetime.strptime(exp_str[2:], "%b").month
    year  = reference_date.year
    try:
        exp_date = datetime.date(year, month, day)
    except ValueError:
        return reference_date   # malformed string fallback
    if exp_date < reference_date:
        exp_date = datetime.date(year + 1, month, day)
    return exp_date


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class data_cleaning():

    def __init__(self, expiry_type, path: string, ticker: string,
                 legs: list = None, strike_rounding: int = 100):
        self.path            = path
        self.ticker          = ticker
        self.expiry_type     = expiry_type
        self.strike_rounding = strike_rounding
        self.trade_uni       = pd.DataFrame()
        self.futures         = pd.DataFrame()

        # Derive unique leg dicts, preserving order and deduplicating by key.
        default_legs = legs or [
            {"option_type": "CE", "strike_offset": 0},
            {"option_type": "PE", "strike_offset": 0},
        ]
        seen = set()
        self.leg_combos = []           # list of unique leg dicts
        for leg in default_legs:
            k = _leg_col_key(leg)
            if k not in seen:
                seen.add(k)
                self.leg_combos.append(leg)

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _cache_paths(self, cache_dir: str):
        combos_str = "_".join(_leg_col_key(leg) for leg in self.leg_combos)
        path_hash  = hashlib.md5((self.path + combos_str).encode()).hexdigest()[:8]
        base = f"{self.ticker}_{self.expiry_type}_{path_hash}"
        return (
            os.path.join(cache_dir, f"{base}_options.parquet"),
            os.path.join(cache_dir, f"{base}_futures.parquet"),
        )

    # ------------------------------------------------------------------
    # Per-file loading
    # ------------------------------------------------------------------

    def data_load(self, file):
        empty = pd.DataFrame(), pd.DataFrame()

        local_df = pd.read_csv(file)
        if local_df.empty:
            return empty

        # Some files (e.g. Jan 2014) have the Time column header missing in the
        # source CSV, causing pandas to name it "Ticker.1" (duplicate detection).
        # Detect this: if Time is absent but a Ticker.1 column looks like HH:MM:SS.
        if "Time" not in local_df.columns and "Ticker.1" in local_df.columns:
            sample = str(local_df["Ticker.1"].dropna().iloc[0]) if not local_df["Ticker.1"].dropna().empty else ""
            if ":" in sample:
                local_df = local_df.rename(columns={"Ticker.1": "Time"})

        if "Time" not in local_df.columns or "Date" not in local_df.columns:
            return empty

        local_df.insert(0, "Timestamp", local_df["Date"] + " " + local_df["Time"])
        # Older files use DD-MM-YY, newer files use DD/MM/YYYY — infer per file.
        local_df["Timestamp"] = pd.to_datetime(local_df["Timestamp"], dayfirst=True)
        local_df = local_df.sort_values(by="Timestamp")
        local_df["Ticker"] = local_df["Ticker"].apply(str)
        local_df.drop('Date', inplace=True, axis=1)
        local_df.drop('Time', inplace=True, axis=1)
        local_df = local_df[local_df["Ticker"].apply(
            lambda a: a[0:len(self.ticker)] == self.ticker)]

        if local_df.empty:
            return empty

        raw_calls = self.get_ticker_call_data(local_df=local_df)
        raw_puts  = self.get_ticker_put_data(local_df=local_df)
        future    = self.get_futures_data(local_df=local_df)

        if raw_calls is None or raw_calls.empty or future is None or future.empty:
            return empty

        if self.expiry_type == "CURRENT_WEEK":
            expiry = get_expiry(futures=raw_calls).current_weekly()
        elif self.expiry_type == "MONTHLY":
            expiry = get_expiry(futures=raw_calls).monthly()
        else:
            raise Exception(f"{self.expiry_type} does not exist")

        # ── Compute T (time to first expiry in years) for delta / greeks ─
        file_date = local_df["Timestamp"].dt.date.min()
        T = None
        if expiry:
            exp_date = _expiry_str_to_date(expiry[0], file_date)
            T = max((exp_date - file_date).days / 365.0, 1.0 / 365.0)

        ss = Strike_selection(
            futures=future, calls=raw_calls, puts=raw_puts,
            strike_rounding=self.strike_rounding,
            T=T,
        )

        merged = None

        for leg in self.leg_combos:
            opt_type    = leg["option_type"]
            strike_data = ss.get_strike_data(leg)
            if strike_data.empty:
                continue

            # Find the first expiry that has rows for this strike.
            matched = pd.DataFrame()
            for exp in expiry:
                prefix   = self.ticker + exp
                exp_rows = strike_data[strike_data["Ticker"].apply(
                    lambda a, p=prefix: a.strip()[:len(p)] == p)]
                if not exp_rows.empty:
                    matched = exp_rows.sort_values("Timestamp").copy()
                    break

            if matched.empty:
                continue

            key = _leg_col_key(leg)
            matched.columns = [
                "Timestamp",
                f"{key}_Ticker", f"{key}_Open",  f"{key}_High",
                f"{key}_Low",    f"{key}_Close",  f"{key}_Volume",
                f"{key}_OI",
            ]

            merged = matched if merged is None else pd.merge(
                merged, matched, on="Timestamp", how="inner")

        if merged is None or merged.empty:
            return empty

        return merged, future

    # ------------------------------------------------------------------
    # Raw data extraction helpers
    # ------------------------------------------------------------------

    def get_ticker_call_data(self, local_df):
        try:
            ticker_calls = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "CE")]
            if ticker_calls.empty:
                ticker_calls = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "CE")]
            return ticker_calls
        except KeyError:
            print(self.ticker + "'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None

    def get_ticker_put_data(self, local_df):
        try:
            ticker_puts = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "PE")]
            if ticker_puts.empty:
                ticker_puts = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "PE")]
            return ticker_puts
        except KeyError:
            print(self.ticker + "'s option data unavailable")
            return None
        except Exception as e:
            print("Error occurred: {}".format(e))
            return None

    def get_futures_data(self, local_df):
        try:
            ticker_fut = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-2:] == "-I")]
            if ticker_fut.empty:
                ticker_fut = local_df[local_df["Ticker"].apply(lambda a: a.strip()[-6:-4] == "-I")]
                if ticker_fut.empty:
                    exp = get_expiry(local_df).monthly()[0][-3:]
                    ticker_fut = local_df[local_df["Ticker"].apply(
                        lambda a: a.strip()[-10:-4] == exp + "FUT")]
            return ticker_fut
        except KeyError:
            print(self.ticker + "'s future's data unavailable")
            return None
        except Exception as e:
            print("Error : {}".format(e))
            return None

    # ------------------------------------------------------------------
    # Main entry point — with parquet caching
    # ------------------------------------------------------------------

    def get_filtered_data(self, use_cache: bool = True, cache_dir: str = None):
        """
        Build the trade universe from raw CSVs, with optional parquet caching.

        First call: processes all CSV files (slow) and saves two parquet files.
        Subsequent calls: loads parquet directly — 10-20x faster.

        Args:
            use_cache:  Load from / save to parquet cache. Set False to force a
                        fresh rebuild (e.g. after adding new data files or legs).
            cache_dir:  Where to write cache files. Defaults to the data path directory.
        """
        if cache_dir is None:
            cache_dir = os.path.dirname(os.path.abspath(self.path.rstrip("/*")))

        opts_path, futs_path = self._cache_paths(cache_dir)

        # ── Cache hit ────────────────────────────────────────────────
        if use_cache and os.path.exists(opts_path) and os.path.exists(futs_path):
            print(f"[Cache] Loading trade universe from parquet ({opts_path})")
            self.trade_uni = pd.read_parquet(opts_path)
            self.futures   = pd.read_parquet(futs_path)
            print(f"[Cache] Loaded {len(self.trade_uni):,} rows.")
            return self.trade_uni, self.futures

        # ── Cache miss — process raw CSVs ────────────────────────────
        print("CREATING TRADE UNIVERSE (this runs once, then cached as parquet)")

        # Recursive search: handles year/month/*.csv nesting at any depth.
        files = glob.glob(os.path.join(self.path, "**", "*.csv"), recursive=True)
        if not files:
            for folder in glob.glob(self.path):
                files.extend(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True))

        if not files:
            print(f"No CSV files found under: {self.path}")
            return self.trade_uni, self.futures

        trade_chunks   = []
        futures_chunks = []

        for file in tqdm.tqdm(files):
            trade_data, futures_data = self.data_load(file=file)
            if not trade_data.empty:
                trade_chunks.append(trade_data)
            if not futures_data.empty:
                futures_chunks.append(futures_data)

        self.trade_uni = (
            pd.concat(trade_chunks, ignore_index=True)
            if trade_chunks else pd.DataFrame()
        )
        self.futures = (
            pd.concat(futures_chunks, ignore_index=True)
            if futures_chunks else pd.DataFrame()
        )

        # ── Save cache ───────────────────────────────────────────────
        if use_cache and not self.trade_uni.empty:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                self.trade_uni.to_parquet(opts_path, index=False)
                self.futures.to_parquet(futs_path, index=False)
                print(f"[Cache] Saved → {opts_path}")
            except ImportError:
                print("[Cache] Skipped — install pyarrow: pip install pyarrow")

        print(f"TRADE UNIVERSE CREATED — {len(self.trade_uni):,} rows")
        return self.trade_uni, self.futures
