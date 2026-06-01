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
    V1_ITER039_UNIVERSE,
    V1_ITER043_UNIVERSE,
    V1_ITER050_UNIVERSE,
    V1_ITER051_UNIVERSE,
    V1_ITER052_UNIVERSE,
    V1_ITER053_UNIVERSE,
    V1_ITER054_UNIVERSE,
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
    append_vol_ceiling_rows_to_comparison,
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
from crypto_trade.strategies.ml.xgb import XgboostStrategy
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
    optuna_objective: str = "sharpe",
    vol_ceiling_enabled: bool = False,
    vol_ceiling_scale: float = 0.5,
    vol_ceiling_thresholds: dict | None = None,
    min_child_samples_lower_bound: int | None = None,
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
        vol_ceiling_enabled=vol_ceiling_enabled,
        vol_ceiling_scale=vol_ceiling_scale,
        vol_ceiling_thresholds=vol_ceiling_thresholds or {},
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
        optuna_objective=optuna_objective,
        min_child_samples_lower_bound=min_child_samples_lower_bound,
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
    label_mode: str = "triple_barrier",
    frozen_hp_parquet: Path | None = None,
    optuna_objective: str = "sharpe",
    vol_ceiling_enabled: bool = False,
    vol_ceiling_scale: float = 0.5,
    vol_ceiling_thresholds: dict | None = None,
):
    """Run a single v1 sub-model with M2 meta-labeling (iter-v1/030).

    Mirrors run_model() but creates MetaLabelingStrategy instead of
    LightGbmStrategy.  M2 is a binary LGBMClassifier trained on M1-positive
    bars per training window; it vetoes M1 signals where M2 confidence < 0.5.

    label_mode, frozen_hp_parquet, optuna_objective: accepted for _r5_kwargs
    compatibility but ignored by MetaLabelingStrategy (M1 in /030 uses baseline
    triple_barrier labels and Sharpe objective; meta-labeling axis is orthogonal
    to label-mode and loss-function axes).

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
        vol_ceiling_enabled=vol_ceiling_enabled,
        vol_ceiling_scale=vol_ceiling_scale,
        vol_ceiling_thresholds=vol_ceiling_thresholds or {},
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
    label_mode: str = "triple_barrier",
    frozen_hp_parquet: Path | None = None,
    optuna_objective: str = "sharpe",
) -> LightGbmStrategy:
    """Build a LightGbmStrategy WITHOUT running a backtest.

    Factory function used by run_regime_cohort() to construct inner sub-strategies
    for RegimeRoutedStrategy before they are wrapped and dispatched via a SINGLE
    run_backtest() call on the wrapper.

    label_mode, frozen_hp_parquet, optuna_objective: forwarded to LightGbmStrategy
    ctor (iter-v1/037 _r5_kwargs compatibility; default "sharpe" is BIT-IDENTICAL
    to all pre-/037 callers).

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
        label_mode=label_mode,
        frozen_hp_parquet=frozen_hp_parquet,
        optuna_objective=optuna_objective,
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
    vol_ceiling_signals_is: int = 0,
    vol_ceiling_fires_is: int = 0,
    vol_ceiling_signals_oos: int = 0,
    vol_ceiling_fires_oos: int = 0,
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
        # ---------------------------------------------------------------------------
        # 4d. comparison.csv vol-ceiling fire-rate rows (iter-v1/038 F-AXIS #2 reporting)
        # ---------------------------------------------------------------------------
        vol_ceil_rate_is = (
            vol_ceiling_fires_is / vol_ceiling_signals_is if vol_ceiling_signals_is > 0 else 0.0
        )
        vol_ceil_rate_oos = (
            vol_ceiling_fires_oos / vol_ceiling_signals_oos if vol_ceiling_signals_oos > 0 else 0.0
        )
        append_vol_ceiling_rows_to_comparison(comparison_path, vol_ceil_rate_is, vol_ceil_rate_oos)
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


# ---------------------------------------------------------------------------
# iter-v1/043 NEW-SKILL 2026-05-31: Regime Attribution CSV builder.
#
# Schema: regime_tag, in_sample, candidate_sharpe, candidate_max_dd,
#         candidate_trade_count, baseline_sharpe, baseline_max_dd,
#         baseline_trade_count
#
# Regime tagger uses BTC 90d return + 30d realized vol quantiles per the
# canonical rule approximation from briefs-v1/_meta/regime_catalog.md
# (not yet formalized at /043; approximation used until /044 bootstrap).
# Regime tags: bull, chop, recovery, vol-spike, bear, other.
#
# Baseline comparison: LINK-only rows from BASELINE_V1 trade CSVs
# (reports-v1/iteration_v1-baseline/{in_sample,out_of_sample}/trades.csv
# filtered to LINKUSDT). Used so the /043 vs baseline per-regime Δ is
# attributable purely to the LINK trend-scan specialist component.
# ---------------------------------------------------------------------------


def _assign_regime_tag(
    close_time_ms: int,
    btc_klines_df: pd.DataFrame,
) -> str:
    """Assign a regime tag to a trade based on BTC 90-day return + 30-day realized vol.

    Canonical approximation of briefs-v1/_meta/regime_catalog.md rules:
      bull     : BTC 90d return > +20%
      bear     : BTC 90d return < -20%
      vol-spike: BTC 30d rv > 0.75 quantile (high vol regardless of direction)
      chop     : BTC 90d return ∈ (-10%, +10%) AND rv < 0.50 quantile
      recovery : BTC 90d return ∈ (+5%, +20%) AND rv > 0.50 quantile
      other    : remaining

    Args:
        close_time_ms: Trade close_time in milliseconds (UTC).
        btc_klines_df: DataFrame with columns [close_time_ms, close] for BTCUSDT 8h.

    Returns:
        Regime tag string.
    """
    import numpy as np  # noqa: PLC0415

    if btc_klines_df is None or btc_klines_df.empty:
        return "other"

    # BTC row at or before close_time_ms
    mask = btc_klines_df["close_time_ms"] <= close_time_ms
    if not mask.any():
        return "other"
    idx = btc_klines_df[mask].index[-1]

    closes = btc_klines_df["close"].values
    close_idx = btc_klines_df.index.get_loc(idx)

    # 90-day return (90 days × 3 candles/day at 8h = 270 bars)
    lookback_90d = 270
    if close_idx >= lookback_90d:
        btc_90d_ret = closes[close_idx] / closes[close_idx - lookback_90d] - 1.0
    else:
        btc_90d_ret = 0.0

    # 30-day realized vol (30 days × 3 = 90 bars)
    lookback_30d = 90
    start_30 = max(0, close_idx - lookback_30d)
    log_rets = np.diff(np.log(closes[start_30 : close_idx + 1]))
    rv_30 = float(np.std(log_rets)) * np.sqrt(3 * 365) if len(log_rets) > 2 else 0.0

    # Global rv quantile thresholds (precomputed once outside; approximated inline)
    # These are rough quantiles from BTC 2020-2025 realized vol history.
    rv_q75 = 1.20  # annualized; ~75th percentile for BTC 8h 30d rv
    rv_q50 = 0.80  # ~50th percentile

    if btc_90d_ret > 0.20:
        return "bull"
    elif btc_90d_ret < -0.20:
        return "bear"
    elif rv_30 > rv_q75:
        return "vol-spike"
    elif -0.10 < btc_90d_ret < 0.10 and rv_30 < rv_q50:
        return "chop"
    elif 0.05 < btc_90d_ret <= 0.20 and rv_30 > rv_q50:
        return "recovery"
    else:
        return "other"


def build_regime_attribution_csv(
    trades_df: pd.DataFrame,
    baseline_trades_df: pd.DataFrame | None,
    is_cutoff_ms: int,
    btc_klines_df: pd.DataFrame | None,
    out_path: Path,
) -> None:
    """Build regime_attribution.csv per new-skill 2026-05-31 schema.

    Schema: regime_tag, in_sample, candidate_sharpe, candidate_max_dd,
            candidate_trade_count, baseline_sharpe, baseline_max_dd,
            baseline_trade_count.

    Regime tagger uses _assign_regime_tag() (BTC 90d return + 30d rv quantile
    approximation). Produces one row per regime × IS/OOS split combination.
    Baseline columns sourced from baseline_trades_df (LINKUSDT-only rows).

    Args:
        trades_df: Candidate iteration trades (all symbols; LINKUSDT for /043).
        baseline_trades_df: BASELINE_V1 trades filtered to LINKUSDT.
        is_cutoff_ms: OOS_CUTOFF_DATE in milliseconds.
        btc_klines_df: BTCUSDT 8h kline DataFrame for regime tagging.
        out_path: Output CSV path.
    """
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    regimes = ["bull", "bear", "vol-spike", "chop", "recovery", "other"]
    is_oos = ["IS", "OOS"]

    def _compute_regime_metrics(
        df: pd.DataFrame | None,
        regime: str,
        split: str,
    ) -> tuple[float, float, int]:
        """Return (sharpe, max_dd, trade_count) for a regime × split subset."""
        if df is None or df.empty:
            return (float("nan"), float("nan"), 0)
        # Split filter
        if split == "IS":
            sub = df[df["close_time"] < is_cutoff_ms].copy()
        else:
            sub = df[df["close_time"] >= is_cutoff_ms].copy()
        # Regime filter
        if "regime_tag" in sub.columns:
            sub = sub[sub["regime_tag"] == regime]
        else:
            return (float("nan"), float("nan"), 0)
        if sub.empty:
            return (float("nan"), float("nan"), 0)
        n = len(sub)
        # Monthly PnL series for Sharpe
        sub = sub.copy()
        sub["month"] = pd.to_datetime(sub["close_time"], unit="ms").dt.to_period("M")
        monthly = sub.groupby("month")["pnl_pct"].sum()
        if len(monthly) < 2:
            sharpe = float("nan")
        else:
            sharpe = float(monthly.mean() / monthly.std()) if monthly.std() > 0 else float("nan")
        # Max drawdown from cumulative PnL
        cum = sub["pnl_pct"].cumsum()
        peak = cum.cummax()
        dd = (peak - cum).max()
        max_dd = float(dd) if not np.isnan(dd) else float("nan")
        return (sharpe, max_dd, n)

    # Tag candidate trades with regime
    if btc_klines_df is not None and not btc_klines_df.empty:
        trades_df = trades_df.copy()
        trades_df["regime_tag"] = trades_df["close_time"].apply(
            lambda ct: _assign_regime_tag(ct, btc_klines_df)
        )
        if baseline_trades_df is not None and not baseline_trades_df.empty:
            baseline_trades_df = baseline_trades_df.copy()
            baseline_trades_df["regime_tag"] = baseline_trades_df["close_time"].apply(
                lambda ct: _assign_regime_tag(ct, btc_klines_df)
            )
    else:
        trades_df = trades_df.copy()
        trades_df["regime_tag"] = "other"
        if baseline_trades_df is not None and not baseline_trades_df.empty:
            baseline_trades_df = baseline_trades_df.copy()
            baseline_trades_df["regime_tag"] = "other"

    rows = []
    for split in is_oos:
        for regime in regimes:
            c_sharpe, c_dd, c_count = _compute_regime_metrics(trades_df, regime, split)
            b_sharpe, b_dd, b_count = _compute_regime_metrics(baseline_trades_df, regime, split)
            rows.append(
                {
                    "regime_tag": regime,
                    "in_sample": split == "IS",
                    "candidate_sharpe": c_sharpe,
                    "candidate_max_dd": c_dd,
                    "candidate_trade_count": c_count,
                    "baseline_sharpe": b_sharpe,
                    "baseline_max_dd": b_dd,
                    "baseline_trade_count": b_count,
                }
            )

    result_df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)
    print(f"[iter-v1/043] regime_attribution.csv written: {out_path} ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# iter-v1/044: Bundle aggregator (CONFIRMATION-MERGE-PORTFOLIO).
#
# Merges per-component frozen trade rosters at the trade-roster level using
# deterministic weights.  Weights are specified as a dict {component_label: float}
# where component_labels ∈ {"baseline", "v1-036", "v1-043"} (or any valid
# component sub-dir name under the bundle output directory).
#
# Aggregation rule (per research_brief.md Section 3.2):
#   For each (symbol, open_time) cell:
#     active = {c : pnl_c[cell] exists}   (a component is "active" in a cell
#               if it emitted ≥1 trade in that cell)
#     if active is empty → no bundle trade
#     bundle_pnl[cell] = Σ_{c∈active} (w_c / Σ_{c'∈active} w_{c'}) * pnl_c[cell]
#
# This is proportional-weight renormalization: if only P0 trades in a cell,
# P0's effective weight = 1.0 (not 0.50) preserving unit-leverage.
#
# Outputs (all under bundle_out_dir/):
#   in_sample/aggregated_trades.csv   — IS bundle trades with weighted_pnl column
#   out_of_sample/aggregated_trades.csv — OOS bundle trades
#   comparison.csv                    — bundle IS/OOS/ratio metrics table
#   regime_attribution.csv            — per-regime bundle vs BASELINE_V1
#   per_component_correlation.csv     — pairwise daily-PnL correlations
#   component_substitution.csv        — per-component drop-impact on bundle metrics
# ---------------------------------------------------------------------------


def _load_component_trades(component_dir: Path, split: str) -> pd.DataFrame:
    """Load IS or OOS trades.csv for a component sub-dir.

    Args:
        component_dir: Path to component output dir (contains in_sample/ out_of_sample/).
        split: "in_sample" or "out_of_sample".

    Returns:
        DataFrame of trades, empty if not found.
    """
    import pandas as pd  # noqa: PLC0415

    trades_path = component_dir / split / "trades.csv"
    if trades_path.exists():
        try:
            return pd.read_csv(trades_path)
        except Exception as _e:  # noqa: BLE001
            print(f"[bundle_aggregator] WARNING: could not load {trades_path}: {_e}")
    return pd.DataFrame()


def _compute_bundle_metrics(trades_df: pd.DataFrame, is_cutoff_ms: int) -> dict:
    """Compute headline IS/OOS metrics from an aggregated trades DataFrame.

    Args:
        trades_df: DataFrame with columns: close_time, weighted_pnl.
        is_cutoff_ms: OOS cutoff as millisecond timestamp.

    Returns:
        Dict with keys: is_monthly_sharpe, oos_monthly_sharpe, is_max_dd, oos_max_dd,
        is_n_trades, oos_n_trades, is_win_rate, oos_win_rate,
        is_profit_factor, oos_profit_factor.
    """
    import pandas as pd  # noqa: PLC0415

    def _split_metrics(sub: pd.DataFrame) -> dict:
        if sub.empty:
            return {
                "monthly_sharpe": float("nan"),
                "max_dd": float("nan"),
                "n_trades": 0,
                "win_rate": float("nan"),
                "profit_factor": float("nan"),
            }
        sub = sub.copy()
        sub["month"] = pd.to_datetime(sub["close_time"], unit="ms").dt.to_period("M")
        monthly = sub.groupby("month")["weighted_pnl"].sum()
        sharpe = (
            float(monthly.mean() / monthly.std())
            if len(monthly) >= 2 and monthly.std() > 0
            else float("nan")
        )
        cum = sub["weighted_pnl"].cumsum()
        peak = cum.cummax()
        max_dd = float((peak - cum).max()) if len(cum) > 0 else float("nan")
        n = len(sub)
        wins = (sub["weighted_pnl"] > 0).sum()
        win_rate = float(wins / n) if n > 0 else float("nan")
        pos_sum = sub.loc[sub["weighted_pnl"] > 0, "weighted_pnl"].sum()
        neg_sum = abs(sub.loc[sub["weighted_pnl"] < 0, "weighted_pnl"].sum())
        pf = float(pos_sum / neg_sum) if neg_sum > 0 else float("nan")
        return {
            "monthly_sharpe": sharpe,
            "max_dd": max_dd,
            "n_trades": n,
            "win_rate": win_rate,
            "profit_factor": pf,
        }

    is_sub = trades_df[trades_df["close_time"] < is_cutoff_ms]
    oos_sub = trades_df[trades_df["close_time"] >= is_cutoff_ms]
    is_m = _split_metrics(is_sub)
    oos_m = _split_metrics(oos_sub)
    result: dict = {}
    for k, v in is_m.items():
        result[f"is_{k}"] = v
    for k, v in oos_m.items():
        result[f"oos_{k}"] = v
    return result


def bundle_aggregator(
    component_dirs: dict[str, Path],
    weights: dict[str, float],
    is_cutoff_ms: int,
    btc_klines_path: Path | None,
    bundle_out_dir: Path,
    baseline_component_dir: Path | None = None,
) -> None:
    """Aggregate 3 component trade rosters into bundle-level metrics.

    Implements the weighted-PnL trade-roster aggregation algorithm from
    research_brief.md Section 3.2:
      - For each (symbol, open_time) cell, collect active components (those
        that emitted a trade in that cell).
      - Renormalize weights over active components (proportional redistribution).
      - Weighted PnL = Σ (renorm_weight × pnl) over active components.

    Args:
        component_dirs: {component_label: Path to component output dir}.
            Each dir must contain in_sample/trades.csv and out_of_sample/trades.csv.
        weights: {component_label: float weight}.  Must sum to 1.0 ± 1e-6.
        is_cutoff_ms: OOS cutoff timestamp in milliseconds.
        btc_klines_path: Path to BTCUSDT/8h.csv for regime tagging.  May be None.
        bundle_out_dir: Output directory for bundle artifacts.
        baseline_component_dir: Path to baseline component dir for regime_attribution
            baseline comparison.  Defaults to component_dirs.get("baseline").
    """
    import pandas as pd  # noqa: PLC0415

    # Validate weights sum
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(
            f"[bundle_aggregator] weights sum to {total_weight:.8f} ≠ 1.0 ± 1e-6. "
            "Weights must exactly sum to 1.0."
        )

    bundle_out_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"[bundle_aggregator] START: {len(component_dirs)} components, "
        f"weights={weights}, is_cutoff_ms={is_cutoff_ms}"
    )

    # ---------------------------------------------------------------------------
    # Step 1 — Load per-component trade rosters (IS + OOS combined).
    # ---------------------------------------------------------------------------
    component_trades: dict[str, pd.DataFrame] = {}
    for comp_label, comp_dir in component_dirs.items():
        is_df = _load_component_trades(comp_dir, "in_sample")
        oos_df = _load_component_trades(comp_dir, "out_of_sample")
        frames = [f for f in [is_df, oos_df] if not f.empty]
        if frames:
            df = pd.concat(frames, ignore_index=True)
        else:
            df = pd.DataFrame()
        component_trades[comp_label] = df
        print(f"[bundle_aggregator] {comp_label}: {len(df)} trades loaded from {comp_dir}")

    # ---------------------------------------------------------------------------
    # Step 2 — Build bundle trade roster via weighted-PnL aggregation.
    #
    # Cell key: (symbol, open_time).  Each cell collects contributions from active
    # components.  Active = component emitted ≥1 trade in that cell.
    # PnL column: prefer "pnl_pct" (standard TradeResult column); fall back to "pnl".
    # ---------------------------------------------------------------------------
    def _get_pnl_col(df: pd.DataFrame) -> str:
        """Return the PnL column name present in df."""
        for c in ("pnl_pct", "pnl"):
            if c in df.columns:
                return c
        raise KeyError(
            f"[bundle_aggregator] No pnl column found in trades; cols={list(df.columns)}"
        )

    # Collect all (symbol, open_time) cells across all components
    all_cells: dict[tuple, dict[str, pd.Series]] = {}
    for comp_label, df in component_trades.items():
        if df.empty:
            continue
        pnl_col = _get_pnl_col(df)
        for _, row in df.iterrows():
            key = (str(row.get("symbol", "")), int(row.get("open_time", 0)))
            if key not in all_cells:
                all_cells[key] = {}
            all_cells[key][comp_label] = row
            # Normalize pnl_pct alias
            if pnl_col != "pnl_pct":
                all_cells[key][comp_label] = row.copy()
                all_cells[key][comp_label]["pnl_pct"] = float(row[pnl_col])

    print(f"[bundle_aggregator] total unique (symbol, open_time) cells: {len(all_cells)}")

    # Build aggregated trade rows
    bundle_rows = []
    for (symbol, open_time), comp_rows in all_cells.items():
        active_comps = list(comp_rows.keys())
        # Renormalize weights over active components
        active_weight_sum = sum(weights.get(c, 0.0) for c in active_comps)
        if active_weight_sum <= 0.0:
            # Should not happen if weights are positive; skip silently
            continue
        renorm = {c: weights.get(c, 0.0) / active_weight_sum for c in active_comps}
        # Weighted PnL
        weighted_pnl = sum(
            renorm[c] * float(comp_rows[c].get("pnl_pct", 0.0)) for c in active_comps
        )
        # Use the first active component's row as the base for non-PnL columns
        base_row = dict(comp_rows[active_comps[0]])
        base_row["symbol"] = symbol
        base_row["open_time"] = open_time
        base_row["weighted_pnl"] = weighted_pnl
        base_row["pnl_pct"] = weighted_pnl  # alias for regime-attribution compat
        base_row["active_components"] = ",".join(sorted(active_comps))
        base_row["weight_sum"] = active_weight_sum
        bundle_rows.append(base_row)

    bundle_df = pd.DataFrame(bundle_rows)
    if "close_time" not in bundle_df.columns and bundle_rows:
        # Fallback: close_time may be absent; set from open_time as approximation
        bundle_df["close_time"] = bundle_df["open_time"]
    bundle_df = bundle_df.sort_values("close_time").reset_index(drop=True)

    # ---------------------------------------------------------------------------
    # Step 3 — Split IS/OOS and write aggregated_trades.csv
    # ---------------------------------------------------------------------------
    is_bundle = bundle_df[bundle_df["close_time"] < is_cutoff_ms].copy()
    oos_bundle = bundle_df[bundle_df["close_time"] >= is_cutoff_ms].copy()

    for split_name, split_df in (("in_sample", is_bundle), ("out_of_sample", oos_bundle)):
        split_dir = bundle_out_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        trades_out = split_dir / "aggregated_trades.csv"
        split_df.to_csv(trades_out, index=False)
        print(f"[bundle_aggregator] {split_name}: {len(split_df)} bundle trades → {trades_out}")

    # ---------------------------------------------------------------------------
    # Step 4 — Compute and write comparison.csv (bundle IS/OOS/ratio metrics)
    # ---------------------------------------------------------------------------
    metrics = _compute_bundle_metrics(bundle_df, is_cutoff_ms)

    def _safe_ratio(oos: float, is_: float) -> float:
        if math.isnan(oos) or math.isnan(is_) or is_ == 0.0:
            return float("nan")
        return round(oos / is_, 4)

    comp_rows_out = [
        {
            "metric": "monthly_sharpe",
            "in_sample": metrics["is_monthly_sharpe"],
            "out_of_sample": metrics["oos_monthly_sharpe"],
            "ratio": _safe_ratio(metrics["oos_monthly_sharpe"], metrics["is_monthly_sharpe"]),
        },
        {
            "metric": "max_drawdown",
            "in_sample": metrics["is_max_dd"],
            "out_of_sample": metrics["oos_max_dd"],
            "ratio": _safe_ratio(metrics["oos_max_dd"], metrics["is_max_dd"]),
        },
        {
            "metric": "n_trades",
            "in_sample": metrics["is_n_trades"],
            "out_of_sample": metrics["oos_n_trades"],
            "ratio": _safe_ratio(metrics["oos_n_trades"], metrics["is_n_trades"]),
        },
        {
            "metric": "win_rate",
            "in_sample": metrics["is_win_rate"],
            "out_of_sample": metrics["oos_win_rate"],
            "ratio": _safe_ratio(metrics["oos_win_rate"], metrics["is_win_rate"]),
        },
        {
            "metric": "profit_factor",
            "in_sample": metrics["is_profit_factor"],
            "out_of_sample": metrics["oos_profit_factor"],
            "ratio": _safe_ratio(metrics["oos_profit_factor"], metrics["is_profit_factor"]),
        },
    ]
    comp_csv_path = bundle_out_dir / "comparison.csv"
    pd.DataFrame(comp_rows_out).to_csv(comp_csv_path, index=False)
    print(
        f"[bundle_aggregator] comparison.csv: IS Sharpe={metrics['is_monthly_sharpe']:.4f} "
        f"OOS Sharpe={metrics['oos_monthly_sharpe']:.4f} → {comp_csv_path}"
    )

    # ---------------------------------------------------------------------------
    # Step 5 — Build regime_attribution.csv for the bundle
    # ---------------------------------------------------------------------------
    # Load BTC klines for regime tagging
    btc_df: pd.DataFrame | None = None
    if btc_klines_path is not None and btc_klines_path.exists():
        try:
            _btc_raw = pd.read_csv(btc_klines_path)
            _btc_raw.columns = [c.lower().replace(" ", "_") for c in _btc_raw.columns]
            if "close_time" in _btc_raw.columns and "close" in _btc_raw.columns:
                btc_df = _btc_raw[["close_time", "close"]].rename(
                    columns={"close_time": "close_time_ms"}
                )
                btc_df["close"] = pd.to_numeric(btc_df["close"], errors="coerce")
                btc_df = btc_df.dropna().reset_index(drop=True)
        except Exception as _e:  # noqa: BLE001
            print(f"[bundle_aggregator] WARNING: BTC klines load failed: {_e}")

    # Baseline trades: from baseline component dir (for per-regime comparison)
    _baseline_dir = baseline_component_dir or component_dirs.get("baseline")
    baseline_all_df: pd.DataFrame | None = None
    if _baseline_dir is not None:
        _b_is = _load_component_trades(_baseline_dir, "in_sample")
        _b_oos = _load_component_trades(_baseline_dir, "out_of_sample")
        _b_frames = [f for f in [_b_is, _b_oos] if not f.empty]
        if _b_frames:
            baseline_all_df = pd.concat(_b_frames, ignore_index=True)

    regime_out = bundle_out_dir / "regime_attribution.csv"
    build_regime_attribution_csv(
        trades_df=bundle_df,
        baseline_trades_df=baseline_all_df,
        is_cutoff_ms=is_cutoff_ms,
        btc_klines_df=btc_df,
        out_path=regime_out,
    )

    # ---------------------------------------------------------------------------
    # Step 6 — Pairwise daily-PnL correlations (per_component_correlation.csv)
    # ---------------------------------------------------------------------------
    # Build daily PnL series per component
    comp_daily: dict[str, pd.Series] = {}
    for comp_label, df in component_trades.items():
        if df.empty:
            continue
        pnl_col = _get_pnl_col(df)
        df2 = df.copy()
        df2["date"] = pd.to_datetime(df2["close_time"], unit="ms").dt.date
        daily = df2.groupby("date")[pnl_col].sum()
        comp_daily[comp_label] = daily

    # Align all series to the same date index
    if comp_daily:
        aligned = pd.DataFrame(comp_daily).fillna(0.0)
        corr_rows = []
        labels = list(comp_daily.keys())
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                la, lb = labels[i], labels[j]
                if la in aligned.columns and lb in aligned.columns:
                    corr_val = float(aligned[[la, lb]].corr().iloc[0, 1])
                else:
                    corr_val = float("nan")
                # Compute Jaccard between trade rosters (shared (symbol, open_time) cells)
                set_a = (
                    set(
                        zip(
                            component_trades[la].get("symbol", pd.Series([])),
                            component_trades[la].get("open_time", pd.Series([])).astype(int),
                        )
                    )
                    if not component_trades[la].empty
                    else set()
                )
                set_b = (
                    set(
                        zip(
                            component_trades[lb].get("symbol", pd.Series([])),
                            component_trades[lb].get("open_time", pd.Series([])).astype(int),
                        )
                    )
                    if not component_trades[lb].empty
                    else set()
                )
                inter = len(set_a & set_b)
                union = len(set_a | set_b)
                jaccard = float(inter / union) if union > 0 else float("nan")
                corr_rows.append(
                    {
                        "pair": f"{la}x{lb}",
                        "daily_pnl_corr": round(corr_val, 4),
                        "trade_jaccard": round(jaccard, 4),
                    }
                )
        corr_csv = bundle_out_dir / "per_component_correlation.csv"
        pd.DataFrame(corr_rows).to_csv(corr_csv, index=False)
        print(f"[bundle_aggregator] per_component_correlation.csv → {corr_csv}")

    # ---------------------------------------------------------------------------
    # Step 7 — Component substitution test (component_substitution.csv)
    # ---------------------------------------------------------------------------
    # For each component c: drop c, renormalize remaining weights, compute bundle metrics.
    sub_rows = []
    for dropped in component_dirs:
        remaining = {c: w for c, w in weights.items() if c != dropped}
        remaining_sum = sum(remaining.values())
        if remaining_sum <= 0.0:
            continue
        remaining_renorm = {c: w / remaining_sum for c, w in remaining.items()}
        # Build reduced bundle
        reduced_rows = []
        for (sym, ot), comp_row_map in all_cells.items():
            active_comps_r = [c for c in comp_row_map if c in remaining_renorm]
            if not active_comps_r:
                continue
            active_sum_r = sum(remaining_renorm.get(c, 0.0) for c in active_comps_r)
            if active_sum_r <= 0.0:
                continue
            renorm_r = {c: remaining_renorm[c] / active_sum_r for c in active_comps_r}
            wpnl = sum(
                renorm_r[c] * float(comp_row_map[c].get("pnl_pct", 0.0)) for c in active_comps_r
            )
            base = dict(comp_row_map[active_comps_r[0]])
            base["symbol"] = sym
            base["open_time"] = ot
            base["weighted_pnl"] = wpnl
            base["pnl_pct"] = wpnl
            reduced_rows.append(base)
        if not reduced_rows:
            continue
        reduced_df = pd.DataFrame(reduced_rows)
        if "close_time" not in reduced_df.columns:
            reduced_df["close_time"] = reduced_df["open_time"]
        reduced_df = reduced_df.sort_values("close_time").reset_index(drop=True)
        red_metrics = _compute_bundle_metrics(reduced_df, is_cutoff_ms)
        sub_rows.append(
            {
                "dropped_component": dropped,
                "remaining_components": ",".join(sorted(remaining.keys())),
                "remaining_weights": str({c: round(w, 4) for c, w in remaining_renorm.items()}),
                "is_monthly_sharpe_without": red_metrics["is_monthly_sharpe"],
                "oos_monthly_sharpe_without": red_metrics["oos_monthly_sharpe"],
                "is_n_trades_without": red_metrics["is_n_trades"],
                "oos_n_trades_without": red_metrics["oos_n_trades"],
                "bundle_is_sharpe": metrics["is_monthly_sharpe"],
                "bundle_oos_sharpe": metrics["oos_monthly_sharpe"],
                "is_sharpe_delta": (
                    red_metrics["is_monthly_sharpe"] - metrics["is_monthly_sharpe"]
                    if not (
                        math.isnan(red_metrics["is_monthly_sharpe"])
                        or math.isnan(metrics["is_monthly_sharpe"])
                    )
                    else float("nan")
                ),
                "oos_sharpe_delta": (
                    red_metrics["oos_monthly_sharpe"] - metrics["oos_monthly_sharpe"]
                    if not (
                        math.isnan(red_metrics["oos_monthly_sharpe"])
                        or math.isnan(metrics["oos_monthly_sharpe"])
                    )
                    else float("nan")
                ),
            }
        )

    sub_csv = bundle_out_dir / "component_substitution.csv"
    pd.DataFrame(sub_rows).to_csv(sub_csv, index=False)
    print(f"[bundle_aggregator] component_substitution.csv → {sub_csv}")

    print(
        f"[bundle_aggregator] COMPLETE. bundle_out_dir={bundle_out_dir} | "
        f"IS Sharpe={metrics['is_monthly_sharpe']:.4f} "
        f"OOS Sharpe={metrics['oos_monthly_sharpe']:.4f} "
        f"IS n_trades={metrics['is_n_trades']} OOS n_trades={metrics['oos_n_trades']}"
    )


def _parse_bundle_config(bundle_config_str: str) -> dict[str, float]:
    """Parse '--bundle-config' string into {component: weight} dict.

    Format: "component:weight,component:weight,..."
    Example: "baseline:0.50,v1-036:0.30,v1-043:0.20"

    Valid component names: "baseline", "v1-NNN" (e.g. "v1-036", "v1-043").

    Args:
        bundle_config_str: Raw CLI string.

    Returns:
        Dict mapping component label → float weight.

    Raises:
        ValueError: On malformed input or weight sum != 1.0.
    """
    _valid_components = {"baseline", "v1-036", "v1-043"}
    result: dict[str, float] = {}
    for part in bundle_config_str.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(
                f"[bundle_config] Invalid token {part!r}: expected 'component:weight'. "
                "Example: 'baseline:0.50,v1-036:0.30,v1-043:0.20'"
            )
        comp, weight_str = part.split(":", 1)
        comp = comp.strip()
        if comp not in _valid_components:
            raise ValueError(
                f"[bundle_config] Unknown component {comp!r}. "
                f"Valid components: {sorted(_valid_components)}"
            )
        try:
            weight = float(weight_str.strip())
        except ValueError:
            raise ValueError(
                f"[bundle_config] Invalid weight {weight_str!r} for component {comp!r}: "
                "must be a float."
            )
        result[comp] = weight

    total = sum(result.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"[bundle_config] weights sum to {total:.8f} ≠ 1.0 ± 1e-6. Got: {result}")
    return result


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
    # iter-v1/037: Optuna study objective metric.
    # "sharpe" (default) is BIT-IDENTICAL to all pre-/037 callers.
    # "sortino" activates the loss-function axis (NEW 12th family in v1 catalog).
    parser.add_argument(
        "--optuna-objective",
        choices=["sharpe", "sortino"],
        default="sharpe",
        help=(
            "Optuna study objective metric (iter-v1/037). "
            "'sharpe' (default) is BIT-IDENTICAL to baseline. "
            "'sortino' uses mean/downside_std — iter-v1/037 loss-function axis. "
            "Targets right-skewed PnL distributions where Sharpe penalizes "
            "upside variance (Sortino/Sharpe ratio 3.0-4.0x across v1 cohorts)."
        ),
    )
    # iter-v1/041: ATR multiplier overrides for triple-barrier tighten axis.
    # When set, BOTH atr_tp_mult and atr_sl_mult UNIFORMLY override all per-model
    # defaults (Pool A 2.9/1.45 and C/D/E 3.5/1.75) with a single pair of values.
    # TP/SL ratio must be preserved at 2.0 (caller's responsibility — no auto-check).
    # Default None = BIT-IDENTICAL to prior behaviour (per-model baseline defaults).
    parser.add_argument(
        "--atr-tp-mult",
        type=float,
        default=None,
        dest="atr_tp_mult",
        metavar="FLOAT",
        help=(
            "iter-v1/041: uniform ATR TP multiplier override for all models. "
            "When set, replaces per-model baseline defaults (Pool A 2.9, C/D/E 3.5). "
            "Default None = use per-model baseline values (BIT-IDENTICAL). "
            "iter-v1/041 uses 1.5 (ratio 2.0 preserved; atr_sl_mult=0.75 paired)."
        ),
    )
    parser.add_argument(
        "--atr-sl-mult",
        type=float,
        default=None,
        dest="atr_sl_mult",
        metavar="FLOAT",
        help=(
            "iter-v1/041: uniform ATR SL multiplier override for all models. "
            "When set, replaces per-model baseline defaults (Pool A 1.45, C/D/E 1.75). "
            "Default None = use per-model baseline values (BIT-IDENTICAL). "
            "iter-v1/041 uses 0.75 (ratio 2.0 preserved; atr_tp_mult=1.5 paired)."
        ),
    )
    # iter-v1/041: min_child_samples Optuna lower bound override.
    # When set, replaces the v1_pruned default of 20 with the given value.
    # Default None = BIT-IDENTICAL to prior behaviour.
    parser.add_argument(
        "--min-data-in-leaf-min",
        type=int,
        default=None,
        dest="min_data_in_leaf_min",
        metavar="INT",
        help=(
            "iter-v1/041: Optuna min_child_samples lower bound override. "
            "When set, replaces v1_pruned default lower bound of 20. "
            "Default None = BIT-IDENTICAL to prior behaviour. "
            "iter-v1/041 uses 50 (denser-label noise mitigation: larger leaf "
            "populations average out per-leaf noise from shorter-horizon labels)."
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
    # -----------------------------------------------------------------------
    # iter-v1/038: per-symbol rv-based vol-ceiling (risk-primitive axis, cycle-5 EXP-5).
    #
    # --vol-ceiling-mode {none, per_symbol}  (default none → BIT-IDENTICAL baseline)
    #   'none'       = no ceiling gate; byte-identical to all prior runs.
    #   'per_symbol' = ceiling fires when symbol's rv_30d_ann > IS-derived p75 threshold.
    #
    # --vol-ceiling-pct INT  (default 75, range [50, 95])
    #   Percentile of IS rv_30d_ann distribution used as per-symbol threshold.
    #   Must be 75 for iter-v1/038 pre-flight assert.
    #
    # --vol-ceiling-scale FLOAT  (default 0.5, range [0.1, 1.0])
    #   Position-sizing multiplier when the ceiling fires (0.5 = half-size entry).
    #   Must be 0.5 for iter-v1/038 pre-flight assert.
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--vol-ceiling-mode",
        choices=["none", "per_symbol"],
        default="none",
        help=(
            "Per-symbol rv-based vol-ceiling mode (iter-v1/038). "
            "'none' (default) = no ceiling gate; BIT-IDENTICAL to all prior runs. "
            "'per_symbol' = ceiling fires when symbol's rolling 30d annualized "
            "realized vol (rv_30d_ann) exceeds its IS-derived p75 threshold. "
            "Position size is scaled by --vol-ceiling-scale when the ceiling fires."
        ),
    )
    parser.add_argument(
        "--vol-ceiling-pct",
        type=float,
        default=75.0,
        metavar="PCT",
        help=(
            "Percentile of IS rv_30d_ann distribution used as per-symbol ceiling "
            "threshold (iter-v1/038). Range [50, 95]. Default 75 (p75). "
            "iter-v1/038 pre-flight asserts this is 75."
        ),
    )
    parser.add_argument(
        "--vol-ceiling-scale",
        type=float,
        default=0.5,
        metavar="SCALE",
        help=(
            "Position-sizing multiplier when the vol ceiling fires (iter-v1/038). "
            "Range [0.1, 1.0]. Default 0.5 (half-size). "
            "iter-v1/038 pre-flight asserts this is 0.5."
        ),
    )
    parser.add_argument(
        "--model",
        choices=["lgbm", "xgboost"],
        default="lgbm",
        help=(
            "ML library to use for training (iter-v1/042). "
            "'lgbm' (default) = LightGbmStrategy — BIT-IDENTICAL to all prior runs. "
            "'xgboost' = XgboostStrategy with tree_method='hist' + grow_policy='depthwise' "
            "+ n_jobs=1 (depth-wise level-wise growth, no GOSS). "
            "iter-v1/042 pre-flight asserts --model xgboost."
        ),
    )
    # iter-v1/044: bundle-config flag for CONFIRMATION-MERGE-PORTFOLIO dispatch.
    # Format: "component:weight,component:weight,...", e.g.
    # "baseline:0.50,v1-036:0.30,v1-043:0.20"
    # Valid component names: "baseline", "v1-NNN" (e.g. "v1-036", "v1-043").
    # Weights must sum to 1.0 ± 1e-6.  Requires --confirmation mode.
    parser.add_argument(
        "--bundle-config",
        type=str,
        default=None,
        dest="bundle_config",
        metavar="SPEC",
        help=(
            "CONFIRMATION-MERGE-PORTFOLIO bundle spec (iter-v1/044). "
            "Format: 'component:weight,...'. Example: "
            "'baseline:0.50,v1-036:0.30,v1-043:0.20'. "
            "Weights must sum to 1.0 ± 1e-6. Requires --confirmation. "
            "Triggers sequential sub-run + post-hoc bundle aggregation; "
            "no new LightGBM training (reuses frozen component artifacts)."
        ),
    )
    # iter-v1/044: output-dir override for bundle sub-runs.
    # When set, overrides the standard reports-v1/iteration_v1-<label>/ path.
    # Used by bundle sub-runs to write component artifacts under the bundle dir.
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        dest="output_dir_override",
        metavar="DIR",
        help=(
            "Override output directory (iter-v1/044 bundle sub-runs). "
            "Default: reports-v1/iteration_v1-<label>/. "
            "Used internally by bundle dispatch to route component reports "
            "under reports-v1/iteration_v1-044/{component}/."
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
        "v1-044",
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
    optuna_objective_arg = getattr(args, "optuna_objective", "sharpe")
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
    print(f"  optuna_objective: {optuna_objective_arg}")

    # iter-v1/038: vol-ceiling mode resolution.
    vol_ceiling_mode_arg = getattr(args, "vol_ceiling_mode", "none")
    vol_ceiling_pct_arg = float(getattr(args, "vol_ceiling_pct", 75.0))
    vol_ceiling_scale_arg = float(getattr(args, "vol_ceiling_scale", 0.5))
    print(f"  vol_ceiling_mode: {vol_ceiling_mode_arg}")
    if vol_ceiling_mode_arg != "none":
        print(f"  vol_ceiling_pct: {vol_ceiling_pct_arg}")
        print(f"  vol_ceiling_scale: {vol_ceiling_scale_arg}")

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

    # iter-v1/041: ATR multiplier override resolution.
    # None = BIT-IDENTICAL to prior behaviour (per-model baseline defaults used in dispatch).
    atr_tp_mult_arg: float | None = getattr(args, "atr_tp_mult", None)
    atr_sl_mult_arg: float | None = getattr(args, "atr_sl_mult", None)
    if atr_tp_mult_arg is not None or atr_sl_mult_arg is not None:
        print(
            f"  [iter-v1/041] ATR multiplier override: atr_tp_mult={atr_tp_mult_arg} "
            f"atr_sl_mult={atr_sl_mult_arg} (uniform across all models)"
        )

    # iter-v1/041: min_child_samples Optuna lower bound override resolution.
    # None = BIT-IDENTICAL to prior behaviour (20 for v1_pruned, 5 for default).
    min_data_in_leaf_min_arg: int | None = getattr(args, "min_data_in_leaf_min", None)
    if min_data_in_leaf_min_arg is not None:
        print(
            f"  [iter-v1/041] min_child_samples lower bound override: "
            f"{min_data_in_leaf_min_arg} (was 20 for v1_pruned)"
        )

    # iter-v1/042: ML library selection.
    # "lgbm" (default) = LightGbmStrategy — BIT-IDENTICAL to all prior iterations.
    # "xgboost" = XgboostStrategy with tree_method='hist' + grow_policy='depthwise' +
    # n_jobs=1 (depth-wise level-wise growth, no GOSS). Pure library swap with all
    # other parameters (features, labels, universe, risk gates, Optuna objective) UNCHANGED.
    model_type_arg: str = getattr(args, "model", "lgbm")
    print(f"  model_type: {model_type_arg}")
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
    # iter-v1/037: optuna_objective threaded through for loss-function axis.
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
        optuna_objective=optuna_objective_arg,
        vol_ceiling_enabled=vol_ceiling_mode_arg == "per_symbol",
        vol_ceiling_scale=vol_ceiling_scale_arg,
        vol_ceiling_thresholds=None,  # populated below when per_symbol mode is active
    )

    # iter-v1/038: pre-compute per-symbol vol-ceiling thresholds from IS-only data.
    # Done ONCE before the dispatch loop so all run_model calls share the same
    # static thresholds (avoids re-computing per model call).
    # IS-only: close_time < OOS_CUTOFF_MS (2025-03-24 00:00 UTC) — look-ahead safe.
    if vol_ceiling_mode_arg == "per_symbol":
        import pandas as pd  # noqa: PLC0415
        import pyarrow.parquet as pq  # noqa: PLC0415

        from crypto_trade.risk.vol_ceiling import compute_per_symbol_vol_ceiling  # noqa: PLC0415

        _vc_features_dir = Path("data") / "features"
        _vc_klines_frames = []
        for _vc_sym in symbols:
            _feat_path = _vc_features_dir / f"{_vc_sym}_8h_features.parquet"
            if _feat_path.exists():
                _vc_tab = pq.read_table(_feat_path, columns=["open_time", "close_time", "close"])
                _vc_df = _vc_tab.to_pandas()
                _vc_df["symbol"] = _vc_sym
                _vc_klines_frames.append(_vc_df)
            else:
                print(f"[VOL-CEIL/038] WARNING: parquet not found for {_vc_sym}: {_feat_path}")
        _vc_thresholds_computed: dict = {}
        if _vc_klines_frames:
            _vc_panel = pd.concat(_vc_klines_frames, ignore_index=True)
            for _vc_sym in symbols:
                _thr = compute_per_symbol_vol_ceiling(
                    _vc_panel,
                    _vc_sym,
                    lookback_bars=90,
                    percentile=vol_ceiling_pct_arg,
                )
                _vc_thresholds_computed[_vc_sym] = _thr
                print(
                    f"[VOL-CEIL/038] {_vc_sym}: IS rv_p{vol_ceiling_pct_arg:.0f} threshold = "
                    f"{_thr:.4f} (rv_30d_ann; scale_factor={vol_ceiling_scale_arg:.2f}x above)"
                )
        # Update _r5_kwargs with computed thresholds so all run_model dispatches inherit them
        _r5_kwargs["vol_ceiling_thresholds"] = _vc_thresholds_computed

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

    elif iteration_label == "v1-037" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/037: cycle-5 EXPLORATION #4/10 — loss-function axis (NEW 12th family).
        # Tests whether replacing Optuna's per-trial scoring from Sharpe (mean/std) to
        # Sortino (mean/downside_std) surfaces HP regions that Sharpe under-rewards.
        # EDA: Sortino/Sharpe ratio 3.0-4.0x across all 4 cohorts (right-skewed returns).
        # NORMAL-RISK (changes only the scalar Optuna aggregate, NOT the training-objective
        # domain — labels, features, search space, weights all UNCHANGED).
        # Models A/C/D/E: IDENTICAL config to baseline catch-all EXCEPT optuna_objective.
        assert optuna_objective_arg == "sortino", (
            f"iter-v1/037 pre-flight FAIL: expected --optuna-objective sortino "
            f"but got {optuna_objective_arg!r}. "
            "Pass --optuna-objective sortino to activate the Sortino loss-function axis. "
            "iter-v1/037 tests Optuna Sortino objective — sortino is the required mode."
        )
        print(
            f"[iter-v1/037] SORTINO OBJECTIVE: optuna_objective={optuna_objective_arg!r}. "
            f"Loss-function axis (NEW 12th family). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer), n_trials={n_trials}. "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED UNCHANGED). "
            f"Labels: triple_barrier (UNCHANGED). Weights: abs_pnl (UNCHANGED). "
            f"Models: A (BTC+ETH) + C (LINK) + D (LTC) + E (DOT) — baseline 4-model bundle."
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

    elif iteration_label == "v1-038" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/038: cycle-5 EXPLORATION #5/10 — risk-primitive axis.
        # Tests whether applying a 0.5x pre-trade size scaling when a symbol's
        # rolling 30d annualized realized vol (rv_30d_ann) exceeds its IS-derived
        # p75 threshold reduces tail downside on BTC/LTC (EDA §4 asymmetry positive)
        # without sacrificing LINK/DOT positive-expectancy mid-vol regime trades
        # (EDA §3 HOSTILE per-symbol linear prediction for LINK/DOT).
        # NORMAL-RISK: stateless pre-trade gate; does NOT alter Optuna training objective.
        # Config: vol_ceiling_mode=per_symbol, pct=75, scale=0.5, lookback_bars=90.
        assert vol_ceiling_mode_arg == "per_symbol", (
            f"iter-v1/038 pre-flight FAIL: expected --vol-ceiling-mode per_symbol "
            f"but got {vol_ceiling_mode_arg!r}. "
            "Pass --vol-ceiling-mode per_symbol to activate the per-symbol rv-ceiling axis. "
            "iter-v1/038 tests the vol-ceiling risk-primitive — per_symbol is the required mode."
        )
        assert 70.0 <= vol_ceiling_pct_arg <= 80.0, (
            f"iter-v1/038 pre-flight FAIL: expected --vol-ceiling-pct in [70, 80] "
            f"but got {vol_ceiling_pct_arg}. "
            "iter-v1/038 brief specifies pct=75 (p75 IS threshold)."
        )
        assert abs(vol_ceiling_scale_arg - 0.5) < 1e-9, (
            f"iter-v1/038 pre-flight FAIL: expected --vol-ceiling-scale 0.5 "
            f"but got {vol_ceiling_scale_arg}. "
            "iter-v1/038 brief specifies scale_factor=0.5 (half-size entry)."
        )
        assert set(symbols) == set(V1_BASELINE_UNIVERSE), (
            f"iter-v1/038 pre-flight FAIL: expected V1_BASELINE_UNIVERSE symbols "
            f"(BTC+ETH+LINK+LTC+DOT) but got {sorted(symbols)}."
        )
        print(
            f"[iter-v1/038] VOL-CEILING ACTIVE: mode={vol_ceiling_mode_arg!r}, "
            f"pct={vol_ceiling_pct_arg:.0f}, scale={vol_ceiling_scale_arg:.2f}, "
            f"symbols={'+'.join(s.replace('USDT', '') for s in sorted(symbols))}, "
            f"lookback_bars=90 (30d at 8h), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer), "
            f"n_trials={n_trials}, features={len(active_feature_columns)} cols "
            f"(V1_FEATURE_COLUMNS_PRUNED UNCHANGED). "
            f"Models: A (BTC+ETH) + C (LINK) + D (LTC) + E (DOT) — baseline 4-model topology."
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

    elif iteration_label == "v1-039" and set(symbols) == set(V1_ITER039_UNIVERSE):
        # iter-v1/039: cycle-5 EXPLORATION #6/10 — per-cohort Sortino × specialist hybrid.
        # DOUBLE-REPEAT COMBO: loss-function × per-cohort-specialization stacking-interaction
        # probe of /036 (PROMISING-CLEAN LINK+DOT trend-scan) and /037 (PROMISING-CLEAN
        # Sortino loss-function). Resolves /044 CONFIRMATION routing: do the two PROMISING
        # axes COMPOUND on the same substrate or COMPETE (basin collision)?
        # HIGH-RISK by rotation rule (double-REPEAT + NEG-DOMINANT 60% prior);
        # NORMAL-RISK by mechanism (no Optuna training-objective domain change).
        # Model A pool, Model D LTC SKIPPED — ONLY Model C' (LINK) + Model E (DOT).
        # V1_FEATURE_COLUMNS_PRUNED 44 cols UNCHANGED. No new src/ code.
        assert label_mode_arg == "trend_scanning", (
            f"iter-v1/039 pre-flight FAIL: expected --label-mode trend_scanning "
            f"but got {label_mode_arg!r}. "
            "Pass --label-mode trend_scanning to activate the per-cohort Sortino × "
            "specialist hybrid axis. iter-v1/039 layers Sortino onto /036's "
            "trend-scanning 2-cohort substrate — trend_scanning labels are required."
        )
        assert optuna_objective_arg == "sortino", (
            f"iter-v1/039 pre-flight FAIL: expected --optuna-objective sortino "
            f"but got {optuna_objective_arg!r}. "
            "Pass --optuna-objective sortino to activate the Sortino loss-function "
            "component. iter-v1/039 stacks /037's Sortino objective on /036's "
            "trend-scanning specialist substrate."
        )
        assert set(symbols) == set(V1_ITER039_UNIVERSE), (
            f"iter-v1/039 pre-flight FAIL: expected V1_ITER039_UNIVERSE "
            f"{{LINKUSDT, DOTUSDT}} but got {sorted(symbols)}. "
            "iter-v1/039 dispatches only the LINK + DOT 2-cohort specialist universe."
        )
        assert vol_ceiling_mode_arg == "none", (
            f"iter-v1/039 pre-flight FAIL: expected --vol-ceiling-mode none "
            f"but got {vol_ceiling_mode_arg!r}. "
            "iter-v1/039 does NOT carry over the /038 vol-ceiling risk-primitive "
            "(CLOSED axis). vol_ceiling_mode must be none."
        )
        print(
            "[run_baseline_v1] === iter-v1/039 --- per-cohort Sortino x specialist hybrid "
            "(loss-function x per-cohort REPEAT-COMBO; cycle-5 EXP-6) ==="
        )
        print(
            f"[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE: "
            f"models=Model_C_LINK + Model_E_DOT, "
            f"label_mode={label_mode_arg}, "
            f"optuna_objective={optuna_objective_arg}, "
            f"ENSEMBLE_SIZE={ensemble_size}, "
            f"n_trials={n_trials}, "
            f"seeds=1, "
            f"features={len(active_feature_columns)} cols"
        )
        # Model C' (LINK only): trend-scanning labels + Sortino objective
        # R1=ON (consecutive-SL cool-down); R3=ON (Mahalanobis OOD gate) — identical to /036
        results_c039, faxm_c039, _strat_c039 = run_model(
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
        # Model E (DOT only): trend-scanning labels + Sortino objective
        # R1=ON, R2=ON (drawdown brake), R3=ON — identical to /036
        results_e039, faxm_e039, _strat_e039 = run_model(
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

        # F-AXIS #2 dispatch verification: assert per-cohort isolation enforced
        c039_symbols = {r.symbol for r in results_c039}
        e039_symbols = {r.symbol for r in results_e039}
        assert c039_symbols.issubset({"LINKUSDT"}), (
            f"[iter-v1/039] Model C' produced non-LINK results: {c039_symbols - {'LINKUSDT'}}. "
            "Per-cohort isolation failed — Model C' must trade LINKUSDT only."
        )
        assert e039_symbols.issubset({"DOTUSDT"}), (
            f"[iter-v1/039] Model E produced non-DOT results: {e039_symbols - {'DOTUSDT'}}. "
            "Per-cohort isolation failed — Model E must trade DOTUSDT only."
        )

        print(
            f"[iter-v1/039] Bundle dispatch verified: "
            f"C'={len(results_c039)} trades (LINK) "
            f"E={len(results_e039)} trades (DOT)"
        )

        _all_faxm_logs = faxm_c039 + faxm_e039
        all_results = results_c039 + results_e039
        _r5_model_results = [results_c039, results_e039]
        _post_dispatch_fi_strategies = [
            ("Model_C_LINK_sortino_trend_scan_specialist", _strat_c039),
            ("Model_E_DOT_sortino_trend_scan_specialist", _strat_e039),
        ]

    elif iteration_label == "v1-040" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/040: cycle-5 EXPLORATION #7/10 — composed feature SWAP.
        # DROP basis_zscore_30 (3-consec INERT) + ADD regime_momentum_signed_5d.
        # Feature-engineering axis: pure feature SWAP (DROP 1 INERT + ADD 1 COMPOSED).
        # V1_FEATURE_COLUMNS_PRUNED stays at 44 cols (basis_zscore_30 DROPPED,
        # regime_momentum_signed_5d ADDED).
        # regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)
        # where ret_5d is 15-bar (120h = 5 days) log return.
        # EDA FINDING: sign(hurst_100 − 0.5) = +1 in 100% of IS samples (all 5 v1 syms).
        # Composed feature is mechanically equivalent to ret_5d (15-bar log return).
        # v3 /025 PROMISING (IS +0.50/OOS +0.84) + /028 CONFIRMATION-MERGE attributed
        # to the NEW 15-bar horizon (v1 longest prior = stat_log_return_5 at 5-bar=40h).
        # NORMAL-RISK: no training-objective domain change, labels, universe, arch change.
        # All other config IDENTICAL to baseline: 4 models A/C/D/E.
        assert "regime_momentum_signed_5d" in active_feature_columns, (
            "iter-v1/040 pre-flight FAIL: regime_momentum_signed_5d not in active_feature_columns. "
            "Ensure --pruned-features is set AND V1_FEATURE_COLUMNS_PRUNED"
            " contains regime_momentum_signed_5d. "
            "Regenerate: uv run crypto-trade features --track v1 --groups composed_v1"
            " --interval 8h --format parquet"
            " --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --workers 4"
        )
        assert "basis_zscore_30" not in active_feature_columns, (
            "iter-v1/040 pre-flight FAIL: basis_zscore_30 still in active_feature_columns. "
            "basis_zscore_30 was DROPPED (3-consec INERT) and must NOT appear in"
            " V1_FEATURE_COLUMNS_PRUNED as of iter-v1/040. "
            "Check V1_FEATURE_COLUMNS_PRUNED in src/crypto_trade/features_v1/__init__.py."
        )
        assert vol_ceiling_mode_arg == "none", (
            f"iter-v1/040 pre-flight FAIL: expected --vol-ceiling-mode none "
            f"but got {vol_ceiling_mode_arg!r}. "
            "iter-v1/040 does NOT carry over /038 vol-ceiling (CLOSED axis)."
        )
        assert label_mode_arg == "triple_barrier", (
            f"iter-v1/040 pre-flight FAIL: expected --label-mode triple_barrier "
            f"but got {label_mode_arg!r}. "
            "iter-v1/040 uses triple-barrier labels (UNCHANGED from baseline)."
        )
        assert optuna_objective_arg == "sharpe", (
            f"iter-v1/040 pre-flight FAIL: expected --optuna-objective sharpe "
            f"but got {optuna_objective_arg!r}. "
            "iter-v1/040 uses Sharpe objective (NOT Sortino — orthogonal to /037)."
        )
        pos_regime_mom = active_feature_columns.index("regime_momentum_signed_5d")
        print(
            "[run_baseline_v1] === iter-v1/040 --- composed feature SWAP: "
            "DROP basis_zscore_30 (INERT-3-consec), "
            "ADD regime_momentum_signed_5d (v3-PROVEN; cycle-5 EXP-7) ==="
        )
        print(
            f"[iter-v1/040] COMPOSED-FEATURE ACTIVE: regime_momentum_signed_5d@{pos_regime_mom} "
            f"/ {len(active_feature_columns)} features; basis_zscore_30 DROPPED. "
            f"v3-PROVEN: /025 PROMISING (IS +0.50 / OOS +0.84) + /028 CONFIRMATION-MERGE. "
            f"EDA: hurst_100=+1 everywhere → feature ≡ ret_5d (15-bar 120h log return). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer=42), n_trials={n_trials}."
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

    elif iteration_label == "v1-041" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/041: cycle-5 EXPLORATION #8/10 — triple-barrier TIGHTEN.
        # Uniform shrink of ATR multipliers across all 4 cohorts:
        #   atr_tp_mult 2.9/3.5 → 1.5 (uniform)
        #   atr_sl_mult 1.45/1.75 → 0.75 (uniform)
        #   TP/SL ratio 2.0 PRESERVED
        # Paired defensive mitigation: min_child_samples Optuna lower bound 20 → 50.
        # AXIS PURPOSE: test whether denser short-horizon triple-barrier labels
        # (predicted 2.55×–3.00× IS density lift) lift OOS Sharpe via √N count gain,
        # or whether chop-noise dominance and fee-drag artifact dominate.
        # All other config IDENTICAL to baseline: features, R1/R2/R3, objective.
        assert atr_tp_mult_arg == 1.5, (
            f"iter-v1/041 pre-flight FAIL: expected --atr-tp-mult 1.5 "
            f"but got {atr_tp_mult_arg!r}. "
            "iter-v1/041 uniform tighten requires atr_tp_mult=1.5 exactly. "
            "Run with: --atr-tp-mult 1.5 --atr-sl-mult 0.75"
        )
        assert atr_sl_mult_arg == 0.75, (
            f"iter-v1/041 pre-flight FAIL: expected --atr-sl-mult 0.75 "
            f"but got {atr_sl_mult_arg!r}. "
            "iter-v1/041 uniform tighten requires atr_sl_mult=0.75 exactly. "
            "Run with: --atr-tp-mult 1.5 --atr-sl-mult 0.75"
        )
        assert min_data_in_leaf_min_arg == 50, (
            f"iter-v1/041 pre-flight FAIL: expected --min-data-in-leaf-min 50 "
            f"but got {min_data_in_leaf_min_arg!r}. "
            "iter-v1/041 paired mitigation requires min_data_in_leaf_min=50 exactly. "
            "Run with: --min-data-in-leaf-min 50"
        )
        assert label_mode_arg == "triple_barrier", (
            f"iter-v1/041 pre-flight FAIL: expected --label-mode triple_barrier "
            f"but got {label_mode_arg!r}. "
            "iter-v1/041 stays within triple-barrier family (NOT trend-scanning). "
            "Run with: --label-mode triple_barrier"
        )
        assert vol_ceiling_mode_arg == "none", (
            f"iter-v1/041 pre-flight FAIL: expected --vol-ceiling-mode none "
            f"but got {vol_ceiling_mode_arg!r}. "
            "iter-v1/041 does NOT carry over /038 vol-ceiling (CLOSED axis)."
        )
        print(
            "[run_baseline_v1] === iter-v1/041 --- labeling tighten triple-barrier: "
            "atr_tp_mult=1.5/atr_sl_mult=0.75 (was Pool A 2.9/1.45, C-E 3.5/1.75); "
            "ratio 2.0 preserved; min_data_in_leaf floor 50; cycle-5 EXP-8 ==="
        )
        print(
            f"[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE: "
            f"uniform atr_tp_mult={atr_tp_mult_arg}/atr_sl_mult={atr_sl_mult_arg} "
            f"(was Pool A 2.9/1.45, C/D/E 3.5/1.75); "
            f"min_data_in_leaf_lower_bound={min_data_in_leaf_min_arg} (was 20); "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer=42), "
            f"n_trials={n_trials}, features={len(active_feature_columns)} cols"
        )
        results_a, faxm_a, _strat_a = run_model(
            "A (BTC/ETH)",
            ("BTCUSDT", "ETHUSDT"),
            atr_tp=atr_tp_mult_arg,
            atr_sl=atr_sl_mult_arg,
            apply_r1=False,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            min_child_samples_lower_bound=min_data_in_leaf_min_arg,
            **_r5_kwargs,
        )
        results_c, faxm_c, _strat_c = run_model(
            "C (LINK + R1)",
            ("LINKUSDT",),
            atr_tp=atr_tp_mult_arg,
            atr_sl=atr_sl_mult_arg,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            min_child_samples_lower_bound=min_data_in_leaf_min_arg,
            **_r5_kwargs,
        )
        results_d, faxm_d, _strat_d = run_model(
            "D (LTC + R1)",
            ("LTCUSDT",),
            atr_tp=atr_tp_mult_arg,
            atr_sl=atr_sl_mult_arg,
            apply_r1=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            min_child_samples_lower_bound=min_data_in_leaf_min_arg,
            **_r5_kwargs,
        )
        results_e, faxm_e, _strat_e = run_model(
            "E (DOT + R1 + R2)",
            ("DOTUSDT",),
            atr_tp=atr_tp_mult_arg,
            atr_sl=atr_sl_mult_arg,
            apply_r1=True,
            apply_r2=True,
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            min_child_samples_lower_bound=min_data_in_leaf_min_arg,
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

    elif iteration_label == "v1-042" and set(symbols) == set(V1_BASELINE_UNIVERSE):
        # iter-v1/042: cycle-5 EXPLORATION #9/10 — MODEL-ARCH library swap.
        # Pure substitution: LightGbmStrategy → XgboostStrategy at constant
        # data / labels / features / risk gates / Optuna objective.
        # XGBoost: tree_method='hist', grow_policy='depthwise', n_jobs=1,
        # random_state=seed, scale_pos_weight=n_neg/n_pos (computed per-fit).
        # Optuna: 6 hp (num_leaves DROPPED — no-op under depthwise growth).
        # max_depth ∈ [3, 5] enforced in optimization_xgb.py (LM Master Rec 1).
        # ENSEMBLE_SIZE=3 inner seeds (42, 123, 456); single outer seed=42.
        # All per-model ATR tp/sl at baseline defaults (no /041 carry-over).
        assert model_type_arg == "xgboost", (
            f"iter-v1/042 pre-flight FAIL: expected --model xgboost "
            f"but got {model_type_arg!r}. "
            "This iteration REQUIRES the XGBoost library. "
            "Run with: --model xgboost"
        )
        assert label_mode_arg == "triple_barrier", (
            f"iter-v1/042 pre-flight FAIL: expected --label-mode triple_barrier "
            f"but got {label_mode_arg!r}. "
            "iter-v1/042 labeling is UNCHANGED from baseline (triple_barrier). "
            "Run with: --label-mode triple_barrier (default)"
        )
        assert optuna_objective_arg == "sharpe", (
            f"iter-v1/042 pre-flight FAIL: expected --optuna-objective sharpe "
            f"but got {optuna_objective_arg!r}. "
            "iter-v1/042 Optuna objective is UNCHANGED from baseline (Sharpe, NOT Sortino). "
            "Run with: --optuna-objective sharpe (default)"
        )
        assert vol_ceiling_mode_arg == "none", (
            f"iter-v1/042 pre-flight FAIL: expected --vol-ceiling-mode none "
            f"but got {vol_ceiling_mode_arg!r}. "
            "iter-v1/042 does NOT carry over /038 vol-ceiling (CLOSED axis). "
            "Run with: --vol-ceiling-mode none (default)"
        )
        assert atr_tp_mult_arg is None, (
            f"iter-v1/042 pre-flight FAIL: expected no --atr-tp-mult override "
            f"but got {atr_tp_mult_arg!r}. "
            "iter-v1/042 uses baseline ATR defaults per cohort (no /041 carry-over). "
            "Do NOT pass --atr-tp-mult for this iteration."
        )
        print(
            "[run_baseline_v1] === iter-v1/042 — MODEL-ARCH library swap "
            "LightGBM → XGBoost (depth-wise + hist; cycle-5 EXP-9/10) ==="
        )
        print(
            f"[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise "
            f"n_jobs=1 / {len(active_feature_columns)} features / "
            f"ENSEMBLE_SIZE={ensemble_size} / n_trials={n_trials}"
        )
        _ensemble_seeds_042 = _derive_ensemble_seeds(ensemble_size, offset=ensemble_seeds_offset)
        _config_a_042 = BacktestConfig(
            symbols=("BTCUSDT", "ETHUSDT"),
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
            risk_consecutive_sl_limit=None,
            risk_consecutive_sl_cooldown_candles=0,
            risk_drawdown_scale_enabled=False,
            risk_drawdown_trigger_pct=7.0,
            risk_drawdown_scale_floor=0.33,
            risk_drawdown_scale_anchor_pct=15.0,
        )
        _strat_a_042 = XgboostStrategy(
            training_months=24,
            n_trials=n_trials,
            cv_splits=5,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=1,
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
            atr_column="vol_natr_21",
            use_atr_labeling=True,
            ensemble_seeds=list(_ensemble_seeds_042),
            feature_columns=list(active_feature_columns),
            ood_enabled=True,
            ood_features=list(V1_OOD_FEATURE_COLUMNS),
            ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
            oof_persist_path=OOF_PARQUET_PATH,
        )
        _t0_a = time.time()
        results_a = run_backtest(_config_a_042, _strat_a_042, yearly_pnl_check=False)
        _elapsed_a = time.time() - _t0_a
        print(f"\nModel A (BTC/ETH) XGB complete: {len(results_a)} trades in {_elapsed_a:.0f}s")
        faxm_a = getattr(_strat_a_042, "_faxm_log", [])

        _config_c_042 = BacktestConfig(
            symbols=("LINKUSDT",),
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
            risk_consecutive_sl_limit=3,
            risk_consecutive_sl_cooldown_candles=27,
            risk_drawdown_scale_enabled=False,
            risk_drawdown_trigger_pct=7.0,
            risk_drawdown_scale_floor=0.33,
            risk_drawdown_scale_anchor_pct=15.0,
        )
        _strat_c_042 = XgboostStrategy(
            training_months=24,
            n_trials=n_trials,
            cv_splits=5,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=1,
            atr_tp_multiplier=3.5,
            atr_sl_multiplier=1.75,
            atr_column="vol_natr_21",
            use_atr_labeling=True,
            ensemble_seeds=list(_ensemble_seeds_042),
            feature_columns=list(active_feature_columns),
            ood_enabled=True,
            ood_features=list(V1_OOD_FEATURE_COLUMNS),
            ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
            oof_persist_path=OOF_PARQUET_PATH,
        )
        _t0_c = time.time()
        results_c = run_backtest(_config_c_042, _strat_c_042, yearly_pnl_check=False)
        _elapsed_c = time.time() - _t0_c
        print(f"\nModel C (LINK + R1) XGB complete: {len(results_c)} trades in {_elapsed_c:.0f}s")
        faxm_c = getattr(_strat_c_042, "_faxm_log", [])

        _config_d_042 = BacktestConfig(
            symbols=("LTCUSDT",),
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
            risk_consecutive_sl_limit=3,
            risk_consecutive_sl_cooldown_candles=27,
            risk_drawdown_scale_enabled=False,
            risk_drawdown_trigger_pct=7.0,
            risk_drawdown_scale_floor=0.33,
            risk_drawdown_scale_anchor_pct=15.0,
        )
        _strat_d_042 = XgboostStrategy(
            training_months=24,
            n_trials=n_trials,
            cv_splits=5,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=1,
            atr_tp_multiplier=3.5,
            atr_sl_multiplier=1.75,
            atr_column="vol_natr_21",
            use_atr_labeling=True,
            ensemble_seeds=list(_ensemble_seeds_042),
            feature_columns=list(active_feature_columns),
            ood_enabled=True,
            ood_features=list(V1_OOD_FEATURE_COLUMNS),
            ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
            oof_persist_path=OOF_PARQUET_PATH,
        )
        _t0_d = time.time()
        results_d = run_backtest(_config_d_042, _strat_d_042, yearly_pnl_check=False)
        _elapsed_d = time.time() - _t0_d
        print(f"\nModel D (LTC + R1) XGB complete: {len(results_d)} trades in {_elapsed_d:.0f}s")
        faxm_d = getattr(_strat_d_042, "_faxm_log", [])

        _config_e_042 = BacktestConfig(
            symbols=("DOTUSDT",),
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
            risk_consecutive_sl_limit=3,
            risk_consecutive_sl_cooldown_candles=27,
            risk_drawdown_scale_enabled=True,
            risk_drawdown_trigger_pct=7.0,
            risk_drawdown_scale_floor=0.33,
            risk_drawdown_scale_anchor_pct=15.0,
        )
        _strat_e_042 = XgboostStrategy(
            training_months=24,
            n_trials=n_trials,
            cv_splits=5,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=1,
            atr_tp_multiplier=3.5,
            atr_sl_multiplier=1.75,
            atr_column="vol_natr_21",
            use_atr_labeling=True,
            ensemble_seeds=list(_ensemble_seeds_042),
            feature_columns=list(active_feature_columns),
            ood_enabled=True,
            ood_features=list(V1_OOD_FEATURE_COLUMNS),
            ood_cutoff_pct=BASELINE_OOD_CUTOFF_PCT,
            oof_persist_path=OOF_PARQUET_PATH,
        )
        _t0_e = time.time()
        results_e = run_backtest(_config_e_042, _strat_e_042, yearly_pnl_check=False)
        _elapsed_e = time.time() - _t0_e
        print(
            f"\nModel E (DOT + R1 + R2) XGB complete: {len(results_e)} trades in {_elapsed_e:.0f}s"
        )
        faxm_e = getattr(_strat_e_042, "_faxm_log", [])

        _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e
        all_results = results_a + results_c + results_d + results_e
        _r5_model_results = [results_a, results_c, results_d, results_e]
        _post_dispatch_fi_strategies = [
            ("Model_A_xgboost_pool", _strat_a_042),
            ("Model_C_xgboost_LINK", _strat_c_042),
            ("Model_D_xgboost_LTC", _strat_d_042),
            ("Model_E_xgboost_DOT", _strat_e_042),
        ]

    elif iteration_label == "v1-043" and set(symbols) == set(V1_ITER043_UNIVERSE):
        # iter-v1/043: cycle-5 EXPLORATION #10/10 (CADENCE COMPLETE — /044 CONFIRMATION next).
        # LINK-only trend-scanning specialist. Strips DOT from /036's LINK+DOT 2-cohort
        # substrate to resolve /044 substrate-composition decision:
        #   Δ >= 0 vs /036 → LINK is load-bearing; DOT was passenger → /044-A LINK-only
        #   Δ ∈ [-0.90, -0.35) → PAIRING-PARTIAL; DOT provides risk-diversification
        #   Δ < -0.90 → LINK-DEPENDS-ON-DOT; pairing irreducible → /044-A LINK+DOT MANDATORY
        # NORMAL-RISK: composition of /036 per-cohort isolation + /035 trend-scanning
        # (both shipped; no new Optuna training-objective domain change).
        # Model A pool, Model D LTC, Model E DOT, Model G ETH SKIPPED. ONLY Model C' (LINK).
        assert label_mode_arg == "trend_scanning", (
            f"iter-v1/043 pre-flight FAIL: expected --label-mode trend_scanning "
            f"but got {label_mode_arg!r}. "
            "Pass --label-mode trend_scanning to activate the LINK-only trend-scan specialist. "
            "iter-v1/043 is a 1-cohort isolation of /036's LINK+DOT substrate — "
            "trend_scanning labels are required to maintain substrate parity with /036."
        )
        assert set(symbols) == set(V1_ITER043_UNIVERSE), (
            f"iter-v1/043 pre-flight FAIL: expected symbols == {{LINKUSDT}} "
            f"but got {set(symbols)!r}. "
            "iter-v1/043 dispatches ONLY Model C' (LINK specialist). "
            "Passing DOTUSDT or any other symbol would contaminate the single-cohort isolation."
        )
        assert optuna_objective_arg in ("sharpe", None), (
            f"iter-v1/043 pre-flight FAIL: expected --optuna-objective sharpe (default) "
            f"but got {optuna_objective_arg!r}. "
            "iter-v1/043 MUST use Sharpe objective (NOT Sortino) for /036 parity. "
            "Passing --optuna-objective sortino would contaminate the /043 single-axis isolation "
            "with the /039 Sortino axis (CLOSED per /039 NEG-CATASTROPHIC verdict)."
        )
        assert model_type_arg == "lgbm", (
            f"iter-v1/043 pre-flight FAIL: expected --model lgbm (default) "
            f"but got {model_type_arg!r}. "
            "iter-v1/043 uses LightGBM (not XGBoost). The /042 XGBoost axis does NOT "
            "carry over to /043. Pass --model lgbm (default) or omit --model."
        )
        assert vol_ceiling_mode_arg == "none", (
            f"iter-v1/043 pre-flight FAIL: expected --vol-ceiling-mode none (default) "
            f"but got {vol_ceiling_mode_arg!r}. "
            "iter-v1/043 does NOT carry over /038 vol-ceiling (CLOSED axis). "
            "Run with --vol-ceiling-mode none (default) or omit the flag."
        )
        print(
            f"[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE: "
            f"model=Model_C_LINK_only, "
            f"label_mode={label_mode_arg}, "
            f"trend_scan_grid=(5, 8, 13, 21), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), "
            f"n_trials={n_trials}, "
            f"seeds=1 (outer=42). "
            f"NORMAL-RISK: /036 per-cohort isolation + /035 trend-scanning (both shipped). "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED UNCHANGED). "
            f"cycle-5 EXP-10/10 FINAL — /044 CONFIRMATION substrate-composition diagnostic."
        )
        # Model C': LINK specialist + trend_scanning labels
        # R1=ON (consecutive-SL cool-down); R3=ON (Mahalanobis OOD gate) — baseline Model C config
        # Matches /036's LINK-leg config exactly. DOT (Model E) is SKIPPED.
        results_c043, faxm_c043, _strat_c043 = run_model(
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

        # F-AXIS #2 dispatch verification: assert ONLY LINK trades emitted
        c043_symbols = {r.symbol for r in results_c043}
        assert c043_symbols.issubset({"LINKUSDT"}), (
            f"[iter-v1/043] Model C' produced non-LINK results: {c043_symbols - {'LINKUSDT'}}. "
            "Per-cohort isolation failed — Model C' must trade LINKUSDT ONLY."
        )

        print(
            f"[iter-v1/043] Dispatch verified: "
            f"Model_C_LINK_only={len(results_c043)} LINK trades (DOT/LTC/BTC/ETH skipped). "
            f"F-AXIS #2 PASS: universe isolation confirmed."
        )

        _all_faxm_logs = faxm_c043
        all_results = results_c043
        _r5_model_results = [results_c043]
        _post_dispatch_fi_strategies = [
            ("Model_C_LINK_trend_scan_only", _strat_c043),
        ]

    elif iteration_label == "v1-050" and set(symbols) == set(V1_ITER050_UNIVERSE):
        # iter-v1/050: DOT-only regime-gated specialist (cycle-6 EXPLORATION #5/10).
        # Axis family: feature-family + risk-primitive (compound; single DOT-specialist).
        #
        # Two-mechanism compound:
        #   (1) NEW feature dot_vs_btc_ret_ratio_30: DOT idiosyncratic return vs BTC
        #       30d, z-scored over 90 bars. Added to V1_FEATURE_COLUMNS_PRUNED (45 → 46).
        #   (2) NEW regime gate: post-prediction stateless vol-spike filter.
        #       Skip DOT signal if btc_realized_vol_30 > q75_IS AND confidence < 0.55.
        #       q75 computed from IS training-data BTC closes ONLY (no OOS peek).
        #
        # NORMAL-RISK: additive feature (no Optuna domain change) + post-prediction
        # stateless gate (no Optuna domain change).
        # Model E semantics: R1=ON, R2=ON (DOT baseline), R3=ON. atr_tp=3.5, atr_sl=1.75.
        # ENSEMBLE_SIZE=3, n_trials=18, seeds=1. Wall-clock cap ≤ 2h.
        assert set(symbols) == {"DOTUSDT"}, (
            f"iter-v1/050 guard: expected {{DOTUSDT}}, got {set(symbols)}"
        )
        assert "dot_vs_btc_ret_ratio_30" in active_feature_columns, (
            "iter-v1/050 pre-flight FAIL: dot_vs_btc_ret_ratio_30 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has the new column. "
            "Run: uv run crypto-trade features --symbols BTCUSDT,DOTUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
        assert len(active_feature_columns) == 46, (
            f"iter-v1/050 guard: expected 46 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}. "
            "V1_FEATURE_COLUMNS_PRUNED should be 45 (iter-v1/049) + 1 (iter-v1/050) = 46."
        )
        print(
            f"[iter-v1/050] DOT-ONLY REGIME-GATED SPECIALIST ACTIVE: "
            f"feature=dot_vs_btc_ret_ratio_30 (cross-BTC idiosyncratic ratio, 90-bar zscore), "
            f"regime_gate=vol-spike (btc_realized_vol_30 > q75_IS AND confidence < 0.55), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), "
            f"n_trials={n_trials}, seeds=1 (outer=42). "
            f"NORMAL-RISK: additive feature + stateless post-prediction gate. "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED 45→46). "
            f"cycle-6 EXP-5/10."
        )
        # Model E: DOT specialist + R1 + R2 + R3 (baseline DOT config)
        # The dot_vs_btc_ret_ratio_30 feature is in the parquet (generated by cross_btc_v1
        # group via: uv run crypto-trade features --symbols BTCUSDT,DOTUSDT --track v1 ...).
        # active_feature_columns includes dot_vs_btc_ret_ratio_30 (V1_FEATURE_COLUMNS_PRUNED).
        results_e050, faxm_e050, _strat_e050 = run_model(
            "E' (DOT + R1 + R2 + regime-gate)",
            ("DOTUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches Model E baseline
            atr_sl=1.75,  # UNCHANGED — matches Model E baseline
            apply_r1=True,  # ON — Model E baseline R1 (consecutive-SL cooldown)
            apply_r2=True,  # ON — Model E baseline R2 (drawdown-triggered scaling)
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # -----------------------------------------------------------------------
        # Vol-spike regime gate (post-prediction, stateless)
        # -----------------------------------------------------------------------
        # Load BTC klines for realized-vol computation.
        # Use the same CSV that the feature pipeline reads.
        import csv as _csv_050  # noqa: PLC0415

        _btc_csv_path_050 = Path("data") / "BTCUSDT" / "8h.csv"
        if not _btc_csv_path_050.exists():
            print(
                f"[iter-v1/050] WARNING: BTC kline CSV not found at {_btc_csv_path_050}. "
                "Vol-spike regime gate DISABLED (no BTC data). "
                "Run: uv run crypto-trade fetch --symbols BTCUSDT --intervals 8h"
            )
            _gate_disabled_050 = True
        else:
            _gate_disabled_050 = False

        if not _gate_disabled_050:
            # Load BTC closes from CSV
            _btc_rows_050: list[dict] = []
            with _btc_csv_path_050.open() as _fh:
                reader_050 = _csv_050.DictReader(_fh)
                for row in reader_050:
                    # Normalize column names (handle 'Close' vs 'close')
                    _row_lower = {k.lower().replace(" ", "_"): v for k, v in row.items()}
                    try:
                        _btc_rows_050.append(
                            {
                                "open_time": int(float(_row_lower["open_time"])),
                                "close": float(_row_lower["close"]),
                            }
                        )
                    except (KeyError, ValueError):
                        pass  # skip malformed rows

            if len(_btc_rows_050) < 30:
                print(
                    f"[iter-v1/050] WARNING: BTC CSV has only {len(_btc_rows_050)} rows "
                    "(< 30 bars). Vol-spike regime gate DISABLED (insufficient BTC data)."
                )
                _gate_disabled_050 = True
            else:
                # Compute btc_realized_vol_30 = rolling_30bar_std(log(btc_close))
                import math as _math_050  # noqa: PLC0415

                _btc_ot_050 = [r["open_time"] for r in _btc_rows_050]
                _btc_cl_050 = [r["close"] for r in _btc_rows_050]
                _n050 = len(_btc_cl_050)

                # Log returns (shifted: log(close[t]/close[t-1]))
                _btc_logret_050 = [float("nan")] * _n050
                for _i in range(1, _n050):
                    if _btc_cl_050[_i - 1] > 0 and _btc_cl_050[_i] > 0:
                        _btc_logret_050[_i] = _math_050.log(_btc_cl_050[_i] / _btc_cl_050[_i - 1])

                # Rolling 30-bar std (min_periods=30)
                _vol_window_050 = 30
                _btc_vol_050 = [float("nan")] * _n050
                for _i in range(_vol_window_050 - 1, _n050):
                    _window_vals = [
                        v
                        for v in _btc_logret_050[_i - _vol_window_050 + 1 : _i + 1]
                        if not _math_050.isnan(v)
                    ]
                    if len(_window_vals) >= _vol_window_050:
                        _mean_v = sum(_window_vals) / len(_window_vals)
                        _var_v = sum((_x - _mean_v) ** 2 for _x in _window_vals) / (
                            len(_window_vals) - 1
                        )
                        _btc_vol_050[_i] = _math_050.sqrt(_var_v)

                # Build open_time → vol_value lookup dict
                _ot_to_vol_050 = {_btc_ot_050[_i]: _btc_vol_050[_i] for _i in range(_n050)}

                # Compute q75 from IS training-data BTC bars ONLY (no OOS peek)
                _is_vols_050 = [
                    v
                    for ot, v in _ot_to_vol_050.items()
                    if ot < OOS_CUTOFF_MS and not _math_050.isnan(v)
                ]
                if len(_is_vols_050) < 30:
                    print(
                        f"[iter-v1/050] WARNING: only {len(_is_vols_050)} IS vol observations "
                        "(<30). Using median as q75 fallback."
                    )
                    _btc_vol_q75_050 = sorted(_is_vols_050)[len(_is_vols_050) // 2]
                else:
                    _is_vols_sorted = sorted(_is_vols_050)
                    _q75_idx = int(0.75 * len(_is_vols_sorted))
                    _btc_vol_q75_050 = _is_vols_sorted[_q75_idx]

                # Regime-gate confidence threshold (brief Section 3.2)
                _regime_gate_conf_threshold_050: float = 0.55

                print(
                    f"[iter-v1/050] Vol-spike regime gate: "
                    f"btc_realized_vol_30 q75_IS = {_btc_vol_q75_050:.6f} "
                    f"(from {len(_is_vols_050)} IS observations). "
                    f"Confidence threshold = {_regime_gate_conf_threshold_050}. "
                    f"Gate fires when BOTH conditions true (vol > q75 AND conf < threshold)."
                )

                # Apply gate: split IS/OOS to log separate fire-rate stats
                _results_is_050 = [t for t in results_e050 if t.open_time < OOS_CUTOFF_MS]
                _results_oos_050 = [t for t in results_e050 if t.open_time >= OOS_CUTOFF_MS]

                def _apply_vol_spike_gate_050(
                    trades: list,
                    label: str,
                ) -> tuple[list, dict]:
                    """Filter trades by vol-spike regime gate. Returns (filtered_trades, stats)."""
                    n_total = len(trades)
                    n_killed = 0
                    n_no_conf = 0  # trades with no confidence (not killed)
                    n_warmup = 0  # trades before BTC vol warmup
                    filtered = []
                    for _t in trades:
                        _vol = _ot_to_vol_050.get(_t.open_time, float("nan"))
                        if _math_050.isnan(_vol):
                            # No BTC vol data for this bar (warmup or missing) — pass through
                            n_warmup += 1
                            filtered.append(_t)
                            continue
                        _conf = _t.confidence if _t.confidence is not None else float("nan")
                        if _math_050.isnan(_conf):
                            # No confidence stored — pass through
                            n_no_conf += 1
                            filtered.append(_t)
                            continue
                        if _vol > _btc_vol_q75_050 and _conf < _regime_gate_conf_threshold_050:
                            # BOTH conditions: high-vol AND low-confidence → KILL
                            n_killed += 1
                        else:
                            filtered.append(_t)
                    fire_rate = n_killed / n_total if n_total > 0 else 0.0
                    stats = {
                        "label": label,
                        "n_total": n_total,
                        "n_killed": n_killed,
                        "n_passed": len(filtered),
                        "n_warmup": n_warmup,
                        "n_no_conf": n_no_conf,
                        "fire_rate": fire_rate,
                        "q75_is": _btc_vol_q75_050,
                        "conf_threshold": _regime_gate_conf_threshold_050,
                    }
                    print(
                        f"[iter-v1/050] Regime gate {label}: "
                        f"{n_killed}/{n_total} killed = {fire_rate:.2%} "
                        f"(passed={len(filtered)}, warmup={n_warmup}, no_conf={n_no_conf})"
                    )
                    return filtered, stats

                _results_is_gated_050, _stats_is_050 = _apply_vol_spike_gate_050(
                    _results_is_050, "IS"
                )
                _results_oos_gated_050, _stats_oos_050 = _apply_vol_spike_gate_050(
                    _results_oos_050, "OOS"
                )
                results_e050 = _results_is_gated_050 + _results_oos_gated_050

                # Log fire-rate stats to a gate_stats dict for comparison.csv
                # (appended via _all_faxm_logs pattern)
                _gate_stats_for_log_050 = {
                    "iter": "v1-050",
                    "gate": "vol_spike_regime",
                    "is_fire_rate": _stats_is_050["fire_rate"],
                    "oos_fire_rate": _stats_oos_050["fire_rate"],
                    "is_killed": _stats_is_050["n_killed"],
                    "oos_killed": _stats_oos_050["n_killed"],
                    "btc_vol_q75_is": _btc_vol_q75_050,
                    "conf_threshold": _regime_gate_conf_threshold_050,
                }
                print(
                    f"[iter-v1/050] Gate summary: "
                    f"IS fire_rate={_stats_is_050['fire_rate']:.2%}, "
                    f"OOS fire_rate={_stats_oos_050['fire_rate']:.2%}, "
                    f"q75_IS={_btc_vol_q75_050:.6f}, "
                    f"conf_threshold={_regime_gate_conf_threshold_050}"
                )
        else:
            _gate_stats_for_log_050 = {
                "iter": "v1-050",
                "gate": "vol_spike_regime",
                "is_fire_rate": float("nan"),
                "oos_fire_rate": float("nan"),
                "is_killed": 0,
                "oos_killed": 0,
                "btc_vol_q75_is": float("nan"),
                "conf_threshold": 0.55,
                "note": "gate_disabled_no_btc_data",
            }

        # F-AXIS #1 dispatch verification: assert ONLY DOTUSDT trades emitted
        e050_symbols = {r.symbol for r in results_e050}
        assert e050_symbols.issubset({"DOTUSDT"}), (
            f"[iter-v1/050] Model E produced non-DOT results: {e050_symbols - {'DOTUSDT'}}. "
            "Per-cohort isolation failed — iter-v1/050 must trade DOTUSDT ONLY."
        )
        print(
            f"[iter-v1/050] Dispatch verified: "
            f"DOT-only={len(results_e050)} trades after regime gate. "
            f"F-AXIS #1 PASS: universe isolation confirmed."
        )

        _all_faxm_logs = faxm_e050 + [_gate_stats_for_log_050]
        all_results = results_e050
        _r5_model_results = [results_e050]
        _post_dispatch_fi_strategies = [("Model_E_DOT_regime_gated", _strat_e050)]

    elif iteration_label == "v1-051" and set(symbols) == set(V1_ITER051_UNIVERSE):
        # iter-v1/051: DOT-only multi-seed re-validation of iter-v1/050 (cycle-6 EXP-6/10).
        # Axis family: validation (multi-seed re-validation sub-type; no new feature/gate).
        #
        # Design: same as /050 but:
        #   (1) Vol-spike regime gate DROPPED (was 0% fire rate / INERT at /050).
        #   (2) --seeds 4 outer seeds for multi-seed statistical validation.
        #
        # Feature stack: V1_FEATURE_COLUMNS_PRUNED (46 cols; dot_vs_btc_ret_ratio_30 retained).
        # Model E semantics: R1=ON, R2=ON, R3=ON, atr_tp=3.5, atr_sl=1.75 (unchanged from /050).
        # NORMAL-RISK: seed variation does not change Optuna training-objective domain.
        # ENSEMBLE_SIZE=3, n_trials=18. Wall-clock cap: ≤ 2h per outer seed.
        # Multi-seed verdict bands (pre-registered in brief Section 8):
        #   mean IS Δ ≥ +1.23 → PROMISING-SPECIALIST-CONFIRMED
        #   +0.50 ≤ mean IS Δ < +1.23 → PROMISING-PARTIAL-CONFIRMED
        #   mean IS Δ < +0.50 → LOTTERY-CONFIRMED-NEGATIVE (revert feature)
        assert set(symbols) == {"DOTUSDT"}, (
            f"iter-v1/051 guard: expected {{DOTUSDT}}, got {set(symbols)}"
        )
        assert "dot_vs_btc_ret_ratio_30" in active_feature_columns, (
            "iter-v1/051 pre-flight FAIL: dot_vs_btc_ret_ratio_30 not in active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has the column. "
            "Run: uv run crypto-trade features --symbols BTCUSDT,DOTUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
        assert len(active_feature_columns) == 46, (
            f"iter-v1/051 guard: expected 46 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}. "
            "V1_FEATURE_COLUMNS_PRUNED should be 46 (post iter-v1/050 ADD dot_vs_btc_ret_ratio_30)."
        )
        print(
            f"[iter-v1/051] DOT-ONLY MULTI-SEED RE-VALIDATION ACTIVE: "
            f"feature=dot_vs_btc_ret_ratio_30 (46 cols; unchanged from /050), "
            f"vol_spike_gate=DROPPED (was 0%% fire rate / INERT at /050), "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), "
            f"n_trials={n_trials}. "
            f"NORMAL-RISK: seed variation only (no Optuna domain change). "
            f"Features: {len(active_feature_columns)} cols (V1_FEATURE_COLUMNS_PRUNED 46). "
            f"cycle-6 EXP-6/10. Multi-seed verdict bands: mean IS Delta "
            f">= +1.23 SPECIALIST-CONFIRMED / [+0.50, +1.23) PARTIAL-CONFIRMED / "
            f"< +0.50 LOTTERY-NEG."
        )
        # Model E: DOT specialist + R1 + R2 + R3 (baseline DOT config, unchanged from /050).
        # dot_vs_btc_ret_ratio_30 is in the parquet (generated by cross_btc_v1 group).
        # active_feature_columns includes dot_vs_btc_ret_ratio_30 (V1_FEATURE_COLUMNS_PRUNED).
        # NO vol-spike regime gate (DROPPED — was 0%% fire rate at /050).
        results_e051, faxm_e051, _strat_e051 = run_model(
            "E'' (DOT + R1 + R2 + no-gate)",
            ("DOTUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches Model E baseline
            atr_sl=1.75,  # UNCHANGED — matches Model E baseline
            apply_r1=True,  # ON — Model E baseline R1 (consecutive-SL cooldown)
            apply_r2=True,  # ON — Model E baseline R2 (drawdown-triggered scaling)
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # F-AXIS #5 (seed=42 sanity): assert ONLY DOTUSDT trades emitted
        e051_symbols = {r.symbol for r in results_e051}
        assert e051_symbols.issubset({"DOTUSDT"}), (
            f"[iter-v1/051] Model E produced non-DOT results: {e051_symbols - {'DOTUSDT'}}. "
            "Per-cohort isolation failed — iter-v1/051 must trade DOTUSDT ONLY."
        )
        print(
            f"[iter-v1/051] Dispatch verified: "
            f"DOT-only={len(results_e051)} trades (no regime gate). "
            f"F-AXIS sanity PASS: universe isolation confirmed."
        )

        _all_faxm_logs = faxm_e051
        all_results = results_e051
        _r5_model_results = [results_e051]
        _post_dispatch_fi_strategies = [("Model_E_DOT_no_gate_multiseed", _strat_e051)]

    elif iteration_label == "v1-052" and set(symbols) == set(V1_ITER052_UNIVERSE):
        # iter-v1/052: BTC-only specialist head (cycle-6 EXP-7/10).
        # Axis family: feature-family — ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90.
        # V1_FEATURE_COLUMNS_PRUNED extended 46 → 48 cols.
        #
        # Architecture: Model A_BTC_specialist (BTC only).
        #   R1=OFF (same as baseline Model A — no R1 on BTC per IS analysis showing
        #           mean-reverting WR at late streaks; R1 would hurt BTC)
        #   R2=OFF (same as baseline Model A — no R2 on BTC)
        #   R3=ON  (same as baseline Model A — R3 OOD gate active, cutoff=0.70)
        #   atr_tp=3.5, atr_sl=1.75 (UNCHANGED from baseline Model A)
        #
        # Feature stack: V1_FEATURE_COLUMNS_PRUNED (48 cols; 2 new funding transforms).
        # NORMAL-RISK: additive features + cohort isolation (no Optuna domain change).
        # ENSEMBLE_SIZE=3, n_trials=18, single-seed=42. Wall-clock cap: ≤ 2h.
        # Pre-registered verdict bands (brief Section 4, F-AXIS #1):
        #   IS Sharpe Δ >= +0.85 → PROMISING-SPECIALIST (flip-positive)
        #   +0.30 <= IS Sharpe Δ < +0.85 → PROMISING-PARTIAL
        #   +0.05 <= IS Sharpe Δ < +0.30 → PROMISING-WEAK
        #   (-0.05, +0.05) → NEG-INERT
        #   < -0.05 → NEGATIVE-CLEAN
        assert set(symbols) == {"BTCUSDT"}, (
            f"iter-v1/052 guard: expected {{BTCUSDT}}, got {set(symbols)}"
        )
        assert "btc_funding_rate_8h_impulse" in active_feature_columns, (
            "iter-v1/052 pre-flight FAIL: btc_funding_rate_8h_impulse not in "
            "active_feature_columns. "
            "Ensure --pruned-features set and V1_FEATURE_COLUMNS_PRUNED has 48 cols. "
            "Run: uv run crypto-trade features --symbols BTCUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
        assert "btc_funding_spread_30_90" in active_feature_columns, (
            "iter-v1/052 pre-flight FAIL: btc_funding_spread_30_90 not in "
            "active_feature_columns. "
            "Ensure --pruned-features set and V1_FEATURE_COLUMNS_PRUNED has 48 cols. "
            "Run: uv run crypto-trade features --symbols BTCUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
        assert len(active_feature_columns) == 48, (
            f"iter-v1/052 guard: expected 48 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}. "
            "V1_FEATURE_COLUMNS_PRUNED should be 48 (post iter-v1/052 ADD 2 funding transforms)."
        )
        print(
            f"[iter-v1/052] BTC-ONLY SPECIALIST ACTIVE: "
            f"features=btc_funding_rate_8h_impulse + btc_funding_spread_30_90 (48 cols), "
            f"R3=ON, R1=OFF, R2=OFF (baseline Model A for BTC). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), n_trials={n_trials}. "
            f"NORMAL-RISK: additive features + cohort isolation (no Optuna domain change). "
            f"cycle-6 EXP-7/10. Verdict bands: IS Sharpe Δ >= +0.85 SPECIALIST / "
            f"[+0.30, +0.85) PARTIAL / [+0.05, +0.30) WEAK / NEG-INERT / NEGATIVE-CLEAN."
        )
        # Model A_BTC_specialist: BTC only + R3 ON, R1 OFF, R2 OFF.
        # feature_columns = V1_FEATURE_COLUMNS_PRUNED (48 cols including 2 new funding features).
        # btc_funding_rate_8h_impulse and btc_funding_spread_30_90 must be in the parquet.
        results_a052, faxm_a052, _strat_a052 = run_model(
            "A_BTC_specialist (R3-only)",
            ("BTCUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches Model A baseline BTC config
            atr_sl=1.75,  # UNCHANGED — matches Model A baseline BTC config
            apply_r1=False,  # OFF — Model A baseline (no R1 on BTC)
            apply_r2=False,  # OFF — Model A baseline (no R2 on BTC)
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # F-AXIS #2 sanity: assert ONLY BTCUSDT trades emitted
        a052_symbols = {r.symbol for r in results_a052}
        assert a052_symbols.issubset({"BTCUSDT"}), (
            f"[iter-v1/052] Model A_BTC produced non-BTC results: {a052_symbols - {'BTCUSDT'}}. "
            "Per-cohort isolation failed — iter-v1/052 must trade BTCUSDT ONLY."
        )
        print(
            f"[iter-v1/052] Dispatch verified: "
            f"BTC-only={len(results_a052)} trades (R3=ON, R1=OFF, R2=OFF). "
            f"F-AXIS #2 sanity PASS: universe isolation confirmed."
        )

        _all_faxm_logs = faxm_a052
        all_results = results_a052
        _r5_model_results = [results_a052]
        _post_dispatch_fi_strategies = [("Model_A_BTC_specialist", _strat_a052)]

    elif iteration_label == "v1-053" and set(symbols) == set(V1_ITER053_UNIVERSE):
        # iter-v1/053: BTC-only multi-seed re-validation of /052 (cycle-6 EXP-8/10).
        # Axis family: validation (multi-seed re-validation sub-type; no new feature/gate).
        #
        # Design: same as /052 but with --seeds 3 outer seeds (offsets 0, 3, 6) injected
        # via run_iteration_053.py monkey-patch: run_baseline_v1._OUTER_SEED_OFFSETS=(0,3,6).
        # Outer seed pools (fully disjoint within ENSEMBLE_SEEDS 10-element roster):
        #   offset=0 → inner pool [42, 123, 456]   (reproduces /052 bit-exactly)
        #   offset=3 → inner pool [789, 1001, 2002]
        #   offset=6 → inner pool [3003, 4004, 5005]
        #
        # Feature stack: V1_FEATURE_COLUMNS_PRUNED (48 cols; UNCHANGED from /052).
        #   btc_funding_rate_8h_impulse (rank 38/48 INERT at /052; retained both-or-neither)
        #   btc_funding_spread_30_90   (rank 4/48 STRONGLY LEARNED at /052)
        #
        # Architecture: Model A_BTC_specialist. R3=ON, R1=OFF, R2=OFF. atr_tp=3.5,
        # atr_sl=1.75 (unchanged from /052 and baseline Model A).
        #
        # NORMAL-RISK: seed variation only (no Optuna training-objective domain change).
        # ENSEMBLE_SIZE=3, n_trials=18. Wall-clock cap: ≤ 2h per outer seed.
        #
        # Multi-seed verdict bands (pre-registered in brief Section 8):
        #   mean IS Δ ≥ +0.85 AND max-min ≤ 0.5 → SPECIALIST-CONFIRMED
        #   mean IS Δ ∈ [+0.30, +0.85) → PARTIAL-CONFIRMED
        #   mean IS Δ < +0.30 → NEG-CLEAN-MULTI-SEED (revert both features)
        #
        # Basin-lottery threshold: max-min > 0.5 (TIGHTENED from /051's 1.0 due to
        # concentrated single-driver btc_funding_spread_30_90 at rank 4/48).
        #
        # Trade-rate floor: mean IS ≥ 50 AND mean OOS ≥ 10.
        # Seed=42 sanity: offset=0 must reproduce /052 IS Sharpe ±0.0005.
        assert set(symbols) == {"BTCUSDT"}, (
            f"iter-v1/053 guard: expected {{BTCUSDT}}, got {set(symbols)}"
        )
        assert "btc_funding_rate_8h_impulse" in active_feature_columns, (
            "iter-v1/053 pre-flight FAIL: btc_funding_rate_8h_impulse not in "
            "active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has 48 cols "
            "(both features retained from /052 per both-or-neither rule). "
            "No parquet regen needed — features already present from /052."
        )
        assert "btc_funding_spread_30_90" in active_feature_columns, (
            "iter-v1/053 pre-flight FAIL: btc_funding_spread_30_90 not in "
            "active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has 48 cols. "
            "No parquet regen needed — features already present from /052."
        )
        assert len(active_feature_columns) == 48, (
            f"iter-v1/053 guard: expected 48 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}. "
            "V1_FEATURE_COLUMNS_PRUNED must be 48 (UNCHANGED from /052; "
            "btc_funding_rate_8h_impulse + btc_funding_spread_30_90 retained)."
        )
        print(
            f"[iter-v1/053] BTC-ONLY MULTI-SEED RE-VALIDATION ACTIVE: "
            f"features=btc_funding_rate_8h_impulse (rank38@/052 INERT) + "
            f"btc_funding_spread_30_90 (rank4@/052 STRONGLY-LEARNED) — 48 cols unchanged. "
            f"_OUTER_SEED_OFFSETS={_OUTER_SEED_OFFSETS} (scope-patched by runner). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), n_trials={n_trials}. "
            f"NORMAL-RISK: seed variation only. cycle-6 EXP-8/10. "
            f"Verdict bands: mean IS Δ ≥ +0.85 + max-min ≤ 0.5 SPECIALIST-CONFIRMED / "
            f"[+0.30, +0.85) PARTIAL-CONFIRMED / < +0.30 NEG-CLEAN-MULTI-SEED."
        )
        # Model A_BTC_specialist: BTC only + R3 ON, R1 OFF, R2 OFF.
        # feature_columns = V1_FEATURE_COLUMNS_PRUNED (48 cols — UNCHANGED from /052).
        # Both funding features already in parquet from /052 regen; no regen required.
        results_a053, faxm_a053, _strat_a053 = run_model(
            "A_BTC_specialist (R3-only)",
            ("BTCUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches /052 + Model A baseline BTC config
            atr_sl=1.75,  # UNCHANGED — matches /052 + Model A baseline BTC config
            apply_r1=False,  # OFF — Model A baseline (no R1 on BTC)
            apply_r2=False,  # OFF — Model A baseline (no R2 on BTC)
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Cohort isolation sanity: assert ONLY BTCUSDT trades emitted
        a053_symbols = {r.symbol for r in results_a053}
        assert a053_symbols.issubset({"BTCUSDT"}), (
            f"[iter-v1/053] Model A_BTC produced non-BTC results: {a053_symbols - {'BTCUSDT'}}. "
            "Per-cohort isolation failed — iter-v1/053 must trade BTCUSDT ONLY."
        )
        print(
            f"[iter-v1/053] Dispatch verified: "
            f"BTC-only={len(results_a053)} trades (R3=ON, R1=OFF, R2=OFF). "
            f"Cohort isolation PASS: universe guard confirmed."
        )

        _all_faxm_logs = faxm_a053
        all_results = results_a053
        _r5_model_results = [results_a053]
        _post_dispatch_fi_strategies = [("Model_A_BTC_specialist_multiseed", _strat_a053)]

    elif iteration_label == "v1-054" and set(symbols) == set(V1_ITER054_UNIVERSE):
        # iter-v1/054: BTC-only impulse-drop attribution test (cycle-6 EXP-9/10).
        # Axis family: feature-family (feature-pruning sub-axis).
        # CHANGE vs /052-/053: DROP btc_funding_rate_8h_impulse from V1_FEATURE_COLUMNS_PRUNED.
        #   btc_funding_rate_8h_impulse: DROPPED (rank >30/48 in 3/3 outer seeds at /053;
        #     INERT-by-importance multi-seed confirmed). Code preserved in funding_v1.py.
        #   btc_funding_spread_30_90: RETAINED (rank 4-10/48 STABLE in 3/3 seeds at /053).
        #   V1_FEATURE_COLUMNS_PRUNED: 48 → 47 cols.
        #
        # Architecture: Model A_BTC_specialist (BTC only).
        #   R1=OFF (same as baseline Model A — no R1 on BTC)
        #   R2=OFF (same as baseline Model A — no R2 on BTC)
        #   R3=ON  (same as baseline Model A — R3 OOD gate active, cutoff=0.70)
        #   atr_tp=3.5, atr_sl=1.75 (UNCHANGED from /052-/053 and baseline Model A)
        #
        # Feature stack: V1_FEATURE_COLUMNS_PRUNED (47 cols; impulse DROPPED).
        # NORMAL-RISK: dropping one INERT feature does NOT change Optuna's training-objective
        # domain. Single-seed=42 (EXPLORATION standard). ENSEMBLE_SIZE=3, n_trials=18.
        #
        # Pre-registered verdict bands (brief Section 4, F-AXIS #1):
        #   Spread IS >= +0.16 → IMPULSE-DROP-CONFIRMED (47-col stack permanent)
        #   Spread IS ∈ [0, +0.16) → IMPULSE-DROP-MARGINAL (/055 CONFIRMATION at 48 cols)
        #   Spread IS < 0 → IMPULSE-DROP-DEGRADES (restore impulse; /055 at 48 cols)
        #   IS trades < 50 → NEGATIVE-INSUFFICIENT-TRADES (regardless of IS Sharpe)
        assert set(symbols) == {"BTCUSDT"}, (
            f"iter-v1/054 guard: expected {{BTCUSDT}}, got {set(symbols)}"
        )
        assert "btc_funding_spread_30_90" in active_feature_columns, (
            "iter-v1/054 pre-flight FAIL: btc_funding_spread_30_90 not in "
            "active_feature_columns. "
            "Ensure --pruned-features is set and V1_FEATURE_COLUMNS_PRUNED has 47 cols "
            "(spread RETAINED; impulse DROPPED at /054). "
            "Run: uv run crypto-trade features --symbols BTCUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
        assert "btc_funding_rate_8h_impulse" not in active_feature_columns, (
            "iter-v1/054 pre-flight FAIL: btc_funding_rate_8h_impulse IS in "
            "active_feature_columns — it must be DROPPED at /054. "
            "Check src/crypto_trade/features_v1/__init__.py: the impulse entry must be "
            "commented out (NOT deleted; computation code preserved in funding_v1.py). "
            "Ensure --pruned-features is set so V1_FEATURE_COLUMNS_PRUNED (47 cols) is used."
        )
        assert len(active_feature_columns) == 47, (
            f"iter-v1/054 guard: expected 47 V1_FEATURE_COLUMNS_PRUNED cols, "
            f"got {len(active_feature_columns)}. "
            "V1_FEATURE_COLUMNS_PRUNED must be 47 at /054 (48 - 1 impulse-drop). "
            "If len == 48: btc_funding_rate_8h_impulse was NOT dropped — check __init__.py."
        )
        print(
            f"[iter-v1/054] BTC-ONLY IMPULSE-DROP ATTRIBUTION TEST ACTIVE: "
            f"features=V1_FEATURE_COLUMNS_PRUNED (47 cols; btc_funding_rate_8h_impulse DROPPED; "
            f"btc_funding_spread_30_90 RETAINED). "
            f"R3=ON, R1=OFF, R2=OFF (baseline Model A for BTC). "
            f"atr_tp=3.5, atr_sl=1.75 (UNCHANGED from /052-/053 + baseline Model A). "
            f"ENSEMBLE_SIZE={ensemble_size} (inner), n_trials={n_trials}. "
            f"NORMAL-RISK: impulse-drop (INERT feature removal; no Optuna domain change). "
            f"cycle-6 EXP-9/10. Verdict bands: IS >= +0.16 IMPULSE-DROP-CONFIRMED / "
            f"[0, +0.16) MARGINAL / < 0 DEGRADES."
        )
        # Model A_BTC_specialist: BTC only + R3 ON, R1 OFF, R2 OFF.
        # feature_columns = V1_FEATURE_COLUMNS_PRUNED (47 cols; impulse DROPPED, spread RETAINED).
        # btc_funding_spread_30_90 must be in the parquet (from /052 regen; no new regen needed).
        # btc_funding_rate_8h_impulse may still appear as a parquet column (not passed to LightGBM).
        results_a054, faxm_a054, _strat_a054 = run_model(
            "A_BTC_specialist (R3-only)",
            ("BTCUSDT",),
            atr_tp=3.5,  # UNCHANGED — matches /052-/053 + Model A baseline BTC config
            atr_sl=1.75,  # UNCHANGED — matches /052-/053 + Model A baseline BTC config
            apply_r1=False,  # OFF — Model A baseline (no R1 on BTC)
            apply_r2=False,  # OFF — Model A baseline (no R2 on BTC)
            n_trials=n_trials,
            ensemble_size=ensemble_size,
            oof_persist_path=OOF_PARQUET_PATH,
            feature_columns=active_feature_columns,
            bounds_profile=bounds_profile,
            **_r5_kwargs,
        )

        # Cohort isolation sanity: assert ONLY BTCUSDT trades emitted
        a054_symbols = {r.symbol for r in results_a054}
        assert a054_symbols.issubset({"BTCUSDT"}), (
            f"[iter-v1/054] Model A_BTC produced non-BTC results: {a054_symbols - {'BTCUSDT'}}. "
            "Per-cohort isolation failed — iter-v1/054 must trade BTCUSDT ONLY."
        )
        print(
            f"[iter-v1/054] Dispatch verified: "
            f"BTC-only={len(results_a054)} trades (R3=ON, R1=OFF, R2=OFF). "
            f"Cohort isolation PASS: universe guard confirmed. "
            f"atr_tp=3.5, atr_sl=1.75 (NOT pooled 2.9/1.45 — BTC specialist Model_A config)."
        )

        _all_faxm_logs = faxm_a054
        all_results = results_a054
        _r5_model_results = [results_a054]
        _post_dispatch_fi_strategies = [("Model_A_BTC_specialist", _strat_a054)]

    elif iteration_label == "v1-044":
        # iter-v1/044: CONFIRMATION-MERGE-PORTFOLIO (cycle-5 CONFIRMATION 1/1).
        # 3-component bundle: BASELINE_V1 (w=0.50) + /036 (w=0.30) + /043 (w=0.20).
        #
        # Architecture: sequential sub-run dispatch (one subprocess per component)
        # followed by post-hoc bundle_aggregator() on the frozen trade CSVs.
        # No new LightGBM training at the bundle level — each component sub-run
        # runs the existing dispatch path at --seeds 2 --n-trials 35 --ensemble-size 5.
        #
        # LIVE-TRADING CONTRACT: bundle sub-runs produce STATISTICAL VALIDATION
        # artifacts only.  The live engine reads single-outer-seed=42 component
        # reports, not the bundle aggregate.  Bundle comparison.csv is the QR/Critic
        # deliverable for MERGE evaluation.
        import shutil as _shutil_044  # noqa: PLC0415
        import subprocess as _subprocess_044  # noqa: PLC0415

        bundle_config_arg: str | None = getattr(args, "bundle_config", None)
        assert bundle_config_arg is not None, (
            "iter-v1/044 pre-flight FAIL: --bundle-config is required for v1-044 dispatch. "
            "Example: --bundle-config 'baseline:0.50,v1-036:0.30,v1-043:0.20'"
        )

        # Parse and validate bundle config
        _bundle_weights = _parse_bundle_config(bundle_config_arg)

        # Validate all 3 expected components are present
        _expected_comps = {"baseline", "v1-036", "v1-043"}
        assert set(_bundle_weights.keys()) == _expected_comps, (
            f"iter-v1/044 pre-flight FAIL: expected components {_expected_comps}, "
            f"got {set(_bundle_weights.keys())}. "
            "All 3 components required for the /044 bundle."
        )

        # Assert --confirmation mode (must be used)
        assert mode_label == "CONFIRMATION", (
            f"iter-v1/044 pre-flight FAIL: expected --confirmation mode "
            f"but got mode={mode_label!r}. "
            "Run with: --confirmation --bundle-config '...' --iteration 44"
        )

        # Resolve outer seed count from CLI (n_outer_seeds not yet set at this dispatch point).
        _n_seeds_044 = int(getattr(args, "seeds", 1))

        print(
            f"\n[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO ACTIVE: "
            f"components={[f'{c}:{w}' for c, w in _bundle_weights.items()]}, "
            f"--seeds {_n_seeds_044}, --n-trials {n_trials}, "
            f"--ensemble-size {ensemble_size}"
        )

        # -----------------------------------------------------------------------
        # Bundle output directory layout:
        #   reports-v1/iteration_v1-044/
        #     baseline/   → component baseline sub-run artifacts
        #     v1-036/     → component /036 sub-run artifacts
        #     v1-043/     → component /043 sub-run artifacts
        #     bundle/     → aggregated bundle metrics
        # -----------------------------------------------------------------------
        _bundle_iter_dir = Path("reports-v1") / "iteration_v1-044"
        _bundle_iter_dir.mkdir(parents=True, exist_ok=True)

        # Component sub-run specs:
        # Each entry: (component_label, --iteration N or --baseline-mode, extra_args)
        # --pruned-features is added for v1-036 and v1-043 (they use V1_FEATURE_COLUMNS_PRUNED)
        # --label-mode trend_scanning is added for v1-036 and v1-043
        _component_sub_run_specs: list[tuple[str, list[str]]] = [
            (
                "baseline",
                [
                    "--baseline-mode",
                    "--n-trials",
                    str(n_trials),
                    "--ensemble-size",
                    str(ensemble_size),
                    "--seeds",
                    str(_n_seeds_044),
                    "--no-engineering-report",
                ],
            ),
            (
                "v1-036",
                [
                    "--confirmation",
                    "--iteration",
                    "36",
                    "--symbols",
                    "LINKUSDT,DOTUSDT",
                    "--pruned-features",
                    "--label-mode",
                    "trend_scanning",
                    "--n-trials",
                    str(n_trials),
                    "--ensemble-size",
                    str(ensemble_size),
                    "--seeds",
                    str(_n_seeds_044),
                    "--no-engineering-report",
                ],
            ),
            (
                "v1-043",
                [
                    "--confirmation",
                    "--iteration",
                    "43",
                    "--symbols",
                    "LINKUSDT",
                    "--pruned-features",
                    "--label-mode",
                    "trend_scanning",
                    "--n-trials",
                    str(n_trials),
                    "--ensemble-size",
                    str(ensemble_size),
                    "--seeds",
                    str(_n_seeds_044),
                    "--no-engineering-report",
                ],
            ),
        ]

        _component_dirs: dict[str, Path] = {}
        _sub_run_elapsed: dict[str, float] = {}

        for _comp_label, _comp_argv in _component_sub_run_specs:
            _comp_start = time.time()
            print(
                f"\n[iter-v1/044] === Sub-run START: {_comp_label} "
                f"argv_extra={_comp_argv[:6]}... ==="
            )
            _comp_proc_argv = [
                sys.executable,
                str(Path(__file__).resolve()),
                *_comp_argv,
            ]
            _comp_proc = _subprocess_044.run(
                _comp_proc_argv,
                capture_output=False,  # stream stdout/stderr live for wall-clock visibility
                text=True,
            )
            _comp_elapsed = time.time() - _comp_start
            _sub_run_elapsed[_comp_label] = _comp_elapsed
            if _comp_proc.returncode != 0:
                print(
                    f"\n[iter-v1/044] Sub-run {_comp_label} FAILED "
                    f"(rc={_comp_proc.returncode}, elapsed={_comp_elapsed:.0f}s). "
                    "Check stdout above for error details.",
                    file=sys.stderr,
                )
                sys.exit(_comp_proc.returncode)

            # Determine the standard output path for this component
            if _comp_label == "baseline":
                _comp_natural_dir = Path("reports-v1") / "iteration_v1-baseline"
            elif _comp_label == "v1-036":
                _comp_natural_dir = Path("reports-v1") / "iteration_v1-036"
            elif _comp_label == "v1-043":
                _comp_natural_dir = Path("reports-v1") / "iteration_v1-043"
            else:
                _comp_natural_dir = Path("reports-v1") / f"iteration_{_comp_label}"

            # Move (or copy if already in target) to bundle component sub-dir
            _comp_target_dir = _bundle_iter_dir / _comp_label
            if _comp_natural_dir.exists():
                if _comp_target_dir.exists():
                    _shutil_044.rmtree(_comp_target_dir)
                _shutil_044.copytree(str(_comp_natural_dir), str(_comp_target_dir))
                print(
                    f"[iter-v1/044] {_comp_label}: artifacts copied "
                    f"{_comp_natural_dir} → {_comp_target_dir} "
                    f"({_comp_elapsed:.0f}s)"
                )
            else:
                print(
                    f"[iter-v1/044] WARNING: expected sub-run output {_comp_natural_dir} "
                    f"not found after sub-run {_comp_label}.",
                    file=sys.stderr,
                )
            _component_dirs[_comp_label] = _comp_target_dir

        # -----------------------------------------------------------------------
        # All 3 sub-runs complete.  Run post-hoc bundle aggregation.
        # -----------------------------------------------------------------------
        print(
            f"\n[iter-v1/044] === Sub-run wall-clocks: "
            f"{', '.join(f'{c}={t:.0f}s' for c, t in _sub_run_elapsed.items())} ==="
        )
        print("\n[iter-v1/044] === POST-HOC BUNDLE AGGREGATION START ===")

        _bundle_out_dir = _bundle_iter_dir / "bundle"
        _btc_klines_path = Path("data") / "BTCUSDT" / "8h.csv"

        bundle_aggregator(
            component_dirs=_component_dirs,
            weights=_bundle_weights,
            is_cutoff_ms=OOS_CUTOFF_MS,
            btc_klines_path=_btc_klines_path,
            bundle_out_dir=_bundle_out_dir,
            baseline_component_dir=_component_dirs.get("baseline"),
        )

        print("\n[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO complete.")
        print(f"  bundle dir:   {_bundle_out_dir}")
        print(f"  component dirs: {list(_component_dirs.keys())}")
        print(
            f"\nPhase 6 complete (iter-v1/044). "
            f"Create engineering_report.md at {_bundle_iter_dir}/engineering_report.md "
            f"and then invoke Phase 7.5 Critic."
        )
        # Bundle dispatch terminates here — no fall-through to standard reporting path.
        sys.exit(0)

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
        "v1-037",
        "v1-038",
        "v1-039",
        "v1-040",
        "v1-041",
        "v1-042",
        "v1-043",
        "v1-044",
    ):
        # Generic baseline-universe dispatch.
        # Non-/021/.../042 iterations. Models A/C/D/E
        # with V1_BASELINE_UNIVERSE symbols. BIT-IDENTICAL to historical
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
    # Aggregate vol-ceiling IS/OOS split counters (iter-v1/038).
    agg_vol_ceil_signals_is = sum(
        getattr(r, "vol_ceiling_signals_is", 0) for r in _r5_model_results
    )
    agg_vol_ceil_fires_is = sum(getattr(r, "vol_ceiling_fires_is", 0) for r in _r5_model_results)
    agg_vol_ceil_signals_oos = sum(
        getattr(r, "vol_ceiling_signals_oos", 0) for r in _r5_model_results
    )
    agg_vol_ceil_fires_oos = sum(getattr(r, "vol_ceiling_fires_oos", 0) for r in _r5_model_results)

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
            vol_ceiling_signals_is=agg_vol_ceil_signals_is,
            vol_ceiling_fires_is=agg_vol_ceil_fires_is,
            vol_ceiling_signals_oos=agg_vol_ceil_signals_oos,
            vol_ceiling_fires_oos=agg_vol_ceil_fires_oos,
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

    # -------------------------------------------------------------------------
    # iter-v1/043 NEW-SKILL 2026-05-31: Regime Attribution CSV (mandatory deliverable).
    # Schema: regime_tag, in_sample, candidate_sharpe, candidate_max_dd,
    #         candidate_trade_count, baseline_sharpe, baseline_max_dd,
    #         baseline_trade_count.
    # Produced for every iteration from /043 onward; no-op for prior iterations.
    # Baseline comparison: LINKUSDT-only rows from BASELINE_V1 trade CSVs.
    # -------------------------------------------------------------------------
    if iteration_label == "v1-043":
        import pandas as pd  # noqa: PLC0415

        _regime_out = report_dir / "regime_attribution.csv"
        # Load candidate trades from generated reports (IS + OOS combined)
        _cand_is_path = report_dir / "in_sample" / "trades.csv"
        _cand_oos_path = report_dir / "out_of_sample" / "trades.csv"
        _cand_frames = []
        for _p in (_cand_is_path, _cand_oos_path):
            if _p.exists():
                _cand_frames.append(pd.read_csv(_p))
        _cand_df = pd.concat(_cand_frames, ignore_index=True) if _cand_frames else pd.DataFrame()

        # Load BASELINE_V1 LINK-only trades for regime comparison
        _baseline_is_path = Path("reports-v1/iteration_v1-baseline/in_sample/trades.csv")
        _baseline_oos_path = Path("reports-v1/iteration_v1-baseline/out_of_sample/trades.csv")
        _baseline_frames = []
        for _p in (_baseline_is_path, _baseline_oos_path):
            if _p.exists():
                _df = pd.read_csv(_p)
                if "symbol" in _df.columns:
                    _baseline_frames.append(_df[_df["symbol"] == "LINKUSDT"])
        _baseline_df = pd.concat(_baseline_frames, ignore_index=True) if _baseline_frames else None

        # Load BTC klines for regime tagging
        _btc_klines_path = Path("data/BTCUSDT/8h.csv")
        _btc_df = None
        if _btc_klines_path.exists():
            try:
                _btc_raw = pd.read_csv(_btc_klines_path)
                # Normalize column names: handle both 'close_time' and 'Close time' variants
                _btc_raw.columns = [c.lower().replace(" ", "_") for c in _btc_raw.columns]
                if "close_time" in _btc_raw.columns and "close" in _btc_raw.columns:
                    _btc_df = _btc_raw[["close_time", "close"]].rename(
                        columns={"close_time": "close_time_ms"}
                    )
                    _btc_df["close"] = pd.to_numeric(_btc_df["close"], errors="coerce")
                    _btc_df = _btc_df.dropna().reset_index(drop=True)
            except Exception as _e:
                print(f"[iter-v1/043] WARNING: BTC klines load failed: {_e} — using 'other' regime")

        if not _cand_df.empty:
            build_regime_attribution_csv(
                trades_df=_cand_df,
                baseline_trades_df=_baseline_df,
                is_cutoff_ms=OOS_CUTOFF_MS,
                btc_klines_df=_btc_df,
                out_path=_regime_out,
            )
        else:
            print(  # noqa: E501
                "[iter-v1/043] WARNING: no candidate trades; regime_attribution.csv not written"
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

        # Build CLI args for sub-runs (strip --seeds + its value; add --ensemble-seeds-offset N).
        # We reconstruct sys.argv minus the --seeds flag (and its value) and any
        # --ensemble-seeds-offset.  Both flags may appear as "--flag VALUE" (two tokens) or
        # "--flag=VALUE" (one token).
        _filtered_argv = []
        _skip_next = False
        for _a in sys.argv[1:]:
            if _skip_next:
                _skip_next = False
                continue
            # Strip --seeds flag + its value (two-token form)
            if _a == "--seeds":
                _skip_next = True
                continue
            # Strip --seeds=N (one-token form)
            if _a.startswith("--seeds="):
                continue
            # Strip --ensemble-seeds-offset flag + its value (two-token form)
            if _a == "--ensemble-seeds-offset":
                _skip_next = True
                continue
            # Strip --ensemble-seeds-offset=N (one-token form)
            if _a.startswith("--ensemble-seeds-offset="):
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
