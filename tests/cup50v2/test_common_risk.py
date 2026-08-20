"""The common risk unit is the only thing that makes two lanes comparable.

CUP-50 scaled by the book's own *realised* volatility over the trailing ninety days, which is a
backward-looking measure of a book that has since changed.  Its winner ran at 23% annualised against
a 10% target because it sat flat half the time and then concentrated: the realised series it was
scaled by never described the position it actually held.  CUP-50 v2 prices the book it is about to
hold, from the covariance of the names in it.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.common_risk import BARS_PER_YEAR, exante_risk_scalars
from crypto_trade.cup50v2.replay import REBALANCE_COLUMN, ExecutionConfig

CONFIG = ExecutionConfig()


def _bars(symbols: dict[str, float], periods: int = 600, seed: int = 7) -> pd.DataFrame:
    """Independent lognormal paths with a per-symbol 8h volatility."""
    generator = np.random.default_rng(seed)
    open_times = pd.date_range("2023-01-01", periods=periods, freq="8h", tz="UTC")
    frames = []
    for symbol, sigma in symbols.items():
        steps = generator.normal(0.0, sigma, size=periods)
        close = 100.0 * np.exp(np.cumsum(steps))
        frames.append(
            pd.DataFrame(
                {
                    "open_time": open_times,
                    "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "symbol": symbol,
                    "close": close,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _targets(rows: dict[pd.Timestamp, dict[str, float]], symbols: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(0.0, index=pd.DatetimeIndex(list(rows)), columns=[*symbols])
    for decision, weights in rows.items():
        for symbol, weight in weights.items():
            frame.loc[decision, symbol] = weight
    frame[REBALANCE_COLUMN] = True
    return frame


def test_a_book_of_known_volatility_is_scaled_to_the_target() -> None:
    """The point of the unit: a book twice as volatile gets half the size."""
    sigma = 0.02
    bars = _bars({"AUSDT": sigma})
    decisions = pd.DatetimeIndex(["2023-06-01T00:00:00Z"])
    targets = _targets({decisions[0]: {"AUSDT": 1.0}}, ["AUSDT"])

    scalar = float(exante_risk_scalars(targets, bars=bars, config=CONFIG).iloc[0])

    realised = sigma * math.sqrt(BARS_PER_YEAR)
    assert scalar == pytest.approx(CONFIG.risk_target / realised, rel=0.25)
    assert 0.10 <= scalar <= 3.0


def test_the_scaled_book_lands_within_a_fifth_of_the_target_volatility() -> None:
    bars = _bars({"AUSDT": 0.015, "BUSDT": 0.03, "CUSDT": 0.008})
    panel = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    weights = {"AUSDT": 0.5, "BUSDT": -0.3, "CUSDT": 0.2}
    decision = pd.Timestamp("2023-08-01T00:00:00Z")
    targets = _targets({decision: weights}, list(weights))

    scalar = float(exante_risk_scalars(targets, bars=bars, config=CONFIG).iloc[0])

    returns = panel.pct_change().loc[panel.index < decision].tail(270)
    book = sum(weight * returns[symbol] for symbol, weight in weights.items())
    achieved = float(book.std(ddof=1)) * math.sqrt(BARS_PER_YEAR) * scalar
    assert achieved == pytest.approx(CONFIG.risk_target, rel=0.20)


def test_diversification_is_priced_so_a_hedged_book_may_grow() -> None:
    """A long/short pair in one correlated name is nearly riskless and must be sized up."""
    open_times = pd.date_range("2023-01-01", periods=600, freq="8h", tz="UTC")
    generator = np.random.default_rng(3)
    common = np.cumsum(generator.normal(0.0, 0.02, size=600))
    bars = pd.concat(
        [
            pd.DataFrame(
                {
                    "open_time": open_times,
                    "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "symbol": symbol,
                    "close": 100.0 * np.exp(common),
                }
            )
            for symbol in ("AUSDT", "BUSDT")
        ],
        ignore_index=True,
    )
    decision = pd.Timestamp("2023-06-01T00:00:00Z")
    hedged = _targets({decision: {"AUSDT": 0.5, "BUSDT": -0.5}}, ["AUSDT", "BUSDT"])
    outright = _targets({decision: {"AUSDT": 0.5, "BUSDT": 0.5}}, ["AUSDT", "BUSDT"])

    hedged_scalar = float(exante_risk_scalars(hedged, bars=bars, config=CONFIG).iloc[0])
    outright_scalar = float(exante_risk_scalars(outright, bars=bars, config=CONFIG).iloc[0])

    assert hedged_scalar > outright_scalar
    assert hedged_scalar == CONFIG.risk_maximum_scale


def test_only_bars_that_closed_before_the_decision_are_used() -> None:
    bars = _bars({"AUSDT": 0.02})
    decision = pd.Timestamp("2023-06-01T00:00:00Z")
    targets = _targets({decision: {"AUSDT": 1.0}}, ["AUSDT"])
    expected = exante_risk_scalars(targets, bars=bars, config=CONFIG)

    corrupted = bars.copy()
    future = corrupted["close_time"] >= decision
    corrupted.loc[future, "close"] = corrupted.loc[future, "close"] * 25.0
    observed = exante_risk_scalars(targets, bars=corrupted, config=CONFIG)

    pd.testing.assert_series_equal(observed, expected)


def test_the_warm_up_scalar_is_one_until_a_book_symbol_has_history() -> None:
    bars = _bars({"AUSDT": 0.02})
    early = pd.Timestamp("2023-01-03T00:00:00Z")
    targets = _targets({early: {"AUSDT": 1.0}}, ["AUSDT"])
    assert float(exante_risk_scalars(targets, bars=bars, config=CONFIG).iloc[0]) == 1.0


def test_a_short_history_symbol_borrows_the_median_variance() -> None:
    """A freshly listed name is priced, not silently treated as riskless."""
    bars = _bars({"AUSDT": 0.02, "BUSDT": 0.02})
    newcomer = bars["symbol"] == "BUSDT"
    bars = pd.concat([bars[~newcomer], bars[newcomer].tail(5)], ignore_index=True)
    decision = pd.Timestamp("2023-06-01T00:00:00Z")

    alone = _targets({decision: {"AUSDT": 1.0}}, ["AUSDT", "BUSDT"])
    with_newcomer = _targets({decision: {"AUSDT": 0.5, "BUSDT": 0.5}}, ["AUSDT", "BUSDT"])

    alone_scalar = float(exante_risk_scalars(alone, bars=bars, config=CONFIG).iloc[0])
    mixed_scalar = float(exante_risk_scalars(with_newcomer, bars=bars, config=CONFIG).iloc[0])

    # Half the book carries the median variance with no covariance, so the pair is less risky than
    # the outright but far from free.
    assert alone_scalar < mixed_scalar < CONFIG.risk_maximum_scale


def test_hold_rows_carry_no_scalar_and_flat_rows_are_neutral() -> None:
    bars = _bars({"AUSDT": 0.02})
    decisions = pd.DatetimeIndex(["2023-06-01T00:00:00Z", "2023-06-01T08:00:00Z"])
    targets = pd.DataFrame({"AUSDT": [1.0, 0.0]}, index=decisions)
    targets[REBALANCE_COLUMN] = [True, False]

    scalars = exante_risk_scalars(targets, bars=bars, config=CONFIG)

    assert scalars.index.equals(decisions)
    assert scalars.iloc[1] == 1.0


def test_the_scalar_is_clamped_to_the_declared_band() -> None:
    calm = _bars({"AUSDT": 0.0001})
    wild = _bars({"AUSDT": 0.5})
    decision = pd.Timestamp("2023-06-01T00:00:00Z")
    targets = _targets({decision: {"AUSDT": 1.0}}, ["AUSDT"])

    assert float(exante_risk_scalars(targets, bars=calm, config=CONFIG).iloc[0]) == 3.0
    assert (
        float(exante_risk_scalars(targets, bars=wild, config=CONFIG).iloc[0])
        == CONFIG.risk_minimum_scale
    )
