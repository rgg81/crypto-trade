"""The fifteen organizer seeds must each actually trade, and trade differently from each other."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext
from crypto_trade.tournament.v5 import lanes, seeds

DECISION = pd.Timestamp("2022-06-01", tz="UTC")
SYMBOLS = tuple(f"S{index:02d}USDT" for index in range(1, 15))


def _bars(symbol_index: int, rows: int = 200) -> pd.DataFrame:
    """A plausible bar history. Each symbol gets its own drift, volatility and flow character, so a
    seed that reads a different column produces a different book."""

    generator = np.random.default_rng(100 + symbol_index)
    drift = 0.0004 * (symbol_index - 7)
    volatility = 0.01 + 0.002 * (symbol_index % 5)
    steps = generator.normal(drift, volatility, size=rows)
    close = 100.0 * np.exp(np.cumsum(steps))
    volume = np.abs(generator.normal(5e6 + 3e5 * symbol_index, 8e5, size=rows))
    counts = np.abs(generator.normal(2000 + 300 * (symbol_index % 4), 200, size=rows)) + 1.0
    taker_share = 0.40 + 0.02 * (symbol_index % 6)
    index = pd.date_range(end=DECISION, periods=rows, freq="8h", tz="UTC")
    return pd.DataFrame(
        {
            "open": close * (1.0 - 0.001),
            "high": close * (1.0 + volatility),
            "low": close * (1.0 - volatility),
            "close": close,
            "volume": volume / close,
            "quote_volume": volume,
            "trade_count": counts,
            "taker_buy_volume": volume * taker_share / close,
            "taker_buy_quote_volume": volume * taker_share,
        },
        index=index,
    )


@pytest.fixture
def context() -> DecisionContext:
    generator = np.random.default_rng(7)
    funding = pd.DataFrame(
        {
            "symbol": np.repeat(SYMBOLS, 12),
            "last_funding_rate": generator.normal(0.0001, 0.0004, size=len(SYMBOLS) * 12),
        }
    )
    return DecisionContext(
        decision_time=DECISION,
        bars={symbol: _bars(index) for index, symbol in enumerate(SYMBOLS, start=1)},
        funding=funding,
        auxiliary={},
        eligible_symbols=list(SYMBOLS),
    )


@pytest.mark.parametrize("name", seeds.seed_names())
def test_every_seed_produces_a_real_two_sided_book(name, context):
    """A seed that returns nothing is not a baseline -- it is an absent lane.

    V4's readiness strategy was flat and therefore exercised none of the evaluator, and six defects
    survived to invalidate all twelve of its trials.
    """

    weights = seeds.build_seed(name).target_weights(context, seed=42)

    assert weights, f"{name} produced no book"
    values = list(weights.values())
    assert any(value > 0 for value in values), f"{name} has no long side"
    assert any(value < 0 for value in values), f"{name} has no short side"
    assert all(abs(value) <= 0.10 + 1e-9 for value in values), f"{name} breaches the per-symbol cap"
    assert sum(abs(value) for value in values) <= 1.0 + 1e-9, f"{name} breaches gross"


@pytest.mark.parametrize("name", seeds.seed_names())
def test_every_seed_is_deterministic(name, context):
    first = seeds.build_seed(name).target_weights(context, seed=42)
    second = seeds.build_seed(name).target_weights(context, seed=42)

    assert first == second


def test_the_seeds_do_not_all_produce_the_same_book(context):
    """Fifteen lanes that agree are one experiment run fifteen times.

    Not a claim that the seeds are good -- only that they read different information. Two seeds
    landing on identical books would mean the mandates are not separating the field at all.
    """

    books = {
        name: tuple(sorted(seeds.build_seed(name).target_weights(context, seed=42).items()))
        for name in seeds.seed_names()
    }
    distinct = set(books.values())

    assert len(distinct) >= 10, f"only {len(distinct)} distinct books across fifteen seeds"


def test_the_directional_seed_carries_net_and_the_others_do_not(context):
    """team-14 is mandated to run non-zero net; a market-neutral book does not satisfy it."""

    directional = seeds.build_seed("breadth_state").target_weights(context, seed=42)
    neutral = seeds.build_seed("defensive_beta").target_weights(context, seed=42)

    assert abs(sum(directional.values())) > 1e-6
    assert abs(sum(directional.values())) <= 0.25
    assert abs(sum(neutral.values())) < 1e-9


def test_only_the_rationed_seed_reads_taker_flow():
    """Rationing is structural, not an instruction a lane is trusted to follow."""

    import inspect

    source = {name: inspect.getsource(type(seeds.build_seed(name))) for name in seeds.seed_names()}
    readers = [name for name, text in source.items() if "taker_buy" in text]

    assert readers == ["taker_flow"]


# -- wiring to the lanes --------------------------------------------------------------------------


def test_every_lane_names_a_seed_that_exists_and_no_seed_is_orphaned():
    seeds.assert_every_lane_has_a_seed([entry.seed for entry in lanes.LANES])


def test_a_lane_naming_a_missing_seed_is_refused():
    with pytest.raises(seeds.SeedError, match="do not exist"):
        seeds.assert_every_lane_has_a_seed(
            [entry.seed for entry in lanes.LANES[:-1]] + ["not_a_real_seed"]
        )


def test_an_orphaned_seed_is_refused():
    """Dead code a reader would mistake for part of the field."""

    with pytest.raises(seeds.SeedError, match="no lane claims"):
        seeds.assert_every_lane_has_a_seed([entry.seed for entry in lanes.LANES[:-1]])


def test_an_unknown_seed_name_is_refused():
    with pytest.raises(seeds.SeedError, match="unknown organizer seed"):
        seeds.build_seed("wishful_thinking")


# -- degenerate inputs ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", seeds.seed_names())
def test_a_seed_holds_rather_than_raising_when_the_cross_section_is_too_small(name, context):
    """Returning None keeps current quantities. An exception would consume a trial."""

    narrow = DecisionContext(
        decision_time=context.decision_time,
        bars={symbol: context.bars[symbol] for symbol in SYMBOLS[:2]},
        funding=context.funding,
        auxiliary={},
        eligible_symbols=list(SYMBOLS[:2]),
    )

    assert seeds.build_seed(name).target_weights(narrow, seed=42) is None


@pytest.mark.parametrize("name", seeds.seed_names())
def test_a_seed_holds_rather_than_raising_when_history_is_short(name, context):
    """The first weeks of a new member are exactly this case, and it must not raise."""

    short = DecisionContext(
        decision_time=context.decision_time,
        bars={symbol: frame.tail(3) for symbol, frame in context.bars.items()},
        funding=context.funding,
        auxiliary={},
        eligible_symbols=list(SYMBOLS),
    )

    weights = seeds.build_seed(name).target_weights(short, seed=42)
    assert weights is None or isinstance(weights, dict)
