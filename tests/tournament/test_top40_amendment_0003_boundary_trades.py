from __future__ import annotations

import csv
import io

import pytest

from crypto_trade.tournament import top40_amendment_0003_boundary_trades as boundary


def _payload(timestamps: list[str]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["timestamp", "symbol"])
    writer.writeheader()
    for timestamp in timestamps:
        writer.writerow({"timestamp": timestamp, "symbol": "BTCUSDT"})
    return stream.getvalue().encode("utf-8")


def test_scored_trade_counts_excludes_exact_end_boundary() -> None:
    payload = _payload(
        [
            "2022-06-30T16:00:00Z",
            "2022-07-01T00:00:00Z",
            "2023-06-30T16:00:00Z",
            "2023-07-01T00:00:00Z",
        ]
    )
    assert boundary._scored_trade_counts(payload) == (1, 2, 3)


def test_scored_trade_counts_accepts_multiple_terminal_settlements() -> None:
    payload = _payload(["2023-07-01T00:00:00Z"] * 10)
    assert boundary._scored_trade_counts(payload) == (0, 0, 0)


def test_scored_trade_counts_rejects_after_end_boundary() -> None:
    with pytest.raises(boundary.BoundaryTradeAddendumError):
        boundary._scored_trade_counts(_payload(["2023-07-01T00:00:01Z"]))


def test_scored_trade_counts_rejects_before_public_start() -> None:
    with pytest.raises(boundary.BoundaryTradeAddendumError):
        boundary._scored_trade_counts(_payload(["2020-02-02T23:59:59Z"]))


def test_scored_trade_counts_rejects_missing_timestamp() -> None:
    with pytest.raises(boundary.BoundaryTradeAddendumError):
        boundary._scored_trade_counts(b"symbol\nBTCUSDT\n")


def test_boundary_canonical_hash_is_order_independent() -> None:
    assert boundary._sha256(
        boundary._canonical({"b": 2, "a": 1})
    ) == boundary._sha256(boundary._canonical({"a": 1, "b": 2}))
