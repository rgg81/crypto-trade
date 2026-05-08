"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/037.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/037 state:
- BCHUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15 features.
  UNCHANGED from iter-v3/035. fracdiff_d05_close PRESENT; cross_asset_divergence_norm ABSENT.
- LDOUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",) = 15
  features. NEW at iter-v3/037. cross_asset_divergence_norm PRESENT; fracdiff_d05_close ABSENT.
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. REVERTED from iter-v3/036.
  No per-symbol entry (iter-v3/036 NEGATIVE: TRX vol_adj_autocorr hurt TRX ~-15 OOS wpnl swing).
- ALGOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. UNCHANGED.
- V3_FEATURES_PER_SYMBOL has exactly 2 entries (BCHUSDT + LDOUSDT).
- BCH and LDO extension features are DISJOINT:
    BCH: fracdiff_d05_close (NOT cross_asset_divergence_norm)
    LDO: cross_asset_divergence_norm (NOT fracdiff_d05_close)
- V3_FEATURE_COLUMNS_TOP_N has 14 features (neither fracdiff_d05_close, vol_adj_autocorr,
  nor cross_asset_divergence_norm appear in the universal list).

Evidence:
- iter-v3/027: universal cross_asset_divergence_norm failed (IS Sharpe collapse -0.2817;
  OOS spike +1.6786; 3-iter monotonic IS degradation). Per-symbol isolation tests LDO-specific
  signal without cross-symbol contamination.
- iter-v3/034: fracdiff_d05_close universally failed for TRX/ALGO/LDO (-20.11/-8.24/-6.81
  OOS wpnl). BCH-only targeting (iter-v3/035) isolated BCH lift: PROMISING OOS +2.85.
- iter-v3/035: LDO at +3.98 OOS wpnl, 35.0% WR (weakest contributor); btc_ret_14d rank 6
  in LDO model — primary candidate for BTC-coupling signal improvement.
- iter-v3/036: TRX vol_adj_autocorr NEGATIVE (~-15 OOS wpnl swing); REVERTED at iter-v3/037.
- Per-symbol architecture (iter-v3/030) provides isolation infrastructure.

Mandatory test cases (iter-v3/037 brief Section 3 sub-fix #5):
1. test_bch_has_fracdiff
2. test_bch_no_cross_asset_divergence
3. test_ldo_has_cross_asset_divergence
4. test_ldo_no_fracdiff
5. test_trx_fallback_14
6. test_trx_no_cross_asset_divergence
7. test_algo_no_fracdiff_no_cross_asset
8. test_bch_per_symbol_entry_has_fracdiff
9. test_ldo_per_symbol_entry_has_cross_asset_divergence
10. test_bch_ldo_per_symbol_entries_are_different
11. test_trxusdt_not_in_per_symbol
12. test_bch_per_symbol_len
13. test_ldo_per_symbol_len
14. test_non_bch_ldo_fallback_no_special_features (parametrized TRX/ALGO)
15. test_non_bch_ldo_fallback_len (parametrized TRX/ALGO)
16. test_subset_invariant_extended_bch
17. test_subset_invariant_extended_ldo
18. test_v3_features_per_symbol_has_two_entries
19. test_regime_momentum_in_universal_list
20. test_fracdiff_not_in_universal_list
21. test_cross_asset_divergence_not_in_universal_list
22. test_vol_adj_autocorr_not_in_universal_list
23. test_universal_list_is_14
24. test_features_for_symbol_unknown_fallback
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
    UNCHANGED from iter-v3/035 through iter-v3/037.
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


def test_bch_no_cross_asset_divergence() -> None:
    """BCHUSDT must NOT include cross_asset_divergence_norm (LDO-only feature).

    iter-v3/037: BCH and LDO extension features are DISJOINT. BCH has fracdiff_d05_close
    only. cross_asset_divergence_norm is reserved for LDO only.
    """
    result = features_for_symbol("BCHUSDT")
    assert "cross_asset_divergence_norm" not in result, (
        f"BCHUSDT: cross_asset_divergence_norm FOUND in BCH feature set — must be ABSENT. "
        f"iter-v3/037: cross_asset_divergence_norm is LDO-only; BCH extension = fracdiff. "
        f"BCH and LDO per-symbol extensions must be DISJOINT. Got: {result}"
    )


def test_ldo_has_cross_asset_divergence() -> None:
    """LDOUSDT must return 15 features including cross_asset_divergence_norm.

    iter-v3/037: LDO per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",).
    LDO at iter-v3/035: +3.98 OOS wpnl, 35.0% WR (weakest contributor); btc_ret_14d rank 6
    in LDO model — primary target for BTC-coupling signal improvement.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 15, (
        f"LDOUSDT: expected 15 features (LDO per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['LDOUSDT'] should be V3_FEATURE_COLUMNS_TOP_N "
        f"+ cross_asset_divergence_norm."
    )
    assert "cross_asset_divergence_norm" in result, (
        f"LDOUSDT: cross_asset_divergence_norm MISSING from feature set. "
        f"iter-v3/037: LDO-only cross_asset_divergence_norm via V3_FEATURES_PER_SYMBOL. "
        f"Got: {result}"
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close (BCH-only feature).

    iter-v3/037: BCH and LDO extension features are DISJOINT. LDO has cross_asset_divergence_norm
    only. fracdiff_d05_close is reserved for BCH only.
    iter-v3/034: TRX had -20.11, ALGO -8.24, LDO -6.81 OOS wpnl regression from universal
    fracdiff — BCH-only targeting confirmed. LDO must NOT receive fracdiff.
    """
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND in LDO feature set — must be ABSENT. "
        f"iter-v3/037: fracdiff_d05_close is BCH-only. "
        f"LDO extension = cross_asset_divergence_norm. Got: {result}"
    )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/037).

    iter-v3/037: TRXUSDT removed from V3_FEATURES_PER_SYMBOL (iter-v3/036 NEGATIVE reverted).
    TRX vol_adj_autocorr hurt TRX ~-15 OOS wpnl swing. TRX returns to 14-feature universal.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/037: TRXUSDT not in V3_FEATURES_PER_SYMBOL (iter-v3/036 NEGATIVE reverted). "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_cross_asset_divergence() -> None:
    """TRXUSDT must NOT include cross_asset_divergence_norm (LDO-only feature).

    iter-v3/037: TRX uses 14-feature fallback. cross_asset_divergence_norm is LDO-only.
    """
    result = features_for_symbol("TRXUSDT")
    assert "cross_asset_divergence_norm" not in result, (
        f"TRXUSDT: cross_asset_divergence_norm FOUND — must be ABSENT (LDO-only feature). "
        f"Got: {result}"
    )
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND — must be ABSENT (BCH-only feature). Got: {result}"
    )


def test_algo_no_fracdiff_no_cross_asset() -> None:
    """ALGOUSDT must return 14 features WITHOUT fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/037: ALGO uses V3_FEATURE_COLUMNS_TOP_N fallback (14 features). Neither
    BCH-only nor LDO-only extension features apply.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}."
    )
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT. BCH-only feature. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"ALGOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. LDO-only feature. "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"ALGOUSDT: vol_adj_autocorr FOUND — must be ABSENT. Dead code since iter-v3/037. "
        f"Got: {result}"
    )


def test_bch_per_symbol_entry_has_fracdiff() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must contain fracdiff_d05_close.

    The dict entry is the source; features_for_symbol("BCHUSDT") returns this entry.
    UNCHANGED from iter-v3/035.
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


def test_ldo_per_symbol_entry_has_cross_asset_divergence() -> None:
    """V3_FEATURES_PER_SYMBOL["LDOUSDT"] must contain cross_asset_divergence_norm.

    iter-v3/037: LDO per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",).
    """
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'LDOUSDT' key — "
        "iter-v3/037: LDO must have a per-symbol entry. "
        "Check features_v3/__init__.py V3_FEATURES_PER_SYMBOL."
    )
    ldo_entry = V3_FEATURES_PER_SYMBOL["LDOUSDT"]
    assert "cross_asset_divergence_norm" in ldo_entry, (
        f"V3_FEATURES_PER_SYMBOL['LDOUSDT']: cross_asset_divergence_norm MISSING. "
        f"LDO entry must include cross_asset_divergence_norm. Got: {ldo_entry}"
    )


def test_bch_ldo_per_symbol_entries_are_different() -> None:
    """BCH and LDO per-symbol entries must be DIFFERENT in content.

    iter-v3/037: BCH has fracdiff_d05_close (NOT cross_asset_divergence_norm);
    LDO has cross_asset_divergence_norm (NOT fracdiff_d05_close).
    The two entries are structurally distinct: different extension features.
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'LDOUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    ldo_entry = V3_FEATURES_PER_SYMBOL["LDOUSDT"]
    assert set(bch_entry) != set(ldo_entry), (
        f"BCH and LDO per-symbol entries are IDENTICAL — must be DIFFERENT. "
        f"iter-v3/037: BCH extends with fracdiff_d05_close; LDO extends with "
        f"cross_asset_divergence_norm. BCH entry: {bch_entry}. LDO entry: {ldo_entry}."
    )
    assert "fracdiff_d05_close" in bch_entry, (
        f"BCH entry missing fracdiff_d05_close. Got: {bch_entry}"
    )
    assert "fracdiff_d05_close" not in ldo_entry, (
        f"LDO entry has fracdiff_d05_close — must be ABSENT (BCH-only). Got: {ldo_entry}"
    )
    assert "cross_asset_divergence_norm" in ldo_entry, (
        f"LDO entry missing cross_asset_divergence_norm. Got: {ldo_entry}"
    )
    assert "cross_asset_divergence_norm" not in bch_entry, (
        f"BCH entry has cross_asset_divergence_norm — must be ABSENT (LDO-only). Got: {bch_entry}"
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/037.

    iter-v3/037: TRX per-symbol entry REVERTED (iter-v3/036 NEGATIVE: vol_adj_autocorr
    hurt TRX ~-15 OOS wpnl swing). TRX must use 14-feature universal fallback.
    """
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/037. "
        f"iter-v3/037: TRX per-symbol entry REVERTED (iter-v3/036 NEGATIVE). "
        f"Remove TRXUSDT from V3_FEATURES_PER_SYMBOL in features_v3/__init__.py. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
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


def test_ldo_per_symbol_len() -> None:
    """V3_FEATURES_PER_SYMBOL["LDOUSDT"] must have exactly 15 features.

    15 = 14 universal (V3_FEATURE_COLUMNS_TOP_N) + cross_asset_divergence_norm.
    NEW at iter-v3/037.
    """
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'LDOUSDT'. Check features_v3/__init__.py."
    )
    ldo_entry = V3_FEATURES_PER_SYMBOL["LDOUSDT"]
    assert len(ldo_entry) == 15, (
        f"V3_FEATURES_PER_SYMBOL['LDOUSDT']: expected 15 features, got {len(ldo_entry)}. "
        f"LDO entry = V3_FEATURE_COLUMNS_TOP_N (14) + cross_asset_divergence_norm (1) = 15."
    )


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "TRXUSDT"])
def test_non_bch_ldo_fallback_no_special_features(symbol: str) -> None:
    """TRX/ALGO must NOT have fracdiff_d05_close or cross_asset_divergence_norm (fallback path).

    iter-v3/037: TRX and ALGO are not in V3_FEATURES_PER_SYMBOL; they fall back
    to V3_FEATURE_COLUMNS_TOP_N which contains neither extension feature.
    TRX reverted from iter-v3/036 (NEGATIVE result).
    """
    result = features_for_symbol(symbol)
    assert "fracdiff_d05_close" not in result, (
        f"{symbol}: fracdiff_d05_close FOUND — must be ABSENT (BCH-only feature). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"{symbol}: cross_asset_divergence_norm FOUND — must be ABSENT (LDO-only feature). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"{symbol}: vol_adj_autocorr FOUND — must be ABSENT (dead code; iter-v3/036 reverted). "
        f"Got: {result}"
    )


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "TRXUSDT"])
def test_non_bch_ldo_fallback_len(symbol: str) -> None:
    """TRX/ALGO fallback must return exactly 14 features.

    iter-v3/037: V3_FEATURE_COLUMNS_TOP_N has 14 features (no extension feature added).
    TRX reverted from iter-v3/036 (NEGATIVE result); ALGO unchanged.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURE_COLUMNS_TOP_N must have exactly 14 at iter-v3/037."
    )


def test_subset_invariant_extended_bch() -> None:
    """BCH entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/035+: BCH entry EXTENDS (not reduces) the universal list by fracdiff_d05_close.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features; only BCH's feature_columns= passed to LightGBM includes it.
    UNCHANGED from iter-v3/035.
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


def test_subset_invariant_extended_ldo() -> None:
    """LDO entry must equal V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",).

    iter-v3/037: LDO entry EXTENDS the universal list by cross_asset_divergence_norm.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features (re-dispatched at iter-v3/037); only LDO's
    feature_columns= passed to LightGBM includes it.
    """
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'LDOUSDT'. Check features_v3/__init__.py."
    )
    ldo_entry = V3_FEATURES_PER_SYMBOL["LDOUSDT"]
    expected = V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",)
    assert set(ldo_entry) == set(expected), (
        f"V3_FEATURES_PER_SYMBOL['LDOUSDT'] content mismatch. "
        f"Expected V3_FEATURE_COLUMNS_TOP_N + ('cross_asset_divergence_norm',). "
        f"Extra in LDO entry: {sorted(set(ldo_entry) - set(expected))}. "
        f"Missing from LDO entry: {sorted(set(expected) - set(ldo_entry))}."
    )


def test_v3_features_per_symbol_has_two_entries() -> None:
    """V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/037.

    The two entries are BCHUSDT (fracdiff_d05_close) and LDOUSDT (cross_asset_divergence_norm).
    TRX/ALGO use the fallback path. TRX reverted from iter-v3/036 (NEGATIVE).
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 2, (
        f"V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/037 (BCH + LDO). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}."
    )
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing BCHUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing LDOUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has TRXUSDT key — must be ABSENT at iter-v3/037 (reverted). "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    BCH+LDO+TRX+ALGO (fallback path) ALL use regime_momentum_signed_5d.
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
    UNCHANGED from iter-v3/035.
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/035+: fracdiff_d05_close is in V3_FEATURES_PER_SYMBOL['BCHUSDT'] only. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_cross_asset_divergence_not_in_universal_list() -> None:
    """cross_asset_divergence_norm must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/037: cross_asset_divergence_norm is in V3_FEATURES_PER_SYMBOL['LDOUSDT'] only.
    Universal list has 14 features. LDO per-symbol has 15 (14 + cross_asset_divergence_norm).
    Universal application failed at iter-v3/027 (IS Sharpe collapse -0.2817; OOS spike +1.6786).
    """
    assert "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N, (
        "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/037: cross_asset_divergence_norm is in V3_FEATURES_PER_SYMBOL['LDOUSDT'] only. "
        "Universal application FALSIFIED at iter-v3/027 (IS Sharpe collapse; 3-iter monotonic). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/037: vol_adj_autocorr is dead code (iter-v3/036 NEGATIVE reverted).
    Universal application failed at iter-v3/026 (IS Sharpe collapse +0.0493; 27× IS/OOS ratio).
    TRX per-symbol application also failed at iter-v3/036 (~-15 OOS wpnl swing).
    """
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/037: vol_adj_autocorr is dead code (iter-v3/036 NEGATIVE reverted). "
        "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS). "
        "TRX per-symbol FALSIFIED at iter-v3/036 (~-15 OOS wpnl swing). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/037.

    iter-v3/037: universal list UNCHANGED from iter-v3/035 (still 14 features).
    Neither fracdiff_d05_close, cross_asset_divergence_norm, nor vol_adj_autocorr
    appear in the universal list.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/037: universal list unchanged (14 features); LDO-only cross_asset_divergence "
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
    assert "cross_asset_divergence_norm" not in result, (
        "Unknown symbol fallback must NOT include cross_asset_divergence_norm (LDO-only feature)."
    )
    assert "vol_adj_autocorr" not in result, (
        "Unknown symbol fallback must NOT include vol_adj_autocorr "
        "(dead code; iter-v3/036 reverted)."
    )
