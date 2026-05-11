"""Adversarial tests for per-symbol ATR multipliers — iter-v3/047 (UPDATED iter-v3/051).

iter-v3/051 state (EXPLORATION — cycle 4 #1 — fracdiff_d05_close UNIVERSAL ADD;
                   SYSTEM-LEVEL REVERT to iter-v3/028 architecture):
  - DEFAULT_ATR_MULTIPLIERS unchanged at (2.0, 1.0).
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY — SYSTEM-LEVEL REVERT per
    `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10; second-cycle
    confirmation of per-symbol-customization anti-pattern at iter-v3/039 + iter-v3/050).
    ALGOUSDT and LDOUSDT entries REVERTED. All 3 symbols (BCH/LDO/TRX) use DEFAULT.
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (ALGO REVERTED).
  - Single-axis change (this iter): fracdiff_d05_close ADD to V3_FEATURE_COLUMNS_TOP_N.

History of V3_ATR_MULTIPLIERS_PER_SYMBOL:
  iter-v3/047: ALGOUSDT + LDOUSDT entries, 2 total (BCH REVERTED from /046).
  iter-v3/051: CLEARED to empty dict. System-level REVERT to /028 architecture.

Validates (iter-v3/051 state):
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/051 (unchanged).
  2. TRX falls back to (2.0, 1.0) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.0) — DEFAULT fallback (REVERTED at iter-v3/051).
  4. LDOUSDT returns (2.0, 1.0) — DEFAULT fallback (REVERTED at iter-v3/051).
  5. BCHUSDT returns (2.0, 1.0) — DEFAULT fallback (REVERTED at iter-v3/047; unchanged).
  6. V3_ATR_MULTIPLIERS_PER_SYMBOL has 0 entries (EMPTY — SYSTEM-LEVEL REVERT).
  7. The runner's _build_v3_model dispatches (2.0, 1.0) for all 3 symbols (BCH/LDO/TRX).
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/051 (unchanged from prior iters).

    iter-v3/051: V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT). All 3 symbols
    (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/051: DEFAULT unchanged from iter-v3/043 revert. "
        "Verify in features_v3/__init__.py."
    )
    # iter-v3/051: TRX uses DEFAULT fallback (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/051: ALGOUSDT REVERTED — falls back to DEFAULT (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0), (
        "ALGOUSDT must return (2.0, 1.0) at iter-v3/051 — SYSTEM-LEVEL REVERT. "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty; ALGO falls back to DEFAULT."
    )
    # iter-v3/051: LDOUSDT REVERTED — falls back to DEFAULT (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0), (
        "LDOUSDT must return (2.0, 1.0) at iter-v3/051 — SYSTEM-LEVEL REVERT. "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty; LDO falls back to DEFAULT."
    )
    # iter-v3/047+051: BCHUSDT returns DEFAULT (2.0, 1.0) — no per-symbol entry.
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0), (
        "BCHUSDT must return (2.0, 1.0) at iter-v3/051 (DEFAULT fallback; "
        "REVERTED at iter-v3/047 per Critic FINAL `5dae6d6`)."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.0) — via DEFAULT fallback — at iter-v3/051.

    iter-v3/047: BCHUSDT entry REMOVED per Critic FINAL `5dae6d6`. BCH falls back
    to DEFAULT. iter-v3/051: unchanged (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty;
    all symbols use DEFAULT).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at "
        f"iter-v3/051. SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.0). "
        f"iter-v3/051: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback "
        f"(V3_ATR_MULTIPLIERS_PER_SYMBOL empty)."
    )


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/051.

    TRX has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty at /051).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/051. "
        f"SYSTEM-LEVEL REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    trx_result = atr_multipliers_for_symbol("TRXUSDT")
    assert trx_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('TRXUSDT') returned {trx_result} — expected (2.0, 1.0). "
        f"iter-v3/051: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); TRX uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/051.

    SYSTEM-LEVEL REVERT: per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED
    2026-05-10 (second-cycle confirmation of per-symbol-customization anti-pattern at
    iter-v3/039 + iter-v3/050). ALGOUSDT and LDOUSDT entries REVERTED to empty dict.

    History:
      iter-v3/040: CLEARED (cycle 3 revert).
      iter-v3/044: ALGOUSDT added.
      iter-v3/045: LDOUSDT added.
      iter-v3/047: BCHUSDT removed (revert BCH wider-SL NEGATIVE).
      iter-v3/051: CLEARED (system-level revert; BOTH-must-improve failed at /050 CONFIRMATION).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/051. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: "
        f"{dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"SYSTEM-LEVEL REVERT to iter-v3/028 architecture per "
        f"`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model dispatches (2.0, 1.0) for ALL 3 symbols at iter-v3/051.

    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; all symbols use DEFAULT_ATR_MULTIPLIERS.
    Only builds BCH/LDO/TRX models (ALGO not in V3_MODELS at iter-v3/051 REVERT).
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

    # iter-v3/051 SYSTEM-LEVEL REVERT: all 3 symbols use DEFAULT (2.0, 1.0).
    for sym, strat in [("BCHUSDT", strat_bch), ("LDOUSDT", strat_ldo), ("TRXUSDT", strat_trx)]:
        assert strat.inner.atr_tp_multiplier == 2.0, (
            f"{sym} atr_tp_multiplier: expected 2.0, got {strat.inner.atr_tp_multiplier}. "
            "iter-v3/051: SYSTEM-LEVEL REVERT — all 3 symbols use DEFAULT_ATR_MULTIPLIERS "
            "= (2.0, 1.0); V3_ATR_MULTIPLIERS_PER_SYMBOL is empty."
        )
        assert strat.inner.atr_sl_multiplier == 1.0, (
            f"{sym} atr_sl_multiplier: expected 1.0, got {strat.inner.atr_sl_multiplier}. "
            "iter-v3/051: SYSTEM-LEVEL REVERT — all 3 symbols use DEFAULT_ATR_MULTIPLIERS "
            "= (2.0, 1.0); V3_ATR_MULTIPLIERS_PER_SYMBOL is empty."
        )
