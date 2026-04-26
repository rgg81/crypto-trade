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


# ----------------------------- Task 5 ---------------------------------------


def test_v2_baseline_models_shape():
    """V2_BASELINE_MODELS mirrors run_baseline_v2.V2_MODELS field-for-field."""
    from crypto_trade.live.models import V2_BASELINE_MODELS, V2_EXCLUDED_SYMBOLS

    expected_symbols = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}
    actual_symbols = {s for mc in V2_BASELINE_MODELS for s in mc.symbols}
    assert actual_symbols == expected_symbols
    assert len(V2_BASELINE_MODELS) == 4

    for mc in V2_BASELINE_MODELS:
        assert mc.risk_wrapper == "v2"
        assert mc.risk_v2_config is not None
        # ood_enabled MUST be False — v2's z-score OOD lives in the wrapper;
        # leaving v1's R3 Mahalanobis enabled would double-gate.
        assert mc.ood_enabled is False
        assert mc.atr_column == "natr_21_raw"
        assert mc.cooldown_candles == 4
        assert mc.vol_targeting is False
        assert str(mc.features_dir) == "data/features_v2"
        assert mc.atr_tp_multiplier == 2.9
        assert mc.atr_sl_multiplier == 1.45
        assert set(mc.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS)


def test_combined_models_unions_v1_and_v2():
    from crypto_trade.live.models import (
        BASELINE_MODELS,
        COMBINED_MODELS,
        V2_BASELINE_MODELS,
    )
    assert len(COMBINED_MODELS) == len(BASELINE_MODELS) + len(V2_BASELINE_MODELS)
    # Symbols disjoint across the two presets
    v1_syms = {s for mc in BASELINE_MODELS for s in mc.symbols}
    v2_syms = {s for mc in V2_BASELINE_MODELS for s in mc.symbols}
    assert v1_syms.isdisjoint(v2_syms)


def test_v2_excluded_symbols_constant():
    from crypto_trade.live.models import V2_EXCLUDED_SYMBOLS
    assert set(V2_EXCLUDED_SYMBOLS) == {"BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"}


# ----------------------------- Task 6 ---------------------------------------


def test_engine_rejects_v2_with_v1_symbol(tmp_path):
    """A v2 ModelConfig naming any V2_EXCLUDED_SYMBOLS symbol must fail at engine init."""
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config

    bad = ModelConfig(
        name="bad-v2",
        symbols=("BTCUSDT",),  # v1 baseline symbol — disallowed
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        features_dir=Path("data/features_v2"),
        risk_wrapper="v2",
        risk_v2_config=RiskV2Config(),
    )
    cfg = LiveConfig(
        models=(bad,),
        dry_run=True,
        db_path=tmp_path / "x.db",
        data_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="V2_EXCLUDED_SYMBOLS"):
        LiveEngine(cfg)


def test_engine_rejects_overlapping_symbols(tmp_path):
    """Two ModelConfigs sharing a symbol corrupt R1/VT state — reject at init."""
    from crypto_trade.live.engine import LiveEngine

    a = ModelConfig(
        name="A1", symbols=("BTCUSDT",),
        use_atr_labeling=True, atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
    )
    b = ModelConfig(
        name="A2", symbols=("BTCUSDT",),  # collides with A1
        use_atr_labeling=True, atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
    )
    cfg = LiveConfig(
        models=(a, b),
        dry_run=True,
        db_path=tmp_path / "y.db",
        data_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="overlapping symbols"):
        LiveEngine(cfg)


def test_engine_combined_models_construct_ok(tmp_path):
    """COMBINED_MODELS must satisfy both guards (disjoint v1+v2 symbols)."""
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import COMBINED_MODELS

    cfg = LiveConfig(
        models=COMBINED_MODELS,
        dry_run=True,
        db_path=tmp_path / "z.db",
        data_dir=tmp_path,
    )
    LiveEngine(cfg)  # must not raise
