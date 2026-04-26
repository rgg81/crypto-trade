"""Live-engine tests for v2 wrapper, V2 baseline models, and combined-track guards.

This file accumulates as Tasks 1-9 land. It mirrors `test_engine.py` for
v1, but covers the new code paths that v2 introduces:
  - Per-model `ModelConfig` overrides (Task 1)
  - `ModelRunner` field resolution with `LiveConfig` fallback (Task 2)
  - `RiskV2Wrapper` wrapping when `risk_wrapper="v2"` (Task 3)
  - `V2_BASELINE_MODELS` / `COMBINED_MODELS` shape (Task 5)
  - `LiveEngine` exclusion + disjointness guards (Task 6)
  - BTC trend filter helper (Task 7)
  - `LiveEngine.catch_up_only()` smoke (Task 9)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.live.models import LiveConfig, ModelConfig


# ----------------------------- Task 1 ---------------------------------------


def test_v1_model_config_keeps_defaults_unchanged():
    """All new override fields default to None ⇒ v1 ModelConfigs preserve pre-change behavior."""
    mc = ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    assert mc.feature_columns is None
    assert mc.features_dir is None
    assert mc.atr_column is None
    assert mc.cooldown_candles is None
    assert mc.vol_targeting is None
    assert mc.ensemble_seeds is None
    assert mc.risk_wrapper == "none"
    assert mc.risk_v2_config is None


# ----------------------------- Task 2 ---------------------------------------


def test_model_runner_resolves_with_fallback():
    """ModelRunner exposes resolved fields and inner_strategy / inner_atr_column.

    A v1-style ModelConfig (all overrides None) resolves to LiveConfig values.
    A v2-style ModelConfig with overrides resolves to its own values, and its
    inner_atr_column reflects the explicit atr_column kwarg passed to LightGbm.
    """
    from crypto_trade.live.engine import ModelRunner

    live = LiveConfig()  # cooldown_candles=2, features_dir=Path("data/features"), ...

    mc_default = ModelConfig(
        name="A",
        symbols=("BTCUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    mc_override = ModelConfig(
        name="V2-DOGE",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        cooldown_candles=4,
        features_dir=Path("data/features_v2"),
        atr_column="natr_21_raw",
        vol_targeting=False,
    )

    r1 = ModelRunner(mc_default, live)
    r2 = ModelRunner(mc_override, live)

    # v1 defaults fall back to LiveConfig
    assert r1.cooldown_candles == 2
    assert str(r1.features_dir) == "data/features"
    assert r1.vol_targeting is True
    assert r1.inner_atr_column == "vol_natr_21"  # LightGbmStrategy default
    assert r1.inner_strategy is r1.strategy  # no wrapping yet (Task 3)

    # v2 overrides take precedence
    assert r2.cooldown_candles == 4
    assert str(r2.features_dir) == "data/features_v2"
    assert r2.vol_targeting is False
    assert r2.inner_atr_column == "natr_21_raw"


# ----------------------------- Task 3 ---------------------------------------


def test_v2_runner_wraps_strategy_with_riskv2():
    """When risk_wrapper='v2', ModelRunner wraps the inner LGBM in RiskV2Wrapper."""
    from crypto_trade.live.engine import ModelRunner
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

    live = LiveConfig()
    mc = ModelConfig(
        name="V2-DOGE",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        features_dir=Path("data/features_v2"),
        cooldown_candles=4,
        vol_targeting=False,
        ood_enabled=False,
        risk_wrapper="v2",
        risk_v2_config=RiskV2Config(zscore_threshold=2.5),
    )
    runner = ModelRunner(mc, live)
    assert isinstance(runner.strategy, RiskV2Wrapper)
    # Inner strategy stays accessible — patcher relies on this
    assert runner.inner_strategy is not runner.strategy
    assert runner.inner_strategy is runner.strategy.inner
    # Wrapper must expose atr_column for use by the patcher and any caller
    # that currently reads strategy.atr_column directly.
    assert runner.strategy.atr_column == runner.inner_atr_column == "natr_21_raw"


def test_v2_runner_requires_risk_v2_config():
    """risk_wrapper='v2' without a config must raise — no silent default."""
    from crypto_trade.live.engine import ModelRunner

    live = LiveConfig()
    mc = ModelConfig(
        name="V2-bad",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        risk_wrapper="v2",
        risk_v2_config=None,
    )
    with pytest.raises(ValueError, match="risk_v2_config"):
        ModelRunner(mc, live)
