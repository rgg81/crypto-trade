"""Synthetic tests for team-02 diagnostic C3RP-no-direction-tilt-002."""

from __future__ import annotations

import hashlib
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
TEAM_DIR = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_team02_c3rp_strategy", TEAM_DIR / "strategy.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load team-02 strategy")
c3rp = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = c3rp
_SPEC.loader.exec_module(c3rp)


def _symbols(count: int = 20) -> tuple[str, ...]:
    return tuple(f"S{index:02d}USDT" for index in range(count))


def _bars_for_symbol(symbol: str, symbol_index: int, count: int) -> pd.DataFrame:
    first_open = CUTOFF - 61 * pd.Timedelta(hours=8)
    price = 80.0 + 2.0 * symbol_index
    rows: list[dict[str, object]] = []
    for step in range(61):
        open_time = first_open + step * pd.Timedelta(hours=8)
        if step:
            market = 0.00045 + 0.0018 * math.sin(step * 0.37) + 0.0007 * math.cos(step * 0.11)
            idiosyncratic = (symbol_index - (count - 1) / 2.0) * 0.000025 + 0.0011 * math.sin(
                step * (0.13 + 0.003 * symbol_index) + 0.41 * symbol_index
            )
            log_return = market * (0.84 + 0.025 * (symbol_index % 5)) + idiosyncratic
            price *= math.exp(log_return)
        rows.append(
            {
                "symbol": symbol,
                "open_time": open_time,
                "close_time": open_time + pd.Timedelta(hours=8),
                "close": price,
            }
        )
    return pd.DataFrame(rows)


def _funding(symbols: tuple[str, ...]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    midpoint = (len(symbols) - 1) / 2.0
    for index, symbol in enumerate(symbols):
        rate = (index - midpoint) * 0.000012
        for days in (6, 3, 1):
            rows.append(
                {
                    "symbol": symbol,
                    "funding_time": CUTOFF - pd.Timedelta(days=days),
                    "funding_rate": rate,
                    "mark_price": 100.0 + index,
                }
            )
    return pd.DataFrame(rows)


def _context(
    *,
    symbols: tuple[str, ...] | None = None,
    decision_time: pd.Timestamp = DECISION_TIME,
    bars: dict[str, pd.DataFrame] | None = None,
    funding: pd.DataFrame | None = None,
) -> DecisionContext:
    eligible = symbols or _symbols()
    frames = bars or {
        symbol: _bars_for_symbol(symbol, index, len(eligible))
        for index, symbol in enumerate(eligible)
    }
    return DecisionContext(
        decision_time=decision_time,
        bars=frames,
        funding=_funding(eligible) if funding is None else funding,
        auxiliary={},
        eligible_symbols=eligible,
    )


def _diagnostic_weights() -> dict[str, float]:
    result = c3rp.build_strategy().target_weights(_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def _target_bytes(weights: dict[str, float]) -> bytes:
    return json.dumps(weights, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()


def test_future_append_corruption_and_truncation_invariance() -> None:
    base = _context()
    baseline = c3rp.build_strategy().target_weights(base, seed=20260801)
    assert baseline

    extended_bars = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    for index, symbol in enumerate(base.eligible_symbols):
        previous = float(extended_bars[symbol].iloc[-1]["close"])
        future = pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "open_time": CUTOFF,
                    "close_time": DECISION_TIME,
                    "close": previous * math.exp(0.5 - index * 0.01),
                }
            ]
        )
        extended_bars[symbol] = pd.concat([extended_bars[symbol], future], ignore_index=True)
    future_funding = pd.DataFrame(
        [
            {
                "symbol": base.eligible_symbols[0],
                "funding_time": CUTOFF + pd.Timedelta(hours=4),
                "funding_rate": 9999.0,
                "mark_price": 1e200,
            }
        ]
    )
    extended_funding = pd.concat([base.funding, future_funding], ignore_index=True)
    appended = c3rp.build_strategy().target_weights(
        _context(bars=extended_bars, funding=extended_funding), seed=20260801
    )
    assert appended == baseline

    corrupted = {symbol: frame.copy(deep=True) for symbol, frame in extended_bars.items()}
    for index, symbol in enumerate(base.eligible_symbols):
        future_mask = corrupted[symbol]["close_time"] > CUTOFF
        corrupted[symbol].loc[future_mask, "close"] = 1e250 / (index + 1)
    corrupted_funding = extended_funding.copy(deep=True)
    corrupted_funding.loc[corrupted_funding["funding_time"] > CUTOFF, "funding_rate"] = -1e250
    corrupted_result = c3rp.build_strategy().target_weights(
        _context(bars=corrupted, funding=corrupted_funding), seed=20260801
    )
    assert corrupted_result == baseline

    truncated = {
        symbol: frame.loc[frame["close_time"] <= CUTOFF].copy()
        for symbol, frame in extended_bars.items()
    }
    truncated_funding = extended_funding.loc[extended_funding["funding_time"] <= CUTOFF].copy()
    truncated_result = c3rp.build_strategy().target_weights(
        _context(bars=truncated, funding=truncated_funding), seed=20260801
    )
    assert truncated_result == baseline


def test_extra_lag_boundary_is_strict_and_right_inclusive() -> None:
    baseline_context = _context()
    assert c3rp.build_strategy().target_weights(baseline_context, seed=20260801)
    delayed = {symbol: frame.copy(deep=True) for symbol, frame in baseline_context.bars.items()}
    anchor_open = CUTOFF - pd.Timedelta(hours=8)
    for symbol in baseline_context.eligible_symbols:
        anchor = delayed[symbol]["open_time"] == anchor_open
        assert int(anchor.sum()) == 1
        delayed[symbol].loc[anchor, "close_time"] = CUTOFF + pd.Timedelta(microseconds=1)
    assert c3rp.build_strategy().target_weights(_context(bars=delayed), seed=20260801) == {}


def test_funding_window_availability_and_carry_sign() -> None:
    symbols = ("A", "B", "C", "D", "E", "MISSING")
    rates = {"A": -0.004, "B": -0.002, "C": 0.0, "D": 0.002, "E": 0.004}
    rows: list[dict[str, object]] = []
    left = CUTOFF - pd.Timedelta(days=7)
    for symbol, rate in rates.items():
        rows.extend(
            [
                {
                    "symbol": symbol,
                    "funding_time": left,
                    "funding_rate": -999.0,
                    "mark_price": 1e200,
                },
                {
                    "symbol": symbol,
                    "funding_time": left + pd.Timedelta(nanoseconds=1),
                    "funding_rate": rate,
                    "mark_price": 100.0,
                },
                {
                    "symbol": symbol,
                    "funding_time": CUTOFF,
                    "funding_rate": rate,
                    "mark_price": 101.0,
                },
                {
                    "symbol": symbol,
                    "funding_time": CUTOFF + pd.Timedelta(nanoseconds=1),
                    "funding_rate": 999.0,
                    "mark_price": 1e200,
                },
            ]
        )
    ranks = c3rp._funding_ranks(pd.DataFrame(rows), symbols, CUTOFF)
    assert ranks["A"] > ranks["B"] > ranks["C"] > ranks["D"] > ranks["E"]
    assert ranks["MISSING"] == 0.0

    duplicate = pd.concat(
        [
            pd.DataFrame(rows),
            pd.DataFrame(
                [
                    {
                        "symbol": "A",
                        "funding_time": CUTOFF,
                        "funding_rate": rates["A"],
                        "mark_price": 999.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    duplicate_ranks = c3rp._funding_ranks(duplicate, symbols, CUTOFF)
    assert duplicate_ranks["A"] == 0.0
    assert duplicate_ranks["B"] > duplicate_ranks["C"] > duplicate_ranks["D"] > duplicate_ranks["E"]

    nonfinite = pd.concat(
        [
            pd.DataFrame(rows),
            pd.DataFrame(
                [
                    {
                        "symbol": "A",
                        "funding_time": CUTOFF - pd.Timedelta(hours=4),
                        "funding_rate": float("nan"),
                        "mark_price": 100.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    nonfinite_ranks = c3rp._funding_ranks(nonfinite, symbols, CUTOFF)
    assert nonfinite_ranks["A"] == 0.0
    assert nonfinite_ranks["B"] > nonfinite_ranks["C"] > nonfinite_ranks["D"] > nonfinite_ranks["E"]


def test_point_in_time_membership_excludes_unlisted_inputs() -> None:
    base = _context()
    baseline = c3rp.build_strategy().target_weights(base, seed=20260801)
    assert baseline
    extra_bars = dict(base.bars)
    extra_bars["ZZZUSDT"] = _bars_for_symbol("ZZZUSDT", 999, len(base.eligible_symbols))
    extra_funding = pd.concat([base.funding, _funding(("ZZZUSDT",))], ignore_index=True)
    result = c3rp.build_strategy().target_weights(
        _context(bars=extra_bars, funding=extra_funding), seed=20260801
    )
    assert result == baseline
    assert set(result).issubset(base.eligible_symbols)


def test_variable_state_preserves_predicted_interaction() -> None:
    low = c3rp._state_probability(0.05, 0.05)
    high = c3rp._state_probability(0.80, 0.80)
    assert 0.0 < low < 0.5 < high < 1.0
    low_state_score = c3rp._state_blend(1.0, -1.0, 0.0, low)
    high_state_score = c3rp._state_blend(1.0, -1.0, 0.0, high)
    assert low_state_score < 0.0 < high_state_score
    assert high_state_score > low_state_score


def test_exact_average_ranks_and_ascii_membership_ties() -> None:
    ranks = c3rp._average_ranks({"A": 1.0, "B": 1.0, "C": 3.0, "D": 5.0})
    assert ranks is not None
    assert ranks["A"] == ranks["B"]
    alpha = {symbol: 0.0 for symbol in _symbols(12)}
    sleeves = c3rp._select_sleeves(alpha)
    assert sleeves is not None
    longs, shorts = sleeves
    assert shorts == _symbols(12)[:4]
    assert longs == _symbols(12)[-4:]
    assert set(longs).isdisjoint(shorts)


def test_deterministic_targets_under_input_reordering() -> None:
    base = _context()
    first = c3rp.build_strategy().target_weights(base, seed=20260801)
    reordered_bars = {
        symbol: base.bars[symbol].iloc[::-1].reset_index(drop=True)
        for symbol in reversed(base.eligible_symbols)
    }
    reordered = DecisionContext(
        decision_time=base.decision_time,
        bars=reordered_bars,
        funding=base.funding.iloc[::-1].reset_index(drop=True),
        auxiliary={},
        eligible_symbols=tuple(reversed(base.eligible_symbols)),
    )
    second = c3rp.build_strategy().target_weights(reordered, seed=20260801)
    third = c3rp.build_strategy().target_weights(base, seed=20260801)
    assert first == second == third
    assert _target_bytes(first) == _target_bytes(second)


def test_no_direction_tilt_preserves_two_sleeves_and_exposure_bounds() -> None:
    weights = _diagnostic_weights()
    positives = [weight for weight in weights.values() if weight > 0.0]
    negatives = [weight for weight in weights.values() if weight < 0.0]
    assert len(positives) >= 4
    assert len(negatives) >= 4
    assert all(math.isfinite(weight) for weight in weights.values())
    assert max(abs(weight) for weight in weights.values()) <= 0.095
    gross = math.fsum(abs(weight) for weight in weights.values())
    net = math.fsum(weights.values())
    long_gross = math.fsum(weight for weight in weights.values() if weight > 0.0)
    short_gross = math.fsum(-weight for weight in weights.values() if weight < 0.0)
    assert abs(long_gross - 0.45) <= 1e-12
    assert abs(short_gross - 0.45) <= 1e-12
    assert abs(gross - 0.90) <= 1e-12
    assert abs(net) <= 1e-12


def test_invalid_data_and_clock_actions_are_conservative() -> None:
    too_small = _context(symbols=_symbols(11))
    assert c3rp.build_strategy().target_weights(too_small, seed=20260801) == {}

    base = _context()
    duplicated = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    anchor_open = CUTOFF - pd.Timedelta(hours=8)
    for symbol in base.eligible_symbols:
        anchor = duplicated[symbol].loc[duplicated[symbol]["open_time"] == anchor_open]
        duplicated[symbol] = pd.concat([duplicated[symbol], anchor], ignore_index=True)
    assert c3rp.build_strategy().target_weights(_context(bars=duplicated), seed=20260801) == {}

    off_grid = _context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    assert c3rp.build_strategy().target_weights(off_grid, seed=20260801) == {}
    unscheduled = _context(decision_time=DECISION_TIME + pd.Timedelta(hours=8))
    assert c3rp.build_strategy().target_weights(unscheduled, seed=20260801) is None
    with pytest.raises(ValueError, match="canonical runtime seed"):
        c3rp.build_strategy().target_weights(base, seed=2026080102)
    with pytest.raises(ValueError, match="canonical runtime seed"):
        c3rp.build_strategy().target_weights(base, seed=1)


def test_context_is_read_only_and_missing_funding_is_neutral() -> None:
    base = _context(funding=pd.DataFrame())
    before_bars = {symbol: frame.copy(deep=True) for symbol, frame in base.bars.items()}
    before_funding = base.funding.copy(deep=True)
    result = c3rp.build_strategy().target_weights(base, seed=20260801)
    assert result
    for symbol in base.eligible_symbols:
        pd.testing.assert_frame_equal(base.bars[symbol], before_bars[symbol])
    pd.testing.assert_frame_equal(base.funding, before_funding)


def test_diagnostic_frozen_json_and_no_control_policy_validate() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["canonical_runtime_seed"] == 20260801
    assert frozen["candidate_id"] == "team-02-c3rp-no-direction-tilt-002"
    assert frozen["parameters"]["maximum_side_tilt"] == 0.0
    assert frozen["mechanism_guardrail"] == {
        "automatically_deployable": False,
        "deployable": False,
        "diagnostic_arm": "component-no-direction-tilt",
        "diagnostic_only": True,
        "eligible_for_automatic_champion_selection": False,
        "fixed_state_forbidden": True,
        "persistence_leg_enabled": True,
        "reversal_leg_enabled": True,
        "variable_state_interaction_enabled": True,
    }
    raw_policy = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(raw_policy)
    assert policy.policy_id == frozen["risk_policy_id"]
    assert not policy.enabled
    assert not policy.same_boundary_reentry


def synthetic_evidence() -> dict[str, object]:
    target = _diagnostic_weights()
    target_payload = _target_bytes(target)
    source_bytes = (TEAM_DIR / "strategy.py").read_bytes()
    return {
        "candidate_id": "team-02-c3rp-no-direction-tilt-002",
        "gross": math.fsum(abs(weight) for weight in target.values()),
        "long_count": sum(weight > 0.0 for weight in target.values()),
        "net": math.fsum(target.values()),
        "short_count": sum(weight < 0.0 for weight in target.values()),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "target_sha256": hashlib.sha256(target_payload).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_evidence(), allow_nan=False, sort_keys=True))
