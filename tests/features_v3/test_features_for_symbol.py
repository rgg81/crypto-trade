"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/040.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/040 state (EXPLORATION — cycle 3 #1 — REVERT all per-symbol customizations):
- V3_FEATURES_PER_SYMBOL is EMPTY (cleared). All symbols fall back to 14-feature universal.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (cleared). LDO uses default (2.0, 1.0) ATR.
- BCHUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
  REVERTED from iter-v3/035-039 (BCH per-symbol fracdiff_d05_close entry removed).
  iter-v3/039 CONFIRMATION NO-MERGE: per-symbol customizations broke IS aggregate.
- ALGOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. Unchanged.
- LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
  ATR reverts to (2.0, 1.0) from (1.5, 0.75) (iter-v3/032 entry cleared).
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. Unchanged.

Evidence:
- iter-v3/029: clean 4-symbol anchor (no per-symbol customizations): IS ~+0.79 / OOS ~+1.77.
- iter-v3/032-039: per-symbol customizations caused ~-0.55 IS Sharpe swing vs iter-v3/029.
- iter-v3/040: REVERT to verify IS recovery toward iter-v3/029 anchor.

Mandatory test cases (iter-v3/040 brief Section 3 sub-fix #5):
1.  test_bch_fallback_14
2.  test_bch_no_fracdiff
3.  test_algo_fallback_14
4.  test_algo_no_fracdiff
5.  test_ldo_fallback_14
6.  test_ldo_no_fracdiff
7.  test_trx_fallback_14
8.  test_trx_no_special_features
9.  test_bchusdt_not_in_per_symbol
10. test_algousdt_not_in_per_symbol
11. test_ldousdt_not_in_per_symbol
12. test_trxusdt_not_in_per_symbol
13. test_v3_features_per_symbol_is_empty
14. test_v3_atr_multipliers_per_symbol_is_empty
15. test_ldo_atr_default
16. test_regime_momentum_in_universal_list
17. test_fracdiff_not_in_universal_list
18. test_cross_asset_divergence_not_in_universal_list
19. test_vol_adj_autocorr_not_in_universal_list
20. test_universal_list_is_14
21. test_features_for_symbol_unknown_fallback
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v3 import (
    V3_ATR_MULTIPLIERS_PER_SYMBOL,
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    atr_multipliers_for_symbol,
    features_for_symbol,
)


def test_bch_fallback_14() -> None:
    """BCHUSDT must return 14 features via fallback at iter-v3/040.

    iter-v3/040: BCHUSDT per-symbol entry CLEARED (BCH fracdiff entry removed).
    BCH returns to V3_FEATURE_COLUMNS_TOP_N (14-feature universal fallback).
    iter-v3/035-039 BCH per-symbol fracdiff entry was the IS degradation source;
    reverting it is the primary action in this EXPLORATION.
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 14, (
        f"BCHUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/040: BCHUSDT per-symbol entry CLEARED (cycle 3 REVERT EXPLORATION). "
        f"V3_FEATURES_PER_SYMBOL must be empty. Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"BCHUSDT must use the universal 14-feature set at iter-v3/040 (no per-symbol entry). "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_no_fracdiff() -> None:
    """BCHUSDT must NOT include fracdiff_d05_close at iter-v3/040.

    iter-v3/040: BCH per-symbol fracdiff entry CLEARED. fracdiff_d05_close is NOT
    a model input for any symbol (V3_FEATURES_PER_SYMBOL is empty).
    BCH uses 14-feature universal fallback which does not include fracdiff_d05_close.
    """
    result = features_for_symbol("BCHUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"BCHUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: BCH per-symbol fracdiff entry CLEARED (cycle 3 REVERT EXPLORATION). "
        f"fracdiff_d05_close is NOT a model input for any symbol at iter-v3/040. "
        f"Got: {result}"
    )


def test_algo_fallback_14() -> None:
    """ALGOUSDT must return 14 features via fallback at iter-v3/040.

    iter-v3/040: ALGOUSDT not in V3_FEATURES_PER_SYMBOL (dict is empty).
    ALGO uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features. Unchanged from iter-v3/039
    (ALGO per-symbol entry was already absent at iter-v3/039 after iter-v3/038 revert).
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL is empty; ALGO uses universal fallback. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 14-feature set exactly at iter-v3/040. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_no_fracdiff() -> None:
    """ALGOUSDT must NOT include fracdiff_d05_close at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. fracdiff_d05_close is NOT a model
    input for any symbol. ALGO uses 14-feature fallback which does not include fracdiff.
    """
    result = features_for_symbol("ALGOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL is empty; fracdiff not a model input. "
        f"Got: {result}"
    )


def test_ldo_fallback_14() -> None:
    """LDOUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/040).

    iter-v3/040: LDOUSDT not in V3_FEATURES_PER_SYMBOL (dict is empty).
    LDO uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL is empty; LDO uses universal fallback. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 14-feature set exactly at iter-v3/040. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. LDO uses 14-feature fallback.
    Neither fracdiff (no per-symbol entries) nor cross_asset_divergence_norm
    (dead at model level since iter-v3/037 NEGATIVE) apply to LDO at iter-v3/040.
    """
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT (no per-symbol entries at "
        f"iter-v3/040). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"iter-v3/037 NEGATIVE: LDO per-symbol cross_asset caused ~-33 OOS swing. "
        f"LDO uses 14-feature fallback at iter-v3/040. Got: {result}"
    )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/040).

    iter-v3/040: TRXUSDT not in V3_FEATURES_PER_SYMBOL (dict is empty).
    TRX uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features. Unchanged from iter-v3/039.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL is empty; TRX uses universal fallback. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_special_features() -> None:
    """TRXUSDT must NOT include fracdiff_d05_close, cross_asset_divergence_norm, vol_adj_autocorr.

    iter-v3/040: TRX uses 14-feature fallback. No extension features apply.
    """
    result = features_for_symbol("TRXUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND — must be ABSENT (no per-symbol entries at "
        f"iter-v3/040). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"TRXUSDT: cross_asset_divergence_norm FOUND — must be ABSENT (dead at model level). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"TRXUSDT: vol_adj_autocorr FOUND — must be ABSENT. Dead code since iter-v3/036 revert. "
        f"Got: {result}"
    )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty (cleared in cycle 3 REVERT EXPLORATION).
    BCHUSDT per-symbol fracdiff entry removed (was present at iter-v3/035-039).
    BCH reverts to 14-feature universal fallback.
    """
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL must be empty (cycle 3 REVERT). "
        f"Remove BCHUSDT from V3_FEATURES_PER_SYMBOL in features_v3/__init__.py. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. ALGOUSDT not present (unchanged from
    iter-v3/039 where ALGO entry was already absent after iter-v3/038 NEGATIVE revert).
    """
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL must be empty. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. Unchanged from iter-v3/039.
    """
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL must be empty. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. Unchanged from iter-v3/039.
    """
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/040. "
        f"iter-v3/040: V3_FEATURES_PER_SYMBOL must be empty. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/040.

    iter-v3/040: cycle 3 EXPLORATION #1 — REVERT all per-symbol feature overrides.
    BCH fracdiff entry (iter-v3/035-039) CLEARED. No per-symbol entries remain.
    All 4 symbols (BCH/ALGO/LDO/TRX) use 14-feature universal fallback.

    This is the DEFINING change of iter-v3/040: clearing V3_FEATURES_PER_SYMBOL
    verifies that the IS degradation at iter-v3/039 was caused by per-symbol
    customizations rather than other factors.
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/040 (cycle 3 REVERT). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/040.

    iter-v3/040: cycle 3 EXPLORATION #1 — REVERT all per-symbol ATR customizations.
    LDO entry (1.5, 0.75) CLEARED (was added at iter-v3/032). LDO reverts to
    DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via atr_multipliers_for_symbol fallback.

    Reverting LDO ATR widens LDO barriers from ~10% to ~13.4% (TP).
    Expected effect: fewer LDO trades (wider barriers harder to reach).
    """
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/040 (cycle 3 REVERT). "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_ldo_atr_default() -> None:
    """atr_multipliers_for_symbol("LDOUSDT") must return (2.0, 1.0) at iter-v3/040.

    iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty. LDO falls back to
    DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).

    Previously at iter-v3/032-039: LDOUSDT returned (1.5, 0.75) from per-symbol dict.
    After revert: LDOUSDT returns (2.0, 1.0) via DEFAULT_ATR_MULTIPLIERS fallback.
    """
    result = atr_multipliers_for_symbol("LDOUSDT")
    assert result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {result} — expected (2.0, 1.0). "
        f"iter-v3/040: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; LDO must use DEFAULT fallback. "
        f"Verify V3_ATR_MULTIPLIERS_PER_SYMBOL == {{}} in features_v3/__init__.py."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    All 4 symbols (BCH/ALGO/TRX/LDO) use regime_momentum_signed_5d via the 14-feature
    universal fallback (V3_FEATURES_PER_SYMBOL is empty at iter-v3/040 — all symbols
    fall back to TOP_N directly).
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS_TOP_N. "
        "Portfolio-level mandate requires all symbols to use this feature. "
        "feedback_v3_engineered_features_proven.md. Do NOT revert."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. fracdiff_d05_close is NOT a model
    input for any symbol. Universal list has 14 features (no fracdiff extension).
    Column still generated in parquets by add_engineered_v3_features but excluded
    from all feature_columns lists.
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/040: fracdiff_d05_close is NOT a model input for any symbol. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_cross_asset_divergence_not_in_universal_list() -> None:
    """cross_asset_divergence_norm must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/040: cross_asset_divergence_norm is dead at model level (iter-v3/037 NEGATIVE
    reverted; no per-symbol entry for any symbol; V3_FEATURES_PER_SYMBOL is empty).
    Column still generated in parquets by engineered_v3 dispatch but NOT in any
    V3_FEATURES_PER_SYMBOL entry and NOT in the universal list.
    Universal application failed at iter-v3/027 (IS Sharpe collapse -0.2817; OOS spike +1.6786).
    """
    assert "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N, (
        "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/040: cross_asset_divergence_norm dead at model level. "
        "Universal application FALSIFIED at iter-v3/027. LDO per-symbol FALSIFIED at iter-v3/037. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/040: vol_adj_autocorr is dead code (iter-v3/036 NEGATIVE reverted;
    iter-v3/037-040 do not reintroduce it; V3_FEATURES_PER_SYMBOL is empty).
    Universal application failed at iter-v3/026 (IS Sharpe collapse +0.0493; 27x IS/OOS ratio).
    TRX per-symbol application also failed at iter-v3/036 (~-15 OOS wpnl swing).
    """
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/040: vol_adj_autocorr is dead code. "
        "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27x IS/OOS). "
        "TRX per-symbol FALSIFIED at iter-v3/036 (~-15 OOS wpnl swing). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/040.

    iter-v3/040: universal list UNCHANGED from iter-v3/035 (still 14 features).
    Neither fracdiff_d05_close, cross_asset_divergence_norm, nor vol_adj_autocorr
    appear in the universal list.
    All 4 symbols fall back to this 14-feature universal list (V3_FEATURES_PER_SYMBOL empty).
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/040: universal list unchanged (14 features); all symbols use this fallback. "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "ALGOUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_14(symbol: str) -> None:
    """All 4 v3 symbols must return exactly 14 features at iter-v3/040.

    iter-v3/040: V3_FEATURES_PER_SYMBOL is empty. All symbols fall back to
    V3_FEATURE_COLUMNS_TOP_N (14 features). No per-symbol extensions exist.
    BCH reverted from iter-v3/035-039 per-symbol fracdiff (IS degradation source).
    LDO, TRX, ALGO: unchanged (no per-symbol entries at iter-v3/039 already).
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty at iter-v3/040. "
        f"All 4 symbols use the 14-feature universal anchor."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
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
        "Unknown symbol fallback must NOT include fracdiff_d05_close "
        "(V3_FEATURES_PER_SYMBOL is empty at iter-v3/040; no per-symbol extensions)."
    )
    assert "cross_asset_divergence_norm" not in result, (
        "Unknown symbol fallback must NOT include cross_asset_divergence_norm "
        "(dead at model level; iter-v3/037 NEGATIVE reverted)."
    )
    assert "vol_adj_autocorr" not in result, (
        "Unknown symbol fallback must NOT include vol_adj_autocorr "
        "(dead code; iter-v3/036 reverted)."
    )
