import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.universe import (
    LIQUIDITY_MEASURE,
    build_membership,
    weekly_reconstitution_times,
)


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
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}


def test_ranking_is_by_trailing_volume_descending():
    volume, eligible = _frames(["AUSDT", "BUSDT", "CUSDT"], 200, [10.0, 30.0, 20.0])
    members = build_membership(
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

    members = build_membership(
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
    members = build_membership(
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
    members = build_membership(
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
    members = build_membership(
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
    members = build_membership(
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
    members = build_membership(
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
        build_membership(
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
    return build_membership(
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
    members = build_membership(
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
        build_membership(
            volume,
            eligible=eligible,
            reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
            lookback_days=180,
            minimum_scored_members=0,
        )
