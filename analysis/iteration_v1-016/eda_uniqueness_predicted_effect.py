"""iter-v1/016 EDA — predict effect of `sample_uniqueness=True` on weight distribution.

Uses the production `compute_sample_uniqueness` function on a sampled IS training
window to verify the prediction that for dense daily-labels in 21-candle horizon,
uniqueness ≈ 1/21 for all rows, effectively uniformizing weights.

Final answer: if uniqueness effectively makes all weights equal to 1/21 × baseline_w,
then the multiplication train_weights *= uniq DOES NOT change relative weights
across samples. The TRUE effect is that LightGBM is fed weights ~10× smaller in
magnitude — which doesn't change the loss surface at all (relative weights matter,
not absolute).

This means **simply enabling `sample_uniqueness=True` may have ZERO effect** at v1's
dense-label regime — it's a near-no-op multiplication by a constant.

To actually flatten the weight distribution, we need a different intervention:
either
(a) Replace `abs(labeled_pnl)` with uniform 1.0 (KILL the existing weighting), OR
(b) Replace with 1/abs(labeled_pnl) (INVERT — downweight high-PnL outliers)
(c) Use uniqueness only AND set baseline weights to uniform (combine `sample_weighting_mode=uniform`
    with `sample_uniqueness=True`)

This script tests these analytically using the production label_trades + uniqueness path.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402
from crypto_trade.strategies.ml.labeling import (  # noqa: E402
    compute_sample_uniqueness,
    label_trades,
)

OUTPUT_DIR = Path(__file__).parent


def _kish_n_eff(weights: np.ndarray) -> float:
    s = weights.sum()
    s2 = (weights ** 2).sum()
    if s2 == 0:
        return 0.0
    return float((s ** 2) / s2)


def main():
    print("\n=== iter-v1/016 EDA — `sample_uniqueness` effect prediction ===")
    print("Using PRODUCTION compute_sample_uniqueness from labeling.py")
    print()

    # Build a master DataFrame for one symbol pair (BTC+ETH = Model A) over IS window
    klines_dir = REPO / "data"
    masters = []
    for sym in ["BTCUSDT", "ETHUSDT"]:
        k_csv = klines_dir / sym / "8h.csv"
        kdf = pd.read_csv(k_csv)
        kdf = kdf[kdf["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        kdf["symbol"] = sym
        masters.append(kdf)
    master = pd.concat(masters, ignore_index=True)
    master = master.sort_values(["open_time", "symbol"]).reset_index(drop=True)
    print(f"Master rows (BTC+ETH IS): {len(master)}")

    # Compute ATR per symbol via groupby (production wires this similarly)
    def _atr(grp, period=14):
        h, l, c = grp["high"].values, grp["low"].values, grp["close"].values
        tr = np.maximum(
            h - l,
            np.maximum(
                np.abs(h - np.roll(c, 1)),
                np.abs(l - np.roll(c, 1)),
            ),
        )
        tr[0] = h[0] - l[0]
        atr = np.zeros_like(tr)
        atr[:period] = np.nan
        atr[period - 1] = tr[:period].mean()
        for i in range(period, len(tr)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        grp = grp.copy()
        grp["atr14"] = atr
        return grp

    # Per-symbol ATR — explicit loop to preserve all columns including symbol
    atr_dfs = []
    for sym, grp in master.groupby("symbol"):
        atr_dfs.append(_atr(grp))
    master = pd.concat(atr_dfs, ignore_index=True)
    master = master.sort_values(["open_time", "symbol"]).reset_index(drop=True)

    # Use a window-of-rows as the training set (last 24 months IS, walk-forward style — final month)
    # Subsample: pick rows where atr is not NaN
    valid_idx = master.index[master["atr14"].notna()].to_numpy()
    print(f"Valid (non-NaN ATR) rows: {len(valid_idx)}")

    # Run label_trades for one trailing 24-month window (anchor = last IS month)
    last_open = master["open_time"].max()
    window_start = last_open - 24 * 30 * 24 * 3600 * 1000  # approx 24 months ms
    train_mask = (master["open_time"] >= window_start) & (master["open_time"] < OOS_CUTOFF_MS)
    train_indices = master.index[train_mask & master["atr14"].notna()].to_numpy()
    print(f"Training window indices (last 24 months): {len(train_indices)} rows")

    atr_values = master["atr14"].to_numpy()
    labels, baseline_weights, long_pnls, short_pnls = label_trades(
        master,
        train_indices,
        tp_pct=2.9,  # ATR multiplier (use_atr=True path)
        sl_pct=1.5,
        timeout_minutes=10080,
        fee_pct=0.1,
        atr_values=atr_values,
        verbose=0,
    )
    print(f"label_trades returned: labels={len(labels)}, weights range=[{baseline_weights.min():.3f}, {baseline_weights.max():.3f}]")

    # Compute uniqueness
    open_time_arr = master["open_time"].to_numpy()
    sym_arr = master["symbol"].to_numpy(dtype=str)
    uniq = compute_sample_uniqueness(
        train_indices,
        timeout_minutes=10080,
        open_time_arr=open_time_arr,
        sym_arr=sym_arr,
    )
    print(f"uniqueness range: [{uniq.min():.4f}, {uniq.max():.4f}], mean={uniq.mean():.4f}")
    print(f"uniqueness std: {uniq.std():.4f} (LOW std = constant-ish across rows)")

    # Compare distributions: baseline_w vs baseline_w × uniq
    final_w = baseline_weights * uniq
    print(f"\nBaseline weights:  Kish n_eff = {_kish_n_eff(baseline_weights):.1f} / actual n = {len(baseline_weights)}")
    print(f"× uniqueness:      Kish n_eff = {_kish_n_eff(final_w):.1f} / actual n = {len(final_w)}")
    print(f"Pure uniform:      Kish n_eff = {len(baseline_weights):.1f} (= n)")
    print(f"Pure uniqueness:   Kish n_eff = {_kish_n_eff(uniq):.1f}")
    print()

    # Per-symbol weight shares
    sym_arr_train = sym_arr[train_indices]
    for sym in ["BTCUSDT", "ETHUSDT"]:
        mask = sym_arr_train == sym
        baseline_share = float(baseline_weights[mask].sum() / baseline_weights.sum())
        final_share = float(final_w[mask].sum() / final_w.sum())
        pure_uniq_share = float(uniq[mask].sum() / uniq.sum())
        uniform_share = float(mask.sum() / len(mask))
        print(f"  {sym}: baseline={baseline_share:.4f} | baseline×uniq={final_share:.4f} | "
              f"pure_uniq={pure_uniq_share:.4f} | uniform={uniform_share:.4f}")

    # CRITICAL question — does multiplying by uniq change the *relative* weight order?
    # Compute correlation between baseline_w and baseline_w × uniq
    if len(baseline_weights) > 1:
        corr_ranks = float(pd.Series(baseline_weights).rank().corr(pd.Series(final_w).rank()))
        print(f"\nSpearman rank correlation (baseline_w vs baseline_w × uniq): {corr_ranks:.4f}")
        print("If ~1.0, multiplying by uniq doesn't change relative weights → no Optuna effect")

    # Write per-row weights for downstream analysis
    out = pd.DataFrame({
        "idx": train_indices,
        "symbol": sym_arr[train_indices],
        "label": labels,
        "long_pnl": long_pnls,
        "short_pnl": short_pnls,
        "w_baseline": baseline_weights,
        "uniqueness": uniq,
        "w_baseline_x_uniq": final_w,
    })
    out.to_csv(OUTPUT_DIR / "uniqueness_effect_prediction.csv", index=False)
    print(f"\n[OK] Per-row weights saved to {OUTPUT_DIR}/uniqueness_effect_prediction.csv")

    # Final prediction summary
    print("\n## PREDICTION SUMMARY")
    print(f"Baseline weight Kish n_eff: {_kish_n_eff(baseline_weights):.1f} ({_kish_n_eff(baseline_weights)/len(baseline_weights):.1%} of n)")
    print(f"With uniqueness:            {_kish_n_eff(final_w):.1f} ({_kish_n_eff(final_w)/len(baseline_weights):.1%} of n)")
    print(f"Change in n_eff_kish:       {(_kish_n_eff(final_w) - _kish_n_eff(baseline_weights)) / max(_kish_n_eff(baseline_weights),1):+.1%}")

    # CONCLUSION + RECOMMENDATION
    rank_corr = float(pd.Series(baseline_weights).rank().corr(pd.Series(final_w).rank()))
    if rank_corr > 0.99:
        print("\n[CONCLUSION] sample_uniqueness=True is NEAR-NO-OP at v1's dense-label regime.")
        print("Rank-order of weights is preserved (rank corr = {:.3f}); only absolute scale shifts.".format(rank_corr))
        print("LightGBM's gradient is scale-invariant → no Optuna effect.")
        print("RECOMMENDATION: enabling sample_uniqueness alone WILL NOT change behavior materially.")
        print("Real interventions for n_eff diversification:")
        print("  (a) REPLACE abs(labeled_pnl) with uniform 1.0 (kill outlier-domination)")
        print("  (b) REPLACE with 1/abs(labeled_pnl) (invert — explicitly downweight outliers)")
        print("  (c) WINSORIZE abs_pnl at p90/p95 before normalization")


if __name__ == "__main__":
    main()
