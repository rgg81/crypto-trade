"""Adversarial tests for per-symbol ATR multipliers — iter-v3/045.

iter-v3/045 state (EXPLORATION — cycle 3 #6 — QR EDA-driven per-symbol ATR for LDO,
                    stacked on iter-v3/044 ALGO ATR):
  - DEFAULT_ATR_MULTIPLIERS unchanged at (2.0, 1.0) from iter-v3/043 revert.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL has TWO entries:
      ALGOUSDT → (2.0, 1.5) — UNCHANGED from iter-v3/044 PROMISING result.
      LDOUSDT  → (2.0, 1.5) — NEW iter-v3/045 entry.
        Per QR EDA SHA `ed949fe`: LDO IS->OOS exit-composition shift (SL:TP 1.14 IS
        -> 2.33 OOS; SL rate 53.3% IS -> 63.6% OOS) is the binding constraint. Wider
        SL targets the IS->OOS regime-shift directly, mirroring iter-v3/044 ALGO
        mechanism. NOT the iter-v3/032 (1.5, 0.75) tighter-barrier path which was
        MULTI-SEED-FALSIFIED at iter-v3/039 — this is the OPPOSITE direction.
  - BCH/TRX still fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  - Single-axis change: V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5) ADDED.
    ALGOUSDT entry UNCHANGED from iter-v3/044.

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/045 (carried forward).
  2. BCH/TRX fall back to (2.0, 1.0) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.5) — via per-symbol entry (UNCHANGED from iter-v3/044).
  4. LDOUSDT returns (2.0, 1.5) — via per-symbol entry (NEW iter-v3/045).
  5. V3_ATR_MULTIPLIERS_PER_SYMBOL has 2 entries: ALGOUSDT, LDOUSDT.
  6. The runner's _build_v3_model dispatches (2.0, 1.0) for BCH/TRX; (2.0, 1.5) for ALGO/LDO.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/045 (unchanged from iter-v3/044).

    iter-v3/045: V3_ATR_MULTIPLIERS_PER_SYMBOL has ALGOUSDT + LDOUSDT entries (both (2.0, 1.5)).
    Non-{ALGO,LDO} symbols (BCH/TRX) fall back to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/045: DEFAULT unchanged from iter-v3/044. "
        "Verify in features_v3/__init__.py."
    )
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/044: ALGOUSDT has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5), (
        "ALGOUSDT must return (2.0, 1.5) at iter-v3/045 (per-symbol entry per QR EDA "
        "SHA `eff841e`; UNCHANGED from iter-v3/044 PROMISING)."
    )
    # iter-v3/045: LDOUSDT has per-symbol entry (2.0, 1.5) — NEW.
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5), (
        "LDOUSDT must return (2.0, 1.5) at iter-v3/045 (per-symbol entry per QR EDA "
        "SHA `ed949fe`; NEW iter-v3/045 — mirror of iter-v3/044 ALGO mechanism). "
        "NOT the iter-v3/032 (1.5, 0.75) which was MULTI-SEED-FALSIFIED at iter-v3/039."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_ldo_per_symbol_widened():
    """LDO must return (2.0, 1.5) — via per-symbol entry — at iter-v3/045.

    iter-v3/044: LDOUSDT used DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    iter-v3/045: LDOUSDT entry ADDED at (2.0, 1.5) — wider SL mirroring iter-v3/044
    ALGO mechanism. QR EDA shows LDO IS->OOS exit-composition shift is the binding
    constraint; wider SL targets it directly.

    NOT the iter-v3/032 (1.5, 0.75) tighter-barrier variant — that was
    MULTI-SEED-FALSIFIED at iter-v3/039 multi-seed CONFIRMATION (broke IS Sharpe -0.59).
    iter-v3/045 is the OPPOSITE direction (wider not tighter).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL missing 'LDOUSDT' key — must be PRESENT at "
        f"iter-v3/045. NEW per-symbol entry per QR EDA SHA `ed949fe`. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_entry = V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"]
    assert ldo_entry == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT'] = {ldo_entry} — expected (2.0, 1.5). "
        f"iter-v3/045: TP unchanged (2.0×ATR), SL widened by 50% (1.0 -> 1.5×ATR). "
        f"NOT the forbidden (1.5, 0.75) tighter-barrier variant from iter-v3/032."
    )
    ldo_result = atr_multipliers_for_symbol("LDOUSDT")
    assert ldo_result == (2.0, 1.5), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (2.0, 1.5). "
        f"iter-v3/045: LDOUSDT per-symbol entry = (2.0, 1.5) (wider SL)."
    )


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.0) via DEFAULT fallback at iter-v3/045.

    BCH has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL has only
    ALGOUSDT + LDOUSDT). DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at iter-v3/045. "
        f"BCH must use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) fallback (no per-symbol entry). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.0). "
        f"iter-v3/045: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); BCH uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_has_algo_and_ldo():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 2 entries: ALGOUSDT + LDOUSDT
    at iter-v3/045.

    iter-v3/044: V3_ATR_MULTIPLIERS_PER_SYMBOL had 1 entry (ALGOUSDT only).
    iter-v3/045: ADD LDOUSDT at (2.0, 1.5) — QR EDA-driven mirror of iter-v3/044
                 ALGO mechanism. SHA `ed949fe`.
    Other symbols (BCH/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 2, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 2 entries at iter-v3/045. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}."
    )
    assert "ALGOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'ALGOUSDT' at iter-v3/045 "
        f"(carried forward from iter-v3/044). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'LDOUSDT' at iter-v3/045 (NEW). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT'] = "
        f"{V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT']} — expected (2.0, 1.5)."
    )
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT'] = "
        f"{V3_ATR_MULTIPLIERS_PER_SYMBOL['LDOUSDT']} — expected (2.0, 1.5)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies (2.0, 1.5) for ALGO + LDO; (2.0, 1.0) for BCH at iter-v3/045."""
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
    _cfg_algo, strat_algo = _build_v3_model(
        symbol="ALGOUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    # iter-v3/045: BCH uses REVERTED DEFAULT (2.0, 1.0) via fallback.
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/045: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.0, (
        f"BCH atr_sl_multiplier: expected 1.0, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/045: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    # iter-v3/045: LDO uses NEW per-symbol entry (2.0, 1.5) — wider SL.
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/045: LDO per-symbol entry (2.0, 1.5) — TP unchanged at 2.0×ATR."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.5, (
        f"LDO atr_sl_multiplier: expected 1.5, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/045: LDO per-symbol entry (2.0, 1.5) — SL widened to 1.5×ATR (NEW)."
    )
    # iter-v3/044: ALGO uses per-symbol entry (2.0, 1.5) — UNCHANGED at iter-v3/045.
    assert strat_algo.inner.atr_tp_multiplier == 2.0, (
        f"ALGO atr_tp_multiplier: expected 2.0, got {strat_algo.inner.atr_tp_multiplier}. "
        "iter-v3/045: ALGO per-symbol entry (2.0, 1.5) — TP unchanged at 2.0×ATR."
    )
    assert strat_algo.inner.atr_sl_multiplier == 1.5, (
        f"ALGO atr_sl_multiplier: expected 1.5, got {strat_algo.inner.atr_sl_multiplier}. "
        "iter-v3/045: ALGO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/044."
    )
