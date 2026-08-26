from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5 import statistics as stats

SCIPY = pytest.importorskip("scipy.stats", reason="dev-only cross-check")


def _returns(sharpe_annualised: float, periods: int = 900, seed: int = 3) -> np.ndarray:
    """Daily returns with a known true annualised Sharpe."""

    generator = np.random.default_rng(seed)
    daily = sharpe_annualised / math.sqrt(stats.TRADING_DAYS_PER_YEAR)
    return generator.normal(daily * 0.01, 0.01, size=periods)


# -- the scipy-free normal functions ---------------------------------------------------------


@pytest.mark.parametrize("value", [-4.0, -1.5, -0.3, 0.0, 0.3, 1.5, 4.0])
def test_normal_cdf_matches_scipy(value: float) -> None:
    assert stats.normal_cdf(value) == pytest.approx(SCIPY.norm.cdf(value), abs=1e-12)


@pytest.mark.parametrize("probability", [1e-6, 0.001, 0.02, 0.1, 0.5, 0.9, 0.99, 1 - 1e-6])
def test_normal_quantile_matches_scipy(probability: float) -> None:
    # Acklam's bound is on RELATIVE error; absolute error therefore grows in the tails.
    assert stats.normal_quantile(probability) == pytest.approx(
        SCIPY.norm.ppf(probability), rel=1.2e-9, abs=1e-12
    )


def test_normal_quantile_rejects_degenerate_probabilities() -> None:
    for probability in (0.0, 1.0, -0.1, 1.1):
        with pytest.raises(stats.StatisticsError):
            stats.normal_quantile(probability)


# -- Sharpe and PSR --------------------------------------------------------------------------


def test_sharpe_annualisation_is_the_square_root_of_the_period_count() -> None:
    values = _returns(1.0)
    ratio = stats.sharpe_ratio(values)
    assert stats.sharpe_ratio(values, annualised=True) == pytest.approx(ratio * math.sqrt(365.0))


def test_a_constant_series_has_no_sharpe_rather_than_an_infinite_one() -> None:
    assert stats.sharpe_ratio(np.full(100, 0.001)) == 0.0


def test_psr_rises_with_evidence() -> None:
    weak = stats.probabilistic_sharpe_ratio(_returns(1.0, periods=60))
    strong = stats.probabilistic_sharpe_ratio(_returns(1.0, periods=1500))
    assert 0.0 < weak < strong < 1.0


def test_psr_accounts_for_a_fat_left_tail() -> None:
    """Skew and kurtosis are load-bearing here, not a refinement.

    Measured trial moments in the V4-R9 field ran from (0.91, 17.8) to (-36.9, 1396). A Gaussian
    Sharpe test on that is far too confident about a positive mean.
    """

    generator = np.random.default_rng(5)
    benign = generator.normal(0.0008, 0.01, size=900)
    skewed = benign.copy()
    skewed[::90] -= 0.09  # rare, large losses; same mean-ish, much worse tail

    assert stats.probabilistic_sharpe_ratio(skewed) < stats.probabilistic_sharpe_ratio(benign)


def test_a_constant_series_yields_no_evidence_either_way() -> None:
    """Zero Sharpe against a zero benchmark is exactly one coin flip of evidence."""

    assert stats.probabilistic_sharpe_ratio(np.full(200, 0.001)) == pytest.approx(0.5)


def test_psr_requires_enough_observations_to_say_anything() -> None:
    with pytest.raises(stats.StatisticsError, match="at least two finite observations"):
        stats.probabilistic_sharpe_ratio(np.array([0.01]))


# -- the deflation benchmark -----------------------------------------------------------------


def test_a_wider_search_raises_the_bar() -> None:
    narrow = stats.expected_maximum_sharpe(8, 0.25)
    wide = stats.expected_maximum_sharpe(64, 0.25)
    assert 0.0 < narrow < wide


def test_a_tighter_cluster_of_trials_lowers_the_bar() -> None:
    """The benchmark scales with a team's own dispersion: spraying costs you."""

    tight = stats.expected_maximum_sharpe(12, 0.05)
    sprayed = stats.expected_maximum_sharpe(12, 0.60)
    assert tight < sprayed


def test_a_single_trial_is_not_deflated() -> None:
    """The sealed blocks are where the gate lives precisely because N is one there."""

    assert stats.expected_maximum_sharpe(1, 0.5) == 0.0


def test_the_v4_field_dispersion_reproduces_the_documented_hurdle() -> None:
    """Guards the arithmetic behind the decision not to gate DSR on development.

    The V4-R9 field's within-team trial-Sharpe dispersion was ~0.768, and 12 trials at that
    dispersion imply a hurdle around 1.25 annualised -- against a field maximum of 1.416.
    """

    variance = stats.annualised_to_period_variance(0.768)
    hurdle = stats.expected_maximum_sharpe(12, variance) * math.sqrt(365.0)
    assert 1.0 < hurdle < 1.6, hurdle
    # And the field's best trial did not clear it, which is why DSR is reported on development
    # rather than gated there.
    assert hurdle > 1.416 * 0.85


def test_deflated_sharpe_prefers_the_less_searched_of_two_identical_results() -> None:
    values = _returns(1.6)
    lightly = stats.deflated_sharpe_ratio(values, trial_count=4, trial_sharpe_variance=0.02)
    heavily = stats.deflated_sharpe_ratio(values, trial_count=200, trial_sharpe_variance=0.02)
    assert lightly.probability > heavily.probability
    assert lightly.observed_sharpe == heavily.observed_sharpe


def test_deflated_sharpe_reports_its_inputs_for_the_record() -> None:
    result = stats.deflated_sharpe_ratio(_returns(1.2), trial_count=12, trial_sharpe_variance=0.3)
    payload = result.as_dict()
    for key in (
        "observed_sharpe_annualised",
        "benchmark_sharpe_annualised",
        "probability",
        "trial_count",
        "trial_sharpe_variance",
        "observations",
        "skewness",
        "kurtosis",
    ):
        assert key in payload
    assert 0.0 <= result.probability <= 1.0


# -- bootstrap -------------------------------------------------------------------------------


def test_the_bootstrap_is_deterministic_given_its_seed() -> None:
    values = _returns(1.0)
    first = stats.bootstrap_probability_positive_mean(values, seed=7)
    second = stats.bootstrap_probability_positive_mean(values, seed=7)
    assert first == second


def test_the_bootstrap_separates_a_real_edge_from_noise() -> None:
    assert stats.bootstrap_probability_positive_mean(_returns(2.0)) > 0.9
    assert 0.2 < stats.bootstrap_probability_positive_mean(_returns(0.0, seed=9)) < 0.8


def test_the_default_resample_count_can_express_the_thresholds_it_is_compared_against() -> None:
    """2,000 resamples quantise to 5e-4, which is what made V4-R2's adjusted floor
    unrepresentable rather than merely strict."""

    values = _returns(1.0)
    indices = stats.stationary_bootstrap_indices(
        values.size, samples=20_000, expected_block=10.0, seed=1
    )
    assert indices.shape == (20_000, values.size)
    assert 1.0 / 20_000 < 6.7e-3, "resolution must be finer than the smallest BH alpha in use"


def test_bootstrap_blocks_preserve_serial_structure() -> None:
    """Independent resampling would understate the variance of an autocorrelated series."""

    indices = stats.stationary_bootstrap_indices(500, samples=200, expected_block=20.0, seed=2)
    consecutive = (np.diff(indices, axis=1) == 1).mean()
    assert consecutive > 0.8


def test_bootstrap_rejects_a_degenerate_request() -> None:
    with pytest.raises(stats.StatisticsError):
        stats.stationary_bootstrap_indices(100, samples=10, expected_block=5.0, seed=1)
    with pytest.raises(stats.StatisticsError):
        stats.stationary_bootstrap_indices(100, samples=200, expected_block=0.0, seed=1)


# -- field multiplicity ----------------------------------------------------------------------


def test_benjamini_hochberg_is_less_punitive_than_family_wise_control() -> None:
    """The concrete reason V5 controls FDR: at fifteen nominees, Bonferroni allows 13 negative
    resamples in 20,000 for every candidate, while BH allows 13 for the best and 66 for the
    fifth. Under the old 180-trial scheme it was one."""

    p_values = {f"team-{index:02d}": 0.02 for index in range(1, 16)}
    p_values["team-01"] = 0.001
    outcome = stats.benjamini_hochberg(p_values, q=0.10)
    assert outcome["team-01"]
    bonferroni = 0.10 / 15
    assert p_values["team-05"] > bonferroni, "the fixture must exercise the difference"


def test_benjamini_hochberg_admits_a_run_of_strong_lanes() -> None:
    p_values = {f"team-{index:02d}": value for index, value in enumerate([0.001, 0.004, 0.008], 1)}
    outcome = stats.benjamini_hochberg(p_values, q=0.10)
    assert all(outcome.values())


def test_benjamini_hochberg_rejects_a_field_of_noise() -> None:
    p_values = {f"team-{index:02d}": 0.6 for index in range(1, 16)}
    assert not any(stats.benjamini_hochberg(p_values, q=0.10).values())


def test_benjamini_hochberg_handles_an_empty_field() -> None:
    """An empty field is a supported terminal state, not an error."""

    assert stats.benjamini_hochberg({}, q=0.10) == {}


def test_benjamini_hochberg_step_up_admits_below_a_gap() -> None:
    """Step-up, not step-down: a lane below the largest passing rank is admitted even if its own
    p-value exceeds its own threshold."""

    p_values = {"a": 0.001, "b": 0.09, "c": 0.02}
    outcome = stats.benjamini_hochberg(p_values, q=0.30)
    assert outcome == {"a": True, "b": True, "c": True}


def test_a_pandas_series_is_accepted_alongside_an_array() -> None:
    """Callers hand these functions evaluator output, which is always a Series."""

    values = _returns(1.0)
    series = pd.Series(values, index=pd.date_range("2021-01-01", periods=values.size, tz="UTC"))
    assert stats.sharpe_ratio(series) == pytest.approx(stats.sharpe_ratio(values))
    assert stats.probabilistic_sharpe_ratio(series) == pytest.approx(
        stats.probabilistic_sharpe_ratio(values)
    )


def test_non_finite_observations_are_dropped_rather_than_poisoning_the_statistic() -> None:
    values = _returns(1.0)
    polluted = pd.Series(values).copy()
    polluted.iloc[10] = np.nan
    clean = pd.Series(values).drop(index=10)
    assert stats.sharpe_ratio(polluted) == pytest.approx(stats.sharpe_ratio(clean))
