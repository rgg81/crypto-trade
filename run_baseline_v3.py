"""Baseline v3 runner — iter-v3/013 drop-MKR universe (BCH+LDO+TRX).

Inherits the same universe {BCH, LDO, TRX} (MKR dropped per iter-v3/013
brief Section 3.1; feedback_mkr_threshold_compression.md FIRED) and model
architecture from iter-v3/004–012.  The single architectural change is the per-cell consumer
pipeline for PBO and n_eff computation (iter-v3/004 brief Section 3.5):

  Sub-fix #1: _compute_cpcv_paths rewritten to iterate over (sym, month)
    cells from trial_oof_returns.parquet, compute per-cell CSCV PBO via
    pbo_from_cpcv, persist per_cell_pbo.csv, return cross-cell mean PBO.
  Sub-fix #2: n_eff rewritten to iterate over cells, compute per-cell n_eff
    via n_effective_trials, return median across cells.
  Sub-fix #3: New adversarial test tests/strategies/ml/test_per_cell_pbo_synthetic.py.
  Sub-fix #4: per_cell_pbo.csv written alongside dsr.json for audit trail.
  Sub-fix #5: seed_summary.json "pbo" field is now a float (not literal "NaN").

Reports written to:
  reports-v3/iteration_v3-004/
    in_sample/  out_of_sample/  comparison.csv  pareto_front.csv
    cpcv_paths.csv  adf_test.csv  ic_matrix.csv  dsr.json  run.log
    trial_oof_returns.parquet  per_cell_pbo.csv  (NEW — iter-v3/004)

Usage:
    uv run python run_baseline_v3.py
    uv run python run_baseline_v3.py --seeds 1 --n-trials 50
    uv run python run_baseline_v3.py --skip-features  # reuse existing parquets
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import (
    V3_EXCLUDED_SYMBOLS,
    V3_FEATURE_COLUMNS,
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    atr_multipliers_for_symbol,
    features_for_symbol,
    process_symbol_v3,
)
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy
from crypto_trade.strategies.ml.risk_v2 import (
    BtcTrendFilterConfig,
    HitRateGateConfig,
    RiskV2Config,
    apply_btc_trend_filter,
    apply_hit_rate_gate,
    load_btc_klines_for_filter,
)
from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper
from crypto_trade.strategies.ml.validation_v3 import (
    REQUIRED_GAP,
    PBOResult,
    combinatorial_purged_cv,
    deflated_sharpe_ratio_v3,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)
from crypto_trade.strategies.ml.xgb import XgboostStrategy

# ============================================================
# Constants — DO NOT CHANGE
# ============================================================
OOS_CUTOFF_DATE = "2025-03-24"  # IMMUTABLE
TRAINING_MONTHS = 24  # IMMUTABLE

# Inner ensemble size (number of seeds combined inside LightGbmStrategy per
# outer seed). Pre-iter-v3/006: a hardcoded constant [42, 123, 456, 789, 1001]
# was passed for ALL outer seeds, so --seeds N produced N IDENTICAL ensembles.
# iter-v3/006 fix: each outer seed now derives a distinct 5-seed inner ensemble
# via `_derive_ensemble_seeds(outer_seed)`. The legacy seed list is preserved
# below for documentation only — it is no longer passed to LightGbmStrategy.
CONFIRMATION_ENSEMBLE_SIZE: int = 10  # CONFIRMATION mode: full unified 10-seed ensemble
# EXPLORATION mode: outer=42-lineage prefix (ENSEMBLE_SEEDS[0:3]); ~1.1h wall-clock
EXPLORATION_ENSEMBLE_SIZE: int = 3
ENSEMBLE_SIZE: int = CONFIRMATION_ENSEMBLE_SIZE  # backward-compat alias; do not change

# Lineage-preserving seed list: first 5 derived from outer=42, last 5 from outer=123
# via legacy _derive_ensemble_seeds.  Hardcoded here for reproducibility and to
# eliminate the outer-seed loop concept.  Values verified by Python REPL:
#   _derive_ensemble_seeds(42,  5) → [191664963, 1662057957, 1405681631, 942484272, 929893137]
#   _derive_ensemble_seeds(123, 5) → [33158374, 1465339467, 1273345680, 115579757, 1952249162]
ENSEMBLE_SEEDS: tuple[int, ...] = (
    191664963,
    1662057957,
    1405681631,
    942484272,
    929893137,  # outer=42 lineage
    33158374,
    1465339467,
    1273345680,
    115579757,
    1952249162,  # outer=123 lineage
)

LEGACY_ENSEMBLE_SEEDS: list[int] = [42, 123, 456, 789, 1001]  # iter-v3/001-005


def _derive_ensemble_seeds(outer_seed: int, size: int = 5) -> list[int]:
    """Deterministically derive `size` inner-ensemble seeds from one outer seed.

    Replaces the pre-iter-v3/006 hardcoded ENSEMBLE_SEEDS that was identical
    across all outer seeds. With this fix, --seeds N produces N distinct
    LightGBM ensembles (the prerequisite for any meaningful 10-seed Pareto
    validation per project memory's seed-validation rule).
    """
    rng = np.random.default_rng(outer_seed)
    return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]


ITERATION_LABEL = "v3-064"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")

# v3 symbols — iter-v3/051: SYSTEM-LEVEL REVERT to iter-v3/028 architecture.
# Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
# confirmation of per-symbol-customization anti-pattern at iter-v3/039 + iter-v3/050
# both CONFIRMATION-NO-MERGE on per-symbol bundle). ALGOUSDT REVERTED (4→3 symbols).
# REQUIRED_GAP updated 88→66 = (21+1)×3 per system-level REVERT.
# Per `analysis/iteration_v3-051/synthesis.md` SHA `290f37b` (cycle 4 #1 EDA).
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)

# Risk gate configs (v2 5-gate + BTC; no R1/R2/R3 — brief Section 3.4)
HIT_RATE_CONFIG = HitRateGateConfig(
    window=20,
    sl_threshold=0.65,
    enabled=False,  # Disabled per iter-v2/045 lesson
)

BTC_TREND_CONFIG = BtcTrendFilterConfig(
    lookback_bars=42,  # 14 days of 8h bars
    threshold_pct=15.0,
    enabled=True,
)

# CPCV parameters (brief Section 0 + 3.5#2)
CPCV_N_SPLITS = 10
CPCV_N_TEST_SPLITS = 2
# gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = (21+1)*3 = 66 (iter-v3/051 REVERT to 3-sym)
# DO NOT use min(REQUIRED_GAP, n_trades//20) — that is the iter-v3/001 bug.
CPCV_EMBARGO = 27  # ~1% of 24-month T ≈ 2742 candles * 0.01


# ============================================================
# Pre-flight checks
# ============================================================


def _verify_branch() -> None:
    """Enforce git workflow guardrail: v3 runs from iteration-v3/* or quant-research."""
    branch = subprocess.check_output(
        ["git", "--no-optional-locks", "branch", "--show-current"],
        text=True,
    ).strip()
    allowed = branch.startswith("iteration-v3/") or branch in ("quant-research", "main")
    if not allowed:
        raise RuntimeError(
            f"v3 runner must run from iteration-v3/*, quant-research, or main; got: {branch}"
        )


def _verify_symbols(symbols: tuple[str, ...]) -> None:
    """Hard assert: no v1/v2 symbols in v3 universe."""
    overlap = set(symbols) & set(V3_EXCLUDED_SYMBOLS)
    if overlap:
        raise RuntimeError(
            f"v3 runner cannot trade v1/v2 symbols: {sorted(overlap)}\n"
            f"V3_EXCLUDED_SYMBOLS = {V3_EXCLUDED_SYMBOLS}"
        )


def _verify_data_freshness(symbols: tuple[str, ...], max_lag_hours: float = 16.0) -> None:
    """Hard-fail on stale data (>16h lag)."""
    now_ms = int(time.time() * 1000)
    stale: list[tuple[str, float]] = []
    for sym in symbols:
        p = DATA_DIR / sym / "8h.csv"
        if not p.exists():
            raise RuntimeError(f"v3 runner: missing CSV for {sym} at {p}")
        df = pd.read_csv(p, usecols=["close_time"])
        last_close = int(df["close_time"].max())
        lag_h = (now_ms - last_close) / 3_600_000
        if lag_h > max_lag_hours:
            stale.append((sym, round(lag_h, 1)))
    if stale:
        raise RuntimeError(
            f"v3 runner: STALE DATA (>{max_lag_hours}h lag): {stale}. "
            f"Run `uv run crypto-trade fetch --symbols {','.join(symbols)} --intervals 8h`"
        )


def _verify_feature_columns(ensemble_size: int | None = None) -> None:
    """Verifies V3_FEATURE_COLUMNS contents per current brief (iter-v3/063).

    Parameters
    ----------
    ensemble_size:
        Effective ensemble size for this run (3 = EXPLORATION, 10 = CONFIRMATION).
        If provided, asserts the value is in (3, 10) to enforce mode discipline.
        If None, skips the ensemble-size mode check (backward compat for direct
        calls in unit tests that don't care about mode).


    iter-v3/061: CYCLE 1 #2 EXPLORATION — TRX-specific RiskV2 vol_scale_floor=0.5 (Path B).
      Axis: per-symbol vol_scale_floor per Critic /060 Rec #3 + QR EDA SHA d198b25.
      Code changes: RiskV2Config.vol_scale_floor_per_symbol={"TRXUSDT": 0.5}; BCH/LDO unchanged.
      Feature bundle IDENTICAL to /060 (no feature changes).
      ITERATION_LABEL = "v3-061".
      Counterfactual: +0.47 OOS wpnl TRX lift; IS bit-identical (+0.008 wpnl).
      Expected classification: INERT-AT-EXPLORATION (~55% probability per Section 7).

    iter-v3/060: CYCLE 1 #1 EXPLORATION — EXPLORATION-MODE-REFERENCE establishment + TRX diagnostic.
      Mode-flag refactor commit `56f5a30`: --exploration CLI flag (EXPLORATION_ENSEMBLE_SIZE=3
        / CONFIRMATION_ENSEMBLE_SIZE=10). User directive 2026-05-13:
        "use 10 seeds only for CONFIRMATION."
      ITERATION_LABEL = "v3-060" — first 3-seed EXPLORATION-mode run; bundle IDENTICAL to /059.
      Cycle 1 cadence: 10 EXPLORATIONs (/060-069) at 3 seeds (~1.1h each)
        → 1 CONFIRMATION (/070) at 10 seeds.

    iter-v3/059: RE-ANCHOR #2 — /028 bundle under unified 10-seed ensemble architecture.
      Phase A commit `0a3c30e`: Optuna n_jobs=2 parallelization —
        REVERTED at `31665f6` (5x GIL slowdown).
      Phase B-3 commit `ab2d9ac`: unified 10-seed ensemble (ENSEMBLE_SIZE=10, ENSEMBLE_SEEDS
        hardcoded as lineage-preserving 10-value tuple; outer-seed loop eliminated).
      Walk-forward fix commit `e149e9d` (cherry-picked from main `5566a69`): post-fix WF.
      ITERATION_LABEL = "v3-059" (only change vs /058 Phase-B-3 prep state).
      Bundle IDENTICAL to /028 BASELINE_V3.md / /058 RE-ANCHOR #1.
      Carry-forward SYSTEM-LEVEL architecture (UNCHANGED from /058):
      - V3_MODELS = (BCH, LDO, TRX) — 3 symbols.
      - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY — SYSTEM-LEVEL REVERT at /051).
      - block_long_for = () (REVERT — primitive 10 cleared at /051).
      - REQUIRED_GAP = 66 = (21+1)*3 (UNCHANGED — universe unchanged).
      - DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — unchanged.
      - V3_FEATURES_PER_SYMBOL: EMPTY (unchanged from iter-v3/040).
      - adx_threshold_per_symbol: {} (unchanged; TRX 21 dropped at iter-v3/050 closeout).
      ENSEMBLE_SIZE = 10 (unified 10-seed; replaces 2-outer × 5-inner architecture).

    tbr_zscore_30 MUST NOT be present (dropped iter-v3/016).
    vwap_dev_50 MUST NOT be present (dropped iter-v3/008 per Critic SHA a544621).
    funding_rate_zscore_30 MUST NOT be present (per-symbol variant PERMANENTLY-CLOSED).
    btc_funding_rate_zscore_30 MUST NOT be present (cross-asset variant PERMANENTLY-CLOSED).
    vol_adj_autocorr MUST NOT be in universal list (dead code since iter-v3/036 revert).
    cross_asset_divergence_norm MUST NOT be in universal list (dead at model level).
    fracdiff_d05_close MUST NOT be in universal list (PARKED at iter-v3/052 SWAP).
    efficiency_ratio_50 MUST NOT be present (DROPPED — iter-v3/043 DISASTROUS NEGATIVE).
    regime_momentum_signed_5d MUST be present (mandate still ACTIVE at iter-v3/059).
    vol_normalized_ret_5d MUST NOT be present (DROPPED iter-v3/049; iter-v3/048 PATH C-clean).
    hurst_drift_50_200 MUST NOT be present (PARKED per /053 PATH D + Critic FINAL `c056354`).
    regime_momentum_signed_3d MUST NOT be present (PARKED per /052 PATH C-suspicious).
    sym_vs_btc_ret_7d MUST be present (RESTORED at iter-v3/042; KEPT at iter-v3/059).
    ret_skew_50 MUST be present (RESTORED iter-v3/058 RE-ANCHOR — /028 BASELINE_V3.md).
    parkinson_gk_ratio_20 MUST NOT be present (REVERTED at iter-v3/058 RE-ANCHOR).

    Per-symbol checks (iter-v3/054 — REVERT carry-forward from /051):
    V3_FEATURES_PER_SYMBOL must be EMPTY (0 entries).
    V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries — REVERT; all syms use DEFAULT).
      ALGOUSDT MUST NOT be a key (REVERTED at iter-v3/051; unchanged at /052-/059).
      LDOUSDT  MUST NOT be a key (REVERTED at iter-v3/051; unchanged at /052-/059).
    features_for_symbol("BCHUSDT") MUST return 14 features = V3_FEATURE_COLUMNS_TOP_N.
    features_for_symbol("LDOUSDT") MUST return 14 features (fallback — no per-symbol ext).
    features_for_symbol("TRXUSDT") MUST return 14 features (fallback).
    atr_multipliers_for_symbol("BCHUSDT") MUST return (2.0, 1.0) (DEFAULT fallback).
    atr_multipliers_for_symbol("LDOUSDT") MUST return (2.0, 1.0) (DEFAULT fallback — REVERT).
    atr_multipliers_for_symbol("TRXUSDT") MUST return (2.0, 1.0) (DEFAULT fallback).
    DEFAULT_ATR_MULTIPLIERS MUST be (2.0, 1.0) (correct since iter-v3/043 revert).
    Primitive 10 (REVERT): risk_cfg.block_long_for == () (empty — system-level REVERT).
    Primitive 11 (DISABLED): risk_cfg.enable_per_symbol_drawdown_brake == False (/028 baseline).
    Per-symbol ADX (UNCHANGED): risk_cfg.adx_threshold_per_symbol == {} (empty; TRX 21
      dropped at iter-v3/050 closeout per Critic FINAL `1908d50`; unchanged at /059).
    """
    from crypto_trade.features_v3 import (  # noqa: PLC0415
        DEFAULT_ATR_MULTIPLIERS,
        V3_ATR_MULTIPLIERS_PER_SYMBOL,
        atr_multipliers_for_symbol,
    )

    # iter-v3/059 RE-ANCHOR #2: unified ensemble architecture — ensemble_size must be 3 or 10.
    # 3 = EXPLORATION mode (ENSEMBLE_SEEDS[0:3], outer=42 lineage subset).
    # 10 = CONFIRMATION mode (full ENSEMBLE_SEEDS tuple, both outer lineages).
    if ensemble_size is not None:
        assert ensemble_size in (EXPLORATION_ENSEMBLE_SIZE, CONFIRMATION_ENSEMBLE_SIZE), (
            f"ensemble_size={ensemble_size} is not a valid mode. "
            f"EXPLORATION mode uses EXPLORATION_ENSEMBLE_SIZE={EXPLORATION_ENSEMBLE_SIZE}; "
            f"CONFIRMATION mode uses CONFIRMATION_ENSEMBLE_SIZE={CONFIRMATION_ENSEMBLE_SIZE}. "
            "Pass either 3 (--exploration) or 10 (default CONFIRMATION)."
        )

    # iter-v3/064: PHASED MASS-EXPANSION #1 — REVERT to 14-feature anchor + ADD adx_14 = 15.
    # /063 mass-expansion (14 → 46) at single-seed n_trials=35 produced SUSPICIOUS-OOS-DOMINANT
    # + IS-COLLAPSE (Critic FINAL `7cbc136`; diary `937f7d6`); axis CLOSED.
    # /064 is phased-mass-expansion #1 per amended `feedback_v3_mass_feature_expansion.md`
    # (2026-05-14 amendment): single-feature additions at single-seed EXPLORATION.
    # vol_adj_autocorr and efficiency_ratio_50 (the two CATASTROPHICALLY NEGATIVE features)
    # remain EXCLUDED. The 31 non-baseline /063 features are all DROPPED for /064.
    n = len(V3_FEATURE_COLUMNS)
    if n != 15:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 15. "
            "iter-v3/064: PHASED MASS-EXPANSION #1 (REVERT to 14-feature anchor + ADD adx_14). "
            "Expected: 14 BASELINE_V3 features + adx_14. "
            "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # vol_adj_autocorr MUST NOT be in the universal list (iter-v3/036 NEGATIVE reverted;
    # catastrophically bad IS collapse at single-seed n_trials=35; dead code retained).
    if "vol_adj_autocorr" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS (universal list) — must be ABSENT. "
            "iter-v3/037: iter-v3/036 NEGATIVE reverted; vol_adj_autocorr is dead code. "
            "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # efficiency_ratio_50 MUST be ABSENT (unsigned Kaufman ER — DISASTROUS NEGATIVE iter-v3/043).
    # NOTE: trend_efficiency_signed (signed variant) IS ALLOWED at iter-v3/063
    # — different mechanism (signed vs unsigned Kaufman ER).
    if "efficiency_ratio_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "at iter-v3/063 (DROPPED at iter-v3/044: iter-v3/043 DISASTROUS NEGATIVE IS -0.8445 / "
            "OOS -0.8990; all 4 symbols broken by unsigned Kaufman ER). "
            "The SIGNED variant 'trend_efficiency_signed' is the /063 NEW feature. "
            "Remove 'efficiency_ratio_50' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    if "vwap_dev_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "vwap_dev_50 found in V3_FEATURE_COLUMNS — must be dropped per "
            "Critic FINAL SHA a544621 (Recommendation 1; IC 0.875 with ema_spread_atr_20). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # regime_momentum_signed_5d MUST be present
    # (mandate from feedback_v3_engineered_features_proven.md).
    if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT. "
            "feedback_v3_engineered_features_proven.md mandate ACTIVE. "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # sym_vs_btc_ret_7d MUST be present (BASELINE_V3 feature).
    if "sym_vs_btc_ret_7d" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT. "
            "BASELINE_V3 feature (RESTORED at iter-v3/042; KEPT). "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # ret_skew_50 MUST be present (BASELINE_V3 feature).
    if "ret_skew_50" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT. "
            "BASELINE_V3 feature (RESTORED iter-v3/058 RE-ANCHOR; /028 BASELINE_V3.md). "
            "Add it back to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # regime_momentum_signed_3d MUST NOT be present (PARKED per /053 PATH C-suspicious).
    if "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS — must be ABSENT. "
            "PARKED per /052 PATH C-suspicious closeout; Critic `34cc46f` rec #2. "
            "Remove 'regime_momentum_signed_3d' from V3_FEATURE_COLUMNS_TOP_N."
        )
    # iter-v3/064: adx_14 MUST be present (PHASED MASS-EXPANSION #1 — single-feature addition).
    # The other 8 NEW features from /063 (candle_dow_sin/cos, ret_1d, sym_vs_btc_ret_3d,
    # sym_vs_btc_vol_14d, taker_buy_imbalance_20, trend_efficiency_signed,
    # vol_regime_x_momentum) are NOT present at /064 — REVERTED with the 46-feature set.
    # They can be considered for phased-mass-expansion #2+ individually.
    if "adx_14" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "adx_14 NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT at iter-v3/064. "
            "PHASED MASS-EXPANSION #1: REVERT to 14-feature anchor + ADD adx_14. "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # /063 NEW features that MUST be ABSENT at /064 (REVERTED with mass expansion).
    _reverted_063_features = (
        "candle_dow_sin",
        "candle_dow_cos",
        "ret_1d",
        "sym_vs_btc_ret_3d",
        "sym_vs_btc_vol_14d",
        "taker_buy_imbalance_20",
        "trend_efficiency_signed",
        "vol_regime_x_momentum",
    )
    for _feat in _reverted_063_features:
        if _feat in V3_FEATURE_COLUMNS:
            raise RuntimeError(
                f"iter-v3/063 NEW feature '{_feat}' FOUND in V3_FEATURE_COLUMNS — must be "
                "ABSENT at iter-v3/064 (PHASED MASS-EXPANSION #1 — single-feature axis). "
                "These 8 features are REVERTED with the 46-feature /063 set; only adx_14 retained. "
                f"Remove '{_feat}' from V3_FEATURE_COLUMNS_TOP_N. Per amended "
                "`feedback_v3_mass_feature_expansion.md` (2026-05-14 amendment)."
            )
    print(
        f"  V3_FEATURE_COLUMNS: {n} columns "
        "(iter-v3/064: PHASED MASS-EXPANSION #1; "
        "14 BASELINE_V3 features present; "
        "1 NEW feature (adx_14) PRESENT; "
        "8 /063-NEW features (candle_dow_sin/cos, ret_1d, sym_vs_btc_ret_3d, "
        "sym_vs_btc_vol_14d, taker_buy_imbalance_20, trend_efficiency_signed, "
        "vol_regime_x_momentum) REVERTED-ABSENT; "
        "vol_adj_autocorr ABSENT; efficiency_ratio_50 ABSENT; "
        "regime_momentum_signed_5d PRESENT; sym_vs_btc_ret_7d PRESENT)  PASS"
    )

    # iter-v3/044: Verify DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0).
    # Already correct since iter-v3/043 revert (was (1.5, 0.75) only at iter-v3/042).
    if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.0):
        raise RuntimeError(
            f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
            "iter-v3/047: DEFAULT_ATR_MULTIPLIERS must be (2.0, 1.0) (reverted at iter-v3/043). "
            "TRX + BCH use DEFAULT via V3_ATR_MULTIPLIERS_PER_SYMBOL fallback. "
            "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
        )
    print("  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) (already correct since iter-v3/043 revert)  PASS")

    # iter-v3/044: V3_FEATURES_PER_SYMBOL MUST BE EMPTY.
    # All per-symbol feature customizations reverted. All symbols use 14-feature fallback.
    n_custom = len(V3_FEATURES_PER_SYMBOL)
    if n_custom != 0:
        raise RuntimeError(
            f"V3_FEATURES_PER_SYMBOL has {n_custom} entries — expected exactly 0 (empty). "
            "iter-v3/040: REVERT all per-symbol feature overrides (cycle 3 EXPLORATION #1). "
            f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}. "
            "Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
        )
    print("  V3_FEATURES_PER_SYMBOL: 0 entries (empty — all symbols use 14-feature fallback)  PASS")

    # iter-v3/051: V3_ATR_MULTIPLIERS_PER_SYMBOL MUST be EMPTY (0 entries — SYSTEM-LEVEL REVERT).
    # Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
    # confirmation of per-symbol-customization anti-pattern). ALGOUSDT and LDOUSDT entries
    # REVERTED. All 3 symbols (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    n_atr_custom = len(V3_ATR_MULTIPLIERS_PER_SYMBOL)
    if n_atr_custom != 0:
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL has {n_atr_custom} entries — expected exactly 0 "
            "(EMPTY; iter-v3/051 SYSTEM-LEVEL REVERT to iter-v3/028 baseline architecture). "
            "ALGOUSDT and LDOUSDT entries must be cleared per "
            "`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10. "
            f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}. "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL = {{}} in features_v3/__init__.py."
        )
    print(
        "  V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries (EMPTY — SYSTEM-LEVEL REVERT to /028; "
        "BCH/LDO/TRX all use (2.0, 1.0) DEFAULT)  PASS"
    )

    # iter-v3/064: Verify all 3 v3 symbols return 15-feature fallback (V3_FEATURE_COLUMNS_TOP_N).
    # PHASED MASS-EXPANSION #1: 14 BASELINE_V3 + adx_14 = 15. V3_FEATURES_PER_SYMBOL is empty.
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        sym_feats = features_for_symbol(sym)
        if len(sym_feats) != 15:
            raise RuntimeError(
                f"{sym} fallback has {len(sym_feats)} features — "
                "expected exactly 15 (iter-v3/064 PHASED MASS-EXPANSION #1). "
                "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py. "
                "V3_FEATURES_PER_SYMBOL must be empty."
            )
        if "adx_14" not in sym_feats:
            raise RuntimeError(
                f"{sym} feature set does not contain adx_14 — must be PRESENT. "
                "iter-v3/064 PHASED MASS-EXPANSION #1: adx_14 is the single-feature axis."
            )
        if "ret_skew_50" not in sym_feats:
            raise RuntimeError(
                f"{sym} feature set does not contain ret_skew_50 — must be PRESENT. "
                "BASELINE_V3 feature. Add 'ret_skew_50' to V3_FEATURE_COLUMNS_TOP_N."
            )
        if "regime_momentum_signed_3d" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains regime_momentum_signed_3d — must be ABSENT. "
                "PARKED per /053 PATH C-suspicious closeout. "
                f"Check V3_FEATURE_COLUMNS_TOP_N and features_for_symbol('{sym}') path."
            )
        if "efficiency_ratio_50" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains efficiency_ratio_50 — must be ABSENT. "
                "iter-v3/044: DISASTROUS NEGATIVE. Use 'trend_efficiency_signed' instead. "
                f"Check features_for_symbol('{sym}') path."
            )
    print(
        "  BCH/LDO/TRX: 15-feature universal fallback "
        "(iter-v3/064: PHASED MASS-EXPANSION #1; "
        "14 BASELINE_V3 features present; adx_14 PRESENT; "
        "8 /063-NEW features REVERTED-ABSENT; "
        "vol_adj_autocorr ABSENT; efficiency_ratio_50 ABSENT; "
        "regime_momentum_signed_5d, sym_vs_btc_ret_7d PRESENT)  PASS"
    )

    # iter-v3/051: All 3 symbols (BCH/LDO/TRX) MUST return (2.0, 1.0) via DEFAULT fallback.
    # SYSTEM-LEVEL REVERT — V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; no per-symbol overrides.
    for _sym_atr in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        sym_atr = atr_multipliers_for_symbol(_sym_atr)
        if sym_atr != (2.0, 1.0):
            raise RuntimeError(
                f"atr_multipliers_for_symbol('{_sym_atr}') returned {sym_atr} — "
                "expected (2.0, 1.0) (DEFAULT fallback). "
                "iter-v3/051: SYSTEM-LEVEL REVERT — V3_ATR_MULTIPLIERS_PER_SYMBOL must be "
                "EMPTY; all 3 symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0). "
                "Clear V3_ATR_MULTIPLIERS_PER_SYMBOL = {{}} in features_v3/__init__.py."
            )
    print(
        "  atr_multipliers_for_symbol: BCH/LDO/TRX all (2.0, 1.0) DEFAULT "
        "(SYSTEM-LEVEL REVERT at iter-v3/051; V3_ATR_MULTIPLIERS_PER_SYMBOL EMPTY)  PASS"
    )

    # iter-v3/051: Primitive 10 REVERT — block_long_for=() per system-level rule.
    # `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 mandates
    # clearing per-symbol customizations. block_long_for was ("BCHUSDT",) at iter-v3/047-050.
    # Cycle 4 starting baseline = iter-v3/028 architecture (no primitive 10).
    _cfg_check, strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model returned {type(strat_check).__name__} — expected RiskV3Wrapper. "
            "iter-v3/051: primitive 10 REVERT check requires RiskV3Wrapper. "
            "Check _build_v3_model returns RiskV3Wrapper."
        )
    if strat_check.config.block_long_for != ():
        raise RuntimeError(
            f"RiskV2Config.block_long_for = {strat_check.config.block_long_for} — "
            "expected () (empty). iter-v3/051: SYSTEM-LEVEL REVERT — primitive 10 "
            "(direction-asymmetric kill switch) REVERTED. block_long_for must be empty. "
            "Set block_long_for=() in RiskV2Config init in _build_v3_model."
        )
    if strat_check.config.block_short_for != ():
        raise RuntimeError(
            f"RiskV2Config.block_short_for = {strat_check.config.block_short_for} — "
            "expected () (empty). iter-v3/051: block_short_for must remain empty. "
            "Set block_short_for=() in RiskV2Config init in _build_v3_model."
        )
    print(
        "  Primitive 10 (direction-asymmetric kill switch): block_long_for=(); "
        "block_short_for=() (SYSTEM-LEVEL REVERT at iter-v3/051)  PASS"
    )

    # iter-v3/044: regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N (mandate ACTIVE).
    if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be "
            "PRESENT at iter-v3/044. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print("  regime_momentum_signed_5d PRESENT in V3_FEATURE_COLUMNS_TOP_N (mandate ACTIVE)  PASS")

    # iter-v3/049: vol_normalized_ret_5d MUST NOT be in V3_FEATURE_COLUMNS_TOP_N (DROPPED).
    # Reverted from iter-v3/048 (PATH C-clean: ranked 13-15/15 across all 4 symbols;
    # IS Sharpe Δ -0.43 + OOS Sharpe Δ -3.15; saturation rule fires).
    if "vol_normalized_ret_5d" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "vol_normalized_ret_5d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/049. DROPPED per iter-v3/048 PATH C-clean closeout (ranked 13-15/15 "
            "across all 4 symbols; IS Sharpe Δ -0.43 + OOS Sharpe Δ -3.15 vs anchor). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print(
        "  vol_normalized_ret_5d ABSENT from V3_FEATURE_COLUMNS_TOP_N "
        "(DROPPED iter-v3/049 per iter-v3/048 PATH C-clean closeout)  PASS"
    )

    # iter-v3/054: hurst_drift_50_200 MUST be ABSENT (PARKED per /053 PATH D NULL-RESULT).
    # 15th-slot SWAP family STRUCTURALLY EXHAUSTED: CPCV 29/45, median +0.3351, Q25 -0.243
    # IDENTICAL across /051/052/053 to 4 decimals — Critic FINAL `c056354` rec #1.
    # compute_hurst_drift_50_200 RETAINED in engineered_v3.py as dead code (zero revert cost).
    if "hurst_drift_50_200" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "hurst_drift_50_200 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/054. PARKED per /053 PATH D NULL-RESULT closeout + Critic FINAL "
            "`c056354` rec #1 (15th-slot SWAP family exhausted; CPCV invariant across "
            "/051/052/053). compute_hurst_drift_50_200 retained in engineered_v3.py as "
            "dead code. Remove 'hurst_drift_50_200' from V3_FEATURE_COLUMNS_TOP_N in "
            "src/crypto_trade/features_v3/__init__.py."
        )
    print(
        "  hurst_drift_50_200 ABSENT from V3_FEATURE_COLUMNS_TOP_N "
        "(PARKED iter-v3/054 per /053 PATH D + Critic FINAL `c056354`)  PASS"
    )

    # iter-v3/053: regime_momentum_signed_3d MUST be ABSENT (PARKED per /052 PATH C-suspicious).
    # Critic FINAL `34cc46f` rec #2: pivot to structurally distinct feature family.
    # compute_regime_momentum_signed_3d dispatch RETAINED as dead code (zero revert cost).
    if "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/053. PARKED per /052 PATH C-suspicious closeout (rank 14-15/15 all "
            "3 symbols; IS-OOS daily ratio 2.327 OUT-OF-BAND). Critic FINAL `34cc46f` rec #2. "
            "Remove 'regime_momentum_signed_3d' from V3_FEATURE_COLUMNS_TOP_N in "
            "src/crypto_trade/features_v3/__init__.py."
        )
    print(
        "  regime_momentum_signed_3d ABSENT from V3_FEATURE_COLUMNS_TOP_N "
        "(PARKED per /052 PATH C-suspicious; compute function retained as dead code)  PASS"
    )

    # iter-v3/044: efficiency_ratio_50 MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N (DROPPED).
    if "efficiency_ratio_50" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/044 (DROPPED: iter-v3/043 DISASTROUS NEGATIVE; all 4 symbols broken). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print("  efficiency_ratio_50 ABSENT from V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/044)  PASS")

    # iter-v3/051: Verify per-symbol ADX threshold is still EMPTY (UNCHANGED from /050).
    # Critic FINAL `1908d50` recommendation #2 at iter-v3/050 closeout: adx_threshold_per_symbol
    # was cleared (TRX 21 dropped); remains empty at iter-v3/051.
    _trx_cfg_check, trx_strat_check = _build_v3_model(
        symbol="TRXUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(trx_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model(TRXUSDT) returned {type(trx_strat_check).__name__} — "
            "expected RiskV3Wrapper. iter-v3/051: per-symbol ADX EMPTY check requires "
            "RiskV3Wrapper. Check _build_v3_model returns RiskV3Wrapper."
        )
    if trx_strat_check.config.adx_threshold_per_symbol != {}:
        raise RuntimeError(
            f"RiskV2Config.adx_threshold_per_symbol = "
            f"{trx_strat_check.config.adx_threshold_per_symbol} — expected {{}} (EMPTY). "
            "iter-v3/051: per-symbol ADX must remain empty (TRX 21 dropped at iter-v3/050). "
            "Set adx_threshold_per_symbol={{}} in RiskV2Config init in _build_v3_model."
        )
    print(
        "  Per-symbol ADX threshold (iter-v3/051): {} (EMPTY UNCHANGED — TRX 21 already "
        "dropped at iter-v3/050; global ADX threshold 20.0 applies to all 3 symbols)  PASS"
    )

    # iter-v3/055: Primitive 11 (per-symbol drawdown brake) MUST be DISABLED.
    # CLOSED-mechanism per iter-v3/054 closeout: brake deadlock suppressed all OOS trades.
    # Backward-compatible defaults (T=10.0, recovery=5.0, window=30) retained in config.
    _p11_cfg_check, p11_strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(p11_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model returned {type(p11_strat_check).__name__} — expected RiskV3Wrapper. "
            "iter-v3/055: primitive 11 check requires RiskV3Wrapper."
        )
    if p11_strat_check.config.enable_per_symbol_drawdown_brake:
        raise RuntimeError(
            "RiskV2Config.enable_per_symbol_drawdown_brake = True — expected False. "
            "iter-v3/055: per-symbol drawdown brake (primitive 11) must be DISABLED "
            "(CLOSED-mechanism per iter-v3/054 closeout). "
            "Set enable_per_symbol_drawdown_brake=False in RiskV2Config in _build_v3_model."
        )
    print(
        "  Primitive 11 (per-symbol drawdown brake): enable=False "
        "(CLOSED-mechanism per iter-v3/054 closeout)  PASS"
    )

    # iter-v3/061: per-symbol vol_scale_floor — TRX-only 0.5; BCH/LDO/ALGO at global 0.3.
    # Calibrated by QR EDA SHA d198b25 + Critic /060 Rec #3.
    # Asserts the vol_scale_floor_per_symbol dict is wired correctly.
    _p12_cfg_check, p12_strat_check = _build_v3_model(
        symbol="TRXUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(p12_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model(TRXUSDT) returned {type(p12_strat_check).__name__} — "
            "expected RiskV3Wrapper. iter-v3/061: vol_scale_floor_per_symbol check "
            "requires RiskV3Wrapper. Check _build_v3_model returns RiskV3Wrapper."
        )
    expected_floor_dict: dict[str, float] = {"TRXUSDT": 0.5}
    if dict(p12_strat_check.config.vol_scale_floor_per_symbol) != expected_floor_dict:
        raise ValueError(
            f"RiskV2Config.vol_scale_floor_per_symbol = "
            f"{p12_strat_check.config.vol_scale_floor_per_symbol} — expected "
            f"{expected_floor_dict}. iter-v3/061: TRX-only floor=0.5; BCH/LDO unchanged. "
            "Set vol_scale_floor_per_symbol={'TRXUSDT': 0.5} in RiskV2Config init in "
            "_build_v3_model."
        )
    print(
        "  Per-symbol vol_scale_floor (iter-v3/061): {'TRXUSDT': 0.5} "
        "(TRX floor raised 0.3→0.5; BCH/LDO unchanged at global 0.3)  PASS"
    )


def _verify_label_leakage_gap() -> None:
    """Assert gap == REQUIRED_GAP and print proof (brief Section 3.5#3)."""
    timeout_minutes = 10080  # 7 days
    candle_minutes = 480  # 8h
    n_symbols = len(V3_MODELS)
    timeout_candles = timeout_minutes // candle_minutes  # = 21
    required_gap = (timeout_candles + 1) * n_symbols  # formula: (timeout_candles+1)*len(V3_MODELS)
    assert required_gap == REQUIRED_GAP, (
        f"REQUIRED_GAP mismatch: formula gives {required_gap}, "
        f"REQUIRED_GAP constant is {REQUIRED_GAP}. Update validation_v3.REQUIRED_GAP."
    )
    print(
        f"  Label-leakage gap: (timeout_candles={timeout_candles}+1) * n_symbols={n_symbols}"
        f" = {required_gap}  [matches REQUIRED_GAP={REQUIRED_GAP}]  PASS"
    )


def _verify_track_isolation() -> None:
    """Grep-check: features_v3 must not import from features (v1) or features_v2.

    Uses '^from ...' to match only actual import statements at line start,
    not occurrences in comments or docstrings.
    """
    import subprocess as sp  # noqa: PLC0415

    for pattern in (
        r"^from crypto_trade\.features ",
        r"^from crypto_trade\.features_v2",
    ):
        out = sp.run(
            ["grep", "-rP", pattern, "src/crypto_trade/features_v3/"],
            capture_output=True,
            text=True,
        )
        if out.stdout.strip():
            raise RuntimeError(
                f"Track isolation FAIL: found '{pattern}' in features_v3/:\n{out.stdout}"
            )
    print("  Track isolation (features_v3 does not import v1/v2): PASS")


# ============================================================
# Feature generation
# ============================================================


def _generate_v3_features(symbols: list[str]) -> None:
    """Generate v3 feature parquets for all symbols."""
    print(f"\n[features] Generating v3 features for {symbols} -> {FEATURES_DIR}")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    for sym in symbols:
        t0 = time.time()
        result = process_symbol_v3(sym, "8h", str(DATA_DIR), str(FEATURES_DIR))
        n_rows, n_cols = result[1], result[2]
        elapsed = time.time() - t0
        print(f"  {sym}: {n_rows} rows, {n_cols} feature cols ({elapsed:.1f}s)")


# ============================================================
# ADF stationarity test — per-(symbol, feature, retraining month)
# brief Section 3.5#4
# ============================================================


def _walk_forward_month_starts(df_is: pd.DataFrame) -> list[int]:
    """Identify the start of each walk-forward retraining month (IS only).

    Returns a list of epoch-ms timestamps representing the first candle of
    each calendar month in the IS window, limited to months that have at
    least 1 candle of data.
    """
    months = pd.to_datetime(df_is["open_time"], unit="ms").dt.to_period("M").unique()
    return sorted(months.tolist())


def _run_adf_tests(symbols: list[str]) -> pd.DataFrame:
    """Run ADF per (symbol, feature, walk-forward retraining month).

    Returns DataFrame with columns:
        symbol, feature_name, month, adf_statistic, p_value, stationary

    Expected row count ≈ n_symbols × n_features × n_months.
    For v3: 4 × 34 × 27 ≈ 3672 rows (varies by symbol listing date).

    LDO was listed 2022-09-22, so it contributes fewer months than BCH/MKR/TRX.
    """
    import math as _math  # noqa: PLC0415

    from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

    rows = []
    for sym in symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not pq_path.exists():
            print(f"  [ADF] Parquet not found for {sym}, skipping")
            continue
        df = pd.read_parquet(pq_path)
        df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")

        # IS only
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if len(df_is) < 200:
            print(f"  [ADF] Insufficient IS data for {sym} ({len(df_is)} rows), skipping")
            continue

        df_is["month_period"] = df_is["open_time_dt"].dt.to_period("M")
        retrain_months = sorted(df_is["month_period"].unique().tolist())

        for month in retrain_months:
            # Training window ending at the START of this month (24-month rolling)
            # We use data from up to TRAINING_MONTHS months before this month
            month_start_ts = int(month.start_time.timestamp() * 1000)
            window_start_month = month - TRAINING_MONTHS
            window_start_ts = int(window_start_month.start_time.timestamp() * 1000)

            df_window = df_is[
                (df_is["open_time"] >= window_start_ts) & (df_is["open_time"] < month_start_ts)
            ]

            if len(df_window) < 30:
                # Too little data in window for ADF (e.g. early LDO months)
                for col in V3_FEATURE_COLUMNS:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                continue

            for col in V3_FEATURE_COLUMNS:
                if col not in df_window.columns:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    continue

                series = df_window[col].dropna().to_numpy()
                if len(series) < 20:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    continue

                try:
                    maxlag = int(_math.floor(12 * (len(series) / 100) ** 0.25))
                    result = adfuller(series, autolag="AIC", maxlag=maxlag)
                    p_val = float(result[1])
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": round(float(result[0]), 6),
                            "p_value": round(p_val, 6),
                            "stationary": p_val < 0.05,
                        }
                    )
                except Exception as e:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    print(f"  [ADF] Error {sym}/{col}/{month}: {e}")

    return pd.DataFrame(rows)


def _verify_adf_row_count(adf_df: pd.DataFrame, symbols: list[str]) -> None:
    """Assert ADF output has approximately the expected number of rows.

    Tolerance: LDO was listed 2022-09-22 so it has fewer walk-forward months
    than BCH/MKR/TRX.  The minimum expected is (n_symbols - 1) × n_features ×
    n_months, where n_months is the fewest months any symbol contributes.
    """
    if adf_df.empty:
        raise RuntimeError("ADF test produced no rows — pipeline broken")

    n_feats = len(V3_FEATURE_COLUMNS)
    n_syms = len(symbols)
    # Count months per symbol
    months_per_sym: dict[str, int] = {}
    for sym, grp in adf_df.groupby("symbol"):
        months_per_sym[str(sym)] = int(grp["month"].nunique())

    total_actual = len(adf_df)
    expected_min = n_syms * n_feats * min(months_per_sym.values())
    expected_max = n_syms * n_feats * max(months_per_sym.values())

    print(
        f"  [ADF] {total_actual} rows; "
        f"expected ∈ [{expected_min}, {expected_max}] "
        f"({n_syms} syms × {n_feats} feats × "
        f"[{min(months_per_sym.values())}, {max(months_per_sym.values())}] months)"
    )
    print(f"  [ADF] Months per symbol: {months_per_sym}")

    if total_actual < expected_min:
        raise RuntimeError(
            f"ADF row count {total_actual} < expected minimum {expected_min}. "
            "The per-(symbol, feature, month) ADF pipeline is missing rows. "
            f"Months per symbol: {months_per_sym}"
        )

    # Secondary falsifier: LDO cusum_reset_count_200 must fail p<0.05 in at least 1 month
    ldo_cusum = adf_df[
        (adf_df["symbol"] == "LDOUSDT") & (adf_df["feature_name"] == "cusum_reset_count_200")
    ]
    if len(ldo_cusum) > 0:
        n_fail = int((ldo_cusum["p_value"] >= 0.05).sum())
        print(
            f"  [ADF] Secondary falsifier: LDOUSDT/cusum_reset_count_200 "
            f"fails p<0.05 in {n_fail}/{len(ldo_cusum)} months  "
            f"({'PASS' if n_fail > 0 else 'FAIL — averaging masking per-symbol non-stationarity'})"
        )
    else:
        print("  [ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output")


# ============================================================
# IC matrix
# ============================================================


def _compute_ic_matrix(symbols: list[str]) -> pd.DataFrame:
    """Pairwise Pearson IC between V3_FEATURE_COLUMNS on IS data."""
    frames = []
    for sym in symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not pq_path.exists():
            continue
        df = pd.read_parquet(pq_path)
        df_is = df[df["open_time"] < OOS_CUTOFF_MS]
        avail = [c for c in V3_FEATURE_COLUMNS if c in df_is.columns]
        if avail:
            frames.append(df_is[avail].copy())

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    avail_cols = [c for c in V3_FEATURE_COLUMNS if c in combined.columns]
    return combined[avail_cols].corr(method="pearson")


# ============================================================
# CPCV path computation on IS candle/feature sequence
# brief Section 3.5#2
# ============================================================


def _compute_cpcv_paths(
    symbols: list[str],
    feature_parquets: dict[str, pd.DataFrame],
    oof_parquet_path: Path | None = None,
    report_dir: Path | None = None,
) -> tuple[pd.DataFrame, np.ndarray, float | None]:
    """Compute CPCV statistics from IS candle/feature sequences.

    UPDATED (iter-v3/004 sub-fix #1): when oof_parquet_path is provided and
    exists, iterates over (symbol, train_month) cells in the parquet.  For each
    cell, deduplicates by natural key, pivots to a (n_candles × 50_trials)
    matrix, runs per-cell CSCV (N=10, k=2 → 45 paths, gap=22 within-cell), and
    calls pbo_from_cpcv to get a per-cell PBO.  The 173 per-cell PBOs are
    aggregated via the cross-cell MEAN to produce a finite float strictly inside
    (0.0, 1.0).  The per_cell_pbo.csv audit trail is written to report_dir.

    The legacy cross-cell CSCV (combining all trial_ids across all cells as a
    global strategy axis) is REMOVED because cross-cell trial_id has no
    statistical meaning — each Optuna study has its own independent TPE sampler
    (brief Section 9 / iter-v3/003 diary lesson #1).

    Falls back to S=1 (return proxy, PBO=None) if parquet is absent or empty.
    The global CPCV candle sequence still runs for cpcv_paths.csv (inherited
    artifact) using the return proxy — this preserves the cpcv_paths.csv schema.

    Parameters
    ----------
    symbols
        v3 symbols (BCH, MKR, LDO, TRX).
    feature_parquets
        Dict mapping symbol -> IS-window feature DataFrame.
    oof_parquet_path
        Path to trial_oof_returns.parquet written during training (iter-v3/003).
    report_dir
        If provided, writes per_cell_pbo.csv to this directory for audit.

    Returns
    -------
    (cpcv_df, path_metric_matrix, per_cell_mean_pbo)
        cpcv_df: DataFrame with path_id, sharpe, max_dd, n_candles.
        path_metric_matrix: np.ndarray of shape (n_paths, 1) — return proxy
            for cpcv_paths.csv (legacy; per-cell PBO is the headline output).
        per_cell_mean_pbo: float mean of per-cell PBOs (None if no cells).
    """
    # ----------------------------------------------------------------
    # Global CPCV candle sequence — for cpcv_paths.csv (inherited schema)
    # ----------------------------------------------------------------
    all_frames = []
    for sym in symbols:
        df = feature_parquets.get(sym)
        if df is None or df.empty:
            continue
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if len(df_is) < 10:
            continue
        # Use close-to-close log return as per-candle return proxy
        if "close" in df_is.columns:
            df_is = df_is.copy()
            df_is["_ret"] = np.log(df_is["close"] / df_is["close"].shift(1)).fillna(0.0)
        else:
            df_is["_ret"] = 0.0
        df_is["_sym"] = sym
        all_frames.append(df_is[["open_time", "_ret", "_sym"]].copy())

    if not all_frames:
        return (
            pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]),
            np.zeros((0, 1)),
            None,
        )

    combined = (
        pd.concat(all_frames, ignore_index=True).sort_values("open_time").reset_index(drop=True)
    )
    n_candles = len(combined)
    print(f"  [CPCV] IS candle sequence: {n_candles} candles across {len(symbols)} symbols")

    if n_candles < CPCV_N_SPLITS * 10:
        print(f"  [CPCV] Insufficient candles ({n_candles}) for CPCV — skipping")
        return (
            pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]),
            np.zeros((0, 1)),
            None,
        )

    candle_timeline = combined["open_time"].to_numpy()
    returns_proxy = combined["_ret"].to_numpy()

    # Assertion: gap must equal REQUIRED_GAP (brief Section 3.5#3)
    splits = combinatorial_purged_cv(
        n_samples=n_candles,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=REQUIRED_GAP,
        embargo=CPCV_EMBARGO,
        expected_gap=REQUIRED_GAP,
    )

    rows = []
    path_metric_cols: list[np.ndarray] = []

    for path_id, (_, test_idx) in enumerate(splits):
        test_candles = candle_timeline[test_idx]
        n_test = len(test_candles)
        proxy_rets = returns_proxy[test_idx]

        if n_test < 2:
            rows.append(
                {
                    "path_id": path_id,
                    "sharpe": float("nan"),
                    "max_dd": float("nan"),
                    "n_candles": n_test,
                }
            )
            path_metric_cols.append(np.array([float("nan")]))
            continue

        s1_sigma = float(np.nanstd(proxy_rets, ddof=1))
        s1_mu = float(np.nanmean(proxy_rets))
        s1_sharpe = s1_mu / s1_sigma * np.sqrt(n_test) if s1_sigma > 0 else 0.0
        path_metric_cols.append(np.array([s1_sharpe]))

        mu = float(np.nanmean(proxy_rets))
        sigma = float(np.nanstd(proxy_rets, ddof=1))
        path_sharpe = mu / sigma * np.sqrt(n_test) if sigma > 0 else 0.0
        cum = np.nancumsum(proxy_rets)
        running_max = np.maximum.accumulate(cum)
        dd = running_max - cum
        max_dd = float(dd.max()) if len(dd) > 0 else 0.0

        rows.append(
            {
                "path_id": path_id,
                "sharpe": round(path_sharpe, 6),
                "max_dd": round(max_dd * 100, 4),
                "n_candles": n_test,
            }
        )

    cpcv_df = pd.DataFrame(rows)
    path_metric_matrix = (
        np.stack(path_metric_cols, axis=0) if path_metric_cols else np.zeros((0, 1))
    )
    print(f"  [CPCV] cpcv_paths.csv: {len(cpcv_df)} paths (return proxy, S=1 — for schema)")

    # ----------------------------------------------------------------
    # Sub-fix #1 (iter-v3/004): per-cell CSCV with cross-cell mean aggregation
    # ----------------------------------------------------------------
    per_cell_mean_pbo: float | None = None
    if oof_parquet_path is not None and oof_parquet_path.exists():
        per_cell_mean_pbo = _compute_per_cell_pbo(oof_parquet_path, report_dir)

    return cpcv_df, path_metric_matrix, per_cell_mean_pbo


# Per-cell CSCV parameters (brief Section 0 — within-cell gap = 22)
PER_CELL_N_SPLITS = 10
PER_CELL_K = 2  # C(10, 2) = 45 paths
PER_CELL_GAP = 22  # (timeout_candles + 1) within a single-symbol cell


def _compute_per_cell_pbo(
    oof_parquet_path: Path,
    report_dir: Path | None = None,
) -> float | None:
    """Compute per-(symbol, train_month) cell CSCV PBO and aggregate via mean.

    Implementation of iter-v3/004 brief Section 3.5 sub-fixes #1 and #4.

    For each (symbol, train_month) cell:
    1. Dedup by natural key (sym, month, trial, fold, candle) — drops the 5x
       seed-duplicate rows the iter-v3/003 writer produced.
    2. Pivot to (n_candles × n_trials) returns matrix.
    3. Run CSCV (N=10, k=2, gap=22) to get 45 paths.
    4. Build (45, n_trials) path-Sharpe matrix.
    5. Call pbo_from_cpcv → per-cell PBO.

    Aggregation: cross-cell MEAN of per-cell PBOs for cells with rank > 1.
    Mean is the only aggregator that is:
    - Strictly in (0.0, 1.0) on the observed bimodal distribution
    - Not saturating (Fisher's method chi² > 5000 at this scale)
    - Interpretable as "fraction of cells showing overfit signature"

    Writes per_cell_pbo.csv to report_dir if provided.

    Returns mean PBO (float) or None if fewer than 1 informative cell.
    """
    print(f"  [per-cell PBO] Loading {oof_parquet_path} ...")
    oof_df = pd.read_parquet(oof_parquet_path)
    n_raw = len(oof_df)

    # Dedup by natural key — drops the 5x seed-duplicate rows
    oof_df = oof_df.drop_duplicates(
        subset=["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    )
    n_dedup = len(oof_df)
    print(f"  [per-cell PBO] Raw={n_raw}, after dedup={n_dedup}")

    # IS-only filter
    oof_df = oof_df[oof_df["candle_open_time_ms"] < OOS_CUTOFF_MS].copy()
    n_is = len(oof_df)
    print(f"  [per-cell PBO] IS-only rows: {n_is}")

    if oof_df.empty:
        print("  [per-cell PBO] OOF parquet IS slice is empty — returning None")
        return None

    cells = sorted(oof_df.groupby(["symbol", "train_month"]).groups.keys())
    n_cells = len(cells)
    print(f"  [per-cell PBO] Iterating over {n_cells} (sym, month) cells ...")

    cell_rows: list[dict] = []

    for cell_idx, (sym, month) in enumerate(cells):
        cell_df = oof_df[(oof_df["symbol"] == sym) & (oof_df["train_month"] == month)]
        n_trials_cell = int(cell_df["trial_id"].nunique())
        n_candles_cell = int(cell_df["candle_open_time_ms"].nunique())

        if n_trials_cell < 2 or n_candles_cell < PER_CELL_N_SPLITS * 3:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": "insufficient_data",
                }
            )
            continue

        try:
            # Pivot: (n_candles, n_trials) returns matrix, averaging over fold_idx
            pivot = cell_df.pivot_table(
                index="candle_open_time_ms",
                columns="trial_id",
                values="oof_return",
                aggfunc="mean",
            ).sort_index()
            returns_mat = pivot.to_numpy()  # (n_candles, n_trials)
            n_candles_mat, n_trials_mat = returns_mat.shape

            # Per-cell CSCV
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

            pbo_res = pbo_from_cpcv(path_mat, max_splits=5000)
            cell_pbo = pbo_res.pbo if pbo_res.pbo is not None else float("nan")

            # n_eff per-cell: (n_trials × n_candles) matrix
            cell_neff = n_effective_trials(returns_mat.T)

            rank = int(np.linalg.matrix_rank(returns_mat))
            mean_path_sharpe = float(np.nanmean(path_mat))

            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_mat,
                    "n_candles": n_candles_mat,
                    "n_paths": n_paths,
                    "rank": rank,
                    "pbo": cell_pbo,
                    "n_eff": cell_neff,
                    "mean_path_sharpe": round(mean_path_sharpe, 6),
                    "error": "",
                }
            )
        except Exception as exc:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": str(exc)[:120],
                }
            )

        if (cell_idx + 1) % 25 == 0:
            print(f"  [per-cell PBO]   {cell_idx + 1}/{n_cells} cells processed")

    print(f"  [per-cell PBO] Completed {n_cells} cells")

    per_cell_df = pd.DataFrame(cell_rows)

    # Write audit CSV (sub-fix #4)
    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        csv_path = report_dir / "per_cell_pbo.csv"
        per_cell_df.to_csv(csv_path, index=False)
        print(f"  [per-cell PBO] Wrote {csv_path} ({len(per_cell_df)} rows)")

    # Aggregate: mean of per-cell PBOs for cells with rank > 1 (informative)
    informative = per_cell_df[per_cell_df["rank"] > 1]["pbo"].dropna()
    n_informative = len(informative)
    print(f"  [per-cell PBO] Informative cells (rank>1): {n_informative}/{n_cells}")

    if n_informative == 0:
        print("  [per-cell PBO] No informative cells — returning None")
        return None

    mean_pbo = float(informative.mean())
    median_pbo = float(informative.median())
    print(
        f"  [per-cell PBO] Aggregated mean PBO={mean_pbo:.4f}, median PBO={median_pbo:.4f} "
        f"(|delta|={abs(mean_pbo - median_pbo):.4f})"
    )
    return mean_pbo


# ============================================================
# Model builder
# ============================================================


def _build_v3_model(
    symbol: str,
    seed: int,
    n_trials: int,
    ensemble_seeds: list[int],
    oof_persist_path: Path | None = None,
    fast_mode: bool = False,
    model_type: str = "lgbm",
) -> tuple[BacktestConfig, RiskV3Wrapper]:
    """Build v3 M1 strategy + RiskV3Wrapper for a single symbol.

    v2 5-gate config + BTC trend filter. NO R1/R2/R3 (brief Section 3.4).
    oof_persist_path: if set, per-trial OOF returns written to parquet
    (sub-fix 1d, iter-v3/003).
    fast_mode: if True, hardcode colsample_bytree=1.0 in Optuna search space
    to minimize per-seed feature-subsampling variance (iter-v3/007 exploration).
    model_type: 'lgbm' (default) or 'xgboost'. Routes to LightGbmStrategy or
    XgboostStrategy. The --model CLI flag controls this. Default 'lgbm' preserves
    backward compatibility for all prior iteration runners (iter-v3/016 §3.5 sub-fix #8).
    """
    cfg = BacktestConfig(
        symbols=(symbol,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,  # 7 days (21 candles at 8h)
        fee_pct=0.1,
        data_dir=DATA_DIR,
        cooldown_candles=4,  # 32h between trades (inherited from v2)
        vol_targeting=False,  # Vol targeting via RiskV3Wrapper
    )
    # iter-v3/016: --model {lgbm,xgboost} routes to the appropriate strategy class.
    # iter-v3/017: --model metalabeling routes to MetaLabelingStrategy (M1+M2).
    # Constructor signatures are identical so we call with the same kwargs.
    # iter-v3/032: per-symbol ATR multipliers via atr_multipliers_for_symbol().
    # LDOUSDT returns (1.5, 0.75); BCH/TRX/ALGO fall back to (2.0, 1.0) via dict.
    _atr_tp, _atr_sl = atr_multipliers_for_symbol(symbol)
    common_kwargs = dict(
        training_months=TRAINING_MONTHS,
        n_trials=n_trials,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir=str(FEATURES_DIR),
        verbose=1,
        atr_tp_multiplier=_atr_tp,
        atr_sl_multiplier=_atr_sl,
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=list(ensemble_seeds),
        # iter-v3/030: per-symbol dispatch — EXPLICIT list, never None.
        feature_columns=list(features_for_symbol(symbol)),
        ood_enabled=False,  # OOD via RiskV3Wrapper z-score gate
        fast_mode=fast_mode,  # iter-v3/007 — colsample_bytree=1.0 when True
    )
    if model_type == "metalabeling":
        # iter-v3/017: MetaLabelingStrategy wraps M1 (LightGbmStrategy) with
        # an M2 binary classifier that filters low-confidence M1 predictions.
        # oof_persist_path is NOT passed to MetaLabelingStrategy (M2 does not
        # write trial OOF returns; only M1's path matters for CPCV).
        m1 = MetaLabelingStrategy(**common_kwargs)
    elif model_type == "xgboost":
        m1 = XgboostStrategy(oof_persist_path=oof_persist_path, **common_kwargs)
    else:
        m1 = LightGbmStrategy(oof_persist_path=oof_persist_path, **common_kwargs)
    risk_cfg = RiskV2Config(
        zscore_threshold=2.0,
        adx_threshold=20.0,  # RESET: iter-v3/014's failed test (25.0) → iter-v3/013 baseline
        max_per_symbol_pnl_share=0.40,  # iter-v3/020: per-symbol cap at 40% rolling share
        max_per_symbol_window_bars=90,  # ≈ 30 days at 8h cadence
        # iter-v3/021: REVERTED per iter-v3/020 PATH C closeout (diary 5287bd6)
        enable_per_symbol_cap=False,
        # iter-v3/022: primitive 9 — regime-conditional kill switch on TRX.
        # Thresholds calibrated at IS-90th/95th percentile (EDA SHA b728313 synthesis.md).
        # Gate fires when BTC drawdown_30d > 20% OR |BTC vol_zscore_30d| > 1.5.
        # iter-v3/023: DISABLED — revert iter-v3/022 axis so the single varied axis
        # vs iter-v3/018 anchor is funding_rate_zscore_30 re-add only.
        # Code stays in repo (zero revert cost for future CONFIRMATION-mode re-eval).
        enable_regime_gate=False,
        regime_gate_symbols=("TRXUSDT",),
        regime_dd_threshold_pct=20.0,
        regime_vol_zscore_threshold=1.5,
        # iter-v3/051: REVERT primitive 10 — block_long_for=() per system-level rule
        # `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
        # confirmation of per-symbol-customization anti-pattern at iter-v3/039 + iter-v3/050
        # CONFIRMATION-NO-MERGE). block_long_for cleared; no direction blocking for any symbol.
        # Cycle 4 starting baseline = iter-v3/028 architecture (no primitive 10).
        # Per analysis/iteration_v3-051/synthesis.md SHA `290f37b`.
        # History: block_long_for=() (iter-v3/028; baseline) → ("BCHUSDT",) (iter-v3/047)
        #   → () (iter-v3/051 system-level REVERT; current state).
        block_long_for=(),
        block_short_for=(),
        # iter-v3/050: per-symbol ADX threshold DROP (iter-v3/049 TRX 21 REVERTED).
        # Critic FINAL `1908d50` recommendation #2: axis CLOSED for cycle 3.
        # adx_threshold_per_symbol reverts to empty dict (global-only ADX threshold=20.0).
        adx_threshold_per_symbol={},
        # iter-v3/055: per-symbol drawdown brake DISABLED (CLOSED-mechanism per /054 closeout).
        # /054 PATH C-clean confirmed deadlock: brake permanently suppressed all OOS trades.
        # Fields retained as backward-compatible defaults; only enable flag changes.
        enable_per_symbol_drawdown_brake=False,  # per iter-v3/054 closeout (CLOSED-mechanism)
        drawdown_brake_threshold_wpnl=10.0,  # retained as backward-compatible default
        drawdown_brake_recovery_wpnl=5.0,  # retained as backward-compatible default
        drawdown_brake_window_days=30,  # retained as backward-compatible default
        # iter-v3/061: TRX-specific vol_scale_floor=0.5 per QR EDA SHA d198b25 + Critic /060 Rec #3.
        # Single per-symbol risk-primitive customization; BCH/LDO unchanged at global 0.3.
        # Counterfactual: +0.47 OOS wpnl TRX lift with bit-identical IS (+0.008 wpnl).
        # BCH/LDO weighted_pnl mathematically invariant per Section 2.5 Q5 invariance check.
        vol_scale_floor_per_symbol={"TRXUSDT": 0.5},
    )
    strategy = RiskV3Wrapper(m1, risk_cfg)
    return cfg, strategy


# ============================================================
# Extended comparison.csv writer (v3 schema)
# ============================================================


def _monthly_sharpe(trades: list) -> float:
    if not trades:
        return 0.0
    months = pd.to_datetime([t.close_time for t in trades], unit="ms").to_period("M")
    monthly = (
        pd.Series([t.weighted_pnl for t in trades], index=months).groupby(level=0).sum() / 100.0
    )
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _max_drawdown(trades: list) -> float:
    if not trades:
        return 0.0
    cum = np.cumsum([float(t.weighted_pnl) for t in sorted(trades, key=lambda t: t.close_time)])
    running_max = np.maximum.accumulate(cum)
    dd = running_max - cum
    return float(dd.max())


def _write_v3_comparison(
    is_trades: list,
    oos_trades: list,
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials_total: int,
    n_eff: int,
) -> None:
    """Write comparison.csv with all v3-required rows."""

    def _daily_sharpe(trades: list) -> float:
        if not trades:
            return 0.0
        by_day: dict[str, float] = {}
        for t in trades:
            day = pd.Timestamp(t.close_time, unit="ms").strftime("%Y-%m-%d")
            by_day[day] = by_day.get(day, 0.0) + float(t.weighted_pnl)
        daily = pd.Series(list(by_day.values()))
        if len(daily) < 2 or daily.std() == 0:
            return 0.0
        return float(daily.mean() / daily.std() * np.sqrt(365))

    def _profit_factor(trades: list) -> float:
        wins = sum(t.weighted_pnl for t in trades if t.weighted_pnl > 0)
        losses = sum(-t.weighted_pnl for t in trades if t.weighted_pnl < 0)
        return float(wins / losses) if losses > 0 else float("inf")

    def _win_rate(trades: list) -> float:
        if not trades:
            return 0.0
        return 100.0 * sum(1 for t in trades if t.weighted_pnl > 0) / len(trades)

    def _calmar(trades: list) -> float:
        dd = _max_drawdown(trades)
        if dd <= 0:
            return 0.0
        return float(sum(t.weighted_pnl for t in trades) / dd)

    is_ms = _monthly_sharpe(is_trades)
    oos_ms = _monthly_sharpe(oos_trades)
    is_ds = _daily_sharpe(is_trades)
    oos_ds = _daily_sharpe(oos_trades)
    is_dd = _max_drawdown(is_trades)
    oos_dd = _max_drawdown(oos_trades)
    is_pf = _profit_factor(is_trades)
    oos_pf = _profit_factor(oos_trades)
    is_wr = _win_rate(is_trades)
    oos_wr = _win_rate(oos_trades)
    is_n = len(is_trades)
    oos_n = len(oos_trades)
    is_pnl = sum(t.weighted_pnl for t in is_trades)
    oos_pnl = sum(t.weighted_pnl for t in oos_trades)
    is_calmar = _calmar(is_trades)
    oos_calmar = _calmar(oos_trades)

    def ratio_str(oos_v: float, is_v: float) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    # PBO: None when S=1; report as "NaN" with frac_positive_paths in dsr.json
    pbo_str = "NaN" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"

    metrics = [
        ("monthly_sharpe", f"{is_ms:.4f}", f"{oos_ms:.4f}", ratio_str(oos_ms, is_ms)),
        ("daily_sharpe", f"{is_ds:.4f}", f"{oos_ds:.4f}", ratio_str(oos_ds, is_ds)),
        ("max_drawdown", f"{is_dd:.4f}", f"{oos_dd:.4f}", ratio_str(oos_dd, is_dd)),
        ("profit_factor", f"{is_pf:.4f}", f"{oos_pf:.4f}", ratio_str(oos_pf, is_pf)),
        ("win_rate", f"{is_wr:.4f}", f"{oos_wr:.4f}", ratio_str(oos_wr, is_wr)),
        ("n_trades", str(is_n), str(oos_n), ratio_str(float(oos_n), float(is_n))),
        ("total_pnl", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", ratio_str(oos_pnl, is_pnl)),
        (
            "monthly_calmar",
            f"{is_calmar:.4f}",
            f"{oos_calmar:.4f}",
            ratio_str(oos_calmar, is_calmar),
        ),
        ("weighted_pnl_total", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", ratio_str(oos_pnl, is_pnl)),
        ("dsr", f"{dsr_val:.6f}", "—", "—"),
        ("pbo", pbo_str, "—", "—"),
        ("psr", f"{psr_val:.4f}", "—", "—"),
        ("n_trials", str(n_trials_total), "—", "—"),
        ("n_effective_trials", str(n_eff), "—", "—"),
    ]

    comp_path = report_dir / "comparison.csv"
    with open(comp_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
        for row in metrics:
            writer.writerow(row)

    all_symbols = list({t.symbol for t in is_trades + oos_trades})
    total_oos_pnl = sum(t.weighted_pnl for t in oos_trades) or 1.0
    with open(comp_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([])
        writer.writerow(
            ["# per_symbol", "weighted_pnl", "n_trades", "win_rate", "concentration_pct"]
        )
        for sym in sorted(all_symbols):
            sym_oos = [t for t in oos_trades if t.symbol == sym]
            if not sym_oos:
                continue
            sym_pnl = sum(t.weighted_pnl for t in sym_oos)
            sym_wr = 100.0 * sum(1 for t in sym_oos if t.weighted_pnl > 0) / len(sym_oos)
            conc = 100.0 * sym_pnl / total_oos_pnl if total_oos_pnl != 0 else 0.0
            writer.writerow([sym, f"{sym_pnl:.4f}", len(sym_oos), f"{sym_wr:.1f}", f"{conc:.2f}"])

    print(
        f"[v3 report] comparison.csv: IS monthly Sharpe={is_ms:+.4f}, "
        f"OOS monthly Sharpe={oos_ms:+.4f}, DSR={dsr_val:.4f}, "
        f"PBO={pbo_str}, PSR={psr_val:.4f}"
    )


# ============================================================
# DSR JSON writer
# ============================================================


_CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD: float = 0.55
"""Gate threshold for cpcv_frac_positive_paths (iter-v3/059: replaces Pareto Gate 10)."""


def _write_dsr_json(
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials: int,
    n_eff: int,
    min_trl_months: float,
    dsr_relative: float = 0.0,
    cpcv_path_sharpe_q75: float = 0.0,
) -> None:
    """Write dsr.json — includes PBO metadata, iter-v3/055 DSR_relative, and
    iter-v3/059 cpcv_frac_positive_paths gate fields."""
    pbo_out = pbo_result.pbo if pbo_result.pbo is not None else None
    frac_pos = pbo_result.frac_positive_paths
    # iter-v3/059: cpcv_frac_positive_paths_gate replaces Pareto Gate 10.
    cpcv_gate_pass = (
        frac_pos >= _CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD
        if not (frac_pos != frac_pos)  # NaN check
        else False
    )
    data = {
        "dsr": round(dsr_val, 8),
        "pbo": pbo_out,
        "pbo_note": pbo_result.note,
        "pbo_frac_positive_paths": round(frac_pos, 4),
        "pbo_path_sharpe_q25": round(pbo_result.path_sharpe_quartiles[0], 4),
        "pbo_path_sharpe_q50": round(pbo_result.path_sharpe_quartiles[1], 4),
        "pbo_path_sharpe_q75": round(pbo_result.path_sharpe_quartiles[2], 4),
        "cpcv_frac_positive_paths_gate_pass": cpcv_gate_pass,
        "cpcv_frac_positive_paths_gate_threshold": _CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD,
        "psr": round(psr_val, 4),
        "dsr_relative": round(dsr_relative, 6),  # iter-v3/055: PSR vs CPCV Q75
        "cpcv_path_sharpe_q75": round(cpcv_path_sharpe_q75, 6),  # iter-v3/055: benchmark
        "n_trials": n_trials,
        "n_eff": n_eff,
        "min_trl_months": round(min_trl_months, 2),
    }
    (report_dir / "dsr.json").write_text(json.dumps(data, indent=2))
    gate_str = "PASS" if cpcv_gate_pass else "FAIL"
    thr = _CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD
    print(
        f"[v3 report] dsr.json: DSR={dsr_val:.4f}, PBO={pbo_out}, "
        f"frac_pos_paths={frac_pos:.3f} (gate {gate_str} @ {thr}), "
        f"PSR={psr_val:.4f}, DSR_relative={dsr_relative:.4f}, "
        f"CPCV_Q75={cpcv_path_sharpe_q75:.4f}, n_eff={n_eff}"
    )


# pareto_front.csv removed at iter-v3/059: outer-seed loop eliminated; per-seed
# Pareto metrics no longer applicable with unified 10-seed ensemble.
# Former Gate 10 ("both Pareto seeds positive") replaced by
# cpcv_frac_positive_paths_gate_pass (>= 0.55 threshold) in dsr.json.


# ============================================================
# Feature importance
# ============================================================


def _write_feature_importance(
    is_trades: list,
    oos_trades: list,
    primary_model_pairs: list,
    report_dir: Path,
) -> None:
    """Write feature importance CSVs from model(s) if available.

    iter-v3/017 fix (Critic Clar 3 of iter-v3/016, sub-fix #3): emit importance
    CSVs to ``in_sample/`` ONLY (the last-month model state reflects IS training;
    duplicating to ``out_of_sample/`` was byte-identical and misleading).
    Renamed output files to ``model_importance_last_month_<SYM>.csv`` and
    ``model_importance_last_month_portfolio.csv`` to make scope explicit.

    For MetaLabelingStrategy: reads importances from M1's inner models
    (self._m1._models).  M2 importances are not reported (14-dim vs 13-dim;
    M2 is a secondary filter, not the primary direction model).

    Works for LightGbmStrategy, XgboostStrategy, and MetaLabelingStrategy
    (all expose ``_models`` on the inner model layer).
    """
    if not primary_model_pairs:
        return

    # Determine canonical feature column list from first available strategy
    cols: list[str] = list(V3_FEATURE_COLUMNS)
    for _, strat in primary_model_pairs:
        inner = strat.inner if hasattr(strat, "inner") else strat
        if hasattr(inner, "_all_feature_cols") and inner._all_feature_cols:
            cols = list(inner._all_feature_cols)
            break

    # Collect per-symbol importance sums.
    # primary_model_pairs is a list of (BacktestConfig, RiskV3Wrapper) — one entry
    # per symbol.  Each strategy's inner._models list holds the ensemble models
    # trained on the LAST walk-forward month (lazy monthly training).
    # For MetaLabelingStrategy: unwrap via inner._m1._models.
    sym_importances: dict[str, dict[str, list[float]]] = {}
    for cfg, strat in primary_model_pairs:
        sym = cfg.symbols[0] if cfg.symbols else "UNKNOWN"
        inner = strat.inner if hasattr(strat, "inner") else strat
        # MetaLabelingStrategy: read M1's models (M1 is the direction model)
        if hasattr(inner, "_m1"):
            inner = inner._m1
        if not hasattr(inner, "_models") or not inner._models:
            continue
        if sym not in sym_importances:
            sym_importances[sym] = {c: [] for c in cols}
        for model in inner._models:
            if hasattr(model, "feature_importances_"):
                fi_arr = model.feature_importances_
                for i, c in enumerate(cols):
                    if i < len(fi_arr):
                        sym_importances[sym][c].append(float(fi_arr[i]))

    if not sym_importances:
        return

    # iter-v3/017: write to in_sample/ ONLY (last-month model scope).
    # Do NOT write to out_of_sample/ — byte-duplication was misleading.
    split_dir = report_dir / "in_sample"
    split_dir.mkdir(parents=True, exist_ok=True)

    # Portfolio-level accumulator (sum across symbols)
    portfolio: dict[str, float] = {c: 0.0 for c in cols}

    for sym, imp_dict in sym_importances.items():
        rows_sym: list[dict] = []
        for col in cols:
            vals = imp_dict.get(col, [])
            mean_fi = float(np.mean(vals)) if vals else 0.0
            rows_sym.append({"feature": col, "importance": round(mean_fi, 4)})
            portfolio[col] += mean_fi
        rows_sym.sort(key=lambda r: r["importance"], reverse=True)

        sym_path = split_dir / f"model_importance_last_month_{sym}.csv"
        with open(sym_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["feature", "importance"])
            writer.writeheader()
            writer.writerows(rows_sym)

    # Portfolio CSV — sum across symbols, ranked descending
    rows_port = [{"feature": c, "importance": round(portfolio[c], 4)} for c in cols]
    rows_port.sort(key=lambda r: r["importance"], reverse=True)
    port_path = split_dir / "model_importance_last_month_portfolio.csv"
    with open(port_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["feature", "importance"])
        writer.writeheader()
        writer.writerows(rows_port)


# ============================================================
# Single-seed run
# ============================================================


def _run_single_seed(
    seed: int,
    n_trials: int,
    btc_times: np.ndarray,
    btc_closes: np.ndarray,
    active_models: tuple[tuple[str, str], ...] | None = None,
    ensemble_size: int | None = None,
    ensemble_seeds_override: tuple[int, ...] | None = None,
    fast_mode: bool = False,
    model_type: str = "lgbm",
) -> tuple[list, list, dict, dict, list]:
    """Run v3 models for a single outer seed (or unified ensemble pass).

    Parameters
    ----------
    active_models:
        Subset of V3_MODELS to run.  Defaults to V3_MODELS when None.
        Pass a filtered tuple to scope the run (e.g. BCH-only for iter-v3/006).
    ensemble_size:
        Override the default ENSEMBLE_SIZE for this run. Useful for fast
        exploration (size=1 → no inner-ensemble averaging, ~5x faster).
        Ignored when ensemble_seeds_override is provided.
    ensemble_seeds_override:
        iter-v3/059: When provided, use this exact tuple of seeds INSTEAD of
        deriving from ``seed`` via _derive_ensemble_seeds.  Enables the unified
        10-seed inner ensemble (ENSEMBLE_SEEDS constant) without an outer loop.
    fast_mode:
        If True, hardcode `colsample_bytree=1.0` in Optuna search space
        (iter-v3/007 — minimize per-seed feature-subsampling variance).
    model_type:
        'lgbm' (default) or 'xgboost'. Forwarded to _build_v3_model.
        Controlled by --model CLI flag (iter-v3/016 §3.5 sub-fix #8).
    """
    models_to_run = active_models if active_models is not None else V3_MODELS
    all_trades: list = []
    model_pairs: list = []

    for name, symbol in models_to_run:
        print("=" * 60)
        print(f"MODEL {name} — seed {seed}")
        print("=" * 60)
        # sub-fix 1d (iter-v3/003): pass OOF persist path so per-trial returns
        # are written to parquet during training (one shared file per run).
        oof_path = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
        # iter-v3/059: when ensemble_seeds_override is provided (unified 10-seed pass),
        # use it directly.  Otherwise fall back to deriving from the outer seed.
        # Pre-iter-v3/006: ensemble_seeds=[42,123,456,789,1001] for ALL outer seeds.
        if ensemble_seeds_override is not None:
            ensemble_seeds_run = list(ensemble_seeds_override)
        else:
            size_for_this_run = ensemble_size if ensemble_size is not None else ENSEMBLE_SIZE
            ensemble_seeds_run = _derive_ensemble_seeds(seed, size=size_for_this_run)
        cfg, strategy = _build_v3_model(
            symbol=symbol,
            seed=seed,
            n_trials=n_trials,
            ensemble_seeds=ensemble_seeds_run,
            oof_persist_path=oof_path,
            fast_mode=fast_mode,
            model_type=model_type,
        )
        _verify_symbols(cfg.symbols)
        t0 = time.time()
        results = run_backtest(cfg, strategy, yearly_pnl_check=False)
        elapsed = time.time() - t0
        print(f"{name}: {len(results)} trades in {elapsed:.0f}s (seed={seed})")
        if hasattr(strategy, "gate_stats_summary"):
            print(f"  gate stats: {strategy.gate_stats_summary()}")
        all_trades.extend(results)
        model_pairs.append((cfg, strategy))

    all_trades.sort(key=lambda t: t.open_time)

    after_btc, btc_fire_stats = apply_btc_trend_filter(
        all_trades,
        btc_times,
        btc_closes,
        BTC_TREND_CONFIG,
    )
    btc_stats_dict = btc_fire_stats.as_dict()
    print(
        f"[btc trend filter seed {seed}] "
        f"killed={btc_stats_dict['n_killed']}/{btc_stats_dict['n_total']} "
        f"fire_rate={btc_stats_dict['fire_rate']:.2%}"
    )

    braked, hr_fire_stats = apply_hit_rate_gate(
        after_btc,
        HIT_RATE_CONFIG,
        activate_at_ms=OOS_CUTOFF_MS,
    )
    braked.sort(key=lambda t: t.close_time)
    hr_stats_dict = hr_fire_stats.as_dict()

    return all_trades, braked, btc_stats_dict, hr_stats_dict, model_pairs


# ============================================================
# Main runner
# ============================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="v3 baseline runner — iter-v3/003")
    parser.add_argument(
        "--seeds",
        type=int,
        default=None,
        help=(
            "DEPRECATED at iter-v3/059 RE-ANCHOR #2. Outer-seed loop eliminated; "
            "single 10-seed inner ensemble per cell now produces ONE Sharpe. "
            "Flag retained for backward compat. Any value passed logs a warning "
            "and is ignored. Internally always ENSEMBLE_SIZE=10."
        ),
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help=(
            "Optuna trials per monthly model per seed. CONFIRMATION default "
            "lowered from 50 → 35 at iter-v3/018 closeout: 50 was below TPE-warmup-saturation "
            "and added wall-clock cost without proportional gain in best-trial "
            "selection. 35 stays above TPE-warmup (~30) while saving ~30%% "
            "wall-clock."
        ),
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip feature generation (use existing parquets)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help=(
            "Comma-separated list of symbols to run (e.g. BCHUSDT).  "
            "Filters V3_MODELS at runtime.  Default: all V3_MODELS.  "
            "Used for iter-v3/006 BCH-only scoped validation."
        ),
    )
    parser.add_argument(
        "--exploration",
        action="store_true",
        help=(
            "EXPLORATION mode: uses ENSEMBLE_SIZE=3 (ENSEMBLE_SEEDS[0:3]). "
            "Default (without flag) is CONFIRMATION mode with ENSEMBLE_SIZE=10."
        ),
    )
    parser.add_argument(
        "--model",
        type=str,
        default="lgbm",
        choices=["lgbm", "xgboost", "metalabeling"],
        help=(
            "ML model backend. 'lgbm' (default) uses LightGbmStrategy "
            "(backward-compatible — all prior iterations). 'xgboost' uses "
            "XgboostStrategy with depth-wise growth + tree_method='hist' "
            "(iter-v3/016 architectural axis; opt-in). 'metalabeling' uses "
            "MetaLabelingStrategy (M1=LightGbmStrategy + M2=LGBMClassifier binary "
            "precision filter at threshold=0.5; the architectural axis for "
            "iter-v3/017 EXPLORATION)."
        ),
    )
    parser.add_argument(
        "--clean-oof",
        action="store_true",
        help=(
            "Delete trial_oof_returns.parquet for the current iteration_label before "
            "starting any backtest work. Required when re-running an iteration that "
            "previously completed (or crashed mid-run) — without this flag, re-running "
            "raises RuntimeError to prevent silent n_trials inflation and DSR contamination. "
            "Per QR A5 + Critic FINAL 785500f recommendation (iter-v3/047 accumulated "
            "5x duplicate rows: 55.78M vs expected 11M, inflating n_trials 140 to 700)."
        ),
    )
    args = parser.parse_args()

    # iter-v3/059: --seeds is deprecated; outer-seed loop eliminated.
    if args.seeds is not None:
        print(
            f"WARNING: --seeds={args.seeds} is DEPRECATED since iter-v3/059 RE-ANCHOR #2. "
            f"The outer-seed loop has been eliminated. The runner now uses a unified "
            f"10-seed inner ensemble (ENSEMBLE_SIZE={ENSEMBLE_SIZE}) in a single pass. "
            f"Proceeding with ENSEMBLE_SIZE={ENSEMBLE_SIZE}; the --seeds value is ignored."
        )

    # iter-v3/060: MODE-AWARE ensemble size.
    # EXPLORATION (--exploration): ENSEMBLE_SIZE=3, uses ENSEMBLE_SEEDS[0:3].
    #   Wall-clock ~1.1h (30% of CONFIRMATION ~3.6h per iter-v3/059).
    # CONFIRMATION (default): ENSEMBLE_SIZE=10, uses full ENSEMBLE_SEEDS tuple.
    #   Wall-clock ~3.6h per iter-v3/059 baseline.
    # fast_mode (colsample_bytree=1.0) is NOT tied to --exploration any more;
    # both modes use the Optuna-tunable search space (fast_mode=False).
    ensemble_size_for_run: int = (
        EXPLORATION_ENSEMBLE_SIZE if args.exploration else CONFIRMATION_ENSEMBLE_SIZE
    )
    fast_mode_for_run: bool = False  # iter-v3/060: fast_mode decoupled from --exploration

    # Build active_models from --symbols filter (iter-v3/006 CLI flag).
    # Default (None) keeps all V3_MODELS.
    if args.symbols is not None:
        requested = {s.strip().upper() for s in args.symbols.split(",")}
        active_models: tuple[tuple[str, str], ...] = tuple(
            (name, sym) for name, sym in V3_MODELS if sym in requested
        )
        if not active_models:
            raise RuntimeError(
                f"--symbols filter {requested!r} matched no V3_MODELS. "
                f"Valid symbols: {[sym for _, sym in V3_MODELS]}"
            )
        unknown = requested - {sym for _, sym in V3_MODELS}
        if unknown:
            raise RuntimeError(f"--symbols contains symbols not in V3_MODELS: {sorted(unknown)}")
    else:
        active_models = V3_MODELS

    t_start = time.time()
    _verify_branch()

    baseline_symbols = tuple(sym for _, sym in active_models)
    _verify_symbols(baseline_symbols)
    _verify_data_freshness(baseline_symbols + ("BTCUSDT",))
    # asserts len == 14, funding NOT present, vwap_dev_50/tbr_zscore_30 absent;
    # also asserts ensemble_size in (3, 10) for mode discipline.
    _verify_feature_columns(ensemble_size=ensemble_size_for_run)
    _verify_label_leakage_gap()  # asserts REQUIRED_GAP == 110 (5-symbol universe, iter-v3/033)
    _verify_track_isolation()  # grep check

    # -----------------------------------------------------------------------
    # OOF parquet contamination guardrail (iter-v3: QR A5 + Critic FINAL 785500f)
    #
    # iter-v3/047 was re-run 5 times unintentionally, accumulating 5x duplicate
    # rows in trial_oof_returns.parquet (55.78M vs expected 11M). This inflated
    # n_trials from 140 to 700 in dsr.json and comparison.csv, mechanically
    # depressing the DSR computation.
    #
    # Rule: if the OOF parquet for this iteration_label already exists at startup,
    # either delete it explicitly via --clean-oof (clean re-run) or abort loudly.
    # This check is STARTUP-ONLY — it does not affect per-trial append logic.
    # -----------------------------------------------------------------------
    oof_parquet_startup = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
    if oof_parquet_startup.exists():
        if args.clean_oof:
            oof_parquet_startup.unlink()
            print(f"[CLEAN-OOF] Removed stale OOF parquet at {oof_parquet_startup}")
        else:
            raise RuntimeError(
                f"OOF parquet for iteration_label '{ITERATION_LABEL}' already exists at "
                f"{oof_parquet_startup}. "
                "This indicates a previous run did not complete cleanly OR the iteration "
                "is being re-executed. Re-running silently inflates n_trials and contaminates "
                "DSR/PSR/comparison.csv. Either: "
                "(a) delete the parquet manually, OR "
                "(b) re-run with --clean-oof flag to delete and start fresh."
            )

    active_sym_names = ", ".join(sym for _, sym in active_models)
    # iter-v3/060: mode-aware startup log
    if args.exploration:
        print(f"[v3] Running in EXPLORATION mode (ensemble_size={ensemble_size_for_run})")
    else:
        print(f"[v3] Running in CONFIRMATION mode (ensemble_size={ensemble_size_for_run})")
    print(f"\nBASELINE v3 iter-{ITERATION_LABEL}: {active_sym_names} (seed-plumbing fix)")
    print(f"Ensemble: {ensemble_size_for_run} seeds  Optuna trials/model: {args.n_trials}")
    print(f"Active models: {len(active_models)}/{len(V3_MODELS)} (--symbols={args.symbols!r})")
    print(f"CPCV: N={CPCV_N_SPLITS}, k={CPCV_N_TEST_SPLITS}, 45 paths on IS CANDLE SEQUENCE")
    print(
        f"Gap: {REQUIRED_GAP} (= (timeout_candles+1) * 4 symbols [BCH+LDO+TRX+ALGO, iter-v3/034])"
    )
    print(
        f"Pre-flight: branch OK, symbols OK, data fresh (<16h), "
        f"feature-cols={len(V3_FEATURE_COLUMNS)}  PASS\n"
    )

    # Feature generation
    if not args.skip_features:
        _generate_v3_features(list(baseline_symbols))
    else:
        print("[features] Skipping feature generation (--skip-features)")

    # Load IS-window feature DataFrames for CPCV and ADF
    print("\n[features] Loading IS-window feature DataFrames...")
    feature_parquets: dict[str, pd.DataFrame] = {}
    for sym in baseline_symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if pq_path.exists():
            feature_parquets[sym] = pd.read_parquet(pq_path)
            print(f"  {sym}: {len(feature_parquets[sym])} rows loaded")
        else:
            print(f"  WARNING: {pq_path} not found")

    # ADF per-(symbol, feature, retraining month) — brief Section 3.5#4
    print("\n[ADF] Running per-(symbol, feature, retraining month) stationarity tests...")
    t_adf0 = time.time()
    adf_df = _run_adf_tests(list(baseline_symbols))
    t_adf1 = time.time()
    if not adf_df.empty:
        n_stationary = int(adf_df["stationary"].sum())
        n_total_adf = len(adf_df)
        print(
            f"  ADF: {n_stationary}/{n_total_adf} "
            f"({100.0 * n_stationary / n_total_adf:.1f}%) cells stationary (p<0.05) "
            f"in {t_adf1 - t_adf0:.1f}s"
        )
        non_stat = adf_df[~adf_df["stationary"]][["symbol", "feature_name", "month", "p_value"]]
        if len(non_stat) > 0:
            print(f"  Non-stationary (feature, month) cells: {len(non_stat)}")
    print(f"  ADF total rows: {len(adf_df)}")

    # IC matrix on IS data
    print("\n[IC] Computing pairwise feature correlation matrix on IS data...")
    ic_mat = _compute_ic_matrix(list(baseline_symbols))

    # BTC klines for trend filter
    btc_times, btc_closes = load_btc_klines_for_filter()
    print(f"Loaded {len(btc_times)} BTC 8h klines for trend filter\n")

    # iter-v3/059 RE-ANCHOR #2: single unified 10-seed ensemble pass.
    # The outer-seed loop is eliminated.  All 10 ensemble seeds are passed
    # directly to _run_single_seed via ensemble_seeds_override, producing ONE
    # Sharpe per (sym, month) cell (not a mean across outer-seed runs).
    # ENSEMBLE_SEEDS[0] is used as "primary" seed for log naming only.
    # iter-v3/060: mode-aware seed slice.
    # EXPLORATION uses ENSEMBLE_SEEDS[0:3] (outer=42 lineage subset).
    # CONFIRMATION uses full ENSEMBLE_SEEDS (all 10).
    active_ensemble_seeds: tuple[int, ...] = ENSEMBLE_SEEDS[:ensemble_size_for_run]
    mode_label = "EXPLORATION" if args.exploration else "CONFIRMATION"
    print(
        f"\n{'#' * 60}\n"
        f"# UNIFIED ENSEMBLE — {mode_label} ({ensemble_size_for_run} seeds)\n"
        f"# Seeds: {active_ensemble_seeds}\n"
        f"{'#' * 60}"
    )
    unbraked, braked, btc_stats, hr_stats, model_pairs = _run_single_seed(
        seed=active_ensemble_seeds[0],
        n_trials=args.n_trials,
        btc_times=btc_times,
        btc_closes=btc_closes,
        active_models=active_models,
        ensemble_size=ensemble_size_for_run,
        ensemble_seeds_override=active_ensemble_seeds,
        fast_mode=fast_mode_for_run,
        model_type=args.model,
    )

    if not braked:
        print("No trades produced by unified ensemble.")
        sys.exit(1)

    is_trades = [t for t in braked if t.open_time < OOS_CUTOFF_MS]
    oos_trades = [t for t in braked if t.open_time >= OOS_CUTOFF_MS]

    is_ms_run = _monthly_sharpe(is_trades)
    oos_ms_run = _monthly_sharpe(oos_trades)
    oos_dd_run = _max_drawdown(oos_trades)
    print(
        f"[ensemble] {len(braked)} trades — IS monthly={is_ms_run:+.4f}, "
        f"OOS monthly={oos_ms_run:+.4f}, OOS MaxDD={oos_dd_run:.4f}, "
        f"BTC killed={btc_stats['n_killed']}"
    )

    print(f"\n[split] {len(is_trades)} IS trades, {len(oos_trades)} OOS trades")

    # -------------------------------------------------------
    # CPCV on IS candle/feature sequence (iter-v3/004 sub-fix #1)
    # -------------------------------------------------------
    print("\n[CPCV] Computing per-cell CSCV PBO (iter-v3/004 per-cell pathway)...")
    oof_parquet = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
    report_dir_cpcv = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    cpcv_df, path_metric_matrix, per_cell_mean_pbo = _compute_cpcv_paths(
        list(baseline_symbols),
        feature_parquets,
        oof_parquet_path=oof_parquet,
        report_dir=report_dir_cpcv,
    )
    print(f"  CPCV: {len(cpcv_df)} paths (return proxy for cpcv_paths.csv)")
    print(f"  Per-cell mean PBO: {per_cell_mean_pbo}")

    # Build PBOResult from per-cell mean PBO (sub-fix #1)
    # The descriptive stats (frac_positive_paths, quartiles) are computed
    # from the global return-proxy cpcv_df as before.
    flat_path_sharpes = cpcv_df["sharpe"].dropna().to_numpy() if len(cpcv_df) > 0 else np.array([])
    frac_pos = float(np.mean(flat_path_sharpes > 0)) if len(flat_path_sharpes) > 0 else float("nan")
    q25, q50, q75 = (
        (
            float(np.percentile(flat_path_sharpes, 25)),
            float(np.percentile(flat_path_sharpes, 50)),
            float(np.percentile(flat_path_sharpes, 75)),
        )
        if len(flat_path_sharpes) >= 4
        else (float("nan"), float("nan"), float("nan"))
    )

    if per_cell_mean_pbo is not None:
        pbo_result = PBOResult(
            pbo=per_cell_mean_pbo,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=len(cpcv_df),
            note=(
                f"Per-cell mean PBO={per_cell_mean_pbo:.4f} (iter-v3/004 cross-cell mean). "
                f"frac_positive_paths={frac_pos:.3f} from {len(cpcv_df)} return-proxy paths."
            ),
        )
    else:
        pbo_result = PBOResult(
            pbo=None,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=len(cpcv_df),
            note="Per-cell PBO: OOF parquet absent or all cells degenerate.",
        )
    print(f"  PBO result: {pbo_result.note}")

    # -------------------------------------------------------
    # DSR (clamp-free, brief Section 3.5#5)
    # -------------------------------------------------------
    is_ms_primary = _monthly_sharpe(is_trades)
    oos_ms_primary = _monthly_sharpe(oos_trades)
    # iter-v3/060: n_trials_total uses ensemble_size_for_run (3 or 10 depending on mode).
    n_trials_total = args.n_trials * ensemble_size_for_run * len(active_models)

    is_wp = np.array([float(t.weighted_pnl) for t in is_trades])
    if len(is_wp) > 1 and is_wp.std() > 0:
        raw_sharpe_is = float(is_wp.mean() / is_wp.std() * np.sqrt(len(is_wp)))
        sk = float(skew(is_wp))
        kt = float(kurtosis(is_wp, fisher=False))
        # Use deflated_sharpe_ratio_v3 — no negative-SR clamp
        dsr_result = deflated_sharpe_ratio_v3(
            observed_sr=raw_sharpe_is,
            num_trials=n_trials_total,
            backtest_length=len(is_wp),
            skewness=sk,
            kurtosis=kt,
        )
        dsr_val = dsr_result["p_value"]
    elif len(is_wp) > 1:
        # Zero variance — use a single-trade placeholder with raw SR = 0
        sk, kt = 0.0, 3.0
        dsr_result = deflated_sharpe_ratio_v3(
            observed_sr=0.0,
            num_trials=n_trials_total,
            backtest_length=len(is_wp),
            skewness=sk,
            kurtosis=kt,
        )
        dsr_val = dsr_result["p_value"]
    else:
        dsr_val = 0.0
        sk, kt = 0.0, 3.0

    # PSR on OOS trades
    oos_wp = np.array([float(t.weighted_pnl) for t in oos_trades])
    if len(oos_wp) > 1 and oos_wp.std() > 0:
        raw_sharpe_oos = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))
        oos_sk = float(skew(oos_wp))
        oos_kt = float(kurtosis(oos_wp, fisher=False))
        psr_val = psr(
            observed_sharpe=raw_sharpe_oos,
            n_obs=len(oos_wp),
            skewness=oos_sk,
            kurtosis=oos_kt,
        )
    else:
        raw_sharpe_oos = 0.0
        oos_sk = 0.0
        oos_kt = 3.0
        psr_val = 0.0

    # DSR_relative — PSR with CPCV path Sharpe Q75 benchmark (iter-v3/056 BUG FIX)
    # Per `analysis/iteration_v3-055/synthesis.md` Section R5: replaces structural
    # DSR=0 artifact with within-iteration null discipline. Reference: AFML Ch. 14
    # + Bailey-LdP (2014) JPM "Deflated Sharpe Ratio".
    # iter-v3/056: use in-memory flat_path_sharpes (already populated at line 2090)
    # instead of reading cpcv_paths.csv from disk (which is only written at line 2295).
    if len(flat_path_sharpes) >= 4:
        cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))
        print(
            f"[dsr_relative] CPCV path Q75 Sharpe = {cpcv_path_sharpe_q75:.4f} "
            f"(from {len(flat_path_sharpes)} in-memory paths)"
        )
    else:
        cpcv_path_sharpe_q75 = 0.0
        print(
            f"[dsr_relative] flat_path_sharpes has only {len(flat_path_sharpes)} elements "
            f"(<4 required) — cpcv_path_sharpe_q75 = 0.0 (fallback)"
        )

    # Compute DSR_relative using existing psr() function with non-zero benchmark
    if len(oos_wp) > 1 and oos_wp.std() > 0:
        dsr_relative = psr(
            observed_sharpe=raw_sharpe_oos,
            n_obs=len(oos_wp),
            skewness=oos_sk,
            kurtosis=oos_kt,
            benchmark_sharpe=cpcv_path_sharpe_q75,
        )
    else:
        dsr_relative = 0.0
    print(f"[dsr_relative] DSR_relative = {dsr_relative:.4f} (benchmark = CPCV Q75)")

    # N_eff: sub-fix #2 (iter-v3/004) — per-cell median aggregation.
    # Reads per_cell_pbo.csv written by _compute_cpcv_paths (which already
    # computed per-cell n_eff via n_effective_trials). Takes the median across
    # cells with rank > 1. Falls back to surrogate if CSV not available.
    per_cell_csv = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "per_cell_pbo.csv"
    n_eff = 1  # safe default

    if per_cell_csv.exists():
        try:
            per_cell_df_neff = pd.read_csv(per_cell_csv)
            informative_neff = per_cell_df_neff[per_cell_df_neff["rank"] > 1]["n_eff"].dropna()
            if len(informative_neff) > 0:
                n_eff = int(np.median(informative_neff))
                print(
                    f"[n_eff] Per-cell median n_eff={n_eff} from {len(informative_neff)} "
                    f"informative cells (rank>1) — iter-v3/004 sub-fix #2"
                )
            else:
                print("[n_eff] per_cell_pbo.csv has no informative cells — using n_eff=1")
        except Exception as e:
            print(f"[n_eff] Could not read per_cell_pbo.csv: {e} — using n_eff=1")
    elif len(is_wp) > 1:
        # Parquet not available — use iter-v3/002 surrogate (sym_month groups)
        sym_month_groups_fb: dict[tuple[str, str], list[float]] = {}
        for t in is_trades:
            sym_f = t.symbol
            month_f = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
            key_f = (sym_f, month_f)
            sym_month_groups_fb.setdefault(key_f, []).append(float(t.weighted_pnl))
        if len(sym_month_groups_fb) >= 2:
            max_len_fb = max(len(v) for v in sym_month_groups_fb.values())
            trial_mat_fallback = np.array(
                [v + [0.0] * (max_len_fb - len(v)) for v in sym_month_groups_fb.values()]
            )
            n_eff = n_effective_trials(trial_mat_fallback)
        else:
            n_eff = max(1, len(sym_month_groups_fb))
        print(f"[n_eff] per_cell_pbo.csv absent — using surrogate n_eff={n_eff}")

    min_trl_months = float(len(is_trades)) / max(1, ensemble_size_for_run * len(active_models))

    print(
        f"\n[metrics] IS monthly Sharpe={is_ms_primary:+.4f}, "
        f"OOS monthly Sharpe={oos_ms_primary:+.4f}"
    )
    print(f"[metrics] DSR={dsr_val:.4f}, PSR={psr_val:.4f}")
    pbo_display_inline = (
        "NaN(per-cell:no-data)" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    )
    print(
        f"[metrics] PBO={pbo_display_inline}, "
        f"frac_positive_paths={pbo_result.frac_positive_paths:.3f}"
    )
    print(f"[metrics] n_trials={n_trials_total}, n_eff={n_eff}")

    # -------------------------------------------------------
    # Reports
    # -------------------------------------------------------
    report_dir = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    report_dir.mkdir(parents=True, exist_ok=True)

    generate_iteration_reports(
        trades=braked,
        iteration=ITERATION_LABEL,
        features_dir="data/features",  # BTC regime annotation only
        reports_dir=str(REPORTS_DIR),
        interval="8h",
        n_trials=n_trials_total,
    )

    _write_feature_importance(is_trades, oos_trades, model_pairs, report_dir)

    _write_v3_comparison(
        is_trades,
        oos_trades,
        report_dir,
        dsr_val,
        pbo_result,
        psr_val,
        n_trials_total,
        n_eff,
    )

    # CPCV paths
    cpcv_path_file = report_dir / "cpcv_paths.csv"
    if not cpcv_df.empty:
        cpcv_df.to_csv(cpcv_path_file, index=False)
        print(f"[v3 report] cpcv_paths.csv: {len(cpcv_df)} paths")
    else:
        pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]).to_csv(
            cpcv_path_file, index=False
        )

    # ADF test results — per-(symbol, feature, month)
    adf_path = report_dir / "adf_test.csv"
    if not adf_df.empty:
        adf_df.to_csv(adf_path, index=False)
        # Verify row count (brief Section 3.5#4 runtime assertion)
        _verify_adf_row_count(adf_df, list(baseline_symbols))
        print(f"[v3 report] adf_test.csv: {len(adf_df)} rows (per sym×feat×month)")
    else:
        pd.DataFrame(
            columns=["symbol", "feature_name", "month", "adf_statistic", "p_value", "stationary"]
        ).to_csv(adf_path, index=False)

    # IC matrix
    ic_path = report_dir / "ic_matrix.csv"
    if not ic_mat.empty:
        ic_mat.to_csv(ic_path)
        print(f"[v3 report] ic_matrix.csv: {ic_mat.shape}")
    else:
        pd.DataFrame().to_csv(ic_path)

    # DSR JSON
    _write_dsr_json(
        report_dir,
        dsr_val,
        pbo_result,
        psr_val,
        n_trials_total,
        n_eff,
        min_trl_months,
        dsr_relative=dsr_relative,
        cpcv_path_sharpe_q75=cpcv_path_sharpe_q75,
    )

    # iter-v3/059: outer-seed loop eliminated.  Replace seed_summary.json +
    # pareto_front.csv with ensemble_summary.json (one record per ensemble seed
    # for reproducibility audit; no multi-seed Sharpe aggregation).
    # iter-v3/060: mode field added; only active_ensemble_seeds appear in the record list.
    ensemble_summary = {
        "mode": "exploration" if args.exploration else "confirmation",
        "ensemble_size": ensemble_size_for_run,
        "seeds": [
            {
                "ensemble_seed_index": i,
                "seed": s,
                "lineage": "outer=42" if i < 5 else "outer=123",
            }
            for i, s in enumerate(active_ensemble_seeds)
        ],
    }
    (report_dir / "ensemble_summary.json").write_text(json.dumps(ensemble_summary, indent=2))
    print(
        f"[v3 report] ensemble_summary.json: mode={ensemble_summary['mode']}, "
        f"{ensemble_summary['ensemble_size']} seeds "
        f"(replaces seed_summary.json + pareto_front.csv)"
    )

    t_end = time.time()
    elapsed_h = (t_end - t_start) / 3600.0
    print(f"\n[DONE] Reports: {report_dir}  (wall-clock: {elapsed_h:.2f}h)")
    print(f"  IS monthly Sharpe:  {is_ms_primary:+.4f}")
    print(f"  OOS monthly Sharpe: {oos_ms_primary:+.4f}")
    pbo_display = "NaN(per-cell:no-data)" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    print(f"  DSR={dsr_val:.4f}  PBO={pbo_display}  PSR={psr_val:.4f}")
    print(f"  n_eff={n_eff}  ADF rows={len(adf_df)}")


if __name__ == "__main__":
    main()
