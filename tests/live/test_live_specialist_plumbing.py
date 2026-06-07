"""Tests for C1/C3/C5/C6 fix: specialist + AXIS-R plumbing in ModelConfig + ModelRunner.

Verifies that:
  - ModelConfig carries all new specialist / AXIS-R fields with correct defaults.
  - ModelRunner threads those fields through to the inner LightGbmStrategy.
  - Legacy ModelConfig instances remain BIT-IDENTICAL (default fields are no-ops).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.live.engine import ModelRunner
from crypto_trade.live.models import LiveConfig, ModelConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_model(**overrides) -> ModelConfig:
    """Return a minimal ModelConfig suitable for ModelRunner construction."""
    defaults = dict(
        name="TEST",
        symbols=("BTCUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    defaults.update(overrides)
    return ModelConfig(**defaults)


def _live_config() -> LiveConfig:
    return LiveConfig(features_dir=Path("/tmp/nonexistent_features"))


# ---------------------------------------------------------------------------
# C1/C5/C6 — ModelConfig field existence and correct defaults
# ---------------------------------------------------------------------------


class TestModelConfigHasSpecialistFields:
    """ModelConfig carries all new specialist + AXIS-R fields with correct defaults."""

    def test_specialist_mode_default_false(self):
        mc = _minimal_model()
        assert mc.specialist_mode is False

    def test_specialist_seed_count_default_zero(self):
        mc = _minimal_model()
        assert mc.specialist_seed_count == 0

    def test_specialist_optuna_trials_default_zero(self):
        mc = _minimal_model()
        assert mc.specialist_optuna_trials == 0

    def test_specialist_n_startup_trials_default_ten(self):
        mc = _minimal_model()
        assert mc.specialist_n_startup_trials == 10

    def test_specialist_n_estimators_max_default_500(self):
        mc = _minimal_model()
        assert mc.specialist_n_estimators_max == 500

    def test_bounds_profile_default_v1_pruned(self):
        mc = _minimal_model()
        assert mc.bounds_profile == "v1_pruned"

    def test_enable_mid_bull_short_veto_default_false(self):
        mc = _minimal_model()
        assert mc.enable_mid_bull_short_veto is False

    def test_mid_bull_short_veto_lo_default(self):
        mc = _minimal_model()
        assert mc.mid_bull_short_veto_lo == pytest.approx(0.20)

    def test_mid_bull_short_veto_hi_default(self):
        mc = _minimal_model()
        assert mc.mid_bull_short_veto_hi == pytest.approx(0.50)

    def test_mid_bull_short_veto_lookback_default(self):
        mc = _minimal_model()
        assert mc.mid_bull_short_veto_lookback == 270

    def test_specialist_fields_settable(self):
        """All specialist fields can be set to non-default values."""
        mc = ModelConfig(
            name="SP",
            symbols=("BTCUSDT",),
            use_atr_labeling=True,
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
            specialist_mode=True,
            specialist_seed_count=50,
            specialist_optuna_trials=30,
            specialist_n_startup_trials=5,
            specialist_n_estimators_max=300,
            bounds_profile="v1_pruned",
            enable_mid_bull_short_veto=True,
            mid_bull_short_veto_lo=0.20,
            mid_bull_short_veto_hi=0.50,
            mid_bull_short_veto_lookback=270,
        )
        assert mc.specialist_mode is True
        assert mc.specialist_seed_count == 50
        assert mc.specialist_optuna_trials == 30
        assert mc.specialist_n_startup_trials == 5
        assert mc.specialist_n_estimators_max == 300
        assert mc.bounds_profile == "v1_pruned"
        assert mc.enable_mid_bull_short_veto is True
        assert mc.mid_bull_short_veto_lo == pytest.approx(0.20)
        assert mc.mid_bull_short_veto_hi == pytest.approx(0.50)
        assert mc.mid_bull_short_veto_lookback == 270

    def test_legacy_modelconfig_unchanged(self):
        """BASELINE_MODELS construction still works after adding new fields."""
        from crypto_trade.live.models import BASELINE_MODELS

        # All 4 legacy models should be constructable without specialist fields.
        for mc in BASELINE_MODELS:
            assert mc.specialist_mode is False
            assert mc.enable_mid_bull_short_veto is False


# ---------------------------------------------------------------------------
# C1/C5/C6 — ModelRunner threads specialist kwargs to LightGbmStrategy
# ---------------------------------------------------------------------------


class TestModelRunnerThreadsSpecialistKwargs:
    """ModelRunner passes specialist fields to the inner LightGbmStrategy."""

    def test_specialist_mode_false_by_default(self):
        """Legacy ModelConfig produces inner strategy with specialist_mode=False."""
        mc = _minimal_model()
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._specialist_mode is False

    def test_specialist_mode_true_threaded(self):
        """specialist_mode=True reaches LightGbmStrategy._specialist_mode."""
        mc = _minimal_model(specialist_mode=True)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._specialist_mode is True

    def test_specialist_n_startup_trials_threaded(self):
        mc = _minimal_model(specialist_mode=True, specialist_n_startup_trials=5)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._specialist_n_startup_trials == 5

    def test_specialist_n_estimators_max_threaded(self):
        mc = _minimal_model(specialist_mode=True, specialist_n_estimators_max=300)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._specialist_n_estimators_max == 300

    def test_bounds_profile_threaded(self):
        mc = _minimal_model(bounds_profile="v1_pruned")
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._bounds_profile == "v1_pruned"

    def test_specialist_optuna_trials_overrides_n_trials(self):
        """When specialist_mode=True + specialist_optuna_trials>0, n_trials is overridden."""
        mc = _minimal_model(specialist_mode=True, specialist_optuna_trials=30)
        runner = ModelRunner(mc, _live_config())
        # LightGbmStrategy.n_trials should match the specialist override (30),
        # NOT the LiveConfig default (50).
        assert runner.inner_strategy.n_trials == 30

    def test_specialist_optuna_trials_zero_falls_back_to_live_config(self):
        """When specialist_optuna_trials=0 (default), LiveConfig.n_trials is used."""
        mc = _minimal_model(specialist_mode=True, specialist_optuna_trials=0)
        cfg = LiveConfig(features_dir=Path("/tmp"), n_trials=42)
        runner = ModelRunner(mc, cfg)
        assert runner.inner_strategy.n_trials == 42

    def test_per_model_n_trials_override_no_specialist(self):
        """ModelConfig.n_trials (non-specialist) overrides LiveConfig.n_trials."""
        mc = _minimal_model(n_trials=18)
        cfg = LiveConfig(features_dir=Path("/tmp"), n_trials=50)
        runner = ModelRunner(mc, cfg)
        assert runner.inner_strategy.n_trials == 18

    def test_per_model_training_months_override(self):
        """ModelConfig.training_months overrides LiveConfig.training_months."""
        mc = _minimal_model(training_months=12)
        cfg = LiveConfig(features_dir=Path("/tmp"), training_months=24)
        runner = ModelRunner(mc, cfg)
        assert runner.inner_strategy.training_months == 12

    def test_per_model_cv_splits_override(self):
        """ModelConfig.cv_splits overrides LiveConfig.cv_splits."""
        mc = _minimal_model(cv_splits=3)
        cfg = LiveConfig(features_dir=Path("/tmp"), cv_splits=5)
        runner = ModelRunner(mc, cfg)
        assert runner.inner_strategy.cv_splits == 3


# ---------------------------------------------------------------------------
# C3 — AXIS-R Mid-Bull SHORT VETO threading
# ---------------------------------------------------------------------------


class TestAxisRVetoThreaded:
    """AXIS-R Mid-Bull SHORT VETO fields reach LightGbmStrategy."""

    def test_veto_disabled_by_default(self):
        mc = _minimal_model()
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._enable_mid_bull_short_veto is False

    def test_veto_enabled_threaded(self):
        mc = _minimal_model(enable_mid_bull_short_veto=True)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._enable_mid_bull_short_veto is True

    def test_veto_lo_threaded(self):
        mc = _minimal_model(enable_mid_bull_short_veto=True, mid_bull_short_veto_lo=0.15)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._mid_bull_short_veto_lo == pytest.approx(0.15)

    def test_veto_hi_threaded(self):
        mc = _minimal_model(enable_mid_bull_short_veto=True, mid_bull_short_veto_hi=0.60)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._mid_bull_short_veto_hi == pytest.approx(0.60)

    def test_veto_lookback_threaded(self):
        mc = _minimal_model(enable_mid_bull_short_veto=True, mid_bull_short_veto_lookback=180)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._mid_bull_short_veto_lookback == 180

    def test_preregistered_band_defaults_match_brief(self):
        """Pre-registered band edges [0.20, 0.50] + lookback=270 match brief spec."""
        mc = _minimal_model(enable_mid_bull_short_veto=True)
        runner = ModelRunner(mc, _live_config())
        assert runner.inner_strategy._mid_bull_short_veto_lo == pytest.approx(0.20)
        assert runner.inner_strategy._mid_bull_short_veto_hi == pytest.approx(0.50)
        assert runner.inner_strategy._mid_bull_short_veto_lookback == 270

    def test_veto_disabled_legacy_models_unaffected(self):
        """All BASELINE_MODELS have veto disabled — no silent behavior change."""
        from crypto_trade.live.models import BASELINE_MODELS

        for mc in BASELINE_MODELS:
            runner = ModelRunner(mc, _live_config())
            assert runner.inner_strategy._enable_mid_bull_short_veto is False, (
                f"Model {mc.name} unexpectedly has AXIS-R veto enabled"
            )
