"""The research loop's snapshot: replayable, approximate, and unmistakably not official."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.replay import run_candidate
from crypto_trade.cup50v2.research_snapshot import research_snapshot_from_team_visible
from crypto_trade.cup50v2.snapshot import (
    load_snapshot,
    write_split_snapshots,
    write_team_visible_snapshot,
)

IS_START = pd.Timestamp("2022-01-03T00:00:00Z")
SPLIT = pd.Timestamp("2022-04-04T00:00:00Z")
END = pd.Timestamp("2022-06-06T00:00:00Z")
SYMBOLS = ("AUSDT", "BUSDT", "CUSDT")


def _panels(tmp_path):
    generator = np.random.default_rng(5)
    open_times = pd.date_range(IS_START, END, freq="8h", inclusive="left", tz="UTC")
    bars, funding, marks, roster = [], [], [], []
    for index, symbol in enumerate(SYMBOLS):
        close = 100.0 * np.exp(
            np.cumsum(generator.normal(0.0002, 0.01 + 0.002 * index, size=len(open_times)))
        )
        opens = np.concatenate(([100.0], close[:-1]))
        bars.append(
            pd.DataFrame(
                {
                    "open_time": open_times,
                    "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "symbol": symbol,
                    "open": opens,
                    "close": close,
                    "high": np.maximum(opens, close) * 1.002,
                    "low": np.minimum(opens, close) * 0.998,
                    "quote_volume": 1e9,
                    "trade_count": 5000,
                    "taker_buy_volume": 1e6,
                    "taker_buy_quote_volume": 5.2e8,
                }
            )
        )
        funding.append(
            pd.DataFrame(
                {
                    "funding_time": open_times,
                    "symbol": symbol,
                    "funding_rate": 0.0001,
                    "funding_interval_hours": 8.0,
                    "mark_price": close,
                }
            )
        )
        marks.append(pd.DataFrame({"mark_time": open_times, "symbol": symbol, "mark_price": close}))
    terminal_marks = pd.DataFrame(
        {"mark_time": [END] * 3, "symbol": list(SYMBOLS), "mark_price": [100.0] * 3}
    )
    terminal_funding = pd.DataFrame(
        {
            "funding_time": [END] * 3,
            "symbol": list(SYMBOLS),
            "funding_rate": [0.0] * 3,
            "funding_interval_hours": [8.0] * 3,
            "mark_price": [100.0] * 3,
        }
    )
    for boundary in pd.date_range(IS_START, END, freq="7D", tz="UTC"):
        for rank, symbol in enumerate(SYMBOLS, start=1):
            roster.append([boundary, symbol, rank, 1e8])

    write_split_snapshots(
        pd.concat(bars, ignore_index=True),
        pd.concat([*funding, terminal_funding], ignore_index=True),
        pd.concat([*marks, terminal_marks], ignore_index=True),
        pd.DataFrame(
            roster,
            columns=[
                "reconstitution_time",
                "symbol",
                "liquidity_rank",
                "median_daily_quote_volume",
            ],
        ),
        pd.DataFrame({"symbol": list(SYMBOLS), "onboard_date": [IS_START] * 3}),
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_start=IS_START,
        oos_start=SPLIT,
        oos_end=END,
    )
    research = load_snapshot(tmp_path / "is")
    write_team_visible_snapshot(research, root=tmp_path / "team")
    return research


class Buyer:
    def target_weights(self, context, *, seed):
        if pd.Timestamp(context.decision_time).hour != 0:
            return None
        eligible = [symbol for symbol in context.eligible_symbols if symbol in context.bars]
        return {symbol: 0.3 for symbol in eligible[:2]} if eligible else {}


def test_the_team_visible_export_alone_becomes_replayable(tmp_path) -> None:
    _panels(tmp_path)
    snapshot = research_snapshot_from_team_visible(tmp_path / "team")

    assert "open" in snapshot.bars
    assert not snapshot.mark_prices.empty
    replay = run_candidate(
        Buyer(),
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
        record_events=False,
    )
    returns = replay.costs[1].returns
    assert float(returns["turnover"].sum()) > 0.0
    assert (returns["equity"] > 0).all()


def test_the_synthesised_open_is_the_previous_close(tmp_path) -> None:
    """A research fill is priced at the last thing the strategy could have seen."""
    _panels(tmp_path)
    snapshot = research_snapshot_from_team_visible(tmp_path / "team")
    for symbol in SYMBOLS:
        history = snapshot.bars[snapshot.bars["symbol"] == symbol].sort_values("open_time")
        assert history["open"].iloc[0] == pytest.approx(history["close"].iloc[0])
        np.testing.assert_allclose(history["open"].to_numpy()[1:], history["close"].to_numpy()[:-1])


def test_the_research_result_is_close_to_the_official_one_but_not_equal(tmp_path) -> None:
    """The gap is the open-to-close difference, which is what a team cannot see."""
    official = _panels(tmp_path)
    approximate = research_snapshot_from_team_visible(tmp_path / "team")

    official_run = (
        run_candidate(
            Buyer(),
            snapshot=official,
            start=official.window_start,
            end=official.window_end,
            seed=1,
            record_events=False,
        )
        .costs[1]
        .returns["net_return"]
    )
    research_run = (
        run_candidate(
            Buyer(),
            snapshot=approximate,
            start=official.window_start,
            end=official.window_end,
            seed=1,
            record_events=False,
        )
        .costs[1]
        .returns["net_return"]
    )

    joined = pd.concat([official_run, research_run], axis=1, join="inner")
    difference = (joined.iloc[:, 0] - joined.iloc[:, 1]).abs()
    assert not official_run.equals(research_run)
    assert float(difference.median()) < 0.005


def test_the_official_loader_refuses_a_research_snapshot(tmp_path) -> None:
    """The approximation must never reach a charged trial by accident."""
    _panels(tmp_path)
    with pytest.raises(ValueError, match="not a CUP-50 v2 snapshot manifest"):
        load_snapshot(tmp_path / "team")


def test_a_snapshot_carrying_a_transaction_open_is_refused(tmp_path) -> None:
    """If an export ever leaked the open, this adapter must not quietly accept it."""
    _panels(tmp_path)
    team_root = tmp_path / "team"
    bars = pd.read_parquet(team_root / "bars.parquet")
    bars["open"] = bars["close"]
    bars.to_parquet(team_root / "bars.parquet", index=False)
    with pytest.raises(ValueError, match="must not carry a transaction open"):
        research_snapshot_from_team_visible(team_root)
