from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import research_extension_v3, research_extension_v3_compat, runner_v3
from crypto_trade.tournament.protocol import DecisionContext

ROOT = Path(__file__).resolve().parents[2]
TEAM06_ORIGINAL = ROOT / "tournament/top40-v3/teams/team-06/strategy.py"
TEAM06_COMMON = (
    ROOT
    / "tournament/top40-v3/teams/team-06/post-tournament-momentum-r1/strategy_common.py"
)
TEAM04_ORIGINAL = (
    ROOT
    / "tournament/top40-v3/teams/team-04/incumbents/"
    "team-04-utc-reference-001-v3-port/strategy.py"
)
TEAM04_COMMON = (
    ROOT / "tournament/top40-v3/teams/team-04/post-tournament-utc-r1/strategy_common.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _team06_context() -> DecisionContext:
    decision = pd.Timestamp("2023-06-26T00:00:00Z")
    symbols = tuple(f"T{index:02d}USDT" for index in range(16))
    times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=100, freq="8h")
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        direction = 1.0 if index < 8 else -1.0
        price = 100.0 + index
        rows: list[dict[str, object]] = []
        for step, open_time in enumerate(times):
            amplitude = 0.00025 + 0.00002 * (index % 4)
            log_return = direction * 0.0009 + amplitude * math.sin(
                0.31 * step + 0.17 * index
            )
            price *= math.exp(log_return)
            rows.append({"open_time": open_time, "symbol": symbol, "close": price})
        bars[symbol] = pd.DataFrame(rows)
    return DecisionContext(
        decision_time=decision,
        bars=bars,
        funding=pd.DataFrame(
            columns=["funding_time", "symbol", "funding_rate", "mark_price"]
        ),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _team04_context(original) -> DecisionContext:
    decision = pd.Timestamp("2023-01-05T00:00:00Z")
    interval = pd.Timedelta(hours=8)
    symbols = tuple(f"C{index:02d}USDT" for index in range(40))
    cutoff = decision - interval
    expected = original._expected_open_times(cutoff, original._REFERENCE.history_return_bars)
    bars: dict[str, pd.DataFrame] = {}
    funding_rows: list[dict[str, object]] = []
    midpoint = (len(symbols) - 1) / 2.0
    for index, symbol in enumerate(symbols):
        loading = (index - midpoint) / midpoint
        price = 100.0 + index
        rows: list[dict[str, object]] = []
        for step, open_time in enumerate(expected):
            move = 0.001 * loading + (0.0003 + 0.00002 * index) * math.sin(
                0.47 * step + 0.19 * index
            )
            price *= math.exp(move)
            rows.append(
                {
                    "symbol": symbol,
                    "open_time": open_time,
                    "close_time": open_time + interval,
                    "close": price,
                }
            )
        bars[symbol] = pd.DataFrame(rows)
        rate = -loading * 0.00004
        start = decision - pd.Timedelta(days=7)
        for event in range(21):
            funding_rows.append(
                {
                    "funding_time": start + event * interval,
                    "symbol": symbol,
                    "funding_rate": rate,
                }
            )
    return DecisionContext(
        decision_time=decision,
        bars=bars,
        funding=pd.DataFrame(funding_rows),
        auxiliary={},
        eligible_symbols=symbols,
    )


def test_policy_has_two_bounded_six_candidate_lanes() -> None:
    policy = research_extension_v3.load_policy(ROOT)
    specs = [
        research_extension_v3.candidate_spec(policy, team_id, row["candidate_id"])
        for team_id in ("team-04", "team-06")
        for row in policy["candidate_matrix"][team_id]
    ]
    assert len(specs) == 12
    assert {spec.team_id for spec in specs} == {"team-04", "team-06"}
    with pytest.raises(research_extension_v3.ResearchExtensionError):
        research_extension_v3.candidate_spec(policy, "team-06", "undeclared")


def test_every_declared_entrypoint_builds_its_exact_parameter_row() -> None:
    policy = research_extension_v3.load_policy(ROOT)
    for team_id in ("team-04", "team-06"):
        candidate_root = ROOT / policy["candidate_roots"][team_id]
        sys.path.insert(0, str(candidate_root))
        try:
            sys.modules.pop("strategy_common", None)
            for index, row in enumerate(policy["candidate_matrix"][team_id]):
                module = _load(
                    candidate_root / row["entrypoint"],
                    f"_research_extension_{team_id.replace('-', '')}_{index}",
                )
                instance = module.build_strategy()
                parameters = (
                    instance._parameters if team_id == "team-04" else instance.parameters
                )
                for name, expected in row["parameters"].items():
                    assert getattr(parameters, name) == expected
        finally:
            sys.modules.pop("strategy_common", None)
            sys.path.remove(str(candidate_root))


def test_team06_research_baseline_exactly_matches_frozen_strategy() -> None:
    original = _load(TEAM06_ORIGINAL, "_research_ext_t06_original")
    research = _load(TEAM06_COMMON, "_research_ext_t06_common")
    context = _team06_context()
    expected = original.build_strategy().target_weights(context, seed=20260718)
    actual = research.OwnCoinMomentumResearch(
        research.StrategyParameters()
    ).target_weights(context, seed=20260718)
    assert actual == expected
    assert research._is_scheduled(
        pd.Timestamp("2023-06-26T00:00:00Z"), research.StrategyParameters(rebalance_days=3)
    )
    assert not research._is_scheduled(
        pd.Timestamp("2023-06-27T00:00:00Z"), research.StrategyParameters(rebalance_days=3)
    )


def test_team04_research_baseline_exactly_matches_frozen_strategy() -> None:
    original = _load(TEAM04_ORIGINAL, "_research_ext_t04_original")
    research = _load(TEAM04_COMMON, "_research_ext_t04_common")
    context = _team04_context(original)
    expected = original.build_strategy().target_weights(context, seed=20260718)
    actual = research.UncrowdedTrendCarryResearch(
        research.StrategyParameters()
    ).target_weights(context, seed=20260718)
    assert actual == expected


def test_team04_rank_buffer_retains_names_until_they_leave_the_wider_band() -> None:
    research = _load(TEAM04_COMMON, "_research_ext_t04_buffer")
    scores = {f"S{index:02d}": float(index) for index in range(40)}
    baseline = research._select_sleeves(
        scores,
        previous_long=frozenset({"S25"}),
        previous_short=frozenset({"S14"}),
        parameters=research.StrategyParameters(rank_buffer_fraction=0.25),
    )
    buffered = research._select_sleeves(
        scores,
        previous_long=frozenset({"S25"}),
        previous_short=frozenset({"S14"}),
        parameters=research.StrategyParameters(rank_buffer_fraction=0.4),
    )
    assert baseline is not None and buffered is not None
    assert "S25" not in baseline[0] and "S14" not in baseline[1]
    assert "S25" in buffered[0] and "S14" in buffered[1]
    assert set(buffered[0]).isdisjoint(buffered[1])


def _passing_summary() -> dict[str, object]:
    fold = {
        "base_cumulative_return": 0.1,
        "base_metrics": {"net_sharpe": 1.0},
        "double_cost_cumulative_return": 0.05,
    }
    return {
        "diagnostics": {
            "annualized_turnover": 20.0,
            "base_cost_share_of_positive_gross_pnl": 0.25,
            "gross_edge_per_turnover_bps": 50.0,
            "trade_count": 1500,
        },
        "double_cost": {"metrics": {"net_sharpe": 0.8}},
        "folds": [dict(fold) for _ in range(4)],
        "regime_sharpe": {"bear": 0.5, "bull": 0.4, "chop": 0.3, "stress": 0.2},
        "scored_window": {
            "metrics": {
                "annualized_return": 0.1,
                "max_drawdown": 0.1,
                "net_sharpe": 1.1,
                "positive_quarter_fraction": 0.75,
            }
        },
    }


def test_selection_is_conjunctive_and_turnover_is_an_economic_floor() -> None:
    policy = research_extension_v3.load_policy(ROOT)
    passing = _passing_summary()
    assert research_extension_v3.assess_selection(passing, policy)["ready"] is True
    passing["diagnostics"]["annualized_turnover"] = 30.0001
    result = research_extension_v3.assess_selection(passing, policy)
    assert result["ready"] is False
    assert result["gates"]["annualized_turnover"] is False


def test_append_only_journal_chain_detects_tampering(tmp_path: Path) -> None:
    extension = tmp_path / research_extension_v3.EXTENSION_ROOT
    extension.mkdir(parents=True)
    first = research_extension_v3._append_event(tmp_path, "test", {"value": 1})
    second = research_extension_v3._append_event(tmp_path, "test", {"value": 2})
    assert second["previous_sha256"] == first["record_sha256"]
    journal = tmp_path / research_extension_v3.JOURNAL_PATH
    rows = journal.read_text(encoding="ascii").splitlines()
    decoded = json.loads(rows[0])
    decoded["value"] = 9
    rows[0] = json.dumps(decoded, separators=(",", ":"), sort_keys=True)
    journal.write_text("\n".join(rows) + "\n", encoding="ascii")
    with pytest.raises(research_extension_v3.ResearchExtensionError, match="chain"):
        research_extension_v3._journal_records(tmp_path)


def test_utc_metric_compatibility_changes_only_bound_normalization() -> None:
    index = pd.date_range("2020-02-03", periods=120, freq="1D", tz="UTC")
    base = pd.Series(0.001 + 0.002 * np.sin(np.arange(120) / 4.0), index=index)
    stressed = base - 0.0001
    btc = pd.Series(0.003 + 0.001 * np.sin(np.arange(120) / 7.0), index=index)
    authorized = runner_v3.AuthorizedWindow(
        stage="public",
        replay_start="2020-02-03T00:00:00Z",
        end_exclusive="2020-06-02T00:00:00Z",
        score_start="2020-02-03T00:00:00Z",
        score_end_inclusive="2020-06-01",
    )
    config = {
        "statistics": {
            "bootstrap_samples": 100,
            "bootstrap_block_days": 10,
            "bootstrap_seed": 7,
        }
    }
    with pytest.raises(ValueError, match="same UTC offset"):
        runner_v3._compute_metrics(base, stressed, btc, config, authorized)
    result = research_extension_v3_compat.compute_metrics_utc_compatible(
        base, stressed, btc, config, authorized
    )
    expected = research_extension_v3.metrics_v3.compute_window_metrics(base)
    assert result["scored_window"].metrics.net_sharpe == pytest.approx(expected.net_sharpe)
    assert result["scored_window"].start == authorized.score_start
    assert result["scored_window"].end == authorized.score_end_inclusive
    original = runner_v3._compute_metrics
    with research_extension_v3_compat.utc_metric_slice_compatibility():
        assert (
            runner_v3._compute_metrics
            is research_extension_v3_compat.compute_metrics_utc_compatible
        )
    assert runner_v3._compute_metrics is original
