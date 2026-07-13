from __future__ import annotations

import pandas as pd

from crypto_trade.tournament.data import (
    eligible_at,
    is_eligible_usdt_perpetual,
    point_in_time_top40,
)


def _bars(days: int = 35) -> pd.DataFrame:
    rows = []
    for date in pd.date_range("2024-01-01", periods=days, freq="D", tz="UTC"):
        for offset in (0, 8, 16):
            timestamp = date + pd.Timedelta(hours=offset)
            rows.extend(
                [
                    {"open_time": timestamp, "symbol": "AAAUSDT", "quote_volume": 200.0},
                    {"open_time": timestamp, "symbol": "BBBUSDT", "quote_volume": 100.0},
                    {
                        "open_time": timestamp,
                        "symbol": "USDCUSDT",
                        "quote_volume": 1_000_000.0,
                    },
                ]
            )
    return pd.DataFrame(rows)


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["AAAUSDT", "BBBUSDT", "USDCUSDT"],
            "contract_type": ["PERPETUAL"] * 3,
            "quote_asset": ["USDT"] * 3,
            "margin_asset": ["USDT"] * 3,
            "is_crypto": [True] * 3,
            "onboard_date": ["2020-01-01"] * 3,
            "delivery_date": [None] * 3,
        }
    )


def test_point_in_time_top40_is_past_only_and_excludes_stablecoin_base():
    as_of = pd.Timestamp("2024-02-05", tz="UTC")
    bars = _bars()
    original = point_in_time_top40(bars, _metadata(), [as_of], top_n=2)
    future = pd.concat(
        [
            bars,
            pd.DataFrame(
                [
                    {
                        "open_time": pd.Timestamp("2024-02-06", tz="UTC"),
                        "symbol": "BBBUSDT",
                        "quote_volume": 1e12,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    perturbed = point_in_time_top40(future, _metadata(), [as_of], top_n=2)
    pd.testing.assert_frame_equal(original, perturbed)
    assert list(original["symbol"]) == ["AAAUSDT", "BBBUSDT"]


def test_eligible_at_uses_latest_past_reconstitution_only():
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-08"], utc=True
            ),
            "symbol": ["AAAUSDT", "BBBUSDT", "CCCUSDT"],
            "liquidity_rank": [1, 2, 1],
            "trailing_quote_volume": [2.0, 1.0, 3.0],
        }
    )
    assert eligible_at(membership, pd.Timestamp("2024-01-07", tz="UTC")) == (
        "AAAUSDT",
        "BBBUSDT",
    )
    assert eligible_at(membership, pd.Timestamp("2024-01-09", tz="UTC")) == ("CCCUSDT",)


def test_symbol_filter_uses_exact_leveraged_names_not_legitimate_suffixes():
    assert not is_eligible_usdt_perpetual("BTCUPUSDT")
    assert not is_eligible_usdt_perpetual("USTCUSDT")
    assert not is_eligible_usdt_perpetual("PAXGUSDT")
    assert not is_eligible_usdt_perpetual("XAUTUSDT")
    assert is_eligible_usdt_perpetual("JUPUSDT")
    assert is_eligible_usdt_perpetual("SYRUPUSDT")
