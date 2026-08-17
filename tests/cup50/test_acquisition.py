from __future__ import annotations

import io
import zipfile

import pandas as pd

from crypto_trade.cup50.acquisition import _funding_archive_rows, _parse_funding


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
