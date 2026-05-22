"""Tests for per-symbol ATR multiplier resolution.

iter-v3/074 state (V3_ATR_MULTIPLIERS_PER_SYMBOL REVERT):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — canonical /059 baseline pair.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY). The iter-v3/073 per-symbol
    triple-barrier asymmetry axis (BCH (2.0,1.25), LDO (1.5,1.25)) was
    SUSPICIOUS-OOS-DOMINANT (OOS/IS monthly Sharpe ratio 6.85 — a holding-time-
    extension axis) and was CLOSED at catalog level. Per `feedback_no_cheating.md`
    anti-drift discipline /074 reverts the dict so no symbol carries an override.
  - V3_MODELS = (BCHUSDT, ADAUSDT, TRXUSDT) — 3 symbols (iter-v3/078 UNIVERSE REVISION).
  - atr_multipliers_for_symbol: BCH/ADA/TRX all (2.0, 1.0) DEFAULT.

iter-v3/124 state (K=63 longer-cadence labels axis — Branch B sqrt(3) ATR scaling):
  - DEFAULT_ATR_MULTIPLIERS = (3.4641, 1.7321) — Branch B: 2.0xsqrt(3), 1.0xsqrt(3).
  - NEGATIVE-catastrophic at closeout — REVERTED before /125.

iter-v3/125 state (WILD CYCLE-7 axis-4: V3_MODELS WHOLESALE REPLACEMENT ATOM/RUNE/UNI):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — REVERT /124 Branch B; /121-canonical K=21.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY) — universal scaling, no per-symbol overrides.
  - atr_multipliers_for_symbol: ATOM/RUNE/UNI all (2.0, 1.0) DEFAULT.

History:
  iter-v3/010: (2.0, 1.0) first set.
  iter-v3/044-047: per-symbol entries (ALGO/LDO/BCH).
  iter-v3/051: CLEARED (system-level revert).
  iter-v3/065-070: EMPTY (universal axes / CONFIRMATION revert).
  iter-v3/073: RE-POPULATED — per-symbol triple-barrier asymmetry axis (BCH/LDO).
  iter-v3/074: REVERTED to {} — the /073 axis was SUSPICIOUS-OOS-DOMINANT.
  iter-v3/071-123: (2.0, 1.0) canonical baseline (53 iterations).
  iter-v3/124: (2.0, 1.0) -> (3.4641, 1.7321) — Branch B sqrt(3) ATR (K=63). NEGATIVE.
  iter-v3/125: (3.4641, 1.7321) -> (2.0, 1.0) — REVERT /124; /121-canonical K=21 restored.

Tests:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) — /121-canonical (reverted at /125).
  2. V3_ATR_MULTIPLIERS_PER_SYMBOL is empty {}.
  3. BCHUSDT returns (2.0, 1.0) — DEFAULT fallback.
  4. ADAUSDT returns (2.0, 1.0) — DEFAULT fallback.
  5. TRXUSDT returns (2.0, 1.0) — DEFAULT fallback.
  6. Unknown symbol returns (2.0, 1.0) — DEFAULT fallback.
  7. The runner's _build_v3_model dispatches the (2.0, 1.0) pair to all syms.
"""

# iter-v3/125: ATR values REVERTED to /121-canonical (2.0, 1.0)
_EXPECTED_TP = 2.0
_EXPECTED_SL = 1.0
_EXPECTED_ATR = (_EXPECTED_TP, _EXPECTED_SL)


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) — /121-canonical (reverted at /125).

    iter-v3/125: REVERT /124 Branch B (3.4641, 1.7321) -> /121-canonical (2.0, 1.0).
    V3_ATR_MULTIPLIERS_PER_SYMBOL stays {}.
    ALL v3 symbols (ATOM/RUNE/UNI) resolve to DEFAULT (per-symbol dict empty).
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == _EXPECTED_ATR, (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected {_EXPECTED_ATR}. "
        "iter-v3/125: REVERT /124 Branch B ATR scaling; /121-canonical (2.0, 1.0). "
        "Set DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) in features_v3/__init__.py."
    )
    # iter-v3/125: every v3 symbol resolves to /121-canonical DEFAULT (per-symbol dict empty).
    assert atr_multipliers_for_symbol("TRXUSDT") == _EXPECTED_ATR
    assert atr_multipliers_for_symbol("BCHUSDT") == _EXPECTED_ATR, (
        f"BCHUSDT must return {_EXPECTED_ATR} at iter-v3/125 — /121-canonical DEFAULT."
    )
    assert atr_multipliers_for_symbol("ADAUSDT") == _EXPECTED_ATR, (
        f"ADAUSDT must return {_EXPECTED_ATR} — DEFAULT fallback (no per-symbol entry)."
    )
    assert atr_multipliers_for_symbol("ALGOUSDT") == _EXPECTED_ATR
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == _EXPECTED_ATR


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.0) via DEFAULT fallback at iter-v3/125.

    iter-v3/125: REVERT /124 Branch B; V3_ATR_MULTIPLIERS_PER_SYMBOL stays {}.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'BCHUSDT' at iter-v3/125 "
        f"(universal scaling, no per-symbol overrides). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert tuple(atr_multipliers_for_symbol("BCHUSDT")) == _EXPECTED_ATR


def test_atr_multipliers_ada_default_fallback():
    """ADA must return (2.0, 1.0) via DEFAULT fallback at iter-v3/125."""
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "ADAUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'ADAUSDT' at iter-v3/125 "
        f"(empty dict). Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert tuple(atr_multipliers_for_symbol("ADAUSDT")) == _EXPECTED_ATR


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/125."""
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert tuple(atr_multipliers_for_symbol("TRXUSDT")) == _EXPECTED_ATR


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL is empty {} at iter-v3/125.

    iter-v3/125: /121-canonical (2.0, 1.0); universal scaling, no per-symbol overrides.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    actual = {k: tuple(v) for k, v in V3_ATR_MULTIPLIERS_PER_SYMBOL.items()}
    assert actual == {}, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL = {actual} — expected {{}} (EMPTY) at "
        "iter-v3/125 (/121-canonical; universal ATR scaling; no per-symbol overrides)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model dispatches the correct ATR multipliers.

    iter-v3/116: REVERT /115's non-binding barriers (100.0, 100.0) -> /059-canonical
    (2.0, 1.0). /116 returns to triple_barrier labeling with canonical ATR multipliers.
    iter-v3/124: ATR updated to Branch B sqrt(3) values (3.4641, 1.7321). NEGATIVE.
    iter-v3/125: REVERT /124 Branch B -> /121-canonical (2.0, 1.0).
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from run_baseline_v3 import _build_v3_model

    _cfg_bch, strat_bch = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    _cfg_trx, strat_trx = _build_v3_model(
        symbol="TRXUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )

    # iter-v3/125: /121-canonical ATR multipliers (2.0, 1.0).
    for sym, strat in [("BCHUSDT", strat_bch), ("TRXUSDT", strat_trx)]:
        assert strat.inner.atr_tp_multiplier == _EXPECTED_TP, (
            f"{sym} atr_tp_multiplier: expected {_EXPECTED_TP},"
            f" got {strat.inner.atr_tp_multiplier}. "
            "iter-v3/125: REVERT /124 Branch B; /121-canonical (2.0). "
            "Check _build_v3_model common_kwargs (atr_tp_multiplier=_atr_tp)."
        )
        assert strat.inner.atr_sl_multiplier == _EXPECTED_SL, (
            f"{sym} atr_sl_multiplier: expected {_EXPECTED_SL},"
            f" got {strat.inner.atr_sl_multiplier}. "
            "iter-v3/125: REVERT /124 Branch B; /121-canonical (1.0). "
            "Check _build_v3_model common_kwargs (atr_sl_multiplier=_atr_sl)."
        )
