"""Analyze the v1 baseline core reproduction (reports/iteration_152_core/).

Compares against BASELINE.md's +2.83 OOS Sharpe target across two windows:
1. Feb-2026-cutoff window (baseline measurement window, exclusive of Apr 2026)
2. Apr-2026 window (full fresh OOS through 2026-04-19)

Also computes per-symbol breakdown, per-month OOS decay, and per-model contribution.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASELINE_OOS_SHARPE = 2.83  # BASELINE.md iter-152
BASELINE_OOS_MAXDD = 21.81
BASELINE_OOS_PF = 1.76

# iter-152 BASELINE was measured on data through ~2026-02-28 (before
# Apr 2026 data arrived). Use this cutoff to verify the reproduction
# on the EXACT baseline window.
FEB_CUTOFF_MS = int(pd.Timestamp("2026-03-01", tz="UTC").timestamp() * 1000)


def _load(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"Report not yet generated: {p}")
    df = pd.read_csv(p)
    df["open_time"] = pd.to_numeric(df["open_time"])
    df["close_time"] = pd.to_numeric(df["close_time"])
    return df


def _daily_pnl(df: pd.DataFrame) -> pd.Series:
    """Zero-filled daily PnL in % (matches v1 Sharpe methodology)."""
    if df.empty:
        return pd.Series(dtype=float)
    ts = pd.to_datetime(df["close_time"], unit="ms")
    daily = df.assign(_d=ts.dt.date).groupby("_d")["weighted_pnl"].sum() / 100.0
    start = pd.Timestamp(daily.index.min())
    end = pd.Timestamp(daily.index.max())
    idx = pd.date_range(start, end, freq="D").date
    return daily.reindex(idx, fill_value=0.0)


def _sharpe_daily(df: pd.DataFrame) -> float:
    """Annualized Sharpe on zero-filled daily returns × sqrt(365)."""
    daily = _daily_pnl(df)
    if len(daily) < 2 or daily.std() == 0:
        return 0.0
    return float(daily.mean() / daily.std() * np.sqrt(365))


def _sharpe_trade(w: np.ndarray) -> float:
    if len(w) < 2 or w.std() == 0:
        return 0.0
    return float(w.mean() / w.std() * np.sqrt(len(w)))


def _maxdd(df: pd.DataFrame) -> float:
    daily = _daily_pnl(df)
    if len(daily) < 2:
        return 0.0
    equity = (1 + daily).cumprod()
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(-dd.min() * 100)


def _pf(w: np.ndarray) -> float:
    pos = w[w > 0].sum()
    neg = -w[w < 0].sum()
    return float(pos / neg) if neg > 0 else float("inf")


def _summarize(df: pd.DataFrame, label: str) -> None:
    w = df["weighted_pnl"].to_numpy()
    print(f"\n{label}")
    print("-" * 60)
    print(f"  Trades: {len(df)}")
    print(f"  Sharpe (daily × √365): {_sharpe_daily(df):+.4f}")
    print(f"  Sharpe (trade):        {_sharpe_trade(w):+.4f}")
    print(f"  MaxDD:                 {_maxdd(df):.2f}%")
    print(f"  Total wpnl:            {w.sum():+.2f}")
    print(f"  Win rate:              {100 * (w > 0).mean():.1f}%")
    print(f"  PF:                    {_pf(w):.3f}")


def _monthly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["close_time"], unit="ms").dt.to_period("M")
    agg = df.groupby("month").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
        wr=("weighted_pnl", lambda s: 100 * (s > 0).mean()),
    )
    agg["sharpe_trade"] = df.groupby("month")["weighted_pnl"].apply(
        lambda s: _sharpe_trade(s.to_numpy())
    )
    return agg


def _per_symbol(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("symbol").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
        wr=("weighted_pnl", lambda s: 100 * (s > 0).mean()),
    )
    grp["sharpe_trade"] = df.groupby("symbol")["weighted_pnl"].apply(
        lambda s: _sharpe_trade(s.to_numpy())
    )
    grp["sharpe_daily"] = df.groupby("symbol").apply(lambda s: _sharpe_daily(s))
    grp = grp.sort_values("wpnl", ascending=False)
    return grp


def main() -> None:
    rpt = Path("reports/iteration_152_core")
    is_p = rpt / "in_sample" / "trades.csv"
    oos_p = rpt / "out_of_sample" / "trades.csv"

    if not is_p.exists() or not oos_p.exists():
        print(f"Reports not ready yet: {rpt}")
        print("Re-run this script after the backtest completes.")
        return

    is_df = _load(is_p)
    oos_df = _load(oos_p)

    print("=" * 70)
    print("v1 BASELINE CORE REPRODUCTION — iter-152 with 193 BASELINE_FEATURE_COLUMNS")
    print("=" * 70)
    print(f"Baseline target (BASELINE.md iter-152): OOS Sharpe +{BASELINE_OOS_SHARPE}")
    print(f"                                        MaxDD {BASELINE_OOS_MAXDD}%")
    print(f"                                        PF {BASELINE_OOS_PF}")

    # BASELINE window = OOS cutoff (2025-03-24) through end of Feb 2026
    baseline_oos = oos_df[oos_df["close_time"] < FEB_CUTOFF_MS]
    full_oos = oos_df

    print()
    _summarize(is_df, "IS (all trades, 2022-01 → 2025-03-23)")
    _summarize(baseline_oos, "OOS — BASELINE WINDOW (2025-03-24 → 2026-02-28)")
    _summarize(full_oos, "OOS — FULL WINDOW (2025-03-24 → 2026-04-19)")

    # Verdict
    baseline_sharpe = _sharpe_daily(baseline_oos)
    full_sharpe = _sharpe_daily(full_oos)
    print("\n" + "=" * 70)
    print("BASELINE REPRODUCTION VERDICT")
    print("=" * 70)
    delta_baseline = baseline_sharpe - BASELINE_OOS_SHARPE
    delta_pct = 100 * delta_baseline / BASELINE_OOS_SHARPE
    print(f"  Baseline window: +{baseline_sharpe:.2f} vs +{BASELINE_OOS_SHARPE} target  "
          f"(Δ {delta_baseline:+.2f}, {delta_pct:+.1f}%)")
    print(f"  Full window:     +{full_sharpe:.2f} (extends through Apr 2026)")

    if abs(delta_baseline) < 0.25:
        print("\n  → BASELINE REPRODUCED (within ±0.25 Sharpe tolerance)")
    else:
        print(f"\n  → DIVERGENCE: {abs(delta_baseline):.2f} Sharpe off baseline target")

    # Monthly breakdown
    print("\n" + "=" * 70)
    print("OOS MONTHLY BREAKDOWN")
    print("=" * 70)
    monthly = _monthly(full_oos)
    print(monthly.to_string())

    # Per-symbol
    print("\n" + "=" * 70)
    print("OOS PER-SYMBOL (full window)")
    print("=" * 70)
    print(_per_symbol(full_oos).to_string())


if __name__ == "__main__":
    main()
