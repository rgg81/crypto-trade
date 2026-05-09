"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/042.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/042 state (EXPLORATION — cycle 3 #3 — REVERT pruning + universal ATR (1.5, 0.75)):
- V3_FEATURE_COLUMNS_TOP_N: 14 features (RESTORED from iter-v3/041 11-feature prune).
  iter-v3/041 Path C NEGATIVE mandate fired (OOS < +1.55 falsifier threshold).
  Three features RESTORED (iter-v3/041 Path C mandate):
    - ret_skew_50               (rank 12/14, importance 412.8)
    - sym_vs_btc_ret_7d         (rank 13/14, importance 398.0)
    - regime_momentum_signed_5d (rank 14/14, importance 390.4)
  feedback_v3_engineered_features_proven.md mandate for regime_momentum_signed_5d
  REINSTATED at iter-v3/042.
- V3_FEATURES_PER_SYMBOL is EMPTY (unchanged from iter-v3/040). All symbols
  fall back to 14-feature universal list.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (unchanged from iter-v3/040).
  DEFAULT_ATR_MULTIPLIERS CHANGED to (1.5, 0.75) — ALL symbols use this.
- BCHUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
- ALGOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
- LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features.

Hypothesis: universal (1.5, 0.75) ATR multipliers (tighter SL, narrower TP) lift
IS Sharpe by reducing trade-duration variance, similar to iter-v3/032 LDO-specific
improvement. 14-feature set = iter-v3/028/040 anchor (verified per research_brief.md).

Mandatory test cases (iter-v3/042 brief Section 3 sub-fix #7):
1.  test_bch_fallback_14                          (CHANGED 11 → 14)
2.  test_bch_no_fracdiff
3.  test_algo_fallback_14                         (CHANGED 11 → 14)
4.  test_algo_no_fracdiff
5.  test_ldo_fallback_14                          (CHANGED 11 → 14)
6.  test_ldo_no_fracdiff
7.  test_trx_fallback_14                          (CHANGED 11 → 14)
8.  test_trx_no_special_features
9.  test_bchusdt_not_in_per_symbol
10. test_algousdt_not_in_per_symbol
11. test_ldousdt_not_in_per_symbol
12. test_trxusdt_not_in_per_symbol
13. test_v3_features_per_symbol_is_empty
14. test_v3_atr_multipliers_per_symbol_is_empty
15. test_all_symbols_atr_tighter                  (NEW iter-v3/042 — (1.5, 0.75) universal)
16. test_regime_momentum_in_universal_list        (REINVERTED — mandate REINSTATED)
17. test_sym_vs_btc_ret_7d_in_universal_list      (POSITIVE assertion — feature RESTORED)
18. test_ret_skew_50_in_universal_list            (POSITIVE assertion — feature RESTORED)
19. test_fracdiff_not_in_universal_list
20. test_cross_asset_divergence_not_in_universal_list
21. test_vol_adj_autocorr_not_in_universal_list
22. test_universal_list_is_14                     (CHANGED 11 → 14)
23. test_features_for_symbol_unknown_fallback
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v3 import (
    DEFAULT_ATR_MULTIPLIERS,
    V3_ATR_MULTIPLIERS_PER_SYMBOL,
    V3_FEATURE_COLUMNS_TOP_N,
    V3_FEATURES_PER_SYMBOL,
    atr_multipliers_for_symbol,
    features_for_symbol,
)


def test_bch_fallback_14() -> None:
    """BCHUSDT must return 14 features via fallback at iter-v3/042.

    iter-v3/042: BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty since iter-v3/040).
    BCH uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features (RESTORED from
    iter-v3/041's 11-feature prune — Path C mandate fired).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 14, (
        f"BCHUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/042), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list RESTORED 11→14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"BCHUSDT must use the universal 14-feature set at iter-v3/042 (no per-symbol entry). "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_no_fracdiff() -> None:
    """BCHUSDT must NOT include fracdiff_d05_close at iter-v3/042.

    iter-v3/040 already cleared the BCH per-symbol fracdiff entry; iter-v3/041/042
    keep V3_FEATURES_PER_SYMBOL empty. fracdiff_d05_close is NOT a model input for any
    symbol at iter-v3/042.
    """
    result = features_for_symbol("BCHUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"BCHUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/042. "
        f"V3_FEATURES_PER_SYMBOL is empty; fracdiff is not a model input for any symbol. "
        f"Got: {result}"
    )


def test_algo_fallback_14() -> None:
    """ALGOUSDT must return 14 features via fallback at iter-v3/042."""
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/042), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list RESTORED 11→14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 14-feature set exactly at iter-v3/042. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_no_fracdiff() -> None:
    """ALGOUSDT must NOT include fracdiff_d05_close at iter-v3/042."""
    result = features_for_symbol("ALGOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/042. "
        f"V3_FEATURES_PER_SYMBOL is empty; fracdiff not a model input. Got: {result}"
    )


def test_ldo_fallback_14() -> None:
    """LDOUSDT must return 14 features via fallback at iter-v3/042."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/042), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list RESTORED 11→14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 14-feature set exactly at iter-v3/042. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_no_fracdiff() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm."""
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT (no per-symbol entries at "
        f"iter-v3/042). Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"LDO uses 14-feature fallback at iter-v3/042. Got: {result}"
    )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback at iter-v3/042."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/042), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list RESTORED 11→14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly at iter-v3/042. "
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
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/042 (no per-symbol "
            f"entries; dead at model level). Got: {result}"
        )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/042 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/042. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/042 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/042. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/042 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/042. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/042 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/042. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/042 (unchanged from iter-v3/040)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/042 (unchanged from iter-v3/040). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/042 (unchanged)."""
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/042. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_all_symbols_atr_tighter() -> None:
    """ALL symbols must return (1.5, 0.75) via DEFAULT at iter-v3/042.

    NEW iter-v3/042: DEFAULT_ATR_MULTIPLIERS changed from (2.0, 1.0) → (1.5, 0.75).
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — all symbols fall back to DEFAULT.
    Per briefs-v3/iteration_v3-042/research_brief.md Section 3 Sub-fix 2.
    """
    assert DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (1.5, 0.75). "
        "iter-v3/042: DEFAULT changed from (2.0, 1.0) to (1.5, 0.75). "
        "Verify in features_v3/__init__.py."
    )
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT"):
        result = atr_multipliers_for_symbol(sym)
        assert result == (1.5, 0.75), (
            f"atr_multipliers_for_symbol('{sym}') returned {result} — expected (1.5, 0.75). "
            f"iter-v3/042: ALL symbols use DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75) "
            f"(V3_ATR_MULTIPLIERS_PER_SYMBOL is empty). "
            f"Verify DEFAULT_ATR_MULTIPLIERS = (1.5, 0.75) in features_v3/__init__.py."
        )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/042.

    REINVERSION of the iter-v3/041 assertion. The iter-v3/041 Path C NEGATIVE mandate
    fired (OOS < +1.55 falsifier threshold). feedback_v3_engineered_features_proven.md
    mandate UPHELD. regime_momentum_signed_5d RESTORED at iter-v3/042.

    iter-v3/028 portfolio importance: rank 14/14, importance 390.4 (64.59% of top).
    iter-v3/040 single-seed cross-check: rank 14/14, importance 454.0.
    Despite low importance rank, OOS signal loss confirmed at iter-v3/041 Path C.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/042 (iter-v3/041 Path C mandate REINSTATES this feature). "
        "feedback_v3_engineered_features_proven.md mandate UPHELD. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/042.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate).
    iter-v3/028 portfolio importance: rank 13/14, importance 398.0 (65.85% of top).
    iter-v3/041 dropped it as bottom-3; iter-v3/042 restores per Path C.
    """
    assert "sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/042 (iter-v3/041 Path C mandate RESTORES this feature). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_ret_skew_50_in_universal_list() -> None:
    """ret_skew_50 MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/042.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate).
    iter-v3/028 portfolio importance: rank 12/14, importance 412.8 (68.30% of top).
    iter-v3/041 dropped it as bottom-3; iter-v3/042 restores per Path C.
    """
    assert "ret_skew_50" in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/042 (iter-v3/041 Path C mandate RESTORES this feature). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list)."""
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/042: fracdiff_d05_close is NOT a model input for any symbol."
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


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/042.

    iter-v3/042 REVERT of iter-v3/041 pruning: 11 → 14 (restored bottom-3 per Path C
    mandate). All 4 symbols fall back to this 14-feature universal list
    (V3_FEATURES_PER_SYMBOL empty). Matches iter-v3/028/040 anchor exactly.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14 at iter-v3/042. "
        f"iter-v3/042 REVERT restored 3 features (ret_skew_50, sym_vs_btc_ret_7d, "
        f"regime_momentum_signed_5d) from iter-v3/041 Path C mandate. "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "ALGOUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_14(symbol: str) -> None:
    """All 4 v3 symbols must return exactly 14 features at iter-v3/042."""
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/042), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list RESTORED 11 → 14."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (14 features at iter-v3/042)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 14, (
        f"Unknown symbol fallback should be 14 features at iter-v3/042, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features)."
    )
    for feat in (
        "fracdiff_d05_close",
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
    ):
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (dead-code policy)."
        )
    # iter-v3/042: regime_momentum_signed_5d MUST be present (mandate REINSTATED).
    assert "regime_momentum_signed_5d" in result, (
        "regime_momentum_signed_5d must be in fallback at iter-v3/042 (mandate REINSTATED). "
        "Path C fired at iter-v3/041; feature RESTORED."
    )
    # iter-v3/042: sym_vs_btc_ret_7d and ret_skew_50 MUST be present (RESTORED).
    assert "sym_vs_btc_ret_7d" in result, (
        "sym_vs_btc_ret_7d must be in fallback at iter-v3/042 (RESTORED from iter-v3/041 prune)."
    )
    assert "ret_skew_50" in result, (
        "ret_skew_50 must be in fallback at iter-v3/042 (RESTORED from iter-v3/041 prune)."
    )
