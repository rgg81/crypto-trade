"""Synthetic, market-data-free tests for the team-02 FIR reference candidate."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext
from crypto_trade.tournament.risk_policy import risk_policy_from_dict

DECISION_TIME = pd.Timestamp("2023-01-05T00:00:00Z")
CUTOFF = DECISION_TIME - pd.Timedelta(hours=8)
INTERVAL = pd.Timedelta(hours=8)
TEAM_DIR = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_team02_fir_strategy", TEAM_DIR / "strategy.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load team-02 FIR strategy")
fir = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = fir
_SPEC.loader.exec_module(fir)


def synthetic_symbols(count: int = 40) -> tuple[str, ...]:
    return tuple(f"S{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, symbol_index: int, *, include_future: bool = False) -> pd.DataFrame:
    expected = fir._expected_price_times(CUTOFF, fir._REFERENCE.volatility_return_bars)
    price = 100.0 + symbol_index
    rows: list[dict[str, object]] = []
    amplitude = 0.0004 + 0.00004 * symbol_index
    for step, open_time in enumerate(expected):
        move = amplitude * math.sin(0.53 * step + 0.17 * symbol_index)
        price *= math.exp(move)
        rows.append(
            {
                "symbol": symbol,
                "open_time": open_time,
                "close_time": open_time + INTERVAL,
                "close": price,
            }
        )
    if include_future:
        rows.append(
            {
                "symbol": symbol,
                "open_time": CUTOFF,
                "close_time": DECISION_TIME,
                "close": price * 1.01,
            }
        )
    return pd.DataFrame(rows)


def synthetic_bar_map(
    symbols: tuple[str, ...] | None = None, *, include_future: bool = False
) -> dict[str, pd.DataFrame]:
    eligible = symbols or synthetic_symbols()
    return {
        symbol: _bar_frame(symbol, index, include_future=include_future)
        for index, symbol in enumerate(eligible)
    }


def synthetic_funding(
    symbols: tuple[str, ...] | None = None, *, include_future: bool = False
) -> pd.DataFrame:
    eligible = symbols or synthetic_symbols()
    midpoint = (len(eligible) - 1) / 2.0
    start = DECISION_TIME - pd.Timedelta(days=21)
    rows: list[dict[str, object]] = []
    for index, symbol in enumerate(eligible):
        centered = index - midpoint
        base = centered * 2e-6
        recent_adjustment = -centered * 2e-7
        for event in range(63):
            timestamp = start + event * INTERVAL
            rate = base + (
                recent_adjustment if timestamp >= DECISION_TIME - pd.Timedelta(days=3) else 0.0
            )
            rows.append(
                {
                    "funding_time": timestamp,
                    "symbol": symbol,
                    "funding_rate": rate,
                    "mark_price": 100.0 + index,
                }
            )
        if include_future:
            rows.append(
                {
                    "funding_time": DECISION_TIME,
                    "symbol": symbol,
                    "funding_rate": float("nan"),
                    "mark_price": 100.0 + index,
                }
            )
    return pd.DataFrame(rows)


def synthetic_context(
    *,
    symbols: tuple[str, ...] | None = None,
    decision_time: pd.Timestamp = DECISION_TIME,
    bars: dict[str, pd.DataFrame] | None = None,
    funding: pd.DataFrame | None = None,
) -> DecisionContext:
    eligible = symbols or synthetic_symbols()
    return DecisionContext(
        decision_time=decision_time,
        bars=bars or synthetic_bar_map(eligible),
        funding=synthetic_funding(eligible) if funding is None else funding,
        auxiliary={},
        eligible_symbols=eligible,
    )


def _reference_weights() -> dict[str, float]:
    result = fir.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def test_funding_level_and_relaxation_are_exact() -> None:
    symbol = synthetic_symbols(1)
    funding = synthetic_funding(symbol)
    features = fir._funding_features(
        funding,
        eligible_symbols=symbol,
        decision_time=DECISION_TIME,
    )
    assert set(features) == set(symbol)
    rates = funding["funding_rate"].tolist()
    prior = rates[:54]
    recent = rates[54:]
    expected_level = math.fsum(rates) / 21
    expected_relaxation = math.fsum(recent) / 3 - math.fsum(prior) / 18
    assert features[symbol[0]].level_per_day == expected_level
    assert features[symbol[0]].relaxation_per_day == expected_relaxation


def test_realized_volatility_formula_and_exact_window() -> None:
    frame = _bar_frame("AUSDT", 3)
    closes = frame["close"].tolist()
    returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
    mean = math.fsum(returns) / len(returns)
    expected = math.sqrt(math.fsum((value - mean) ** 2 for value in returns) / len(returns))
    assert fir._realized_volatility(frame, cutoff=CUTOFF) == expected
    assert fir._realized_volatility(frame.iloc[1:], cutoff=CUTOFF) is None


def test_average_rank_ties_and_low_volatility_filter() -> None:
    ranks = fir._average_ranks({"A": 1.0, "B": 1.0, "C": 3.0, "D": 5.0})
    assert ranks is not None
    assert ranks["A"] == ranks["B"] == 2.0 * (1.5 - 1.0) / 3.0 - 1.0
    volatility = {symbol: float(index) for index, symbol in enumerate(synthetic_symbols())}
    retained = fir._lowest_volatility_symbols(volatility)
    assert retained == synthetic_symbols(32)
    assert fir._lowest_volatility_symbols(dict(list(volatility.items())[:29])) is None


def test_funding_sign_and_relaxation_define_sleeves() -> None:
    context = synthetic_context()
    weights = _reference_weights()
    funding = fir._funding_features(
        context.funding,
        eligible_symbols=context.eligible_symbols,
        decision_time=DECISION_TIME,
    )
    long_levels = [
        funding[symbol].level_per_day for symbol, weight in weights.items() if weight > 0
    ]
    short_levels = [
        funding[symbol].level_per_day for symbol, weight in weights.items() if weight < 0
    ]
    assert math.fsum(long_levels) / len(long_levels) < math.fsum(short_levels) / len(short_levels)
    assert all(
        funding[symbol].relaxation_per_day > 0 for symbol, weight in weights.items() if weight > 0
    )
    assert all(
        funding[symbol].relaxation_per_day < 0 for symbol, weight in weights.items() if weight < 0
    )


def test_future_append_corruption_and_truncation_invariance() -> None:
    baseline = _reference_weights()
    future_bars = synthetic_bar_map(include_future=True)
    future_funding = synthetic_funding(include_future=True)
    appended = fir.build_strategy().target_weights(
        synthetic_context(bars=future_bars, funding=future_funding), seed=20260801
    )
    assert appended == baseline

    corrupted = {symbol: frame.copy(deep=True) for symbol, frame in future_bars.items()}
    for frame in corrupted.values():
        future = frame["close_time"] > CUTOFF
        frame.loc[future, "close"] = 1e200
    future_funding.loc[future_funding["funding_time"] >= DECISION_TIME, "funding_rate"] = float(
        "inf"
    )
    assert (
        fir.build_strategy().target_weights(
            synthetic_context(bars=corrupted, funding=future_funding), seed=20260801
        )
        == baseline
    )

    truncated_bars = {
        symbol: frame.loc[frame["close_time"] <= CUTOFF].copy()
        for symbol, frame in future_bars.items()
    }
    truncated_funding = future_funding.loc[future_funding["funding_time"] < DECISION_TIME].copy()
    assert (
        fir.build_strategy().target_weights(
            synthetic_context(bars=truncated_bars, funding=truncated_funding), seed=20260801
        )
        == baseline
    )


def test_missing_duplicate_stale_and_invalid_funding_fail_closed() -> None:
    symbols = synthetic_symbols()
    base = synthetic_funding(symbols)
    affected = set(symbols[:11])
    missing = base.loc[~base["symbol"].isin(affected)].copy()
    assert (
        fir.build_strategy().target_weights(synthetic_context(funding=missing), seed=20260801) == {}
    )

    duplicated = pd.concat(
        [
            base,
            base.loc[base["symbol"].isin(affected)].groupby("symbol").tail(1),
        ],
        ignore_index=True,
    )
    assert (
        fir.build_strategy().target_weights(synthetic_context(funding=duplicated), seed=20260801)
        == {}
    )

    stale = base.loc[
        ~(
            base["symbol"].isin(affected)
            & (base["funding_time"] > DECISION_TIME - pd.Timedelta(hours=24))
        )
    ].copy()
    assert (
        fir.build_strategy().target_weights(synthetic_context(funding=stale), seed=20260801) == {}
    )

    invalid = base.copy()
    invalid.loc[invalid["symbol"].isin(affected), "funding_rate"] = 0.051
    assert (
        fir.build_strategy().target_weights(synthetic_context(funding=invalid), seed=20260801) == {}
    )


def test_missing_duplicate_and_corrupt_price_window_fail_closed() -> None:
    symbols = synthetic_symbols()
    affected = symbols[:11]
    missing = synthetic_bar_map(symbols)
    for symbol in affected:
        missing[symbol] = missing[symbol].iloc[1:].copy()
    assert fir.build_strategy().target_weights(synthetic_context(bars=missing), seed=20260801) == {}

    duplicated = synthetic_bar_map(symbols)
    for symbol in affected:
        duplicated[symbol] = pd.concat(
            [duplicated[symbol], duplicated[symbol].tail(1)], ignore_index=True
        )
    assert (
        fir.build_strategy().target_weights(synthetic_context(bars=duplicated), seed=20260801) == {}
    )

    corrupt = synthetic_bar_map(symbols)
    for symbol in affected:
        corrupt[symbol].loc[corrupt[symbol].index[-1], "close"] = float("nan")
    assert fir.build_strategy().target_weights(synthetic_context(bars=corrupt), seed=20260801) == {}


def test_membership_and_input_order_determinism() -> None:
    context = synthetic_context()
    first = _reference_weights()
    extra_bars = dict(context.bars)
    extra_bars["ZZZUSDT"] = _bar_frame("ZZZUSDT", 99)
    extra_funding = pd.concat([context.funding, synthetic_funding(("ZZZUSDT",))], ignore_index=True)
    second = fir.build_strategy().target_weights(
        synthetic_context(bars=extra_bars, funding=extra_funding), seed=20260801
    )
    assert second == first
    assert "ZZZUSDT" not in second

    reordered = DecisionContext(
        decision_time=context.decision_time,
        bars={
            symbol: context.bars[symbol].iloc[::-1].reset_index(drop=True)
            for symbol in reversed(context.eligible_symbols)
        },
        funding=context.funding.iloc[::-1].reset_index(drop=True),
        auxiliary={},
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    third = fir.build_strategy().target_weights(reordered, seed=20260801)
    assert first == third
    assert json.dumps(first, sort_keys=True) == json.dumps(third, sort_keys=True)


def test_two_sleeves_gross_net_cap_and_cash_capacity() -> None:
    weights = _reference_weights()
    positives = [weight for weight in weights.values() if weight > 0]
    negatives = [weight for weight in weights.values() if weight < 0]
    assert len(positives) == len(negatives) == 8
    assert math.fsum(positives) == pytest.approx(0.20, abs=1e-12)
    assert math.fsum(-weight for weight in negatives) == pytest.approx(0.20, abs=1e-12)
    assert math.fsum(abs(weight) for weight in weights.values()) == pytest.approx(0.40, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert max(abs(weight) for weight in weights.values()) <= 0.03

    six = fir._equal_side_allocation(tuple("ABCDEF"))
    assert six is not None
    assert set(six.values()) == {0.03}
    assert math.fsum(six.values()) == pytest.approx(0.18, abs=1e-12)


def test_clock_minimum_cross_section_seed_and_context_immutability() -> None:
    too_small = synthetic_context(symbols=synthetic_symbols(29))
    assert fir.build_strategy().target_weights(too_small, seed=20260801) == {}
    off_grid = synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    assert fir.build_strategy().target_weights(off_grid, seed=20260801) == {}
    non_rebalance = synthetic_context(decision_time=DECISION_TIME + INTERVAL)
    assert fir.build_strategy().target_weights(non_rebalance, seed=20260801) is None
    with pytest.raises(ValueError, match="canonical runtime seed"):
        fir.build_strategy().target_weights(synthetic_context(), seed=2026080102)

    context = synthetic_context()
    before_bars = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    before_funding = context.funding.copy(deep=True)
    assert fir.build_strategy().target_weights(context, seed=20260801)
    for symbol in context.eligible_symbols:
        pd.testing.assert_frame_equal(context.bars[symbol], before_bars[symbol])
    pd.testing.assert_frame_equal(context.funding, before_funding)


def test_frozen_reference_and_no_control_policy_validate() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["candidate_id"] == "team-02-fir-reference-001"
    assert frozen["family_id"] == "team-02-funding-inventory-relaxation-v1"
    assert frozen["canonical_runtime_seed"] == 20260801
    assert frozen["parameters"] == {
        "funding_window_days": 21,
        "gross_target": 0.4,
        "level_weight": 0.75,
        "maximum_absolute_funding_rate": 0.05,
        "maximum_funding_staleness_hours": 16,
        "minimum_cross_section": 24,
        "minimum_prefilter_cross_section": 30,
        "minimum_prior_events": 18,
        "minimum_recent_events": 3,
        "minimum_names_per_sleeve": 6,
        "rebalance_bars": 9,
        "recent_funding_days": 3,
        "relaxation_weight": 0.25,
        "selected_fraction_per_side": "1/4",
        "side_budget": 0.2,
        "symbol_cap": 0.03,
        "volatility_keep_fraction": "4/5",
        "volatility_lookback_days": 30,
    }
    policy_raw = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(policy_raw)
    assert policy.policy_id == frozen["risk_policy_id"] == "team-02-fir-reference-no-control"
    assert not policy.enabled
    assert not policy.same_boundary_reentry
