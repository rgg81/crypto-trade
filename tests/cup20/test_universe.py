import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.universe import (
    LIQUIDITY_MEASURE,
    build_membership,
    unmarkable_member_boundaries,
    weekly_reconstitution_times,
)


def _grid(volume):
    """The evaluator's 8h decision grid, spanning the daily volume frame."""
    return pd.date_range(
        volume.index.min(),
        volume.index.max() + pd.Timedelta(days=1),
        freq="8h",
        tz="UTC",
        inclusive="left",
    )


def _coverage(volume):
    """``(fillable, markable)`` with nothing missing: the neutral element for the other tests."""
    grid = _grid(volume)
    fillable = pd.DataFrame(True, index=grid, columns=list(volume.columns))
    return fillable, fillable.copy()


def _membership(volume, **kwargs):
    """``build_membership`` with full mark coverage unless the caller supplies its own.

    Mark coverage is a REQUIRED argument of the real function (a default would let a caller rebuild
    the universe without saying where the evaluator can mark, which is how the defect shipped).
    Every test below that is not about marks would otherwise carry two frames of noise, so this
    shim supplies the neutral value -- and the tests that ARE about marks pass their own.
    """
    fillable, markable = _coverage(volume)
    kwargs.setdefault("fillable", fillable)
    kwargs.setdefault("markable", markable)
    return build_membership(volume, **kwargs)


def _frames(symbols, days, volumes):
    index = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
    volume = pd.DataFrame(
        {symbol: np.full(days, value, dtype=float) for symbol, value in zip(symbols, volumes)},
        index=index,
    )
    eligible = pd.DataFrame(True, index=index, columns=list(symbols))
    return volume, eligible


def test_weekly_reconstitution_times_are_mondays_at_utc_midnight():
    times = weekly_reconstitution_times(
        pd.Timestamp("2020-01-01T00:00:00Z"), pd.Timestamp("2020-02-01T00:00:00Z")
    )
    assert times[0] == pd.Timestamp("2020-01-06T00:00:00Z")
    assert all(time.weekday() == 0 and time.hour == 0 for time in times)
    assert all(time.tzinfo is not None for time in times)


def test_incomplete_history_is_ineligible():
    volume, eligible = _frames(["AUSDT", "BUSDT"], 200, [100.0, 90.0])
    volume.loc[volume.index < "2020-03-01", "BUSDT"] = np.nan
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}


def test_ranking_is_by_trailing_volume_descending():
    volume, eligible = _frames(["AUSDT", "BUSDT", "CUSDT"], 200, [10.0, 30.0, 20.0])
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    ordered = members.sort_values("liquidity_rank")["symbol"].tolist()
    assert ordered == ["BUSDT", "CUSDT", "AUSDT"]
    assert members.sort_values("liquidity_rank")["liquidity_rank"].tolist() == [1, 2, 3]


def _spike_frames(days=200, steady=100.0, quiet=1.0, spike=1e7):
    """One steadily-liquid symbol against one that traded once, enormously.

    ``SPIKEUSDT``'s single day dominates a MEAN over the window and barely moves a MEDIAN, so the
    two statistics rank this pair in opposite orders. That is the entire difference between the
    universe rules, expressed in the smallest fixture that can hold it.
    """
    index = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
    volume = pd.DataFrame(
        {
            "STEADYUSDT": np.full(days, steady, dtype=float),
            "SPIKEUSDT": np.full(days, quiet, dtype=float),
        },
        index=index,
    )
    volume.loc[index[days // 2], "SPIKEUSDT"] = spike
    eligible = pd.DataFrame(True, index=index, columns=["STEADYUSDT", "SPIKEUSDT"])
    return volume, eligible


def test_a_single_volume_spike_does_not_outrank_steady_liquidity():
    """The property the median buys, and the one nothing else in this file asserts.

    Every other fixture here uses volumes that are constant within each lookback window, where mean
    and median coincide exactly -- which is why the universe ranked on the mean for a full build
    without a single test noticing. This one separates them.

    The arithmetic is asserted first, so the test cannot quietly become vacuous if a future fixture
    edit stops making the two statistics disagree: if SPIKEUSDT ever fails to win on the mean, the
    ranking assertion below would prove nothing.
    """
    volume, eligible = _spike_frames()
    boundary = pd.Timestamp("2020-06-29T00:00:00Z")
    window = volume.loc[volume.index < boundary].iloc[-180:]
    assert window["SPIKEUSDT"].mean() > window["STEADYUSDT"].mean(), (
        "fixture no longer separates the statistics: the spike must win on the mean"
    )
    assert window["SPIKEUSDT"].median() < window["STEADYUSDT"].median()

    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=20,
    )
    ordered = members.sort_values("liquidity_rank")["symbol"].tolist()
    assert ordered == ["STEADYUSDT", "SPIKEUSDT"], (
        "ranking followed the mean: a one-day volume spike outranked steady liquidity"
    )
    # The reported liquidity is the ranking statistic itself, not some other summary of the window.
    reported = members.set_index("symbol")["trailing_quote_volume"]
    assert reported["STEADYUSDT"] == pytest.approx(window["STEADYUSDT"].median())
    assert reported["SPIKEUSDT"] == pytest.approx(window["SPIKEUSDT"].median())


def test_a_spiking_symbol_loses_the_only_seat_to_a_steady_one():
    """The same property at the level that actually matters: who gets into the index.

    Ranking order alone is a weaker claim than membership -- with one seat available, the spiking
    symbol must not take it.
    """
    volume, eligible = _spike_frames()
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=1,
        entry_rank=1,
        exit_rank=1,
    )
    assert list(members["symbol"]) == ["STEADYUSDT"]


def _ranked_frames(count=30, days=40):
    """Thirty symbols with strictly decreasing constant volume: S00 is rank 1, S29 is rank 30."""
    index = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
    symbols = [f"S{position:02d}USDT" for position in range(count)]
    volume = pd.DataFrame(
        {symbol: np.full(days, 1000.0 - position) for position, symbol in enumerate(symbols)},
        index=index,
    )
    eligible = pd.DataFrame(True, index=index, columns=symbols)
    return volume, eligible, index


def test_hysteresis_keeps_incumbent_between_entry_and_exit_rank():
    volume, eligible, index = _ranked_frames()
    first, second = index[7], index[14]
    # From the second window onward S00 sits between S22 (978) and S23 (977), i.e. rank 23:
    # worse than entry rank 20, better than exit rank 25, so an incumbent must survive.
    volume.loc[index[7] :, "S00USDT"] = 977.5
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[first, second],
        lookback_days=7,
        target_size=20,
        entry_rank=20,
        exit_rank=25,
    )
    first_members = set(members.loc[members["reconstitution_time"] == first, "symbol"])
    second_members = set(members.loc[members["reconstitution_time"] == second, "symbol"])
    # First boundary has no incumbents yet, so it is a plain top-20-by-rank cut.
    assert first_members == {f"S{position:02d}USDT" for position in range(20)}
    # Second boundary: S00 falls to rank 23 but every other incumbent (S01..S19) still ranks
    # 1..19, so no seat opens up and membership is unchanged from the first boundary.
    assert second_members == first_members
    # TOURNAMENT-CHARTER-CUP20.md:70-71 -- "keep incumbents with rank <= 25 in rank order,
    # truncated to 20; fill any remaining slots from non-incumbents with rank <= 20". S20USDT
    # (rank 20) is a non-incumbent competing for a seat that never opens, so it must lose to the
    # rank-23 incumbent S00USDT even though S20USDT is individually more liquid.
    assert "S20USDT" not in second_members
    assert len(second_members) == 20


def test_symbol_beyond_exit_rank_is_dropped_and_slot_refilled():
    volume, eligible, index = _ranked_frames()
    first, second = index[7], index[14]
    volume.loc[index[7] :, "S00USDT"] = 1.0
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[first, second],
        lookback_days=7,
        target_size=20,
        entry_rank=20,
        exit_rank=25,
    )
    second_members = set(members.loc[members["reconstitution_time"] == second, "symbol"])
    # TOURNAMENT-CHARTER-CUP20.md:70-71 -- S00USDT falls to rank 30 (beyond exit_rank), vacating
    # its seat; S20USDT is the best-ranked non-incumbent (rank 20 <= entry_rank) and fills it. The
    # other nineteen incumbents (S01..S19) still rank <= exit_rank and keep their seats untouched.
    assert second_members == {f"S{position:02d}USDT" for position in range(1, 21)}
    assert "S00USDT" not in second_members
    assert "S20USDT" in second_members
    assert len(second_members) == 20


def test_ineligible_symbol_is_excluded_even_with_complete_history():
    volume, eligible = _frames(["AUSDT", "BUSDT"], 200, [100.0, 90.0])
    eligible.loc[eligible.index >= "2020-06-01", "AUSDT"] = False
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"BUSDT"}


def test_lookback_window_excludes_the_reconstitution_day_itself():
    volume, eligible = _frames(["AUSDT"], 400, [10.0])
    boundary = pd.Timestamp("2020-06-29T00:00:00Z")
    volume.loc[boundary:, "AUSDT"] = 1_000_000.0
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=20,
    )
    assert members["trailing_quote_volume"].iloc[0] == pytest.approx(10.0)


def test_the_declared_liquidity_measure_names_the_median():
    """A one-line guard against renaming the constant without changing what it means."""
    assert LIQUIDITY_MEASURE == "median-daily-quote-volume"


def test_naive_timestamps_are_rejected():
    volume, eligible = _frames(["AUSDT"], 200, [10.0])
    with pytest.raises(ValueError):
        _membership(
            volume,
            eligible=eligible,
            reconstitution_times=[pd.Timestamp("2020-06-29")],
            lookback_days=180,
        )


# --- minimum_scored_members: the charter's "a boundary with fewer than 8 members is not scored"
#
# The config declared `universe.minimum_scored_members = 8` and NOTHING read it -- a policy value
# that existed only as a number in a file. It is now enforced here, at the one place that decides
# what a boundary's membership is, rather than deleted: the charter states the rule in section 3,
# so the honest fix is to implement it. It is inert on the built snapshot by measurement (every
# shipped boundary carries exactly 20 members), which is why enforcing it did not change a single
# byte of the frozen data -- it is a guarantee against a future delisting wave, not a filter that
# shaped this artifact.


def _three_symbol_boundary(minimum):
    volume, eligible = _frames(["AUSDT", "BUSDT", "CUSDT"], 200, [30.0, 20.0, 10.0])
    return _membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
        minimum_scored_members=minimum,
    )


def test_a_boundary_below_the_minimum_is_not_emitted():
    assert _three_symbol_boundary(4).empty


def test_a_boundary_exactly_at_the_minimum_is_emitted():
    # Inclusive: "fewer than N" is dropped, N itself is kept.
    assert len(_three_symbol_boundary(3)) == 3


def test_the_default_minimum_changes_nothing():
    assert len(_three_symbol_boundary(1)) == 3


def test_only_the_thin_boundaries_are_dropped():
    """A universe that thins out and recovers keeps the boundaries that are thick enough."""
    volume, eligible = _frames(["AUSDT", "BUSDT", "CUSDT"], 400, [30.0, 20.0, 10.0])
    thin = (volume.index >= "2020-08-01") & (volume.index < "2020-10-01")
    eligible.loc[thin, ["BUSDT", "CUSDT"]] = False
    boundaries = list(
        weekly_reconstitution_times(
            pd.Timestamp("2020-06-29T00:00:00Z"), pd.Timestamp("2020-12-01T00:00:00Z")
        )
    )
    members = _membership(
        volume,
        eligible=eligible,
        reconstitution_times=boundaries,
        lookback_days=180,
        target_size=20,
        minimum_scored_members=3,
    )
    kept = set(members["reconstitution_time"])
    assert kept, "every boundary was dropped; the fixture proves nothing"
    assert len(kept) < len(boundaries), "no boundary was dropped; the fixture proves nothing"
    sizes = members.groupby("reconstitution_time").size()
    assert (sizes >= 3).all()


def test_minimum_scored_members_must_be_positive():
    volume, eligible = _frames(["AUSDT"], 200, [10.0])
    with pytest.raises(ValueError, match="minimum_scored_members"):
        _membership(
            volume,
            eligible=eligible,
            reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
            lookback_days=180,
            minimum_scored_members=0,
        )


# --- mark coverage: the criterion that keeps `evaluate_targets` from raising on the ELIGIBLE set
#
# `crypto_trade.tournament.engine_v2.evaluate_targets` raises `missing current mark for eligible
# symbols` at any decision boundary where a member has an executable bar open and no mark price.
# It fires before any strategy code runs, so ONE unmarkable member crashes EVERY candidate. Every
# fixture in this file above constructed volume and eligibility and said nothing about marks --
# which is exactly why 862 tests passed while the built snapshot held 21 such boundaries for
# SUIUSDT (member from 2023-10-30, bars from 2023-05-03, marks only from 2023-11-06).
#
# Each test below names the mutation it kills, because a coverage criterion has four independent
# dials -- WHERE it starts, WHERE it ends, whether it is conditioned on fillability, and whether an
# unknown cell fails open -- and a fixture that pins only one of them looks like a test and is not.

BOUNDARY = pd.Timestamp("2020-06-29T00:00:00Z")
NEXT_BOUNDARY = pd.Timestamp("2020-07-06T00:00:00Z")


def _marked_frames(volumes=(100.0, 90.0)):
    """Two complete-history symbols, A more liquid than B, with full coverage to start from."""
    volume, eligible = _frames(["AUSDT", "BUSDT"], 400, list(volumes))
    fillable, markable = _coverage(volume)
    return volume, eligible, fillable, markable


def test_a_symbol_with_bars_but_no_marks_is_not_a_member():
    """The headline fixture, and the shape every pre-existing test in this file lacks.

    Kills the mutation: dropping `& markable_now` from the candidate filter -- i.e. the code as it
    shipped, where a symbol with a complete 180-day volume history and no mark price at all became
    a member and crashed the evaluator.
    """
    volume, eligible, fillable, markable = _marked_frames()
    markable.loc[markable.index >= BOUNDARY, "BUSDT"] = False
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}
    # ... and the property that matters is the absence of the evaluator's raise condition, not the
    # membership list, so assert it directly on the frame that shipped.
    assert unmarkable_member_boundaries(members, fillable=fillable, markable=markable) == []


def test_marks_must_cover_the_whole_membership_period_not_just_the_boundary():
    """Kills the mutation: narrowing the criterion to the reconstitution boundary itself.

    A mark AT `BOUNDARY` says nothing about the twenty intra-week decision boundaries that follow,
    and the evaluator visits every one of them.
    """
    volume, eligible, fillable, markable = _marked_frames()
    gap = BOUNDARY + pd.Timedelta(hours=8)
    markable.loc[gap, "BUSDT"] = False
    assert markable.loc[BOUNDARY, "BUSDT"], "fixture must keep the boundary itself marked"
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}


def test_marks_are_not_required_outside_the_membership_period():
    """Kills the mutation: widening the criterion to the whole grid, or to a trailing lookback.

    Either would be a real cost, not a harmless over-reach: Binance's mark archive begins on one
    date for every symbol at once, so a trailing-lookback mark rule admits nobody for 180 days
    after it and drags `IS_START` -- a computed, frozen tournament parameter -- months later.
    """
    volume, eligible, fillable, markable = _marked_frames()
    markable.loc[markable.index >= NEXT_BOUNDARY, "BUSDT"] = False
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY, NEXT_BOUNDARY],
        lookback_days=180,
        target_size=20,
    )
    held = {time: set(group) for time, group in members.groupby("reconstitution_time")["symbol"]}
    assert held[BOUNDARY] == {"AUSDT", "BUSDT"}, "the gap is after this period; B belongs here"
    assert held[NEXT_BOUNDARY] == {"AUSDT"}, "the gap is inside this period; B must lose its seat"


def test_an_incumbent_loses_its_seat_when_it_stops_being_markable():
    """Hysteresis protects an incumbent's RANK; it must not protect an unmarkable one.

    Kills the mutation: applying the mark filter to new entrants only (the natural place to put it
    if one thinks of it as a listing-age rule), which would leave every incumbent free to carry an
    unmarkable seat forward indefinitely.
    """
    volume, eligible, fillable, markable = _marked_frames()
    markable.loc[markable.index >= NEXT_BOUNDARY, "BUSDT"] = False
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY, NEXT_BOUNDARY],
        lookback_days=180,
        target_size=20,
        entry_rank=20,
        exit_rank=25,
    )
    second = members.loc[members["reconstitution_time"] == NEXT_BOUNDARY, "symbol"]
    assert "BUSDT" in set(members.loc[members["reconstitution_time"] == BOUNDARY, "symbol"])
    assert "BUSDT" not in set(second), "an incumbent survived a period it cannot be marked in"


def test_a_missing_mark_where_the_symbol_is_not_fillable_does_not_exclude_it():
    """Kills the mutation: dropping the `fillable &` conjunction and demanding marks everywhere.

    The evaluator demands a mark only for symbols in `eligible_at(...) & fillable`, so a boundary
    at which the symbol has no executable bar open needs none. Over-reaching here is not free:
    measured on the built acquisition, the unconditional rule moves 84 membership rows against
    this rule's 56, all of the extra ones for symbols the evaluator would never have asked about.
    """
    volume, eligible, fillable, markable = _marked_frames()
    halt = (markable.index >= BOUNDARY) & (markable.index < BOUNDARY + pd.Timedelta(days=2))
    markable.loc[halt, "BUSDT"] = False
    fillable.loc[halt, "BUSDT"] = False
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT", "BUSDT"}


def test_the_final_boundary_is_checked_to_the_end_of_the_grid():
    """Kills the mutation: giving the last boundary an empty or one-row period.

    It has no successor to bound it, so it is the one boundary whose period has to be derived
    differently -- and the natural off-by-one there admits everything.
    """
    volume, eligible, fillable, markable = _marked_frames()
    markable.iloc[-1, markable.columns.get_loc("BUSDT")] = False
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}


def test_coverage_must_span_every_ranked_symbol():
    """Kills the mutation: reindexing a missing symbol to all-False (silently ineligible) or to
    all-True (silently admitted). Neither is a fact; the caller has to supply one."""
    volume, eligible, fillable, markable = _marked_frames()
    with pytest.raises(ValueError, match="do not cover every ranked symbol"):
        build_membership(
            volume,
            eligible=eligible,
            fillable=fillable.drop(columns=["BUSDT"]),
            markable=markable.drop(columns=["BUSDT"]),
            reconstitution_times=[BOUNDARY],
            lookback_days=180,
        )


def test_fillable_and_markable_must_share_one_grid():
    volume, eligible, fillable, markable = _marked_frames()
    with pytest.raises(ValueError, match="share one decision grid"):
        build_membership(
            volume,
            eligible=eligible,
            fillable=fillable,
            markable=markable.iloc[1:],
            reconstitution_times=[BOUNDARY],
            lookback_days=180,
        )


def test_fillable_and_markable_must_cover_the_same_symbols():
    volume, eligible, fillable, markable = _marked_frames()
    with pytest.raises(ValueError, match="cover the same symbols"):
        build_membership(
            volume,
            eligible=eligible,
            fillable=fillable,
            markable=markable.drop(columns=["BUSDT"]),
            reconstitution_times=[BOUNDARY],
            lookback_days=180,
        )


def test_a_boundary_off_the_decision_grid_is_refused():
    """Kills the mutation: letting `searchsorted` produce an empty period, which admits everything.

    An off-grid boundary is not a hypothetical -- it is what a caller gets by passing a daily
    reconstitution schedule with an 8h coverage grid built from a different frame.
    """
    volume, eligible, fillable, markable = _marked_frames()
    off_grid = BOUNDARY + pd.Timedelta(hours=1)
    markable.loc[markable.index >= BOUNDARY, "BUSDT"] = False
    with pytest.raises(ValueError, match="absent from the decision grid"):
        build_membership(
            volume,
            eligible=eligible,
            fillable=fillable,
            markable=markable,
            reconstitution_times=[off_grid],
            lookback_days=180,
        )


def test_non_boolean_coverage_is_refused_rather_than_cast():
    """Kills the mutation: `astype(bool)` on the coverage frames.

    The cast is the fail-open: pandas maps NaN to True, so every unknown cell would be read as
    "marked". The fixture asserts that directly, so the test cannot become vacuous if the cast's
    behaviour is ever misremembered.
    """
    volume, eligible, fillable, markable = _marked_frames()
    floated = markable.astype(float)
    floated.loc[BOUNDARY, "BUSDT"] = np.nan
    assert bool(floated.loc[BOUNDARY, "BUSDT"].astype(bool)) is True, (
        "astype(bool) no longer maps NaN to True; this test's premise needs rewriting"
    )
    with pytest.raises(ValueError, match="markable must be a Boolean frame"):
        build_membership(
            volume,
            eligible=eligible,
            fillable=fillable,
            markable=floated,
            reconstitution_times=[BOUNDARY],
            lookback_days=180,
        )


def test_non_boolean_eligibility_is_refused_rather_than_cast():
    """The same fail-open, on the input that always had it: `eligible` was `.astype(bool)`."""
    volume, eligible = _frames(["AUSDT", "BUSDT"], 400, [100.0, 90.0])
    floated = eligible.astype(float)
    floated.loc[BOUNDARY, "BUSDT"] = np.nan
    with pytest.raises(ValueError, match="eligible must be a Boolean frame"):
        _membership(
            volume,
            eligible=floated,
            reconstitution_times=[BOUNDARY],
            lookback_days=180,
        )


def test_unsorted_reconstitution_times_are_refused():
    """Kills the mutation: reading `[t_i, t_{i+1})` off an unordered schedule, where the period
    runs backwards and `any()` over an empty slice admits everything."""
    volume, eligible = _frames(["AUSDT"], 400, [100.0])
    with pytest.raises(ValueError, match="sorted ascending"):
        _membership(
            volume,
            eligible=eligible,
            reconstitution_times=[NEXT_BOUNDARY, BOUNDARY],
            lookback_days=180,
        )


def test_duplicate_reconstitution_times_are_refused():
    volume, eligible = _frames(["AUSDT"], 400, [100.0])
    with pytest.raises(ValueError, match="duplicate timestamps"):
        _membership(
            volume,
            eligible=eligible,
            reconstitution_times=[BOUNDARY, BOUNDARY],
            lookback_days=180,
        )


# --- unmarkable_member_boundaries: the post-condition, which must be able to DISAGREE


def test_the_post_condition_is_silent_on_a_clean_membership():
    volume, eligible, fillable, markable = _marked_frames()
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY, NEXT_BOUNDARY],
        lookback_days=180,
    )
    assert not members.empty, "empty membership would make this assertion vacuous"
    assert unmarkable_member_boundaries(members, fillable=fillable, markable=markable) == []


def test_the_post_condition_names_every_offending_boundary_and_symbol():
    """It replays the evaluator's own test over a membership frame it did not build, which is what
    lets it disagree. Kills the mutation: re-deriving membership instead of reading it."""
    volume, eligible, fillable, markable = _marked_frames()
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
    )
    holed = markable.copy()
    gaps = [BOUNDARY, BOUNDARY + pd.Timedelta(hours=16)]
    holed.loc[gaps, "BUSDT"] = False
    assert unmarkable_member_boundaries(members, fillable=fillable, markable=holed) == [
        (gaps[0], "BUSDT"),
        (gaps[1], "BUSDT"),
    ]


def test_the_post_condition_catches_a_boundary_that_emitted_nothing():
    """The one gap `build_membership`'s own criterion cannot close.

    A boundary below `minimum_scored_members` emits no rows, so `eligible_at` keeps returning the
    PREVIOUS boundary's members through a period their coverage was never checked over. Modelled
    here by a membership frame that holds only the first boundary while the gap sits in the second
    boundary's period.
    """
    volume, eligible, fillable, markable = _marked_frames()
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
    )
    holed = markable.copy()
    later = NEXT_BOUNDARY + pd.Timedelta(hours=8)
    holed.loc[later, "BUSDT"] = False
    assert unmarkable_member_boundaries(members, fillable=fillable, markable=holed) == [
        (later, "BUSDT")
    ]


def test_the_post_condition_reports_a_member_with_no_coverage_column_at_all():
    """Kills the mutation: `columns.get(symbol)` returning None and being skipped, which would read
    a symbol the coverage frames have never heard of as fully marked."""
    volume, eligible, fillable, markable = _marked_frames()
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
    )
    trimmed_fillable = fillable.drop(columns=["BUSDT"])
    trimmed_markable = markable.drop(columns=["BUSDT"])
    found = unmarkable_member_boundaries(
        members, fillable=trimmed_fillable, markable=trimmed_markable
    )
    held = trimmed_fillable.index[trimmed_fillable.index >= BOUNDARY]
    assert found == [(time, "BUSDT") for time in held]


def test_the_post_condition_is_empty_on_an_empty_membership():
    volume, _, fillable, markable = _marked_frames()
    empty = pd.DataFrame(columns=["reconstitution_time", "symbol"])
    assert unmarkable_member_boundaries(empty, fillable=fillable, markable=markable) == []


def test_the_post_condition_refuses_a_membership_past_the_end_of_the_coverage_grid():
    """Kills the mutation: a boundary beyond the last grid row scanning an empty slice.

    An empty slice yields no findings, so the frame the check cannot speak about is the one it
    would report clean -- the same fail-open shape as an off-grid boundary in `build_membership`.
    """
    volume, eligible, fillable, markable = _marked_frames()
    members = build_membership(
        volume,
        eligible=eligible,
        fillable=fillable,
        markable=markable,
        reconstitution_times=[BOUNDARY],
        lookback_days=180,
    )
    truncated = fillable.index < BOUNDARY
    assert truncated.any(), "the truncated grid must still have rows, or nothing is being tested"
    with pytest.raises(ValueError, match="coverage grid ends at"):
        unmarkable_member_boundaries(
            members, fillable=fillable.loc[truncated], markable=markable.loc[truncated]
        )
