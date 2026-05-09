"""Adversarial tests for per-symbol ATR multipliers — iter-v3/046.

iter-v3/046 state (EXPLORATION — cycle 3 #7 — QR EDA-driven per-symbol ATR for BCH,
                    stacked on iter-v3/044 ALGO ATR + iter-v3/045 LDO ATR):
  - DEFAULT_ATR_MULTIPLIERS unchanged at (2.0, 1.0) from iter-v3/043 revert.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL has THREE entries:
      ALGOUSDT → (2.0, 1.5) — UNCHANGED from iter-v3/044 PROMISING result.
      LDOUSDT  → (2.0, 1.5) — UNCHANGED from iter-v3/045 STRONGEST PROMISING result.
      BCHUSDT  → (2.0, 1.5) — NEW iter-v3/046 entry.
        Per QR EDA SHA `d86b1f9`: BCH direction asymmetry: LONG IS -25.07% (39 trades,
        30.8% WR — toxic), SHORT IS +48.69% (55 trades, 43.6% WR). BCH IS=OOS SL:TP=1.93
        STABLE (no IS->OOS regime shift; mean_SL -3.90% IS / -3.45% OOS). Wider SL helps
        IS AND OOS SYMMETRICALLY, distinct mechanism from iter-v3/045 LDO which addressed
        an asymmetric IS->OOS shift. Third application of validated wider-SL mechanism.
  - TRX still falls back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    (TRX OOS SL:TP=0.96 already < IS=2.24 — wider SL would HURT TRX OOS; skipped this iter
    per brief Section 2.7.)
  - Single-axis change: V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5) ADDED.
    ALGOUSDT and LDOUSDT entries UNCHANGED from iter-v3/045.

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/046 (carried forward).
  2. TRX falls back to (2.0, 1.0) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.5) — via per-symbol entry (UNCHANGED from iter-v3/044).
  4. LDOUSDT returns (2.0, 1.5) — via per-symbol entry (UNCHANGED from iter-v3/045).
  5. BCHUSDT returns (2.0, 1.5) — via per-symbol entry (NEW iter-v3/046).
  6. V3_ATR_MULTIPLIERS_PER_SYMBOL has 3 entries: ALGOUSDT, LDOUSDT, BCHUSDT.
  7. The runner's _build_v3_model dispatches (2.0, 1.0) for TRX; (2.0, 1.5) for ALGO/LDO/BCH.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/046 (unchanged from iter-v3/045).

    iter-v3/046: V3_ATR_MULTIPLIERS_PER_SYMBOL has ALGOUSDT + LDOUSDT + BCHUSDT entries
    (all (2.0, 1.5)). Non-{ALGO,LDO,BCH} symbols (TRX) fall back to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/046: DEFAULT unchanged from iter-v3/045. "
        "Verify in features_v3/__init__.py."
    )
    # iter-v3/046: TRX uses DEFAULT fallback (no per-symbol entry — see brief Section 2.7).
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/044: ALGOUSDT has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5), (
        "ALGOUSDT must return (2.0, 1.5) at iter-v3/046 (per-symbol entry per QR EDA "
        "SHA `eff841e`; UNCHANGED from iter-v3/044 PROMISING)."
    )
    # iter-v3/045: LDOUSDT has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5), (
        "LDOUSDT must return (2.0, 1.5) at iter-v3/046 (per-symbol entry per QR EDA "
        "SHA `ed949fe`; UNCHANGED from iter-v3/045 STRONGEST PROMISING)."
    )
    # iter-v3/046: BCHUSDT has per-symbol entry (2.0, 1.5) — NEW.
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.5), (
        "BCHUSDT must return (2.0, 1.5) at iter-v3/046 (per-symbol entry per QR EDA "
        "SHA `d86b1f9`; NEW iter-v3/046 — 3rd application of validated wider-SL "
        "mechanism). BCH IS=OOS SL:TP=1.93 STABLE; LONG IS -25.07% toxic. Wider SL "
        "helps IS AND OOS SYMMETRICALLY."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_bch_per_symbol_widened():
    """BCH must return (2.0, 1.5) — via per-symbol entry — at iter-v3/046.

    iter-v3/045: BCHUSDT used DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    iter-v3/046: BCHUSDT entry ADDED at (2.0, 1.5) — 3rd application of validated
    wider-SL mechanism (mirror of iter-v3/044 ALGO + iter-v3/045 LDO PROMISINGs).

    QR EDA shows BCH direction asymmetry (LONG IS -25.07% toxic / SHORT IS +48.69%
    positive) and high SL rate (IS 59.6% / OOS 60.5%; SL:TP 1.93 stable across both
    windows). Wider SL helps IS AND OOS SYMMETRICALLY, distinct from iter-v3/045 LDO
    which addressed an asymmetric IS->OOS shift.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL missing 'BCHUSDT' key — must be PRESENT at "
        f"iter-v3/046. NEW per-symbol entry per QR EDA SHA `d86b1f9`. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_entry = V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"]
    assert bch_entry == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['BCHUSDT'] = {bch_entry} — expected (2.0, 1.5). "
        f"iter-v3/046: TP unchanged (2.0×ATR), SL widened by 50% (1.0 -> 1.5×ATR). "
        f"3rd application of validated wider-SL mechanism."
    )
    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.5), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.5). "
        f"iter-v3/046: BCHUSDT per-symbol entry = (2.0, 1.5) (wider SL)."
    )


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/046.

    TRX has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL has only
    ALGOUSDT + LDOUSDT + BCHUSDT). DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).

    Per brief Section 2.7: TRX OOS SL:TP=0.96 (already < IS=2.24) — wider SL would
    HURT TRX OOS. TRX deliberately skipped at iter-v3/046; reserved for future
    EXPLORATION with OOS-regression-risk awareness.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/046. "
        f"TRX must use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) fallback (no per-symbol entry). "
        f"Per brief Section 2.7: TRX OOS SL:TP=0.96 already < IS — widening SL would HURT OOS. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    trx_result = atr_multipliers_for_symbol("TRXUSDT")
    assert trx_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('TRXUSDT') returned {trx_result} — expected (2.0, 1.0). "
        f"iter-v3/046: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); TRX uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_has_algo_ldo_bch():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 3 entries: ALGOUSDT + LDOUSDT +
    BCHUSDT at iter-v3/046.

    iter-v3/045: V3_ATR_MULTIPLIERS_PER_SYMBOL had 2 entries (ALGOUSDT + LDOUSDT).
    iter-v3/046: ADD BCHUSDT at (2.0, 1.5) — QR EDA-driven 3rd application of
                 validated wider-SL mechanism. SHA `d86b1f9`.
    Other symbols (TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 3, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 3 entries at iter-v3/046. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}."
    )
    assert "ALGOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'ALGOUSDT' at iter-v3/046 "
        f"(carried forward from iter-v3/044). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'LDOUSDT' at iter-v3/046 "
        f"(carried forward from iter-v3/045). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert "BCHUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'BCHUSDT' at iter-v3/046 (NEW). "
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
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['BCHUSDT'] = "
        f"{V3_ATR_MULTIPLIERS_PER_SYMBOL['BCHUSDT']} — expected (2.0, 1.5)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies (2.0, 1.5) for ALGO + LDO + BCH; (2.0, 1.0) for TRX at iter-v3/046."""
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
    _cfg_trx, strat_trx = _build_v3_model(
        symbol="TRXUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    # iter-v3/046: BCH uses NEW per-symbol entry (2.0, 1.5) — wider SL.
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/046: BCH per-symbol entry (2.0, 1.5) — TP unchanged at 2.0×ATR."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.5, (
        f"BCH atr_sl_multiplier: expected 1.5, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/046: BCH per-symbol entry (2.0, 1.5) — SL widened to 1.5×ATR (NEW)."
    )
    # iter-v3/045: LDO uses per-symbol entry (2.0, 1.5) — UNCHANGED at iter-v3/046.
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/046: LDO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/045."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.5, (
        f"LDO atr_sl_multiplier: expected 1.5, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/046: LDO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/045."
    )
    # iter-v3/044: ALGO uses per-symbol entry (2.0, 1.5) — UNCHANGED at iter-v3/046.
    assert strat_algo.inner.atr_tp_multiplier == 2.0, (
        f"ALGO atr_tp_multiplier: expected 2.0, got {strat_algo.inner.atr_tp_multiplier}. "
        "iter-v3/046: ALGO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/044."
    )
    assert strat_algo.inner.atr_sl_multiplier == 1.5, (
        f"ALGO atr_sl_multiplier: expected 1.5, got {strat_algo.inner.atr_sl_multiplier}. "
        "iter-v3/046: ALGO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/044."
    )
    # iter-v3/046: TRX uses DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    assert strat_trx.inner.atr_tp_multiplier == 2.0, (
        f"TRX atr_tp_multiplier: expected 2.0, got {strat_trx.inner.atr_tp_multiplier}. "
        "iter-v3/046: TRX uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_trx.inner.atr_sl_multiplier == 1.0, (
        f"TRX atr_sl_multiplier: expected 1.0, got {strat_trx.inner.atr_sl_multiplier}. "
        "iter-v3/046: TRX uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
