from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN


def _market() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    times = pd.date_range("2024-01-01", periods=4, freq="8h", tz="UTC")
    rows = []
    for symbol, prices in {
        "AAAUSDT": [100.0, 100.0, 110.0, 110.0],
        "BBBUSDT": [100.0, 100.0, 90.0, 90.0],
    }.items():
        for timestamp, price in zip(times, prices, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price,
                    "quote_volume": 1_000_000.0,
                }
            )
    bars = pd.DataFrame(rows)
    funding = pd.DataFrame(
        {
            "funding_time": [times[1] + pd.Timedelta(hours=4)] * 2,
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "funding_rate": [0.01, 0.01],
            "mark_price": [100.0, 100.0],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0]],
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [2.0, 1.0],
        }
    )
    return bars, funding, membership, times


def _config() -> EvaluatorConfig:
    return EvaluatorConfig(max_bar_participation=1.0, max_symbol_exposure=0.20)


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return bars.loc[:, ["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )


def test_next_open_long_short_pnl_and_funding_sign_reconcile():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1, "BBBUSDT": -0.1}, {"AAAUSDT": 0.1, "BBBUSDT": -0.1}],
        index=[times[1], times[2]],
    )
    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    row = result.returns.iloc[0]
    assert row["price_pnl"] == pytest.approx(0.02)
    # Equal long and short notionals cancel when both pay/receive the same positive funding rate.
    assert row["funding_pnl"] == pytest.approx(0.0)
    assert row["long_price_pnl"] + row["short_price_pnl"] == pytest.approx(row["price_pnl"])
    assert row["long_funding_pnl"] + row["short_funding_pnl"] == pytest.approx(row["funding_pnl"])
    assert row["turnover"] == pytest.approx(0.2)
    assert row["fees"] == pytest.approx(0.0001)
    assert row["slippage"] == pytest.approx(0.00005)
    assert row["net_return"] == pytest.approx(0.01985)
    assert {"funding", "mark_to_market", "trade"}.issubset(set(result.events["event_type"]))


def test_positive_funding_charges_long_and_double_cost_is_real_rerun():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame([{"AAAUSDT": 0.1}, {"AAAUSDT": 0.1}], index=[times[1], times[2]])
    base, stressed = evaluate_base_and_double_cost(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    assert base.returns.iloc[0]["funding_pnl"] == pytest.approx(-0.001)
    assert stressed.returns.iloc[0]["funding_pnl"] == pytest.approx(-0.001)
    assert stressed.returns.iloc[0]["fees"] == pytest.approx(2 * base.returns.iloc[0]["fees"])
    assert stressed.returns.iloc[0]["slippage"] == pytest.approx(
        2 * base.returns.iloc[0]["slippage"]
    )


def test_funding_at_rebalance_is_charged_to_carried_position_before_trade():
    bars, _, membership, times = _market()
    funding = pd.DataFrame(
        {
            "funding_time": [times[2]],
            "symbol": ["AAAUSDT"],
            "funding_rate": [0.01],
            "mark_price": [110.0],
        }
    )
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1}, {"AAAUSDT": 0.0}, {"AAAUSDT": 0.0}],
        index=[times[1], times[2], times[3]],
    )
    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    # The long held into times[2] pays funding even though it exits at the same timestamp.
    prior_equity = result.returns.iloc[0]["equity"]
    assert result.returns.iloc[1]["funding_pnl"] == pytest.approx(-110.0 / prior_equity)


def test_millisecond_jittered_funding_keeps_actual_event_time_but_uses_boundary_ordering():
    bars, _, membership, times = _market()
    actual_event_time = times[2] + pd.Timedelta(milliseconds=7)
    funding = pd.DataFrame(
        {
            "funding_time": [actual_event_time],
            "symbol": ["AAAUSDT"],
            "funding_rate": [0.01],
            "mark_price": [110.0],
        }
    )
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1}, {"AAAUSDT": 0.0}, {"AAAUSDT": 0.0}],
        index=[times[1], times[2], times[3]],
    )
    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    prior_equity = result.returns.iloc[0]["equity"]
    assert result.returns.iloc[1]["funding_pnl"] == pytest.approx(-110.0 / prior_equity)
    funding_events = result.events[result.events["event_type"] == "funding"]
    assert funding_events.iloc[0]["timestamp"] == actual_event_time
    assert funding_events.iloc[0]["phase"] == "before_rebalance"


@pytest.mark.parametrize(("target_weight", "expected_cashflow"), [(0.1, -100.0), (-0.1, 100.0)])
def test_delisting_boundary_funding_charges_only_forced_quantity_once(
    target_weight: float,
    expected_cashflow: float,
):
    bars, _, membership, times = _market()
    bars = bars[(bars["symbol"] != "AAAUSDT") | bars["open_time"].isin(times[:2])].copy()
    funding = pd.DataFrame(
        {
            "funding_time": [times[2], times[2]],
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "funding_rate": [0.01, 0.01],
            "mark_price": [100.0, 100.0],
        }
    )
    targets = pd.DataFrame(
        [
            {"AAAUSDT": target_weight, "BBBUSDT": 0.1},
            {"AAAUSDT": 0.0, "BBBUSDT": 0.1},
            {"AAAUSDT": 0.0, "BBBUSDT": 0.1},
        ],
        index=times[1:],
    )

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    boundary_events = result.events[
        result.events["event_type"].eq("funding") & result.events["timestamp"].eq(times[2])
    ]
    aaa_events = boundary_events[boundary_events["symbol"].eq("AAAUSDT")]
    bbb_events = boundary_events[boundary_events["symbol"].eq("BBBUSDT")]
    assert len(aaa_events) == 1
    assert aaa_events.iloc[0]["phase"] == "before_forced_exit"
    assert aaa_events.iloc[0]["cashflow"] == pytest.approx(expected_cashflow)
    assert len(bbb_events) == 1
    assert bbb_events.iloc[0]["phase"] == "before_rebalance"
    assert result.returns.loc[times[1], "forced_exit_boundary_funding_pnl"] == pytest.approx(
        expected_cashflow / 100_000.0
    )
    assert result.returns.loc[times[2], "forced_exit_boundary_funding_pnl"] == pytest.approx(0.0)


@pytest.mark.parametrize(("target_weight", "expected_cashflow"), [(0.1, -100.0), (-0.1, 100.0)])
def test_terminal_boundary_funding_precedes_forced_exit_for_long_and_short(
    target_weight: float,
    expected_cashflow: float,
):
    bars, _, membership, times = _market()
    bars.loc[bars["symbol"].eq("AAAUSDT"), ["open", "close"]] = 100.0
    funding = pd.DataFrame(
        {
            "funding_time": [times[3]],
            "symbol": ["AAAUSDT"],
            "funding_rate": [0.01],
            "mark_price": [100.0],
        }
    )
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
            "AAAUSDT": [target_weight, 0.0],
        },
        index=times[1:3],
    )

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    boundary_events = result.events[
        result.events["event_type"].eq("funding")
        & result.events["timestamp"].eq(times[3])
        & result.events["symbol"].eq("AAAUSDT")
    ]
    assert len(boundary_events) == 1
    assert boundary_events.iloc[0]["phase"] == "before_forced_exit"
    assert boundary_events.iloc[0]["cashflow"] == pytest.approx(expected_cashflow)
    equity_at_start = result.returns.loc[times[1], "equity"]
    assert result.returns.loc[times[2], "funding_pnl"] == pytest.approx(
        expected_cashflow / equity_at_start
    )
    assert result.returns.loc[times[2], "forced_exit_boundary_funding_pnl"] == pytest.approx(
        expected_cashflow / equity_at_start
    )


def test_ineligible_target_is_rejected():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame([{"CCCUSDT": 0.1}, {"CCCUSDT": 0.1}], index=[times[1], times[2]])
    with pytest.raises(ValueError, match="ineligible target"):
        evaluate_targets(
            bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
        )


def test_final_zero_target_is_executed_and_open_book_is_terminally_closed():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame([{"AAAUSDT": 0.1}, {"AAAUSDT": 0.0}], index=[times[1], times[2]])
    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    assert len(result.returns) == 2
    assert result.positions.iloc[-1]["AAAUSDT"] == pytest.approx(0.0)
    trades_at_end = result.events[
        (result.events["timestamp"] == times[2]) & (result.events["event_type"] == "trade")
    ]
    assert len(trades_at_end) == 1
    assert trades_at_end.iloc[0]["notional"] < 0


def test_slow_target_price_drift_triggers_costed_risk_reduction_instead_of_abort():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame([{"AAAUSDT": 0.1}, {"AAAUSDT": 0.1}], index=[times[1], times[3]])
    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=EvaluatorConfig(max_bar_participation=1.0),
    )
    reductions = result.events[result.events["event_type"] == "risk_reduction"]
    assert len(reductions) >= 1
    assert (reductions["notional"] < 0).all()
    assert result.returns["gross_exposure"].max() <= 1.0 + 1e-10
    assert result.positions.abs().max().max() <= 0.1 + 1e-10


def test_mark_notional_sizes_targets_while_transaction_open_sizes_the_trade():
    bars, funding, membership, times = _market()
    marks = _marks(bars)
    marks.loc[marks["symbol"].eq("AAAUSDT"), "mark_price"] = 200.0
    targets = pd.DataFrame([{"AAAUSDT": 0.08}, {"AAAUSDT": 0.08}], index=[times[1], times[2]])

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=marks, config=_config()
    )

    entry = result.events[
        (result.events["event_type"] == "trade") & (result.events["symbol"] == "AAAUSDT")
    ].iloc[0]
    # 8,000 USDT of marked exposure is 40 contracts at a 200 mark, but only 4,000 USDT executes
    # against the transaction open of 100.
    assert entry["quantity"] == pytest.approx(40.0)
    assert entry["notional"] == pytest.approx(4_000.0)
    assert result.positions.iloc[0]["AAAUSDT"] == pytest.approx(0.08, rel=1e-3)


def test_mark_drift_and_execution_costs_trigger_immediate_costed_cap_reductions():
    bars, _, membership, times = _market()
    bars.loc[bars["symbol"].eq("AAAUSDT"), ["open", "close"]] = 100.0
    marks = _marks(bars)
    marks.loc[marks["symbol"].eq("AAAUSDT") & marks["mark_time"].eq(times[2]), "mark_price"] = 200.0
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    targets = pd.DataFrame([{"AAAUSDT": 0.08}, {"AAAUSDT": 0.08}], index=[times[1], times[3]])
    config = EvaluatorConfig(max_bar_participation=1.0)

    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks, config=config)

    mark_reduction = result.events[
        (result.events["timestamp"] == times[2]) & (result.events["event_type"] == "risk_reduction")
    ]
    assert len(mark_reduction) == 1
    assert mark_reduction.iloc[0]["notional"] < 0.0
    assert result.positions.loc[times[2], "AAAUSDT"] <= 0.1 + 1e-10
    assert not bool(result.returns.loc[times[2], "risk_cap_breach"])

    # A fresh target exactly at the symbol cap must also pay for its own immediate de-risk trade;
    # post-cost equity cannot be ignored when measuring exposure.
    capped_targets = pd.DataFrame(
        [{"AAAUSDT": 0.10}, {"AAAUSDT": 0.10}], index=[times[1], times[2]]
    )
    capped = evaluate_targets(
        bars,
        funding,
        membership,
        capped_targets,
        mark_prices=_marks(bars),
        config=config,
    )
    at_entry = capped.events[
        (capped.events["timestamp"] == times[1]) & (capped.events["event_type"] == "risk_reduction")
    ]
    assert len(at_entry) == 1
    assert capped.positions.loc[times[1], "AAAUSDT"] <= 0.1 + 1e-10
    assert not bool(capped.returns.loc[times[1], "risk_cap_breach"])


class _RecordingStrategy:
    def __init__(self):
        self.latest_bar_time: list[pd.Timestamp] = []
        self.latest_funding_time: list[pd.Timestamp] = []
        self.visible_symbols: list[set[str]] = []
        self.visible_funding_symbols: list[set[str]] = []

    def target_weights(self, context, *, seed):
        assert seed == 7
        self.visible_symbols.append(set(context.bars))
        self.latest_bar_time.append(
            max(frame["open_time"].max() for frame in context.bars.values())
        )
        if context.funding.empty:
            self.latest_funding_time.append(pd.NaT)
        else:
            self.latest_funding_time.append(context.funding["funding_time"].max())
        self.visible_funding_symbols.append(set(context.funding["symbol"]))
        return {context.eligible_symbols[0]: 0.1}


def test_generate_targets_exposes_only_closed_bars_and_past_funding():
    bars, funding, membership, times = _market()
    strategy = _RecordingStrategy()
    targets = generate_targets(
        strategy,
        bars,
        funding,
        membership,
        [times[1], times[2]],
        seed=7,
    )
    assert list(targets.index) == [times[1], times[2]]
    assert strategy.latest_bar_time == [times[0], times[1]]
    assert pd.isna(strategy.latest_funding_time[0])
    assert strategy.latest_funding_time[1] < times[2]
    assert strategy.visible_symbols == [{"AAAUSDT", "BBBUSDT"}] * 2


class _SparseOnceStrategy:
    def __init__(self, weight: float = 0.1):
        self.calls = 0
        self.weight = weight

    def target_weights(self, context, *, seed):
        self.calls += 1
        if self.calls == 1:
            return {"AAAUSDT": self.weight}
        return None


def test_none_holds_quantities_without_drift_retarget_turnover():
    bars, funding, membership, times = _market()
    targets = generate_targets(
        _SparseOnceStrategy(),
        bars,
        funding,
        membership,
        times[1:],
        seed=7,
    )

    assert targets[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, False, False]
    held = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    repeated = evaluate_targets(
        bars,
        funding,
        membership,
        pd.DataFrame([{"AAAUSDT": 0.1}] * 3, index=times[1:]),
        mark_prices=_marks(bars),
        config=_config(),
    )

    assert held.returns.loc[times[2], "turnover"] == pytest.approx(0.0)
    assert repeated.returns.loc[times[2], "turnover"] > 0.0
    assert REBALANCE_INSTRUCTION_COLUMN not in held.positions.columns


def test_empty_mapping_is_an_explicit_flat_rebalance_not_a_hold():
    bars, funding, membership, times = _market()

    class FlatThenHoldStrategy:
        def __init__(self):
            self.calls = 0

        def target_weights(self, context, *, seed):
            self.calls += 1
            if self.calls == 1:
                return {"AAAUSDT": 0.1}
            if self.calls == 2:
                return {}
            return None

    targets = generate_targets(
        FlatThenHoldStrategy(),
        bars,
        funding,
        membership,
        times[1:],
        seed=7,
    )
    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    assert targets[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, True, False]
    assert result.returns.loc[times[2], "turnover"] > 0.0
    assert result.positions.loc[times[2], "AAAUSDT"] == pytest.approx(0.0)


def test_none_still_enforces_membership_exits():
    bars, funding, _, times = _market()
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0], times[2]],
            "symbol": ["AAAUSDT", "BBBUSDT", "BBBUSDT"],
            "liquidity_rank": [1, 2, 1],
            "trailing_quote_volume": [2.0, 1.0, 2.0],
        }
    )
    targets = generate_targets(
        _SparseOnceStrategy(),
        bars,
        funding,
        membership,
        times[1:],
        seed=7,
    )

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    membership_exit = result.events[
        result.events["timestamp"].eq(times[2])
        & result.events["symbol"].eq("AAAUSDT")
        & result.events["event_type"].eq("trade")
    ]
    assert not bool(targets.loc[times[2], REBALANCE_INSTRUCTION_COLUMN])
    assert len(membership_exit) == 1
    assert membership_exit.iloc[0]["notional"] < 0.0
    assert result.positions.loc[times[2], "AAAUSDT"] == pytest.approx(0.0)


def test_none_still_runs_central_per_bar_risk_reductions():
    times = pd.date_range("2024-01-01", periods=4, freq="8h", tz="UTC")
    prices = [100.0, 100.0, 400.0, 400.0]
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": "AAAUSDT",
            "open": prices,
            "close": prices,
            "quote_volume": 1_000_000_000.0,
        }
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]],
            "symbol": ["AAAUSDT"],
            "liquidity_rank": [1],
            "trailing_quote_volume": [1.0],
        }
    )
    targets = generate_targets(
        _SparseOnceStrategy(weight=0.05),
        bars,
        funding,
        membership,
        times[1:],
        seed=7,
    )
    config = EvaluatorConfig(max_bar_participation=1.0, max_symbol_exposure=0.1)

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=config
    )

    reductions = result.events[
        result.events["timestamp"].eq(times[2]) & result.events["event_type"].eq("risk_reduction")
    ]
    assert not bool(targets.loc[times[2], REBALANCE_INSTRUCTION_COLUMN])
    assert len(reductions) == 1
    assert result.returns.loc[times[2], "risk_reduction_turnover"] > 0.0
    assert result.positions.loc[times[2], "AAAUSDT"] <= 0.1 + 1e-10


def test_generate_targets_hides_out_of_universe_market_and_funding_rows():
    bars, funding, membership, times = _market()
    membership = membership[membership["symbol"] == "AAAUSDT"].copy()
    strategy = _RecordingStrategy()
    generate_targets(
        strategy,
        bars,
        funding,
        membership,
        [times[2]],
        seed=7,
    )
    assert strategy.visible_symbols == [{"AAAUSDT"}]
    assert strategy.visible_funding_symbols == [{"AAAUSDT"}]


class _FillableStrategy:
    def __init__(self):
        self.eligible: list[tuple[str, ...]] = []
        self.visible: list[set[str]] = []

    def target_weights(self, context, *, seed):
        self.eligible.append(tuple(context.eligible_symbols))
        self.visible.append(set(context.bars))
        return {symbol: 0.1 for symbol in context.eligible_symbols if symbol == "AAAUSDT"}


def test_midweek_missing_bar_is_hidden_and_position_exits_at_last_close_with_costs():
    bars, _, membership, times = _market()
    # AAA remains in weekly membership but stops printing after times[1]. BBB keeps the common
    # evaluation clock alive through the rest of the week.
    bars = bars[(bars["symbol"] != "AAAUSDT") | bars["open_time"].isin(times[:2])].copy()
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    strategy = _FillableStrategy()

    targets = generate_targets(
        strategy,
        bars,
        funding,
        membership,
        times[1:],
        seed=7,
    )

    assert strategy.eligible[0] == ("AAAUSDT", "BBBUSDT")
    assert strategy.eligible[1:] == [("BBBUSDT",), ("BBBUSDT",)]
    assert strategy.visible[0] == {"AAAUSDT", "BBBUSDT"}
    assert strategy.visible[1:] == [{"BBBUSDT"}, {"BBBUSDT"}]
    assert targets.loc[times[1], "AAAUSDT"] == pytest.approx(0.1)
    assert (targets.loc[times[2] :, "AAAUSDT"] == 0.0).all()

    result = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    forced = result.events[
        (result.events["event_type"] == "forced_exit") & (result.events["symbol"] == "AAAUSDT")
    ]
    assert len(forced) == 1
    assert forced.iloc[0]["timestamp"] == times[2]
    assert forced.iloc[0]["phase"] == "delisting"
    assert forced.iloc[0]["price"] == pytest.approx(100.0)
    assert forced.iloc[0]["fee"] > 0.0
    assert forced.iloc[0]["slippage"] > 0.0
    assert result.returns.loc[times[1], "forced_exit_turnover"] > 0.0
    assert result.returns.loc[times[1], "fees"] > 0.0
    assert result.returns.loc[times[1], "slippage"] > 0.0
    assert result.positions.loc[times[2] :, "AAAUSDT"].eq(0.0).all()


@pytest.mark.parametrize("target_weight", [0.1, -0.1])
def test_delisting_exit_is_participation_capped_and_residual_is_conservatively_settled(
    target_weight: float,
):
    bars, funding, membership, times = _market()
    bars = bars[(bars["symbol"] != "AAAUSDT") | bars["open_time"].isin(times[:3])].copy()
    # Entry capacity is ample using only prior bars.  The final executable AAA bar supports only
    # 5,000 USDT at the configured participation rate, less than the 11,000 USDT carried notional.
    bars.loc[bars["symbol"].eq("AAAUSDT") & bars["open_time"].eq(times[0]), "quote_volume"] = (
        100_000_000.0
    )
    bars.loc[bars["symbol"].eq("AAAUSDT") & bars["open_time"].eq(times[2]), "quote_volume"] = (
        5_000_000.0
    )
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False, False],
            "AAAUSDT": [target_weight, 0.0, 0.0],
        },
        index=times[1:],
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=EvaluatorConfig(max_bar_participation=0.001, max_symbol_exposure=0.2),
    )

    row = result.returns.loc[times[2]]
    forced = result.events[
        result.events["symbol"].eq("AAAUSDT") & result.events["event_type"].eq("forced_exit")
    ].iloc[0]
    settlement = result.events[
        result.events["symbol"].eq("AAAUSDT")
        & result.events["event_type"].eq("conservative_settlement")
    ].iloc[0]
    assert abs(forced["notional"]) == pytest.approx(5_000.0)
    assert row["forced_exit_requested_notional"] == pytest.approx(11_000.0)
    assert row["forced_exit_unfilled_notional"] == pytest.approx(6_000.0)
    assert row["conservative_settlement_notional"] == pytest.approx(6_000.0)
    assert row["terminal_unresolved_notional"] == pytest.approx(0.0)
    assert row["price_pnl"] == pytest.approx(-6_000.0 / result.returns.loc[times[1], "equity"])
    assert settlement["phase"] == "delisting_residual_100pct_haircut"
    assert settlement["cashflow"] == pytest.approx(-6_000.0)
    assert result.positions.loc[times[3], "AAAUSDT"] == pytest.approx(0.0)


def test_terminal_exit_reports_unresolved_capacity_residual_without_delisting_haircut():
    bars, funding, membership, times = _market()
    bars.loc[bars["symbol"].eq("AAAUSDT") & bars["open_time"].eq(times[0]), "quote_volume"] = (
        100_000_000.0
    )
    bars.loc[bars["symbol"].eq("AAAUSDT") & bars["open_time"].eq(times[2]), "quote_volume"] = (
        10_000.0
    )
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
            "AAAUSDT": [0.1, 0.0],
        },
        index=times[1:3],
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=EvaluatorConfig(max_bar_participation=0.001, max_symbol_exposure=0.2),
    )

    row = result.returns.loc[times[2]]
    unresolved = result.events[
        result.events["symbol"].eq("AAAUSDT")
        & result.events["event_type"].eq("unresolved_residual")
    ]
    assert row["forced_exit_turnover"] > 0.0
    assert row["forced_exit_unfilled_notional"] > 10_000.0
    assert row["terminal_unresolved_notional"] == pytest.approx(
        row["forced_exit_unfilled_notional"]
    )
    assert row["conservative_settlement_notional"] == pytest.approx(0.0)
    assert len(unresolved) == 1
    assert unresolved.iloc[0]["cashflow"] == pytest.approx(0.0)


def test_nonfinite_market_or_funding_inputs_fail_loudly():
    bars, funding, membership, times = _market()
    targets = pd.DataFrame([{}, {}], index=[times[1], times[2]])
    broken_bars = bars.copy()
    broken_bars.loc[0, "open"] = float("nan")
    with pytest.raises(ValueError, match="non-finite open"):
        evaluate_targets(
            broken_bars,
            funding,
            membership,
            targets,
            mark_prices=_marks(bars),
            config=_config(),
        )
    broken_funding = funding.copy()
    broken_funding.loc[0, "mark_price"] = float("nan")
    with pytest.raises(ValueError, match="non-finite mark_price"):
        evaluate_targets(
            bars,
            broken_funding,
            membership,
            targets,
            mark_prices=_marks(bars),
            config=_config(),
        )
    missing_mark = _marks(bars)
    missing_mark = missing_mark[
        ~(missing_mark["symbol"].eq("AAAUSDT") & missing_mark["mark_time"].eq(times[1]))
    ]
    with pytest.raises(ValueError, match="missing current mark for eligible symbols"):
        evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=missing_mark,
            config=_config(),
        )


def test_nonfinite_strategy_and_target_frame_weights_fail_loudly():
    bars, funding, membership, times = _market()

    class NonFiniteStrategy:
        def target_weights(self, context, *, seed):
            return {context.eligible_symbols[0]: float("nan")}

    with pytest.raises(ValueError, match="non-finite target weight"):
        generate_targets(
            NonFiniteStrategy(),
            bars,
            funding,
            membership,
            [times[1], times[2]],
            seed=7,
        )

    targets = pd.DataFrame(
        [{"AAAUSDT": float("nan")}, {"AAAUSDT": 0.0}],
        index=[times[1], times[2]],
    )
    with pytest.raises(ValueError, match="non-finite target weight"):
        evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=_marks(bars),
            config=_config(),
        )
