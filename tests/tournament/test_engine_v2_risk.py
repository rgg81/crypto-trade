from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import engine, engine_v2
from crypto_trade.tournament.engine_v2 import (
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.risk_policy import RiskPolicy, risk_policy_from_dict


def _policy(**changes: object) -> RiskPolicy:
    path = Path(__file__).parents[2] / "tournament/top40-v2/templates/risk-policy.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["policy_id"] = "engine-test"
    for key, value in changes.items():
        raw[key] = value
    return risk_policy_from_dict(raw)


def _market(
    prices_by_symbol: dict[str, list[float]],
    *,
    lows_by_symbol: dict[str, list[float]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    periods = len(next(iter(prices_by_symbol.values())))
    times = pd.date_range("2024-01-01", periods=periods, freq="8h", tz="UTC")
    rows: list[dict[str, object]] = []
    for symbol, prices in prices_by_symbol.items():
        assert len(prices) == periods
        lows = (lows_by_symbol or {}).get(symbol, prices)
        for timestamp, price, low in zip(times, prices, lows, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "high": max(price, low),
                    "low": low,
                    "close": price,
                    "quote_volume": 1_000_000_000.0,
                }
            )
    bars = pd.DataFrame(rows)
    funding = pd.DataFrame(
        columns=["funding_time", "symbol", "funding_rate", "mark_price"]
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(prices_by_symbol),
            "symbol": list(prices_by_symbol),
            "liquidity_rank": range(1, len(prices_by_symbol) + 1),
            "trailing_quote_volume": range(len(prices_by_symbol), 0, -1),
        }
    )
    return bars, funding, membership, times


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return bars.loc[:, ["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )


def _config() -> EvaluatorConfig:
    return EvaluatorConfig(max_bar_participation=1.0, max_symbol_exposure=0.20)


def test_no_policy_preserves_v1_evaluator_behavior() -> None:
    bars, funding, membership, times = _market(
        {"AAAUSDT": [100.0, 100.0, 110.0, 110.0]}
    )
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1}, {"AAAUSDT": 0.0}], index=[times[1], times[2]]
    )

    expected = engine.evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )
    actual = evaluate_targets(
        bars, funding, membership, targets, mark_prices=_marks(bars), config=_config()
    )

    pd.testing.assert_frame_equal(actual.returns, expected.returns)
    pd.testing.assert_frame_equal(actual.positions, expected.positions)
    pd.testing.assert_frame_equal(actual.events, expected.events)


def test_causal_symbol_admission_preserves_the_established_arithmetic_axis() -> None:
    symbol_count = 667
    times = pd.date_range("2024-01-01", periods=4, freq="8h", tz="UTC")
    symbols = [f"S{index:03d}USDT" for index in range(symbol_count)]
    rng = np.random.default_rng(4)
    active_indices = np.sort(rng.choice(symbol_count, 17, replace=False))
    active = {
        symbols[index]: (weight, move)
        for index, weight, move in zip(
            active_indices,
            rng.uniform(0.002, 0.01, 17),
            rng.normal(0.0, 1.0, 17),
            strict=True,
        )
    }
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        move = active.get(symbol, (0.0, 0.0))[1]
        for timestamp, price in zip(
            times,
            [100.0, 100.0, 100.0 + move, 100.0 + move],
            strict=True,
        ):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "quote_volume": 1_000_000_000.0,
                }
            )
    bars = pd.DataFrame(rows)
    funding = pd.DataFrame(
        columns=["funding_time", "symbol", "funding_rate", "mark_price"]
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * symbol_count,
            "symbol": symbols,
            "liquidity_rank": range(1, symbol_count + 1),
            "trailing_quote_volume": range(symbol_count, 0, -1),
        }
    )
    target = {symbol: active.get(symbol, (0.0, 0.0))[0] for symbol in symbols}
    targets = pd.DataFrame([target, target], index=times[1:3])
    config = EvaluatorConfig(
        taker_fee_bps_per_side=0.0,
        slippage_bps_per_side=0.0,
        max_bar_participation=1.0,
        max_symbol_exposure=0.20,
    )
    baseline = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=config,
    )

    added_symbol = "A_NEWUSDT"
    for added_time in (times[0], times[2]):
        added_bar = pd.DataFrame(
            [
                {
                    "open_time": added_time,
                    "symbol": added_symbol,
                    "open": 100.0,
                    "high": 100.0,
                    "low": 100.0,
                    "close": 100.0,
                    "quote_volume": 1_000_000_000.0,
                }
            ]
        )
        augmented_bars = pd.concat([bars, added_bar], ignore_index=True)
        augmented_targets = targets.assign(**{added_symbol: 0.0})
        augmented = evaluate_targets(
            augmented_bars,
            funding,
            membership,
            augmented_targets,
            mark_prices=_marks(augmented_bars),
            config=config,
            initial_symbols=symbols,
        )

        pd.testing.assert_frame_equal(augmented.returns, baseline.returns, check_exact=True)
        pd.testing.assert_frame_equal(augmented.events, baseline.events, check_exact=True)
        pd.testing.assert_frame_equal(
            augmented.positions.drop(columns=added_symbol),
            baseline.positions,
            check_exact=True,
        )
        assert augmented.positions[added_symbol].eq(0.0).all()
        assert not augmented.events["symbol"].eq(added_symbol).any()


def test_causal_symbol_is_tradable_at_its_first_eligible_boundary() -> None:
    bars, funding, _, times = _market({"AAAUSDT": [100.0] * 4})
    new_bars = pd.DataFrame(
        {
            "open_time": times[1:4],
            "symbol": ["NEWUSDT"] * 3,
            "open": [100.0] * 3,
            "high": [100.0] * 3,
            "low": [100.0] * 3,
            "close": [100.0] * 3,
            "quote_volume": [1_000_000_000.0] * 3,
        }
    )
    bars = pd.concat([bars, new_bars], ignore_index=True)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[2], times[2]],
            "symbol": ["AAAUSDT", "AAAUSDT", "NEWUSDT"],
            "liquidity_rank": [1, 1, 2],
            "trailing_quote_volume": [2.0, 2.0, 1.0],
        }
    )
    targets = pd.DataFrame(
        [
            {"AAAUSDT": 0.1, "NEWUSDT": 0.0},
            {"AAAUSDT": 0.0, "NEWUSDT": 0.1},
        ],
        index=times[1:3],
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        initial_symbols=("AAAUSDT",),
    )

    assert result.positions.loc[times[1], "NEWUSDT"] == 0.0
    assert result.positions.loc[times[2], "NEWUSDT"] > 0.0
    new_trades = result.events[
        result.events["symbol"].eq("NEWUSDT")
        & result.events["event_type"].eq("trade")
    ]
    assert new_trades["timestamp"].tolist() == [times[2]]


def test_causal_symbol_nonzero_ineligible_target_still_fails_closed() -> None:
    bars, funding, membership, times = _market({"AAAUSDT": [100.0] * 4})
    new_bar = pd.DataFrame(
        [
            {
                "open_time": times[2],
                "symbol": "NEWUSDT",
                "open": 100.0,
                "high": 100.0,
                "low": 100.0,
                "close": 100.0,
                "quote_volume": 1_000_000_000.0,
            }
        ]
    )
    bars = pd.concat([bars, new_bar], ignore_index=True)
    targets = pd.DataFrame(
        [
            {"AAAUSDT": 0.0, "NEWUSDT": 0.0},
            {"AAAUSDT": 0.0, "NEWUSDT": 0.1},
        ],
        index=times[1:3],
    )

    with pytest.raises(ValueError, match="ineligible target symbols.*NEWUSDT"):
        evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=_marks(bars),
            config=_config(),
            initial_symbols=("AAAUSDT",),
        )


def test_position_stop_ignores_intrabar_low_and_exits_at_next_open_without_reentry() -> None:
    bars, funding, membership, times = _market(
        {"AAAUSDT": [100.0, 100.0, 100.0, 80.0, 80.0, 80.0]},
        lows_by_symbol={"AAAUSDT": [100.0, 100.0, 10.0, 80.0, 80.0, 80.0]},
    )
    targets = pd.DataFrame([{"AAAUSDT": 0.1}] * 4, index=times[1:5])
    policy = _policy(
        position_stop={"enabled": True, "loss_fraction": 0.10, "cooldown_bars": 2}
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=policy,
    )

    actions = result.events[result.events["event_type"].eq("risk_policy_action")]
    assert not actions["timestamp"].eq(times[2]).any()
    stop = actions[actions["timestamp"].eq(times[3])].iloc[0]
    assert stop["reason"] == "position_stop"
    assert stop["price"] == pytest.approx(80.0)
    assert stop["notional"] < 0.0
    assert stop["fee"] > 0.0
    assert stop["slippage"] > 0.0
    assert result.positions.loc[times[3], "AAAUSDT"] == pytest.approx(0.0)
    same_boundary_trades = result.events[
        result.events["timestamp"].eq(times[3])
        & result.events["event_type"].eq("trade")
    ]
    assert same_boundary_trades.empty
    block = result.events[
        result.events["timestamp"].eq(times[3])
        & result.events["event_type"].eq("risk_policy_block")
    ].iloc[0]
    assert block["reason"] == "same_boundary_reentry"


def test_same_boundary_reentry_occurs_only_when_frozen_policy_allows_it() -> None:
    bars, funding, membership, times = _market(
        {"AAAUSDT": [100.0, 100.0, 100.0, 80.0, 80.0, 80.0]}
    )
    targets = pd.DataFrame([{"AAAUSDT": 0.1}] * 4, index=times[1:5])
    policy = _policy(
        same_boundary_reentry=True,
        position_stop={"enabled": True, "loss_fraction": 0.10, "cooldown_bars": 2},
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=policy,
    )

    at_trigger = result.events[result.events["timestamp"].eq(times[3])]
    assert len(at_trigger[at_trigger["event_type"].eq("risk_policy_action")]) == 1
    reopened = at_trigger[at_trigger["event_type"].eq("trade")]
    assert len(reopened) == 1
    assert reopened.iloc[0]["notional"] > 0.0
    assert result.positions.loc[times[3], "AAAUSDT"] > 0.0


def test_double_cost_rerun_forwards_policy_and_charges_risk_actions_twice() -> None:
    bars, funding, membership, times = _market(
        {"AAAUSDT": [100.0, 100.0, 100.0, 80.0, 80.0, 80.0]}
    )
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False, False, False],
            "AAAUSDT": [0.1, 0.0, 0.0, 0.0],
        },
        index=times[1:5],
    )
    policy = _policy(
        position_stop={"enabled": True, "loss_fraction": 0.10, "cooldown_bars": 2}
    )

    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=policy,
    )

    base_action = base.events[base.events["event_type"].eq("risk_policy_action")].iloc[0]
    stressed_action = stressed.events[
        stressed.events["event_type"].eq("risk_policy_action")
    ].iloc[0]
    assert stressed_action["fee"] == pytest.approx(2 * base_action["fee"])
    assert stressed_action["slippage"] == pytest.approx(2 * base_action["slippage"])


def test_time_stop_cooldown_blocks_two_later_boundaries_then_expires() -> None:
    bars, funding, membership, times = _market(
        {"AAAUSDT": [100.0] * 8}
    )
    targets = pd.DataFrame([{"AAAUSDT": 0.1}] * 6, index=times[1:7])
    policy = _policy(
        time_stop={"enabled": True, "maximum_holding_bars": 2, "cooldown_bars": 2}
    )

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=policy,
    )

    timeout = result.events[
        result.events["timestamp"].eq(times[3])
        & result.events["event_type"].eq("risk_policy_action")
    ].iloc[0]
    assert timeout["reason"] == "time_stop"
    cooldown_blocks = result.events[
        result.events["event_type"].eq("risk_policy_block")
        & result.events["reason"].eq("cooldown")
    ]
    assert cooldown_blocks["timestamp"].tolist() == [times[4], times[5]]
    reentry = result.events[
        result.events["timestamp"].eq(times[6])
        & result.events["event_type"].eq("trade")
    ]
    assert len(reentry) == 1
    assert reentry.iloc[0]["notional"] > 0.0


def test_drawdown_brake_uses_authoritative_equity_and_reason_codes_reduction() -> None:
    bars, funding, membership, times = _market(
        {
            "AAAUSDT": [100.0, 100.0, 100.0, 100.0, 100.0],
            "BBBUSDT": [100.0, 100.0, 50.0, 50.0, 50.0],
        }
    )
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1, "BBBUSDT": 0.1}] * 3,
        index=times[1:4],
    )
    policy = _policy(drawdown_brakes=[{"drawdown": 0.04, "gross_scale": 0.5}])

    result = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=policy,
    )

    action = result.events[
        result.events["timestamp"].eq(times[2])
        & result.events["event_type"].eq("risk_policy_action")
    ].iloc[0]
    assert action["reason"] == "drawdown_brake"
    assert action["symbol"] == "AAAUSDT"
    assert action["price"] == pytest.approx(100.0)
    assert result.returns.loc[times[2], "risk_policy_gross_scale"] == 0.5
    assert result.returns.loc[times[2], "risk_policy_drawdown"] > 0.04
    assert result.positions.loc[times[2], "AAAUSDT"] == pytest.approx(0.05, rel=1e-3)
    assert result.positions.loc[times[2]].abs().sum() == pytest.approx(0.10, rel=1e-3)


def test_side_scaling_and_turnover_limit_are_applied_before_execution() -> None:
    bars, funding, membership, times = _market(
        {
            "AAAUSDT": [100.0] * 4,
            "BBBUSDT": [100.0] * 4,
        }
    )
    targets = pd.DataFrame(
        [{"AAAUSDT": 0.1, "BBBUSDT": -0.1}] * 2,
        index=times[1:3],
    )
    scaled_policy = _policy(side_scaling={"long_scale": 0.5, "short_scale": 0.25})
    scaled = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=scaled_policy,
    )
    assert scaled.positions.loc[times[1], "AAAUSDT"] == pytest.approx(0.05, rel=1e-3)
    assert scaled.positions.loc[times[1], "BBBUSDT"] == pytest.approx(-0.025, rel=1e-3)

    limited_policy = _policy(
        turnover_limit={"enabled": True, "maximum_one_way_turnover": 0.05}
    )
    limited = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=_marks(bars),
        config=_config(),
        risk_policy=limited_policy,
    )
    assert limited.returns.loc[times[1], "risk_policy_turnover"] == pytest.approx(0.0)
    assert limited.returns.loc[times[1], "turnover"] == pytest.approx(0.05)
    assert limited.positions.loc[times[1]].abs().sum() == pytest.approx(0.05, rel=1e-3)


def test_volatility_estimate_requires_only_a_complete_past_lookback() -> None:
    one_bar = [{"net_return": 0.01}]
    two_bars = [{"net_return": 0.01}, {"net_return": -0.01}]

    assert (
        engine_v2._past_annualized_volatility(
            one_bar, lookback_days=2, interval_hours=24
        )
        is None
    )
    observed = engine_v2._past_annualized_volatility(
        two_bars, lookback_days=2, interval_hours=24
    )
    assert observed == pytest.approx(pd.Series([0.01, -0.01]).std() * 365**0.5)
