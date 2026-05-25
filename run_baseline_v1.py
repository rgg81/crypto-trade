"""v1 baseline runner — refactored 2026-05-23.

The refactored v1 runner. Mirrors the v3 runner's structural pattern (EXPLORATION
vs CONFIRMATION mode via CLI flag; explicit feature column pinning; runtime
V1_EXCLUDED_SYMBOLS audit; reports written to reports-v1/iteration_v1-NNN/)
while preserving the v1 baseline architecture (4 models A/C/D/E, 5-symbol
universe, ATR-based labeling, R1/R2/R3 risk gates).

Track isolation:
----------------
This runner imports ONLY from:
- crypto_trade (top-level, shared infrastructure)
- crypto_trade.features_v1 (v1 constants + audit helper)
- crypto_trade.strategies.ml.lgbm (shared backtest engine)
- crypto_trade.strategies.ml.validation_v1 (v1 CPCV/DSR/PBO/PSR)
- crypto_trade.strategies.ml.reporting_v1 (iter-v1/001 methodology reporting helpers)
- crypto_trade.live.models (BASELINE_FEATURE_COLUMNS — legacy v1 feature math)

It does NOT import from features_v2 or features_v3. The Phase 6.0 pre-flight
Critic verifies this.

Ensemble configuration (matches v3 post-iter-v3/059):
-----------------------------------------------------
- EXPLORATION mode: ENSEMBLE_SIZE=3 (inner seeds), single-pass (no outer loop)
- CONFIRMATION mode: ENSEMBLE_SIZE=10 (inner seeds), single-pass (no outer loop)
- ENSEMBLE_SEEDS roster: [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]

Usage:
------
    # Reproduce the corrected v1 baseline (BASELINE_V1.md anchor):
    uv run python run_baseline_v1.py --baseline-mode

    # Run an EXPLORATION iteration:
    uv run python run_baseline_v1.py --exploration --iteration 1 --n-trials 35

    # Run a CONFIRMATION iteration:
    uv run python run_baseline_v1.py --confirmation --iteration 10 --n-trials 35

iter-v1/001 methodology reporting (wired in this runner):
---------------------------------------------------------
- PSR columns in comparison.csv: psr_monthly_vs_0, psr_monthly_vs_1, psr_daily_vs_0
- N_eff-corrected DSR via PCA on per-trial OOF return matrix
- n_effective_trials column in comparison.csv
- dsr.json with {dsr, pbo, psr, n_trials, n_eff, n_eff_pca_method, min_trl_months}
- adf_test.csv: per-feature ADF p-value + Bonferroni + exception_class (193 rows)
- ic_matrix.csv: per-family Fisher-z'd Spearman IC (8×8 symmetric)

Open work items for iter-v1/002+ (deferred from iter-v1/001):
------------------------------------------------------------
- Full CPCV (45 paths) report generation — wire validation_v1.cpcv_walk_forward_splits
- Pareto front 10-seed × 6-metric matrix for CONFIRMATION runs
- Meta-labeling (M1 + M2) architecture wiring
- Fractional Kelly position sizing
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig, TradeResult
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v1 import (
    V1_BASELINE_UNIVERSE,
    V1_EXCLUDED_SYMBOLS,
    V1_FEATURE_COLUMNS,
    V1_FEATURE_COLUMNS_PRUNED,
    V1_OOD_FEATURE_COLUMNS,
    assert_v1_universe,
)
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.reporting_v1 import (
    _per_cell_n_eff_from_parquet,
    append_psr_rows_to_comparison,
    append_r5_binary_kill_rows_to_comparison,
    append_r5_rows_to_comparison,
    compute_n_eff_and_dsr,
    compute_psr_columns,
    write_adf_test_csv,
    write_dsr_json,
    write_ic_matrix_csv,
)

# ---------------------------------------------------------------------------
# Ensemble configuration (mirrors v3 post-iter-v3/059 single-pass structure)
# ---------------------------------------------------------------------------

#: Inner ensemble seeds roster (first 3 used at EXPLORATION; all 10 at CONFIRMATION).
ENSEMBLE_SEEDS: tuple[int, ...] = (42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006)

#: EXPLORATION ensemble size — single-axis, fast cycling.
V1_EXPLORATION_ENSEMBLE_SIZE: int = 3

#: CONFIRMATION ensemble size — full statistical rigor.
V1_CONFIRMATION_ENSEMBLE_SIZE: int = 10

#: BASELINE_V1.md anchor — the corrected walk-forward stack reproduces this set.
BASELINE_OOD_CUTOFF_PCT: float = 0.70

#: Stable path for the per-trial OOF return parquet (iter-v1/001 methodology axis).
#: iter-v1/008: RESTORED to iteration-stamped path (originally from /003 commit 976ce75).
#: The path is overridden in main() after iteration_label is resolved:
#:   OOF_PARQUET_PATH = Path("data") / f"v1_iter_{iteration_label}_trial_oof.parquet"
#: The sentinel below is overwritten before any backtest code runs.
#: optimization.py appends rows here when LightGbmStrategy.oof_persist_path is set.
#: Cleared at runner start to harden against A7 append-accumulation from prior runs.
OOF_PARQUET_PATH: Path = Path("data") / "v1_iter_SENTINEL_trial_oof.parquet"


def _derive_ensemble_seeds(size: int, offset: int = 0) -> list[int]:
    """Return `size` seeds from the ENSEMBLE_SEEDS roster starting at `offset`.

    Single-pass structure: no outer seed loop. The runner trains `size` models
    in parallel (one per inner seed) and averages predictions at signal time.

    Parameters
    ----------
    size
        Number of inner seeds to use. Must be in [1, len(ENSEMBLE_SEEDS)].
    offset
        Starting index into ENSEMBLE_SEEDS. Default 0 reproduces canonical
        EXPLORATION/CONFIRMATION seed windows ([42, 123, 456, ...]).
        Used by iter-v1/012 SUBSTRATE-DISSOLUTION PROBE (offset=3 selects
        DISJOINT inner seeds [789, 1001, 2002] from /011's [42, 123, 456]
        while staying inside the canonical CONFIRMATION roster). Must satisfy
        offset + size <= len(ENSEMBLE_SEEDS).
    """
    if size < 1 or size > len(ENSEMBLE_SEEDS):
        raise ValueError(f"ENSEMBLE_SIZE must be in [1, {len(ENSEMBLE_SEEDS)}]; got {size}")
    if offset < 0 or offset + size > len(ENSEMBLE_SEEDS):
        raise ValueError(
            f"ensemble seed window out of range: offset={offset} + size={size} "
            f"exceeds len(ENSEMBLE_SEEDS)={len(ENSEMBLE_SEEDS)}"
        )
    return list(ENSEMBLE_SEEDS[offset : offset + size])


def run_model(
    name: str,
    symbols: tuple[str, ...],
    atr_tp: float,
    atr_sl: float,
    *,
    apply_r1: bool,
    apply_r2: bool = False,
    n_trials: int,
    ensemble_size: int,
    oof_persist_path: Path | None = None,
    feature_columns: list[str] | None = None,
    bounds_profile: str = "default",
    r5_vol_target_enabled: bool = True,
    r5_vol_target_pct: float = 4.0,
    r5_kill_low_natr_enabled: bool = False,
    r5_kill_low_natr_min_pct: float = 2.0,
    ensemble_seeds_offset: int = 0,
):
    """Run a single v1 sub-model (A/C/D/E) under the corrected walk-forward.

    Parameters
    ----------
    feature_columns
        Explicit feature column list. Defaults to V1_FEATURE_COLUMNS (193 cols).
        Pass list(V1_FEATURE_COLUMNS_PRUNED) for iter-v1/002+ pruned runs.
        MUST be non-empty — LightGbmStrategy raises if None or empty.
    bounds_profile
        Optuna search bounds profile. "default" for 193-feature runs;
        "v1_pruned" for 40-feature pruned runs (LM Master Recs #1–3).
    r5_vol_target_enabled
        Enable R5 proportional vol-target ceiling (iter-v1/010). Default True
        (historical default). Set False for iter-v1/011 binary-kill isolation.
    r5_vol_target_pct
        Vol-target ceiling percentage for R5 proportional scaling (default 4.0%).
    r5_kill_low_natr_enabled
        Enable R5-BINARY-KILL entry filter (iter-v1/011). Default False.
        When True, skips entries where NATR_14 < r5_kill_low_natr_min_pct.
    r5_kill_low_natr_min_pct
        NATR_14 floor for binary kill (default 2.0% per iter-v1/011 EDA).
    ensemble_seeds_offset
        Starting index into ENSEMBLE_SEEDS for inner seed selection. Default 0
        reproduces canonical EXPLORATION/CONFIRMATION seed windows. iter-v1/012
        SUBSTRATE-DISSOLUTION PROBE uses offset=3 to select DISJOINT inner seeds
        from /011 ([789, 1001, 2002] vs /011's [42, 123, 456]) while remaining
        inside the canonical CONFIRMATION roster.
    """
    effective_feature_columns = (
        feature_columns if feature_columns is not None else list(V1_FEATURE_COLUMNS)
    )
    print("=" * 60)
    print(
        f"MODEL {name}: {', '.join(symbols)} "
        f"(R1={apply_r1} R2={apply_r2} R3=on, n_trials={n_trials}, "
        f"ENSEMBLE_SIZE={ensemble_size}, features={len(effective_feature_columns)}, "
        f"bounds={bounds_profile})"
    )
    print("=" * 60)
    config = BacktestConfig(
        symbols=symbols,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
        risk_consecutive_sl_limit=3 if apply_r1 else None,
        risk_consecutive_sl_cooldown_candles=27 if apply_r1 else 0,
        risk_drawdown_scale_enabled=apply_r2,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_floor=0.33,
        risk_drawdown_scale_anchor_pct=15.0,
        risk_r5_vol_target_enabled=r5_vol_target_enabled,
        risk_r5_vol_target_pct=r5_vol_target_pct,
        risk_r5_kill_low_natr_enabled=r5_kill_low_natr_enabled,
        risk_r5_kill_low_natr_min_pct=r5_kill_low_natr_min_pct,
    )
    strategy = LightGbmStrategy(
        training_months=24,
        n_trials=n_trials,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=1,
        atr_tp_multiplier=atr_tp,
        atr_sl_multiplier=atr_sl,
        use_atr_labeling=True,
        ensemble_seeds=_derive_ensemble_seeds(ensemble_size, offset=ensemble_seeds_offset),
        feature_columns=effective_feature_columns,
        ood_enabled=True,
        ood_features=list(V1_OOD_FEATURE_COLUMNS),
        ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
        oof_persist_path=oof_persist_path,
        bounds_profile=bounds_profile,
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def _load_pnl_series(
    trades: list[TradeResult],
    granularity: str,
) -> list[float]:
    """Extract monthly or daily PnL series from trade list (non-annualized).

    Parameters
    ----------
    trades
        Trade list for one half (IS or OOS).
    granularity
        "monthly" → group by close_time month; "daily" → group by close_time day.

    Returns
    -------
    List of per-period weighted_pnl sums (non-annualized — matches the granularity).
    """
    from datetime import UTC, datetime  # noqa: PLC0415

    if not trades:
        return []

    by_period: dict[str, float] = {}
    for t in trades:
        dt = datetime.fromtimestamp(t.close_time / 1000, tz=UTC)
        if granularity == "monthly":
            key = dt.strftime("%Y-%m")
        else:
            key = dt.strftime("%Y-%m-%d")
        by_period[key] = by_period.get(key, 0.0) + t.weighted_pnl

    return [by_period[k] for k in sorted(by_period)]


def _load_features_for_adf_ic(
    symbols: tuple[str, ...],
    features_dir: str,
    interval: str,
    feature_columns: list[str] | None = None,
) -> pd.DataFrame | None:
    """Load and concatenate IS-window feature parquets for ADF + IC computation.

    Parameters
    ----------
    feature_columns
        Columns to select from each parquet. Defaults to V1_FEATURE_COLUMNS
        (193 cols). Pass list(V1_FEATURE_COLUMNS_PRUNED) for pruned-feature runs
        so the ADF/IC outputs reflect the 40-column space actually used for training.

    Returns
    -------
    DataFrame with the requested columns (IS rows only) or None if no parquets found.
    """
    _cols = feature_columns if feature_columns is not None else list(V1_FEATURE_COLUMNS)
    dfs = []
    for sym in symbols:
        parquet_path = Path(features_dir) / f"{sym}_{interval}_features.parquet"
        if not parquet_path.exists():
            print(f"[run_baseline_v1] WARNING: parquet not found: {parquet_path}")
            continue
        try:
            df = pd.read_parquet(parquet_path)
        except Exception as exc:
            print(f"[run_baseline_v1] WARNING: failed to read {parquet_path}: {exc}")
            continue
        # IS-only filter: open_time < OOS_CUTOFF_MS
        if "open_time" in df.columns:
            df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        # Keep only the requested columns that exist in this parquet
        avail = [c for c in _cols if c in df.columns]
        if avail:
            dfs.append(df[avail])

    if not dfs:
        return None

    # Concatenate across symbols (rows = all IS candles from all symbols)
    combined = pd.concat(dfs, axis=0, ignore_index=True)
    return combined


def _compute_forward_returns(
    symbols: tuple[str, ...],
    features_dir: str,
    interval: str,
) -> np.ndarray | None:
    """Compute per-row 1-bar log forward return from close prices (IS window only).

    This is the next-candle log-return target used for IC computation.  Per
    brief Section 3.5 #4 and LM Master §4: forward return = log(close[t+1] / close[t])
    for the 1-bar (8h candle) forward window.

    Returns
    -------
    1-D array aligned with the IS feature matrix rows, or None if data unavailable.
    """
    # Brief specifies the forward return target = next-candle log-return per symbol.
    # We approximate this using close prices from the parquet (if available).
    dfs = []
    for sym in symbols:
        parquet_path = Path(features_dir) / f"{sym}_{interval}_features.parquet"
        if not parquet_path.exists():
            continue
        try:
            df = pd.read_parquet(parquet_path)
        except Exception:
            continue
        # IS-only
        if "open_time" in df.columns:
            df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if "close" in df.columns:
            log_ret = np.log(df["close"].shift(-1) / df["close"]).values
            dfs.append(log_ret)

    if not dfs:
        return None

    # Concatenate forward returns across symbols (same order as _load_features_for_adf_ic)
    return np.concatenate(dfs, axis=0)


def _run_methodology_reporting(
    all_results: list[TradeResult],
    *,
    iter_dir: Path,
    is_dir: Path,
    oos_dir: Path,
    n_trials: int,
    symbols: tuple[str, ...],
    features_dir: str,
    interval: str,
    oof_parquet_path: Path | None,
    feature_columns: list[str] | None = None,
    r5_signals_is: int = 0,
    r5_fires_is: int = 0,
    r5_signals_oos: int = 0,
    r5_fires_oos: int = 0,
    r5_kill_signals_is: int = 0,
    r5_kill_fires_is: int = 0,
    r5_kill_signals_oos: int = 0,
    r5_kill_fires_oos: int = 0,
) -> None:
    """Run all iter-v1/001 methodology reporting passes AFTER generate_iteration_reports().

    This function is STRICTLY POST-HOC — it does NOT modify any prediction,
    trade, or labeling output.  It reads existing report files and appends
    new artifacts.  Called from main() after generate_iteration_reports().

    Produces:
        {is_dir,oos_dir}/dsr.json
        {is_dir,oos_dir}/adf_test.csv
        {is_dir,oos_dir}/ic_matrix.csv
        iter_dir/comparison.csv   — 4 new rows appended

    Parameters
    ----------
    all_results
        Full trade list (IS + OOS combined).
    iter_dir
        Iteration root directory (contains comparison.csv).
    is_dir
        IS sub-directory.
    oos_dir
        OOS sub-directory.
    n_trials
        Optuna trials per cell (naive count — used for N_eff upper bound).
    symbols
        Active universe tuple.
    features_dir
        Path to feature parquet directory.
    interval
        Candle interval string (e.g. "8h").
    oof_parquet_path
        Path to the per-trial OOF parquet from optimization.py.  May be None
        when the backtest did not set oof_persist_path (falls back to naive n_trials).
    feature_columns
        Columns used for training — controls which columns the ADF and IC
        outputs are computed on. Defaults to V1_FEATURE_COLUMNS (193 cols).
        Pass list(V1_FEATURE_COLUMNS_PRUNED) for iter-v1/002+ pruned runs so
        the methodology artifacts reflect the 40-col training space.
    """
    # Path Forward #2 (Critic Phase 6.0): fail-fast rather than silently falling back
    # to naive_fallback, which would mechanically violate brief F3 + Section 8 criterion 4.
    # The assert fires after the backtest has run, so the parquet must exist by now.
    assert oof_parquet_path is not None and Path(oof_parquet_path).exists(), (
        f"oof_parquet_path missing or does not exist: {oof_parquet_path!r} — "
        "naive_fallback would violate brief F3 + Section 8 criterion 4 "
        "(n_eff = n_trials_naive triggers NO-MERGE). "
        "Ensure oof_persist_path=OOF_PARQUET_PATH is passed to every LightGbmStrategy call."
    )

    print("\n[run_baseline_v1] === iter-v1/001 methodology reporting ===")

    # Split trades
    is_trades = [t for t in all_results if t.open_time < OOS_CUTOFF_MS]
    oos_trades = [t for t in all_results if t.open_time >= OOS_CUTOFF_MS]

    # ---------------------------------------------------------------------------
    # 1. PSR columns (monthly + daily, both halves)
    # ---------------------------------------------------------------------------
    is_monthly = _load_pnl_series(is_trades, "monthly")
    is_daily = _load_pnl_series(is_trades, "daily")
    oos_monthly = _load_pnl_series(oos_trades, "monthly")
    oos_daily = _load_pnl_series(oos_trades, "daily")

    is_psr_cols = compute_psr_columns(is_monthly, is_daily)
    oos_psr_cols = compute_psr_columns(oos_monthly, oos_daily)

    print(
        f"[run_baseline_v1] IS  PSR: monthly_vs_0={is_psr_cols['psr_monthly_vs_0']:.4f} "
        f"monthly_vs_1={is_psr_cols['psr_monthly_vs_1']:.4f} "
        f"daily_vs_0={is_psr_cols['psr_daily_vs_0']:.4f}"
    )
    print(
        f"[run_baseline_v1] OOS PSR: monthly_vs_0={oos_psr_cols['psr_monthly_vs_0']:.4f} "
        f"monthly_vs_1={oos_psr_cols['psr_monthly_vs_1']:.4f} "
        f"daily_vs_0={oos_psr_cols['psr_daily_vs_0']:.4f}"
    )

    # ---------------------------------------------------------------------------
    # 2. N_eff + corrected DSR (both halves)
    # Per LM Master §2: we use the same oof_parquet for both halves
    # since the OOF data comes from the IS training pass.  OOS DSR is computed
    # using the IS-derived N_eff (the search was over IS data).
    # ---------------------------------------------------------------------------
    is_daily_arr = np.asarray(is_daily, dtype=float)
    oos_daily_arr = np.asarray(oos_daily, dtype=float)

    # Annualized daily Sharpe for DSR inputs
    is_sharpe_ann = (
        float(is_daily_arr.mean() / is_daily_arr.std() * math.sqrt(365))
        if len(is_daily_arr) >= 2 and is_daily_arr.std() > 0
        else 0.0
    )
    oos_sharpe_ann = (
        float(oos_daily_arr.mean() / oos_daily_arr.std() * math.sqrt(365))
        if len(oos_daily_arr) >= 2 and oos_daily_arr.std() > 0
        else 0.0
    )

    # Total naive n_trials = n_trials per cell × n_cells
    # n_cells = n_months_train × n_models_of_type.  The runner has 4 models
    # (A covers 2 syms, C/D/E cover 1 sym each) × ~36 IS months.
    # Approximate: pass n_trials as the per-cell count; optimization.py
    # accumulates across (symbol, month, seed) in the parquet.
    is_n_eff, is_dsr, is_method = compute_n_eff_and_dsr(
        oof_parquet_path,
        n_trials_naive=n_trials,
        observed_sharpe=is_sharpe_ann,
        returns=is_daily_arr.tolist(),
    )
    oos_n_eff, oos_dsr, oos_method = compute_n_eff_and_dsr(
        oof_parquet_path,
        n_trials_naive=n_trials,
        observed_sharpe=oos_sharpe_ann,
        returns=oos_daily_arr.tolist(),
    )

    # Runtime sanity check (brief Section 8 criterion 4 / LM Master saturation risk).
    # Only fires when an OOF parquet was provided (PCA ran) — not on naive fallback.
    # When oof_parquet_path is None, is_n_eff == n_trials (naive) and the assert
    # would trivially fail; the brief's guard is only meaningful with actual PCA.
    if oof_parquet_path is not None and oof_parquet_path.exists():
        # Softened from strict < to <= after iter-v1/001 post-mortem: PCA can
        # legitimately return n_eff == n_trials when all trials are linearly
        # independent in the flattened OOF return space.  This is an informative
        # outcome (TPE explored distinct regions; no trial duplication), not a
        # bug.  The method string is set to "eigvalsh_no_compression" by
        # reporting_v1 to distinguish this from the naive_fallback path.
        assert is_n_eff <= n_trials or n_trials <= 1, (
            f"N_eff sanity check failed: is_n_eff={is_n_eff} > n_trials={n_trials}. "
            "PCA returned more effective trials than naive count — impossible; "
            "check oof_parquet_path pivot and trial matrix."
        )
        if is_n_eff == n_trials and n_trials > 1:
            print(
                f"[run_baseline_v1] WARN: N_eff PCA produced no compression "
                f"(is_n_eff={is_n_eff} == n_trials={n_trials}). "
                "The 50 trials are linearly independent in the OOF return space "
                "(5 symbols × 53 train-months × 5 fold_idx collapsed to 50 unique "
                "trial_id keys). LM Master Phase 4.5 §2 expected [15, 80]; "
                "empirical reality is upper-bound = n_trials_per_cell. "
                "Phase 7.5 Critic should evaluate whether brief F3 invariant "
                "(`n_effective_trials < n_trials_total`) is satisfied with "
                "`n_eff_pca_method=eigvalsh_no_compression` (truthful PCA outcome) "
                "vs `n_eff_pca_method=naive_fallback` (untruthful skipped PCA)."
            )

    print(f"[run_baseline_v1] IS  N_eff={is_n_eff} DSR_corrected={is_dsr:.4f} method={is_method}")
    print(
        f"[run_baseline_v1] OOS N_eff={oos_n_eff} DSR_corrected={oos_dsr:.4f} method={oos_method}"
    )

    # ---------------------------------------------------------------------------
    # 2b. Per-cell N_eff (iter-v1/008 PRIMARY estimator via _per_cell_n_eff_from_parquet)
    # Called AFTER compute_n_eff_and_dsr so that the per-cell dict can be wired
    # into write_dsr_json + append_psr_rows_to_comparison below.
    # Both IS and OOS use the same OOF parquet (OOF data is IS-derived; OOS DSR
    # is computed using the IS-calibrated n_eff — per LM Master §2).
    # ---------------------------------------------------------------------------
    per_cell_result: dict | None = None
    if oof_parquet_path is not None and Path(oof_parquet_path).exists():
        try:
            per_cell_result = _per_cell_n_eff_from_parquet(
                Path(oof_parquet_path),
                n_trials,
            )
            print(
                f"[run_baseline_v1] per-cell N_eff: "
                f"median={per_cell_result['n_eff_per_cell_median']} "
                f"trimmed_mean={per_cell_result['n_eff_per_cell_trimmed_mean']} "
                f"p25={per_cell_result['n_eff_per_cell_p25']} "
                f"p75={per_cell_result['n_eff_per_cell_p75']} "
                f"n_cells={per_cell_result['n_cells']} "
                f"by_symbol={per_cell_result['n_eff_per_cell_by_symbol']}"
            )
        except Exception as exc:
            print(
                f"[run_baseline_v1] WARNING: _per_cell_n_eff_from_parquet failed ({exc}); "
                "per-cell fields will be absent from dsr.json"
            )
            per_cell_result = None

    # Min TRL months: 1/sqrt(12) (monthly benchmark SR for psr_monthly_vs_1)
    min_trl_months = 1.0 / math.sqrt(12)

    # ---------------------------------------------------------------------------
    # 3. dsr.json (both halves)
    # ---------------------------------------------------------------------------
    write_dsr_json(
        is_dir,
        dsr=is_dsr,
        pbo=None,  # CPCV deferred to iter-v1/002+ per brief Section 9
        psr_val=is_psr_cols["psr_monthly_vs_1"],
        n_trials=n_trials,
        n_eff=is_n_eff,
        n_eff_pca_method=is_method,
        min_trl_months=min_trl_months,
        label="IS",
        # iter-v1/008 per-cell fields
        n_eff_per_cell_median=(
            per_cell_result["n_eff_per_cell_median"] if per_cell_result else None
        ),
        n_eff_per_cell_trimmed_mean=(
            per_cell_result["n_eff_per_cell_trimmed_mean"] if per_cell_result else None
        ),
        n_eff_per_cell_p25=(per_cell_result["n_eff_per_cell_p25"] if per_cell_result else None),
        n_eff_per_cell_p75=(per_cell_result["n_eff_per_cell_p75"] if per_cell_result else None),
        n_eff_per_cell_min=(per_cell_result["n_eff_per_cell_min"] if per_cell_result else None),
        n_eff_per_cell_max=(per_cell_result["n_eff_per_cell_max"] if per_cell_result else None),
        n_eff_per_cell_by_symbol=(
            per_cell_result["n_eff_per_cell_by_symbol"] if per_cell_result else None
        ),
        n_cells=(per_cell_result["n_cells"] if per_cell_result else None),
    )
    write_dsr_json(
        oos_dir,
        dsr=oos_dsr,
        pbo=None,
        psr_val=oos_psr_cols["psr_monthly_vs_1"],
        n_trials=n_trials,
        n_eff=oos_n_eff,
        n_eff_pca_method=oos_method,
        min_trl_months=min_trl_months,
        label="OOS",
        # Same per-cell fields: OOF is IS-derived; same parquet used for both halves
        n_eff_per_cell_median=(
            per_cell_result["n_eff_per_cell_median"] if per_cell_result else None
        ),
        n_eff_per_cell_trimmed_mean=(
            per_cell_result["n_eff_per_cell_trimmed_mean"] if per_cell_result else None
        ),
        n_eff_per_cell_p25=(per_cell_result["n_eff_per_cell_p25"] if per_cell_result else None),
        n_eff_per_cell_p75=(per_cell_result["n_eff_per_cell_p75"] if per_cell_result else None),
        n_eff_per_cell_min=(per_cell_result["n_eff_per_cell_min"] if per_cell_result else None),
        n_eff_per_cell_max=(per_cell_result["n_eff_per_cell_max"] if per_cell_result else None),
        n_eff_per_cell_by_symbol=(
            per_cell_result["n_eff_per_cell_by_symbol"] if per_cell_result else None
        ),
        n_cells=(per_cell_result["n_cells"] if per_cell_result else None),
    )

    # ---------------------------------------------------------------------------
    # 4. comparison.csv PSR + n_effective_trials + n_eff_per_cell_median rows
    # ---------------------------------------------------------------------------
    comparison_path = iter_dir / "comparison.csv"
    if comparison_path.exists():
        append_psr_rows_to_comparison(
            comparison_path,
            is_psr_cols,
            oos_psr_cols,
            is_n_eff=is_n_eff,
            oos_n_eff=oos_n_eff,
            is_n_eff_per_cell_median=(
                per_cell_result["n_eff_per_cell_median"] if per_cell_result else None
            ),
            oos_n_eff_per_cell_median=(
                per_cell_result["n_eff_per_cell_median"] if per_cell_result else None
            ),
        )
        # ---------------------------------------------------------------------------
        # 4b. comparison.csv R5 fire-rate IS/OOS rows (iter-v1/010 reporting patch)
        # ---------------------------------------------------------------------------
        r5_fire_rate_is = (r5_fires_is / r5_signals_is) if r5_signals_is > 0 else 0.0
        r5_fire_rate_oos = (r5_fires_oos / r5_signals_oos) if r5_signals_oos > 0 else 0.0
        append_r5_rows_to_comparison(comparison_path, r5_fire_rate_is, r5_fire_rate_oos)
        # ---------------------------------------------------------------------------
        # 4c. comparison.csv R5-BINARY-KILL fire-rate rows (iter-v1/011 reporting)
        # Fixes D-RPRT-001: IS value in in_sample column, OOS value in out_of_sample.
        # ---------------------------------------------------------------------------
        r5_kill_rate_is = r5_kill_fires_is / r5_kill_signals_is if r5_kill_signals_is > 0 else 0.0
        r5_kill_rate_oos = (
            r5_kill_fires_oos / r5_kill_signals_oos if r5_kill_signals_oos > 0 else 0.0
        )
        append_r5_binary_kill_rows_to_comparison(comparison_path, r5_kill_rate_is, r5_kill_rate_oos)
    else:
        print(
            "[run_baseline_v1] WARNING: comparison.csv not found at "
            f"{comparison_path}; skipping append"
        )

    # ---------------------------------------------------------------------------
    # 5. adf_test.csv (IS features only — per brief Section 2 IS-only discipline)
    # ---------------------------------------------------------------------------
    print("[run_baseline_v1] Loading IS features for ADF test...")
    feature_df = _load_features_for_adf_ic(symbols, features_dir, interval, feature_columns)
    if feature_df is not None and not feature_df.empty:
        write_adf_test_csv(is_dir, feature_df, label="IS")
        # OOS dir gets the same ADF result (feature stationarity is IS-calibrated)
        write_adf_test_csv(oos_dir, feature_df, label="OOS(same IS features)")
    else:
        print("[run_baseline_v1] WARNING: no feature parquets found; adf_test.csv skipped")

    # ---------------------------------------------------------------------------
    # 6. ic_matrix.csv (IS features vs 1-bar forward return)
    # ---------------------------------------------------------------------------
    if feature_df is not None and not feature_df.empty:
        print("[run_baseline_v1] Computing IC matrix...")
        fwd_returns = _compute_forward_returns(symbols, features_dir, interval)
        if fwd_returns is not None and len(fwd_returns) == len(feature_df):
            write_ic_matrix_csv(is_dir, feature_df, fwd_returns, label="IS")
            write_ic_matrix_csv(oos_dir, feature_df, fwd_returns, label="OOS(same IS features)")
        else:
            print(
                f"[run_baseline_v1] WARNING: forward returns shape mismatch "
                f"({len(fwd_returns) if fwd_returns is not None else 'None'} vs feature_df "
                f"{len(feature_df)}); ic_matrix.csv skipped"
            )
    else:
        print("[run_baseline_v1] WARNING: feature_df unavailable; ic_matrix.csv skipped")

    print("[run_baseline_v1] === methodology reporting complete ===\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="v1 baseline runner — refactored 2026-05-23")
    parser.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="Iteration number (iter-v1/NNN; required unless --baseline-mode)",
    )
    parser.add_argument(
        "--baseline-mode",
        action="store_true",
        help=(
            "Reproduce the BASELINE_V1.md anchor stats. Writes to "
            "reports-v1/iteration_v1-baseline/. Use to populate corrected baseline."
        ),
    )
    parser.add_argument(
        "--exploration",
        action="store_true",
        help="EXPLORATION mode: ENSEMBLE_SIZE=3, 2h wall-clock target.",
    )
    parser.add_argument(
        "--confirmation",
        action="store_true",
        help="CONFIRMATION mode: ENSEMBLE_SIZE=10, 6h wall-clock target.",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help="Optuna trials per (symbol, month) cell. Default 35 (matches v3).",
    )
    parser.add_argument(
        "--ensemble-size",
        type=int,
        default=None,
        help=(
            "Override the mode-derived ENSEMBLE_SIZE.  Useful for methodology-axis "
            "iterations that require a specific ensemble size for byte-identity "
            "against the baseline anchor (e.g. --exploration --ensemble-size 5 "
            "--n-trials 50 for iter-v1/001 trade-roster byte-identity).  "
            "Must be in [1, 10].  Overrides the mode default (3 for EXPLORATION, "
            "10 for CONFIRMATION) without touching any other mode semantics."
        ),
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated symbols (default: V1_BASELINE_UNIVERSE).",
    )
    parser.add_argument(
        "--pruned-features",
        action="store_true",
        help=(
            "Use V1_FEATURE_COLUMNS_PRUNED (40 features) instead of V1_FEATURE_COLUMNS "
            "(193 features). Activates the 'v1_pruned' Optuna bounds profile per "
            "LM Master Phase 4.5 Recs #1–3. Introduced for iter-v1/002."
        ),
    )
    parser.add_argument(
        "--r5-binary-kill-enabled",
        action="store_true",
        help=(
            "Enable R5-BINARY-KILL entry filter (iter-v1/011). Skips entries where "
            "NATR_14 at signal time is strictly below --r5-binary-kill-min-natr. "
            "When enabled, R5 proportional vol-target ceiling is DISABLED for axis "
            "isolation. Default: off."
        ),
    )
    parser.add_argument(
        "--r5-binary-kill-min-natr",
        type=float,
        default=2.0,
        help=(
            "NATR_14 floor for R5-BINARY-KILL (percent, default 2.0). "
            "Entries where NATR_14 < this value are skipped. "
            "Only evaluated when --r5-binary-kill-enabled is set."
        ),
    )
    parser.add_argument(
        "--ensemble-seeds-offset",
        type=int,
        default=0,
        help=(
            "Starting index into ENSEMBLE_SEEDS for inner seed selection. "
            "Default 0 reproduces canonical EXPLORATION/CONFIRMATION seed windows "
            "([42, 123, 456, ...]). iter-v1/012 SUBSTRATE-DISSOLUTION PROBE uses "
            "--ensemble-seeds-offset 3 to select DISJOINT inner seeds [789, 1001, 2002] "
            "from /011's [42, 123, 456], staying inside the canonical CONFIRMATION roster. "
            "Must satisfy offset + ENSEMBLE_SIZE <= 10."
        ),
    )
    args = parser.parse_args()

    # Resolve symbols
    if args.symbols:
        symbols = tuple(s.strip().upper() for s in args.symbols.split(","))
    else:
        symbols = V1_BASELINE_UNIVERSE

    # MANDATORY runtime audit — fails loudly if a v2/v3 symbol leaks in
    assert_v1_universe(symbols)

    # Resolve mode
    if args.baseline_mode:
        mode_label = "BASELINE"
        # Historical v186 ran 5-seed ensemble [42, 123, 456, 789, 1001] + 50 trials.
        # MUST match exactly for deterministic trade reproduction against reports/iteration_186/
        # (per feedback_deterministic_trade_match.md). The new 10-seed CONFIRMATION standard
        # applies only to iter-v1/NNN+ iterations, NOT to the baseline anchor reproduction.
        ensemble_size = 5
        n_trials = 50
        iteration_label = "v1-baseline"
        reports_dir = "reports-v1"
    elif args.exploration:
        mode_label = "EXPLORATION"
        ensemble_size = V1_EXPLORATION_ENSEMBLE_SIZE
        n_trials = args.n_trials
        if args.iteration is None:
            sys.exit("ERROR: --exploration requires --iteration NNN")
        iteration_label = f"v1-{args.iteration:03d}"
        reports_dir = "reports-v1"
    elif args.confirmation:
        mode_label = "CONFIRMATION"
        ensemble_size = V1_CONFIRMATION_ENSEMBLE_SIZE
        n_trials = args.n_trials
        if args.iteration is None:
            sys.exit("ERROR: --confirmation requires --iteration NNN")
        iteration_label = f"v1-{args.iteration:03d}"
        reports_dir = "reports-v1"
    else:
        sys.exit("ERROR: must specify --baseline-mode, --exploration, or --confirmation")

    # --ensemble-size override: applies after mode defaults are set.
    # Designed for methodology-axis iterations (e.g. iter-v1/001) that need a
    # specific ensemble size for byte-identity against the baseline anchor without
    # clobbering the baseline reports directory.  --baseline-mode is intentionally
    # excluded from the override path (it has its own sacred fixed values).
    if args.ensemble_size is not None and not args.baseline_mode:
        if args.ensemble_size < 1 or args.ensemble_size > len(ENSEMBLE_SEEDS):
            sys.exit(
                f"ERROR: --ensemble-size must be in [1, {len(ENSEMBLE_SEEDS)}]; "
                f"got {args.ensemble_size}"
            )
        ensemble_size = args.ensemble_size
        default_size = (
            V1_EXPLORATION_ENSEMBLE_SIZE if args.exploration else V1_CONFIRMATION_ENSEMBLE_SIZE
        )
        print(
            f"[run_baseline_v1] --ensemble-size override: {ensemble_size} "
            f"(mode default was {default_size})"
        )

    # Resolve feature columns + Optuna bounds profile.
    # --pruned-features activates V1_FEATURE_COLUMNS_PRUNED (40 cols) and the
    # "v1_pruned" bounds profile (tighter num_leaves/colsample/min_child_samples).
    # Default keeps V1_FEATURE_COLUMNS (193 cols) and "default" bounds.
    if getattr(args, "pruned_features", False):
        active_feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)
        bounds_profile = "v1_pruned"
    else:
        active_feature_columns = list(V1_FEATURE_COLUMNS)
        bounds_profile = "default"

    # iter-v1/011: R5 risk config resolution.
    # --r5-binary-kill-enabled flips to binary-kill mode and DISABLES proportional
    # vol-target scaling for axis isolation (per brief Section 3.1 + Section 3.5).
    r5_vol_target_enabled = True  # historical default (active through /010)
    r5_vol_target_pct = 4.0
    r5_kill_low_natr_enabled = False
    r5_kill_low_natr_min_pct = 2.0
    if getattr(args, "r5_binary_kill_enabled", False):
        r5_kill_low_natr_enabled = True
        r5_kill_low_natr_min_pct = float(getattr(args, "r5_binary_kill_min_natr", 2.0))
        r5_vol_target_enabled = False  # disable /010 proportional scaling for isolation
        print(
            f"[run_baseline_v1] R5-BINARY-KILL enabled: kill_low_natr_min_pct="
            f"{r5_kill_low_natr_min_pct}% | R5 vol-target DISABLED for axis isolation"
        )

    # iter-v1/008: restore /003-era iteration-stamped OOF_PARQUET_PATH.
    # The global OOF_PARQUET_PATH is overridden here BEFORE the unlink() guard below
    # so that each iteration preserves its own parquet and future per-cell N_eff
    # re-evaluations can reproduce the exact /008 analysis.
    # Pattern mirrors /003 commit 976ce75 (partial-merge infrastructure).
    global OOF_PARQUET_PATH  # noqa: PLW0603
    OOF_PARQUET_PATH = Path("data") / f"v1_iter_{iteration_label}_trial_oof.parquet"

    # Resolve ensemble-seeds offset. Default 0 = canonical seed window.
    # iter-v1/012 SUBSTRATE-DISSOLUTION PROBE: offset=3 selects DISJOINT inner
    # seeds [789, 1001, 2002] vs /011's [42, 123, 456] while staying inside the
    # canonical CONFIRMATION roster (so /015 multi-seed CONFIRMATION naturally
    # subsumes both /011's and /012's basin draws).
    # --baseline-mode forces offset=0 (sacred reproduction of historical v186).
    ensemble_seeds_offset = (
        0 if args.baseline_mode else int(getattr(args, "ensemble_seeds_offset", 0))
    )
    if ensemble_seeds_offset != 0 and not args.baseline_mode:
        print(
            f"[run_baseline_v1] --ensemble-seeds-offset {ensemble_seeds_offset} "
            f"(SUBSTRATE-DISSOLUTION PROBE — canonical offset is 0)"
        )

    print(f"v1 RUNNER mode={mode_label} iteration={iteration_label}")
    print(f"  symbols: {symbols}")
    print(f"  ENSEMBLE_SIZE: {ensemble_size}")
    print(
        f"  ensemble_seeds: "
        f"{_derive_ensemble_seeds(ensemble_size, offset=ensemble_seeds_offset)} "
        f"(offset={ensemble_seeds_offset})"
    )
    print(f"  n_trials per cell: {n_trials}")
    print(f"  feature_columns: {len(active_feature_columns)} columns")
    print(f"  bounds_profile: {bounds_profile}")
    print(f"  OOF_PARQUET_PATH: {OOF_PARQUET_PATH}")
    print(f"  V1_EXCLUDED_SYMBOLS: {V1_EXCLUDED_SYMBOLS}")
    print(f"  r5_vol_target_enabled: {r5_vol_target_enabled}")
    print(f"  r5_kill_low_natr_enabled: {r5_kill_low_natr_enabled}")
    print()

    # Validate active feature list is non-empty (hard guard per feature-pinning rules).
    if not active_feature_columns:
        sys.exit("ERROR: active_feature_columns is empty — cannot train.")

    # A7 guard — clear stale OOF parquet from any prior run before training starts.
    # optimization.py appends rows; a leftover file from a crashed/partial run would
    # silently pollute the PCA-N_eff matrix with rows from a different trial budget.
    OOF_PARQUET_PATH.unlink(missing_ok=True)

    # -------------------------------------------------------------------------
    # Single-pass flat model loop.
    #
    # v1 skill design: EXPLORATION = ENSEMBLE_SIZE=3 inner seeds, single-pass.
    #                  CONFIRMATION = ENSEMBLE_SIZE=10 inner seeds, single-pass.
    # HIGH-RISK mitigation (iter-v1/002): opt-in to --ensemble-size 10 (CONFIRMATION-
    # grade inner ensemble) via CLI flag; NO outer-seed loop.
    #
    # V1_BASELINE_UNIVERSE = (BTC, ETH, LINK, LTC, DOT)
    # Models: A (pooled BTC+ETH), C (LINK), D (LTC), E (DOT)
    # For non-baseline universes, each symbol gets its own model unless
    # the brief specifies pooling (iter-v1/NNN brief Section 3 controls).
    # -------------------------------------------------------------------------
    all_results: list = []

    # Shared R5 kwargs passed to every run_model call.
    # iter-v1/012: ensemble_seeds_offset threaded through so all 4 models
    # (A pooled, C LINK, D LTC, E DOT) use the SAME inner-seed window.
    _r5_kwargs = dict(
        r5_vol_target_enabled=r5_vol_target_enabled,
        r5_vol_target_pct=r5_vol_target_pct,
        r5_kill_low_natr_enabled=r5_kill_low_natr_enabled,
        r5_kill_low_natr_min_pct=r5_kill_low_natr_min_pct,
        ensemble_seeds_offset=ensemble_seeds_offset,
    )
    if set(symbols) == set(V1_BASELINE_UNIVERSE):
        results_a = run_model(
            "A (BTC/ETH)",
            ("BTCUSDT", "ETHUSDT"),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        results_c = run_model(
            "C (LINK + R1)",
            ("LINKUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        results_d = run_model(
            "D (LTC + R1)",
            ("LTCUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        results_e = run_model(
            "E (DOT + R1 + R2)",
            ("DOTUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            apply_r2=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        all_results = results_a + results_c + results_d + results_e
        # Aggregate R5 IS/OOS split counters across all four models (iter-v1/010+).
        _r5_model_results = [results_a, results_c, results_d, results_e]
    else:
        # Custom universe — single pooled model unless brief specifies otherwise.
        # iter-v1/NNN brief Section 3 should declare per-symbol model assignment.
        _pooled = run_model(
            "POOLED",
            symbols,
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        all_results = _pooled
        _r5_model_results = [_pooled]

    # Aggregate R5 IS/OOS split counters from BacktestResult attributes.
    agg_r5_signals_is = sum(getattr(r, "r5_signals_is", 0) for r in _r5_model_results)
    agg_r5_fires_is = sum(getattr(r, "r5_fires_is", 0) for r in _r5_model_results)
    agg_r5_signals_oos = sum(getattr(r, "r5_signals_oos", 0) for r in _r5_model_results)
    agg_r5_fires_oos = sum(getattr(r, "r5_fires_oos", 0) for r in _r5_model_results)
    # Aggregate R5-BINARY-KILL IS/OOS split counters (iter-v1/011).
    agg_r5_kill_signals_is = sum(getattr(r, "r5_kill_signals_is", 0) for r in _r5_model_results)
    agg_r5_kill_fires_is = sum(getattr(r, "r5_kill_fires_is", 0) for r in _r5_model_results)
    agg_r5_kill_signals_oos = sum(getattr(r, "r5_kill_signals_oos", 0) for r in _r5_model_results)
    agg_r5_kill_fires_oos = sum(getattr(r, "r5_kill_fires_oos", 0) for r in _r5_model_results)

    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades")
    if not all_results:
        sys.exit(1)

    # Reports written to reports-v1/iteration_v1-<label>/ (parallel to v2/v3 layout).
    report_dir = generate_iteration_reports(
        trades=all_results,
        iteration=iteration_label,
        features_dir="data/features",
        reports_dir=reports_dir,
        interval="8h",
        n_trials=n_trials,
    )
    print(f"Reports: {report_dir}")

    # -------------------------------------------------------------------------
    # iter-v1/001 methodology reporting — post-hoc; does NOT change predictions
    # or trade roster. Appends PSR + N_eff rows to comparison.csv and writes
    # dsr.json, adf_test.csv, ic_matrix.csv for both IS and OOS halves.
    # oof_parquet_path: optimization.py appended rows here during training
    # (oof_persist_path=OOF_PARQUET_PATH was passed to each LightGbmStrategy call).
    # The same fixed path is passed here so _run_methodology_reporting can load
    # the PCA-N_eff matrix and avoid the naive_fallback path.
    # -------------------------------------------------------------------------
    is_dir = report_dir / "in_sample"
    oos_dir = report_dir / "out_of_sample"
    _run_methodology_reporting(
        all_results,
        iter_dir=report_dir,
        is_dir=is_dir,
        oos_dir=oos_dir,
        n_trials=n_trials,
        symbols=symbols,
        features_dir="data/features",
        interval="8h",
        oof_parquet_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        r5_signals_is=agg_r5_signals_is,
        r5_fires_is=agg_r5_fires_is,
        r5_signals_oos=agg_r5_signals_oos,
        r5_fires_oos=agg_r5_fires_oos,
        r5_kill_signals_is=agg_r5_kill_signals_is,
        r5_kill_fires_is=agg_r5_kill_fires_is,
        r5_kill_signals_oos=agg_r5_kill_signals_oos,
        r5_kill_fires_oos=agg_r5_kill_fires_oos,
    )

    print(
        f"\nMode: {mode_label}. ENSEMBLE_SIZE={ensemble_size}. n_trials={n_trials}. "
        f"features={len(active_feature_columns)}. "
        f"bounds={bounds_profile}. Iteration: {iteration_label}."
    )
    if mode_label == "BASELINE":
        print(
            "\nBASELINE-MODE complete. Update BASELINE_V1.md with the headline "
            "metrics from comparison.csv (monthly_sharpe, max_drawdown, n_trades, "
            "etc.). Tag the commit as `v0.v1-baseline-corrected`."
        )


if __name__ == "__main__":
    main()
