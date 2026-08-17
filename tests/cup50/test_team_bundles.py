from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from crypto_trade.cup50.config import TEAM_IDS
from crypto_trade.cup50.neighbourhood import Dimension, generate_neighbourhood
from crypto_trade.cup50.protocol import DecisionContextV2
from crypto_trade.cup50.replay import load_strategy_module, strategy_from_module


def test_all_twelve_fresh_lane_entrypoints_are_loadable_and_bounded() -> None:
    now = pd.Timestamp("2026-01-01T00:00:00Z")
    periods = 600
    times = pd.date_range(end=now - pd.Timedelta(milliseconds=1), periods=periods, freq="8h")
    bars = pd.DataFrame(
        {
            "open_time": times - pd.Timedelta(hours=8) + pd.Timedelta(milliseconds=1),
            "close_time": times,
            "high": [101 + number * 0.01 for number in range(periods)],
            "low": [99 + number * 0.01 for number in range(periods)],
            "close": [100 + number * 0.01 for number in range(periods)],
            "quote_volume": [1_000_000.0] * periods,
            "taker_buy_quote_volume": [550_000.0] * periods,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": pd.date_range(end=now - pd.Timedelta(hours=8), periods=200, freq="8h"),
            "symbol": ["BTCUSDT"] * 200,
            "funding_rate": [0.0001] * 200,
            "mark_price": [100.0] * 200,
        }
    )
    context = DecisionContextV2(now, {"BTCUSDT": bars}, funding, {}, ("BTCUSDT",))
    for team_id in TEAM_IDS:
        source = Path("tournament/cup50/teams") / team_id / "strategy.py"
        strategy = strategy_from_module(load_strategy_module(source))
        target = strategy.target_weights(context, seed=0)
        assert target is None or isinstance(target, dict)
        if team_id == "team-11":
            assert target
        if target:
            assert set(target) <= {"BTCUSDT"}
            assert sum(abs(value) for value in target.values()) <= 1.0 + 1e-12


def test_team_sources_do_not_import_prior_tournament_namespaces() -> None:
    for source in Path("tournament/cup50/teams").glob("team-*/strategy.py"):
        text = source.read_text().lower()
        assert "cup20" not in text
        assert "top40" not in text


def test_preregistered_centres_match_strategy_attributes_and_have_seven_points() -> None:
    for team_id in TEAM_IDS:
        root = Path("tournament/cup50/teams") / team_id
        strategy = strategy_from_module(load_strategy_module(root / "strategy.py"))
        payload = json.loads((root / "parameters.json").read_text())
        dimensions = tuple(Dimension(**item) for item in payload["dimensions"])
        neighbourhood = generate_neighbourhood(payload["centre"], dimensions)
        assert len(neighbourhood.points) == 7
        for name, value in payload["centre"].items():
            assert getattr(strategy, name) == value
