"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/036.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/036 state:
- BCHUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15 features.
  UNCHANGED from iter-v3/035. fracdiff_d05_close PRESENT; vol_adj_autocorr ABSENT.
- TRXUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",) = 15 features.
  NEW at iter-v3/036. vol_adj_autocorr PRESENT; fracdiff_d05_close ABSENT.
- ALGOUSDT, LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
  NO fracdiff_d05_close. NO vol_adj_autocorr.
- V3_FEATURES_PER_SYMBOL has exactly 2 entries (BCHUSDT + TRXUSDT).
- BCH and TRX extension features are DISJOINT:
    BCH: fracdiff_d05_close (NOT vol_adj_autocorr)
    TRX: vol_adj_autocorr (NOT fracdiff_d05_close)
- V3_FEATURE_COLUMNS_TOP_N has 14 features (neither fracdiff_d05_close nor vol_adj_autocorr
  appear in the universal list).

Evidence:
- iter-v3/026: universal vol_adj_autocorr failed (IS Sharpe +0.0493; 27× IS/OOS ratio).
  Per-symbol isolation tests TRX-specific signal without cross-symbol contamination.
- iter-v3/034: fracdiff_d05_close universally failed for TRX (-20.11 OOS wpnl).
  BCH-only targeting (iter-v3/035) isolated BCH lift: PROMISING OOS +2.85.
- iter-v3/035: TRX at 52.2% OOS win rate, +29.24 OOS wpnl (anchor for TRX vol_adj_autocorr).
- Per-symbol architecture (iter-v3/030) provides isolation infrastructure.

Mandatory test cases (iter-v3/036 brief Section 3 sub-fix #5):
1. test_bch_has_fracdiff
2. test_bch_no_vol_adj_autocorr
3. test_trx_has_vol_adj_autocorr
4. test_trx_no_fracdiff
5. test_ldo_no_fracdiff_no_vol_adj
6. test_algo_no_fracdiff_no_vol_adj
7. test_bch_per_symbol_entry_has_fracdiff
8. test_trx_per_symbol_entry_has_vol_adj_autocorr
9. test_bch_trx_per_symbol_entries_are_different
10. test_bch_per_symbol_len
11. test_trx_per_symbol_len
12. test_non_bch_trx_fallback_no_special_features (parametrized LDO/ALGO)
13. test_non_bch_trx_fallback_len (parametrized LDO/ALGO)
14. test_subset_invariant_extended_bch
15. test_subset_invariant_extended_trx
16. test_v3_features_per_symbol_has_two_entries
17. test_regime_momentum_in_universal_list
18. test_fracdiff_not_in_universal_list
19. test_vol_adj_autocorr_not_in_universal_list
20. test_universal_list_is_14
21. test_features_for_symbol_unknown_fallback
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

    iter-v3/035+: BCH per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).
    UNCHANGED from iter-v3/035.
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


def test_bch_no_vol_adj_autocorr() -> None:
    """BCHUSDT must NOT include vol_adj_autocorr (TRX-only feature).

    iter-v3/036: BCH and TRX extension features are DISJOINT. BCH has fracdiff_d05_close
    only. vol_adj_autocorr is reserved for TRX only.
    """
    result = features_for_symbol("BCHUSDT")
    assert "vol_adj_autocorr" not in result, (
        f"BCHUSDT: vol_adj_autocorr FOUND in BCH feature set — must be ABSENT. "
        f"iter-v3/036: vol_adj_autocorr is TRX-only; BCH extension = fracdiff_d05_close. "
        f"BCH and TRX per-symbol extensions must be DISJOINT. Got: {result}"
    )


def test_trx_has_vol_adj_autocorr() -> None:
    """TRXUSDT must return 15 features including vol_adj_autocorr.

    iter-v3/036: TRX per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",).
    TRX at iter-v3/035: 52.2% OOS win rate, +29.24 OOS wpnl — primary target for
    per-symbol vol_adj_autocorr isolation.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 15, (
        f"TRXUSDT: expected 15 features (TRX per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['TRXUSDT'] should be V3_FEATURE_COLUMNS_TOP_N + vol_adj_autocorr."
    )
    assert "vol_adj_autocorr" in result, (
        f"TRXUSDT: vol_adj_autocorr MISSING from feature set. "
        f"iter-v3/036: TRX-only vol_adj_autocorr via V3_FEATURES_PER_SYMBOL. "
        f"Got: {result}"
    )


def test_trx_no_fracdiff() -> None:
    """TRXUSDT must NOT include fracdiff_d05_close (BCH-only feature).

    iter-v3/036: BCH and TRX extension features are DISJOINT. TRX has vol_adj_autocorr
    only. fracdiff_d05_close is reserved for BCH only.
    iter-v3/034: TRX had -20.11 OOS wpnl regression from universal fracdiff — BCH-only
    targeting confirmed.
    """
    result = features_for_symbol("TRXUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND in TRX feature set — must be ABSENT. "
        f"iter-v3/036: fracdiff_d05_close is BCH-only. TRX extension = vol_adj_autocorr. "
        f"Got: {result}"
    )


def test_ldo_no_fracdiff_no_vol_adj() -> None:
    """LDOUSDT must return 14 features WITHOUT fracdiff_d05_close or vol_adj_autocorr.

    iter-v3/036: LDO uses V3_FEATURE_COLUMNS_TOP_N fallback (14 features). Neither
    BCH-only nor TRX-only extension features apply.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT. BCH-only feature. Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"LDOUSDT: vol_adj_autocorr FOUND — must be ABSENT. TRX-only feature. Got: {result}"
    )


def test_algo_no_fracdiff_no_vol_adj() -> None:
    """ALGOUSDT must return 14 features WITHOUT fracdiff_d05_close or vol_adj_autocorr.

    iter-v3/036: ALGO uses V3_FEATURE_COLUMNS_TOP_N fallback (14 features). Neither
    BCH-only nor TRX-only extension features apply.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT. BCH-only feature. Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"ALGOUSDT: vol_adj_autocorr FOUND — must be ABSENT. TRX-only feature. Got: {result}"
    )


def test_bch_per_symbol_entry_has_fracdiff() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must contain fracdiff_d05_close.

    The dict entry is the source; features_for_symbol("BCHUSDT") returns this entry.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT' key — "
        "iter-v3/035+: BCH must have a per-symbol entry. "
        "Check features_v3/__init__.py V3_FEATURES_PER_SYMBOL."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    assert "fracdiff_d05_close" in bch_entry, (
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT']: fracdiff_d05_close MISSING. "
        f"BCH entry must include fracdiff_d05_close. Got: {bch_entry}"
    )


def test_trx_per_symbol_entry_has_vol_adj_autocorr() -> None:
    """V3_FEATURES_PER_SYMBOL["TRXUSDT"] must contain vol_adj_autocorr.

    iter-v3/036: TRX per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",).
    """
    assert "TRXUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'TRXUSDT' key — "
        "iter-v3/036: TRX must have a per-symbol entry. "
        "Check features_v3/__init__.py V3_FEATURES_PER_SYMBOL."
    )
    trx_entry = V3_FEATURES_PER_SYMBOL["TRXUSDT"]
    assert "vol_adj_autocorr" in trx_entry, (
        f"V3_FEATURES_PER_SYMBOL['TRXUSDT']: vol_adj_autocorr MISSING. "
        f"TRX entry must include vol_adj_autocorr. Got: {trx_entry}"
    )


def test_bch_trx_per_symbol_entries_are_different() -> None:
    """BCH and TRX per-symbol entries must be DIFFERENT in content.

    iter-v3/036: BCH has fracdiff_d05_close (NOT vol_adj_autocorr);
    TRX has vol_adj_autocorr (NOT fracdiff_d05_close).
    The two entries are structurally distinct: different extension features.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    assert "TRXUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'TRXUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    trx_entry = V3_FEATURES_PER_SYMBOL["TRXUSDT"]
    assert set(bch_entry) != set(trx_entry), (
        f"BCH and TRX per-symbol entries are IDENTICAL — must be DIFFERENT. "
        f"iter-v3/036: BCH extends with fracdiff_d05_close; TRX extends with vol_adj_autocorr. "
        f"BCH entry: {bch_entry}. TRX entry: {trx_entry}."
    )
    assert "fracdiff_d05_close" in bch_entry, (
        f"BCH entry missing fracdiff_d05_close. Got: {bch_entry}"
    )
    assert "fracdiff_d05_close" not in trx_entry, (
        f"TRX entry has fracdiff_d05_close — must be ABSENT (BCH-only). Got: {trx_entry}"
    )
    assert "vol_adj_autocorr" in trx_entry, f"TRX entry missing vol_adj_autocorr. Got: {trx_entry}"
    assert "vol_adj_autocorr" not in bch_entry, (
        f"BCH entry has vol_adj_autocorr — must be ABSENT (TRX-only). Got: {bch_entry}"
    )


def test_bch_per_symbol_len() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must have exactly 15 features.

    15 = 14 universal (V3_FEATURE_COLUMNS_TOP_N) + fracdiff_d05_close.
    UNCHANGED from iter-v3/035.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    assert len(bch_entry) == 15, (
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT']: expected 15 features, got {len(bch_entry)}. "
        f"BCH entry = V3_FEATURE_COLUMNS_TOP_N (14) + fracdiff_d05_close (1) = 15."
    )


def test_trx_per_symbol_len() -> None:
    """V3_FEATURES_PER_SYMBOL["TRXUSDT"] must have exactly 15 features.

    15 = 14 universal (V3_FEATURE_COLUMNS_TOP_N) + vol_adj_autocorr.
    NEW at iter-v3/036.
    """
    assert "TRXUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'TRXUSDT'. Check features_v3/__init__.py."
    )
    trx_entry = V3_FEATURES_PER_SYMBOL["TRXUSDT"]
    assert len(trx_entry) == 15, (
        f"V3_FEATURES_PER_SYMBOL['TRXUSDT']: expected 15 features, got {len(trx_entry)}. "
        f"TRX entry = V3_FEATURE_COLUMNS_TOP_N (14) + vol_adj_autocorr (1) = 15."
    )


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "LDOUSDT"])
def test_non_bch_trx_fallback_no_special_features(symbol: str) -> None:
    """LDO/ALGO must NOT have fracdiff_d05_close or vol_adj_autocorr (fallback path).

    iter-v3/036: LDO and ALGO are not in V3_FEATURES_PER_SYMBOL; they fall back
    to V3_FEATURE_COLUMNS_TOP_N which contains neither extension feature.
    """
    result = features_for_symbol(symbol)
    assert "fracdiff_d05_close" not in result, (
        f"{symbol}: fracdiff_d05_close FOUND — must be ABSENT (BCH-only feature). Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"{symbol}: vol_adj_autocorr FOUND — must be ABSENT (TRX-only feature). Got: {result}"
    )


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "LDOUSDT"])
def test_non_bch_trx_fallback_len(symbol: str) -> None:
    """LDO/ALGO fallback must return exactly 14 features.

    iter-v3/036: V3_FEATURE_COLUMNS_TOP_N has 14 features (neither extension feature added).
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURE_COLUMNS_TOP_N must have exactly 14 at iter-v3/036."
    )


def test_subset_invariant_extended_bch() -> None:
    """BCH entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/035+: BCH entry EXTENDS (not reduces) the universal list by fracdiff_d05_close.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features; only BCH's feature_columns= passed to LightGBM includes it.
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


def test_subset_invariant_extended_trx() -> None:
    """TRX entry must equal V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",).

    iter-v3/036: TRX entry EXTENDS the universal list by vol_adj_autocorr.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features (re-dispatched at iter-v3/036); only TRX's
    feature_columns= passed to LightGBM includes it.
    """
    assert "TRXUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'TRXUSDT'. Check features_v3/__init__.py."
    )
    trx_entry = V3_FEATURES_PER_SYMBOL["TRXUSDT"]
    expected = V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",)
    assert set(trx_entry) == set(expected), (
        f"V3_FEATURES_PER_SYMBOL['TRXUSDT'] content mismatch. "
        f"Expected V3_FEATURE_COLUMNS_TOP_N + ('vol_adj_autocorr',). "
        f"Extra in TRX entry: {sorted(set(trx_entry) - set(expected))}. "
        f"Missing from TRX entry: {sorted(set(expected) - set(trx_entry))}."
    )


def test_v3_features_per_symbol_has_two_entries() -> None:
    """V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/036.

    The two entries are BCHUSDT (fracdiff_d05_close) and TRXUSDT (vol_adj_autocorr).
    LDO/ALGO use the fallback path.
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 2, (
        f"V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/036 (BCH + TRX). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}."
    )
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing BCHUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "TRXUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing TRXUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    BCH+TRX+ALGO+LDO (fallback path) ALL use regime_momentum_signed_5d.
    This feature is in the universal 14-feature list; ALL per-symbol entries inherit it.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS_TOP_N. "
        "Portfolio-level mandate requires all symbols to use this feature via fallback. "
        "feedback_v3_engineered_features_proven.md. Do NOT revert."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/035+: fracdiff_d05_close moved from universal list to BCH per-symbol only.
    Universal list has 14 features. BCH per-symbol has 15 (14 + fracdiff_d05_close).
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/035+: fracdiff_d05_close is in V3_FEATURES_PER_SYMBOL['BCHUSDT'] only. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/036: vol_adj_autocorr is in V3_FEATURES_PER_SYMBOL['TRXUSDT'] only.
    Universal list has 14 features. TRX per-symbol has 15 (14 + vol_adj_autocorr).
    Universal application failed at iter-v3/026 (IS Sharpe collapse; 27× IS/OOS ratio).
    """
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/036: vol_adj_autocorr is in V3_FEATURES_PER_SYMBOL['TRXUSDT'] only. "
        "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/036.

    iter-v3/036: universal list UNCHANGED from iter-v3/035 (still 14 features).
    Neither fracdiff_d05_close nor vol_adj_autocorr appear in the universal list.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/036: universal list unchanged (14 features); TRX-only vol_adj_autocorr "
        f"added via V3_FEATURES_PER_SYMBOL only. "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (14 features, no extensions)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) > 0, "features_for_symbol must never return an empty tuple."
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features)."
    )
    assert "fracdiff_d05_close" not in result, (
        "Unknown symbol fallback must NOT include fracdiff_d05_close (BCH-only feature)."
    )
    assert "vol_adj_autocorr" not in result, (
        "Unknown symbol fallback must NOT include vol_adj_autocorr (TRX-only feature)."
    )
