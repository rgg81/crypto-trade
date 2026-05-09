"""Adversarial tests for per-symbol ATR multipliers — iter-v3/044.

iter-v3/044 state (EXPLORATION — cycle 3 #5 — QR EDA-driven per-symbol ATR for ALGO):
  - DEFAULT_ATR_MULTIPLIERS unchanged at (2.0, 1.0) from iter-v3/043 revert.
  - V3_ATR_MULTIPLIERS_PER_SYMBOL has ONE entry: ALGOUSDT → (2.0, 1.5).
    Per QR EDA SHA `eff841e`: ALGO LONG SL/TP exit ratio 4.5:1 (largest IS attribution
    loss, 33 trades, -53.26 PnL, 18.2% IS WR / 11.1% OOS WR).
    Wider SL targets ALGO LONG bottleneck directly. Proven mechanism per iter-v3/032
    LDO ATR success.
  - BCH/LDO/TRX still fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  - Single-axis change: V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5).

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/044 (carried forward).
  2. BCH/LDO/TRX fall back to (2.0, 1.0) (no per-symbol entry).
  3. ALGOUSDT returns (2.0, 1.5) — via per-symbol entry.
  4. V3_ATR_MULTIPLIERS_PER_SYMBOL has 1 entry: ALGOUSDT.
  5. The runner's _build_v3_model dispatches (2.0, 1.0) for BCH/LDO; (2.0, 1.5) for ALGO.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/044 (unchanged from iter-v3/043).

    iter-v3/044: V3_ATR_MULTIPLIERS_PER_SYMBOL has ALGOUSDT entry (2.0, 1.5) per QR EDA.
    Non-ALGO symbols (BCH/LDO/TRX) fall back to DEFAULT.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/044: DEFAULT unchanged from iter-v3/043 revert. "
        "Verify in features_v3/__init__.py."
    )
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    # iter-v3/044: ALGOUSDT now has per-symbol entry (2.0, 1.5).
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5), (
        "ALGOUSDT must return (2.0, 1.5) at iter-v3/044 (per-symbol entry per QR EDA "
        "SHA `eff841e`). Wider SL targets ALGO LONG SL/TP exit asymmetry (27/6 = 4.5:1)."
    )
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)
    # LDO returns (2.0, 1.0) via DEFAULT at iter-v3/044 (no per-symbol entry).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0), (
        "LDOUSDT must return (2.0, 1.0) at iter-v3/044 (DEFAULT fallback). "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL has only ALGOUSDT entry — LDO uses DEFAULT."
    )


def test_atr_multipliers_ldo_universal_tighter():
    """LDO must return (2.0, 1.0) — via REVERTED DEFAULT — at iter-v3/043.

    iter-v3/042: LDO returned (1.5, 0.75) via DEFAULT (tighter).
    iter-v3/043: DEFAULT REVERTED to (2.0, 1.0); LDO still uses DEFAULT fallback.
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — LDO has no per-symbol entry.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/043. "
        f"LDO must use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) fallback (no per-symbol entry). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_result = atr_multipliers_for_symbol("LDOUSDT")
    assert ldo_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (2.0, 1.0). "
        f"iter-v3/043: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); LDO uses DEFAULT fallback."
    )


def test_atr_multipliers_bch_universal_tighter():
    """BCH must return (2.0, 1.0) via REVERTED DEFAULT at iter-v3/043.

    BCH has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
    DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) at iter-v3/043 (REVERTED from (1.5, 0.75)).
    """
    from crypto_trade.features_v3 import atr_multipliers_for_symbol

    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.0). "
        f"iter-v3/043: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); BCH uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_has_algo():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 1 entry: ALGOUSDT → (2.0, 1.5) at iter-v3/044.

    iter-v3/044: QR EDA-driven per-symbol ATR for ALGO (SHA `eff841e`).
    ALGO LONG SL/TP exit ratio 4.5:1 (largest IS attribution loss); wider SL targets bottleneck.
    Other symbols (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 1, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must have exactly 1 entry at iter-v3/044. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}."
    )
    assert "ALGOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must contain 'ALGOUSDT' at iter-v3/044. "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] == (2.0, 1.5), (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT'] = "
        f"{V3_ATR_MULTIPLIERS_PER_SYMBOL['ALGOUSDT']} — expected (2.0, 1.5)."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies (2.0, 1.0) for ALL symbols at iter-v3/043 (REVERTED DEFAULT)."""
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
    # iter-v3/043: ALL symbols use REVERTED DEFAULT (2.0, 1.0).
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/043: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.0, (
        f"BCH atr_sl_multiplier: expected 1.0, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/043: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/043: LDO uses DEFAULT (2.0, 1.0) via empty per-symbol dict."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.0, (
        f"LDO atr_sl_multiplier: expected 1.0, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/043: LDO uses DEFAULT (2.0, 1.0) via empty per-symbol dict."
    )
