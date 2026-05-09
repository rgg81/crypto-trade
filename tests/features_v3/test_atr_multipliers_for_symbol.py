"""Adversarial tests for per-symbol ATR multipliers — iter-v3/040.

iter-v3/040 state (EXPLORATION — cycle 3 #1 — REVERT all per-symbol ATR customizations):
  - V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (cleared at iter-v3/040).
  - All symbols fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via atr_multipliers_for_symbol.
  - LDOUSDT: returns (2.0, 1.0) via default fallback (was (1.5, 0.75) at iter-v3/032-039).
  - Architecture (dict + helper) KEPT; only dict contents emptied.

iter-v3/032 EDA context (preserved for reference):
  LDOUSDT natr_21_raw median 5.01 vs peer median 3.70 (1.35× higher).
  At (2.0, 1.0) multipliers: LDO TP barrier = 10.01%, SL = 5.01%.
  (1.5, 0.75) was introduced to align LDO barriers with peer aggregate.
  Reverted at iter-v3/040 to test whether the LDO ATR customization contributed
  to the IS degradation observed at iter-v3/039 CONFIRMATION NO-MERGE.

Validates:
  1. All symbols fall back to (2.0, 1.0) (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
  2. LDOUSDT returns (2.0, 1.0) — NOT the iter-v3/032 (1.5, 0.75).
  3. The runner's _build_v3_model dispatches default multipliers for all symbols.
  4. V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (0 entries).
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """All symbols fall back to (2.0, 1.0) at iter-v3/040.

    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (cleared in cycle 3 REVERT EXPLORATION).
    DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) applies to all symbols via fallback.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)
    # LDO also returns default at iter-v3/040 (REVERTED from iter-v3/032 (1.5, 0.75)).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0), (
        "LDOUSDT must return (2.0, 1.0) at iter-v3/040 (V3_ATR_MULTIPLIERS_PER_SYMBOL empty). "
        "iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL CLEARED (cycle 3 REVERT EXPLORATION). "
        "LDO reverts to DEFAULT_ATR_MULTIPLIERS fallback."
    )


def test_atr_multipliers_ldo_reverted():
    """LDO must return DEFAULT (2.0, 1.0) — NOT (1.5, 0.75) — at iter-v3/040.

    iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty. LDOUSDT per-symbol entry
    (1.5, 0.75) CLEARED (was added at iter-v3/032; reverted at iter-v3/040).
    LDO uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback.

    Reverts wider barrier (LDO TP: ~10% → ~13.4% at natr_21_raw median 6.68%).
    Expected effect: fewer LDO trades (wider barriers harder to reach).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL CLEARED (cycle 3 REVERT). "
        f"LDO must use (2.0, 1.0) default. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_result = atr_multipliers_for_symbol("LDOUSDT")
    assert ldo_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (2.0, 1.0). "
        f"iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; LDO must use default. "
        f"Verify V3_ATR_MULTIPLIERS_PER_SYMBOL == {{}} in features_v3/__init__.py."
    )
    assert ldo_result != (1.5, 0.75), (
        "atr_multipliers_for_symbol('LDOUSDT') returned (1.5, 0.75) — must be REVERTED. "
        "iter-v3/040: LDO per-symbol ATR entry cleared (cycle 3 REVERT). "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/040."
    )


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty (0 entries) at iter-v3/040.

    iter-v3/040: cycle 3 EXPLORATION #1 — REVERT all per-symbol ATR customizations.
    LDO entry (1.5, 0.75) cleared. All symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/040 (cycle 3 REVERT). "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies default (2.0, 1.0) for ALL symbols at iter-v3/040."""
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
    # iter-v3/040: ALL symbols use default (2.0, 1.0) — V3_ATR_MULTIPLIERS_PER_SYMBOL is empty.
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/040: BCH uses default multipliers (V3_ATR_MULTIPLIERS_PER_SYMBOL empty)."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.0, (
        f"BCH atr_sl_multiplier: expected 1.0, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/040: BCH uses default multipliers."
    )
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/040: LDO reverts to default (2.0, 1.0) — per-symbol entry CLEARED."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.0, (
        f"LDO atr_sl_multiplier: expected 1.0, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/040: LDO reverts to default (2.0, 1.0) — per-symbol entry CLEARED."
    )
