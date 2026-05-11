"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/052 (UPDATED from /051).

iter-v3/052 state (EXPLORATION — cycle 4 #2 — SWAP: regime_momentum_signed_3d ACTIVATED;
                   fracdiff_d05_close PARKED; SYSTEM-LEVEL REVERT carry-forward from /051):
- V3_FEATURE_COLUMNS_TOP_N: 15 features (14-anchor + regime_momentum_signed_3d as 15th).
  SWAP: fracdiff_d05_close DROPPED (PARKED per /051 EXPLORATION-NULL-RESULT +
  Critic FINAL `32cc46f` rec #2); regime_momentum_signed_3d ACTIVATED (/051 EDA RANKED #2
  SHA `290f37b`; ADF p=0 all 4 syms; IC strict-gate PASS max|IC|=0.6192<0.70).
- V3_FEATURES_PER_SYMBOL is EMPTY (REVERT carry-forward). All symbols fall back to 15.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT carry-forward).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /051).
- block_long_for = () (REVERT carry-forward from /051).

History of V3_FEATURE_COLUMNS_TOP_N count:
  iter-v3/040-044: 14 features (anchor).
  iter-v3/051: 15 features (fracdiff_d05_close ADDED — single axis, cycle 4 #1).
  iter-v3/052: 15 features (SWAP: fracdiff PARKED; regime_momentum_signed_3d ACTIVATED).

Mandatory test cases (iter-v3/052 state):
 1. test_bch_fallback_15                 — BCH returns 15 features via fallback
 2. test_bch_has_fracdiff                — BCH does NOT include fracdiff (PARKED at /052)
 3. test_algo_fallback_15               — ALGO returns 15 features via fallback
 4. test_algo_has_fracdiff              — ALGO does NOT include fracdiff (PARKED at /052)
 5. test_ldo_fallback_15               — LDO returns 15 features via fallback
 6. test_ldo_has_fracdiff              — LDO does NOT include fracdiff (PARKED at /052)
 7. test_trx_fallback_15               — TRX returns 15 features via fallback
 8. test_trx_no_dead_features          — TRX does NOT include dead-code features
 9. test_bchusdt_not_in_per_symbol     — BCH absent from V3_FEATURES_PER_SYMBOL
10. test_algousdt_not_in_per_symbol    — ALGO absent from V3_FEATURES_PER_SYMBOL
11. test_ldousdt_not_in_per_symbol     — LDO absent from V3_FEATURES_PER_SYMBOL
12. test_trxusdt_not_in_per_symbol     — TRX absent from V3_FEATURES_PER_SYMBOL
13. test_v3_features_per_symbol_is_empty — empty dict
14. test_v3_atr_multipliers_per_symbol_is_empty — EMPTY (REVERT from /047-/050 state)
15. test_all_symbols_atr_default_iter_v3_051    — all 3 syms return (2.0, 1.0)
16. test_regime_momentum_in_universal_list      — mandate ACTIVE
17. test_sym_vs_btc_ret_7d_in_universal_list    — RESTORED iter-v3/042; KEPT
18. test_ret_skew_50_in_universal_list          — RESTORED iter-v3/042; KEPT
19. test_efficiency_ratio_50_not_in_universal_list — DROPPED iter-v3/044
20. test_regime_momentum_signed_3d_not_in_universal_list — NOW PRESENT (ACTIVATED /052)
21. test_fracdiff_in_universal_list             — NOW ABSENT (PARKED /052)
22. test_cross_asset_divergence_not_in_universal_list — dead code
23. test_vol_adj_autocorr_not_in_universal_list — dead code
24. test_universal_list_is_15               — 15 features at iter-v3/052 (UNCHANGED count)
25. test_all_symbols_fallback_15            — parametrized; BCH/LDO/TRX all 15 features
26. test_features_for_symbol_unknown_fallback — unknown sym falls back to 15-feature list
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


def test_bch_fallback_15() -> None:
    """BCHUSDT must return 15 features via fallback at iter-v3/051.

    iter-v3/051: BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty — SYSTEM-LEVEL REVERT).
    BCH uses V3_FEATURE_COLUMNS_TOP_N fallback = 15 features (14-anchor + fracdiff_d05_close).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 15, (
        f"BCHUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/051), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"BCHUSDT must use the universal 15-feature set at iter-v3/051 (no per-symbol entry). "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_has_fracdiff() -> None:
    """BCHUSDT MUST NOT include fracdiff_d05_close or regime_momentum_signed_3d at /053.

    iter-v3/052 SWAP: fracdiff DROPPED; regime_momentum_signed_3d ACTIVATED.
    iter-v3/053 SWAP: regime_momentum_signed_3d DROPPED (PARKED); hurst_drift_50_200 ACTIVATED.
    """
    result = features_for_symbol("BCHUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"BCHUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/052 SWAP: fracdiff PARKED. Got: {result}"
    )
    assert "regime_momentum_signed_3d" not in result, (
        f"BCHUSDT: regime_momentum_signed_3d FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/053 SWAP: 3d PARKED per /052 PATH C-suspicious closeout. "
        f"Got: {result}"
    )
    assert "hurst_drift_50_200" in result, (
        f"BCHUSDT: hurst_drift_50_200 ABSENT — must be PRESENT at iter-v3/053. "
        f"iter-v3/053 SWAP: hurst_drift_50_200 ACTIVATED as 15th element. "
        f"Got: {result}"
    )


def test_algo_fallback_15() -> None:
    """ALGOUSDT must return 15 features via fallback at iter-v3/051.

    ALGO is NOT in V3_MODELS at iter-v3/051 (SYSTEM-LEVEL REVERT) but V3_FEATURES_PER_SYMBOL
    is empty and features_for_symbol still returns the universal list for ALGO.
    Reserved-for-future per brief Section 3.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 15, (
        f"ALGOUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/051), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"ALGOUSDT must use the universal 15-feature set exactly at iter-v3/051. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_has_fracdiff() -> None:
    """ALGOUSDT must reflect /053 SWAP state (fracdiff ABSENT; 3d ABSENT; hurst_drift PRESENT).

    iter-v3/053 SWAP: regime_momentum_signed_3d PARKED; hurst_drift_50_200 ACTIVATED.
    ALGO not in V3_MODELS at /053 but universal feature list reflects SWAP.
    """
    result = features_for_symbol("ALGOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"ALGOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/052 SWAP: fracdiff PARKED. Got: {result}"
    )
    assert "regime_momentum_signed_3d" not in result, (
        f"ALGOUSDT: regime_momentum_signed_3d FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/053 SWAP: 3d PARKED per /052 PATH C-suspicious. Got: {result}"
    )
    assert "hurst_drift_50_200" in result, (
        f"ALGOUSDT: hurst_drift_50_200 ABSENT — must be PRESENT at iter-v3/053. "
        f"Universal list now has hurst_drift_50_200 as 15th element. Got: {result}"
    )


def test_ldo_fallback_15() -> None:
    """LDOUSDT must return 15 features via fallback at iter-v3/051."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 15, (
        f"LDOUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/051), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 15-feature set exactly at iter-v3/051. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_has_fracdiff() -> None:
    """LDOUSDT must reflect /053 SWAP state (fracdiff ABSENT; 3d ABSENT; hurst_drift PRESENT).

    iter-v3/053 SWAP: regime_momentum_signed_3d PARKED; hurst_drift_50_200 ACTIVATED.
    LDO remains in V3_MODELS (LDO removal pre-falsified by /052 EDA SHA `0a10581`).
    """
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/052 SWAP: fracdiff PARKED. Got: {result}"
    )
    assert "regime_momentum_signed_3d" not in result, (
        f"LDOUSDT: regime_momentum_signed_3d FOUND — must be ABSENT at iter-v3/053. "
        f"iter-v3/053 SWAP: 3d PARKED per /052 PATH C-suspicious. Got: {result}"
    )
    assert "hurst_drift_50_200" in result, (
        f"LDOUSDT: hurst_drift_50_200 ABSENT — must be PRESENT at iter-v3/053. "
        f"Universal SWAP: hurst_drift_50_200 as 15th element. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"Universal application FALSIFIED at iter-v3/027; LDO per-symbol FALSIFIED at /037. "
        f"Got: {result}"
    )


def test_trx_fallback_15() -> None:
    """TRXUSDT must return 15 features via fallback at iter-v3/051."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 15, (
        f"TRXUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/051), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 15-feature set exactly at iter-v3/051. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_dead_features() -> None:
    """TRXUSDT must NOT include dead-code features at iter-v3/053.

    fracdiff_d05_close PARKED at /052; regime_momentum_signed_3d PARKED at /053.
    hurst_drift_50_200 ACTIVATED as 15th element at /053.
    Dead-code = features that were NEGATIVE/FALSIFIED and removed from universal list.
    """
    result = features_for_symbol("TRXUSDT")
    # PARKED/dead-code features — must remain absent from V3_FEATURE_COLUMNS_TOP_N:
    for feat in (
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
        "efficiency_ratio_50",
        "fracdiff_d05_close",
        "regime_momentum_signed_3d",  # PARKED at /053 (was ACTIVATED at /052)
    ):
        assert feat not in result, (
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/053 "
            f"(dead-code or PARKED: falsified/NEGATIVE or dropped via SWAP). Got: {result}"
        )
    # hurst_drift_50_200 IS present at iter-v3/053 (SWAP ACTIVATED)
    assert "hurst_drift_50_200" in result, (
        f"TRXUSDT: hurst_drift_50_200 ABSENT — must be PRESENT at iter-v3/053. "
        f"iter-v3/053 SWAP: hurst_drift_50_200 ACTIVATED as 15th element. Got: {result}"
    )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/051 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/051. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/051 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/051. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/051 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/051. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/051 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/051. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/051 (SYSTEM-LEVEL REVERT)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/051 (SYSTEM-LEVEL REVERT). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/051.

    SYSTEM-LEVEL REVERT: was ALGOUSDT→(2.0,1.5) + LDOUSDT→(2.0,1.5) at /047-/050.
    per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10:
    second-cycle confirmation of per-symbol-customization anti-pattern at /039 + /050.
    Both ALGOUSDT and LDOUSDT entries REVERTED.

    CHANGED from iter-v3/044 `test_v3_atr_multipliers_per_symbol_has_algo`
    which asserted 1 entry (ALGO→(2.0,1.5)).
    """
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/051. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"SYSTEM-LEVEL REVERT to iter-v3/028 architecture per "
        f"`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10."
    )


def test_all_symbols_atr_default_iter_v3_051() -> None:
    """All 3 active symbols (BCH/LDO/TRX) must return (2.0, 1.0) via DEFAULT at iter-v3/051.

    CHANGED from iter-v3/044 `test_non_algo_symbols_atr_default_iter_v3_044`:
    - iter-v3/044: ALGOUSDT→(2.0,1.5), BCH/LDO/TRX DEFAULT (2.0,1.0).
    - iter-v3/051: V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY; ALL symbols use DEFAULT (2.0,1.0).
    - ALGO not in V3_MODELS at /051 (SYSTEM-LEVEL REVERT); but atr_multipliers_for_symbol
      still dispatches DEFAULT for ALGO as fallback.

    SYSTEM-LEVEL REVERT: per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10.
    """
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/051: DEFAULT unchanged. Verify features_v3/__init__.py."
    )
    # Active V3_MODELS at /051:
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        result = atr_multipliers_for_symbol(sym)
        assert result == (2.0, 1.0), (
            f"atr_multipliers_for_symbol('{sym}') returned {result} — expected (2.0, 1.0). "
            "iter-v3/051 SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
            "all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback."
        )
    # ALGO also falls back to DEFAULT (not in V3_MODELS but function should not raise):
    algo_atr = atr_multipliers_for_symbol("ALGOUSDT")
    assert algo_atr == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('ALGOUSDT') returned {algo_atr} — expected (2.0, 1.0). "
        "iter-v3/051 SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
        "ALGO uses DEFAULT fallback (was (2.0,1.5) at /047-/050)."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/051.

    feedback_v3_engineered_features_proven.md mandate ACTIVE through iter-v3/051.
    Restored at iter-v3/042 (iter-v3/041 Path C); KEPT at iter-v3/043-051.

    iter-v3/028 portfolio importance: rank 14/14, importance 390.4 (64.59% of top).
    Despite low importance rank, OOS signal loss confirmed at iter-v3/041 Path C.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/051. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/051.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate); KEPT at iter-v3/043-051.
    iter-v3/028 portfolio importance: rank 13/14, importance 398.0 (65.85% of top).
    """
    assert "sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/051 (RESTORED iter-v3/042; KEPT iter-v3/043-051). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_ret_skew_50_in_universal_list() -> None:
    """ret_skew_50 MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/051.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate); KEPT at iter-v3/043-051.
    iter-v3/028 portfolio importance: rank 12/14, importance 412.8 (68.30% of top).
    """
    assert "ret_skew_50" in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/051 (RESTORED iter-v3/042; KEPT iter-v3/043-051). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_efficiency_ratio_50_not_in_universal_list() -> None:
    """efficiency_ratio_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/051 (DROPPED).

    iter-v3/043 added efficiency_ratio_50 (Kaufman 1995 ER) — DISASTROUS NEGATIVE result
    (IS -0.8445 / OOS -0.8990; all 4 symbols broken). iter-v3/044 dropped it.
    compute_efficiency_ratio_50 retained as dead code in engineered_v3.py; NOT dispatched.
    """
    assert "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/051 (DROPPED iter-v3/044: DISASTROUS NEGATIVE IS -0.8445 / OOS -0.8990). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_regime_momentum_signed_3d_not_in_universal_list() -> None:  # noqa: N802
    """regime_momentum_signed_3d MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/053.

    iter-v3/052 SWAP: ACTIVATED as 15th element.
    iter-v3/053 SWAP: PARKED (PATH C-suspicious; Critic FINAL `34cc46f` rec #2;
    rank 14-15/15 all 3 syms; IS-OOS daily ratio 2.327 OUT-OF-BAND).
    Test name kept for traceability; assertion updated for /053 PARKED state.
    """
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/053 (PARKED per /052 PATH C-suspicious; Critic `34cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_fracdiff_in_universal_list() -> None:
    """fracdiff_d05_close MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/052 (PARKED).

    CHANGED from iter-v3/051 (fracdiff was PRESENT). iter-v3/052 SWAP: fracdiff DROPPED
    from V3_FEATURE_COLUMNS_TOP_N per /051 EXPLORATION-NULL-RESULT + Critic `32cc46f` rec #2.
    compute_fracdiff_d05_close RETAINED in dispatch (column in parquets; zero revert cost).
    Test name kept for traceability; assertion INVERTED for /052.
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/052 (PARKED per /051 EXPLORATION-NULL-RESULT + Critic `32cc46f` rec #2). "
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


def test_universal_list_is_15() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 15 features at iter-v3/051.

    CHANGED from iter-v3/044 `test_universal_list_is_14` (was 14).
    iter-v3/051: 14-anchor + fracdiff_d05_close = 15.
    Single axis change: fracdiff_d05_close ADDED (cycle 4 #1 EXPLORATION).
    System-level REVERT does NOT change the feature count (REVERT only affects
    V3_MODELS, V3_ATR_MULTIPLIERS_PER_SYMBOL, block_long_for, REQUIRED_GAP).
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 15 at iter-v3/051. "
        f"iter-v3/051: 14-anchor + fracdiff_d05_close (ADD axis). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_15(symbol: str) -> None:
    """All 3 active V3_MODELS symbols must return exactly 15 features at iter-v3/051.

    CHANGED from iter-v3/044 `test_all_symbols_fallback_14` (was 14; included ALGO).
    iter-v3/051: 15 features (fracdiff_d05_close ADDED). ALGO not in V3_MODELS (REVERT).
    Parametrized over BCH/LDO/TRX only.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 15, (
        f"{symbol}: expected 15 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/051), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list = 15 (14-anchor + fracdiff_d05_close)."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (15 features at iter-v3/053).

    iter-v3/053 SWAP: hurst_drift_50_200 PRESENT; regime_momentum_signed_3d PARKED (ABSENT);
    fracdiff_d05_close PARKED (ABSENT from model input).
    """
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 15, (
        f"Unknown symbol fallback should be 15 features at iter-v3/053, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (15 features)."
    )
    # Dead-code or PARKED features — must remain absent:
    for feat in (
        "cross_asset_divergence_norm",
        "vol_adj_autocorr",
        "efficiency_ratio_50",  # DROPPED iter-v3/044 — DISASTROUS NEGATIVE
        "fracdiff_d05_close",  # PARKED iter-v3/052 — SWAP dropped from model input
        "regime_momentum_signed_3d",  # PARKED iter-v3/053 — PATH C-suspicious /052
    ):
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (dead-code or PARKED). "
            f"Got: {result}"
        )
    # iter-v3/053: hurst_drift_50_200 MUST be present (SWAP ACTIVATED)
    assert "hurst_drift_50_200" in result, (
        "hurst_drift_50_200 must be in fallback at iter-v3/053 (SWAP ACTIVATED). "
        "V3_FEATURE_COLUMNS_TOP_N[14] = hurst_drift_50_200."
    )
    # iter-v3/044: regime_momentum_signed_5d MUST be present (mandate ACTIVE).
    assert "regime_momentum_signed_5d" in result, (
        "regime_momentum_signed_5d must be in fallback at iter-v3/053 (mandate ACTIVE). "
        "feedback_v3_engineered_features_proven.md mandate UPHELD."
    )
    # iter-v3/042: sym_vs_btc_ret_7d and ret_skew_50 MUST be present (RESTORED; KEPT).
    assert "sym_vs_btc_ret_7d" in result, (
        "sym_vs_btc_ret_7d must be in fallback at iter-v3/053 (RESTORED iter-v3/042; KEPT)."
    )
    assert "ret_skew_50" in result, (
        "ret_skew_50 must be in fallback at iter-v3/053 (RESTORED iter-v3/042; KEPT)."
    )
