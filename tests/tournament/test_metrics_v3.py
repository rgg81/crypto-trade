from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import metrics_v3


def _daily(values: list[float] | np.ndarray, start: str = "2024-01-01") -> pd.Series:
    return pd.Series(
        np.asarray(values, dtype=float),
        index=pd.date_range(start, periods=len(values), freq="1D", tz="UTC"),
    )


def test_v3_authorities_and_window_schema_are_local_and_frozen() -> None:
    assert metrics_v3.BOOTSTRAP_SEED == 20260718
    assert metrics_v3.REQUIRED_REGIMES == {"bull", "bear", "chop", "stress"}
    assert [field.name for field in dataclasses.fields(metrics_v3.WindowMetrics)] == [
        "net_sharpe",
        "net_sortino",
        "calmar",
        "annualized_return",
        "max_drawdown",
        "positive_quarter_fraction",
    ]
    packet = metrics_v3.WindowMetrics(1.0, 2.0, 3.0, 4.0, 0.1, 0.5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        packet.max_drawdown = 0.2  # type: ignore[misc]


def test_empty_inputs_have_exact_neutral_outputs() -> None:
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    assert metrics_v3.aggregate_daily_returns(empty).empty
    assert metrics_v3.compute_window_metrics(empty) == metrics_v3.WindowMetrics(
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    )
    regimes = metrics_v3.classify_btc_regimes(empty)
    assert regimes.empty and regimes.name == "regime"
    assert metrics_v3.compute_regime_sharpes(empty, regimes) == {
        "bear": 0.0,
        "bull": 0.0,
        "chop": 0.0,
        "stress": 0.0,
    }
    assert metrics_v3.sharpe_confidence_interval(empty) == (0.0, 0.0)
    assert metrics_v3.sharpe_confidence_interval(_daily([0.01])) == (0.0, 0.0)


def test_daily_aggregation_compounds_sorts_and_fills_calendar_gaps() -> None:
    bars = pd.Series(
        [0.02, -0.10, 0.10],
        index=pd.to_datetime(
            [
                "2024-01-03T00:00:00Z",
                "2024-01-01T08:00:00Z",
                "2024-01-01T00:00:00Z",
            ],
            utc=True,
        ),
    )
    result = metrics_v3.aggregate_daily_returns(bars)
    expected = pd.Series(
        [-0.01, 0.0, 0.02],
        index=pd.date_range("2024-01-01", periods=3, freq="1D", tz="UTC"),
        name="net_return",
    )
    pd.testing.assert_series_equal(result, expected, rtol=0.0, atol=1.0e-15)


def test_window_metrics_use_compounded_equity_and_peak_to_trough_drawdown() -> None:
    returns = _daily([0.10, -0.20, 0.05])
    result = metrics_v3.compute_window_metrics(returns)
    growth = 1.10 * 0.80 * 1.05
    annualized = growth ** (365 / 3) - 1.0
    downside = np.sqrt((0.0**2 + (-0.20) ** 2 + 0.0**2) / 3)
    expected_sharpe = np.sqrt(365) * returns.mean() / returns.std(ddof=1)
    expected_sortino = np.sqrt(365) * returns.mean() / downside

    assert result.net_sharpe == pytest.approx(expected_sharpe, abs=1.0e-14)
    assert result.net_sortino == pytest.approx(expected_sortino, abs=1.0e-14)
    assert result.annualized_return == pytest.approx(annualized, abs=1.0e-14)
    assert result.max_drawdown == pytest.approx(0.20, abs=1.0e-15)
    assert result.calmar == pytest.approx(annualized / 0.20, abs=1.0e-12)
    assert result.positive_quarter_fraction == 0.0


def test_btc_regimes_are_one_day_lagged_and_stress_has_precedence() -> None:
    values = np.full(62, 0.002, dtype=float)
    values[60] = -0.90
    values[61] = 0.0
    regimes = metrics_v3.classify_btc_regimes(_daily(values))

    assert regimes.iloc[:60].isna().all()
    # Day 60 sees only the preceding sixty positive days; its own crash is not used.
    assert regimes.iloc[60] == "bull"
    # The crash enters the lagged volatility window on the following day.
    assert regimes.iloc[61] == "stress"


def test_btc_regime_classifier_reaches_all_four_exclusive_buckets() -> None:
    bull = np.full(70, 0.003)
    chop = np.zeros(70)
    bear = np.full(70, -0.003)
    stress = np.resize(np.array([0.06, -0.06]), 70)
    regimes = metrics_v3.classify_btc_regimes(
        _daily(np.concatenate([bull, chop, bear, stress]))
    )

    selected = {
        regimes.iloc[61],
        regimes.iloc[139],
        regimes.iloc[201],
        regimes.iloc[271],
    }
    assert selected == metrics_v3.REQUIRED_REGIMES
    assert regimes.dropna().isin(metrics_v3.REQUIRED_REGIMES).all()


def test_regime_sharpes_use_fixed_buckets_and_zero_for_an_empty_bucket() -> None:
    returns = _daily([0.01, -0.005, 0.02, 0.01, -0.01, 0.005, 0.03, -0.02])
    labels = pd.Series(
        ["bear", "bear", "bull", "bull", "chop", "chop", "stress", "stress"],
        index=returns.index,
    )
    result = metrics_v3.compute_regime_sharpes(returns, labels)
    bull = returns.iloc[2:4]
    expected_bull = np.sqrt(365) * bull.mean() / bull.std(ddof=1)
    assert set(result) == metrics_v3.REQUIRED_REGIMES
    assert result["bull"] == pytest.approx(expected_bull, abs=1.0e-14)

    only_bull = metrics_v3.compute_regime_sharpes(
        returns.iloc[:2], pd.Series(["bull", "bull"], index=returns.index[:2])
    )
    assert only_bull["bear"] == 0.0
    assert only_bull["chop"] == 0.0
    assert only_bull["stress"] == 0.0


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf, -1.0, -1.01])
def test_every_return_entrypoint_rejects_nonfinite_or_total_losses(
    bad_value: float,
) -> None:
    returns = _daily([0.01, bad_value])
    labels = pd.Series(["chop", "chop"], index=returns.index)
    with pytest.raises(ValueError):
        metrics_v3.aggregate_daily_returns(returns)
    with pytest.raises(ValueError):
        metrics_v3.compute_window_metrics(returns)
    with pytest.raises(ValueError):
        metrics_v3.classify_btc_regimes(returns)
    with pytest.raises(ValueError):
        metrics_v3.compute_regime_sharpes(returns, labels)
    with pytest.raises(ValueError):
        metrics_v3.sharpe_confidence_interval(returns)


def test_circular_block_bootstrap_is_deterministic_and_seeded_for_v3() -> None:
    phase = np.arange(120, dtype=float)
    returns = _daily(0.0005 + 0.008 * np.sin(phase / 5.0))
    implicit = metrics_v3.sharpe_confidence_interval(returns, samples=250, block_days=7)
    repeated = metrics_v3.sharpe_confidence_interval(returns, samples=250, block_days=7)
    explicit = metrics_v3.sharpe_confidence_interval(
        returns,
        samples=250,
        block_days=7,
        seed=20260718,
    )
    alternate = metrics_v3.sharpe_confidence_interval(
        returns,
        samples=250,
        block_days=7,
        seed=1,
    )

    assert implicit == repeated == explicit
    assert implicit != alternate
    assert implicit[0] <= implicit[1]
    with pytest.raises(ValueError, match="at least 100"):
        metrics_v3.sharpe_confidence_interval(returns, samples=99)
    with pytest.raises(ValueError, match="positive block"):
        metrics_v3.sharpe_confidence_interval(returns, block_days=0)
