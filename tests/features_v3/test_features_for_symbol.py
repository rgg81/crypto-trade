"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/076.

iter-v3/076 state (cycle-2 EXPLORATION #6 — NEW feature range_efficiency_50):
- V3_FEATURE_COLUMNS_TOP_N: 15 features.
  14 BASELINE_V3 anchor features + range_efficiency_50 (a sign-invariant
  Kaufman-style trend-efficiency feature; the cycle-2 EXPLORATION #6 axis).
  range_efficiency_50 added on its own EDA backing (SHA 40b6e66) per
  feedback_v3_axis_selection_quant_discipline.md.
- V3_FEATURES_PER_SYMBOL is EMPTY. All 3 symbols (BCH/LDO/TRX) use 15-feature fallback.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT carry-forward from /051).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /051).
- block_long_for = () — primitive 10 REVERTED at iter-v3/051 (carry-forward).

iter-v3/063 NEW features REVERTED at /064 (kept-implemented; not in V3_FEATURE_COLUMNS_TOP_N):
  candle_dow_sin, candle_dow_cos, ret_1d, sym_vs_btc_ret_3d, sym_vs_btc_vol_14d,
  taker_buy_imbalance_20, trend_efficiency_signed, vol_regime_x_momentum.
These 8 features remain implemented in features_v3/ modules and parquets (zero revert cost).
They can be considered for phased-mass-expansion #2+ individually.

Permanently excluded features (catastrophic results; never re-evaluated):
  vol_adj_autocorr (IS collapse /026), efficiency_ratio_50 (DISASTROUS /043),
  regime_momentum_signed_3d (PARKED /053), vwap_dev_50 (Critic rec),
  vol_normalized_ret_5d (DROPPED /049), hurst_drift_50_200 (PARKED /053).

Mandatory test cases (iter-v3/064 state):
 1. test_bch_fallback_15             — BCH returns 15 features via fallback
 2. test_bch_absent_dead_features    — BCH does NOT include catastrophic-dead features
 3. test_algo_fallback_15            — ALGO returns 15 features via fallback
 4. test_algo_absent_dead_features   — ALGO does NOT include catastrophic-dead features
 5. test_ldo_fallback_15             — LDO returns 15 features via fallback
 6. test_ldo_absent_dead_features    — LDO does NOT include catastrophic-dead features
 7. test_trx_fallback_15             — TRX returns 15 features via fallback
 8. test_trx_no_dead_features        — TRX does NOT include catastrophically-dead features
 9. test_bchusdt_not_in_per_symbol   — BCH absent from V3_FEATURES_PER_SYMBOL
10. test_algousdt_not_in_per_symbol  — ALGO absent from V3_FEATURES_PER_SYMBOL
11. test_ldousdt_not_in_per_symbol   — LDO absent from V3_FEATURES_PER_SYMBOL
12. test_trxusdt_not_in_per_symbol   — TRX absent from V3_FEATURES_PER_SYMBOL
13. test_v3_features_per_symbol_is_empty — empty dict
14. test_v3_atr_multipliers_per_symbol_is_empty — EMPTY (REVERT from /047-/050 state)
15. test_all_symbols_atr_default_iter_v3_070     — all 3 syms return (2.0, 1.0) post-revert
16. test_regime_momentum_in_universal_list       — mandate ACTIVE
17. test_sym_vs_btc_ret_7d_in_universal_list     — RESTORED iter-v3/042; KEPT
18. test_ret_skew_50_in_universal_list           — RESTORED iter-v3/058; KEPT
19. test_efficiency_ratio_50_not_in_universal_list — DROPPED iter-v3/044
20. test_regime_momentum_signed_3d_not_in_universal_list — PARKED /053
21. test_vol_adj_autocorr_not_in_universal_list  — dead code
22. test_vwap_dev_50_not_in_universal_list       — Critic rec (IC 0.875 with ema_spread)
23. test_universal_list_is_15                    — 15 features at iter-v3/064
24. test_all_symbols_fallback_15                 — parametrized; BCH/LDO/TRX all 15 features
25. test_features_for_symbol_unknown_fallback    — unknown sym falls back to 15-feature list
26. test_baseline_v3_features_all_present        — all 14 BASELINE_V3 features preserved
27. test_adx_14_in_universal_list                — adx_14 PRESENT (PHASED-MASS-EXPANSION #1)
28. test_iter_063_new_features_reverted          — 8 of 9 /063-NEW features ABSENT at /064
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

# 14 BASELINE_V3 features — MUST all be present at iter-v3/064
_BASELINE_V3_FEATURES = frozenset(
    [
        "max_dd_window_50",
        "ret_skew_200",
        "ret_skew_50",
        "ret_kurt_200",
        "ret_kurt_50",
        "range_realized_vol_50",
        "vwap_dev_20",
        "btc_ret_14d",
        "sym_vs_btc_ret_7d",
        "ret_autocorr_lag1_50",
        "ema_spread_atr_20",
        "hurst_100",
        "hurst_diff_100_50",
        "regime_momentum_signed_5d",
    ]
)

# Catastrophically-bad features — MUST remain ABSENT forever
_CATASTROPHIC_DEAD = frozenset(
    [
        "vol_adj_autocorr",  # IS collapse iter-v3/026
        "efficiency_ratio_50",  # DISASTROUS NEGATIVE iter-v3/043
        "regime_momentum_signed_3d",  # PARKED iter-v3/053 PATH C-suspicious
        "vwap_dev_50",  # Critic FINAL SHA a544621 rec #1
        "vol_normalized_ret_5d",  # DROPPED iter-v3/049 PATH C-clean
        "hurst_drift_50_200",  # PARKED iter-v3/053 PATH D Critic c056354
    ]
)

# iter-v3/063 NEW features REVERTED at /064 — REMAIN-implemented but ABSENT from feature list
_ITER_063_NEW_REVERTED = frozenset(
    [
        "candle_dow_sin",
        "candle_dow_cos",
        "ret_1d",
        "sym_vs_btc_ret_3d",
        "sym_vs_btc_vol_14d",
        "taker_buy_imbalance_20",
        "trend_efficiency_signed",
        "vol_regime_x_momentum",
    ]
)


def test_bch_fallback_15() -> None:
    """BCHUSDT must return 15 features via fallback at iter-v3/076.

    BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty); BCH uses the
    V3_FEATURE_COLUMNS_TOP_N fallback = 15 features (14 BASELINE_V3 anchor +
    range_efficiency_50, the iter-v3/076 cycle-2 EXPLORATION #6 axis).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 15, (
        f"BCHUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/076), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_absent_dead_features() -> None:
    """BCHUSDT MUST NOT include catastrophic-dead features at /065."""
    result = features_for_symbol("BCHUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"BCHUSDT: {feat} FOUND — must be ABSENT at iter-v3/076 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_algo_fallback_15() -> None:
    """ALGOUSDT must return 15 features via fallback at iter-v3/076.

    ALGO is NOT in V3_MODELS but V3_FEATURES_PER_SYMBOL is empty and
    features_for_symbol returns the universal 15-feature list for ALGO.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 15, (
        f"ALGOUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/076), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_absent_dead_features() -> None:
    """ALGOUSDT must reflect /065 state (catastrophic-dead features ABSENT)."""
    result = features_for_symbol("ALGOUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"ALGOUSDT: {feat} FOUND — must be ABSENT at iter-v3/076 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_ldo_fallback_15() -> None:
    """LDOUSDT returns 15 features via fallback at iter-v3/076 (14 anchor + range_efficiency)."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 15, (
        f"LDOUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/076), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_absent_dead_features() -> None:
    """LDOUSDT must reflect /065 state (catastrophic-dead features ABSENT)."""
    result = features_for_symbol("LDOUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"LDOUSDT: {feat} FOUND — must be ABSENT at iter-v3/076 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_trx_fallback_15() -> None:
    """TRXUSDT returns 15 features via fallback at iter-v3/076 (14 anchor + range_efficiency)."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 15, (
        f"TRXUSDT: expected 15 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/076), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 15. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_dead_features() -> None:
    """TRXUSDT must NOT include catastrophic-dead features at iter-v3/076."""
    result = features_for_symbol("TRXUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/076 "
            f"(catastrophic-dead). Got: {result}"
        )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/076 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/076. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/076 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/076. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/076 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/076. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/076 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/076. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/076 (SYSTEM-LEVEL carry-forward)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/076. "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/076.

    SYSTEM-LEVEL REVERT carry-forward from iter-v3/051.
    """
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/076. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: "
        f"{dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"SYSTEM-LEVEL REVERT to iter-v3/028 architecture per "
        f"`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10."
    )


def test_all_symbols_atr_default_iter_v3_070() -> None:
    """All 3 active symbols (BCH/LDO/TRX) must return (2.0, 1.0) via DEFAULT at iter-v3/070.

    iter-v3/070 CYCLE 1 CONFIRMATION CLOSEOUT: Component A (/065 universal SL widening
    (2.0, 1.5)) was REJECTED — the IS-collapse + OOS-soar pattern persisted at multi-seed
    (IS Sharpe -0.97; OOS/IS ratio 10.81). (2.0, 1.5) → (2.0, 1.0) REVERTED to the /059
    canonical anchor. See diary-v3/iteration_v3-070.md Section 6 + Section 7.
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; all 3 symbols fall back to DEFAULT = (2.0, 1.0).
    """
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/070 CLOSEOUT: Component A (/065 SL widening) REJECTED; reverted to /059 anchor. "
        "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
    )
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        result = atr_multipliers_for_symbol(sym)
        assert result == (2.0, 1.0), (
            f"atr_multipliers_for_symbol('{sym}') returned {result} — expected (2.0, 1.0). "
            "iter-v3/070 CLOSEOUT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
            "all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback."
        )
    algo_atr = atr_multipliers_for_symbol("ALGOUSDT")
    assert algo_atr == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('ALGOUSDT') returned {algo_atr} — expected (2.0, 1.0). "
        "iter-v3/070: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; ALGO uses DEFAULT fallback."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/064.

    feedback_v3_engineered_features_proven.md mandate ACTIVE through iter-v3/064.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT "
        "at iter-v3/064. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/064.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate); KEPT through iter-v3/064.
    """
    assert "sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/064 (RESTORED iter-v3/042; KEPT iter-v3/043-064). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_ret_skew_50_in_universal_list() -> None:
    """ret_skew_50 MUST be PRESENT in V3_FEATURE_COLUMNS_TOP_N at iter-v3/064.

    iter-v3/058: RE-ANCHOR — REVERT /057 A4 base-stack SWAP. ret_skew_50 RESTORED.
    KEPT through iter-v3/064.
    """
    assert "ret_skew_50" in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/064 (RE-ANCHOR at /058; KEPT through /064). "
        "Add 'ret_skew_50' to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_efficiency_ratio_50_not_in_universal_list() -> None:
    """efficiency_ratio_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N (DROPPED, not re-evaluated)."""
    assert "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/064 (DROPPED iter-v3/044: DISASTROUS NEGATIVE IS -0.8445 / OOS -0.8990; "
        "NOT re-evaluated at /063 either). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_regime_momentum_signed_3d_not_in_universal_list() -> None:  # noqa: N802
    """regime_momentum_signed_3d MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/064.

    PARKED per /053 PATH C-suspicious; Critic FINAL `34cc46f` rec #2. NOT re-evaluated.
    """
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/064 (PARKED per /052 PATH C-suspicious; Critic `34cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (catastrophic IS collapse)."""
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/064. "
        "IS collapse at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS ratio)."
    )


def test_vwap_dev_50_not_in_universal_list() -> None:
    """vwap_dev_50 must NOT be in V3_FEATURE_COLUMNS_TOP_N (Critic rec; IC 0.875 ema_spread)."""
    assert "vwap_dev_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vwap_dev_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/064. "
        "Dropped per Critic FINAL SHA a544621 (Recommendation 1; IC 0.875 with ema_spread_atr_20)."
    )


def test_universal_list_is_15() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 15 features at iter-v3/076.

    CHANGED from iter-v3/064 `test_universal_list_is_15` (was 15 with adx_14).
    iter-v3/064 closeout: adx_14 REMOVED (NEGATIVE per Critic `452fcf2`).
    V3_FEATURE_COLUMNS_TOP_N reverted to 14 BASELINE_V3 features (commit `04080c4`).
    iter-v3/076: cycle-2 EXPLORATION #6 — NEW feature range_efficiency_50; count = 15.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 15 at iter-v3/076 "
        f"(14 BASELINE_V3 anchor features + range_efficiency_50, the cycle-2 "
        f"EXPLORATION #6 axis). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_15(symbol: str) -> None:
    """All 3 active V3_MODELS symbols must return exactly 15 features at iter-v3/076.

    CHANGED from iter-v3/064 `test_all_symbols_fallback_15` (was 15).
    iter-v3/076: 15 features (14 BASELINE_V3 anchor + range_efficiency_50).
    Parametrized over BCH/LDO/TRX.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 15, (
        f"{symbol}: expected 15 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/076), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list = 15 (14 BASELINE_V3 anchor + range_efficiency_50)."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (15 features at iter-v3/076).

    iter-v3/064 closeout: adx_14 REMOVED. Feature count reverted to 14.
    iter-v3/076: cycle-2 EXPLORATION #6 — feature count = 15.
    """
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 15, (
        f"Unknown symbol fallback should be 15 features at iter-v3/076, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (15 features)."
    )
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (catastrophic-dead). Got: {result}"
        )
    assert "regime_momentum_signed_5d" in result, (
        "regime_momentum_signed_5d must be in fallback at iter-v3/076 (mandate ACTIVE). "
        "feedback_v3_engineered_features_proven.md mandate UPHELD."
    )
    assert "sym_vs_btc_ret_7d" in result, (
        "sym_vs_btc_ret_7d must be in fallback at iter-v3/076 (RESTORED iter-v3/042; KEPT)."
    )
    assert "ret_skew_50" in result, (
        "ret_skew_50 must be PRESENT in fallback at iter-v3/076 "
        "(RE-ANCHOR from /028 BASELINE_V3.md; KEPT through /065)."
    )
    assert "adx_14" not in result, (
        "adx_14 must be ABSENT in fallback at iter-v3/076 "
        "(REMOVED at /064 closeout per Critic FINAL `452fcf2`)."
    )


def test_baseline_v3_features_all_present() -> None:
    """ALL 14 BASELINE_V3 features must be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/076.

    iter-v3/076: cycle-2 EXPLORATION #6. Feature count = 15.
    All 14 BASELINE_V3 features preserved (adx_14 removed at /064 closeout).
    """
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _BASELINE_V3_FEATURES - feature_set
    assert not missing, (
        f"BASELINE_V3 features missing from V3_FEATURE_COLUMNS_TOP_N at iter-v3/076: "
        f"{sorted(missing)}. All 14 BASELINE_V3 features must be preserved. "
        f"Add missing features to V3_FEATURE_COLUMNS_TOP_N."
    )


def test_adx_14_absent_from_universal_list() -> None:
    """adx_14 MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/076.

    iter-v3/064 closeout: adx_14 REMOVED (NEGATIVE per Critic FINAL `452fcf2`).
    Cycle 1 #6+ pivots to NON-FEATURE axes per Critic /064 Rec #4.
    V3_FEATURE_COLUMNS_TOP_N reverted to 14 BASELINE_V3 features (commit `04080c4`).
    iter-v3/076: NON-FEATURE axis (universal SL widening); adx_14 remains ABSENT.
    """
    assert "adx_14" not in V3_FEATURE_COLUMNS_TOP_N, (
        "adx_14 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/076. "
        "adx_14 was REMOVED at iter-v3/064 closeout (NEGATIVE per Critic `452fcf2`). "
        "Remove 'adx_14' from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_iter_063_new_features_reverted() -> None:
    """All 9 iter-v3/063 NEW features must be ABSENT at iter-v3/076.

    iter-v3/064 PHASED MASS-EXPANSION #1: only adx_14 was retained, then REMOVED at /064 closeout.
    iter-v3/076: NON-FEATURE axis; all /063 mass-expansion features remain ABSENT.
    They remain implemented in features_v3/ modules (zero revert cost) but
    are NOT in V3_FEATURE_COLUMNS_TOP_N for /065.
    """
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    found = _ITER_063_NEW_REVERTED & feature_set
    assert not found, (
        f"iter-v3/063 NEW features FOUND in V3_FEATURE_COLUMNS_TOP_N at /065: {sorted(found)}. "
        "These features should be ABSENT (kept-implemented; ABSENT from feature list) at "
        "iter-v3/076 NON-FEATURE axis. "
        "Per amended `feedback_v3_mass_feature_expansion.md` (2026-05-14)."
    )
