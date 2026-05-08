"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/030.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.  Three mandatory cases (from brief §3 sub-fix #5
and §10 adversarial test specification):

1. ``test_features_for_symbol_subset_invariant`` — every per-symbol subset is a
   strict subset of ``V3_FEATURE_COLUMNS_TOP_N``.  Catches LDO-subset drift where
   a feature is added to ``V3_FEATURES_PER_SYMBOL['LDOUSDT']`` that was not first
   added to ``V3_FEATURE_COLUMNS_TOP_N``.

2. ``test_features_for_symbol_fallback`` — symbols not in ``V3_FEATURES_PER_SYMBOL``
   fall back to exactly ``V3_FEATURE_COLUMNS_TOP_N`` (tuple identity check).  Covers
   BCH, TRX, ALGO, and any unknown symbol.  Catches a dispatch-path bug where the
   fallback path resolves to a different object (e.g., ``V3_FEATURE_COLUMNS_FULL``
   or an empty tuple).

3. ``test_features_for_symbol_ldo`` — LDOUSDT returns the canonical iter-v3/028
   multi-seed top-7 feature set.  Catches LDO-config drift where the subset is
   silently updated without updating the brief.

Additional safety cases:

4. ``test_features_for_symbol_ldo_count`` — LDO tuple has exactly 7 elements.
5. ``test_features_for_symbol_unknown_symbol`` — arbitrary unknown symbol falls
   back to ``V3_FEATURE_COLUMNS_TOP_N`` (not None, not empty).
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v3 import (
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    features_for_symbol,
)


def test_features_for_symbol_subset_invariant() -> None:
    """Every per-symbol subset must be a strict subset of V3_FEATURE_COLUMNS_TOP_N."""
    full = set(V3_FEATURE_COLUMNS_TOP_N)
    for sym, subset in V3_FEATURES_PER_SYMBOL.items():
        extra = set(subset) - full
        assert not extra, (
            f"{sym}: features {sorted(extra)} are in V3_FEATURES_PER_SYMBOL['{sym}'] "
            f"but NOT in V3_FEATURE_COLUMNS_TOP_N. "
            f"Per-symbol subsets must be strict subsets of V3_FEATURE_COLUMNS_TOP_N."
        )


def test_features_for_symbol_fallback() -> None:
    """Symbols not in V3_FEATURES_PER_SYMBOL fall back to V3_FEATURE_COLUMNS_TOP_N."""
    assert features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N, (
        "BCHUSDT should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features) — "
        "not in V3_FEATURES_PER_SYMBOL."
    )
    assert features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N, (
        "TRXUSDT should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features) — "
        "not in V3_FEATURES_PER_SYMBOL."
    )
    assert features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N, (
        "ALGOUSDT should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features) — "
        "not in V3_FEATURES_PER_SYMBOL."
    )


def test_features_for_symbol_ldo() -> None:
    """LDOUSDT returns the canonical iter-v3/028 multi-seed top-7 feature set."""
    expected = {
        "ret_skew_200",
        "ret_kurt_50",
        "ret_kurt_200",
        "vwap_dev_20",
        "hurst_diff_100_50",
        "btc_ret_14d",
        "range_realized_vol_50",
    }
    result = features_for_symbol("LDOUSDT")
    assert set(result) == expected, (
        f"LDOUSDT feature set mismatch. "
        f"Expected: {sorted(expected)}. "
        f"Got: {sorted(result)}. "
        f"Source: analysis/iteration_v3-030/ldo_feature_subset_analysis.py (SHA 36aaacd)."
    )


def test_features_for_symbol_ldo_count() -> None:
    """LDOUSDT tuple has exactly 7 elements (iter-v3/030 brief §1 + §2.1)."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 7, (
        f"LDOUSDT feature count is {len(result)}, expected 7. "
        f"iter-v3/030: top-7 by iter-v3/028 multi-seed IS importance."
    )


def test_features_for_symbol_unknown_symbol() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (never None, never empty)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) > 0, "features_for_symbol must never return an empty tuple."
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N."
    )


def test_v3_features_per_symbol_has_ldo() -> None:
    """V3_FEATURES_PER_SYMBOL must contain LDOUSDT (iter-v3/030 single entry)."""
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL must contain 'LDOUSDT'. iter-v3/030 brief §3 sub-fix #1."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "TRXUSDT", "ALGOUSDT"])
def test_fallback_symbols_have_14_features(symbol: str) -> None:
    """BCH, TRX, ALGO must each receive the full 14-feature set via fallback."""
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "TRXUSDT", "ALGOUSDT"])
def test_fallback_symbols_include_regime_momentum(symbol: str) -> None:
    """BCH, TRX, ALGO must each include regime_momentum_signed_5d via fallback.

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md.
    LDO is the only symbol permitted to omit this feature (rank 13/14 at
    iter-v3/028 multi-seed; per-symbol prescriptive override; iter-v3/030 brief §2.2).
    """
    result = features_for_symbol(symbol)
    assert "regime_momentum_signed_5d" in result, (
        f"{symbol}: regime_momentum_signed_5d MISSING from feature set. "
        f"Portfolio-level mandate requires BCH+TRX+ALGO to use this feature. "
        f"feedback_v3_engineered_features_proven.md."
    )
