"""Every seed must trade against the *real* snapshot, not against a fixture of my assumptions.

This file exists because the unit tests could not have caught what it caught.

An earlier revision read the funding column as ``last_funding_rate`` -- the raw Binance name rather
than the tournament's canonical ``funding_rate``. Two seeds returned an empty score series on every
decision, produced no book at all, and scored exactly zero across 808 days. Nothing raised. The unit
fixture declared the same wrong column, so every unit test passed: the fixture encoded the same
assumption as the code, and a fixture that shares the code's assumption cannot falsify it.

The only thing that could have caught it is contact with the real data, which is what this does.
It is skipped when the snapshot is absent so a checkout without 746 MB of parquet still runs green,
and that skip is the honest trade -- but the readiness load and activation both run it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext
from crypto_trade.tournament.v5 import lanes, seeds
from crypto_trade.tournament.v5.engine import generate_targets

SNAPSHOT = Path("data/top40/snapshot-v3")
# A quiet stretch well inside the development window, long enough for the deepest seed's 120-bar
# lookback to be satisfied from real history.
PROBE_START = pd.Timestamp("2022-03-01", tz="UTC")
PROBE_END = pd.Timestamp("2022-03-08", tz="UTC")

pytestmark = pytest.mark.skipif(
    not (SNAPSHOT / "bars.parquet").is_file(),
    reason="snapshot-v3 is not present in this checkout",
)


@pytest.fixture(scope="module")
def snapshot() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership")
    }


@pytest.fixture(scope="module")
def live_context(snapshot) -> DecisionContext:
    """A real DecisionContext, captured from the evaluator rather than constructed by hand.

    Constructing one by hand would reintroduce exactly the problem: it would carry whatever columns
    I believe are there.
    """

    captured: dict[str, DecisionContext] = {}

    class _Capture:
        def target_weights(self, context, *, seed):
            captured.setdefault("context", context)
            return None

    decisions = list(pd.date_range(PROBE_START, PROBE_END, freq="8h", tz="UTC"))
    generate_targets(
        _Capture(),
        snapshot["bars"],
        snapshot["funding"],
        snapshot["membership"],
        decisions,
        seed=42,
    )
    if "context" not in captured:
        pytest.fail("the evaluator never called the strategy; the probe window has no decisions")
    return captured["context"]


def test_the_declared_funding_columns_exist_in_the_real_context(live_context):
    """The assertion that would have caught the defect, stated against real data."""

    missing = [name for name in seeds.FUNDING_COLUMNS if name not in live_context.funding.columns]
    assert not missing, (
        f"seeds read funding columns that the snapshot does not provide: {missing}; "
        f"available columns are {sorted(live_context.funding.columns)}"
    )


def test_the_declared_bar_columns_exist_in_the_real_context(live_context):
    symbol = next(iter(live_context.bars))
    available = set(live_context.bars[symbol].columns)
    missing = [name for name in seeds.BAR_COLUMNS if name not in available]

    assert not missing, f"seeds read bar columns the snapshot does not provide: {missing}"


@pytest.mark.parametrize("name", seeds.seed_names())
def test_every_seed_produces_a_book_on_real_data(name, live_context):
    """A seed that never trades is not a baseline -- it is an absent lane.

    team-01 and team-02 would each have started their first charged trial with a strategy that
    could not produce a single position, and the leaderboard would have reported that as a result.
    """

    weights = seeds.build_seed(name).target_weights(live_context, seed=42)

    assert weights, f"{name} produced no book against real data"
    assert any(value > 0 for value in weights.values()), f"{name} has no long side"
    assert any(value < 0 for value in weights.values()), f"{name} has no short side"


def test_the_funding_seeds_specifically_read_a_column_that_carries_values(live_context):
    """Presence is not enough -- an all-NaN column would pass a column check and score nothing."""

    funding = live_context.funding
    rates = funding[funding["symbol"].isin(live_context.eligible_symbols)]["funding_rate"]

    assert len(rates) > 0
    assert rates.notna().any()
    assert float(rates.abs().sum()) > 0.0


def test_every_lane_seed_is_reachable_from_the_roster(live_context):
    """The roster and the real data agree on what each lane will actually run."""

    for lane in lanes.LANES:
        weights = seeds.build_seed(lane.seed).target_weights(live_context, seed=42)
        assert weights, f"{lane.team_id}'s seed {lane.seed} produced no book"
