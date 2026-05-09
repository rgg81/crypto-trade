"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/041.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/041 state (EXPLORATION — cycle 3 #2 — UNIVERSAL FEATURE PRUNING):
- V3_FEATURE_COLUMNS_TOP_N: 11 features (was 14 at iter-v3/040; dropped 3 lowest by
  iter-v3/028 portfolio split-importance).
  Dropped (per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712):
    - ret_skew_50               (rank 12/14, importance 412.8)
    - sym_vs_btc_ret_7d         (rank 13/14, importance 398.0)
    - regime_momentum_signed_5d (rank 14/14, importance 390.4)
  Combined dropped importance: 17.6% of total split count.
- V3_FEATURES_PER_SYMBOL is EMPTY (unchanged from iter-v3/040). All symbols
  fall back to 11-feature universal list.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (unchanged from iter-v3/040).
  LDO continues to use default (2.0, 1.0) ATR multipliers.
- BCHUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 11 features.
- ALGOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 11 features.
- LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 11 features.
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 11 features.

Hypothesis: dropping 17.6% of split-importance frees Optuna search-space noise
and lifts IS Sharpe toward +1.0 while maintaining OOS Sharpe at the iter-v3/040
anchor (~+1.77).

Mandate-revocation note: regime_momentum_signed_5d MUST-be-present mandate from
feedback_v3_engineered_features_proven.md (iter-v3/025) is being REVISITED at
iter-v3/041 EXPLORATION as the universal-pruning axis. EXPLORATIONs can falsify
any prior assumption (3-path resolution per brief Section 8 — PROMISING /
PROMISING-INERT / NEGATIVE).

Mandatory test cases (iter-v3/041 brief Section 3 sub-fix #4):
1.  test_bch_fallback_11
2.  test_bch_no_fracdiff
3.  test_algo_fallback_11
4.  test_algo_no_fracdiff
5.  test_ldo_fallback_11
6.  test_ldo_no_fracdiff
7.  test_trx_fallback_11
8.  test_trx_no_special_features
9.  test_bchusdt_not_in_per_symbol
10. test_algousdt_not_in_per_symbol
11. test_ldousdt_not_in_per_symbol
12. test_trxusdt_not_in_per_symbol
13. test_v3_features_per_symbol_is_empty
14. test_v3_atr_multipliers_per_symbol_is_empty
15. test_ldo_atr_default
16. test_regime_momentum_not_in_universal_list   (INVERTED at iter-v3/041)
17. test_sym_vs_btc_ret_7d_not_in_universal_list (NEW iter-v3/041)
18. test_ret_skew_50_not_in_universal_list       (NEW iter-v3/041)
19. test_fracdiff_not_in_universal_list
20. test_cross_asset_divergence_not_in_universal_list
21. test_vol_adj_autocorr_not_in_universal_list
22. test_universal_list_is_11                    (CHANGED 14 → 11 at iter-v3/041)
23. test_features_for_symbol_unknown_fallback
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


def test_bch_fallback_11() -> None:
    """BCHUSDT must return 11 features via fallback at iter-v3/041.

    iter-v3/041: BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty since iter-v3/040).
    BCH uses V3_FEATURE_COLUMNS_TOP_N fallback = 11 features (was 14 at iter-v3/040;
    dropped 3 bottom by iter-v3/028 portfolio importance).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 11, (
        f"BCHUSDT: expected 11 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/041), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list pruned 14→11. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"BCHUSDT must use the universal 11-feature set at iter-v3/041 (no per-symbol entry). "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_no_fracdiff() -> None:
    """BCHUSDT must NOT include fracdiff_d05_close at iter-v3/041.

    iter-v3/040 already cleared the BCH per-symbol fracdiff entry; iter-v3/041 keeps
    V3_FEATURES_PER_SYMBOL empty. fracdiff_d05_close is NOT a model input for any
    symbol at iter-v3/041.
    """
    result = features_for_symbol("BCHUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"BCHUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/041. "
        f"V3_FEATURES_PER_SYMBOL is empty; fracdiff is not a model input for any symbol. "
        f"Got: {result}"
    )


def test_algo_fallback_11() -> None:
    """ALGOUSDT must return 11 features via fallback at iter-v3/041."""
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 11, (
        f"ALGOUSDT: expected 11 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/041), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list pruned 14→11. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 11-feature set exactly at iter-v3/041. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_no_fracdiff() -> None:
    """ALGOUSDT must NOT include fracdiff_d05_close at iter-v3/041."""
    result = features_for_symbol("ALGOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/041. "
        f"V3_FEATURES_PER_SYMBOL is empty; fracdiff not a model input. Got: {result}"
    )


def test_ldo_fallback_11() -> None:
    """LDOUSDT must return 11 features via fallback at iter-v3/041."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 11, (
        f"LDOUSDT: expected 11 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/041), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list pruned 14→11. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 11-feature set exactly at iter-v3/041. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm."""
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT (no per-symbol entries at "
        f"iter-v3/041). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"LDO uses 11-feature fallback at iter-v3/041. Got: {result}"
    )


def test_trx_fallback_11() -> None:
    """TRXUSDT must return 11 features via fallback at iter-v3/041."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 11, (
        f"TRXUSDT: expected 11 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/041), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list pruned 14→11. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 11-feature set exactly at iter-v3/041. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_special_features() -> None:
    """TRXUSDT must NOT include fracdiff/cross_asset_divergence/vol_adj_autocorr."""
    result = features_for_symbol("TRXUSDT")
    for feat in (
        "fracdiff_d05_close",
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
    ):
        assert feat not in result, (
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/041 (no per-symbol "
            f"entries; dead at model level). Got: {result}"
        )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/041 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/041. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/041 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/041. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/041 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/041. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/041 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/041. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/041 (unchanged from iter-v3/040)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/041 (unchanged from iter-v3/040). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/041 (unchanged)."""
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/041. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_ldo_atr_default() -> None:
    """atr_multipliers_for_symbol("LDOUSDT") must return (2.0, 1.0) at iter-v3/041 (default)."""
    result = atr_multipliers_for_symbol("LDOUSDT")
    assert result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {result} — expected (2.0, 1.0). "
        f"iter-v3/041: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; LDO must use DEFAULT fallback."
    )


def test_regime_momentum_not_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/041.

    INVERSION of the prior iter-v3/025-040 assertion. The MUST-be-present mandate from
    feedback_v3_engineered_features_proven.md is being revisited at iter-v3/041
    EXPLORATION (universal feature pruning axis). 3-path resolution per brief Section 8 —
    PROMISING (mandate FALSIFIED) / PROMISING-INERT / NEGATIVE (mandate UPHELD; restore
    at iter-v3/042).

    iter-v3/028 portfolio importance: rank 14/14, importance 390.4 (64.59% of top).
    iter-v3/040 single-seed cross-check: rank 14/14, importance 454.0 (49.56% of top).
    Both rankings place this engineered feature at the bottom — strongest evidence
    that it warrants removal as part of universal pruning.
    """
    assert "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/041 (universal feature pruning EXPLORATION). "
        "Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_not_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/041.

    NEW iter-v3/041 drop. iter-v3/028 portfolio importance: rank 13/14, importance 398.0
    (65.85% of top). Bottom-3 by canonical multi-seed ranking. ALSO bottom-3 in
    iter-v3/040 single-seed cross-check (rank 12/14, importance 606.0).
    """
    assert "sym_vs_btc_ret_7d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/041 (universal feature pruning EXPLORATION). "
        "Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712."
    )


def test_ret_skew_50_not_in_universal_list() -> None:
    """ret_skew_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/041.

    NEW iter-v3/041 drop. iter-v3/028 portfolio importance: rank 12/14, importance 412.8
    (68.30% of top). Bottom-3 by canonical multi-seed ranking. (Note: ret_skew_50 ranks
    higher in iter-v3/040 single-seed at rank 6, importance 697.0 — but iter-v3/028
    multi-seed is the canonical source per task spec.)
    """
    assert "ret_skew_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/041 "
        "(universal feature pruning EXPLORATION). "
        "Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list)."""
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/041: fracdiff_d05_close is NOT a model input for any symbol."
    )


def test_cross_asset_divergence_not_in_universal_list() -> None:
    """cross_asset_divergence_norm must NOT be in V3_FEATURE_COLUMNS_TOP_N."""
    assert "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N, (
        "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "Universal application FALSIFIED at iter-v3/027; LDO per-symbol FALSIFIED at iter-v3/037."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N."""
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "Dead code; iter-v3/036 NEGATIVE reverted."
    )


def test_universal_list_is_11() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 11 features at iter-v3/041.

    iter-v3/041 universal feature pruning: 14 → 11 (dropped bottom-3 by iter-v3/028
    portfolio split-importance). All 4 symbols fall back to this 11-feature universal list
    (V3_FEATURES_PER_SYMBOL empty).
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 11, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 11 at iter-v3/041. "
        f"Universal feature pruning dropped 3 bottom features (regime_momentum_signed_5d, "
        f"sym_vs_btc_ret_7d, ret_skew_50). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "ALGOUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_11(symbol: str) -> None:
    """All 4 v3 symbols must return exactly 11 features at iter-v3/041."""
    result = features_for_symbol(symbol)
    assert len(result) == 11, (
        f"{symbol}: expected 11 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/041), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list pruned 14 → 11."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (11 features at iter-v3/041)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 11, (
        f"Unknown symbol fallback should be 11 features at iter-v3/041, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (11 features)."
    )
    for feat in (
        "fracdiff_d05_close",
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
        "regime_momentum_signed_5d",  # NEW iter-v3/041
        "sym_vs_btc_ret_7d",  # NEW iter-v3/041
        "ret_skew_50",  # NEW iter-v3/041
    ):
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (iter-v3/041 universal pruning "
            f"or dead-code policy)."
        )
