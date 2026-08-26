"""A common ex-ante risk unit, owned by the organizer.

Without one, a cross-team drawdown comparison collapses into "whoever sized smallest wins".
V4-R9's five finalists spanned realized volatility from 7.3% to 20.2% -- a 2.8x range -- so a
shared drawdown cap capped book *size*, not risk-adjusted quality. Normalised to a 10% unit the
least-risky book's 20.0% drawdown becomes 27.4%, the worst in the field, and the winner's 19.4%
becomes 9.6%. CUP-50 v2 mandated the same unit and held twelve lanes to 9.0%-11.7% realized.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5 import engine

START = pd.Timestamp("2021-01-04", tz="UTC")
SYMBOLS = ("AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT")
PERIODS = 250


def _grid(periods: int = PERIODS) -> pd.DatetimeIndex:
    return pd.date_range(START, periods=periods, freq="8h", tz="UTC")


def _bars(volatility: float = 0.01, seed: int = 11) -> pd.DataFrame:
    generator = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for index, symbol in enumerate(SYMBOLS):
        price = 100.0 * (index + 1)
        for stamp in _grid():
            open_price = price
            close_price = max(0.01, price * (1.0 + float(generator.normal(0.0, volatility))))
            price = close_price
            rows.append(
                {
                    "open_time": stamp,
                    "symbol": symbol,
                    "open": open_price,
                    "high": max(open_price, close_price) * 1.001,
                    "low": min(open_price, close_price) * 0.999,
                    "close": close_price,
                    "volume": 1_000.0,
                    "quote_volume": 5.0e9,
                    "trade_count": 500,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 2.5e9,
                }
            )
    return pd.DataFrame(rows)


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {"mark_time": bars["open_time"], "symbol": bars["symbol"], "mark_price": bars["open"]}
    )


def _funding(bars: pd.DataFrame) -> pd.DataFrame:
    rows = bars.loc[:, ["open_time", "symbol"]].rename(columns={"open_time": "settlement_time"})
    rows["funding_time"] = rows["settlement_time"]
    rows["funding_rate"] = 0.0
    rows["mark_price"] = 100.0
    return rows


def _membership() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reconstitution_time": week,
                "symbol": symbol,
                "liquidity_rank": rank,
                "trailing_quote_volume": 1.0e9,
            }
            for week in pd.date_range(START, periods=PERIODS // 21 + 2, freq="7D", tz="UTC")
            for rank, symbol in enumerate(SYMBOLS, start=1)
        ]
    )


def _targets(weight: float = 0.02) -> pd.DataFrame:
    frame = pd.DataFrame(0.0, index=_grid(), columns=list(SYMBOLS))
    frame["AAAUSDT"] = weight
    frame["BBBUSDT"] = -weight
    frame["CCCUSDT"] = weight
    frame["DDDUSDT"] = -weight
    return frame


def _run(bars: pd.DataFrame, targets: pd.DataFrame, **overrides):  # type: ignore[no-untyped-def]
    return engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        targets,
        mark_prices=_marks(bars),
        config=engine.EvaluatorConfig(**overrides),
    )


def _scored(result) -> pd.DataFrame:  # type: ignore[no-untyped-def]
    """Bars where the unit had an estimate, i.e. past warmup."""

    return result.returns[result.returns["risk_unit_binding"] != "warmup"]


def test_a_low_volatility_book_is_levered_up_to_the_unit() -> None:
    """Every V4-R9 finalist was a low-vol book; a unit that could only scale down is no unit."""

    # Chosen so the required leverage sits inside the scale bounds: a book needing 30x would be
    # clipped at max_scale, which is correct behaviour but tests the clip, not the convergence.
    bars = _bars(volatility=0.020)
    result = _run(bars, _targets(0.05))
    scored = _scored(result)
    assert not scored.empty
    assert (scored["risk_unit_scale"] > 1.0).any()
    attained = scored["risk_unit_attained_vol"].dropna()
    assert attained.median() == pytest.approx(0.10, rel=0.05)


def test_a_high_volatility_book_is_scaled_down_to_the_same_unit() -> None:
    bars = _bars(volatility=0.06)
    result = _run(bars, _targets(0.10))
    scored = _scored(result)
    assert (scored["risk_unit_scale"] < 1.0).any()
    attained = scored["risk_unit_attained_vol"].dropna()
    assert attained.median() == pytest.approx(0.10, rel=0.35)


def test_two_books_of_different_volatility_are_compared_at_equal_risk() -> None:
    """The whole point: without this, a drawdown comparison ranks book size."""

    quiet = _scored(_run(_bars(volatility=0.020), _targets(0.05)))
    loud = _scored(_run(_bars(volatility=0.050, seed=12), _targets(0.06)))
    # Submitted volatility differs by roughly 3x and the scales move in opposite directions.
    assert quiet["risk_unit_scale"].median() > 1.0
    assert loud["risk_unit_scale"].median() < 1.0
    ratio = loud["risk_unit_attained_vol"].median() / quiet["risk_unit_attained_vol"].median()
    assert ratio == pytest.approx(1.0, rel=0.05), (
        "attained volatility must converge even when submitted volatility differs"
    )


def test_the_estimator_is_past_only() -> None:
    """Corrupting every bar from the decision forward must not move a single decision.

    This is the same future-invariance trick the candidate review already uses on strategies. A
    one-bar look-ahead here would be invisible in every downstream metric.
    """

    bars = _bars()
    cut = _grid()[200]
    corrupted = bars.copy()
    future = corrupted["open_time"] >= cut
    for column in ("open", "high", "low", "close"):
        corrupted.loc[future, column] = corrupted.loc[future, column] * 7.0

    baseline = _run(bars, _targets())
    tampered = _run(corrupted, _targets())
    before = baseline.returns.index < cut
    pd.testing.assert_series_equal(
        baseline.returns.loc[before, "risk_unit_scale"],
        tampered.returns.loc[before, "risk_unit_scale"],
        check_exact=True,
    )


def test_the_unit_never_breaches_the_exposure_caps() -> None:
    """It may scale up, so the projection back into the caps is load-bearing."""

    config = engine.EvaluatorConfig()
    result = _run(_bars(volatility=0.002), _targets(0.01))
    gross = result.returns["gross_exposure"]
    assert (gross <= config.max_gross_exposure + 1e-9).all()
    net = result.returns["net_exposure"].abs()
    assert (net <= config.max_abs_net_exposure + 1e-9).all()
    assert (result.positions.abs().max(axis=1) <= config.max_symbol_exposure + 1e-9).all()


def test_a_capped_book_reports_which_cap_bound_it() -> None:
    """Under-risked is a finding, not a failure -- but it has to be visible to be a finding."""

    result = _run(_bars(volatility=0.0005), _targets(0.10))
    bindings = set(_scored(result)["risk_unit_binding"])
    assert bindings & {"max_scale", "gross_cap", "symbol_cap", "net_cap"}


def test_the_unit_is_reported_as_an_explicit_central_action() -> None:
    result = _run(_bars(volatility=0.005), _targets(0.01))
    events = result.events[result.events["event_type"] == "risk_unit"]
    assert not events.empty
    assert set(events["phase"]) - {"none"}


def test_warmup_leaves_the_book_untouched_and_says_so() -> None:
    """'No estimate yet' and 'no adjustment needed' are different claims."""

    result = _run(_bars(), _targets())
    warmup = result.returns[result.returns["risk_unit_binding"] == "warmup"]
    assert not warmup.empty
    assert (warmup["risk_unit_scale"] == 1.0).all()
    assert warmup["risk_unit_ex_ante_vol"].isna().all()


def test_disabling_the_unit_leaves_the_submitted_book_alone() -> None:
    """Mutation: the unit is what moves the exposure, not something else in the path."""

    bars = _bars(volatility=0.020)
    targets = _targets(0.05)
    with_unit = _run(bars, targets)
    without = _run(bars, targets, risk_unit_enabled=False)
    assert without.returns["gross_exposure"].median() == pytest.approx(0.20, abs=1e-6)
    assert with_unit.returns["gross_exposure"].median() > without.returns["gross_exposure"].median()
    assert without.events[without.events["event_type"] == "risk_unit"].empty


def test_a_flat_book_is_not_scaled() -> None:
    flat = pd.DataFrame(0.0, index=_grid(), columns=list(SYMBOLS))
    result = _run(_bars(), flat)
    assert (result.returns["risk_unit_scale"] == 1.0).all()
    assert result.returns["gross_exposure"].abs().max() == 0.0


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"risk_unit_annualized_target": 0.0}, "must be positive"),
        ({"risk_unit_halflife_bars": 0}, "halflife and window must be positive"),
        ({"risk_unit_window_bars": 10, "risk_unit_warmup_bars": 50}, "shorter than its warmup"),
        ({"risk_unit_shrinkage": 1.5}, "shrinkage must lie"),
        ({"risk_unit_minimum_scale": 0.0}, "invalid risk-unit scale bounds"),
        ({"risk_unit_maximum_scale": 0.5, "risk_unit_minimum_scale": 0.1}, "cannot lever"),
    ],
)
def test_invalid_risk_unit_settings_are_rejected(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        engine.EvaluatorConfig(**overrides).validate()  # type: ignore[arg-type]
