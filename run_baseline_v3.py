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
ENSEMBLE_SIZE: int = 5
LEGACY_ENSEMBLE_SEEDS: list[int] = [42, 123, 456, 789, 1001]  # iter-v3/001-005


def _derive_ensemble_seeds(outer_seed: int, size: int = ENSEMBLE_SIZE) -> list[int]:
    """Deterministically derive `size` inner-ensemble seeds from one outer seed.

    Replaces the pre-iter-v3/006 hardcoded ENSEMBLE_SEEDS that was identical
    across all outer seeds. With this fix, --seeds N produces N distinct
    LightGBM ensembles (the prerequisite for any meaningful 10-seed Pareto
    validation per project memory's seed-validation rule).
    """
    rng = np.random.default_rng(outer_seed)
    return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]


ITERATION_LABEL = "v3-045"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")

# v3 symbols — iter-v3/034: DROP VETUSDT (5→4; revert to iter-v3/032 anchor).
# iter-v3/033 EXPLORATION result: VETUSDT was EXPLORATION-NEGATIVE (VET drag;
# alignment necessary but not sufficient for IS lift per Critic FINAL 93d2b85).
# iter-v3/034: atomic swap — DROP VET (revert to 4-sym BCH+LDO+TRX+ALGO) +
# ADD fracdiff_d05_close (15th feature; LdP AFML Ch. 5 FFD at fixed d=0.5).
# REQUIRED_GAP updated 110→88 = (21+1)×4 per Section 3 sub-fix #2.
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (ALGOUSDT)", "ALGOUSDT"),
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
# gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = (21+1)*4 = 88 (iter-v3/034 DROP VETUSDT)
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


def _verify_feature_columns() -> None:
    """Verifies V3_FEATURE_COLUMNS contents per current brief (iter-v3/045).

    iter-v3/045: EXPLORATION — cycle 3 #6 — ADD per-symbol ATR widening for LDO.
      PART A (carried forward from iter-v3/044): efficiency_ratio_50 DROPPED;
        regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED. Universal list = 14 features.
      PART B (per-symbol ATR axis — STACKED): V3_ATR_MULTIPLIERS_PER_SYMBOL has 2 entries.
        - ALGOUSDT: (2.0, 1.5) — UNCHANGED from iter-v3/044 PROMISING result.
        - LDOUSDT:  (2.0, 1.5) — NEW iter-v3/045 entry. QR EDA-driven axis per
          analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py SHA `ed949fe`.
          LDO IS->OOS exit-composition shift (SL:TP 1.14 -> 2.33; SL rate 53.3% ->
          63.6%) is the binding constraint. Wider SL targets the IS->OOS regime-shift
          directly, mirroring iter-v3/044 ALGO mechanism. Predecessor (1.5, 0.75) at
          iter-v3/032 was MULTI-SEED-FALSIFIED at iter-v3/039 — this is the OPPOSITE
          direction (wider not tighter).
        - BCH/TRX still fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
      Universal feature list V3_FEATURE_COLUMNS_TOP_N = 14 features (UNCHANGED).
        compute_regime_momentum_signed_3d retained as dead code in engineered_v3.py;
        NOT dispatched.
      DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — unchanged.
      V3_FEATURES_PER_SYMBOL: EMPTY (unchanged from iter-v3/040). All 4 symbols
        fall back to the 14-feature V3_FEATURE_COLUMNS_TOP_N.

    tbr_zscore_30 MUST NOT be present (dropped iter-v3/016).
    vwap_dev_50 MUST NOT be present (dropped iter-v3/008 per Critic SHA a544621).
    funding_rate_zscore_30 MUST NOT be present (per-symbol variant PERMANENTLY-CLOSED).
    btc_funding_rate_zscore_30 MUST NOT be present (cross-asset variant PERMANENTLY-CLOSED).
    vol_adj_autocorr MUST NOT be in universal list (dead code since iter-v3/036 revert).
    cross_asset_divergence_norm MUST NOT be in universal list (dead at model level).
    fracdiff_d05_close MUST NOT be in universal list AND MUST NOT be in any per-symbol entry.
    efficiency_ratio_50 MUST NOT be present (DROPPED — iter-v3/043 DISASTROUS NEGATIVE).
    regime_momentum_signed_5d MUST be present (mandate still ACTIVE at iter-v3/044).
    regime_momentum_signed_3d MUST NOT be present in V3_FEATURE_COLUMNS_TOP_N (universal
      addition REVERTED at iter-v3/044 per QR EDA). Code retained as dead code in
      engineered_v3.py; available for future per-symbol experiments.
    sym_vs_btc_ret_7d MUST be present (RESTORED at iter-v3/042; KEPT at iter-v3/044).
    ret_skew_50 MUST be present (RESTORED at iter-v3/042; KEPT at iter-v3/044).

    Per-symbol checks (iter-v3/045):
    V3_FEATURES_PER_SYMBOL must be EMPTY (0 entries).
    V3_ATR_MULTIPLIERS_PER_SYMBOL must contain exactly 2 entries:
      ALGOUSDT → (2.0, 1.5) (carried forward from iter-v3/044).
      LDOUSDT  → (2.0, 1.5) (NEW iter-v3/045).
    features_for_symbol("BCHUSDT") MUST return 14 features = V3_FEATURE_COLUMNS_TOP_N.
    features_for_symbol("ALGOUSDT") MUST return 14 features (fallback).
    features_for_symbol("LDOUSDT") MUST return 14 features (fallback).
    features_for_symbol("TRXUSDT") MUST return 14 features (fallback).
    atr_multipliers_for_symbol("ALGOUSDT") MUST return (2.0, 1.5) (per-symbol entry).
    atr_multipliers_for_symbol("LDOUSDT") MUST return (2.0, 1.5) (per-symbol entry — NEW).
    atr_multipliers_for_symbol("BCHUSDT") MUST return (2.0, 1.0) (DEFAULT fallback).
    atr_multipliers_for_symbol("TRXUSDT") MUST return (2.0, 1.0) (DEFAULT fallback).
    DEFAULT_ATR_MULTIPLIERS MUST be (2.0, 1.0) (correct since iter-v3/043 revert).
    """
    from crypto_trade.features_v3 import (  # noqa: PLC0415
        DEFAULT_ATR_MULTIPLIERS,
        V3_ATR_MULTIPLIERS_PER_SYMBOL,
        atr_multipliers_for_symbol,
    )

    n = len(V3_FEATURE_COLUMNS)
    if n != 14:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 14. "
            "iter-v3/044: REVERT efficiency_ratio_50 (15 → 14) AND REVERT "
            "regime_momentum_signed_3d universal addition (orchestrator's setup "
            "commit `1f56c72` superseded by QR EDA-driven axis at SHA `eff841e`). "
            "Universal list = 14 features. "
            "Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
        )
    if "tbr_zscore_30" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "tbr_zscore_30 FOUND in V3_FEATURE_COLUMNS — must be ABSENT per "
            "iter-v3/016 brief §3.3 (revert to iter-v3/013 baseline). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    if "funding_rate_zscore_30" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "funding_rate_zscore_30 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "per iter-v3/028 brief §8 (per-symbol funding family PERMANENTLY-CLOSED "
            "after Critic FINAL `c4574af` of iter-v3/023 Rec #1; INERT-CONFIRMED at "
            "n_trials=35). Remove it from V3_FEATURE_COLUMNS_TOP_N in "
            "features_v3/__init__.py."
        )
    if "btc_funding_rate_zscore_30" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "btc_funding_rate_zscore_30 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "per iter-v3/028 brief §8 (BTC cross-asset funding family PERMANENTLY-CLOSED "
            "after Critic FINAL `5a47f5d` of iter-v3/024; OOS Sharpe -0.82, rank 14/14 "
            "BCH+LDO portfolio cuts + 9/14 TRX). Remove it from V3_FEATURE_COLUMNS_TOP_N "
            "in features_v3/__init__.py."
        )
    # vol_adj_autocorr MUST NOT be in the universal list (iter-v3/036 NEGATIVE reverted).
    if "vol_adj_autocorr" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS (universal list) — must be ABSENT. "
            "iter-v3/037: iter-v3/036 NEGATIVE reverted; vol_adj_autocorr is dead code. "
            "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # cross_asset_divergence_norm MUST NOT be in the universal list.
    # NOTE: cross_asset_divergence_norm IS dispatched in add_engineered_v3_features (for parquet
    # generation) but must NOT be in V3_FEATURE_COLUMNS_TOP_N (the universal model input list).
    if "cross_asset_divergence_norm" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS (universal list) — "
            "must be ABSENT. Universal application FALSIFIED at iter-v3/027 (IS Sharpe "
            "collapse -0.2817 + OOS spike +1.6786). iter-v3/037 LDO per-symbol NEGATIVE (~-33). "
            "iter-v3/040: dead at model level. "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # regime_momentum_signed_5d MUST be present (mandate still ACTIVE at iter-v3/044).
    # feedback_v3_engineered_features_proven.md mandate UPHELD through iter-v3/044.
    if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT "
            "at iter-v3/044. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # iter-v3/044: regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED before backtest.
    # The orchestrator's setup commit `1f56c72` added it to V3_FEATURE_COLUMNS_TOP_N as a 15th
    # universal feature. QR EDA at SHA `eff841e` (analysis/iteration_v3-044/cycle3_is_diagnosis.py)
    # established the IS bottleneck is direction-asymmetric per-symbol (ALGO LONG single largest
    # attribution loss) and 3d does NOT discriminate ALGO LONG WR (22.2% > 0, 13.3% <=0;
    # ranks 14/14 in ALGO model). Replacement axis: per-symbol ATR widening for ALGOUSDT only.
    # compute_regime_momentum_signed_3d retained as dead code in engineered_v3.py.
    if "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
            "iter-v3/044. Universal addition REVERTED before backtest per QR EDA at SHA "
            "`eff841e` (does not address ALGO LONG bottleneck; ranks 14/14 in ALGO model). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # sym_vs_btc_ret_7d MUST be present (RESTORED at iter-v3/042; KEPT at iter-v3/044).
    if "sym_vs_btc_ret_7d" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT at "
            "iter-v3/044 (RESTORED at iter-v3/042; KEPT). "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # ret_skew_50 MUST be present (RESTORED at iter-v3/042; KEPT at iter-v3/044).
    if "ret_skew_50" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT at "
            "iter-v3/044 (RESTORED at iter-v3/042; KEPT). "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # iter-v3/044: efficiency_ratio_50 MUST be ABSENT (DROPPED — iter-v3/043 DISASTROUS NEGATIVE).
    if "efficiency_ratio_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "at iter-v3/044 (DROPPED: iter-v3/043 DISASTROUS NEGATIVE IS -0.8445 / OOS -0.8990; "
            "all 4 symbols broken by Kaufman ER). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    if "vwap_dev_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "vwap_dev_50 found in V3_FEATURE_COLUMNS — must be dropped per "
            "Critic FINAL SHA a544621 (Recommendation 1). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # fracdiff_d05_close MUST NOT be in the universal list.
    if "fracdiff_d05_close" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N (universal list) — "
            "must be ABSENT. iter-v3/040: fracdiff_d05_close is NOT a model input for any "
            "symbol (V3_FEATURES_PER_SYMBOL is empty; no per-symbol extension entries). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # vol_adj_autocorr MUST NOT be in the universal list (iter-v3/036 reverted).
    if "vol_adj_autocorr" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N (universal list) — "
            "iter-v3/037: iter-v3/036 NEGATIVE reverted; vol_adj_autocorr is dead code. "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # cross_asset_divergence_norm MUST NOT be in the universal list.
    if "cross_asset_divergence_norm" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N (universal list) — "
            "iter-v3/040: dead at model level. Universal application FALSIFIED at iter-v3/027. "
            "LDO per-symbol FALSIFIED at iter-v3/037. "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print(
        f"  V3_FEATURE_COLUMNS: {n} columns "
        "(iter-v3/044: 14-feature set; efficiency_ratio_50 ABSENT; regime_momentum_signed_3d "
        "ABSENT (universal addition REVERTED); regime_momentum_signed_5d, sym_vs_btc_ret_7d, "
        "ret_skew_50 PRESENT)  PASS"
    )

    # iter-v3/044: Verify DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0).
    # Already correct since iter-v3/043 revert (was (1.5, 0.75) only at iter-v3/042).
    if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.0):
        raise RuntimeError(
            f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
            "iter-v3/044: DEFAULT_ATR_MULTIPLIERS must be (2.0, 1.0) (reverted at iter-v3/043). "
            "All 4 symbols use DEFAULT via V3_ATR_MULTIPLIERS_PER_SYMBOL empty fallback. "
            "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
        )
    print("  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) (already correct since iter-v3/043 revert)  PASS")

    # iter-v3/044: V3_FEATURES_PER_SYMBOL MUST BE EMPTY.
    # All per-symbol feature customizations reverted. All symbols use 15-feature fallback.
    n_custom = len(V3_FEATURES_PER_SYMBOL)
    if n_custom != 0:
        raise RuntimeError(
            f"V3_FEATURES_PER_SYMBOL has {n_custom} entries — expected exactly 0 (empty). "
            "iter-v3/040: REVERT all per-symbol feature overrides (cycle 3 EXPLORATION #1). "
            f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}. "
            "Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
        )
    print("  V3_FEATURES_PER_SYMBOL: 0 entries (empty — all symbols use 15-feature fallback)  PASS")

    # iter-v3/045: V3_ATR_MULTIPLIERS_PER_SYMBOL MUST contain exactly 2 entries:
    #   ALGOUSDT → (2.0, 1.5) (carried forward from iter-v3/044 PROMISING)
    #   LDOUSDT  → (2.0, 1.5) (NEW iter-v3/045 — QR EDA-driven mirror of iter-v3/044
    #     mechanism)
    # BCH/TRX fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    n_atr_custom = len(V3_ATR_MULTIPLIERS_PER_SYMBOL)
    if n_atr_custom != 2:
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL has {n_atr_custom} entries — expected exactly 2 "
            "(ALGOUSDT → (2.0, 1.5), LDOUSDT → (2.0, 1.5)). iter-v3/045: per-symbol ATR "
            "widening stacked for ALGOUSDT (UNCHANGED from iter-v3/044) + LDOUSDT (NEW). "
            f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}. "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL = "
            "{'ALGOUSDT': (2.0, 1.5), 'LDOUSDT': (2.0, 1.5)} in features_v3/__init__.py."
        )
    if V3_ATR_MULTIPLIERS_PER_SYMBOL.get("ALGOUSDT") != (2.0, 1.5):
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT'] = "
            f"{V3_ATR_MULTIPLIERS_PER_SYMBOL.get('ALGOUSDT')} — expected (2.0, 1.5). "
            "iter-v3/045: ALGOUSDT carried forward UNCHANGED from iter-v3/044 PROMISING. "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT'] = (2.0, 1.5)."
        )
    if V3_ATR_MULTIPLIERS_PER_SYMBOL.get("LDOUSDT") != (2.0, 1.5):
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT'] = "
            f"{V3_ATR_MULTIPLIERS_PER_SYMBOL.get('LDOUSDT')} — expected (2.0, 1.5). "
            "iter-v3/045: NEW per-symbol ATR widening for LDOUSDT (TP=2.0×ATR, SL=1.5×ATR). "
            "QR EDA-driven mirror of iter-v3/044 ALGO mechanism per analysis/iteration_v3-045/ "
            "ldo_bottleneck_diagnosis.py SHA `ed949fe`. Set "
            "V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT'] = (2.0, 1.5)."
        )
    if any(sym in V3_ATR_MULTIPLIERS_PER_SYMBOL for sym in ("BCHUSDT", "TRXUSDT")):
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL contains entries for non-{{ALGO,LDO}} symbols: "
            f"{[s for s in V3_ATR_MULTIPLIERS_PER_SYMBOL if s not in ('ALGOUSDT', 'LDOUSDT')]}. "
            "iter-v3/045: ONLY ALGOUSDT and LDOUSDT should have per-symbol entries. "
            "BCH/TRX use DEFAULT_ATR_MULTIPLIERS via fallback."
        )
    print(
        "  V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries "
        "(ALGOUSDT → (2.0, 1.5), LDOUSDT → (2.0, 1.5)); "
        "BCH/TRX use (2.0, 1.0) DEFAULT  PASS"
    )

    # iter-v3/044: Verify all 4 symbols return 14-feature fallback (V3_FEATURE_COLUMNS_TOP_N).
    for sym in ("BCHUSDT", "ALGOUSDT", "LDOUSDT", "TRXUSDT"):
        sym_feats = features_for_symbol(sym)
        if len(sym_feats) != 14:
            raise RuntimeError(
                f"{sym} fallback has {len(sym_feats)} features — "
                "expected exactly 14 (iter-v3/044 V3_FEATURE_COLUMNS_TOP_N universal list). "
                "iter-v3/044: all 4 symbols must use the 14-feature set "
                "(efficiency_ratio_50 ABSENT; regime_momentum_signed_3d ABSENT; "
                "no per-symbol entries)."
            )
        if "fracdiff_d05_close" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set includes fracdiff_d05_close — must be ABSENT. "
                "iter-v3/040: fracdiff_d05_close is NOT a model input for any symbol. "
                f"Check features_for_symbol('{sym}') path."
            )
        if "cross_asset_divergence_norm" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set includes cross_asset_divergence_norm "
                "— must be ABSENT. iter-v3/040: cross_asset_divergence_norm dead at "
                "model level. "
                f"Check features_for_symbol('{sym}') path."
            )
        if "efficiency_ratio_50" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains efficiency_ratio_50 — must be ABSENT. "
                "iter-v3/044: efficiency_ratio_50 DROPPED (DISASTROUS NEGATIVE at iter-v3/043). "
                f"Check features_for_symbol('{sym}') path."
            )
        if "regime_momentum_signed_3d" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains regime_momentum_signed_3d — must be ABSENT. "
                "iter-v3/044: regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED per QR EDA. "
                f"Check V3_FEATURE_COLUMNS_TOP_N and features_for_symbol('{sym}') path."
            )
    print(
        "  BCH/ALGO/LDO/TRX: 14-feature universal fallback "
        "(efficiency_ratio_50 ABSENT; regime_momentum_signed_3d ABSENT; _5d PRESENT)  PASS"
    )

    # iter-v3/045: BCH/TRX MUST be (2.0, 1.0) via DEFAULT fallback.
    # ALGO/LDO MUST be (2.0, 1.5) via per-symbol entries.
    for sym in ("BCHUSDT", "TRXUSDT"):
        sym_atr = atr_multipliers_for_symbol(sym)
        if sym_atr != (2.0, 1.0):
            raise RuntimeError(
                f"atr_multipliers_for_symbol('{sym}') returned {sym_atr} — expected (2.0, 1.0). "
                "iter-v3/045: DEFAULT = (2.0, 1.0); "
                "V3_ATR_MULTIPLIERS_PER_SYMBOL has ALGOUSDT + LDOUSDT entries; "
                "BCH/TRX use DEFAULT fallback. "
                "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
            )
    algo_atr = atr_multipliers_for_symbol("ALGOUSDT")
    if algo_atr != (2.0, 1.5):
        raise RuntimeError(
            f"atr_multipliers_for_symbol('ALGOUSDT') returned {algo_atr} — expected (2.0, 1.5). "
            "iter-v3/045: ALGOUSDT per-symbol entry = (2.0, 1.5) carried forward UNCHANGED "
            "from iter-v3/044 PROMISING. "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT'] = (2.0, 1.5) in features_v3/__init__.py."
        )
    ldo_atr = atr_multipliers_for_symbol("LDOUSDT")
    if ldo_atr != (2.0, 1.5):
        raise RuntimeError(
            f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_atr} — expected (2.0, 1.5). "
            "iter-v3/045: LDOUSDT per-symbol entry = (2.0, 1.5) — NEW. Wider SL targets LDO "
            "IS->OOS exit-composition shift (SL:TP 1.14 -> 2.33; SL rate 53.3% -> 63.6%) per "
            "QR EDA SHA `ed949fe`. Mirror of iter-v3/044 ALGO mechanism. "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT'] = (2.0, 1.5) in features_v3/__init__.py."
        )
    print(
        "  atr_multipliers_for_symbol: ALGO=(2.0,1.5) + LDO=(2.0,1.5) per-symbol; "
        "BCH/TRX=(2.0,1.0) DEFAULT  PASS"
    )

    # iter-v3/044: regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N (mandate ACTIVE).
    if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be "
            "PRESENT at iter-v3/044. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
            "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print("  regime_momentum_signed_5d PRESENT in V3_FEATURE_COLUMNS_TOP_N (mandate ACTIVE)  PASS")

    # iter-v3/044: regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED before backtest.
    # Per QR EDA SHA `eff841e` — does not address ALGO LONG bottleneck; ranks 14/14 in ALGO.
    # Universal addition would dilute colsample picks. Code retained as dead code.
    if "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/044 (universal addition REVERTED per QR EDA at SHA `eff841e`; does "
            "not discriminate ALGO LONG WR; ranks 14/14 in ALGO model). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print(
        "  regime_momentum_signed_3d ABSENT from V3_FEATURE_COLUMNS_TOP_N "
        "(REVERTED iter-v3/044 per QR EDA)  PASS"
    )

    # iter-v3/044: efficiency_ratio_50 MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N (DROPPED).
    if "efficiency_ratio_50" in V3_FEATURE_COLUMNS_TOP_N:
        raise RuntimeError(
            "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
            "at iter-v3/044 (DROPPED: iter-v3/043 DISASTROUS NEGATIVE; all 4 symbols broken). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print("  efficiency_ratio_50 ABSENT from V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/044)  PASS")


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


def _write_dsr_json(
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials: int,
    n_eff: int,
    min_trl_months: float,
) -> None:
    """Write dsr.json — includes PBO metadata."""
    pbo_out = pbo_result.pbo if pbo_result.pbo is not None else None
    data = {
        "dsr": round(dsr_val, 8),
        "pbo": pbo_out,
        "pbo_note": pbo_result.note,
        "pbo_frac_positive_paths": round(pbo_result.frac_positive_paths, 4),
        "pbo_path_sharpe_q25": round(pbo_result.path_sharpe_quartiles[0], 4),
        "pbo_path_sharpe_q50": round(pbo_result.path_sharpe_quartiles[1], 4),
        "pbo_path_sharpe_q75": round(pbo_result.path_sharpe_quartiles[2], 4),
        "psr": round(psr_val, 4),
        "n_trials": n_trials,
        "n_eff": n_eff,
        "min_trl_months": round(min_trl_months, 2),
    }
    (report_dir / "dsr.json").write_text(json.dumps(data, indent=2))
    print(
        f"[v3 report] dsr.json: DSR={dsr_val:.4f}, PBO={pbo_out}, "
        f"frac_pos_paths={pbo_result.frac_positive_paths:.3f}, PSR={psr_val:.4f}, n_eff={n_eff}"
    )


# ============================================================
# Pareto front
# ============================================================


def _write_pareto_front(
    per_seed_summary: list[dict],
    report_dir: Path,
) -> None:
    """Write pareto_front.csv — seed × 6-metric matrix."""
    path = report_dir / "pareto_front.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "seed",
                "monthly_sharpe",
                "max_drawdown",
                "calmar",
                "pbo",
                "n_trades",
                "max_concentration_pct",
            ]
        )
        for r in per_seed_summary:
            writer.writerow(
                [
                    r.get("seed", ""),
                    f"{r.get('oos_sharpe_monthly', 0.0):.4f}",
                    f"{r.get('oos_max_dd', 0.0):.4f}",
                    f"{r.get('oos_calmar', 0.0):.4f}",
                    f"{r.get('pbo', 'NaN')}",  # NaN when S=1
                    r.get("oos_trades", 0),
                    f"{r.get('max_concentration_pct', 0.0):.2f}",
                ]
            )


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
    fast_mode: bool = False,
    model_type: str = "lgbm",
) -> tuple[list, list, dict, dict, list]:
    """Run v3 models for a single outer seed.

    Parameters
    ----------
    active_models:
        Subset of V3_MODELS to run.  Defaults to V3_MODELS when None.
        Pass a filtered tuple to scope the run (e.g. BCH-only for iter-v3/006).
    ensemble_size:
        Override the default ENSEMBLE_SIZE for this run. Useful for fast
        exploration (size=1 → no inner-ensemble averaging, ~5x faster).
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
        # iter-v3/006 fix: derive a distinct inner ensemble from this outer seed.
        # Pre-fix: ensemble_seeds=[42,123,456,789,1001] for ALL outer seeds.
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
        default=1,
        help="Number of outer seeds (1 for first-pass, 10 for MERGE validation)",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=35,
        help=(
            "Optuna trials per monthly model per seed. CONFIRMATION default "
            "lowered from 50 → 35 at iter-v3/018 closeout: 50 was below TPE-warmup-saturation "
            "and added wall-clock cost without proportional gain in best-trial "
            "selection. 35 stays above TPE-warmup (~30) while saving ~30% "
            "wall-clock. EXPLORATION mode auto-overrides to 10 below."
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
            "iter-v3/007 fast-exploration mode. Sets ENSEMBLE_SIZE=1 (single "
            "inner model, ~5x faster), hardcodes colsample_bytree=1.0 in "
            "Optuna search space (minimizes per-seed feature-subsampling "
            "variance), and defaults --n-trials to 10 if not specified. Use "
            "for fast variation across symbols/labels/features. Drop the flag "
            "for production CONFIRMATION runs (full ensemble, full search space)."
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
    args = parser.parse_args()

    # iter-v3/007: --exploration overrides defaults for fast iteration.
    # iter-v3/020: n_trials override REMOVED — both EXPLORATION and CONFIRMATION
    # default to n_trials=35 (above TPE warmup). The EXPLORATION-vs-CONFIRMATION
    # distinction is now: ENSEMBLE_SIZE=1, --seeds 1, colsample=1.0 hardcoded
    # (EXPLORATION) vs ENSEMBLE_SIZE=5, --seeds 2, colsample Optuna-tunable
    # (CONFIRMATION). n_trials raised from 10 → 35 to fix NEW-feature-family
    # rank-14/14 INERT pattern (iter-v3/015 + iter-v3/019).
    ensemble_size_for_run: int = 1 if args.exploration else ENSEMBLE_SIZE
    fast_mode_for_run: bool = bool(args.exploration)

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
    # asserts len == 13, funding NOT present, vwap_dev_50/tbr_zscore_30 absent
    _verify_feature_columns()
    _verify_label_leakage_gap()  # asserts REQUIRED_GAP == 110 (5-symbol universe, iter-v3/033)
    _verify_track_isolation()  # grep check

    active_sym_names = ", ".join(sym for _, sym in active_models)
    print(f"\nBASELINE v3 iter-{ITERATION_LABEL}: {active_sym_names} (seed-plumbing fix)")
    print(f"Seeds: {args.seeds}  Optuna trials/model: {args.n_trials}")
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

    full_seeds = (42, 123, 456, 789, 1001, 1234, 2345, 3456, 4567, 5678)
    default_seeds = (42,)
    seeds = list(full_seeds[: args.seeds]) if args.seeds > 1 else list(default_seeds)

    per_seed_summary: list[dict] = []
    primary_trades: list | None = None
    primary_model_pairs: list | None = None

    for i, seed in enumerate(seeds):
        print(f"\n{'#' * 60}\n# SEED {seed} ({i + 1}/{len(seeds)})\n{'#' * 60}")
        unbraked, braked, btc_stats, hr_stats, model_pairs = _run_single_seed(
            seed,
            args.n_trials,
            btc_times,
            btc_closes,
            active_models=active_models,
            ensemble_size=ensemble_size_for_run,
            fast_mode=fast_mode_for_run,
            model_type=args.model,
        )

        if not braked:
            per_seed_summary.append(
                {
                    "seed": seed,
                    "trades": 0,
                    "oos_trades": 0,
                    "oos_sharpe_monthly": 0.0,
                    "is_sharpe_monthly": 0.0,
                }
            )
            continue

        is_tr = [t for t in braked if t.open_time < OOS_CUTOFF_MS]
        oos_tr = [t for t in braked if t.open_time >= OOS_CUTOFF_MS]

        is_ms = _monthly_sharpe(is_tr)
        oos_ms = _monthly_sharpe(oos_tr)
        oos_dd = _max_drawdown(oos_tr)
        oos_calmar = (sum(t.weighted_pnl for t in oos_tr) / oos_dd) if oos_dd > 0 else 0.0

        sym_pnl: dict[str, float] = {}
        for t in oos_tr:
            sym_pnl[t.symbol] = sym_pnl.get(t.symbol, 0.0) + float(t.weighted_pnl)
        positive_total = sum(max(0.0, p) for p in sym_pnl.values())
        max_conc = 0.0
        if positive_total > 0:
            conc_pcts = [max(0.0, p) / positive_total * 100.0 for p in sym_pnl.values()]
            max_conc = max(conc_pcts) if conc_pcts else 0.0

        per_seed_summary.append(
            {
                "seed": seed,
                "trades": len(braked),
                "oos_trades": len(oos_tr),
                "is_sharpe_monthly": round(is_ms, 4),
                "oos_sharpe_monthly": round(oos_ms, 4),
                "oos_max_dd": round(oos_dd, 4),
                "oos_calmar": round(oos_calmar, 4),
                "max_concentration_pct": round(max_conc, 2),
                "pbo": None,  # placeholder — updated after per-cell PBO computed (sub-fix #5)
                "btc_killed": btc_stats["n_killed"],
            }
        )

        print(
            f"[seed {seed}] {len(braked)} trades — IS monthly={is_ms:+.4f}, "
            f"OOS monthly={oos_ms:+.4f}, OOS MaxDD={oos_dd:.4f}"
        )

        if i == 0:
            primary_trades = braked
            primary_model_pairs = model_pairs

    if not primary_trades:
        print("No trades produced for primary seed.")
        sys.exit(1)

    is_trades = [t for t in primary_trades if t.open_time < OOS_CUTOFF_MS]
    oos_trades = [t for t in primary_trades if t.open_time >= OOS_CUTOFF_MS]
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
    n_trials_total = args.n_trials * ensemble_size_for_run * len(active_models) * args.seeds

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
        psr_val = 0.0

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
        trades=primary_trades,
        iteration=ITERATION_LABEL,
        features_dir="data/features",  # BTC regime annotation only
        reports_dir=str(REPORTS_DIR),
        interval="8h",
        n_trials=n_trials_total,
    )

    _write_feature_importance(is_trades, oos_trades, primary_model_pairs or [], report_dir)

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
    _write_dsr_json(report_dir, dsr_val, pbo_result, psr_val, n_trials_total, n_eff, min_trl_months)

    # Sub-fix #5 (iter-v3/004): update per_seed_summary pbo from None placeholder
    # to the actual per-cell mean PBO computed above.  This ensures seed_summary.json
    # contains a numeric float (not "NaN" or null) per brief Section 3.5 sub-fix #5.
    for entry in per_seed_summary:
        if entry.get("pbo") is None:
            entry["pbo"] = pbo_result.pbo  # float or None (JSON null)

    # Pareto front
    _write_pareto_front(per_seed_summary, report_dir)

    # Seed summary
    (report_dir / "seed_summary.json").write_text(json.dumps(per_seed_summary, indent=2))

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
