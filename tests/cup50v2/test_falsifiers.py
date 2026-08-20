"""The battery a candidate must survive before it is observed."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2 import falsifiers
from crypto_trade.cup50v2.replay import REBALANCE_COLUMN

KEY = b"k" * 32


def _targets(values: list[float], rebalance: bool = True) -> pd.DataFrame:
    index = pd.date_range("2022-01-01", periods=len(values), freq="8h", tz="UTC")
    frame = pd.DataFrame({"AUSDT": values, "BUSDT": [-value for value in values]}, index=index)
    frame[REBALANCE_COLUMN] = rebalance
    return frame


def _bars(periods: int = 60) -> pd.DataFrame:
    open_times = pd.date_range("2022-01-01", periods=periods, freq="8h", tz="UTC")
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
            "symbol": "AUSDT",
            "close": np.linspace(100.0, 140.0, periods),
        }
    )


def test_sign_inversion_fails_a_book_whose_opposite_scores_as_well() -> None:
    assert falsifiers.sign_inversion(40.0, 12.0).passed
    assert not falsifiers.sign_inversion(40.0, 40.0).passed
    assert not falsifiers.sign_inversion(40.0, 55.0).passed


def test_inverting_targets_flips_weights_and_keeps_the_schedule() -> None:
    targets = _targets([0.3, 0.0, -0.2])
    inverted = falsifiers.invert_targets(targets)
    assert list(inverted["AUSDT"]) == [-0.3, 0.0, 0.2]
    assert list(inverted[REBALANCE_COLUMN]) == list(targets[REBALANCE_COLUMN])


def test_future_corruption_passes_a_causal_generator() -> None:
    def causal(bars: pd.DataFrame) -> pd.DataFrame:
        closes = bars.sort_values("close_time")["close"].to_numpy(dtype=float)
        index = pd.DatetimeIndex(pd.to_datetime(bars["close_time"], utc=True)).sort_values()
        # Weight from the bar that has already closed; nothing later is reachable.
        values = [0.0] + [
            float(np.sign(closes[step] - closes[step - 1])) * 0.1 for step in range(1, len(closes))
        ]
        frame = pd.DataFrame({"AUSDT": values}, index=index)
        frame[REBALANCE_COLUMN] = True
        return frame

    cuts = falsifiers.corruption_cut_points(
        pd.DatetimeIndex(pd.to_datetime(_bars()["close_time"], utc=True)), key=KEY
    )
    outcome = falsifiers.future_corruption(causal, _bars(), cut_points=cuts)
    assert outcome.passed, outcome.detail


def test_future_corruption_catches_a_generator_that_reaches_forward() -> None:
    """The evaluator slices causally, so this is a test of the candidate's own memory."""

    def peeking(bars: pd.DataFrame) -> pd.DataFrame:
        index = pd.DatetimeIndex(pd.to_datetime(bars["close_time"], utc=True)).sort_values()
        final = float(bars["close"].iloc[-1])
        frame = pd.DataFrame({"AUSDT": [final / 1000.0] * len(index)}, index=index)
        frame[REBALANCE_COLUMN] = True
        return frame

    cuts = falsifiers.corruption_cut_points(
        pd.DatetimeIndex(pd.to_datetime(_bars()["close_time"], utc=True)), key=KEY
    )
    outcome = falsifiers.future_corruption(peeking, _bars(), cut_points=cuts)
    assert not outcome.passed
    assert "changed when the future was corrupted" in outcome.detail


def test_cut_points_come_from_the_key_and_are_stable() -> None:
    decisions = pd.DatetimeIndex(pd.to_datetime(_bars()["close_time"], utc=True))
    first = falsifiers.corruption_cut_points(decisions, key=KEY)
    assert first == falsifiers.corruption_cut_points(decisions, key=KEY)
    assert first != falsifiers.corruption_cut_points(decisions, key=b"j" * 32)
    assert len(first) == 6


def test_determinism_compares_the_whole_stream() -> None:
    left = _targets([0.1, 0.2, 0.3])
    assert falsifiers.determinism(left, left.copy()).passed
    assert not falsifiers.determinism(left, _targets([0.1, 0.2, 0.4])).passed


def test_the_placebo_preserves_holding_periods_and_destroys_alignment() -> None:
    """A symbol permutation is a no-op on a uniform book; shuffling spells is not."""
    values = [0.2] * 6 + [-0.2] * 3 + [0.0] * 5 + [0.2] * 2
    targets = _targets(values)
    placebo = falsifiers.regime_spell_placebo(targets, key=KEY)

    assert list(placebo.index) == list(targets.index)
    assert sorted(placebo["AUSDT"].round(9)) == sorted(targets["AUSDT"].round(9))
    assert not placebo["AUSDT"].equals(targets["AUSDT"])

    def spells(series: pd.Series) -> sorted:
        lengths, start = [], 0
        array = series.to_numpy()
        for position in range(1, len(array) + 1):
            if position == len(array) or array[position] != array[start]:
                lengths.append(position - start)
                start = position
        return sorted(lengths)

    assert spells(placebo["AUSDT"]) == spells(targets["AUSDT"])


def test_the_placebo_is_stable_in_the_key_and_survives_an_empty_book() -> None:
    targets = _targets([0.2, 0.2, -0.1, 0.0])
    assert falsifiers.regime_spell_placebo(targets, key=KEY).equals(
        falsifiers.regime_spell_placebo(targets, key=KEY)
    )
    empty = pd.DataFrame(columns=["AUSDT", REBALANCE_COLUMN])
    assert falsifiers.regime_spell_placebo(empty, key=KEY).empty


@pytest.mark.parametrize("team_id", ["team-01", "team-08", "team-11"])
def test_a_shipped_seed_survives_future_corruption(team_id: str) -> None:
    """Includes the event lane and the learner: the two that carry the most state."""
    from crypto_trade.cup50v2.replay import (
        decision_grid,
        generate_targets,
        load_strategy_module,
        strategy_from_module,
    )

    from .test_seed_field import _synthetic_snapshot

    snapshot = _synthetic_snapshot()
    decisions = decision_grid(snapshot.window_start, snapshot.window_end)

    def generate(bars: pd.DataFrame) -> pd.DataFrame:
        return generate_targets(
            strategy_from_module(
                load_strategy_module(f"tournament/cup50v2/seeds/{team_id}/strategy.py")
            ),
            bars=bars,
            funding=snapshot.funding,
            auxiliary={},
            membership=snapshot.membership,
            decision_times=decisions,
            seed=1,
        )

    cuts = falsifiers.corruption_cut_points(decisions, key=KEY, count=3)
    outcome = falsifiers.future_corruption(generate, snapshot.bars, cut_points=cuts)
    assert outcome.passed, (team_id, outcome.detail)
