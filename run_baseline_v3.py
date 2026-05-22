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
import io
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
from crypto_trade.iteration_report import (
    _write_confidence_distribution,
    generate_iteration_reports,
)
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
# TeeLogger — iter-v3/130 run.log fix (5-occurrence recurrence)
# ============================================================


class _TeeLogger(io.TextIOWrapper):
    """Write stdout to both the original stream and a log file.

    iter-v3/130: fixes the 5-occurrence run.log missing pattern (/124/125/127/128/129).
    The runner prints heavily via print(); redirecting sys.stdout ensures all
    output — including from library callbacks — lands in the log file.

    Usage:
        tee = _TeeLogger(log_path)
        try:
            ...
        finally:
            tee.close()
    """

    def __init__(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = open(log_path, "w", encoding="utf-8", buffering=1)  # noqa: SIM115
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        # Point sys.stdout/sys.stderr at self (which delegates to both).
        sys.stdout = self  # type: ignore[assignment]
        sys.stderr = self  # type: ignore[assignment]

    def write(self, data: str) -> int:  # type: ignore[override]
        self._original_stdout.write(data)
        self._log_file.write(data)
        return len(data)

    def flush(self) -> None:
        self._original_stdout.flush()
        self._log_file.flush()

    def close(self) -> None:  # type: ignore[override]
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._log_file.close()

    # Needed so subprocess / os calls that check isatty() don't break.
    def isatty(self) -> bool:
        return False

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return "utf-8"


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


ITERATION_LABEL = "v3-130"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
FEATURES_DIR_24H = Path("data/features_v3_24h")
# iter-v3/130: 4h bar-interval axis — native 4h klines + 4h feature parquets.
FEATURES_DIR_4H = Path("data/features_v3_4h")
DATA_DIR = Path("data")

# v3 symbols — iter-v3/051: SYSTEM-LEVEL REVERT to iter-v3/028 architecture.
# Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
# confirmation of per-symbol-customization anti-pattern at iter-v3/039 + iter-v3/050
# both CONFIRMATION-NO-MERGE on per-symbol bundle). ALGOUSDT REVERTED (4→3 symbols).
# iter-v3/069: UNIVERSE EXPANSION axis — ADAUSDT added (4th symbol).
# iter-v3/070: REVERT /069 universe expansion — ADAUSDT removed (INERT at EXPLORATION);
# cycle 1 CONFIRMATION runs on 3-symbol universe (BCH+LDO+TRX).
# iter-v3/078 (cycle-2 EXPLORATION #8): UNIVERSE REVISION axis — REPLACE LDOUSDT
# with ADAUSDT. Verdict SUSPICIOUS-OOS-DOMINANT (Critic FINAL `75f4d42`): the
# universe swap loaded the v3 IS/OOS regime factor via ADA's duration-loaded roster
# (+2.23-candle holding-time gap). The universe-revision axis is CLOSED for cycle 2.
# iter-v3/079 (cycle-2 EXPLORATION #9): V3_MODELS REVERTS BCH/ADA/TRX → BCH/LDO/TRX.
# This is a BASELINE-RESTORE of the closed /078 axis (the established "mandatory
# secondary edit" pattern — cf. /076 reverting /075's primitive 12, /077 reverting
# /076's feature), NOT a new varied axis. The /079 PRIMARY axis is the
# conviction-weighted per-trade sizing primitive (primitive 13) in lgbm.py — see
# briefs-v3/iteration_v3-079/research_brief.md Section 3. REQUIRED_GAP stays
# 66 = (21+1)×3 (3 symbols).
# iter-v3/083 (cycle-3 EXPLORATION #2): UNIVERSE EXPANSION axis — V3_MODELS grew
# 3 → 4 symbols by ADDING FILUSDT. Verdict NEGATIVE/NO-MERGE (Critic FINAL
# `1116124`): IS monthly Sharpe collapsed −0.9156 (FIL's own −32% IS edge + a
# confounding ~70pp /059 anchor-staleness drift). FILUSDT joins HBAR/AVAX/ADA as
# a CLOSED universe-expansion candidate.
# iter-v3/084 (cycle-3 REFERENCE / METHODOLOGY): V3_MODELS REVERTS BCH/LDO/TRX/FIL
# → BCH/LDO/TRX (drop FILUSDT — a NEGATIVE-axis symbol is not carried forward).
# iter-v3/087 (cycle-3 EXPLORATION #6): WHOLESALE universe-breadth EXPANSION —
# V3_MODELS grows 3 → 6 by ADDING GALAUSDT + MANAUSDT + SANDUSDT in ONE step.
# This is the SOLE /087 axis: denominator expansion via the Grinold-Kahn breadth
# lever (IR = IC*sqrt(breadth)). It is structurally DISTINCT from the CLOSED
# swap-by-replacement family (/078 swapped LDO→ADA at constant count) — every
# incumbent is KEPT, 3 symbols are ADDED. It is NOT /083's single-weak-symbol
# add (FILUSDT, which collapsed IS -0.92): /087 is a WHOLESALE expansion (N
# 3->6, a 2.04x breadth multiplier) and the 3 symbols were selected on the
# Bailey-Lopez de Prado (2012, SSRN 2003638) Sharpe-Ratio-Indifference-Curve
# framework — the per-symbol-Sharpe + cross-symbol strategy-PnL-correlation
# screen the /083 per-symbol-only screen lacked. EDA SHA `1a117b2`: the
# wholesale-6 book aggregate IS monthly Sharpe lifts +0.2371 over the 3-symbol
# book, leave-one-out all positive. Each added symbol gets one independent
# per-symbol LightGBM, the identical 14-feature stack, identical (2.0,1.0)-ATR
# triple-barrier, identical 7-gate risk stack — a fully universal addition
# (feedback_v3_per_symbol_lifts_oos_breaks_is.md satisfied). REQUIRED_GAP
# recomputes 66 → 132 = (21+1)*6 (6 symbols). See
# briefs-v3/iteration_v3-087/research_brief.md.
# iter-v3/088 (cycle-3 EXPLORATION #7 — RE-ARCHITECTURE): MANDATORY /087
# baseline-restore — V3_MODELS REVERTS 6 → 3 (drop GALAUSDT/MANAUSDT/SANDUSDT;
# /087's wholesale expansion classified NEGATIVE, a NEGATIVE-axis universe is
# not carried forward). REQUIRED_GAP recomputes 132 → 66 = (21+1)*3.
# V3_MODELS below is the PER-SYMBOL legacy path. iter-v3/088 RE-ARCHITECTS to a
# cross-sectional relative-value ranking model: the production cross-sectional
# path uses XS_UNIVERSE (the 22-symbol cross-section screened IS-only in
# analysis/iteration_v3-088/cross_sectional_signal_eda.py, EDA SHA aebd9f3) and
# a NEW pooled-ranking backtest path built in Phase 6 per brief Section 3. The
# 3-symbol V3_MODELS is the clean /059-state restore the QE builds the new path
# onto — it is NOT the iter-v3/088 trading universe.
V3_MODELS: tuple[tuple[str, str], ...] = (
    # iter-v3/127: V3_MODELS BCH/LDO/TRX (sole axis was per-symbol drawdown brake). NEGATIVE
    # (IS +0.31 / OOS -0.19; catastrophic OOS collapse). Drawdown brake axis CLOSED per
    # Critic FINAL. /128 mandatory baseline-restore: brake REVERTED
    # (enable_per_symbol_drawdown_brake=False).
    # iter-v3/128: WHOLESALE V3_MODELS REPLACEMENT BCH/LDO/TRX → 6-symbol sector-pure L1
    # universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO). 9/9 NEGATIVE (catastrophic across all L1
    # symbols; universe-substitution axis CLOSED at /128). REQUIRED_GAP 66→132 override.
    # iter-v3/129: REVERT V3_MODELS → BCH/LDO/TRX (/121 baseline universe).
    # REQUIRED_GAP REVERT 132→66 = (21+1)*3. Sole axis: continuous size-scaling
    # at per-symbol 45-day rolling drawdown (primitive 13).
    # iter-v3/130: bar-interval 8h→4h axis. /127 binary brake REVERTED (closed).
    # /129 continuous scaling REVERTED (closed). Sole axis: 4h bar interval.
    # enable_per_symbol_drawdown_scaling REVERTED to False.
    ("v3-130-BCH", "BCHUSDT"),
    ("v3-130-LDO", "LDOUSDT"),
    ("v3-130-TRX", "TRXUSDT"),
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


def _verify_data_freshness(
    symbols: tuple[str, ...],
    max_lag_hours: float = 16.0,
    bar_interval: str = "8h",
) -> None:
    """Hard-fail on stale data (>16h lag).

    iter-v3/130: bar_interval-conditional — checks 4h.csv at 4h, 8h.csv at 8h.
    BTCUSDT is always checked at 8h (BTC trend filter uses 8h klines regardless).
    """
    now_ms = int(time.time() * 1000)
    stale: list[tuple[str, float]] = []
    for sym in symbols:
        # BTC trend filter always uses 8h klines; other symbols use the bar_interval.
        _csv_interval = "8h" if sym == "BTCUSDT" else bar_interval
        p = DATA_DIR / sym / f"{_csv_interval}.csv"
        if not p.exists():
            raise RuntimeError(
                f"v3 runner: missing CSV for {sym} at {p}. "
                f"Run `uv run crypto-trade fetch --symbols {sym} --intervals {_csv_interval}`"
            )
        df = pd.read_csv(p, usecols=["close_time"])
        last_close = int(df["close_time"].max())
        lag_h = (now_ms - last_close) / 3_600_000
        if lag_h > max_lag_hours:
            stale.append((sym, round(lag_h, 1)))
    if stale:
        _fetch_interval = bar_interval
        raise RuntimeError(
            f"v3 runner: STALE DATA (>{max_lag_hours}h lag): {stale}. "
            f"Run `uv run crypto-trade fetch --symbols {','.join(s for s, _ in stale)} "
            f"--intervals {_fetch_interval}`"
        )


def _verify_feature_columns(
    ensemble_size: int | None = None,
    bar_interval: str = "8h",
) -> None:
    """Verifies V3_FEATURE_COLUMNS contents per current brief (iter-v3/088).

    Parameters
    ----------
    ensemble_size:
        Effective ensemble size for this run (3 = EXPLORATION, 10 = CONFIRMATION).
        If provided, asserts the value is in (3, 10) to enforce mode discipline.
        If None, skips the ensemble-size mode check (backward compat for direct
        calls in unit tests that don't care about mode).
    bar_interval:
        iter-v3/130: '4h' or '8h' (default). Controls the expected label_timeout_minutes
        in the model pre-flight check. At 4h: 5040 (K=21 × 4h × 60). At 8h: 10080.

    iter-v3/088: CYCLE 3 EXPLORATION #7 — RE-ARCHITECTURE. The axis is a NEW
      cross-sectional relative-value RANKING model (brief Section 3); it is NOT
      a feature-column change. The 14-feature /059 anchor stack
      V3_FEATURE_COLUMNS_TOP_N is UNCHANGED — the cross-sectional ranking model
      reuses it (cross-sectionally normalized; btc_ret_14d is dropped from the
      XS feature set per EDA T6 zero-dispersion, but the column constant is
      untouched). This check still asserts len == 14 and the closed-feature
      ABSENT-bans hold. ITERATION_LABEL = "v3-088".
      Evidence: analysis/iteration_v3-087/.

    iter-v3/086: CYCLE 3 EXPLORATION #5 — APPENDED the 3-feature perp-spot BASIS
      family (count 14 -> 17). Verdict INERT (the 7-FEED STRUCTURAL VERDICT) —
      the 3 basis features are DROPPED at the /087 setup and join the
      ABSENT-assertion list.

    iter-v3/085: CYCLE 3 EXPLORATION #4 — APPEND funding_regime_momentum_5d (the
      15th feature, the /085 axis). A Category-2 composed feature
      regime_momentum_signed_5d × sign(funding_z_30). INERT-by-importance +
      SUSPICIOUS (trade-selection sub-channel) — DROPPED at the /086 setup.

    iter-v3/081: CYCLE 2 CONFIRMATION — re-validate the /059 canonical config.
      Cycle 2 (/071-/080) produced 0 clean PROMISING; /081 is a multi-seed
      RE-VALIDATION (analogous to cycle 1's /070 NO-MERGE), NOT an edge bundle.
      Code change: REVERT the iter-v3/061 illegitimate accretion —
      vol_scale_floor_per_symbol {"TRXUSDT": 0.5} -> {} (empty). /061 was an
      INERT EXPLORATION, never MERGED (no v0.v3-061 tag, not a /070-bundle
      component); the /059 canonical config has no per-symbol vol-floor. /081
      runs the genuine /059 config (10-seed CONFIRMATION mode, n_trials=35).
      ITERATION_LABEL = "v3-081". Evidence: analysis/iteration_v3-081/.

    iter-v3/061: CYCLE 1 #2 EXPLORATION — TRX-specific RiskV2 vol_scale_floor=0.5 (Path B).
      Axis: per-symbol vol_scale_floor per Critic /060 Rec #3 + QR EDA SHA d198b25.
      Code changes: RiskV2Config.vol_scale_floor_per_symbol={"TRXUSDT": 0.5}; BCH/LDO unchanged.
      Feature bundle IDENTICAL to /060 (no feature changes).
      ITERATION_LABEL = "v3-061".
      Counterfactual: +0.47 OOS wpnl TRX lift; IS bit-identical (+0.008 wpnl).
      Classification: INERT-AT-EXPLORATION. REVERTED at iter-v3/081 (illegitimate
      accretion — INERT EXPLORATION never carried by a CONFIRMATION-MERGE).

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
    features_for_symbol(<any V3_MODELS sym>) MUST return 14 features = V3_FEATURE_COLUMNS_TOP_N.
    basis_zscore_30 / basis_momentum_3 / basis_extreme_flag MUST be ABSENT
      (iter-v3/087 — the 3 /086 perp-spot basis features DROPPED, Critic /086 Rec #3;
      /086 INERT-by-importance, the 7-FEED STRUCTURAL VERDICT).
    funding_regime_momentum_5d MUST be ABSENT (DROPPED at /086 — /085 INERT + SUSPICIOUS).
    atr_multipliers_for_symbol(<any V3_MODELS sym>) MUST return (2.0, 1.0) (DEFAULT fallback).
    iter-v3/088 RE-ARCHITECTURE: the legacy per-symbol V3_MODELS universe
      reverts to the 3-symbol BCH/LDO/TRX /059 set (/087's 6-sym expansion was
      NEGATIVE). The /088 axis is the NEW cross-sectional ranking path.
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

    # iter-v3/077: V3_FEATURE_COLUMNS = 14 (the BASELINE_V3 /059/060 anchor stack).
    # iter-v3/077 (cycle-2 EXPLORATION #7) is a PASSIVE-DIAGNOSTIC iteration
    # (conditional-orthogonality report instrumentation; brief Section 3) — it
    # adds NO feature and REVERTS /076's range_efficiency_50, returning to the
    # 14-feature anchor carried /065-/075. /076's range_efficiency_50 was
    # SUSPICIOUS-OOS-DOMINANT (NON-ADVANCING); the Kaufman path-efficiency axis
    # is CLOSED across 2 data points (/043 + /076 — BASELINE_V3.md Dead Ideas).
    # iter-v3/087 (cycle-3 EXPLORATION #6): V3_FEATURE_COLUMNS = 14 — the
    # BASELINE_V3 /059/060 anchor stack. The /086 perp-spot BASIS family
    # (basis_zscore_30, basis_momentum_3, basis_extreme_flag) is REVERTED:
    # /086 was INERT (the 3 basis features ranked 15/16/17 of 17; the 7th INERT
    # crypto-native feed — the 7-FEED STRUCTURAL VERDICT). Per Critic /086
    # Rec #3 + `feedback_v3_inert_features_at_higher_budget.md` an INERT feature
    # family is dropped and not retested at higher budget. The SOLE /087 axis is
    # the WHOLESALE V3_MODELS 3 -> 6 universe-breadth expansion, NOT a feature
    # change — the basis-revert is a mandatory baseline-restore (the established
    # "revert the non-merged prior iteration" pattern). count 17 -> 14.
    # iter-v3/102 CLOSEOUT: alpha032 REVERTED — NEGATIVE (IS collapsed +0.3993,
    # F2 falsifier fired IS < +0.60; OOS +1.55 overfitting/regime-luck per Critic).
    # alpha032 joins the ABSENT-assertion ban (the established /082 funding-family /
    # /086 basis-family / /064 adx_14 pattern). formulaic_v3.py + test_formulaic_v3.py
    # RETAINED as infrastructure; the group key is removed from GROUP_REGISTRY dispatch.
    if "alpha032" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "alpha032 FOUND in V3_FEATURE_COLUMNS — must be ABSENT at iter-v3/102 "
            "closeout (NEGATIVE: IS collapsed to +0.3993, F2 falsifier IS < +0.60 "
            "fired; OOS +1.55 confirmed overfitting/regime-luck by Critic). "
            "Remove 'alpha032' from V3_FEATURE_COLUMNS_TOP_N in "
            "features_v3/__init__.py. The formulaic_v3.py module is RETAINED as "
            "reusable infrastructure but NOT wired into GROUP_REGISTRY."
        )
    n = len(V3_FEATURE_COLUMNS)
    # iter-v3/127: REVERT V3_FEATURE_COLUMNS_TOP_N 15 → 14 (drop d24_ret_autocorr_lag1_50).
    # /126 NEGATIVE-catastrophic (EDA methodology FALSIFIED at 3-occurrence pattern per diary;
    # Critic FINAL `<see /126 diary>`). d24_ret_autocorr_lag1_50 joins the ABSENT-assertion ban.
    if n != 14:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 14. "
            "iter-v3/127: REVERT /126's d24_ret_autocorr_lag1_50 (15th feature); "
            "V3_FEATURE_COLUMNS_TOP_N reverts to /121-canonical 14-feature stack. "
            "Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
        )
    # iter-v3/127: d24_ret_autocorr_lag1_50 MUST be ABSENT (DROPPED — /126 NEGATIVE-catastrophic).
    if "d24_ret_autocorr_lag1_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "d24_ret_autocorr_lag1_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
            "iter-v3/127 (/126 NEGATIVE-catastrophic; EDA methodology FALSIFIED at 3-occurrence "
            "pattern). d24_ret_autocorr_lag1_50 joins the ABSENT-assertion ban. "
            "Remove 'd24_ret_autocorr_lag1_50' from V3_FEATURE_COLUMNS_TOP_N in "
            "features_v3/__init__.py. The multifreq_v3_24h function is RETAINED as dead code."
        )
    # iter-v3/124: eth_vs_sym_rv_50 MUST be ABSENT (REMOVED — /123 NEGATIVE-catastrophic)
    if "eth_vs_sym_rv_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "eth_vs_sym_rv_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT at iter-v3/124. "
            "/123 NEGATIVE-catastrophic closeout; cycle-7 cross-asset OHLCV axis CLOSED. "
            "Remove 'eth_vs_sym_rv_50' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py. "
            "The eth_vs_sym_rv_50 function in cross_btc_v3.py is MUSEUM code (not deleted)."
        )
    # iter-v3/123: eth_ret_3d MUST be ABSENT (NEGATIVE-INERT at /122; Critic `9e0eeb6`)
    if "eth_ret_3d" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "eth_ret_3d FOUND in V3_FEATURE_COLUMNS — must be ABSENT at iter-v3/123. "
            "/122 NEGATIVE-INERT verdict (Critic FINAL `9e0eeb6`): IC=0.5613 with "
            "vwap_dev_20 — substantially spanned by incumbents. eth_vs_sym_rv_50 "
            "replaces it per /122 Critic Rec 1. "
            "Remove 'eth_ret_3d' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # iter-v3/087: the 3 /086 basis-family features MUST be ABSENT (DROPPED —
    # Critic /086 Rec #3: /086 INERT-by-importance, rank 15/16/17 of 17, the 7th
    # INERT crypto-native feed). Per `feedback_v3_inert_features_at_higher_
    # budget.md` an INERT feature family is not carried forward and not retested
    # at a higher Optuna budget — the established `funding_regime_momentum_5d` /
    # `range_efficiency_50` ABSENT-ban pattern. (The fetch-spot subcommand,
    # basis_v3.py, and data/spot/ cache are RETAINED as reusable infrastructure;
    # only the 3 feature columns are dropped.)
    for _bf in ("basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"):
        if _bf in V3_FEATURE_COLUMNS:
            raise RuntimeError(
                f"{_bf} FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
                "iter-v3/087 (DROPPED — /086 INERT-by-importance, rank "
                "15/16/17 of 17; Critic /086 Rec #3; the 7-FEED STRUCTURAL "
                "VERDICT). An INERT feature family is not carried forward and "
                "not retested at higher budget. Remove it from "
                "V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
            )
    # iter-v3/086: funding_regime_momentum_5d MUST be ABSENT (DROPPED — Critic
    # /085 Rec #1: /085 INERT-by-importance rank 13/14/15-of-15 + SUSPICIOUS
    # trade-selection sub-channel). Per `feedback_v3_inert_features_at_higher_
    # budget.md` an INERT feature is not carried forward and not retested at a
    # higher Optuna budget — the established `vol_normalized_ret_5d` /
    # `range_efficiency_50` ABSENT-ban pattern.
    if "funding_regime_momentum_5d" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "funding_regime_momentum_5d FOUND in V3_FEATURE_COLUMNS — must be "
            "ABSENT at iter-v3/086 (DROPPED — /085 INERT-by-importance + "
            "SUSPICIOUS trade-selection sub-channel; Critic /085 Rec #1). An "
            "INERT feature is not carried forward and not retested at higher "
            "budget. Remove 'funding_regime_momentum_5d' from "
            "V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    # iter-v3/086: the 4 /082 funding-FAMILY columns MUST be ABSENT (stay reverted).
    for _fam in (
        "funding_sign_persist_9",
        "funding_momentum_3",
        "funding_accel_3",
        "funding_price_divergence_6",
    ):
        if _fam in V3_FEATURE_COLUMNS:
            raise RuntimeError(
                f"{_fam} FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
                "iter-v3/083 (the /082 funding family is reverted; funding axis "
                "CLOSED at 4 data points per `feedback_v3_inert_features_at_"
                "higher_budget.md`). Remove it from V3_FEATURE_COLUMNS_TOP_N."
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
    # The Kaufman path-efficiency axis is now CLOSED across 2 data points: /043
    # (efficiency_ratio_50 DISASTROUS) + /076 (the bit-identical-math
    # range_efficiency_50 re-evaluation SUSPICIOUS-OOS-DOMINANT — BASELINE_V3.md
    # Dead Ideas; the feedback_v3_walkforward_lookahead_bug.md re-eval eligibility
    # is DISCHARGED). Both the literal name 'efficiency_ratio_50' AND the
    # bit-identical 'range_efficiency_50' must stay absent (the latter is
    # asserted separately above). This assertion bans the literal name
    # 'efficiency_ratio_50'.
    if "efficiency_ratio_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "(DROPPED at iter-v3/044: iter-v3/043 DISASTROUS NEGATIVE IS -0.8445 / "
            "OOS -0.8990; all 4 symbols broken by unsigned Kaufman ER as a "
            "standalone directional signal). The Kaufman path-efficiency axis is "
            "CLOSED across /043 + /076 — do not re-propose it. "
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
    # iter-v3/077: range_efficiency_50 MUST be ABSENT — REVERTED at /077.
    # /076 added it (15th feature) and was SUSPICIOUS-OOS-DOMINANT (NON-ADVANCING);
    # the Kaufman path-efficiency axis is CLOSED across /043 + /076
    # (BASELINE_V3.md Dead Ideas). /077 is a PASSIVE-DIAGNOSTIC iteration on the
    # 14-feature anchor (brief Section 3.2).
    if "range_efficiency_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "range_efficiency_50 FOUND in V3_FEATURE_COLUMNS — must be ABSENT "
            "at iter-v3/077 (REVERTED — /076 SUSPICIOUS-OOS-DOMINANT; the Kaufman "
            "path-efficiency axis is CLOSED across /043 + /076). /077 is a "
            "PASSIVE-DIAGNOSTIC iteration on the 14-feature BASELINE_V3 anchor. "
            "Remove 'range_efficiency_50' from V3_FEATURE_COLUMNS_TOP_N."
        )
    # regime_momentum_signed_3d MUST NOT be present (PARKED per /053 PATH C-suspicious).
    if "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS — must be ABSENT. "
            "PARKED per /052 PATH C-suspicious closeout; Critic `34cc46f` rec #2. "
            "Remove 'regime_momentum_signed_3d' from V3_FEATURE_COLUMNS_TOP_N."
        )
    # iter-v3/065+: ALL 9 /063 NEW features (including adx_14) MUST be ABSENT.
    # /064 adx_14 phased-mass-expansion #1 NEGATIVE per Critic `452fcf2` (IS Δ -0.68).
    # Cycle 1 #6+ pivots to NON-FEATURE axes per Critic /064 Rec #4.
    _reverted_063_features = (
        "adx_14",
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
                "ABSENT at iter-v3/065+ (post-/064 NEGATIVE; REVERT to /060 14-feature anchor). "
                f"Remove '{_feat}' from V3_FEATURE_COLUMNS_TOP_N. "
                "Per `feedback_v3_iter064_process_lessons.md` Rule 5 "
                "(/060 14-feature anchor is local optimum at single-seed n_trials=35)."
            )
    # iter-v3/119: ema_signed_volregime MUST be ABSENT (REMOVED from TOP_N at /119
    # closeout housekeeping — /118 NEGATIVE catastrophic, IS Δ -0.4543;
    # `value × sign(vol-regime-classifier)` Category-2 lineage CLOSED;
    # Critic /118 Rec 3. Function STAYS in engineered_v3.py for code-museum value;
    # MUST NOT appear in V3_FEATURE_COLUMNS_TOP_N).
    if "ema_signed_volregime" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "ema_signed_volregime FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
            "iter-v3/119 (/118 NEGATIVE catastrophic: IS Δ -0.4543; broader "
            "`value × sign(vol-regime-classifier)` Category-2 lineage CLOSED "
            "at single-seed budget; Critic /118 Rec 3). "
            "Remove 'ema_signed_volregime' from V3_FEATURE_COLUMNS_TOP_N in "
            "features_v3/__init__.py. The compute_ema_signed_volregime function "
            "is RETAINED in engineered_v3.py for code-museum value."
        )
    # iter-v3/121-METHODOLOGY: ret5d_signed_tbi MUST be ABSENT (Component B REVERTED).
    # /120 CONFIRMATION-NO-MERGE on F3-DROP (sister-redistribution) + F4 IS regime-cost.
    # Per /120 F3-DROP binding pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`:
    # Component B dropped; V3_FEATURE_COLUMNS_TOP_N reverts to /059 canonical 14-feature stack.
    # compute_ret5d_signed_tbi RETAINED in engineered_v3.py (code-museum value per /118//119
    # precedent).
    if "ret5d_signed_tbi" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "ret5d_signed_tbi FOUND in V3_FEATURE_COLUMNS — must be ABSENT at "
            "iter-v3/121-METHODOLOGY (Component B REVERTED per /120 F3-DROP binding "
            "pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`). "
            "Remove 'ret5d_signed_tbi' from V3_FEATURE_COLUMNS_TOP_N in "
            "features_v3/__init__.py. compute_ret5d_signed_tbi function is "
            "RETAINED in engineered_v3.py for code-museum value."
        )
    print(
        f"  V3_FEATURE_COLUMNS: {n} columns "
        "(iter-v3/127: 14-feature /121-canonical anchor — d24_ret_autocorr_lag1_50 ABSENT "
        "(/126 NEGATIVE-catastrophic; REVERTED to /121 14-feature stack); "
        "eth_vs_sym_rv_50 ABSENT (/123 NEGATIVE-catastrophic; cross-asset OHLCV axis CLOSED); "
        "eth_ret_3d ABSENT (/122 NEGATIVE-INERT); "
        "ret5d_signed_tbi ABSENT (/121-METHODOLOGY REVERTED); "
        "ema_signed_volregime ABSENT (/118 NEGATIVE catastrophic); "
        "regime_momentum_signed_5d PRESENT; sym_vs_btc_ret_7d PRESENT)  PASS"
    )

    # iter-v3/125: REVERT DEFAULT_ATR_MULTIPLIERS (3.4641, 1.7321) → (2.0, 1.0).
    # /124 NEGATIVE-catastrophic (K=63 Branch B longer-cadence labels axis CLOSED).
    # /125 WILD CYCLE-7 axis-4 uses /121-canonical (2.0, 1.0) ATR multipliers.
    # The /121 baseline +2/-1 ATR triple-barrier K=21 is fully restored.
    _expected_atr = (2.0, 1.0)
    if DEFAULT_ATR_MULTIPLIERS != _expected_atr:
        raise RuntimeError(
            f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected {_expected_atr}. "
            "iter-v3/125: REVERT /124 Branch B ATR scaling (was 3.4641, 1.7321). "
            "Set DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
        )
    print(
        f"  DEFAULT_ATR_MULTIPLIERS = {_expected_atr} "
        "(iter-v3/127: UNCHANGED; /121-canonical DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0))  PASS"
    )

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
    print(
        "  V3_FEATURES_PER_SYMBOL: 0 entries "
        "(empty — all symbols use 14-feature /121-canonical fallback)  PASS"
    )

    # iter-v3/074: V3_ATR_MULTIPLIERS_PER_SYMBOL REVERTED to {} (empty). The
    # iter-v3/073 per-symbol triple-barrier asymmetry axis (BCH (2.0,1.25), LDO
    # (1.5,1.25)) was SUSPICIOUS-OOS-DOMINANT (OOS/IS ratio 6.85; holding-time-
    # extension axis) — closed at catalog level, did NOT advance. Per anti-drift
    # discipline (`feedback_no_cheating.md`) /074 reverts it so all symbols use
    # DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0). /074's axis is the regime-conditional
    # kill switch (primitive 9), orthogonal to labeling.
    _expected_atr_per_symbol: dict[str, tuple[float, float]] = {}
    _actual_atr_per_symbol = {k: tuple(v) for k, v in V3_ATR_MULTIPLIERS_PER_SYMBOL.items()}
    if _actual_atr_per_symbol != _expected_atr_per_symbol:
        raise RuntimeError(
            f"V3_ATR_MULTIPLIERS_PER_SYMBOL = {_actual_atr_per_symbol} — expected "
            "{} (EMPTY — iter-v3/074 REVERT of the /073 per-symbol triple-barrier "
            "asymmetry axis; all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)). "
            "Set V3_ATR_MULTIPLIERS_PER_SYMBOL = {} in features_v3/__init__.py."
        )
    print(
        "  V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries (iter-v3/074 REVERT of /073 "
        "per-symbol asymmetry; all symbols DEFAULT (2.0, 1.0))  PASS"
    )

    # iter-v3/097: universe RE-SELECTION — LDO/GALA/ADA (BCH/TRX DROPPED).
    # 14-feature universal set (V3_FEATURES_PER_SYMBOL empty — all 3 symbols fall
    # back to V3_FEATURE_COLUMNS_TOP_N = the BASELINE_V3 /059/060 14-feature anchor).
    # REQUIRED_GAP 66 = (21+1)*3 — count stays 3-symbol. /082's funding FAMILY stays
    # REVERTED; /085's funding_regime_momentum_5d stays DROPPED; the 3 /086 basis
    # features stay DROPPED.
    #
    # Section 3.2 disjointness gate — HARD assert: traded symbols must NOT overlap
    # V3_EXCLUDED_SYMBOLS (v1/v2 symbols + MKR). BCH/LDO/TRX are all disjoint.
    _v3_traded = {sym for _label, sym in V3_MODELS}
    _excluded_overlap = _v3_traded & set(V3_EXCLUDED_SYMBOLS)
    if _excluded_overlap:
        raise RuntimeError(
            f"DISJOINTNESS VIOLATION (iter-v3/101): "
            f"{_excluded_overlap} are in BOTH V3_MODELS and V3_EXCLUDED_SYMBOLS. "
            "The v3 universe must be disjoint from v1/v2 symbols and MKR. "
            "Remove offending symbols from V3_MODELS or V3_EXCLUDED_SYMBOLS."
        )
    print(
        "  V3_MODELS ∩ V3_EXCLUDED_SYMBOLS = ∅ (disjointness PASS; iter-v3/101 Section 3.2): "
        "{BCH, LDO, TRX} ∩ {v1/v2/MKR excluded} = ∅  PASS"
    )
    for _label, sym in V3_MODELS:
        sym_feats = features_for_symbol(sym)
        # iter-v3/127: V3_FEATURE_COLUMNS_TOP_N REVERTED 15 → 14 (drop d24_ret_autocorr_lag1_50).
        # /126 NEGATIVE-catastrophic; per-symbol fallback must match 14-feature /121 anchor.
        if len(sym_feats) != len(V3_FEATURE_COLUMNS):
            raise RuntimeError(
                f"{sym} fallback has {len(sym_feats)} features — "
                f"expected exactly {len(V3_FEATURE_COLUMNS)} (V3_FEATURE_COLUMNS at "
                "iter-v3/127: 14-feature /121-canonical anchor; d24_ret_autocorr_lag1_50 "
                "REVERTED (/126 NEGATIVE-catastrophic); V3_MODELS BCH/LDO/TRX unchanged. "
                "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py. "
                "V3_FEATURES_PER_SYMBOL must be empty."
            )
        for _bf in ("basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"):
            if _bf in sym_feats:
                raise RuntimeError(
                    f"{sym} feature set contains {_bf} — must be ABSENT at "
                    "iter-v3/087 (the 3 /086 perp-spot basis features are "
                    "DROPPED — Critic /086 Rec #3; /086 INERT-by-importance, "
                    "the 7-FEED STRUCTURAL VERDICT). Remove it from "
                    "V3_FEATURE_COLUMNS_TOP_N."
                )
        if "funding_regime_momentum_5d" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains funding_regime_momentum_5d — must "
                "be ABSENT at iter-v3/087 (DROPPED at /086 — /085 INERT + "
                "SUSPICIOUS). Remove it from V3_FEATURE_COLUMNS_TOP_N."
            )
        for _fam in (
            "funding_sign_persist_9",
            "funding_momentum_3",
            "funding_accel_3",
            "funding_price_divergence_6",
        ):
            if _fam in sym_feats:
                raise RuntimeError(
                    f"{sym} feature set contains {_fam} — must be ABSENT "
                    "at iter-v3/086 (the /082 funding family stays REVERTED; funding "
                    "axis CLOSED at 5 data points). Remove it from V3_FEATURE_COLUMNS_TOP_N."
                )
        if "adx_14" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains adx_14 — must be ABSENT at iter-v3/077. "
                "iter-v3/064 phased mass-expansion #1 NEGATIVE per Critic `452fcf2`."
            )
        if "ret_skew_50" not in sym_feats:
            raise RuntimeError(
                f"{sym} feature set does not contain ret_skew_50 — must be PRESENT. "
                "BASELINE_V3 feature. Add 'ret_skew_50' to V3_FEATURE_COLUMNS_TOP_N."
            )
        if "range_efficiency_50" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains range_efficiency_50 — must be ABSENT "
                "at iter-v3/077 (/076 SUSPICIOUS-OOS-DOMINANT; the Kaufman "
                "path-efficiency axis is CLOSED across /043 + /076). Remove "
                "'range_efficiency_50' from V3_FEATURE_COLUMNS_TOP_N."
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
                "iter-v3/044: DISASTROUS NEGATIVE. The Kaufman path-efficiency axis "
                "is CLOSED. "
                f"Check features_for_symbol('{sym}') path."
            )
        if "alpha032" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains alpha032 — must be ABSENT at "
                "iter-v3/102 closeout (NEGATIVE: IS collapsed +0.3993, F2 falsifier "
                "fired; OOS +1.55 overfitting/regime-luck per Critic). "
                "Remove 'alpha032' from V3_FEATURE_COLUMNS_TOP_N in "
                "features_v3/__init__.py."
            )
        # iter-v3/119: ema_signed_volregime MUST be ABSENT per-symbol
        # (REMOVED from TOP_N at /119; /118 NEGATIVE catastrophic; Critic /118 Rec 3).
        if "ema_signed_volregime" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains ema_signed_volregime — must be ABSENT "
                "at iter-v3/119 (/118 NEGATIVE catastrophic: IS Δ -0.4543; "
                "`value × sign(vol-regime-classifier)` Category-2 lineage CLOSED; "
                "Critic /118 Rec 3). Remove 'ema_signed_volregime' from "
                "V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
            )
        # iter-v3/121-METHODOLOGY: ret5d_signed_tbi MUST be ABSENT per-symbol
        # (Component B REVERTED per /120 F3-DROP + Critic FINAL `a49dd17`).
        if "ret5d_signed_tbi" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains ret5d_signed_tbi — must be ABSENT at "
                "iter-v3/121-METHODOLOGY (Component B REVERTED per /120 F3-DROP "
                "binding pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`). "
                "Remove 'ret5d_signed_tbi' from V3_FEATURE_COLUMNS_TOP_N in "
                "features_v3/__init__.py. compute_ret5d_signed_tbi is RETAINED "
                "in engineered_v3.py for code-museum value."
            )
        # iter-v3/123: eth_ret_3d MUST be ABSENT per-symbol (/122 NEGATIVE-INERT;
        # Critic FINAL `9e0eeb6`; IC=0.5613 with vwap_dev_20 — spanned by incumbents).
        if "eth_ret_3d" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains eth_ret_3d — must be ABSENT at "
                "iter-v3/123 (/122 NEGATIVE-INERT verdict: Critic FINAL `9e0eeb6`; "
                "IC=0.5613 with vwap_dev_20, substantially spanned by 2 incumbents). "
                "eth_vs_sym_rv_50 replaces it. Remove 'eth_ret_3d' from "
                "V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
            )
        # iter-v3/124: eth_vs_sym_rv_50 MUST be ABSENT per-symbol (/123 NEGATIVE-catastrophic).
        # cycle-7 cross-asset OHLCV axis CLOSED at 6th consecutive failure.
        # Museum code remains in cross_btc_v3.py but NOT wired into V3_FEATURE_COLUMNS.
        if "eth_vs_sym_rv_50" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains eth_vs_sym_rv_50 — must be ABSENT at "
                "iter-v3/124 (/123 NEGATIVE-catastrophic; cycle-7 cross-asset OHLCV "
                "axis CLOSED at 6th consecutive failure). "
                "Remove 'eth_vs_sym_rv_50' from V3_FEATURE_COLUMNS_TOP_N in "
                "features_v3/__init__.py."
            )
        # iter-v3/127: d24_ret_autocorr_lag1_50 MUST be ABSENT per-symbol
        # (REVERTED — /126 NEGATIVE-catastrophic; EDA methodology FALSIFIED).
        if "d24_ret_autocorr_lag1_50" in sym_feats:
            raise RuntimeError(
                f"{sym} feature set contains d24_ret_autocorr_lag1_50 — must be ABSENT at "
                "iter-v3/127 (/126 NEGATIVE-catastrophic; EDA methodology FALSIFIED; "
                "d24_ret_autocorr_lag1_50 joins the ABSENT-assertion ban). "
                "Remove 'd24_ret_autocorr_lag1_50' from V3_FEATURE_COLUMNS_TOP_N in "
                "features_v3/__init__.py."
            )
        for _d_feat in (
            "d_ret_5d",
            "d_ret_10d",
            "d_trend_slope_10",
            "d_realvol_10",
            "d_realvol_ratio",
            "d_atr_pctrank_60",
            "d_efficiency_10",
            "d_close_pos_20",
        ):
            if _d_feat in sym_feats:
                raise RuntimeError(
                    f"{sym} feature set contains {_d_feat} — must be ABSENT at "
                    "iter-v3/114 closeout of /113 (the 8 multi-frequency daily "
                    "features are REVERTED — Critic /113 Recommendation 2; /113 "
                    "NEGATIVE-INERT). Remove it from V3_FEATURE_COLUMNS_TOP_N in "
                    "features_v3/__init__.py."
                )
    print(
        "  3-symbol universe (BCH/LDO/TRX): 14-feature /121-canonical universal "
        "fallback (iter-v3/127: d24_ret_autocorr_lag1_50 ABSENT (/126 NEGATIVE-catastrophic; "
        "REVERTED to /121 14-feature stack); V3_MODELS BCH/LDO/TRX UNCHANGED; "
        "eth_vs_sym_rv_50 ABSENT (/123 NEGATIVE-catastrophic; cross-asset OHLCV axis CLOSED); "
        "eth_ret_3d ABSENT (/122 NEGATIVE-INERT); ret5d_signed_tbi ABSENT (/121 REVERTED); "
        "ema_signed_volregime ABSENT; /113 daily features ABSENT; /086 basis family ABSENT; "
        "/085 funding_regime_momentum_5d ABSENT)  PASS"
    )

    # iter-v3/074: V3_ATR_MULTIPLIERS_PER_SYMBOL reverted to {} (the /073 per-symbol
    # axis was SUSPICIOUS-OOS-DOMINANT). ALL symbols fall back to
    # DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — the canonical /059 baseline labeling.
    # iter-v3/125: REVERT /124 Branch B (3.4641, 1.7321) → /121-canonical (2.0, 1.0).
    # Universe replaced BCH/LDO/TRX → ATOM/RUNE/UNI; all 3 candidates use DEFAULT (2.0, 1.0).
    _expected_atr_loop = (2.0, 1.0)
    for _label_atr, _sym_atr in V3_MODELS:
        sym_atr = tuple(atr_multipliers_for_symbol(_sym_atr))
        if sym_atr != _expected_atr_loop:
            raise RuntimeError(
                f"atr_multipliers_for_symbol('{_sym_atr}') returned {sym_atr} — "
                f"expected {_expected_atr_loop} (iter-v3/125: REVERT /124 Branch B; "
                "/121-canonical (2.0, 1.0)). "
                "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
            )
    print(
        f"  atr_multipliers_for_symbol: all {len(V3_MODELS)} symbols "
        "(ATOM/RUNE/AVAX/HBAR/ICP/ALGO) "
        "(2.0, 1.0) DEFAULT "
        "(iter-v3/128: new 6-symbol L1 universe; all use DEFAULT /121-canonical)  PASS"
    )

    # iter-v3/051: Primitive 10 REVERT — block_long_for=() per system-level rule.
    # `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 mandates
    # clearing per-symbol customizations. block_long_for was ("BCHUSDT",) at iter-v3/047-050.
    # iter-v3/129: check uses BCHUSDT (first symbol in reverted BCH/LDO/TRX universe).
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

    # iter-v3/075: Primitive 9 (regime-conditional kill switch) REVERTED to
    # DISABLED. /074 enabled it as the cycle-2 EXPLORATION #4 axis (INERT — the
    # gate suppressed only 3 IS + 5 OOS TRX trades; closed across two data points).
    # /075's axis is primitive 12, NOT primitive 9 — the regime gate must be OFF
    # to restore the /060 baseline risk-gate stack per `feedback_no_cheating.md`
    # anti-drift discipline.
    if strat_check.config.enable_regime_gate:
        raise RuntimeError(
            "RiskV2Config.enable_regime_gate = True — expected False. iter-v3/075: "
            "the /074 regime-conditional kill switch (primitive 9) axis is closed "
            "and must be REVERTED to OFF (the /060 baseline state). /075's axis is "
            "primitive 12. Set enable_regime_gate=False, regime_gate_symbols=() in "
            "RiskV2Config init in _build_v3_model."
        )
    # iter-v3/115: the iter-v3/114 primitive-9 axis (LDO-scoped kill_LOW
    # ldo_realvol_zscore gate) is CLOSED. iter-v3/115 reverts to the
    # /059-canonical risk stack — primitive 9 DISABLED, no LDO regime-gate
    # target. The /075-era "regime_gate_symbols must be ()" semantics are
    # restored. This guard now asserts the reverted /059-canonical state, so
    # an accidental carry-over of the /114 kill-switch state (the
    # iter-v3/110 trend_scanning stale-knob confound) crashes pre-flight.
    if strat_check.config.regime_gate_symbols != ():
        raise RuntimeError(
            f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
            "— expected (). iter-v3/115: the iter-v3/114 LDO primitive-9 axis is "
            "CLOSED; the /059-canonical risk stack has no regime-gate target. Set "
            "regime_gate_symbols=() in RiskV2Config init in _build_v3_model."
        )
    if strat_check.config.enable_ldo_realvol_gate:
        raise RuntimeError(
            "RiskV2Config.enable_ldo_realvol_gate = True — expected False. "
            "iter-v3/115: the iter-v3/114 LDO-realvol kill_LOW gate (primitive 9 "
            "variant) axis is CLOSED; iter-v3/115 reverts to the /059-canonical "
            "risk stack with primitive 9 DISABLED. Set "
            "enable_ldo_realvol_gate=False in RiskV2Config init in "
            "_build_v3_model."
        )

    # iter-v3/077: Primitive 12 (BTC-trend-regime position-SIZE de-rate scalar)
    # stays DISABLED (reverted OFF at /076; remains OFF at /077). /075 enabled it
    # as the cycle-2 EXPLORATION #5 axis (INERT-AT-EXPLORATION — a post-gate macro
    # BTC-trend classifier whose sign IS the IS/OOS regime axis is OOS-costly by
    # construction; it did NOT advance to CONFIRMATION). /077's axis is a
    # PASSIVE-DIAGNOSTIC report instrumentation; Primitive 12 must be OFF to keep
    # the /060 baseline risk-gate stack per `feedback_no_cheating.md` anti-drift
    # discipline. The RiskV2Config fields stay DEFINED (Primitive 12's mechanics
    # remain test-covered by test_regime_size_scalar.py) — only enablement is OFF.
    if strat_check.config.enable_regime_size_scalar:
        raise RuntimeError(
            "RiskV2Config.enable_regime_size_scalar = True — expected False. "
            "iter-v3/077: the /075 BTC-trend-regime position-SIZE de-rate scalar "
            "(primitive 12) axis is closed and stays OFF (the /060 baseline "
            "state). /077's axis is a PASSIVE-DIAGNOSTIC report instrumentation. "
            "Set enable_regime_size_scalar=False in RiskV2Config init in "
            "_build_v3_model."
        )
    if strat_check.config.regime_size_scalar_symbols != ():
        raise RuntimeError(
            f"RiskV2Config.regime_size_scalar_symbols = "
            f"{strat_check.config.regime_size_scalar_symbols} — expected () "
            "(empty). iter-v3/076: the /075 Primitive-12 de-rate is reverted; "
            "regime_size_scalar_symbols must be empty."
        )
    print(
        "  Primitive 12 (BTC-trend-regime position-SIZE de-rate scalar): "
        "enable_regime_size_scalar=False (iter-v3/076 REVERT of the /075 "
        "EXPLORATION #5 axis; /060 baseline risk-gate stack restored)  PASS"
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
    # iter-v3/129: check uses BCHUSDT (first symbol in reverted BCH/LDO/TRX universe).
    _trx_cfg_check, trx_strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(trx_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model(BCHUSDT) returned {type(trx_strat_check).__name__} — "
            "expected RiskV3Wrapper. iter-v3/051: per-symbol ADX EMPTY check requires "
            "RiskV3Wrapper. Check _build_v3_model returns RiskV3Wrapper."
        )
    if trx_strat_check.config.adx_threshold_per_symbol != {}:
        raise RuntimeError(
            f"RiskV2Config.adx_threshold_per_symbol = "
            f"{trx_strat_check.config.adx_threshold_per_symbol} — expected {{}} (EMPTY). "
            "iter-v3/051: per-symbol ADX must remain empty (global 20.0 applies to all symbols). "
            "Set adx_threshold_per_symbol={{}} in RiskV2Config init in _build_v3_model."
        )
    print(
        "  Per-symbol ADX threshold (iter-v3/051): {} (EMPTY — global ADX threshold 20.0 "
        "applies to all 6 symbols ATOM/RUNE/AVAX/HBAR/ICP/ALGO)  PASS"
    )

    # iter-v3/128: Primitive 11 (per-symbol drawdown brake) MUST be DISABLED (REVERTED).
    # /127 NEGATIVE — drawdown brake axis CLOSED per Critic FINAL. /128 REVERTS brake to False
    # (the /121-canonical state; mandatory baseline-restore per established pattern).
    # The /128 sole axis is universe substitution; brake must be off.
    # Use BCHUSDT (first symbol in reverted BCH/LDO/TRX universe) for the check.
    _p11_cfg_check, p11_strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(p11_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model returned {type(p11_strat_check).__name__} — expected RiskV3Wrapper. "
            "iter-v3/129: primitive 11 revert check uses BCHUSDT. "
            "Check _build_v3_model returns RiskV3Wrapper."
        )
    if p11_strat_check.config.enable_per_symbol_drawdown_brake:
        raise RuntimeError(
            "RiskV2Config.enable_per_symbol_drawdown_brake = True — expected False. "
            "iter-v3/128: per-symbol drawdown brake (primitive 11) MUST be DISABLED "
            "(/127 NEGATIVE — brake axis CLOSED; mandatory /128 baseline-restore). "
            "Set enable_per_symbol_drawdown_brake=False in RiskV2Config in _build_v3_model."
        )
    print(
        "  Primitive 11 (per-symbol drawdown brake): DISABLED "
        "(iter-v3/128: /127 brake REVERTED — axis CLOSED after NEGATIVE; "
        "/121-canonical False)  PASS"
    )

    # iter-v3/081: per-symbol vol_scale_floor REVERTED to {} (empty). The
    # iter-v3/061 {"TRXUSDT": 0.5} floor was illegitimate accretion — an INERT
    # EXPLORATION axis (never PROMISING, never MERGED, no v0.v3-061 tag, not a
    # /070-bundle component) that persisted in the active runner config. The /059
    # canonical baseline (setup commit 20095a8) has NO per-symbol vol-floor; the
    # /081 cycle-2 CONFIRMATION reverts it so the run measures the genuine /059
    # config. See analysis/iteration_v3-081/ (T1 accretion ledger + T2 vol-floor
    # provenance) and brief Section 2-3. With the empty {} all 3 symbols use the
    # global 0.3 floor. This assertion now guards the GENUINE /059 value — it
    # blocks the /061 accretion from silently re-creeping in.
    _p12_cfg_check, p12_strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(p12_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model(BCHUSDT) returned {type(p12_strat_check).__name__} — "
            "expected RiskV3Wrapper. iter-v3/081: vol_scale_floor_per_symbol check "
            "requires RiskV3Wrapper. Check _build_v3_model returns RiskV3Wrapper."
        )
    expected_floor_dict: dict[str, float] = {}
    if dict(p12_strat_check.config.vol_scale_floor_per_symbol) != expected_floor_dict:
        raise ValueError(
            f"RiskV2Config.vol_scale_floor_per_symbol = "
            f"{p12_strat_check.config.vol_scale_floor_per_symbol} — expected "
            f"{expected_floor_dict}. iter-v3/081: the iter-v3/061 TRX floor=0.5 was "
            "REVERTED as illegitimate accretion (never-merged INERT EXPLORATION). "
            "Set vol_scale_floor_per_symbol={} in RiskV2Config init in "
            "_build_v3_model — all 6 symbols use the global 0.3 floor."
        )
    print(
        "  Per-symbol vol_scale_floor (iter-v3/081): {} "
        "(REVERTED iter-v3/061 accretion; all 6 symbols "
        "ATOM/RUNE/AVAX/HBAR/ICP/ALGO at global 0.3 floor)  PASS"
    )

    # iter-v3/082 (cycle-3 EXPLORATION #1) — GENERALISED CONFIG-ACCRETION CHECK.
    # Per Critic /081 Recommendation #3 + briefs-v3/cycle3_plan.md Section 5: the
    # /061 vol-floor rode 19 iterations undetected because each EXPLORATION
    # varied one OTHER axis and never touched the floor line. This consolidated
    # pre-flight asserts every behavior-affecting knob equals its /059-canonical
    # value, so a future /061-style accretion is caught at runtime, not by
    # git-archaeology.
    #
    # iter-v3/088 (cycle-3 EXPLORATION #7 — RE-ARCHITECTURE): the legacy
    # per-symbol path is fully RESTORED to the /059-canonical 3-symbol state —
    # /087's WHOLESALE 6-sym expansion was NEGATIVE and is reverted (mandatory
    # baseline-restore). ALL 11 knobs below MUST equal /059-canonical: the
    # iter-v3/088 axis is NOT a per-symbol-path knob change — it is a NEW
    # cross-sectional ranking path (brief Section 3). This check guards the
    # legacy per-symbol path against accretion; the new path has its own gates.
    _acc_cfg, _acc_strat = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    if not isinstance(_acc_strat, RiskV3Wrapper):
        raise RuntimeError("config-accretion check: _build_v3_model did not return RiskV3Wrapper.")
    _rc = _acc_strat.config
    # (knob_name, observed, expected value). iter-v3/088: ALL 11 knobs are
    # /059-canonical — the per-symbol path is a clean restore.
    # iter-v3/129: 22 knobs (added 5 scaling primitives + REVERT V3_MODELS to BCH/LDO/TRX).
    _v3_model_symbols = tuple(sym for _label, sym in V3_MODELS)
    # iter-v3/111: extract inner LightGbmStrategy from _acc_strat to inspect label knobs.
    _acc_inner = _acc_strat.inner if hasattr(_acc_strat, "inner") else _acc_strat
    _canonical_v059 = [
        # iter-v3/128: V3_MODELS WHOLESALE REPLACEMENT BCH/LDO/TRX → 6-symbol sector-pure L1
        # (ATOM/RUNE/AVAX/HBAR/ICP/ALGO). 9/9 NEGATIVE; axis CLOSED.
        # iter-v3/129: REVERT V3_MODELS → BCH/LDO/TRX (/121 baseline); REQUIRED_GAP REVERT
        # 132→66; add primitive 13 (continuous size-scaling at per-symbol 45d rolling drawdown).
        (
            "V3_MODELS symbols",
            _v3_model_symbols,
            ("BCHUSDT", "LDOUSDT", "TRXUSDT"),
        ),
        # REQUIRED_GAP from validation_v3.py is always 66 (the 8h baseline constant).
        # iter-v3/117: at --bar-interval 24h, the runner uses 72 as a LOCAL OVERRIDE
        # (computed in _verify_label_leakage_gap at runtime). The validation_v3.py
        # constant is NOT changed — this guard verifies the base constant is intact.
        # 8h base constant; 24h override=72 handled separately in _verify_label_leakage_gap.
        ("REQUIRED_GAP", REQUIRED_GAP, 66),  # (21+1)*3 — 8h base constant from validation_v3.py
        # iter-v3/111: label_mode guard — prevents stale trend_scanning from riding
        # undetected again (root cause of /110's label confound).
        # iter-v3/116: REVERT /115's label_mode="fixed_horizon" → "triple_barrier".
        # /116 returns to the /059-canonical triple_barrier labeling architecture;
        # label_mode expected value updated here in lockstep with Section 3.5 Change 7(e).
        ("label_mode", _acc_inner.label_mode, "triple_barrier"),
        # trend_scan_grid: LightGbmStrategy default (5,8,13,21). Guard checks
        # it was NOT explicitly overridden. Canonical = LightGbmStrategy default.
        ("trend_scan_grid", tuple(_acc_inner.trend_scan_grid), (5, 8, 13, 21)),
        # /059-canonical knobs (must NOT drift — single-axis discipline guard):
        # iter-v3/125: REVERT /124 Branch B ATR (3.4641, 1.7321) → /121-canonical (2.0, 1.0).
        ("DEFAULT_ATR_MULTIPLIERS", tuple(DEFAULT_ATR_MULTIPLIERS), (2.0, 1.0)),
        ("V3_ATR_MULTIPLIERS_PER_SYMBOL", dict(V3_ATR_MULTIPLIERS_PER_SYMBOL), {}),
        ("zscore_threshold", _rc.zscore_threshold, 2.0),
        ("adx_threshold", _rc.adx_threshold, 20.0),
        ("adx_threshold_per_symbol", dict(_rc.adx_threshold_per_symbol), {}),
        ("vol_scale_floor_per_symbol", dict(_rc.vol_scale_floor_per_symbol), {}),
        ("block_long_for", tuple(_rc.block_long_for), ()),
        ("block_short_for", tuple(_rc.block_short_for), ()),
        # iter-v3/128: primitive 11 REVERTED False (the /127 brake axis is CLOSED — NEGATIVE).
        # The accretion guard tracks the /129-canonical state; brake REVERTED to /121-baseline.
        ("enable_per_symbol_drawdown_brake", _rc.enable_per_symbol_drawdown_brake, False),
        # iter-v3/129: primitive 13 — continuous size-scaling at per-symbol 45-day rolling
        # drawdown. New axis; T_R=6.0 wpnl (full size), T_max=7.0 wpnl (zero size),
        # N=45 days, M=21 candles time-override (deadlock-impossibility carry-forward).
        # iter-v3/130: /129 continuous scaling axis REVERTED to False (axis CLOSED at /129
        # NEGATIVE-catastrophic; REVERT mandatory per single-axis discipline).
        (
            "enable_per_symbol_drawdown_scaling",
            _rc.enable_per_symbol_drawdown_scaling,
            False,
        ),
        ("drawdown_scaling_t_r", _rc.drawdown_scaling_t_r, 6.0),
        ("drawdown_scaling_t_max", _rc.drawdown_scaling_t_max, 7.0),
        ("drawdown_scaling_window_days", _rc.drawdown_scaling_window_days, 45),
        (
            "drawdown_scaling_time_override_candles",
            _rc.drawdown_scaling_time_override_candles,
            21,
        ),
        # iter-v3/116: three BacktestConfig knobs added to the accretion guard.
        # iter-v3/117: enable_no_confirm_exit REVERTED False (was True at /116).
        # iter-v3/120: CONFIRMATION bundle RE-ENABLES enable_no_confirm_exit=True
        # (Component A of the TWO-COMPONENT /116+/119 bundle). The /116 no_confirm
        # primitive is carried forward unchanged; only the enable flag is flipped.
        ("enable_no_confirm_exit", _acc_cfg.enable_no_confirm_exit, True),
        ("no_confirm_trigger_atr", _acc_cfg.no_confirm_trigger_atr, 0.50),
        ("no_confirm_k_candles", _acc_cfg.no_confirm_k_candles, 4),
    ]
    _drift = [(name, obs, exp) for name, obs, exp in _canonical_v059 if obs != exp]
    if _drift:
        _msg = "; ".join(f"{n}: observed {o!r} != expected {e!r}" for n, o, e in _drift)
        raise ValueError(
            f"config-accretion check FAILED — {len(_drift)} knob(s) drifted: {_msg}. "
            "Runner carries /130-state config (BCH/LDO/TRX 3-symbol universe [REVERT from /128], "
            "REQUIRED_GAP=66 [REVERT from /128 132], label_mode=triple_barrier, "
            "enable_no_confirm_exit=True [/116 no_confirm Component A — still active], "
            "enable_per_symbol_drawdown_brake=False [/127 brake REVERTED — axis CLOSED], "
            "enable_per_symbol_drawdown_scaling=False [/129 continuous scaling REVERTED — "
            "axis CLOSED at /129 NEGATIVE-catastrophic]): "
            "ALL 22 knobs must equal /130-state. Any drift is illegitimate accretion. "
            "Revert the drifted knob(s)."
        )
    print(
        f"  Config-accretion check (Critic /081 Rec #3): "
        f"{len(_canonical_v059)} knobs verified — ALL /130-state "
        f"(BCH/LDO/TRX 3-symbol [REVERT /128], label_mode=triple_barrier, "
        f"DEFAULT_ATR_MULTIPLIERS=(2.0,1.0), "
        f"enable_no_confirm_exit=True [/116 no_confirm Comp-A], "
        f"enable_per_symbol_drawdown_brake=False [/127 brake REVERTED], "
        f"enable_per_symbol_drawdown_scaling=False [/129 continuous scaling REVERTED])  PASS"
    )

    # iter-v3/068: REVERT inference_threshold_floor to default 0.0 (/067 INERT-AT-EXPLORATION).
    # iter-v3/067's axis is closed per Critic FINAL `b8d3bb5` (Path D non-activation).
    # /068 reverts to default for clean single-axis attribution of Path C label-timeout widening.
    # vol_scale_ceiling stays at default 1.0 (already reverted at /067).
    # brief Section 3 Sub-fix 2 + Sub-fix 3.
    # iter-v3/129: check uses BCHUSDT (first symbol in reverted BCH/LDO/TRX universe).
    # iter-v3/130: probe model built at actual bar_interval so label_timeout_minutes matches.
    _p13_cfg_check, p13_strat_check = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42], bar_interval=bar_interval
    )
    if not isinstance(p13_strat_check, RiskV3Wrapper):
        raise RuntimeError(
            f"_build_v3_model(BCHUSDT) returned {type(p13_strat_check).__name__} — "
            "expected RiskV3Wrapper. iter-v3/112: inference_threshold_floor revert check "
            "requires RiskV3Wrapper around LightGbmStrategy."
        )
    _p13_inner = p13_strat_check.inner if hasattr(p13_strat_check, "inner") else p13_strat_check
    if hasattr(_p13_inner, "_inference_threshold_floor"):
        if _p13_inner._inference_threshold_floor != 0.0:
            raise RuntimeError(
                f"LightGbmStrategy._inference_threshold_floor = "
                f"{_p13_inner._inference_threshold_floor} — expected 0.0 at iter-v3/068. "
                "iter-v3/068 REVERTS /067's INERT inference_threshold_floor (Critic FINAL "
                "`b8d3bb5` closed the Path D axis). Remove inference_threshold_floor=0.60 "
                "from _build_v3_model common_kwargs (brief Section 3 Sub-fix 2)."
            )
    if p13_strat_check.config.vol_scale_ceiling != 1.0:
        raise RuntimeError(
            f"RiskV2Config.vol_scale_ceiling = {p13_strat_check.config.vol_scale_ceiling} — "
            "expected 1.0 (default). iter-v3/068: vol_scale_ceiling reverted at /067 and "
            "must remain at default 1.0 (brief Section 3 Sub-fix 3)."
        )
    # iter-v3/069: label_timeout_minutes REVERTED to 10080 on all v3 models.
    # iter-v3/124: label_timeout_minutes UPDATED to 30240 — K=63 longer-cadence labels axis.
    # iter-v3/125: label_timeout_minutes REVERTED to 10080 — /124 NEGATIVE-catastrophic (CLOSED).
    # iter-v3/126: label_timeout_minutes UNCHANGED at 10080 — /121-canonical K=21.
    # iter-v3/130: at 4h, expected = 5040 (K=21 × 4h × 60min).
    expected_label_timeout = 5040 if bar_interval == "4h" else 10080
    _p13_lgbm = _p13_inner
    if not hasattr(_p13_lgbm, "label_timeout_minutes"):
        raise RuntimeError(
            "LightGbmStrategy for BCHUSDT has no label_timeout_minutes attribute. "
            "iter-v3/069: LightGbmStrategy must expose label_timeout_minutes. "
            "Check lgbm.py __init__ and _build_v3_model call."
        )
    if _p13_lgbm.label_timeout_minutes != expected_label_timeout:
        raise RuntimeError(
            f"LightGbmStrategy.label_timeout_minutes = "
            f"{_p13_lgbm.label_timeout_minutes} — expected {expected_label_timeout}. "
            f"iter-v3/125: REVERT label_timeout_minutes to 10080 (K=21 at 8h; /124 NEGATIVE). "
            f"In _build_v3_model common_kwargs use label_timeout_minutes=10080."
        )
    # iter-v3/111: label_mode guard — prevents stale trend_scanning from riding
    # undetected (root cause of /110's label confound).
    # iter-v3/116: REVERT /115's label_mode="fixed_horizon" → "triple_barrier".
    # The expected value is updated here in lockstep with Section 3.5 Change 7(e).
    if not hasattr(_p13_lgbm, "label_mode"):
        raise RuntimeError(
            "LightGbmStrategy for BCHUSDT has no label_mode attribute. "
            "iter-v3/072: LightGbmStrategy must expose label_mode. "
            "Check lgbm.py __init__ and _build_v3_model call."
        )
    expected_label_mode = "triple_barrier"
    if _p13_lgbm.label_mode != expected_label_mode:
        raise RuntimeError(
            f"LightGbmStrategy.label_mode = '{_p13_lgbm.label_mode}' — "
            f"expected '{expected_label_mode}'. "
            "iter-v3/116: label_mode must be 'triple_barrier' — REVERTED from /115's "
            "'fixed_horizon'. Check _build_v3_model common_kwargs label_mode='triple_barrier'."
        )
    print(
        f"  label_mode (iter-v3/116 revert): '{_p13_lgbm.label_mode}'  PASS"
        f" (triple_barrier — /059-canonical; /115 fixed_horizon REVERTED)"
    )
    print(
        "  inference_threshold_floor REVERTED to default 0.0 "
        "(iter-v3/068 reverts /067 INERT axis; unchanged at /069)  PASS"
    )
    print("  vol_scale_ceiling at default 1.0 (reverted at /067, unchanged at /069)  PASS")
    _timeout_desc = (
        f"21 candles at {bar_interval} = {expected_label_timeout} min"
        if bar_interval == "4h"
        else f"21 candles at 8h = {expected_label_timeout} min"
    )
    print(
        f"  Universal label_timeout_minutes (iter-v3/130 bar-interval-conditional K=21): "
        f"{expected_label_timeout} min "
        f"({_timeout_desc}; /121-canonical ATR (2.0, 1.0); "
        f"embargo 22 per cell; cross-cell gap 66 per 3-sym universe BCH/LDO/TRX)  PASS"
    )

    # iter-v3/070 NEW: _verify_timeout_consistency — Critic /069 Rec #1.
    # Assert BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes.
    # The /069 iteration had these two values silently fall out of sync.
    # Verify on the BCHUSDT model already built above (p13_strat_check).
    # iter-v3/130: pass bar_interval so the check uses correct expected_timeout (5040 at 4h).
    _verify_timeout_consistency(_p13_cfg_check, _p13_lgbm, bar_interval=bar_interval)
    print(
        "  Timeout consistency (iter-v3/070 Critic /069 Rec #1): "
        f"BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes "
        f"== {expected_label_timeout}  PASS"
    )


def _verify_label_leakage_gap(bar_interval: str = "8h") -> None:
    """Assert gap == REQUIRED_GAP and print proof (brief Section 3.5 Change 4).

    iter-v3/112 UNIVERSE REVERT: 4-symbol → 3-symbol (BCH+LDO+TRX).
    iter-v3/117: bar_interval-conditional REQUIRED_GAP.
    iter-v3/125: REVERT /124 K=63 → K=21 (/124 NEGATIVE-catastrophic CLOSED).
    iter-v3/130: 4h bar interval added. K=21 candles × 4h = 84h = 5040 min.
        timeout_candles = 5040 / 240 = 21 (same candle count as 8h K=21).
        required_gap = (21+1)*3 = 66 = REQUIRED_GAP (UNCHANGED in candle-count terms).
        The absolute time gap is HALVED (11 days at 4h vs 22 days at 8h) but the
        candle-count purge is identical — the López de Prado requirement is in
        candle counts, not absolute time.

    At 8h (default), iter-v3/125 (/121-canonical restored):
        timeout_minutes=10080, candle_minutes=480, timeout_candles=21.
        required_gap = (21+1)*3 = 66 (REQUIRED_GAP from validation_v3.py — no override needed).

    At 4h (iter-v3/130 bar-interval axis):
        timeout_minutes=5040, candle_minutes=240, timeout_candles=21.
        required_gap = (21+1)*3 = 66 (SAME as 8h in candle-count terms; no override needed).

    At 24h (iter-v3/117 candle-frequency axis):
        timeout_minutes=10080, candle_minutes=1440, timeout_candles=7.
        n_offset_series=3 (the 3 UTC offsets; each offset forms its own series).
        required_gap = (7+1)*3*3 = 72 (brief Section 3.5 Change 4 formula).

    The 24h formula adds a factor of n_offset_series=3 because the concatenated
    multi-offset panel has 3 rows per calendar day per symbol; the cross-offset
    label-leakage purge must cover both within-offset (7+1 bars) and cross-offset
    (x3 offsets) boundaries.

    At 24h the runner overrides REQUIRED_GAP (imported from validation_v3.py as 66)
    with 72 via a local variable passed to the CV functions. The validation_v3.py
    constant is NOT changed — it remains the 8h baseline's value.
    """
    # iter-v3/128: timeout_minutes UNCHANGED at 10080 (K=21 at 8h — /121-canonical).
    # iter-v3/130: at 4h, timeout_minutes=5040 (K=21 × 4h × 60min).
    # validation_v3.REQUIRED_GAP = 66 = (21+1)*3 is the module constant (3-symbol baseline).
    # iter-v3/128: cardinality 6 at 8h requires RUNNER-LOCAL OVERRIDE 132 = (21+1)*6.
    # The validation_v3.py constant is NOT changed — same override pattern as 24h=72 at /117.
    if bar_interval == "4h":
        timeout_minutes = 5040  # K=21 × 4h × 60min — iter-v3/130 bar-interval axis
    else:
        timeout_minutes = 10080  # 21 candles at 8h — /121-canonical K=21 (UNCHANGED /128)
    n_symbols = len(V3_MODELS)
    if bar_interval == "4h":
        candle_minutes = 240  # 4h bar — iter-v3/130
        timeout_candles = timeout_minutes // candle_minutes  # = 5040/240 = 21
        required_gap = (timeout_candles + 1) * n_symbols  # = (21+1)*3 = 66
        assert required_gap == REQUIRED_GAP, (
            f"REQUIRED_GAP(4h, K=21, 3-sym) formula gives {required_gap} != {REQUIRED_GAP}. "
            "Check (timeout_candles+1)*n_symbols = (21+1)*3 = 66. "
            "iter-v3/130: gap is UNCHANGED in candle-count terms at 4h vs 8h."
        )
        print(
            f"  Label-leakage gap [4h, K=21]: timeout_minutes={timeout_minutes}, "
            f"candle_minutes={candle_minutes}, timeout_candles={timeout_candles}, "
            f"(timeout_candles+1)*n_symbols={timeout_candles + 1}*{n_symbols}"
            f" = {required_gap}  [iter-v3/130; UNCHANGED in candle-count; "
            f"module REQUIRED_GAP={REQUIRED_GAP}]  PASS"
        )
        return
    if bar_interval == "24h":
        candle_minutes = 1440  # 24h bar
        n_offset_series = 3  # offsets 0/8/16 — each forms an independent series
        timeout_candles = timeout_minutes // candle_minutes  # = 7 (10080/1440)
        required_gap = (timeout_candles + 1) * n_symbols * n_offset_series  # = 8*N*3
        # At 24h the runner uses the local required_gap override (not REQUIRED_GAP=66).
        expected_24h_gap = (7 + 1) * n_symbols * 3  # cardinality-dependent
        assert required_gap == expected_24h_gap, (
            f"REQUIRED_GAP(24h, K=21) formula gives {required_gap} != {expected_24h_gap}. "
            "Check (timeout_candles+1)*n_symbols*n_offset_series at K=21."
        )
        print(
            f"  Label-leakage gap [24h, K=21]: (timeout_candles={timeout_candles}+1)"
            f" * n_symbols={n_symbols} * n_offsets={n_offset_series}"
            f" = {required_gap}  [/128 cardinality-{n_symbols} formula]  PASS"
        )
    else:
        candle_minutes = 480  # 8h
        timeout_candles = timeout_minutes // candle_minutes  # = 21
        required_gap = (timeout_candles + 1) * n_symbols  # = 22*n_symbols
        if n_symbols == 3:
            # 3-symbol baseline: REQUIRED_GAP=66 from validation_v3.py; no runner-local override.
            assert required_gap == 66, (
                f"REQUIRED_GAP(8h, K=21, 3-sym) formula gives {required_gap} != 66. "
                "Check (timeout_candles+1)*n_symbols = (21+1)*3 = 66."
            )
            print(
                f"  Label-leakage gap [8h, K=21]: (timeout_candles={timeout_candles}+1)"
                f" * n_symbols={n_symbols}"
                f" = {required_gap}  [/121-canonical; module REQUIRED_GAP={REQUIRED_GAP}]  PASS"
            )
        else:
            # iter-v3/128: cardinality 6 — runner-local override 132 = (21+1)*6.
            # validation_v3.REQUIRED_GAP stays 66 (the 3-symbol module constant); the override
            # is applied at the CV-call site via _runtime_gap.
            expected_gap_6sym = (21 + 1) * 6  # = 132
            assert required_gap == expected_gap_6sym, (
                f"REQUIRED_GAP(8h, K=21, {n_symbols}-sym) formula gives {required_gap} "
                f"!= {expected_gap_6sym}. "
                f"Check (timeout_candles+1)*n_symbols = (21+1)*{n_symbols}."
            )
            print(
                f"  Label-leakage gap [8h, K=21, cardinality-{n_symbols}]: "
                f"(timeout_candles={timeout_candles}+1) * n_symbols={n_symbols}"
                f" = {required_gap}  [iter-v3/128 cardinality-conditional override; "
                f"module REQUIRED_GAP={REQUIRED_GAP} (3-sym constant, unchanged)]  PASS"
            )


def _verify_timeout_consistency(
    cfg: BacktestConfig,
    lgbm_strategy: LightGbmStrategy,
    bar_interval: str = "8h",
) -> None:
    """Assert BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes.

    iter-v3/070 NEW runtime assertion per Critic /069 Rec #1 anchor-byte gate enforcement.
    The /069 iteration had BacktestConfig.timeout_minutes (line 1407) and
    LightGbmStrategy.label_timeout_minutes (line 1425) fall out of sync silently.
    This function enforces the single-source-of-truth invariant at runner startup,
    catching any future desync between the two fields before any backtest data is produced.

    Called from _verify_model_config() for each (model, symbol) pair after _build_v3_model().

    iter-v3/130: bar_interval-conditional expected value.
    At 4h: expected = 5040 (K=21 × 4h × 60min — brief Section 3.3).
    At 8h/24h: expected = 10080 (/121-canonical K=21).
    """
    # iter-v3/125: REVERT expected_timeout_minutes 30240 → 10080 (K=21; /124 NEGATIVE).
    # /124 had set 30240 (K=63 Branch B axis); /125 restores /121-canonical K=21.
    # iter-v3/130: at 4h, expected = 5040 (K=21 candles × 4h × 60 = 5040 min).
    if bar_interval == "4h":
        expected_timeout_minutes = 5040  # K=21 × 4h × 60 — iter-v3/130 bar-interval axis
    else:
        expected_timeout_minutes = 10080  # 21 candles at 8h — /121-canonical K=21 restored
    assert cfg.timeout_minutes == expected_timeout_minutes, (
        f"BacktestConfig.timeout_minutes ({cfg.timeout_minutes}) != expected "
        f"({expected_timeout_minutes}) at bar_interval={bar_interval!r}. "
        f"iter-v3/130: at 4h, timeout_minutes must be 5040 (K=21 × 4h × 60min). "
        f"At 8h: 10080 (K=21 × 8h × 60min). "
        "Verify _build_v3_model BacktestConfig(timeout_minutes=_label_timeout_minutes). "
        "Critic /069 Rec #1: label horizon must be consistent at "
        "BacktestConfig + LightGbmStrategy."
    )
    assert lgbm_strategy.label_timeout_minutes == expected_timeout_minutes, (
        f"LightGbmStrategy.label_timeout_minutes ({lgbm_strategy.label_timeout_minutes}) "
        f"!= expected ({expected_timeout_minutes}) at bar_interval={bar_interval!r}. "
        "Verify _build_v3_model common_kwargs label_timeout_minutes=_label_timeout_minutes. "
        "Critic /069 Rec #1: same single-source-of-truth invariant."
    )
    assert cfg.timeout_minutes == lgbm_strategy.label_timeout_minutes, (
        f"BacktestConfig.timeout_minutes ({cfg.timeout_minutes}) != "
        f"LightGbmStrategy.label_timeout_minutes ({lgbm_strategy.label_timeout_minutes}) — "
        f"DESYNC DETECTED at bar_interval={bar_interval!r}. "
        f"Both must be {expected_timeout_minutes}. "
        "Critic /069 Rec #1: desync of these two fields silently corrupts label horizon."
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
    For v3: 3 × 14 × 27 ≈ 1134 rows (varies by symbol listing date; LDO listed late).

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
    required_gap_override: int | None = None,
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

    # iter-v3/117: at --bar-interval 24h, required_gap_override=72 (vs REQUIRED_GAP=66 at 8h).
    _effective_gap: int = (
        required_gap_override if required_gap_override is not None else REQUIRED_GAP
    )
    # Assertion: gap must equal _effective_gap (brief Section 3.5#3)
    splits = combinatorial_purged_cv(
        n_samples=n_candles,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=_effective_gap,
        embargo=CPCV_EMBARGO,
        expected_gap=_effective_gap,
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
# iter-v3/084 METHODOLOGY FIX (the SINGLE declared change of /084; /083 Critic
# FINAL `1116124` Rec #2): PER_CELL_GAP was the stale value 43 = (42+1), left
# over from the iter-v3/068 42-candle timeout-widening, which /069/070 REVERTED
# to 21 candles. The per-cell CSCV is a SINGLE-symbol per-(symbol, month) cell —
# the purge gap is (timeout_candles+1) = (21+1) = 22; the *n_symbols factor
# applies ONLY to the pooled global CPCV (REQUIRED_GAP), which interleaves all
# symbols into one candle sequence. The stale 43 OVER-purged (the conservative
# direction — it biased per-cell PBO pessimistically, so it did NOT invalidate
# /083). tests/strategies/ml/test_per_cell_pbo_synthetic.py already carried the
# correct 22 — the runner was out of sync with its own regression test; this
# fix brings the runner INTO sync. Correcting 43→22 changes the per-cell PBO
# number going forward.
PER_CELL_GAP = 22  # (timeout_candles + 1) = (21 + 1) within a SINGLE-symbol cell


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

            # Per-cell CSCV — iter-v3/084: expected_gap self-assertion added
            # (/083 Critic FINAL `1116124` Rec #2) so PER_CELL_GAP cannot
            # silently drift again; mirrors the global _compute_cpcv_paths
            # call which already passes expected_gap=REQUIRED_GAP.
            cell_splits = combinatorial_purged_cv(
                n_samples=n_candles_mat,
                n_splits=PER_CELL_N_SPLITS,
                n_test_splits=PER_CELL_K,
                gap=PER_CELL_GAP,
                embargo=0,
                expected_gap=PER_CELL_GAP,
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
    symbol: str | tuple[str, ...],
    seed: int,
    n_trials: int,
    ensemble_seeds: list[int],
    oof_persist_path: Path | None = None,
    fast_mode: bool = False,
    model_type: str = "lgbm",
    bar_interval: str = "8h",
) -> tuple[BacktestConfig, RiskV3Wrapper]:
    """Build v3 M1 strategy + RiskV3Wrapper for one symbol or a pooled multi-symbol panel.

    v2 5-gate config + BTC trend filter. NO R1/R2/R3 (brief Section 3.4).
    oof_persist_path: if set, per-trial OOF returns written to parquet
    (sub-fix 1d, iter-v3/003).
    fast_mode: if True, hardcode colsample_bytree=1.0 in Optuna search space
    to minimize per-seed feature-subsampling variance (iter-v3/007 exploration).
    model_type: 'lgbm' (default) or 'xgboost'. Routes to LightGbmStrategy or
    XgboostStrategy. The --model CLI flag controls this. Default 'lgbm' preserves
    backward compatibility for all prior iteration runners (iter-v3/016 §3.5 sub-fix #8).

    iter-v3/112 POOLED architecture: when ``symbol`` is a tuple of symbols,
    BacktestConfig.symbols is set to that tuple so build_master concatenates all
    three panels. The strategy is ONE LightGbmStrategy trained on the pooled
    BCH+LDO+TRX panel. feature_columns and atr_multipliers come from the FIRST
    symbol's per-symbol lookup — since V3_FEATURES_PER_SYMBOL={} and
    V3_ATR_MULTIPLIERS_PER_SYMBOL={}, every symbol returns the identical 14-feature
    stack and (2.0, 1.0) ATR default, so the single lookup is equivalent to any.
    """
    # iter-v3/112: symbol may be a tuple (pooled) or a str (per-symbol legacy).
    if isinstance(symbol, tuple):
        symbols_tuple: tuple[str, ...] = symbol
        # For feature_columns and ATR lookup, use the first symbol (all return
        # the same values since V3_FEATURES_PER_SYMBOL and
        # V3_ATR_MULTIPLIERS_PER_SYMBOL are both empty).
        _probe_sym = symbols_tuple[0]
    else:
        symbols_tuple = (symbol,)
        _probe_sym = symbol

    # iter-v3/117: bar_interval-conditional BacktestConfig.
    # iter-v3/130: 4h bar interval added — K=21 candles × 4h = 84h = 5040 min label horizon.
    if bar_interval == "24h":
        _interval_str = "24h"
        _cooldown_candles = 2  # 2 daily bars = 48h refractory (brief Section 3.5 Change 3)
        _features_dir_str = str(FEATURES_DIR_24H)
        _label_timeout_minutes = 10080  # K=21 × 24h = 504h — same as 8h in minutes but K=7
        # feature_columns: /059 14-feature stack + offset_id as the 15th feature.
        _base_feature_cols = list(features_for_symbol(_probe_sym))
        _feature_columns = _base_feature_cols + ["offset_id"]
    elif bar_interval == "4h":
        # iter-v3/130: 4h native klines. K=21 candles × 4h = 84h = 5040 min.
        _interval_str = "4h"
        _cooldown_candles = 8  # 8 × 4h = 32h between trades (same absolute time as 8h baseline)
        _features_dir_str = str(FEATURES_DIR_4H)
        _label_timeout_minutes = 5040  # K=21 × 4h × 60min = 5040 min (brief Section 3.3)
        _feature_columns = list(features_for_symbol(_probe_sym))
    else:
        _interval_str = "8h"
        _cooldown_candles = 4  # 32h between trades (inherited from v2)
        _features_dir_str = str(FEATURES_DIR)
        _label_timeout_minutes = 10080  # K=21 × 8h × 60min = 10080 min
        _feature_columns = list(features_for_symbol(_probe_sym))

    cfg = BacktestConfig(
        symbols=symbols_tuple,
        interval=_interval_str,
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        # iter-v3/130: timeout_minutes is bar-interval-conditional.
        # At 4h: K=21 × 4h × 60 = 5040 min (brief Section 3.3, label_timeout_minutes).
        # At 8h/24h: K=21 × 8h × 60 = 10080 min (/121-canonical K=21).
        timeout_minutes=_label_timeout_minutes,
        fee_pct=0.1,
        data_dir=DATA_DIR,
        cooldown_candles=_cooldown_candles,
        vol_targeting=False,  # Vol targeting via RiskV3Wrapper
        # iter-v3/116: early-exit-on-no-confirmation exit primitive.
        # iter-v3/117: REVERT enable_no_confirm_exit False (was True at /116).
        # iter-v3/120: CONFIRMATION bundle RE-ENABLES enable_no_confirm_exit=True
        # (Component A of the TWO-COMPONENT /116+/119 bundle — RULE-layer
        # PROMISING-MECHANICAL). Parameters trigger_atr=0.50 and k_candles=4 are
        # unchanged from the /116 EXPLORATION hand-chosen values (brief Section 0).
        enable_no_confirm_exit=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
    )
    # iter-v3/016: --model {lgbm,xgboost} routes to the appropriate strategy class.
    # iter-v3/017: --model metalabeling routes to MetaLabelingStrategy (M1+M2).
    # Constructor signatures are identical so we call with the same kwargs.
    # iter-v3/032: per-symbol ATR multipliers via atr_multipliers_for_symbol().
    # LDOUSDT returns (1.5, 0.75); BCH/TRX/ALGO fall back to (2.0, 1.0) via dict.
    # iter-v3/112: use _probe_sym for ATR and feature lookups. Since
    # V3_ATR_MULTIPLIERS_PER_SYMBOL={} and V3_FEATURES_PER_SYMBOL={}, every
    # symbol returns the global (2.0, 1.0) DEFAULT and the 14-feature fallback
    # respectively — the pooled single-lookup is identical to any per-symbol lookup.
    # iter-v3/116: REVERT /115's non-binding-barrier override.
    # /115 used _atr_tp, _atr_sl = 100.0, 100.0 to make barriers non-binding
    # under fixed_horizon labeling. /116 returns to triple_barrier labels with
    # the /059-canonical (2.0, 1.0) ATR multipliers. The per-symbol lookup
    # returns the global defaults since V3_ATR_MULTIPLIERS_PER_SYMBOL is empty.
    _atr_tp, _atr_sl = atr_multipliers_for_symbol(_probe_sym)
    common_kwargs = dict(
        training_months=TRAINING_MONTHS,
        n_trials=n_trials,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        # iter-v3/130: label_timeout_minutes is bar-interval-conditional.
        # At 4h: 5040 min (K=21 × 4h × 60). At 8h/24h: 10080 min (/121-canonical K=21).
        label_timeout_minutes=_label_timeout_minutes,
        fee_pct=0.1,
        features_dir=_features_dir_str,  # iter-v3/117/130: conditional on bar_interval
        verbose=1,
        atr_tp_multiplier=_atr_tp,  # 2.0 — /059-canonical triple-barrier (reverted from /115)
        atr_sl_multiplier=_atr_sl,  # 1.0 — /059-canonical triple-barrier (reverted from /115)
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=list(ensemble_seeds),
        # iter-v3/030: per-symbol dispatch — EXPLICIT list, never None.
        # iter-v3/112: pooled case uses _probe_sym (all symbols identical since
        # V3_FEATURES_PER_SYMBOL is empty — universal 14-feature fallback).
        # iter-v3/117: at 24h, _feature_columns includes offset_id as the 15th feature.
        feature_columns=_feature_columns,
        ood_enabled=False,  # OOD via RiskV3Wrapper z-score gate
        fast_mode=fast_mode,  # iter-v3/007 — colsample_bytree=1.0 when True
        # iter-v3/116: REVERT /115's label_mode="fixed_horizon".
        # /116 returns to triple_barrier labels (the /059-canonical labeling
        # architecture). The early-exit-on-no-confirmation primitive does NOT
        # change the label estimand — only the execution exit path.
        # trend_scan_grid carries its LightGbmStrategy default (5,8,13,21).
        label_mode="triple_barrier",
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
        # iter-v3/068: REVERT inference_threshold_floor to default 0.0 (iter-v3/067 INERT closed).
        # /067's Path D axis (floor=0.60) was INERT-AT-EXPLORATION per Critic FINAL `b8d3bb5`.
        # /068 isolates the single varied axis: label_timeout_minutes=20160 (Path C).
        m1 = LightGbmStrategy(
            oof_persist_path=oof_persist_path,
            **common_kwargs,
        )
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
        # iter-v3/023-073: DISABLED (axis isolation for other iterations' single axes).
        # iter-v3/074: ENABLED — the cycle-2 EXPLORATION #4 axis (regime kill switch,
        #   TRX-scoped). INERT-AT-EXPLORATION (Critic FINAL `2371324`); the gate
        #   suppressed only 3 IS + 5 OOS TRX trades — too few to lift the IS drag.
        #   Primitive 9 is now CLOSED across two data points (NEGATIVE-pre-fix /022 +
        #   INERT-post-fix /074; BASELINE_V3.md "Dead Ideas").
        # iter-v3/075: REVERTED to DISABLED. /074's regime-gate axis is closed and
        #   must not silently carry into /075 per `feedback_no_cheating.md` anti-drift
        #   discipline. This revert restores the /060 baseline risk-gate stack
        #   (primitive 9 OFF). /075's axis is primitive 12 (BTC-trend-regime SIZE
        #   de-rate scalar), enabled below. regime_dd/vol thresholds left as inert
        #   defaults — they have no effect when enable_regime_gate=False.
        enable_regime_gate=False,  # UNCHANGED — BTC-stress trigger stays OFF
        #   (EDA: BTC triggers do not separate LDO)
        # iter-v3/115: the iter-v3/114 primitive-9 axis (LDO-scoped kill_LOW
        # ldo_realvol_zscore gate) is CLOSED. iter-v3/115 reverts to the
        # /059-canonical risk stack — primitive 9 DISABLED, no LDO regime-gate
        # target. See Change 5 in Section 3.5 of the iter-v3/115 research brief.
        regime_gate_symbols=(),
        regime_dd_threshold_pct=20.0,
        regime_vol_zscore_threshold=1.5,
        # ldo_realvol_zscore_floor and ldo_realvol_lookback_bars kept (inert
        # when enable_ldo_realvol_gate=False) — avoids touching RiskV2Config
        # field set unnecessarily.
        enable_ldo_realvol_gate=False,
        ldo_realvol_zscore_floor=0.30,  # inert — gate is OFF
        ldo_realvol_lookback_bars=90,  # inert — gate is OFF
        # iter-v3/075: primitive 12 — BTC-trend-regime position-SIZE de-rate scalar.
        # /075 enabled this as the cycle-2 EXPLORATION #5 axis (INERT-AT-EXPLORATION
        # per Critic FINAL `2211927` — the de-rate traded IS for OOS roughly 1:1; a
        # post-gate macro BTC-trend classifier whose sign IS the IS/OOS regime axis
        # is OOS-costly by construction). /075 did NOT advance to CONFIRMATION.
        # iter-v3/077: Primitive 12 stays DISABLED (reverted OFF at /076; OFF at
        #   /077). /075's Primitive-12 axis is closed and must not silently carry
        #   forward per `feedback_no_cheating.md` anti-drift discipline. Keeping it
        #   OFF holds the /060 baseline risk-gate stack. /077's axis is a
        #   PASSIVE-DIAGNOSTIC report instrumentation (a per-feature conditional-
        #   orthogonality map; the trade roster is bit-identical to /060) — the
        #   structurally-correct response to the cycle-2 0/6-PROMISING state:
        #   build the conditional-orthogonality tooling /078+ need before
        #   proposing another feature. regime_size_scalar_value and
        #   regime_size_ma_window left as inert defaults — they have no effect
        #   when enable_regime_size_scalar=False. The RiskV2Config fields stay
        #   DEFINED (Primitive 12's mechanics remain test-covered by
        #   test_regime_size_scalar.py); only the runner enablement reverts.
        enable_regime_size_scalar=False,
        regime_size_scalar_symbols=(),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=270,
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
        # iter-v3/127: per-symbol drawdown brake ENABLED (sole /127 axis) — REVERTED at /128.
        # /127 NEGATIVE (catastrophic OOS collapse); drawdown brake axis CLOSED per Critic FINAL.
        # iter-v3/128: REVERT enable_per_symbol_drawdown_brake=False (mandatory baseline-restore).
        # The /128 sole axis is universe substitution (BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO);
        # the brake field reverts to /121-canonical False (per "mandatory secondary baseline-restore
        # edit" pattern from /083/077/126).
        enable_per_symbol_drawdown_brake=False,  # /128: REVERT /127 brake (axis CLOSED)
        # iter-v3/129: primitive 13 — per-symbol drawdown SIZE-SCALING (continuous form).
        # iter-v3/130: REVERT primitive 13 to False (axis CLOSED at /129 NEGATIVE-catastrophic).
        # Single-axis bar-interval attribution requires all other axes at /121-canonical values.
        enable_per_symbol_drawdown_scaling=False,
        drawdown_scaling_t_r=6.0,
        drawdown_scaling_t_max=7.0,
        drawdown_scaling_window_days=45,
        drawdown_scaling_time_override_candles=21,
        # iter-v3/130: candle interval minutes is bar-interval-conditional.
        drawdown_scaling_candle_interval_minutes=240 if bar_interval == "4h" else 480,
        # iter-v3/081: REVERT the iter-v3/061 per-symbol vol_scale_floor accretion.
        # The {"TRXUSDT": 0.5} floor was introduced by iter-v3/061 — an EXPLORATION
        # classified INERT-AT-EXPLORATION (IS Δ -0.009 / OOS Δ +0.015 vs /060 anchor,
        # inside the noise band; never even PROMISING). iter-v3/061 was never MERGED
        # (no v0.v3-061 tag; cycle-1 CONFIRMATION /070 was NO-MERGE), and the floor
        # was NOT a component of the /070 bundle. Per the v3 cadence rule "only
        # CONFIRMATION-MERGE updates the canonical config", an INERT EXPLORATION axis
        # that persisted in the active runner config is ILLEGITIMATE ACCRETION. The
        # /059 canonical baseline (BASELINE_V3.md, setup commit 20095a8) has NO
        # per-symbol vol-floor — TRX uses the global 0.3 floor like BCH/LDO.
        # The /081 cycle-2 CONFIRMATION reverts the floor to {} so it measures the
        # genuine /059 canonical config. Evidence: analysis/iteration_v3-081/
        # (T1 accretion ledger + T2 vol-floor provenance), brief Section 2-3.
        # This mirrors the iter-v3/070-closeout precedent (revert 8bdf392 stripped
        # the rejected /065 SL-widening). The RiskV2Config.vol_scale_floor_per_symbol
        # FIELD and the risk_v2.py _vol_scale per-symbol lookup STAY — backward-
        # compatible mechanism, empty {} reproduces pre-/061 behavior bit-identically.
        vol_scale_floor_per_symbol={},
        # iter-v3/067: REVERT vol_scale_ceiling to default 1.0 (per brief Section 3 Sub-fix 4).
        # /066's vol_scale_ceiling=0.8 axis was INERT-AT-EXPLORATION (closed per Critic /066).
        # Scenario B: revert to default for clean single-axis attribution of Path D threshold floor.
        # vol_scale_ceiling not set here — defaults to 1.0 per risk_v2.py:58.
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
    dsr_relative_b4: float = 0.0,
    daily_sharpe_oos_b4_at_sqrt252: float = 0.0,
    cpcv_q75_annualized_b4: float = 0.0,
    n_daily_obs_oos: int = 0,
) -> None:
    """Write dsr.json — includes PBO metadata, iter-v3/055 DSR_relative, and
    iter-v3/059 cpcv_frac_positive_paths gate fields, and iter-v3/070 Path B4 fields."""
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
        "dsr_relative": round(dsr_relative, 6),  # iter-v3/055: PSR vs CPCV Q75 (legacy)
        "cpcv_path_sharpe_q75": round(cpcv_path_sharpe_q75, 6),  # iter-v3/055: benchmark
        "n_trials": n_trials,
        "n_eff": n_eff,
        "min_trl_months": round(min_trl_months, 2),
        # iter-v3/070 Path B4: annualized-both-sides DSR_relative reformulation.
        # Resolves granularity-mismatch artifact in legacy dsr_relative.
        # Per briefs-v3/iteration_v3-062/research_brief.md Section 3 (deferred) +
        # briefs-v3/iteration_v3-070/research_brief.md Section 2.4 T3 traceback.
        "dsr_relative_b4": round(dsr_relative_b4, 6),
        "daily_sharpe_oos_b4_at_sqrt252": round(daily_sharpe_oos_b4_at_sqrt252, 6),
        "cpcv_q75_annualized_b4": round(cpcv_q75_annualized_b4, 6),
        "n_daily_obs_oos": n_daily_obs_oos,
    }
    (report_dir / "dsr.json").write_text(json.dumps(data, indent=2))
    gate_str = "PASS" if cpcv_gate_pass else "FAIL"
    thr = _CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD
    b4_gate = "PASS" if dsr_relative_b4 >= 0.95 else "FAIL"
    print(
        f"[v3 report] dsr.json: DSR={dsr_val:.4f}, PBO={pbo_out}, "
        f"frac_pos_paths={frac_pos:.3f} (gate {gate_str} @ {thr}), "
        f"PSR={psr_val:.4f}, DSR_relative={dsr_relative:.4f}, "
        f"CPCV_Q75={cpcv_path_sharpe_q75:.4f}, n_eff={n_eff}, "
        f"DSR_relative_B4={dsr_relative_b4:.4f} ({b4_gate} @ 0.95)"
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
# Conditional-orthogonality report (iter-v3/077 PASSIVE-DIAGNOSTIC axis)
# ============================================================


def _write_conditional_orthogonality(
    primary_model_pairs: list,
    report_dir: Path,
) -> None:
    """Write `conditional_orthogonality.csv` — the iter-v3/077 PASSIVE-DIAGNOSTIC
    axis (brief Section 3.1).

    This is a REPORT-EMISSION-ONLY function. It reads the already-trained models
    in ``primary_model_pairs`` (the same object ``_write_feature_importance``
    consumes) and emits a per-feature conditional-orthogonality table. It does
    NOT touch the model, the feature set, the labeling, the risk gates, or the
    trade roster — the iter-v3/077 trade roster is bit-identical to /060.

    Two parts are emitted:
      PART A — last-month gain-importance SHARE per feature, per symbol. This is
        the runner-self-contained part: ``inner._models`` carries only the LAST
        walk-forward month's ensemble (lazy monthly training — same scope as
        ``_write_feature_importance``), so the runner can report the last-month
        model-split-allocation share but cannot reconstruct the per-IS-month
        trajectory at the report stage.
      PART B — the EDA's committed full per-IS-month conditional-orthogonality
        correlation, copied from ``analysis/iteration_v3-077/
        T3_conditional_orthogonality.csv`` (EDA SHA 313d3c0). This is the full
        diagnostic deliverable — the correlation of each feature's per-(symbol,
        IS-month) importance share with the BTC monthly regime label. The EDA
        produces it; the runner surfaces it in the report directory so the
        conditional-orthogonality map ships with the iteration's reports.

    The engineering report must state which parts were emitted (per brief
    Section 3.1 implementation note).
    """
    if not primary_model_pairs:
        return

    cols: list[str] = list(V3_FEATURE_COLUMNS)
    for _, strat in primary_model_pairs:
        inner = strat.inner if hasattr(strat, "inner") else strat
        if hasattr(inner, "_all_feature_cols") and inner._all_feature_cols:
            cols = list(inner._all_feature_cols)
            break

    # PART A — last-month gain-importance SHARE per (symbol, feature).
    sym_share: dict[str, dict[str, float]] = {}
    for cfg, strat in primary_model_pairs:
        sym = cfg.symbols[0] if cfg.symbols else "UNKNOWN"
        inner = strat.inner if hasattr(strat, "inner") else strat
        if hasattr(inner, "_m1"):
            inner = inner._m1
        if not hasattr(inner, "_models") or not inner._models:
            continue
        acc = {c: 0.0 for c in cols}
        n_models = 0
        for model in inner._models:
            if hasattr(model, "feature_importances_"):
                fi_arr = model.feature_importances_
                for i, c in enumerate(cols):
                    if i < len(fi_arr):
                        acc[c] += float(fi_arr[i])
                n_models += 1
        if n_models == 0:
            continue
        total = sum(acc.values())
        sym_share[sym] = {c: (acc[c] / total if total > 0 else 0.0) for c in cols}

    # PART B — the EDA's committed full per-IS-month conditional-orthogonality map.
    eda_t3 = (
        Path(__file__).resolve().parent
        / "analysis"
        / "iteration_v3-077"
        / "T3_conditional_orthogonality.csv"
    )
    cond_corr: dict[str, dict] = {}
    if eda_t3.is_file():
        with open(eda_t3, newline="") as f:
            for row in csv.DictReader(f):
                cond_corr[row["feature"]] = row

    out_path = report_dir / "conditional_orthogonality.csv"
    fieldnames = [
        "feature",
        "last_month_importance_share_portfolio",
        "eda_corr_portfolio_pooled",
        "eda_max_abs_corr",
        "eda_conditionally_regime_loaded",
        "source",
    ]
    rows: list[dict] = []
    for c in cols:
        # portfolio-mean last-month share across symbols
        shares = [sym_share[s][c] for s in sym_share if c in sym_share[s]]
        lm_share = round(sum(shares) / len(shares), 6) if shares else 0.0
        ec = cond_corr.get(c, {})
        rows.append(
            {
                "feature": c,
                "last_month_importance_share_portfolio": lm_share,
                "eda_corr_portfolio_pooled": ec.get("corr_portfolio_pooled", ""),
                "eda_max_abs_corr": ec.get("max_abs_corr", ""),
                "eda_conditionally_regime_loaded": (
                    "True"
                    if ec.get("max_abs_corr") and float(ec["max_abs_corr"]) > 0.35
                    else "False"
                    if ec.get("max_abs_corr")
                    else ""
                ),
                "source": (
                    "PART_A_runner + PART_B_eda_313d3c0"
                    if ec
                    else "PART_A_runner_only (EDA T3 not found)"
                ),
            }
        )
    rows.sort(
        key=lambda r: float(r["eda_max_abs_corr"]) if r["eda_max_abs_corr"] else -1.0,
        reverse=True,
    )
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"[v3 report] conditional_orthogonality.csv: {len(rows)} features "
        f"(PART A last-month share + PART B EDA per-month map)"
    )


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
    bar_interval: str = "8h",
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
    bar_interval:
        iter-v3/117: '8h' (default, backward-compat) or '24h' (3-offset
        multi-offset derived-series axis). Forwarded to _build_v3_model.
    """
    models_to_run = active_models if active_models is not None else V3_MODELS
    all_trades: list = []
    model_pairs: list = []

    # iter-v3/112 POOLED architecture: detect whether all entries in models_to_run
    # share the same label (the "v3-pooled" sentinel). When pooled, build ONE
    # LightGbmStrategy on the concatenated multi-symbol panel instead of one per symbol.
    # The per-symbol loop is retained unchanged for non-pooled runs (backward compat).
    _labels = [name for name, _sym in models_to_run]
    _is_pooled = len(_labels) > 1 and len(set(_labels)) == 1

    # Shared ensemble-seed resolve (used by both paths below).
    if ensemble_seeds_override is not None:
        ensemble_seeds_run = list(ensemble_seeds_override)
    else:
        size_for_this_run = ensemble_size if ensemble_size is not None else ENSEMBLE_SIZE
        ensemble_seeds_run = _derive_ensemble_seeds(seed, size=size_for_this_run)

    oof_path = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"

    if _is_pooled:
        # Pooled path: ONE model on the concatenated 3-symbol panel.
        pooled_symbols: tuple[str, ...] = tuple(sym for _n, sym in models_to_run)
        pooled_label = _labels[0]
        print("=" * 60)
        print(f"MODEL {pooled_label} [POOLED: {', '.join(pooled_symbols)}] — seed {seed}")
        print("=" * 60)
        cfg, strategy = _build_v3_model(
            symbol=pooled_symbols,
            seed=seed,
            n_trials=n_trials,
            ensemble_seeds=ensemble_seeds_run,
            oof_persist_path=oof_path,
            fast_mode=fast_mode,
            model_type=model_type,
            bar_interval=bar_interval,
        )
        _verify_symbols(cfg.symbols)
        t0 = time.time()
        results = run_backtest(cfg, strategy, yearly_pnl_check=False)
        elapsed = time.time() - t0
        print(
            f"{pooled_label} [POOLED {len(pooled_symbols)} syms]: "
            f"{len(results)} trades in {elapsed:.0f}s (seed={seed})"
        )
        if hasattr(strategy, "gate_stats_summary"):
            print(f"  gate stats: {strategy.gate_stats_summary()}")
        all_trades.extend(results)
        model_pairs.append((cfg, strategy))
    else:
        # Per-symbol path (legacy — pre-/112 behaviour, unchanged).
        for name, symbol in models_to_run:
            print("=" * 60)
            print(f"MODEL {name} — seed {seed}")
            print("=" * 60)
            cfg, strategy = _build_v3_model(
                symbol=symbol,
                seed=seed,
                n_trials=n_trials,
                ensemble_seeds=ensemble_seeds_run,
                oof_persist_path=oof_path,
                fast_mode=fast_mode,
                model_type=model_type,
                bar_interval=bar_interval,
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
    parser.add_argument(
        "--bar-interval",
        type=str,
        default="8h",
        choices=["8h", "24h", "4h"],
        help=(
            "iter-v3/117: candle bar interval. '8h' (default) is backward-compatible "
            "with /001-/116 (all prior iterations). '24h' enables the 3-offset "
            "multi-offset derived-series axis: 8h CSVs aggregated into 24h bars at "
            "UTC offsets 0h/8h/16h, concatenated as a pooled panel with offset_id "
            "as the 15th feature. Features written to data/features_v3_24h/; kline "
            "CSVs written to data/<SYM>/24h.csv for the backtest engine. "
            "REQUIRED_GAP override: 72 = (7+1)*3*3 at 24h (vs 66 at 8h). "
            "iter-v3/130: '4h' enables native 4h klines. K=21 candles × 4h = 84h = "
            "3.5 days label horizon (HALVED from 7 days at 8h). Features written to "
            "data/features_v3_4h/; kline CSVs at data/<SYM>/4h.csv. "
            "REQUIRED_GAP=66 UNCHANGED in candle-count terms (same K=21 × 3 symbols). "
            "Default 8h preserves byte-identity with all prior iterations."
        ),
    )
    args = parser.parse_args()

    # iter-v3/130: run.log capture — fix the 5-occurrence instrumentation gap
    # (/124/125/127/128/129 all missing run.log per engineering reports).
    # TeeLogger redirects sys.stdout + sys.stderr to both terminal and run.log file.
    # The log path is computed from ITERATION_LABEL (already set at module level).
    _run_log_path = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "run.log"
    _tee = _TeeLogger(_run_log_path)
    try:
        _main_body(args)
    finally:
        _tee.close()


def _main_body(args) -> None:  # noqa: ANN001
    """Main execution body — extracted to allow TeeLogger try/finally wrapping.

    iter-v3/130: run.log fix. All backtest logic moved here so the TeeLogger
    context manager in main() captures the complete stdout/stderr output.
    """
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
    # iter-v3/130: pass bar_interval so 4h CSVs are checked at 4h (BTCUSDT stays 8h).
    _verify_data_freshness(baseline_symbols + ("BTCUSDT",), bar_interval=args.bar_interval)
    # asserts len == 14 (BASELINE_V3 /059 14-feature anchor);
    # funding_regime_momentum_5d / vwap_dev_50 / closed funding-FAMILY / basis-family ABSENT;
    # also asserts ensemble_size in (3, 10) for mode discipline.
    # iter-v3/130: pass bar_interval so label_timeout probe uses correct expected value.
    _verify_feature_columns(ensemble_size=ensemble_size_for_run, bar_interval=args.bar_interval)
    # asserts REQUIRED_GAP appropriate for bar_interval:
    # 8h → 66 = (21+1)*3; 24h → 72 = (7+1)*3*3 (iter-v3/117 multi-offset formula)
    _verify_label_leakage_gap(bar_interval=args.bar_interval)
    _verify_track_isolation()  # grep check

    # iter-v3/121-METHODOLOGY: SINGLE-COMPONENT pre-flight assertions.
    # Component A: /116 no_confirm exit REMAINS enabled (enable_no_confirm_exit=True).
    # Component B: /119 C6 ret5d_signed_tbi REVERTED — NOT in V3_FEATURE_COLUMNS_TOP_N (14).
    # The accretion guard above already catches drift; these assertions fire a
    # human-readable message if someone bypasses the guard.
    # iter-v3/130: pass bar_interval so BacktestConfig.timeout_minutes matches expected.
    _pf_cfg, _ = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42], bar_interval=args.bar_interval
    )
    assert _pf_cfg.enable_no_confirm_exit is True, (
        "PREFLIGHT FAIL: enable_no_confirm_exit must be True for iter-v3/121-METHODOLOGY "
        "(Component A — /116 no_confirm REMAINS enabled; /117 revert was undone at /120). "
        "Set enable_no_confirm_exit=True in BacktestConfig in _build_v3_model."
    )
    assert _pf_cfg.no_confirm_trigger_atr == 0.50, (
        f"PREFLIGHT FAIL: no_confirm_trigger_atr={_pf_cfg.no_confirm_trigger_atr} — "
        "expected 0.50. Check _build_v3_model BacktestConfig."
    )
    assert _pf_cfg.no_confirm_k_candles == 4, (
        f"PREFLIGHT FAIL: no_confirm_k_candles={_pf_cfg.no_confirm_k_candles} — "
        "expected 4. Check _build_v3_model BacktestConfig."
    )
    print(
        "  iter-v3/121-METHODOLOGY pre-flight: enable_no_confirm_exit=True "
        "(/116 no_confirm Component A — REMAINS enabled at /121 SINGLE-COMPONENT run), "
        "no_confirm_trigger_atr=0.50, no_confirm_k_candles=4  PASS"
    )
    # iter-v3/121-METHODOLOGY: verify Component B is ABSENT (C6 REVERTED).
    # Brief Section 3 Sub-fix 3: assert inverted from /120 PRESENT to /121 ABSENT.
    assert _pf_cfg.enable_no_confirm_exit is True, (
        "PREFLIGHT FAIL: enable_no_confirm_exit must be True for iter-v3/121-METHODOLOGY "
        "(Component A still active)."
    )
    assert _pf_cfg.no_confirm_trigger_atr == 0.50, "PREFLIGHT FAIL: trigger_atr must be 0.50"
    assert _pf_cfg.no_confirm_k_candles == 4, "PREFLIGHT FAIL: k_candles must be 4"
    assert "ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N, (
        "PREFLIGHT FAIL: ret5d_signed_tbi must NOT be in V3_FEATURE_COLUMNS_TOP_N for "
        "iter-v3/121-METHODOLOGY (Component B REVERTED per /120 F3-DROP binding "
        "pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`). "
        "Remove 'ret5d_signed_tbi' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert len(V3_FEATURE_COLUMNS_TOP_N) == 14, (
        "PREFLIGHT FAIL: V3_FEATURE_COLUMNS_TOP_N must be 14 features for iter-v3/128 "
        "(/121 BASELINE 14-feature stack; d24_ret_autocorr_lag1_50 REMOVED per /126 "
        "NEGATIVE-catastrophic; universe substitution is NOT a feature axis)."
    )
    assert "d24_ret_autocorr_lag1_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "PREFLIGHT FAIL: d24_ret_autocorr_lag1_50 must NOT be in V3_FEATURE_COLUMNS_TOP_N for "
        "iter-v3/128 (/126 NEGATIVE-catastrophic; multi-frequency axis CLOSED)."
    )
    assert "eth_vs_sym_rv_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "PREFLIGHT FAIL: eth_vs_sym_rv_50 must NOT be in V3_FEATURE_COLUMNS_TOP_N for "
        "iter-v3/128 (/123 NEGATIVE-catastrophic; cross-asset OHLCV axis CLOSED)."
    )
    assert "eth_ret_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "PREFLIGHT FAIL: eth_ret_3d must NOT be in V3_FEATURE_COLUMNS_TOP_N for "
        "iter-v3/128 (/122 NEGATIVE-INERT; axis CLOSED)."
    )
    print(
        "  iter-v3/129 pre-flight: enable_no_confirm_exit=True (Component A from /121), "
        "V3_FEATURE_COLUMNS_TOP_N=14 (/121 BASELINE; d24_ret_autocorr_lag1_50 REMOVED /126), "
        "BCH/LDO/TRX 3-symbol universe (REVERT from /128), drawdown brake REVERTED False, "
        "continuous size-scaling primitive 13 ENABLED (T_R=6.0, T_max=7.0, N=45d, M=21c)  PASS"
    )
    # iter-v3/130: assert /129 continuous scaling REVERTED (axis CLOSED) + bar-interval 4h.
    # /129 primitive 13 (continuous size-scaling) is REVERTED to False for single-axis
    # bar-interval attribution. /127 binary brake already False (axis CLOSED at /127).
    _pf130_cfg, _pf130_strat = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42], bar_interval=args.bar_interval
    )
    _pf130_rc = _pf130_strat.config
    assert _pf130_rc.enable_per_symbol_drawdown_scaling is False, (
        "PREFLIGHT FAIL: enable_per_symbol_drawdown_scaling must be False for iter-v3/130 "
        "(/129 continuous scaling axis CLOSED — NEGATIVE-catastrophic; REVERT mandatory). "
        "Set enable_per_symbol_drawdown_scaling=False in RiskV2Config in _build_v3_model."
    )
    assert _pf130_rc.enable_per_symbol_drawdown_brake is False, (
        "PREFLIGHT FAIL: enable_per_symbol_drawdown_brake must be False for iter-v3/130 "
        "(/127 binary brake REVERTED — axis CLOSED). "
        "Set enable_per_symbol_drawdown_brake=False in RiskV2Config in _build_v3_model."
    )
    assert tuple(sym for _, sym in V3_MODELS) == ("BCHUSDT", "LDOUSDT", "TRXUSDT"), (
        f"PREFLIGHT FAIL: V3_MODELS symbols = {tuple(sym for _, sym in V3_MODELS)} — "
        "expected ('BCHUSDT', 'LDOUSDT', 'TRXUSDT'). "
        "V3_MODELS must be BCH/LDO/TRX (/121 baseline preserved; /128 universe CLOSED)."
    )
    _expected_timeout_130 = 5040 if args.bar_interval == "4h" else 10080
    assert _pf130_cfg.timeout_minutes == _expected_timeout_130, (
        f"PREFLIGHT FAIL: BacktestConfig.timeout_minutes={_pf130_cfg.timeout_minutes} — "
        f"expected {_expected_timeout_130} at bar_interval={args.bar_interval!r}. "
        "iter-v3/130: at 4h, K=21 × 4h × 60 = 5040 min. At 8h: K=21 × 8h × 60 = 10080 min."
    )
    print(
        "  iter-v3/130 pre-flight: "
        f"bar_interval={args.bar_interval!r}, "
        f"timeout_minutes={_pf130_cfg.timeout_minutes} (K=21 × {args.bar_interval} × 60), "
        "enable_per_symbol_drawdown_scaling=False [/129 REVERTED — axis CLOSED], "
        "enable_per_symbol_drawdown_brake=False [/127 REVERTED], "
        "V3_MODELS=BCH/LDO/TRX  PASS"
    )
    print(
        f"Universe: BCH/LDO/TRX | Bar interval: {args.bar_interval} | "
        f"K=21 (label horizon {_pf130_cfg.timeout_minutes // 60}h "
        f"= {_pf130_cfg.timeout_minutes // 60 / 24:.1f}d) | "
        "/127 binary brake REVERTED | /129 continuous scaling REVERTED"
    )
    # Explicit /115 revert assertion: label_mode must be triple_barrier.
    # This is also caught by the accretion guard but we name it explicitly for
    # the run.log so the Critic's Check 8 can verify the revert at a glance.
    _pf_inner = _
    if hasattr(_pf_inner, "inner"):
        _pf_lgbm = _pf_inner.inner
    else:
        _pf_lgbm = _pf_inner
    if hasattr(_pf_lgbm, "label_mode"):
        assert _pf_lgbm.label_mode == "triple_barrier", (
            f"PREFLIGHT FAIL: label_mode='{_pf_lgbm.label_mode}' — "
            "expected 'triple_barrier'. /115's fixed_horizon must be REVERTED. "
            "Check _build_v3_model common_kwargs label_mode='triple_barrier'."
        )
        print(
            f"  iter-v3/116 /115-revert: label_mode='{_pf_lgbm.label_mode}'  PASS "
            "(triple_barrier — fixed_horizon REVERTED)"
        )

    # -----------------------------------------------------------------------
    # iter-v3/080 baseline-restore: /079's conviction-derate (primitive 13) is
    # REVERTED. /079 was NULL-RESULT (behavioral saturation — the de-rate
    # engaged only 7.5% of IS trades; PARKED per diary-v3/iteration_v3-079.md
    # Section 5). iter-v3/080 restores the /060-config flat weight=100 in
    # lgbm.get_signal — so the conviction-derate 3-point pre-flight assertion
    # is no longer a /080 invariant and is removed with the runner import.
    # The /080 axis is the PASSIVE-DIAGNOSTIC persisted-`confidence`
    # instrument (brief Section 3.1) — verified by the QE Phase-6 adversarial
    # test suite, not by a runner pre-flight assertion.
    # -----------------------------------------------------------------------

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

    # iter-v3/129: runtime REQUIRED_GAP is cardinality-conditional + bar_interval-conditional.
    # iter-v3/130: 4h bar interval — REQUIRED_GAP=66 UNCHANGED in candle-count terms (K=21×3).
    # 24h: (7+1)*n_symbols*3 (multi-offset). 8h/4h, cardinality 3: REQUIRED_GAP=66 (module).
    _n_active_symbols = len(V3_MODELS)
    if args.bar_interval == "24h":
        _runtime_gap: int = (7 + 1) * _n_active_symbols * 3
    elif _n_active_symbols != 3:
        # cardinality-conditional 8h override (kept for future use; not active at /130)
        _runtime_gap = (21 + 1) * _n_active_symbols
    else:
        # 4h and 8h both use REQUIRED_GAP=66 in candle-count terms (K=21, 3 symbols)
        _runtime_gap = REQUIRED_GAP  # 66 = (21+1)*3 module constant
    _timeout_min = 5040 if args.bar_interval == "4h" else 10080
    active_sym_names = ", ".join(sym for _, sym in active_models)
    # iter-v3/060: mode-aware startup log
    if args.exploration:
        print(f"[v3] Running in EXPLORATION mode (ensemble_size={ensemble_size_for_run})")
    else:
        print(f"[v3] Running in CONFIRMATION mode (ensemble_size={ensemble_size_for_run})")
    print(f"\nBASELINE v3 iter-{ITERATION_LABEL}: {active_sym_names}")
    print(
        f"Universe: BCH/LDO/TRX | Bar interval: {args.bar_interval} | "
        f"K=21 (label horizon {_timeout_min // 60}h = {_timeout_min // 60 / 24:.1f}d) | "
        "/127 binary brake DISABLED | /129 continuous scaling DISABLED  [iter-v3/130]"
    )
    # The mandatory pre-flight print per brief Section 5.6 smoke test item 12:
    print(
        f"Universe: BCH/LDO/TRX | Bar interval: {args.bar_interval} | "
        f"K=21 (label horizon {_timeout_min // 60}h "
        f"≈ {_timeout_min // 60 / 24:.1f}d)"
    )
    print(
        f"Bar interval: {args.bar_interval}  "
        f"(/116 no_confirm STAYS enabled; /127 binary brake REVERTED False; "
        f"/129 continuous size-scaling REVERTED False [iter-v3/130 bar-interval axis])"
    )
    print(f"Ensemble: {ensemble_size_for_run} seeds  Optuna trials/model: {args.n_trials}")
    print(f"Active models: {len(active_models)}/{len(V3_MODELS)} (--symbols={args.symbols!r})")
    print(f"CPCV: N={CPCV_N_SPLITS}, k={CPCV_N_TEST_SPLITS}, 45 paths on IS CANDLE SEQUENCE")
    _gap_label: str
    if args.bar_interval == "24h":
        _gap_label = f"(7+1)*{_n_active_symbols}*3={_runtime_gap} [24h override]"
    elif args.bar_interval == "4h":
        _gap_label = (
            f"(21+1)*{_n_active_symbols}={_runtime_gap} [4h: UNCHANGED in candle-count terms vs 8h]"
        )
    else:
        _gap_label = (
            f"(21+1)*{_n_active_symbols}={_runtime_gap} "
            f"[8h cardinality-{_n_active_symbols} "
            f"{'module constant' if _n_active_symbols == 3 else 'override'}]"
        )
    _n_feature_cols = "14+offset_id" if args.bar_interval == "24h" else "14"
    print(
        f"Gap: {_runtime_gap} ({_gap_label}; "
        f"module REQUIRED_GAP={REQUIRED_GAP} [3-sym constant, unchanged]; "
        f"timeout={_timeout_min} min (K=21 × {args.bar_interval} × 60); "
        f"label_mode=triple_barrier; V3_FEATURE_COLUMNS={_n_feature_cols})"
    )
    print(
        f"Pre-flight: branch OK, symbols OK, data fresh (<16h), "
        f"feature-cols={len(V3_FEATURE_COLUMNS)}  PASS\n"
    )

    # Feature generation
    if not args.skip_features:
        if args.bar_interval == "24h":
            # iter-v3/117: 24h multi-offset derived-series.
            # generate_all_multioffset_24h_features writes:
            #   data/<SYM>/24h.csv — kline-compatible CSV for backtest engine
            #   data/features_v3_24h/<SYM>_24h_features.parquet — feature parquets
            # BTCUSDT gets the 24h.csv (for BTC cross-asset features) but no parquet.
            from crypto_trade.features_v3.multioffset_24h import (  # noqa: PLC0415
                generate_all_multioffset_24h_features,
            )

            FEATURES_DIR_24H.mkdir(parents=True, exist_ok=True)
            # Include BTCUSDT so write_24h_kline_csv can produce the BTC 24h.csv.
            symbols_for_24h = list(baseline_symbols) + ["BTCUSDT"]
            generate_all_multioffset_24h_features(
                symbols=symbols_for_24h,
                data_dir=str(DATA_DIR),
                features_24h_dir=str(FEATURES_DIR_24H),
            )
            print(f"[features-24h] Multi-offset 24h features written to {FEATURES_DIR_24H}")
        elif args.bar_interval == "4h":
            # iter-v3/130: native 4h klines — generate features at 4h cadence.
            # process_symbol_v3 uses interval="4h" and writes to FEATURES_DIR_4H.
            # 4h klines must already be fetched via:
            #   uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT --intervals 4h
            # before running the backtest (pre-launch data pipeline per brief Section 5.2).
            FEATURES_DIR_4H.mkdir(parents=True, exist_ok=True)
            print(
                f"\n[features-4h] Generating 4h features for "
                f"{list(baseline_symbols)} -> {FEATURES_DIR_4H}"
            )
            for sym in baseline_symbols:
                t0_4h = time.time()
                result_4h = process_symbol_v3(sym, "4h", str(DATA_DIR), str(FEATURES_DIR_4H))
                n_rows_4h, n_cols_4h = result_4h[1], result_4h[2]
                elapsed_4h = time.time() - t0_4h
                print(
                    f"  {sym}: {n_rows_4h} rows, {n_cols_4h} feature cols at 4h ({elapsed_4h:.1f}s)"
                )
            print(f"[features-4h] 4h features written to {FEATURES_DIR_4H}")
        else:
            _generate_v3_features(list(baseline_symbols))
    else:
        print("[features] Skipping feature generation (--skip-features)")

    # Load IS-window feature DataFrames for CPCV and ADF
    print("\n[features] Loading IS-window feature DataFrames...")
    feature_parquets: dict[str, pd.DataFrame] = {}
    for sym in baseline_symbols:
        if args.bar_interval == "24h":
            # iter-v3/117: load from 24h multi-offset parquet.
            pq_path = FEATURES_DIR_24H / f"{sym}_24h_features.parquet"
        elif args.bar_interval == "4h":
            # iter-v3/130: load from 4h native parquet.
            pq_path = FEATURES_DIR_4H / f"{sym}_4h_features.parquet"
        else:
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
        bar_interval=args.bar_interval,
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
    # iter-v3/128: pass _runtime_gap as override whenever it differs from REQUIRED_GAP
    # (24h=144 or 8h cardinality-6=132). At 8h cardinality-3, _runtime_gap==REQUIRED_GAP so
    # override=None preserves the same behaviour as before.
    _cpcv_gap_override = _runtime_gap if _runtime_gap != REQUIRED_GAP else None
    cpcv_df, path_metric_matrix, per_cell_mean_pbo = _compute_cpcv_paths(
        list(baseline_symbols),
        feature_parquets,
        oof_parquet_path=oof_parquet,
        report_dir=report_dir_cpcv,
        required_gap_override=_cpcv_gap_override,
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

    # Compute DSR_relative (legacy) using existing psr() function with non-zero benchmark.
    # This is the LEGACY computation: trade-level Sharpe (NOT annualized), which produces
    # systematically low PSR values when compared to the CPCV-Q75 benchmark
    # (a candle-period Sharpe). The granularity mismatch was the root cause of the
    # /059 dsr_relative_legacy = 0.1134 artifact.
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
    print(
        f"[dsr_relative] DSR_relative (legacy, trade-level) = {dsr_relative:.4f} "
        "(benchmark = CPCV Q75)"
    )

    # -------------------------------------------------------
    # Path B4 — annualized-both-sides DSR_relative (iter-v3/070 Component B)
    # Per briefs-v3/iteration_v3-062/research_brief.md Section 3 lines 260-301
    # and briefs-v3/iteration_v3-070/research_brief.md Section 2.4 T3 traceback.
    #
    # Resolves the granularity-mismatch artifact in dsr_relative (legacy):
    #   legacy: trade-level observed_sharpe vs candle-period CPCV-Q75 benchmark
    #   Path B4: BOTH sides annualized to same basis (daily Sharpe at √252)
    #
    # Inputs (per Section 2.4 T3):
    #   observed_sharpe: daily_sharpe_oos at √252 (mean/std of daily PnL * √252)
    #   n_obs: n_daily_obs_oos (number of distinct OOS dates with at least one trade)
    #   benchmark_sharpe: cpcv_q75 de-annualized from raw path Sharpe then re-annualized
    #                     to √756 (3 candles/day × 252 trading days)
    #   skewness / kurtosis: computed on OOS daily PnL series
    #
    # CONVENTION NOTE: this function uses √252 (trading days) for daily Sharpe,
    # whereas the existing _daily_sharpe() helper uses √365 (calendar days).
    # This is DELIBERATE per brief Section 2.4 T3 CRITICAL convention divergence note.
    # The resulting daily_sharpe_oos_b4_at_sqrt252 value will be LOWER than the
    # comparison.csv daily_sharpe field (which uses √365). Documented to prevent
    # Critic confusion at Phase 7.5.
    # -------------------------------------------------------
    oos_trades_for_b4 = [t for t in braked if t.open_time >= OOS_CUTOFF_MS]
    dsr_relative_b4 = 0.0
    daily_sharpe_oos_b4 = 0.0
    cpcv_q75_annualized_b4 = 0.0
    n_daily_obs_oos = 0

    if oos_trades_for_b4:
        # Build OOS daily PnL series (group weighted_pnl by calendar date)
        oos_daily_series: dict[str, float] = {}
        for t in oos_trades_for_b4:
            trade_date = str(pd.Timestamp(t.close_time, unit="ms").date())
            oos_daily_series[trade_date] = oos_daily_series.get(trade_date, 0.0) + float(
                t.weighted_pnl
            )
        oos_daily_arr = np.array(list(oos_daily_series.values()), dtype=float)
        n_daily_obs_oos = len(oos_daily_arr)

        if n_daily_obs_oos >= 2 and oos_daily_arr.std() > 0:
            # Daily Sharpe at √252 (trading days convention per brief Section 2.4 T3)
            daily_sharpe_oos_b4 = float(oos_daily_arr.mean() / oos_daily_arr.std() * np.sqrt(252))
            daily_skew_oos_b4 = float(skew(oos_daily_arr))
            daily_kurt_oos_b4 = float(kurtosis(oos_daily_arr, fisher=False))

            # CPCV-Q75 annualized to √756 basis:
            #   flat_path_sharpes are raw candle-level Sharpes (from cpcv_paths.csv).
            #   Each path spans ~1296 candles (= 54 months × 24 candles/month on 8h data).
            #   Annualize: cpcv_q75_raw / sqrt(1296) * sqrt(756)
            #   where 756 = 3 candles/day × 252 trading days.
            #   Then compare to daily_sharpe_oos_b4 (also annualized, at √252).
            #   Effective: cpcv_q75_raw * sqrt(756 / 1296) = cpcv_q75_raw * sqrt(7/12).
            if len(flat_path_sharpes) >= 4:
                cpcv_q75_raw = float(np.percentile(flat_path_sharpes, 75))
                # De-annualize from candle-period (per-path), re-annualize to daily at √756
                cpcv_q75_annualized_b4 = cpcv_q75_raw / np.sqrt(1296) * np.sqrt(756)
            else:
                cpcv_q75_annualized_b4 = 0.0

            dsr_relative_b4 = psr(
                observed_sharpe=daily_sharpe_oos_b4,
                n_obs=max(2, n_daily_obs_oos),
                benchmark_sharpe=cpcv_q75_annualized_b4,
                skewness=daily_skew_oos_b4,
                kurtosis=daily_kurt_oos_b4,
            )
            print(
                f"[dsr_relative_b4] daily_sharpe_oos_at_√252={daily_sharpe_oos_b4:.4f}, "
                f"cpcv_q75_annualized_B4={cpcv_q75_annualized_b4:.4f}, "
                f"n_daily_obs={n_daily_obs_oos}, DSR_relative_B4={dsr_relative_b4:.6f}"
            )
        else:
            print(
                f"[dsr_relative_b4] n_daily_obs_oos={n_daily_obs_oos} < 2 or zero variance "
                "— dsr_relative_b4 = 0.0 (degenerate; not a binding gate failure)"
            )
    else:
        print("[dsr_relative_b4] No OOS trades — dsr_relative_b4 = 0.0")

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

    # iter-v3/077 PASSIVE-DIAGNOSTIC axis — per-feature conditional-orthogonality
    # map (brief Section 3.1). Report-emission only; the trade roster is
    # bit-identical to /060.
    _write_conditional_orthogonality(model_pairs, report_dir)

    # iter-v3/080 PASSIVE-DIAGNOSTIC axis — per-trade M1 confidence distribution.
    # Reads IS trades (which now carry TradeResult.confidence) and emits
    # confidence_distribution.csv (schema: symbol, is_month, conf_bin_lo,
    # conf_bin_hi, n_trades, realized_optuna_conf_threshold).
    # Report-emission only; the trade roster is bit-identical to /060.
    _write_confidence_distribution(is_trades, model_pairs, report_dir)

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

    # DSR JSON — includes legacy dsr_relative and iter-v3/070 Path B4 fields
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
        dsr_relative_b4=dsr_relative_b4,
        daily_sharpe_oos_b4_at_sqrt252=daily_sharpe_oos_b4,
        cpcv_q75_annualized_b4=cpcv_q75_annualized_b4,
        n_daily_obs_oos=n_daily_obs_oos,
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
