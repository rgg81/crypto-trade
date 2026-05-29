"""Basin-lottery diagnostics for v1 iterations.

Provides automatic emission and computation of three basin-lottery metrics:
  V1 — cross-outer-seed Optuna-trial Sharpe variance (is the basin stable across seeds?)
  V2 — per-cell Spearman rank correlation of trial Sharpe across inner seeds
       (does the same trial rank similarly regardless of inner seed?)
  V3 — trade-roster Jaccard overlap between main-run and baseline
       (did the axis produce materially different trade decisions?)

These were computed post-hoc at iter-v1/031 closeout (commit 09ad8e0).  This module
makes them AUTOMATIC at every backtest end — callable from run_baseline_v1.py after
the main walk-forward loop completes.

Live-trading note
-----------------
This module is a REPORTING-ONLY module.  It is never imported by the live engine.
It has zero runtime effect on trade signals, confidence scores, or position sizing.
The canonical live model is single-outer-seed=42 with inner-ensemble-averaged
predictions.  Multi-outer-seed reports produced by this module are STATISTICAL
VALIDATION artifacts only.

Usage from runner
-----------------
    from crypto_trade.strategies.ml.basin_diagnostics import (
        emit_optuna_trials_parquet,
        compute_v1_cross_seed_variance,
        compute_v2_per_cell_spearman,
        compute_v3_roster_overlap,
        emit_basin_diagnostics_summary,
    )
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds for PASS/FAIL/BORDERLINE classification
# ---------------------------------------------------------------------------

# V1: cross-seed Sharpe std below this = PASS (stable basin)
V1_STD_PASS_THRESHOLD: float = 0.30
V1_STD_FAIL_THRESHOLD: float = 0.60  # above this = FAIL (lottery-dominant)

# V2: mean Spearman ρ above this = PASS (trial ranking is reproducible)
V2_SPEARMAN_PASS_THRESHOLD: float = 0.50
V2_SPEARMAN_FAIL_THRESHOLD: float = 0.20  # below this = FAIL (chaotic ranking)

# V3: Jaccard overlap above this = PASS (similar trade roster → stable decisions)
V3_JACCARD_PASS_THRESHOLD: float = 0.40
V3_JACCARD_FAIL_THRESHOLD: float = 0.15  # below this = FAIL (lottery relocation)


# ---------------------------------------------------------------------------
# V1 — Cross-outer-seed Optuna-trial Sharpe variance
# ---------------------------------------------------------------------------


def compute_v1_cross_seed_variance(parquet_path: Path) -> pd.DataFrame:
    """Compute cross-outer-seed Sharpe variance from the trials parquet.

    The trials parquet (emitted by emit_optuna_trials_parquet) has columns:
        outer_seed, model, month, inner_seed, trial_number, sharpe, *hyperparams

    Returns a DataFrame with one row per (model, month, inner_seed) cell:
        model, month, inner_seed, mean_sharpe, std_sharpe, n_outer_seeds

    Args:
        parquet_path: Path to the Optuna trials parquet file.

    Returns:
        DataFrame with cross-seed variance stats per cell.

    Raises:
        FileNotFoundError: If parquet_path does not exist.
        KeyError: If required columns are missing.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Trials parquet not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    required = {"outer_seed", "model", "month", "inner_seed", "trial_number", "sharpe"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Trials parquet missing columns: {missing}")

    # Per-cell best trial Sharpe (one number per outer_seed × model × month × inner_seed)
    best_per_seed = (
        df.groupby(["outer_seed", "model", "month", "inner_seed"])["sharpe"]
        .max()
        .reset_index()
        .rename(columns={"sharpe": "best_sharpe"})
    )

    # Cross outer-seed variance per (model, month, inner_seed)
    stats = (
        best_per_seed.groupby(["model", "month", "inner_seed"])["best_sharpe"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "mean_sharpe", "std": "std_sharpe", "count": "n_outer_seeds"})
    )
    stats["std_sharpe"] = stats["std_sharpe"].fillna(0.0)
    return stats


# ---------------------------------------------------------------------------
# V2 — Per-cell Spearman rank correlation of trial Sharpe across inner seeds
# ---------------------------------------------------------------------------


def compute_v2_per_cell_spearman(parquet_path: Path) -> pd.DataFrame:
    """Compute per-cell Spearman ρ of trial-Sharpe rankings across inner seeds.

    For each (outer_seed, model, month) cell, compute the Spearman ρ between
    every pair of inner-seed trial-Sharpe vectors, then average across pairs.

    A high mean ρ (> 0.50) indicates that Optuna's trial landscape is stable —
    the same trials rank similarly regardless of inner seed.  A low ρ (<0.20)
    indicates chaotic landscape where the best trial is seed-lottery-dependent.

    Args:
        parquet_path: Path to the Optuna trials parquet file.

    Returns:
        DataFrame with columns: outer_seed, model, month, mean_spearman, n_inner_seeds.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Trials parquet not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    required = {"outer_seed", "model", "month", "inner_seed", "trial_number", "sharpe"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Trials parquet missing columns: {missing}")

    rows = []
    for (outer_seed, model, month), cell_df in df.groupby(["outer_seed", "model", "month"]):
        inner_seeds = sorted(cell_df["inner_seed"].unique())
        if len(inner_seeds) < 2:
            rows.append(
                {
                    "outer_seed": outer_seed,
                    "model": model,
                    "month": month,
                    "mean_spearman": float("nan"),
                    "n_inner_seeds": len(inner_seeds),
                }
            )
            continue

        # Build trial-Sharpe matrix: rows=trials, cols=inner_seeds
        trial_nums = sorted(cell_df["trial_number"].unique())
        matrix = {}
        for seed in inner_seeds:
            seed_df = cell_df[cell_df["inner_seed"] == seed].set_index("trial_number")["sharpe"]
            matrix[seed] = seed_df.reindex(trial_nums).fillna(float("nan"))

        mat_df = pd.DataFrame(matrix, index=trial_nums)

        # Pairwise Spearman ρ
        rho_values = []
        for i, s1 in enumerate(inner_seeds):
            for s2 in inner_seeds[i + 1 :]:
                col1 = mat_df[s1].dropna()
                col2 = mat_df[s2].dropna()
                common_idx = col1.index.intersection(col2.index)
                if len(common_idx) < 3:
                    continue
                rho = float(col1.loc[common_idx].rank().corr(col2.loc[common_idx].rank()))
                rho_values.append(rho)

        mean_rho = float(np.mean(rho_values)) if rho_values else float("nan")
        rows.append(
            {
                "outer_seed": outer_seed,
                "model": model,
                "month": month,
                "mean_spearman": mean_rho,
                "n_inner_seeds": len(inner_seeds),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# V3 — Trade-roster Jaccard overlap
# ---------------------------------------------------------------------------


def compute_v3_roster_overlap(
    trades_path: Path,
    baseline_trades_path: Path,
    *,
    symbols: list[str] | None = None,
) -> pd.DataFrame:
    """Compute trade-roster Jaccard overlap between main run and baseline.

    Jaccard is computed per symbol and globally as:
        |intersection| / |union|
    where each trade is identified by (symbol, open_time_ms).

    A low Jaccard (< 0.15) indicates basin relocation — the axis produced
    a fundamentally different set of trade decisions (not just scaled weights).

    Args:
        trades_path: Path to the main run's trades CSV.
        baseline_trades_path: Path to the baseline trades CSV.
        symbols: Optional list of symbols to filter. If None, use all.

    Returns:
        DataFrame with columns: symbol, n_main, n_baseline, n_intersection,
        n_union, jaccard.
    """
    if not trades_path.exists():
        raise FileNotFoundError(f"Main trades CSV not found: {trades_path}")
    if not baseline_trades_path.exists():
        raise FileNotFoundError(f"Baseline trades CSV not found: {baseline_trades_path}")

    main_df = pd.read_csv(trades_path)
    base_df = pd.read_csv(baseline_trades_path)

    if symbols is not None:
        main_df = main_df[main_df["symbol"].isin(symbols)]
        base_df = base_df[base_df["symbol"].isin(symbols)]

    all_symbols = sorted(set(main_df["symbol"].unique()) | set(base_df["symbol"].unique()))
    rows = []
    for sym in all_symbols:
        main_sym = main_df[main_df["symbol"] == sym]
        base_sym = base_df[base_df["symbol"] == sym]

        main_ids = set(zip(main_sym["symbol"], main_sym["open_time"].astype(int)))
        base_ids = set(zip(base_sym["symbol"], base_sym["open_time"].astype(int)))

        n_main = len(main_ids)
        n_base = len(base_ids)
        n_inter = len(main_ids & base_ids)
        n_union = len(main_ids | base_ids)
        jaccard = n_inter / n_union if n_union > 0 else float("nan")

        rows.append(
            {
                "symbol": sym,
                "n_main": n_main,
                "n_baseline": n_base,
                "n_intersection": n_inter,
                "n_union": n_union,
                "jaccard": jaccard,
            }
        )

    # Global row
    main_ids_all = set(zip(main_df["symbol"], main_df["open_time"].astype(int)))
    base_ids_all = set(zip(base_df["symbol"], base_df["open_time"].astype(int)))
    n_inter_all = len(main_ids_all & base_ids_all)
    n_union_all = len(main_ids_all | base_ids_all)
    rows.append(
        {
            "symbol": "ALL",
            "n_main": len(main_ids_all),
            "n_baseline": len(base_ids_all),
            "n_intersection": n_inter_all,
            "n_union": n_union_all,
            "jaccard": n_inter_all / n_union_all if n_union_all > 0 else float("nan"),
        }
    )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# OOF-parquet → basin-trials-parquet bridge
# ---------------------------------------------------------------------------

# Annualisation factor for 8h candles: 365.25 * 3 candles/day
_CANDLES_PER_YEAR_8H: float = 365.25 * 3.0


def derive_basin_trials_from_oof_parquet(
    oof_parquet_path: Path,
    output_path: Path,
    *,
    outer_seed: int = 42,
    model_name: str = "combined",
) -> None:
    """Derive the basin-diagnostics trials parquet from the OOF candle-return parquet.

    The OOF parquet produced by optimization.py has schema:
        trial_id, symbol, train_month, fold_idx, candle_open_time_ms, oof_return

    The basin-diagnostics V1/V2 functions expect schema:
        outer_seed, model, month, inner_seed, trial_number, sharpe

    This bridge function aggregates OOF returns per (trial_id, symbol, train_month)
    cell into a per-trial annualised Sharpe ratio, then renames columns to match
    the expected schema.  ``inner_seed`` is set to 0 (single pseudo-seed) since the
    OOF parquet does not record inner_seed.

    If oof_parquet_path does not exist or has no valid rows after NaN-drop, this is
    a no-op and a warning is logged.

    Args:
        oof_parquet_path: Path to the OOF candle-return parquet (from optimization.py).
        output_path: Path to write the derived basin-trials parquet.
        outer_seed: Outer seed label to embed in the output (default 42 = canonical).
        model_name: Model label to embed in the output (default "combined").
    """
    if not oof_parquet_path.exists():
        log.warning(
            "derive_basin_trials_from_oof_parquet: %s not found; skipping derivation.",
            oof_parquet_path,
        )
        return

    df = pd.read_parquet(oof_parquet_path)
    required = {"trial_id", "oof_return"}
    missing = required - set(df.columns)
    if missing:
        log.warning(
            "derive_basin_trials_from_oof_parquet: OOF parquet missing columns %s; "
            "skipping derivation.",
            missing,
        )
        return

    df = df.dropna(subset=["oof_return"])
    if df.empty:
        log.warning(
            "derive_basin_trials_from_oof_parquet: OOF parquet has no non-NaN rows; "
            "skipping derivation."
        )
        return

    # Determine grouping: prefer (symbol, train_month) per-cell; fall back gracefully.
    group_cols = ["trial_id"]
    if "train_month" in df.columns:
        group_cols = ["trial_id", "train_month"]
    if "symbol" in df.columns and "train_month" in df.columns:
        group_cols = ["trial_id", "symbol", "train_month"]

    rows = []
    for key, cell in df.groupby(group_cols):
        returns = cell["oof_return"].values.astype(float)
        if len(returns) < 2:
            continue
        mu = float(np.mean(returns))
        sigma = float(np.std(returns, ddof=1))
        sharpe = (mu / sigma * np.sqrt(_CANDLES_PER_YEAR_8H)) if sigma > 0.0 else 0.0

        if isinstance(key, tuple):
            trial_id = int(key[0])
            month = str(key[1]) if len(key) > 1 else "unknown"
        else:
            trial_id = int(key)
            month = "unknown"

        rows.append(
            {
                "outer_seed": outer_seed,
                "model": model_name,
                "month": month,
                "inner_seed": 0,  # OOF parquet does not record inner_seed
                "trial_number": trial_id,
                "sharpe": sharpe,
            }
        )

    if not rows:
        log.warning(
            "derive_basin_trials_from_oof_parquet: no rows produced (too few returns per cell); "
            "skipping write."
        )
        return

    out_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(output_path, index=False)
    log.info(
        "derive_basin_trials_from_oof_parquet: derived %d rows → %s",
        len(rows),
        output_path,
    )


# ---------------------------------------------------------------------------
# Trials parquet emitter (called at end of each run_model invocation)
# ---------------------------------------------------------------------------

# Expected hyperparameter columns in trials parquet
TRIAL_HP_COLUMNS = (
    "confidence_threshold",
    "training_days",
    "n_estimators",
    "max_depth",
    "num_leaves",
    "learning_rate",
    "subsample",
    "colsample_bytree",
    "min_child_samples",
    "reg_alpha",
    "reg_lambda",
)


def emit_optuna_trials_parquet(
    strategy: LightGbmStrategy,
    output_path: Path,
    *,
    model_name: str,
    outer_seed: int = 42,
) -> None:
    """Persist per-trial Optuna results from a trained LightGbmStrategy to parquet.

    This function is called at the end of each run_model invocation.  It reads
    the Optuna study objects from the strategy's walk-forward month cache and
    emits a structured parquet with one row per (outer_seed, model, month,
    inner_seed, trial_number).

    If the strategy has no Optuna studies (e.g., frozen-HP mode), this is a no-op
    and a warning is emitted.

    Args:
        strategy: A trained LightGbmStrategy instance.
        output_path: Path to write (or append to) the parquet file.
        model_name: Label for the model (e.g., "A", "C", "D", "E").
        outer_seed: The outer seed index for this run (default 42 = canonical).
    """
    study_cache = getattr(strategy, "_optuna_study_cache", None)
    if not study_cache:
        log.warning(
            "emit_optuna_trials_parquet: strategy has no _optuna_study_cache "
            "(frozen-HP mode or no training yet). Skipping emission."
        )
        return

    rows = []
    for (month_str, inner_seed), study in study_cache.items():
        for trial in study.trials:
            if trial.value is None:
                continue
            row: dict = {
                "outer_seed": outer_seed,
                "model": model_name,
                "month": month_str,
                "inner_seed": inner_seed,
                "trial_number": trial.number,
                "sharpe": float(trial.value),
            }
            for hp_col in TRIAL_HP_COLUMNS:
                row[hp_col] = trial.params.get(hp_col, float("nan"))
            rows.append(row)

    if not rows:
        log.warning(
            "emit_optuna_trials_parquet: no trial rows extracted for model=%s. "
            "Possibly all trials had None value (pruned/failed).",
            model_name,
        )
        return

    new_df = pd.DataFrame(rows)

    # Append to existing parquet if it exists (multi-model, multi-seed accumulation)
    if output_path.exists():
        existing = pd.read_parquet(output_path)
        new_df = pd.concat([existing, new_df], ignore_index=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    new_df.to_parquet(output_path, index=False)
    log.info(
        "emit_optuna_trials_parquet: wrote %d rows to %s (model=%s outer_seed=%d)",
        len(rows),
        output_path,
        model_name,
        outer_seed,
    )


# ---------------------------------------------------------------------------
# Summary emitter — called once at end of backtest
# ---------------------------------------------------------------------------


def emit_basin_diagnostics_summary(
    *,
    diagnostics_dir: Path,
    trials_parquet: Path,
    main_trades_oos: Path,
    baseline_trades_oos: Path,
    symbols: list[str] | None = None,
) -> dict:
    """Compute all three metrics and write summary files.

    Writes to diagnostics_dir/:
        v1_cross_seed_variance.csv
        v2_param_spearman.csv
        v3_roster_overlap.csv
        basin_diagnostics.json  (PASS/FAIL/BORDERLINE per metric + global verdict)

    Args:
        diagnostics_dir: Directory to write output files.
        trials_parquet: Path to the accumulated Optuna trials parquet.
        main_trades_oos: OOS trades CSV from the main (axis) run.
        baseline_trades_oos: OOS trades CSV from the baseline run.
        symbols: Optional symbol filter for V3.

    Returns:
        The summary dict (same content as basin_diagnostics.json).
    """
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    summary: dict = {}

    # V1 — cross-seed variance
    v1_verdict = "SKIPPED"
    v1_global_std = float("nan")
    if trials_parquet.exists():
        try:
            v1_df = compute_v1_cross_seed_variance(trials_parquet)
            v1_path = diagnostics_dir / "v1_cross_seed_variance.csv"
            v1_df.to_csv(v1_path, index=False)
            # Global std: mean of per-cell std_sharpe
            v1_global_std = float(v1_df["std_sharpe"].mean())
            if v1_global_std <= V1_STD_PASS_THRESHOLD:
                v1_verdict = "PASS"
            elif v1_global_std >= V1_STD_FAIL_THRESHOLD:
                v1_verdict = "FAIL"
            else:
                v1_verdict = "BORDERLINE"
        except Exception as exc:  # noqa: BLE001
            log.warning("V1 cross-seed variance computation failed: %s", exc)
            v1_verdict = "ERROR"
    summary["v1"] = {
        "metric": "cross_seed_sharpe_std",
        "value": v1_global_std,
        "pass_threshold": V1_STD_PASS_THRESHOLD,
        "fail_threshold": V1_STD_FAIL_THRESHOLD,
        "verdict": v1_verdict,
    }

    # V2 — per-cell Spearman
    v2_verdict = "SKIPPED"
    v2_global_rho = float("nan")
    if trials_parquet.exists():
        try:
            v2_df = compute_v2_per_cell_spearman(trials_parquet)
            v2_path = diagnostics_dir / "v2_param_spearman.csv"
            v2_df.to_csv(v2_path, index=False)
            valid_rho = v2_df["mean_spearman"].dropna()
            v2_global_rho = float(valid_rho.mean()) if len(valid_rho) > 0 else float("nan")
            if v2_global_rho >= V2_SPEARMAN_PASS_THRESHOLD:
                v2_verdict = "PASS"
            elif v2_global_rho <= V2_SPEARMAN_FAIL_THRESHOLD:
                v2_verdict = "FAIL"
            else:
                v2_verdict = "BORDERLINE"
        except Exception as exc:  # noqa: BLE001
            log.warning("V2 per-cell Spearman computation failed: %s", exc)
            v2_verdict = "ERROR"
    summary["v2"] = {
        "metric": "per_cell_spearman_rho",
        "value": v2_global_rho,
        "pass_threshold": V2_SPEARMAN_PASS_THRESHOLD,
        "fail_threshold": V2_SPEARMAN_FAIL_THRESHOLD,
        "verdict": v2_verdict,
    }

    # V3 — roster overlap
    v3_verdict = "SKIPPED"
    v3_global_jaccard = float("nan")
    if main_trades_oos.exists() and baseline_trades_oos.exists():
        try:
            v3_df = compute_v3_roster_overlap(main_trades_oos, baseline_trades_oos, symbols=symbols)
            v3_path = diagnostics_dir / "v3_roster_overlap.csv"
            v3_df.to_csv(v3_path, index=False)
            global_row = v3_df[v3_df["symbol"] == "ALL"]
            if len(global_row) > 0:
                v3_global_jaccard = float(global_row.iloc[0]["jaccard"])
            if not np.isnan(v3_global_jaccard):
                if v3_global_jaccard >= V3_JACCARD_PASS_THRESHOLD:
                    v3_verdict = "PASS"
                elif v3_global_jaccard <= V3_JACCARD_FAIL_THRESHOLD:
                    v3_verdict = "FAIL"
                else:
                    v3_verdict = "BORDERLINE"
        except Exception as exc:  # noqa: BLE001
            log.warning("V3 roster overlap computation failed: %s", exc)
            v3_verdict = "ERROR"
    summary["v3"] = {
        "metric": "oos_trade_roster_jaccard",
        "value": v3_global_jaccard,
        "pass_threshold": V3_JACCARD_PASS_THRESHOLD,
        "fail_threshold": V3_JACCARD_FAIL_THRESHOLD,
        "verdict": v3_verdict,
    }

    # Global verdict: PASS if all non-SKIPPED pass; FAIL if any fail
    verdicts = [v for v in [v1_verdict, v2_verdict, v3_verdict] if v not in ("SKIPPED", "ERROR")]
    if not verdicts:
        global_verdict = "SKIPPED"
    elif any(v == "FAIL" for v in verdicts):
        global_verdict = "FAIL"
    elif any(v == "BORDERLINE" for v in verdicts):
        global_verdict = "BORDERLINE"
    else:
        global_verdict = "PASS"

    summary["global_verdict"] = global_verdict

    json_path = diagnostics_dir / "basin_diagnostics.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(
        f"[basin_diagnostics] V1={v1_verdict}(std={v1_global_std:.3f}) "
        f"V2={v2_verdict}(ρ={v2_global_rho:.3f}) "
        f"V3={v3_verdict}(J={v3_global_jaccard:.3f}) "
        f"→ GLOBAL={global_verdict}"
    )
    return summary
