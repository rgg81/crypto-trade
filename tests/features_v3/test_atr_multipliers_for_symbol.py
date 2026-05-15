"""Tests for per-symbol ATR multiplier resolution at iter-v3/074.

iter-v3/074 state (V3_ATR_MULTIPLIERS_PER_SYMBOL REVERT):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — canonical /059 baseline pair.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY). The iter-v3/073 per-symbol
    triple-barrier asymmetry axis (BCH (2.0,1.25), LDO (1.5,1.25)) was
    SUSPICIOUS-OOS-DOMINANT (OOS/IS monthly Sharpe ratio 6.85 — a holding-time-
    extension axis) and was CLOSED at catalog level. Per `feedback_no_cheating.md`
    anti-drift discipline /074 reverts the dict so no symbol carries an override.
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols.
  - atr_multipliers_for_symbol: BCH/LDO/TRX all (2.0, 1.0) DEFAULT.

History:
  iter-v3/010: (2.0, 1.0) first set.
  iter-v3/044-047: per-symbol entries (ALGO/LDO/BCH).
  iter-v3/051: CLEARED (system-level revert).
  iter-v3/065-070: EMPTY (universal axes / CONFIRMATION revert).
  iter-v3/073: RE-POPULATED — per-symbol triple-barrier asymmetry axis (BCH/LDO).
  iter-v3/074: REVERTED to {} — the /073 axis was SUSPICIOUS-OOS-DOMINANT.

Tests:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0).
  2. V3_ATR_MULTIPLIERS_PER_SYMBOL is empty {}.
  3. BCHUSDT returns (2.0, 1.0) — DEFAULT fallback (/073 entry reverted).
  4. LDOUSDT returns (2.0, 1.0) — DEFAULT fallback (/073 entry reverted).
  5. TRXUSDT returns (2.0, 1.0) — DEFAULT fallback.
  6. Unknown symbol returns (2.0, 1.0) — DEFAULT fallback.
  7. The runner's _build_v3_model dispatches the global (2.0, 1.0) pair to all syms.
"""


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) — the canonical /059 baseline pair.

    iter-v3/074: V3_ATR_MULTIPLIERS_PER_SYMBOL reverted to {}; ALL v3 symbols
    resolve to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0)."
    )
    # iter-v3/074: every v3 symbol resolves to DEFAULT (per-symbol dict empty).
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0), (
        "BCHUSDT must return (2.0, 1.0) at iter-v3/074 — the /073 (2.0, 1.25) "
        "per-symbol entry is reverted."
    )
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0), (
        "LDOUSDT must return (2.0, 1.0) at iter-v3/074 — the /073 (1.5, 1.25) "
        "per-symbol entry is reverted."
    )
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.0) via DEFAULT fallback at iter-v3/074.

    iter-v3/074: the /073 per-symbol (2.0, 1.25) BCH entry is reverted —
    V3_ATR_MULTIPLIERS_PER_SYMBOL no longer contains BCHUSDT.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'BCHUSDT' at iter-v3/074 "
        f"(the /073 entry is reverted). Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert tuple(atr_multipliers_for_symbol("BCHUSDT")) == (2.0, 1.0)


def test_atr_multipliers_ldo_default_fallback():
    """LDO must return (2.0, 1.0) via DEFAULT fallback at iter-v3/074.

    iter-v3/074: the /073 per-symbol (1.5, 1.25) LDO entry is reverted.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'LDOUSDT' at iter-v3/074 "
        f"(the /073 entry is reverted). Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert tuple(atr_multipliers_for_symbol("LDOUSDT")) == (2.0, 1.0)


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/074."""
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert tuple(atr_multipliers_for_symbol("TRXUSDT")) == (2.0, 1.0)


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL is empty {} at iter-v3/074.

    iter-v3/074: REVERT of the /073 per-symbol triple-barrier asymmetry axis
    (SUSPICIOUS-OOS-DOMINANT). All symbols use DEFAULT_ATR_MULTIPLIERS.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    actual = {k: tuple(v) for k, v in V3_ATR_MULTIPLIERS_PER_SYMBOL.items()}
    assert actual == {}, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL = {actual} — expected {{}} (EMPTY) at "
        "iter-v3/074 (REVERT of the /073 per-symbol triple-barrier asymmetry axis)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model dispatches the global (2.0, 1.0) pair at iter-v3/074.

    All three v3 symbols (BCH/LDO/TRX) receive DEFAULT_ATR_MULTIPLIERS — the
    labeling layer is symbol-homogeneous after the /073 axis revert.
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

    for sym, strat in [("BCHUSDT", strat_bch), ("LDOUSDT", strat_ldo), ("TRXUSDT", strat_trx)]:
        assert strat.inner.atr_tp_multiplier == 2.0, (
            f"{sym} atr_tp_multiplier: expected 2.0, got {strat.inner.atr_tp_multiplier}. "
            "iter-v3/074: all symbols use DEFAULT (2.0, 1.0)."
        )
        assert strat.inner.atr_sl_multiplier == 1.0, (
            f"{sym} atr_sl_multiplier: expected 1.0, got {strat.inner.atr_sl_multiplier}. "
            "iter-v3/074: all symbols use DEFAULT (2.0, 1.0)."
        )
