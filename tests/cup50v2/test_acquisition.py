from __future__ import annotations

import io
import zipfile

import pandas as pd

from crypto_trade.cup50v2.acquisition import (
    _execution_gaps,
    _funding_archive_rows,
    _parse_funding,
)


def _archive(text: str) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as bundle:
        bundle.writestr("funding.csv", text)
    return output.getvalue()


def test_monthly_funding_archive_joins_canonical_mark_and_right_interval() -> None:
    decision = pd.Timestamp("2022-11-14T00:00:00Z")
    settlement = decision + pd.Timedelta(hours=8)
    rows, covered = _funding_archive_rows(
        _archive(
            "calc_time,funding_interval_hours,last_funding_rate\n"
            f"{int(settlement.value // 1_000_000) + 15},8,0.0001\n"
        ),
        symbol="LITUSDT",
        required={decision},
        mark_prices={(settlement, "LITUSDT"): 0.75},
    )
    assert covered == {decision}
    assert rows[0]["funding_time"] == settlement + pd.Timedelta(milliseconds=15)
    assert rows[0]["settlement_time"] == settlement
    assert rows[0]["mark_price"] == 0.75


def test_monthly_funding_archive_keeps_multiple_settlements_in_one_interval() -> None:
    decision = pd.Timestamp("2025-12-23T16:00:00Z")
    first = decision + pd.Timedelta(hours=4)
    second = decision + pd.Timedelta(hours=8)
    rows, covered = _funding_archive_rows(
        _archive(
            "calc_time,funding_interval_hours,last_funding_rate\n"
            f"{int(first.value // 1_000_000) + 5},4,0.0001\n"
            f"{int(second.value // 1_000_000) + 5},4,0.0002\n"
        ),
        symbol="LITUSDT",
        required={decision},
        mark_prices={(first, "LITUSDT"): 0.75, (second, "LITUSDT"): 0.80},
    )

    assert covered == {decision}
    assert [row["settlement_time"] for row in rows] == [first, second]


def test_monthly_funding_archive_proves_zero_event_interval() -> None:
    decision = pd.Timestamp("2025-11-06T08:00:00Z")
    rows, covered = _funding_archive_rows(
        _archive("calc_time,funding_interval_hours,last_funding_rate\n"),
        symbol="AI16ZUSDT",
        required={decision},
        mark_prices={},
    )

    assert rows == []
    assert covered == {decision}


def test_funding_rest_blank_mark_uses_checksum_bound_mark() -> None:
    settlement = pd.Timestamp("2022-01-17T08:00:00Z")
    timestamp = int(settlement.value // 1_000_000) + 5
    rows = _parse_funding(
        [
            {
                "symbol": "TLMUSDT",
                "fundingTime": timestamp,
                "fundingRate": "0.0001",
                "markPrice": "",
            }
        ],
        symbol="TLMUSDT",
        lower_ms=timestamp - 1,
        upper_ms=timestamp + 1,
        mark_prices={(settlement, "TLMUSDT"): 0.12},
    )
    assert rows[0]["mark_price"] == 0.12
    assert rows[0]["settlement_time"] == settlement


def test_execution_coverage_follows_active_archives_after_membership_exit() -> None:
    start = pd.Timestamp("2024-01-08T00:00:00Z")
    terminal = start + pd.Timedelta(hours=16)
    decisions = [start, start + pd.Timedelta(hours=8)]
    bars = pd.DataFrame(
        [
            {
                "open_time": decision,
                "symbol": symbol,
                "quote_volume": 1_000_000.0,
                "trade_count": 100,
            }
            for decision in decisions
            for symbol in ("AUSDT", "BUSDT")
        ]
    )
    marks = pd.DataFrame(
        [{"mark_time": decision, "symbol": "AUSDT"} for decision in decisions]
        + [{"mark_time": terminal, "symbol": "AUSDT"}]
    )
    funding = pd.DataFrame(
        [
            {
                "funding_time": decision + pd.Timedelta(hours=8),
                "settlement_time": decision + pd.Timedelta(hours=8),
                "symbol": "AUSDT",
                "funding_rate": 0.0,
                "mark_price": 1.0,
            }
            for decision in decisions
        ]
    )
    membership = pd.DataFrame(
        [
            {
                "reconstitution_time": start - pd.Timedelta(days=7),
                "symbol": "BUSDT",
                "liquidity_rank": 1,
            },
            {"reconstitution_time": start, "symbol": "AUSDT", "liquidity_rank": 1},
        ]
    )

    bar_gaps, mark_gaps, funding_gaps = _execution_gaps(
        bars=bars,
        marks=marks,
        funding=funding,
        membership=membership,
        start=start,
        terminal=terminal,
    )

    assert bar_gaps == []
    mark_gap_set = set(mark_gaps)
    assert (start, "BUSDT") in mark_gap_set
    assert (start + pd.Timedelta(hours=4), "AUSDT") in mark_gap_set
    assert (start + pd.Timedelta(hours=4), "BUSDT") in mark_gap_set
    assert (start + pd.Timedelta(hours=8), "BUSDT") in mark_gap_set
    assert (terminal, "BUSDT") in mark_gap_set
    assert funding_gaps == [
        (start, "BUSDT"),
        (start + pd.Timedelta(hours=8), "BUSDT"),
    ]
