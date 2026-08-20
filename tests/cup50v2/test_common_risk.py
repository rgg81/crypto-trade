from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.common_risk import common_risk_scalars


def test_common_risk_uses_only_strictly_earlier_returns() -> None:
    times = pd.date_range("2024-01-01", periods=272, freq="8h", tz="UTC")
    returns = pd.Series(np.linspace(-0.01, 0.01, len(times)), index=times)
    decision = times[-1]
    expected = common_risk_scalars(returns, [decision])

    corrupted = returns.copy()
    corrupted.loc[decision] = 1_000.0
    observed = common_risk_scalars(corrupted, [decision])

    pd.testing.assert_series_equal(observed, expected)


def test_common_risk_requires_utc_and_finite_window() -> None:
    naive = pd.Series([0.0, 0.1], index=pd.date_range("2024-01-01", periods=2, freq="8h"))
    with pytest.raises(ValueError, match="timezone-aware"):
        common_risk_scalars(naive, [pd.Timestamp("2024-01-02", tz="UTC")])

    times = pd.date_range("2024-01-01", periods=271, freq="8h", tz="UTC")
    nonfinite = pd.Series(0.0, index=times)
    nonfinite.iloc[-1] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        common_risk_scalars(nonfinite, [times[-1] + pd.Timedelta(hours=8)])


def test_common_risk_clamps_scale_and_warmup_is_one() -> None:
    times = pd.date_range("2024-01-01", periods=271, freq="8h", tz="UTC")
    flat = pd.Series(0.0, index=times)
    decisions = [times[1], times[-1] + pd.Timedelta(hours=8)]

    result = common_risk_scalars(flat, decisions)

    assert result.iloc[0] == 1.0
    assert result.iloc[1] == 3.0
