"""Signed-request timestamp correction under host clock drift.

Regression cover for the 2026-07-27 incident: the WSL host clock ran +1.34s AHEAD of Binance,
so every signed call returned -1021 ("Timestamp for this request was 1000ms ahead of the
server's time") while unsigned kline fetches kept working. The engine computed correct
rebalance plans and placed nothing. recvWindow cannot fix this — it only widens the tolerance
for timestamps that are BEHIND server time.

The correction is REACTIVE: sign with a cached offset (0 until proven otherwise) and re-sync
once if Binance rejects the timestamp. That keeps the happy path free of an extra round-trip.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from crypto_trade.live.auth_client import AuthenticatedBinanceClient

SERVER_NOW_MS = 1_785_000_000_000


def _build(monkeypatch, *, local_skew_ms: float):
    """Client whose local clock is `local_skew_ms` ahead of a Binance-rule-enforcing mock."""
    monkeypatch.setattr(
        "crypto_trade.live.auth_client.time.time",
        lambda: (SERVER_NOW_MS + local_skew_ms) / 1000.0,
    )
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/fapi/v1/time":
            return httpx.Response(200, json={"serverTime": SERVER_NOW_MS})
        ts = int(parse_qs(urlparse(str(request.url)).query)["timestamp"][0])
        recv = int(parse_qs(urlparse(str(request.url)).query)["recvWindow"][0])
        # Mirror BOTH of Binance's timestamp rules so the test fails the way production would.
        # Note both rejections carry code -1021 — the ahead-cliff is a fixed 1000ms and is NOT
        # widened by recvWindow, whereas the behind-tolerance IS recvWindow.
        if ts > SERVER_NOW_MS + 1000:
            return httpx.Response(
                400,
                json={
                    "code": -1021,
                    "msg": "Timestamp for this request was 1000ms ahead of the server's time.",
                },
            )
        if ts < SERVER_NOW_MS - recv:
            return httpx.Response(
                400,
                json={
                    "code": -1021,
                    "msg": "Timestamp for this request is outside of the recvWindow.",
                },
            )
        return httpx.Response(200, content=json.dumps({"ok": True}))

    client = AuthenticatedBinanceClient(
        api_key="k",
        api_secret="s",
        base_url="https://testnet.binancefuture.com",
        transport=httpx.MockTransport(handler),
    )
    return client, seen


def test_signed_call_recovers_from_host_clock_running_fast(monkeypatch):
    """+1.34s ahead — the exact skew that blocked trading — must succeed after one re-sync."""
    c, seen = _build(monkeypatch, local_skew_ms=1340)
    assert c.get_positions() == {"ok": True}
    assert c._time_offset_ms == pytest.approx(-1340, abs=5)
    # rejected attempt -> time probe -> successful retry
    assert [r.url.path for r in seen][-3:] == [
        "/fapi/v3/positionRisk",
        "/fapi/v1/time",
        "/fapi/v3/positionRisk",
    ]


def test_signed_call_recovers_from_host_clock_running_slow(monkeypatch):
    """Drift the OTHER way must also recover.

    Binance reports a too-old timestamp as -1021 as well ("outside of the recvWindow"), so the
    same re-sync path covers it. Live on 2026-07-29 the host was free-running and had drifted
    from +1.3s AHEAD to -0.4s BEHIND in ~2 days, heading for the -5000ms recvWindow floor — so
    this direction is a real trajectory, not a hypothetical.
    """
    c, seen = _build(monkeypatch, local_skew_ms=-9000)
    assert c.get_positions() == {"ok": True}
    assert c._time_offset_ms == pytest.approx(9000, abs=5)
    assert [r.url.path for r in seen][-3:] == [
        "/fapi/v3/positionRisk",
        "/fapi/v1/time",
        "/fapi/v3/positionRisk",
    ]


def test_no_extra_request_when_clock_is_healthy(monkeypatch):
    """The happy path must not pay a time-probe round-trip."""
    c, seen = _build(monkeypatch, local_skew_ms=0)
    assert c.get_positions() == {"ok": True}
    assert [r.url.path for r in seen] == ["/fapi/v3/positionRisk"]
    assert c._time_offset_ms == 0.0


def test_offset_is_reused_so_only_the_first_call_pays_for_it(monkeypatch):
    """Once learned, the offset applies to later calls without re-probing."""
    c, seen = _build(monkeypatch, local_skew_ms=1340)
    for _ in range(4):
        c.get_positions()
    assert sum(1 for r in seen if r.url.path == "/fapi/v1/time") == 1


def test_order_is_not_double_placed_on_timestamp_retry(monkeypatch):
    """A -1021 is rejected at the gateway before matching, so the retry must place exactly one."""
    c, seen = _build(monkeypatch, local_skew_ms=1340)
    c.place_market_order("BTCUSDT", "BUY", 1.0)
    orders = [r for r in seen if r.url.path == "/fapi/v1/order"]
    assert len(orders) == 2  # one rejected, one accepted
    accepted = parse_qs(urlparse(str(orders[-1].url)).query)
    assert int(accepted["timestamp"][0]) <= SERVER_NOW_MS + 1000


def test_persistently_bad_clock_raises_rather_than_looping(monkeypatch):
    """Only one retry: if the re-sync doesn't help, surface the error."""
    monkeypatch.setattr("crypto_trade.live.auth_client.time.time", lambda: SERVER_NOW_MS / 1000.0)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/fapi/v1/time":
            return httpx.Response(200, json={"serverTime": SERVER_NOW_MS})
        return httpx.Response(400, json={"code": -1021, "msg": "nope"})

    c = AuthenticatedBinanceClient(
        api_key="k",
        api_secret="s",
        base_url="https://testnet.binancefuture.com",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(httpx.HTTPStatusError):
        c.get_positions()


def test_time_probe_failure_does_not_mask_the_original_error(monkeypatch):
    """If /fapi/v1/time is unreachable, the -1021 must still surface, not a ConnectError."""
    monkeypatch.setattr("crypto_trade.live.auth_client.time.time", lambda: SERVER_NOW_MS / 1000.0)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/fapi/v1/time":
            raise httpx.ConnectError("boom")
        return httpx.Response(400, json={"code": -1021, "msg": "nope"})

    c = AuthenticatedBinanceClient(
        api_key="k",
        api_secret="s",
        base_url="https://testnet.binancefuture.com",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(httpx.HTTPStatusError):
        c.get_positions()
