from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.cup50v2.config import TEAM_IDS
from crypto_trade.cup50v2.neighbourhood import Dimension, generate_neighbourhood
from crypto_trade.cup50v2.protocol import DecisionContextV2
from crypto_trade.cup50v2.replay import load_strategy_module, strategy_from_module

SEED_ROOT = Path("tournament/cup50v2/seeds")
PRIOR_NAMESPACE = re.compile(r"cup20|top40|cup50(?!v2)")

pytestmark = pytest.mark.skipif(
    not SEED_ROOT.is_dir(),
    reason="organizer lane seeds are written in the policy-artifact phase",
)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT", "AVAXUSDT")


def _context(symbols: tuple[str, ...] = SYMBOLS) -> DecisionContextV2:
    """A causal, multi-symbol context wide enough for every declared centre lookback."""
    now = pd.Timestamp("2026-01-01T00:00:00Z")
    periods = 1200
    close_times = pd.date_range(end=now - pd.Timedelta(milliseconds=1), periods=periods, freq="8h")
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        drift = 1.0 + 0.0005 * (index + 1)
        close = pd.Series([100.0 * drift**step for step in range(periods)])
        bars[symbol] = pd.DataFrame(
            {
                "open_time": close_times - pd.Timedelta(hours=8) + pd.Timedelta(milliseconds=1),
                "close_time": close_times,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "volume": [1_000.0 + index] * periods,
                "quote_volume": [1_000_000.0 * (index + 1)] * periods,
                "trade_count": [10_000 + index] * periods,
                "taker_buy_volume": [500.0 + index] * periods,
                "taker_buy_quote_volume": [520_000.0 * (index + 1)] * periods,
            }
        )
    funding_times = pd.date_range(end=now - pd.Timedelta(hours=8), periods=600, freq="8h")
    funding = pd.concat(
        [
            pd.DataFrame(
                {
                    "funding_time": funding_times,
                    "symbol": symbol,
                    "funding_rate": 0.0001 * (index + 1),
                    "funding_interval_hours": 8.0,
                }
            )
            for index, symbol in enumerate(symbols)
        ],
        ignore_index=True,
    )
    return DecisionContextV2(now, bars, funding, {}, symbols)


def _expected_points(dimensions: int) -> int:
    """The frozen CUP-50 v2 neighbourhood cardinality."""
    return 7 if dimensions <= 1 else 1 + 4 * dimensions


def test_all_twelve_lane_seeds_are_loadable_and_bounded() -> None:
    context = _context()
    for team_id in TEAM_IDS:
        strategy = strategy_from_module(load_strategy_module(SEED_ROOT / team_id / "strategy.py"))
        target = strategy.target_weights(context, seed=0)
        assert target is None or isinstance(target, dict), team_id
        if target:
            assert set(target) <= set(SYMBOLS), team_id
            assert sum(abs(value) for value in target.values()) <= 1.0 + 1e-12, team_id


def test_lane_seeds_degrade_gracefully_on_a_thin_cross_section() -> None:
    """A one-symbol roster must not raise; the evaluator would score that a candidate failure."""
    context = _context(("BTCUSDT",))
    for team_id in TEAM_IDS:
        strategy = strategy_from_module(load_strategy_module(SEED_ROOT / team_id / "strategy.py"))
        target = strategy.target_weights(context, seed=0)
        assert target is None or isinstance(target, dict), team_id
        if target:
            assert set(target) <= {"BTCUSDT"}, team_id
            assert sum(abs(value) for value in target.values()) <= 1.0 + 1e-12, team_id


def test_lane_seeds_do_not_reference_a_prior_tournament_namespace() -> None:
    sources = sorted(SEED_ROOT.glob("team-*/strategy.py"))
    assert len(sources) == len(TEAM_IDS)
    for source in sources:
        assert not PRIOR_NAMESPACE.search(source.read_text().lower()), source


def test_preregistered_centres_match_seed_attributes_and_declared_geometry() -> None:
    for team_id in TEAM_IDS:
        root = SEED_ROOT / team_id
        strategy = strategy_from_module(load_strategy_module(root / "strategy.py"))
        payload = json.loads((root / "parameters.json").read_text())
        dimensions = tuple(Dimension(**item) for item in payload["dimensions"])
        assert 1 <= len(dimensions) <= 5, team_id
        neighbourhood = generate_neighbourhood(payload["centre"], dimensions)
        assert len(neighbourhood.points) == _expected_points(len(dimensions)), team_id
        for name, value in payload["centre"].items():
            assert getattr(strategy, name) == value, (team_id, name)
