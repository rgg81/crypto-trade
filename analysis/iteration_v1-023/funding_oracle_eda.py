"""iter-v1/023 — ORACLE EDA: baseline trade-roster intersection with funding z-score regimes.

CRITICAL CAVEAT (per `feedback_v3_oracle_eda_validity.md`):
This ORACLE EDA evaluates how baseline trades distribute across funding z-score
regimes. It is descriptively valid because the funding feature is STATELESS
(no signal-emission state propagation). It does NOT predict /023 trade-roster
outcome because adding the feature to V1_FEATURE_COLUMNS_PRUNED retrains
LightGBM and the basin will relocate (Jaccard 0.10 IS / 0.093 OOS at /022 vs
baseline LTC-in-pool). The roster will differ; the prior is descriptive only.

PURPOSE:
- Identify whether funding-z-score regimes (extreme negative / negative / neutral /
  positive / extreme positive) show differential trade outcomes on the baseline
  roster. If yes → mechanism story has IS-anchored support. If no → mechanism
  story relies entirely on the model learning a non-obvious signal (higher prior
  on INERT verdict).
- This is brief Section 2 IS-only evidence, NOT a falsifier or anchor for /023's
  predicted OOS Sharpe Δ.

USE:
- baseline trades from BASELINE_V1.md anchor (corrected walk-forward, 5-seed,
  reports-v1/iteration_v1-baseline/in_sample/trades.csv).
- IS-only (open_time < OOS_CUTOFF_DATE = 2025-03-24).
- Z-score computed on the trade entry candle's funding rate (past-only via .shift(1)).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from crypto_trade.config import OOS_CUTOFF_DATE  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402

OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE).timestamp() * 1000)

ROOT_DIR = ROOT
DATA_DIR = ROOT_DIR / "data"
FUNDING_DIR = DATA_DIR / "funding_rates"
TRADES_CSV = ROOT_DIR / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OUT_DIR = ROOT_DIR / "analysis" / "iteration_v1-023"


def compute_funding_zscore(kline_df: pd.DataFrame, funding_df: pd.DataFrame, window: int = 30) -> pd.Series:
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    kline = kline_df.copy()
    kline["open_time_aligned"] = (kline["open_time"] // 60_000) * 60_000
    merged = kline.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])
    s = merged["funding_rate"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    z = (s - rmean) / rstd.replace(0, np.nan)
    return z.clip(-10.0, 10.0)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load baseline IS trades
    trades = pd.read_csv(TRADES_CSV)
    print(f"Baseline IS trades: {len(trades)}")
    print(f"Columns: {list(trades.columns)[:10]}")

    # Build z-score lookup per symbol (full series merged with funding)
    sym_z30: dict[str, pd.DataFrame] = {}
    for symbol in V1_BASELINE_UNIVERSE:
        kline = pd.read_csv(DATA_DIR / symbol / "8h.csv")
        funding = pd.read_csv(FUNDING_DIR / f"{symbol}.csv")
        z = compute_funding_zscore(kline, funding, window=30)
        sym_z30[symbol] = pd.DataFrame({"open_time": kline["open_time"], "z30": z.values})

    # Trade open_time is actually the candle's close_time (ends in 99999).
    # Convert to kline open_time: subtract 8h - 1ms = 28800000 - 1 = 28799999.
    CANDLE_DELTA_MS = 8 * 3600 * 1000  # 28800000 for 8h

    # Helper: find trade entry candle's z-score
    def lookup_z30(row) -> float:
        sym = row["symbol"]
        if sym not in sym_z30:
            return np.nan
        # row["open_time"] is the candle's close_time; convert to open_time
        ot = row["open_time"] + 1 - CANDLE_DELTA_MS
        match = sym_z30[sym][sym_z30[sym]["open_time"] == ot]
        if len(match) == 0:
            return np.nan
        return match["z30"].iloc[0]

    trades["z30_at_entry"] = trades.apply(lookup_z30, axis=1)
    trades_with_z = trades.dropna(subset=["z30_at_entry"]).copy()
    print(f"  with z30 lookup: {len(trades_with_z)}")

    # Bin trades by z30 regime
    def bin_z(z: float) -> str:
        if z < -2.0:
            return "extreme_negative_z<-2"
        if z < -1.0:
            return "negative_-2_to_-1"
        if z <= 1.0:
            return "neutral_-1_to_1"
        if z <= 2.0:
            return "positive_1_to_2"
        return "extreme_positive_z>2"

    trades_with_z["z30_band"] = trades_with_z["z30_at_entry"].apply(bin_z)

    # Per-band attribution: trade count, win rate, mean pnl, sum pnl
    grouped = trades_with_z.groupby("z30_band").agg(
        n_trades=("symbol", "size"),
        n_wins=("net_pnl_pct", lambda s: int((s > 0).sum())),
        mean_pnl_pct=("net_pnl_pct", "mean"),
        sum_pnl_pct=("net_pnl_pct", "sum"),
        weighted_sum=("weighted_pnl", "sum") if "weighted_pnl" in trades_with_z.columns else ("net_pnl_pct", "sum"),
    )
    grouped["win_rate"] = grouped["n_wins"] / grouped["n_trades"]

    # Direction-conditional bands
    direction_rows = []
    for band in ["extreme_negative_z<-2", "negative_-2_to_-1", "neutral_-1_to_1",
                 "positive_1_to_2", "extreme_positive_z>2"]:
        sub = trades_with_z[trades_with_z["z30_band"] == band]
        for direction_label, mask in [
            ("longs", sub.get("direction", pd.Series([1] * len(sub))).fillna(1) == 1),
            ("shorts", sub.get("direction", pd.Series([-1] * len(sub))).fillna(-1) == -1),
        ]:
            sub_dir = sub[mask]
            if len(sub_dir) == 0:
                continue
            direction_rows.append({
                "z30_band": band,
                "direction": direction_label,
                "n_trades": len(sub_dir),
                "win_rate": float((sub_dir["net_pnl_pct"] > 0).sum() / len(sub_dir)),
                "mean_pnl_pct": float(sub_dir["net_pnl_pct"].mean()),
                "sum_pnl_pct": float(sub_dir["net_pnl_pct"].sum()),
            })

    # Per-symbol band attribution (mechanism-story-relevant for who responds to funding regime)
    per_sym_band_rows = []
    for symbol in V1_BASELINE_UNIVERSE:
        sub = trades_with_z[trades_with_z["symbol"] == symbol]
        for band in ["extreme_negative_z<-2", "negative_-2_to_-1", "neutral_-1_to_1",
                     "positive_1_to_2", "extreme_positive_z>2"]:
            sub_b = sub[sub["z30_band"] == band]
            if len(sub_b) == 0:
                continue
            per_sym_band_rows.append({
                "symbol": symbol,
                "z30_band": band,
                "n_trades": len(sub_b),
                "win_rate": float((sub_b["net_pnl_pct"] > 0).sum() / len(sub_b)),
                "mean_pnl_pct": float(sub_b["net_pnl_pct"].mean()),
                "sum_pnl_pct": float(sub_b["net_pnl_pct"].sum()),
            })

    grouped.to_csv(OUT_DIR / "funding_oracle_band_attribution.csv")
    pd.DataFrame(direction_rows).to_csv(OUT_DIR / "funding_oracle_direction_attribution.csv", index=False)
    pd.DataFrame(per_sym_band_rows).to_csv(OUT_DIR / "funding_oracle_per_sym_band.csv", index=False)

    print()
    print("=== Baseline IS trades by z30 band ===")
    print(grouped.to_string())
    print()
    print("=== Direction × band attribution ===")
    print(pd.DataFrame(direction_rows).to_string())
    print()
    print("=== Per-symbol × band attribution (head 30 rows) ===")
    print(pd.DataFrame(per_sym_band_rows).head(30).to_string())


if __name__ == "__main__":
    main()
