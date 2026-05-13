"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/063 (UPDATED from /054).

iter-v3/063 state (MASS FEATURE EXPANSION — 14 → 48 features; Path B EDA SHA c833f48):
- V3_FEATURE_COLUMNS_TOP_N: 48 features.
  14 BASELINE_V3 mandatory + 34 promoted from parquet + 9 NEW implementations.
  IC pruning: greedy LDP-style; 22 dropped at |IC|>0.70 (non-carveout pairs).
  ADF: 1 drop (candle_hour_sin — constant at 8h cadence).
  User-approved 48 < 50 mandate deviation (methodology > strict count per LDP).
- V3_FEATURES_PER_SYMBOL is EMPTY. All 3 symbols (BCH/LDO/TRX) use 48-feature fallback.
- V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT carry-forward from /051).
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED from /051).
- block_long_for = ("BCHUSDT",) — primitive 10 (BCH LONG direction block).

Re-evaluated features at /063 (previously closed; re-included under mass-expansion mandate
+ post-WF-fix landscape; documented in brief Section 3 adversarial flags):
  fracdiff_d05_close (PARKED /052), cross_asset_divergence_norm (dead code /028),
  hurst_drift_50_200 (PARKED /053), vol_normalized_ret_5d (DROPPED /049),
  funding_rate_zscore_30 (CLOSED /024), btc_funding_rate_zscore_30 (CLOSED /025),
  tbr_zscore_30 (DROPPED /016).

Permanently excluded features (catastrophic results; never re-evaluated):
  vol_adj_autocorr (IS collapse /026), efficiency_ratio_50 (DISASTROUS /043),
  regime_momentum_signed_3d (PARKED /053), vwap_dev_50 (Critic rec).

Mandatory test cases (iter-v3/063 state):
 1. test_bch_fallback_48             — BCH returns 48 features via fallback
 2. test_bch_absent_dead_features    — BCH does NOT include catastrophic-dead features
 3. test_algo_fallback_48            — ALGO returns 48 features via fallback
 4. test_algo_absent_dead_features   — ALGO does NOT include catastrophic-dead features
 5. test_ldo_fallback_48             — LDO returns 48 features via fallback
 6. test_ldo_absent_dead_features    — LDO does NOT include catastrophic-dead features
 7. test_trx_fallback_48             — TRX returns 48 features via fallback
 8. test_trx_no_dead_features        — TRX does NOT include catastrophically-dead features
 9. test_bchusdt_not_in_per_symbol   — BCH absent from V3_FEATURES_PER_SYMBOL
10. test_algousdt_not_in_per_symbol  — ALGO absent from V3_FEATURES_PER_SYMBOL
11. test_ldousdt_not_in_per_symbol   — LDO absent from V3_FEATURES_PER_SYMBOL
12. test_trxusdt_not_in_per_symbol   — TRX absent from V3_FEATURES_PER_SYMBOL
13. test_v3_features_per_symbol_is_empty — empty dict
14. test_v3_atr_multipliers_per_symbol_is_empty — EMPTY (REVERT from /047-/050 state)
15. test_all_symbols_atr_default_iter_v3_063     — all 3 syms return (2.0, 1.0)
16. test_regime_momentum_in_universal_list       — mandate ACTIVE
17. test_sym_vs_btc_ret_7d_in_universal_list     — RESTORED iter-v3/042; KEPT
18. test_ret_skew_50_in_universal_list           — RESTORED iter-v3/058; KEPT
19. test_efficiency_ratio_50_not_in_universal_list — DROPPED iter-v3/044
20. test_regime_momentum_signed_3d_not_in_universal_list — PARKED /053
21. test_vol_adj_autocorr_not_in_universal_list  — dead code
22. test_vwap_dev_50_not_in_universal_list       — Critic rec (IC 0.875 with ema_spread)
23. test_universal_list_is_48                    — 48 features at iter-v3/063
24. test_all_symbols_fallback_48                 — parametrized; BCH/LDO/TRX all 48 features
25. test_features_for_symbol_unknown_fallback    — unknown sym falls back to 48-feature list
26. test_baseline_v3_features_all_present        — all 14 BASELINE_V3 features preserved
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

# 14 BASELINE_V3 features — MUST all be present at iter-v3/063
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
    ]
)


def test_bch_fallback_48() -> None:
    """BCHUSDT must return 48 features via fallback at iter-v3/063.

    iter-v3/063: BCHUSDT not in V3_FEATURES_PER_SYMBOL (dict empty).
    BCH uses V3_FEATURE_COLUMNS_TOP_N fallback = 48 features (MASS EXPANSION).
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 48, (
        f"BCHUSDT: expected 48 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/063), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 48. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"BCHUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_bch_absent_dead_features() -> None:
    """BCHUSDT MUST NOT include catastrophic-dead features at /063."""
    result = features_for_symbol("BCHUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"BCHUSDT: {feat} FOUND — must be ABSENT at iter-v3/063 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_algo_fallback_48() -> None:
    """ALGOUSDT must return 48 features via fallback at iter-v3/063.

    ALGO is NOT in V3_MODELS at iter-v3/063 but V3_FEATURES_PER_SYMBOL is empty
    and features_for_symbol still returns the universal 48-feature list for ALGO.
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 48, (
        f"ALGOUSDT: expected 48 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/063), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 48. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"ALGOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_algo_absent_dead_features() -> None:
    """ALGOUSDT must reflect /063 state (catastrophic-dead features ABSENT)."""
    result = features_for_symbol("ALGOUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"ALGOUSDT: {feat} FOUND — must be ABSENT at iter-v3/063 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_ldo_fallback_48() -> None:
    """LDOUSDT must return 48 features via fallback at iter-v3/063."""
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 48, (
        f"LDOUSDT: expected 48 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/063), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 48. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_absent_dead_features() -> None:
    """LDOUSDT must reflect /063 state (catastrophic-dead features ABSENT)."""
    result = features_for_symbol("LDOUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"LDOUSDT: {feat} FOUND — must be ABSENT at iter-v3/063 (catastrophic-dead). "
            f"Got: {result}"
        )


def test_trx_fallback_48() -> None:
    """TRXUSDT must return 48 features via fallback at iter-v3/063."""
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 48, (
        f"TRXUSDT: expected 48 features (V3_FEATURE_COLUMNS_TOP_N fallback at iter-v3/063), "
        f"got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + universal list = 48. "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_dead_features() -> None:
    """TRXUSDT must NOT include catastrophic-dead features at iter-v3/063."""
    result = features_for_symbol("TRXUSDT")
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"TRXUSDT: {feat} FOUND — must be ABSENT at iter-v3/063 "
            f"(catastrophic-dead). Got: {result}"
        )


def test_bchusdt_not_in_per_symbol() -> None:
    """BCHUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/063 (empty dict)."""
    assert "BCHUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/063. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_algousdt_not_in_per_symbol() -> None:
    """ALGOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/063 (empty dict)."""
    assert "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'ALGOUSDT' key — must be ABSENT at iter-v3/063. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/063 (empty dict)."""
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/063. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/063 (empty dict)."""
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/063. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_v3_features_per_symbol_is_empty() -> None:
    """V3_FEATURES_PER_SYMBOL must be EMPTY at iter-v3/063 (SYSTEM-LEVEL carry-forward)."""
    assert len(V3_FEATURES_PER_SYMBOL) == 0, (
        f"V3_FEATURES_PER_SYMBOL must be empty at iter-v3/063. "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}. "
        f"Clear V3_FEATURES_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_v3_atr_multipliers_per_symbol_is_empty() -> None:
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/063.

    SYSTEM-LEVEL REVERT carry-forward from iter-v3/051.
    """
    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/063. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: "
        f"{dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"SYSTEM-LEVEL REVERT to iter-v3/028 architecture per "
        f"`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10."
    )


def test_all_symbols_atr_default_iter_v3_063() -> None:
    """All 3 active symbols (BCH/LDO/TRX) must return (2.0, 1.0) via DEFAULT at iter-v3/063.

    SYSTEM-LEVEL REVERT carry-forward from iter-v3/051.
    """
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/063: DEFAULT unchanged. Verify features_v3/__init__.py."
    )
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        result = atr_multipliers_for_symbol(sym)
        assert result == (2.0, 1.0), (
            f"atr_multipliers_for_symbol('{sym}') returned {result} — expected (2.0, 1.0). "
            "iter-v3/063 SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; "
            "all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback."
        )
    algo_atr = atr_multipliers_for_symbol("ALGOUSDT")
    assert algo_atr == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('ALGOUSDT') returned {algo_atr} — expected (2.0, 1.0). "
        "iter-v3/063: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; ALGO uses DEFAULT fallback."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/063.

    feedback_v3_engineered_features_proven.md mandate ACTIVE through iter-v3/063.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT "
        "at iter-v3/063. feedback_v3_engineered_features_proven.md mandate ACTIVE. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_sym_vs_btc_ret_7d_in_universal_list() -> None:
    """sym_vs_btc_ret_7d MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/063.

    RESTORED at iter-v3/042 (iter-v3/041 Path C mandate); KEPT through iter-v3/063.
    """
    assert "sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS_TOP_N, (
        "sym_vs_btc_ret_7d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/063 (RESTORED iter-v3/042; KEPT iter-v3/043-063). "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_ret_skew_50_in_universal_list() -> None:
    """ret_skew_50 MUST be PRESENT in V3_FEATURE_COLUMNS_TOP_N at iter-v3/063.

    iter-v3/058: RE-ANCHOR — REVERT /057 A4 base-stack SWAP. ret_skew_50 RESTORED.
    KEPT through iter-v3/063.
    """
    assert "ret_skew_50" in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT at "
        "iter-v3/063 (RE-ANCHOR at /058; KEPT through /063). "
        "Add 'ret_skew_50' to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_efficiency_ratio_50_not_in_universal_list() -> None:
    """efficiency_ratio_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N (DROPPED, not re-evaluated)."""
    assert "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "efficiency_ratio_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at "
        "iter-v3/063 (DROPPED iter-v3/044: DISASTROUS NEGATIVE IS -0.8445 / OOS -0.8990; "
        "NOT re-evaluated at /063; the SIGNED variant trend_efficiency_signed is SEPARATE). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_regime_momentum_signed_3d_not_in_universal_list() -> None:  # noqa: N802
    """regime_momentum_signed_3d MUST be ABSENT from V3_FEATURE_COLUMNS_TOP_N at iter-v3/063.

    PARKED per /053 PATH C-suspicious; Critic FINAL `34cc46f` rec #2. NOT re-evaluated.
    """
    assert "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_3d FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/063 (PARKED per /052 PATH C-suspicious; Critic `34cc46f` rec #2). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (catastrophic IS collapse)."""
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/063. "
        "IS collapse at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS ratio). "
        "NOT re-evaluated at /063 mass expansion."
    )


def test_vwap_dev_50_not_in_universal_list() -> None:
    """vwap_dev_50 must NOT be in V3_FEATURE_COLUMNS_TOP_N (Critic rec; IC 0.875 ema_spread)."""
    assert "vwap_dev_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vwap_dev_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/063. "
        "Dropped per Critic FINAL SHA a544621 (Recommendation 1; IC 0.875 with ema_spread_atr_20)."
    )


def test_universal_list_is_48() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 48 features at iter-v3/063.

    CHANGED from iter-v3/054 `test_universal_list_is_14` (was 14).
    iter-v3/063: MASS FEATURE EXPANSION 14 → 48 (Path B EDA SHA c833f48).
    14 BASELINE_V3 preserved + 34 promoted from parquet + 9 NEW implementations.
    User-approved 48 < 50 mandate deviation (LDP IC-pruning Pareto-optimum).
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 48, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 48 at iter-v3/063. "
        f"iter-v3/063: MASS FEATURE EXPANSION 14 → 48 (Path B per EDA SHA c833f48). "
        f"Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
    )


@pytest.mark.parametrize("symbol", ["BCHUSDT", "LDOUSDT", "TRXUSDT"])
def test_all_symbols_fallback_48(symbol: str) -> None:
    """All 3 active V3_MODELS symbols must return exactly 48 features at iter-v3/063.

    CHANGED from iter-v3/054 `test_all_symbols_fallback_14` (was 14).
    iter-v3/063: 48 features (MASS EXPANSION). Parametrized over BCH/LDO/TRX.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 48, (
        f"{symbol}: expected 48 features (V3_FEATURE_COLUMNS_TOP_N universal fallback at "
        f"iter-v3/063), got {len(result)}. V3_FEATURES_PER_SYMBOL must be empty + "
        f"universal list = 48 (MASS EXPANSION from 14)."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"{symbol}: result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_features_for_symbol_unknown_fallback() -> None:
    """An unknown symbol falls back to V3_FEATURE_COLUMNS_TOP_N (48 features at iter-v3/063)."""
    result = features_for_symbol("XYZUSDT")
    assert result is not None, "features_for_symbol must never return None."
    assert len(result) == 48, (
        f"Unknown symbol fallback should be 48 features at iter-v3/063, got {len(result)}."
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        "Unknown symbol 'XYZUSDT' should fall back to V3_FEATURE_COLUMNS_TOP_N (48 features)."
    )
    for feat in _CATASTROPHIC_DEAD:
        assert feat not in result, (
            f"Unknown symbol fallback must NOT include {feat} (catastrophic-dead). Got: {result}"
        )
    assert "regime_momentum_signed_5d" in result, (
        "regime_momentum_signed_5d must be in fallback at iter-v3/063 (mandate ACTIVE). "
        "feedback_v3_engineered_features_proven.md mandate UPHELD."
    )
    assert "sym_vs_btc_ret_7d" in result, (
        "sym_vs_btc_ret_7d must be in fallback at iter-v3/063 (RESTORED iter-v3/042; KEPT)."
    )
    assert "ret_skew_50" in result, (
        "ret_skew_50 must be PRESENT in fallback at iter-v3/063 "
        "(RE-ANCHOR from /028 BASELINE_V3.md; KEPT through /063)."
    )


def test_baseline_v3_features_all_present() -> None:
    """ALL 14 BASELINE_V3 features must be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/063.

    iter-v3/063 MASS EXPANSION mandate: all 14 BASELINE_V3 features preserved.
    Per brief Section 3 / EDA SHA c833f48 Path B constraints.
    """
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _BASELINE_V3_FEATURES - feature_set
    assert not missing, (
        f"BASELINE_V3 features missing from V3_FEATURE_COLUMNS_TOP_N at iter-v3/063: "
        f"{sorted(missing)}. All 14 BASELINE_V3 features must be preserved in the 48-feature "
        f"expansion. Add missing features to V3_FEATURE_COLUMNS_TOP_N."
    )
