"""A destroyed book is a measurement, not a crash.

V4-R9 recorded 86 of 180 research trials as infrastructure failures because the evaluator raised
when equity went non-positive. That threw away the strongest risk signal a candidate can produce
and, worse, threw it away unevenly: eleven of fifteen teams lost trials to it and two of the three
that escaped became IS rank 1 and the champion. The bracket was decided partly by who avoided one
bar.

Scoring ruin keeps the evidence. The return series ends with a -100% bar so every downstream
statistic sees the loss, rather than stopping early and leaving a Sharpe that looks untroubled.
"""

from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import engine

START = pd.Timestamp("2021-01-04", tz="UTC")
SYMBOLS = ("AAAUSDT", "BBBUSDT")


def _grid(periods: int = 12) -> pd.DatetimeIndex:
    return pd.date_range(START, periods=periods, freq="8h", tz="UTC")


def _bars(last_index: dict[str, int] | None = None, quote_volume: float = 5.0e9) -> pd.DataFrame:
    """Bars for every symbol, optionally truncated per symbol to model a delisting.

    The default quote volume is deliberately large. Damage from this path is bounded by the
    participation cap, so a thin fixture saturates around -40% and never ruins; LUNA reached
    insolvency precisely because its collapse-week bars carried ~1.5e9 of quote volume, which
    gave the cap room to build the position that was later settled at the frozen close.
    """

    stops = last_index or {}
    rows = [
        {
            "open_time": stamp,
            "symbol": symbol,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1_000.0,
            "quote_volume": quote_volume,
            "trade_count": 500,
            "taker_buy_volume": 500.0,
            "taker_buy_quote_volume": 2_500_000.0,
        }
        for position, stamp in enumerate(_grid())
        for symbol in SYMBOLS
        if position <= stops.get(symbol, len(_grid()))
    ]
    return pd.DataFrame(rows)


def _marks(bars: pd.DataFrame, stale: dict[tuple[str, pd.Timestamp], float] | None = None):
    frame = pd.DataFrame(
        {"mark_time": bars["open_time"], "symbol": bars["symbol"], "mark_price": bars["open"]}
    )
    for (symbol, stamp), price in (stale or {}).items():
        frame.loc[frame["symbol"].eq(symbol) & frame["mark_time"].eq(stamp), "mark_price"] = price
    return frame


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
                "reconstitution_time": START,
                "symbol": symbol,
                "liquidity_rank": rank,
                "trailing_quote_volume": 1_000_000.0,
            }
            for rank, symbol in enumerate(SYMBOLS, start=1)
        ]
    )


class _ShortTheDormant:
    def target_weights(self, context, *, seed):  # type: ignore[no-untyped-def]
        return {
            symbol: (-0.1 if symbol == "BBBUSDT" else 0.1) for symbol in context.eligible_symbols
        }


def _ruinous_inputs():  # type: ignore[no-untyped-def]
    """The V4-R9 path: a contract goes quiet, publishes frozen bars while its mark collapses,
    then stops publishing -- and the residual is settled at the frozen close."""

    bars = _bars(last_index={"BBBUSDT": 7})
    bars.loc[bars["symbol"].eq("BBBUSDT") & bars["open_time"].ge(_grid()[5]), "quote_volume"] = 0.0
    marks = _marks(bars, stale={("BBBUSDT", stamp): 0.00002 for stamp in _grid()[5:8]})
    targets = engine.generate_targets(
        _ShortTheDormant(),
        bars,
        _funding(bars),
        _membership(),
        list(_grid()),
        seed=1,
        require_traded_bar=False,
    )
    return bars, marks, targets


def _evaluate(bars, marks, targets, **overrides):  # type: ignore[no-untyped-def]
    config = engine.EvaluatorConfig(require_traded_bar_to_fill=False, **overrides)
    return engine.evaluate_targets(
        bars, _funding(bars), _membership(), targets, mark_prices=marks, config=config
    )


def test_ruin_is_scored_rather_than_raised() -> None:
    bars, marks, targets = _ruinous_inputs()
    result = _evaluate(bars, marks, targets)

    assert result.ruined_at is not None
    assert float(result.returns["net_return"].iloc[-1]) == -1.0
    assert float(result.returns["equity"].iloc[-1]) == 0.0
    assert result.returns.index[-1] == result.ruined_at


def test_the_same_run_raises_when_ruin_scoring_is_disabled() -> None:
    """Mutation: the flag is what converts the crash into a measurement."""

    bars, marks, targets = _ruinous_inputs()
    with pytest.raises(ValueError, match="insolvent"):
        _evaluate(bars, marks, targets, score_ruin_instead_of_raising=False)


def test_a_ruined_run_reports_a_total_loss_to_downstream_statistics() -> None:
    """The point of the final bar: a truncated series would leave the Sharpe untroubled."""

    bars, marks, targets = _ruinous_inputs()
    result = _evaluate(bars, marks, targets)
    cumulative = float((1.0 + result.returns["net_return"]).prod() - 1.0)
    assert cumulative == pytest.approx(-1.0)
    assert result.returns["net_return"].min() == -1.0


def test_the_run_stops_at_ruin_and_invents_no_recovery() -> None:
    bars, marks, targets = _ruinous_inputs()
    result = _evaluate(bars, marks, targets)
    assert result.returns.index.max() == result.ruined_at
    assert (result.returns.index <= result.ruined_at).all()
    assert result.ruined_at < _grid()[-1], "the fixture must ruin before the grid ends"


def test_ruin_is_recorded_as_an_event_with_its_phase() -> None:
    bars, marks, targets = _ruinous_inputs()
    result = _evaluate(bars, marks, targets)
    ruin = result.events[result.events["event_type"] == "ruin"]
    assert len(ruin) == 1
    assert str(ruin["phase"].iloc[0]) in {
        "after_boundary_funding",
        "after_execution_costs",
        "after_settlement",
        "after_held_weights",
    }
    assert pd.Timestamp(ruin["timestamp"].iloc[0]) == result.ruined_at


def test_a_healthy_run_is_not_marked_ruined() -> None:
    """'Ruined' and 'finished' must not be the same result."""

    bars = _bars()
    targets = engine.generate_targets(
        _ShortTheDormant(), bars, _funding(bars), _membership(), list(_grid()), seed=1
    )
    result = engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        targets,
        mark_prices=_marks(bars),
        config=engine.EvaluatorConfig(),
    )
    assert result.ruined_at is None
    assert result.events[result.events["event_type"] == "ruin"].empty
    assert result.returns["net_return"].min() > -1.0


def test_ruin_row_matches_the_normal_row_schema() -> None:
    """A ragged frame would break every downstream statistic; drift must fail here first."""

    bars = _bars()
    targets = engine.generate_targets(
        _ShortTheDormant(), bars, _funding(bars), _membership(), list(_grid()), seed=1
    )
    healthy = engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        targets,
        mark_prices=_marks(bars),
        config=engine.EvaluatorConfig(),
    )
    produced = tuple(healthy.returns.reset_index().columns)
    assert produced == engine.RETURN_ROW_FIELDS
    assert tuple(engine._ruin_row(START)) == engine.RETURN_ROW_FIELDS


def test_the_ruined_frame_is_not_ragged() -> None:
    bars, marks, targets = _ruinous_inputs()
    result = _evaluate(bars, marks, targets)
    assert list(result.returns.reset_index().columns) == list(engine.RETURN_ROW_FIELDS)
    # The risk-unit volatility diagnostics are deliberately NaN when no estimate exists -- "not
    # computed" and "zero volatility" are different claims and must not be conflated.
    economic = result.returns.drop(columns=["risk_unit_ex_ante_vol", "risk_unit_attained_vol"])
    assert not economic.isna().any().any()
