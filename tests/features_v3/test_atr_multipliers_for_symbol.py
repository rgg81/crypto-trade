"""Adversarial tests for per-symbol ATR multipliers — iter-v3/047 (UPDATED iter-v3/070).

iter-v3/070 state (CYCLE 1 CONFIRMATION — Component A: universal SL widening RE-APPLIED):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5).
    /065 set (2.0, 1.5); /066-/069 reverted to (2.0, 1.0) for single-axis attribution.
    /070 CYCLE 1 CONFIRMATION: Component A = re-apply /065 SL widening universally.
    EDA SHA `fe219c1`; briefs-v3/iteration_v3-070/research_brief.md Section 3 Sub-fix 1.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY — SYSTEM-LEVEL REVERT carry-forward
    from iter-v3/051 per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`).
    All 3 symbols (BCH/LDO/TRX) use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5).
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (REVERT /069 ADAUSDT).

History of DEFAULT_ATR_MULTIPLIERS:
  iter-v3/010: (2.0, 1.0) first set.
  iter-v3/042: (1.5, 0.75) — NEGATIVE IS collapse; reverted immediately.
  iter-v3/043: (2.0, 1.0) — reverted from (1.5, 0.75) mandate.
  iter-v3/065: (2.0, 1.5) — universal SL widening, Path D (EDA SHA `662659c`).
  iter-v3/066: (2.0, 1.0) — REVERTED for axis isolation (Path E0.8 only).
  iter-v3/067-069: (2.0, 1.0) — carry-forward (non-labeling axes).
  iter-v3/070: (2.0, 1.5) — RE-APPLIED /065 Component A at CONFIRMATION.

History of V3_ATR_MULTIPLIERS_PER_SYMBOL:
  iter-v3/047: ALGOUSDT + LDOUSDT entries, 2 total (BCH REVERTED from /046).
  iter-v3/051: CLEARED to empty dict. System-level REVERT to /028 architecture.
  iter-v3/065-070: still EMPTY (carry-forward; universal DEFAULT change only).

Validates (iter-v3/070 state):
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5) at iter-v3/070 (Component A re-applied).
  2. TRX falls back to (2.0, 1.5) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.5) — DEFAULT fallback.
  4. LDOUSDT returns (2.0, 1.5) — DEFAULT fallback.
  5. BCHUSDT returns (2.0, 1.5) — DEFAULT fallback.
  6. V3_ATR_MULTIPLIERS_PER_SYMBOL has 0 entries (EMPTY — carry-forward).
  7. The runner's _build_v3_model dispatches (2.0, 1.5) for all 3 symbols (BCH/LDO/TRX).
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5) at iter-v3/070 (Component A re-applied).

    iter-v3/070: /065's SL widening (2.0, 1.5) RE-APPLIED as Component A of CONFIRMATION bundle.
    V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (SYSTEM-LEVEL REVERT carry-forward from /051).
    All 3 symbols (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5).
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.5). "
        "iter-v3/070 CONFIRMATION Component A: RE-APPLY /065 SL widening (2.0, 1.5). "
        "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) in features_v3/__init__.py."
    )
    # iter-v3/070: TRX uses DEFAULT fallback (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.5)
    # iter-v3/070: ALGOUSDT falls back to DEFAULT (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5), (
        "ALGOUSDT must return (2.0, 1.5) at iter-v3/070 — DEFAULT fallback. "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty; ALGO falls back to DEFAULT."
    )
    # iter-v3/070: LDOUSDT falls back to DEFAULT (V3_ATR_MULTIPLIERS_PER_SYMBOL empty).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5), (
        "LDOUSDT must return (2.0, 1.5) at iter-v3/070 — DEFAULT fallback. "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty; LDO falls back to DEFAULT."
    )
    # iter-v3/070: BCHUSDT returns DEFAULT (2.0, 1.5) — no per-symbol entry.
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.5), (
        "BCHUSDT must return (2.0, 1.5) at iter-v3/070 (DEFAULT fallback; "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL is empty)."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.5)


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.5) — via DEFAULT fallback — at iter-v3/070.

    iter-v3/047: BCHUSDT entry REMOVED per Critic FINAL `5dae6d6`. BCH falls back
    to DEFAULT. iter-v3/051: V3_ATR_MULTIPLIERS_PER_SYMBOL cleared (system-level REVERT).
    iter-v3/070: DEFAULT RE-APPLIED to (2.0, 1.5) (Component A); BCH still uses DEFAULT fallback.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at "
        f"iter-v3/070. V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (carry-forward). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.5), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.5). "
        f"iter-v3/070 CONFIRMATION Component A: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) "
        f"via fallback (V3_ATR_MULTIPLIERS_PER_SYMBOL empty)."
    )


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.5) via DEFAULT fallback at iter-v3/070.

    TRX has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty at /070).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/070. "
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (carry-forward from /051). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    trx_result = atr_multipliers_for_symbol("TRXUSDT")
    assert trx_result == (2.0, 1.5), (
        f"atr_multipliers_for_symbol('TRXUSDT') returned {trx_result} — expected (2.0, 1.5). "
        f"iter-v3/070 CONFIRMATION Component A: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5); "
        f"TRX uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/066.

    SYSTEM-LEVEL REVERT carry-forward from iter-v3/051: per
    `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10.
    iter-v3/066 is a RISK PRIMITIVE axis change only — no per-symbol labeling entries added.

    History:
      iter-v3/040: CLEARED (cycle 3 revert).
      iter-v3/044: ALGOUSDT added.
      iter-v3/045: LDOUSDT added.
      iter-v3/047: BCHUSDT removed (revert BCH wider-SL NEGATIVE).
      iter-v3/051: CLEARED (system-level revert; BOTH-must-improve failed at /050 CONFIRMATION).
      iter-v3/065: still EMPTY (universal DEFAULT labeling change; no per-symbol overrides).
      iter-v3/066: still EMPTY (risk primitive axis; no per-symbol labeling overrides).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be EMPTY (0 entries) at iter-v3/066. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: "
        f"{dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"iter-v3/066 Path E0.8 is a universal risk primitive change — no per-symbol overrides."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model dispatches (2.0, 1.5) for ALL 3 symbols at iter-v3/070.

    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty; all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5).
    Only builds BCH/LDO/TRX models (ALGO not in V3_MODELS at iter-v3/051 REVERT carry-forward).
    iter-v3/070 CONFIRMATION Component A: DEFAULT RE-APPLIED from /065's (2.0, 1.5).
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

    # iter-v3/070 CONFIRMATION Component A: all 3 symbols use DEFAULT (2.0, 1.5).
    for sym, strat in [("BCHUSDT", strat_bch), ("LDOUSDT", strat_ldo), ("TRXUSDT", strat_trx)]:
        assert strat.inner.atr_tp_multiplier == 2.0, (
            f"{sym} atr_tp_multiplier: expected 2.0, got {strat.inner.atr_tp_multiplier}. "
            "iter-v3/070: TP multiplier unchanged at 2.0×ATR for all symbols."
        )
        assert strat.inner.atr_sl_multiplier == 1.5, (
            f"{sym} atr_sl_multiplier: expected 1.5, got {strat.inner.atr_sl_multiplier}. "
            "iter-v3/070 CONFIRMATION Component A: /065 SL widening (1.5) RE-APPLIED. "
            "All 3 symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) via fallback."
        )
