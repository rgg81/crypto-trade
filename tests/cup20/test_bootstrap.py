"""Tests for the CUP-20 circular block bootstrap and trial-adjusted confidence."""

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.bootstrap import (
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)


def _daily(values):
    index = pd.date_range("2021-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(np.asarray(values, dtype=float), index=index)


# --- brief Step 1, verbatim -------------------------------------------------


def test_strongly_positive_series_gives_fraction_one():
    assert circular_block_bootstrap_positive_fraction(_daily([0.01] * 400)) == 1.0


def test_strongly_negative_series_gives_fraction_zero():
    assert circular_block_bootstrap_positive_fraction(_daily([-0.01] * 400)) == 0.0


def test_bootstrap_is_deterministic_for_a_fixed_seed():
    rng = np.random.default_rng(9)
    series = _daily(rng.normal(0.0005, 0.01, 500))
    first = circular_block_bootstrap_positive_fraction(series, seed=123)
    second = circular_block_bootstrap_positive_fraction(series, seed=123)
    assert first == second


def test_different_seeds_are_permitted_to_differ():
    rng = np.random.default_rng(4)
    series = _daily(rng.normal(0.0002, 0.02, 500))
    values = {
        circular_block_bootstrap_positive_fraction(series, seed=seed) for seed in (1, 2, 3, 4, 5)
    }
    assert len(values) >= 1


def test_short_series_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 5), block_days=10)


def test_trial_adjustment_penalises_multiplicity():
    assert trial_adjusted_confidence(1.0, 12) == 1.0
    assert trial_adjusted_confidence(0.99, 12) == pytest.approx(0.88)
    assert trial_adjusted_confidence(0.95, 12) == pytest.approx(0.40)
    assert trial_adjusted_confidence(0.90, 12) == 0.0
    assert trial_adjusted_confidence(0.99, 1) == pytest.approx(0.99)


def test_trial_adjustment_rejects_bad_inputs():
    with pytest.raises(ValueError):
        trial_adjusted_confidence(1.2, 3)
    with pytest.raises(ValueError):
        trial_adjusted_confidence(0.9, 0)


# --- additional coverage: raise paths and branches the brief's tests miss --
#
# Called out explicitly in the task instructions: the short-series rejection
# is covered above, but non-finite rejection, invalid samples/block_days, and
# the full range of both trial_adjusted_confidence validations are not.


def test_zero_samples_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 400), samples=0)


def test_negative_samples_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 400), samples=-1)


def test_zero_block_days_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 400), block_days=0)


def test_negative_block_days_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 400), block_days=-1)


def test_positive_infinity_is_rejected():
    values = [0.01] * 30
    values[10] = float("inf")
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily(values))


def test_negative_infinity_is_rejected():
    values = [0.01] * 30
    values[10] = float("-inf")
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily(values))


def test_nan_values_are_dropped_before_the_length_and_finiteness_checks():
    # daily.dropna() runs first, so NaN observations are silently removed
    # rather than tripping the non-finite rejection -- a real behavioural
    # branch (not a raise path) worth pinning explicitly. The series is only
    # long enough once the leading NaNs are dropped (400 remain of 500).
    values = [np.nan] * 100 + [0.01] * 400
    result = circular_block_bootstrap_positive_fraction(_daily(values))
    assert result == 1.0


def test_series_exactly_at_the_minimum_length_is_accepted():
    # block_days * 2 is the shortest length that does NOT raise.
    series = _daily([0.01] * 20)
    result = circular_block_bootstrap_positive_fraction(series, block_days=10)
    assert result == 1.0


def test_series_one_below_the_minimum_length_is_rejected():
    series = _daily([0.01] * 19)
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(series, block_days=10)


def test_block_days_not_a_divisor_of_series_length_still_returns_a_valid_fraction():
    # length=23 is not a multiple of block_days=3 (blocks=ceil(23/3)=8,
    # 8*3=24 != 23), exercising the reshape-then-truncate path that trims
    # the one extra flattened observation back down to exactly `length`.
    series = _daily([0.01] * 23)
    result = circular_block_bootstrap_positive_fraction(series, block_days=3, samples=50)
    assert result == 1.0


def test_bootstrap_is_deterministic_with_the_default_seed():
    # The frozen policy calls this with no seed override at all -- confirm
    # the documented default (seed=20260804) reproduces bit-for-bit, not
    # just the explicit-seed case the brief already covers.
    rng = np.random.default_rng(7)
    series = _daily(rng.normal(0.0003, 0.01, 300))
    first = circular_block_bootstrap_positive_fraction(series)
    second = circular_block_bootstrap_positive_fraction(series)
    assert first == second


def test_trial_adjustment_matches_hand_derived_values_at_several_trial_counts():
    # trial_adjusted_confidence = clamp(1 - trial_count * (1 - positive_fraction), 0, 1)
    assert trial_adjusted_confidence(1.0, 5) == 1.0
    assert trial_adjusted_confidence(0.98, 5) == pytest.approx(0.9)
    assert trial_adjusted_confidence(0.995, 20) == pytest.approx(0.9)
    assert trial_adjusted_confidence(0.9, 3) == pytest.approx(0.7)
    assert trial_adjusted_confidence(0.5, 1) == pytest.approx(0.5)
    assert trial_adjusted_confidence(0.5, 100) == 0.0


def test_trial_adjustment_accepts_the_boundary_fractions():
    assert trial_adjusted_confidence(0.0, 1) == 0.0
    assert trial_adjusted_confidence(1.0, 1) == 1.0


def test_trial_adjustment_rejects_a_negative_positive_fraction():
    with pytest.raises(ValueError):
        trial_adjusted_confidence(-0.1, 3)


def test_trial_adjustment_rejects_a_negative_trial_count():
    with pytest.raises(ValueError):
        trial_adjusted_confidence(0.9, -1)
