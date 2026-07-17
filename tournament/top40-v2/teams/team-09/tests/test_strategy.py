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


def _context(*, symbol_count: int = 24, periods: int = 310) -> SimpleNamespace:
    decision = pd.Timestamp("2023-01-02T00:00:00Z")
    symbols = tuple(f"C{index:02d}USDT" for index in range(symbol_count))
    times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=periods, freq="8h")
    step = np.arange(periods, dtype=float)
    midpoint = (symbol_count - 1) / 2.0
    common = 0.00055 * np.sin(step / 9.0) + 0.00020 * np.cos(step / 23.0)
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        relative_drift = 0.00042 * (index - midpoint) / midpoint
        idiosyncratic = 0.00002 * np.sin(step / 17.0 + index * 0.31)
        increments = common + relative_drift + idiosyncratic
        log_close = math.log(100.0 + index) + np.cumsum(increments)
        closes = np.exp(log_close)
        bars[symbol] = pd.DataFrame(
            {
                "open_time": times,
                "symbol": symbol,
                "open": closes / np.exp(0.5 * increments),
                "close": closes,
                "quote_volume": 1_000_000.0 + index,
            }
        )
    return SimpleNamespace(
        decision_time=decision,
        eligible_symbols=symbols,
        bars=bars,
        auxiliary={},
    )


def _weights(context: SimpleNamespace) -> dict[str, float]:
    result = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert isinstance(result, dict)
    return result


def test_center_is_broad_balanced_and_structurally_low_gross() -> None:
    context = _context()
    weights = _weights(context)
    longs = {symbol: weight for symbol, weight in weights.items() if weight > 0.0}
    shorts = {symbol: weight for symbol, weight in weights.items() if weight < 0.0}

    assert 6 <= len(longs) <= 8
    assert 6 <= len(shorts) <= 8
    assert sum(longs.values()) == pytest.approx(-sum(shorts.values()))
    assert sum(abs(weight) for weight in weights.values()) < 0.20
    assert abs(sum(weights.values())) <= 1e-12
    assert max(abs(weight) for weight in weights.values()) <= 0.015
    assert max(abs(weight) for weight in weights.values()) <= 0.0125 + 1e-12
    assert set(weights).issubset(context.eligible_symbols)


def test_persistent_relative_leaders_are_long_and_laggards_short() -> None:
    context = _context()
    weights = _weights(context)
    indices = {symbol: index for index, symbol in enumerate(context.eligible_symbols)}
    long_indices = [indices[symbol] for symbol, weight in weights.items() if weight > 0.0]
    short_indices = [indices[symbol] for symbol, weight in weights.items() if weight < 0.0]
    assert min(long_indices) > max(short_indices)


def test_extreme_crash_fragility_is_zeroed_before_a5_and_never_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    symbol = context.eligible_symbols[len(context.eligible_symbols) // 2]
    frame = context.bars[symbol].copy()
    start_log = math.log(float(frame["close"].iloc[-92]))
    shocks = np.resize(np.array([0.20, -0.19], dtype=float), 91)
    frame.loc[frame.index[-91:], "close"] = np.exp(start_log + np.cumsum(shocks))
    context.bars[symbol] = frame
    captured: dict[str, float] = {}

    def capture(scores: dict[str, float]) -> dict[str, float]:
        captured.update(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    weights = _weights(context)
    assert captured[symbol] == 0.0
    assert symbol not in weights
    assert any(weight > 0.0 for weight in weights.values())
    assert any(weight < 0.0 for weight in weights.values())


def test_score_magnitude_shrinks_weights_without_gross_restoration() -> None:
    config = STRATEGY.StrategyConfig()
    weights = _weights(_context())
    structural_base = config.target_side_gross / config.maximum_symbols_per_side
    assert max(abs(weight) for weight in weights.values()) <= structural_base
    assert sum(abs(weight) for weight in weights.values()) < 2.0 * config.target_side_gross


def test_no_funding_or_portfolio_state_is_required() -> None:
    context = _context()
    assert not hasattr(context, "funding")
    assert not hasattr(context, "positions")
    assert _weights(context)


def test_missing_gap_or_stale_symbol_is_excluded_without_time_compression() -> None:
    for stale in (False, True):
        context = _context()
        affected = context.eligible_symbols[0]
        if stale:
            context.bars[affected] = context.bars[affected].iloc[:-1].copy()
        else:
            context.bars[affected] = context.bars[affected].drop(context.bars[affected].index[-10])
        weights = _weights(context)
        assert affected not in weights
        assert any(weight > 0.0 for weight in weights.values())
        assert any(weight < 0.0 for weight in weights.values())


def test_under_history_new_member_does_not_abort_cross_section() -> None:
    context = _context()
    symbol = "NEWUSDT"
    context.eligible_symbols = (*context.eligible_symbols, symbol)
    context.bars[symbol] = next(iter(context.bars.values())).iloc[-50:].assign(symbol=symbol)
    weights = _weights(context)
    assert symbol not in weights
    assert weights


def test_input_order_and_clean_instances_are_deterministic() -> None:
    context = _context()
    expected = _weights(context)
    context.eligible_symbols = tuple(reversed(context.eligible_symbols))
    context.bars = {
        symbol: context.bars[symbol].iloc[::-1].reset_index(drop=True)
        for symbol in context.eligible_symbols
    }
    assert _weights(context) == expected
    assert _weights(_context()) == expected


def test_declared_score_boundary_is_called_once_and_returned_dict_drives_book(
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


def test_scheduled_insufficient_breadth_captures_one_empty_score_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, float]] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
        calls.append(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    assert _weights(_context(symbol_count=12)) == {}
    assert calls == [{}]


def test_declared_score_boundary_rejects_identity_keys_and_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(STRATEGY, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(ValueError, match="object identity"):
        _weights(_context())

    def remove_key(scores: dict[str, float]) -> dict[str, float]:
        scores.pop(next(iter(scores)))
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", remove_key)
    with pytest.raises(ValueError, match="exact score keys"):
        _weights(_context())

    def inject_nonfinite(scores: dict[str, float]) -> dict[str, float]:
        scores[next(iter(scores))] = math.inf
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", inject_nonfinite)
    with pytest.raises(TypeError, match="invalid score values"):
        _weights(_context())


def test_future_duplicate_and_invalid_bars_fail_closed() -> None:
    future_context = _context()
    symbol = future_context.eligible_symbols[0]
    future = future_context.bars[symbol].iloc[[-1]].copy()
    future.loc[:, "open_time"] = future_context.decision_time
    future_context.bars[symbol] = pd.concat(
        [future_context.bars[symbol], future], ignore_index=True
    )
    with pytest.raises(ValueError, match="unavailable"):
        _weights(future_context)

    duplicate_context = _context()
    symbol = duplicate_context.eligible_symbols[0]
    duplicate_context.bars[symbol] = pd.concat(
        [duplicate_context.bars[symbol], duplicate_context.bars[symbol].iloc[[-1]]],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="duplicate"):
        _weights(duplicate_context)

    invalid_context = _context()
    symbol = invalid_context.eligible_symbols[0]
    invalid_context.bars[symbol].loc[invalid_context.bars[symbol].index[-1], "close"] = np.inf
    with pytest.raises(ValueError, match="invalid close"):
        _weights(invalid_context)


def test_context_membership_must_match_a6_eligible_set_exactly() -> None:
    context = _context()
    context.bars["OUTSIDEUSDT"] = next(iter(context.bars.values())).copy()
    with pytest.raises(ValueError, match="match the eligible-symbol set"):
        _weights(context)

    duplicate = _context()
    duplicate.eligible_symbols = (*duplicate.eligible_symbols, duplicate.eligible_symbols[0])
    with pytest.raises(ValueError, match="duplicates"):
        _weights(duplicate)

    mismatch = _context()
    symbol = mismatch.eligible_symbols[0]
    mismatch.bars[symbol].loc[:, "symbol"] = "OTHERUSDT"
    with pytest.raises(ValueError, match="mismatched symbol"):
        _weights(mismatch)


def test_schedule_grid_and_seed_are_exact() -> None:
    context = _context()
    context.decision_time += pd.Timedelta(hours=8)
    assert STRATEGY.build_strategy().target_weights(context, seed=20260801) is None

    off_grid = _context()
    off_grid.decision_time += pd.Timedelta(hours=1)
    with pytest.raises(ValueError, match="eight-hour grid"):
        STRATEGY.build_strategy().target_weights(off_grid, seed=20260801)

    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=7)
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=20260801.0)


def test_frozen_config_and_trial_template_cover_every_strategy_parameter() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    trial = json.loads((TEAM_DIR / "trial_registration_template.json").read_text(encoding="utf-8"))
    expected = dataclasses.asdict(STRATEGY.StrategyConfig())
    assert frozen["parameters"] == expected
    trial_parameters = dict(trial["parameters"])
    score_opt_in = trial_parameters.pop("_top40_v2_score_adapter")
    assert trial_parameters == expected
    assert score_opt_in == {
        "adapter_id": STRATEGY.SCORE_ADAPTER_ID,
        "manifest_sha256": "<organizer-fill-canonical-score-adapter-manifest-64-hex-sha256>",
        "schema_version": 1,
    }
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
            TEAM_DIR / "score-adapters/team09-drp-pivot02-v1.score-adapter-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["adapter_id"] == STRATEGY.SCORE_ADAPTER_ID
    assert manifest["capture_boundary"] == STRATEGY.SCORE_CAPTURE_BOUNDARY
    assert manifest["hook"] == "strategy.score_boundary"
    expected_horizon = (
        STRATEGY.StrategyConfig().interval_hours * STRATEGY.StrategyConfig().rebalance_every_bars
    )
    assert expected_horizon == 72
    assert manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 72,
    }
    assert manifest["label"] == {
        "executable_price_column": "open",
        "holding_horizon_hours": 72,
        "label_id": "manifest-horizon-simple-executable-open-to-open-return-v1",
        "minimum_pairs": 240,
        "purge_cross_fold_endpoints": True,
        "return_definition": "simple-executable-open-to-open",
        "score_direction": "higher-score-higher-return",
        "statistic_id": "globally-pooled-pearson-v1",
    }
    assert manifest["schedule_utc"]["interval_hours"] == expected_horizon
    assert manifest["label"]["holding_horizon_hours"] == expected_horizon


def test_a7_a5_pure_crypto_identity_and_pivot02_gates_are_exact() -> None:
    authority = json.loads((TEAM_DIR / "a7_execution_authority.json").read_text(encoding="utf-8"))
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    lineage = json.loads((TEAM_DIR / "a5_score_lineage.json").read_text(encoding="utf-8"))
    thresholds = json.loads(
        (TEAM_DIR / "qualification_thresholds.json").read_text(encoding="utf-8")
    )
    assert authority["candidate_id"] == "team09-drp-pivot02-v1"
    assert authority["family_id"] == "team09-defensive-residual-persistence-v1"
    assert authority["active_entrypoint"] == {
        "path": "scripts/top40_v2_tournament_runtime_preload_v7.py",
        "sha256": "8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9",
    }
    pure_crypto = authority["pure_crypto_report"]
    assert pure_crypto == {
        "policy_sha256": "2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350",
        "report_sha256": "b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b",
        "violations": 0,
    }
    assert (
        frozen["pure_crypto_authority"]["canonical_report_sha256"] == (pure_crypto["report_sha256"])
    )
    assert frozen["pure_crypto_authority"]["required_violations"] == 0
    assert lineage["candidate_identity"]["candidate_id"] == "team09-drp-pivot02-v1"
    assert lineage["candidate_identity"]["family_id"] == (
        "team09-defensive-residual-persistence-v1"
    )
    assert lineage["pivot_lineage"]["ordinal"] == 2
    assert len(lineage["pivot_lineage"]["prior_trials"]) == 2
    assert thresholds["a5_score_diagnostics"]["holding_horizon_hours"] == 72
    assert thresholds["a5_score_diagnostics"]["schedule_interval_hours"] == 72
    assert thresholds["pivot_02_mechanism_gate"] == {
        "bear_net_return": {"comparison": ">", "threshold": 0.0},
        "bear_net_sharpe": {"comparison": ">", "threshold": 0.0},
        "bull_net_return": {"comparison": ">", "threshold": 0.0},
        "bull_net_sharpe": {"comparison": ">", "threshold": 0.0},
        "chop_net_return": {"comparison": ">", "threshold": 0.0},
        "chop_net_sharpe": {"comparison": ">", "threshold": 0.0},
        "completed_without_insolvency": True,
        "maximum_drawdown": {"comparison": "<=", "threshold": 0.25},
        "maximum_requested_gross": {"comparison": "<=", "threshold": 0.2},
        "maximum_requested_symbol_weight": {
            "comparison": "<=",
            "threshold": 0.015,
        },
        "non_compensatory": True,
    }


def test_neighbor_staging_has_center_gate_and_preresult_read_barrier() -> None:
    plan = json.loads((TEAM_DIR / "neighbor_staging_plan.json").read_text(encoding="utf-8"))
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    assert plan["candidate_id"] == "team09-drp-pivot02-v1"
    assert plan["declared_neighbor_count"] == len(neighborhood["neighbors"]) == 10
    assert plan["execution_mode"] == "strictly-serial"
    assert "all ten registrations are first-added" in plan["result_read_barrier"]
    assert "no-control pivot-02 center" in plan["stages"][1]["requirements"][0]
    assert any("may be an input" in rule for rule in plan["circularity_prohibitions"])


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"interval_hours": 8.0}, "integers"),
        ({"expected_seed": 20260801.0}, "integers"),
        ({"rebalance_every_bars": 1}, "slower"),
        ({"persistence_block_count": 1}, "at least two"),
        ({"fragility_bars": 271}, "fit inside"),
        ({"minimum_cross_section": 10}, "support both"),
        ({"fragility_exclusion_quantile": 0.5}, "must be in"),
        ({"fragility_exclusion_quantile": 0.55}, "leave both"),
        ({"downside_semideviation_weight": 0.5}, "sum to one"),
        ({"fragility_shrink_strength": math.inf}, "finite"),
        ({"target_side_gross": 0.16}, "must be in"),
        ({"maximum_symbol_weight": 0.01}, "base allocation"),
    ],
)
def test_invalid_configuration_domain_fails_closed(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **changes).validate()
