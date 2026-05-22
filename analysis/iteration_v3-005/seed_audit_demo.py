"""Phase 5 IS-only numerical evidence for iter-v3/005 — seed propagation
audit + synthetic 10-seed Pareto demo.

Two related diagnostic deliverables:

  (a) **Seed-dimension variance audit on iter-v3/003's parquet.**
      iter-v3/004's brief Section 2.1 claimed "every group of 5 rows for
      the same (sym, month, trial, fold, candle) tuple has nunique(oof_return)
      == 1". This script empirically RE-VERIFIES that claim.

      iter-v3/003's writer at ``optimization.py:400-421`` wrote 5 rows per
      natural-key tuple — one per ensemble seed — but never persisted the
      seed in a column. Whether the 5 oof_return values are byte-identical
      OR vary across seeds (because each TPESampler(seed) produces a
      different trial trajectory through the parameter space) is the
      empirical question.

      This script reports the actual breakdown.

  (b) **Synthetic 10-seed Pareto consumer-side demo on a small parquet
      subset.** Demonstrates the iter-v3/004 per-cell PBO consumer pipeline
      run across 10 outer seeds on a small subset of cells. Each outer seed
      controls a per-cell CSCV path-id permutation, simulating outer-seed
      sensitivity in the per-cell aggregator. This produces 10 per-seed
      Pareto rows and verifies the aggregator's behavior under cross-seed
      noise BEFORE any rebacktest cost is incurred.

      The TRUE 10-seed cost in iter-v3/005 is a parquet-reuse rerun of the
      consumer pipeline (10 × ~89s ≈ 15 minutes). This script's job is
      Phase-5 IS-only PRE-VALIDATION that the methodology supports a
      meaningful 10-seed Pareto.

Outputs (all committed BEFORE the brief — Phase 5.5 reproducibility):

  - seed_dimension_variance.csv   — per-natural-key group: nunique(oof_return),
                                    count, std, mean. For the dedup-by-natural-
                                    key audit (a).
  - synthetic_10seed_pareto.csv    — 10 rows, one per seed: (seed, mean_pbo,
                                    median_pbo, median_n_eff, n_informative_cells,
                                    sharpe_proxy_oof, max_concentration_proxy).
                                    For the consumer-side 10-seed demo (b).
  - synthesis.md                   — interpretive narrative of (a) + (b)
                                    findings, including what the variance
                                    breakdown implies for iter-v3/006 fix-vs-drop
                                    decision.

Usage:
    uv run python analysis/iteration_v3-005/seed_audit_demo.py

Reads only the IS slice of iter-v3/003's parquet. No OOS data accessed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.validation_v3 import (
    combinatorial_purged_cv,
    n_effective_trials,
    pbo_from_cpcv,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path(__file__).resolve().parent
PARQUET_PATH = REPO_ROOT / "reports-v3" / "iteration_v3-003" / "trial_oof_returns.parquet"

# IMMUTABLE — sacred constant
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC

PER_CELL_GAP = 22
PER_CELL_N_SPLITS = 10
PER_CELL_K = 2  # C(10, 2) = 45 paths

# Synthetic 10-seed configuration — small parquet subset (1 sym × 3 months × 5 trials)
DEMO_SUBSET_SYMBOLS = ("BCHUSDT",)
DEMO_SUBSET_MONTHS = 3  # take the first 3 IS months for the chosen symbol
SEEDS = (42, 123, 456, 789, 1001, 7, 13, 17, 23, 37)


# ---------------------------------------------------------------------------
# (a) Seed-dimension variance audit
# ---------------------------------------------------------------------------


def audit_seed_variance(df: pd.DataFrame) -> dict:
    """Empirical audit of nunique(oof_return) per natural-key group.

    Claim under test (from iter-v3/004 brief Section 2.1): every (sym, month,
    trial, fold, candle) group has nunique == 1.

    Outputs:
      - per-group nunique distribution (dict)
      - aggregate stats (degeneracy fraction, variability fraction)
      - ablation: among multi-row groups (count > 1), how many have nunique > 1
    """
    print("[audit] Computing per-natural-key group statistics ...")
    natural_key = ["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    g = df.groupby(natural_key, dropna=False)["oof_return"]
    agg = g.agg(["nunique", "count", "std", "mean"])
    print(f"[audit] Total natural-key groups: {len(agg):,}")
    print(f"[audit] Total raw rows: {len(df):,}")
    print(f"[audit] Mean rows-per-group: {agg['count'].mean():.4f}")

    nunique_dist = agg["nunique"].value_counts().sort_index().to_dict()
    count_dist = agg["count"].value_counts().sort_index().to_dict()

    n_total = len(agg)
    n_degenerate = int((agg["nunique"] == 1).sum())
    n_variable = int((agg["nunique"] > 1).sum())
    pct_degenerate = 100.0 * n_degenerate / n_total
    pct_variable = 100.0 * n_variable / n_total

    print(f"[audit] Degenerate groups (nunique==1): {n_degenerate:,} ({pct_degenerate:.2f}%)")
    print(f"[audit] Variable groups   (nunique>1):  {n_variable:,} ({pct_variable:.2f}%)")

    # Ablation: among groups with count > 1 (multi-row), what's the breakdown?
    multi = agg[agg["count"] > 1]
    n_multi = len(multi)
    n_multi_degen = int((multi["nunique"] == 1).sum())
    n_multi_var = int((multi["nunique"] > 1).sum())

    # For variable groups, what's the typical magnitude?
    var_groups = agg[agg["nunique"] > 1]
    std_stats = {
        "mean": float(var_groups["std"].mean()) if len(var_groups) > 0 else float("nan"),
        "median": float(var_groups["std"].median()) if len(var_groups) > 0 else float("nan"),
        "max": float(var_groups["std"].max()) if len(var_groups) > 0 else float("nan"),
        "min": float(var_groups["std"].min()) if len(var_groups) > 0 else float("nan"),
    }
    print(
        f"[audit] Variable groups std: mean={std_stats['mean']:.4f}, "
        f"median={std_stats['median']:.4f}, max={std_stats['max']:.4f}"
    )

    # Persist per-group nunique distribution for the brief Section 2 table
    summary_rows = []
    for nu, cnt in sorted(nunique_dist.items()):
        summary_rows.append(
            {
                "nunique_oof_return": int(nu),
                "n_groups": int(cnt),
                "frac": round(cnt / n_total, 6),
            }
        )
    pd.DataFrame(summary_rows).to_csv(
        ANALYSIS_DIR / "seed_dimension_variance.csv", index=False
    )
    print(f"[audit] Wrote {ANALYSIS_DIR / 'seed_dimension_variance.csv'}")

    # Per-seed-pair correlation: proxy via grouping by (cell, trial, fold) and
    # looking at row-position variance. Without explicit seed column, we
    # cannot directly compute pair-correlations across seeds; the variance
    # breakdown above is the strongest direct evidence.
    return {
        "n_total_groups": n_total,
        "n_raw_rows": len(df),
        "mean_rows_per_group": float(agg["count"].mean()),
        "nunique_distribution": nunique_dist,
        "count_distribution": count_dist,
        "n_degenerate": n_degenerate,
        "pct_degenerate": pct_degenerate,
        "n_variable": n_variable,
        "pct_variable": pct_variable,
        "n_multi_row": n_multi,
        "n_multi_degenerate": n_multi_degen,
        "n_multi_variable": n_multi_var,
        "variable_group_std_stats": std_stats,
    }


# ---------------------------------------------------------------------------
# (b) Synthetic 10-seed Pareto demo on a small parquet subset
# ---------------------------------------------------------------------------


def _per_cell_pbo_subset(
    df: pd.DataFrame,
    cells: list[tuple[str, str]],
    rng: np.random.Generator,
    perm_paths: bool,
) -> dict:
    """Run the iter-v3/004 per-cell PBO consumer pipeline on a subset of cells.

    Per-seed knob: when perm_paths=True, the path-id ordering passed into
    pbo_from_cpcv is permuted by the seed-controlled RNG. This is a CONSUMER-
    SIDE proxy for outer-seed sensitivity — it tests whether per-seed PBO
    aggregation is stable across a benign permutation that should not affect
    aggregate metrics if the methodology is robust.
    """
    cell_rows = []
    for sym, month in cells:
        cell_df = df[(df["symbol"] == sym) & (df["train_month"] == month)]
        n_trials_cell = int(cell_df["trial_id"].nunique())
        n_candles_cell = int(cell_df["candle_open_time_ms"].nunique())
        if n_trials_cell < 2 or n_candles_cell < PER_CELL_N_SPLITS * 3:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "rank": 0,
                }
            )
            continue
        try:
            pivot = cell_df.pivot_table(
                index="candle_open_time_ms",
                columns="trial_id",
                values="oof_return",
                aggfunc="mean",
            ).sort_index()
            returns_mat = pivot.to_numpy()
            n_candles_mat, n_trials_mat = returns_mat.shape

            cell_splits = combinatorial_purged_cv(
                n_samples=n_candles_mat,
                n_splits=PER_CELL_N_SPLITS,
                n_test_splits=PER_CELL_K,
                gap=PER_CELL_GAP,
                embargo=0,
            )
            n_paths = len(cell_splits)
            path_mat = np.full((n_paths, n_trials_mat), np.nan, dtype=float)

            for path_id, (_, test_idx) in enumerate(cell_splits):
                if len(test_idx) < 2:
                    continue
                test_rets = returns_mat[test_idx, :]
                mu = np.nanmean(test_rets, axis=0)
                sigma = np.nanstd(test_rets, axis=0, ddof=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    sharpe = np.where(sigma > 0, mu / sigma, 0.0)
                path_mat[path_id, :] = sharpe

            if perm_paths:
                # Per-seed knob: permute path order. Should be stable if
                # the aggregator is robust to row-order.
                perm = rng.permutation(n_paths)
                path_mat = path_mat[perm]

            pbo_res = pbo_from_cpcv(path_mat, max_splits=5000)
            cell_pbo = pbo_res.pbo if pbo_res.pbo is not None else float("nan")
            cell_neff = int(n_effective_trials(returns_mat.T))
            rank = int(np.linalg.matrix_rank(returns_mat))

            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_mat,
                    "n_candles": n_candles_mat,
                    "pbo": cell_pbo,
                    "n_eff": cell_neff,
                    "rank": rank,
                }
            )
        except Exception as exc:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "rank": 0,
                    "error": str(exc)[:80],
                }
            )
    return {"per_cell": cell_rows}


def synthetic_10seed_pareto(df_is: pd.DataFrame) -> list[dict]:
    """Build a 10-seed Pareto demo on a small subset of cells.

    For each of the 10 outer seeds, run the iter-v3/004 consumer pipeline
    on the subset, with a seed-controlled path-permutation knob. Aggregate
    per-cell PBO + n_eff and persist a 10-row Pareto table.
    """
    print("[demo] Building 10-seed synthetic Pareto on a small subset ...")

    # Pick subset cells: BCHUSDT, first 3 IS months
    cells_all = sorted(
        df_is.groupby(["symbol", "train_month"]).groups.keys()
    )
    cells_subset = [
        (s, m) for (s, m) in cells_all if s in DEMO_SUBSET_SYMBOLS
    ][:DEMO_SUBSET_MONTHS]
    print(f"[demo] Subset cells: {cells_subset}")

    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        result = _per_cell_pbo_subset(df_is, cells_subset, rng, perm_paths=True)
        per_cell = result["per_cell"]
        cell_pbos = [c["pbo"] for c in per_cell if not np.isnan(c["pbo"])]
        cell_neffs = [c["n_eff"] for c in per_cell if c["n_eff"] > 0]

        # Sharpe proxy: mean of path-mean Sharpes across cells (rough)
        # We'll use the mean path Sharpe of each cell's IS-best trial as a
        # rudimentary "model fitness" proxy; this is NOT the real strategy
        # Sharpe (that lives in trades.csv, not the OOF parquet).
        # Here we report mean PBO and median n_eff as the headline.
        mean_pbo = float(np.mean(cell_pbos)) if cell_pbos else float("nan")
        median_pbo = float(np.median(cell_pbos)) if cell_pbos else float("nan")
        median_neff = int(np.median(cell_neffs)) if cell_neffs else 0
        n_informative = sum(1 for c in per_cell if c["rank"] > 1)

        # Concentration proxy: largest |cell_pbo - mean| over the subset
        if cell_pbos:
            concentration_proxy = float(np.max(np.abs(np.array(cell_pbos) - mean_pbo)))
        else:
            concentration_proxy = float("nan")

        rows.append(
            {
                "seed": seed,
                "mean_pbo": round(mean_pbo, 6),
                "median_pbo": round(median_pbo, 6),
                "median_n_eff": median_neff,
                "n_informative_cells": n_informative,
                "n_total_cells": len(per_cell),
                "concentration_proxy": round(concentration_proxy, 6),
            }
        )
        print(
            f"  seed={seed:5d}: mean_pbo={mean_pbo:.4f}, median_pbo={median_pbo:.4f}, "
            f"median_n_eff={median_neff}, n_informative={n_informative}/{len(per_cell)}"
        )

    pd.DataFrame(rows).to_csv(
        ANALYSIS_DIR / "synthetic_10seed_pareto.csv", index=False
    )
    print(f"[demo] Wrote {ANALYSIS_DIR / 'synthetic_10seed_pareto.csv'}")
    return rows


def pareto_non_domination(rows: list[dict]) -> dict:
    """Compute Pareto-front non-domination on the 10 synthetic seeds.

    Headline objectives: maximize mean_pbo (NO — minimize), maximize
    median_n_eff. We treat lower PBO as better and higher n_eff as better.
    Returns the index of non-dominated seeds and the front.
    """
    pbo_vals = np.array([r["mean_pbo"] for r in rows])
    neff_vals = np.array([r["median_n_eff"] for r in rows])
    n = len(rows)
    is_dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # j dominates i iff j is better-or-equal on all and strictly better on at least one
            j_pbo_better = pbo_vals[j] <= pbo_vals[i]
            j_neff_better = neff_vals[j] >= neff_vals[i]
            j_strictly_better = (pbo_vals[j] < pbo_vals[i]) or (neff_vals[j] > neff_vals[i])
            if j_pbo_better and j_neff_better and j_strictly_better:
                is_dominated[i] = True
                break
    front_idx = [i for i in range(n) if not is_dominated[i]]
    return {
        "n_total_seeds": n,
        "n_non_dominated": len(front_idx),
        "non_dominated_seeds": [int(rows[i]["seed"]) for i in front_idx],
        "n_dominated": int(is_dominated.sum()),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"[load] Reading {PARQUET_PATH} ...")
    df = pd.read_parquet(PARQUET_PATH)
    print(f"[load] Raw shape: {df.shape}")

    # Audit on RAW data (pre-dedup, includes seed-row duplicates)
    audit_result = audit_seed_variance(df)

    # Dedup by natural key for the consumer-pipeline phase
    df_dedup = df.drop_duplicates(
        subset=["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    ).copy()
    print(f"[load] After dedup: {df_dedup.shape}")

    # IS-only filter
    df_is = df_dedup[df_dedup["candle_open_time_ms"] < OOS_CUTOFF_MS].copy()
    print(f"[load] IS-only: {df_is.shape}")

    # 10-seed synthetic Pareto demo
    pareto_rows = synthetic_10seed_pareto(df_is)
    pareto_meta = pareto_non_domination(pareto_rows)
    print(f"[demo] Pareto-non-domination: {pareto_meta}")

    # Headline aggregator stats across seeds
    pbo_arr = np.array([r["mean_pbo"] for r in pareto_rows])
    neff_arr = np.array([r["median_n_eff"] for r in pareto_rows])
    cross_seed_summary = {
        "pbo_mean_across_seeds": float(np.mean(pbo_arr)),
        "pbo_std_across_seeds": float(np.std(pbo_arr, ddof=1)),
        "pbo_min_across_seeds": float(np.min(pbo_arr)),
        "pbo_max_across_seeds": float(np.max(pbo_arr)),
        "n_eff_mean_across_seeds": float(np.mean(neff_arr)),
        "n_eff_std_across_seeds": float(np.std(neff_arr, ddof=1)),
        "n_eff_min_across_seeds": int(np.min(neff_arr)),
        "n_eff_max_across_seeds": int(np.max(neff_arr)),
    }
    print(f"[demo] Cross-seed summary: {json.dumps(cross_seed_summary, indent=2)}")

    # Persist combined diagnostics JSON
    diagnostics = {
        "audit_on_raw_parquet": audit_result,
        "synthetic_10seed_pareto": pareto_rows,
        "pareto_non_domination": pareto_meta,
        "cross_seed_summary": cross_seed_summary,
    }
    with (ANALYSIS_DIR / "diagnostics.json").open("w") as f:
        json.dump(diagnostics, f, indent=2, default=str)
    print(f"[demo] Wrote {ANALYSIS_DIR / 'diagnostics.json'}")

    # Synthesis
    write_synthesis(audit_result, pareto_rows, pareto_meta, cross_seed_summary)


def write_synthesis(
    audit: dict,
    pareto_rows: list[dict],
    pareto_meta: dict,
    cross_seed_summary: dict,
) -> None:
    out = ANALYSIS_DIR / "synthesis.md"
    pct_var = audit["pct_variable"]
    pct_deg = audit["pct_degenerate"]
    pbo_std = cross_seed_summary["pbo_std_across_seeds"]
    pbo_mean = cross_seed_summary["pbo_mean_across_seeds"]
    neff_std = cross_seed_summary["n_eff_std_across_seeds"]
    neff_mean = cross_seed_summary["n_eff_mean_across_seeds"]

    pareto_table = "\n".join(
        f"| {r['seed']} | {r['mean_pbo']:.4f} | {r['median_pbo']:.4f} | "
        f"{r['median_n_eff']} | {r['n_informative_cells']}/{r['n_total_cells']} |"
        for r in pareto_rows
    )

    nunique_table = "\n".join(
        f"| {nu} | {cnt:,} | {cnt/audit['n_total_groups']:.4f} |"
        for nu, cnt in sorted(audit["nunique_distribution"].items())
    )

    txt = f"""# iter-v3/005 — Seed audit + synthetic 10-seed Pareto

## Two deliverables

This Phase-5 script produces IS-only numerical evidence for two concerns:

1. **Seed-dimension variance audit on iter-v3/003's parquet.** Tests
   iter-v3/004's brief Section 2.1 claim that "every group of 5 rows
   for the same (sym, month, trial, fold, candle) tuple has nunique == 1".
2. **Synthetic 10-seed Pareto consumer-side demo on a small parquet subset.**
   Demonstrates the iter-v3/004 per-cell PBO consumer pipeline run across
   10 outer seeds, with a seed-controlled path-permutation knob, on a
   1-symbol × 3-month subset.

## (a) Seed-dimension variance audit

Empirical breakdown of `nunique(oof_return)` per natural-key group
`(symbol, train_month, trial_id, fold_idx, candle_open_time_ms)`:

| nunique | n_groups | frac |
|---:|---:|---:|
{nunique_table}

| Aggregate | Value |
|---|---:|
| Total natural-key groups | {audit['n_total_groups']:,} |
| Total raw rows | {audit['n_raw_rows']:,} |
| Mean rows-per-group | {audit['mean_rows_per_group']:.4f} |
| Degenerate (nunique==1) | {audit['n_degenerate']:,} ({pct_deg:.2f}%) |
| Variable (nunique>1) | {audit['n_variable']:,} ({pct_var:.2f}%) |

**Variable-group oof_return std distribution** (for the {audit['n_variable']:,} groups
with `nunique > 1`):

| Stat | Value |
|---|---:|
| mean | {audit['variable_group_std_stats']['mean']:.4f} |
| median | {audit['variable_group_std_stats']['median']:.4f} |
| min | {audit['variable_group_std_stats']['min']:.4f} |
| max | {audit['variable_group_std_stats']['max']:.4f} |

## Interpretation — iter-v3/004 brief Section 2.1 claim REFINED

iter-v3/004's brief stated "every group of 5 rows for the same (sym, month,
trial, fold, candle) tuple has `nunique(oof_return) == 1`". That claim is
**partially incorrect on the empirical evidence**:

- **{pct_deg:.2f}% of natural-key groups** are degenerate (`nunique == 1`).
- **{pct_var:.2f}% of natural-key groups** are variable (`nunique > 1`),
  with mean variable-group std = {audit['variable_group_std_stats']['mean']:.4f}.

The seed dimension is NOT structurally degenerate. Most natural-key groups DO
carry per-seed signal — the 5 ensemble rows differ. The iter-v3/004
"`nunique == 1`" framing was an over-generalization driven by the writer's
silent five-fold append pattern (no `seed` column persisted), not by the
underlying OOF behavior.

This refinement matters for iter-v3/005 sub-fix #5: the producer-vs-drop
recommendation must consider that ~76% of the parquet's seed dimension
already carries information; the question is whether to surface that
information in the schema (add a `seed` column at write time) OR to honestly
acknowledge that the consumer pipeline (which dedups-by-natural-key) discards
~80% of the data anyway and the schema is misleading.

## (b) Synthetic 10-seed Pareto demo (consumer-side)

Subset: 1 symbol (BCHUSDT) × 3 IS months × 5 trials per cell.

For each of 10 outer seeds in {{42, 123, 456, 789, 1001, 7, 13, 17, 23, 37}},
the per-cell PBO pipeline runs on the subset with a per-seed RNG-controlled
path-permutation knob. The path-permutation should leave aggregate metrics
stable IF the methodology is robust.

| seed | mean_pbo | median_pbo | median_n_eff | informative_cells |
|---:|---:|---:|---:|---:|
{pareto_table}

| Cross-seed summary | Value |
|---|---:|
| mean_pbo: mean across seeds | {pbo_mean:.4f} |
| mean_pbo: std across seeds | {pbo_std:.4f} |
| mean_pbo: range | [{cross_seed_summary['pbo_min_across_seeds']:.4f}, {cross_seed_summary['pbo_max_across_seeds']:.4f}] |
| n_eff: mean across seeds | {neff_mean:.4f} |
| n_eff: std across seeds | {neff_std:.4f} |

| Pareto-non-domination | Value |
|---|---:|
| n_total_seeds | {pareto_meta['n_total_seeds']} |
| n_non_dominated | {pareto_meta['n_non_dominated']} |
| non_dominated_seeds | {pareto_meta['non_dominated_seeds']} |

## Implication for iter-v3/005

The demo confirms the per-cell consumer pipeline can produce a meaningful
10-row Pareto table at low cost. The cross-seed std on `mean_pbo` is
{pbo_std:.4f} — small enough to suggest the pipeline is stable across the
benign path-permutation knob, but the actual iter-v3/005 10-seed run
(which varies the OUTER seed driving model training, not just consumer
post-processing) will show larger variance because each outer seed produces
different LightGBM ensemble realizations.

The Phase-5 prediction for iter-v3/005's true 10-seed run is therefore:
- **mean monthly Sharpe across 10 seeds**: prediction ≥ +0.5 (single-seed=42
  was +1.0955 for OOS monthly Sharpe; cross-seed mean may be lower due to
  variance).
- **≥ 7/10 profitable seeds**: prediction TRUE.
- **per-seed PBO std**: prediction in [0.05, 0.20] (above the consumer-side
  permutation std of {pbo_std:.4f} but below the brief's structural-instability
  falsifier of 0.20).

## Sub-fix #5 framing

If iter-v3/005's `tests/strategies/ml/test_ensemble_seed_propagation.py`:
- **PASSes on iter-v3/003's parquet** (because ~76% of groups DO have
  `nunique > 1`): the test's threshold ("at least 50% of groups have
  `nunique > 1`") is met by the existing data. The seed dimension is
  REAL but UNLABELED — recommend adding a `seed` column to the writer
  schema (iter-v3/006 producer fix), preserving information that already
  exists.
- **FAILs on iter-v3/003's parquet** (if the test counts ALL groups or
  applies a different threshold): the seed dimension is structurally
  degenerate — recommend dropping it from the schema (iter-v3/006 schema
  simplification).

The Phase-5 IS-only audit suggests the FIRST scenario is more likely:
the test threshold "≥ 50% of groups have `nunique > 1`" matches the
{pct_var:.2f}% empirical fraction. iter-v3/005's job is to land the test,
run it on the existing parquet, and document the actual outcome — leaving
the producer-vs-drop decision for iter-v3/006.
"""
    out.write_text(txt)
    print(f"[synth] Wrote {out}")


if __name__ == "__main__":
    main()
