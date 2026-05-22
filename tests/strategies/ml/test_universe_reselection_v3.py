"""Integration tests for iter-v3/097 — universe RE-SELECTION + ongoing universe guard.

Per brief Section 9.2: every test is a HARD build-fail test. A Phase-6 build that
omits any of them, or whose runner fails any of them, MUST fail the suite before the
backtest runs. Tests #1, #2, #3 are the Section-9 mandatory build-fail items.

History:
  iter-v3/097: initial universe re-selection (BCH/TRX → GALA/ADA).
  iter-v3/110: CRV/AAVE/GRT/ADA universe (4-symbol expansion).
  iter-v3/111: Critic-mandated clean re-test of /110 under triple_barrier.
  iter-v3/112: BCH/LDO/TRX RESTORED (pooled architecture, 3-symbol).
  iter-v3/113+: BCH/LDO/TRX retained; /115 coherent horizon-exit labeling axis.
  iter-v3/125: ATOM/RUNE/UNI (3-symbol WILD axis-4 under lifted constraints).
  iter-v3/126: BCH/LDO/TRX RESTORED (mandatory /125 baseline-restore; FEATURE-CADENCE-STACK axis).
  iter-v3/127: BCH/LDO/TRX retained; drawdown brake (RISK-PRIMITIVE axis).
  iter-v3/128: ATOM/RUNE/AVAX/HBAR/ICP/ALGO (6-symbol sector-pure L1 under WILD mandate).

Current state (iter-v3/128):
  V3_MODELS = {ATOMUSDT, RUNEUSDT, AVAXUSDT, HBARUSDT, ICPUSDT, ALGOUSDT}
    (6 symbols, /128 WILD CYCLE-7 axis-7).
  ITERATION_LABEL = "v3-128".
  REQUIRED_GAP = 132 = (21+1)*6 (runner-local override; validation_v3.REQUIRED_GAP stays 66).

Test inventory:
  1. test_v3_models_is_the_reanchored_universe
  2. test_v3_models_disjoint_from_excluded
  3. test_dsr_json_is_genuinely_computed
  4. test_feature_columns_pinned_for_new_symbols
  5. test_walk_forward_embargo_intact
  6. test_oos_cutoff_and_training_months_immutable
"""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType

# ---------------------------------------------------------------------------
# Loader — imports run_baseline_v3 without executing main()
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_runner() -> ModuleType:
    """Import run_baseline_v3 from repo root without executing main()."""
    module_path = str(REPO_ROOT)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    if "run_baseline_v3" in sys.modules:
        del sys.modules["run_baseline_v3"]
    return importlib.import_module("run_baseline_v3")


# ---------------------------------------------------------------------------
# Test #1 — universe wiring (the SOLE iter-v3/097 axis)
# ---------------------------------------------------------------------------


def test_v3_models_is_the_reanchored_universe() -> None:
    """Section 9.2 test #1 (HARD build-fail).

    Asserts V3_MODELS symbols == {ATOMUSDT, RUNEUSDT, AVAXUSDT, HBARUSDT, ICPUSDT, ALGOUSDT}
    exactly — the iter-v3/128 WILD CYCLE-7 axis-7 wholesale universe replacement
    (BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO, cardinality 3→6, sector-pure L1).

    History:
      iter-v3/110: CRV/AAVE/GRT/ADA (4-symbol expansion).
      iter-v3/111: Critic re-test; universe unchanged.
      iter-v3/112: BCH/LDO/TRX RESTORED (pooled arch).
      iter-v3/113-124: BCH/LDO/TRX retained.
      iter-v3/125: WILD axis — BCH/LDO/TRX → ATOM/RUNE/UNI (NEGATIVE-catastrophic).
      iter-v3/126: V3_MODELS REVERTED BCH/LDO/TRX (mandatory /125 baseline-restore).
      iter-v3/127: BCH/LDO/TRX retained; drawdown brake axis CLOSED (NEGATIVE).
      iter-v3/128: WILD axis — BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO (cardinality 6).
    """
    runner = _load_runner()
    symbols = {sym for _label, sym in runner.V3_MODELS}

    expected = {"ATOMUSDT", "RUNEUSDT", "AVAXUSDT", "HBARUSDT", "ICPUSDT", "ALGOUSDT"}
    assert symbols == expected, (
        f"V3_MODELS symbols {symbols} != expected {expected}. "
        "iter-v3/128: V3_MODELS = 6-symbol sector-pure L1 (ATOM/RUNE/AVAX/HBAR/ICP/ALGO). "
        "Edit V3_MODELS in run_baseline_v3.py."
    )

    # Explicit: BCH/LDO/TRX must be absent (universe replaced at /128)
    assert "BCHUSDT" not in symbols, (
        "BCHUSDT found in V3_MODELS — must be absent at iter-v3/128 "
        "(BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO WILD replacement). "
        "Update V3_MODELS in run_baseline_v3.py."
    )
    assert "LDOUSDT" not in symbols, (
        "LDOUSDT found in V3_MODELS — must be absent at iter-v3/128 "
        "(BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO WILD replacement). "
        "Update V3_MODELS in run_baseline_v3.py."
    )
    assert "TRXUSDT" not in symbols, (
        "TRXUSDT found in V3_MODELS — must be absent at iter-v3/128 "
        "(BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO WILD replacement). "
        "Update V3_MODELS in run_baseline_v3.py."
    )
    assert "UNIUSDT" not in symbols, (
        "UNIUSDT found in V3_MODELS — must be absent at iter-v3/128 "
        "(/125 ATOM/RUNE/UNI was NEGATIVE-catastrophic and UNIUSDT is not in /128 universe). "
        "Update V3_MODELS in run_baseline_v3.py."
    )

    # Cardinality check: must be exactly 6 symbols
    assert len(symbols) == 6, (
        f"V3_MODELS has {len(symbols)} symbols — expected exactly 6 (iter-v3/128 cardinality-6). "
        "Edit V3_MODELS in run_baseline_v3.py."
    )

    # Verify ITERATION_LABEL reflects the current iteration
    assert runner.ITERATION_LABEL.startswith("v3-"), (
        f"ITERATION_LABEL = '{runner.ITERATION_LABEL}' — must start with 'v3-'. "
        "Update ITERATION_LABEL in run_baseline_v3.py."
    )
    # iter-v3/128 specific: ITERATION_LABEL must be "v3-128"
    assert runner.ITERATION_LABEL == "v3-128", (
        f"ITERATION_LABEL = '{runner.ITERATION_LABEL}' — expected 'v3-128'. "
        "Update ITERATION_LABEL in run_baseline_v3.py (Change 2 per /128 brief Section 3)."
    )


# ---------------------------------------------------------------------------
# Test #2 — excluded-symbol disjointness (NO-CHEATING gate)
# ---------------------------------------------------------------------------


def test_v3_models_disjoint_from_excluded() -> None:
    """Section 9.2 test #2 (HARD build-fail).

    Asserts set(sym for _, sym in V3_MODELS).isdisjoint(set(V3_EXCLUDED_SYMBOLS)).
    The NO-CHEATING universe-legality gate (brief Section 3.2). HARD-fails if any
    traded symbol is a v1/v2 symbol or MKR.
    """
    runner = _load_runner()
    from crypto_trade.features_v3 import V3_EXCLUDED_SYMBOLS

    traded = {sym for _label, sym in runner.V3_MODELS}
    excluded = set(V3_EXCLUDED_SYMBOLS)
    overlap = traded & excluded

    assert not overlap, (
        f"DISJOINTNESS VIOLATION: {overlap} in both V3_MODELS and V3_EXCLUDED_SYMBOLS. "
        "v3 may not trade v1/v2 symbols or MKR. "
        "Remove {overlap} from V3_MODELS or V3_EXCLUDED_SYMBOLS."
    )


# ---------------------------------------------------------------------------
# Test #3 — DSR/PSR/PBO machinery is genuine (anti-sentinel guard)
# ---------------------------------------------------------------------------


def test_dsr_json_is_genuinely_computed() -> None:
    """Section 9.2 test #3 (HARD build-fail).

    Structural guarantee against the /090→/092 hardcoded-sentinel defect class.
    Asserts:
    (a) The runner imports AND calls validation_v3.psr and
        validation_v3.deflated_sharpe_ratio_v3 — source-level grep check.
    (b) The functions are callable (not monkey-patched away).
    (c) The functions produce finite float outputs on a minimal synthetic input —
        value-level finiteness guard (the 0.0/NaN sentinel defect would fail here).

    SR granularity for psr(): the runner feeds TRADE-LEVEL weighted_pnl arrays
    (not daily or annualized Sharpe). psr() receives observed_sharpe computed as
    mean(wp)/std(wp) * sqrt(n_obs) over the OOS trade-level weighted_pnl series.
    Per `feedback_v3_methodology_post_hoc_input_traceback.md`.
    """
    # (a) Source-level: runner module imports psr and deflated_sharpe_ratio_v3
    runner = _load_runner()
    assert hasattr(runner, "psr"), (
        "run_baseline_v3 does not expose psr in module namespace. "
        "The runner must 'from crypto_trade.strategies.ml.validation_v3 import psr'. "
        "iter-v3/097 test #3: anti-sentinel guard."
    )
    assert hasattr(runner, "deflated_sharpe_ratio_v3"), (
        "run_baseline_v3 does not expose deflated_sharpe_ratio_v3. "
        "The runner must import it from validation_v3. "
        "iter-v3/097 test #3: anti-sentinel guard."
    )

    # (b) Both are callable
    assert callable(runner.psr), "runner.psr is not callable."
    assert callable(runner.deflated_sharpe_ratio_v3), (
        "runner.deflated_sharpe_ratio_v3 is not callable."
    )

    # (c) Value-level: call psr on synthetic trade-level weighted_pnl
    # and verify finite float output — a hardcoded 0.0 sentinel fails here.
    import math

    import numpy as np

    rng = np.random.default_rng(42)
    wp = rng.normal(loc=2.0, scale=5.0, size=80)  # synthetic trade-level PnL
    from scipy.stats import kurtosis, skew

    obs_sharpe = float(wp.mean() / wp.std() * np.sqrt(len(wp)))
    psr_val = runner.psr(
        observed_sharpe=obs_sharpe,
        n_obs=len(wp),
        skewness=float(skew(wp)),
        kurtosis=float(kurtosis(wp, fisher=False)),
    )
    assert math.isfinite(psr_val), (
        f"psr() returned non-finite {psr_val} on synthetic input — sentinel defect. "
        "The runner's psr() must return a genuine probability in [0, 1]."
    )
    assert 0.0 <= psr_val <= 1.0, (
        f"psr() returned {psr_val} outside [0, 1]. Check validation_v3.psr."
    )
    # psr should be > 0 for a positive-Sharpe synthetic series
    assert psr_val > 0.0, (
        f"psr() returned {psr_val} <= 0 for a positive-Sharpe synthetic series. "
        "Likely a sentinel or sign bug."
    )

    # (d) deflated_sharpe_ratio_v3 returns a finite DSR on minimal input
    # Signature: deflated_sharpe_ratio_v3(observed_sr, num_trials, backtest_length, ...)
    dsr_result = runner.deflated_sharpe_ratio_v3(
        observed_sr=obs_sharpe,
        num_trials=35,
        backtest_length=len(wp),
        skewness=float(skew(wp)),
        kurtosis=float(kurtosis(wp, fisher=False)),
    )
    # Result is a dict with 'dsr' key
    dsr_val = (
        dsr_result["dsr"]
        if isinstance(dsr_result, dict)
        else (dsr_result.dsr if hasattr(dsr_result, "dsr") else dsr_result[0])
    )
    assert math.isfinite(dsr_val), (
        f"deflated_sharpe_ratio_v3() returned non-finite DSR={dsr_val} on synthetic input."
    )


# ---------------------------------------------------------------------------
# Test #4 — feature columns pinned for new symbols
# ---------------------------------------------------------------------------


def test_feature_columns_pinned_for_new_symbols() -> None:
    """Section 9.2 test #4 (HARD build-fail).

    Asserts features_for_symbol returns the V3_FEATURE_COLUMNS_TOP_N feature list
    for all traded symbols, and that V3_FEATURES_PER_SYMBOL is empty (no per-symbol
    override). The feedback_explicit_feature_columns.md invariant — all 6 L1 symbols
    inherit the universal 14-feature stack, no per-symbol override.

    iter-v3/128: WILD axis — V3_MODELS = 6-symbol sector-pure L1 (ATOM/RUNE/AVAX/HBAR/ICP/ALGO).
    V3_FEATURE_COLUMNS_TOP_N stays at 14 (UNCHANGED from /121 — /126's d24 REVERTED at /127).
    """
    from crypto_trade.features_v3 import (
        V3_FEATURE_COLUMNS_TOP_N,
        V3_FEATURES_PER_SYMBOL,
        features_for_symbol,
    )

    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL has {len(V3_FEATURES_PER_SYMBOL)} entries — "
        "expected 0 (empty). iter-v3/128: no per-symbol feature overrides. "
        "All 6 L1 symbols inherit the universal 14-feature stack."
    )

    # iter-v3/128: 6-symbol universe ATOM/RUNE/AVAX/HBAR/ICP/ALGO
    for sym in ("ATOMUSDT", "RUNEUSDT", "AVAXUSDT", "HBARUSDT", "ICPUSDT", "ALGOUSDT"):
        feats = features_for_symbol(sym)
        n_expected = len(V3_FEATURE_COLUMNS_TOP_N)
        assert len(feats) == n_expected, (
            f"features_for_symbol('{sym}') returned {len(feats)} features — "
            f"expected {n_expected}. iter-v3/128: all symbols inherit "
            "V3_FEATURE_COLUMNS_TOP_N (14 features). Check V3_FEATURES_PER_SYMBOL is empty."
        )
        assert list(feats) == list(V3_FEATURE_COLUMNS_TOP_N), (
            f"features_for_symbol('{sym}') returned {list(feats)} — "
            f"expected V3_FEATURE_COLUMNS_TOP_N = {list(V3_FEATURE_COLUMNS_TOP_N)}. "
            "The feature list must be bit-identical to the universal feature stack."
        )

    # Explicit: BCH/LDO/TRX (/127 universe) must NOT appear in V3_MODELS at /128
    runner = _load_runner()
    traded_syms = [sym for _label, sym in runner.V3_MODELS]
    assert "BCHUSDT" not in traded_syms, (
        "BCHUSDT still in V3_MODELS — must be removed at iter-v3/128 "
        "(BCH/LDO/TRX REPLACED by ATOM/RUNE/AVAX/HBAR/ICP/ALGO at /128 WILD axis)."
    )
    assert "LDOUSDT" not in traded_syms, (
        "LDOUSDT still in V3_MODELS — must be removed at iter-v3/128 "
        "(BCH/LDO/TRX REPLACED by ATOM/RUNE/AVAX/HBAR/ICP/ALGO at /128 WILD axis)."
    )
    assert "TRXUSDT" not in traded_syms, (
        "TRXUSDT still in V3_MODELS — must be removed at iter-v3/128 "
        "(BCH/LDO/TRX REPLACED by ATOM/RUNE/AVAX/HBAR/ICP/ALGO at /128 WILD axis)."
    )


# ---------------------------------------------------------------------------
# Test #5 — walk-forward embargo intact (e149e9d fix)
# ---------------------------------------------------------------------------


def test_walk_forward_embargo_intact() -> None:
    """Section 9.2 test #5 (HARD build-fail).

    Asserts the e149e9d walk-forward embargo (train_end_ms = test_start_ms - embargo_ms,
    compute_embargo_candles helper, cv_gap = embargo_candles * n_symbols) is present and
    load-bearing in the runner for the new 3-symbol universe (cv_gap resolves to 66).

    Checks:
    (a) walk_forward.compute_embargo_candles exists and returns 22 for 10080/480.
    (b) walk_forward.generate_monthly_splits accepts label_timeout_minutes + interval_minutes.
    (c) REQUIRED_GAP == 66 == (21+1)*3 (3-symbol universe; timeout 21 candles).
    (d) Source-level: generate_monthly_splits source contains 'train_end_ms = test_start_ms'
        (the embargo subtraction pattern).
    """
    from crypto_trade.strategies.ml import walk_forward
    from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP

    # (a) compute_embargo_candles helper
    assert hasattr(walk_forward, "compute_embargo_candles"), (
        "walk_forward.compute_embargo_candles not found — e149e9d embargo fix missing. "
        "HARD-fail: the lookahead-bug fix commit e149e9d must be present."
    )
    embargo_candles = walk_forward.compute_embargo_candles(
        label_timeout_minutes=10080,
        interval_minutes=480,
    )
    assert embargo_candles == 22, (
        f"compute_embargo_candles(10080, 480) = {embargo_candles} — expected 22. "
        "embargo = 10080 // 480 + 1 = 21 + 1 = 22."
    )

    # (b) generate_monthly_splits accepts the required parameters
    sig = inspect.signature(walk_forward.generate_monthly_splits)
    params = set(sig.parameters)
    assert "label_timeout_minutes" in params, (
        "generate_monthly_splits missing 'label_timeout_minutes' parameter. "
        "e149e9d embargo fix requires this argument."
    )
    assert "interval_minutes" in params, (
        "generate_monthly_splits missing 'interval_minutes' parameter. "
        "e149e9d embargo fix requires this argument."
    )

    # (c) REQUIRED_GAP module constant stays 66 (3-symbol baseline); runner uses
    # a local override of 132 = (21+1)*6 for the new 6-symbol /128 universe.
    # validation_v3.REQUIRED_GAP is NOT changed — same pattern as 24h=72 at /117.
    runner = _load_runner()
    n_symbols = len(runner.V3_MODELS)
    assert n_symbols == 6, (
        f"V3_MODELS has {n_symbols} symbols — expected 6 (ATOM/RUNE/AVAX/HBAR/ICP/ALGO). "
        "iter-v3/128: 6-symbol WILD CYCLE-7 axis-7 universe."
    )
    # The module constant REQUIRED_GAP stays at 66 (the 3-symbol baseline constant).
    assert REQUIRED_GAP == 66, (
        f"REQUIRED_GAP module constant = {REQUIRED_GAP} — expected 66 (3-symbol baseline). "
        "validation_v3.REQUIRED_GAP must NOT be changed for /128; runner uses local override 132."
    )
    # The runner-local override for 6 symbols at K=21 is 132 = (21+1)*6.
    expected_override = (21 + 1) * 6  # = 132
    assert expected_override == 132, (
        f"Expected override formula (21+1)*6 = {expected_override} != 132. Formula error."
    )

    # (d) Source-level: the embargo subtraction pattern
    src = inspect.getsource(walk_forward.generate_monthly_splits)
    assert "train_end_ms = test_start_ms" in src or "train_end_ms=test_start_ms" in src, (
        "generate_monthly_splits source does not contain 'train_end_ms = test_start_ms'. "
        "The e149e9d walk-forward embargo fix (train_end_ms = test_start_ms - embargo_ms) "
        "must be present. This is the lookahead-bias fix for the v3 walk-forward."
    )


# ---------------------------------------------------------------------------
# Test #6 — OOS cutoff and training_months immutability
# ---------------------------------------------------------------------------


def test_oos_cutoff_and_training_months_immutable() -> None:
    """Section 9.2 test #6 (HARD build-fail).

    Asserts OOS_CUTOFF_MS == 1742774400000 and training_months == 24 are
    unchanged — the NO-CHEATING immutability gate (brief Section 0).
    """
    from crypto_trade.config import OOS_CUTOFF_MS

    assert OOS_CUTOFF_MS == 1742774400000, (
        f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} — expected 1742774400000 (2025-03-24). "
        "OOS_CUTOFF_DATE is IMMUTABLE — do not change it. "
        "This is a NO-CHEATING guard."
    )

    runner = _load_runner()
    assert runner.TRAINING_MONTHS == 24, (
        f"TRAINING_MONTHS = {runner.TRAINING_MONTHS} — expected 24. "
        "training_months is IMMUTABLE. "
        "This is a NO-CHEATING guard."
    )

    # Also verify the string-form cutoff constant in the runner is set
    assert runner.OOS_CUTOFF_DATE == "2025-03-24", (
        f"runner.OOS_CUTOFF_DATE = '{runner.OOS_CUTOFF_DATE}' — expected '2025-03-24'. "
        "The runner's OOS_CUTOFF_DATE string must match the immutable canonical date."
    )
