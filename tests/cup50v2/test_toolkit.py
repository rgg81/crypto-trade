"""The shared primitives every lane is built on.

If these are wrong, twelve lanes are wrong in the same direction and the field measures the
toolkit rather than the mechanisms.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2


def _context(symbols=("AUSDT", "BUSDT", "CUSDT"), periods=400, drift=0.001):
    now = pd.Timestamp("2024-06-01T00:00:00Z")
    close_times = pd.date_range(end=now - pd.Timedelta(milliseconds=1), periods=periods, freq="8h")
    bars = {}
    for index, symbol in enumerate(symbols):
        close = pd.Series([100.0 * (1.0 + drift * (index + 1)) ** step for step in range(periods)])
        bars[symbol] = pd.DataFrame(
            {
                "open_time": close_times - pd.Timedelta(hours=8) + pd.Timedelta(milliseconds=1),
                "close_time": close_times,
                "close": close,
                "high": close * 1.01,
                "low": close * 0.99,
                "quote_volume": 1e6 * (index + 1),
                "trade_count": 1000 + index,
                "taker_buy_quote_volume": 6e5 * (index + 1),
            }
        )
    funding = pd.concat(
        [
            pd.DataFrame(
                {
                    "funding_time": close_times,
                    "symbol": symbol,
                    "funding_rate": 0.0001 * (index + 1),
                    "funding_interval_hours": 8.0,
                }
            )
            for index, symbol in enumerate(symbols)
        ],
        ignore_index=True,
    )
    return DecisionContextV2(now, bars, funding, {}, tuple(symbols))


def test_panels_are_causal_and_wide() -> None:
    context = _context()
    panel = toolkit.close_panel(context)
    assert list(panel.columns) == ["AUSDT", "BUSDT", "CUSDT"]
    assert (panel.index < context.decision_time).all()
    assert panel.index.is_monotonic_increasing
    volume = toolkit.column_panel(context, "quote_volume")
    assert volume.iloc[-1]["CUSDT"] == pytest.approx(3e6)


def test_an_empty_or_thin_cross_section_returns_empty_rather_than_raising() -> None:
    empty = DecisionContextV2(pd.Timestamp("2024-06-01T00:00:00Z"), {}, pd.DataFrame(), {}, ())
    assert toolkit.close_panel(empty).empty
    assert toolkit.realised_sigma(toolkit.close_panel(empty)).empty
    assert toolkit.vol_parity({}, pd.Series(dtype=float)) == {}
    assert toolkit.long_short_extremes(pd.Series({"AUSDT": 1.0}), 3) == {}


def test_trailing_return_skips_the_requested_bars() -> None:
    panel = toolkit.close_panel(_context(symbols=("AUSDT",), drift=0.01))
    plain = float(toolkit.trailing_return(panel, 10)["AUSDT"])
    skipped = float(toolkit.trailing_return(panel, 10, skip=5)["AUSDT"])
    assert plain == pytest.approx(1.01**10 - 1.0)
    assert skipped == pytest.approx(1.01**10 - 1.0)
    assert float(toolkit.trailing_return(panel, 400).get("AUSDT", float("nan"))) != 0.0


def test_realised_sigma_is_annualised_from_eight_hour_bars() -> None:
    generator = np.random.default_rng(4)
    close_times = pd.date_range("2024-01-01", periods=300, freq="8h", tz="UTC")
    steps = generator.normal(0.0, 0.01, size=300)
    panel = pd.DataFrame({"AUSDT": 100.0 * np.exp(np.cumsum(steps))}, index=close_times)
    sigma = float(toolkit.realised_sigma(panel, bars=270)["AUSDT"])
    assert sigma == pytest.approx(0.01 * math.sqrt(toolkit.BARS_PER_YEAR), rel=0.2)


def test_vol_parity_risks_each_name_equally_and_balances_the_two_sides() -> None:
    sigma = pd.Series({"AUSDT": 0.20, "BUSDT": 0.80, "CUSDT": 0.40})
    weights = toolkit.vol_parity({"AUSDT": 1.0, "BUSDT": 1.0, "CUSDT": -1.0}, sigma, symbol_cap=1.0)

    # Half the volatility, twice the weight.
    assert weights["AUSDT"] == pytest.approx(4.0 * weights["BUSDT"])
    assert sum(value for value in weights.values() if value > 0) == pytest.approx(0.5)
    assert sum(-value for value in weights.values() if value < 0) == pytest.approx(0.5)
    assert sum(abs(value) for value in weights.values()) == pytest.approx(1.0)


def test_vol_parity_caps_each_name_and_never_grows_the_book() -> None:
    sigma = pd.Series({"AUSDT": 0.01, "BUSDT": 1.0, "CUSDT": 1.0, "DUSDT": 1.0})
    weights = toolkit.vol_parity(
        {"AUSDT": 1.0, "BUSDT": 1.0, "CUSDT": -1.0, "DUSDT": -1.0}, sigma, symbol_cap=0.15
    )
    assert max(abs(value) for value in weights.values()) <= 0.15 + 1e-12
    assert sum(abs(value) for value in weights.values()) <= 1.0 + 1e-12


def test_a_one_sided_book_uses_its_whole_budget() -> None:
    sigma = pd.Series({symbol: 0.5 for symbol in "ABCDEFGH"})
    weights = toolkit.vol_parity({symbol: 1.0 for symbol in "ABCDEFGH"}, sigma)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_the_cap_redistributes_rather_than_shrinking_the_book() -> None:
    """One wild name hitting its ceiling must not leave the rest of the budget unspent."""
    sigma = pd.Series({"AUSDT": 0.02, "BUSDT": 0.5, "CUSDT": 0.5, "DUSDT": 0.5, "EUSDT": 0.5})
    signals = {symbol: 1.0 for symbol in sigma.index}
    weights = toolkit.vol_parity(signals, sigma, symbol_cap=0.25)

    assert weights["AUSDT"] == pytest.approx(0.25)
    assert sum(weights.values()) == pytest.approx(1.0)
    assert all(value <= 0.25 + 1e-12 for value in weights.values())


def test_a_book_that_cannot_fill_its_budget_stays_below_it() -> None:
    """Three names under a 0.15 ceiling simply cannot deploy a full unit of gross."""
    sigma = pd.Series({"AUSDT": 0.5, "BUSDT": 0.5, "CUSDT": 0.5})
    weights = toolkit.vol_parity({"AUSDT": 1.0, "BUSDT": 1.0, "CUSDT": 1.0}, sigma, symbol_cap=0.15)
    assert sum(weights.values()) == pytest.approx(0.45)


def test_rank_and_z_are_finite_on_a_degenerate_cross_section() -> None:
    flat = pd.Series({"AUSDT": 2.0, "BUSDT": 2.0, "CUSDT": 2.0})
    assert (toolkit.cross_sectional_z(flat) == 0.0).all()
    assert toolkit.cross_sectional_rank(flat).abs().max() <= 0.5
    single = pd.Series({"AUSDT": 2.0})
    assert float(toolkit.cross_sectional_rank(single)["AUSDT"]) == 0.0


def test_long_short_extremes_are_deterministic_under_ties() -> None:
    values = pd.Series({"BUSDT": 1.0, "AUSDT": 1.0, "CUSDT": 0.0, "DUSDT": 0.0})
    first = toolkit.long_short_extremes(values, 2)
    second = toolkit.long_short_extremes(values.reindex(["DUSDT", "CUSDT", "BUSDT", "AUSDT"]), 2)
    assert first == second


@pytest.mark.parametrize("seed", [0, 3, 7, 11, 42])
def test_kmeans_is_deterministic_and_never_collapses_to_one_cluster(seed: int) -> None:
    """Uniform seeding can seat both centres in one group, and then the clustering does nothing."""
    matrix = np.vstack([np.zeros((10, 3)), np.ones((10, 3)) * 5.0])
    labels = toolkit.kmeans_labels(matrix, 2, seed=seed)
    assert np.array_equal(labels, toolkit.kmeans_labels(matrix, 2, seed=seed))
    assert len(set(labels[:10])) == 1 and len(set(labels[10:])) == 1
    assert labels[0] != labels[-1]


def test_kmeans_survives_a_degenerate_cross_section() -> None:
    identical = np.ones((6, 2))
    assert len(toolkit.kmeans_labels(identical, 3, seed=1)) == 6
    assert len(toolkit.kmeans_labels(np.zeros((0, 2)), 3, seed=1)) == 0


def test_the_smoother_blends_toward_the_request_and_holds_inside_the_band() -> None:
    smoother = toolkit.TargetSmoother(decay=0.5, band=0.10)
    eligible = ["AUSDT", "BUSDT"]

    first = smoother.update({"AUSDT": 1.0}, eligible)
    assert first == {"AUSDT": pytest.approx(0.5)}

    second = smoother.update({"AUSDT": 1.0}, eligible)
    assert second == {"AUSDT": pytest.approx(0.75)}

    # A request that barely moves the book is held rather than paid for.
    assert smoother.update({"AUSDT": 0.76}, eligible) is None


def test_the_smoother_drops_names_that_left_the_universe() -> None:
    smoother = toolkit.TargetSmoother(decay=1.0, band=0.0)
    smoother.update({"AUSDT": 0.5, "BUSDT": 0.5}, ["AUSDT", "BUSDT"])
    result = smoother.update({"AUSDT": 0.5}, ["AUSDT"])
    assert result is not None and set(result) == {"AUSDT"}


def test_the_smoother_never_emits_more_than_its_gross_budget() -> None:
    smoother = toolkit.TargetSmoother(decay=1.0, band=0.0, gross=1.0)
    result = smoother.update({"AUSDT": 3.0, "BUSDT": -3.0}, ["AUSDT", "BUSDT"])
    assert sum(abs(value) for value in result.values()) == pytest.approx(1.0)


def test_beta_and_drawdown_describe_the_panel() -> None:
    context = _context(symbols=("AUSDT", "BUSDT"), drift=0.002)
    panel = toolkit.close_panel(context)
    index = toolkit.equal_weight_index(panel)
    betas = toolkit.beta_to(panel, index, 200)
    assert set(betas.index) == {"AUSDT", "BUSDT"}
    assert (toolkit.drawdown_from_high(panel, 100) <= 0.0).all()


def test_funding_history_is_grouped_oldest_first() -> None:
    funding = toolkit.funding_by_symbol(_context())
    assert set(funding) == {"AUSDT", "BUSDT", "CUSDT"}
    assert float(funding["CUSDT"].iloc[-1]) == pytest.approx(0.0003)
