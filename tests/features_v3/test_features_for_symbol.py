"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/039.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/039 state (CONFIRMATION — iter-v3/035 bundle restored):
- BCHUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15 features.
  UNCHANGED from iter-v3/035. fracdiff_d05_close PRESENT.
- ALGOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
  REVERTED from iter-v3/038 (ALGO per-symbol entry REMOVED — iter-v3/038 NEGATIVE:
  ALGO does NOT benefit from fracdiff; fracdiff is BCH-SPECIFIC).
- LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. Unchanged from iter-v3/038.
  No per-symbol entry (iter-v3/037 NEGATIVE: LDO cross_asset_divergence_norm OOS swing ~-33).
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. Unchanged.
- V3_FEATURES_PER_SYMBOL has exactly 1 entry (BCHUSDT only).
- V3_FEATURE_COLUMNS_TOP_N has 14 features (neither fracdiff_d05_close, vol_adj_autocorr,
  nor cross_asset_divergence_norm appear in the universal list).

Evidence:
- iter-v3/034: fracdiff_d05_close universally failed for TRX/ALGO/LDO (-20.11/-8.24/-6.81
  OOS wpnl). BCH-only targeting (iter-v3/035) isolated BCH lift: PROMISING OOS +2.85.
- iter-v3/038: ALGO fracdiff specificity probe — NEGATIVE. ALGO does NOT benefit from
  fracdiff. fracdiff is BCH-SPECIFIC. ALGO per-symbol entry REVERTED at iter-v3/039.
- iter-v3/039: CONFIRMATION of iter-v3/035 bundle at --seeds 2 (multi-seed validation).

Mandatory test cases (iter-v3/039 brief Section 3 sub-fix #4):
1.  test_bch_has_fracdiff
2.  test_algo_no_fracdiff
3.  test_algo_fallback_14
4.  test_algousdt_not_in_per_symbol
5.  test_ldo_fallback_14
6.  test_ldo_no_fracdiff
7.  test_trx_fallback_14
8.  test_trx_no_special_features
9.  test_bch_per_symbol_entry_has_fracdiff
10. test_ldousdt_not_in_per_symbol
11. test_trxusdt_not_in_per_symbol
12. test_bch_per_symbol_len
13. test_non_bch_fallback_len (parametrized ALGO/LDO/TRX)
14. test_non_bch_fallback_no_special_features (parametrized ALGO/LDO/TRX)
15. test_subset_invariant_bch
16. test_v3_features_per_symbol_has_one_entry
17. test_regime_momentum_in_universal_list
18. test_fracdiff_not_in_universal_list
19. test_cross_asset_divergence_not_in_universal_list
20. test_vol_adj_autocorr_not_in_universal_list
21. test_universal_list_is_14
22. test_features_for_symbol_unknown_fallback
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
    UNCHANGED from iter-v3/035 through iter-v3/039.
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 15, (
        f"BCHUSDT: expected 15 features (BCH per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT'] should be V3_FEATURE_COLUMNS_TOP_N + fracdiff."
    )
    assert "fracdiff_d05_close" in result, (
        f"BCHUSDT: fracdiff_d05_close MISSING from feature set. "
        f"BCH is the primary (and only) beneficiary of fracdiff "
        f"(iter-v3/034 +37.98 OOS wpnl swing; iter-v3/038 confirmed BCH-SPECIFIC). "
        f"Got: {result}"
    )


def test_algo_no_fracdiff() -> None:
    """ALGOUSDT must NOT include fracdiff_d05_close at iter-v3/039.

    iter-v3/039: ALGO per-symbol entry REVERTED from iter-v3/038 NEGATIVE.
    iter-v3/038 EXPLORATION result: ALGO does NOT benefit from fracdiff.
    fracdiff is BCH-SPECIFIC (confirmed across iter-v3/034/035/038 data points).
    ALGO returns to 14-feature V3_FEATURE_COLUMNS_TOP_N fallback.
    """
    result = features_for_symbol("ALGOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/039. "
        f"iter-v3/038 NEGATIVE: ALGO does NOT benefit from fracdiff; BCH-SPECIFIC confirmed. "
        f"ALGO per-symbol entry REVERTED. Got: {result}"
    )


def test_algo_fallback_14() -> None:
    """ALGOUSDT must return 14 features via fallback at iter-v3/039.

    iter-v3/039: ALGOUSDT not in V3_FEATURES_PER_SYMBOL (iter-v3/038 NEGATIVE reverted).
    ALGO uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/039: ALGOUSDT not in V3_FEATURES_PER_SYMBOL (iter-v3/038 NEGATIVE reverted). "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 14-feature set exactly at iter-v3/039. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/039.

    iter-v3/039: ALGO per-symbol entry REVERTED (iter-v3/038 NEGATIVE — ALGO does NOT
    benefit from fracdiff; fracdiff is BCH-SPECIFIC). ALGO uses 14-feature fallback.
    """
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/039. "
        f"iter-v3/039: ALGO per-symbol entry REVERTED (iter-v3/038 NEGATIVE; BCH-SPECIFIC). "
        f"Remove ALGOUSDT from V3_FEATURES_PER_SYMBOL in features_v3/__init__.py. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldo_fallback_14() -> None:
    """LDOUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/039).

    iter-v3/039: LDOUSDT unchanged from iter-v3/038 — not in V3_FEATURES_PER_SYMBOL.
    iter-v3/037 NEGATIVE: LDO cross_asset_divergence_norm OOS swing ~-33. LDO uses 14-feature
    universal fallback.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/039: LDOUSDT not in V3_FEATURES_PER_SYMBOL (iter-v3/037 NEGATIVE unchanged). "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/039: LDO uses 14-feature fallback. Neither fracdiff (BCH-only per-symbol) nor
    cross_asset_divergence_norm (dead at model level since iter-v3/037 NEGATIVE) apply to LDO.
    """
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT (BCH-only per-symbol). "
        f"iter-v3/034: LDO was -6.81 OOS wpnl from universal fracdiff. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"iter-v3/037 NEGATIVE: LDO per-symbol cross_asset caused ~-33 OOS swing. "
        f"LDO uses 14-feature fallback at iter-v3/039. Got: {result}"
    )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/039).

    iter-v3/039: TRXUSDT unchanged — no per-symbol entry since iter-v3/036 revert.
    TRX uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/039: TRXUSDT not in V3_FEATURES_PER_SYMBOL (unchanged). Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_special_features() -> None:
    """TRXUSDT must NOT include fracdiff_d05_close, cross_asset_divergence_norm, vol_adj_autocorr.

    iter-v3/039: TRX uses 14-feature fallback. No extension features apply.
    """
    result = features_for_symbol("TRXUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND — must be ABSENT (BCH-only per-symbol). "
        f"iter-v3/034: TRX was -20.11 OOS wpnl from universal fracdiff. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"TRXUSDT: cross_asset_divergence_norm FOUND — must be ABSENT (dead at model level). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"TRXUSDT: vol_adj_autocorr FOUND — must be ABSENT. Dead code since iter-v3/036 revert. "
        f"Got: {result}"
    )


def test_bch_per_symbol_entry_has_fracdiff() -> None:
    """V3_FEATURES_PER_SYMBOL["BCHUSDT"] must contain fracdiff_d05_close.

    The dict entry is the source; features_for_symbol("BCHUSDT") returns this entry.
    UNCHANGED from iter-v3/035 through iter-v3/039.
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


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/039.

    Unchanged from iter-v3/038. iter-v3/037 NEGATIVE: LDO cross_asset_divergence_norm
    OOS swing ~-33. LDO uses 14-feature universal fallback.
    """
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/039. "
        f"iter-v3/037 NEGATIVE: LDO cross_asset_divergence_norm failed; 14-feature fallback. "
        f"Remove LDOUSDT from V3_FEATURES_PER_SYMBOL in features_v3/__init__.py. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/039.

    TRXUSDT has no per-symbol entry since iter-v3/036 revert. Unchanged through iter-v3/039.
    """
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/039. "
        f"TRXUSDT has no per-symbol entry since iter-v3/036 revert. "
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


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "LDOUSDT", "TRXUSDT"])
def test_non_bch_fallback_len(symbol: str) -> None:
    """ALGO/LDO/TRX fallback must return exactly 14 features.

    iter-v3/039: V3_FEATURE_COLUMNS_TOP_N has 14 features (no extension feature added).
    ALGO reverted from iter-v3/038 NEGATIVE; LDO reverted from iter-v3/037 NEGATIVE;
    TRX unchanged.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURE_COLUMNS_TOP_N must have exactly 14 at iter-v3/039."
    )


@pytest.mark.parametrize("symbol", ["ALGOUSDT", "LDOUSDT", "TRXUSDT"])
def test_non_bch_fallback_no_special_features(symbol: str) -> None:
    """ALGO/LDO/TRX must NOT have fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/039: ALGO/LDO/TRX are not in V3_FEATURES_PER_SYMBOL; they fall back
    to V3_FEATURE_COLUMNS_TOP_N which contains neither extension feature.
    ALGO reverted from iter-v3/038 (NEGATIVE result; BCH-SPECIFIC confirmed).
    LDO reverted from iter-v3/037 (NEGATIVE result). TRX unchanged.
    """
    result = features_for_symbol(symbol)
    assert "fracdiff_d05_close" not in result, (
        f"{symbol}: fracdiff_d05_close FOUND — must be ABSENT (BCH-only per-symbol). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"{symbol}: cross_asset_divergence_norm FOUND — must be ABSENT (dead at model level). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"{symbol}: vol_adj_autocorr FOUND — must be ABSENT (dead code; iter-v3/036 reverted). "
        f"Got: {result}"
    )


def test_subset_invariant_bch() -> None:
    """BCH entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/035+: BCH entry EXTENDS (not reduces) the universal list by fracdiff_d05_close.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features; only BCH's feature_columns= list includes it at model level.
    UNCHANGED from iter-v3/035 through iter-v3/039.
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
    """V3_FEATURES_PER_SYMBOL must have exactly 1 entry at iter-v3/039.

    The one entry is BCHUSDT (fracdiff_d05_close).
    ALGO/LDO/TRX use the fallback path.
    ALGO reverted from iter-v3/038 NEGATIVE (ALGO does NOT benefit from fracdiff).
    LDO reverted from iter-v3/037 NEGATIVE.
    TRX unchanged.
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 1, (
        f"V3_FEATURES_PER_SYMBOL must have exactly 1 entry at iter-v3/039 (BCH only). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}."
    )
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing BCHUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has ALGOUSDT key — must be ABSENT at iter-v3/039 "
        f"(iter-v3/038 NEGATIVE: ALGO does NOT benefit from fracdiff; BCH-SPECIFIC confirmed). "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has LDOUSDT key — must be ABSENT at iter-v3/039 "
        f"(iter-v3/037 NEGATIVE reverted). Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has TRXUSDT key — must be ABSENT at iter-v3/039. "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    BCH+ALGO+TRX+LDO ALL use regime_momentum_signed_5d.
    BCH per-symbol entry EXTENDS TOP_N; ALGO/TRX/LDO fallback returns TOP_N directly.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS_TOP_N. "
        "Portfolio-level mandate requires all symbols to use this feature. "
        "feedback_v3_engineered_features_proven.md. Do NOT revert."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/035+: fracdiff_d05_close in BCH per-symbol entry only (not universal).
    iter-v3/039: fracdiff_d05_close in BCH per-symbol only (ALGO entry reverted).
    Universal list has 14 features. BCH per-symbol has 15 (14 + fracdiff_d05_close).
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/039: fracdiff_d05_close is in V3_FEATURES_PER_SYMBOL['BCHUSDT'] only. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_cross_asset_divergence_not_in_universal_list() -> None:
    """cross_asset_divergence_norm must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/039: cross_asset_divergence_norm is dead at model level (iter-v3/037 NEGATIVE
    reverted; no per-symbol entry for any symbol). Column still generated in parquets by
    engineered_v3 dispatch but NOT in any V3_FEATURES_PER_SYMBOL entry.
    Universal application failed at iter-v3/027 (IS Sharpe collapse -0.2817; OOS spike +1.6786).
    """
    assert "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N, (
        "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/039: cross_asset_divergence_norm dead at model level. "
        "Universal application FALSIFIED at iter-v3/027. LDO per-symbol FALSIFIED at iter-v3/037. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/039: vol_adj_autocorr is dead code (iter-v3/036 NEGATIVE reverted;
    iter-v3/037/038/039 do not reintroduce it).
    Universal application failed at iter-v3/026 (IS Sharpe collapse +0.0493; 27x IS/OOS ratio).
    TRX per-symbol application also failed at iter-v3/036 (~-15 OOS wpnl swing).
    """
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/039: vol_adj_autocorr is dead code. "
        "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27x IS/OOS). "
        "TRX per-symbol FALSIFIED at iter-v3/036 (~-15 OOS wpnl swing). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/039.

    iter-v3/039: universal list UNCHANGED from iter-v3/035 (still 14 features).
    Neither fracdiff_d05_close, cross_asset_divergence_norm, nor vol_adj_autocorr
    appear in the universal list.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/039: universal list unchanged (14 features); fracdiff_d05_close added "
        f"via V3_FEATURES_PER_SYMBOL for BCH only. "
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
        "Unknown symbol fallback must NOT include fracdiff_d05_close (BCH per-symbol only)."
    )
    assert "cross_asset_divergence_norm" not in result, (
        "Unknown symbol fallback must NOT include cross_asset_divergence_norm "
        "(dead at model level; iter-v3/037 NEGATIVE reverted)."
    )
    assert "vol_adj_autocorr" not in result, (
        "Unknown symbol fallback must NOT include vol_adj_autocorr "
        "(dead code; iter-v3/036 reverted)."
    )
