"""iter-v3/008 Phase 1 — IC redundancy drop analysis.

Reads `ic_matrix.csv` from iter-v3/007 (full v3 universe, top-14 features,
single seed=42 EXPLORATION).  Identifies feature pairs whose absolute Pearson
IC exceeds the v3 hard threshold IC_threshold=0.70 declared in `BASELINE_V3.md`.

Per Critic FINAL review SHA `a544621` Recommendation 1, iter-v3/008 (CONFIRMATION
TYPE) MUST address the carry-forward redundancies before Phase 5.5 PASS.  The
two flagged pairs in iter-v3/007 are:

  - vwap_dev_50  ×  ema_spread_atr_20  =  0.875
  - vwap_dev_50  ×  vwap_dev_20        =  0.794

Both pairs share `vwap_dev_50`.  Dropping that one feature kills BOTH
redundancies in a single move (option (a) per Critic), taking the trained
feature set from 14 to 13.  The remaining 13-feature subset must have NO
pair above 0.70 — verified at the bottom of this script.

This script is IS-only.  It reads only the iter-v3/007 IC matrix (computed on
candles with `close_time < OOS_CUTOFF_DATE = 2025-03-24` — see
`run_baseline_v3.py:_compute_ic_matrix`) and emits:

  - `ic_no_redundancy_subset.csv`  — the 13-feature retained set
  - `dropped_pairs.csv`            — the 2 redundant pairs and which feature
                                     was kept vs dropped
  - `ic_matrix_13.csv`             — the 13×13 IC sub-matrix after drop
                                     (subset of iter-v3/007 ic_matrix.csv)
  - `summary.json`                 — selected_features, dropped_features,
                                     max_residual_ic, n_pairs_above_threshold
  - `synthesis.md`                 — interpretive narrative for brief
                                     Section 2

Run with:
    uv run python analysis/iteration_v3-008/ic_redundancy_drop_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-008"

ITER007_IC = REPO_ROOT / "reports-v3" / "iteration_v3-007" / "ic_matrix.csv"
IC_THRESHOLD = 0.70  # |IC| above this is a redundancy per BASELINE_V3.md


def load_ic_matrix(path: Path) -> pd.DataFrame:
    """Load the iter-v3/007 IC matrix.  First column is the feature name index."""
    df = pd.read_csv(path, index_col=0)
    # Sanity: square, symmetric, diag = 1.
    assert df.shape[0] == df.shape[1], (
        f"IC matrix not square: {df.shape}"
    )
    diag = np.diag(df.to_numpy())
    if not np.allclose(diag, 1.0, atol=1e-6):
        raise ValueError(f"IC matrix diag not all 1.0: {diag}")
    if not np.allclose(df.to_numpy(), df.to_numpy().T, atol=1e-6):
        raise ValueError("IC matrix not symmetric")
    return df


def find_pairs_above_threshold(
    ic: pd.DataFrame, threshold: float
) -> list[tuple[str, str, float]]:
    """Return all (feat_a, feat_b, |IC|) triples with |IC| > threshold.

    Only upper-triangle (a < b alphabetically) so each pair appears once.
    """
    out: list[tuple[str, str, float]] = []
    cols = list(ic.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = cols[i], cols[j]
            v = abs(float(ic.loc[a, b]))
            if v > threshold:
                out.append((a, b, v))
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("iter-v3/008 Phase 1 — IC redundancy drop analysis")
    print("=" * 72)
    print(f"IC matrix: {ITER007_IC.relative_to(REPO_ROOT)}")
    print(f"|IC| threshold: {IC_THRESHOLD}")
    print()

    if not ITER007_IC.exists():
        raise FileNotFoundError(
            f"iter-v3/007 IC matrix not found: {ITER007_IC}.\n"
            "Cannot run iter-v3/008 redundancy analysis without it."
        )

    ic_14 = load_ic_matrix(ITER007_IC)
    feats_14 = list(ic_14.columns)
    print(f"Input: {len(feats_14)}-feature IC matrix from iter-v3/007.")
    assert len(feats_14) == 14, f"Expected 14 features, got {len(feats_14)}"

    # ---------------------------------------------------------------- step 1
    pairs_14 = find_pairs_above_threshold(ic_14, IC_THRESHOLD)
    print(f"\nStep 1 — pairs with |IC| > {IC_THRESHOLD} in 14-feature set:")
    if not pairs_14:
        print("  NONE — no redundancy in iter-v3/007's 14-feature set.")
    for a, b, v in sorted(pairs_14, key=lambda t: -t[2]):
        print(f"  {a:30s} × {b:30s} = {v:.4f}")

    # ---------------------------------------------------------------- step 2
    # Identify which features appear in MULTIPLE redundant pairs.  Dropping a
    # feature that participates in many pairs kills more redundancies per drop.
    appearance: dict[str, int] = {}
    for a, b, _ in pairs_14:
        appearance[a] = appearance.get(a, 0) + 1
        appearance[b] = appearance.get(b, 0) + 1

    print("\nStep 2 — feature appearance count in redundant pairs:")
    for feat, count in sorted(appearance.items(), key=lambda t: -t[1]):
        print(f"  {feat:30s} appears in {count} redundant pair(s)")

    # ---------------------------------------------------------------- step 3
    # Drop the feature that appears in the MOST pairs.  Tie-breaker: keep the
    # one with the LOWER mean importance rank from iter-v3/007 brief Section 2.
    # In iter-v3/007 ranks: vwap_dev_50 = rank 2 (mean 2.5); ema_spread_atr_20
    # = rank 3 (mean 3.0); vwap_dev_20 = rank 12 (mean 13.0).  vwap_dev_50 is
    # the highest-importance of the three, but it is in BOTH pairs — dropping
    # it kills both redundancies in one move.  Critic Recommendation 1 (option
    # (a)) explicitly recommends this drop.
    if not appearance:
        # Vacuous case: no redundancy.  No drop needed.
        to_drop = []
    else:
        max_count = max(appearance.values())
        candidates = [f for f, c in appearance.items() if c == max_count]
        # If a unique most-frequent feature exists, drop it.
        if len(candidates) == 1:
            to_drop = [candidates[0]]
        else:
            # Tie-break: drop the one whose retention forces the most drops
            # (i.e., the one with HIGHER importance is preferred to keep —
            # so drop the one with LOWER importance).  Mean ranks per
            # iter-v3/007 brief Section 2.1 (lower = better):
            mean_ranks = {
                "max_dd_window_50": 2.5,
                "vwap_dev_50": 2.5,
                "ema_spread_atr_20": 3.0,
                "ret_kurt_50": 5.0,
                "ret_skew_200": 5.0,
                "range_realized_vol_50": 6.5,
                "hurst_diff_100_50": 11.5,
                "ret_kurt_200": 11.5,
                "hurst_100": 11.5,
                "btc_ret_14d": 12.5,
                "ret_skew_50": 12.5,
                "vwap_dev_20": 13.0,
                "ret_autocorr_lag1_50": 13.5,
                "sym_vs_btc_ret_7d": 14.5,
            }
            # Drop the candidate with the WORST (highest) rank.
            candidates_sorted = sorted(
                candidates, key=lambda f: -mean_ranks.get(f, 999)
            )
            to_drop = [candidates_sorted[0]]

    print(f"\nStep 3 — DROP decision: {to_drop}")
    if "vwap_dev_50" in to_drop:
        print(
            "  ✓ Matches Critic FINAL Recommendation 1 option (a): "
            "drop vwap_dev_50, kills 2 redundancies in 1 drop."
        )

    # ---------------------------------------------------------------- step 4
    feats_13 = [f for f in feats_14 if f not in to_drop]
    print(f"\nStep 4 — retained 13-feature subset:")
    for i, f in enumerate(feats_13, 1):
        print(f"  {i:2d}. {f}")

    # ---------------------------------------------------------------- step 5
    ic_13 = ic_14.loc[feats_13, feats_13]
    pairs_13 = find_pairs_above_threshold(ic_13, IC_THRESHOLD)
    print(f"\nStep 5 — verify 13-feature subset has NO pair > {IC_THRESHOLD}:")
    if pairs_13:
        print(
            f"  FAIL — {len(pairs_13)} residual pair(s) above threshold:"
        )
        for a, b, v in sorted(pairs_13, key=lambda t: -t[2]):
            print(f"    {a} × {b} = {v:.4f}")
        raise SystemExit(
            "Drop did not eliminate all redundancies — iter-v3/008 brief "
            "must drop additional features OR provide paired-bootstrap proof."
        )
    print("  PASS — no residual redundancy in 13-feature subset.")

    # ---------------------------------------------------------------- step 6
    # Compute the maximum off-diagonal |IC| in the 13-feature subset (for the
    # brief Section 2.3 'headroom' summary).
    ic_13_arr = ic_13.to_numpy()
    np.fill_diagonal(ic_13_arr, 0.0)
    max_residual_ic = float(np.max(np.abs(ic_13_arr)))
    # Find the argmax pair.
    flat_idx = int(np.argmax(np.abs(ic_13_arr)))
    i_max, j_max = np.unravel_index(flat_idx, ic_13_arr.shape)
    max_pair = (feats_13[i_max], feats_13[j_max])
    print(
        f"\nMax off-diagonal |IC| in 13-feature subset: {max_residual_ic:.4f} "
        f"({max_pair[0]} × {max_pair[1]})"
    )
    print(
        f"Headroom to threshold {IC_THRESHOLD}: "
        f"{IC_THRESHOLD - max_residual_ic:+.4f}"
    )

    # ---------------------------------------------------------------- write outputs
    # 1. ic_no_redundancy_subset.csv — 13-row table with retained feature names
    out_subset = pd.DataFrame({
        "rank": range(1, len(feats_13) + 1),
        "feature": feats_13,
    })
    out_subset.to_csv(OUT_DIR / "ic_no_redundancy_subset.csv", index=False)
    print(f"\nWrote: {OUT_DIR / 'ic_no_redundancy_subset.csv'}")

    # 2. dropped_pairs.csv — the 2 redundant pairs plus the drop decision
    dropped_pairs_rows = []
    for a, b, v in sorted(pairs_14, key=lambda t: -t[2]):
        if a in to_drop:
            dropped, kept = a, b
        elif b in to_drop:
            dropped, kept = b, a
        else:
            dropped, kept = "(none)", f"{a},{b}"
        dropped_pairs_rows.append({
            "feature_a": a,
            "feature_b": b,
            "abs_ic": round(v, 6),
            "above_threshold": True,
            "dropped": dropped,
            "kept": kept,
        })
    pd.DataFrame(dropped_pairs_rows).to_csv(
        OUT_DIR / "dropped_pairs.csv", index=False
    )
    print(f"Wrote: {OUT_DIR / 'dropped_pairs.csv'}")

    # 3. ic_matrix_13.csv — 13×13 IC sub-matrix (subset of iter-v3/007's matrix)
    ic_13.to_csv(OUT_DIR / "ic_matrix_13.csv")
    print(f"Wrote: {OUT_DIR / 'ic_matrix_13.csv'}")

    # 4. summary.json — machine-readable summary
    summary = {
        "input_feature_count": len(feats_14),
        "input_redundant_pairs": len(pairs_14),
        "input_redundant_pairs_detail": [
            {"feature_a": a, "feature_b": b, "abs_ic": round(v, 6)}
            for a, b, v in sorted(pairs_14, key=lambda t: -t[2])
        ],
        "feature_appearance_in_pairs": {
            f: appearance.get(f, 0) for f in feats_14
        },
        "dropped_features": list(to_drop),
        "drop_rationale": (
            "vwap_dev_50 appears in BOTH redundant pairs (vwap_dev_50 × "
            "ema_spread_atr_20 = 0.875 AND vwap_dev_50 × vwap_dev_20 = 0.794). "
            "Dropping vwap_dev_50 eliminates BOTH redundancies in a single "
            "move (option (a) per Critic FINAL Recommendation 1, SHA a544621). "
            "Net feature count: 14 → 13."
        ),
        "retained_feature_count": len(feats_13),
        "retained_features": list(feats_13),
        "residual_pairs_above_threshold": len(pairs_13),
        "max_residual_abs_ic": max_residual_ic,
        "max_residual_pair": list(max_pair),
        "headroom_to_threshold": IC_THRESHOLD - max_residual_ic,
        "ic_threshold": IC_THRESHOLD,
    }
    with (OUT_DIR / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote: {OUT_DIR / 'summary.json'}")

    # 5. synthesis.md — narrative for brief Section 2
    synthesis = f"""# iter-v3/008 — IC Redundancy Drop Synthesis

## Input

iter-v3/007 EXPLORATION shipped a 14-feature subset (`V3_FEATURE_COLUMNS_TOP_N`)
chosen by mean importance rank across two prior IS runs.  The Phase 7.5 Critic
review (FINAL SHA `a544621`) flagged two carry-forward feature pairs whose
absolute Pearson IC exceeds the v3 hard threshold `IC_threshold = 0.70`:

| feature_a | feature_b | abs IC |
|---|---|---:|
"""
    for a, b, v in sorted(pairs_14, key=lambda t: -t[2]):
        synthesis += f"| `{a}` | `{b}` | {v:.4f} |\n"

    synthesis += f"""
Both pairs share `vwap_dev_50`.  This is the structural pivot the Critic noted
("the redundancy was masked in earlier IC matrices by the broader 34-feature
dilution"; under colsample-Optuna-sampled production config the redundancy
biases the ensemble).

## Decision (Critic Recommendation 1, option (a))

DROP `vwap_dev_50`.  Because it appears in both flagged pairs, a single drop
eliminates both redundancies.  Net feature count: 14 → 13.

Rationale for choosing option (a) over option (b) (paired-bootstrap CV proof):

- Option (a) ships with one code edit and zero new computation — minimal
  surface area for Phase 5.5 verification.
- Option (b) requires a paired-bootstrap CV pipeline (5–10 outer folds × 50
  bootstrap reps) on iter-v3/007's IS-only data; the wall-clock investment
  (~1–2h) and the risk that the joint-necessity verdict is itself sample-
  dependent (single 14-feature run) outweigh the marginal value of retaining
  `vwap_dev_50`.
- `ema_spread_atr_20` and `vwap_dev_20` both have non-trivial standalone
  importance from iter-v3/007 ranks 3 and 12, so the model is not stripped
  of either VWAP-deviation OR EMA-spread family signal.

## 13-feature subset

| rank | feature |
|---:|---|
"""
    for i, f in enumerate(feats_13, 1):
        synthesis += f"| {i} | `{f}` |\n"

    synthesis += f"""
## Verification

Maximum off-diagonal |IC| in the 13-feature subset: **{max_residual_ic:.4f}**
({max_pair[0]} × {max_pair[1]}).  Headroom to threshold:
**{IC_THRESHOLD - max_residual_ic:+.4f}**.  No pair above 0.70 remains.

## Implication for Phase 6

iter-v3/008 ships a SINGLE source-code edit:

```python
# src/crypto_trade/features_v3/__init__.py
V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
    # iter-v3/008: dropped vwap_dev_50 (Critic Rec 1 SHA a544621)
    "max_dd_window_50",
    # vwap_dev_50  REMOVED — IC 0.875 with ema_spread_atr_20, 0.794 with vwap_dev_20
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 13
```

`run_baseline_v3.py` `_verify_feature_columns()` updates from `n != 14` to
`n != 13`, AND the cosmetic stale runtime banner at line 1315 parametrizes
against `len(V3_FEATURE_COLUMNS)` (Critic Recommendation 4 cleanup).

## Pre-condition checklist

| # | Pre-condition (Critic FINAL SHA `a544621`) | Status |
|---|---|---|
| 1 | IC redundancy carry-forward addressed | DONE — option (a), drop `vwap_dev_50` |
| 2 | Mechanical Section 8 thresholds (no discretion) | Brief Section 0.5 + Section 8 |
| 3 | Per-symbol concentration mechanical gate or ex-ante MKR story | Brief Section 5 — option (a), gate |

All three pre-conditions addressed by the iter-v3/008 brief at this analysis's
commit-time.
"""
    (OUT_DIR / "synthesis.md").write_text(synthesis)
    print(f"Wrote: {OUT_DIR / 'synthesis.md'}")

    print()
    print("=" * 72)
    print("DONE.  Outputs in:", OUT_DIR.relative_to(REPO_ROOT))
    print("=" * 72)


if __name__ == "__main__":
    main()
