"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/035.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/035 state:
- BCHUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15 features.
- TRXUSDT, ALGOUSDT, LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features (no fracdiff).
- V3_FEATURES_PER_SYMBOL has exactly 1 entry (BCHUSDT).
- fracdiff_d05_close is BCH-ONLY; must NOT appear in TRX/ALGO/LDO feature sets.
- V3_FEATURE_COLUMNS_TOP_N has 14 features (fracdiff_d05_close removed from universal list).

Evidence from iter-v3/034 per-symbol OOS (BCH +37.98 wpnl swing from fracdiff;
TRX -20.11 / ALGO -8.24 / LDO -6.81 regressions when fracdiff applied universally).
Per-symbol targeting isolates BCH lift while restoring TRX/ALGO/LDO anchor.

Mandatory test cases (iter-v3/035 brief Section 3 sub-fix #7):
1. test_bch_has_fracdiff
2. test_trx_no_fracdiff
3. test_ldo_no_fracdiff
4. test_algo_no_fracdiff
5. test_bch_per_symbol_entry_has_fracdiff
6. test_non_bch_fallback_no_fracdiff (parametrized TRX/ALGO/LDO)
7. test_bch_per_symbol_len
8. test_non_bch_fallback_len (parametrized TRX/ALGO/LDO)
9. test_subset_invariant_extended
10. test_v3_features_per_symbol_has_one_entry
11. test_regime_momentum_in_universal_list
12. test_fracdiff_not_in_universal_list
13. test_universal_list_is_14
14. test_features_for_symbol_unknown_fallback
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v3 import (
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    features_for_symbol,
)


def test_bch_has_fracdiff() -> None:
    """BCHUSDT must return 15 features including fracdiff_d05_close.

    iter-v3/035: BCH per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 15, (
        f"BCHUSDT: expected 15 features (BCH per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT'] should be V3_FEATURE_COLUMNS_TOP_N + fracdiff."
    )
    assert "fracdiff_d05_close" in result, (
        f"BCHUSDT: fracdiff_d05_close MISSING from feature set. "
        f"BCH is the sole beneficiary of fracdiff (iter-v3/034 +37.98 OOS wpnl swing). "
        f"Got: {result}"
    )


def test_trx_no_fracdiff() -> None:
    """TRXUSDT must return 14 features WITHOUT fracdiff_d05_close.

    iter-v3/034 showed TRX -20.11 OOS wpnl regression from universal fracdiff.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND in feature set — must be ABSENT. "
        f"fracdiff is BCH-only at iter-v3/035. Got: {result}"
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must return 14 features WITHOUT fracdiff_d05_close.

    iter-v3/034 showed LDO -6.81 OOS wpnl regression from universal fracdiff.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND in feature set — must be ABSENT. "
        f"fracdiff is BCH-only at iter-v3/035. Got: {result}"
    )


def test_algo_no_fracdiff() -> None:
    """ALGOUSDT must return 14 features WITHOUT fracdiff_d05_close.

    iter-v3/034 showed ALGO -8.24 OOS wpnl regression from universal fracdiff.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND in feature set — must be ABSENT. "
        f"fracdiff is BCH-only at iter-v3/035. Got: {result}"
    )


def test_bch_per_symbol_entry_has_fracdiff() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must contain fracdiff_d05_close.

    The dict entry is the source; features_for_symbol("BCHUSDT") returns this entry.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT' key — "
        "iter-v3/035: BCH must have a per-symbol entry. "
        "Check features_v3/__init__.py V3_FEATURES_PER_SYMBOL."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    assert "fracdiff_d05_close" in bch_entry, (
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT']: fracdiff_d05_close MISSING. "
        f"BCH entry must include fracdiff_d05_close. Got: {bch_entry}"
    )


@pytest.mark.parametrize("symbol", ["TRXUSDT", "ALGOUSDT", "LDOUSDT"])
def test_non_bch_fallback_no_fracdiff(symbol: str) -> None:
    """TRX/ALGO/LDO must NOT have fracdiff_d05_close (fallback path, no per-symbol entry).

    All three fall back to V3_FEATURE_COLUMNS_TOP_N which does not contain fracdiff.
    """
    result = features_for_symbol(symbol)
    assert "fracdiff_d05_close" not in result, (
        f"{symbol}: fracdiff_d05_close FOUND in feature set — must be ABSENT. "
        f"fracdiff is BCH-only at iter-v3/035 (BCH-only targeting via V3_FEATURES_PER_SYMBOL). "
        f"Got: {result}"
    )


def test_bch_per_symbol_len() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must have exactly 15 features.

    15 = 14 universal (V3_FEATURE_COLUMNS_TOP_N) + fracdiff_d05_close.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    assert len(bch_entry) == 15, (
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT']: expected 15 features, got {len(bch_entry)}. "
        f"BCH entry = V3_FEATURE_COLUMNS_TOP_N (14) + fracdiff_d05_close (1) = 15."
    )


@pytest.mark.parametrize("symbol", ["TRXUSDT", "ALGOUSDT", "LDOUSDT"])
def test_non_bch_fallback_len(symbol: str) -> None:
    """TRX/ALGO/LDO fallback must return exactly 14 features.

    iter-v3/035: V3_FEATURE_COLUMNS_TOP_N has 14 features (fracdiff removed from universal).
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURE_COLUMNS_TOP_N must have exactly 14 at iter-v3/035."
    )


def test_subset_invariant_extended() -> None:
    """BCH entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/035: BCH entry EXTENDS (not reduces) the universal list. The extension feature
    (fracdiff_d05_close) is already computed in the parquet for all symbols by
    add_engineered_v3_features; only the feature_columns= passed to LightGBM differs.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    expected = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
    assert set(bch_entry) == set(expected), (
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT'] content mismatch. "
        f"Expected V3_FEATURE_COLUMNS_TOP_N + ('fracdiff_d05_close',). "
        f"Extra in BCH entry: {sorted(set(bch_entry) - set(expected))}. "
        f"Missing from BCH entry: {sorted(set(expected) - set(bch_entry))}."
    )


def test_v3_features_per_symbol_has_one_entry() -> None:
    """V3_FEATURES_PER_SYMBOL must have exactly 1 entry at iter-v3/035.

    The sole entry is BCHUSDT. TRX/ALGO/LDO use the fallback path.
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 1, (
        f"V3_FEATURES_PER_SYMBOL must have exactly 1 entry at iter-v3/035 (BCHUSDT only). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}."
    )
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 1 entry but it is not BCHUSDT. "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    BCH+TRX+ALGO+LDO (fallback path) ALL use regime_momentum_signed_5d.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS_TOP_N. "
        "Portfolio-level mandate requires all symbols to use this feature via fallback. "
        "feedback_v3_engineered_features_proven.md. Do NOT revert."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/035: fracdiff_d05_close moved from universal list to BCH per-symbol only.
    Universal list has 14 features. BCH per-symbol has 15 (14 + fracdiff).
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/035: fracdiff_d05_close is in V3_FEATURES_PER_SYMBOL['BCHUSDT'] only. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/035.

    iter-v3/034 had 15 (fracdiff added). iter-v3/035 reverts to 14 (fracdiff to BCH-only).
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/035: fracdiff_d05_close moved to V3_FEATURES_PER_SYMBOL['BCHUSDT']; "
        f"universal list reverts to 14 (iter-v3/028/032 anchor). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (14 features, no fracdiff)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) > 0, "features_for_symbol must never return an empty tuple."
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features)."
    )
    assert "fracdiff_d05_close" not in result, (
        "Unknown symbol fallback must NOT include fracdiff_d05_close (BCH-only feature)."
    )
