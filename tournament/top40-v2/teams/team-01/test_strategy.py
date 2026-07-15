"""Synthetic, evaluator-free tests for the team-01 strategy contract."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext

_TEAM_DIR = Path(__file__).resolve().parent
_DECISION_TIME = pd.Timestamp(year=2023, month=6, day=30, tz="UTC")
_RUNTIME_SEED = 20260801
_BASELINE_FROZEN_PARAMETERS = {
    "beta_clip": [-1.0, 3.0],
    "beta_lookback_days": 30,
    "btc_symbol": "BTCUSDT",
    "btc_variance_floor": 1e-12,
    "direction_lookback_days": 60,
    "direction_return_scale": 0.2,
    "direction_tilt_delta": 0.075,
    "funding_lookback_days": 7,
    "funding_penalty": 0.35,
    "minimum_funding_events": 14,
    "minimum_names_per_side": 6,
    "minimum_paired_returns": 72,
    "minimum_valid_symbols": 24,
    "path_efficiency_exponent": 0.5,
    "per_symbol_target_cap": 0.09,
    "rank_tail_fraction": 0.25,
    "residual_denominator_floor": 1e-8,
    "residual_lookback_days": 21,
    "skip_days": 3,
    "total_gross": 0.8,
}


def _load_strategy_module():
    module_name = "_top40_v2_team01_strategy_test"
    module = sys.modules.get(module_name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(module_name, _TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy_module()


def _bar_frame(symbol: str, open_times: pd.DatetimeIndex, log_returns: np.ndarray) -> pd.DataFrame:
    assert len(log_returns) == len(open_times) - 1
    initial = math.log(100.0 + len(symbol))
    log_prices = initial + np.concatenate(([0.0], np.cumsum(log_returns)))
    closes = np.exp(log_prices)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "symbol": symbol,
            "open": closes * 0.999,
            "close": closes,
            "quote_volume": np.full(len(open_times), 10_000_000.0),
        }
    )


def _synthetic_context(*, asset_count: int = 28) -> DecisionContext:
    periods = 240
    open_times = pd.date_range(
        end=_DECISION_TIME - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
    )
    step = np.arange(periods - 1, dtype=float)
    btc_returns = (
        0.00045
        + 0.0028 * np.sin(0.29 * step)
        + 0.0011 * np.cos(0.13 * step)
    )
    bars: dict[str, pd.DataFrame] = {
        "BTCUSDT": _bar_frame("BTCUSDT", open_times, btc_returns)
    }

    symbols = [f"A{index:02d}USDT" for index in range(asset_count)]
    center = (asset_count - 1) / 2.0
    for index, symbol in enumerate(symbols):
        rank = index - center
        beta = 0.55 + 0.02 * index
        residual = (
            rank * 0.000075
            + 0.00024 * np.sin(0.37 * step + 0.41 * index)
            + 0.00009 * np.cos(0.19 * step + 0.17 * index)
        )
        bars[symbol] = _bar_frame(symbol, open_times, beta * btc_returns + residual)

    funding_times = pd.date_range(
        start=_DECISION_TIME - pd.Timedelta(days=7),
        periods=21,
        freq="8h",
    )
    funding_rows: list[dict[str, object]] = []
    for index, symbol in enumerate(symbols):
        rate = ((index % 5) - 2) * 2.0e-7
        for funding_time in funding_times:
            funding_rows.append(
                {
                    "settlement_time": funding_time,
                    "funding_time": funding_time,
                    "symbol": symbol,
                    "funding_rate": rate,
                    "mark_price": 100.0,
                }
            )
    funding = pd.DataFrame(funding_rows).sort_values(
        ["settlement_time", "funding_time", "symbol"]
    )
    # Deliberately reverse the asset order: target selection must not depend on membership order.
    eligible = ("BTCUSDT", *reversed(symbols))
    return DecisionContext(
        decision_time=_DECISION_TIME,
        bars=bars,
        funding=funding,
        auxiliary={},
        eligible_symbols=eligible,
    )


def _targets(context: DecisionContext) -> dict[str, float]:
    result = strategy_module.build_strategy().target_weights(context, seed=_RUNTIME_SEED)
    assert isinstance(result, dict)
    return result


def _target_hash(targets: dict[str, float]) -> str:
    encoded = json.dumps(
        targets,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _official_worker_targets(context: DecisionContext) -> dict[str, float]:
    root = _TEAM_DIR.parents[3]
    entrypoint = _TEAM_DIR / "strategy.py"
    source_fingerprint, _ = runner_v2.source_bundle_fingerprint(
        root,
        "team-01",
        entrypoint.relative_to(root),
    )

    bar_frames: list[pd.DataFrame] = []
    for frame in context.bars.values():
        future_open = frame.iloc[[-1]].copy(deep=True)
        future_open.loc[:, "open_time"] = context.decision_time
        bar_frames.append(pd.concat([frame, future_open], ignore_index=True))
    bars = pd.concat(bar_frames, ignore_index=True)
    membership = pd.DataFrame(
        [
            {
                "reconstitution_time": context.decision_time - pd.Timedelta(days=4),
                "symbol": symbol,
                "liquidity_rank": rank,
                "trailing_quote_volume": 10_000_000.0 - rank,
            }
            for rank, symbol in enumerate(context.eligible_symbols, start=1)
        ]
    )
    target_frame = runner_v2._generate_targets_in_worker(
        root,
        "team-01",
        entrypoint,
        bars,
        context.funding,
        membership,
        [context.decision_time],
        seed=_RUNTIME_SEED,
        interval_hours=8,
        expected_source_bundle_sha256=source_fingerprint,
    )
    row = target_frame.loc[context.decision_time]
    assert bool(row[REBALANCE_INSTRUCTION_COLUMN])
    return {
        str(symbol): float(weight)
        for symbol, weight in row.items()
        if symbol != REBALANCE_INSTRUCTION_COLUMN and float(weight) != 0.0
    }


def test_candidate_factory_is_fresh_deterministic_and_bounded() -> None:
    first_strategy = strategy_module.build_strategy()
    second_strategy = strategy_module.build_strategy()
    assert first_strategy is not second_strategy
    assert first_strategy._parameters == strategy_module.REFERENCE_PARAMETERS

    context = _synthetic_context()
    first = first_strategy.target_weights(context, seed=_RUNTIME_SEED)
    second = second_strategy.target_weights(context, seed=_RUNTIME_SEED)
    assert first == second
    assert isinstance(first, dict) and first
    assert set(first).issubset(set(context.eligible_symbols))
    assert "BTCUSDT" not in first
    assert any(weight > 0.0 for weight in first.values())
    assert any(weight < 0.0 for weight in first.values())
    assert all(math.isfinite(weight) for weight in first.values())
    assert sum(abs(weight) for weight in first.values()) == pytest.approx(0.80, abs=1e-10)
    assert abs(sum(first.values())) <= 0.15 + 1e-10
    assert max(abs(weight) for weight in first.values()) <= 0.09 + 1e-12


def test_daily_clock_returns_hold_between_rebalances_and_rejects_wrong_seed() -> None:
    context = _synthetic_context()
    hold_context = DecisionContext(
        decision_time=context.decision_time + pd.Timedelta(hours=8),
        bars=context.bars,
        funding=context.funding,
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    assert strategy_module.build_strategy().target_weights(
        hold_context, seed=_RUNTIME_SEED
    ) is None
    with pytest.raises(ValueError, match="canonical runtime seed"):
        strategy_module.build_strategy().target_weights(context, seed=2026080101)


def test_future_append_corruption_and_unexposed_open_are_invariant() -> None:
    context = _synthetic_context()
    baseline = _targets(context)
    mutated_bars = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    for symbol, frame in mutated_bars.items():
        frame.loc[:, "open"] = np.inf
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = _DECISION_TIME
        future.loc[:, "open"] = -np.inf
        future.loc[:, "close"] = np.nan
        mutated_bars[symbol] = pd.concat([frame, future], ignore_index=True)
    mutated_bars["FUTUREUSDT"] = pd.DataFrame(
        {
            "open_time": [_DECISION_TIME],
            "symbol": ["FUTUREUSDT"],
            "open": [-1.0],
            "close": [np.nan],
            "quote_volume": [np.inf],
        }
    )
    future_funding = pd.DataFrame(
        [
            {
                "settlement_time": _DECISION_TIME,
                "funding_time": _DECISION_TIME,
                "symbol": "A00USDT",
                "funding_rate": np.inf,
                "mark_price": np.nan,
            },
            {
                "settlement_time": _DECISION_TIME + pd.Timedelta(hours=8),
                "funding_time": _DECISION_TIME + pd.Timedelta(hours=8),
                "symbol": "FUTUREUSDT",
                "funding_rate": -np.inf,
                "mark_price": np.nan,
            },
        ]
    )
    mutated_context = DecisionContext(
        decision_time=context.decision_time,
        bars=mutated_bars,
        funding=pd.concat([context.funding, future_funding], ignore_index=True),
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    assert _targets(mutated_context) == baseline


def test_point_in_time_membership_removal_never_leaks_removed_symbol() -> None:
    context = _synthetic_context()
    baseline = _targets(context)
    removed = next(iter(baseline))
    remaining = tuple(symbol for symbol in context.eligible_symbols if symbol != removed)
    changed = DecisionContext(
        decision_time=context.decision_time,
        bars=context.bars,
        funding=context.funding,
        auxiliary={},
        eligible_symbols=remaining,
    )
    changed_targets = _targets(changed)
    assert removed not in changed_targets
    assert _targets(context) == baseline


def test_positive_funding_lowers_score_and_negative_funding_raises_it() -> None:
    scores = strategy_module._combine_scores(
        [1.0, 1.0, 1.0],
        [-2.0, 0.0, 2.0],
        penalty=0.35,
    )
    assert scores is not None
    assert scores[0] > scores[1] > scores[2]


def test_equal_scores_use_ascending_symbol_tie_break() -> None:
    selected = strategy_module._select_signed_tails(
        [
            ("B", -2.0, 0.1),
            ("A", -2.0, 0.1),
            ("D", -1.0, 0.1),
            ("C", -0.5, 0.1),
            ("F", 0.5, 0.1),
            ("E", 1.0, 0.1),
            ("H", 2.0, 0.1),
            ("G", 2.0, 0.1),
        ],
        tail_fraction=0.25,
        minimum_names_per_side=2,
    )
    assert selected is not None
    short_tail, long_tail = selected
    assert [symbol for symbol, _, _ in short_tail] == ["A", "B"]
    assert [symbol for symbol, _, _ in long_tail] == ["G", "H"]


def test_gamma_one_applies_the_exact_registered_path_efficiency_exponent() -> None:
    context = _synthetic_context()
    symbol = "A14USDT"
    btc_history = strategy_module._closed_history(
        context.bars["BTCUSDT"], context.decision_time
    )
    symbol_history = strategy_module._closed_history(
        context.bars[symbol], context.decision_time
    )
    assert btc_history is not None and symbol_history is not None
    _, btc_returns = btc_history
    _, symbol_returns = symbol_history
    funding = strategy_module._funding_pressures(
        context.funding,
        eligible=context.eligible_symbols,
        decision_time=context.decision_time,
        lookback_days=7,
        minimum_events=14,
    )
    assert funding is not None and symbol in funding

    gamma_one = strategy_module.build_strategy()
    baseline_parameters = dataclasses.replace(
        strategy_module.REFERENCE_PARAMETERS,
        path_efficiency_exponent=0.5,
    )
    gamma_half = strategy_module.ResidualDriftFundingStrategy(baseline_parameters)
    signal_one = gamma_one._symbol_signal(
        symbol,
        symbol_returns=symbol_returns,
        btc_returns=btc_returns,
        funding_pressure=funding[symbol],
        decision_time=context.decision_time,
    )
    signal_half = gamma_half._symbol_signal(
        symbol,
        symbol_returns=symbol_returns,
        btc_returns=btc_returns,
        funding_pressure=funding[symbol],
        decision_time=context.decision_time,
    )
    assert signal_one is not None and signal_half is not None

    parameters = strategy_module.REFERENCE_PARAMETERS
    beta_times = pd.date_range(
        end=context.decision_time,
        periods=3 * parameters.beta_lookback_days,
        freq="8h",
    )
    y_beta = symbol_returns.reindex(beta_times).to_numpy(dtype=float)
    x_beta = btc_returns.reindex(beta_times).to_numpy(dtype=float)
    paired = np.isfinite(y_beta) & np.isfinite(x_beta)
    centered_x = x_beta[paired] - float(np.mean(x_beta[paired]))
    centered_y = y_beta[paired] - float(np.mean(y_beta[paired]))
    beta = float(np.mean(centered_x * centered_y) / np.mean(centered_x * centered_x))
    beta = float(np.clip(beta, -1.0, 3.0))
    drift_times = pd.date_range(
        end=context.decision_time - pd.Timedelta(days=3),
        periods=63,
        freq="8h",
    )
    residuals = (
        symbol_returns.reindex(drift_times).to_numpy(dtype=float)
        - beta * btc_returns.reindex(drift_times).to_numpy(dtype=float)
    )
    residual_sum = float(np.sum(residuals))
    residual_volatility = float(np.std(residuals, ddof=1))
    trend = residual_sum / max(residual_volatility * math.sqrt(63.0), 1e-8)
    efficiency = abs(residual_sum) / max(float(np.sum(np.abs(residuals))), 1e-8)
    assert 0.0 < efficiency < 1.0
    assert signal_one.drift == pytest.approx(trend * efficiency, rel=1e-13, abs=1e-13)
    assert signal_half.drift == pytest.approx(
        trend * math.sqrt(efficiency), rel=1e-13, abs=1e-13
    )
    assert abs(signal_one.drift) < abs(signal_half.drift)


@pytest.mark.parametrize("defect", ["duplicate", "nonfinite_close", "nonfinite_funding"])
def test_invalid_past_data_with_inadequate_remaining_coverage_requests_flat(defect: str) -> None:
    context = _synthetic_context(asset_count=24)
    bars = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    funding = context.funding.copy(deep=True)
    symbol = "A00USDT"
    if defect == "duplicate":
        bars[symbol] = pd.concat([bars[symbol], bars[symbol].iloc[[-1]]], ignore_index=True)
    elif defect == "nonfinite_close":
        bars[symbol].loc[bars[symbol].index[-2], "close"] = np.inf
    else:
        row = funding.index[funding["symbol"].eq(symbol)][-1]
        funding.loc[row, "funding_rate"] = np.nan
    defective = DecisionContext(
        decision_time=context.decision_time,
        bars=bars,
        funding=funding,
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    assert _targets(defective) == {}


def test_inadequate_coverage_missing_btc_and_one_sided_infeasibility_are_flat() -> None:
    sparse = _synthetic_context(asset_count=23)
    assert _targets(sparse) == {}

    complete = _synthetic_context()
    no_btc = DecisionContext(
        decision_time=complete.decision_time,
        bars=complete.bars,
        funding=complete.funding,
        auxiliary={},
        eligible_symbols=tuple(
            symbol for symbol in complete.eligible_symbols if symbol != "BTCUSDT"
        ),
    )
    assert _targets(no_btc) == {}

    identical_bars = copy.deepcopy(complete.bars)
    template = identical_bars["A00USDT"].copy(deep=True)
    for symbol in complete.eligible_symbols:
        if symbol != "BTCUSDT":
            cloned = template.copy(deep=True)
            cloned.loc[:, "symbol"] = symbol
            identical_bars[symbol] = cloned
    one_sided = DecisionContext(
        decision_time=complete.decision_time,
        bars=identical_bars,
        funding=complete.funding,
        auxiliary={},
        eligible_symbols=complete.eligible_symbols,
    )
    assert _targets(one_sided) == {}


def test_canonical_target_hash_is_clean_process_stable() -> None:
    first = _target_hash(_targets(_synthetic_context()))
    second = _target_hash(_targets(_synthetic_context()))
    assert first == second
    assert first == "7a08069e083289a37204b6be93f2916b2219c35272c1ba4e0a2617137a3c2f03"


def test_official_namespaced_worker_matches_direct_synthetic_targets_twice() -> None:
    context = _synthetic_context()
    direct = _targets(context)
    first_worker = _official_worker_targets(context)
    second_worker = _official_worker_targets(context)
    assert first_worker == direct
    assert second_worker == direct
    assert _target_hash(first_worker) == _target_hash(second_worker)


def test_frozen_current_candidate_and_no_control_policy_match_qr_decision() -> None:
    frozen = json.loads((_TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    risk_policy_bytes = (_TEAM_DIR / "risk_policy.json").read_bytes()
    policy = json.loads(risk_policy_bytes)
    assert frozen["candidate_id"] == "rdf-core-h21-k3-g10"
    assert (
        frozen["candidate_status"]
        == "deterministic_core_candidate_not_yet_registered_or_evaluated"
    )
    expected_candidate = dict(_BASELINE_FROZEN_PARAMETERS)
    expected_candidate["path_efficiency_exponent"] = 1.0
    assert frozen["parameters"] == expected_candidate
    assert {
        key: value
        for key, value in frozen["parameters"].items()
        if key != "path_efficiency_exponent"
    } == {
        key: value
        for key, value in _BASELINE_FROZEN_PARAMETERS.items()
        if key != "path_efficiency_exponent"
    }
    assert dataclasses.asdict(strategy_module.REFERENCE_PARAMETERS) == {
        "residual_lookback_days": 21,
        "skip_days": 3,
        "path_efficiency_exponent": 1.0,
        "rank_tail_fraction": 0.25,
        "direction_tilt_delta": 0.075,
        "beta_lookback_days": 30,
        "minimum_paired_returns": 72,
        "funding_lookback_days": 7,
        "minimum_funding_events": 14,
        "funding_penalty": 0.35,
        "direction_lookback_days": 60,
        "direction_return_scale": 0.2,
        "total_gross": 0.8,
        "per_symbol_cap": 0.09,
        "minimum_valid_symbols": 24,
        "minimum_names_per_side": 6,
    }
    assert frozen["execution_contract"] == {
        "bar_interval": "8h",
        "funding_availability": "funding_time < decision_time",
        "invalid_scheduled_request": "flat_empty_mapping",
        "non_rebalance_request": "hold_none",
        "rebalance_boundary_utc": "00:00",
        "target_execution": "organizer_owned_next_executable_open",
    }
    assert frozen["risk_policy"] == {
        "cost_multiplier": 1.0,
        "enabled_controls": [],
        "path": "risk_policy.json",
        "policy_id": "team-01-base",
    }
    assert frozen["seeds"] == {
        "canonical_runtime": _RUNTIME_SEED,
        "team_trial_search_placebo_namespace_not_used_for_targets": 2026080101,
    }
    assert hashlib.sha256(risk_policy_bytes).hexdigest() == (
        "9efd1401ffec46a7767fe625d70538b1aa5a9281a46fdb1bc06e90c264dc7e5b"
    )
    assert policy["drawdown_brakes"] == []
    assert policy["volatility_target"]["enabled"] is False
    assert policy["position_stop"]["enabled"] is False
    assert policy["time_stop"]["enabled"] is False
    assert policy["turnover_limit"]["enabled"] is False
    assert policy["side_scaling"] == {"long_scale": 1.0, "short_scale": 1.0}
    assert policy["same_boundary_reentry"] is False
