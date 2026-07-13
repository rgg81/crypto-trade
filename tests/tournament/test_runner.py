from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import _strategy_worker as strategy_worker
from crypto_trade.tournament import engine, runner
from crypto_trade.tournament.engine import EvaluationResult
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext


def _authorized_run_team(*args, **kwargs):
    kwargs["_authorization"] = runner._ORGANIZER_RUN_AUTHORIZATION
    return runner.run_team(*args, **kwargs)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_layout(root: Path, *, strategy_source: str | None = None) -> tuple[Path, Path, Path]:
    entrypoint = root / "tournament/top40/teams/team-01/strategy.py"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text(
        strategy_source
        or """
class Strategy:
    def target_weights(self, context, *, seed):
        return {}

def build_strategy():
    return Strategy()
""".lstrip(),
        encoding="utf-8",
    )
    config = root / "tournament/top40/config.toml"
    config.write_text(
        """
teams = ["team-01"]

[data]
warmup_start = "2020-01-01"
hard_end_exclusive = "2026-07-01"
transaction_interval = "8h"

[splits]
in_sample_start = "2020-02-03"
in_sample_end_inclusive = "2024-06-30"
public_oos_start = "2024-07-01"
public_oos_end_inclusive = "2026-06-30"

[execution]
base_interval = "8h"
initial_equity_usdt = 100000.0
taker_fee_bps_per_side = 5.0
slippage_bps_per_side = 2.5
max_gross_exposure = 1.0
max_abs_net_exposure = 0.25
max_symbol_exposure = 0.10
max_bar_participation = 0.001
double_cost_multiplier = 2.0
annualization_days = 365

[regimes]
stress_trailing_days = 30
stress_annualized_btc_vol = 0.80
direction_trailing_days = 60
bull_btc_return = 0.10
bear_btc_return = -0.10
lag_days = 1

[statistics]
bootstrap_samples = 100
bootstrap_block_days = 10
bootstrap_seed = 123

[research_budget]
strategy_seed = 7
""".lstrip(),
        encoding="utf-8",
    )
    manifest = root / "tournament/top40/data_manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    return entrypoint, config, manifest


def _write_phase0_bound_snapshot(root: Path) -> tuple[Path, dict[str, Path]]:
    """Create a minimal canonical snapshot with the real Phase-0 Git topology."""
    snapshot_dir = root / "data/top40/snapshot-v1"
    snapshot_dir.mkdir(parents=True)
    frames = {
        "bars": pd.DataFrame(
            {
                "open_time": [pd.Timestamp("2020-01-01", tz="UTC")],
                "symbol": ["BTCUSDT"],
                "open": [10_000.0],
                "close": [10_001.0],
                "quote_volume": [1_000_000.0],
            }
        ),
        "funding": pd.DataFrame(
            {
                "funding_time": [pd.Timestamp("2020-01-01", tz="UTC")],
                "symbol": ["BTCUSDT"],
                "funding_rate": [0.0001],
                "mark_price": [10_000.0],
            }
        ),
        "mark_prices": pd.DataFrame(
            {
                "mark_time": [pd.Timestamp("2020-01-01", tz="UTC")],
                "symbol": ["BTCUSDT"],
                "mark_price": [10_000.0],
            }
        ),
        "membership": pd.DataFrame(
            {
                "reconstitution_time": [pd.Timestamp("2019-12-30", tz="UTC")],
                "symbol": ["BTCUSDT"],
                "liquidity_rank": [1],
                "trailing_quote_volume": [1_000_000.0],
            }
        ),
        "contract_metadata": pd.DataFrame({"symbol": ["BTCUSDT"], "contract_type": ["PERPETUAL"]}),
    }
    canonical_paths: dict[str, Path] = {}
    for name, frame in frames.items():
        path = snapshot_dir / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        canonical_paths[name] = path
    text_files = {
        "archive_provenance": snapshot_dir / "archive_provenance.jsonl",
        "coverage": snapshot_dir / "coverage.json",
        "exchange_info": snapshot_dir / "exchange_info.json",
        "mark_rest_provenance": snapshot_dir / "mark_rest_provenance.jsonl",
        "rest_provenance": snapshot_dir / "rest_provenance.jsonl",
        "btc_daily_returns": root / "reports-top40/common/btc_daily_returns.csv",
        "btc_regimes": root / "reports-top40/common/btc_regimes.csv",
    }
    for name, path in text_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"canonical {name}\n", encoding="utf-8")
        canonical_paths[name] = path

    common_paths = {
        runner.tournament_contract.CANONICAL_CONFIG_PATH: "[data]\n",
        runner.tournament_contract.PHASE0_POLICY_PATH: "frozen policy\n",
        runner.tournament_contract.ROOT_DEPENDENCY_LOCK_PATH: "frozen dependencies\n",
        runner.tournament_contract.ORCHESTRATOR_SCRIPT_PATH: "# frozen organizer\n",
        runner._SNAPSHOT_BUILDER_PATH: "# frozen snapshot builder\n",
    }
    for relative in (
        *runner.tournament_contract.EVALUATOR_SOURCE_PATHS,
        *runner.tournament_contract.METHODOLOGY_PATHS,
    ):
        common_paths.setdefault(relative, f"frozen {relative}\n")
    for relative, content in common_paths.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    entries = []
    for name, path in canonical_paths.items():
        entries.append(
            {
                "name": name,
                "path": path.relative_to(root).as_posix(),
                "rows": len(frames[name]) if name in frames else 1,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": path.stat().st_size,
            }
        )
    entries.sort(key=lambda entry: entry["path"])
    builder = root / runner._SNAPSHOT_BUILDER_PATH
    manifest_payload = {
        "schema_version": 1,
        "parser_version": "top40-snapshot-v1",
        "window": {
            "warmup_start": "2020-01-01T00:00:00+00:00",
            "evaluation_start": "2020-02-03T00:00:00+00:00",
            "hard_end_exclusive": "2026-07-01T00:00:00+00:00",
        },
        "sources": {
            "builder_path": runner._SNAPSHOT_BUILDER_PATH,
            "builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        },
        "limitations": ["frozen test limitation"],
        "files": entries,
    }
    manifest = root / runner.tournament_contract.CANONICAL_MANIFEST_PATH
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    teams = {
        f"team-{number:02d}": {"champion": None, "canonical_run": "pending"}
        for number in range(1, 11)
    }
    state_path = root / runner.tournament_contract.RUN_STATE_PATH
    state_path.write_text(
        json.dumps({"phase": "phase0", "teams": teams}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Top40 Test")
    _git(root, "checkout", "-qb", runner.tournament_contract.TOURNAMENT_BRANCH)
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "common Phase-0 inputs")
    common_commit = _git(root, "rev-parse", "HEAD")

    evaluator_sha256 = runner.sha256_manifest(
        [root / path for path in runner.tournament_contract.EVALUATOR_SOURCE_PATHS],
        root=root,
    )[0]
    methodology_sha256 = runner.sha256_manifest(
        [root / path for path in runner.tournament_contract.METHODOLOGY_PATHS],
        root=root,
    )[0]
    by_name = {entry["name"]: entry for entry in entries}
    freeze = {
        "schema_version": 1,
        "frozen_at_utc": "2026-07-13T00:00:00+00:00",
        "branch": runner.tournament_contract.TOURNAMENT_BRANCH,
        "common_freeze_commit": common_commit,
        "data_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "evaluator_sha256": evaluator_sha256,
        "methodology_sha256": methodology_sha256,
        "config_sha256": hashlib.sha256(
            (root / runner.tournament_contract.CANONICAL_CONFIG_PATH).read_bytes()
        ).hexdigest(),
        "btc_daily_returns_sha256": by_name["btc_daily_returns"]["sha256"],
        "btc_regimes_sha256": by_name["btc_regimes"]["sha256"],
        "phase0_policy_sha256": hashlib.sha256(
            (root / runner.tournament_contract.PHASE0_POLICY_PATH).read_bytes()
        ).hexdigest(),
        "snapshot_builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        "root_dependency_lock_sha256": hashlib.sha256(
            (root / runner.tournament_contract.ROOT_DEPENDENCY_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "orchestrator_sha256": hashlib.sha256(
            (root / runner.tournament_contract.ORCHESTRATOR_SCRIPT_PATH).read_bytes()
        ).hexdigest(),
    }
    freeze_path = root / runner.tournament_contract.PHASE0_FREEZE_PATH
    freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state = {
        "phase": "research",
        "teams": teams,
        **{
            field: freeze[field]
            for field in (
                "common_freeze_commit",
                "data_manifest_sha256",
                "evaluator_sha256",
                "methodology_sha256",
                "config_sha256",
                "orchestrator_sha256",
            )
        },
    }
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _git(root, "add", runner.tournament_contract.PHASE0_FREEZE_PATH)
    _git(root, "add", runner.tournament_contract.RUN_STATE_PATH)
    _git(root, "commit", "-qm", "first-add Phase-0 record")
    return manifest, canonical_paths


def _snapshot(
    manifest_sha256: str = "a" * 64,
    *,
    file_hashes: dict[Path, str] | None = None,
) -> runner._SnapshotData:
    times = pd.date_range("2020-01-01", "2026-07-01", freq="8h", inclusive="left", tz="UTC")
    price = 10_000.0 * np.exp(np.arange(len(times), dtype=float) * 0.00001)
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": "BTCUSDT",
            "open": price,
            "close": price * 1.00001,
            "quote_volume": 10_000_000.0,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": pd.Series(dtype="datetime64[ns, UTC]"),
            "symbol": pd.Series(dtype=str),
            "funding_rate": pd.Series(dtype=float),
            "mark_price": pd.Series(dtype=float),
        }
    )
    mark_prices = bars.loc[:, ["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [pd.Timestamp("2019-12-30", tz="UTC")],
            "symbol": ["BTCUSDT"],
            "liquidity_rank": [1],
            "trailing_quote_volume": [1.0],
        }
    )
    contracts = pd.DataFrame({"symbol": ["BTCUSDT"], "contract_type": ["PERPETUAL"]})
    return runner._SnapshotData(
        manifest_sha256=manifest_sha256,
        paths={},
        file_hashes=file_hashes or {},
        bars=bars,
        funding=funding,
        mark_prices=mark_prices,
        membership=membership,
        contract_metadata=contracts,
    )


def _result(index: pd.DatetimeIndex, *, stressed: bool = False) -> EvaluationResult:
    phase = np.arange(len(index), dtype=float)
    net_return = np.where((phase.astype(int) % 5) == 0, 0.0002, -0.00002)
    if stressed:
        net_return = net_return - 0.00001
    returns = pd.DataFrame(
        {
            "price_pnl": net_return,
            "long_price_pnl": net_return,
            "short_price_pnl": 0.0,
            "funding_pnl": 0.0,
            "long_funding_pnl": 0.0,
            "short_funding_pnl": 0.0,
            "fees": 0.0,
            "slippage": 0.0,
            "net_return": net_return,
            "turnover": 0.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "long_exposure": 0.0,
            "short_exposure": 0.0,
            "requested_notional": 0.0,
            "unfilled_notional": 0.0,
            "forced_exit_turnover": 0.0,
            "risk_reduction_turnover": 0.0,
            "risk_cap_breach": False,
            "risk_cap_required_scale": 1.0,
            "equity": 100_000.0 * np.cumprod(1.0 + net_return),
        },
        index=index,
    )
    positions = pd.DataFrame({"BTCUSDT": np.zeros(len(index))}, index=index)
    events = pd.DataFrame(
        {
            "timestamp": [index[0], index[-1]],
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "event_type": ["trade", "funding"],
            "phase": ["rebalance", "holding"],
            "quantity": [1.0, 1.0],
            "price": [10_000.0, 10_000.0],
            "notional": [10_000.0, 10_000.0],
            "funding_rate": [0.0, 0.0001],
            "cashflow": [0.0, -1.0],
            "fee": [5.0, 0.0],
            "slippage": [2.5, 0.0],
        }
    )
    return EvaluationResult(returns=returns, positions=positions, events=events)


def _mock_canonical_evaluation(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    monkeypatch.setattr(
        runner,
        "_load_verified_snapshot",
        lambda _root, path: _snapshot(hashlib.sha256(path.read_bytes()).hexdigest()),
    )
    observed_seeds: list[int] = []

    def fake_generate(
        root,
        team_id,
        entrypoint,
        bars,
        funding,
        membership,
        decision_times,
        *,
        seed,
        interval_hours,
        expected_source_bundle_sha256,
    ):
        assert root.is_dir()
        assert team_id == "team-01"
        assert entrypoint.name == "strategy.py"
        assert interval_hours == 8
        assert len(expected_source_bundle_sha256) == 64
        observed_seeds.append(seed)
        return pd.DataFrame({"BTCUSDT": 0.0}, index=decision_times)

    def fake_evaluate(bars, funding, membership, targets, *, mark_prices, config):
        assert config.interval_hours == 8
        assert set(mark_prices) == {"mark_time", "symbol", "mark_price"}
        return _result(targets.index), _result(targets.index, stressed=True)

    monkeypatch.setattr(runner, "_generate_targets_in_worker", fake_generate)
    monkeypatch.setattr(runner, "evaluate_base_and_double_cost", fake_evaluate)
    return observed_seeds


def _bypass_worker_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    def command(
        root: Path,
        repository_parent: Path,
        bundle: Path,
        site_packages: Path,
        runtime_site_packages: Path,
        entrypoint: str,
        empty_dir: Path,
        empty_file: Path,
    ) -> list[str]:
        return [
            sys.executable,
            "-u",
            "-m",
            "crypto_trade.tournament._strategy_worker",
            "--root",
            str(root),
            "--repository-parent",
            str(repository_parent),
            "--bundle",
            str(bundle),
            "--site-packages",
            str(site_packages),
            "--runtime-site-packages",
            str(runtime_site_packages),
            "--entrypoint",
            entrypoint,
            "--empty-dir",
            str(empty_dir),
            "--empty-file",
            str(empty_file),
            "--test-bypass-namespace",
        ]

    monkeypatch.setattr(runner, "_strategy_worker_command", command)


def _small_market() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    times = pd.date_range("2020-01-01", periods=5, freq="8h", tz="UTC")
    rows = []
    for symbol_index, symbol in enumerate(("AAAUSDT", "BBBUSDT")):
        for index, timestamp in enumerate(times):
            price = 100.0 + symbol_index * 10 + index
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price + 0.5,
                    "quote_volume": 1_000_000.0,
                }
            )
    bars = pd.DataFrame(rows)
    funding = pd.DataFrame(
        {
            "funding_time": [times[0] + pd.Timedelta(hours=4), times[2]],
            "symbol": ["AAAUSDT", "AAAUSDT"],
            "funding_rate": [0.0001, 0.0002],
            "mark_price": [100.0, 102.0],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0], times[2], times[3]],
            "symbol": ["AAAUSDT", "BBBUSDT", "BBBUSDT", "AAAUSDT"],
            "liquidity_rank": [1, 2, 1, 1],
            "trailing_quote_volume": [2.0, 1.0, 2.0, 2.0],
        }
    )
    return bars, funding, membership, times[1:]


class _RecordingWorker:
    def __init__(self) -> None:
        self.init_payload: dict[str, object] | None = None
        self.requests: list[dict[str, object]] = []

    def initialise(self, payload) -> None:
        self.init_payload = dict(payload)

    def request(self, payload):
        self.requests.append(dict(payload))
        return {"type": "weights", "weights": {}}


def _captured_context(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    decision_time: pd.Timestamp,
) -> DecisionContext:
    contexts: list[DecisionContext] = []

    class CaptureStrategy:
        def target_weights(self, context: DecisionContext, *, seed: int):
            contexts.append(context)
            return {}

    engine.generate_targets(
        CaptureStrategy(),
        bars,
        funding,
        membership,
        [decision_time],
        seed=7,
    )
    return contexts[0]


def _empty_worker_state(strategy) -> strategy_worker._WorkerState:
    bars, funding, _, _ = _small_market()
    canonical_bars = engine._normalise_bars(bars)
    canonical_funding = engine._normalise_funding(funding)
    return strategy_worker._WorkerState(
        strategy=strategy,
        seed=7,
        interval=pd.Timedelta(hours=8),
        bar_columns=tuple(str(column) for column in canonical_bars.columns),
        bar_dtypes=tuple(str(dtype) for dtype in canonical_bars.dtypes),
        bar_datetime_columns=frozenset(runner._datetime_columns(canonical_bars)),
        funding_columns=tuple(str(column) for column in canonical_funding.columns),
        funding_dtypes=tuple(str(dtype) for dtype in canonical_funding.dtypes),
        funding_datetime_columns=frozenset(runner._datetime_columns(canonical_funding)),
    )


def test_full_window_runner_requires_organizer_authorization(tmp_path: Path):
    entrypoint, config, manifest = _write_layout(tmp_path)
    with pytest.raises(PermissionError, match="trusted organizer operation"):
        runner.run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )


def test_run_team_publishes_exact_deterministic_artifacts_and_submission_scalars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    observed_seeds = _mock_canonical_evaluation(monkeypatch)

    result = _authorized_run_team(
        tmp_path,
        "team-01",
        entrypoint.relative_to(tmp_path),
        config.relative_to(tmp_path),
        manifest.relative_to(tmp_path),
    )

    assert observed_seeds == [7]
    expected_grid = pd.date_range("2020-02-03", "2026-07-01", freq="8h", inclusive="left", tz="UTC")
    report = tmp_path / result.output_dir
    assert sorted(path.name for path in report.iterdir()) == [
        "bar_returns.csv",
        "daily_returns.csv",
        "double_cost_bar_returns.csv",
        "double_cost_daily_returns.csv",
        "events.parquet",
        "positions.parquet",
        "targets.parquet",
        "trades.csv",
    ]
    targets = pd.read_parquet(report / "targets.parquet")
    assert pd.DatetimeIndex(targets["timestamp"]).equals(expected_grid)
    assert targets[REBALANCE_INSTRUCTION_COLUMN].dtype == bool
    assert targets[REBALANCE_INSTRUCTION_COLUMN].all()
    bars = pd.read_csv(report / "bar_returns.csv")
    assert len(bars) == len(expected_grid)
    daily = pd.read_csv(report / "daily_returns.csv")
    assert len(daily) == len(pd.date_range("2020-02-03", "2026-06-30", freq="1D"))
    trades = pd.read_csv(report / "trades.csv")
    assert trades["event_type"].tolist() == ["trade"]
    assert result.decision_count == len(expected_grid)
    assert result.event_count == 2
    assert result.trade_count == 1
    assert set(result.regime_sharpe) == {"bear", "bull", "chop", "stress"}
    assert set(result.confidence_intervals) == {
        "is_net_sharpe_95",
        "public_oos_net_sharpe_95",
        "double_cost_oos_net_sharpe_95",
    }
    fields = result.submission_fields()
    assert fields["in_sample"]["start"] == "2020-02-03"
    assert fields["public_oos"]["end"] == "2026-06-30"

    first_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in report.iterdir()
    }
    _authorized_run_team(
        tmp_path,
        "team-01",
        entrypoint.relative_to(tmp_path),
        config.relative_to(tmp_path),
        manifest.relative_to(tmp_path),
    )
    second_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in report.iterdir()
    }
    assert first_hashes == second_hashes


def test_run_team_rejects_truncated_evaluator_before_creating_team_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    monkeypatch.setattr(
        runner,
        "_load_verified_snapshot",
        lambda _root, path: _snapshot(hashlib.sha256(path.read_bytes()).hexdigest()),
    )
    monkeypatch.setattr(
        runner,
        "_generate_targets_in_worker",
        lambda _root, _team, _entrypoint, _bars, _funding, _membership, decision_times, **_kwargs: (
            pd.DataFrame({"BTCUSDT": 0.0}, index=decision_times)
        ),
    )

    def truncated(_bars, _funding, _membership, targets, **_kwargs):
        index = targets.index[:-1]
        return _result(index), _result(index, stressed=True)

    monkeypatch.setattr(runner, "evaluate_base_and_double_cost", truncated)
    with pytest.raises(ValueError, match="canonical 8h grid"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )
    assert not (tmp_path / "reports-top40/team-01").exists()


def test_run_team_binds_and_rehashes_the_complete_worker_source_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    helper = entrypoint.with_name("helper.py")
    helper.write_text("VALUE = 1\n", encoding="utf-8")
    _mock_canonical_evaluation(monkeypatch)

    def mutating_evaluator(_bars, _funding, _membership, targets, **_kwargs):
        helper.write_text("VALUE = 2\n", encoding="utf-8")
        return _result(targets.index), _result(targets.index, stressed=True)

    monkeypatch.setattr(runner, "evaluate_base_and_double_cost", mutating_evaluator)
    with pytest.raises(ValueError, match="source_bundle"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )
    assert not (tmp_path / "reports-top40/team-01").exists()


def test_run_team_blocks_network_in_build_strategy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    entrypoint, config, manifest = _write_layout(
        tmp_path,
        strategy_source="""
import socket

def build_strategy():
    try:
        socket.create_connection(("example.com", 443))
    except Exception:
        pass

    class Strategy:
        def target_weights(self, context, *, seed):
            return {}

    return Strategy()
""".lstrip(),
    )
    monkeypatch.setattr(
        runner,
        "_load_verified_snapshot",
        lambda _root, path: _snapshot(hashlib.sha256(path.read_bytes()).hexdigest()),
    )
    with pytest.raises(runner.NetworkAccessError, match="network access is disabled"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )
    assert not (tmp_path / "reports-top40/team-01").exists()


def test_run_team_rehashes_snapshot_files_after_team_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    snapshot_file = tmp_path / "data/top40/snapshot-v1/bars.parquet"
    snapshot_file.parent.mkdir(parents=True)
    snapshot_file.write_bytes(b"frozen snapshot bytes")
    snapshot_sha256 = hashlib.sha256(snapshot_file.read_bytes()).hexdigest()
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    monkeypatch.setattr(
        runner,
        "_load_verified_snapshot",
        lambda *_args: _snapshot(manifest_sha256, file_hashes={snapshot_file: snapshot_sha256}),
    )
    monkeypatch.setattr(
        runner,
        "_generate_targets_in_worker",
        lambda _root, _team, _entrypoint, _bars, _funding, _membership, decision_times, **_kwargs: (
            pd.DataFrame({"BTCUSDT": 0.0}, index=decision_times)
        ),
    )

    def mutating_evaluator(_bars, _funding, _membership, targets, **_kwargs):
        snapshot_file.write_bytes(b"team-mutated snapshot bytes")
        return _result(targets.index), _result(targets.index, stressed=True)

    monkeypatch.setattr(runner, "evaluate_base_and_double_cost", mutating_evaluator)
    with pytest.raises(ValueError, match="snapshot file changed during team run"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )
    assert not (tmp_path / "reports-top40/team-01").exists()


def test_verified_manifest_supports_explicit_names_and_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    snapshot_dir = tmp_path / "data/top40/snapshot-v1"
    snapshot_dir.mkdir(parents=True)
    frames = {
        "market.parquet": pd.DataFrame({"open_time": [1], "symbol": ["BTCUSDT"]}),
        "rates.parquet": pd.DataFrame({"funding_time": [1], "symbol": ["BTCUSDT"]}),
        "marks.parquet": pd.DataFrame({"mark_time": [1], "symbol": ["BTCUSDT"]}),
        "membership.parquet": pd.DataFrame({"reconstitution_time": [1], "symbol": ["BTCUSDT"]}),
        "contract_metadata.parquet": pd.DataFrame({"symbol": ["BTCUSDT"]}),
    }
    entries = []
    for filename, frame in frames.items():
        path = snapshot_dir / filename
        frame.to_parquet(path, index=False)
        entry = {
            "path": path.relative_to(tmp_path).as_posix(),
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        if filename == "market.parquet":
            entry["dataset"] = "bars"
        elif filename == "rates.parquet":
            entry["name"] = "funding.parquet"
        elif filename == "marks.parquet":
            entry["dataset"] = "mark_prices"
        entries.append(entry)
    manifest = tmp_path / "tournament/top40/data_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    monkeypatch.setattr(runner, "_invoke_snapshot_verifier", lambda *_args: None)

    loaded = runner._load_verified_snapshot(tmp_path, manifest)
    assert loaded.paths["bars"].name == "market.parquet"
    assert loaded.paths["funding"].name == "rates.parquet"
    assert set(loaded.paths) == {
        "bars",
        "funding",
        "mark_prices",
        "membership",
        "contract_metadata",
    }

    with (snapshot_dir / "market.parquet").open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="size mismatch|sha256 mismatch"):
        runner._load_verified_snapshot(tmp_path, manifest)


def test_snapshot_loader_calls_full_verifier_without_phase0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest, _ = _write_phase0_bound_snapshot(tmp_path)
    (tmp_path / runner.tournament_contract.PHASE0_FREEZE_PATH).unlink()
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        runner,
        "_invoke_snapshot_verifier",
        lambda root, path: calls.append((root, path)),
    )

    loaded = runner._load_verified_snapshot(tmp_path, manifest)

    assert calls == [(tmp_path, manifest)]
    assert set(loaded.paths) == set(runner._REQUIRED_DATASETS)


def test_snapshot_loader_skips_full_verifier_only_for_exact_phase0_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest, _ = _write_phase0_bound_snapshot(tmp_path)
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        runner,
        "_invoke_snapshot_verifier",
        lambda root, path: calls.append((root, path)),
    )

    runner._load_verified_snapshot(tmp_path, manifest)
    assert calls == []

    builder = tmp_path / runner._SNAPSHOT_BUILDER_PATH
    builder.write_text("# changed after Phase-0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid Phase-0 snapshot binding"):
        runner._load_verified_snapshot(tmp_path, manifest)
    assert calls == []


def test_phase0_fast_path_rejects_manifest_and_canonical_file_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest, canonical_paths = _write_phase0_bound_snapshot(tmp_path)
    monkeypatch.setattr(
        runner,
        "_invoke_snapshot_verifier",
        lambda *_args: pytest.fail("a present but invalid Phase-0 record must fail closed"),
    )

    original_manifest = manifest.read_text(encoding="utf-8")
    payload = json.loads(original_manifest)
    payload["parser_version"] = "tampered-parser"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="data_manifest_sha256|common_freeze_commit"):
        runner._load_verified_snapshot(tmp_path, manifest)

    manifest.write_text(original_manifest, encoding="utf-8")
    bars = canonical_paths["bars"]
    original_bars = bars.read_bytes()
    bars.write_bytes(original_bars[:-1] + bytes([original_bars[-1] ^ 1]))
    with pytest.raises(ValueError, match="snapshot sha256 mismatch"):
        runner._load_verified_snapshot(tmp_path, manifest)


def test_entrypoint_must_remain_in_declared_team_namespace(tmp_path: Path):
    entrypoint, config, manifest = _write_layout(tmp_path)
    wrong = tmp_path / "tournament/top40/teams/team-02/strategy.py"
    wrong.parent.mkdir(parents=True)
    wrong.write_text(entrypoint.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="team-01"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            wrong.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )


def test_worker_command_uses_required_linux_namespaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(runner.shutil, "which", lambda name: f"/usr/bin/{name}")
    command = runner._strategy_worker_command(
        tmp_path,
        tmp_path / "repository-parent",
        tmp_path / "bundle",
        tmp_path / "site-packages",
        tmp_path / "runtime-site-packages",
        "strategy.py",
        tmp_path / "empty-dir",
        tmp_path / "empty-file",
    )
    assert command[:10] == [
        "/usr/bin/unshare",
        "--user",
        "--map-root-user",
        "--mount",
        "--net",
        "--pid",
        "--fork",
        "--kill-child=KILL",
        "--mount-proc",
        sys.executable,
    ]


def test_worker_command_fails_closed_without_unshare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(runner.shutil, "which", lambda _name: None)
    with pytest.raises(runner.StrategySandboxError, match="refusing an unsandboxed"):
        runner._strategy_worker_command(
            tmp_path,
            tmp_path / "repository-parent",
            tmp_path / "bundle",
            tmp_path / "site-packages",
            tmp_path / "runtime-site-packages",
            "strategy.py",
            tmp_path / "empty-dir",
            tmp_path / "empty-file",
        )


def test_worker_environment_pins_hash_seed_and_single_thread_libraries(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("PYTHONHASHSEED", "random")
    monkeypatch.setenv("OMP_NUM_THREADS", "64")
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "32")
    monkeypatch.setenv("LD_PRELOAD", "/tmp/untrusted.so")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "organizer-cloud-secret")
    monkeypatch.setenv("GITHUB_TOKEN", "organizer-github-secret")
    monkeypatch.setenv("HTTPS_PROXY", "http://organizer-proxy.invalid")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/organizer-agent.sock")

    environment = runner._strategy_worker_environment(20260713)

    assert environment["PYTHONHASHSEED"] == "20260713"
    assert environment["PYTHONUNBUFFERED"] == "1"
    assert all(environment[name] == "1" for name in runner._SINGLE_THREAD_ENVIRONMENT_VARIABLES)
    assert environment["HOME"] == "/nonexistent"
    assert not {
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "HTTPS_PROXY",
        "LD_PRELOAD",
        "SSH_AUTH_SOCK",
    }.intersection(environment)
    assert os.environ["PYTHONHASHSEED"] == "random"
    with pytest.raises(runner.StrategySandboxError, match="PYTHONHASHSEED"):
        runner._strategy_worker_environment(-1)


def test_launched_worker_observes_canonical_deterministic_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
import os

THREAD_VARIABLES = (
    "BLIS_NUM_THREADS",
    "GOTO_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OMP_THREAD_LIMIT",
    "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)

class Strategy:
    def target_weights(self, context, *, seed):
        deterministic = (
            os.environ.get("PYTHONHASHSEED") == str(seed)
            and all(os.environ.get(name) == "1" for name in THREAD_VARIABLES)
        )
        return {
            context.eligible_symbols[0]: 0.01 if deterministic else -0.01
        }

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times[:1],
        seed=7,
        interval_hours=8,
    )

    assert targets.iloc[0]["AAAUSDT"] == pytest.approx(0.01)


def test_complete_tree_fingerprint_stages_only_python_and_fixed_config(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "strategy.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "model.json").write_text("{}\n", encoding="utf-8")
    (source / "notes.md").write_text("Research evidence.\n", encoding="utf-8")
    (source / "frozen_config.json").write_text('{"lookback": 30}\n', encoding="utf-8")
    (source / "submission.json").write_text("secret\n", encoding="utf-8")
    (source / "artifact_manifest.json").write_text("secret\n", encoding="utf-8")
    destination = tmp_path / "destination"

    fingerprint = runner._copy_team_source_bundle(source, destination)
    entries = runner._team_tree_files(source)

    assert fingerprint == runner._team_tree_fingerprint(entries)
    assert {item.relative for item in entries} == {
        "frozen_config.json",
        "model.json",
        "notes.md",
        "strategy.py",
    }
    assert sorted(path.name for path in destination.iterdir()) == [
        "frozen_config.json",
        "strategy.py",
    ]

    (source / "model.json").write_text('{"changed": true}\n', encoding="utf-8")
    assert runner._team_tree_fingerprint(runner._team_tree_files(source)) != fingerprint


def test_team_tree_rejects_opaque_prefit_artifacts(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "strategy.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "prefit-model.pkl").write_bytes(b"opaque learned state")

    with pytest.raises(runner.StrategySandboxError, match="opaque/prefit"):
        runner._copy_team_source_bundle(source, tmp_path / "destination")


def test_team_tree_rejects_timestamp_keyed_target_artifacts(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "strategy.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "strategy_config.json").write_text(
        '{"2025-01-01": {"BTCUSDT": 0.5}}\n', encoding="utf-8"
    )

    with pytest.raises(runner.StrategySandboxError, match="timestamp-keyed"):
        runner._copy_team_source_bundle(source, tmp_path / "destination")


def test_worker_proxy_requires_exact_bar_symbols_and_uses_private_canonical_prefix():
    bars, funding, membership, decision_times = _small_market()
    canonical_bars = engine._normalise_bars(bars)
    canonical_funding = engine._normalise_funding(funding)
    context = _captured_context(bars, funding, membership, decision_times[-1])
    worker = _RecordingWorker()
    proxy = runner._WorkerStrategyProxy(
        worker,
        seed=7,
        interval_hours=8,
        bar_schema=canonical_bars.iloc[0:0],
        funding_schema=canonical_funding.iloc[0:0],
        bar_history=canonical_bars,
        funding_history=canonical_funding,
    )

    with pytest.raises(runner.StrategySandboxError, match="exactly the eligible"):
        proxy.target_weights(dataclasses.replace(context, bars={}), seed=7)
    extra = dict(context.bars)
    extra["ZZZUSDT"] = next(iter(context.bars.values()))
    with pytest.raises(runner.StrategySandboxError, match="exactly the eligible"):
        proxy.target_weights(dataclasses.replace(context, bars=extra), seed=7)

    symbol = context.eligible_symbols[0]
    changed_edge = context.bars[symbol].copy(deep=True)
    changed_edge.loc[0, "close"] = -1.0
    with pytest.raises(runner.StrategySandboxError, match="boundary changed"):
        proxy.target_weights(dataclasses.replace(context, bars={symbol: changed_edge}), seed=7)

    changed_middle = context.bars[symbol].copy(deep=True)
    changed_middle.loc[1, "close"] = -999.0
    proxy.target_weights(dataclasses.replace(context, bars={symbol: changed_middle}), seed=7)

    request = worker.requests[-1]
    close_index = proxy.bar_columns.index("close")
    canonical_symbol = proxy.bar_history[symbol]
    assert request["bars"][symbol][1][close_index] == canonical_symbol.iloc[1]["close"]
    assert request["bars"][symbol][1][close_index] != -999.0


def test_worker_rejects_row_key_mismatch_and_non_append_only_timestamps():
    class NullStrategy:
        def target_weights(self, context, *, seed):
            return {}

    bars, funding, _, times = _small_market()
    canonical_bars = engine._normalise_bars(bars)
    canonical_funding = engine._normalise_funding(funding)
    first_bar = canonical_bars[canonical_bars["symbol"].eq("AAAUSDT")].iloc[[0]]
    bar_row = runner._encoded_rows(first_bar, canonical_bars.columns)[0]

    mismatched = list(bar_row)
    mismatched[list(canonical_bars.columns).index("symbol")] = "BBBUSDT"
    with pytest.raises(ValueError, match="symbol differs from its update key"):
        strategy_worker._decision(
            _empty_worker_state(NullStrategy()),
            {
                "type": "decision",
                "decision_time": times[0].isoformat(),
                "eligible_symbols": ["AAAUSDT"],
                "bars": {"AAAUSDT": [mismatched]},
                "funding": {},
            },
        )

    state = _empty_worker_state(NullStrategy())
    strategy_worker._decision(
        state,
        {
            "type": "decision",
            "decision_time": times[0].isoformat(),
            "eligible_symbols": ["AAAUSDT"],
            "bars": {"AAAUSDT": [bar_row]},
            "funding": {},
        },
    )
    with pytest.raises(ValueError, match="strictly append-only"):
        strategy_worker._decision(
            state,
            {
                "type": "decision",
                "decision_time": times[1].isoformat(),
                "eligible_symbols": ["AAAUSDT"],
                "bars": {"AAAUSDT": [bar_row]},
                "funding": {},
            },
        )

    future_funding = canonical_funding.iloc[[0]].copy()
    future_funding.loc[:, "funding_time"] = times[0]
    future_funding.loc[:, "settlement_time"] = times[0]
    funding_row = runner._encoded_rows(future_funding, canonical_funding.columns)[0]
    with pytest.raises(ValueError, match="funding that was not strictly past"):
        strategy_worker._decision(
            _empty_worker_state(NullStrategy()),
            {
                "type": "decision",
                "decision_time": times[0].isoformat(),
                "eligible_symbols": ["AAAUSDT"],
                "bars": {"AAAUSDT": [bar_row]},
                "funding": {"AAAUSDT": [funding_row]},
            },
        )


def test_worker_proxy_matches_authoritative_contexts_across_drop_and_reentry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
class Strategy:
    def target_weights(self, context, *, seed):
        funding_score = sum(
            (index + 1) * float(row.funding_rate)
            for index, row in enumerate(context.funding.itertuples(index=False))
        )
        return {
            symbol: sum(
                (index + 1) * float(close)
                for index, close in enumerate(context.bars[symbol]["close"])
            ) * 0.00001 + funding_score
            for symbol in context.eligible_symbols
        }

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    class LocalStrategy:
        def target_weights(self, context, *, seed):
            funding_score = sum(
                (index + 1) * float(row.funding_rate)
                for index, row in enumerate(context.funding.itertuples(index=False))
            )
            return {
                symbol: sum(
                    (index + 1) * float(close)
                    for index, close in enumerate(context.bars[symbol]["close"])
                )
                * 0.00001
                + funding_score
                for symbol in context.eligible_symbols
            }

    expected = engine.generate_targets(
        LocalStrategy(),
        bars,
        funding,
        membership,
        decision_times,
        seed=7,
    )
    actual = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times,
        seed=7,
        interval_hours=8,
    )

    pd.testing.assert_frame_equal(actual, expected)
    assert actual.loc[decision_times[-1], "AAAUSDT"] > actual.loc[decision_times[0], "AAAUSDT"]


def test_none_survives_worker_runner_engine_and_published_target_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
class Strategy:
    def __init__(self):
        self.calls = 0

    def target_weights(self, context, *, seed):
        self.calls += 1
        if self.calls == 1:
            return {context.eligible_symbols[0]: 0.05}
        return None

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    times = pd.date_range("2020-01-01", periods=5, freq="8h", tz="UTC")
    prices = [100.0, 100.0, 200.0, 200.0, 200.0]
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": "AAAUSDT",
            "open": prices,
            "close": prices,
            "quote_volume": 1_000_000_000.0,
        }
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]],
            "symbol": ["AAAUSDT"],
            "liquidity_rank": [1],
            "trailing_quote_volume": [1.0],
        }
    )
    decisions = times[1:]
    raw = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decisions,
        seed=7,
        interval_hours=8,
    )
    targets = runner._canonical_targets(raw, bars, decisions)
    marks = bars.loc[:, ["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    config = engine.EvaluatorConfig(max_bar_participation=1.0, max_symbol_exposure=0.2)
    base, stressed = engine.evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=marks,
        config=config,
    )
    daily = pd.Series([0.0], index=pd.DatetimeIndex([decisions[0].normalize()]))
    artifacts = runner._publish_artifacts(
        tmp_path,
        "team-01",
        targets=targets,
        base=base,
        stressed=stressed,
        base_daily=daily,
        stressed_daily=daily,
    )

    assert targets[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, False, False, False]
    assert base.returns.loc[decisions[1], "turnover"] == pytest.approx(0.0)
    strategy_trades = base.events[
        base.events["timestamp"].eq(decisions[1]) & base.events["event_type"].eq("trade")
    ]
    assert strategy_trades.empty
    published = pd.read_parquet(tmp_path / artifacts["targets"])
    assert pd.api.types.is_bool_dtype(published[REBALANCE_INSTRUCTION_COLUMN].dtype)
    assert published[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, False, False, False]


def test_worker_strategy_mutations_cannot_change_later_contexts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
class Strategy:
    def __init__(self):
        self.retained = []

    def target_weights(self, context, *, seed):
        result = {}
        for symbol in context.eligible_symbols:
            frame = context.bars[symbol]
            contaminated = "injected" in frame
            close = float(frame["close"].iloc[0])
            funding_rate = (
                0.0 if context.funding.empty
                else float(context.funding["funding_rate"].iloc[0])
            )
            result[symbol] = -1.0 if contaminated else close * 0.0001 + funding_rate
            for retained in self.retained:
                try:
                    retained.loc[retained.index[0], "close"] = -777.0
                except Exception:
                    pass
            try:
                frame.loc[frame.index[0], "close"] = -999.0
            except Exception:
                pass
            try:
                frame["close"].to_numpy(copy=False)[0] = -888.0
            except Exception:
                pass
            frame["injected"] = 1
            self.retained.append(frame)
        if not context.funding.empty:
            try:
                context.funding.loc[context.funding.index[0], "funding_rate"] = 9.0
            except Exception:
                pass
            context.funding["injected"] = 1
        return result

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times,
        seed=7,
        interval_hours=8,
    )

    expected_aaa = 100.5 * 0.0001 + 0.0001
    assert targets.loc[decision_times[0], "AAAUSDT"] == pytest.approx(expected_aaa)
    assert targets.loc[decision_times[2], "AAAUSDT"] == pytest.approx(expected_aaa)
    assert (targets.to_numpy() >= 0.0).all()


def test_worker_stable_universe_uses_geometric_buffers_without_history_rebuilds(
    monkeypatch: pytest.MonkeyPatch,
):
    class MeasuringStrategy:
        def __init__(self) -> None:
            self.observed_lengths: list[tuple[tuple[int, ...], int]] = []

        def target_weights(self, context, *, seed):
            self.observed_lengths.append(
                (
                    tuple(len(context.bars[symbol]) for symbol in context.eligible_symbols),
                    len(context.funding),
                )
            )
            return {}

    strategy = MeasuringStrategy()
    state = _empty_worker_state(strategy)
    original_rebuild = strategy_worker._rebuild_funding_context
    rebuild_count = 0

    def tracked_rebuild(*args, **kwargs):
        nonlocal rebuild_count
        rebuild_count += 1
        return original_rebuild(*args, **kwargs)

    monkeypatch.setattr(strategy_worker, "_rebuild_funding_context", tracked_rebuild)
    symbols = ("AAAUSDT", "BBBUSDT", "CCCUSDT")
    start = pd.Timestamp("2020-01-01", tz="UTC")
    decisions = 70
    for index in range(decisions):
        open_time = start + pd.Timedelta(hours=8 * index)
        decision_time = open_time + pd.Timedelta(hours=8)
        funding_time = decision_time - pd.Timedelta(hours=4)
        bar_updates = {
            symbol: [[open_time.isoformat(), symbol, 100.0, 100.5, 1_000_000.0]]
            for symbol in symbols
        }
        funding_updates = {
            symbol: [
                [
                    0.0001,
                    funding_time.isoformat(),
                    100.0,
                    symbol,
                    funding_time.floor("h").isoformat(),
                ]
            ]
            for symbol in symbols
        }
        strategy_worker._decision(
            state,
            {
                "type": "decision",
                "decision_time": decision_time.isoformat(),
                "eligible_symbols": list(symbols),
                "bars": bar_updates,
                "funding": funding_updates,
            },
        )

    assert rebuild_count == 1
    assert strategy.observed_lengths[-1] == ((decisions,) * len(symbols), decisions * 3)
    assert state.funding_context is not None
    buffers = [*(state.bars[symbol] for symbol in symbols), state.funding_context]
    for buffer in buffers:
        assert buffer.length <= buffer.capacity < 2 * buffer.length
        assert all(not values.flags.writeable for values in buffer.arrays.values())
    close_values = state.bars[symbols[0]].frame()["close"].to_numpy(copy=False)
    assert np.shares_memory(close_values, state.bars[symbols[0]].arrays["close"])


def test_worker_cannot_monkeypatch_parent_runner_or_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
def poison(*args, **kwargs):
    raise AssertionError("child replaced trusted evaluator")

try:
    import crypto_trade.tournament.engine as attacked_engine
    import crypto_trade.tournament.runner as attacked_runner
except ImportError:
    pass
else:
    attacked_engine.evaluate_base_and_double_cost = poison
    attacked_runner.evaluate_base_and_double_cost = poison

class Strategy:
    def target_weights(self, context, *, seed):
        return {symbol: 0.0 for symbol in context.eligible_symbols}

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()
    parent_runner_evaluator = runner.evaluate_base_and_double_cost
    parent_engine_evaluator = engine.evaluate_base_and_double_cost

    with pytest.raises(runner.StrategySandboxError, match="runtime allowlist"):
        runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times,
            seed=7,
            interval_hours=8,
        )

    assert runner.evaluate_base_and_double_cost is parent_runner_evaluator
    assert engine.evaluate_base_and_double_cost is parent_engine_evaluator


def test_worker_cannot_read_snapshot_or_another_team(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    snapshot_secret = tmp_path / "data/top40/snapshot-v1/secret.txt"
    other_team_secret = tmp_path / "tournament/top40/teams/team-02/secret.txt"
    snapshot_secret.parent.mkdir(parents=True)
    other_team_secret.parent.mkdir(parents=True)
    snapshot_secret.write_text("future snapshot value\n", encoding="utf-8")
    other_team_secret.write_text("other team value\n", encoding="utf-8")
    source = f"""
from pathlib import Path

SECRETS = ({str(snapshot_secret)!r}, {str(other_team_secret)!r})

class Strategy:
    def target_weights(self, context, *, seed):
        exposed = False
        for path in SECRETS:
            try:
                exposed = exposed or bool(Path(path).read_text())
            except Exception:
                pass
        return {{symbol: 0.05 if exposed else 0.0 for symbol in context.eligible_symbols}}

def build_strategy():
    return Strategy()
""".lstrip()
    entrypoint, _, _ = _write_layout(tmp_path, strategy_source=source)
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    with pytest.raises(runner.StrategySandboxError, match="runtime allowlist"):
        runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times,
            seed=7,
            interval_hours=8,
        )


def test_landlock_blocks_native_reads_of_arbitrary_host_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    host_secret = tmp_path / "organizer-secret.txt"
    host_secret.write_text("host credential material\n", encoding="utf-8")
    source = f"""
import ctypes
import errno
import os

HOST_SECRET = {str(host_secret)!r}

class Strategy:
    def target_weights(self, context, *, seed):
        libc = ctypes.CDLL(None, use_errno=True)
        libc.open.argtypes = [ctypes.c_char_p, ctypes.c_int]
        libc.open.restype = ctypes.c_int
        descriptor = libc.open(HOST_SECRET.encode(), os.O_RDONLY)
        blocked = descriptor < 0 and ctypes.get_errno() in (errno.EACCES, errno.EPERM)
        if descriptor >= 0:
            os.close(descriptor)
        return {{symbol: 0.01 if blocked else 0.09 for symbol in context.eligible_symbols}}

def build_strategy():
    return Strategy()
""".lstrip()
    entrypoint, _, _ = _write_layout(tmp_path, strategy_source=source)
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times[:1],
        seed=7,
        interval_hours=8,
    )

    assert targets.loc[decision_times[0], "AAAUSDT"] == pytest.approx(0.01)


@pytest.mark.parametrize("native_call", ["fork", "socket"])
def test_seccomp_blocks_native_process_and_network_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, native_call: str
):
    if native_call == "fork":
        syscall = """
        result = libc.fork()
        if result == 0:
            os._exit(99)
        if result > 0:
            os.waitpid(result, 0)
        """
    else:
        syscall = """
        result = libc.socket(2, 1, 0)
        if result >= 0:
            os.close(result)
        """
    source = f"""
import ctypes
import errno
import os

class Strategy:
    def target_weights(self, context, *, seed):
        libc = ctypes.CDLL(None, use_errno=True)
{syscall.rstrip()}
        blocked = result == -1 and ctypes.get_errno() == errno.EPERM
        return {{symbol: 0.01 if blocked else 0.09 for symbol in context.eligible_symbols}}

def build_strategy():
    return Strategy()
""".lstrip()
    entrypoint, _, _ = _write_layout(tmp_path, strategy_source=source)
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times[:1],
        seed=7,
        interval_hours=8,
    )

    assert targets.loc[decision_times[0], "AAAUSDT"] == pytest.approx(0.01)


def test_worker_enforces_resource_limits_and_rejects_oversized_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
import resource

import numpy as np

EXPECTED_MAXIMA = {
    resource.RLIMIT_AS: 4 * 1024**3,
    resource.RLIMIT_CORE: 0,
    resource.RLIMIT_CPU: 900,
    resource.RLIMIT_FSIZE: 1024 * 1024,
    resource.RLIMIT_NOFILE: 128,
    resource.RLIMIT_NPROC: 32,
}

class Strategy:
    def target_weights(self, context, *, seed):
        bounded = all(
            soft == hard and soft <= maximum
            for resource_id, maximum in EXPECTED_MAXIMA.items()
            for soft, hard in (resource.getrlimit(resource_id),)
        )
        try:
            np.empty((5 * 1024**3,), dtype=np.uint8)
        except MemoryError:
            allocation_blocked = True
        else:
            allocation_blocked = False
        safe = bounded and allocation_blocked
        return {symbol: 0.01 if safe else 0.09 for symbol in context.eligible_symbols}

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times[:1],
        seed=7,
        interval_hours=8,
    )

    assert targets.loc[decision_times[0], "AAAUSDT"] == pytest.approx(0.01)


def test_landlock_requirement_fails_closed_on_old_kernel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    bundle = tmp_path / "bundle"
    runtime = tmp_path / "runtime"
    bundle.mkdir()
    runtime.mkdir()
    monkeypatch.setattr(strategy_worker, "_landlock_abi", lambda _libc: 5)

    with pytest.raises(RuntimeError, match=r"Landlock ABI 6\+"):
        strategy_worker._install_landlock(bundle, runtime)


def test_worker_subprocess_attempt_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
import subprocess

class Strategy:
    def target_weights(self, context, *, seed):
        try:
            subprocess.run(["true"], check=True)
            escaped = True
        except Exception:
            escaped = False
        return {symbol: 0.05 if escaped else 0.0 for symbol in context.eligible_symbols}

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    with pytest.raises(runner.StrategySandboxError, match="subprocess execution"):
        runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times,
            seed=7,
            interval_hours=8,
        )


def test_worker_rejects_nonfinite_weights(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
class Strategy:
    def target_weights(self, context, *, seed):
        return {symbol: float("nan") for symbol in context.eligible_symbols}

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    bars, funding, membership, decision_times = _small_market()

    with pytest.raises(runner.StrategyExecutionError, match="non-finite"):
        runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times,
            seed=7,
            interval_hours=8,
        )


def test_worker_timeout_is_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    entrypoint, _, _ = _write_layout(
        tmp_path,
        strategy_source="""
class Strategy:
    def target_weights(self, context, *, seed):
        while True:
            pass

def build_strategy():
    return Strategy()
""".lstrip(),
    )
    _bypass_worker_namespace(monkeypatch)
    monkeypatch.setattr(runner, "_WORKER_RESPONSE_TIMEOUT_SECONDS", 0.1)
    bars, funding, membership, decision_times = _small_market()

    with pytest.raises(runner.StrategySandboxError, match="timed out"):
        runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times,
            seed=7,
            interval_hours=8,
        )


def test_worker_whole_run_wall_deadline_is_cumulative(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(runner, "_WORKER_TOTAL_TIMEOUT_SECONDS", 0.45)
    monkeypatch.setattr(runner, "_WORKER_RESPONSE_TIMEOUT_SECONDS", 2.0)
    diagnostics = tempfile.TemporaryFile(mode="w+b")
    script = """
import json
import sys
import time

for line in sys.stdin:
    message = json.loads(line)
    if message.get("type") == "shutdown":
        print('{"type":"bye"}', flush=True)
        break
    time.sleep(0.17)
    print('{"type":"ok"}', flush=True)
"""
    process = subprocess.Popen(
        [sys.executable, "-u", "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=diagnostics,
        text=True,
        start_new_session=True,
    )
    client = runner._StrategyWorkerClient(process, diagnostics)
    try:
        assert client.request({"type": "work"}) == {"type": "ok"}
        assert client.request({"type": "work"}) == {"type": "ok"}
        with pytest.raises(runner.StrategySandboxError, match="whole-run wall deadline"):
            client.request({"type": "work"})
    finally:
        client.abort()


def test_worker_response_size_is_bounded(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(runner, "_MAX_WORKER_RESPONSE_BYTES", 1_024)
    diagnostics = tempfile.TemporaryFile(mode="w+b")
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os, time; os.write(1, b'x' * 2048); time.sleep(10)",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=diagnostics,
        text=True,
        start_new_session=True,
    )
    client = runner._StrategyWorkerClient(process, diagnostics)
    try:
        with pytest.raises(runner.StrategySandboxError, match="maximum size"):
            client.request({"type": "init"})
    finally:
        client.abort()


def test_unclean_worker_shutdown_prevents_parent_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    snapshot = _snapshot(hashlib.sha256(manifest.read_bytes()).hexdigest())
    decisions = pd.date_range("2020-01-01", periods=2, freq="8h", tz="UTC")
    evaluated = False

    class BadShutdownWorker:
        def initialise(self, _payload):
            return None

        def request(self, payload):
            assert payload["type"] == "decision"
            return {"type": "weights", "weights": {}}

        def abort(self):
            return None

        def finish(self):
            raise runner.StrategySandboxError("unclean worker shutdown")

    class Sandbox:
        def cleanup(self):
            return None

    def forbidden_evaluation(*_args, **_kwargs):
        nonlocal evaluated
        evaluated = True
        raise AssertionError("evaluation ran after an unclean strategy worker")

    monkeypatch.setattr(runner, "_load_verified_snapshot", lambda *_args: snapshot)
    monkeypatch.setattr(runner, "_decision_grid", lambda _config: decisions)
    monkeypatch.setattr(
        runner,
        "_launch_strategy_worker",
        lambda *_args: (BadShutdownWorker(), Sandbox()),
    )
    monkeypatch.setattr(runner, "evaluate_base_and_double_cost", forbidden_evaluation)

    with pytest.raises(runner.StrategySandboxError, match="unclean worker shutdown"):
        _authorized_run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
        )
    assert not evaluated
    assert not (tmp_path / "reports-top40/team-01").exists()


def test_real_namespaced_worker_smoke(tmp_path: Path):
    entrypoint, _, _ = _write_layout(tmp_path)
    bars, funding, membership, decision_times = _small_market()

    targets = runner._generate_targets_in_worker(
        tmp_path,
        "team-01",
        entrypoint,
        bars,
        funding,
        membership,
        decision_times[:2],
        seed=7,
        interval_hours=8,
    )

    assert targets.index.equals(decision_times[:2])
    assert targets[REBALANCE_INSTRUCTION_COLUMN].all()
    assert not targets.drop(columns=REBALANCE_INSTRUCTION_COLUMN).to_numpy().any()


def test_real_namespace_masks_repository_parent_and_stages_runtime(tmp_path: Path):
    repository_parent = runner._runner_repository_parent()
    sibling = Path(
        tempfile.mkdtemp(prefix="worker-sibling-sentinel-", dir=repository_parent / ".worktrees")
    )
    sentinel = sibling / "secret.txt"
    sentinel.write_text("prohibited sibling-worktree value\n", encoding="utf-8")
    source = f"""
import ctypes
import os

import numpy as np
import pandas as pd
import sklearn
from numpy.polynomial import Polynomial
from sklearn.linear_model import LinearRegression

SENTINEL = {str(sentinel)!r}
MASKED_REPOSITORY = {str(repository_parent)!r}

class Strategy:
    def target_weights(self, context, *, seed):
        libc = ctypes.CDLL(None, use_errno=True)
        libc.open.argtypes = [ctypes.c_char_p, ctypes.c_int]
        libc.open.restype = ctypes.c_int
        fd = libc.open(SENTINEL.encode(), os.O_RDONLY)
        exposed = False
        if fd >= 0:
            exposed = bool(os.read(fd, 128))
            os.close(fd)
        frame = pd.DataFrame({{"feature": np.array([0.0, 1.0, 2.0])}})
        model = LinearRegression().fit(frame, np.array([0.0, 1.0, 2.0]))
        runtime_weight = float(Polynomial([0.01])(model.predict(frame.iloc[[0]])[0]))
        runtime_is_external = all(
            not str(module.__file__).startswith(MASKED_REPOSITORY)
            for module in (np, pd, sklearn)
        )
        weight = 0.09 if exposed else (runtime_weight if runtime_is_external else 0.08)
        return {{symbol: weight for symbol in context.eligible_symbols}}

def build_strategy():
    return Strategy()
""".lstrip()
    try:
        entrypoint, _, _ = _write_layout(tmp_path, strategy_source=source)
        bars, funding, membership, decision_times = _small_market()

        targets = runner._generate_targets_in_worker(
            tmp_path,
            "team-01",
            entrypoint,
            bars,
            funding,
            membership,
            decision_times[:2],
            seed=7,
            interval_hours=8,
        )
    finally:
        shutil.rmtree(sibling)

    assert targets.loc[decision_times[0], "AAAUSDT"] == pytest.approx(0.01)
    assert targets.loc[decision_times[0], "BBBUSDT"] == pytest.approx(0.01)
