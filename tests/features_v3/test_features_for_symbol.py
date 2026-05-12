"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/054 (UPDATED from /053).

iter-v3/054 state (EXPLORATION — cycle 4 #4 — per-symbol drawdown brake primitive 11;
                   hurst_drift_50_200 PARKED per /053 PATH D; SYSTEM-LEVEL REVERT carry-forward):
- V3_FEATURE_COLUMNS_TOP_N: 14 features (14-anchor; hurst_drift_50_200 DROPPED PARKED).
  REVERT: hurst_drift_50_200 DROPPED (PARKED per /053 PATH D NULL-RESULT; 15th-slot SWAP
  family STRUCTURALLY EXHAUSTED; Critic FINAL `c056354` rec #1).
- V3_FEATURES_PER_SYMBOL is EMPTY (REVERT carry-forward). All symbols fall back to 14.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT carry-forward).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /051).
- block_long_for = () (REVERT carry-forward from /051).

History of V3_FEATURE_COLUMNS_TOP_N count:
  iter-v3/040-044: 14 features (anchor).
  iter-v3/048: 15 features (vol_normalized_ret_5d ADDED — cycle 3 #9).
  iter-v3/049: 14 features (vol_normalized_ret_5d DROPPED — PATH C-clean).
  iter-v3/051: 15 features (fracdiff_d05_close ADDED — single axis, cycle 4 #1).
  iter-v3/052: 15 features (SWAP: fracdiff PARKED; regime_momentum_signed_3d ACTIVATED).
  iter-v3/053: 15 features (SWAP: 3d PARKED; hurst_drift_50_200 ACTIVATED).
  iter-v3/054: 14 features (hurst_drift_50_200 PARKED per /053 PATH D).

Mandatory test cases (iter-v3/054 state):
 1. test_bch_fallback_14                 — BCH returns 14 features via fallback
 2. test_bch_absent_parked_features     — BCH does NOT include PARKED features
 3. test_algo_fallback_14              — ALGO returns 14 features via fallback
 4. test_algo_absent_parked_features   — ALGO does NOT include PARKED features
 5. test_ldo_fallback_14              — LDO returns 14 features via fallback
 6. test_ldo_absent_parked_features   — LDO does NOT include PARKED features
 7. test_trx_fallback_14              — TRX returns 14 features via fallback
 8. test_trx_no_dead_features         — TRX does NOT include dead-code features
 9. test_bchusdt_not_in_per_symbol    — BCH absent from V3_FEATURES_PER_SYMBOL
10. test_algousdt_not_in_per_symbol   — ALGO absent from V3_FEATURES_PER_SYMBOL
11. test_ldousdt_not_in_per_symbol    — LDO absent from V3_FEATURES_PER_SYMBOL
12. test_trxusdt_not_in_per_symbol    — TRX absent from V3_FEATURES_PER_SYMBOL
13. test_v3_features_per_symbol_is_empty — empty dict
14. test_v3_atr_multipliers_per_symbol_is_empty — EMPTY (REVERT from /047-/050 state)
15. test_all_symbols_atr_default_iter_v3_051    — all 3 syms return (2.0, 1.0)
16. test_regime_momentum_in_universal_list      — mandate ACTIVE
17. test_sym_vs_btc_ret_7d_in_universal_list    — RESTORED iter-v3/042; KEPT
18. test_ret_skew_50_in_universal_list          — RESTORED iter-v3/042; KEPT
19. test_efficiency_ratio_50_not_in_universal_list — DROPPED iter-v3/044
20. test_regime_momentum_signed_3d_not_in_universal_list — PARKED /053
21. test_fracdiff_in_universal_list             — PARKED /052
22. test_cross_asset_divergence_not_in_universal_list — dead code
23. test_vol_adj_autocorr_not_in_universal_list — dead code
24. test_universal_list_is_14               — 14 features at iter-v3/054 (REVERT from 15)
25. test_all_symbols_fallback_14            — parametrized; BCH/LDO/TRX all 14 features
26. test_features_for_symbol_unknown_fallback — unknown sym falls back to 14-feature list
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
    """BCHUSDT must return 14 features via fallback at iter-v3/054.

    iter-v3/054: BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty — SYSTEM-LEVEL REVERT).
    BCH uses V3_FEATURE_COLUMNS_TOP_N fallback = 14 features (hurst_drift_50_200 PARKED).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 14, (
        f"BCHUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/054), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"BCHUSDT must use the universal 14-feature set at iter-v3/054 (no per-symbol entry). "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_absent_parked_features() -> None:
    """BCHUSDT MUST NOT include PARKED/dead features at /054.

    iter-v3/054: fracdiff PARKED (/052), regime_momentum_signed_3d PARKED (/053),
    hurst_drift_50_200 PARKED (/054).
    """
    result = features_for_symbol("BCHUSDT")
    for feat in ("fracdiff_d05_close", "regime_momentum_signed_3d", "hurst_drift_50_200"):
        assert feat not in result, (
            f"BCHUSDT: {feat} FOUND — must be ABSENT at iter-v3/054 (PARKED). Got: {result}"
        )


def test_algo_fallback_14() -> None:
    """ALGOUSDT must return 14 features via fallback at iter-v3/054.

    ALGO is NOT in V3_MODELS at iter-v3/054 (SYSTEM-LEVEL REVERT) but V3_FEATURES_PER_SYMBOL
    is empty and features_for_symbol still returns the universal list for ALGO.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 14, (
        f"ALGOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/054), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 14-feature set exactly at iter-v3/054. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_absent_parked_features() -> None:
    """ALGOUSDT must reflect /054 state (fracdiff ABSENT; 3d ABSENT; hurst_drift ABSENT)."""
    result = features_for_symbol("ALGOUSDT")
    for feat in ("fracdiff_d05_close", "regime_momentum_signed_3d", "hurst_drift_50_200"):
        assert feat not in result, (
            f"ALGOUSDT: {feat} FOUND — must be ABSENT at iter-v3/054 (PARKED). Got: {result}"
        )


def test_ldo_fallback_14() -> None:
    """LDOUSDT must return 14 features via fallback at iter-v3/054."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/054), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 14-feature set exactly at iter-v3/054. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_absent_parked_features() -> None:
    """LDOUSDT must reflect /054 state (fracdiff ABSENT; 3d ABSENT; hurst_drift ABSENT)."""
    result = features_for_symbol("LDOUSDT")
    for feat in (
        "fracdiff_d05_close",
        "regime_momentum_signed_3d",
        "hurst_drift_50_200",
        "cross_asset_divergence_norm",
    ):
        assert feat not in result, (
            f"LDOUSDT: {feat} FOUND — must be ABSENT at iter-v3/054. Got: {result}"
        )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback at iter-v3/054."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/054), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 14. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly at iter-v3/054. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_dead_features() -> None:
    """TRXUSDT must NOT include dead-code features at iter-v3/054.

    fracdiff_d05_close PARKED at /052; regime_momentum_signed_3d PARKED at /053;
    hurst_drift_50_200 PARKED at /054.
    Dead-code = features that were NEGATIVE/FALSIFIED and removed from universal list.
    """
    result = features_for_symbol("TRXUSDT")
    for feat in (
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
        "efficiency_ratio_50",
        "fracdiff_d05_close",
        "regime_momentum_signed_3d",
        "hurst_drift_50_200",
    ):
        assert feat not in result, (
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/054 "
            f"(dead-code or PARKED). Got: {result}"
        )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/054 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/054. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/054 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/054. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/054 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/054. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/054 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/054. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/054 (SYSTEM-LEVEL REVERT)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/054 (SYSTEM-LEVEL REVERT). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/054.

    SYSTEM-LEVEL REVERT: was ALGOUSDT→(2.0,1.5) + LDOUSDT→(2.0,1.5) at /047-/050.
    per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10:
    second-cycle confirmation of per-symbol-customization anti-pattern at /039 + /050.
    Both ALGOUSDT and LDOUSDT entries REVERTED.
    """
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/054. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: "
        f"{dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"SYSTEM-LEVEL REVERT to iter-v3/028 architecture per "
        f"`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10."
    )


def test_all_symbols_atr_default_iter_v3_051() -> None:
    """All 3 active symbols (BCH/LDO/TRX) must return (2.0, 1.0) via DEFAULT at iter-v3/054.

    SYSTEM-LEVEL REVERT: per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10.
    """
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/054: DEFAULT unchanged. Verify features_v3/__init__.py."
    )
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        result = atr_multipliers_for_symbol(sym)
        assert result == (2.0, 1.0), (
            f"atr_multipliers_for_symbol('{sym}') returned {result} — expected (2.0, 1.0). "
            "iter-v3/054 SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
            "all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback."
        )
    algo_atr = atr_multipliers_for_symbol("ALGOUSDT")
    assert algo_atr == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('ALGOUSDT') returned {algo_atr} — expected (2.0, 1.0). "
        "iter-v3/054 SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
        "ALGO uses DEFAULT fallback."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/054.

    feedback_v3_engineered_features_proven.md mandate ACTIVE through iter-v3/054.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/054. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/054.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate); KEPT at iter-v3/043-054.
    """
    assert "sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/054 (RESTORED iter-v3/042; KEPT iter-v3/043-054). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_ret_skew_50_in_universal_list() -> None:
    """ret_skew_50 MUST be PRESENT in V3_FEATURE_COLUMNS_TOP_N at iter-v3/058.

    iter-v3/058: RE-ANCHOR — REVERT /057 A4 base-stack SWAP. ret_skew_50 RESTORED
    to /028 BASELINE_V3.md composition. parkinson_gk_ratio_20 REVERTED (compute
    function retained as dead code for future cycle 1+ use).
    """
    assert "ret_skew_50" in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/058 (RE-ANCHOR: REVERT /057 SWAP; restore /028 BASELINE_V3.md composition). "
        "Add 'ret_skew_50' to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert "parkinson_gk_ratio_20" not in V3_FEATURE_COLUMNS_TOP_N, (
        "parkinson_gk_ratio_20 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/058 (RE-ANCHOR: /057 SWAP REVERTED; compute function retained as "
        "dead code for future cycle 1+ use). "
        "Remove 'parkinson_gk_ratio_20' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_efficiency_ratio_50_not_in_universal_list() -> None:
    """efficiency_ratio_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/054 (DROPPED)."""
    assert "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/054 (DROPPED iter-v3/044: DISASTROUS NEGATIVE IS -0.8445 / OOS -0.8990). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_regime_momentum_signed_3d_not_in_universal_list() -> None:  # noqa: N802
    """regime_momentum_signed_3d MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/054.

    PARKED per /053 PATH C-suspicious; Critic FINAL `34cc46f` rec #2.
    """
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/054 (PARKED per /052 PATH C-suspicious; Critic `34cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_fracdiff_in_universal_list() -> None:
    """fracdiff_d05_close MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/054 (PARKED)."""
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/054 (PARKED per /051 EXPLORATION-NULL-RESULT + Critic `32cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
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
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/054.

    CHANGED from iter-v3/053 `test_universal_list_is_15` (was 15).
    iter-v3/054: hurst_drift_50_200 PARKED (15 → 14 REVERT). 14-feature base stack restored.
    Single axis change for /054: ADD per-symbol drawdown brake (primitive 11), NOT a feature.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14 at iter-v3/054. "
        f"iter-v3/054: hurst_drift_50_200 PARKED (15→14; /053 PATH D + Critic `c056354`). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_14(symbol: str) -> None:
    """All 3 active V3_MODELS symbols must return exactly 14 features at iter-v3/054.

    CHANGED from iter-v3/053 `test_all_symbols_fallback_15` (was 15).
    iter-v3/054: 14 features (hurst_drift_50_200 PARKED). Parametrized over BCH/LDO/TRX.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/054), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list = 14 (14-anchor base stack; hurst_drift_50_200 PARKED)."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (14 features at iter-v3/054).

    iter-v3/054: hurst_drift_50_200 PARKED; regime_momentum_signed_3d PARKED;
    fracdiff_d05_close PARKED.
    """
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 14, (
        f"Unknown symbol fallback should be 14 features at iter-v3/054, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (14 features)."
    )
    for feat in (
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
        "efficiency_ratio_50",
        "fracdiff_d05_close",
        "regime_momentum_signed_3d",
        "hurst_drift_50_200",
        "parkinson_gk_ratio_20",  # iter-v3/058: RE-ANCHOR REVERT — ABSENT (reverted from /057)
    ):
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (dead-code, PARKED, or REVERTED). "
            f"Got: {result}"
        )
    assert "regime_momentum_signed_5d" in result, (
        "regime_momentum_signed_5d must be in fallback at iter-v3/058 (mandate ACTIVE). "
        "feedback_v3_engineered_features_proven.md mandate UPHELD."
    )
    assert "sym_vs_btc_ret_7d" in result, (
        "sym_vs_btc_ret_7d must be in fallback at iter-v3/058 (RESTORED iter-v3/042; KEPT)."
    )
    assert "ret_skew_50" in result, (
        "ret_skew_50 must be PRESENT in fallback at iter-v3/058 "
        "(RE-ANCHOR: RESTORED from /028 BASELINE_V3.md; /057 SWAP REVERTED)."
    )
