"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/031/034.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/031 update: LDOUSDT dropped from V3_MODELS (9-of-9 OOS-negative;
PROMISING-MECHANICAL per iter-v3/013 precedent). V3_FEATURES_PER_SYMBOL is
now empty. Tests updated accordingly:

- LDO now falls back to V3_FEATURE_COLUMNS_TOP_N (same as BCH/TRX/ALGO).
- V3_FEATURES_PER_SYMBOL must be empty (no per-symbol overrides active).
- Architecture preserved: fallback path works for all symbols.

iter-v3/034 update: fracdiff_d05_close ADDED (14→15 features).
V3_FEATURE_COLUMNS_TOP_N now has 15 entries. All count assertions updated.

Three core mandatory cases (inherited from iter-v3/030 brief §3 sub-fix #5
and §10 adversarial test specification, updated for iter-v3/031/034):

1. ``test_features_for_symbol_subset_invariant`` — every per-symbol subset is a
   strict subset of ``V3_FEATURE_COLUMNS_TOP_N``.  Trivially passes when dict is empty.

2. ``test_features_for_symbol_fallback`` — symbols not in ``V3_FEATURES_PER_SYMBOL``
   fall back to exactly ``V3_FEATURE_COLUMNS_TOP_N`` (tuple identity check).  Covers
   BCH, TRX, ALGO, LDO, and any unknown symbol.

3. ``test_v3_features_per_symbol_is_empty`` — V3_FEATURES_PER_SYMBOL must be empty
   at iter-v3/031 (LDO entry cleared per brief §3 sub-fix #3).
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v3 import (
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    features_for_symbol,
)


def test_features_for_symbol_subset_invariant() -> None:
    """Every per-symbol subset must be a strict subset of V3_FEATURE_COLUMNS_TOP_N.

    Trivially passes at iter-v3/031 when dict is empty. Preserved as a guard
    for future per-symbol entries.
    """
    full = set(V3_FEATURE_COLUMNS_TOP_N)
    for sym, subset in V3_FEATURES_PER_SYMBOL.items():
        extra = set(subset) - full
        assert not extra, (
            f"{sym}: features {sorted(extra)} are in V3_FEATURES_PER_SYMBOL['{sym}'] "
            f"but NOT in V3_FEATURE_COLUMNS_TOP_N. "
            f"Per-symbol subsets must be strict subsets of V3_FEATURE_COLUMNS_TOP_N."
        )


def test_features_for_symbol_fallback() -> None:
    """Symbols not in V3_FEATURES_PER_SYMBOL fall back to V3_FEATURE_COLUMNS_TOP_N.

    iter-v3/031: ALL active symbols (BCH, TRX, ALGO) and dropped symbol (LDO) fall back.
    iter-v3/034: V3_FEATURE_COLUMNS_TOP_N now has 15 features (fracdiff_d05_close added).
    """
    for symbol in ["BCHUSDT", "TRXUSDT", "ALGOUSDT", "LDOUSDT"]:
        result = features_for_symbol(symbol)
        assert result == V3_FEATURE_COLUMNS_TOP_N, (
            f"{symbol} should fall back to V3_FEATURE_COLUMNS_TOP_N (15 features) — "
            f"V3_FEATURES_PER_SYMBOL is empty at iter-v3/031/034."
        )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be empty at iter-v3/031.

    LDOUSDT entry cleared per iter-v3/031 brief §3 sub-fix #3 (LDO dropped from
    V3_MODELS; 9-of-9 OOS-negative; PROMISING-MECHANICAL per iter-v3/013 precedent).
    Architecture preserved: dict exists and helper function works.
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/031. "
        f"Got: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"LDOUSDT was cleared per iter-v3/031 brief §3 sub-fix #3."
    )


def test_features_for_symbol_ldo_fallback() -> None:
    """LDOUSDT falls back to V3_FEATURE_COLUMNS_TOP_N (15 features) at iter-v3/034.

    iter-v3/030: LDO had a 7-feature per-symbol subset.
    iter-v3/031: LDO dropped from V3_MODELS; V3_FEATURES_PER_SYMBOL cleared;
                 LDO now falls back to V3_FEATURE_COLUMNS_TOP_N (14 features).
    iter-v3/034: fracdiff_d05_close ADDED; V3_FEATURE_COLUMNS_TOP_N has 15 features.
    """
    result = features_for_symbol("LDOUSDT")
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT should fall back to V3_FEATURE_COLUMNS_TOP_N (15 features) at iter-v3/034. "
        f"Got {len(result)} features. "
        f"LDO was dropped from V3_MODELS; per-symbol entry cleared."
    )
    assert len(result) == 15, f"LDOUSDT fallback must have exactly 15 features. Got {len(result)}."


def test_features_for_symbol_unknown_symbol() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (never None, never empty)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) > 0, "features_for_symbol must never return an empty tuple."
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "TRXUSDT", "ALGOUSDT"])
def test_fallback_symbols_have_15_features(symbol: str) -> None:
    """BCH, TRX, ALGO must each receive the full 15-feature set via fallback.

    iter-v3/034: fracdiff_d05_close ADDED (14→15). Count updated from 14.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 15, (
        f"{symbol}: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback, "
        f"iter-v3/034 fracdiff_d05_close added), got {len(result)}."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "TRXUSDT", "ALGOUSDT"])
def test_fallback_symbols_include_regime_momentum(symbol: str) -> None:
    """BCH, TRX, ALGO must each include regime_momentum_signed_5d via fallback.

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md.
    """
    result = features_for_symbol(symbol)
    assert "regime_momentum_signed_5d" in result, (
        f"{symbol}: regime_momentum_signed_5d MISSING from feature set. "
        f"Portfolio-level mandate requires BCH+TRX+ALGO to use this feature. "
        f"feedback_v3_engineered_features_proven.md."
    )
