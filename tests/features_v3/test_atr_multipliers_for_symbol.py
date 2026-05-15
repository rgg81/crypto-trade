"""Tests for per-symbol ATR multiplier resolution at iter-v3/073.

iter-v3/073 state (per-symbol triple-barrier asymmetry axis):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED (TRX fallback).
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5, 1.25)}.
    Per-symbol triple-barrier asymmetry: EDA `b004bc9` showed the global (2.0, 1.0)
    SL-saturates training labels on all 3 symbols (NATR differs ~2×). Per-symbol
    calibration balances barriers. Label-execution consistent by construction.
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols.
  - atr_multipliers_for_symbol: BCH (2.0, 1.25), LDO (1.5, 1.25), TRX (2.0, 1.0) fallback.

History:
  iter-v3/010: (2.0, 1.0) first set.
  iter-v3/044-047: per-symbol entries (ALGO/LDO/BCH).
  iter-v3/051: CLEARED (system-level revert).
  iter-v3/065-070: EMPTY (universal axes / CONFIRMATION revert).
  iter-v3/073: RE-POPULATED — per-symbol triple-barrier asymmetry axis (BCH/LDO entries).

Tests:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) UNCHANGED (TRX fallback base).
  2. V3_ATR_MULTIPLIERS_PER_SYMBOL has exactly 2 entries (BCH, LDO).
  3. BCHUSDT returns (2.0, 1.25) — per-symbol entry.
  4. LDOUSDT returns (1.5, 1.25) — per-symbol entry.
  5. TRXUSDT returns (2.0, 1.0) — DEFAULT fallback (no per-symbol entry).
  6. Unknown symbol returns (2.0, 1.0) — DEFAULT fallback.
  7. The runner's _build_v3_model dispatches per-symbol multipliers correctly.
"""


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/073 (TRX fallback base).

    iter-v3/073: per-symbol triple-barrier asymmetry. DEFAULT is unchanged at (2.0, 1.0);
    BCH and LDO have per-symbol entries; TRX falls back to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/073: DEFAULT unchanged; per-symbol entries override for BCH/LDO."
    )
    # iter-v3/073: TRX has no per-symbol entry — DEFAULT fallback.
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/073: ALGOUSDT not in V3_MODELS — DEFAULT fallback.
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0), (
        "ALGOUSDT must return (2.0, 1.0) — DEFAULT fallback (not in V3_ATR_MULTIPLIERS_PER_SYMBOL)."
    )
    # iter-v3/073: BCHUSDT has a per-symbol entry — (2.0, 1.25).
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.25), (
        "BCHUSDT must return (2.0, 1.25) at iter-v3/073 — per-symbol triple-barrier asymmetry."
    )
    # iter-v3/073: LDOUSDT has a per-symbol entry — (1.5, 1.25).
    assert atr_multipliers_for_symbol("LDOUSDT") == (1.5, 1.25), (
        "LDOUSDT must return (1.5, 1.25) at iter-v3/073 — per-symbol triple-barrier asymmetry."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_bch_per_symbol_entry():
    """BCH must return (2.0, 1.25) — per-symbol entry — at iter-v3/073.

    iter-v3/073: per-symbol triple-barrier asymmetry axis. BCH's 8h NATR median ~3.70%;
    the (2.0, 1.25) pair balances its triple-barrier training label vs the global (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'BCHUSDT' at iter-v3/073. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_result = tuple(atr_multipliers_for_symbol("BCHUSDT"))
    assert bch_result == (2.0, 1.25), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.25). "
        "iter-v3/073 per-symbol triple-barrier asymmetry."
    )


def test_atr_multipliers_ldo_per_symbol_entry():
    """LDO must return (1.5, 1.25) — per-symbol entry — at iter-v3/073.

    iter-v3/073: LDO's 8h NATR median ~5.01% (highest of the 3 syms); the (1.5, 1.25)
    pair tightens TP + widens SL to balance the 69%-SL-saturated triple-barrier label.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'LDOUSDT' at iter-v3/073. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_result = tuple(atr_multipliers_for_symbol("LDOUSDT"))
    assert ldo_result == (1.5, 1.25), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (1.5, 1.25). "
        "iter-v3/073 per-symbol triple-barrier asymmetry."
    )


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/073.

    iter-v3/073: TRX has NO per-symbol entry (its 8h NATR ~2.65% — the higher-spread
    cells were all SL-saturated and excluded by the balance band). TRX falls back to DEFAULT.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'TRXUSDT' at iter-v3/073 — "
        "TRX uses DEFAULT fallback. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    trx_result = tuple(atr_multipliers_for_symbol("TRXUSDT"))
    assert trx_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('TRXUSDT') returned {trx_result} — expected (2.0, 1.0). "
        "iter-v3/073: TRX uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_has_two_entries():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL has exactly 2 entries (BCH, LDO) at iter-v3/073.

    iter-v3/073: per-symbol triple-barrier asymmetry axis. RE-POPULATED after the
    /051 system-level clear. BCH (2.0, 1.25), LDO (1.5, 1.25); TRX absent (DEFAULT).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    actual = {k: tuple(v) for k, v in V3_ATR_MULTIPLIERS_PER_SYMBOL.items()}
    expected = {"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5, 1.25)}
    assert actual == expected, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL = {actual} — expected {expected} at iter-v3/073 "
        "(per-symbol triple-barrier asymmetry axis)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model dispatches per-symbol multipliers at iter-v3/073.

    BCH (2.0, 1.25), LDO (1.5, 1.25), TRX (2.0, 1.0) DEFAULT fallback.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from run_baseline_v3 import _build_v3_model

    _cfg_bch, strat_bch = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    _cfg_ldo, strat_ldo = _build_v3_model(
        symbol="LDOUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    _cfg_trx, strat_trx = _build_v3_model(
        symbol="TRXUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )

    expected = {
        "BCHUSDT": (2.0, 1.25),
        "LDOUSDT": (1.5, 1.25),
        "TRXUSDT": (2.0, 1.0),
    }
    for sym, strat in [("BCHUSDT", strat_bch), ("LDOUSDT", strat_ldo), ("TRXUSDT", strat_trx)]:
        exp_tp, exp_sl = expected[sym]
        assert strat.inner.atr_tp_multiplier == exp_tp, (
            f"{sym} atr_tp_multiplier: expected {exp_tp}, got {strat.inner.atr_tp_multiplier}. "
            "iter-v3/073 per-symbol triple-barrier asymmetry."
        )
        assert strat.inner.atr_sl_multiplier == exp_sl, (
            f"{sym} atr_sl_multiplier: expected {exp_sl}, got {strat.inner.atr_sl_multiplier}. "
            "iter-v3/073 per-symbol triple-barrier asymmetry."
        )
