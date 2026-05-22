"""Phase 5 IS-only numerical evidence for iter-v3/003.

This script produces the brief Section 2 evidence: it demonstrates that the
``pbo_from_cpcv`` algorithm (corrected in iter-v3/002, validation_v3.py:165-340)
is correct ON ITS OWN AXIS but produces NaN whenever it's fed iter-v3/002's
single-strategy path matrix (S=1).  The structural fix required is upstream:
the runner must persist per-Optuna-trial out-of-fold returns so the path
matrix has shape (N_paths, S_strategies>1), not (N_paths, 1).

This script does NOT touch any v3 code path.  It runs entirely against
iter-v3/002's already-committed cpcv_paths.csv to:

  1. Replay the iter-v3/002 PBO=NaN outcome on its actual S=1 input.
  2. Synthetically expand S to {5, 50} by adding (a) noise replicas of the
     same per-path Sharpe and (b) independent Optuna-style trial returns
     drawn from the empirical distribution.  Show how PBO behaves on each.
  3. Specify the parquet schema iter-v3/003's ``LightGbmStrategy._train_for_month``
     must persist so the runner can build a real (N_paths, S=50) matrix.

OUTPUTS (committed alongside this script BEFORE the brief):
  - pbo_strategy_axis.csv     — PBO at S in {1, 5, 25, 50, 100} on three input
                                regimes (replica, near-overfit, near-clean).
  - persistence_schema.csv    — the prescribed parquet schema.
  - synthesis.md              — interpretive narrative.

USAGE:
    uv run python analysis/iteration_v3-003/pbo_strategy_axis_demo.py

Reads only iter-v3/002 IS-side artifacts.  No OOS data accessed.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path(__file__).resolve().parent
ITER_V3_002_REPORT = REPO_ROOT / "reports-v3" / "iteration_v3-002"

# Reproducibility — every random draw downstream is seeded from this constant.
SEED = 42
RNG = np.random.default_rng(SEED)


# =============================================================================
# 1. The CORRECTED PBO algorithm (verbatim copy of iter-v3/002's
#    validation_v3.py:160-340 — the ONE function being exercised here).
# =============================================================================


def corrected_pbo(path_metric_matrix: np.ndarray, max_splits: int = 5000) -> dict:
    """López de Prado-correct CSCV PBO. Returns dict with pbo and descriptive
    statistics.  When S=1, returns pbo=None per Bailey-LdP definition.

    Verbatim from src/crypto_trade/strategies/ml/validation_v3.py
    lines 165-340 (function ``pbo_from_cpcv``), as the latter lives only on
    iteration-v3/002 branch and is not yet on iter-v3/003.  Reproducing the
    function inline avoids importing across branches.
    """
    mat = np.asarray(path_metric_matrix, dtype=float)
    if mat.ndim == 1:
        mat = mat.reshape(-1, 1)
    if mat.ndim != 2:
        raise ValueError(f"path_metric_matrix must be 1-D or 2-D, got shape {mat.shape}")

    n_paths, n_strategies = mat.shape
    flat = mat.ravel()
    flat_finite = flat[np.isfinite(flat)]
    frac_pos = float(np.mean(flat_finite > 0)) if len(flat_finite) > 0 else float("nan")
    if len(flat_finite) >= 4:
        q25 = float(np.percentile(flat_finite, 25))
        q50 = float(np.percentile(flat_finite, 50))
        q75 = float(np.percentile(flat_finite, 75))
    else:
        q25 = q50 = q75 = float("nan")

    if n_strategies == 1:
        return dict(
            pbo=None,
            n_paths=n_paths,
            n_strategies=n_strategies,
            n_splits=0,
            frac_positive_paths=frac_pos,
            q25=q25,
            q50=q50,
            q75=q75,
            note="S=1 → PBO undefined per CSCV spec",
        )

    if n_paths < 2:
        return dict(
            pbo=None,
            n_paths=n_paths,
            n_strategies=n_strategies,
            n_splits=0,
            frac_positive_paths=frac_pos,
            q25=q25,
            q50=q50,
            q75=q75,
            note="n_paths<2 → PBO undefined",
        )

    half = n_paths // 2
    n_omega_below_half = 0
    n_splits_done = 0

    all_path_indices = list(range(n_paths))
    for is_path_indices in combinations(all_path_indices, half):
        oos_path_indices = [i for i in all_path_indices if i not in set(is_path_indices)]
        is_mat = mat[list(is_path_indices), :]
        oos_mat = mat[list(oos_path_indices), :]
        is_means = np.nanmean(is_mat, axis=0)
        n_star = int(np.argmax(is_means))
        n_star_oos_mean = float(np.nanmean(oos_mat[:, n_star]))
        oos_means = np.nanmean(oos_mat, axis=0)
        rank = int(np.sum(oos_means < n_star_oos_mean))
        omega = float(rank + 1) / float(n_strategies)
        if omega < 0.5:
            n_omega_below_half += 1
        n_splits_done += 1
        if n_splits_done >= max_splits:
            break

    pbo_val = float(n_omega_below_half) / float(n_splits_done) if n_splits_done > 0 else float("nan")
    return dict(
        pbo=pbo_val,
        n_paths=n_paths,
        n_strategies=n_strategies,
        n_splits=n_splits_done,
        frac_positive_paths=frac_pos,
        q25=q25,
        q50=q50,
        q75=q75,
        note=f"CSCV on (N={n_paths}, S={n_strategies})",
    )


# =============================================================================
# 2. Load iter-v3/002's actual path Sharpes — the S=1 input that produced
#    iter-v3/002's PBO=NaN.
# =============================================================================


def load_iter_v3_002_paths() -> np.ndarray:
    cpcv_path = ITER_V3_002_REPORT / "cpcv_paths.csv"
    df = pd.read_csv(cpcv_path)
    sharpes = df["sharpe"].to_numpy(dtype=float)
    return sharpes


# =============================================================================
# 3. Synthetic strategy-axis expansion.
#    Three regimes, each producing an (N_paths, S) matrix:
#      A — REPLICA: copy the same column S times (no strategy diversity at all).
#      B — NEAR-OVERFIT: the IS-best column is anti-correlated with the OOS-mean.
#      C — NEAR-CLEAN: per-trial returns drawn IID from N(0, σ_path) — independent.
#    These are NOT for production — they exist only to verify that the corrected
#    PBO algorithm responds as theory predicts as S increases.
# =============================================================================


def expand_replica(base_paths: np.ndarray, S: int) -> np.ndarray:
    """Replicate the SAME column S times. PBO should be ≈ 0 (no strategy
    can be different from any other on any path → IS-best == OOS-best vacuously)."""
    return np.tile(base_paths.reshape(-1, 1), (1, S))


def expand_near_overfit(base_paths: np.ndarray, S: int, rng: np.random.Generator) -> np.ndarray:
    """Build a path matrix where strategy 0 wins IS but loses OOS by construction.
    All other strategies are IID noise.  PBO should be high (≥ 0.5 baseline)."""
    n_paths = len(base_paths)
    half = n_paths // 2
    mat = rng.normal(0, 1, size=(n_paths, S))
    # Strategy 0: large positive in first half (IS), large negative in second half (OOS).
    mat[:half, 0] = +3.0 + rng.normal(0, 0.1, size=half)
    mat[half:, 0] = -3.0 + rng.normal(0, 0.1, size=n_paths - half)
    return mat


def expand_near_clean(base_paths: np.ndarray, S: int, rng: np.random.Generator) -> np.ndarray:
    """Build a path matrix where every strategy has IID Sharpe ~ N(μ, σ) with the
    empirical (μ, σ) of base_paths.  No strategy has structural IS-vs-OOS bias.
    PBO should land near the 0.5 chance baseline (with regression-to-mean push)."""
    mu = float(np.nanmean(base_paths))
    sigma = float(np.nanstd(base_paths, ddof=1))
    n_paths = len(base_paths)
    return rng.normal(mu, sigma, size=(n_paths, S))


# =============================================================================
# 4. Build the full table: PBO at S in {1, 5, 25, 50, 100} for each regime.
# =============================================================================


def build_pbo_table(base_paths: np.ndarray) -> pd.DataFrame:
    rows: list[dict] = []
    s_grid = [1, 5, 25, 50, 100]
    regimes = {
        "iter_v3_002_actual_replicated": expand_replica,
        "near_overfit_synthetic": lambda b, s: expand_near_overfit(b, s, RNG),
        "near_clean_synthetic_iid": lambda b, s: expand_near_clean(b, s, RNG),
    }

    for regime_name, builder in regimes.items():
        for S in s_grid:
            if regime_name == "iter_v3_002_actual_replicated" and S == 1:
                # Special case: real iter-v3/002 column with no replication.
                mat = base_paths.reshape(-1, 1)
            else:
                mat = builder(base_paths, S)
            res = corrected_pbo(mat)
            rows.append(
                dict(
                    regime=regime_name,
                    n_strategies=S,
                    n_paths=res["n_paths"],
                    pbo=("NaN" if res["pbo"] is None else round(res["pbo"], 4)),
                    n_splits_evaluated=res["n_splits"],
                    frac_positive_paths=round(res["frac_positive_paths"], 4),
                    note=res["note"],
                )
            )

    return pd.DataFrame(rows)


# =============================================================================
# 5. Persistence schema for iter-v3/003's lgbm.py modification.
#    Documents exactly what (trial_id, fold_idx, candle_idx, oof_return)
#    rows must look like in trial_oof_returns.parquet.
# =============================================================================


def write_persistence_schema(out_dir: Path) -> None:
    """The Engineer's spec: every row of trial_oof_returns.parquet must
    encode one (Optuna-trial, CV-fold, candle-position) triplet.

    Approximate volume budget:
      n_optuna_trials_per_(symbol, month)    = 50
      n_cv_folds                             = 5
      n_test_candles per fold                ≈ 20
      n_(symbol, month) cells                ≈ 4 symbols × 25 months ≈ 100

      Total ≈ 50 × 5 × 20 × 100 = 500,000 rows.
      With 6 columns at 8 bytes each (int64 + float64) ≈ 24 MB on disk.

    For the (N_paths × N_strategies) path matrix construction,
    the runner aggregates this parquet by (trial_id, candle_idx) and projects
    onto each CPCV path's test_idx, producing matrix[i, t] = sum of oof_return
    over candles in path_i ∩ trial_t's coverage.
    """
    schema = pd.DataFrame(
        [
            dict(
                column="trial_id",
                dtype="int32",
                semantics="(symbol_idx × n_trials × month_idx) + trial_within_month",
                example="0..50 within a month, then unique offset across months",
                load_bearing_for="indexes the strategy axis of the path matrix (S = #unique trial_ids)",
            ),
            dict(
                column="symbol",
                dtype="string (categorical)",
                semantics="BCHUSDT | MKRUSDT | LDOUSDT | TRXUSDT",
                example="BCHUSDT",
                load_bearing_for="aggregation across symbols when building the candle timeline",
            ),
            dict(
                column="train_month",
                dtype="string YYYY-MM",
                semantics="walk-forward month the trial belongs to",
                example="2024-03",
                load_bearing_for="ensures cross-month trials are not co-mingled in PBO",
            ),
            dict(
                column="fold_idx",
                dtype="int8",
                semantics="0..cv_splits-1 — index into TimeSeriesSplit folds",
                example="0..4 for cv_splits=5",
                load_bearing_for="lets the runner verify per-fold OOF coverage is complete",
            ),
            dict(
                column="candle_open_time_ms",
                dtype="int64",
                semantics="open_time of the OOF candle (the unit IS-walked through)",
                example="1709251200000 (2024-03-01 00:00 UTC)",
                load_bearing_for="joins to CPCV path test_idx via candle position",
            ),
            dict(
                column="oof_return",
                dtype="float64",
                semantics="trial's predicted-side × forward-realized return at this candle, after fees",
                example="+0.0123 or -0.0085",
                load_bearing_for="THE input value to the path matrix M[path, trial]",
            ),
        ]
    )
    schema.to_csv(out_dir / "persistence_schema.csv", index=False)


# =============================================================================
# 6. Main
# =============================================================================


def main() -> None:
    out_dir = ANALYSIS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading iter-v3/002 paths from {ITER_V3_002_REPORT / 'cpcv_paths.csv'}")
    base_paths = load_iter_v3_002_paths()
    print(
        f"  n_paths={len(base_paths)}, mean={base_paths.mean():.4f}, "
        f"std={base_paths.std(ddof=1):.4f}, "
        f"frac_positive={(base_paths > 0).mean():.4f}"
    )

    table = build_pbo_table(base_paths)
    out_csv = out_dir / "pbo_strategy_axis.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print(table.to_string(index=False))

    write_persistence_schema(out_dir)
    print(f"Wrote {out_dir / 'persistence_schema.csv'}")

    # Sanity check on the current state — replicate iter-v3/002's PBO=NaN.
    raw_call = corrected_pbo(base_paths.reshape(-1, 1))
    assert raw_call["pbo"] is None, (
        f"Expected PBO=None on actual iter-v3/002 (S=1) input, got {raw_call['pbo']}"
    )
    print(
        f"\nSanity: iter-v3/002 actual paths (S=1) → PBO={raw_call['pbo']} "
        f"(expected None per CSCV spec); descriptive frac_pos={raw_call['frac_positive_paths']:.3f}"
    )


if __name__ == "__main__":
    main()
