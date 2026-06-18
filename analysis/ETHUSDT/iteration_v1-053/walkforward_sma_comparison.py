"""iter-v1/053-054 — WALK-FORWARD OPTUNA SMA SELECTION vs FIXED-200 (ETH), 2026-06-18.

POST-HOC EVALUATION script (Phase 7). NOT an IS-design script: it deliberately reads BOTH
the IS and OOS backtest trade CSVs of already-run iterations and splits them at OOS_CUTOFF
to compare the two regimes — so there is no IS-only leak-guard here (the OOS read is the
whole point of the IS-vs-OOS comparison). The leak-safety that matters lives in the
SELECTION itself (lgbm.LightGbmStrategy._simulate_trend_window): the per-month SMA window is
chosen on train_start..train_end ONLY, proven leak-free by a future-data-perturbation test.

WHAT IT SHOWS (consistent apples-to-apples monthly-sum aggregation across all iters; the
per-iter comparison.csv uses each iter's own vol-targeted/weighted series, so absolute
Sharpes differ — the RELATIVE finding is the robust claim):

  iter-034  fixed SMA=200             IS +0.75 / OOS +0.82 / FULL +0.78   (the merged baseline)
  iter-053  walk-forward SMA 50..400  IS -0.32 / OOS +0.60 / FULL -0.07   (worse every seg + yr)
  iter-054  walk-forward SMA 100..300 IS +0.04 / OOS +0.60 / FULL +0.22   (plateau recovers IS
              from -0.32 but still far below fixed-200; finding holds regardless of grid width)

FINDING: naive walk-forward Optuna selection of the trend SMA window UNDERPERFORMS the fixed
200. The window that maximizes the TRAILING 24-month Sharpe overfits the trailing regime and
fails on regime shifts: in 2022-01 it picked a LONG window (400) because the 2020-21 bull
rewarded slow trend-following, then that slow SMA LAGGED into the 2022 bear and stayed long
through the crash (-41.5% vs the fixed-200's +50.9%); in 2023-24 chop it picked SHORT windows
(50-125) that whipsawed. The fixed 200 generalizes better precisely because it is a
non-overfit prior. => This is the direct answer to the "is the 200 cheated / how do we tune
it?" worry: 200 is a robust crypto-canonical prior; legitimately re-tuning it per-month on a
rolling basis makes it WORSE, not better. Keep it fixed.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
ITERS = {
    "iter-034 fixed-200": "reports-v1/ETHUSDT/iteration_v1-034",
    "iter-053 wf-SMA 50..400": "reports-v1/ETHUSDT/iteration_v1-053",
    "iter-054 wf-SMA 100..300": "reports-v1/ETHUSDT/iteration_v1-054",
}


def monthly(iterdir: str) -> pd.DataFrame | None:
    frames = []
    for sub in ("in_sample", "out_of_sample"):
        p = f"{iterdir}/{sub}/trades.csv"
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        tcol = "close_time" if "close_time" in d.columns else "open_time"
        pcol = "net_pnl_pct" if "net_pnl_pct" in d.columns else "pnl_pct"
        d["m"] = pd.to_datetime(d[tcol], unit="ms").dt.to_period("M")
        frames.append(d[["m", pcol]].rename(columns={pcol: "pnl"}))
    if not frames:
        return None
    return pd.concat(frames).groupby("m")["pnl"].agg(["sum", "count"])


def sharpe(x: pd.Series) -> float:
    return x.mean() / x.std() * np.sqrt(12) if len(x) > 1 and x.std() > 0 else float("nan")


def main() -> None:
    for name, d in ITERS.items():
        m = monthly(d)
        if m is None:
            print(f"{name}: (no reports)")
            continue
        m.index = m.index.to_timestamp()
        for seg, lo, hi in [
            ("FULL", pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")),
            ("IS", pd.Timestamp("2000-01-01"), OOS_CUTOFF),
            ("OOS", OOS_CUTOFF, pd.Timestamp("2100-01-01")),
        ]:
            seg_df = m[(m.index >= lo) & (m.index < hi)]
            print(
                f"{name:28s} {seg:4s}: Sharpe={sharpe(seg_df['sum']):+.3f} "
                f"(n={int(seg_df['count'].sum())})"
            )
        print()


if __name__ == "__main__":
    main()
