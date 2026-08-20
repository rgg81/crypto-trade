from __future__ import annotations

import math

import pandas as pd
import pytest

from crypto_trade.cup50v2.config import OOS_END, OOS_START
from crypto_trade.cup50v2.neighbourhood import (
    Dimension,
    generate_neighbourhood,
    reject_inert_dimensions,
)
from crypto_trade.cup50v2.scoring import (
    RankedEntry,
    rank_entries,
    round_half_even,
    score_cell,
    score_neighbourhood,
    score_point,
)


def _returns(value: float, exposure: float = 1.0) -> pd.DataFrame:
    index = pd.date_range(OOS_START, OOS_END, freq="D", inclusive="left")
    return pd.DataFrame(
        {"net_return": value, "gross_return": value, "gross_exposure": exposure}, index=index
    )


def test_neighbourhood_cardinality_and_transforms() -> None:
    assert len(generate_neighbourhood({"fixed": 2.0}, ()).points) == 1
    one = generate_neighbourhood({"lookback": 100.0}, [Dimension("lookback", "integer")])
    assert len(one.points) == 7
    assert one.points[0]["lookback"] == 100
    two = generate_neighbourhood(
        {"decay": 10.0, "fraction": 0.5},
        [Dimension("decay", "positive"), Dimension("fraction", "fraction")],
    )
    assert len(two.points) == 7
    three = generate_neighbourhood(
        {"a": 10.0, "b": 20.0, "c": 0.0},
        [
            Dimension("a", "positive"),
            Dimension("b", "integer"),
            Dimension("c", "signed", natural_scale=5.0),
        ],
    )
    assert len(three.points) == 7
    with pytest.raises(ValueError, match="inert"):
        reject_inert_dimensions(one, lambda parameters: "same-target-stream")


def test_flat_cell_penalty_and_monotonic_return() -> None:
    flat = score_cell(_returns(0.0, exposure=0.0), OOS_START, OOS_END)
    expected = 50.0 * (1.0 + math.tanh(-0.15 / 0.10))
    assert math.isclose(flat.q, expected)
    assert flat.concentration == 1.0
    profitable = score_cell(_returns(0.0002), OOS_START, OOS_END)
    costly = score_cell(_returns(-0.0002), OOS_START, OOS_END)
    assert profitable.q > flat.q > costly.q


def test_point_weakest_fold_and_neighbourhood_formula() -> None:
    point = score_point({1: _returns(0.0001), 2: _returns(0.0001), 3: _returns(0.0001)})
    assert 0 < point.score <= 100
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    neighbourhood = score_neighbourhood(values, centre_index=0)
    # ceil(7/4) = position 2 => 20; median 40; centre 10.
    assert neighbourhood.lower_quartile_score == 20.0
    assert neighbourhood.official_score == 27.5


def test_rounding_and_deterministic_dnf_order() -> None:
    assert round_half_even(1.2345665) == 1.234566
    valid = RankedEntry("team-02", "c", True, 1, 1, 1, 1, 1, 1, 1, "b" * 64)
    dnf = RankedEntry("team-01", "d", False, 100, 100, 100, 100, 100, 0, 0, "a" * 64, "crash")
    assert rank_entries([dnf, valid]) == (valid, dnf)
