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
    # Strengthened in fix round 1: `len(values) >= 1` is vacuously true for
    # any implementation that returns a float at all, including one that
    # ignores `seed` entirely. `>= 2` is a real seed-sensitivity assertion --
    # verified non-flaky for this exact fixture: seeds 1-5 give five
    # distinct fractions (0.5935-0.6320), deterministically, every run.
    rng = np.random.default_rng(4)
    series = _daily(rng.normal(0.0002, 0.02, 500))
    values = {
        circular_block_bootstrap_positive_fraction(series, seed=seed) for seed in (1, 2, 3, 4, 5)
    }
    assert len(values) >= 2


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


def test_nan_values_are_rejected():
    # Fix round 1, Finding 1: there is no .dropna() any more. A NaN-bearing
    # series must raise the same "non-finite values" error as inf, not be
    # silently trimmed to a shorter, temporally-spliced series.
    values = [0.01] * 400
    values[100] = float("nan")
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily(values))


def test_series_exactly_at_the_minimum_length_is_accepted():
    # block_days * 2 is the shortest length that does NOT raise.
    series = _daily([0.01] * 20)
    result = circular_block_bootstrap_positive_fraction(series, block_days=10)
    assert result == 1.0


def test_series_one_below_the_minimum_length_is_rejected():
    series = _daily([0.01] * 19)
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(series, block_days=10)


def _reference_block_bootstrap_positive_fraction(values, samples, block_days, seed):
    """Deliberately non-vectorized reimplementation of the same documented
    contract as circular_block_bootstrap_positive_fraction (ceil block
    count, each block wraps circularly modulo length, blocks concatenate
    then truncate back to exactly `length` observations) -- via explicit
    loops and a floor-division ceiling trick instead of the production
    reshape/broadcast, so it is a structurally different code path, not a
    copy. Used only to cross-check the production index arithmetic in
    test_index_arithmetic_matches_an_independent_reference_implementation.
    """
    length = len(values)
    blocks = -(-length // block_days)  # ceiling division without np.ceil
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, length, size=(samples, blocks))
    positive = 0
    for sample_starts in starts:
        drawn = [
            values[(start + offset) % length]
            for start in sample_starts
            for offset in range(block_days)
        ][:length]
        assert len(drawn) == length, "reference must average exactly `length` observations"
        if np.array(drawn).mean() > 0.0:
            positive += 1
    return positive / samples


def test_index_arithmetic_matches_an_independent_reference_implementation():
    # Fix round 1, Finding 3: the brief's all-0.01 fixture proved nothing
    # about the reshape/truncate/wrap arithmetic, since any subset or
    # superset of identical values averages the same. This fixture uses a
    # non-constant, index-distinguishable series (alternating sign, distinct
    # magnitude per index) so that a wrong block count, wrong truncation
    # side, or a forgotten circular wrap selects genuinely different values
    # and changes the result -- empirically confirmed against three
    # plausible bugs (floor-instead-of-ceil block count: shape mismatch;
    # truncate-from-the-end instead of the start: 0.695 vs 0.705;
    # no modulo wrap: 0.48 vs 0.705) before this test was written.
    length, block_days, samples, seed = 23, 4, 200, 2026
    values = np.array([(-1.0) ** i * (i + 1) for i in range(length)])
    series = _daily(values)

    expected = _reference_block_bootstrap_positive_fraction(values, samples, block_days, seed)
    result = circular_block_bootstrap_positive_fraction(
        series, samples=samples, block_days=block_days, seed=seed
    )
    assert result == expected


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


def test_trial_adjustment_rejects_a_nan_trial_count():
    # Fix round 1, Finding 4: `trial_count < 1` did not reject NaN (`nan < 1`
    # is False), so a garbage trial count used to propagate through to
    # `min(1.0, nan) == 1.0` -- the *most* favourable confidence a module
    # whose entire job is to penalise could return. The fixed check
    # (`not trial_count >= 1`) closes this the same way positive_fraction's
    # chained comparison already did.
    with pytest.raises(ValueError):
        trial_adjusted_confidence(0.9, float("nan"))


def test_trial_adjustment_rejects_a_nan_positive_fraction():
    # Regression pin for the accidental-but-correct half of the same bug
    # class: `not 0.0 <= positive_fraction <= 1.0` already rejects NaN
    # today (the chained comparison is False for NaN, so `not False` is
    # True), but that was untested before this fix round.
    with pytest.raises(ValueError):
        trial_adjusted_confidence(float("nan"), 3)
