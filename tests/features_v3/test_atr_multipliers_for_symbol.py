"""Adversarial tests for per-symbol ATR multipliers — iter-v3/042.

iter-v3/042 state (EXPLORATION — cycle 3 #3 — REVERT pruning + universal ATR (1.5, 0.75)):
  - DEFAULT_ATR_MULTIPLIERS CHANGED from (2.0, 1.0) → (1.5, 0.75) at iter-v3/042.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (unchanged from iter-v3/040).
  - ALL symbols (BCH/LDO/TRX/ALGO) fall back to DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75).
  - Architecture (dict + helper) KEPT; only DEFAULT changed.
  - Single-axis change: DEFAULT_ATR_MULTIPLIERS change is the new variation.
    Feature revert (11→14) is the mandatory pre-commit per iter-v3/041 Path C mandate.

iter-v3/032 EDA context (preserved for reference):
  LDOUSDT natr_21_raw median 5.01 vs peer median 3.70 (1.35× higher).
  At (2.0, 1.0) multipliers: LDO TP barrier = 10.01%, SL = 5.01%.
  (1.5, 0.75) aligns LDO barriers with peer aggregate at iter-v3/032.
  iter-v3/042 EXPLORATION: tests whether same (1.5, 0.75) works universally
  for ALL 4 symbols (BCH/LDO/TRX/ALGO), not just LDO.

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75) (CHANGED from (2.0, 1.0) at iter-v3/042).
  2. All symbols fall back to (1.5, 0.75) (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
  3. LDOUSDT returns (1.5, 0.75) — via DEFAULT (NOT via per-symbol entry).
  4. BCHUSDT returns (1.5, 0.75) — via DEFAULT (new vs iter-v3/040).
  5. V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (0 entries).
  6. The runner's _build_v3_model dispatches (1.5, 0.75) for all symbols.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75) at iter-v3/042.

    iter-v3/042: DEFAULT changed from (2.0, 1.0) to (1.5, 0.75).
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — all symbols use DEFAULT via fallback.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (1.5, 0.75). "
        "iter-v3/042: DEFAULT changed from (2.0, 1.0) to (1.5, 0.75). "
        "Verify in features_v3/__init__.py."
    )
    assert atr_multipliers_for_symbol("BCHUSDT") == (1.5, 0.75)
    assert atr_multipliers_for_symbol("TRXUSDT") == (1.5, 0.75)
    assert atr_multipliers_for_symbol("ALGOUSDT") == (1.5, 0.75)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (1.5, 0.75)
    # LDO also returns (1.5, 0.75) via DEFAULT at iter-v3/042.
    # At iter-v3/032, LDO had (1.5, 0.75) via per-symbol entry.
    # At iter-v3/040/041, LDO returned (2.0, 1.0) via DEFAULT (old default).
    # At iter-v3/042, LDO returns (1.5, 0.75) via DEFAULT (new default).
    assert atr_multipliers_for_symbol("LDOUSDT") == (1.5, 0.75), (
        "LDOUSDT must return (1.5, 0.75) at iter-v3/042 (DEFAULT_ATR_MULTIPLIERS changed). "
        "iter-v3/042: DEFAULT changed from (2.0, 1.0) to (1.5, 0.75). "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — LDO uses DEFAULT fallback."
    )


def test_atr_multipliers_ldo_universal_tighter():
    """LDO must return (1.5, 0.75) — via DEFAULT, NOT per-symbol — at iter-v3/042.

    iter-v3/040/041: LDO returned (2.0, 1.0) via DEFAULT (empty per-symbol dict).
    iter-v3/042: DEFAULT changed to (1.5, 0.75); LDO still uses DEFAULT fallback.
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — LDO has no per-symbol entry.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/042. "
        f"LDO must use DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75) fallback (no per-symbol entry). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_result = atr_multipliers_for_symbol("LDOUSDT")
    assert ldo_result == (1.5, 0.75), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (1.5, 0.75). "
        f"iter-v3/042: DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75); LDO uses DEFAULT fallback."
    )


def test_atr_multipliers_bch_universal_tighter():
    """BCH must return (1.5, 0.75) via DEFAULT at iter-v3/042.

    BCH has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
    DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75) at iter-v3/042.
    """
    from crypto_trade.features_v3 import atr_multipliers_for_symbol

    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (1.5, 0.75), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (1.5, 0.75). "
        f"iter-v3/042: DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75); BCH uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty (0 entries) at iter-v3/042.

    iter-v3/040: cycle 3 EXPLORATION #1 — REVERT all per-symbol ATR customizations.
    iter-v3/041/042: dict remains empty. DEFAULT changed at iter-v3/042 only.
    All symbols use DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/042. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies (1.5, 0.75) for ALL symbols at iter-v3/042 (universal DEFAULT)."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from run_baseline_v3 import _build_v3_model

    _cfg_bch, strat_bch = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    _cfg_ldo, strat_ldo = _build_v3_model(
        symbol="LDOUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    # iter-v3/042: ALL symbols use DEFAULT (1.5, 0.75).
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 1.5, (
        f"BCH atr_tp_multiplier: expected 1.5, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/042: BCH uses DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75)."
    )
    assert strat_bch.inner.atr_sl_multiplier == 0.75, (
        f"BCH atr_sl_multiplier: expected 0.75, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/042: BCH uses DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75)."
    )
    assert strat_ldo.inner.atr_tp_multiplier == 1.5, (
        f"LDO atr_tp_multiplier: expected 1.5, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/042: LDO uses DEFAULT (1.5, 0.75) via empty per-symbol dict."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 0.75, (
        f"LDO atr_sl_multiplier: expected 0.75, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/042: LDO uses DEFAULT (1.5, 0.75) via empty per-symbol dict."
    )
