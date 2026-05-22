"""Threshold sweep — at which BTC drawdown / vol z-score thresholds does the
regime gate capture the 2023 TRX SHORT toxic concentration WITHOUT firing in
2025/2026 OOS healthy windows?

Tests 3 thresholds (relaxing from default 20% / 1.5):
- T1: DD>20% OR vol_z>1.5 (default — already tested, FIRES TOO RARELY in 2023)
- T2: DD>15% OR vol_z>1.0 (relaxed — should capture more of 2023)
- T3: DD>10% OR vol_z>0.5 (very relaxed — captures broader regime)

For each threshold, compute:
- TRX SHORT IS stressed-regime n_trades + weighted_pnl
- TRX SHORT OOS stressed-regime n_trades + weighted_pnl (must be SMALL — preserves OOS edge)
- TRX LONG IS stressed-regime n_trades + weighted_pnl (collateral damage if blocked)
- TRX LONG OOS stressed-regime n_trades + weighted_pnl (collateral damage)

Decision criterion: at which threshold is TRX SHORT IS stressed_pnl ≥ -X% AND
TRX SHORT OOS stressed_n_trades ≤ Y, AND TRX LONG IS stressed_pnl ≥ -Z?
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-048"

ITER045_IS = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "trades.csv"
ITER045_OOS = REPO / "reports-v3" / "iteration_v3-045" / "out_of_sample" / "trades.csv"
BTC_CSV = REPO / "data" / "BTCUSDT" / "8h.csv"


def build_btc_regime_lookup_with_thresholds(
    dd_threshold: float, vol_z_threshold: float
) -> pd.DataFrame:
    """Same as in regime_gate_validation.py, with custom thresholds."""
    df = pd.read_csv(BTC_CSV, usecols=["open_time", "close"])
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = df["close"].astype(float)

    close_shifted = df["close"].shift(1)
    rolling_max = close_shifted.rolling(window=90, min_periods=1).max()
    df["drawdown_pct"] = (close_shifted - rolling_max) / rolling_max * 100.0

    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    logret_shifted = df["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=90, min_periods=2).std()
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)
    df["vol_zscore"] = (rolling_std - expanding_mean) / expanding_std

    df["dd_fires"] = df["drawdown_pct"].abs() > dd_threshold
    df["vol_fires"] = df["vol_zscore"].abs() > vol_z_threshold
    df["regime_stressed"] = df["dd_fires"] | df["vol_fires"]

    return df[["open_time", "drawdown_pct", "vol_zscore", "regime_stressed"]]


def tag_trades(trades_path: Path, regime_lookup: pd.DataFrame) -> pd.DataFrame:
    trades = pd.read_csv(trades_path)
    btc_times = regime_lookup["open_time"].to_numpy(dtype=np.int64)
    regime_arr = regime_lookup["regime_stressed"].to_numpy(dtype=bool)

    regimes = []
    for ot in trades["open_time"]:
        idx = int(np.searchsorted(btc_times, int(ot), side="left")) - 1
        regimes.append(False if idx < 0 else bool(regime_arr[idx]))
    trades["regime_stressed"] = regimes
    trades["dir_label"] = trades["direction"].map({1: "LONG", -1: "SHORT"})
    return trades


def threshold_sweep_summary(
    is_trades: pd.DataFrame, oos_trades: pd.DataFrame, t_label: str,
    dd_t: float, vz_t: float
) -> list[dict]:
    """For one threshold, summarize TRX direction × regime breakdown."""
    rows = []
    for label, df in (("IS", is_trades), ("OOS", oos_trades)):
        sub = df[df["symbol"] == "TRXUSDT"]
        for d_label in ("LONG", "SHORT"):
            for regime in (False, True):
                d = sub[(sub["dir_label"] == d_label) & (sub["regime_stressed"] == regime)]
                regime_label = "STRESSED" if regime else "HEALTHY"
                rows.append(
                    {
                        "threshold_label": t_label,
                        "dd_threshold": dd_t,
                        "vol_z_threshold": vz_t,
                        "set": label,
                        "direction": d_label,
                        "regime": regime_label,
                        "n_trades": len(d),
                        "wins": int((d["net_pnl_pct"] > 0).sum()),
                        "win_rate_pct": (
                            round((d["net_pnl_pct"] > 0).mean() * 100, 2) if len(d) else 0.0
                        ),
                        "net_pnl_pct_sum": round(d["net_pnl_pct"].sum(), 4),
                        "weighted_pnl_sum": round(d["weighted_pnl"].sum(), 4),
                    }
                )
        # All-symbols regime fire rate at this threshold
        for sym in ("BCHUSDT", "TRXUSDT", "LDOUSDT", "ALGOUSDT"):
            ssub = df[df["symbol"] == sym]
            n_total = len(ssub)
            n_stressed = int(ssub["regime_stressed"].sum())
            rows.append(
                {
                    "threshold_label": t_label,
                    "dd_threshold": dd_t,
                    "vol_z_threshold": vz_t,
                    "set": label,
                    "direction": "ALL",
                    "regime": f"FIRE_RATE_{sym}",
                    "n_trades": n_stressed,
                    "wins": n_total,  # use 'wins' field for n_total here
                    "win_rate_pct": round(n_stressed / n_total * 100, 2) if n_total else 0.0,
                    "net_pnl_pct_sum": 0,
                    "weighted_pnl_sum": 0,
                }
            )
    return rows


def main() -> int:
    print("=" * 78)
    print("Regime threshold sweep — find threshold that captures 2023 toxicity")
    print("=" * 78)

    thresholds = [
        ("T1_default_20pct_1.5z", 20.0, 1.5),
        ("T2_relaxed_15pct_1.0z", 15.0, 1.0),
        ("T3_more_relaxed_10pct_0.5z", 10.0, 0.5),
        ("T4_dd_only_10pct", 10.0, 999.0),  # DD-only (vol_z effectively disabled)
        ("T5_vol_only_0.5z", 999.0, 0.5),  # vol_z-only (DD effectively disabled)
    ]

    all_rows = []
    for t_label, dd_t, vz_t in thresholds:
        print(f"\n=== Threshold {t_label}: DD>{dd_t}% OR |vol_z|>{vz_t} ===")
        regime_lookup = build_btc_regime_lookup_with_thresholds(dd_t, vz_t)
        n_total = len(regime_lookup)
        n_stressed = int(regime_lookup["regime_stressed"].sum())
        print(
            f"  BTC bars stressed: {n_stressed} of {n_total} "
            f"({round(n_stressed / n_total * 100, 2)}%)"
        )

        is_trades = tag_trades(ITER045_IS, regime_lookup)
        oos_trades = tag_trades(ITER045_OOS, regime_lookup)

        rows = threshold_sweep_summary(is_trades, oos_trades, t_label, dd_t, vz_t)
        all_rows.extend(rows)

        # Highlight key finding: TRX SHORT in stressed vs healthy regime
        df = pd.DataFrame(rows)
        trx_short = df[(df["direction"] == "SHORT") & (df["regime"] == "STRESSED")]
        for _, r in trx_short.iterrows():
            print(
                f"  TRX SHORT {r['set']} STRESSED: n={r['n_trades']}, WR={r['win_rate_pct']}%, "
                f"weighted_pnl={r['weighted_pnl_sum']}"
            )
        trx_long = df[(df["direction"] == "LONG") & (df["regime"] == "STRESSED")]
        for _, r in trx_long.iterrows():
            print(
                f"  TRX LONG  {r['set']} STRESSED: n={r['n_trades']}, WR={r['win_rate_pct']}%, "
                f"weighted_pnl={r['weighted_pnl_sum']}"
            )

    # Persist
    out_csv = ANALYSIS_DIR / "regime_threshold_sweep.csv"
    df_all = pd.DataFrame(all_rows)
    df_all.to_csv(out_csv, index=False)
    print(f"\nWrote: {out_csv}")

    # Summary table
    print("\n" + "=" * 78)
    print("SUMMARY — TRX SHORT stressed-regime stratification across thresholds")
    print("=" * 78)
    pivot = df_all[
        (df_all["direction"] == "SHORT") & (df_all["regime"] == "STRESSED")
    ][["threshold_label", "set", "n_trades", "win_rate_pct", "weighted_pnl_sum"]]
    print(pivot.to_string(index=False))

    print("\n" + "=" * 78)
    print("SUMMARY — TRX LONG stressed-regime collateral (would be blocked too)")
    print("=" * 78)
    pivot_long = df_all[
        (df_all["direction"] == "LONG") & (df_all["regime"] == "STRESSED")
    ][["threshold_label", "set", "n_trades", "win_rate_pct", "weighted_pnl_sum"]]
    print(pivot_long.to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
