from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_trade.cup50.config import OOS_END
from crypto_trade.cup50_desk.authority import WINNER_TEAM_ID, verify_lineage
from crypto_trade.cup50_desk.live_data import CacheGenerationError, current_generation
from crypto_trade.cup50_desk.schedule import ready_boundary
from crypto_trade.cup50_desk.tick import (
    _event_rows,
    _historical_stream,
    _return_rows,
    verify_historical_prefix,
)


def test_corrected_winner_lineage_is_team02() -> None:
    lineage = verify_lineage()
    assert lineage["authority"]["public_data_only"] is True
    assert lineage["reconstruction"]["winner_team_id"] == WINNER_TEAM_ID
    assert lineage["reconstruction"]["parity"] is True
    assert lineage["nomination"]["centre"] == {"lookback_bars": 189.0}


def test_ready_boundary_waits_for_own_bar_and_lag() -> None:
    assert ready_boundary("2026-08-18T08:24:59Z") == pd.Timestamp(
        "2026-08-17T16:00:00Z"
    )
    assert ready_boundary("2026-08-18T08:25:00Z") == pd.Timestamp(
        "2026-08-18T00:00:00Z"
    )


def test_unsafe_cache_pointer_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "CURRENT").write_text("../../elsewhere\n")
    with pytest.raises(CacheGenerationError, match="unsafe"):
        current_generation(tmp_path)


def test_funding_at_seam_is_historical_and_right_edge_belongs_to_interval() -> None:
    events = pd.DataFrame(
        [
            {
                "timestamp": OOS_END,
                "symbol": "BTCUSDT",
                "event_type": "funding",
                "notional": 1.0,
            },
            {
                "timestamp": OOS_END + pd.Timedelta(hours=8),
                "symbol": "BTCUSDT",
                "event_type": "funding",
                "notional": 2.0,
            },
        ]
    )
    result = _event_rows(
        SimpleNamespace(events=events), pd.Timestamp("2026-08-18T00:00:00Z")
    )
    assert result["notional"].tolist() == [2.0]
    assert result["phase"].tolist() == ["bridge"]


def test_terminal_return_is_withheld_until_the_following_tick() -> None:
    first = OOS_END
    second = first + pd.Timedelta(hours=8)
    returns = pd.DataFrame(
        {
            "right_boundary": [second, second + pd.Timedelta(hours=8)],
            "price_return": [0.01, 0.02],
            "funding_return": [0.0, 0.0],
            "gross_return": [0.01, 0.02],
            "fees_slippage": [0.001, 0.001],
            "net_return": [0.009, 0.019],
            "turnover": [0.1, 0.2],
            "gross_exposure": [0.3, 0.4],
            "equity": [100_900.0, 102_817.1],
        },
        index=pd.DatetimeIndex([first, second], name="decision_time"),
    )
    result = SimpleNamespace(returns=returns)

    at_second = _return_rows(result, first, second)
    assert at_second["decision_time"].tolist() == [first]

    later = _return_rows(result, first, second + pd.Timedelta(hours=8))
    assert later["decision_time"].tolist() == [first, second]


def test_terminal_events_are_withheld_until_the_following_tick() -> None:
    boundary = OOS_END + pd.Timedelta(hours=8)
    events = pd.DataFrame(
        [
            {
                "timestamp": boundary,
                "symbol": "BTCUSDT",
                "event_type": "trade",
                "notional": 1.0,
            },
            {
                "timestamp": boundary + pd.Timedelta(hours=8),
                "symbol": "BTCUSDT",
                "event_type": "funding",
                "notional": 2.0,
            },
        ]
    )
    result = _event_rows(SimpleNamespace(events=events), boundary, boundary)
    assert result["timestamp"].tolist() == [boundary]


def test_historical_prefix_is_exact_not_toleranced(tmp_path: Path) -> None:
    index = pd.DatetimeIndex([pd.Timestamp("2026-07-31T16:00:00Z")], name="decision_time")
    row = pd.DataFrame(
        {
            "right_boundary": [OOS_END],
            "price_return": [0.01],
            "funding_return": [0.0],
            "gross_return": [0.01],
            "fees_slippage": [0.001],
            "net_return": [0.009],
            "turnover": [0.1],
            "gross_exposure": [0.5],
            "equity": [100_900.0],
        },
        index=index,
    )
    replay = SimpleNamespace(
        costs={value: SimpleNamespace(returns=row.copy()) for value in (1, 2, 3)}
    )
    path = tmp_path / "prefix.parquet"
    _historical_stream(replay).to_parquet(path, index=False)
    verify_historical_prefix(replay, path)
    changed = pd.read_parquet(path)
    changed.loc[0, "net_return"] += 1e-15
    changed.to_parquet(path, index=False)
    with pytest.raises(Exception, match="historical prefix changed"):
        verify_historical_prefix(replay, path)


def test_runner_has_no_order_or_credential_path() -> None:
    source = Path("run_cup50_team02_paper.py").read_text().lower()
    forbidden = ("create_order", "new_order", "api_secret", "api_key", "/fapi/v1/order")
    assert not any(token in source for token in forbidden)
    assert "publicmarketdataclient" in source


def test_monitor_skill_is_installed_and_observe_only() -> None:
    skill = Path("/home/roberto/.codex/skills/cup50-team02-monitor/SKILL.md")
    text = skill.read_text()
    assert "name: cup50-team02-monitor" in text
    assert "Never flatten, hedge, resize, tune" in text
    interface = skill.parent / "agents" / "openai.yaml"
    payload = interface.read_text()
    assert "$cup50-team02-monitor" in payload


def test_authority_file_remains_digest_valid_json() -> None:
    authority = json.loads(Path("paper-cup50/team-02/authority.json").read_text())
    assert authority["namespace"] == "cup50-paper"
    assert authority["lineage_sha256"] == (
        "8dda00b28ae1888bd76e8207bfa1549bb3533e3b82a61c37b5ed41b3b9cad905"
    )
