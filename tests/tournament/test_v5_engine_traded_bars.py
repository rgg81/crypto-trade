"""A bar in which nothing traded is not executable.

Reproducing V4-R9's 2022-05-13 insolvency with a real candidate showed the cause was not the
delisting settlement but a stale-bar / live-mark divergence. LUNA had stopped trading, so its bar
carried prices forward at 0.008000 with zero volume while the index mark fell to 0.000310 -- a
25.77x disagreement. Sizing quantity on the mark gave 32,054,124 units for a -0.1 weight, and
settling that at the close cost $256,433 against $99,496 of equity.

288 member-bars in the V5 snapshot never traded, across six symbols and present in the holdout as
well as development, with close/mark divergence reaching 989x. The universe rule removes the cases
it can see, but weekly reconstitution cannot foresee a contract going quiet mid-week, so the
execution contract has to hold the line.
"""

from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import engine

START = pd.Timestamp("2021-01-04", tz="UTC")
SYMBOLS = ("AAAUSDT", "BBBUSDT")


def _grid(periods: int = 12) -> pd.DatetimeIndex:
    return pd.date_range(START, periods=periods, freq="8h", tz="UTC")


def _bars(last_index: dict[str, int] | None = None) -> pd.DataFrame:
    """Bars for every symbol, optionally truncated per symbol to model a delisting."""

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
            "quote_volume": 5_000_000.0,
            "trade_count": 500,
            "taker_buy_volume": 500.0,
            "taker_buy_quote_volume": 2_500_000.0,
        }
        for position, stamp in enumerate(_grid())
        for symbol in SYMBOLS
        if position <= stops.get(symbol, len(_grid()))
    ]
    return pd.DataFrame(rows)


def _marks(bars: pd.DataFrame, *, stale: dict[tuple[str, pd.Timestamp], float] | None = None):
    frame = pd.DataFrame(
        {
            "mark_time": bars["open_time"],
            "symbol": bars["symbol"],
            "mark_price": bars["open"],
        }
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


class _AllIn:
    def target_weights(self, context, *, seed):  # type: ignore[no-untyped-def]
        return {symbol: 0.1 for symbol in context.eligible_symbols}


def test_a_dormant_bar_is_hidden_from_the_strategy() -> None:
    """Fillability shown to a strategy must match what the evaluator will enforce."""

    bars = _bars()
    boundary = _grid()[5]
    bars.loc[bars["symbol"].eq("BBBUSDT") & bars["open_time"].eq(boundary), "quote_volume"] = 0.0

    targets = engine.generate_targets(
        _AllIn(), bars, _funding(bars), _membership(), list(_grid()), seed=1
    )
    assert targets.loc[boundary, "BBBUSDT"] == 0.0
    assert targets.loc[boundary, "AAAUSDT"] == 0.1

    permissive = engine.generate_targets(
        _AllIn(),
        bars,
        _funding(bars),
        _membership(),
        list(_grid()),
        seed=1,
        require_traded_bar=False,
    )
    assert permissive.loc[boundary, "BBBUSDT"] == 0.1


def test_a_dormant_bar_cannot_be_filled_by_the_evaluator() -> None:
    bars = _bars()
    boundary = _grid()[5]
    bars.loc[bars["symbol"].eq("BBBUSDT") & bars["open_time"].eq(boundary), "quote_volume"] = 0.0

    targets = engine.generate_targets(
        _AllIn(), bars, _funding(bars), _membership(), list(_grid()), seed=1
    )
    result = engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        targets,
        mark_prices=_marks(bars),
        config=engine.EvaluatorConfig(),
    )
    # Exiting where you cannot enter is correct and necessary: a position carried into a bar that
    # stopped trading still has to be closed. What must not happen is holding exposure that was
    # established on a bar where nothing traded.
    previous = result.positions["BBBUSDT"].shift(1).loc[boundary]
    assert previous > 0.0, "the fixture must carry a position into the dormant bar"
    assert result.positions.loc[boundary, "BBBUSDT"] == 0.0

    trades = result.events[
        (result.events["timestamp"] == boundary)
        & (result.events["symbol"] == "BBBUSDT")
        & (result.events["event_type"] == "trade")
    ]
    assert len(trades) == 1
    assert float(trades["quantity"].iloc[0]) < 0.0, "the only fill permitted here is an exit"


def test_a_stale_bar_beside_a_collapsed_mark_no_longer_wipes_the_book() -> None:
    """The V4-R9 mechanism, in miniature: frozen close, collapsed mark, zero volume."""

    # Faithful to the LUNA path: the contract goes quiet, keeps publishing frozen bars while the
    # index mark collapses, and only then stops publishing -- which is the boundary at which the
    # forced exit charges the residual at the frozen close using a mark-inflated quantity.
    bars = _bars(last_index={"BBBUSDT": 7})
    boundary = _grid()[7]
    dormant = bars["symbol"].eq("BBBUSDT") & bars["open_time"].ge(_grid()[5])
    bars.loc[dormant, "quote_volume"] = 0.0
    marks = _marks(bars, stale={("BBBUSDT", stamp): 0.004 for stamp in _grid()[5:8]})

    class ShortTheDormant:
        def target_weights(self, context, *, seed):  # type: ignore[no-untyped-def]
            return {
                symbol: (-0.1 if symbol == "BBBUSDT" else 0.1)
                for symbol in context.eligible_symbols
            }

    guarded_targets = engine.generate_targets(
        ShortTheDormant(), bars, _funding(bars), _membership(), list(_grid()), seed=1
    )
    guarded = engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        guarded_targets,
        mark_prices=marks,
        config=engine.EvaluatorConfig(),
    )
    guarded_settlements = guarded.events[guarded.events["event_type"] == "conservative_settlement"]
    assert guarded_settlements.empty, "the guard should prevent the residual from ever forming"
    assert guarded.returns["net_return"].min() > -0.01

    # Mutation: let the dormant bars fill and the residual is charged at the frozen close using a
    # mark-inflated quantity -- the exact V4-R9 mechanism, differing from LUNA only in magnitude.
    permissive_targets = engine.generate_targets(
        ShortTheDormant(),
        bars,
        _funding(bars),
        _membership(),
        list(_grid()),
        seed=1,
        require_traded_bar=False,
    )
    permissive = engine.evaluate_targets(
        bars,
        _funding(bars),
        _membership(),
        permissive_targets,
        mark_prices=marks,
        config=engine.EvaluatorConfig(require_traded_bar_to_fill=False),
    )
    settlements = permissive.events[permissive.events["event_type"] == "conservative_settlement"]
    assert len(settlements) == 1
    assert float(settlements["notional"].abs().iloc[0]) > 10_000.0
    assert permissive.returns["net_return"].min() < -0.10
    # The guard reduces the worst bar by orders of magnitude, not by a margin.
    assert guarded.returns["net_return"].min() > 100 * permissive.returns["net_return"].min()
    assert boundary in set(_grid())


def test_generation_and_evaluation_must_agree_on_fillability() -> None:
    """A mismatch between the two flags is loud, and must stay loud.

    Targets built under the permissive rule name symbols the strict evaluator will not fill. The
    right response is to fix the caller, never to relax the rejection: silently dropping such a
    target would let a strategy hold a position the evaluator believes it never opened.
    """

    bars = _bars()
    dormant = bars["symbol"].eq("BBBUSDT") & bars["open_time"].ge(_grid()[5])
    bars.loc[dormant, "quote_volume"] = 0.0

    permissive_targets = engine.generate_targets(
        _AllIn(),
        bars,
        _funding(bars),
        _membership(),
        list(_grid()),
        seed=1,
        require_traded_bar=False,
    )
    with pytest.raises(ValueError, match="ineligible target symbols"):
        engine.evaluate_targets(
            bars,
            _funding(bars),
            _membership(),
            permissive_targets,
            mark_prices=_marks(bars),
            config=engine.EvaluatorConfig(require_traded_bar_to_fill=True),
        )
