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
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig, BacktestResult, TradeResult
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
from crypto_trade.strategies.ml.risk_v2 import (
    BtcTrendFilterConfig,
    apply_btc_trend_filter,
    load_btc_klines_for_filter,
)
from crypto_trade.strategies.regime_gate_v1 import (
    RegimeGateConfig,
    RegimeRoutedStrategy,
    make_extreme_filter,
    make_normal_filter,
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

#: iter-v1/017: 6-symbol universe for EXPLORATION.
#: LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
#: updates V1_BASELINE_UNIVERSE). Adding SOLUSDT as isolated Model F preserves
#: baseline A/C/D/E semantics for clean single-axis attribution.
V1_ITER017_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "SOLUSDT",  # NEW — Model F (iter-v1/017 universe expansion)
)

#: iter-v1/018: LINK-only single-cohort EXPLORATION (cycle-3 #3 of 10).
#:
#: USER STRATEGIC PIVOT 2026-05-26 (feedback_v1_per_cohort_exploration_strategy.md):
#: EXPLORATIONs test per-cohort specializations; CONFIRMATION /027 bundles
#: specialists for diversification edge. iter-v1/018 is the FIRST per-cohort
#: EXPLORATION — LINK structural OOS prior is strongest at 8/8 iterations positive.
#:
#: LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
#: updates V1_BASELINE_UNIVERSE). Single-symbol subset of V1_BASELINE_UNIVERSE.
#: assert_v1_universe() accepts {LINKUSDT} because LINKUSDT is NOT in V1_EXCLUDED_SYMBOLS.
V1_ITER018_UNIVERSE: tuple[str, ...] = ("LINKUSDT",)

#: iter-v1/019: ETH-only single-cohort EXPLORATION + direction-aware BTC-trend gate
#:              (cycle-3 #4 of 10; per-cohort-specialization-ETH; NEW 10th axis family).
#:
#: USER STRATEGIC PIVOT 2026-05-26 cycle-3 #4 EXPLORATION:
#: per-cohort-specialization-ETH. ETH has strongest NEGATIVE per-symbol structural
#: prior (5/5 IS-OOS negative across baseline + /014-/017).
#: Direction-aware BTC-trend gate at +-8% on BTC 14d return kills counter-trend ETH
#: entries; IS EDA shows +42.47% PnL lift with cross-year stability (H1 +6.33% / H2 +36.15%).
#:
#: LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
#: updates V1_BASELINE_UNIVERSE). assert_v1_universe() accepts {ETHUSDT} because
#: ETHUSDT is NOT in V1_EXCLUDED_SYMBOLS.
V1_ITER019_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)

#: Gate configuration constants (frozen for /019 per brief Section 3.3 + LM Master §6.4).
#: Tunable at /020+ verdict-conditional (TIGHTER +-5% if under-fire, WIDER +-12% if over-kill).
V1_ITER019_BTC_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h cadence
V1_ITER019_BTC_GATE_THRESHOLD_PCT: float = 8.0  # +-8% BTC 14d return
V1_ITER019_BTC_GATE_ENABLED: bool = True

#: iter-v1/020: BTC-only single-cohort EXPLORATION (cycle-3 #5 of 10).
#:
#: USER STRATEGIC PIVOT 2026-05-26 cycle-3 #5 EXPLORATION:
#: per-cohort-specialization-BTC (NEW 11th axis family). BTC has UNIQUE IS-OOS
#: asymmetric rotation prior: 5/5 IS-NEGATIVE (mean -38.12%) + 4/5 OOS-POSITIVE
#: (mean +7.70%) across baseline + /014-/017. EDA diagnostics support H_INTRINSIC
#: (regime-bound IS catastrophic in IS_H1; Pearson(BTC,ETH) monthly = -0.0220
#: in pool → labels statistically independent, H_POOL_ANCHOR refuted at ρ ≈ 0).
#:
#: Pure cohort isolation: NO BTC-trend gate, NO new feature, NO new labeling.
#: Tests whether cohort isolation ALONE restructures BTC's asymmetric rotation
#: or whether a specialization knob is required at later iters.
#:
#: LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
#: updates V1_BASELINE_UNIVERSE). assert_v1_universe() accepts {BTCUSDT} because
#: BTCUSDT is in V1_BASELINE_UNIVERSE.
V1_ITER020_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)

#: iter-v1/021: METHODOLOGY PIVOT — diagnostic run of BOTH Model A pool (5-sym) AND
#: Model H (BTC-only) side-by-side at n_trials=18 seed=42 to capture Optuna best-trial
#: parameters per (model_role, symbol, train_month, seed) for the H1 pool-anchor falsifier.
#: Also adds _write_feature_importance for the H2 feature-signature diagnostic.
#:
#: The FULL 5-symbol pool universe is used for the dispatch trigger (set equality).
#: All 5 symbols are needed because Model A pool trains on BTC+ETH and Models C/D/E
#: are BIT-IDENTICAL to baseline; Model H (BTC-only) runs as a second model dispatched
#: alongside Model A pool.
V1_ITER021_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

V1_ITER022_UNIVERSE: tuple[str, ...] = ("LTCUSDT",)
"""iter-v1/022 cohort: LTC-only with stateless long-suppression BTC-trend gate.

USER STRATEGIC PIVOT 2026-05-26 cycle-3 #7 EXPLORATION:
per-cohort-specialization-LTC (NEW 14th family). LTC is the WORST OOS contributor
in baseline (-47.25% / -0.27 per-trade Sharpe). LTC has the strongest directional
asymmetry of any v1 cohort: 89% of OOS loss in LONG direction; OOS shorts neutral.

Long-suppression BTC-trend gate at -4% on 42-bar BTC return (14 days at 8h) kills
LTC long entries when BTC is in bear regime; LTC shorts UNRESTRICTED. IS ORACLE EDA
shows +10.79% IS / +12.45% OOS lift (both halves positive).

LOCAL to runner. assert set(symbols) == {"LTCUSDT"} guard fires for this branch.
"""

#: iter-v1/023: full V1_BASELINE_UNIVERSE (5-sym) with funding-rate z-score feature family.
#: Feature-family EXPLORATION cycle-3 #8/10. V1_FEATURE_COLUMNS_PRUNED 40 → 42.
#: Dispatch is handled by the iteration_label == "v1-023" elif branch.
#: Feature importance for all 4 models collected via _post_dispatch_fi_strategies.

#: Gate configuration constants (frozen for /022; tunable at /023+ verdict-conditional).
V1_ITER022_BTC_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h (matches /019)
V1_ITER022_BTC_GATE_THRESHOLD_PCT: float = 4.0  # -4% BTC 14d return (TIGHTER than /019's 8%)
V1_ITER022_BTC_GATE_ENABLED: bool = True
V1_ITER022_BTC_GATE_LONG_ONLY: bool = True  # NEW asymmetric mode (long-suppression only)

#: iter-v1/024: regime-conditional sub-model architecture constants.
#: MODEL-ARCH axis: 3 cohorts (Pool A, LINK, LTC) × 2 sub-models + 1 cohort (DOT) × 1 = 7 total.
#: DOT excluded from regime conditioning per LM Master §1 (8 IS extreme trades — degenerate).
#: Funding-rate z-score regime threshold: |funding_rate_zscore_30| > 1.5 → extreme regime.
V1_ITER024_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)
V1_ITER024_REGIME_THRESHOLD: float = 1.5  # |z30| > 1.5 → extreme regime (EDA Section 2.3)
V1_ITER024_Z30_COLUMN: str = "funding_rate_zscore_30"  # past-only by .shift(1) in feature pipeline

#: iter-v1/021: stable path for Optuna best-params parquet (H1 diagnostic substrate).
#: Written by optimize_and_train when params_persist_path is set.
#: Cleared at runner start (same pattern as OOF_PARQUET_PATH) to prevent accumulation.
PARAMS_PARQUET_PATH: Path = Path("data") / "v1_iter_SENTINEL_optuna_best_params.parquet"

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
    sigma_source: str = "natr",
    sigma_k_tp: float | None = None,
    sigma_k_sl: float | None = None,
    sigma_halflife_days: int = 14,
    sample_weight_mode: str = "abs_pnl",
    params_persist_path: Path | None = None,
    model_role: str = "",
    symbol: str = "",
    data_filter_callback: Callable[[pd.DataFrame], np.ndarray] | None = None,
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
        "v1_pruned_axis016" for /016 sample-weighting axis isolation
        (pins subsample=colsample_bytree=1.0 per LM Master Rec #2).
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
    sigma_source
        iter-v1/014 — barrier labeling source. "natr" (default) preserves
        BIT-IDENTICAL behaviour to /013. "ewma14d" activates past-only EWMA
        σ_t-scaled barriers at sigma_halflife_days half-life.
    sigma_k_tp
        TP barrier multiplier for σ_t path (e.g. 1.06). Only used when
        sigma_source="ewma14d".
    sigma_k_sl
        SL barrier multiplier for σ_t path (e.g. 0.53). Only used when
        sigma_source="ewma14d".
    sigma_halflife_days
        Half-life in calendar days for EWMA σ_t (default 14 = 42 candles at 8h).
    sample_weight_mode
        iter-v1/016 — per-row weight mode for LightGBM training.
        "abs_pnl" (default) = BIT-IDENTICAL baseline behavior.
        "uniform" = np.ones(n); Kish n_eff = 1.000; selected for /016.
        "uniqueness_only" = raw AFML uniqueness replacing abs_pnl.
    data_filter_callback
        iter-v1/024 — optional training-data partition callback.
        Callable[[pd.DataFrame], np.ndarray] returning a boolean mask.
        Applied to train_indices BEFORE labeling in _train_for_month().
        Default None = no filter (backward-compatible).
    """
    effective_feature_columns = (
        feature_columns if feature_columns is not None else list(V1_FEATURE_COLUMNS)
    )
    sigma_halflife_candles = sigma_halflife_days * 3  # 3 candles per day at 8h
    print("=" * 60)
    print(
        f"MODEL {name}: {', '.join(symbols)} "
        f"(R1={apply_r1} R2={apply_r2} R3=on, n_trials={n_trials}, "
        f"ENSEMBLE_SIZE={ensemble_size}, features={len(effective_feature_columns)}, "
        f"bounds={bounds_profile}, sigma_source={sigma_source})"
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
        sigma_source=sigma_source,
        sigma_k_tp=sigma_k_tp,
        sigma_k_sl=sigma_k_sl,
        sigma_halflife_candles=sigma_halflife_candles,
        sample_weight_mode=sample_weight_mode,
        params_persist_path=params_persist_path,
        model_role=model_role,
        symbol=symbol,
        data_filter_callback=data_filter_callback,
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    # iter-v1/016: expose F-AXIS-MECHANISM log so the runner can write f_axis_mechanism.csv.
    # iter-v1/021: also return the strategy object for _write_feature_importance access.
    return results, strategy._faxm_log, strategy


def build_lgbm_strategy(
    atr_tp: float,
    atr_sl: float,
    *,
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
    sigma_source: str = "natr",
    sigma_k_tp: float | None = None,
    sigma_k_sl: float | None = None,
    sigma_halflife_days: int = 14,
    sample_weight_mode: str = "abs_pnl",
    params_persist_path: Path | None = None,
    model_role: str = "",
    symbol: str = "",
    data_filter_callback: Callable[[pd.DataFrame], np.ndarray] | None = None,
) -> LightGbmStrategy:
    """Build a LightGbmStrategy WITHOUT running a backtest.

    Factory function used by run_regime_cohort() to construct inner sub-strategies
    for RegimeRoutedStrategy before they are wrapped and dispatched via a SINGLE
    run_backtest() call on the wrapper.

    Parameters match run_model() exactly (minus the name/symbols/apply_r1/apply_r2
    arguments which belong to the BacktestConfig, not the strategy).  All semantics
    are identical to run_model() — this is just the strategy-construction portion
    separated from the backtest-execution portion.

    This function does NOT call run_backtest().  The caller (run_regime_cohort) is
    responsible for wrapping the returned strategy in RegimeRoutedStrategy and then
    calling run_backtest() exactly ONCE on the wrapper.
    """
    effective_feature_columns = (
        feature_columns if feature_columns is not None else list(V1_FEATURE_COLUMNS)
    )
    sigma_halflife_candles = sigma_halflife_days * 3  # 3 candles per day at 8h
    return LightGbmStrategy(
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
        sigma_source=sigma_source,
        sigma_k_tp=sigma_k_tp,
        sigma_k_sl=sigma_k_sl,
        sigma_halflife_candles=sigma_halflife_candles,
        sample_weight_mode=sample_weight_mode,
        params_persist_path=params_persist_path,
        model_role=model_role,
        symbol=symbol,
        data_filter_callback=data_filter_callback,
    )


def build_backtest_config(
    symbols: tuple[str, ...],
    *,
    apply_r1: bool,
    apply_r2: bool = False,
    r5_vol_target_enabled: bool = True,
    r5_vol_target_pct: float = 4.0,
    r5_kill_low_natr_enabled: bool = False,
    r5_kill_low_natr_min_pct: float = 2.0,
) -> BacktestConfig:
    """Build a BacktestConfig WITHOUT running a backtest.

    Factory function used by run_regime_cohort() to construct the BacktestConfig
    for a RegimeRoutedStrategy cohort.  Parameters and semantics are identical to
    the BacktestConfig construction inside run_model().

    Note: atr_tp / atr_sl are LightGbmStrategy parameters (labeling), NOT
    BacktestConfig parameters.  BacktestConfig uses fixed stop_loss_pct=4.0 and
    take_profit_pct=8.0 as percentage caps for the backtest engine.

    This function does NOT call run_backtest().
    """
    return BacktestConfig(
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


def run_regime_cohort(
    name: str,
    extreme_strategy: LightGbmStrategy,
    normal_strategy: LightGbmStrategy,
    config: BacktestConfig,
    regime_config: RegimeGateConfig,
    cohort_name: str = "",
) -> tuple[BacktestResult, list[dict], RegimeRoutedStrategy]:
    """Run ONE backtest via RegimeRoutedStrategy wrapper (iter-v1/024 regime dispatch).

    This is the CORRECT dispatch path for regime-conditional cohorts.  It:
    1. Wraps extreme_strategy + normal_strategy in a RegimeRoutedStrategy.
    2. Calls run_backtest() EXACTLY ONCE on the wrapper.
    3. Returns (results, combined_faxm_log, wrapper).

    The inner strategies must have been constructed with build_lgbm_strategy() and
    their respective data_filter_callback (make_extreme_filter / make_normal_filter).
    They must NOT have been passed to run_backtest() individually — doing so would
    run independent backtests on regime-partitioned training data and bypass the
    inference-time routing logic entirely (the defect this function fixes).

    The combined faxm_log merges extreme._faxm_log + normal._faxm_log so the runner's
    F-AXIS-MECHANISM reporting is complete across both sub-strategies.

    Parameters
    ----------
    name:
        Display name for logging (e.g. "Model_A_regime (BTC/ETH regime-routed)").
    extreme_strategy:
        LightGbmStrategy built with data_filter_callback=make_extreme_filter(...).
        NOT previously passed to run_backtest().
    normal_strategy:
        LightGbmStrategy built with data_filter_callback=make_normal_filter(...).
        NOT previously passed to run_backtest().
    config:
        BacktestConfig for the cohort's symbols + risk gates.
    regime_config:
        RegimeGateConfig specifying threshold + z30_column + enabled.
    cohort_name:
        Label for engineering report gate stats (e.g. "Pool_A").

    Returns
    -------
    (results, combined_faxm_log, wrapper)
        results: BacktestResult from run_backtest(config, wrapper).
        combined_faxm_log: extreme._faxm_log + normal._faxm_log.
        wrapper: the RegimeRoutedStrategy instance (for gate stats + FI access).
    """
    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strategy,
        normal_strategy=normal_strategy,
        config=regime_config,
        cohort_name=cohort_name,
    )
    print("=" * 60)
    print(
        f"MODEL {name}: {', '.join(config.symbols)} "
        f"(REGIME-ROUTED via RegimeRoutedStrategy, cohort={cohort_name})"
    )
    print("=" * 60)
    t0 = time.time()
    results = run_backtest(config, wrapper, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    # Merge faxm logs from both sub-strategies.
    combined_faxm: list[dict] = list(extreme_strategy._faxm_log) + list(normal_strategy._faxm_log)
    return results, combined_faxm, wrapper


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


def _write_feature_importance(
    strategies: list[tuple[str, object]],
    feature_columns: list[str],
    report_dir: Path,
) -> None:
    """Write per-model feature importance CSVs from trained LightGbmStrategy objects.

    iter-v1/021: Ported from run_baseline_v3.py:2730-2818 (iter-v3/017).
    Differences from v3:
    - Uses ``feature_columns`` (the active v1 feature list, e.g. V1_FEATURE_COLUMNS_PRUNED)
      as the fallback feature list instead of V3_FEATURE_COLUMNS.
    - Output naming: ``feature_importance_<MODEL_NAME>.csv`` for per-model and
      ``feature_importance_portfolio.csv`` for the portfolio aggregate.
    - Importance method: ``importance_type='gain'`` per LM Master Phase 4.5 §4 mandate
      (LOCKED in brief Section 3.2). Raw split count (noisier) and permutation
      importance (deferred) are NOT used.
    - Scope: last walk-forward month's model state (lazy monthly training — same
      scope as v3's ``_write_feature_importance``). Per-month aggregation is deferred
      per LM Master Phase 7.4 §6 outstanding gap.
    - Emits to ``in_sample/`` ONLY (per v3/017 fix — duplicating to OOS is misleading
      since the model state is IS-anchored at last-month training).

    Parameters
    ----------
    strategies
        List of (name_str, LightGbmStrategy-or-subclass) tuples. ``name_str`` is
        used as the per-model CSV filename suffix.
    feature_columns
        The active feature column list the models were trained on.
    report_dir
        Root report directory (CSVs written to ``report_dir / "in_sample"``).

    Notes
    -----
    iter-v1/021 BLOCK-PENDING-FIX H2: reads from ``_per_month_fi_log`` instead of
    ``inner._models``.  ``_models`` is reset to ``[]`` at the start of each
    walk-forward month in ``_train_for_month``; a post-dispatch read captures
    stale (empty) state for any model whose last month finished before the others.
    ``_per_month_fi_log`` is accumulated inside ``_train_for_month`` after the
    ensemble loop, immediately after ``self._confidence_threshold`` is set, so it
    is always written while ``_models`` is still populated for that month.

    Aggregation: across months, mean gain per feature (arithmetic mean of per-month
    means, unweighted by trade count — consistent with the per-month equal-weight
    pattern in the v3 reference at run_baseline_v3.py:2778-2783).
    """
    import csv as _csv  # noqa: PLC0415

    if not strategies:
        return

    cols = list(feature_columns)
    if not cols:
        return

    is_dir = report_dir / "in_sample"
    is_dir.mkdir(parents=True, exist_ok=True)

    portfolio: dict[str, float] = {c: 0.0 for c in cols}

    for name_str, strat in strategies:
        # Access the inner LightGbmStrategy (strategies passed directly here)
        inner = strat.inner if hasattr(strat, "inner") else strat

        # iter-v1/021 BLOCK-PENDING-FIX H2: use _per_month_fi_log (stale-safe)
        # instead of _models (stale after each _train_for_month call resets _models=[]).
        fi_log = getattr(inner, "_per_month_fi_log", [])
        if not fi_log:
            # Fallback: attempt legacy _models path (for strategies that do not yet
            # populate _per_month_fi_log — backward compatibility).
            if not hasattr(inner, "_models") or not inner._models:
                print(
                    f"[_write_feature_importance] WARNING: {name_str} has empty "
                    f"_per_month_fi_log AND empty _models — skipping (all-zero CSV avoided)."
                )
                continue

        if fi_log:
            # Primary path: aggregate mean gain across all walk-forward months.
            col_vals: dict[str, list[float]] = {c: [] for c in cols}
            for month_entry in fi_log:
                mg = month_entry.get("mean_gain", {})
                for c in cols:
                    if c in mg:
                        col_vals[c].append(mg[c])
            # If _per_month_fi_log present but all values still 0 (edge case), warn.
            total_gain = sum(v for vals in col_vals.values() for v in vals)
            if total_gain == 0.0:
                print(
                    f"[_write_feature_importance] WARNING: {name_str} _per_month_fi_log "
                    f"present ({len(fi_log)} months) but all gains are 0.0 — "
                    f"model may have trained with empty feature arrays."
                )
        else:
            # Legacy fallback: read from _models (last walk-forward month only).
            col_vals = {c: [] for c in cols}
            for model in inner._models:
                fi_arr = model.feature_importances_
                if hasattr(model, "booster_"):
                    fi_arr = model.booster_.feature_importance(importance_type="gain")
                for i, c in enumerate(cols):
                    if i < len(fi_arr):
                        col_vals[c].append(float(fi_arr[i]))

        if not any(col_vals.values()):
            continue

        rows: list[dict] = []
        for col in cols:
            vals = col_vals.get(col, [])
            mean_fi = float(np.mean(vals)) if vals else 0.0
            rows.append({"feature_name": col, "mean_gain": round(mean_fi, 4)})
            portfolio[col] += mean_fi

        # Sort descending by mean_gain and add rank
        rows.sort(key=lambda r: r["mean_gain"], reverse=True)
        for rank, row in enumerate(rows, start=1):
            row["importance_rank"] = rank

        out_path = is_dir / f"feature_importance_{name_str}.csv"
        _fi_fields = ["feature_name", "mean_gain", "importance_rank"]
        with open(out_path, "w", newline="") as fh:
            writer = _csv.DictWriter(fh, fieldnames=_fi_fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[run_baseline_v1] Feature importance: {out_path.name} ({len(rows)} features)")

    # Portfolio aggregate CSV
    port_rows = [{"feature_name": c, "mean_gain": round(portfolio[c], 4)} for c in cols]
    port_rows.sort(key=lambda r: r["mean_gain"], reverse=True)
    for rank, row in enumerate(port_rows, start=1):
        row["importance_rank"] = rank
    port_path = is_dir / "feature_importance_portfolio.csv"
    with open(port_path, "w", newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=["feature_name", "mean_gain", "importance_rank"])
        writer.writeheader()
        writer.writerows(port_rows)
    print(f"[run_baseline_v1] Feature importance portfolio: {port_path.name}")


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
    # iter-v1/014: σ_t-scaled barrier labeling flags.
    parser.add_argument(
        "--label-sigma-source",
        choices=["natr", "ewma14d"],
        default="natr",
        help=(
            "Barrier labeling source. 'natr' (default) preserves BIT-IDENTICAL "
            "behaviour to /013. 'ewma14d' activates past-only EWMA σ_t-scaled "
            "barriers at --label-sigma-halflife-days half-life. When 'ewma14d', "
            "R5-BINARY-KILL is auto-disabled for axis isolation."
        ),
    )
    parser.add_argument(
        "--label-sigma-k-tp",
        type=float,
        default=1.06,
        help=(
            "TP barrier multiplier for σ_t-scaled labeling (default 1.06, "
            "calibrated by volume-weighted portfolio-median ATR match per "
            "iter-v1/014 EDA Section 2.3). Only used when --label-sigma-source ewma14d."
        ),
    )
    parser.add_argument(
        "--label-sigma-k-sl",
        type=float,
        default=0.53,
        help=(
            "SL barrier multiplier for σ_t-scaled labeling (default 0.53, "
            "calibrated by volume-weighted portfolio-median ATR match per "
            "iter-v1/014 EDA Section 2.3). Only used when --label-sigma-source ewma14d."
        ),
    )
    parser.add_argument(
        "--label-sigma-halflife-days",
        type=int,
        default=14,
        help=(
            "Half-life in calendar days for EWMA σ_t (default 14 = 42 candles "
            "at 8h interval). Only used when --label-sigma-source ewma14d."
        ),
    )
    parser.add_argument(
        "--no-engineering-report",
        action="store_true",
        default=False,
        help=(
            "Suppress the engineering_report.md existence HARD-STOP (sys.exit(1)). "
            "Use ONLY for mid-pipeline orchestration where the report is created "
            "separately after the runner exits.  (iter-v1/015 — Critic /014 Rec #2)"
        ),
    )
    # iter-v1/016: sample-weighting axis.
    # Controls per-row weight assignment to LightGBM during training.
    # "abs_pnl"         (default) — BIT-IDENTICAL to baseline; uses label_trades abs PnL weights.
    # "uniform"         — replaces with np.ones(n); Kish n_eff = 1.000; selected for /016.
    # "uniqueness_only" — replaces with raw López de Prado uniqueness (NOT multiplied by abs_pnl).
    parser.add_argument(
        "--sample-weight-mode",
        choices=["abs_pnl", "uniform", "uniqueness_only"],
        default="abs_pnl",
        help=(
            "Sample weighting mode for LightGBM training (iter-v1/016). "
            "'abs_pnl' (default) is BIT-IDENTICAL to baseline. "
            "'uniform' passes np.ones(n) — selected for /016. "
            "'uniqueness_only' replaces with raw AFML uniqueness (replaces, not multiplies)."
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

    # iter-v1/016: sample-weighting axis config resolution.
    # Resolve mode from --sample-weight-mode (default "abs_pnl" = BIT-IDENTICAL to baseline).
    # When mode is "uniform" or "uniqueness_only" AND --pruned-features is active,
    # escalate bounds_profile to "v1_pruned_axis016" to additionally pin
    # subsample=1.0 and colsample_bytree=1.0 (LM Master Rec #2 ADOPTED-CONDITIONAL).
    # This ensures only the sample-weighting axis is free in Optuna — no subsampling
    # perturbations can confound F-AXIS-MECHANISM attribution.
    sample_weight_mode_arg = getattr(args, "sample_weight_mode", "abs_pnl")
    if sample_weight_mode_arg != "abs_pnl" and bounds_profile == "v1_pruned":
        bounds_profile = "v1_pruned_axis016"
        print(
            f"[run_baseline_v1] iter-v1/016 axis isolation: sample_weight_mode="
            f"{sample_weight_mode_arg!r} → bounds_profile upgraded to "
            f"'v1_pruned_axis016' (subsample=colsample_bytree=1.0 pinned)"
        )
    # AXIS ISOLATION: when sample_weight_mode != "abs_pnl", disable BOTH R5 axes
    # (proportional vol-target AND binary-kill). /016 tests the sample-weighting
    # axis only; comparison anchor is BASELINE_V1 which has NO R5 enabled.
    # Pattern mirrors /014 σ_t labeling axis isolation fix.
    _disable_r5_for_sample_weighting = sample_weight_mode_arg != "abs_pnl"

    # iter-v1/011: R5 risk config resolution.
    # --r5-binary-kill-enabled flips to binary-kill mode and DISABLES proportional
    # vol-target scaling for axis isolation (per brief Section 3.1 + Section 3.5).
    # iter-v1/017 cycle-3 discipline: BASELINE_V1 anchor (`f8bc12c`) was measured
    # WITHOUT R5 (run_baseline_v1.py at that commit had zero R5 mentions). For
    # axis-isolated comparison vs BASELINE_V1, R5 vol-target defaults OFF in
    # cycle-3+. /010 era reruns must explicitly enable (no flag exposed yet).
    r5_vol_target_enabled = False  # cycle-3+ default — matches BASELINE_V1 anchor
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
    # iter-v1/016 axis isolation: when sample_weight_mode != "abs_pnl", disable BOTH R5
    # axes so the sample-weighting axis is tested against BASELINE_V1 anchor (no R5).
    if _disable_r5_for_sample_weighting:
        if r5_vol_target_enabled:
            print(
                "[run_baseline_v1] AXIS-ISOLATION: sample_weight_mode="
                f"{sample_weight_mode_arg!r} auto-disables R5 vol-target ceiling "
                "(clean single-axis test vs BASELINE_V1)"
            )
            r5_vol_target_enabled = False
        if r5_kill_low_natr_enabled:
            print(
                "[run_baseline_v1] AXIS-ISOLATION: sample_weight_mode="
                f"{sample_weight_mode_arg!r} auto-disables R5-BINARY-KILL"
            )
            r5_kill_low_natr_enabled = False

    # iter-v1/014: σ_t-scaled barrier labeling config resolution.
    # DEFAULT sigma_source="natr" → BIT-IDENTICAL to /013 with no behaviour change.
    # When sigma_source="ewma14d", R5-BINARY-KILL is auto-disabled (axis isolation:
    # /014 tests the labeling axis only, not R5; Section 0.2 + Section 3.4).
    sigma_source_arg = getattr(args, "label_sigma_source", "natr")
    sigma_k_tp_arg: float | None = None
    sigma_k_sl_arg: float | None = None
    sigma_halflife_days_arg = int(getattr(args, "label_sigma_halflife_days", 14))
    if sigma_source_arg == "ewma14d":
        sigma_k_tp_arg = float(getattr(args, "label_sigma_k_tp", 1.06))
        sigma_k_sl_arg = float(getattr(args, "label_sigma_k_sl", 0.53))
        # AXIS ISOLATION: disable BOTH R5 axes (proportional vol-target AND
        # binary-kill) when σ_t labeling is active. /014 tests the labeling
        # axis only; comparison anchor is BASELINE_V1 which has no R5.
        if r5_kill_low_natr_enabled:
            print(
                "[run_baseline_v1] AXIS-ISOLATION: sigma_source=ewma14d auto-disables "
                "R5-BINARY-KILL (Section 0.2 + 3.4 axis isolation rule)"
            )
            r5_kill_low_natr_enabled = False
        if r5_vol_target_enabled:
            print(
                "[run_baseline_v1] AXIS-ISOLATION: sigma_source=ewma14d auto-disables "
                "R5 vol-target ceiling (clean single-axis test vs BASELINE_V1)"
            )
            r5_vol_target_enabled = False
        print(
            f"[run_baseline_v1] σ_t labeling ENABLED: k_tp={sigma_k_tp_arg} "
            f"k_sl={sigma_k_sl_arg} halflife={sigma_halflife_days_arg}d "
            f"({sigma_halflife_days_arg * 3} candles at 8h)"
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
    print(f"  sigma_source: {sigma_source_arg}")
    if sigma_source_arg == "ewma14d":
        print(f"  sigma_k_tp: {sigma_k_tp_arg}  sigma_k_sl: {sigma_k_sl_arg}")
        print(f"  sigma_halflife_days: {sigma_halflife_days_arg}")
    print(f"  sample_weight_mode: {sample_weight_mode_arg}")
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

    # Shared kwargs passed to every run_model call.
    # iter-v1/012: ensemble_seeds_offset threaded through so all 4 models
    # (A pooled, C LINK, D LTC, E DOT) use the SAME inner-seed window.
    # iter-v1/014: sigma_source + sigma_k_tp/sl/halflife threaded through.
    # iter-v1/016: sample_weight_mode threaded through for sample-weighting axis.
    _r5_kwargs = dict(
        r5_vol_target_enabled=r5_vol_target_enabled,
        r5_vol_target_pct=r5_vol_target_pct,
        r5_kill_low_natr_enabled=r5_kill_low_natr_enabled,
        r5_kill_low_natr_min_pct=r5_kill_low_natr_min_pct,
        ensemble_seeds_offset=ensemble_seeds_offset,
        sigma_source=sigma_source_arg,
        sigma_k_tp=sigma_k_tp_arg,
        sigma_k_sl=sigma_k_sl_arg,
        sample_weight_mode=sample_weight_mode_arg,
        sigma_halflife_days=sigma_halflife_days_arg,
    )
    # iter-v1/016: collect F-AXIS-MECHANISM logs from all model runs.
    _all_faxm_logs: list[dict] = []
    # iter-v1/021+: store strategies for post-dispatch _write_feature_importance call.
    # Renamed from _iter021_fi_strategies to _post_dispatch_fi_strategies (iter-v1/022
    # Critic Rec #2 CARRY-FORWARD: refactor literal name to generic). Non-feature-importance
    # iterations leave this empty; the post-dispatch call is a no-op.
    _post_dispatch_fi_strategies: list[tuple[str, object]] = []
    if set(symbols) == set(V1_BASELINE_UNIVERSE) and iteration_label == "v1-023":
        # iter-v1/023: funding-rate z-score feature family (cycle-3 #8/10).
        # Feature-family EXPLORATION: adds funding_rate_zscore_30 + funding_rate_zscore_90
        # to V1_FEATURE_COLUMNS_PRUNED (40 → 42). Full 5-symbol universe; 4 models A/C/D/E.
        # The funding features are in the parquets (regenerated with add_funding_v1_features
        # via the features CLI before backtest). V1_FEATURE_COLUMNS_PRUNED already contains
        # the 2 new columns — no runner-side feature injection needed since lgbm.py reads
        # the feature parquets which now carry the funding columns.
        #
        # Pre-flight assertions (per brief Section 3.3):
        # - funding_rate_zscore_30 + funding_rate_zscore_90 must be in active_feature_columns
        # - Both columns must be present in the feature parquets (verified by LightGbmStrategy
        #   at training time — raises on missing feature_columns)
        assert "funding_rate_zscore_30" in active_feature_columns, (
            "iter-v1/023 pre-flight: funding_rate_zscore_30 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has funding cols."
        )
        assert "funding_rate_zscore_90" in active_feature_columns, (
            "iter-v1/023 pre-flight: funding_rate_zscore_90 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has funding cols."
        )
        pos30 = active_feature_columns.index("funding_rate_zscore_30")
        pos90 = active_feature_columns.index("funding_rate_zscore_90")
        print(
            f"[iter-v1/023] Funding-rate feature family ACTIVE: "
            f"funding_rate_zscore_30@{pos30} "
            f"funding_rate_zscore_90@{pos90} "
            f"/ {len(active_feature_columns)} total features"
        )
        results_a, faxm_a, _strat_a = run_model(
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
        results_c, faxm_c, _strat_c = run_model(
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
        results_d, faxm_d, _strat_d = run_model(
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
        results_e, faxm_e, _strat_e = run_model(
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
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e
        all_results = results_a + results_c + results_d + results_e
        # Aggregate R5 IS/OOS split counters across all four models (iter-v1/010+).
        _r5_model_results = [results_a, results_c, results_d, results_e]
        # Feature importance for all 4 models (F-AXIS-MECHANISM #1 dual gate: rank + gain-share).
        # All 4 models required per LM Master §4 recommendation and Section 4.2.
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK", _strat_c),
            ("Model_D_LTC", _strat_d),
            ("Model_E_DOT", _strat_e),
        ]
    elif set(symbols) == set(V1_ITER024_UNIVERSE) and iteration_label == "v1-024":
        # iter-v1/024: regime-conditional sub-model architecture (cycle-3 #9/10).
        # MODEL-ARCH axis: first multi-model architecture in v1 history.
        # 3 cohorts (Pool A, LINK, LTC) × 2 sub-models + 1 cohort (DOT) × 1 = 7 sub-models.
        # DOT excluded from regime conditioning (8 IS extreme trades — degenerate per LM Master §1).
        #
        # Training-time partition:
        #   Each sub-model receives a data_filter_callback that selects only its regime
        #   rows from the training window.  The callback reads funding_rate_zscore_30
        #   from the master DataFrame (already past-only via .shift(1) in feature pipeline).
        #
        # Inference-time dispatch:
        #   RegimeRoutedStrategy wrapper calls both sub-strategies' get_signal(),
        #   then dispatches based on past-only z30 from the feature cache.
        #
        # Feature columns: V1_FEATURE_COLUMNS_PRUNED 42 cols (funding cols included).
        # Risk gates: UNCHANGED from /023 baseline (R1/R2/R3 per cohort).

        # Pre-flight: funding columns must be in active_feature_columns.
        assert V1_ITER024_Z30_COLUMN in active_feature_columns, (
            f"iter-v1/024 pre-flight: {V1_ITER024_Z30_COLUMN} not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has funding cols."
        )
        assert "funding_rate_zscore_90" in active_feature_columns, (
            "iter-v1/024 pre-flight: funding_rate_zscore_90 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has funding cols."
        )
        print(
            f"[iter-v1/024] Regime-conditional dispatch ACTIVE: "
            f"{V1_ITER024_Z30_COLUMN} threshold=|{V1_ITER024_REGIME_THRESHOLD}|; "
            f"7 sub-models (Pool A ×2 + LINK ×2 + LTC ×2 + DOT ×1)"
        )

        # Build shared regime gate config
        _regime_config = RegimeGateConfig(
            threshold=V1_ITER024_REGIME_THRESHOLD,
            z30_column=V1_ITER024_Z30_COLUMN,
            enabled=True,
        )
        _extreme_filter = make_extreme_filter(V1_ITER024_Z30_COLUMN, V1_ITER024_REGIME_THRESHOLD)
        _normal_filter = make_normal_filter(V1_ITER024_Z30_COLUMN, V1_ITER024_REGIME_THRESHOLD)

        # ----------------------------------------------------------------
        # Model A — Pool BTC+ETH: 2 sub-models via RegimeRoutedStrategy
        # FIXED (BLOCK-PENDING-FIX): build inner strategies WITHOUT running
        # run_backtest on them individually; wrap in RegimeRoutedStrategy;
        # call run_backtest ONCE on the wrapper so get_signal() IS reached.
        # ----------------------------------------------------------------
        _strat_a_ext = build_lgbm_strategy(
            atr_tp=2.9,
            atr_sl=1.45,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_A_extreme",
            symbol="BTC+ETH",
            data_filter_callback=_extreme_filter,
            **_r5_kwargs,
        )
        _strat_a_norm = build_lgbm_strategy(
            atr_tp=2.9,
            atr_sl=1.45,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_A_normal",
            symbol="BTC+ETH",
            data_filter_callback=_normal_filter,
            **_r5_kwargs,
        )
        _cfg_a = build_backtest_config(
            ("BTCUSDT", "ETHUSDT"),
            apply_r1=False,
            apply_r2=False,
            **{
                k: v
                for k, v in _r5_kwargs.items()
                if k
                in (
                    "r5_vol_target_enabled",
                    "r5_vol_target_pct",
                    "r5_kill_low_natr_enabled",
                    "r5_kill_low_natr_min_pct",
                )
            },
        )
        results_a, faxm_a, _strat_a_regime = run_regime_cohort(
            "Model_A_regime (BTC/ETH regime-routed)",
            _strat_a_ext,
            _strat_a_norm,
            _cfg_a,
            _regime_config,
            cohort_name="Pool_A",
        )

        # ----------------------------------------------------------------
        # Model C — LINK: 2 sub-models via RegimeRoutedStrategy
        # ----------------------------------------------------------------
        _strat_c_ext = build_lgbm_strategy(
            atr_tp=3.5,
            atr_sl=1.75,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_C_extreme",
            symbol="LINKUSDT",
            data_filter_callback=_extreme_filter,
            **_r5_kwargs,
        )
        _strat_c_norm = build_lgbm_strategy(
            atr_tp=3.5,
            atr_sl=1.75,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_C_normal",
            symbol="LINKUSDT",
            data_filter_callback=_normal_filter,
            **_r5_kwargs,
        )
        _cfg_c = build_backtest_config(
            ("LINKUSDT",),
            apply_r1=True,
            apply_r2=False,
            **{
                k: v
                for k, v in _r5_kwargs.items()
                if k
                in (
                    "r5_vol_target_enabled",
                    "r5_vol_target_pct",
                    "r5_kill_low_natr_enabled",
                    "r5_kill_low_natr_min_pct",
                )
            },
        )
        results_c, faxm_c, _strat_c_regime = run_regime_cohort(
            "Model_C_regime (LINK regime-routed)",
            _strat_c_ext,
            _strat_c_norm,
            _cfg_c,
            _regime_config,
            cohort_name="Model_C_LINK",
        )

        # ----------------------------------------------------------------
        # Model D — LTC: 2 sub-models via RegimeRoutedStrategy
        # ----------------------------------------------------------------
        _strat_d_ext = build_lgbm_strategy(
            atr_tp=3.5,
            atr_sl=1.75,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_D_extreme",
            symbol="LTCUSDT",
            data_filter_callback=_extreme_filter,
            **_r5_kwargs,
        )
        _strat_d_norm = build_lgbm_strategy(
            atr_tp=3.5,
            atr_sl=1.75,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="Model_D_normal",
            symbol="LTCUSDT",
            data_filter_callback=_normal_filter,
            **_r5_kwargs,
        )
        _cfg_d = build_backtest_config(
            ("LTCUSDT",),
            apply_r1=True,
            apply_r2=False,
            **{
                k: v
                for k, v in _r5_kwargs.items()
                if k
                in (
                    "r5_vol_target_enabled",
                    "r5_vol_target_pct",
                    "r5_kill_low_natr_enabled",
                    "r5_kill_low_natr_min_pct",
                )
            },
        )
        results_d, faxm_d, _strat_d_regime = run_regime_cohort(
            "Model_D_regime (LTC regime-routed)",
            _strat_d_ext,
            _strat_d_norm,
            _cfg_d,
            _regime_config,
            cohort_name="Model_D_LTC",
        )

        # ----------------------------------------------------------------
        # Model E — DOT: BASELINE single-model (DOT excluded from regime routing)
        # Per LM Master §1: 8 IS extreme trades — degenerate; direction reversed.
        # DOT path unchanged — uses run_model() directly (no regime wrapper).
        # ----------------------------------------------------------------
        results_e, faxm_e, _strat_e = run_model(
            "Model_E_baseline (DOT baseline)",
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
            model_role="Model_E_baseline",
            symbol="DOTUSDT",
            # NO data_filter_callback — DOT uses full training set (baseline)
            **_r5_kwargs,
        )

        # ----------------------------------------------------------------
        # Merge results: 3 regime-wrapped cohorts + DOT baseline.
        # results_a/c/d are BacktestResults from run_regime_cohort() —
        # each produced by a SINGLE run_backtest(wrapper) call.
        # ----------------------------------------------------------------
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e
        all_results = results_a + results_c + results_d + results_e
        _r5_model_results = [results_a, results_c, results_d, results_e]
        # Feature importance: inner sub-strategies (for gain-share recurrence check).
        # Post-dispatch FI collection from inner LightGbmStrategy instances, not wrappers,
        # because _write_feature_importance needs _models / _selected_cols attributes.
        _post_dispatch_fi_strategies = [
            ("Model_A_extreme", _strat_a_ext),
            ("Model_A_normal", _strat_a_norm),
            ("Model_C_extreme", _strat_c_ext),
            ("Model_C_normal", _strat_c_norm),
            ("Model_D_extreme", _strat_d_ext),
            ("Model_D_normal", _strat_d_norm),
            ("Model_E_baseline", _strat_e),
        ]
        # Expose regime wrappers for gate stats (engineering report).
        _iter024_regime_wrappers = {
            "Pool_A": _strat_a_regime,
            "Model_C_LINK": _strat_c_regime,
            "Model_D_LTC": _strat_d_regime,
        }
    elif set(symbols) == set(V1_BASELINE_UNIVERSE) and iteration_label not in (
        "v1-021",
        "v1-023",
        "v1-024",
    ):
        # Generic baseline-universe dispatch (non-/021, non-/023, non-/024 iterations).
        # Models A/C/D/E with V1_BASELINE_UNIVERSE symbols. BIT-IDENTICAL to historical
        # v186 baseline when active_feature_columns=list(V1_FEATURE_COLUMNS) + n_trials=50.
        results_a, faxm_a, _strat_a = run_model(
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
        results_c, faxm_c, _strat_c = run_model(
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
        results_d, faxm_d, _strat_d = run_model(
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
        results_e, faxm_e, _strat_e = run_model(
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
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e
        all_results = results_a + results_c + results_d + results_e
        # Aggregate R5 IS/OOS split counters across all four models (iter-v1/010+).
        _r5_model_results = [results_a, results_c, results_d, results_e]
    elif set(symbols) == set(V1_ITER017_UNIVERSE):
        # iter-v1/017: 6-symbol universe expansion (cycle-3 #2).
        # Models A/C/D/E are BIT-IDENTICAL to baseline dispatch above.
        # NEW Model F (SOL): atr=2.9/1.45 (Model A profile), R3-only (no R1/R2),
        # bounds_profile=v1_pruned (same as A/C/D/E), single-symbol isolated.
        results_a, faxm_a, _strat_a = run_model(
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
        results_c, faxm_c, _strat_c = run_model(
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
        results_d, faxm_d, _strat_d = run_model(
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
        results_e, faxm_e, _strat_e = run_model(
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
        # Model F — SOL: single-symbol, R3-only (sister to Model A), ATR 2.9/1.45.
        results_f, faxm_f, _strat_f = run_model(
            "F (SOL)",
            ("SOLUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            apply_r2=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e + faxm_f
        all_results = results_a + results_c + results_d + results_e + results_f
        # Aggregate R5 IS/OOS split counters across all five models.
        _r5_model_results = [results_a, results_c, results_d, results_e, results_f]
    elif set(symbols) == set(V1_ITER018_UNIVERSE):
        # iter-v1/018: LINK-only single-cohort EXPLORATION (cycle-3 #3 of 10).
        # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
        # ONLY Model C (LINK + R1 + R3) dispatched.
        # Models A (BTC+ETH), D (LTC), E (DOT) DROPPED — single-axis isolation.
        # All Model C parameters are BIT-IDENTICAL to the baseline dispatch above:
        #   atr_tp=3.5, atr_sl=1.75, apply_r1=True, bounds_profile=v1_pruned.
        # Single-axis isolation: ONLY the SYMBOL DIMENSION changes (5→1 symbol).
        # Zero changes to features, labeling, risk gates, or Optuna bounds.
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY LINKUSDT rows.
        results_c, faxm_c, _strat_c = run_model(
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
        _all_faxm_logs = faxm_c
        all_results = results_c
        # Single model — no aggregation across multiple models needed.
        _r5_model_results = [results_c]
    elif set(symbols) == set(V1_ITER019_UNIVERSE):
        # iter-v1/019: ETH-only single-cohort EXPLORATION + stateless BTC-trend gate
        # (cycle-3 #4 of 10; per-cohort-specialization-ETH; NEW 10th axis family).
        # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
        #
        # Dispatch — ONLY Model G (ETH-only; mirrors Model A's apply_r1=False semantics;
        # ATR 2.9/1.45 matches Model A which trained ETH in pool).
        # Models A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) DROPPED.
        # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym) + post-hoc gate.
        #
        # The BTC-trend gate is a STATELESS post-hoc trade-stream filter applied AFTER
        # the model produces its trade roster. Deadlock-impossible by construction
        # (numpy boolean mask; no persistent state). Brief Section 6.5 proof.
        #
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY ETHUSDT rows.
        # F-AXIS-MECHANISM #2: ETH IS [80,200] / OOS [25,90] trade band.
        # F-AXIS-MECHANISM #3: gate fire rate IS [10%,30%] / OOS [5%,35%] LOAD-BEARING.
        assert set(symbols) == {"ETHUSDT"}, (
            f"iter-v1/019 guard: expected {{ETHUSDT}}, got {set(symbols)}"
        )
        results_g, faxm_g, _strat_g = run_model(
            "G (ETH-only + R3 + BTC-trend gate)",
            ("ETHUSDT",),
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
        # Apply stateless direction-aware BTC-trend gate as post-hoc trade-stream filter.
        # Gate kills counter-trend ETH trades: ETH long when BTC ret14 < -8%, or
        # ETH short when BTC ret14 > +8%. IS EDA: +42.47% PnL lift, cross-year stable.
        # load_btc_klines_for_filter() reads data/BTCUSDT/8h.csv (must be fresh
        # per Section 10.3 pre-flight check: close_time within 16h of measurement time).
        btc_open_times, btc_closes = load_btc_klines_for_filter()
        gate_cfg = BtcTrendFilterConfig(
            lookback_bars=V1_ITER019_BTC_GATE_LOOKBACK_BARS,
            threshold_pct=V1_ITER019_BTC_GATE_THRESHOLD_PCT,
            enabled=V1_ITER019_BTC_GATE_ENABLED,
        )
        results_g, gate_stats = apply_btc_trend_filter(
            results_g,
            btc_open_times,
            btc_closes,
            gate_cfg,
        )
        gate_stats_dict = gate_stats.as_dict()
        print(
            f"[iter-v1/019 BTC-trend gate] "
            f"normal={gate_stats_dict['n_normal']} "
            f"warmup={gate_stats_dict['n_warmup']} "
            f"killed={gate_stats_dict['n_killed']}/{gate_stats_dict['n_total']} "
            f"fire_rate={gate_stats_dict['fire_rate']:.2%}"
        )
        _all_faxm_logs = faxm_g
        all_results = results_g
        _r5_model_results = [results_g]
    elif set(symbols) == set(V1_ITER020_UNIVERSE):
        # iter-v1/020: BTC-only single-cohort EXPLORATION (cycle-3 #5 of 10).
        # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
        #
        # Dispatch — ONLY Model H (BTC-only; mirrors Model A's apply_r1=False
        # apply_r2=False semantics; ATR 2.9/1.45 matches Model A which trained
        # BTC in pool).
        # Models A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) DROPPED.
        # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym).
        # NO gate, NO new feature, NO new labeling — pure cohort isolation.
        #
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY BTCUSDT rows.
        # F-AXIS-MECHANISM #2: BTC IS [70,150] / OOS [25,55] trade band.
        # F-AXIS-MECHANISM #3 (load-bearing per /019 Critic Rec #2 at |IS Sharpe| ≈ 0.12):
        #   IS_H1 net_pnl preserved catastrophic per regime-binding hypothesis;
        #   pre-registered band [−45%, −15%] (Section 4 F-AXIS #3).
        assert set(symbols) == {"BTCUSDT"}, (
            f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
        )
        results_h, faxm_h, _strat_h = run_model(
            "H (BTC-only + R3)",
            ("BTCUSDT",),
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
        _all_faxm_logs = faxm_h
        all_results = results_h
        _r5_model_results = [results_h]
    elif set(symbols) == set(V1_ITER021_UNIVERSE) and iteration_label == "v1-021":
        # iter-v1/021: METHODOLOGY PIVOT diagnostic.
        # Dispatches TWO models side-by-side at n_trials=18 seed=42:
        #   - Model A pool (BTC+ETH, 5-sym universe, BASELINE config) for Layer B determinism
        #     AND feature importance baseline.
        #   - Model H (BTC-only, same config as /020) for pool-anchor H1 diagnostic.
        # Models C (LINK), D (LTC), E (DOT) are NOT dispatched (not relevant to H1/H2).
        # params_persist_path is SET for BOTH models so H1 parquet is populated.
        #
        # NOTE: The full 5-sym universe is passed as the `symbols` argument to this
        # branch but Model A only trains on BTC+ETH (same as baseline) and Model H
        # only trains on BTC. The universe constant V1_ITER021_UNIVERSE matches
        # V1_BASELINE_UNIVERSE — the iteration_label guard above disambiguates.
        assert set(symbols) == set(V1_ITER021_UNIVERSE), (
            f"iter-v1/021 guard: expected {{BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT}}, "
            f"got {set(symbols)}"
        )

        # Override PARAMS_PARQUET_PATH to the iteration-stamped path
        global PARAMS_PARQUET_PATH  # noqa: PLW0603
        PARAMS_PARQUET_PATH = Path("data") / f"v1_iter_{iteration_label}_optuna_best_params.parquet"
        # Clear stale params parquet (same pattern as OOF_PARQUET_PATH)
        PARAMS_PARQUET_PATH.unlink(missing_ok=True)
        print(f"[iter-v1/021] PARAMS_PARQUET_PATH: {PARAMS_PARQUET_PATH}")

        # Model A pool (BTC+ETH, BASELINE config, n_trials=35 for Layer B bit-identity)
        # Brief Layer B: pool config at n_trials=35 MUST produce bit-identical comparison.csv
        # to v0.v1-baseline-corrected — adding params_persist_path MUST be a no-op.
        _n_trials_pool = 35  # Layer B: match baseline n_trials exactly
        print(
            f"[iter-v1/021] Model A pool: n_trials={_n_trials_pool} seed=42 "
            f"(Layer B determinism — must match v0.v1-baseline-corrected)"
        )
        results_a, faxm_a, _strat_a = run_model(
            "A (BTC/ETH pool — /021 Layer B)",
            ("BTCUSDT", "ETHUSDT"),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=_n_trials_pool,
            ensemble_size=1,  # single seed=42 only (diagnostic; matches /020)
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            params_persist_path=PARAMS_PARQUET_PATH,
            model_role="Model_A_pool",
            symbol="BTC+ETH",
            **_r5_kwargs,
        )

        # Model H (BTC-only, n_trials=18 seed=42 — matches /020 canonical budget)
        print(
            "[iter-v1/021] Model H BTC-only: n_trials=18 seed=42 "
            "(H1 diagnostic — matches /020 canonical budget)"
        )
        results_h, faxm_h, _strat_h = run_model(
            "H (BTC-only — /021 H1 diagnostic)",
            ("BTCUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=18,  # matches /020; H1 falsifier requires SAME budget as /020
            ensemble_size=1,  # single seed=42 only (diagnostic)
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            params_persist_path=PARAMS_PARQUET_PATH,
            model_role="Model_H_BTC",
            symbol="BTCUSDT",
            **_r5_kwargs,
        )

        # For the diagnostic, the trade results are the POOL results only
        # (Model H BTC-only is a separate diagnostic model; combining with pool
        # would double-count BTC trades). Layer B determinism is verified by
        # comparing Model A pool's comparison.csv to v0.v1-baseline-corrected.
        _all_faxm_logs = faxm_a + faxm_h
        all_results = results_a  # Pool results only for official reports
        _r5_model_results = [results_a]

        # Feature importance is written AFTER report_dir is resolved (post-dispatch).
        # Store strategies reference for the post-dispatch call.
        _post_dispatch_fi_strategies = [
            ("POOL_Model_A", _strat_a),
            ("BTC_Model_H", _strat_h),
        ]
        print(
            f"[iter-v1/021] params parquet: {PARAMS_PARQUET_PATH} "
            f"(Layer A: expect ≥48 rows after run — 24 pool + 24 BTC-only)"
        )
        # Verify Layer A row count after backtest.
        # Corrected arithmetic (Critic Phase 6.0 BLOCKER B):
        #   Model A pool: _train_for_month calls optimize_and_train ONCE per walk-forward month
        #     on COMBINED BTC+ETH data — NOT per-symbol. symbol field = "BTC+ETH" literal.
        #     24 train_months × 1 call = 24 rows.
        #   Model H BTC-only: same pattern. 24 train_months × 1 call = 24 rows.
        #   Total = 48 rows (NOT 168; the 168 assumed per-symbol breakdown which pool does not do).
        if PARAMS_PARQUET_PATH.exists():
            _params_df = pd.read_parquet(PARAMS_PARQUET_PATH)
            print(
                f"[iter-v1/021] Layer A audit: {len(_params_df)} rows in params parquet "
                f"(≥48 required; PASS={len(_params_df) >= 48})"
            )
            _missing = _params_df.isnull().any()
            _missing_cols = [c for c, v in _missing.items() if v and c not in ("training_days",)]
            if _missing_cols:
                print(
                    f"[iter-v1/021] Layer C WARNING: NULL values in {_missing_cols} "
                    "— H1 falsifier is partially blind",
                    file=sys.stderr,
                )
            else:
                print("[iter-v1/021] Layer C audit: all mandatory param columns non-null. PASS")
        else:
            print(
                "[iter-v1/021] Layer A WARNING: params parquet NOT FOUND after run",
                file=sys.stderr,
            )
    elif set(symbols) == set(V1_ITER022_UNIVERSE):
        # iter-v1/022: LTC-only single-cohort EXPLORATION + stateless long-suppression
        # BTC-trend gate (cycle-3 #7 of 10; per-cohort-specialization-LTC; NEW 14th family).
        # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
        #
        # Dispatch — ONLY Model D' (LTC-only; mirrors Model D semantics with apply_r1=True
        # which baseline Model D uses; ATR 3.5/1.75 matches Model D's per-symbol config).
        # Models A (BTC+ETH pooled), C (LINK), D (LTC pooled), E (DOT) DROPPED.
        # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym) + post-hoc
        # direction-asymmetric BTC-trend gate as the specialization.
        # The gate is STATELESS post-hoc trade-stream filter (no model retrain; mirrors
        # /019 BtcTrendFilterConfig pattern but asymmetric long_only_mode=True).
        #
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY LTCUSDT rows.
        # F-AXIS-MECHANISM #2: LTC IS [80, 180] / OOS [20, 60] trade band.
        # F-AXIS-MECHANISM #3 (LOAD-BEARING per LM Master /022 §4+§8): gate fire rate
        #   IS in [15%, 40%] / OOS in [5%, 30%]. OOS < 5% → NEGATIVE-UNDER-FIRE.
        assert set(symbols) == {"LTCUSDT"}, (
            f"iter-v1/022 guard: expected {{LTCUSDT}}, got {set(symbols)}"
        )
        results_dprime, faxm_dprime, _strat_dprime = run_model(
            "D' (LTC-only + R1 + R3 + BTC-trend long-suppress gate)",
            ("LTCUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,  # NOTE: baseline Model D has R1; preserved for LTC cohort
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        # Apply stateless long-suppression BTC-trend gate as post-hoc filter.
        # ASYMMETRIC: kills only LTC longs (direction=+1) when BTC ret_42 < -4%;
        # LTC shorts UNRESTRICTED (long_only_mode=True).
        btc_open_times, btc_closes = load_btc_klines_for_filter()
        gate_cfg = BtcTrendFilterConfig(
            lookback_bars=V1_ITER022_BTC_GATE_LOOKBACK_BARS,
            threshold_pct=V1_ITER022_BTC_GATE_THRESHOLD_PCT,
            enabled=V1_ITER022_BTC_GATE_ENABLED,
            long_only_mode=V1_ITER022_BTC_GATE_LONG_ONLY,
        )
        results_dprime, gate_stats = apply_btc_trend_filter(
            results_dprime,
            btc_open_times,
            btc_closes,
            gate_cfg,
        )
        gate_stats_dict = gate_stats.as_dict()
        print(
            f"[iter-v1/022 BTC-trend long-suppress gate] "
            f"normal={gate_stats_dict['n_normal']} "
            f"warmup={gate_stats_dict['n_warmup']} "
            f"killed={gate_stats_dict['n_killed']}/{gate_stats_dict['n_total']} "
            f"fire_rate={gate_stats_dict['fire_rate']:.2%} "
            f"long_only={V1_ITER022_BTC_GATE_LONG_ONLY}"
        )
        _all_faxm_logs = faxm_dprime
        all_results = results_dprime
        _r5_model_results = [results_dprime]
    else:
        # Custom universe — single pooled model unless brief specifies otherwise.
        # iter-v1/NNN brief Section 3 should declare per-symbol model assignment.
        _pooled, faxm_pooled, _strat_pooled = run_model(
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
        _all_faxm_logs = faxm_pooled
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
    # iter-v1/021+: write feature importance CSVs (post-dispatch).
    # _post_dispatch_fi_strategies is populated when iteration_label is one of:
    #   "v1-021" (methodology pivot — H1/H2 diagnostic)
    #   "v1-023" (funding-rate feature family — F-AXIS-MECHANISM #1 dual gate)
    #   "v1-024" (regime-conditional sub-models — 7 sub-models × gain-share recurrence)
    # For all other iterations, this is a no-op (empty list).
    # Renamed from _iter021_fi_strategies → _post_dispatch_fi_strategies
    # (iter-v1/022 Critic Rec #2 CARRY-FORWARD: generic name per /022 review.md).
    # -------------------------------------------------------------------------
    if _post_dispatch_fi_strategies:
        _write_feature_importance(
            _post_dispatch_fi_strategies,
            feature_columns=active_feature_columns,
            report_dir=report_dir,
        )

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

    # iter-v1/016: write f_axis_mechanism.csv for F-AXIS-MECHANISM falsifier.
    # Only emits when sample_weight_mode != "abs_pnl" (active axis run) AND
    # _all_faxm_logs is non-empty. Safe no-op for baseline and all other iterations.
    if _all_faxm_logs:
        import csv as _csv  # noqa: PLC0415

        faxm_path = report_dir / "f_axis_mechanism.csv"
        all_keys: list[str] = []
        for _row in _all_faxm_logs:
            for _k in _row:
                if _k not in all_keys:
                    all_keys.append(_k)
        with faxm_path.open("w", newline="") as _fh:
            writer = _csv.DictWriter(_fh, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            for _row in _all_faxm_logs:
                writer.writerow(_row)
        print(f"[run_baseline_v1] F-AXIS-MECHANISM log: {len(_all_faxm_logs)} cells → {faxm_path}")
        # Emit summary stats for F-AXIS-MECHANISM falsifier checks.
        if _all_faxm_logs:
            _kish_ratios = [r["kish_ratio"] for r in _all_faxm_logs if "kish_ratio" in r]
            _timeout_shares = [
                r["timeout_fallback_share"] for r in _all_faxm_logs if "timeout_fallback_share" in r
            ]
            if _kish_ratios:
                print(
                    f"  Kish ratio: mean={sum(_kish_ratios) / len(_kish_ratios):.4f} "
                    f"min={min(_kish_ratios):.4f} max={max(_kish_ratios):.4f}"
                )
            if _timeout_shares:
                print(
                    f"  Timeout share: mean={sum(_timeout_shares) / len(_timeout_shares):.4f} "
                    f"max={max(_timeout_shares):.4f}"
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

    # iter-v1/015: engineering_report.md HARD-STOP (Critic /014 Rec #2 4th-strike).
    # sys.exit(1) instead of WARNING — Phase 7.5 dispatch is BLOCKED without the report.
    # Use --no-engineering-report to opt out explicitly (mid-pipeline orchestration only).
    engineering_report_path = report_dir / "engineering_report.md"
    if not engineering_report_path.exists() and not args.no_engineering_report:
        print(
            f"\n[FATAL] engineering_report.md NOT FOUND at {engineering_report_path}",
            file=sys.stderr,
        )
        print(
            "[FATAL] This file is a BLOCKING deliverable for Phase 7.5 dispatch.\n"
            "[FATAL] Use --no-engineering-report to suppress this exit "
            "(e.g. mid-pipeline orchestration).",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
