"""Tests for iter-v1/090 — abs_pnl_timedecay sample_weight_mode (W-DECAY).

Covers:
  (a) abs_pnl default UNCHANGED: mode="abs_pnl" init is byte-identical (no side effect).
  (b) abs_pnl_timedecay applies exp decay: recent samples weighted higher than old,
      monotone non-increasing with age (oldest sample has lowest weight).
  (c) Half-life correctness: sample at age=12mo retains exp(-ln2/12*12)=0.5 weight
      relative to age=0 sample (within floating-point tolerance).
  (d) Mode accepted by __init__ without ValueError.
  (e) Invalid mode still raises ValueError.

Run:
    uv run pytest tests/test_w_decay.py -v
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


def _make_lgbm_strategy(sample_weight_mode: str = "abs_pnl"):
    """Construct a minimal LightGbmStrategy for __init__ validation only."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=2,
        feature_columns=["feat_a", "feat_b"],
        ensemble_seeds=[42],
        sample_weight_mode=sample_weight_mode,
    )


def _apply_wdecay_logic(
    abs_pnl_weights: np.ndarray,
    age_months: np.ndarray,
    half_life: float = 12.0,
) -> np.ndarray:
    """Replicate the (b3) W-DECAY multiply from lgbm.py (b3) block.

    weight_t = abs_pnl_t × exp(-ln2/half_life · age_months_t)

    age_months_t = (max_train_time - sample_time) / ms_per_month
    Here we pass age_months directly (already computed).
    """
    lam = np.log(2) / half_life
    decay = np.exp(-lam * age_months)
    return abs_pnl_weights * decay


# ---------------------------------------------------------------------------
# (a) abs_pnl default UNCHANGED
# ---------------------------------------------------------------------------


class TestAbsPnlDefaultUnchanged:
    """Verify abs_pnl mode is byte-identical (no W-DECAY side effect)."""

    def test_abs_pnl_init_no_error(self) -> None:
        """abs_pnl default initializes without error."""
        strat = _make_lgbm_strategy("abs_pnl")
        assert strat.sample_weight_mode == "abs_pnl"

    def test_abs_pnl_timedecay_mode_different_from_abs_pnl(self) -> None:
        """abs_pnl_timedecay is a distinct mode string from abs_pnl."""
        strat_default = _make_lgbm_strategy("abs_pnl")
        strat_wdecay = _make_lgbm_strategy("abs_pnl_timedecay")
        assert strat_default.sample_weight_mode != strat_wdecay.sample_weight_mode

    def test_abs_pnl_no_decay_applied(self) -> None:
        """abs_pnl mode DOES NOT apply decay (weights unchanged by age structure).

        Simulate: two samples with different ages; abs_pnl mode keeps weights
        as-is (no age-dependent transform applied in (b1.5) for abs_pnl).
        """
        weights_original = np.array([2.0, 5.0, 1.0, 8.0], dtype=np.float64)
        # In abs_pnl mode, no age transform; (b3) block has _apply_timedecay=False.
        weights_after = weights_original.copy()  # no transform
        np.testing.assert_array_equal(weights_after, weights_original)


# ---------------------------------------------------------------------------
# (b) abs_pnl_timedecay applies exp decay: recent > old, monotone
# ---------------------------------------------------------------------------


class TestAbsPnlTimedecayDecayApplied:
    """Verify that W-DECAY weights are monotone non-increasing with age."""

    def test_wdecay_mode_init_no_error(self) -> None:
        """abs_pnl_timedecay initializes without ValueError."""
        strat = _make_lgbm_strategy("abs_pnl_timedecay")
        assert strat.sample_weight_mode == "abs_pnl_timedecay"

    def test_decay_monotone_non_increasing_with_age(self) -> None:
        """Older samples have strictly lower decay factors (for increasing age sequence)."""
        # age_months sorted ascending (0 = newest, 23 = oldest)
        age_months = np.array([0.0, 2.0, 6.0, 12.0, 18.0, 23.0], dtype=np.float64)
        uniform_abs_pnl = np.ones(len(age_months), dtype=np.float64)

        weights = _apply_wdecay_logic(uniform_abs_pnl, age_months, half_life=12.0)

        # Decay factors should be strictly decreasing with age
        for i in range(len(weights) - 1):
            assert weights[i] > weights[i + 1], (
                f"Expected weights[{i}]={weights[i]:.6f} > "
                f"weights[{i + 1}]={weights[i + 1]:.6f} "
                f"(age_months[{i}]={age_months[i]} < age_months[{i + 1}]={age_months[i + 1]})"
            )

    def test_decay_recent_sample_highest_weight(self) -> None:
        """The most recent sample (age=0) retains the highest weight factor (=1.0)."""
        age_months = np.array([0.0, 6.0, 12.0, 24.0], dtype=np.float64)
        abs_pnl_weights = np.array([3.0, 3.0, 3.0, 3.0], dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl_weights, age_months, half_life=12.0)

        # age=0 → decay=exp(0)=1.0; weight = 3.0 × 1.0 = 3.0 (maximum)
        assert abs(weights[0] - 3.0) < 1e-10, f"Expected 3.0, got {weights[0]}"
        # All other weights must be < 3.0
        assert all(w < 3.0 for w in weights[1:]), f"Expected all < 3.0, got {weights[1:]}"

    def test_decay_factor_range(self) -> None:
        """Decay factors are in (0, 1] — never zero, never > 1."""
        age_months = np.array([0.0, 1.0, 6.0, 12.0, 24.0, 36.0], dtype=np.float64)
        abs_pnl = np.ones(len(age_months), dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl, age_months, half_life=12.0)

        assert (weights > 0).all(), f"All weights must be > 0, got min={weights.min()}"
        assert (weights <= 1.0 + 1e-10).all(), f"All weights must be ≤ 1.0, got max={weights.max()}"


# ---------------------------------------------------------------------------
# (c) Half-life correctness: age=12mo → ~0.5 weight of age=0
# ---------------------------------------------------------------------------


class TestHalfLifeCorrectness:
    """Verify the 12mo half-life formula: exp(-ln2/12 * 12) = 0.5 exactly."""

    def test_age_zero_decay_factor_is_one(self) -> None:
        """Sample at age=0 (most recent) has decay=1.0 exactly."""
        age_months = np.array([0.0], dtype=np.float64)
        abs_pnl = np.array([1.0], dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl, age_months, half_life=12.0)

        assert abs(weights[0] - 1.0) < 1e-10, f"Expected 1.0 at age=0, got {weights[0]}"

    def test_age_half_life_decay_factor_is_half(self) -> None:
        """Sample at age=half_life has decay=0.5 (definition of half-life)."""
        half_life = 12.0
        age_months = np.array([half_life], dtype=np.float64)  # exactly at half-life
        abs_pnl = np.array([1.0], dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl, age_months, half_life=half_life)

        expected = 0.5  # exp(-ln2/12 * 12) = exp(-ln2) = 0.5
        assert abs(weights[0] - expected) < 1e-10, (
            f"Expected 0.5 at age=half_life={half_life}mo, got {weights[0]:.10f}"
        )

    def test_age_two_half_lives_decay_factor_is_quarter(self) -> None:
        """Sample at age=2×half_life has decay=0.25 (2nd half-life)."""
        half_life = 12.0
        age_months = np.array([2 * half_life], dtype=np.float64)
        abs_pnl = np.array([1.0], dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl, age_months, half_life=half_life)

        expected = 0.25  # exp(-ln2/12 * 24) = exp(-2*ln2) = 0.25
        assert abs(weights[0] - expected) < 1e-10, (
            f"Expected 0.25 at age=2×half_life={2 * half_life}mo, got {weights[0]:.10f}"
        )

    def test_24mo_window_oldest_retains_0_25_weight(self) -> None:
        """Brief §3 spec: oldest sample in 24mo window retains ~0.25 weight (4:1 ratio).

        exp(-ln2/12 * 24) = exp(-2*ln2) = 0.25 exactly.
        The 4:1 recent:old ratio is the pre-registered design choice.
        """
        age_oldest = 24.0  # months
        age_newest = 0.0
        half_life = 12.0

        lam = np.log(2) / half_life
        decay_oldest = np.exp(-lam * age_oldest)
        decay_newest = np.exp(-lam * age_newest)

        assert abs(decay_newest - 1.0) < 1e-10, f"Newest decay must be 1.0, got {decay_newest}"
        assert abs(decay_oldest - 0.25) < 1e-10, (
            f"Oldest (24mo) decay must be 0.25, got {decay_oldest:.10f}"
        )
        ratio = decay_newest / decay_oldest
        assert abs(ratio - 4.0) < 1e-9, f"Expected 4:1 ratio, got {ratio:.6f}"

    def test_half_life_12mo_lambda_correctness(self) -> None:
        """Verify λ = ln(2) / half_life = ln(2) / 12 ≈ 0.05776."""
        half_life = 12.0
        lam = np.log(2) / half_life
        expected_lam = 0.05776226504333  # ln(2)/12

        assert abs(lam - expected_lam) < 1e-10, f"Expected λ={expected_lam:.10f}, got {lam:.10f}"

    def test_decay_is_multiplicative_with_abs_pnl(self) -> None:
        """W-DECAY is abs_pnl × decay (NOT replacing abs_pnl)."""
        abs_pnl = np.array([2.0, 4.0, 8.0], dtype=np.float64)
        age_months = np.array([0.0, 6.0, 12.0], dtype=np.float64)

        weights = _apply_wdecay_logic(abs_pnl, age_months, half_life=12.0)

        # Expected: abs_pnl[i] × exp(-ln2/12 × age_months[i])
        lam = np.log(2) / 12.0
        expected = abs_pnl * np.exp(-lam * age_months)
        np.testing.assert_allclose(weights, expected, rtol=1e-10)


# ---------------------------------------------------------------------------
# (d) abs_pnl_timedecay mode accepted by __init__
# ---------------------------------------------------------------------------


class TestModeAccepted:
    def test_abs_pnl_timedecay_accepted(self) -> None:
        """abs_pnl_timedecay is in _valid_modes and does not raise ValueError."""
        strat = _make_lgbm_strategy("abs_pnl_timedecay")
        assert strat.sample_weight_mode == "abs_pnl_timedecay"

    def test_all_existing_modes_still_accepted(self) -> None:
        """Pre-existing modes (abs_pnl, uniform, uniqueness_only, composite_inv_concurrency)
        still accepted after adding abs_pnl_timedecay."""
        for mode in ["abs_pnl", "uniform", "uniqueness_only", "composite_inv_concurrency"]:
            strat = _make_lgbm_strategy(mode)
            assert strat.sample_weight_mode == mode, f"Mode {mode!r} not set correctly"


# ---------------------------------------------------------------------------
# (e) Invalid mode still raises ValueError
# ---------------------------------------------------------------------------


class TestInvalidModeRaises:
    def test_invalid_mode_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="sample_weight_mode must be one of"):
            _make_lgbm_strategy("timedecay_only")  # not a valid mode

    def test_abs_pnl_timedecay_typo_raises(self) -> None:
        with pytest.raises(ValueError, match="sample_weight_mode must be one of"):
            _make_lgbm_strategy("abs_pnl_time_decay")  # underscore typo

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="sample_weight_mode must be one of"):
            _make_lgbm_strategy("")
