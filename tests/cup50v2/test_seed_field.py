"""Every lane seed, through the real evaluator.

CUP-50's activation readiness ran a flat strategy, so it exercised no carried position, no roster
exit, no participation limit and no post-exit coverage -- and three organizer defects survived into
a live field, invalidating all twelve trials twice. A readiness check has to trade.

This is the fast synthetic version, run on every commit. The full version runs the twelve seeds over
the real in-sample snapshot at activation.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.common_risk import BARS_PER_YEAR
from crypto_trade.cup50v2.config import TEAM_IDS
from crypto_trade.cup50v2.replay import (
    ExecutionConfig,
    load_strategy_module,
    run_candidate,
    strategy_from_module,
)
from crypto_trade.cup50v2.snapshot import Snapshot

SEED_ROOT = "tournament/cup50v2/seeds"
SYMBOL_COUNT = 24
PERIODS = 480


def _synthetic_snapshot(seed: int = 17) -> Snapshot:
    """A cross-section with a market factor, dispersion, and a rotating roster."""
    generator = np.random.default_rng(seed)
    start = pd.Timestamp("2022-01-03T00:00:00Z")
    open_times = pd.date_range(start, periods=PERIODS, freq="8h", tz="UTC")
    symbols = [f"S{index:02d}USDT" for index in range(SYMBOL_COUNT)]
    market = generator.normal(0.0002, 0.012, size=PERIODS)

    bars, funding, marks = [], [], []
    for index, symbol in enumerate(symbols):
        beta = 0.5 + 1.5 * (index % 5) / 4.0
        idio = generator.normal(0.0, 0.008 + 0.004 * (index % 3), size=PERIODS)
        steps = beta * market + idio
        volume = 5e7 * (1.0 + (index % 7)) * np.exp(generator.normal(0.0, 0.3, size=PERIODS))
        # Liquidation cascades: a large adverse move on a volume spike, which is the event the
        # shock-reversal lane exists for. Without one, that lane is flat and readiness would report
        # a field that never exercised its own event path.
        for shock in range(30 + index * 7, PERIODS, 120):
            steps[shock] += -0.16 if (index + shock) % 2 else 0.16
            volume[shock] *= 7.0
        close = 100.0 * np.exp(np.cumsum(steps))
        taker = volume * (0.5 + generator.normal(0.0, 0.05, size=PERIODS)).clip(0.2, 0.8)
        opens = np.concatenate(([100.0], close[:-1]))
        bars.append(
            pd.DataFrame(
                {
                    "open_time": open_times,
                    "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "symbol": symbol,
                    "open": opens,
                    "close": close,
                    "high": np.maximum(opens, close) * 1.004,
                    "low": np.minimum(opens, close) * 0.996,
                    "volume": volume / close,
                    "quote_volume": volume,
                    "trade_count": (volume / 1000.0).astype(int),
                    "taker_buy_volume": taker / close,
                    "taker_buy_quote_volume": taker,
                }
            )
        )
        rate = generator.normal(0.0001 * (1 + index % 4), 0.0003, size=PERIODS)
        funding.append(
            pd.DataFrame(
                {
                    "funding_time": open_times,
                    "symbol": symbol,
                    "funding_rate": rate,
                    "mark_price": close,
                }
            )
        )
        marks.append(pd.DataFrame({"mark_time": open_times, "symbol": symbol, "mark_price": close}))

    # A roster that rotates, so a lane meets names arriving and leaving rather than a fixed set.
    roster = []
    for week, boundary in enumerate(pd.date_range(start, open_times[-1], freq="7D", tz="UTC")):
        members = symbols[: SYMBOL_COUNT - 4] if week % 3 else symbols[4:]
        for rank, symbol in enumerate(members, start=1):
            roster.append([boundary, symbol, rank, 1e8])

    return Snapshot(
        pd.concat(bars, ignore_index=True),
        pd.concat(funding, ignore_index=True),
        pd.concat(marks, ignore_index=True),
        pd.DataFrame(
            roster,
            columns=[
                "reconstitution_time",
                "symbol",
                "liquidity_rank",
                "median_daily_quote_volume",
            ],
        ),
        pd.DataFrame({"symbol": symbols}),
        "x" * 64,
        open_times[0],
        open_times[-1],
        False,
    )


@pytest.fixture(scope="module")
def snapshot() -> Snapshot:
    return _synthetic_snapshot()


@pytest.mark.parametrize("team_id", TEAM_IDS)
def test_every_lane_seed_survives_a_full_replay(team_id: str, snapshot: Snapshot) -> None:
    strategy = strategy_from_module(load_strategy_module(f"{SEED_ROOT}/{team_id}/strategy.py"))
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=int(team_id.split("-")[1]),
        record_events=False,
    )
    config = ExecutionConfig()
    for multiplier, result in replay.costs.items():
        returns = result.returns
        assert len(returns) > 0, team_id
        assert np.isfinite(returns["net_return"].to_numpy()).all(), (team_id, multiplier)
        assert returns["gross_exposure"].max() <= config.max_gross_exposure + 1e-9
        assert (returns["equity"] > 0).all(), (team_id, multiplier)

    targets = replay.raw_targets.drop(
        columns=[column for column in replay.raw_targets.columns if column.startswith("__")]
    )
    # A held decision is an all-NaN row by design, and most rows are held: the house convention is
    # one decision a day on an eight-hour grid. Reduce past them rather than through them.
    emitted = targets.to_numpy(dtype=float)
    assert np.isnan(emitted).all(axis=1).any(), f"{team_id} never held"
    assert np.nanmax(np.abs(emitted)) <= 1.0 + 1e-9


@pytest.mark.parametrize("team_id", TEAM_IDS)
def test_every_lane_seed_is_deterministic(team_id: str, snapshot: Snapshot) -> None:
    """Two clean runs of the same source and seed must agree bit for bit."""
    source = f"{SEED_ROOT}/{team_id}/strategy.py"
    runs = []
    for _ in range(2):
        strategy = strategy_from_module(load_strategy_module(source))
        replay = run_candidate(
            strategy,
            snapshot=snapshot,
            start=snapshot.window_start,
            end=snapshot.window_end,
            seed=7,
            record_events=False,
        )
        runs.append(replay.costs[1].returns["net_return"].to_numpy())
    assert np.array_equal(runs[0], runs[1]), team_id


def test_the_field_as_a_whole_trades_and_is_sized_by_the_common_unit(snapshot: Snapshot) -> None:
    """Readiness means the field exercises execution, not that it runs without raising."""
    active, volatilities, turnover = [], {}, {}
    for team_id in TEAM_IDS:
        strategy = strategy_from_module(load_strategy_module(f"{SEED_ROOT}/{team_id}/strategy.py"))
        replay = run_candidate(
            strategy,
            snapshot=snapshot,
            start=snapshot.window_start,
            end=snapshot.window_end,
            seed=int(team_id.split("-")[1]),
            record_events=False,
        )
        returns = replay.costs[1].returns
        deployed = float((returns["gross_exposure"] >= 0.05).mean())
        gross = returns["gross_return"].to_numpy(dtype=float)[240:]
        volatilities[team_id] = float(np.std(gross, ddof=1)) * math.sqrt(BARS_PER_YEAR)
        if deployed > 0.05:
            active.append(team_id)
        turnover[team_id] = float(returns["turnover"].sum())

    # Most lanes must deploy. An event lane is legitimately flat much of the time, and the learner
    # is flat until it has enough accumulated rows, so this is a floor on the field, not on each.
    assert len(active) >= 9, sorted(set(TEAM_IDS) - set(active))
    assert all(turnover[team] > 0.0 for team in active), turnover
    sized = [value for team, value in volatilities.items() if team in active]
    assert max(sized) < 0.60, volatilities


def test_the_event_lane_fires_on_a_cascade_and_is_flat_otherwise(snapshot: Snapshot) -> None:
    """An event lane that never fires is indistinguishable from one that is broken."""
    strategy = strategy_from_module(load_strategy_module(f"{SEED_ROOT}/team-08/strategy.py"))
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=8,
        record_events=False,
    )
    returns = replay.costs[1].returns
    deployed = returns["gross_exposure"] >= 0.05
    assert float(returns["turnover"].sum()) > 0.0, "the shock lane never traded"
    assert 0.0 < float(deployed.mean()) < 0.90, "an event lane should be flat between events"
