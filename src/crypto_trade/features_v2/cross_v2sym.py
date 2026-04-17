"""iter-v2/043: cross-symbol relative strength features within the v2 universe.

Adds 3 features per symbol that capture how it's performing RELATIVE TO
the other v2 symbols:

- ``sym_ret_7d_rank_v2`` — this symbol's 7d log return ranked among the
  v2 peer symbols (0=worst, 1=best). Captures relative momentum.
- ``sym_ret_14d_rank_v2`` — same but 14-day horizon. Slower signal.
- ``sym_vs_v2mean_ret_7d`` — this symbol's 7d log return minus the
  equal-weighted mean of the v2 peers' 7d log returns. Captures
  distance from group behavior.

These are scale-invariant by construction (ranks + differences of
log-returns) and stationary. No overlap with the BTC cross-asset
features (which measure the symbol vs BTC, not vs v2 peers).

The v2 peer universe is a hardcoded constant here. If V2_MODELS in
run_baseline_v2.py changes, update V2_PEER_SYMBOLS to match.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path

V2_PEER_SYMBOLS: tuple[str, ...] = ("DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT")

_PEERS_CACHE: dict[str, pd.DataFrame] | None = None


def _load_peer_returns() -> dict[str, pd.DataFrame]:
    """Load 7d and 14d log returns for each v2 peer symbol. Cached."""
    global _PEERS_CACHE
    if _PEERS_CACHE is not None:
        return _PEERS_CACHE

    out: dict[str, pd.DataFrame] = {}
    for sym in V2_PEER_SYMBOLS:
        path = csv_path(Path("data"), sym, "8h")
        ka = load_kline_array(path)
        if len(ka) == 0:
            continue
        df = ka.df[["open_time", "close"]].copy()
        log_close = np.log(df["close"].to_numpy(dtype=np.float64))
        n = len(log_close)

        # 21 candles = 7 days on 8h (3 candles per day)
        if n >= 21:
            ret_7d = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
        else:
            ret_7d = np.full(n, np.nan)

        if n >= 42:
            ret_14d = np.concatenate([np.full(42, np.nan), log_close[42:] - log_close[:-42]])
        else:
            ret_14d = np.full(n, np.nan)

        out[sym] = pd.DataFrame(
            {"open_time": df["open_time"].to_numpy(), "ret_7d": ret_7d, "ret_14d": ret_14d}
        )

    _PEERS_CACHE = out
    return out


def add_cross_v2sym_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add 3 cross-v2-symbol relative-strength features."""
    peers = _load_peer_returns()
    if not peers:
        df["sym_ret_7d_rank_v2"] = np.nan
        df["sym_ret_14d_rank_v2"] = np.nan
        df["sym_vs_v2mean_ret_7d"] = np.nan
        return df

    df = df.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    # Build a wide table: rows=open_time, cols=(sym, ret_7d|ret_14d)
    # Use an outer join on open_time so all timestamps are represented.
    peer_frames = []
    for sym, pdf in peers.items():
        pdf = pdf.rename(columns={"ret_7d": f"{sym}_ret_7d", "ret_14d": f"{sym}_ret_14d"})
        peer_frames.append(pdf)
    peer_wide = peer_frames[0]
    for pf in peer_frames[1:]:
        peer_wide = peer_wide.merge(pf, on="open_time", how="outer")
    peer_wide = peer_wide.sort_values("open_time").reset_index(drop=True)

    ret_7d_cols = [c for c in peer_wide.columns if c.endswith("_ret_7d")]
    ret_14d_cols = [c for c in peer_wide.columns if c.endswith("_ret_14d")]

    # Per-row rank (0..1) of each peer's 7d return
    def _per_row_rank(row: np.ndarray) -> np.ndarray:
        valid_mask = ~np.isnan(row)
        n_valid = int(valid_mask.sum())
        out = np.full_like(row, np.nan, dtype=np.float64)
        if n_valid <= 1:
            return out
        valid_vals = row[valid_mask]
        # argsort-of-argsort → 0..n_valid-1 rank
        order = np.argsort(np.argsort(valid_vals))
        scaled = order / (n_valid - 1)  # 0 = worst, 1 = best
        out[valid_mask] = scaled
        return out

    ranks_7d = np.apply_along_axis(_per_row_rank, 1, peer_wide[ret_7d_cols].to_numpy())
    ranks_14d = np.apply_along_axis(_per_row_rank, 1, peer_wide[ret_14d_cols].to_numpy())
    mean_7d = peer_wide[ret_7d_cols].mean(axis=1).to_numpy()

    rank_7d_df = pd.DataFrame(ranks_7d, columns=[f"rank_{c}" for c in ret_7d_cols])
    rank_7d_df["open_time"] = peer_wide["open_time"].to_numpy()
    rank_14d_df = pd.DataFrame(ranks_14d, columns=[f"rank_{c}" for c in ret_14d_cols])
    rank_14d_df["open_time"] = peer_wide["open_time"].to_numpy()
    mean_df = pd.DataFrame(
        {"open_time": peer_wide["open_time"].to_numpy(), "v2_mean_ret_7d": mean_7d}
    )

    # Identify the current symbol. Look it up from the symbol column if present,
    # else fall back to matching close values against peer data.
    sym_col = None
    if "symbol" in df.columns:
        symbols_unique = df["symbol"].dropna().unique()
        if len(symbols_unique) == 1:
            sym_col = str(symbols_unique[0])

    if sym_col is None:
        # Fallback: derive from the parquet path if available through kline metadata
        # If we still cannot determine, return NaN features.
        df["sym_ret_7d_rank_v2"] = np.nan
        df["sym_ret_14d_rank_v2"] = np.nan
        df["sym_vs_v2mean_ret_7d"] = np.nan
        if had_open_time_index:
            df = df.set_index("open_time", drop=False)
            df.index.name = "open_time"
        return df

    # Merge the peer rank + mean data onto the symbol's timeline
    rank_7d_col = f"rank_{sym_col}_ret_7d"
    rank_14d_col = f"rank_{sym_col}_ret_14d"

    # Handle non-peer symbols (e.g., ATOMUSDT when peers are DOGE/SOL/XRP/NEAR)
    if rank_7d_col not in rank_7d_df.columns:
        df["sym_ret_7d_rank_v2"] = np.nan
        df["sym_ret_14d_rank_v2"] = np.nan
        df["sym_vs_v2mean_ret_7d"] = np.nan
        if had_open_time_index:
            df = df.set_index("open_time", drop=False)
            df.index.name = "open_time"
        return df

    df = df.merge(
        rank_7d_df[["open_time", rank_7d_col]], on="open_time", how="left"
    )
    df = df.merge(
        rank_14d_df[["open_time", rank_14d_col]], on="open_time", how="left"
    )
    df = df.merge(mean_df, on="open_time", how="left")

    # Compute sym_vs_v2mean_ret_7d = sym_ret_7d - v2_mean_ret_7d
    # sym_ret_7d comes from the peer_wide table for this symbol
    sym_ret_7d_col = f"{sym_col}_ret_7d"
    if sym_ret_7d_col in peer_wide.columns:
        sym_ret_df = peer_wide[["open_time", sym_ret_7d_col]].copy()
        df = df.merge(sym_ret_df, on="open_time", how="left")
        df["sym_vs_v2mean_ret_7d"] = df[sym_ret_7d_col] - df["v2_mean_ret_7d"]
        df = df.drop(columns=[sym_ret_7d_col, "v2_mean_ret_7d"])
    else:
        df["sym_vs_v2mean_ret_7d"] = np.nan
        df = df.drop(columns=["v2_mean_ret_7d"], errors="ignore")

    df = df.rename(
        columns={
            rank_7d_col: "sym_ret_7d_rank_v2",
            rank_14d_col: "sym_ret_14d_rank_v2",
        }
    )

    if had_open_time_index:
        df = df.set_index("open_time", drop=False)
        df.index.name = "open_time"

    return df
