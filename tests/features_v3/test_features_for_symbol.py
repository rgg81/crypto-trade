"""Adversarial tests for per-symbol feature-set dispatch — iter-v3/038.

Tests the ``V3_FEATURES_PER_SYMBOL`` dict and the ``features_for_symbol()``
helper introduced in iter-v3/030.

iter-v3/038 state:
- BCHUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15 features.
  UNCHANGED from iter-v3/035. fracdiff_d05_close PRESENT.
- ALGOUSDT: per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15
  features. NEW at iter-v3/038. fracdiff_d05_close PRESENT.
- LDOUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. REVERTED from iter-v3/037.
  No per-symbol entry (iter-v3/037 NEGATIVE: LDO cross_asset_divergence_norm OOS swing ~-33).
- TRXUSDT: fallback to V3_FEATURE_COLUMNS_TOP_N = 14 features. UNCHANGED.
- V3_FEATURES_PER_SYMBOL has exactly 2 entries (BCHUSDT + ALGOUSDT).
- BCH and ALGO per-symbol entries share the same extension feature (fracdiff_d05_close).
- V3_FEATURE_COLUMNS_TOP_N has 14 features (neither fracdiff_d05_close, vol_adj_autocorr,
  nor cross_asset_divergence_norm appear in the universal list).

Evidence:
- iter-v3/034: fracdiff_d05_close universally failed for TRX/ALGO/LDO (-20.11/-8.24/-6.81
  OOS wpnl). BCH-only targeting (iter-v3/035) isolated BCH lift: PROMISING OOS +2.85.
- iter-v3/037: LDO cross_asset_divergence_norm NEGATIVE (~-33 OOS swing); REVERTED at
  iter-v3/038. LDO returns to 14-feature fallback.
- iter-v3/038: ALGO receives fracdiff_d05_close in isolated per-symbol test (specificity probe).
  Scientific purpose: if ALGO benefits → fracdiff BROADLY USEFUL; if not → BCH-SPECIFIC.

Mandatory test cases (iter-v3/038 brief Section 3 sub-fix #4):
1. test_bch_has_fracdiff
2. test_algo_has_fracdiff
3. test_algo_no_cross_asset_divergence
4. test_ldo_fallback_14
5. test_ldo_no_fracdiff_no_cross_asset
6. test_trx_fallback_14
7. test_trx_no_special_features
8. test_bch_per_symbol_entry_has_fracdiff
9. test_algo_per_symbol_entry_has_fracdiff
10. test_bch_algo_per_symbol_entries_same_extension_feature
11. test_ldousdt_not_in_per_symbol
12. test_trxusdt_not_in_per_symbol
13. test_bch_per_symbol_len
14. test_algo_per_symbol_len
15. test_non_bch_algo_fallback_no_special_features (parametrized LDO/TRX)
16. test_non_bch_algo_fallback_len (parametrized LDO/TRX)
17. test_subset_invariant_extended_bch
18. test_subset_invariant_extended_algo
19. test_v3_features_per_symbol_has_two_entries
20. test_regime_momentum_in_universal_list
21. test_fracdiff_not_in_universal_list
22. test_cross_asset_divergence_not_in_universal_list
23. test_vol_adj_autocorr_not_in_universal_list
24. test_universal_list_is_14
25. test_features_for_symbol_unknown_fallback
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
    UNCHANGED from iter-v3/035 through iter-v3/038.
    """
    result = features_for_symbol("BCHUSDT")
    assert len(result) == 15, (
        f"BCHUSDT: expected 15 features (BCH per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['BCHUSDT'] should be V3_FEATURE_COLUMNS_TOP_N + fracdiff."
    )
    assert "fracdiff_d05_close" in result, (
        f"BCHUSDT: fracdiff_d05_close MISSING from feature set. "
        f"BCH is the primary beneficiary of fracdiff (iter-v3/034 +37.98 OOS wpnl swing). "
        f"Got: {result}"
    )


def test_algo_has_fracdiff() -> None:
    """ALGOUSDT must return 15 features including fracdiff_d05_close.

    iter-v3/038: ALGO per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).
    Tests fracdiff SPECIFICITY: is fracdiff BCH-specific or broadly useful?
    ALGO at iter-v3/035: +20.87 OOS wpnl, 25 trades, 40.0% WR (second-weakest contributor).
    """
    result = features_for_symbol("ALGOUSDT")
    assert len(result) == 15, (
        f"ALGOUSDT: expected 15 features (ALGO per-symbol entry), got {len(result)}. "
        f"V3_FEATURES_PER_SYMBOL['ALGOUSDT'] should be V3_FEATURE_COLUMNS_TOP_N + fracdiff."
    )
    assert "fracdiff_d05_close" in result, (
        f"ALGOUSDT: fracdiff_d05_close MISSING from feature set. "
        f"iter-v3/038: ALGO-only fracdiff via V3_FEATURES_PER_SYMBOL. "
        f"Got: {result}"
    )


def test_algo_no_cross_asset_divergence() -> None:
    """ALGOUSDT must NOT include cross_asset_divergence_norm.

    iter-v3/038: ALGO's per-symbol extension is fracdiff_d05_close ONLY.
    cross_asset_divergence_norm is dead at model level (iter-v3/037 NEGATIVE reverted).
    """
    result = features_for_symbol("ALGOUSDT")
    assert "cross_asset_divergence_norm" not in result, (
        f"ALGOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"iter-v3/038: ALGO extension = fracdiff_d05_close only. "
        f"cross_asset_divergence_norm is dead at model level (iter-v3/037 NEGATIVE). "
        f"Got: {result}"
    )


def test_ldo_fallback_14() -> None:
    """LDOUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/038).

    iter-v3/038: LDOUSDT removed from V3_FEATURES_PER_SYMBOL (iter-v3/037 NEGATIVE reverted).
    LDO cross_asset_divergence_norm OOS swing ~-33. LDO returns to 14-feature universal.
    """
    result = features_for_symbol("LDOUSDT")
    assert len(result) == 14, (
        f"LDOUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/038: LDOUSDT not in V3_FEATURES_PER_SYMBOL (iter-v3/037 NEGATIVE reverted). "
        f"Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"LDOUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"LDOUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_ldo_no_fracdiff_no_cross_asset() -> None:
    """LDOUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/038: LDO uses 14-feature fallback. Neither fracdiff (BCH+ALGO per-symbol only) nor
    cross_asset_divergence_norm (dead at model level since iter-v3/037 NEGATIVE) apply to LDO.
    """
    result = features_for_symbol("LDOUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"LDOUSDT: fracdiff_d05_close FOUND — must be ABSENT (BCH+ALGO per-symbol only). "
        f"iter-v3/034: LDO was -6.81 OOS wpnl from universal fracdiff. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"LDOUSDT: cross_asset_divergence_norm FOUND — must be ABSENT. "
        f"iter-v3/037 NEGATIVE: LDO per-symbol cross_asset caused ~-33 OOS swing. "
        f"LDO reverted to 14-feature fallback at iter-v3/038. Got: {result}"
    )


def test_trx_fallback_14() -> None:
    """TRXUSDT must return 14 features via fallback (no per-symbol entry at iter-v3/038).

    iter-v3/038: TRXUSDT has no per-symbol entry (unchanged from iter-v3/037).
    iter-v3/036 NEGATIVE reverted TRX vol_adj_autocorr; TRX remains at 14-feature universal.
    """
    result = features_for_symbol("TRXUSDT")
    assert len(result) == 14, (
        f"TRXUSDT: expected 14 features (V3_FEATURE_COLUMNS_TOP_N fallback), got {len(result)}. "
        f"iter-v3/038: TRXUSDT not in V3_FEATURES_PER_SYMBOL. Got: {result}"
    )
    assert result == V3_FEATURE_COLUMNS_TOP_N, (
        f"TRXUSDT: fallback result differs from V3_FEATURE_COLUMNS_TOP_N. "
        f"TRXUSDT must use the universal 14-feature set exactly. "
        f"Extra: {sorted(set(result) - set(V3_FEATURE_COLUMNS_TOP_N))}. "
        f"Missing: {sorted(set(V3_FEATURE_COLUMNS_TOP_N) - set(result))}."
    )


def test_trx_no_special_features() -> None:
    """TRXUSDT must NOT include fracdiff_d05_close or cross_asset_divergence_norm.

    iter-v3/038: TRX uses 14-feature fallback. Neither extension feature applies.
    """
    result = features_for_symbol("TRXUSDT")
    assert "fracdiff_d05_close" not in result, (
        f"TRXUSDT: fracdiff_d05_close FOUND — must be ABSENT (BCH+ALGO per-symbol only). "
        f"iter-v3/034: TRX was -20.11 OOS wpnl from universal fracdiff. Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"TRXUSDT: cross_asset_divergence_norm FOUND — must be ABSENT (dead at model level). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"TRXUSDT: vol_adj_autocorr FOUND — must be ABSENT. Dead code since iter-v3/037. "
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


def test_algo_per_symbol_entry_has_fracdiff() -> None:
    """V3_FEATURES_PER_SYMBOL["ALGOUSDT"] must contain fracdiff_d05_close.

    iter-v3/038: ALGO per-symbol entry = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).
    """
    assert "ALGOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'ALGOUSDT' key — "
        "iter-v3/038: ALGO must have a per-symbol entry. "
        "Check features_v3/__init__.py V3_FEATURES_PER_SYMBOL."
    )
    algo_entry = V3_FEATURES_PER_SYMBOL["ALGOUSDT"]
    assert "fracdiff_d05_close" in algo_entry, (
        f"V3_FEATURES_PER_SYMBOL['ALGOUSDT']: fracdiff_d05_close MISSING. "
        f"ALGO entry must include fracdiff_d05_close. Got: {algo_entry}"
    )


def test_bch_algo_per_symbol_entries_same_extension_feature() -> None:
    """BCH and ALGO per-symbol entries must both have fracdiff_d05_close.

    iter-v3/038: BCH has fracdiff (since iter-v3/035); ALGO has fracdiff (NEW at iter-v3/038).
    Both entries are structurally similar (same extension feature) — this is the specificity test.
    The scientific question is whether fracdiff is BCH-specific (iter-v3/034/035 history) or
    broadly useful (ALGO benefits too).
    """
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'BCHUSDT'. Check features_v3/__init__.py."
    )
    assert "ALGOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'ALGOUSDT'. Check features_v3/__init__.py."
    )
    bch_entry = V3_FEATURES_PER_SYMBOL["BCHUSDT"]
    algo_entry = V3_FEATURES_PER_SYMBOL["ALGOUSDT"]
    assert "fracdiff_d05_close" in bch_entry, (
        f"BCH entry missing fracdiff_d05_close. Got: {bch_entry}"
    )
    assert "fracdiff_d05_close" in algo_entry, (
        f"ALGO entry missing fracdiff_d05_close. Got: {algo_entry}"
    )
    # Both entries should be V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
    assert set(bch_entry) == set(algo_entry), (
        f"BCH and ALGO per-symbol entries are DIFFERENT — expected IDENTICAL at iter-v3/038. "
        f"iter-v3/038: both BCH and ALGO extend with fracdiff_d05_close. "
        f"BCH entry: {bch_entry}. ALGO entry: {algo_entry}."
    )


def test_ldousdt_not_in_per_symbol() -> None:
    """LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/038.

    iter-v3/038: LDO per-symbol entry REVERTED (iter-v3/037 NEGATIVE: cross_asset_divergence_norm
    OOS swing ~-33 vs iter-v3/035 anchor). LDO must use 14-feature universal fallback.
    """
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/038. "
        f"iter-v3/038: LDO per-symbol entry REVERTED (iter-v3/037 NEGATIVE). "
        f"Remove LDOUSDT from V3_FEATURES_PER_SYMBOL in features_v3/__init__.py. "
        f"Current keys: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_trxusdt_not_in_per_symbol() -> None:
    """TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL at iter-v3/038.

    TRXUSDT has no per-symbol entry since iter-v3/037 (iter-v3/036 NEGATIVE reverted).
    Unchanged through iter-v3/038.
    """
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/038. "
        f"TRXUSDT has no per-symbol entry since iter-v3/036/037/038 (all NEGATIVEs reverted). "
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


def test_algo_per_symbol_len() -> None:
    """V3_FEATURES_PER_SYMBOL["ALGOUSDT"] must have exactly 15 features.

    15 = 14 universal (V3_FEATURE_COLUMNS_TOP_N) + fracdiff_d05_close.
    NEW at iter-v3/038.
    """
    assert "ALGOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'ALGOUSDT'. Check features_v3/__init__.py."
    )
    algo_entry = V3_FEATURES_PER_SYMBOL["ALGOUSDT"]
    assert len(algo_entry) == 15, (
        f"V3_FEATURES_PER_SYMBOL['ALGOUSDT']: expected 15 features, got {len(algo_entry)}. "
        f"ALGO entry = V3_FEATURE_COLUMNS_TOP_N (14) + fracdiff_d05_close (1) = 15."
    )


@pytest.mark.parametrize("symbol", ["LDOUSDT", "TRXUSDT"])
def test_non_bch_algo_fallback_no_special_features(symbol: str) -> None:
    """LDO/TRX must NOT have fracdiff_d05_close or cross_asset_divergence_norm (fallback path).

    iter-v3/038: LDO and TRX are not in V3_FEATURES_PER_SYMBOL; they fall back
    to V3_FEATURE_COLUMNS_TOP_N which contains neither extension feature.
    LDO reverted from iter-v3/037 (NEGATIVE result). TRX unchanged.
    """
    result = features_for_symbol(symbol)
    assert "fracdiff_d05_close" not in result, (
        f"{symbol}: fracdiff_d05_close FOUND — must be ABSENT (BCH+ALGO per-symbol only). "
        f"Got: {result}"
    )
    assert "cross_asset_divergence_norm" not in result, (
        f"{symbol}: cross_asset_divergence_norm FOUND — must be ABSENT (dead at model level). "
        f"Got: {result}"
    )
    assert "vol_adj_autocorr" not in result, (
        f"{symbol}: vol_adj_autocorr FOUND — must be ABSENT (dead code; iter-v3/036/037 reverted). "
        f"Got: {result}"
    )


@pytest.mark.parametrize("symbol", ["LDOUSDT", "TRXUSDT"])
def test_non_bch_algo_fallback_len(symbol: str) -> None:
    """LDO/TRX fallback must return exactly 14 features.

    iter-v3/038: V3_FEATURE_COLUMNS_TOP_N has 14 features (no extension feature added).
    LDO reverted from iter-v3/037 (NEGATIVE result); TRX unchanged.
    """
    result = features_for_symbol(symbol)
    assert len(result) == 14, (
        f"{symbol}: expected 14 features (V3_FEATURE_COLUMNS_TOP_N universal fallback), "
        f"got {len(result)}. V3_FEATURE_COLUMNS_TOP_N must have exactly 14 at iter-v3/038."
    )


def test_subset_invariant_extended_bch() -> None:
    """BCH entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/035+: BCH entry EXTENDS (not reduces) the universal list by fracdiff_d05_close.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features; only BCH+ALGO feature_columns= lists include it at model level.
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


def test_subset_invariant_extended_algo() -> None:
    """ALGO entry must equal V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",).

    iter-v3/038: ALGO entry EXTENDS the universal list by fracdiff_d05_close.
    The extension feature is computed in the parquet for all symbols by
    add_engineered_v3_features; only BCH+ALGO feature_columns= lists include it at model level.
    """
    assert "ALGOUSDT" in V3_FEATURES_PER_SYMBOL, (
        "V3_FEATURES_PER_SYMBOL missing 'ALGOUSDT'. Check features_v3/__init__.py."
    )
    algo_entry = V3_FEATURES_PER_SYMBOL["ALGOUSDT"]
    expected = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
    assert set(algo_entry) == set(expected), (
        f"V3_FEATURES_PER_SYMBOL['ALGOUSDT'] content mismatch. "
        f"Expected V3_FEATURE_COLUMNS_TOP_N + ('fracdiff_d05_close',). "
        f"Extra in ALGO entry: {sorted(set(algo_entry) - set(expected))}. "
        f"Missing from ALGO entry: {sorted(set(expected) - set(algo_entry))}."
    )


def test_v3_features_per_symbol_has_two_entries() -> None:
    """V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/038.

    The two entries are BCHUSDT (fracdiff_d05_close) and ALGOUSDT (fracdiff_d05_close).
    LDO/TRX use the fallback path. LDO reverted from iter-v3/037 (NEGATIVE).
    """
    assert len(V3_FEATURES_PER_SYMBOL) == 2, (
        f"V3_FEATURES_PER_SYMBOL must have exactly 2 entries at iter-v3/038 (BCH + ALGO). "
        f"Got {len(V3_FEATURES_PER_SYMBOL)} entries: {dict(V3_FEATURES_PER_SYMBOL)}."
    )
    assert "BCHUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing BCHUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "ALGOUSDT" in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL missing ALGOUSDT key. Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has LDOUSDT key — must be ABSENT at iter-v3/038 (reverted). "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )
    assert "TRXUSDT" not in V3_FEATURES_PER_SYMBOL, (
        f"V3_FEATURES_PER_SYMBOL has TRXUSDT key — must be ABSENT at iter-v3/038. "
        f"Got: {list(V3_FEATURES_PER_SYMBOL.keys())}."
    )


def test_regime_momentum_in_universal_list() -> None:
    """regime_momentum_signed_5d must be in V3_FEATURE_COLUMNS_TOP_N (portfolio mandate).

    Portfolio-level mandate from feedback_v3_engineered_features_proven.md:
    BCH+ALGO+TRX+LDO ALL use regime_momentum_signed_5d.
    Per-symbol entries (BCH+ALGO) EXTEND TOP_N; fallback (LDO+TRX) returns TOP_N directly.
    """
    assert "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N, (
        "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS_TOP_N. "
        "Portfolio-level mandate requires all symbols to use this feature via fallback. "
        "feedback_v3_engineered_features_proven.md. Do NOT revert."
    )


def test_fracdiff_not_in_universal_list() -> None:
    """fracdiff_d05_close must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/035+: fracdiff_d05_close moved from universal list to BCH per-symbol only.
    iter-v3/038: fracdiff in BCH+ALGO per-symbol entries; still NOT in universal list.
    Universal list has 14 features. BCH+ALGO per-symbol have 15 (14 + fracdiff_d05_close).
    """
    assert "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N, (
        "fracdiff_d05_close FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/038: fracdiff_d05_close is in V3_FEATURES_PER_SYMBOL['BCHUSDT'] + "
        "V3_FEATURES_PER_SYMBOL['ALGOUSDT'] only. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_cross_asset_divergence_not_in_universal_list() -> None:
    """cross_asset_divergence_norm must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/038: cross_asset_divergence_norm is dead at model level (iter-v3/037 NEGATIVE
    reverted; LDO entry removed). Column still generated in parquets by engineered_v3
    dispatch but NOT in any V3_FEATURES_PER_SYMBOL entry.
    Universal application failed at iter-v3/027 (IS Sharpe collapse -0.2817; OOS spike +1.6786).
    """
    assert "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N, (
        "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/038: cross_asset_divergence_norm dead at model level. "
        "Universal application FALSIFIED at iter-v3/027. LDO per-symbol FALSIFIED at iter-v3/037. "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_vol_adj_autocorr_not_in_universal_list() -> None:
    """vol_adj_autocorr must NOT be in V3_FEATURE_COLUMNS_TOP_N (universal list).

    iter-v3/038: vol_adj_autocorr is dead code (iter-v3/036 NEGATIVE reverted;
    iter-v3/037/038 do not reintroduce it).
    Universal application failed at iter-v3/026 (IS Sharpe collapse +0.0493; 27× IS/OOS ratio).
    TRX per-symbol application also failed at iter-v3/036 (~-15 OOS wpnl swing).
    """
    assert "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N, (
        "vol_adj_autocorr FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT. "
        "iter-v3/038: vol_adj_autocorr is dead code. "
        "Universal application FALSIFIED at iter-v3/026 (IS Sharpe +0.0493; 27× IS/OOS). "
        "TRX per-symbol FALSIFIED at iter-v3/036 (~-15 OOS wpnl swing). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )


def test_universal_list_is_14() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 features at iter-v3/038.

    iter-v3/038: universal list UNCHANGED from iter-v3/035 (still 14 features).
    Neither fracdiff_d05_close, cross_asset_divergence_norm, nor vol_adj_autocorr
    appear in the universal list.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected exactly 14. "
        f"iter-v3/038: universal list unchanged (14 features); fracdiff_d05_close added "
        f"via V3_FEATURES_PER_SYMBOL for BCH+ALGO only. "
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
        "Unknown symbol fallback must NOT include fracdiff_d05_close (BCH+ALGO per-symbol only)."
    )
    assert "cross_asset_divergence_norm" not in result, (
        "Unknown symbol fallback must NOT include cross_asset_divergence_norm "
        "(dead at model level; iter-v3/037 NEGATIVE reverted)."
    )
    assert "vol_adj_autocorr" not in result, (
        "Unknown symbol fallback must NOT include vol_adj_autocorr "
        "(dead code; iter-v3/036 reverted)."
    )
