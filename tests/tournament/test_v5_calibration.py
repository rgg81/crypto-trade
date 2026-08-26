"""The bar must be measured before it can be activated.

V4-R2 shipped a field-adjusted floor no candidate could reach: the best of ninety-four measured
trials scored 0.01 against a 0.90 requirement. The consequence was not a strict tournament but a
bypassed one -- the bracket was filled from a fallback that ranked on worst-fold Sharpe and so
preferred a book that barely traded. Nobody had measured what the gate did.

These tests fix the operating characteristic of the V5 bar in place, including the parts that are
unflattering. They run on development-derived synthetic paths only and read no sealed or holdout
row, so everything here can be committed before either is opened.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from crypto_trade.tournament.v5 import calibration as cal
from crypto_trade.tournament.v5 import gates
from crypto_trade.tournament.v5 import statistics as stats

# The sealed budget is 360 days. The bar has to be characterised on the evidence it will actually
# see, not on a comfortable length.
SEALED_PERIODS = 360

THRESHOLDS = dataclasses.replace(
    gates.GateThresholds(
        minimum_mean_gross_exposure=0.30,
        minimum_median_effective_breadth=6.0,
        minimum_breadth_pass_fraction=0.80,
        minimum_active_bar_fraction=0.80,
        minimum_side_exposure_share=0.20,
        volatility_band=(0.06, 0.15),
        maximum_risk_unit_capped_fraction=0.50,
        minimum_annualised_turnover=4.0,
        maximum_annualised_turnover=90.0,
        minimum_gross_edge_bps_per_turnover=20.0,
        maximum_cost_share_of_positive_gross=0.50,
        minimum_positive_fold_fraction=0.60,
        minimum_deflated_sharpe_probability=0.60,
        maximum_vol_normalised_drawdown=0.25,
        maximum_top_symbol_gross_pnl_share=0.40,
        minimum_deletion_profile_p05_sharpe=0.0,
        minimum_accepted_trials=8,
    )
)


@pytest.fixture(scope="module", name="report")
def _report() -> cal.CalibrationReport:
    return cal.calibrate(THRESHOLDS, null_count=100, per_level=40, periods=SEALED_PERIODS, seed=99)


# -- the measurements the charter has to publish ---------------------------------------------


def test_a_book_that_is_not_a_portfolio_never_clears_the_bar(
    report: cal.CalibrationReport,
) -> None:
    """Degeneracy is the one thing a 360-day window resolves cleanly."""

    assert report.degenerate_pass_rate == 0.0


def test_every_degenerate_archetype_is_rejected_individually() -> None:
    """Each is drawn from something a prior edition actually produced, not invented."""

    for name, evidence in cal.build_degenerate_population():
        assessment = gates.assess(evidence, THRESHOLDS, stage=gates.SEALED_STAGE)
        assert not assessment.eligible, f"{name} cleared the bar"


def test_the_bar_is_passable_by_a_strategy_worth_deploying(
    report: cal.CalibrationReport,
) -> None:
    """The failure V4-R2 shipped was a bar nothing could pass. This is the guard against it."""

    assert report.power_at(2.0) >= 0.60


def test_the_bar_is_not_a_formality(report: cal.CalibrationReport) -> None:
    assert report.null_pass_rate < 0.50
    assert report.power_at(2.0) > report.null_pass_rate


def test_power_rises_monotonically_with_true_edge(report: cal.CalibrationReport) -> None:
    levels = sorted(report.power_by_sharpe)
    powers = [report.power_at(level) for level in levels]
    assert powers == sorted(powers), dict(zip(levels, powers, strict=True))


def test_the_sealed_stage_is_a_usable_screen_but_not_a_certification(
    report: cal.CalibrationReport,
) -> None:
    """What the stage can and cannot do, measured.

    It lets most genuinely good books through, which is what a funnel into the 2.5-year window
    needs. It does not certify: roughly a third of edgeless books also pass, because at 360 days
    the standard error of an annualised Sharpe is about 1.0 and no threshold separates a real
    Sharpe of 1.0 from luck at that width.

    An earlier version of this file asserted the opposite -- that power at 1.0 was necessarily
    below 0.60. That was a consequence of a design error (deflating the sealed estimate by the
    team's full trial count, double-charging a search that happened on other data), not of the
    window. Removing the double count took power from 0.24 to 0.70.
    """

    assert report.power_at(1.0) >= 0.60
    assert 0.15 < report.null_pass_rate < 0.50


def test_the_deflation_benchmark_exceeds_a_sharpe_of_one_at_field_dispersion() -> None:
    """The arithmetic behind the test above, stated so it cannot drift unnoticed."""

    benchmark = stats.expected_maximum_sharpe(
        12, stats.annualised_to_period_variance(0.768)
    ) * math.sqrt(stats.TRADING_DAYS_PER_YEAR)
    assert benchmark > 1.0


def test_a_narrower_search_faces_a_lower_bar_on_development() -> None:
    """Deflation prices the search that produced the claim, so discipline is rewarded.

    This is a statement about the *development* report, where the nominee was selected from the
    same data. On the sealed blocks the trial count is one and dispersion is irrelevant, which is
    the whole point of holding them out.
    """

    wide = cal.calibrate(
        THRESHOLDS,
        null_count=60,
        per_level=25,
        periods=SEALED_PERIODS,
        seed=5,
        trial_count=12,
        dispersion=0.768,
    )
    narrow = cal.calibrate(
        THRESHOLDS,
        null_count=60,
        per_level=25,
        periods=SEALED_PERIODS,
        seed=5,
        trial_count=12,
        dispersion=0.30,
    )
    assert narrow.power_at(1.5) > wide.power_at(1.5)
    assert narrow.null_pass_rate > wide.null_pass_rate


def test_dispersion_is_irrelevant_once_the_data_is_held_out() -> None:
    """At a trial count of one the benchmark is zero however widely the team searched."""

    assert stats.expected_maximum_sharpe(1, stats.annualised_to_period_variance(0.768)) == 0.0
    assert stats.expected_maximum_sharpe(1, stats.annualised_to_period_variance(0.20)) == 0.0


# -- the activation gate ---------------------------------------------------------------------


def test_activation_accepts_a_measured_usable_bar(report: cal.CalibrationReport) -> None:
    cal.assert_bar_is_usable(report, maximum_null_pass_rate=0.45, minimum_power_at={2.0: 0.60})


def test_activation_refuses_a_bar_no_plausible_strategy_can_pass() -> None:
    """The V4-R2 failure, made unshippable."""

    impossible = dataclasses.replace(THRESHOLDS, minimum_deflated_sharpe_probability=0.999999)
    report = cal.calibrate(impossible, null_count=40, per_level=20, periods=SEALED_PERIODS)
    with pytest.raises(cal.CalibrationError, match="cannot be passed by a plausible strategy"):
        cal.assert_bar_is_usable(report, maximum_null_pass_rate=0.45, minimum_power_at={2.0: 0.60})


def test_activation_refuses_a_bar_a_null_population_walks_through() -> None:
    """The opposite failure is just as disqualifying.

    Note the permissive fixture cannot exceed a null pass rate of about 0.40 however far the
    performance thresholds are relaxed: survives_triple_cost compares against zero and has no
    threshold to loosen, so a book that cannot pay triple costs is rejected regardless. The
    activation requirement is therefore set below that, which is what makes this fixture bite
    rather than pass vacuously.
    """

    permissive = dataclasses.replace(
        THRESHOLDS,
        minimum_deflated_sharpe_probability=0.0,
        minimum_positive_fold_fraction=0.0,
        minimum_deletion_profile_p05_sharpe=-99.0,
        maximum_vol_normalised_drawdown=99.0,
    )
    report = cal.calibrate(permissive, null_count=60, per_level=20, periods=SEALED_PERIODS)
    assert report.null_pass_rate > 0.25, "the fixture must actually admit nulls"
    with pytest.raises(cal.CalibrationError, match="null pass rate"):
        cal.assert_bar_is_usable(report, maximum_null_pass_rate=0.25, minimum_power_at={2.0: 0.60})


def test_activation_refuses_a_bar_that_admits_a_degenerate_book() -> None:
    toothless = dataclasses.replace(
        THRESHOLDS,
        minimum_mean_gross_exposure=0.0,
        minimum_median_effective_breadth=0.0,
        minimum_breadth_pass_fraction=0.0,
        minimum_active_bar_fraction=0.0,
        minimum_side_exposure_share=0.0,
        maximum_annualised_turnover=1e6,
        minimum_gross_edge_bps_per_turnover=-1e6,
        minimum_deflated_sharpe_probability=0.0,
        minimum_positive_fold_fraction=0.0,
        minimum_deletion_profile_p05_sharpe=-99.0,
        maximum_vol_normalised_drawdown=99.0,
        maximum_top_symbol_gross_pnl_share=1.0,
        maximum_cost_share_of_positive_gross=1e6,
        minimum_accepted_trials=0,
        volatility_band=(0.0, 99.0),
        maximum_risk_unit_capped_fraction=1.0,
    )
    report = cal.calibrate(toothless, null_count=20, per_level=10, periods=SEALED_PERIODS)
    with pytest.raises(cal.CalibrationError, match="degenerate books"):
        cal.assert_bar_is_usable(report, maximum_null_pass_rate=0.99, minimum_power_at={2.0: 0.0})


# -- the machinery --------------------------------------------------------------------------


def test_statistical_evidence_is_computed_rather_than_declared() -> None:
    """A fixture that hand-sets its own DSR would calibrate nothing."""

    strong = cal.evidence_from_returns(
        cal._path(3.0, periods=SEALED_PERIODS, seed=1), trial_count=12, trial_sharpe_dispersion=0.3
    )
    weak = cal.evidence_from_returns(
        cal._path(0.0, periods=SEALED_PERIODS, seed=1), trial_count=12, trial_sharpe_dispersion=0.3
    )
    assert strong.deflated_sharpe_probability > weak.deflated_sharpe_probability
    assert strong.deletion_profile_p05_sharpe > weak.deletion_profile_p05_sharpe


def test_the_lottery_search_is_harder_to_reject_than_a_single_null_draw() -> None:
    """The population the correction exists to catch: a team that searched until it looked good."""

    generator = np.random.default_rng(3)
    single = [
        cal._path(0.0, periods=SEALED_PERIODS, seed=int(generator.integers(1 << 31)))
        for _ in range(40)
    ]
    best_of_twelve = []
    for _ in range(40):
        attempts = [
            cal._path(0.0, periods=SEALED_PERIODS, seed=int(generator.integers(1 << 31)))
            for _ in range(12)
        ]
        best_of_twelve.append(max(attempts, key=stats.sharpe_ratio))

    assert np.mean([stats.sharpe_ratio(p, annualised=True) for p in best_of_twelve]) > np.mean(
        [stats.sharpe_ratio(p, annualised=True) for p in single]
    )


def test_the_deletion_profile_sees_deletions_the_calendar_version_cannot() -> None:
    """Calendar-aligned deletions are a strict subset of all contiguous ones, so the calendar
    version cannot find the worst window unless it happens to start on a month boundary.

    Measured on the V4-R9 holdout, the winner's best-month-removed Sharpe was 0.674 while its
    worst contiguous 30-day deletion gave 0.600.
    """

    returns = cal._path(1.5, periods=SEALED_PERIODS, seed=11)
    every = [
        stats.sharpe_ratio(np.delete(returns, slice(start, start + 30)), annualised=True)
        for start in range(returns.size - 30)
    ]
    calendar = [
        stats.sharpe_ratio(np.delete(returns, slice(start, start + 30)), annualised=True)
        for start in range(0, returns.size - 30, 30)
    ]
    assert min(every) <= min(calendar) + 1e-12


def test_the_profile_declines_to_take_the_extreme() -> None:
    """The percentile is deliberately not the minimum.

    Over ~330 overlapping windows the minimum is an extreme-value statistic of a highly dependent
    sample, and selecting on it would rank which candidate happened to contain the unluckiest
    thirty days rather than which is fragile. The fifth percentile sits strictly above it.

    Note this is a choice about what to select on, not a claim that the percentile is measurably
    more stable across paths -- measured over a dozen equivalent paths the two vary about equally,
    because path-level Sharpe variation dominates both.
    """

    for seed in range(20, 28):
        path = cal._path(1.5, periods=SEALED_PERIODS, seed=seed)
        deletions = [
            stats.sharpe_ratio(np.delete(path, slice(start, start + 30)), annualised=True)
            for start in range(path.size - 30)
        ]
        assert cal.deletion_profile_p05(path) > min(deletions)


def test_a_series_too_short_for_a_deletion_profile_is_refused() -> None:
    with pytest.raises(cal.CalibrationError, match="too short"):
        cal.deletion_profile_p05(np.zeros(10))


def test_an_empty_population_cannot_produce_a_pass_rate() -> None:
    """'No candidates passed' and 'no candidates were measured' are different claims."""

    with pytest.raises(cal.CalibrationError, match="empty population"):
        cal._pass_rate([], THRESHOLDS, gates.SEALED_STAGE)


def test_the_report_serialises_its_thresholds_with_its_measurements(
    report: cal.CalibrationReport,
) -> None:
    """A published operating characteristic is only meaningful beside the bar it measured."""

    payload = report.as_dict()
    assert payload["schema_version"] == "top40-v5-calibration-v1"
    assert payload["thresholds"]["minimum_deflated_sharpe_probability"] == pytest.approx(0.60)
    assert set(payload["power_by_sharpe"]) == {"0.5", "1.0", "1.5", "2.0"}


def test_calibration_is_deterministic_given_its_seed() -> None:
    first = cal.calibrate(THRESHOLDS, null_count=20, per_level=10, periods=SEALED_PERIODS, seed=4)
    second = cal.calibrate(THRESHOLDS, null_count=20, per_level=10, periods=SEALED_PERIODS, seed=4)
    assert first.as_dict() == second.as_dict()


# -- where the search penalty belongs ----------------------------------------------------------


def test_the_sealed_stage_does_not_charge_the_search_twice() -> None:
    """A team selected its nominee on visible data the sealed blocks never saw.

    Holding those blocks out is already the correction. Deflating the sealed estimate again by the
    team's twelve-trial benchmark charges the same search a second time, and the cost is most of
    the stage's power.
    """

    once = cal.calibrate(
        THRESHOLDS, null_count=100, per_level=50, periods=SEALED_PERIODS, seed=99, trial_count=1
    )
    twice = cal.calibrate(
        THRESHOLDS, null_count=100, per_level=50, periods=SEALED_PERIODS, seed=99, trial_count=12
    )
    assert once.power_at(1.0) > 2 * twice.power_at(1.0)
    # And it buys almost nothing in exchange.
    assert twice.null_pass_rate < once.null_pass_rate + 0.10


def test_the_calibration_default_is_the_sealed_multiplicity() -> None:
    """A default of twelve would silently reinstate the double count."""

    import inspect

    default = inspect.signature(cal.calibrate).parameters["trial_count"].default
    assert default == gates.SEALED_TRIAL_COUNT == 1


def test_the_screened_stage_passes_a_usable_fraction_of_real_teams(
    report: cal.CalibrationReport,
) -> None:
    """The sealed stage is a funnel into the 2.5-year window, not the decision itself.

    It has to let genuinely good books through at a workable rate; the ranking happens later,
    where the standard error is 0.63 rather than 1.0.
    """

    assert report.power_at(1.0) >= 0.60
    assert report.power_at(1.5) >= 0.75


def test_field_wide_correction_would_empty_the_bracket() -> None:
    """Why field multiplicity is reported rather than gated.

    At 360 days a true Sharpe of 1.0 produces p-values around 0.15-0.30, while Benjamini-Hochberg
    at q=0.10 over fifteen nominees needs the best below 0.0067. Averaged over repeated fields
    containing five genuinely good teams it selects about half a team, so applying it here would
    repeat V4-R2's failure in a new form: a correct-looking correction no candidate can pass.

    Averaged deliberately -- a single draw is noisy enough to select three, which is exactly the
    kind of one-shot reading that would make this look fine.
    """

    selected_counts = []
    for trial in range(40):
        generator = np.random.default_rng(1000 + trial)
        p_values = {}
        for index in range(15):
            sealed = cal._path(
                1.0 if index < 5 else 0.0,
                periods=SEALED_PERIODS,
                seed=int(generator.integers(1 << 31)),
            )
            p_values[f"team-{index:02d}"] = 1.0 - stats.probabilistic_sharpe_ratio(sealed)
        selected_counts.append(sum(stats.benjamini_hochberg(p_values, q=0.10).values()))

    assert float(np.mean(selected_counts)) < 2.0, (
        "field-wide correction at this window length selects almost nobody, which is why the "
        "charter reports it beside the leaderboard instead of gating on it"
    )
