from __future__ import annotations

import dataclasses
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "team09_strategy_under_test", TEAM_DIR / "strategy.py"
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _context(*, confirmed: bool = True) -> SimpleNamespace:
    decision = pd.Timestamp(year=2023, month=1, day=2, tz="UTC")
    symbols = tuple(f"T{index:02d}USDT" for index in range(16))
    funding_levels = np.linspace(-0.0008, 0.0008, len(symbols))
    bar_times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=90, freq="8h")
    funding_times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=21, freq="8h")
    bars: dict[str, pd.DataFrame] = {}
    funding_rows: list[dict[str, object]] = []
    for symbol, level in zip(symbols, funding_levels, strict=True):
        desired = -1.0 if level > 0 else 1.0
        price_direction = desired if confirmed else -desired
        closes = 100.0 * np.exp(price_direction * 0.002 * np.arange(len(bar_times)))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": bar_times,
                "symbol": symbol,
                "open": closes / math.exp(price_direction * 0.001),
                "close": closes,
                "quote_volume": 1_000_000.0,
            }
        )
        funding_rows.extend(
            {
                "funding_time": timestamp,
                "symbol": symbol,
                "funding_rate": float(level),
                "mark_price": 100.0,
                "settlement_time": timestamp,
            }
            for timestamp in funding_times
        )
    return SimpleNamespace(
        decision_time=decision,
        eligible_symbols=symbols,
        bars=bars,
        funding=pd.DataFrame(funding_rows),
        auxiliary={},
    )


def _weights(context: SimpleNamespace) -> dict[str, float]:
    result = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert isinstance(result, dict)
    return result


def test_center_creates_balanced_material_long_and_short_sleeves() -> None:
    context = _context()
    weights = _weights(context)
    longs = {symbol: weight for symbol, weight in weights.items() if weight > 0}
    shorts = {symbol: weight for symbol, weight in weights.items() if weight < 0}

    assert len(longs) >= 4
    assert len(shorts) >= 4
    assert sum(longs.values()) == pytest.approx(-sum(shorts.values()))
    assert sum(abs(weight) for weight in weights.values()) <= 1.0
    assert abs(sum(weights.values())) <= 0.25
    assert max(abs(weight) for weight in weights.values()) <= 0.10
    assert set(weights).issubset(context.eligible_symbols)


def test_synthetic_positions_have_correct_relative_funding_carry_direction() -> None:
    context = _context()
    weights = _weights(context)
    mean_rates = context.funding.groupby("symbol")["funding_rate"].mean()
    # The central evaluator uses cashflow = -position * mark * funding_rate.
    relative_carry = sum(-weight * float(mean_rates[symbol]) for symbol, weight in weights.items())
    assert relative_carry > 0


def test_price_confirmation_is_required() -> None:
    assert _weights(_context(confirmed=False)) == {}


def test_equal_funding_pressure_requests_flat() -> None:
    context = _context()
    context.funding.loc[:, "funding_rate"] = 0.0001
    assert _weights(context) == {}


@pytest.mark.parametrize("stale", [False, True])
def test_missing_gap_or_stale_latest_bar_is_not_time_compressed(stale: bool) -> None:
    context = _context()
    affected = context.eligible_symbols[0]
    if stale:
        context.bars[affected] = context.bars[affected].iloc[:-1].copy()
    else:
        context.bars[affected] = context.bars[affected].drop(context.bars[affected].index[-10])
    weights = _weights(context)
    assert affected not in weights
    assert any(weight > 0 for weight in weights.values())
    assert any(weight < 0 for weight in weights.values())


def test_under_history_new_member_with_funding_does_not_abort_cross_section() -> None:
    context = _context()
    symbol = "NEWUSDT"
    context.eligible_symbols = (*context.eligible_symbols, symbol)
    context.bars[symbol] = next(iter(context.bars.values())).iloc[-10:].assign(symbol=symbol)
    extra = context.funding[context.funding["symbol"] == context.eligible_symbols[0]].copy()
    extra.loc[:, "symbol"] = symbol
    context.funding = pd.concat([context.funding, extra], ignore_index=True)

    weights = _weights(context)
    assert symbol not in weights
    assert weights


@pytest.mark.parametrize("funding_history", ["none", "insufficient", "stale"])
def test_member_without_usable_funding_is_excluded_without_aborting(
    funding_history: str,
) -> None:
    context = _context()
    symbol = "NEWUSDT"
    context.eligible_symbols = (*context.eligible_symbols, symbol)
    context.bars[symbol] = next(iter(context.bars.values())).assign(symbol=symbol)
    if funding_history != "none":
        extra = context.funding[context.funding["symbol"] == context.eligible_symbols[0]].copy()
        extra.loc[:, "symbol"] = symbol
        if funding_history == "insufficient":
            extra = extra.tail(STRATEGY.StrategyConfig().minimum_funding_events - 1)
        else:
            extra.loc[:, "funding_time"] -= pd.Timedelta(hours=24)
        context.funding = pd.concat([context.funding, extra], ignore_index=True)

    weights = _weights(context)
    assert symbol not in weights
    assert any(weight > 0 for weight in weights.values())
    assert any(weight < 0 for weight in weights.values())


def test_input_order_does_not_change_targets() -> None:
    context = _context()
    expected = _weights(context)
    context.eligible_symbols = tuple(reversed(context.eligible_symbols))
    context.bars = {
        symbol: context.bars[symbol].iloc[::-1].reset_index(drop=True)
        for symbol in context.eligible_symbols
    }
    context.funding = context.funding.iloc[::-1].reset_index(drop=True)
    assert _weights(context) == expected


def test_clean_instances_are_deterministic() -> None:
    context = _context()
    first = _weights(context)
    second = _weights(_context())
    assert first == second


def test_declared_score_boundary_is_called_once_and_returned_dict_drives_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, float]] = []

    def capture_and_zero(scores: dict[str, float]) -> dict[str, float]:
        assert type(scores) is dict
        assert scores
        assert all(type(symbol) is str for symbol in scores)
        assert all(type(value) is float and math.isfinite(value) for value in scores.values())
        calls.append(scores)
        for symbol in scores:
            scores[symbol] = 0.0
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture_and_zero)
    assert _weights(_context()) == {}
    assert len(calls) == 1


def test_declared_score_boundary_rejects_changed_object_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(STRATEGY, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(ValueError, match="object identity"):
        _weights(_context())


def test_future_bar_and_funding_rows_fail_closed() -> None:
    bar_context = _context()
    symbol = bar_context.eligible_symbols[0]
    future = bar_context.bars[symbol].iloc[[-1]].copy()
    future.loc[:, "open_time"] = bar_context.decision_time
    bar_context.bars[symbol] = pd.concat([bar_context.bars[symbol], future], ignore_index=True)
    with pytest.raises(ValueError, match="unavailable"):
        _weights(bar_context)

    funding_context = _context()
    future_funding = funding_context.funding.iloc[[0]].copy()
    future_funding.loc[:, "funding_time"] = funding_context.decision_time
    funding_context.funding = pd.concat(
        [funding_context.funding, future_funding], ignore_index=True
    )
    with pytest.raises(ValueError, match="non-past"):
        _weights(funding_context)


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("duplicate", "duplicate"),
        ("timestamp", "invalid"),
        ("rate", "invalid"),
        ("ineligible", "ineligible"),
    ],
)
def test_malformed_funding_fails_closed(fault: str, message: str) -> None:
    context = _context()
    if fault == "duplicate":
        context.funding = pd.concat([context.funding, context.funding.iloc[[0]]], ignore_index=True)
    elif fault == "timestamp":
        context.funding.loc[0, "funding_time"] = pd.NaT
    elif fault == "rate":
        context.funding.loc[0, "funding_rate"] = np.inf
    else:
        context.funding.loc[0, "symbol"] = "OUTSIDEUSDT"
    with pytest.raises(ValueError, match=message):
        _weights(context)


def test_non_rebalance_boundary_holds_and_wrong_seed_fails() -> None:
    context = _context()
    context.decision_time += pd.Timedelta(hours=8)
    assert STRATEGY.build_strategy().target_weights(context, seed=20260801) is None
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=7)
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=20260801.0)


def test_frozen_config_and_trial_template_cover_every_strategy_parameter() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    trial = json.loads((TEAM_DIR / "trial_registration_template.json").read_text(encoding="utf-8"))
    expected = dataclasses.asdict(STRATEGY.StrategyConfig())
    assert frozen["parameters"] == expected
    assert trial["parameters"] == expected
    assert frozen["seed"] == expected["expected_seed"]


def test_every_declared_neighbor_is_feasible_and_one_axis_from_center() -> None:
    manifest = json.loads((TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8"))
    center = STRATEGY.StrategyConfig()
    assert len(manifest["neighbors"]) == 10
    assert len({item["neighbor_id"] for item in manifest["neighbors"]}) == 10
    axes: dict[str, list[float]] = {}
    for item in manifest["neighbors"]:
        assert len(item["changes"]) == 1
        neighbor = dataclasses.replace(center, **item["changes"])
        neighbor.validate()
        assert neighbor != center
        field, value = next(iter(item["changes"].items()))
        axes.setdefault(field, []).append(value)
    assert len(axes) == 5
    for field, values in axes.items():
        assert len(values) == 2
        assert min(values) < getattr(center, field) < max(values)


def test_complete_family_cartesian_domain_is_declared_and_feasible() -> None:
    family = json.loads(
        (TEAM_DIR / "family_registration_template.json").read_text(encoding="utf-8")
    )
    domains = family["parameter_ranges"]
    fields = [field.name for field in dataclasses.fields(STRATEGY.StrategyConfig)]
    center = STRATEGY.StrategyConfig()
    assert set(domains) == set(fields)
    assert all(getattr(center, field) in domains[field] for field in fields)
    combinations = 0
    for values in itertools.product(*(domains[field] for field in fields)):
        dataclasses.replace(center, **dict(zip(fields, values, strict=True))).validate()
        combinations += 1
    assert combinations == 3**5


def test_score_manifest_binds_exact_a5_boundary_schedule_and_label() -> None:
    manifest = json.loads(
        (
            TEAM_DIR / "score-adapters/team09-fcpc-center-v1.score-adapter-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["adapter_id"] == STRATEGY.SCORE_ADAPTER_ID
    assert manifest["capture_boundary"] == STRATEGY.SCORE_CAPTURE_BOUNDARY
    assert manifest["hook"] == "strategy.score_boundary"
    assert manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 24,
    }
    assert manifest["label"] == {
        "executable_price_column": "open",
        "holding_horizon_hours": 24,
        "label_id": "manifest-horizon-simple-executable-open-to-open-return-v1",
        "minimum_pairs": 240,
        "purge_cross_fold_endpoints": True,
        "return_definition": "simple-executable-open-to-open",
        "score_direction": "higher-score-higher-return",
        "statistic_id": "globally-pooled-pearson-v1",
    }


def test_a7_a5_identity_chain_and_numeric_thresholds_are_candidate_exact() -> None:
    authority = json.loads((TEAM_DIR / "a7_execution_authority.json").read_text(encoding="utf-8"))
    lineage = json.loads((TEAM_DIR / "a5_score_lineage.json").read_text(encoding="utf-8"))
    thresholds = json.loads(
        (TEAM_DIR / "qualification_thresholds.json").read_text(encoding="utf-8")
    )
    assert authority["active_entrypoint"] == {
        "path": "scripts/top40_v2_tournament_runtime_preload_v7.py",
        "sha256": "8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9",
    }
    assert lineage["candidate_identity"] == {
        "candidate_id": "team09-fcpc-center-v1",
        "config_path": "tournament/top40-v2/teams/team-09/frozen_config.json",
        "family_id": "team09-funding-crowding-confirmation-v1",
        "risk_policy_id": "team09-risk-none",
        "risk_policy_path": "tournament/top40-v2/teams/team-09/risk_policy.json",
        "seed": 20260801,
        "strategy_factory": "build_strategy",
        "strategy_path": "tournament/top40-v2/teams/team-09/strategy.py",
        "team_id": "team-09",
    }
    development = thresholds["development_qualification"]
    assert thresholds["a5_score_diagnostics"] == {
        "complete_manifest_scheduled_score_coverage_required": True,
        "holding_horizon_hours": 24,
        "independent_semantic_coupling_approval_required": True,
        "minimum_pairs_per_fold": 240,
        "minimum_positive_fold_pearson_count": 4,
        "pooled_development_pearson": {"comparison": ">", "threshold": 0.0},
        "required_fold_count": 6,
        "schedule_interval_hours": 24,
        "team_noncompensatory_gate": True,
    }
    assert development["aggregate"] == {
        "maximum_drawdown": 0.3,
        "minimum_annualized_return": 0.0,
        "minimum_calmar": 0.4,
        "minimum_double_cost_sharpe": 0.35,
        "minimum_net_sharpe": 0.75,
        "minimum_positive_quarter_fraction": 0.55,
        "minimum_trial_adjusted_probability_positive": 0.9,
    }
    assert development["regimes"] == {
        "minimum_positive_sharpe_regimes": 3,
        "minimum_worst_regime_sharpe": -0.25,
        "required_positive_return_regimes": ["bull", "bear", "chop"],
    }
    assert development["stability"] == {
        "maximum_positive_pnl_concentration": 0.4,
        "minimum_neighbor_median_sharpe": 0.5,
        "minimum_profitable_neighbor_fraction": 0.7,
    }


def test_neighbor_staging_has_a_preresult_freeze_and_read_barrier() -> None:
    plan = json.loads((TEAM_DIR / "neighbor_staging_plan.json").read_text(encoding="utf-8"))
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    assert plan["declared_neighbor_count"] == len(neighborhood["neighbors"]) == 10
    assert plan["execution_mode"] == "strictly-serial"
    assert "all ten registrations are first-added" in plan["result_read_barrier"]
    assert any("may be an input" in rule for rule in plan["circularity_prohibitions"])


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"interval_hours": 8.0}, "integers"),
        ({"confirmation_bars": 9.5}, "integers"),
        ({"expected_seed": 20260801.0}, "integers"),
        ({"funding_half_life_hours": math.inf}, "finite"),
        ({"funding_lookback_hours": 170}, "complete funding intervals"),
        (
            {"funding_lookback_hours": 80, "minimum_funding_events": 12},
            "available slots",
        ),
        (
            {
                "funding_lookback_hours": 16,
                "minimum_funding_events": 2,
                "maximum_funding_age_hours": 24,
            },
            "cannot exceed",
        ),
        (
            {
                "maximum_symbols_per_side": 5,
                "maximum_symbol_weight": 0.08,
                "target_side_gross": 0.5,
            },
            "cannot fund",
        ),
    ],
)
def test_invalid_configuration_domain_fails_closed(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **changes).validate()
