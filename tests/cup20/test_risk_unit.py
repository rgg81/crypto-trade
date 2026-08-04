import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

BARS_PER_YEAR = 365 * 24 / 8


def _returns(count, sigma_per_bar, seed=0):
    index = pd.date_range("2020-01-01T00:00:00Z", periods=count, freq="8h")
    values = np.random.default_rng(seed).normal(0.0, sigma_per_bar, count)
    return pd.Series(values, index=index)


def test_scale_is_one_before_the_lookback_is_full():
    series = _returns(100, 0.01)
    decisions = [series.index[50]]
    scalars = common_risk_scalars(series, decisions, lookback_days=90)
    assert scalars.iloc[0] == 1.0


def test_scale_targets_ten_percent_annualised_volatility():
    sigma_per_bar = 0.30 / math.sqrt(BARS_PER_YEAR)
    series = _returns(600, sigma_per_bar, seed=7)
    decision = series.index[-1] + pd.Timedelta(hours=8)
    scalars = common_risk_scalars(series, [decision], lookback_days=90)
    realized = series.iloc[-270:].std(ddof=1) * math.sqrt(BARS_PER_YEAR)
    assert scalars.iloc[0] == pytest.approx(0.10 / realized)


def test_scale_is_clamped_to_the_declared_band():
    calm = pd.Series(
        np.full(400, 1e-9), index=pd.date_range("2020-01-01T00:00:00Z", periods=400, freq="8h")
    )
    decision = calm.index[-1] + pd.Timedelta(hours=8)
    assert common_risk_scalars(calm, [decision]).iloc[0] == 3.0

    wild = _returns(400, 0.5, seed=3)
    decision = wild.index[-1] + pd.Timedelta(hours=8)
    assert common_risk_scalars(wild, [decision]).iloc[0] == 0.20


def test_scalar_uses_only_returns_strictly_before_the_decision():
    series = _returns(400, 0.01, seed=11)
    decision = series.index[350]
    baseline = common_risk_scalars(series, [decision]).iloc[0]
    corrupted = series.copy()
    corrupted.iloc[350:] = 10.0
    assert common_risk_scalars(corrupted, [decision]).iloc[0] == baseline


def test_scale_transitions_from_fallback_to_real_computation_at_required_length():
    target_annualized_volatility = 0.10
    lookback_days = 90
    interval_hours = 8
    bars_per_year = 365 * 24 / interval_hours
    required = max(2, math.ceil(lookback_days * 24 / interval_hours))
    series = _returns(required + 1, 0.01, seed=13)

    short_decision = series.index[required - 1]
    scalars_short = common_risk_scalars(
        series,
        [short_decision],
        target_annualized_volatility=target_annualized_volatility,
        lookback_days=lookback_days,
        interval_hours=interval_hours,
    )
    assert scalars_short.iloc[0] == 1.0

    full_decision = series.index[required]
    scalars_full = common_risk_scalars(
        series,
        [full_decision],
        target_annualized_volatility=target_annualized_volatility,
        lookback_days=lookback_days,
        interval_hours=interval_hours,
    )
    realized = series.iloc[:required].std(ddof=1) * math.sqrt(bars_per_year)
    assert scalars_full.iloc[0] == pytest.approx(target_annualized_volatility / realized)


def test_common_risk_scalars_rejects_non_positive_target_annualized_volatility():
    series = _returns(10, 0.01)
    decision = [series.index[5]]
    with pytest.raises(ValueError):
        common_risk_scalars(series, decision, target_annualized_volatility=0.0)
    with pytest.raises(ValueError):
        common_risk_scalars(series, decision, target_annualized_volatility=-0.1)


def test_common_risk_scalars_rejects_nan_target_annualized_volatility():
    series = _returns(10, 0.01)
    decision = [series.index[5]]
    with pytest.raises(ValueError):
        common_risk_scalars(series, decision, target_annualized_volatility=float("nan"))


def test_common_risk_scalars_rejects_invalid_scale_band():
    series = _returns(10, 0.01)
    decision = [series.index[5]]
    with pytest.raises(ValueError):
        common_risk_scalars(series, decision, minimum_scale=0.0, maximum_scale=3.0)
    with pytest.raises(ValueError):
        common_risk_scalars(series, decision, minimum_scale=3.0, maximum_scale=0.20)


def test_common_risk_scalars_rejects_tz_naive_gross_returns_index():
    naive_index = pd.date_range("2020-01-01T00:00:00", periods=10, freq="8h")
    series = pd.Series(np.full(10, 0.01), index=naive_index)
    with pytest.raises(ValueError):
        common_risk_scalars(series, [pd.Timestamp("2020-01-05T00:00:00Z")])


def test_common_risk_scalars_rejects_tz_naive_decision_time():
    series = _returns(10, 0.01)
    with pytest.raises(ValueError):
        common_risk_scalars(series, [pd.Timestamp("2020-01-05T00:00:00")])


def test_common_risk_scalars_rejects_non_finite_values_inside_the_causal_window():
    values = np.full(300, 0.01)
    values[100] = np.nan
    series = pd.Series(values, index=pd.date_range("2020-01-01T00:00:00Z", periods=300, freq="8h"))
    decision = series.index[-1] + pd.Timedelta(hours=8)
    with pytest.raises(ValueError):
        common_risk_scalars(series, [decision])


def test_apply_risk_scalars_leaves_the_instruction_column_untouched():
    index = pd.date_range("2020-01-01T00:00:00Z", periods=2, freq="8h")
    targets = pd.DataFrame(
        {"AUSDT": [0.5, -0.5], "BUSDT": [-0.5, 0.5], REBALANCE_INSTRUCTION_COLUMN: [True, False]},
        index=index,
    )
    scaled = apply_risk_scalars(targets, pd.Series([0.5, 2.0], index=index))
    assert scaled["AUSDT"].tolist() == [0.25, -1.0]
    assert scaled[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, False]


def test_apply_risk_scalars_requires_matching_index():
    index = pd.date_range("2020-01-01T00:00:00Z", periods=2, freq="8h")
    targets = pd.DataFrame({"AUSDT": [0.5, -0.5]}, index=index)
    with pytest.raises(ValueError):
        apply_risk_scalars(targets, pd.Series([0.5], index=index[:1]))
