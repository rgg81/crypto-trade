"""Synthetic, market-data-free tests for the Team 04 UTC reference."""

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
_SPEC = importlib.util.spec_from_file_location("_team04_utc_strategy", TEAM_DIR / "strategy.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load Team 04 UTC strategy")
utc = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = utc
_SPEC.loader.exec_module(utc)


def synthetic_symbols(count: int = 40) -> tuple[str, ...]:
    return tuple(f"S{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, include_future: bool = False) -> pd.DataFrame:
    expected = utc._expected_open_times(CUTOFF, utc._REFERENCE.history_return_bars)
    midpoint = 19.5
    direction = ((index - midpoint) / midpoint) * 0.001
    amplitude = 0.0003 + 0.00002 * index
    price = 100.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(expected):
        move = direction + amplitude * math.sin(0.47 * step + 0.19 * index)
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
                "close": price * 100.0,
            }
        )
    return pd.DataFrame(rows)


def synthetic_bars(
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
    start = DECISION_TIME - pd.Timedelta(days=7)
    rows: list[dict[str, object]] = []
    for index, symbol in enumerate(eligible):
        rate = -(index - midpoint) * 2e-6
        for event in range(21):
            rows.append(
                {
                    "funding_time": start + event * INTERVAL,
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
        bars=synthetic_bars(eligible) if bars is None else bars,
        funding=synthetic_funding(eligible) if funding is None else funding,
        auxiliary={},
        eligible_symbols=eligible,
    )


def _reference_weights() -> dict[str, float]:
    result = utc.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def test_exact_skipped_trend_and_volatility_formulas() -> None:
    frame = _bar_frame("AUSDT", 17)
    closes = frame["close"].tolist()
    returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
    feature = utc._price_feature(frame, cutoff=CUTOFF)
    assert feature is not None
    assert feature.slow_trend == math.fsum(returns[-132:-6])
    assert feature.fast_trend == math.fsum(returns[-45:-3])
    vol_returns = returns[-90:]
    mean = math.fsum(vol_returns) / len(vol_returns)
    expected_vol = math.sqrt(
        math.fsum((value - mean) ** 2 for value in vol_returns) / len(vol_returns)
    )
    assert feature.volatility == expected_vol
    assert utc._price_feature(frame.iloc[1:], cutoff=CUTOFF) is None


def test_exact_calendar_day_funding_sum_and_sign() -> None:
    symbols = ("AUSDT", "BUSDT")
    funding = synthetic_funding(symbols)
    result = utc._funding_per_day(
        funding,
        eligible_symbols=symbols,
        decision_time=DECISION_TIME,
    )
    for symbol in symbols:
        rates = funding.loc[funding["symbol"].eq(symbol), "funding_rate"]
        assert result[symbol] == math.fsum(rates) / 7
    assert result["AUSDT"] > result["BUSDT"]


def test_average_rank_ties_and_volatility_filter() -> None:
    ranks = utc._average_ranks({"A": 1.0, "B": 1.0, "C": 3.0, "D": 5.0})
    assert ranks is not None
    assert ranks["A"] == ranks["B"] == 2.0 * (1.5 - 1.0) / 3.0 - 1.0
    features = {
        symbol: utc._Feature(0.0, 0.0, 0.0, float(index))
        for index, symbol in enumerate(synthetic_symbols())
    }
    assert utc._retain_low_volatility(features) == synthetic_symbols(32)
    assert utc._retain_low_volatility(dict(list(features.items())[:29])) is None


def test_composite_places_uncrowded_leaders_long_and_laggards_short() -> None:
    context = synthetic_context()
    weights = _reference_weights()
    funding = utc._funding_per_day(
        context.funding,
        eligible_symbols=context.eligible_symbols,
        decision_time=DECISION_TIME,
    )
    prices = {
        symbol: utc._price_feature(context.bars[symbol], cutoff=CUTOFF)
        for symbol in context.eligible_symbols
    }
    long_slow = [prices[symbol].slow_trend for symbol, weight in weights.items() if weight > 0]
    short_slow = [prices[symbol].slow_trend for symbol, weight in weights.items() if weight < 0]
    long_funding = [funding[symbol] for symbol, weight in weights.items() if weight > 0]
    short_funding = [funding[symbol] for symbol, weight in weights.items() if weight < 0]
    assert math.fsum(long_slow) / len(long_slow) > math.fsum(short_slow) / len(short_slow)
    assert math.fsum(long_funding) / len(long_funding) < math.fsum(short_funding) / len(
        short_funding
    )


def test_future_append_corrupt_and_truncate_invariance() -> None:
    baseline = _reference_weights()
    bars = synthetic_bars(include_future=True)
    funding = synthetic_funding(include_future=True)
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(bars=bars, funding=funding), seed=20260801
        )
        == baseline
    )
    corrupted = {symbol: frame.copy(deep=True) for symbol, frame in bars.items()}
    for frame in corrupted.values():
        frame.loc[frame["close_time"] > CUTOFF, "close"] = 1e200
    funding.loc[funding["funding_time"] >= DECISION_TIME, "funding_rate"] = float("inf")
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(bars=corrupted, funding=funding), seed=20260801
        )
        == baseline
    )
    truncated_bars = {
        symbol: frame.loc[frame["close_time"] <= CUTOFF].copy() for symbol, frame in bars.items()
    }
    truncated_funding = funding.loc[funding["funding_time"] < DECISION_TIME].copy()
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(bars=truncated_bars, funding=truncated_funding), seed=20260801
        )
        == baseline
    )


def test_invalid_missing_duplicate_and_stale_funding_fail_closed() -> None:
    symbols = synthetic_symbols()
    affected = set(symbols[:11])
    base = synthetic_funding(symbols)
    missing = base.loc[~base["symbol"].isin(affected)].copy()
    assert (
        utc.build_strategy().target_weights(synthetic_context(funding=missing), seed=20260801) == {}
    )
    duplicated = pd.concat(
        [
            base,
            base.loc[base["symbol"].isin(affected)].groupby("symbol").tail(1),
        ],
        ignore_index=True,
    )
    assert (
        utc.build_strategy().target_weights(synthetic_context(funding=duplicated), seed=20260801)
        == {}
    )
    stale = base.loc[
        ~(
            base["symbol"].isin(affected)
            & (base["funding_time"] > DECISION_TIME - pd.Timedelta(hours=24))
        )
    ].copy()
    assert (
        utc.build_strategy().target_weights(synthetic_context(funding=stale), seed=20260801) == {}
    )
    invalid = base.copy()
    invalid.loc[invalid["symbol"].isin(affected), "funding_rate"] = 0.051
    assert (
        utc.build_strategy().target_weights(synthetic_context(funding=invalid), seed=20260801) == {}
    )


def test_missing_duplicate_and_nonfinite_price_history_fail_closed() -> None:
    symbols = synthetic_symbols()
    affected = symbols[:11]
    missing = synthetic_bars(symbols)
    for symbol in affected:
        missing[symbol] = missing[symbol].iloc[1:].copy()
    assert utc.build_strategy().target_weights(synthetic_context(bars=missing), seed=20260801) == {}
    duplicated = synthetic_bars(symbols)
    for symbol in affected:
        duplicated[symbol] = pd.concat(
            [duplicated[symbol], duplicated[symbol].tail(1)], ignore_index=True
        )
    assert (
        utc.build_strategy().target_weights(synthetic_context(bars=duplicated), seed=20260801) == {}
    )
    corrupted = synthetic_bars(symbols)
    for symbol in affected:
        corrupted[symbol].loc[corrupted[symbol].index[-1], "close"] = float("nan")
    assert (
        utc.build_strategy().target_weights(synthetic_context(bars=corrupted), seed=20260801) == {}
    )


def test_membership_input_order_and_context_immutability() -> None:
    context = synthetic_context()
    baseline = _reference_weights()
    extra_bars = dict(context.bars)
    extra_bars["ZZZUSDT"] = _bar_frame("ZZZUSDT", 99)
    extra_funding = pd.concat([context.funding, synthetic_funding(("ZZZUSDT",))], ignore_index=True)
    result = utc.build_strategy().target_weights(
        synthetic_context(bars=extra_bars, funding=extra_funding), seed=20260801
    )
    assert result == baseline
    assert "ZZZUSDT" not in result

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
    assert utc.build_strategy().target_weights(reordered, seed=20260801) == baseline
    before_bars = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    before_funding = context.funding.copy(deep=True)
    assert utc.build_strategy().target_weights(context, seed=20260801) == baseline
    for symbol in context.eligible_symbols:
        pd.testing.assert_frame_equal(context.bars[symbol], before_bars[symbol])
    pd.testing.assert_frame_equal(context.funding, before_funding)


def test_two_sleeves_gross_net_cap_and_capacity_cash() -> None:
    weights = _reference_weights()
    positives = [weight for weight in weights.values() if weight > 0]
    negatives = [weight for weight in weights.values() if weight < 0]
    assert len(positives) == len(negatives) == 8
    assert math.fsum(positives) == pytest.approx(0.30, abs=1e-12)
    assert math.fsum(-weight for weight in negatives) == pytest.approx(0.30, abs=1e-12)
    assert math.fsum(abs(weight) for weight in weights.values()) == pytest.approx(0.60, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert max(abs(weight) for weight in weights.values()) <= 0.04
    six = utc._equal_allocation(tuple("ABCDEF"))
    assert six is not None
    assert set(six.values()) == {0.04}
    assert math.fsum(six.values()) == pytest.approx(0.24, abs=1e-12)


def test_clock_minimum_universe_and_seed_contract() -> None:
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(symbols=synthetic_symbols(29)), seed=20260801
        )
        == {}
    )
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1)),
            seed=20260801,
        )
        == {}
    )
    assert (
        utc.build_strategy().target_weights(
            synthetic_context(decision_time=DECISION_TIME + INTERVAL), seed=20260801
        )
        is None
    )
    with pytest.raises(ValueError, match="canonical runtime seed"):
        utc.build_strategy().target_weights(synthetic_context(), seed=2026080104)


def test_frozen_reference_config_and_no_control_policy() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["candidate_id"] == "team-04-utc-reference-001"
    assert frozen["family_id"] == "team-04-uncrowded-trend-carry-v1"
    assert frozen["canonical_runtime_seed"] == 20260801
    assert frozen["parameters"] == {
        "fast_skip_days": 1,
        "fast_trend_days": 14,
        "fast_weight": 0.3,
        "funding_lookback_days": 7,
        "funding_weight": 0.2,
        "gross_target": 0.6,
        "maximum_absolute_funding_rate": 0.05,
        "maximum_funding_staleness_hours": 16,
        "minimum_cross_section": 24,
        "minimum_funding_events": 7,
        "minimum_names_per_sleeve": 6,
        "minimum_prefilter_cross_section": 30,
        "rebalance_bars": 9,
        "selected_fraction_per_side": "1/4",
        "side_budget": 0.3,
        "slow_skip_days": 2,
        "slow_trend_days": 42,
        "slow_weight": 0.5,
        "symbol_cap": 0.04,
        "volatility_keep_fraction": "4/5",
        "volatility_lookback_days": 30,
    }
    policy_raw = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(policy_raw)
    assert policy.policy_id == frozen["risk_policy_id"] == "team-04-utc-reference-no-control"
    assert not policy.enabled
    assert not policy.same_boundary_reentry
