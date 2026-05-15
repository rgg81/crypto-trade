"""iter-v3/073 — adversarial tests for per-symbol triple-barrier asymmetry.

CYCLE 2 EXPLORATION #3. The single varied axis is V3_ATR_MULTIPLIERS_PER_SYMBOL:
BCH (2.0, 1.25), LDO (1.5, 1.25); TRX falls back to DEFAULT_ATR_MULTIPLIERS.

These tests pin the per-symbol multiplier wiring so a future regression that
silently mutates the dict or the fallback path is caught.
"""

from __future__ import annotations

from crypto_trade.features_v3 import (
    DEFAULT_ATR_MULTIPLIERS,
    V3_ATR_MULTIPLIERS_PER_SYMBOL,
    atr_multipliers_for_symbol,
)


def test_bch_per_symbol_multipliers() -> None:
    """BCH must resolve to the iter-v3/073 recalibrated pair (2.0, 1.25)."""
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.25)


def test_ldo_per_symbol_multipliers() -> None:
    """LDO must resolve to the iter-v3/073 recalibrated pair (1.5, 1.25)."""
    assert atr_multipliers_for_symbol("LDOUSDT") == (1.5, 1.25)


def test_trx_falls_back_to_default() -> None:
    """TRX is NOT in the dict — it must fall back to DEFAULT_ATR_MULTIPLIERS.

    The EDA keep-decision: TRX's eligible-grid optimum did not beat the current
    global pair, so TRX is deliberately left at the default (2.0, 1.0).
    """
    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert atr_multipliers_for_symbol("TRXUSDT") == DEFAULT_ATR_MULTIPLIERS
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)


def test_unknown_symbol_falls_back_to_default() -> None:
    """Any symbol not in the dict resolves to DEFAULT_ATR_MULTIPLIERS."""
    assert atr_multipliers_for_symbol("NOTASYMBOLUSDT") == DEFAULT_ATR_MULTIPLIERS


def test_dict_has_exactly_two_keys() -> None:
    """iter-v3/073 recalibrates exactly 2 of 3 v3 symbols (BCH, LDO)."""
    assert set(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys()) == {"BCHUSDT", "LDOUSDT"}


def test_recalibration_widens_sl_vs_default() -> None:
    """Both recalibrated symbols widen the SL multiplier vs the global default.

    The EDA rationale: the global (2.0, 1.0) pair is SL-saturated (66% SL-hit);
    a wider SL rebalances the barrier toward TP-hits. This test documents the
    SL-widening direction explicitly (the regime-exposure caveat is pre-registered
    in the brief Section 4.4 SUSPICIOUS gate).
    """
    _, default_sl = DEFAULT_ATR_MULTIPLIERS
    for sym in ("BCHUSDT", "LDOUSDT"):
        _, sl = atr_multipliers_for_symbol(sym)
        assert sl > default_sl, f"{sym} SL {sl} should exceed default {default_sl}"
