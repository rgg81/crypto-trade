"""Adversarial tests for per-symbol ATR multipliers — iter-v3/047.

iter-v3/047 state (EXPLORATION — cycle 3 #8 — REVERT iter-v3/046 BCH ATR per Critic
                    FINAL `5dae6d6`; QR-driven BCH direction-asymmetric axis chosen
                    SEPARATELY at the brief Section 3 level — see brief for new axis):
  - DEFAULT_ATR_MULTIPLIERS unchanged at (2.0, 1.0) from iter-v3/043 revert.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL has TWO entries (state = iter-v3/045 config):
      ALGOUSDT → (2.0, 1.5) — UNCHANGED from iter-v3/044 PROMISING result.
      LDOUSDT  → (2.0, 1.5) — UNCHANGED from iter-v3/045 STRONGEST PROMISING result.
      BCHUSDT  REMOVED (was (2.0, 1.5) at iter-v3/046; -45 OOS swing). REVERT per
        Critic FINAL `5dae6d6`: "Stable SL:TP across IS/OOS = WRONG axis. Wider-SL
        mechanism is REGIME-MISMATCH-SPECIFIC." BCH falls back to DEFAULT (2.0, 1.0).
  - TRX still falls back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  - Single-axis change (this iter): V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] REMOVED.
    ALGOUSDT and LDOUSDT entries UNCHANGED from iter-v3/045/046.
  - The NEW iter-v3/047 axis (BCH direction-asymmetric mechanism) is dispatched at a
    DIFFERENT layer (signal-side filter or per-direction barrier — see brief Section 3).
    This test file validates the labeling-layer state (V3_ATR_MULTIPLIERS_PER_SYMBOL
    must be back to iter-v3/045 config); the new direction-axis tests live elsewhere
    (or are in this file if dispatched at the same layer; orchestrator brief mandates
    the QR's chosen axis layer).

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/047 (carried forward).
  2. TRX falls back to (2.0, 1.0) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.5) — via per-symbol entry (UNCHANGED from iter-v3/044).
  4. LDOUSDT returns (2.0, 1.5) — via per-symbol entry (UNCHANGED from iter-v3/045).
  5. BCHUSDT returns (2.0, 1.0) — via DEFAULT fallback (REVERT iter-v3/046; not in dict).
  6. V3_ATR_MULTIPLIERS_PER_SYMBOL has 2 entries: ALGOUSDT, LDOUSDT (BCHUSDT REMOVED).
  7. The runner's _build_v3_model dispatches (2.0, 1.0) for TRX + BCH; (2.0, 1.5) for
     ALGO/LDO.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/047 (unchanged from iter-v3/045/046).

    iter-v3/047: V3_ATR_MULTIPLIERS_PER_SYMBOL has only ALGOUSDT + LDOUSDT entries
    (both (2.0, 1.5)). Non-{ALGO,LDO} symbols (TRX, BCH) fall back to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/047: DEFAULT unchanged from iter-v3/045/046. "
        "Verify in features_v3/__init__.py."
    )
    # iter-v3/047: TRX uses DEFAULT fallback (no per-symbol entry — see iter-v3/046 brief 2.7).
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/044: ALGOUSDT has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5), (
        "ALGOUSDT must return (2.0, 1.5) at iter-v3/047 (per-symbol entry per QR EDA "
        "SHA `eff841e`; UNCHANGED from iter-v3/044 PROMISING)."
    )
    # iter-v3/045: LDOUSDT has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5), (
        "LDOUSDT must return (2.0, 1.5) at iter-v3/047 (per-symbol entry per QR EDA "
        "SHA `ed949fe`; UNCHANGED from iter-v3/045 STRONGEST PROMISING)."
    )
    # iter-v3/047 REVERT: BCHUSDT entry REMOVED — falls back to DEFAULT (2.0, 1.0).
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0), (
        "BCHUSDT must return (2.0, 1.0) at iter-v3/047 (DEFAULT fallback; REVERT "
        "iter-v3/046 (2.0, 1.5) per Critic FINAL `5dae6d6`). Mirror mechanism "
        "(wider SL) doesn't transfer to symbols with stable SL:TP — BCH IS=OOS "
        "SL:TP=1.93 stable. iter-v3/046 caused -45 BCH OOS swing."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_bch_default_fallback():
    """BCH must return (2.0, 1.0) — via DEFAULT fallback — at iter-v3/047.

    iter-v3/045: BCHUSDT used DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    iter-v3/046: BCHUSDT entry ADDED at (2.0, 1.5) — 3rd application of validated
                  wider-SL mechanism. Result: NEGATIVE — BCH IS-axis collapse + -45 OOS swing.
    iter-v3/047: BCHUSDT entry REMOVED per Critic FINAL `5dae6d6` recommendation.
                  State = iter-v3/045 config. Mirror mechanism is REGIME-MISMATCH-SPECIFIC;
                  BCH IS=OOS SL:TP=1.93 stable means BCH is NOT a regime-mismatch case.

    The NEW iter-v3/047 axis (BCH direction-asymmetric mechanism) is dispatched at a
    DIFFERENT layer (signal-side filter or per-direction barrier — see brief Section 3).
    This test enforces the labeling-layer state ONLY (V3_ATR_MULTIPLIERS_PER_SYMBOL =
    iter-v3/045 config; BCH absent).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'BCHUSDT' key — must be ABSENT at "
        f"iter-v3/047. REVERT iter-v3/046 per Critic FINAL `5dae6d6` (mirror "
        f"mechanism failed on stable-SL:TP symbols; BCH -45 OOS swing). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.0). "
        f"iter-v3/047: BCHUSDT REVERTED; uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via "
        f"fallback. iter-v3/046 BCH ATR (2.0, 1.5) caused -45 OOS swing."
    )


def test_atr_multipliers_trx_default_fallback():
    """TRX must return (2.0, 1.0) via DEFAULT fallback at iter-v3/047.

    TRX has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL has only
    ALGOUSDT + LDOUSDT). DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).

    Per iter-v3/046 brief Section 2.7: TRX OOS SL:TP=0.96 (already < IS=2.24) — wider SL
    would HURT TRX OOS. TRX deliberately skipped at iter-v3/046 and remains skipped at
    iter-v3/047; reserved for future EXPLORATION with OOS-regression-risk awareness.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "TRXUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'TRXUSDT' key — must be ABSENT at iter-v3/047. "
        f"TRX must use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) fallback (no per-symbol entry). "
        f"Per iter-v3/046 brief Section 2.7: TRX OOS SL:TP=0.96 already < IS — widening SL "
        f"would HURT OOS. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    trx_result = atr_multipliers_for_symbol("TRXUSDT")
    assert trx_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('TRXUSDT') returned {trx_result} — expected (2.0, 1.0). "
        f"iter-v3/047: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); TRX uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_has_algo_and_ldo():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 2 entries: ALGOUSDT + LDOUSDT
    at iter-v3/047 (state = iter-v3/045 config; BCHUSDT entry REVERTED).

    iter-v3/045: V3_ATR_MULTIPLIERS_PER_SYMBOL had 2 entries (ALGOUSDT + LDOUSDT).
    iter-v3/046: ADD BCHUSDT at (2.0, 1.5) — 3rd application of wider-SL mechanism.
                  Result: NEGATIVE — BCH IS collapse + -45 OOS swing.
    iter-v3/047: REVERT BCHUSDT per Critic FINAL `5dae6d6`. State = iter-v3/045 config.
    Other symbols (TRX, BCH) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 2, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 2 entries at iter-v3/047. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"State after iter-v3/047 REVERT = iter-v3/045 config (ALGOUSDT + LDOUSDT only)."
    )
    assert "ALGOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'ALGOUSDT' at iter-v3/047 "
        f"(carried forward from iter-v3/044). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'LDOUSDT' at iter-v3/047 "
        f"(carried forward from iter-v3/045). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert "BCHUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must NOT contain 'BCHUSDT' at iter-v3/047 "
        f"(REVERTED per Critic FINAL `5dae6d6`). "
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
    applies (2.0, 1.5) for ALGO + LDO; (2.0, 1.0) for TRX + BCH at iter-v3/047."""
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
    # iter-v3/047 REVERT: BCH uses DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/047 REVERT: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.0, (
        f"BCH atr_sl_multiplier: expected 1.0, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/047 REVERT: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback "
        "(was 1.5 at iter-v3/046; reverted per Critic FINAL `5dae6d6`)."
    )
    # iter-v3/045: LDO uses per-symbol entry (2.0, 1.5) — UNCHANGED at iter-v3/047.
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/047: LDO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/045."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.5, (
        f"LDO atr_sl_multiplier: expected 1.5, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/047: LDO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/045."
    )
    # iter-v3/044: ALGO uses per-symbol entry (2.0, 1.5) — UNCHANGED at iter-v3/047.
    assert strat_algo.inner.atr_tp_multiplier == 2.0, (
        f"ALGO atr_tp_multiplier: expected 2.0, got {strat_algo.inner.atr_tp_multiplier}. "
        "iter-v3/047: ALGO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/044."
    )
    assert strat_algo.inner.atr_sl_multiplier == 1.5, (
        f"ALGO atr_sl_multiplier: expected 1.5, got {strat_algo.inner.atr_sl_multiplier}. "
        "iter-v3/047: ALGO per-symbol entry (2.0, 1.5) — UNCHANGED from iter-v3/044."
    )
    # iter-v3/047: TRX uses DEFAULT (2.0, 1.0) via fallback (no per-symbol entry).
    assert strat_trx.inner.atr_tp_multiplier == 2.0, (
        f"TRX atr_tp_multiplier: expected 2.0, got {strat_trx.inner.atr_tp_multiplier}. "
        "iter-v3/047: TRX uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_trx.inner.atr_sl_multiplier == 1.0, (
        f"TRX atr_sl_multiplier: expected 1.0, got {strat_trx.inner.atr_sl_multiplier}. "
        "iter-v3/047: TRX uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
