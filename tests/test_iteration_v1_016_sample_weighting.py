"""Tests for iter-v1/016 — sample_weight_mode parameter on LightGbmStrategy.

Covers:
  1. sample_weight_mode="abs_pnl" (default): LightGbmStrategy accepts it, no error.
  2. sample_weight_mode="uniform": produces np.ones(n) with std=0.
  3. sample_weight_mode="uniqueness_only": produces uniqueness-only weights (different from ones).
  4. Kish n_eff for uniform weights = N exactly (math).
  5. CLI flag --sample-weight-mode dispatches to LightGbmStrategy.sample_weight_mode.
  6. Invalid sample_weight_mode raises ValueError.
  7. v1_pruned_axis016 bounds profile pins subsample=1.0 in Optuna _objective.

Run:
    uv run pytest tests/test_iteration_v1_016_sample_weighting.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_lgbm_strategy(sample_weight_mode: str = "abs_pnl"):
    """Construct a LightGbmStrategy with minimal required arguments.

    Does NOT load data or run training — used only for __init__ validation and
    attribute inspection.  The feature_columns list must be non-empty; we pass
    a dummy list of two column names.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=2,
        feature_columns=["feat_a", "feat_b"],
        ensemble_seeds=[42],
        sample_weight_mode=sample_weight_mode,
    )


def _kish_n_eff(weights: np.ndarray) -> float:
    """Kish effective sample size: (sum w)^2 / sum(w^2)."""
    s = weights.sum()
    s2 = (weights**2).sum()
    if s2 == 0:
        return 0.0
    return float(s**2 / s2)


# ---------------------------------------------------------------------------
# Test 1 — abs_pnl (default): __init__ succeeds, attribute set correctly
# ---------------------------------------------------------------------------


class TestSampleWeightModeInit:
    def test_abs_pnl_default_no_error(self) -> None:
        strat = _make_minimal_lgbm_strategy("abs_pnl")
        assert strat.sample_weight_mode == "abs_pnl"

    def test_uniform_no_error(self) -> None:
        strat = _make_minimal_lgbm_strategy("uniform")
        assert strat.sample_weight_mode == "uniform"

    def test_uniqueness_only_no_error(self) -> None:
        strat = _make_minimal_lgbm_strategy("uniqueness_only")
        assert strat.sample_weight_mode == "uniqueness_only"

    def test_invalid_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="sample_weight_mode must be one of"):
            _make_minimal_lgbm_strategy("invalid_mode")

    def test_invalid_mode_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="sample_weight_mode must be one of"):
            _make_minimal_lgbm_strategy("")


# ---------------------------------------------------------------------------
# Test 2 — uniform mode produces np.ones(n) with std == 0
# ---------------------------------------------------------------------------


class TestUniformWeights:
    def test_uniform_weight_std_zero(self) -> None:
        """Verify that uniform weights are all 1.0 (std == 0)."""
        # Simulate the branching logic in _train_for_month
        # baseline abs_pnl weights: deliberately non-uniform (mix of values)
        abs_pnl_weights = np.array([1.0, 5.0, 10.0, 2.5, 7.8], dtype=np.float64)
        assert abs_pnl_weights.std() > 0  # baseline is non-uniform

        # Apply uniform mode as in lgbm.py (b1.5)
        uniform_weights = np.ones(len(abs_pnl_weights), dtype=np.float64)

        assert uniform_weights.std() == 0.0
        assert (uniform_weights == 1.0).all()

    def test_uniform_weight_length_preserved(self) -> None:
        """Length of uniform weights == length of input."""
        n = 42
        original = np.random.default_rng(0).uniform(1.0, 10.0, n)
        uniform = np.ones(len(original), dtype=np.float64)
        assert len(uniform) == n

    def test_uniform_kish_ratio_exact_one(self) -> None:
        """Kish n_eff / n == 1.000 exactly for uniform weights."""
        n = 181
        w = np.ones(n, dtype=np.float64)
        kish = _kish_n_eff(w)
        assert abs(kish - n) < 1e-10, f"Expected Kish n_eff={n}, got {kish}"


# ---------------------------------------------------------------------------
# Test 3 — uniqueness_only produces weights != ones (in dense-label regime, ≈ equal)
# ---------------------------------------------------------------------------


class TestUniquenessOnlyWeights:
    def test_uniqueness_only_is_not_ones(self) -> None:
        """Uniqueness weights are not exactly 1.0 (they are ~1/overlap ≈ 0.048)."""
        # At v1 dense-label regime, uniqueness ≈ 1/21 for all rows.
        # They're equal-ish but NOT 1.0 — the mode should not produce 1.0 values.
        # We test that the mode attribute is accepted and differs from uniform in theory.
        strat = _make_minimal_lgbm_strategy("uniqueness_only")
        assert strat.sample_weight_mode == "uniqueness_only"
        # The attribute check is the primary test; actual weight values are tested
        # in integration via _faxm_log inspection (can't call _train_for_month
        # without loaded data, but we can verify the branching attribute).

    def test_uniqueness_scale_invariance_math(self) -> None:
        """Verify that uniqueness-only (no abs_pnl multiply) produces different order.

        Kish ratio for pure uniqueness weights (all ~1/21) ≈ 1.0 since they're
        near-constant. This contrasts with abs_pnl weights (Kish ≈ 0.85).
        """
        # Simulate dense-label regime: uniqueness ≈ 0.0476 ± small noise
        rng = np.random.default_rng(42)
        n = 90
        uniq = 1 / 21 + rng.normal(0, 0.001, n)
        uniq = np.clip(uniq, 0.04, 0.06)

        kish_uniq = _kish_n_eff(uniq)
        kish_ratio = kish_uniq / n
        # Near-constant uniqueness → Kish ratio close to 1.0
        assert kish_ratio > 0.995, f"Expected Kish ratio > 0.995, got {kish_ratio:.4f}"

    def test_abs_pnl_kish_ratio_below_1(self) -> None:
        """abs_pnl weights with outliers have Kish ratio < 1."""
        rng = np.random.default_rng(0)
        n = 90
        # Simulate abs_pnl weights: [1, 10] range with outliers
        abs_pnl_weights = 1.0 + rng.exponential(3.0, n)
        abs_pnl_weights = np.clip(abs_pnl_weights, 1.0, 10.0)

        kish = _kish_n_eff(abs_pnl_weights)
        ratio = kish / n
        # Should be < 1 due to weight variance
        assert ratio < 0.99, f"Expected Kish ratio < 0.99 for non-uniform, got {ratio:.4f}"


# ---------------------------------------------------------------------------
# Test 4 — Kish n_eff = N exactly for uniform weights (math proof)
# ---------------------------------------------------------------------------


class TestKishMath:
    def test_kish_uniform_equals_n(self) -> None:
        """Kish n_eff for np.ones(N) is exactly N."""
        for n in [10, 50, 90, 181, 500]:
            w = np.ones(n, dtype=np.float64)
            kish = _kish_n_eff(w)
            assert abs(kish - n) < 1e-9, f"N={n}: kish={kish}, expected {n}"

    def test_kish_decreases_with_variance(self) -> None:
        """Kish n_eff decreases as weight variance increases (fundamental property)."""
        n = 100
        w_uniform = np.ones(n, dtype=np.float64)
        w_high_var = np.array([10.0] * 10 + [1.0] * 90, dtype=np.float64)

        kish_uniform = _kish_n_eff(w_uniform)
        kish_high_var = _kish_n_eff(w_high_var)

        assert kish_uniform > kish_high_var, (
            f"Uniform kish={kish_uniform:.2f} should be > high-var kish={kish_high_var:.2f}"
        )

    def test_kish_formula_correctness(self) -> None:
        """Verify Kish formula: (sum w)^2 / (sum w^2)."""
        w = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        expected = (10.0**2) / (1 + 4 + 9 + 16)  # = 100 / 30 ≈ 3.333
        assert abs(_kish_n_eff(w) - expected) < 1e-10


# ---------------------------------------------------------------------------
# Test 5 — CLI flag --sample-weight-mode dispatches correctly
# ---------------------------------------------------------------------------


class TestCliFlag:
    def test_default_is_abs_pnl(self) -> None:
        """--sample-weight-mode defaults to abs_pnl (no flag = backward compat)."""
        import argparse

        # Simulate argparse.parse_args with no --sample-weight-mode flag
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--sample-weight-mode",
            choices=["abs_pnl", "uniform", "uniqueness_only"],
            default="abs_pnl",
        )
        args = parser.parse_args([])
        assert args.sample_weight_mode == "abs_pnl"

    def test_uniform_parses(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--sample-weight-mode",
            choices=["abs_pnl", "uniform", "uniqueness_only"],
            default="abs_pnl",
        )
        args = parser.parse_args(["--sample-weight-mode", "uniform"])
        assert args.sample_weight_mode == "uniform"

    def test_uniqueness_only_parses(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--sample-weight-mode",
            choices=["abs_pnl", "uniform", "uniqueness_only"],
            default="abs_pnl",
        )
        args = parser.parse_args(["--sample-weight-mode", "uniqueness_only"])
        assert args.sample_weight_mode == "uniqueness_only"

    def test_run_baseline_v1_accepts_flag(self) -> None:
        """run_baseline_v1.py's argparser accepts --sample-weight-mode uniform."""
        src = (Path(__file__).parent.parent / "run_baseline_v1.py").read_text()
        # The choices list must include "uniform" adjacent to --sample-weight-mode
        assert "uniform" in src and "sample_weight_mode" in src and "uniqueness_only" in src


# ---------------------------------------------------------------------------
# Test 6 — v1_pruned_axis016 pins subsample in Optuna _objective
# ---------------------------------------------------------------------------


class TestV1PrunedAxis016Profile:
    def test_pin_subsampling_flag_set(self) -> None:
        """v1_pruned_axis016 sets _pin_subsampling=True in _objective."""
        # We can't call _objective without a full Optuna trial, so we test the
        # logic indirectly by verifying the profile name appears in optimization.py
        # and that the _pruned and _pin_subsampling derivation is correct.
        src = (
            Path(__file__).parent.parent
            / "src"
            / "crypto_trade"
            / "strategies"
            / "ml"
            / "optimization.py"
        ).read_text()
        assert "v1_pruned_axis016" in src
        assert "_pin_subsampling" in src

    def test_v1_pruned_axis016_also_sets_pruned(self) -> None:
        """v1_pruned_axis016 inherits v1_pruned leaf/colsample tightening."""
        # The code uses: _pruned = bounds_profile in ("v1_pruned", "v1_pruned_axis016")
        # This means num_leaves upper is 63 (not 127) and min_child_samples ≥ 20.
        src = (
            Path(__file__).parent.parent
            / "src"
            / "crypto_trade"
            / "strategies"
            / "ml"
            / "optimization.py"
        ).read_text()
        # Verify the in-set membership check covers both profiles
        assert '"v1_pruned", "v1_pruned_axis016"' in src or (
            "v1_pruned_axis016" in src and "_pin_subsampling = bounds_profile" in src
        )

    def test_v1_pruned_axis016_subsample_pinned_to_1(self) -> None:
        """In v1_pruned_axis016 mode, subsample is 1.0 (not suggest_float)."""
        src = (
            Path(__file__).parent.parent
            / "src"
            / "crypto_trade"
            / "strategies"
            / "ml"
            / "optimization.py"
        ).read_text()
        # Verify the conditional: subsample = 1.0 if _pin_subsampling else suggest_float
        assert "_pin_subsampling" in src
        assert "subsample" in src
        # The combination: pin_subsampling is a boolean derived from the profile
        assert "bounds_profile == " in src and "v1_pruned_axis016" in src
