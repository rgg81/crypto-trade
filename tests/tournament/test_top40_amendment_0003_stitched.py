from __future__ import annotations

import csv
import io

import pandas as pd
import pytest

from crypto_trade.tournament import metrics_v3
from crypto_trade.tournament import top40_amendment_0003_stitched as stitched


def _daily_payload(values: list[float], start: str = "2020-02-03") -> bytes:
    index = pd.date_range(start, periods=len(values), freq="1D", tz="UTC")
    lines = ["date,net_return"]
    lines.extend(f"{day.date().isoformat()},{value}" for day, value in zip(index, values))
    return ("\n".join(lines) + "\n").encode("ascii")


def test_daily_series_accepts_exact_ordered_finite_grid() -> None:
    series = stitched._daily_series(_daily_payload([0.01, -0.02, 0.03]), "test")
    assert list(series) == [0.01, -0.02, 0.03]
    assert str(series.index.tz) == "UTC"


@pytest.mark.parametrize(
    "payload",
    [
        b"date,value\n2020-02-03,0.1\n",
        b"date,net_return\n2020-02-03,nan\n",
        b"date,net_return\n2020-02-03,-1.0\n",
        b"date,net_return\n2020-02-04,0.1\n2020-02-03,0.2\n",
    ],
)
def test_daily_series_fails_closed(payload: bytes) -> None:
    with pytest.raises(stitched.Amendment0003StitchedError):
        stitched._daily_series(payload, "test")


def test_trade_counts_partition_the_public_window() -> None:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["timestamp", "symbol"])
    writer.writeheader()
    writer.writerows(
        [
            {"timestamp": "2022-06-30T16:00:00Z", "symbol": "BTCUSDT"},
            {"timestamp": "2022-07-01T00:00:00Z", "symbol": "ETHUSDT"},
            {"timestamp": "2023-06-30T16:00:00Z", "symbol": "SOLUSDT"},
        ]
    )
    assert stitched._trade_counts(stream.getvalue().encode("utf-8")) == (1, 2, 3)


def test_trade_counts_reject_rows_outside_public_window() -> None:
    payload = b"timestamp,symbol\n2023-07-01T00:00:00Z,BTCUSDT\n"
    with pytest.raises(stitched.Amendment0003StitchedError):
        stitched._trade_counts(payload)


def test_metrics_mapping_uses_frozen_v3_algorithms() -> None:
    index = pd.date_range("2021-01-01", periods=365, freq="1D", tz="UTC")
    returns = pd.Series([0.001] * 365, index=index)
    stressed = pd.Series([0.0005] * 365, index=index)
    labels = pd.Series(
        (["bull"] * 100) + (["bear"] * 90) + (["chop"] * 90) + (["stress"] * 85),
        index=index,
    )
    observed = stitched._metrics_mapping(returns, stressed, labels, 1_234)
    canonical = metrics_v3.compute_window_metrics(returns)
    assert observed["net_sharpe"] == canonical.net_sharpe
    assert observed["annualized_return"] == canonical.annualized_return
    assert observed["trade_count"] == 1_234
    assert set(observed["regime_sharpe"]) == set(stitched.REGIMES)


def test_close_uses_tight_numerical_reproduction_tolerance() -> None:
    stitched._close(1.0, 1.0 + 1e-12, "metric")
    with pytest.raises(stitched.Amendment0003StitchedError):
        stitched._close(1.0, 1.001, "metric")


def test_canonical_record_hash_is_order_independent() -> None:
    assert stitched._sha256(stitched._canonical({"b": 2, "a": 1})) == stitched._sha256(
        stitched._canonical({"a": 1, "b": 2})
    )
