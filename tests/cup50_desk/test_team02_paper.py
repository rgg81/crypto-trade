from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from crypto_trade.cup20_desk.live_data import (
    EXCHANGE_INFO_ENDPOINT,
    FUNDING_RATE_ENDPOINT,
    KLINES_ENDPOINT,
    MARK_PRICE_KLINES_ENDPOINT,
    AppendInvarianceError,
    BinancePublicDataError,
    PublicMarketDataClient,
    append_frame,
    conform_frame,
)
from crypto_trade.cup50.config import OOS_END
from crypto_trade.cup50_desk.authority import WINNER_TEAM_ID, verify_lineage
from crypto_trade.cup50_desk.live_data import (
    PERPETUAL_DELIVERY_SENTINEL,
    CacheGenerationError,
    _defer_announced_delivery_dates,
    current_generation,
)
from crypto_trade.cup50_desk.schedule import ready_boundary
from crypto_trade.cup50_desk.snapshot_forward import _causal_reconstitution_times
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


def test_forward_reconstitution_times_never_include_tomorrow() -> None:
    sunday = pd.Timestamp("2026-08-23T08:00:00Z")
    boundaries = _causal_reconstitution_times(sunday)

    assert boundaries[-1] == pd.Timestamp("2026-08-17T00:00:00Z")
    assert pd.Timestamp("2026-08-24T00:00:00Z") not in boundaries
    assert all(boundary <= sunday for boundary in boundaries)


def test_monday_reconstitution_first_appears_at_monday_decision() -> None:
    monday = pd.Timestamp("2026-08-24T00:00:00Z")

    assert _causal_reconstitution_times(monday)[-1] == monday


def test_only_transaction_klines_are_routed_through_proxy() -> None:
    urls: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(request.url)
        return httpx.Response(200, json=[])

    with PublicMarketDataClient(
        base_url="https://direct.example",
        klines_base_url="http://proxy.example:8000",
        pause_seconds=0,
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    ) as client:
        for endpoint in (
            KLINES_ENDPOINT,
            MARK_PRICE_KLINES_ENDPOINT,
            FUNDING_RATE_ENDPOINT,
            EXCHANGE_INFO_ENDPOINT,
        ):
            assert client.get_json(endpoint) == []

    assert [url.host for url in urls] == [
        "proxy.example",
        "direct.example",
        "direct.example",
        "direct.example",
    ]
    assert [url.path for url in urls] == [
        KLINES_ENDPOINT,
        MARK_PRICE_KLINES_ENDPOINT,
        FUNDING_RATE_ENDPOINT,
        EXCHANGE_INFO_ENDPOINT,
    ]


def test_proxy_failure_never_falls_back_to_direct_klines() -> None:
    urls: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(request.url)
        return httpx.Response(503, headers={"Retry-After": "1"}, json={"code": -1003})

    with PublicMarketDataClient(
        base_url="https://direct.example",
        klines_base_url="http://proxy.example:8000",
        pause_seconds=0,
        max_attempts=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    ) as client:
        with pytest.raises(BinancePublicDataError, match="exhausted retries"):
            client.get_json(KLINES_ENDPOINT)

    assert len(urls) == 1
    assert urls[0].host == "proxy.example"


def test_unsafe_cache_pointer_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "CURRENT").write_text("../../elsewhere\n")
    with pytest.raises(CacheGenerationError, match="unsafe"):
        current_generation(tmp_path)


def _current_contract(delivery_date: pd.Timestamp = PERPETUAL_DELIVERY_SENTINEL) -> pd.DataFrame:
    return conform_frame(
        "contract_metadata",
        pd.DataFrame(
            [
                {
                    "symbol": "ICXUSDT",
                    "contract_type": "PERPETUAL",
                    "quote_asset": "USDT",
                    "margin_asset": "USDT",
                    "is_crypto": True,
                    "onboard_date": pd.Timestamp("2020-01-01T00:00:00Z"),
                    "delivery_date": delivery_date,
                    "underlying_type": "COIN",
                    "metadata_source": "current_exchangeInfo",
                }
            ]
        ),
    )


def test_future_delivery_announcement_is_deferred_and_audited(tmp_path: Path) -> None:
    path = tmp_path / "contract_metadata.parquet"
    recorded = _current_contract()
    append_frame(path, recorded, name="contract_metadata")
    before = path.read_bytes()
    announced = pd.Timestamp("2026-08-26T09:00:00Z")

    normalized, observations = _defer_announced_delivery_dates(
        tmp_path,
        _current_contract(announced),
        observed_at=pd.Timestamp("2026-08-20T08:00:00Z"),
    )
    result = append_frame(path, normalized, name="contract_metadata")

    assert (result.appended, result.unchanged, result.transitioned) == (0, 1, 0)
    assert path.read_bytes() == before
    assert normalized.iloc[0]["delivery_date"] == PERPETUAL_DELIVERY_SENTINEL
    assert observations == (
        {
            "symbol": "ICXUSDT",
            "field": "delivery_date",
            "recorded_value": PERPETUAL_DELIVERY_SENTINEL.isoformat(),
            "observed_value": announced.isoformat(),
            "observed_at": "2026-08-20T08:00:00+00:00",
            "disposition": "deferred_until_delisting_transition",
        },
    )


def test_past_delivery_revision_still_aborts(tmp_path: Path) -> None:
    path = tmp_path / "contract_metadata.parquet"
    append_frame(path, _current_contract(), name="contract_metadata")
    revised = _current_contract(pd.Timestamp("2026-08-19T09:00:00Z"))

    normalized, observations = _defer_announced_delivery_dates(
        tmp_path,
        revised,
        observed_at=pd.Timestamp("2026-08-20T08:00:00Z"),
    )

    assert observations == ()
    with pytest.raises(AppendInvarianceError, match="delivery_date"):
        append_frame(path, normalized, name="contract_metadata")


def test_delivery_deferral_does_not_hide_identity_change(tmp_path: Path) -> None:
    path = tmp_path / "contract_metadata.parquet"
    append_frame(path, _current_contract(), name="contract_metadata")
    announced = _current_contract(pd.Timestamp("2026-08-26T09:00:00Z"))
    announced.loc[0, "quote_asset"] = "USDC"

    normalized, observations = _defer_announced_delivery_dates(
        tmp_path,
        announced,
        observed_at=pd.Timestamp("2026-08-20T08:00:00Z"),
    )

    assert len(observations) == 1
    with pytest.raises(AppendInvarianceError, match="quote_asset"):
        append_frame(path, normalized, name="contract_metadata")


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
    assert 'klines_proxy_base_url = "http://127.0.0.1:8000"' in source
    assert "publicmarketdataclient(klines_base_url=klines_proxy_base_url)" in source


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
