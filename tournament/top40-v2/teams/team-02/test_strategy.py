"""Synthetic, market-data-free tests for team-02 DAA reference candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext
from crypto_trade.tournament.risk_policy import risk_policy_from_dict

DECISION_TIME = pd.Timestamp("2023-01-05T00:00:00Z")
CUTOFF = DECISION_TIME - pd.Timedelta(hours=8)
INTERVAL = pd.Timedelta(hours=8)
TEAM_DIR = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_team02_daa_strategy", TEAM_DIR / "strategy.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load team-02 DAA strategy")
daa = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = daa
_SPEC.loader.exec_module(daa)


def synthetic_symbols(count: int = 28) -> tuple[str, ...]:
    return tuple(f"S{index:02d}USDT" for index in range(count))


def _bar_frame(
    symbol: str,
    symbol_index: int,
    symbol_count: int,
    *,
    include_execution_open: bool = False,
) -> pd.DataFrame:
    first_open = CUTOFF - 37 * INTERVAL
    last_open = DECISION_TIME if include_execution_open else CUTOFF
    bars = int((last_open - first_open) / INTERVAL) + 1
    midpoint = (symbol_count - 1) / 2.0
    scale = max(1.0, midpoint)
    previous_close = 80.0 + 1.75 * symbol_index
    rows: list[dict[str, object]] = []
    for step in range(bars):
        open_time = first_open + step * INTERVAL
        open_price = previous_close
        directional = ((symbol_index - midpoint) / scale) * 0.00125
        cyclic = 0.0014 * math.sin(step * 0.43 + symbol_index * 0.29)
        close = open_price * math.exp(directional + cyclic)
        spread = 0.004 + 0.0002 * (symbol_index % 4)
        high = max(open_price, close) * (1.0 + spread)
        low = min(open_price, close) * (1.0 - spread)
        quote_volume = 1_000_000.0 + 10_000.0 * symbol_index + 250.0 * step
        taker_share = 0.5 + 0.24 * math.sin(step * 0.31 + symbol_index * 0.37)
        rows.append(
            {
                "symbol": symbol,
                "open_time": open_time,
                "close_time": open_time + INTERVAL,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "quote_volume": quote_volume,
                "taker_buy_quote_volume": quote_volume * taker_share,
            }
        )
        previous_close = close
    return pd.DataFrame(rows)


def synthetic_bar_map(
    symbols: tuple[str, ...] | None = None, *, include_execution_open: bool = False
) -> dict[str, pd.DataFrame]:
    eligible = symbols or synthetic_symbols()
    return {
        symbol: _bar_frame(
            symbol,
            index,
            len(eligible),
            include_execution_open=include_execution_open,
        )
        for index, symbol in enumerate(eligible)
    }


def empty_funding() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "funding_time": pd.Series([], dtype="datetime64[ns, UTC]"),
            "symbol": pd.Series([], dtype="object"),
            "funding_rate": pd.Series([], dtype="float64"),
            "mark_price": pd.Series([], dtype="float64"),
        }
    )


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
        funding=empty_funding() if funding is None else funding,
        auxiliary={},
        eligible_symbols=eligible,
    )


def synthetic_worker_inputs() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, list[pd.Timestamp]
]:
    symbols = synthetic_symbols()
    bars = pd.concat(
        synthetic_bar_map(symbols, include_execution_open=True).values(), ignore_index=True
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [DECISION_TIME - pd.Timedelta(days=3)] * len(symbols),
            "symbol": symbols,
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [10_000_000.0 - index for index in range(len(symbols))],
        }
    )
    return bars, empty_funding(), membership, [DECISION_TIME]


def _reference_weights() -> dict[str, float]:
    result = daa.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def _target_bytes(weights: dict[str, float]) -> bytes:
    return json.dumps(weights, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()


def test_exact_path_efficiency_formula() -> None:
    closes = [100.0, 110.0, 99.0, 118.8]
    returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
    expected = math.fsum(returns) / (math.fsum(abs(value) for value in returns) + 1e-12)
    assert daa._path_efficiency(closes) == expected
    assert 0.0 < daa._path_efficiency([100.0, 110.0, 121.0]) < 1.0
    assert -1.0 < daa._path_efficiency([121.0, 110.0, 100.0]) < 0.0
    assert daa._path_efficiency([100.0]) is None
    assert daa._path_efficiency([100.0, 0.0]) is None


def test_exact_flow_closing_location_gap_and_smoothing() -> None:
    gap = daa._absorption_gap(
        open_price=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        quote_volume=100.0,
        taker_buy_quote_volume=25.0,
    )
    assert gap == 0.5
    gaps = [-0.25, 0.25, 0.75]
    raw = [0.5, math.sqrt(0.5), 1.0]
    expected = math.fsum(
        (weight / math.fsum(raw)) * value for weight, value in zip(raw, gaps, strict=True)
    )
    assert daa._smooth_absorption(gaps) == expected


@pytest.mark.parametrize(
    "change",
    [
        {"high": 100.0, "low": 100.0},
        {"open_price": 111.0},
        {"close": 89.0},
        {"quote_volume": 0.0},
        {"taker_buy_quote_volume": -1.0},
        {"taker_buy_quote_volume": 101.0},
        {"high": float("nan")},
    ],
)
def test_ohlc_and_taker_flow_validation(change: dict[str, float]) -> None:
    fields = {
        "open_price": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "quote_volume": 100.0,
        "taker_buy_quote_volume": 25.0,
    }
    fields.update(change)
    assert daa._absorption_gap(**fields) is None


def test_average_rank_ties_and_ascii_membership_ties() -> None:
    ranks = daa._average_ranks({"A": 1.0, "B": 1.0, "C": 3.0, "D": 5.0})
    assert ranks is not None
    expected_tie_rank = 2.0 * (1.5 - 1.0) / 3.0 - 1.0
    assert ranks["A"] == ranks["B"] == expected_tie_rank
    scores = {symbol: 0.0 for symbol in synthetic_symbols(24)}
    sleeves = daa._select_sleeves(scores)
    assert sleeves is not None
    longs, shorts = sleeves
    assert shorts == synthetic_symbols(24)[:6]
    assert longs == synthetic_symbols(24)[-6:]
    assert set(longs).isdisjoint(shorts)


def test_equal_allocation_capacity_and_reconciliation() -> None:
    six = daa._equal_side_allocation(tuple("ABCDEF"))
    assert six is not None
    assert set(six.values()) == {0.06}
    assert math.fsum(six.values()) == pytest.approx(0.36, abs=1e-12)
    seven = daa._equal_side_allocation(tuple("ABCDEFG"))
    assert seven is not None
    assert math.fsum(seven.values()) == pytest.approx(0.40, abs=1e-12)
    assert max(seven.values()) <= 0.06
    assert len(set(seven.values())) <= 2


def test_future_append_corruption_and_truncation_invariance() -> None:
    base = synthetic_context()
    baseline = daa.build_strategy().target_weights(base, seed=20260801)
    assert baseline
    extended = synthetic_bar_map(include_execution_open=True)
    appended = daa.build_strategy().target_weights(synthetic_context(bars=extended), seed=20260801)
    assert appended == baseline

    corrupted = {symbol: frame.copy(deep=True) for symbol, frame in extended.items()}
    for index, symbol in enumerate(base.eligible_symbols):
        future = corrupted[symbol]["close_time"] > CUTOFF
        corrupted[symbol].loc[future, "open"] = 1e100 + index
        corrupted[symbol].loc[future, "high"] = 1e200
        corrupted[symbol].loc[future, "low"] = 1.0
        corrupted[symbol].loc[future, "close"] = 1e100 - index
        corrupted[symbol].loc[future, "quote_volume"] = 1e200
        corrupted[symbol].loc[future, "taker_buy_quote_volume"] = 1e200
    corrupted_result = daa.build_strategy().target_weights(
        synthetic_context(bars=corrupted), seed=20260801
    )
    assert corrupted_result == baseline

    truncated = {
        symbol: frame.loc[frame["close_time"] <= CUTOFF].copy()
        for symbol, frame in extended.items()
    }
    truncated_result = daa.build_strategy().target_weights(
        synthetic_context(bars=truncated), seed=20260801
    )
    assert truncated_result == baseline


def test_extra_lag_anchor_is_exact_and_not_substituted() -> None:
    base = synthetic_context()
    assert daa.build_strategy().target_weights(base, seed=20260801)
    anchor_open = CUTOFF - INTERVAL

    late = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    for symbol in base.eligible_symbols:
        anchor = late[symbol]["open_time"] == anchor_open
        assert int(anchor.sum()) == 1
        late[symbol].loc[anchor, "close_time"] = CUTOFF + pd.Timedelta(microseconds=1)
    assert daa.build_strategy().target_weights(synthetic_context(bars=late), seed=20260801) == {}

    non_grid = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    for symbol in base.eligible_symbols:
        anchor = non_grid[symbol]["open_time"] == anchor_open
        non_grid[symbol].loc[anchor, "open_time"] = anchor_open + pd.Timedelta(hours=1)
    assert (
        daa.build_strategy().target_weights(synthetic_context(bars=non_grid), seed=20260801) == {}
    )


def _corrupt_latest_five(
    bars: Mapping[str, pd.DataFrame], column: str, value: float
) -> dict[str, pd.DataFrame]:
    copied = {symbol: frame.copy(deep=True) for symbol, frame in bars.items()}
    anchor_open = CUTOFF - INTERVAL
    for symbol in tuple(copied)[:5]:
        anchor = copied[symbol]["open_time"] == anchor_open
        copied[symbol].loc[anchor, column] = value
    return copied


def test_invalid_ohlc_flow_history_and_duplicates_fail_closed() -> None:
    base = synthetic_context()
    assert daa.build_strategy().target_weights(base, seed=20260801)
    invalid_range = _corrupt_latest_five(base.bars, "low", 1e9)
    assert (
        daa.build_strategy().target_weights(synthetic_context(bars=invalid_range), seed=20260801)
        == {}
    )
    invalid_flow = _corrupt_latest_five(base.bars, "quote_volume", 0.0)
    assert (
        daa.build_strategy().target_weights(synthetic_context(bars=invalid_flow), seed=20260801)
        == {}
    )
    invalid_close = _corrupt_latest_five(base.bars, "close", float("nan"))
    assert (
        daa.build_strategy().target_weights(synthetic_context(bars=invalid_close), seed=20260801)
        == {}
    )

    duplicated = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    anchor_open = CUTOFF - INTERVAL
    for symbol in tuple(duplicated)[:5]:
        anchor = duplicated[symbol].loc[duplicated[symbol]["open_time"] == anchor_open]
        duplicated[symbol] = pd.concat([duplicated[symbol], anchor], ignore_index=True)
    assert (
        daa.build_strategy().target_weights(synthetic_context(bars=duplicated), seed=20260801) == {}
    )


def test_membership_funding_independence_and_input_order_determinism() -> None:
    base = synthetic_context()
    first = daa.build_strategy().target_weights(base, seed=20260801)
    assert first
    extra = dict(base.bars)
    extra["ZZZUSDT"] = _bar_frame("ZZZUSDT", 999, len(base.eligible_symbols))
    arbitrary_funding = pd.DataFrame({"not_a_strategy_input": [float("nan")]})
    membership_result = daa.build_strategy().target_weights(
        synthetic_context(bars=extra, funding=arbitrary_funding), seed=20260801
    )
    assert membership_result == first
    assert set(membership_result).issubset(base.eligible_symbols)

    reordered = DecisionContext(
        decision_time=base.decision_time,
        bars={
            symbol: base.bars[symbol].iloc[::-1].reset_index(drop=True)
            for symbol in reversed(base.eligible_symbols)
        },
        funding=arbitrary_funding,
        auxiliary={},
        eligible_symbols=tuple(reversed(base.eligible_symbols)),
    )
    second = daa.build_strategy().target_weights(reordered, seed=20260801)
    third = daa.build_strategy().target_weights(base, seed=20260801)
    assert first == second == third
    assert _target_bytes(first) == _target_bytes(second)


def test_reference_two_sleeves_gross_net_and_cap() -> None:
    weights = _reference_weights()
    positives = [value for value in weights.values() if value > 0.0]
    negatives = [value for value in weights.values() if value < 0.0]
    assert len(positives) == len(negatives) == 7
    assert all(math.isfinite(value) for value in weights.values())
    assert max(abs(value) for value in weights.values()) <= 0.06
    assert math.fsum(positives) == pytest.approx(0.40, abs=1e-12)
    assert math.fsum(-value for value in negatives) == pytest.approx(0.40, abs=1e-12)
    assert math.fsum(abs(value) for value in weights.values()) == pytest.approx(0.80, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)

    minimum = daa.build_strategy().target_weights(
        synthetic_context(symbols=synthetic_symbols(24)), seed=20260801
    )
    assert minimum
    assert len(minimum) == 12
    assert set(abs(value) for value in minimum.values()) == {0.06}
    assert math.fsum(abs(value) for value in minimum.values()) == pytest.approx(0.72, abs=1e-12)


def test_clock_minimum_cross_section_and_seed_contract() -> None:
    too_small = synthetic_context(symbols=synthetic_symbols(23))
    assert daa.build_strategy().target_weights(too_small, seed=20260801) == {}
    off_grid = synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    assert daa.build_strategy().target_weights(off_grid, seed=20260801) == {}
    non_rebalance = synthetic_context(decision_time=DECISION_TIME + INTERVAL)
    assert daa.build_strategy().target_weights(non_rebalance, seed=20260801) is None
    with pytest.raises(ValueError, match="canonical runtime seed"):
        daa.build_strategy().target_weights(synthetic_context(), seed=2026080102)
    with pytest.raises(ValueError, match="canonical runtime seed"):
        daa.build_strategy().target_weights(synthetic_context(), seed=1)


def test_context_is_read_only() -> None:
    context = synthetic_context()
    before = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    assert daa.build_strategy().target_weights(context, seed=20260801)
    for symbol in context.eligible_symbols:
        pd.testing.assert_frame_equal(context.bars[symbol], before[symbol])


def test_frozen_reference_config_and_no_control_policy_validate() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["candidate_id"] == "team-02-daa-reference-001"
    assert frozen["family_id"] == "team-02-directional-auction-absorption-v1"
    assert frozen["canonical_runtime_seed"] == 20260801
    assert frozen["parameters"] == {
        "absorption_half_life_bars": 2.0,
        "absorption_weight": 0.4,
        "absorption_window_bars": 3,
        "feature_lag_bars": 1,
        "gross_target": 0.8,
        "minimum_cross_section": 24,
        "minimum_names_per_sleeve": 6,
        "rebalance_bars": 3,
        "selected_fraction_per_side": "1/4",
        "side_budget": 0.4,
        "symbol_cap": 0.06,
        "trend_efficiency_days": 12,
        "trend_weight": 0.6,
    }
    assert frozen["mechanism_guardrail"]["trend_component_enabled"]
    assert frozen["mechanism_guardrail"]["absorption_component_enabled"]
    assert frozen["information_contract"]["funding_used"] is False
    raw_policy = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(raw_policy)
    assert policy.policy_id == "team-02-daa-reference-no-control"
    assert policy.policy_id == frozen["risk_policy_id"]
    assert not policy.enabled
    assert not policy.same_boundary_reentry


def synthetic_evidence() -> dict[str, object]:
    weights = _reference_weights()
    payload = _target_bytes(weights)
    source = (TEAM_DIR / "strategy.py").read_bytes()
    return {
        "candidate_id": "team-02-daa-reference-001",
        "gross": math.fsum(abs(value) for value in weights.values()),
        "long_count": sum(value > 0.0 for value in weights.values()),
        "net": math.fsum(weights.values()),
        "short_count": sum(value < 0.0 for value in weights.values()),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "target_sha256": hashlib.sha256(payload).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_evidence(), allow_nan=False, sort_keys=True))
