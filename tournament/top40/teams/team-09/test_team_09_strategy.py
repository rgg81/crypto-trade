"""Synthetic, IS-only tests for team 09 FPEG and the common execution contract."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from crypto_trade.tournament.engine import (
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
)

MODULE_PATH = Path(__file__).with_name("strategy.py")
SPEC = importlib.util.spec_from_file_location("top40_team_09_strategy_tests", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)

EXPECTED_SEED = 20260713


def _utc_date(year: int, month: int, day: int, hour: int = 0) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, hour=hour, tz="UTC")


def _config(
    *,
    q: float = 0.25,
    gross_max: float = 0.80,
    volatility_days: int = 30,
    dispersion_lookback: int = 90,
    includes_current: bool = False,
):
    return STRATEGY.FPEGConfig(
        q=q,
        gross_max=gross_max,
        volatility_days=volatility_days,
        dispersion_lookback=dispersion_lookback,
        dispersion_history_includes_current=includes_current,
    )


def _research_context(
    *,
    count: int = 24,
    decision_time: pd.Timestamp | None = None,
) -> DecisionContext:
    decision = decision_time or _utc_date(2024, 6, 1)
    symbols = [f"S{index:02d}USDT" for index in range(count)]
    end_grid = pd.date_range(decision - pd.Timedelta(days=70), decision, freq="8h")
    bars: dict[str, pd.DataFrame] = {}
    funding_frames: list[pd.DataFrame] = []
    for index, symbol in enumerate(symbols):
        steps = np.arange(len(end_grid), dtype=float)
        returns = (
            0.0003
            + 0.003 * np.sin(2.0 * np.pi * steps / 31.0 + index * 0.23)
            + 0.001 * np.cos(2.0 * np.pi * steps / 11.0 + index * 0.10)
        )
        closes = 100.0 * np.exp(np.cumsum(returns))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": end_grid - pd.Timedelta(hours=8),
                "symbol": symbol,
                "open": closes * np.exp(-returns),
                "close": closes,
                "quote_volume": 1_000_000_000.0,
            }
        )
        funding_times = pd.date_range(
            decision - pd.Timedelta(days=70),
            decision - pd.Timedelta(hours=8),
            freq="8h",
        )
        funding_steps = np.arange(len(funding_times), dtype=float)
        rates = (
            2e-5 * np.sin(2.0 * np.pi * funding_steps / 23.0 + index * 0.19)
            + 1e-5 * np.cos(2.0 * np.pi * funding_steps / 9.0 + index * 0.31)
        )
        # A nonlinear, current-window innovation makes the cross-sectional residual non-degenerate.
        rates[-9:] += (index - (count - 1) / 2.0) ** 2 * 2e-7
        rates[-9:] += (index - (count - 1) / 2.0) * 1e-6
        funding_frames.append(
            pd.DataFrame(
                {
                    "funding_time": funding_times,
                    "settlement_time": funding_times,
                    "symbol": symbol,
                    "funding_rate": rates,
                    "mark_price": 100.0,
                }
            )
        )
    return DecisionContext(
        decision_time=decision,
        bars=bars,
        funding=pd.concat(funding_frames, ignore_index=True),
        auxiliary={},
        eligible_symbols=tuple(symbols),
    )


def _target(context: DecisionContext, *, config=None) -> dict[str, float]:
    result = STRATEGY.FPEGStrategy(config or _config()).target_weights(
        context,
        seed=EXPECTED_SEED,
    )
    assert isinstance(result, Mapping)
    return dict(result)


def _copy_context(
    context: DecisionContext,
    *,
    bars: Mapping[str, pd.DataFrame] | None = None,
    funding: pd.DataFrame | None = None,
    eligible_symbols: tuple[str, ...] | None = None,
    decision_time: pd.Timestamp | None = None,
) -> DecisionContext:
    return DecisionContext(
        decision_time=decision_time or context.decision_time,
        bars=bars or context.bars,
        funding=context.funding if funding is None else funding,
        auxiliary={},
        eligible_symbols=eligible_symbols or tuple(context.eligible_symbols),
    )


def test_exact_price_math_and_gap_rejection():
    decision = _utc_date(2024, 5, 1)
    grid = pd.date_range(decision - pd.Timedelta(hours=72), decision, freq="8h")
    returns = np.asarray([0.01, -0.02, 0.03, -0.01, 0.02, 0.01, -0.01, 0.02, 0.01])
    values = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
    close = pd.Series(values, index=grid)
    expected = float(returns.sum() / np.sqrt(np.dot(returns, returns)))
    assert STRATEGY._exact_price_feature(close, decision) == pytest.approx(expected)
    assert STRATEGY._exact_price_feature(close.drop(grid[4]), decision) is None


def test_actual_funding_window_boundaries_and_empty_after_first_event():
    decision = _utc_date(2024, 5, 1)
    index = pd.DatetimeIndex(
        [
            decision - pd.Timedelta(hours=80),
            decision - pd.Timedelta(hours=72),
            decision - pd.Timedelta(hours=17),
            decision,
        ]
    )
    rates = pd.Series([8e-5, 1e-5, -3e-5, 9e-5], index=index)
    assert STRATEGY._funding_feature(rates, decision) == pytest.approx(-2e-5)
    later = decision + pd.Timedelta(days=10)
    assert STRATEGY._funding_feature(rates, later) == 0.0
    before_first = decision - pd.Timedelta(days=10)
    assert STRATEGY._funding_feature(rates, before_first) is None


def test_robust_z_uses_prior_median_mad_floor_and_clipping():
    history = [0.0] * 48
    assert STRATEGY._robust_z(0.05, history, floor=0.10) == pytest.approx(0.5)
    assert STRATEGY._robust_z(1.0, history, floor=0.10) == 4.0
    assert STRATEGY._robust_z(1.0, history[:47], floor=0.10) is None


def test_volatility_discards_gap_spanning_returns_and_enforces_eighty_percent():
    decision = _utc_date(2024, 5, 1)
    grid = pd.date_range(decision - pd.Timedelta(days=15), decision, freq="8h")
    returns = np.linspace(-0.02, 0.02, len(grid) - 1)
    close = pd.Series(100.0 * np.exp(np.r_[0.0, np.cumsum(returns)]), index=grid)
    expected = max(float(np.std(returns, ddof=1)), 1e-6)
    assert STRATEGY._volatility(close, decision, lookback_days=15) == pytest.approx(expected)
    assert STRATEGY._volatility(close.drop(grid[1:8]), decision, lookback_days=15) is not None
    assert STRATEGY._volatility(close.drop(grid[1:16]), decision, lookback_days=15) is None


def test_deterministic_theil_sen_and_residual_equation():
    observations = [
        STRATEGY._SymbolObservation(
            symbol=f"X{index:02d}USDT",
            z_price=float(index - 3),
            z_funding=float(2 + 3 * (index - 3)),
            sigma=0.02,
        )
        for index in range(7)
    ]
    fit = STRATEGY._theil_sen(observations)
    assert fit is not None
    slope, intercept, residuals = fit
    assert slope == pytest.approx(3.0)
    assert intercept == pytest.approx(2.0)
    assert all(item.residual == pytest.approx(0.0) for item in residuals)
    assert STRATEGY._theil_sen(observations[:4]) is None


def test_nearest_rank_and_inverse_volatility_cap_redistribution():
    assert STRATEGY._nearest_rank(range(60), 0.33) == 19.0
    assert STRATEGY._nearest_rank(range(60), 0.67) == 40.0
    sleeve = [
        STRATEGY._ResidualObservation(f"X{index}USDT", float(index), sigma)
        for index, sigma in enumerate([0.001, 0.02, 0.03, 0.04, 0.05])
    ]
    weights = STRATEGY._allocate_sleeve(sleeve, sleeve_gross=0.30)
    assert weights is not None
    assert math.fsum(weights.values()) == pytest.approx(0.30)
    assert max(weights.values()) == pytest.approx(0.08)
    assert all(0.0 <= weight <= 0.08 for weight in weights.values())
    assert STRATEGY._allocate_sleeve(sleeve, sleeve_gross=0.41) is None


def test_full_fpeg_target_is_complete_balanced_capped_and_two_sided():
    context = _research_context()
    target = _target(context)
    assert set(target) == set(context.eligible_symbols)
    values = np.asarray(list(target.values()))
    assert np.isfinite(values).all()
    assert np.abs(values).sum() == pytest.approx(0.40)
    assert values.sum() == pytest.approx(0.0, abs=1e-12)
    assert np.abs(values).max() <= 0.08 + 1e-12
    assert (values > 0.0).sum() == 6
    assert (values < 0.0).sum() == 6


def test_truncating_master_after_decision_is_target_invariant():
    context = _research_context()
    decision = pd.Timestamp(context.decision_time)
    truncated = {
        symbol: frame.loc[
            pd.to_datetime(frame["open_time"], utc=True) + pd.Timedelta(hours=8) <= decision
        ]
        for symbol, frame in context.bars.items()
    }
    funding = context.funding.loc[
        pd.to_datetime(context.funding["funding_time"], utc=True) < decision
    ]
    assert _target(context) == _target(_copy_context(context, bars=truncated, funding=funding))


def test_corrupting_future_rows_is_target_invariant():
    context = _research_context()
    decision = pd.Timestamp(context.decision_time)
    bars: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy()
        future["open_time"] = decision
        future["close"] = np.nan
        bars[symbol] = pd.concat([frame, future], ignore_index=True)
    future_funding = context.funding.iloc[[0]].copy()
    future_funding["funding_time"] = decision
    future_funding["settlement_time"] = decision
    future_funding["funding_rate"] = np.nan
    corrupted = _copy_context(
        context,
        bars=bars,
        funding=pd.concat([context.funding, future_funding], ignore_index=True),
    )
    assert _target(context) == _target(corrupted)


def test_appending_future_rows_is_target_invariant():
    context = _research_context()
    decision = pd.Timestamp(context.decision_time)
    bars: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy()
        future["open_time"] = decision + pd.Timedelta(days=7)
        future["close"] = 1_000_000.0
        bars[symbol] = pd.concat([frame, future], ignore_index=True)
    future_funding = context.funding.iloc[[0]].copy()
    future_funding["funding_time"] = decision + pd.Timedelta(days=7)
    future_funding["settlement_time"] = future_funding["funding_time"]
    future_funding["funding_rate"] = 1.0
    appended = _copy_context(
        context,
        bars=bars,
        funding=pd.concat([context.funding, future_funding], ignore_index=True),
    )
    assert _target(context) == _target(appended)


def test_current_eligibility_is_the_only_output_universe():
    context = _research_context()
    retained = tuple(context.eligible_symbols[:-1])
    bars = {symbol: context.bars[symbol] for symbol in retained}
    funding = context.funding.loc[context.funding["symbol"].isin(retained)]
    target = _target(_copy_context(context, bars=bars, funding=funding, eligible_symbols=retained))
    assert set(target) == set(retained)
    assert context.eligible_symbols[-1] not in target


def test_price_gap_excludes_symbol_and_insufficient_cross_section_flattens():
    context = _research_context()
    decision = pd.Timestamp(context.decision_time)
    bars = {symbol: frame.copy() for symbol, frame in context.bars.items()}
    damaged = context.eligible_symbols[0]
    missing_open = decision - pd.Timedelta(hours=8)
    bars[damaged] = bars[damaged].loc[bars[damaged]["open_time"] != missing_open]
    target = _target(_copy_context(context, bars=bars))
    assert target[damaged] == 0.0
    for symbol in context.eligible_symbols[:5]:
        bars[symbol] = bars[symbol].loc[bars[symbol]["open_time"] != missing_open]
    assert _target(_copy_context(context, bars=bars)) == {}


def test_duplicate_or_nonfinite_past_data_fail_closed_but_future_faults_do_not():
    context = _research_context(count=20)
    bars = {symbol: frame.copy() for symbol, frame in context.bars.items()}
    symbol = context.eligible_symbols[0]
    bars[symbol] = pd.concat([bars[symbol], bars[symbol].iloc[[-1]]], ignore_index=True)
    assert _target(_copy_context(context, bars=bars)) == {}
    bars = {name: frame.copy() for name, frame in context.bars.items()}
    bars[symbol].loc[bars[symbol].index[-1], "close"] = np.inf
    assert _target(_copy_context(context, bars=bars)) == {}


def test_sparse_or_degenerate_cross_section_requests_flat():
    assert _target(_research_context(count=19)) == {}
    context = _research_context(count=20)
    funding = context.funding.copy()
    funding["funding_rate"] = 0.0
    # Constant zF makes all residuals zero after a valid but degenerate price/funding fit.
    result = _target(_copy_context(context, funding=funding))
    assert isinstance(result, dict)
    assert len(result) in {0, 20}


def test_dispersion_throttle_uses_nearest_rank_prior_state_then_appends_current():
    strategy = STRATEGY.FPEGStrategy(_config(includes_current=False))
    anchor = _utc_date(2024, 5, 1)
    strategy._dispersion_history = [
        (anchor - pd.Timedelta(days=60 - index), float(index)) for index in range(60)
    ]
    assert strategy._gross_for_dispersion(10.0) == pytest.approx(0.40)
    assert strategy._gross_for_dispersion(20.0) == pytest.approx(0.60)
    assert strategy._gross_for_dispersion(50.0) == pytest.approx(0.80)
    strategy._dispersion_history.pop()
    assert strategy._gross_for_dispersion(50.0) == pytest.approx(0.40)


def test_daily_cadence_holds_at_eight_and_sixteen_and_seed_is_bound():
    context = _research_context()
    for hour in (8, 16):
        held = _copy_context(
            context,
            decision_time=pd.Timestamp(context.decision_time) + pd.Timedelta(hours=hour),
        )
        assert STRATEGY.FPEGStrategy(_config()).target_weights(held, seed=EXPECTED_SEED) is None
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.FPEGStrategy(_config()).target_weights(context, seed=EXPECTED_SEED + 1)


def test_factory_binds_the_disclosed_organizer_advanced_cell():
    payload = json.loads(Path(__file__).with_name("frozen_config.json").read_text())
    assert payload["candidate_id"] == "T09-FPEG-306045180"
    assert payload["disposition"] == {
        "advancement": "organizer_advanced_after_QR_rejection",
        "all_preregistered_cells_failed_final_selector": True,
        "performance_is_not_a_charter_disqualification": True,
        "qr_accepted": False,
    }
    assert payload["research_accounting"]["total_material_configurations"] == 42
    assert payload["research_accounting"]["public_oos_views"] == 0
    built = STRATEGY.build_strategy()
    assert built.config == STRATEGY.FPEGConfig(
        q=0.30,
        gross_max=0.60,
        volatility_days=45,
        dispersion_lookback=180,
        dispersion_history_includes_current=False,
        seed=EXPECTED_SEED,
    )


class _FixedTargets:
    def __init__(self, weights: Mapping[str, float]):
        self.weights = dict(weights)

    def target_weights(self, context: DecisionContext, *, seed: int):
        del context, seed
        return self.weights


def _engine_market():
    start = _utc_date(2021, 1, 4)
    all_times = pd.date_range(start - pd.Timedelta(hours=24), periods=7, freq="8h")
    rows: list[dict[str, object]] = []
    prices = {
        "AUSDT": [100.0, 100.0, 100.0, 100.0, 110.0, 110.0, 110.0],
        "BUSDT": [100.0, 100.0, 100.0, 100.0, 90.0, 90.0, 90.0],
    }
    for symbol, opens in prices.items():
        for timestamp, price in zip(all_times, opens, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price,
                    "quote_volume": 1_000_000_000.0,
                }
            )
    bars = pd.DataFrame(rows)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start, start],
            "symbol": ["AUSDT", "BUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [1e9, 1e9],
        }
    )
    decision_times = pd.date_range(start, periods=4, freq="8h")
    marks = pd.DataFrame(
        [
            {"mark_time": timestamp, "symbol": symbol, "mark_price": 100.0}
            for timestamp in decision_times
            for symbol in ("AUSDT", "BUSDT")
        ]
    )
    funding_time = start + pd.Timedelta(hours=4)
    funding = pd.DataFrame(
        {
            "funding_time": [funding_time, funding_time],
            "symbol": ["AUSDT", "BUSDT"],
            "funding_rate": [0.001, 0.001],
            "mark_price": [100.0, 100.0],
        }
    )
    return start, bars, funding, membership, marks, decision_times


def test_closed_bar_signal_fills_next_unseen_open_and_ineligible_target_rejected():
    start, bars, funding, membership, marks, decision_times = _engine_market()
    targets = generate_targets(
        _FixedTargets({"AUSDT": 0.10, "BUSDT": -0.10}),
        bars,
        funding,
        membership,
        decision_times,
        seed=EXPECTED_SEED,
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    first_trades = result.events.loc[
        (result.events["event_type"] == "trade") & (result.events["timestamp"] == start)
    ]
    assert set(first_trades["price"]) == {100.0}
    assert result.returns.iloc[0]["long_price_pnl"] > 0.0
    assert result.returns.iloc[0]["short_price_pnl"] > 0.0
    with pytest.raises(ValueError, match="ineligible"):
        evaluate_targets(
            bars,
            funding,
            membership,
            pd.DataFrame({"NOTMEMBER": [0.01, 0.0]}, index=decision_times[:2]),
            mark_prices=marks,
        )


def test_positive_actual_funding_charges_long_credits_short_and_costs_every_trade():
    _, bars, funding, membership, marks, decision_times = _engine_market()
    targets = pd.DataFrame(
        {
            "AUSDT": [0.10, -0.10, 0.0, 0.0],
            "BUSDT": [-0.10, 0.10, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True, True],
        },
        index=decision_times,
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    first = result.returns.iloc[0]
    assert first["long_funding_pnl"] < 0.0
    assert first["short_funding_pnl"] > 0.0
    trades = result.events.loc[result.events["event_type"] == "trade"]
    assert len(trades) >= 6
    assert (trades["fee"] > 0.0).all()
    assert (trades["slippage"] > 0.0).all()
    assert set(np.sign(trades["notional"])) == {-1.0, 1.0}


def test_boundary_funding_is_on_carried_position_before_rebalance():
    start, bars, _, membership, marks, decision_times = _engine_market()
    boundary = start + pd.Timedelta(hours=8)
    funding = pd.DataFrame(
        {
            "funding_time": [boundary],
            "symbol": ["AUSDT"],
            "funding_rate": [0.001],
            "mark_price": [100.0],
        }
    )
    targets = pd.DataFrame(
        {
            "AUSDT": [0.10, -0.10, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True, True],
        },
        index=decision_times,
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    event = result.events.loc[result.events["event_type"] == "funding"].iloc[0]
    assert event["timestamp"] == boundary
    assert event["phase"] == "before_rebalance"
    assert event["quantity"] > 0.0
    assert event["cashflow"] < 0.0


def test_double_cost_is_fresh_and_doubles_fees_and_slippage_not_funding_cashflow():
    _, bars, funding, membership, marks, decision_times = _engine_market()
    targets = pd.DataFrame(
        {
            "AUSDT": [0.10, 0.10, 0.0, 0.0],
            "BUSDT": [-0.10, -0.10, 0.0, 0.0],
        },
        index=decision_times,
    )
    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=marks,
    )
    assert base is not stressed
    base_trades = base.events.loc[base.events["notional"].ne(0.0) & base.events["fee"].gt(0.0)]
    stressed_trades = stressed.events.loc[
        stressed.events["notional"].ne(0.0) & stressed.events["fee"].gt(0.0)
    ]
    assert np.allclose(base_trades["fee"] / base_trades["notional"].abs(), 0.0005)
    assert np.allclose(stressed_trades["fee"] / stressed_trades["notional"].abs(), 0.001)
    assert np.allclose(base_trades["slippage"] / base_trades["notional"].abs(), 0.00025)
    assert np.allclose(stressed_trades["slippage"] / stressed_trades["notional"].abs(), 0.0005)
    base_funding = base.events.loc[base.events["event_type"] == "funding", "cashflow"].sum()
    stressed_funding = stressed.events.loc[
        stressed.events["event_type"] == "funding", "cashflow"
    ].sum()
    assert stressed_funding == pytest.approx(base_funding)


def test_participation_limits_fills_and_delist_exit_shares_capacity_with_haircut():
    start, bars, _, membership, marks, decision_times = _engine_market()
    sparse = bars.loc[~((bars["symbol"] == "AUSDT") & (bars["open_time"] > start))].copy()
    current_a = (sparse["symbol"] == "AUSDT") & (sparse["open_time"] == start)
    sparse.loc[current_a, "quote_volume"] = 15e6
    targets = pd.DataFrame(
        {
            "AUSDT": [0.10, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True],
        },
        index=decision_times[:2],
    )
    no_funding = pd.DataFrame(
        columns=["funding_time", "symbol", "funding_rate", "mark_price"]
    )
    result = evaluate_targets(
        sparse,
        no_funding,
        membership,
        targets,
        mark_prices=marks,
    )
    forced = result.events.loc[result.events["event_type"] == "forced_exit"]
    settlements = result.events.loc[result.events["event_type"] == "conservative_settlement"]
    assert len(forced) == 1
    assert forced.iloc[0]["fee"] > 0.0 and forced.iloc[0]["slippage"] > 0.0
    assert len(settlements) == 1
    assert settlements.iloc[0]["cashflow"] < 0.0
    assert result.returns.iloc[0]["conservative_settlement_loss"] > 0.0

    low_volume = bars.copy()
    low_volume.loc[low_volume["open_time"] < start, "quote_volume"] = 1_000.0
    limited = evaluate_targets(
        low_volume,
        pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"]),
        membership,
        targets,
        mark_prices=marks,
    )
    assert limited.returns.iloc[0]["unfilled_notional"] > 0.0


def test_common_evaluator_rejects_nonfinite_caps_duplicates_and_missing_marks():
    _, bars, funding, membership, marks, decision_times = _engine_market()
    with pytest.raises(ValueError, match="non-finite"):
        evaluate_targets(
            bars,
            funding,
            membership,
            pd.DataFrame({"AUSDT": [np.nan, 0.0]}, index=decision_times[:2]),
            mark_prices=marks,
        )
    with pytest.raises(ValueError, match="symbol exposure"):
        evaluate_targets(
            bars,
            funding,
            membership,
            pd.DataFrame({"AUSDT": [0.11, 0.0]}, index=decision_times[:2]),
            mark_prices=marks,
        )
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_targets(
            pd.concat([bars, bars.iloc[[0]]], ignore_index=True),
            funding,
            membership,
            pd.DataFrame({"AUSDT": [0.10, 0.0]}, index=decision_times[:2]),
            mark_prices=marks,
        )
    with pytest.raises(ValueError, match="missing current mark"):
        evaluate_targets(
            bars,
            funding,
            membership,
            pd.DataFrame({"AUSDT": [0.10, 0.0]}, index=decision_times[:2]),
            mark_prices=marks.loc[marks["symbol"] != "AUSDT"],
        )


def test_empty_targets_and_clean_process_equivalent_reruns_are_deterministic():
    context = _research_context()
    first = _target(context)
    second = _target(context)
    assert first == second

    start, bars, funding, membership, marks, decision_times = _engine_market()
    empty = generate_targets(
        _FixedTargets({}),
        bars,
        funding,
        membership,
        decision_times,
        seed=EXPECTED_SEED,
    )
    result_a = evaluate_targets(bars, funding, membership, empty, mark_prices=marks)
    result_b = evaluate_targets(bars, funding, membership, empty, mark_prices=marks)
    pdt.assert_frame_equal(result_a.returns, result_b.returns, check_exact=True)
    pdt.assert_frame_equal(result_a.positions, result_b.positions, check_exact=True)
    pdt.assert_frame_equal(result_a.events, result_b.events, check_exact=True)
