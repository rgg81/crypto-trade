import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times


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


def test_naive_timestamps_are_rejected():
    volume, eligible = _frames(["AUSDT"], 200, [10.0])
    with pytest.raises(ValueError):
        build_membership(
            volume,
            eligible=eligible,
            reconstitution_times=[pd.Timestamp("2020-06-29")],
            lookback_days=180,
        )
