"""iter-v1/017 — Phase 1 EDA: symbol data availability + dead-feed pre-screen.

Verifies that candidate expansion symbols SOLUSDT and XRPUSDT have:
1. Full training window coverage (data starts before training_start = OOS_CUTOFF - 24mo).
2. OOS coverage extending past OOS_CUTOFF_DATE = 2025-03-24.
3. No A14 dead-feed pattern (per /006 closeout MKR lesson — flat-price runs ≥ 50 candles).
4. Pricing distribution check (median, std, range) vs baseline V1_BASELINE_UNIVERSE.

Writes:
- data_availability_summary.csv — per-symbol kline coverage stats
- dead_feed_screen.csv — A14 dead-feed detector results
- pricing_distribution.csv — log-return distribution stats for candidate vs baseline

IS-only data: this script uses OOS data ONLY for boundary verification (last-timestamp
checks); no model training or labeling occurs here. The training window for the next
iteration uses ONLY pre-OOS_CUTOFF data per the foundation discipline.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Project constants (sacred)
OOS_CUTOFF_DATE = "2025-03-24"
TRAINING_MONTHS = 24

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v1-017"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Symbols under examination
CANDIDATES = ["SOLUSDT", "XRPUSDT"]
BASELINE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]
ALL_SYMBOLS = BASELINE_SYMBOLS + CANDIDATES


def load_klines(symbol: str) -> pd.DataFrame:
    """Load 8h klines for a symbol from data/<sym>/8h.csv."""
    path = REPO_ROOT / "data" / symbol / "8h.csv"
    df = pd.read_csv(path)
    df["open_dt"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_dt"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    return df


def detect_dead_feed(df: pd.DataFrame, threshold_candles: int = 50) -> dict:
    """A14 dead-feed detector per /006 MKR lesson.

    Returns dict with:
    - max_consecutive_flat_close: longest run where close didn't change
    - max_consecutive_flat_ohlc: longest run where {open, high, low, close} all identical
    - num_zero_volume_candles
    - dead_feed_flag: True if any anomaly exceeds threshold
    """
    n = len(df)
    close = df["close"].to_numpy()

    # Consecutive identical close
    close_run = 0
    max_close_run = 0
    for i in range(1, n):
        if close[i] == close[i - 1]:
            close_run += 1
            if close_run > max_close_run:
                max_close_run = close_run
        else:
            close_run = 0

    # Consecutive identical OHLC (stronger dead-feed signal)
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    low_arr = df["low"].to_numpy()
    c = df["close"].to_numpy()
    ohlc_run = 0
    max_ohlc_run = 0
    for i in range(1, n):
        if (
            o[i] == o[i - 1]
            and h[i] == h[i - 1]
            and low_arr[i] == low_arr[i - 1]
            and c[i] == c[i - 1]
        ):
            ohlc_run += 1
            if ohlc_run > max_ohlc_run:
                max_ohlc_run = ohlc_run
        else:
            ohlc_run = 0

    zero_vol = int((df["volume"] == 0).sum())

    dead_feed_flag = (
        max_close_run >= threshold_candles
        or max_ohlc_run >= threshold_candles
        or zero_vol >= threshold_candles
    )

    return {
        "max_consecutive_flat_close": int(max_close_run),
        "max_consecutive_flat_ohlc": int(max_ohlc_run),
        "num_zero_volume_candles": zero_vol,
        "dead_feed_flag": dead_feed_flag,
    }


def compute_log_returns(df: pd.DataFrame, is_only: bool = True) -> pd.Series:
    """Log returns; if is_only=True, restrict to pre-OOS_CUTOFF."""
    df = df.copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    if is_only:
        oos_cutoff_ms = int(
            pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000
        )
        df = df[df["open_time"] < oos_cutoff_ms]
    close = df["close"].astype(float)
    return np.log(close / close.shift(1)).dropna()


def main() -> None:
    oos_cutoff_dt = datetime.fromisoformat(OOS_CUTOFF_DATE).replace(tzinfo=timezone.utc)
    training_start = oos_cutoff_dt - pd.Timedelta(days=30 * TRAINING_MONTHS)

    print(f"OOS_CUTOFF_DATE: {oos_cutoff_dt.isoformat()}")
    print(f"Training start (24mo before OOS): {training_start.isoformat()}")
    print()

    # ---------- Table 1: data availability ----------
    rows = []
    for sym in ALL_SYMBOLS:
        df = load_klines(sym)
        first = df["open_dt"].min()
        last = df["open_dt"].max()
        is_first_ok = first <= training_start
        is_last_ok = last >= oos_cutoff_dt + pd.Timedelta(days=30)  # at least 1mo OOS
        rows.append(
            {
                "symbol": sym,
                "is_candidate": sym in CANDIDATES,
                "n_klines": len(df),
                "first_open": first.isoformat(),
                "last_open": last.isoformat(),
                "covers_training_window": is_first_ok,
                "covers_oos_window": is_last_ok,
                "days_of_oos": (last - oos_cutoff_dt).days,
            }
        )
    avail_df = pd.DataFrame(rows)
    avail_df.to_csv(OUT_DIR / "data_availability_summary.csv", index=False)
    print("=== Table 1: Data Availability ===")
    print(avail_df.to_string(index=False))
    print()

    # ---------- Table 2: dead-feed pre-screen ----------
    rows = []
    for sym in ALL_SYMBOLS:
        df = load_klines(sym)
        dead = detect_dead_feed(df, threshold_candles=50)
        dead["symbol"] = sym
        dead["is_candidate"] = sym in CANDIDATES
        rows.append(dead)
    dead_df = pd.DataFrame(rows)
    cols = ["symbol", "is_candidate"] + [c for c in dead_df.columns if c not in ("symbol", "is_candidate")]
    dead_df = dead_df[cols]
    dead_df.to_csv(OUT_DIR / "dead_feed_screen.csv", index=False)
    print("=== Table 2: A14 Dead-Feed Pre-Screen (threshold=50 candles) ===")
    print(dead_df.to_string(index=False))
    print()

    # ---------- Table 3: IS log-return distribution ----------
    rows = []
    for sym in ALL_SYMBOLS:
        df = load_klines(sym)
        ret = compute_log_returns(df, is_only=True)
        ret_pct = ret * 100  # to percentage points for readability
        rows.append(
            {
                "symbol": sym,
                "is_candidate": sym in CANDIDATES,
                "n_is_returns": len(ret),
                "mean_pct": round(ret_pct.mean(), 4),
                "std_pct": round(ret_pct.std(), 4),
                "p10_pct": round(ret_pct.quantile(0.10), 4),
                "p50_pct": round(ret_pct.quantile(0.50), 4),
                "p90_pct": round(ret_pct.quantile(0.90), 4),
                "abs_p50_pct": round(ret_pct.abs().quantile(0.50), 4),
                "abs_p95_pct": round(ret_pct.abs().quantile(0.95), 4),
                "skew": round(float(ret_pct.skew()), 4),
                "kurtosis": round(float(ret_pct.kurtosis()), 4),
            }
        )
    dist_df = pd.DataFrame(rows)
    dist_df.to_csv(OUT_DIR / "pricing_distribution.csv", index=False)
    print("=== Table 3: IS Log-Return Distribution (pre-OOS_CUTOFF) ===")
    print(dist_df.to_string(index=False))
    print()

    # ---------- Table 4: IS correlation vs BTC (denominator-dilution justification) ----------
    btc_ret = compute_log_returns(load_klines("BTCUSDT"), is_only=True)
    btc_ret.name = "BTCUSDT"
    rows = []
    for sym in ALL_SYMBOLS:
        if sym == "BTCUSDT":
            rho = 1.0
        else:
            sym_ret = compute_log_returns(load_klines(sym), is_only=True)
            # Reindex to BTC's open_time grid via the symbol's own DataFrame
            df_sym = load_klines(sym)
            df_sym = df_sym.sort_values("open_time").reset_index(drop=True)
            oos_cutoff_ms = int(
                pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000
            )
            df_sym = df_sym[df_sym["open_time"] < oos_cutoff_ms]
            sym_ret.index = df_sym["open_time"].iloc[1:].to_numpy()

            df_btc = load_klines("BTCUSDT")
            df_btc = df_btc.sort_values("open_time").reset_index(drop=True)
            df_btc = df_btc[df_btc["open_time"] < oos_cutoff_ms]
            btc_ret_indexed = btc_ret.copy()
            btc_ret_indexed.index = df_btc["open_time"].iloc[1:].to_numpy()

            joined = pd.DataFrame({"sym": sym_ret, "btc": btc_ret_indexed}).dropna()
            rho = float(joined["sym"].corr(joined["btc"]))
        rows.append({"symbol": sym, "is_candidate": sym in CANDIDATES, "is_corr_vs_BTC": round(rho, 4)})
    corr_df = pd.DataFrame(rows)
    corr_df.to_csv(OUT_DIR / "is_correlation_vs_btc.csv", index=False)
    print("=== Table 4: IS Log-Return Correlation vs BTC ===")
    print(corr_df.to_string(index=False))
    print()

    # ---------- Outputs summary ----------
    print(f"Outputs written to {OUT_DIR}/")
    for f in sorted(OUT_DIR.glob("*.csv")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
