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
