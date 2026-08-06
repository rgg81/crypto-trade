"""The section 4 caps applied by reduction, to the team's book as well as the organiser's.

Charter section 4 says the caps are **applied**, not enforced by rejection. Until now only half of
that was true: ``apply_exposure_caps`` reduced the book the common risk unit produced, but the
team's own normalised book went straight to ``evaluate_targets``, whose ``_validate_weight_limits``
RAISES. At ``max_symbol_exposure = 0.20`` that made an entire shape of strategy un-evaluable --
four equal names at unit gross is 0.25 each, so the run died at the first boundary, in pass 1,
before ``s_t`` existed at all.

This file proves the four shapes that used to crash now evaluate, that the cap still binds on every
one of them, that the reduction preserves the book's shape rather than reshuffling it, and that a
team can see it happened.

**Why the caps run at BOTH ends of the risk unit.** Capping only after ``s_t`` (what section 4 said)
cannot rescue a concentrated book, because pass 1 rejects it first. Capping only before ``s_t``
cannot hold, because ``s_t`` reaches 3.0. Both are asserted below rather than argued:
``test_capping_only_after_the_risk_unit_would_not_have_rescued_pass_one`` and
``test_capping_only_before_the_risk_unit_would_not_hold_the_executed_book``.

**Why the trimmed weight is not redistributed.** One uniform per-boundary scale means the executed
book is always a positive multiple of the requested one. Redistribution -- pushing the trimmed
0.05 onto the other names -- would RAISE a weight above what the team asked for and let a team
reach a shape it was not allowed to request, which is an evasion surface rather than a courtesy.
``test_capping_a_dominant_name_does_not_reshuffle_the_others`` is the test with teeth here: every
pairwise ratio survives, which per-symbol clipping would not manage.
"""

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.runner import (
    CAP_NAMES,
    STAGE_EXECUTED,
    STAGE_REQUESTED,
    ExposureCapTrim,
    apply_exposure_caps,
    apply_risk_scalars,
    decision_grid,
    exposure_cap_trim,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.tournament.engine_v2 import EvaluatorConfig, evaluate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from tests.cup20.test_runner import _snapshot

SYMBOLS = ("AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT")
START = pd.Timestamp("2021-01-01T00:00:00Z")

# The FROZEN CUP-20 per-symbol cap, deliberately -- unlike the 0.5 the other cup20 test modules use
# to keep three-symbol fixtures evaluable, this file's whole subject is what 0.20 does to a book
# that concentrates, so it must be the real number.
CAPS = EvaluatorConfig(
    interval_hours=8,
    initial_equity=100_000.0,
    taker_fee_bps_per_side=5.0,
    slippage_bps_per_side=2.5,
    max_gross_exposure=1.0,
    max_abs_net_exposure=1.0,
    max_symbol_exposure=0.20,
    max_bar_participation=0.001,
)
# lookback_days=10 rather than the frozen 90 so a 450-bar fixture actually exercises the scalar in
# both directions instead of sitting at 1.0 for its first 270 boundaries.
RISK_UNIT = {"target_annualized_volatility": 0.10, "lookback_days": 10}

SNAPSHOT = _snapshot(days=60, symbols=SYMBOLS)
GRID = decision_grid(SNAPSHOT.bars["open_time"].min(), SNAPSHOT.bars["open_time"].max())
WEIGHTS = list(SYMBOLS)


class FixedBook:
    """Ask for one fixed set of raw weights at every boundary."""

    def __init__(self, weights):
        self._weights = dict(weights)

    def target_weights(self, context, *, seed):
        eligible = set(context.eligible_symbols)
        return {s: w for s, w in self._weights.items() if s in eligible}


def _run(weights, *, config=CAPS):
    return run_candidate(
        FixedBook(weights),
        SNAPSHOT,
        decision_times=GRID,
        seed=42,
        config=config,
        risk_unit=RISK_UNIT,
    )


FOUR_NAME = "four-name equal weight"
TWO_NAME = "two-name long/short"
ONE_NAME = "single name"
DOMINANT = "one dominant name among small ones"

SHAPES = {
    FOUR_NAME: {"AUSDT": 1.0, "BUSDT": 1.0, "CUSDT": 1.0, "DUSDT": 1.0},
    TWO_NAME: {"AUSDT": 1.0, "BUSDT": -1.0},
    ONE_NAME: {"AUSDT": 1.0},
    DOMINANT: {
        "AUSDT": 0.90,
        "BUSDT": 0.04,
        "CUSDT": 0.03,
        "DUSDT": -0.02,
        "EUSDT": 0.01,
    },
}
# The reference book each shape must reduce to: one uniform scale = cap / largest requested leg.
EXPECTED_REFERENCE = {
    FOUR_NAME: {"AUSDT": 0.20, "BUSDT": 0.20, "CUSDT": 0.20, "DUSDT": 0.20, "EUSDT": 0.0},
    TWO_NAME: {"AUSDT": 0.20, "BUSDT": -0.20, "CUSDT": 0.0, "DUSDT": 0.0, "EUSDT": 0.0},
    ONE_NAME: {"AUSDT": 0.20, "BUSDT": 0.0, "CUSDT": 0.0, "DUSDT": 0.0, "EUSDT": 0.0},
    DOMINANT: {
        "AUSDT": 0.20,
        "BUSDT": 0.04 * 0.20 / 0.90,
        "CUSDT": 0.03 * 0.20 / 0.90,
        "DUSDT": -0.02 * 0.20 / 0.90,
        "EUSDT": 0.01 * 0.20 / 0.90,
    },
}
EXPECTED_SCALE = {FOUR_NAME: 0.80, TWO_NAME: 0.40, ONE_NAME: 0.20, DOMINANT: 0.20 / 0.90}

RUNS = {name: _run(weights) for name, weights in SHAPES.items()}
# The five-name book sits exactly ON the 0.20 cap and is this file's negative control.
UNTRIMMED_RUN = _run({symbol: 1.0 for symbol in SYMBOLS})


def _book(frame: pd.DataFrame) -> pd.DataFrame:
    """The weight columns, reindexed over the whole fixture universe.

    ``generate_targets`` only creates a column for a symbol the strategy actually named, so the
    four-name book has no ``EUSDT`` column at all. Filling the unnamed members with zero is what
    makes the four shapes comparable with each other and with ``EXPECTED_REFERENCE``.
    """
    return frame.reindex(columns=WEIGHTS, fill_value=0.0)


def _first(book: pd.DataFrame) -> pd.Series:
    return _book(book).loc[GRID[0]].astype(float)


# --- the premises, so nothing below is vacuous -------------------------------------------------


@pytest.mark.parametrize("shape", list(SHAPES))
def test_every_shape_here_really_does_breach_the_per_symbol_cap(shape):
    """Without this, every "it evaluated" assertion below would be about an un-capped book.

    Mutation this catches: a fixture edit that softens a shape until the cap no longer binds, which
    would leave the whole file passing while testing nothing.
    """
    requested = _first(RUNS[shape].requested_targets)
    assert requested.abs().max() > CAPS.max_symbol_exposure
    assert requested.abs().sum() == pytest.approx(1.0)


def test_the_five_name_control_does_not_breach_any_cap():
    """The other half of the premise: a diagnostic that reported a trim on every book would be as
    useless as one that never reported any. Five equal names is 0.20 each -- exactly at the cap and
    therefore not over it."""
    requested = _first(UNTRIMMED_RUN.requested_targets)
    assert requested.abs().max() == pytest.approx(CAPS.max_symbol_exposure)
    assert requested.abs().max() <= CAPS.max_symbol_exposure


# --- the shapes that used to crash now evaluate, and are executed at known weights --------------


@pytest.mark.parametrize("shape", list(SHAPES))
def test_a_concentrated_book_evaluates_at_every_cost_level(shape):
    """The regression. Before this change each of these raised ``symbol exposure ... exceeds cap``
    from ``_validate_weight_limits`` at the first boundary of pass 1.

    Deliberately NOT left as a bare "it did not crash": that proves almost nothing on its own, so
    the executed weights are asserted in
    ``test_the_executed_book_is_the_requested_shape_uniformly_reduced`` and the caps are asserted
    still to bind in ``test_the_caps_still_bind_on_every_shape``. This test's own contribution is
    that all three cost levels completed over the whole grid.
    """
    run = RUNS[shape]
    assert sorted(run.results) == [1, 2, 3]
    for multiplier in (1, 2, 3):
        returns = run.results[multiplier].returns
        assert len(returns) == len(GRID)
        assert returns.index[-1] == GRID[-1]


@pytest.mark.parametrize("shape", list(SHAPES))
def test_the_executed_book_is_the_requested_shape_uniformly_reduced(shape):
    """The weights, name by name, at a boundary where the risk unit is still 1.0.

    Mutation this catches: renormalising the trimmed book back to unit gross. A four-name book
    capped at 0.20 each must run at 0.80 gross, not be levered back to 1.0 -- redistribution would
    change which names the book is in and in what proportion, which is the strategy's expressed
    intent and not the organiser's to rewrite.
    """
    reference = _first(RUNS[shape].targets)
    expected = pd.Series(EXPECTED_REFERENCE[shape], dtype=float).reindex(WEIGHTS)
    pd.testing.assert_series_equal(reference, expected, check_names=False, atol=1e-15, rtol=0)
    # Reduced, never renormalised: gross lands BELOW 1.0 by exactly the reduction.
    assert reference.abs().sum() == pytest.approx(EXPECTED_SCALE[shape])


@pytest.mark.parametrize("shape", [*SHAPES, "five-name control"])
def test_the_caps_still_bind_on_every_shape(shape):
    """The cap must bind by reduction, not stop binding. Asserted on BOTH books -- the reference
    book pass 1 evaluates and the executed book pass 2 evaluates -- and at every boundary, not just
    the first, because ``s_t`` varies across the grid and reaches 3.0.

    Mutation this catches: applying the caps to only one of the two books (either one), which the
    other assertions in this file would not all detect on their own.
    """
    run = UNTRIMMED_RUN if shape == "five-name control" else RUNS[shape]
    for book in (run.targets, run.scaled_targets):
        weights = _book(book)
        assert (weights.abs().max(axis=1) <= CAPS.max_symbol_exposure + 1e-12).all()
        assert (weights.abs().sum(axis=1) <= CAPS.max_gross_exposure + 1e-12).all()
        assert (weights.sum(axis=1).abs() <= CAPS.max_abs_net_exposure + 1e-12).all()


def test_capping_a_dominant_name_does_not_reshuffle_the_others():
    """Uniform reduction preserves EVERY pairwise ratio, so ordering survives a fortiori.

    Mutation this catches: per-symbol clipping (clip each ``|w|`` to the cap and leave the rest
    alone). Clipping satisfies every cap assertion in this file and even preserves the ordering, so
    ordering alone would not detect it -- the ratio assertion is the one with teeth. Clipping is
    also the redistribution-shaped hazard: it changes the book's shape, so a team could reach a
    shape it was not allowed to request by asking for an over-cap leg it knew would be clipped.
    """
    run = RUNS[DOMINANT]
    requested = _first(run.requested_targets)
    reference = _first(run.targets)

    # The premise: exactly one leg breaches, so a clipping implementation would touch only that one.
    assert requested["AUSDT"] > CAPS.max_symbol_exposure
    assert (requested.drop("AUSDT").abs() < CAPS.max_symbol_exposure).all()

    ordered = list(requested.sort_values(ascending=False).index)
    assert list(reference.sort_values(ascending=False).index) == ordered
    ratios = (reference / requested).to_numpy(dtype=float)
    assert np.allclose(ratios, ratios[0], rtol=0, atol=1e-15)
    assert ratios[0] == pytest.approx(EXPECTED_SCALE[DOMINANT])


def test_a_book_asking_for_almost_everything_in_one_name_still_lands_exactly_at_the_cap():
    """The cap binds by reduction rather than by exception -- it is not a way to evade the caps.

    Mutation this catches: a cap that reduces toward the ceiling without reaching it, or one that
    only reduces the gross term and lets a single 0.90 leg through under a 1.0 gross cap.
    """
    run = RUNS[DOMINANT]
    for book in (run.targets, run.scaled_targets):
        largest = _book(book).abs().max(axis=1)
        assert largest.max() == pytest.approx(CAPS.max_symbol_exposure)
        assert (largest <= CAPS.max_symbol_exposure + 1e-12).all()


# --- why the caps run at both ends of the common risk unit --------------------------------------


def test_capping_only_after_the_risk_unit_would_not_have_rescued_pass_one():
    """Charter section 4's original "applied after the common risk unit" is necessary, not
    sufficient: pass 1 evaluates the team's own normalised book and REJECTS it, so a concentrated
    book never reaches the risk unit at all. Reproduced directly against the evaluator.
    """
    # Two boundaries, not one: the evaluator needs at least two bars inside the target span, and a
    # single-row frame fails on that instead of on the cap, which would make the raise unattributed.
    requested = normalise_unit_gross(
        pd.DataFrame(
            {name: [1.0, 1.0] for name in ("AUSDT", "BUSDT", "CUSDT", "DUSDT")}
            | {REBALANCE_INSTRUCTION_COLUMN: [True, True]},
            index=pd.DatetimeIndex([GRID[0], GRID[1]]),
        )
    )
    assert requested["AUSDT"].iloc[0] == pytest.approx(0.25)
    with pytest.raises(ValueError, match="symbol exposure"):
        evaluate_targets(
            SNAPSHOT.bars,
            SNAPSHOT.funding,
            SNAPSHOT.membership,
            requested,
            mark_prices=SNAPSHOT.mark_prices,
            config=CAPS,
            cost_multiplier=1.0,
        )


def test_capping_only_before_the_risk_unit_would_not_hold_the_executed_book():
    """The other direction: ``s_t = clamp(0.10 / sigma_t, 0.20, 3.0)`` reaches 3.0, so a book
    capped once, before the risk unit, is over the caps again after it.

    Asserted on this fixture's own scalars rather than in the abstract: ``s_t x`` the (already
    capped) reference book breaches the caps at real boundaries, and the executed book does not.
    """
    run = RUNS[FOUR_NAME]
    assert (run.risk_scalars > 1.0).any(), "fixture must reach a boundary where s_t levers up"
    uncapped_second_pass = _book(apply_risk_scalars(run.targets, run.risk_scalars))
    breaching = uncapped_second_pass.abs().max(axis=1) > CAPS.max_symbol_exposure + 1e-12
    assert breaching.any(), "fixture must reach a boundary where the second cap has work to do"
    assert (_book(run.scaled_targets).abs().max(axis=1) <= CAPS.max_symbol_exposure + 1e-12).all()


# --- what a team is shown -----------------------------------------------------------------------


def test_the_trim_a_team_is_shown_is_the_trim_that_was_applied():
    """Both halves come from one ``_cap_scale`` call, so this cannot drift -- and this test is what
    keeps it that way. Mutation this catches: computing the disclosure independently of the
    reduction (for example reporting ``cap / gross`` while applying ``cap / largest``).
    """
    run = RUNS[DOMINANT]
    assert run.requested_trim.stage == STAGE_REQUESTED
    assert run.executed_trim.stage == STAGE_EXECUTED
    pd.testing.assert_frame_equal(
        _book(run.targets),
        _book(run.requested_targets).mul(run.requested_trim.scale, axis=0),
    )
    pd.testing.assert_frame_equal(
        _book(run.scaled_targets),
        _book(apply_risk_scalars(run.targets, run.risk_scalars)).mul(
            run.executed_trim.scale, axis=0
        ),
    )


def test_the_requested_trim_summary_says_how_far_the_book_was_reduced():
    summary = RUNS[FOUR_NAME].requested_trim.summary()
    assert summary["stage"] == STAGE_REQUESTED
    assert summary["boundaries"] == len(GRID)
    assert summary["trimmed_boundaries"] == len(GRID)
    assert summary["trimmed_fraction"] == pytest.approx(1.0)
    assert summary["minimum_scale"] == pytest.approx(0.80)
    assert summary["median_scale"] == pytest.approx(0.80)
    assert summary["binding_cap_counts"] == {"gross": 0, "net": 0, "symbol": len(GRID)}
    assert set(summary["binding_cap_counts"]) == set(CAP_NAMES)


def test_an_untrimmed_book_is_reported_as_untrimmed():
    """The negative control for the disclosure itself. Mutation this catches: a summary that
    reports a trim unconditionally, or one seeded from ``cap / magnitude`` rather than 1.0."""
    run = UNTRIMMED_RUN
    summary = run.requested_trim.summary()
    assert summary["trimmed_boundaries"] == 0
    assert summary["trimmed_fraction"] == 0.0
    assert summary["minimum_scale"] == 1.0
    assert summary["median_scale"] == 1.0
    assert summary["binding_cap_counts"] == {"gross": 0, "net": 0, "symbol": 0}
    assert list(run.requested_trim.trimmed) == []
    pd.testing.assert_frame_equal(run.targets, run.requested_targets)


def test_every_summary_value_is_finite_so_the_packet_can_serialise_it():
    """``build_packet`` writes with ``allow_nan=False``. An empty median is NaN, so the untrimmed
    case has to report 1.0 rather than letting a released artifact fail to serialise -- or, worse,
    emit the non-standard ``NaN`` token."""
    for trim in (UNTRIMMED_RUN.requested_trim, RUNS[DOMINANT].executed_trim):
        summary = trim.summary()
        assert np.isfinite(summary["trimmed_fraction"])
        assert np.isfinite(summary["minimum_scale"])
        assert np.isfinite(summary["median_scale"])


def test_a_hold_row_is_recorded_but_never_counted_as_a_traded_boundary():
    """``summary()`` counts only rows carrying an explicit target, because those are the only rows
    the evaluator acts on. Mutation this catches: counting every row, which on a sparse mandate
    that rebalances one boundary in six would report a trim rate six times too low.
    """
    frame = pd.DataFrame(
        {
            "AUSDT": [0.60, 0.60],
            "BUSDT": [-0.10, -0.10],
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
        },
        index=pd.date_range(START, periods=2, freq="8h"),
    )
    trim = exposure_cap_trim(frame, CAPS, stage=STAGE_REQUESTED)
    # The hold row's own scale is still recorded, so the series lines up with the targets frame...
    assert trim.scale.iloc[1] == pytest.approx(CAPS.max_symbol_exposure / 0.60)
    # ...but it is not a boundary anyone traded.
    summary = trim.summary()
    assert summary["boundaries"] == 1
    assert summary["trimmed_boundaries"] == 1
    assert summary["trimmed_fraction"] == pytest.approx(1.0)
    assert list(trim.trimmed) == [frame.index[0]]


def test_float_noise_in_the_unit_gross_normalisation_is_not_reported_as_a_trim():
    """A 20-name equal-weight book -- the exact shape of a universe-wide CUP-20 candidate --
    renormalises to ``1.0000000000000002``, two ULP above the 1.0 gross cap.

    Mutation this catches: dropping ``_CAP_TOLERANCE`` and comparing strictly. That would rescale
    every such boundary by ``1 - 2e-16`` (a change nobody can observe) and then TELL the team its
    book was reduced at every boundary it ever traded, which is a false statement in a released
    artifact.
    """
    names = [f"S{index:02d}USDT" for index in range(20)]
    frame = pd.DataFrame(
        {name: [1.0, 1.0] for name in names} | {REBALANCE_INSTRUCTION_COLUMN: [True, True]},
        index=pd.date_range(START, periods=2, freq="8h"),
    )
    normalised = normalise_unit_gross(frame)
    values = normalised[names].to_numpy(dtype=float)
    # The premise, measured the same way the cap measures it.
    assert np.abs(values).sum(axis=1)[0] > CAPS.max_gross_exposure
    assert np.abs(values).sum(axis=1)[0] < CAPS.max_gross_exposure + 1e-12

    trim = exposure_cap_trim(normalised, CAPS, stage=STAGE_REQUESTED)
    assert trim.summary()["trimmed_boundaries"] == 0
    pd.testing.assert_frame_equal(apply_exposure_caps(normalised, CAPS), normalised)


# --- raise paths, each on its own ---------------------------------------------------------------


def _one_row(**weights) -> pd.DataFrame:
    return pd.DataFrame(
        {name: [value] for name, value in weights.items()} | {REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.DatetimeIndex([START]),
    )


def test_exposure_cap_trim_rejects_an_unknown_stage():
    """The stage is written into a released packet, so it may not be free text. Mutation this
    catches: dropping the membership check, which would let a typo ("reference") reach
    ``summary.json`` as if it named one of the two passes."""
    with pytest.raises(ValueError, match="stage must be one of"):
        exposure_cap_trim(_one_row(AUSDT=0.1), CAPS, stage="reference")


def test_exposure_cap_trim_rejects_a_nan_weight_rather_than_reporting_no_trim():
    """No fail-open on NaN, on the disclosure path as well as the application path. ``nan >
    ceiling`` is False, so without the guard a NaN row would be REPORTED as untrimmed -- a clean
    bill of health for a book nobody could size."""
    with pytest.raises(ValueError, match="non-finite"):
        exposure_cap_trim(_one_row(AUSDT=np.nan, BUSDT=0.5), CAPS, stage=STAGE_REQUESTED)


def test_exposure_cap_trim_rejects_an_infinite_weight_too():
    with pytest.raises(ValueError, match="non-finite"):
        exposure_cap_trim(_one_row(AUSDT=np.inf, BUSDT=0.5), CAPS, stage=STAGE_EXECUTED)


def test_run_candidate_raises_on_a_non_finite_weight_before_pass_one():
    """The end-to-end raise path: a strategy that returns a non-finite weight is refused, and it is
    refused by ``generate_targets`` before the caps ever see it. Mutation this catches: a cap that
    swallowed non-finite input would let it through to the evaluator one pass later, unattributed.
    """

    class NanBook:
        def target_weights(self, context, *, seed):
            return {"AUSDT": float("nan")}

    with pytest.raises(ValueError, match="non-finite"):
        run_candidate(
            NanBook(),
            SNAPSHOT,
            decision_times=GRID,
            seed=1,
            config=CAPS,
            risk_unit=RISK_UNIT,
        )


def test_a_trim_with_no_weight_columns_reports_nothing_rather_than_failing():
    """``ExposureCapTrim`` must survive the degenerate frame ``apply_exposure_caps`` already
    tolerates, so the two cannot disagree about it."""
    frame = pd.DataFrame({REBALANCE_INSTRUCTION_COLUMN: [True]}, index=pd.DatetimeIndex([START]))
    trim = exposure_cap_trim(frame, CAPS, stage=STAGE_REQUESTED)
    assert isinstance(trim, ExposureCapTrim)
    assert trim.summary()["trimmed_boundaries"] == 0
    assert trim.summary()["boundaries"] == 1
