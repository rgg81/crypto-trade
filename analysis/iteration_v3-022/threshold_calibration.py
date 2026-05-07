"""Threshold calibration for iter-v3/022 regime gate.

Observed: max DD% in 2022-09..2023-03 = 26.3%, max |vol z| = 1.65.
The naive 30%/2.5 thresholds NEVER FIRE in the target window.

This script searches for an IS-only-calibrated threshold pair that:
  (a) captures the high-PBO TRX cells (PBO ≥ 0.99 in 2022-10 + 2023-01)
  (b) does NOT blanket-kill TRX trades across the whole IS window
  (c) is past-only (no peeking)

We sweep DD thresholds in {15, 18, 20, 22, 25}% and |vol z| thresholds in
{1.0, 1.25, 1.5, 1.75, 2.0}. For each pair, we report:
  - n_TRX_kills_2022Q4_2023Q1 (target window)
  - n_TRX_kills_total_IS (IS-wide)
  - frac_high_PBO_cells_with_fire (the metric the gate is designed to fix)
  - PnL preservation ratio (kept / total)

Output: analysis/iteration_v3-022/threshold_calibration.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd

from regime_gate_eda import (
    ANALYSIS_DIR,
    OOS_CUTOFF_MS,
    build_btc_signal,
    load_btc,
    load_trx_is_trades,
    ms_to_month,
)
from regime_gate_eda import compute_btc_drawdown_30d, compute_btc_vol_zscore


def grid_search() -> pd.DataFrame:
    btc = load_btc()
    btc["dd_pct_30d"] = compute_btc_drawdown_30d(btc)
    btc["vol_zscore_30d"] = compute_btc_vol_zscore(btc)
    trx = load_trx_is_trades()

    # Pre-compute per-trade BTC bar lookup
    btc_open_times = btc["open_time"].astype(np.int64).to_numpy()
    btc_dd = btc["dd_pct_30d"].to_numpy()
    btc_vol = btc["vol_zscore_30d"].to_numpy()

    trx_idxs = (
        np.searchsorted(btc_open_times, trx["open_time"].astype(np.int64).to_numpy(), side="left")
        - 1
    )
    trx_idxs = np.clip(trx_idxs, 0, len(btc_open_times) - 1)
    trx_dd_at_entry = btc_dd[trx_idxs]
    trx_vol_at_entry = btc_vol[trx_idxs]

    target_months = ["2022-10", "2022-11", "2022-12", "2023-01", "2023-02", "2023-03"]
    high_pbo_target_months = ["2022-10", "2023-01"]

    rows = []
    dd_grid = [15.0, 18.0, 20.0, 22.0, 25.0]
    vol_grid = [1.0, 1.25, 1.5, 1.75, 2.0]
    for dd_t in dd_grid:
        for vol_t in vol_grid:
            killed = (trx_dd_at_entry > dd_t) | (np.abs(trx_vol_at_entry) > vol_t)
            killed = np.where(np.isnan(trx_dd_at_entry) & np.isnan(trx_vol_at_entry), False, killed)
            n_killed_full = int(killed.sum())
            n_total = len(trx)
            kill_rate_full_pct = n_killed_full / n_total * 100

            # Target-window subset
            trx_target = trx[trx["month"].isin(target_months)]
            mask_target = trx["month"].isin(target_months).to_numpy()
            n_killed_target = int(killed[mask_target].sum())
            n_target = int(mask_target.sum())

            # High-PBO cell fire (2022-10 + 2023-01: do gate fires happen IN those months?)
            n_high_pbo_with_fire = 0
            for mo in high_pbo_target_months:
                mask_month = trx["month"].eq(mo).to_numpy()
                if killed[mask_month].any():
                    n_high_pbo_with_fire += 1

            # PnL preservation (IS-wide)
            pnl_total = float(trx["weighted_pnl"].sum())
            pnl_arr = trx["weighted_pnl"].to_numpy()
            pnl_kept = float(pnl_arr[~killed].sum())
            pnl_preservation = pnl_kept / pnl_total if pnl_total != 0 else 0.0

            rows.append(
                {
                    "dd_threshold_pct": dd_t,
                    "vol_zscore_threshold": vol_t,
                    "n_killed_full_IS": n_killed_full,
                    "n_total_IS": n_total,
                    "kill_rate_full_pct": kill_rate_full_pct,
                    "n_killed_target_window": n_killed_target,
                    "n_target_window": n_target,
                    "n_high_pbo_cells_with_fire": n_high_pbo_with_fire,
                    "pnl_total": pnl_total,
                    "pnl_kept": pnl_kept,
                    "pnl_preservation_ratio": pnl_preservation,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["n_high_pbo_cells_with_fire", "pnl_preservation_ratio"],
        ascending=[False, False],
    )


def main() -> None:
    df = grid_search()
    df.to_csv(ANALYSIS_DIR / "threshold_calibration.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
