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
    V1_ITER028_UNIVERSE,
    V1_ITER029_UNIVERSE,
    V1_ITER036_UNIVERSE,
    V1_OOD_FEATURE_COLUMNS,
    assert_v1_universe,
)
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.basin_diagnostics import (
    derive_basin_trials_from_oof_parquet,
    emit_basin_diagnostics_summary,
)
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy
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

#: iter-v1/025: OI delta feature-family EXPLORATION (cycle-3 #10/10 — LAST EXPLORATION).
#: Single feature addition: oi_delta_30_z90 (open-interest 30-bar delta, 90-bar z-score).
#: V1_FEATURE_COLUMNS_PRUNED 42 → 43. Full 5-symbol V1_BASELINE_UNIVERSE.
#: Dispatch: analogue of /023 funding-family dispatch. No model-arch change.
#: HARD BLOCK: ≥3/5 symbols must have ≥1000 IS rows in data/open_interest/<SYM>/8h.csv.
V1_ITER025_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)
V1_ITER025_OI_DELTA_COLUMN: str = "oi_delta_30_z90"
V1_ITER025_OI_MIN_IS_ROWS: int = 1000  # HARD BLOCK threshold per LM Master §4
V1_ITER025_OI_MIN_COVERED: int = 3  # ≥3/5 symbols must clear the HARD BLOCK

#: iter-v1/027: CYCLE-3 CONFIRMATION METHODOLOGY VALIDATION.
#: 5-Model replacement bundle: Pool A (BTC+ETH baseline pool training) + Model C'
#: (LINK specialist /018) + Model D (LTC baseline) + Model E (DOT baseline) +
#: Model G (ETH+gate specialist /019 with asymmetric long-suppress BTC-trend gate).
#:
#: REPLACEMENT SEMANTICS: at trade aggregation, drop Model A's ETH trades and
#: keep ONLY Model G's ETH trades. Model C' is LINK-only by construction.
#: Effective per-cohort dispatch: BTC <- Model A pool, ETH <- Model G specialist,
#: LINK <- Model C' specialist, LTC <- Model D, DOT <- Model E.
#:
#: BASELINE-FROZEN: 40-col feature set (V1_FEATURE_COLUMNS_PRUNED 43 MINUS
#: funding_rate_zscore_30, funding_rate_zscore_90, oi_delta_30_z90 per /023+/025
#: NEGATIVE verdicts). Brief §3.3: "NOT 42, NOT 43; OI and funding EXCLUDED".
#:
#: NO-MERGE pre-committed. BASELINE_V1.md UNCHANGED regardless of /027 outcome.
#: LOCAL to runner — NOT shared via features_v1/__init__.py.
V1_ITER027_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

#: ETH+gate specialist constants — BIT-IDENTICAL to /019 config.
V1_ITER027_ETH_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h cadence
V1_ITER027_ETH_GATE_THRESHOLD_PCT: float = 8.0  # +-8% BTC 14d return
V1_ITER027_ETH_GATE_ENABLED: bool = True
V1_ITER027_ETH_GATE_LONG_ONLY: bool = False  # symmetric direction-aware (/019 mode)

#: Funding+OI columns excluded from /027 substrate (NEGATIVE verdicts at /023+/025).
_V1_ITER027_EXCLUDED_COLS: frozenset[str] = frozenset(
    {
        "funding_rate_zscore_30",
        "funding_rate_zscore_90",
        "oi_delta_30_z90",
    }
)

#: iter-v1/029: DOT-only E-specialist + symmetric BTC-trend gate ±8% (mirror /019).
#: Cycle-4 EXPLORATION #2/10. Axis family: per-cohort-specialization-DOT-v2 (NEW 16th).
#: Path C per LM Master §4 BINDING recommendation. NORMAL-RISK (post-Optuna gate only).
#: Gate spec: lookback_bars=42 (14 days at 8h), threshold_pct=8.0 (±8% BTC 14d return),
#:   enabled=True, long_only_mode=False (symmetric — mirrors /019 exactly).
#: Model E semantics: R1=ON, R2=OFF, R3=ON, atr_tp=3.5, atr_sl=1.75 (FROZEN).
#: ENSEMBLE_SIZE=10, n_trials=35, single-seed=42 (EXPLORATION; ~30-45 min wall-clock).
V1_ITER029_BTC_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h cadence (mirror /019)
V1_ITER029_BTC_GATE_THRESHOLD_PCT: float = 8.0  # +-8% BTC 14d return (mirror /019)
V1_ITER029_BTC_GATE_ENABLED: bool = True

#: iter-v1/030: 3-separate M2 meta-labeling layer on top of M1 baseline dispatch.
#: Axis family: meta-labeling (NEW NINTH family; UNUSED in v1 across cycles 1-3).
#: Cycle-4 EXPLORATION #3/10. Anchor: BASELINE_V1.md v0.v1-baseline-corrected.
#:
#: Architecture:
#:   - Models A/C/D each get a per-model M2 binary LGBMClassifier.
#:   - Model E (DOT) is EXCLUDED per LM Master §3 sample-size binding call
#:     (75 cumulative M1-positives < LightGBM threshold for 45-feature × n_trials=18).
#:   - M2 input: 43 V1_FEATURE_COLUMNS_PRUNED + m1_confidence + m1_direction = 45 dims.
#:   - M2 threshold: 0.5 PINNED (single-axis discipline).
#:   - n_trials_m2: 18 (LM Master §2.3 ADOPTED; TPE warmup ≥15 trials required).
#:   - bounds_profile_m2: "v1_030" (LM Master §2 tightened bounds).
#:   - scale_pos_weight = n_neg/n_pos explicit per cell (NOT is_unbalance=True).
#:
#: F-AXIS-MECHANISM (pre-registered, verdict-capping):
#:   F-AXIS #1: M2-trained cells ≥ 80 of 159 expected (53 months × 3 models A/C/D)
#:   F-AXIS #2: OOS trades ∈ [95, 165] modal 130; OOS < 90 → NEG-OVER cap
#:   F-AXIS #3: M2-pass OOS WR ≥ 48% (LOAD-BEARING; verdict-positive determinant)
#:   F-AXIS #5: OOS TP-exit ≥ 15; Model D OOS TP ≥ 3 (LOAD-BEARING; LTC-long veto)
#:
V1_ITER030_N_TRIALS_M2: int = 18  # LM Master §2.3 ADOPTED
V1_ITER030_BOUNDS_PROFILE_M2: str = "v1_030"  # LM Master §2 tightened bounds
V1_ITER030_M2_THRESHOLD: float = 0.5  # PINNED (single-axis discipline; not tuned)
V1_ITER030_M2_CELLS_EXPECTED: int = 159  # 53 months × 3 models (A/C/D; E EXCLUDED)
V1_ITER030_M2_CELLS_MIN: int = 80  # F-AXIS #1 threshold (≥50% of expected)
V1_ITER030_OOS_TRADES_FLOOR: int = 90  # F-AXIS #2 critical threshold (OOS < 90 → NEG-OVER cap)
V1_ITER030_OOS_TP_FLOOR: int = 15  # F-AXIS #5 overall OOS TP-exit floor
V1_ITER030_MODEL_D_OOS_TP_FLOOR: int = 3  # F-AXIS #5 Model D LOAD-BEARING floor

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
    label_mode: str = "triple_barrier",
    params_persist_path: Path | None = None,
    model_role: str = "",
    symbol: str = "",
    data_filter_callback: Callable[[pd.DataFrame], np.ndarray] | None = None,
    nan_skip_columns: list[str] | None = None,
    nan_skip_threshold: float = 0.5,
    frozen_hp_parquet: Path | None = None,
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
        label_mode=label_mode,
        params_persist_path=params_persist_path,
        model_role=model_role,
        symbol=symbol,
        data_filter_callback=data_filter_callback,
        nan_skip_columns=nan_skip_columns,
        nan_skip_threshold=nan_skip_threshold,
        frozen_hp_parquet=frozen_hp_parquet,
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    # iter-v1/016: expose F-AXIS-MECHANISM log so the runner can write f_axis_mechanism.csv.
    # iter-v1/021: also return the strategy object for _write_feature_importance access.
    return results, strategy._faxm_log, strategy


def run_meta_model(
    name: str,
    symbols: tuple[str, ...],
    atr_tp: float,
    atr_sl: float,
    *,
    apply_r1: bool,
    apply_r2: bool = False,
    n_trials: int,
    ensemble_size: int,
    n_trials_m2: int = V1_ITER030_N_TRIALS_M2,
    bounds_profile_m2: str = V1_ITER030_BOUNDS_PROFILE_M2,
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
):
    """Run a single v1 sub-model with M2 meta-labeling (iter-v1/030).

    Mirrors run_model() but creates MetaLabelingStrategy instead of
    LightGbmStrategy.  M2 is a binary LGBMClassifier trained on M1-positive
    bars per training window; it vetoes M1 signals where M2 confidence < 0.5.

    M2 input: feature_columns (43 V1_FEATURE_COLUMNS_PRUNED) + m1_confidence
    + m1_direction = 45-dim (include_m1_direction=True, per brief §3.3).

    Model E (DOT) MUST NOT be dispatched through this function — use run_model()
    directly for DOT (sample-size floor mandate, LM Master §3).

    Returns (results, faxm_log, strategy) same as run_model().
    """
    effective_feature_columns = (
        feature_columns if feature_columns is not None else list(V1_FEATURE_COLUMNS)
    )
    sigma_halflife_candles = sigma_halflife_days * 3  # 3 candles per day at 8h
    print("=" * 60)
    print(
        f"MODEL {name} [M2-META]: {', '.join(symbols)} "
        f"(R1={apply_r1} R2={apply_r2} R3=on, n_trials={n_trials}, "
        f"n_trials_m2={n_trials_m2}, bounds_m2={bounds_profile_m2}, "
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
    strategy = MetaLabelingStrategy(
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
        atr_column="vol_natr_21",  # v1 parquet schema (v3 default is natr_21_raw)
        use_atr_labeling=True,
        ensemble_seeds=_derive_ensemble_seeds(ensemble_size, offset=ensemble_seeds_offset),
        feature_columns=effective_feature_columns,
        ood_enabled=True,
        ood_features=list(V1_OOD_FEATURE_COLUMNS),
        ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
        oof_persist_path=oof_persist_path,
        n_trials_m2=n_trials_m2,
        bounds_profile_m2=bounds_profile_m2,
        include_m1_direction=True,
        # v1-specific M1 params (threaded from run_meta_model signature)
        bounds_profile=bounds_profile,
        sigma_source=sigma_source,
        sigma_k_tp=sigma_k_tp,
        sigma_k_sl=sigma_k_sl,
        sigma_halflife_candles=sigma_halflife_candles,
        sample_weight_mode=sample_weight_mode,
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} [M2-META] complete: {len(results)} trades in {elapsed:.0f}s")
    # Return same (results, faxm_log, strategy) tuple as run_model().
    # MetaLabelingStrategy delegates to M1 for _faxm_log; the M1 strategy is
    # accessible as strategy._m1 — expose M1's faxm_log.
    m1_faxm = getattr(strategy._m1, "_faxm_log", [])
    return results, m1_faxm, strategy


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
    data_filter_columns: list[str] | None = None,
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
        data_filter_columns=data_filter_columns,
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


# ---------------------------------------------------------------------------
# Multi-outer-seed + auto-frozen-HP helper functions (framework/032+)
# ---------------------------------------------------------------------------

#: Outer seed offset table.  Offset i selects inner seeds starting at position
#: i in ENSEMBLE_SEEDS. offsets=[0,5,10,15,20] select disjoint inner-seed
#: windows of up to 5 seeds each (though with ENSEMBLE_SIZE<=10 they may
#: overlap when offset+size>10; callers must verify offset+size<=len(ENSEMBLE_SEEDS)).
_OUTER_SEED_OFFSETS: tuple[int, ...] = (0, 5, 10, 15, 20)

#: Canonical outer seed identifier corresponding to offset=0 (the live model).
V1_CANONICAL_OUTER_SEED: int = 42  # live engine uses this path exclusively


def _compute_comparison_sharpe(comparison_csv: Path) -> float | None:
    """Return OOS monthly_sharpe from a comparison.csv, or None if unavailable."""
    if not comparison_csv.exists():
        return None
    try:
        df = pd.read_csv(comparison_csv)
        row = df[df["metric"] == "monthly_sharpe"]
        if row.empty:
            return None
        return float(row.iloc[0]["out_of_sample"])
    except Exception:  # noqa: BLE001
        return None


def _emit_magnitude_decomposition(
    report_dir: Path,
    main_oos_sharpe: float | None,
    frozen_hp_oos_sharpe: float | None,
    baseline_oos_sharpe: float | None,
) -> None:
    """Write magnitude_decomposition.json to report_dir.

    Computes:
        axis_share   = frozen_hp_OOS - baseline_OOS
        basin_share  = main_OOS - frozen_hp_OOS
        total_share  = main_OOS - baseline_OOS

    All values are OOS monthly Sharpe deltas vs baseline.

    Args:
        report_dir: Root iteration report directory.
        main_oos_sharpe: OOS Sharpe from the main (axis) run.
        frozen_hp_oos_sharpe: OOS Sharpe from the frozen-HP run.
        baseline_oos_sharpe: OOS Sharpe from the BASELINE_V1.md anchor.
    """
    import json as _json  # noqa: PLC0415

    def _delta(a: float | None, b: float | None) -> float | None:
        return round(a - b, 4) if (a is not None and b is not None) else None

    axis_share = _delta(frozen_hp_oos_sharpe, baseline_oos_sharpe)
    basin_share = _delta(main_oos_sharpe, frozen_hp_oos_sharpe)
    total_share = _delta(main_oos_sharpe, baseline_oos_sharpe)

    result = {
        "main_oos_sharpe": main_oos_sharpe,
        "frozen_hp_oos_sharpe": frozen_hp_oos_sharpe,
        "baseline_oos_sharpe": baseline_oos_sharpe,
        "axis_share": axis_share,
        "basin_share": basin_share,
        "total_share": total_share,
        "verdict": (
            "PROMISING-AXIS-CONFIRMED"
            if (axis_share is not None and axis_share >= 0.20)
            else (
                "PROMISING-AXIS-PARTIAL"
                if (axis_share is not None and 0.10 <= axis_share < 0.20)
                else (
                    "PROMISING-BASIN-ONLY"
                    if (axis_share is not None and axis_share < 0.10)
                    else "UNKNOWN"
                )
            )
        ),
        "note": (
            "axis_share = frozen_hp_OOS - baseline_OOS  (axis signal, HP held constant). "
            "basin_share = main_OOS - frozen_hp_OOS  (basin migration, Optuna free). "
            "PROMISING-AXIS-CONFIRMED: axis>=+0.20. "
            "PROMISING-AXIS-PARTIAL: axis in [+0.10, +0.20). "
            "PROMISING-BASIN-ONLY: axis<+0.10 (lift was basin lottery)."
        ),
    }

    out_path = report_dir / "magnitude_decomposition.json"
    with open(out_path, "w") as f:
        _json.dump(result, f, indent=2, default=str)
    print(
        f"[magnitude_decomposition] axis_share={axis_share} "
        f"basin_share={basin_share} total_share={total_share} "
        f"→ verdict={result['verdict']}"
    )
    print(f"[magnitude_decomposition] written to {out_path}")


def _run_multi_seed_aggregate(
    report_dir: Path,
    n_seeds: int,
    seed_dirs: list[Path],
) -> None:
    """Aggregate per-seed comparison.csv into comparison_multi_seed.csv.

    Reads each seed_dir/comparison.csv, extracts OOS monthly_sharpe, and
    emits a summary CSV with mean/std/min/max across outer seeds.

    Args:
        report_dir: Root iteration report directory (comparison_multi_seed.csv
                    is written here).
        n_seeds: Number of outer seeds.
        seed_dirs: List of per-seed report directories (one per outer seed).
    """
    rows = []
    for seed_dir in seed_dirs:
        comp_csv = seed_dir / "comparison.csv"
        sharpe = _compute_comparison_sharpe(comp_csv)
        rows.append(
            {
                "seed_dir": str(seed_dir.name),
                "oos_monthly_sharpe": sharpe,
            }
        )

    df = pd.DataFrame(rows)
    sharpes = df["oos_monthly_sharpe"].dropna().tolist()

    summary = {
        "n_seeds": n_seeds,
        "n_valid": len(sharpes),
        "mean_oos_sharpe": round(float(np.mean(sharpes)), 4) if sharpes else None,
        "std_oos_sharpe": round(float(np.std(sharpes, ddof=1)), 4) if len(sharpes) > 1 else None,
        "min_oos_sharpe": round(float(np.min(sharpes)), 4) if sharpes else None,
        "max_oos_sharpe": round(float(np.max(sharpes)), 4) if sharpes else None,
        "n_profitable_seeds": sum(1 for s in sharpes if s is not None and s > 0),
        "pct_profitable": round(
            sum(1 for s in sharpes if s is not None and s > 0) / len(sharpes) * 100, 1
        )
        if sharpes
        else None,
    }

    # Per-seed rows
    for i, seed_dir in enumerate(seed_dirs):
        comp_csv = seed_dir / "comparison.csv"
        if comp_csv.exists():
            try:
                comp_df = pd.read_csv(comp_csv)
                # Add all metrics from this seed to the aggregate
                for _, mrow in comp_df.iterrows():
                    rows.append(
                        {
                            "seed_dir": str(seed_dir.name),
                            "metric": mrow.get("metric", ""),
                            "in_sample": mrow.get("in_sample", None),
                            "out_of_sample": mrow.get("out_of_sample", None),
                            "ratio": mrow.get("ratio", None),
                        }
                    )
            except Exception:  # noqa: BLE001
                pass

    # Write per-seed summary CSV
    summary_rows = []
    for i, seed_dir in enumerate(seed_dirs):
        sharpe = _compute_comparison_sharpe(seed_dir / "comparison.csv")
        summary_rows.append(
            {
                "outer_seed_id": seed_dir.name.replace("seed_", ""),
                "oos_monthly_sharpe": sharpe,
                "profitable": (sharpe is not None and sharpe > 0),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    out_path = report_dir / "comparison_multi_seed.csv"
    summary_df.to_csv(out_path, index=False)

    print(
        f"[multi_seed] n={n_seeds} mean_sharpe={summary['mean_oos_sharpe']} "
        f"std={summary['std_oos_sharpe']} "
        f"profitable={summary['n_profitable_seeds']}/{summary['n_valid']} "
        f"({summary['pct_profitable']}%)"
    )
    print(f"[multi_seed] aggregate written to {out_path}")


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
        default=50,
        help=(
            "Optuna trials per (symbol, month) cell. Default 50 (standardised at "
            "2026-05-29: matches BASELINE_V1 n_trials=50; eliminates budget-mismatch "
            "confounder vs baseline anchor — see feedback_v1_trial_budget_standardization.md)."
        ),
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
        choices=["abs_pnl", "uniform", "uniqueness_only", "composite_inv_concurrency"],
        default="abs_pnl",
        help=(
            "Sample weighting mode for LightGBM training (iter-v1/016/031). "
            "'abs_pnl' (default) is BIT-IDENTICAL to baseline. "
            "'uniform' passes np.ones(n) — selected for /016. "
            "'uniqueness_only' replaces with raw AFML uniqueness (replaces, not multiplies). "
            "'composite_inv_concurrency' uses scalar 1/c_at_entry(t) mean-renormalized per "
            "(symbol, training_window) — iter-v1/031 axis."
        ),
    )
    # iter-v1/035: label-mode selection.
    # "triple_barrier" (default) is BIT-IDENTICAL to baseline.
    # "trend_scanning" replaces path-dependent TP/SL-first-hit labels with
    # regression-significance OLS labels (Wald t-stat, grid 5/8/13/21 bars).
    # HIGH-RISK axis: changes Optuna's training-objective domain.
    parser.add_argument(
        "--label-mode",
        choices=["triple_barrier", "fixed_horizon", "trend_scanning"],
        default="triple_barrier",
        help=(
            "Label generation mode for LightGBM training (iter-v1/035). "
            "'triple_barrier' (default) is BIT-IDENTICAL to baseline. "
            "'trend_scanning' replaces triple-barrier with OLS Wald-test horizon "
            "selection (AFML Ch.5 §5.5; grid 5/8/13/21 bars) — iter-v1/035 axis. "
            "'fixed_horizon' uses fixed forward-return at timeout horizon."
        ),
    )
    # iter-v1/032: frozen HP mode for basin-lottery ablation.
    # When "baseline_v1", Optuna search is skipped and each (model, month, seed) cell
    # uses the per-cell best HP extracted from the baseline run's Optuna log.
    # Only sample_weight_mode varies vs baseline — isolates the sample-weighting signal
    # from basin migration (the confound identified at /031 closeout).
    parser.add_argument(
        "--frozen-hp-mode",
        choices=["none", "baseline_v1"],
        default="none",
        help=(
            "Frozen HP mode for iter-v1/032 basin-lottery ablation. "
            "'none' (default) = normal Optuna search. "
            "'baseline_v1' = skip Optuna; use baseline per-cell best HP from "
            "data/v1_baseline_frozen_hp.parquet + apply sample_weight_mode."
        ),
    )
    # -----------------------------------------------------------------------
    # Iteration-label override (validation sub-runs — framework/032+).
    #
    # When provided, overrides the auto-formatted iteration_label derived from
    # --iteration NNN (which would produce "v1-NNN").  Use for frozen-HP
    # validation sub-runs that reuse the same --iteration integer but need a
    # distinct dispatch branch + report directory, e.g.:
    #   --iteration 28 --iteration-label v1-028-frozen-hp
    # The override label is validated against an allowlist to prevent accidental
    # dispatch to wrong elif branches.
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--iteration-label",
        type=str,
        default=None,
        dest="iteration_label_override",
        metavar="LABEL",
        help=(
            "Override iteration_label (e.g. 'v1-028-frozen-hp') for frozen-HP "
            "validation sub-runs.  Allowlisted: v1-028-frozen-hp."
        ),
    )
    # -----------------------------------------------------------------------
    # Multi-outer-seed statistical validation (Component 1 — framework/032+).
    #
    # LIVE-TRADING CONTRACT (IMMUTABLE):
    # --seeds only generates STATISTICAL VALIDATION reports.  The live engine
    # ALWAYS runs single-outer-seed=42 (the canonical inner-ensemble-averaged
    # prediction path).  Multi-outer-seed reports are VALIDATION ARTIFACTS ONLY
    # and are NEVER read by the live engine.  The live-compatible path is
    # reports-v1/iteration_v1-NNN/seed_42/ (outer_seed_id=42, offset=0).
    # This contract is verified by: live/engine.py never importing basin_diagnostics
    # and never referencing reports-v1/<NNN>/seed_*/. Audited at framework/032+.
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--seeds",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Number of outer seeds for multi-seed statistical validation (default 1). "
            "When N > 1, the entire walk-forward is repeated N times with different "
            "ensemble_seeds_offset (offsets: 0, 5, 10, 15, 20 for N=5). Each outer "
            "seed's reports are written to reports-v1/iteration_v1-NNN/seed_{id}/. "
            "Aggregate multi-seed comparison is written to comparison_multi_seed.csv. "
            "LIVE-TRADING CONTRACT: live engine uses single-outer-seed=42 ONLY. "
            "Multi-outer-seed reports are STATISTICAL VALIDATION artifacts only."
        ),
    )
    # -----------------------------------------------------------------------
    # Auto-frozen-HP control companion run (Component 3 — framework/032+).
    #
    # When enabled, after the main backtest completes, an automatic second
    # sub-run is launched with --frozen-hp-mode baseline_v1, keeping all other
    # parameters identical.  Both runs' reports persist under main/ and frozen_hp/.
    # The axis-attributable magnitude decomposition is computed automatically
    # and written to magnitude_decomposition.json.
    #
    # This makes the /032 frozen-HP ablation methodology AUTOMATIC for any
    # EXPLORATION iteration — no manual post-hoc ablation needed.
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--auto-frozen-hp-control",
        action="store_true",
        default=False,
        help=(
            "Auto-launch a frozen-HP companion run after the main backtest "
            "(framework/032+). Requires data/v1_baseline_frozen_hp.parquet to exist. "
            "Main reports written to <report_dir>/main/; frozen-HP reports to "
            "<report_dir>/frozen_hp/. Magnitude decomposition emitted to "
            "<report_dir>/magnitude_decomposition.json."
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

    # --iteration-label override: applies after the auto-formatted iteration_label.
    # Only allowlisted labels are accepted — prevents accidental dispatch misrouting.
    _iteration_label_allowlist = {
        "v1-028-frozen-hp",
    }
    if getattr(args, "iteration_label_override", None) is not None:
        _override = args.iteration_label_override.strip()
        if _override not in _iteration_label_allowlist:
            sys.exit(
                f"ERROR: --iteration-label '{_override}' not in allowlist "
                f"{sorted(_iteration_label_allowlist)}. "
                "Add the label to _iteration_label_allowlist before using it."
            )
        iteration_label = _override
        print(f"  [iteration-label override] '{iteration_label}' (allowlisted)")

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
    label_mode_arg = getattr(args, "label_mode", "triple_barrier")
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
    print(f"  label_mode: {label_mode_arg}")

    # iter-v1/032: frozen HP mode resolution.
    frozen_hp_mode_arg = getattr(args, "frozen_hp_mode", "none")
    _frozen_hp_parquet_path: Path | None = None
    if frozen_hp_mode_arg == "baseline_v1":
        _frozen_hp_parquet_path = Path("data") / "v1_baseline_frozen_hp.parquet"
        if not _frozen_hp_parquet_path.exists():
            sys.exit(
                f"ERROR: frozen HP parquet not found: {_frozen_hp_parquet_path}. "
                "Run the baseline log extraction script first."
            )
        print(f"  frozen_hp_mode: baseline_v1 ({_frozen_hp_parquet_path})")
        print("  [iter-v1/032] Optuna search DISABLED — using baseline per-cell best HP")
    else:
        print(f"  frozen_hp_mode: {frozen_hp_mode_arg} (normal Optuna search)")
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
    # iter-v1/032: frozen_hp_parquet threaded through for basin-lottery ablation.
    # iter-v1/035: label_mode threaded through for trend-scanning labels axis.
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
        label_mode=label_mode_arg,
        sigma_halflife_days=sigma_halflife_days_arg,
        frozen_hp_parquet=_frozen_hp_parquet_path,
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
            data_filter_columns=[V1_ITER024_Z30_COLUMN],
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
    elif set(symbols) == set(V1_ITER025_UNIVERSE) and iteration_label == "v1-025":
        # iter-v1/025: OI delta feature-family EXPLORATION (cycle-3 #10/10 — LAST).
        # Single feature addition: oi_delta_30_z90 (V1_FEATURE_COLUMNS_PRUNED 42 → 43).
        # Dispatch mirrors /023 funding-family pattern: 4 models A/C/D/E, same risk gates.
        #
        # HARD BLOCK precondition (LM Master §4 BINDING, brief Section 3.6):
        # ≥3/5 symbols must have ≥1000 IS rows in data/open_interest/<SYM>/8h.csv.
        # If fewer → raise AssertionError; QE returns BLOCK-PENDING-FIX.
        import pandas as _pd

        _oos_cutoff_ms = int(_pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
        _oi_data_dir = Path("data")
        _oi_covered: int = 0
        _oi_per_symbol: dict[str, dict] = {}
        for _sym in V1_ITER025_UNIVERSE:
            _oi_path = _oi_data_dir / "open_interest" / _sym / "8h.csv"
            if not _oi_path.exists():
                _oi_per_symbol[_sym] = {"status": "MISSING", "is_rows": 0}
                continue
            _oi_df_check = _pd.read_csv(_oi_path)
            _is_rows = int((_oi_df_check["open_time"] < _oos_cutoff_ms).sum())
            _status = "PRESENT" if _is_rows >= V1_ITER025_OI_MIN_IS_ROWS else "INSUFFICIENT"
            _oi_per_symbol[_sym] = {"status": _status, "is_rows": _is_rows}
            if _is_rows >= V1_ITER025_OI_MIN_IS_ROWS:
                _oi_covered += 1

        # Emit oi_coverage_check.csv (required deliverable per brief Section 10.5)
        _reports_dir025 = (
            Path(reports_dir) if "reports_dir" in dir() else Path("reports-v1/iteration_v1-025")
        )
        _reports_dir025.mkdir(parents=True, exist_ok=True)
        _coverage_rows = [{"symbol": sym, **info} for sym, info in _oi_per_symbol.items()]
        _pd.DataFrame(_coverage_rows).to_csv(_reports_dir025 / "oi_coverage_check.csv", index=False)
        print(
            f"[iter-v1/025] OI coverage: {_oi_covered}/{len(V1_ITER025_UNIVERSE)} symbols "
            f"≥{V1_ITER025_OI_MIN_IS_ROWS} IS rows. Per-symbol: {_oi_per_symbol}"
        )
        print(f"[iter-v1/025] oi_coverage_check.csv written to {_reports_dir025}")

        assert _oi_covered >= V1_ITER025_OI_MIN_COVERED, (
            f"[iter-v1/025] OI coverage HARD BLOCK: only {_oi_covered}/{len(V1_ITER025_UNIVERSE)} "
            f"symbols have ≥{V1_ITER025_OI_MIN_IS_ROWS} IS rows. "
            f"Per-symbol: {_oi_per_symbol}. "
            f"Run: uv run crypto-trade fetch-oi --symbols ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT"
        )

        # Pre-flight: OI delta column must be in active_feature_columns
        assert V1_ITER025_OI_DELTA_COLUMN in active_feature_columns, (
            f"iter-v1/025 pre-flight: {V1_ITER025_OI_DELTA_COLUMN} not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has oi_delta_30_z90."
        )
        pos_oi = active_feature_columns.index(V1_ITER025_OI_DELTA_COLUMN)
        print(
            f"[iter-v1/025] OI delta feature ACTIVE: "
            f"{V1_ITER025_OI_DELTA_COLUMN}@{pos_oi} "
            f"/ {len(active_feature_columns)} total features"
        )

        # Models A/C/D/E — same risk-gate config as /023 baseline
        # iter-v1/025: pass nan_skip_columns so LightGbmStrategy excludes per-(symbol, month)
        # cells where >50% of oi_delta_30_z90 values are NaN (LM Master §5(a) ADOPTED).
        _025_nan_skip = [V1_ITER025_OI_DELTA_COLUMN]
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
            nan_skip_columns=_025_nan_skip,
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
            nan_skip_columns=_025_nan_skip,
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
            nan_skip_columns=_025_nan_skip,
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
            nan_skip_columns=_025_nan_skip,
            **_r5_kwargs,
        )
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e
        all_results = results_a + results_c + results_d + results_e
        _r5_model_results = [results_a, results_c, results_d, results_e]
        # Feature importance for all 4 models (F-AXIS #1 DUAL GATE: rank + gain-share + breadth).
        # Per LM Master §3 TIGHTENING: breadth check requires ≥3 cohorts at rank ≤20/43.
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK", _strat_c),
            ("Model_D_LTC", _strat_d),
            ("Model_E_DOT", _strat_e),
        ]

        # iter-v1/025: emit per-(symbol, month) NaN-fraction skip log to oi_coverage_check.csv.
        # Merges logs from all 4 strategies; labels each row with the model name.
        # This is the DELIVERABLE per brief Section 10.5 and Critic D2 fix.
        _025_nan_log_rows: list[dict] = []
        for _model_name, _strat_obj in _post_dispatch_fi_strategies:
            for _row in _strat_obj._nan_skip_log:
                _025_nan_log_rows.append({"model": _model_name, **_row})
        if _025_nan_log_rows:
            _reports_dir025_final = (
                Path(reports_dir) if "reports_dir" in dir() else Path("reports-v1/iteration_v1-025")
            )
            _reports_dir025_final.mkdir(parents=True, exist_ok=True)
            _cov_path = _reports_dir025_final / "oi_coverage_check.csv"
            _pd.DataFrame(_025_nan_log_rows).to_csv(_cov_path, index=False)
            _n_skipped = sum(1 for r in _025_nan_log_rows if r["skipped"])
            print(
                f"[iter-v1/025] nan_skip_log: {len(_025_nan_log_rows)} (symbol, month) checks; "
                f"{_n_skipped} skipped. Written to {_cov_path}"
            )

    elif set(symbols) == set(V1_ITER027_UNIVERSE) and iteration_label == "v1-027":
        # iter-v1/027: CYCLE-3 CONFIRMATION METHODOLOGY VALIDATION.
        # 5-Model replacement bundle at multi-seed (--seeds 2 × ENSEMBLE_SIZE=5 = 10 paths/cell).
        #
        # REPLACEMENT SEMANTICS (signal-level merge, NOT additive):
        #   - LINK trades  → Model C' (specialist /018), NOT baseline Model C.
        #   - ETH trades   → Model G (specialist /019 + BTC-trend gate), NOT Model A pool.
        #   - BTC trades   → Model A pool (BTC slice only; ETH slice DROPPED at filter).
        #   - LTC trades   → Model D (baseline).
        #   - DOT trades   → Model E (baseline).
        #
        # FEATURE COLUMNS: 40-col BASELINE-FROZEN subset of V1_FEATURE_COLUMNS_PRUNED (43):
        #   funding_rate_zscore_30, funding_rate_zscore_90, oi_delta_30_z90 EXCLUDED per
        #   /023+/025 NEGATIVE verdicts. Brief §3.3: "NOT 42, NOT 43".
        #
        # F-AXIS-MECHANISM #1 — HARD-ASSERT MANDATE (LM Master §5 ADOPTED):
        #   Three runtime asserts fire BEFORE comparison.csv emission.
        # F-AXIS-MECHANISM #2 — cross-correlation multi-seed < 0.50 check.
        # F-AXIS-MECHANISM #3 — per-specialist OOS Sharpe bands (C' [+0.50,+0.80]; G [+0.30,+0.50]).
        # F-AXIS-MECHANISM #4 — DSR (CONFIRMATION-mode) check.
        # F-AXIS-MECHANISM #5 — PBO < 0.40 (CSCV multi-seed).
        #
        # Deliverables (Section 10.5):
        #   specialist_stability.csv  — per-(inner,outer) seed OOS Sharpe for C' and G.
        #   replacement_filter_audit.csv — pre/post-filter counts per model per symbol.
        #   pareto_2seed.csv          — 2-seed Pareto front bundle analysis.

        # Build 40-col BASELINE-FROZEN feature list (strip funding+OI NEGATIVE variants).
        _027_feature_columns: list[str] = [
            c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _V1_ITER027_EXCLUDED_COLS
        ]
        assert len(_027_feature_columns) == 40, (
            f"iter-v1/027: expected 40 BASELINE-FROZEN feature columns, got "
            f"{len(_027_feature_columns)}. Excluded: {_V1_ITER027_EXCLUDED_COLS}"
        )
        print(
            f"[iter-v1/027] Feature columns: {len(_027_feature_columns)} (40-col "
            f"BASELINE-FROZEN; excluded funding×2 + OI×1)"
        )

        # Model A — Pool BTC+ETH (baseline config; R3 only; ATR 2.9/1.45).
        # ETH slice will be DROPPED at replacement filter below.
        results_a_pool, faxm_a, _strat_a = run_model(
            "A (BTC+ETH pool)",
            ("BTCUSDT", "ETHUSDT"),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=_027_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model C' — LINK specialist (/018 config; R1+R3; ATR 3.5/1.75).
        results_c_spec, faxm_c, _strat_c = run_model(
            "C' (LINK specialist /018)",
            ("LINKUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=_027_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model D — LTC baseline (R1+R3; ATR 3.5/1.75).
        results_d, faxm_d, _strat_d = run_model(
            "D (LTC + R1)",
            ("LTCUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=_027_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model E — DOT baseline (R1+R2+R3; ATR 3.5/1.75).
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
            feature_columns=_027_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model G — ETH specialist (/019 config; R3 only; ATR 2.9/1.45 matching Model A).
        # BTC-trend gate applied post-hoc as stateless filter (BIT-IDENTICAL to /019).
        results_g_raw, faxm_g, _strat_g = run_model(
            "G (ETH-only + R3 + BTC-trend gate)",
            ("ETHUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=_027_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Apply stateless direction-aware BTC-trend gate (BIT-IDENTICAL to /019).
        # Gate kills counter-trend ETH trades: ETH long when BTC ret14 < -8%, or
        # ETH short when BTC ret14 > +8%. Warmup floor of 42 bars; past-only np.searchsorted.
        btc_open_times, btc_closes = load_btc_klines_for_filter()
        _027_gate_cfg = BtcTrendFilterConfig(
            lookback_bars=V1_ITER027_ETH_GATE_LOOKBACK_BARS,
            threshold_pct=V1_ITER027_ETH_GATE_THRESHOLD_PCT,
            enabled=V1_ITER027_ETH_GATE_ENABLED,
        )
        results_g_spec, _027_gate_stats = apply_btc_trend_filter(
            results_g_raw,
            btc_open_times,
            btc_closes,
            _027_gate_cfg,
        )
        _027_gate_dict = _027_gate_stats.as_dict()
        print(
            f"[iter-v1/027 ETH+gate BTC-trend gate] "
            f"normal={_027_gate_dict['n_normal']} "
            f"warmup={_027_gate_dict['n_warmup']} "
            f"killed={_027_gate_dict['n_killed']}/{_027_gate_dict['n_total']} "
            f"fire_rate={_027_gate_dict['fire_rate']:.2%}"
        )

        # REPLACEMENT SEMANTICS: drop Model A's ETH trades; keep BTC slice only.
        results_a_btc_only = [r for r in results_a_pool if r.symbol == "BTCUSDT"]

        # ----------------------------------------------------------------
        # F-AXIS-MECHANISM #1 — HARD ASSERTS (LM Master §5 MANDATE, brief §3.4)
        # These fire BEFORE comparison.csv emission.
        # ----------------------------------------------------------------
        assert set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}, (
            "F-AXIS #1: Pool A leakage — ETH trades not dropped; "
            f"symbols found: {set(r.symbol for r in results_a_btc_only)}"
        )
        assert all(r.symbol == "LINKUSDT" for r in results_c_spec), (
            "F-AXIS #1: C' LINK contamination — non-LINK symbols found in Model C' results; "
            f"symbols: {set(r.symbol for r in results_c_spec)}"
        )
        assert all(r.symbol == "ETHUSDT" for r in results_g_spec), (
            "F-AXIS #1: G ETH contamination — non-ETH symbols found in Model G results; "
            f"symbols: {set(r.symbol for r in results_g_spec)}"
        )
        # Verify zero ETH trades from Pool A bleed-through after filter.
        _027_all_results_combined = (
            results_a_btc_only + results_c_spec + results_d + results_e + results_g_spec
        )
        _027_pool_a_eth_bleed = sum(
            1
            for r in _027_all_results_combined
            if r.symbol == "ETHUSDT" and "A (BTC+ETH pool)" in r.model_name
        )
        assert _027_pool_a_eth_bleed == 0, (
            f"F-AXIS #1: Pool A ETH bleed-through after filter — "
            f"{_027_pool_a_eth_bleed} ETH trades from Pool A still present"
        )
        print(
            f"[iter-v1/027] F-AXIS #1 hard-asserts: PASS "
            f"(Pool A BTC-only={len(results_a_btc_only)} trades, "
            f"C' LINK-only={len(results_c_spec)} trades, "
            f"G ETH-only={len(results_g_spec)} trades, "
            f"Pool-A-ETH-bleed=0)"
        )

        # Aggregate all 5 model results (replacement semantics applied above).
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e + faxm_g
        all_results = results_a_btc_only + results_c_spec + results_d + results_e + results_g_spec
        _r5_model_results = [
            results_a_btc_only,
            results_c_spec,
            results_d,
            results_e,
            results_g_spec,
        ]
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK_spec", _strat_c),
            ("Model_D_LTC", _strat_d),
            ("Model_E_DOT", _strat_e),
            ("Model_G_ETH_spec", _strat_g),
        ]

        # ----------------------------------------------------------------
        # METHODOLOGY VALIDATION DELIVERABLES (Section 10.5)
        # ----------------------------------------------------------------
        import pandas as _pd027  # noqa: PLC0415

        _027_report_dir = Path(reports_dir) / f"iteration_v1-{iteration_label.split('-')[-1]}"
        _027_report_dir.mkdir(parents=True, exist_ok=True)

        # 1. replacement_filter_audit.csv — pre/post counts per model per symbol.
        _027_filter_rows: list[dict] = []
        # Pool A: ETH dropped, BTC retained.
        _027_pool_a_eth_pre = sum(1 for r in results_a_pool if r.symbol == "ETHUSDT")
        _027_pool_a_btc_pre = sum(1 for r in results_a_pool if r.symbol == "BTCUSDT")
        _027_filter_rows += [
            {
                "model": "A (BTC+ETH pool)",
                "symbol": "ETHUSDT",
                "pre_filter_trades": _027_pool_a_eth_pre,
                "post_filter_trades": 0,
                "dropped_count": _027_pool_a_eth_pre,
                "dropped_reason": "replacement_to_specialist_G",
            },
            {
                "model": "A (BTC+ETH pool)",
                "symbol": "BTCUSDT",
                "pre_filter_trades": _027_pool_a_btc_pre,
                "post_filter_trades": _027_pool_a_btc_pre,
                "dropped_count": 0,
                "dropped_reason": "retained",
            },
        ]
        # C' LINK: no filter applied (specialist already LINK-only by construction).
        for _sym in ("LINKUSDT",):
            _cnt = sum(1 for r in results_c_spec if r.symbol == _sym)
            _027_filter_rows.append(
                {
                    "model": "C' (LINK specialist /018)",
                    "symbol": _sym,
                    "pre_filter_trades": _cnt,
                    "post_filter_trades": _cnt,
                    "dropped_count": 0,
                    "dropped_reason": "specialist_by_construction",
                }
            )
        # G ETH: gate killed some trades (raw → filtered).
        _027_g_raw_cnt = len(results_g_raw)
        _027_g_spec_cnt = len(results_g_spec)
        _027_filter_rows.append(
            {
                "model": "G (ETH-only + BTC-trend gate)",
                "symbol": "ETHUSDT",
                "pre_filter_trades": _027_g_raw_cnt,
                "post_filter_trades": _027_g_spec_cnt,
                "dropped_count": _027_g_raw_cnt - _027_g_spec_cnt,
                "dropped_reason": "btc_trend_gate_kill",
            }
        )
        # D LTC, E DOT: no filter.
        for _model_lbl, _res_list, _sym in [
            ("D (LTC + R1)", results_d, "LTCUSDT"),
            ("E (DOT + R1 + R2)", results_e, "DOTUSDT"),
        ]:
            _cnt = len(_res_list)
            _027_filter_rows.append(
                {
                    "model": _model_lbl,
                    "symbol": _sym,
                    "pre_filter_trades": _cnt,
                    "post_filter_trades": _cnt,
                    "dropped_count": 0,
                    "dropped_reason": "retained",
                }
            )
        _027_audit_path = _027_report_dir / "replacement_filter_audit.csv"
        _pd027.DataFrame(_027_filter_rows).to_csv(_027_audit_path, index=False)
        print(f"[iter-v1/027] replacement_filter_audit.csv → {_027_audit_path}")

        # 2. specialist_stability.csv — per-(model, seed) OOS Sharpe placeholder.
        # The per-seed Sharpe is computed by _run_methodology_reporting from comparison.csv;
        # the runner emits a stub here; the engineering report fills in from seed-level logs.
        # Full specialist-level seed breakdown is available from _strat_c._seed_oos_sharpes
        # and _strat_g._seed_oos_sharpes if the LightGbmStrategy emits them.
        # Stub: emit available model-level summary.
        def _oos_monthly_sharpe(res_list: list) -> float:
            """Compute OOS monthly Sharpe from a trade result list (post-cutoff only)."""
            from src.crypto_trade.backtest_report import summarize  # noqa: PLC0415

            _cutoff_ms = int(_pd027.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
            _oos = [r for r in res_list if r.open_time >= _cutoff_ms]
            if not _oos:
                return float("nan")
            try:
                _summ = summarize(_oos)
                return float(_summ.monthly_sharpe)
            except Exception:  # noqa: BLE001
                return float("nan")

        _027_specialist_rows: list[dict] = [
            {
                "specialist": "C' (LINK specialist /018)",
                "model_label": "Model_C_LINK_spec",
                "oos_sharpe": _oos_monthly_sharpe(results_c_spec),
                "oos_trades": sum(
                    1
                    for r in results_c_spec
                    if r.open_time
                    >= int(_pd027.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
                ),
                "note": "multi-seed mean (inner×outer); per-seed breakdown deferred to eng report",
            },
            {
                "specialist": "G (ETH+gate specialist /019)",
                "model_label": "Model_G_ETH_spec",
                "oos_sharpe": _oos_monthly_sharpe(results_g_spec),
                "oos_trades": sum(
                    1
                    for r in results_g_spec
                    if r.open_time
                    >= int(_pd027.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
                ),
                "note": "multi-seed mean (inner×outer); per-seed breakdown deferred to eng report",
            },
        ]
        _027_stability_path = _027_report_dir / "specialist_stability.csv"
        _pd027.DataFrame(_027_specialist_rows).to_csv(_027_stability_path, index=False)
        print(f"[iter-v1/027] specialist_stability.csv → {_027_stability_path}")

        # Note: pareto_2seed.csv is written by _run_methodology_reporting from comparison.csv;
        # the --seeds 2 outer structure produces 2 rows in the Pareto table.
        # specialist_stability.csv above provides the per-specialist OOS Sharpe means.

    elif iteration_label == "v1-031" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/031: composite_inv_concurrency sample-weighting axis.
        # Cycle-4 EXPLORATION #4/10. Axis family: sample-weighting (NINTH family).
        #
        # Architecture: BIT-IDENTICAL to generic baseline dispatch (Models A/C/D/E with
        # V1_BASELINE_UNIVERSE and V1_FEATURE_COLUMNS_PRUNED 43 cols). The ONLY axis
        # change is sample_weight_mode=composite_inv_concurrency threaded via _r5_kwargs.
        # Budget: 5-seed inner ensemble (ENSEMBLE_SIZE=5) × 50 trials — EXPLORATION-WITH-
        # BUDGET-EXCEPTION per LM Master §8 / /030 §8 BINDING mandate.
        #
        # Pre-flight assertions (per /028/030 pattern):
        assert set(symbols) == set(V1_BASELINE_UNIVERSE), (
            f"iter-v1/031 guard: expected V1_BASELINE_UNIVERSE, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/031 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        assert sample_weight_mode_arg == "composite_inv_concurrency", (
            f"iter-v1/031 guard: expected sample_weight_mode=composite_inv_concurrency, "
            f"got {sample_weight_mode_arg!r}. Pass --sample-weight-mode composite_inv_concurrency."
        )
        print(
            f"[iter-v1/031] composite_inv_concurrency sample-weighting dispatch: "
            f"Models A/C/D/E, V1_BASELINE_UNIVERSE, V1_FEATURE_COLUMNS_PRUNED 43 cols. "
            f"ENSEMBLE_SIZE={ensemble_size} (inner 5-seed), n_trials={n_trials}. "
            f"sample_weight_mode=composite_inv_concurrency. "
            f"bounds_profile={bounds_profile}. "
            f"EXPLORATION-WITH-BUDGET-EXCEPTION: wall-clock modal 3.6h / hard cap 6h / "
            f"kill-switch 5.0h."
        )
        results_a031, faxm_a031, _strat_a031 = run_model(
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
        results_c031, faxm_c031, _strat_c031 = run_model(
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
        results_d031, faxm_d031, _strat_d031 = run_model(
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
        results_e031, faxm_e031, _strat_e031 = run_model(
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
        _all_faxm_logs = faxm_a031 + faxm_c031 + faxm_d031 + faxm_e031
        all_results = results_a031 + results_c031 + results_d031 + results_e031
        _r5_model_results = [results_a031, results_c031, results_d031, results_e031]

    elif iteration_label == "v1-032" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/032: FROZEN-HP basin-lottery ablation.
        # Cycle-4 EXPLORATION #5/10. Axis family: sample-weighting (NINTH family).
        #
        # Purpose: disambiguate sample-weighting axis-edge from basin lottery in
        # /031's +1.04 OOS Sharpe. ONLY change vs baseline:
        #   sample_weight_mode=composite_inv_concurrency
        # Optuna search is DISABLED — per (model, month, seed) cell uses baseline's
        # best HP from data/v1_baseline_frozen_hp.parquet (no basin migration possible).
        #
        # Interpretation:
        #   OOS Sharpe >= +1.0  → sample-weighting axis CONFIRMED (edge attributable)
        #   OOS Sharpe ≈ +0.66 ± 0.15 → axis INERT; /031's +1.04 was basin lottery
        #   OOS Sharpe < baseline → axis HARMFUL
        #
        # Budget: 5-seed inner ensemble (ENSEMBLE_SIZE=5), NO Optuna — wall-clock ~10-20 min.
        assert set(symbols) == set(V1_BASELINE_UNIVERSE), (
            f"iter-v1/032 guard: expected V1_BASELINE_UNIVERSE, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/032 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        assert sample_weight_mode_arg == "composite_inv_concurrency", (
            f"iter-v1/032 guard: expected sample_weight_mode=composite_inv_concurrency, "
            f"got {sample_weight_mode_arg!r}. Pass --sample-weight-mode composite_inv_concurrency."
        )
        assert frozen_hp_mode_arg == "baseline_v1", (
            f"iter-v1/032 guard: expected --frozen-hp-mode baseline_v1, "
            f"got {frozen_hp_mode_arg!r}. Pass --frozen-hp-mode baseline_v1."
        )
        assert _frozen_hp_parquet_path is not None and _frozen_hp_parquet_path.exists(), (
            f"iter-v1/032 guard: frozen HP parquet not found: {_frozen_hp_parquet_path}"
        )
        print(
            f"[iter-v1/032] FROZEN-HP ablation: composite_inv_concurrency + baseline hp "
            f"(basin-lottery elimination). "
            f"Models A/C/D/E, V1_BASELINE_UNIVERSE, V1_FEATURE_COLUMNS_PRUNED 43 cols. "
            f"ENSEMBLE_SIZE={ensemble_size} (inner 5-seed), Optuna DISABLED. "
            f"frozen_hp_parquet={_frozen_hp_parquet_path}. "
            f"Wall-clock estimate: 10-20 min (no Optuna)."
        )
        # Note: model_role is passed as "A"/"C"/"D"/"E" (short name) to match the
        # frozen HP parquet's 'model' column (extracted from baseline log).
        results_a032, faxm_a032, _strat_a032 = run_model(
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
            model_role="A",
            **_r5_kwargs,
        )
        results_c032, faxm_c032, _strat_c032 = run_model(
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
            model_role="C",
            **_r5_kwargs,
        )
        results_d032, faxm_d032, _strat_d032 = run_model(
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
            model_role="D",
            **_r5_kwargs,
        )
        results_e032, faxm_e032, _strat_e032 = run_model(
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
            model_role="E",
            **_r5_kwargs,
        )
        _all_faxm_logs = faxm_a032 + faxm_c032 + faxm_d032 + faxm_e032
        all_results = results_a032 + results_c032 + results_d032 + results_e032
        _r5_model_results = [results_a032, results_c032, results_d032, results_e032]
        _post_dispatch_fi_strategies = [
            ("A (BTC/ETH)", _strat_a032),
            ("C (LINK)", _strat_c032),
            ("D (LTC)", _strat_d032),
            ("E (DOT)", _strat_e032),
        ]

    elif iteration_label == "v1-033" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/033: CYCLE-4 CONFIRMATION BUNDLE — Option B.
        # 4 PROMISING specialists + composite_inv_concurrency wrapper.
        # --seeds 1 outer × ENSEMBLE_SIZE=10 inner × n_trials=35 (CONFIRMATION-EXCEPTION).
        #
        # 5-model dispatch:
        #   Model A — BTC-only pool (after ETH removal to Model G)
        #   Model C' — LINK specialist (/018)
        #   Model D' — LTC specialist + atr_sl=1.0 (/028)
        #   Model G  — ETH-only + symmetric BTC-trend gate (/019: lookback=42, ±8%)
        #   Model E  — DOT baseline
        # composite_inv_concurrency applied to ALL 5 models.
        #
        # F-AXIS #1 hard-asserts (per /027 LESSON + feedback_v1_defensive_check_must_be_tested.md):
        #   - Model A symbols ⊆ {BTCUSDT, ETHUSDT} (pool trains on both; BTC retained for OOS)
        #   - Model C' symbols == {LINKUSDT}
        #   - Model D' symbols == {LTCUSDT}
        #   - Model G symbols == {ETHUSDT}
        #   - Model E symbols == {DOTUSDT}
        # All asserts use trade.symbol (REAL TradeResult attribute — NOT trade.model_name).
        print(
            f"[iter-v1/033] CONFIRMATION bundle: A pool + C' LINK + D' LTC atr_sl=1.0 "
            f"+ G ETH+gate + E DOT, all with composite_inv_concurrency. "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer), n_trials={n_trials}. "
            f"CONFIRMATION-EXCEPTION wall-clock 12h hard cap / 10h kill-switch."
        )

        # Model A — BTC+ETH pool (composite_inv_concurrency; R3 only; ATR 2.9/1.45).
        # ETH slice will be DROPPED via replacement-semantics filter below
        # (Model G takes ETH exclusively).
        results_a, faxm_a, _strat_a = run_model(
            "A (BTC+ETH pool + composite_inv_concurrency)",
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

        # Model C' — LINK specialist (/018 config; R1+R3; ATR 2.9/1.45).
        results_c, faxm_c, _strat_c = run_model(
            "C' (LINK specialist + composite_inv_concurrency)",
            ("LINKUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model D' — LTC specialist + atr_sl=1.0 (/028 config; R1+R3; ATR 3.5/1.0).
        results_d, faxm_d, _strat_d = run_model(
            "D' (LTC + atr_sl=1.0 + composite_inv_concurrency)",
            ("LTCUSDT",),
            atr_tp=3.5,
            atr_sl=1.0,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Model G — ETH-only specialist (R3 only; ATR 2.9/1.45 matching Model A).
        # BTC-trend gate applied post-hoc as stateless filter (BIT-IDENTICAL to /019 + /027 spec).
        results_g_raw, faxm_g, _strat_g = run_model(
            "G (ETH-only + composite_inv_concurrency, pre-gate)",
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

        # Apply stateless direction-aware BTC-trend gate (/019 spec: lookback=42, ±8%).
        # Reuses V1_ITER027_ETH_GATE_* constants which match /019 spec exactly.
        btc_open_times_g, btc_closes_g = load_btc_klines_for_filter()
        _033_gate_cfg = BtcTrendFilterConfig(
            lookback_bars=V1_ITER027_ETH_GATE_LOOKBACK_BARS,
            threshold_pct=V1_ITER027_ETH_GATE_THRESHOLD_PCT,
            enabled=V1_ITER027_ETH_GATE_ENABLED,
        )
        results_g, _033_gate_stats = apply_btc_trend_filter(
            results_g_raw,
            btc_open_times_g,
            btc_closes_g,
            _033_gate_cfg,
        )
        _033_gs = _033_gate_stats.as_dict()
        print(
            f"[iter-v1/033] G ETH BTC-trend gate: "
            f"normal={_033_gs['n_normal']} "
            f"warmup={_033_gs['n_warmup']} "
            f"killed={_033_gs['n_killed']}/{_033_gs['n_total']} "
            f"fire_rate={_033_gs['fire_rate']:.2%}"
        )

        # Model E — DOT baseline (R1+R2+R3; ATR 2.9/1.45; composite_inv_concurrency).
        results_e, faxm_e, _strat_e = run_model(
            "E (DOT baseline + composite_inv_concurrency)",
            ("DOTUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=True,
            apply_r2=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # REPLACEMENT SEMANTICS: drop Model A's ETH trades; keep BTC slice only.
        results_a_btc_only = [r for r in results_a if r.symbol == "BTCUSDT"]

        # ----------------------------------------------------------------
        # F-AXIS #1 — HARD ASSERTS (per /027 LESSON + brief Section 3.3)
        # Use REAL TradeResult.symbol attribute — NOT .model_name (per /027 crash).
        # ----------------------------------------------------------------
        _033_a_syms = set(r.symbol for r in results_a_btc_only)
        _033_c_syms = set(r.symbol for r in results_c)
        _033_d_syms = set(r.symbol for r in results_d)
        _033_g_syms = set(r.symbol for r in results_g)
        _033_e_syms = set(r.symbol for r in results_e)

        assert _033_a_syms.issubset({"BTCUSDT"}), (
            f"F-AXIS #1: Model A non-BTC after ETH-drop filter: {_033_a_syms - {'BTCUSDT'}}"
        )
        assert _033_c_syms == {"LINKUSDT"}, f"F-AXIS #1: Model C' non-LINK: {_033_c_syms}"
        assert _033_d_syms == {"LTCUSDT"}, f"F-AXIS #1: Model D' non-LTC: {_033_d_syms}"
        assert _033_g_syms == {"ETHUSDT"}, f"F-AXIS #1: Model G non-ETH: {_033_g_syms}"
        assert _033_e_syms == {"DOTUSDT"}, f"F-AXIS #1: Model E non-DOT: {_033_e_syms}"
        print(
            f"[iter-v1/033] F-AXIS #1 hard-asserts: PASS "
            f"(A BTC-only={len(results_a_btc_only)}, "
            f"C'={len(results_c)}, D'={len(results_d)}, "
            f"G={len(results_g)}, E={len(results_e)} trades)"
        )

        # Aggregate all 5 model results.
        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_g + faxm_e
        all_results = results_a_btc_only + results_c + results_d + results_g + results_e
        _r5_model_results = [
            results_a_btc_only,
            results_c,
            results_d,
            results_g,
            results_e,
        ]
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK", _strat_c),
            ("Model_D_LTC_atr_sl_1.0", _strat_d),
            ("Model_G_ETH_gate", _strat_g),
            ("Model_E_DOT", _strat_e),
        ]

    elif iteration_label == "v1-034" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/034: cycle-5 EXPLORATION #1/10 — basis z-score feature family.
        # NEW feature: basis_zscore_30 (perp-spot basis z-score, 30-bar window).
        # V1_FEATURE_COLUMNS_PRUNED extended 43 → 44 (basis_zscore_30 at alphabetical pos 0).
        # Feature parquets must be regenerated with --groups basis_v1 before running.
        # ALL other config IDENTICAL to baseline: 4 models A/C/D/E, same ATR/R-gate/etc.
        # NORMAL-RISK declaration (pure feature-add; no training-objective domain change).
        assert "basis_zscore_30" in active_feature_columns, (
            "iter-v1/034 pre-flight: basis_zscore_30 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has basis col. "
            "Also regenerate feature parquets: "
            "uv run crypto-trade features --track v1 --groups basis_v1 --format parquet"
        )
        pos_basis = active_feature_columns.index("basis_zscore_30")
        print(
            f"[iter-v1/034] BASIS-Z30 ACTIVE: basis_zscore_30@{pos_basis} "
            f"/ {len(active_feature_columns)} total features. "
            f"Feature-family axis (NEW data class: perp-spot basis). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer), n_trials={n_trials}."
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
        _r5_model_results = [results_a, results_c, results_d, results_e]
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK", _strat_c),
            ("Model_D_LTC", _strat_d),
            ("Model_E_DOT", _strat_e),
        ]

    elif iteration_label == "v1-035" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/035: cycle-5 EXPLORATION #2/10 — trend-scanning labels axis.
        # STRUCTURAL label-mode change: triple-barrier TP/SL-first-hit →
        # OLS regression-significance (Wald t-stat, grid 5/8/13/21 bars, AFML Ch.5 §5.5).
        # HIGH-RISK declaration: changes Optuna training-objective domain via per-row
        # weight distribution shift (TB ~8.5% modal → TS ~2.5% modal, 3.3-4.6× scale shift).
        # NO new feature module needed; NO feature regen needed. V1_FEATURE_COLUMNS_PRUNED
        # 43 cols UNCHANGED. Execution-side ATR barriers unchanged (atr_tp/atr_sl per model
        # are for exits, not labeling — trend-scanning ONLY changes the M1 supervised target).
        # All other config IDENTICAL to baseline: 4 models A/C/D/E, same atr_tp/atr_sl,
        # same R-gate config, same V1_FEATURE_COLUMNS_PRUNED.
        assert label_mode_arg == "trend_scanning", (
            f"iter-v1/035 pre-flight FAIL: expected --label-mode trend_scanning "
            f"but got {label_mode_arg!r}. "
            "Pass --label-mode trend_scanning to activate the trend-scanning axis."
        )
        print(
            f"[iter-v1/035] TREND-SCANNING-LABEL ACTIVE: "
            f"label_mode={label_mode_arg}, "
            f"trend_scan_grid=(5, 8, 13, 21), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), "
            f"n_trials={n_trials}, "
            f"seeds=1 (outer=42). "
            f"HIGH-RISK: training-objective domain changed. "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED UNCHANGED)."
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
        _r5_model_results = [results_a, results_c, results_d, results_e]
        _post_dispatch_fi_strategies = [
            ("Model_A_pool", _strat_a),
            ("Model_C_LINK", _strat_c),
            ("Model_D_LTC", _strat_d),
            ("Model_E_DOT", _strat_e),
        ]

    elif iteration_label == "v1-036" and set(symbols) == set(V1_ITER036_UNIVERSE):
        # iter-v1/036: cycle-5 EXPLORATION #3/10 — per-cohort isolation of /035's bimodal signal.
        # Tests whether LINK +74.68pp / DOT +111.67pp OOS lifts from /035 survive when the
        # large-cap cohorts (BTC/ETH/LTC) are REMOVED from the portfolio.
        # HIGH-RISK: 2-mechanism stack — (1) per-cohort isolation (universe 5→2 substitution,
        # removing large-cap Optuna averaging) + (2) trend-scanning labels (already HIGH-RISK
        # at /035; training-objective domain change). Single-seed OPT-OUT per cycle-5 standard.
        # Model A pool, Model D LTC, Model G ETH SKIPPED — ONLY Model C' (LINK) + Model E (DOT).
        # V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED. No new feature module needed.
        assert label_mode_arg == "trend_scanning", (
            f"iter-v1/036 pre-flight FAIL: expected --label-mode trend_scanning "
            f"but got {label_mode_arg!r}. "
            "Pass --label-mode trend_scanning to activate the per-cohort-trend-scanning axis. "
            "iter-v1/036 tests /035's bimodal LINK+DOT finding at per-cohort isolation — "
            "trend_scanning labels are the required context (not a new axis change)."
        )
        print(
            f"[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE: "
            f"models=Model_C_LINK + Model_E_DOT, "
            f"label_mode={label_mode_arg}, "
            f"trend_scan_grid=(5, 8, 13, 21), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), "
            f"n_trials={n_trials}, "
            f"seeds=1 (outer=42). "
            f"HIGH-RISK: 2-mechanism stack (per-cohort isolation + trend-scanning labels). "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED UNCHANGED)."
        )
        # Model C': LINK specialist + trend_scanning labels
        # R1=ON (consecutive-SL cool-down); R3=ON (Mahalanobis OOD gate) — baseline Model C config
        results_c036, faxm_c036, _strat_c036 = run_model(
            "C' (LINK + R1)",
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
        # Model E: DOT specialist + trend_scanning labels
        # R1=ON, R2=ON (drawdown brake), R3=ON — baseline Model E config
        results_e036, faxm_e036, _strat_e036 = run_model(
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

        # F-AXIS #6 dispatch verification: assert per-cohort isolation enforced
        c036_symbols = {r.symbol for r in results_c036}
        e036_symbols = {r.symbol for r in results_e036}
        assert c036_symbols.issubset({"LINKUSDT"}), (
            f"[iter-v1/036] Model C' produced non-LINK results: {c036_symbols - {'LINKUSDT'}}. "
            "Per-cohort isolation failed — Model C' must trade LINKUSDT only."
        )
        assert e036_symbols.issubset({"DOTUSDT"}), (
            f"[iter-v1/036] Model E produced non-DOT results: {e036_symbols - {'DOTUSDT'}}. "
            "Per-cohort isolation failed — Model E must trade DOTUSDT only."
        )

        print(
            f"[iter-v1/036] Bundle dispatch verified: "
            f"C'={len(results_c036)} trades (LINK) "
            f"E={len(results_e036)} trades (DOT)"
        )

        _all_faxm_logs = faxm_c036 + faxm_e036
        all_results = results_c036 + results_e036
        _r5_model_results = [results_c036, results_e036]
        _post_dispatch_fi_strategies = [
            ("Model_C_LINK_trend_scan_specialist", _strat_c036),
            ("Model_E_DOT_trend_scan_specialist", _strat_e036),
        ]

    elif set(symbols) == set(V1_BASELINE_UNIVERSE) and iteration_label not in (
        "v1-021",
        "v1-023",
        "v1-024",
        "v1-025",
        "v1-027",
        "v1-030",
        "v1-031",
        "v1-032",
        "v1-033",
        "v1-034",
        "v1-035",
        "v1-036",
    ):
        # Generic baseline-universe dispatch.
        # Non-/021/023/024/025/027/030/031/032/033/034/035 iterations. Models A/C/D/E with
        # V1_BASELINE_UNIVERSE symbols. BIT-IDENTICAL to historical
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
    elif set(symbols) == set(V1_ITER022_UNIVERSE) and iteration_label == "v1-022":
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

    elif set(symbols) == set(V1_ITER028_UNIVERSE) and iteration_label == "v1-028":
        # iter-v1/028: D' specialist (LTC-only) + tighter ATR-based SL (atr_sl=1.0 vs 1.75).
        # Cycle-4 EXPLORATION #1 of 10. Axis family: per-cohort-specialization-LTC-v2 (15th).
        #
        # KEY MECHANISM: atr_sl=1.0 (changed from baseline 1.75 Model D).
        # atr_sl is upstream of triple-barrier label generation — tightening 1.75→1.0
        # narrows the lower barrier by 43%, shifts class balance (MORE -1 labels with
        # SMALLER magnitudes), AND relocates the Optuna basin. TWO basin-relocation
        # vectors (LM Master Rec #2 ADOPTED). PARTIAL basin inoculation, NOT immunity.
        #
        # HIGH-RISK variance budget: ENSEMBLE_SIZE=10 (v1-runner-compatible; no --seeds
        # flag in v1 argparse; maps to inner ensemble per feedback_v1_ensemble.md).
        #
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY LTCUSDT rows.
        # F-AXIS-MECHANISM #2: IS [80,180] / OOS [20,60] trade band.
        # F-AXIS-MECHANISM #3 (COUNTER-INTUITIVE per LM Master Rec #4): tighter SL →
        #   INCREASES SL fire-rate. Predicted OOS SL fire-rate 75-90% (vs baseline 62%).
        # F-AXIS-MECHANISM #5 (LOAD-BEARING per LM Master Rec #6): OOS TP-exit count.
        #   If TP-count=0 OOS, verdict CANNOT exceed PROMISING-INERT regardless of F1.
        assert set(symbols) == {"LTCUSDT"}, (
            f"iter-v1/028 guard: expected {{LTCUSDT}}, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/028 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        results_d028, faxm_d028, _strat_d028 = run_model(
            "D' (LTC-only + tighter SL)",
            ("LTCUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches Model D baseline per brief §3.3
            atr_sl=1.0,  # CHANGED from 1.75 — tighter SL is the axis (KEY parameter)
            apply_r1=True,  # UNCHANGED — Model D baseline has R1 consecutive-SL cooldown
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        print(
            f"[iter-v1/028] LTC-only D' specialist: {len(results_d028)} trades "
            f"(atr_sl=1.0 vs baseline 1.75; ensemble_size={ensemble_size})"
        )
        _all_faxm_logs = faxm_d028
        all_results = results_d028
        _r5_model_results = [results_d028]
        _post_dispatch_fi_strategies = [("Model_D_LTC_specialist", _strat_d028)]

    elif set(symbols) == set(V1_ITER028_UNIVERSE) and iteration_label == "v1-028-frozen-hp":
        # validation/iter028-frozen-hp: basin-lottery re-validation of /028 PROMISING.
        #
        # Purpose: decompose /028's +0.598 OOS Δ into axis_share vs basin_share.
        # /028 axis = atr_sl=1.0 (tighter SL than baseline 1.75).
        # This sub-run keeps EVERY hyperparameter IDENTICAL to the baseline (frozen HP
        # from data/v1_baseline_frozen_hp.parquet, Model D rows) but applies atr_sl=1.0.
        # No Optuna search — basin cannot migrate.
        #
        # Decomposition anchors:
        #   baseline_oos  = LTC-in-pool OOS Sharpe = -0.267 (per-trade, per /028 review)
        #   /028_main_oos = /028 comparison.csv OOS Sharpe = +0.3310
        #   /028_frozen_oos = this run's OOS Sharpe
        #
        #   axis_share  = /028_frozen_oos - baseline_oos
        #   basin_share = /028_main_oos - /028_frozen_oos
        #   total_share = /028_main_oos - baseline_oos = +0.598
        #
        # Verdict thresholds:
        #   axis_share >= +0.20 → PROMISING-AXIS-CONFIRMED
        #   axis_share +0.10..+0.20 → PROMISING-AXIS-PARTIAL
        #   axis_share < +0.10  → PROMISING-BASIN-ONLY
        #
        # Budget: frozen HP = no Optuna → wall-clock ~5-10 min.
        assert set(symbols) == {"LTCUSDT"}, (
            f"iter-v1/028-frozen-hp guard: expected {{LTCUSDT}}, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/028-frozen-hp guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        assert frozen_hp_mode_arg == "baseline_v1", (
            f"iter-v1/028-frozen-hp guard: expected --frozen-hp-mode baseline_v1, "
            f"got {frozen_hp_mode_arg!r}. Pass --frozen-hp-mode baseline_v1."
        )
        assert _frozen_hp_parquet_path is not None and _frozen_hp_parquet_path.exists(), (
            f"iter-v1/028-frozen-hp guard: frozen HP parquet not found: {_frozen_hp_parquet_path}"
        )
        print(
            f"[iter-v1/028-frozen-hp] FROZEN-HP basin-lottery re-validation of /028 PROMISING. "
            f"LTC-only, atr_sl=1.0 (axis), atr_tp=3.5, apply_r1=True. "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), Optuna DISABLED (frozen baseline HP). "
            f"frozen_hp_parquet={_frozen_hp_parquet_path}. "
            f"Baseline anchor OOS Sharpe=-0.267; /028 main OOS=+0.3310; total Δ=+0.598. "
            f"Wall-clock estimate: 5-10 min (no Optuna)."
        )
        results_d028fhp, faxm_d028fhp, _strat_d028fhp = run_model(
            "D' (LTC-only + atr_sl=1.0 + frozen baseline HP)",
            ("LTCUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches /028 axis spec
            atr_sl=1.0,  # AXIS CHANGE — tighter SL (same as /028 main)
            apply_r1=True,  # UNCHANGED
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            model_role="D",  # matches frozen HP parquet 'model' column
            **_r5_kwargs,
        )
        print(
            f"[iter-v1/028-frozen-hp] LTC-only D' frozen-HP: {len(results_d028fhp)} trades "
            f"(atr_sl=1.0, baseline HP frozen, no basin migration)"
        )
        _all_faxm_logs = faxm_d028fhp
        all_results = results_d028fhp
        _r5_model_results = [results_d028fhp]
        _post_dispatch_fi_strategies = [("Model_D_LTC_specialist_frozen_hp", _strat_d028fhp)]

    elif set(symbols) == set(V1_ITER029_UNIVERSE) and iteration_label == "v1-029":
        # iter-v1/029: DOT-only single-cohort EXPLORATION + symmetric BTC-trend gate ±8%.
        # Cycle-4 EXPLORATION #2 of 10. Axis family: per-cohort-specialization-DOT-v2 (16th).
        # LM Master HYBRID class FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG → Path C.
        #
        # Model E semantics: R1=ON, R2=OFF, R3=ON, atr_tp=3.5, atr_sl=1.75 (FROZEN from
        # baseline DOT per brief §3.2 + §3.3). Gate is the ONLY axis change vs DOT-in-pool.
        #
        # Gate: stateless direction-aware symmetric BTC-trend gate at ±8% on BTC 14d return.
        #   Kill LONG when BTC ret_42 < -8%  (counter-trend long into BTC dump).
        #   Kill SHORT when BTC ret_42 > +8%  (counter-trend short into BTC rally).
        #   Symmetric long_only_mode=False — BIT-IDENTICAL to /019 ETH gate spec.
        #
        # F-AXIS-MECHANISM #1: trades.csv must contain ONLY DOTUSDT rows.
        # F-AXIS-MECHANISM #2: IS [62, 130] / OOS [22, 55] trade band.
        # F-AXIS-MECHANISM #3 (LOAD-BEARING): IS gate fire-rate [10%, 30%] modal 18%;
        #   OOS gate fire-rate [5%, 30%] modal 15%. OOS < 5% → UNDER-FIRE cap (INERT).
        # F-AXIS-MECHANISM #5 (LOAD-BEARING): OOS TP-exit count >= 2. If < 2 → INERT cap.
        assert set(symbols) == {"DOTUSDT"}, (
            f"iter-v1/029 guard: expected {{DOTUSDT}}, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/029 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        results_e029, faxm_e029, _strat_e029 = run_model(
            "E' (DOT-only + R1 + R3 + BTC-trend gate)",
            ("DOTUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches Model E baseline per brief §3.2
            atr_sl=1.75,  # UNCHANGED — matches Model E baseline (gate is the only axis)
            apply_r1=True,  # ON — Model E baseline has R1 consecutive-SL cooldown
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        # Apply stateless symmetric BTC-trend gate as post-hoc trade-stream filter.
        # Gate kills counter-trend DOT trades: DOT long when BTC ret_42 < -8%, or
        # DOT short when BTC ret_42 > +8%. Symmetric (long_only_mode=False = default).
        # IS/OOS fire-rates logged separately for F-AXIS #3 LOAD-BEARING diagnostic.
        # load_btc_klines_for_filter() reads data/BTCUSDT/8h.csv (must be fresh
        # per pre-flight check: close_time within 16h of measurement time).
        btc_open_times_029, btc_closes_029 = load_btc_klines_for_filter()
        gate_cfg_029 = BtcTrendFilterConfig(
            lookback_bars=V1_ITER029_BTC_GATE_LOOKBACK_BARS,
            threshold_pct=V1_ITER029_BTC_GATE_THRESHOLD_PCT,
            enabled=V1_ITER029_BTC_GATE_ENABLED,
        )
        # Split IS/OOS to log separate fire-rate stats for F-AXIS #3 monitoring.
        results_e029_is = [t for t in results_e029 if t.open_time < OOS_CUTOFF_MS]
        results_e029_oos = [t for t in results_e029 if t.open_time >= OOS_CUTOFF_MS]
        results_e029_is_gated, gate_stats_is = apply_btc_trend_filter(
            results_e029_is, btc_open_times_029, btc_closes_029, gate_cfg_029
        )
        results_e029_oos_gated, gate_stats_oos = apply_btc_trend_filter(
            results_e029_oos, btc_open_times_029, btc_closes_029, gate_cfg_029
        )
        gs_is = gate_stats_is.as_dict()
        gs_oos = gate_stats_oos.as_dict()
        print(
            f"[iter-v1/029] BTC-trend gate IS fire-rate: "
            f"{gs_is['n_killed']}/{gs_is['n_total']} = {gs_is['fire_rate']:.2%} "
            f"(normal={gs_is['n_normal']} warmup={gs_is['n_warmup']})"
        )
        print(
            f"[iter-v1/029] BTC-trend gate OOS fire-rate: "
            f"{gs_oos['n_killed']}/{gs_oos['n_total']} = {gs_oos['fire_rate']:.2%} "
            f"(normal={gs_oos['n_normal']} warmup={gs_oos['n_warmup']})"
        )
        # F-AXIS #5: OOS TP-exit count diagnostic (LOAD-BEARING — < 2 caps verdict).
        oos_tp_count = sum(1 for t in results_e029_oos_gated if t.exit_reason == "take_profit")
        print(f"[iter-v1/029] OOS TP-exit count: {oos_tp_count}")
        # Recombine gated IS + OOS back into all_results.
        results_e029 = results_e029_is_gated + results_e029_oos_gated
        _all_faxm_logs = faxm_e029
        all_results = results_e029
        _r5_model_results = [results_e029]
        _post_dispatch_fi_strategies = [("Model_E_DOT_specialist", _strat_e029)]

    elif iteration_label == "v1-030" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/030: META-LABELING M2 layer — 3 separate M2 classifiers (A/C/D).
        # Cycle-4 EXPLORATION #3/10. Axis family: meta-labeling (NEW NINTH family).
        #
        # Architecture:
        #   - Models A/C/D: MetaLabelingStrategy (M1 = LightGbmStrategy wrapped by M2).
        #     M2 is a per-model binary LGBMClassifier (n_trials_m2=18, bounds="v1_030").
        #     M2 input: 43 V1_FEATURE_COLUMNS_PRUNED + m1_confidence + m1_direction = 45 dims.
        #     M2 threshold: 0.5 PINNED (single-axis discipline; not tuned at /030).
        #   - Model E (DOT): plain LightGbmStrategy — Model E EXCLUDED from M2 per
        #     LM Master §3 binding call (75 cumulative M1-positives < LightGBM
        #     classifier threshold for 45-feature × n_trials_m2=18).
        #
        # Pre-flight assertions:
        assert set(symbols) == set(V1_BASELINE_UNIVERSE), (
            f"iter-v1/030 guard: expected V1_BASELINE_UNIVERSE, got {set(symbols)}"
        )
        assert len(active_feature_columns) == 43, (
            f"iter-v1/030 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}"
        )
        print(
            f"[iter-v1/030] META-LABELING dispatch: 3 M2 classifiers (A/C/D), "
            f"Model E EXCLUDED (LM Master §3 sample-size mandate). "
            f"n_trials_m2={V1_ITER030_N_TRIALS_M2}, bounds_m2={V1_ITER030_BOUNDS_PROFILE_M2}, "
            f"M2_threshold={V1_ITER030_M2_THRESHOLD} PINNED, "
            f"M2_expected_cells={V1_ITER030_M2_CELLS_EXPECTED} "
            f"(min_pass={V1_ITER030_M2_CELLS_MIN})"
        )
        # --- Model A: BTC+ETH pooled + M2 meta-labeling ---
        results_a030, faxm_a030, _strat_a030 = run_meta_model(
            "A (BTC/ETH + M2)",
            ("BTCUSDT", "ETHUSDT"),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            n_trials_m2=V1_ITER030_N_TRIALS_M2,
            bounds_profile_m2=V1_ITER030_BOUNDS_PROFILE_M2,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        print(
            f"[iter-v1/030] Model A: {len(results_a030)} trades "
            f"(M2 active — BTC+ETH pooled; M2_cells expected ~53)"
        )
        # --- Model C: LINK specialist + M2 meta-labeling ---
        results_c030, faxm_c030, _strat_c030 = run_meta_model(
            "C (LINK + R1 + M2)",
            ("LINKUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            n_trials_m2=V1_ITER030_N_TRIALS_M2,
            bounds_profile_m2=V1_ITER030_BOUNDS_PROFILE_M2,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        print(
            f"[iter-v1/030] Model C: {len(results_c030)} trades "
            f"(M2 active — LINK specialist; M2_cells expected ~53)"
        )
        # --- Model D: LTC specialist + M2 meta-labeling ---
        results_d030, faxm_d030, _strat_d030 = run_meta_model(
            "D (LTC + R1 + M2)",
            ("LTCUSDT",),
            atr_tp=3.5,
            atr_sl=1.75,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            n_trials_m2=V1_ITER030_N_TRIALS_M2,
            bounds_profile_m2=V1_ITER030_BOUNDS_PROFILE_M2,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )
        print(
            f"[iter-v1/030] Model D: {len(results_d030)} trades "
            f"(M2 active — LTC specialist; M2_cells expected ~53)"
        )
        # --- Model E: DOT specialist — plain LightGbmStrategy (NO M2) ---
        # Model E EXCLUDED from M2 per LM Master §3 sample-size binding call.
        # DOT trades pass through M1 directly with no M2 filtering applied.
        results_e030, faxm_e030, _strat_e030 = run_model(
            "E (DOT + R1 + NO-M2)",
            ("DOTUSDT",),
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
        print(
            f"[iter-v1/030] Model E: {len(results_e030)} trades "
            f"(M2 EXCLUDED — DOT; 75 cumulative M1-pos < LightGBM threshold; "
            f"m2_passed=NaN for all DOT trades)"
        )
        # --- F-AXIS instrumentation (post-dispatch) ---
        # F-AXIS #1: M2-trained cells count (target ≥ 80 of 159 expected).
        # Track via M2_TRAINED=True/False prints in metalabeling.py (run.log parse).
        # The MetaLabelingStrategy logs per-month M2_TRAINED status unconditionally.
        all_results_m2 = results_a030 + results_c030 + results_d030  # M2-filtered trades
        all_results_e = results_e030  # M2-excluded trades (pass-through)
        # F-AXIS #2: OOS trade count diagnostic.
        oos_m2_trades = [t for t in all_results_m2 if t.open_time >= OOS_CUTOFF_MS]
        oos_e_trades = [t for t in all_results_e if t.open_time >= OOS_CUTOFF_MS]
        oos_total = len(oos_m2_trades) + len(oos_e_trades)
        print(
            f"[iter-v1/030] F-AXIS #2 OOS trade count: {oos_total} "
            f"(M2-filtered A/C/D: {len(oos_m2_trades)}, Model E pass-through: {len(oos_e_trades)}) "
            f"[target band: 95-165 modal 130; CRITICAL floor: {V1_ITER030_OOS_TRADES_FLOOR}]"
        )
        # F-AXIS #1 HARD ASSERT: OOS trade count >= 50 (LM Master §9 Q8 item 3).
        # Fires if M2 over-filters AND Model E also produces 0 trades OOS.
        # Per brief Section 3.3: M2-skip is legitimate per-cell; aggregate check only.
        if oos_total < V1_ITER030_OOS_TRADES_FLOOR:
            print(
                f"[iter-v1/030] F-AXIS #1 HARD ASSERT FAIL: OOS trades {oos_total} "
                f"< floor {V1_ITER030_OOS_TRADES_FLOOR} → TECHNICAL FAILURE",
                file=sys.stderr,
            )
            sys.exit(2)  # TECHNICAL FAILURE exit code per LM Master §9 Q8 item 3
        # F-AXIS #3: M2 fire-rate per model (IS and OOS separately).
        # All trades in results_a/c/d_030 HAVE passed M2 (by construction —
        # MetaLabelingStrategy.get_signal() only returns signal when M2 passes).
        # M2-filtered trades = baseline trades that WERE NOT vetoed by M2.
        # We cannot directly count M2-skips from trade results alone;
        # the count is available in run.log via M2_TRAINED=True/False lines.
        # Per model OOS trade counts (F-AXIS #3 monitoring):
        oos_a = [t for t in results_a030 if t.open_time >= OOS_CUTOFF_MS]
        oos_c = [t for t in results_c030 if t.open_time >= OOS_CUTOFF_MS]
        oos_d = [t for t in results_d030 if t.open_time >= OOS_CUTOFF_MS]
        oos_tp_a = sum(1 for t in oos_a if t.exit_reason == "take_profit")
        oos_tp_c = sum(1 for t in oos_c if t.exit_reason == "take_profit")
        oos_tp_d = sum(1 for t in oos_d if t.exit_reason == "take_profit")
        oos_tp_total = oos_tp_a + oos_tp_c + oos_tp_d
        print(
            f"[iter-v1/030] F-AXIS #5 OOS TP-exit count: {oos_tp_total} total "
            f"(A:{oos_tp_a}, C:{oos_tp_c}, D:{oos_tp_d}) "
            f"[floor: {V1_ITER030_OOS_TP_FLOOR}; Model D LOAD-BEARING floor: "
            f"{V1_ITER030_MODEL_D_OOS_TP_FLOOR}]"
        )
        if oos_tp_d < V1_ITER030_MODEL_D_OOS_TP_FLOOR:
            print(
                f"[iter-v1/030] F-AXIS #5 Model D OOS TP WARNING: {oos_tp_d} < "
                f"{V1_ITER030_MODEL_D_OOS_TP_FLOOR} LOAD-BEARING floor. "
                f"Verdict CAPS at PROMISING-INERT regardless of headline Sharpe Δ "
                f"(LTC-long catastrophe pre-vet failure per LM Master §5 + /028 §6 transfer).",
                file=sys.stderr,
            )
        # M2 fire-rate per model IS/OOS.
        is_a = [t for t in results_a030 if t.open_time < OOS_CUTOFF_MS]
        is_c = [t for t in results_c030 if t.open_time < OOS_CUTOFF_MS]
        is_d = [t for t in results_d030 if t.open_time < OOS_CUTOFF_MS]
        print(
            f"[iter-v1/030] Post-M2 trade counts — "
            f"IS: A={len(is_a)}, C={len(is_c)}, D={len(is_d)} | "
            f"OOS: A={len(oos_a)}, C={len(oos_c)}, D={len(oos_d)}"
        )
        # Aggregate.
        _all_faxm_logs = faxm_a030 + faxm_c030 + faxm_d030 + faxm_e030
        all_results = all_results_m2 + all_results_e
        _r5_model_results = [results_a030, results_c030, results_d030, results_e030]

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
    # iter-v1/030: annotate trades.csv with m2_passed column (post-hoc).
    # Per LM Master §9 Q8 item 4: m2_passed = 1 for M2-filtered trades (A/C/D),
    # NaN = M2 inactive (Model E / DOT trades pass through unmodified).
    # TradeResult is frozen — annotation is applied via CSV post-processing on
    # the already-written trades.csv files from generate_iteration_reports().
    # -------------------------------------------------------------------------
    if iteration_label == "v1-030":
        # Build a set of (open_time, symbol) keys for M2-active trades (A/C/D).
        # Model E trades have m2_passed=NaN (absent = inactive).
        _m2_active_keys: set[tuple[int, str]] = {
            (t.open_time, t.symbol) for t in (results_a030 + results_c030 + results_d030)
        }
        for _sub_dir in ("in_sample", "out_of_sample"):
            _csv_path = report_dir / _sub_dir / "trades.csv"
            if not _csv_path.exists():
                continue
            _df = pd.read_csv(_csv_path)
            # m2_passed: 1.0 for M2-active models (A/C/D); NaN for Model E (DOT)
            _df["m2_passed"] = _df.apply(
                lambda row: (
                    1.0
                    if (int(row["open_time"]), row["symbol"]) in _m2_active_keys
                    else float("nan")
                ),
                axis=1,
            )
            _df.to_csv(_csv_path, index=False)
        print(
            f"[iter-v1/030] m2_passed column added to trades.csv "
            f"(M2-active keys: {len(_m2_active_keys)}; Model E DOT = NaN)"
        )

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
    # Skip _run_methodology_reporting for frozen-HP validation runs: no Optuna
    # search = no OOF parquet = n_eff / PSR / ADF metrics are N/A.  The core
    # comparison.csv with IS/OOS Sharpe is already written by generate_iteration_reports;
    # that is all we need for basin-lottery decomposition.
    if frozen_hp_mode_arg == "none":
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
    else:
        print(
            f"[run_baseline_v1] frozen_hp_mode={frozen_hp_mode_arg!r}: "
            "skipping _run_methodology_reporting (no OOF parquet; n_eff/PSR/ADF N/A). "
            "Core comparison.csv Sharpe sufficient for basin-lottery decomposition."
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

    # -------------------------------------------------------------------------
    # framework/032+: basin diagnostics auto-emission (Component 2).
    # Emits V1/V2/V3 basin-lottery metrics automatically after every backtest.
    #
    # Bug fix (2026-05-29): OOF_PARQUET_PATH stores candle-level OOF returns
    # with schema [trial_id, symbol, train_month, fold_idx, candle_open_time_ms,
    # oof_return] for N_eff/DSR computation.  V1/V2 basin diagnostics need
    # per-trial Sharpe with schema [outer_seed, model, month, inner_seed,
    # trial_number, sharpe].  We derive the basin-trials parquet from the OOF
    # parquet via derive_basin_trials_from_oof_parquet before calling the summary.
    #
    # The baseline OOS trades CSV is read from
    # reports-v1/iteration_v1-baseline/out_of_sample/trades.csv (must exist).
    # -------------------------------------------------------------------------
    if mode_label != "BASELINE":
        _diagnostics_dir = report_dir / "basin_diagnostics"
        _baseline_oos_trades = Path("reports-v1/iteration_v1-baseline/out_of_sample/trades.csv")
        _main_oos_trades = report_dir / "out_of_sample" / "trades.csv"
        # Derive basin-trials parquet (per-trial Sharpe) from OOF candle-return parquet.
        _basin_trials_parquet = Path("data") / f"v1_iter_{iteration_label}_basin_trials.parquet"
        _basin_trials_parquet.unlink(missing_ok=True)
        derive_basin_trials_from_oof_parquet(
            OOF_PARQUET_PATH,
            _basin_trials_parquet,
            outer_seed=ensemble_seeds_offset,  # encode outer seed offset as seed label
            model_name=iteration_label,
        )
        emit_basin_diagnostics_summary(
            diagnostics_dir=_diagnostics_dir,
            trials_parquet=_basin_trials_parquet,
            main_trades_oos=_main_oos_trades,
            baseline_trades_oos=_baseline_oos_trades,
            symbols=list(symbols),
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
    #
    # Bug fix (2026-05-29): when --seeds N > 1, the main process (seed 0) runs here
    # as the canonical outer-seed pass.  Its reports will be moved to seed_42/ below,
    # and the engineering_report.md is created SEPARATELY by the orchestrator after all
    # seeds complete.  Suppress the FATAL exit for multi-seed runs (same effect as
    # --no-engineering-report, but automatic — avoids requiring the caller to remember
    # the flag when also passing --seeds N).
    _n_outer_seeds_peek = int(getattr(args, "seeds", 1))
    _suppress_eng_report_check = args.no_engineering_report or (_n_outer_seeds_peek > 1)
    engineering_report_path = report_dir / "engineering_report.md"
    if not engineering_report_path.exists() and not _suppress_eng_report_check:
        print(
            f"\n[FATAL] engineering_report.md NOT FOUND at {engineering_report_path}",
            file=sys.stderr,
        )
        print(
            "[FATAL] This file is a BLOCKING deliverable for Phase 7.5 dispatch.\n"
            "[FATAL] Use --no-engineering-report to suppress this exit "
            "(e.g. mid-pipeline orchestration).\n"
            "[FATAL] When using --seeds N > 1, this check is auto-suppressed for the "
            "main (seed 0) pass — sub-runs already pass --no-engineering-report.",
            file=sys.stderr,
        )
        sys.exit(1)

    # -------------------------------------------------------------------------
    # framework/032+: multi-outer-seed statistical validation (Component 1).
    #
    # When --seeds N is passed (N > 1), emit a seed_42/ subdirectory for the
    # canonical outer seed (already complete above), then launch N-1 additional
    # subprocess runs with ensemble_seeds_offset=5,10,... each writing to
    # seed_{offset}/ subdirectory.  Finally aggregate into comparison_multi_seed.csv.
    #
    # LIVE-TRADING CONTRACT: seed_42/ is the only path the live engine reads.
    # Multi-outer-seed reports are STATISTICAL VALIDATION artifacts only.
    # The live engine does NOT import basin_diagnostics and does NOT reference
    # the seed_*/ subdirectories.  This contract is audited at framework/032+.
    # -------------------------------------------------------------------------
    n_outer_seeds = int(getattr(args, "seeds", 1))
    auto_frozen_hp = bool(getattr(args, "auto_frozen_hp_control", False))

    if n_outer_seeds > 1 and mode_label != "BASELINE":
        import subprocess  # noqa: PLC0415

        if n_outer_seeds > len(_OUTER_SEED_OFFSETS):
            print(
                f"[multi_seed] WARNING: --seeds {n_outer_seeds} exceeds available "
                f"offset table ({len(_OUTER_SEED_OFFSETS)}). Capping at "
                f"{len(_OUTER_SEED_OFFSETS)}.",
                file=sys.stderr,
            )
            n_outer_seeds = len(_OUTER_SEED_OFFSETS)

        # The main run above used offset=0 → seed_42 (canonical live path).
        # Move its reports to seed_42/ subdirectory.
        seed_42_dir = report_dir / f"seed_{V1_CANONICAL_OUTER_SEED}"
        if not seed_42_dir.exists():
            import shutil  # noqa: PLC0415

            seed_42_dir.mkdir(parents=True, exist_ok=True)
            # Move existing report contents into seed_42/
            for child in list(report_dir.iterdir()):
                if child.name not in (f"seed_{V1_CANONICAL_OUTER_SEED}",):
                    # Skip already-moved items; move everything else
                    try:
                        shutil.move(str(child), str(seed_42_dir / child.name))
                    except Exception as _exc:  # noqa: BLE001
                        print(
                            f"[multi_seed] WARNING: could not move {child} → "
                            f"{seed_42_dir / child.name}: {_exc}",
                            file=sys.stderr,
                        )
        print(f"[multi_seed] Canonical (outer_seed=42 offset=0) reports → {seed_42_dir}")

        # Build CLI args for sub-runs (strip --seeds; add --ensemble-seeds-offset N).
        # We reconstruct sys.argv minus the --seeds flag and any --ensemble-seeds-offset.
        base_argv = [a for a in sys.argv[1:] if a != "--seeds"]
        # Remove any existing --ensemble-seeds-offset args
        _filtered_argv = []
        _skip_next = False
        for _a in base_argv:
            if _skip_next:
                _skip_next = False
                continue
            if _a.startswith("--ensemble-seeds-offset"):
                if "=" not in _a:
                    _skip_next = True
                continue
            _filtered_argv.append(_a)
        base_argv = _filtered_argv

        seed_dirs: list[Path] = [seed_42_dir]

        for seed_idx in range(1, n_outer_seeds):
            offset = _OUTER_SEED_OFFSETS[seed_idx]
            # offset encodes the ensemble_seeds_offset; use it as seed ID label
            seed_label = f"offset{offset}"
            seed_dir = report_dir / f"seed_{seed_label}"
            print(
                f"\n[multi_seed] Launching outer seed {seed_idx + 1}/{n_outer_seeds} "
                f"(offset={offset}) → {seed_dir}"
            )

            # Verify offset+ensemble_size <= len(ENSEMBLE_SEEDS)
            if offset + ensemble_size > len(ENSEMBLE_SEEDS):
                print(
                    f"[multi_seed] WARNING: offset={offset} + ensemble_size={ensemble_size} "
                    f"> {len(ENSEMBLE_SEEDS)} (ENSEMBLE_SEEDS length). Skipping this seed.",
                    file=sys.stderr,
                )
                continue

            sub_argv = [
                sys.executable,
                str(Path(__file__).resolve()),
                *base_argv,
                f"--ensemble-seeds-offset={offset}",
                "--no-engineering-report",  # sub-runs don't need engineering_report
            ]
            # Override output dir — we can't directly override the report dir from
            # CLI, but the sub-run writes to the same iteration label. After it
            # completes we'll move its output from the standard path to seed_dir.
            result_proc = subprocess.run(
                sub_argv,
                capture_output=True,
                text=True,
            )
            print(result_proc.stdout[-4000:] if result_proc.stdout else "(no stdout)")
            if result_proc.returncode != 0:
                print(
                    f"[multi_seed] Sub-run offset={offset} FAILED (rc={result_proc.returncode}). "
                    f"stderr:\n{result_proc.stderr[-2000:]}",
                    file=sys.stderr,
                )
                continue

            # Move the sub-run's standard report_dir to seed_dir
            import shutil as _shutil  # noqa: PLC0415

            sub_report_dir = report_dir  # sub-run writes to same label
            if sub_report_dir.exists():
                seed_dir.mkdir(parents=True, exist_ok=True)
                for _child in list(sub_report_dir.iterdir()):
                    if _child.name.startswith("seed_"):
                        continue  # don't move existing seed dirs
                    try:
                        _shutil.move(str(_child), str(seed_dir / _child.name))
                    except Exception as _exc:  # noqa: BLE001
                        print(
                            f"[multi_seed] WARNING: move failed {_child} → "
                            f"{seed_dir / _child.name}: {_exc}",
                            file=sys.stderr,
                        )
            seed_dirs.append(seed_dir)

        # Aggregate all seed comparison.csv files
        _run_multi_seed_aggregate(report_dir, n_outer_seeds, seed_dirs)

    # -------------------------------------------------------------------------
    # framework/032+: auto-frozen-HP companion run (Component 3).
    #
    # When --auto-frozen-hp-control is passed, after the main backtest completes:
    # 1. Move main reports to <report_dir>/main/
    # 2. Run a second sub-run with --frozen-hp-mode baseline_v1
    # 3. Move frozen-HP reports to <report_dir>/frozen_hp/
    # 4. Emit magnitude_decomposition.json to <report_dir>/
    # -------------------------------------------------------------------------
    if auto_frozen_hp and mode_label not in ("BASELINE",) and frozen_hp_mode_arg == "none":
        import shutil as _shutil2  # noqa: PLC0415
        import subprocess as _subprocess2  # noqa: PLC0415

        frozen_hp_parquet_check = Path("data") / "v1_baseline_frozen_hp.parquet"
        if not frozen_hp_parquet_check.exists():
            print(
                "[auto_frozen_hp] WARNING: data/v1_baseline_frozen_hp.parquet not found. "
                "Skipping auto-frozen-HP companion run. Generate it first with the "
                "baseline frozen-HP extraction script.",
                file=sys.stderr,
            )
        else:
            # 1. Move main run's reports to main/ subdirectory
            main_sub_dir = report_dir / "main"
            main_sub_dir.mkdir(parents=True, exist_ok=True)
            for _child in list(report_dir.iterdir()):
                if _child.name in ("main", "frozen_hp"):
                    continue
                try:
                    _shutil2.move(str(_child), str(main_sub_dir / _child.name))
                except Exception as _exc:  # noqa: BLE001
                    print(
                        f"[auto_frozen_hp] WARNING: move failed {_child} → "
                        f"{main_sub_dir / _child.name}: {_exc}",
                        file=sys.stderr,
                    )
            print(f"[auto_frozen_hp] Main reports moved to {main_sub_dir}")

            # 2. Launch frozen-HP sub-run
            base_argv_fhp = [a for a in sys.argv[1:]]
            # Add --frozen-hp-mode baseline_v1
            base_argv_fhp += ["--frozen-hp-mode", "baseline_v1"]
            # Remove --auto-frozen-hp-control to avoid infinite recursion
            base_argv_fhp = [a for a in base_argv_fhp if a != "--auto-frozen-hp-control"]

            print(
                "\n[auto_frozen_hp] Launching frozen-HP companion run "
                "(--frozen-hp-mode baseline_v1)..."
            )
            fhp_proc = _subprocess2.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *base_argv_fhp,
                    "--no-engineering-report",
                ],
                capture_output=True,
                text=True,
            )
            print(fhp_proc.stdout[-4000:] if fhp_proc.stdout else "(no stdout)")
            if fhp_proc.returncode != 0:
                print(
                    f"[auto_frozen_hp] Frozen-HP sub-run FAILED (rc={fhp_proc.returncode}). "
                    f"stderr:\n{fhp_proc.stderr[-2000:]}",
                    file=sys.stderr,
                )
            else:
                # 3. Move frozen-HP reports to frozen_hp/ subdirectory
                fhp_sub_dir = report_dir / "frozen_hp"
                fhp_sub_dir.mkdir(parents=True, exist_ok=True)
                for _child in list(report_dir.iterdir()):
                    if _child.name in ("main", "frozen_hp"):
                        continue
                    try:
                        _shutil2.move(str(_child), str(fhp_sub_dir / _child.name))
                    except Exception as _exc:  # noqa: BLE001
                        print(
                            f"[auto_frozen_hp] WARNING: move failed {_child} → "
                            f"{fhp_sub_dir / _child.name}: {_exc}",
                            file=sys.stderr,
                        )
                print(f"[auto_frozen_hp] Frozen-HP reports moved to {fhp_sub_dir}")

                # 4. Compute and emit magnitude decomposition
                main_sharpe = _compute_comparison_sharpe(main_sub_dir / "comparison.csv")
                fhp_sharpe = _compute_comparison_sharpe(fhp_sub_dir / "comparison.csv")
                # Baseline OOS Sharpe is read from BASELINE_V1.md comparison.csv if available
                baseline_report = Path("reports-v1/iteration_v1-baseline/comparison.csv")
                baseline_sharpe = _compute_comparison_sharpe(baseline_report)

                _emit_magnitude_decomposition(
                    report_dir,
                    main_oos_sharpe=main_sharpe,
                    frozen_hp_oos_sharpe=fhp_sharpe,
                    baseline_oos_sharpe=baseline_sharpe,
                )


if __name__ == "__main__":
    main()
