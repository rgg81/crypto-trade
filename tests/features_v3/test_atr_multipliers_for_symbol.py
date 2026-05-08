"""Adversarial tests for iter-v3/032 per-symbol ATR multipliers.

Validates:
  1. Symbols absent from V3_ATR_MULTIPLIERS_PER_SYMBOL fall back to (2.0, 1.0).
  2. LDOUSDT returns the EDA-tuned (1.5, 0.75) multipliers.
  3. The runner's _build_v3_model dispatches per-symbol multipliers correctly.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """Symbols not in V3_ATR_MULTIPLIERS_PER_SYMBOL fall back to (2.0, 1.0)."""
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_ldo():
    """LDO returns the iter-v3/032 EDA-tuned (1.5, 0.75) multipliers."""
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] == (1.5, 0.75)
    assert atr_multipliers_for_symbol("LDOUSDT") == (1.5, 0.75)


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    correctly applies different multipliers per symbol."""
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
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0
    assert strat_bch.inner.atr_sl_multiplier == 1.0
    assert strat_ldo.inner.atr_tp_multiplier == 1.5
    assert strat_ldo.inner.atr_sl_multiplier == 0.75
