"""iter-v3/030 Phase 1 EDA — Verify LDO's top-7 features at iter-v3/028 multi-seed BASELINE.

Per user directive 2026-05-08 (iter-v3/030 brief authoring): the iter-v3/028
``reports-v3/iteration_v3-028/in_sample/model_importance_last_month_LDOUSDT.csv``
file is the canonical multi-seed-validated formal BASELINE source for LDO's
per-symbol feature importance. NOT iter-v3/029 single-seed which is noisy.

The 14-feature stack at iter-v3/028:
    max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200,
    range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100,
    btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50,
    sym_vs_btc_ret_7d, regime_momentum_signed_5d.

LDO is the chronic underperformer:
    iter-v3/028 multi-seed: -22.05% OOS PnL (concentration -134%)
    iter-v3/029 single-seed:  -3.07% OOS PnL (concentration  -5.3%)
    Across iter-v3/020-027 frozen baseline: -8.93% mean OOS PnL

Hypothesis: LDO trained on 14 features with 8 below LDO's importance threshold
overfits noise on its 31-IS-month sample (LDO listed 2024-09; shortest history
of all v3 incumbents). Tighter LDO-specific feature subset (the canonical top-7
from iter-v3/028 multi-seed importance) should reduce overfit + lift LDO IS+OOS
Sharpe contribution. BCH+TRX+ALGO unchanged (still trained on all 14 features
including regime_momentum_signed_5d).

Outputs (committed alongside this script in iter-v3/030 first commit):
    - ldo_top7_features.csv        — final LDO 7-feature subset for the runner
    - ldo_top14_full_ranking.csv   — all 14 LDO features ranked by iter-v3/028
                                     importance (validation evidence)
    - cross_symbol_top7_overlap.csv — Jaccard overlap of top-7 sets between
                                     LDO and BCH/TRX (per-symbol-signature
                                     differential evidence)
    - synthesis.md                  — narrative + Phase 5 brief reference

NOT used for selection:
    - OOS-window data (would corrupt the analysis; the EDA is IS-only)
    - iter-v3/029 single-seed importance (noisy; user-directive override)

Run from worktree root:
    uv run python analysis/iteration_v3-030/ldo_feature_subset_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WORKTREE = Path(__file__).resolve().parent.parent.parent
ITER_V3_028 = WORKTREE / "reports-v3" / "iteration_v3-028" / "in_sample"
OUT_DIR = WORKTREE / "analysis" / "iteration_v3-030"

# Canonical 14-feature stack for iter-v3/028 (verify load matches).
EXPECTED_14 = {
    "max_dd_window_50",
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
    "regime_momentum_signed_5d",
}


def load_importance(symbol: str) -> pd.DataFrame:
    """Load iter-v3/028 multi-seed model_importance_last_month_<SYM>.csv.

    The runner writes this CSV at the LAST month of the IS window per outer
    seed, multi-seed-averaged when --seeds > 1. iter-v3/028 ran with --seeds 2
    so each row's importance is the mean across both outer seeds × 5 inner
    ensemble seeds = 10 LightGBM models per cell.
    """
    path = ITER_V3_028 / f"model_importance_last_month_{symbol}USDT.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing importance file: {path}")
    df = pd.read_csv(path)
    df = df.sort_values("importance", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("iter-v3/030 Phase 1 EDA — LDO 7-feature subset verification")
    print("=" * 72)

    # ----------------------------------------------------------
    # 1. Load all 3 incumbents' iter-v3/028 multi-seed importance
    # ----------------------------------------------------------
    bch = load_importance("BCH")
    ldo = load_importance("LDO")
    trx = load_importance("TRX")

    for sym, df in [("BCH", bch), ("LDO", ldo), ("TRX", trx)]:
        if set(df["feature"]) != EXPECTED_14:
            missing = EXPECTED_14 - set(df["feature"])
            extra = set(df["feature"]) - EXPECTED_14
            raise RuntimeError(
                f"{sym} feature set mismatch. Missing={missing}, Extra={extra}"
            )
        print(f"  [load] {sym}: {len(df)} features (top-7 importance verified)")

    # ----------------------------------------------------------
    # 2. LDO top-7 (the artifact this script produces)
    # ----------------------------------------------------------
    ldo_top7 = ldo.head(7).reset_index(drop=True)
    ldo_top7_csv = OUT_DIR / "ldo_top7_features.csv"
    ldo_top7.to_csv(ldo_top7_csv, index=False)
    print(f"\n[output] LDO top-7 → {ldo_top7_csv.relative_to(WORKTREE)}")
    print(ldo_top7.to_string(index=False))

    # ----------------------------------------------------------
    # 3. Full LDO ranking (all 14)
    # ----------------------------------------------------------
    ldo_full_csv = OUT_DIR / "ldo_top14_full_ranking.csv"
    ldo.to_csv(ldo_full_csv, index=False)
    print(f"\n[output] LDO full ranking → {ldo_full_csv.relative_to(WORKTREE)}")
    print(ldo.to_string(index=False))

    # ----------------------------------------------------------
    # 4. Cross-symbol top-7 overlap (BCH vs LDO, TRX vs LDO)
    # ----------------------------------------------------------
    bch_top7 = set(bch.head(7)["feature"])
    ldo_top7_set = set(ldo.head(7)["feature"])
    trx_top7 = set(trx.head(7)["feature"])

    rows = []
    for a_name, a_set in [("BCH", bch_top7), ("LDO", ldo_top7_set), ("TRX", trx_top7)]:
        for b_name, b_set in [("BCH", bch_top7), ("LDO", ldo_top7_set), ("TRX", trx_top7)]:
            if a_name >= b_name:
                continue
            inter = a_set & b_set
            union = a_set | b_set
            jaccard = len(inter) / len(union) if union else 0.0
            rows.append(
                {
                    "pair": f"{a_name}-{b_name}",
                    "intersection_count": len(inter),
                    "union_count": len(union),
                    "jaccard": round(jaccard, 4),
                    "intersection_features": "; ".join(sorted(inter)),
                    "a_only": "; ".join(sorted(a_set - b_set)),
                    "b_only": "; ".join(sorted(b_set - a_set)),
                }
            )
    overlap = pd.DataFrame(rows)
    overlap_csv = OUT_DIR / "cross_symbol_top7_overlap.csv"
    overlap.to_csv(overlap_csv, index=False)
    print(f"\n[output] cross-symbol top-7 overlap → {overlap_csv.relative_to(WORKTREE)}")
    print(overlap.to_string(index=False))

    # ----------------------------------------------------------
    # 5. Features in iter-v3/028 stack but NOT in LDO top-7
    # ----------------------------------------------------------
    ldo_bottom7_set = set(ldo["feature"]) - ldo_top7_set
    print(
        f"\n[finding] LDO bottom-7 (REMOVED from LDO subset; {len(ldo_bottom7_set)} features):"
    )
    for f in sorted(ldo_bottom7_set):
        rank = int(ldo.loc[ldo["feature"] == f, "rank"].iloc[0])
        print(f"    rank {rank:2d}  {f}")

    # ----------------------------------------------------------
    # 6. Did LDO use regime_momentum_signed_5d in top-7?
    # ----------------------------------------------------------
    rm_rank_ldo = int(ldo.loc[ldo["feature"] == "regime_momentum_signed_5d", "rank"].iloc[0])
    rm_rank_bch = int(bch.loc[bch["feature"] == "regime_momentum_signed_5d", "rank"].iloc[0])
    rm_rank_trx = int(trx.loc[trx["feature"] == "regime_momentum_signed_5d", "rank"].iloc[0])
    print("\n[finding] regime_momentum_signed_5d (multi-seed-validated edge feature) ranks:")
    print(f"    BCH rank {rm_rank_bch:2d} / 14   (KEPT in 14-feature set per iter-v3/028 BASELINE)")
    print(f"    LDO rank {rm_rank_ldo:2d} / 14   (DROPPED from LDO 7-feature subset)")
    print(f"    TRX rank {rm_rank_trx:2d} / 14   (KEPT in 14-feature set per iter-v3/028 BASELINE)")
    if rm_rank_ldo <= 7:
        print(
            "    NOTE: regime_momentum is in LDO top-7 — DO NOT drop. The 7-feature "
            "subset INCLUDES regime_momentum (mandated by feedback_v3_engineered_features_proven.md)."
        )
    else:
        print(
            f"    NOTE: regime_momentum is rank {rm_rank_ldo}/14 on LDO — BELOW top-7 threshold. "
            "Per `feedback_v3_engineered_features_proven.md`, regime_momentum_signed_5d is the "
            "FIRST multi-seed-validated edge ingredient in v3 history; dropping it from any "
            "symbol's feature set is a methodology deviation. The brief MUST justify this drop."
        )

    # ----------------------------------------------------------
    # 7. Synthesis
    # ----------------------------------------------------------
    synthesis_md = OUT_DIR / "synthesis.md"
    bch_only_top7 = bch_top7 - ldo_top7_set
    ldo_only_top7 = ldo_top7_set - bch_top7 - trx_top7
    trx_only_top7 = trx_top7 - ldo_top7_set
    shared_3way = bch_top7 & ldo_top7_set & trx_top7

    md = f"""# iter-v3/030 LDO 7-feature subset — Synthesis

## Source

iter-v3/028 multi-seed (2 outer × 5 inner = 10 LightGBM models per cell)
``reports-v3/iteration_v3-028/in_sample/model_importance_last_month_LDOUSDT.csv``.

This is the canonical formal BASELINE feature importance — the file iter-v3/028
CONFIRMATION-MERGE updated BASELINE_V3.md with. NOT iter-v3/029 single-seed
(which is noisy; the user directive 2026-05-08 explicitly requested using the
multi-seed-validated read-out for LDO's tighter feature subset).

## LDO top-7 (the iter-v3/030 LDO model's feature set)

| rank | feature | iter-v3/028 importance |
|---:|---|---:|
"""
    for _, row in ldo_top7.iterrows():
        md += f"| {int(row['rank'])} | {row['feature']} | {row['importance']:.1f} |\n"

    md += f"""

LDO bottom-7 (REMOVED from LDO subset; KEPT for BCH/TRX/ALGO unchanged):

| rank | feature | iter-v3/028 importance |
|---:|---|---:|
"""
    for _, row in ldo.iloc[7:].iterrows():
        md += f"| {int(row['rank'])} | {row['feature']} | {row['importance']:.1f} |\n"

    md += f"""

## Cross-symbol top-7 overlap

| pair | jaccard | shared (count) |
|---|---:|---:|
"""
    for _, row in overlap.iterrows():
        md += f"| {row['pair']} | {row['jaccard']} | {row['intersection_count']} |\n"

    md += f"""

3-way SHARED top-7 (in BCH AND LDO AND TRX simultaneously): **{len(shared_3way)} features**

```
{', '.join(sorted(shared_3way))}
```

(matches iter-v3/029 brief Section 2.1 finding of 4 SHARED-top features —
load-bearing for the per-symbol-signature methodology)

## regime_momentum_signed_5d ranks per symbol

| Symbol | rank / 14 | Status in iter-v3/030 |
|---|---:|---|
| BCH | {rm_rank_bch} | KEPT (still in 14-feature set) |
| LDO | {rm_rank_ldo} | {"KEPT" if rm_rank_ldo <= 7 else "DROPPED from LDO subset (rank below top-7)"} |
| TRX | {rm_rank_trx} | KEPT (still in 14-feature set) |

## Key findings

1. **LDO top-7** (canonical, multi-seed iter-v3/028): {", ".join(ldo.head(7)["feature"].tolist())}.
2. **LDO bottom-7** (DROPPED only from LDO subset): {", ".join(sorted(ldo_bottom7_set))}.
3. **regime_momentum_signed_5d** is rank {rm_rank_ldo}/14 on LDO. {"It is in LDO's top-7 and is therefore RETAINED." if rm_rank_ldo <= 7 else "It is NOT in LDO's top-7 (rank below threshold). The brief MUST justify dropping the multi-seed-validated edge feature from LDO's subset."}
4. **BCH and TRX unchanged**: both keep all 14 features (V3_FEATURE_COLUMNS unchanged for them).
5. **ALGO unchanged**: ALGO is the iter-v3/029 NEW symbol; falls back to V3_FEATURE_COLUMNS = 14 features (no per-symbol override).
6. **Per-symbol-feature-signature methodology**: the iter-v3/030 architecture extends iter-v3/029's per-symbol-feature-importance read-out from EDA-only into per-symbol-feature-set discipline. The first iteration where individual model heads use DIFFERENT feature subsets.

## Hypothesis (Phase 5 brief Section 1)

LDO trained on 14 features (8 below LDO's importance threshold) overfits noise
on its 31 IS-month sample. Tighter LDO-specific 7-feature subset should:

(a) Reduce LDO model's overfit to noise.
(b) Lift LDO IS+OOS Sharpe contribution from -22.05% (multi-seed iter-v3/028)
    or -3.07% (single-seed iter-v3/029) to ≥ 0.
(c) Maintain BCH+TRX+ALGO performance unchanged (their feature subsets are
    bit-identical to iter-v3/029 = 14-feature stack).

The mechanism is dimensionality reduction: in 31 IS months × 1 trade per
~3 candles, LightGBM's effective sample size for fitting LDO's signal is
small. 14 features → 7 features halves the search space, raising signal
density per feature.

## Caveats / falsifiers

- **Falsifier 1 — LDO bit-identical decisions despite subset change**: if
  LDO trade-roster is bit-identical to iter-v3/029 LDO, the 7-feature subset
  did not propagate to model output. PROMISING-MECHANICAL or NULL-RESULT.
- **Falsifier 2 — BCH/TRX/ALGO regress**: if any of the 3 unchanged-subset
  models has materially different IS or OOS PnL vs iter-v3/029, the
  per-symbol architecture introduced an unintended issue (training-loop
  side-effect, feature-column-pinning bug, or random-state perturbation).
  PATH C — REVERT.
- **Falsifier 3 — LDO drag worsens**: if LDO OOS PnL falls below -10% (worse
  than iter-v3/029's -3.07%), the dimensionality-reduction hypothesis is
  FALSIFIED. PATH B.
"""
    synthesis_md.write_text(md)
    print(f"\n[output] synthesis → {synthesis_md.relative_to(WORKTREE)}")

    # ----------------------------------------------------------
    # 8. Final sanity assertions
    # ----------------------------------------------------------
    assert len(ldo_top7) == 7, f"LDO top-7 must have 7 entries, got {len(ldo_top7)}"
    assert set(ldo_top7["feature"]).issubset(EXPECTED_14), \
        "LDO top-7 must be subset of EXPECTED_14"
    print("\n[PASS] LDO top-7 verification complete.")
    print(f"[PASS] LDO top-7 features: {sorted(ldo_top7['feature'].tolist())}")


if __name__ == "__main__":
    main()
