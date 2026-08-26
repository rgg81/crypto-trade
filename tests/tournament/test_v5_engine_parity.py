"""The V5 evaluator must start indistinguishable from the one it forked.

V4-R2's completed record binds the hash of ``engine_v2``, so V5 forks rather than edits it. A fork
is only safe if it starts identical: otherwise a later behavioural difference cannot be attributed
to the change that was meant to cause it. These tests pin that baseline against the parent's own
fixtures, and every V5 feature is added behind a flag that is off here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import engine_v2
from crypto_trade.tournament.v5 import engine as engine_v5

INTERVAL_HOURS = 8
START = pd.Timestamp("2021-01-04", tz="UTC")
SYMBOLS = ("AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT")


def _grid(periods: int = 30) -> pd.DatetimeIndex:
    return pd.date_range(START, periods=periods, freq=f"{INTERVAL_HOURS}h", tz="UTC")


def _bars(seed: int = 7) -> pd.DataFrame:
    generator = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for index, symbol in enumerate(SYMBOLS):
        price = 100.0 * (index + 1)
        for stamp in _grid():
            step = float(generator.normal(0.0, 0.02))
            open_price = price
            close_price = max(0.01, price * (1.0 + step))
            price = close_price
            rows.append(
                {
                    "open_time": stamp,
                    "symbol": symbol,
                    "open": open_price,
                    "high": max(open_price, close_price) * 1.01,
                    "low": min(open_price, close_price) * 0.99,
                    "close": close_price,
                    "volume": 1_000.0,
                    "quote_volume": 5_000_000.0,
                    "trade_count": 500,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 2_500_000.0,
                }
            )
    return pd.DataFrame(rows)


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "mark_time": bars["open_time"],
            "symbol": bars["symbol"],
            "mark_price": bars["open"],
        }
    )


def _funding(bars: pd.DataFrame) -> pd.DataFrame:
    rows = bars.loc[:, ["open_time", "symbol"]].copy()
    rows = rows.rename(columns={"open_time": "settlement_time"})
    rows["funding_time"] = rows["settlement_time"]
    rows["funding_rate"] = 0.0001
    rows["mark_price"] = 100.0
    return rows


def _membership() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reconstitution_time": week,
                "symbol": symbol,
                "liquidity_rank": rank,
                "trailing_quote_volume": 1_000_000.0,
            }
            for week in pd.date_range(START, periods=3, freq="7D", tz="UTC")
            for rank, symbol in enumerate(SYMBOLS, start=1)
        ]
    )


def _targets(index: pd.DatetimeIndex) -> pd.DataFrame:
    frame = pd.DataFrame(0.0, index=index, columns=list(SYMBOLS))
    frame["AAAUSDT"] = 0.10
    frame["BBBUSDT"] = -0.10
    frame["CCCUSDT"] = 0.05
    frame["DDDUSDT"] = -0.05
    return frame


@pytest.fixture(name="fixtures")
def _fixtures() -> dict[str, pd.DataFrame]:
    bars = _bars()
    return {
        "bars": bars,
        "funding": _funding(bars),
        "marks": _marks(bars),
        "membership": _membership(),
        "targets": _targets(_grid()),
    }


def _evaluate(module, fixtures, **config_overrides):  # type: ignore[no-untyped-def]
    config = module.EvaluatorConfig(**config_overrides)
    return module.evaluate_targets(
        fixtures["bars"],
        fixtures["funding"],
        fixtures["membership"],
        fixtures["targets"],
        mark_prices=fixtures["marks"],
        config=config,
    )


@pytest.mark.parametrize("cost_multiplier", [1.0, 2.0, 3.0])
def test_v5_evaluator_matches_its_parent_frame_for_frame(
    fixtures: dict[str, pd.DataFrame], cost_multiplier: float
) -> None:
    parent = engine_v2.evaluate_targets(
        fixtures["bars"],
        fixtures["funding"],
        fixtures["membership"],
        fixtures["targets"],
        mark_prices=fixtures["marks"],
        config=engine_v2.EvaluatorConfig(),
        cost_multiplier=cost_multiplier,
    )
    forked = engine_v5.evaluate_targets(
        fixtures["bars"],
        fixtures["funding"],
        fixtures["membership"],
        fixtures["targets"],
        mark_prices=fixtures["marks"],
        config=engine_v5.EvaluatorConfig(require_traded_bar_to_fill=False),
        cost_multiplier=cost_multiplier,
    )
    pd.testing.assert_frame_equal(parent.returns, forked.returns, check_exact=True)
    pd.testing.assert_frame_equal(parent.positions, forked.positions, check_exact=True)
    pd.testing.assert_frame_equal(parent.events, forked.events, check_exact=True)


def test_v5_target_generation_matches_its_parent(fixtures: dict[str, pd.DataFrame]) -> None:
    class Strategy:
        def target_weights(self, context, *, seed):  # type: ignore[no-untyped-def]
            weights = {}
            for position, symbol in enumerate(context.eligible_symbols):
                weights[symbol] = 0.05 if position % 2 == 0 else -0.05
            return weights

    times = list(_grid())
    parent = engine_v2.generate_targets(
        Strategy(), fixtures["bars"], fixtures["funding"], fixtures["membership"], times, seed=1
    )
    forked = engine_v5.generate_targets(
        Strategy(),
        fixtures["bars"],
        fixtures["funding"],
        fixtures["membership"],
        times,
        seed=1,
        require_traded_bar=False,
    )
    pd.testing.assert_frame_equal(parent, forked, check_exact=True)


def test_the_parity_fixture_is_not_degenerate(fixtures: dict[str, pd.DataFrame]) -> None:
    """A parity test over a book that never trades proves nothing.

    'Clean' and 'parsed nothing' must not be the same result, so assert the baseline run actually
    exercises fills, both sides, costs and returns of both signs before trusting the comparison.
    """

    result = _evaluate(engine_v5, fixtures)
    trades = result.events[result.events["event_type"] == "trade"]
    assert len(trades) > 0
    assert trades["symbol"].nunique() >= 2
    assert (result.returns["turnover"] > 0).any()
    assert (result.returns["net_return"] > 0).any()
    assert (result.returns["net_return"] < 0).any()
    assert (result.positions.abs() > 0).any(axis=1).sum() >= 2
    assert result.positions.gt(0).any().any() and result.positions.lt(0).any().any()


def test_v5_config_defaults_match_the_parent() -> None:
    """A silently different *shared* default would make every later comparison meaningless.

    V5-only fields deliberately default to the safe behaviour rather than the parent's, so the
    hazard has to be opted into. Parity is asserted by switching them off explicitly above.
    """

    parent = engine_v2.EvaluatorConfig()
    forked = engine_v5.EvaluatorConfig()
    shared = {field.name for field in parent.__dataclass_fields__.values()}
    for name in sorted(shared):
        assert getattr(parent, name) == getattr(forked, name), name
