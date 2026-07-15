from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament.engine_v2 import EvaluationResult
from crypto_trade.tournament.metrics import compute_window_metrics
from crypto_trade.tournament.top40_v2 import (
    PHASE0_FROZEN_FILES,
    EvaluationWindow,
    WindowMetrics,
    load_config,
    new_run_state,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_layout(root: Path) -> tuple[Path, Path, Path]:
    entrypoint = root / "tournament/top40-v2/teams/team-01/strategy.py"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text(
        """
class Strategy:
    def target_weights(self, context, *, seed):
        return {}

def build_strategy():
    return Strategy()
""".lstrip(),
        encoding="utf-8",
    )
    shutil.copyfile(
        _REPOSITORY_ROOT / "tournament/top40-v2/templates/risk-policy.json",
        entrypoint.parent / "risk_policy.json",
    )
    config = root / "tournament/top40-v2/config.toml"
    config.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_REPOSITORY_ROOT / "tournament/top40-v2/config.toml", config)
    manifest = root / "tournament/top40/data_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}\n", encoding="utf-8")
    return entrypoint, config, manifest


def _snapshot(manifest_sha256: str) -> runner_v2._SnapshotData:
    times = pd.DatetimeIndex(
        [
            "2020-01-01T00:00:00Z",
            "2023-06-30T16:00:00Z",
            "2023-07-01T00:00:00Z",
            "2024-06-30T16:00:00Z",
            "2024-07-01T00:00:00Z",
            "2026-06-30T16:00:00Z",
        ]
    )
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": "BTCUSDT",
            "open": np.arange(len(times), dtype=float) + 10_000.0,
            "close": np.arange(len(times), dtype=float) + 10_001.0,
            "quote_volume": 1_000_000.0,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": times,
            "symbol": "BTCUSDT",
            "funding_rate": 0.0001,
            "mark_price": 10_000.0,
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": times,
            "symbol": "BTCUSDT",
            "mark_price": 10_000.0,
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.DatetimeIndex(
                ["2019-12-30T00:00:00Z", "2024-07-01T00:00:00Z"]
            ),
            "symbol": "BTCUSDT",
            "liquidity_rank": 1,
            "trailing_quote_volume": 1_000_000.0,
        }
    )
    return runner_v2._SnapshotData(
        manifest_sha256=manifest_sha256,
        paths={},
        file_hashes={},
        bars=bars,
        funding=funding,
        mark_prices=marks,
        membership=membership,
        contract_metadata=pd.DataFrame(
            {"symbol": ["BTCUSDT"], "contract_type": ["PERPETUAL"]}
        ),
    )


def _result(index: pd.DatetimeIndex) -> EvaluationResult:
    returns = pd.DataFrame({"net_return": np.zeros(len(index))}, index=index)
    positions = pd.DataFrame({"BTCUSDT": np.zeros(len(index))}, index=index)
    return EvaluationResult(returns=returns, positions=positions, events=pd.DataFrame())


@pytest.mark.parametrize(
    ("stage", "cutoff"),
    (("development", "2023-07-01"), ("private", "2024-07-01")),
)
def test_run_team_never_passes_rows_beyond_authorized_cutoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    cutoff: str,
):
    entrypoint, config, manifest = _write_layout(tmp_path)
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    monkeypatch.setattr(
        runner_v2,
        "_load_verified_snapshot",
        lambda _root, _manifest: _snapshot(manifest_sha256),
    )
    monkeypatch.setattr(runner_v2, "_validate_snapshot_bounds", lambda *_args: None)
    observed: list[pd.Timestamp] = []

    def fake_generate(
        _root,
        _team_id,
        _entrypoint,
        bars,
        funding,
        membership,
        decision_times,
        **_kwargs,
    ):
        cutoff_timestamp = pd.Timestamp(cutoff, tz="UTC")
        for frame, column in (
            (bars, "open_time"),
            (funding, "funding_time"),
            (membership, "reconstitution_time"),
        ):
            timestamps = pd.to_datetime(frame[column], utc=True)
            assert (timestamps < cutoff_timestamp).all()
        assert (decision_times < cutoff_timestamp).all()
        observed.append(decision_times.max())
        return pd.DataFrame({"BTCUSDT": 0.0}, index=decision_times)

    def fake_evaluate(
        bars, funding, membership, targets, *, mark_prices, config, risk_policy
    ):
        del config
        assert risk_policy.policy_id == "replace-me"
        cutoff_timestamp = pd.Timestamp(cutoff, tz="UTC")
        for frame, column in (
            (bars, "open_time"),
            (funding, "funding_time"),
            (membership, "reconstitution_time"),
            (mark_prices, "mark_time"),
        ):
            timestamps = pd.to_datetime(frame[column], utc=True)
            assert (timestamps < cutoff_timestamp).all()
        return _result(targets.index), _result(targets.index)

    def fake_metrics(_base, _stressed, _btc, _config, authorized):
        return {
            "scored_window": EvaluationWindow(
                authorized.score_start,
                authorized.score_end_inclusive,
                WindowMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ),
            "double_cost_sharpe": 0.0,
            "regime_sharpe": {name: 0.0 for name in ("bear", "bull", "chop", "stress")},
            "net_sharpe_confidence_interval": (0.0, 0.0),
            "double_cost_sharpe_confidence_interval": (0.0, 0.0),
        }

    monkeypatch.setattr(runner_v2, "_generate_targets_in_worker", fake_generate)
    monkeypatch.setattr(runner_v2, "evaluate_base_and_double_cost", fake_evaluate)
    monkeypatch.setattr(runner_v2, "_btc_daily_returns", lambda *_args: pd.Series(dtype=float))
    monkeypatch.setattr(runner_v2, "_compute_metrics", fake_metrics)
    monkeypatch.setattr(runner_v2, "_publish_artifacts", lambda *_args, **_kwargs: {})

    result = runner_v2.run_team(
        tmp_path,
        "team-01",
        entrypoint.relative_to(tmp_path),
        config.relative_to(tmp_path),
        manifest.relative_to(tmp_path),
        stage=stage,
        _authorization=runner_v2._ORGANIZER_RUN_AUTHORIZATION,
    )

    assert observed == [pd.Timestamp(cutoff, tz="UTC") - pd.Timedelta(hours=8)]
    assert result.stage == stage
    assert result.risk_policy_sha256 == hashlib.sha256(
        (entrypoint.parent / "risk_policy.json").read_bytes()
    ).hexdigest()
    assert result.scored_window.end == (
        "2023-06-30" if stage == "development" else "2024-06-30"
    )
    assert "public_oos" not in result.organizer_fields()
    assert "final_oos" not in result.organizer_fields()


def test_authorized_windows_and_outputs_are_stage_specific():
    config = load_config(_REPOSITORY_ROOT / "tournament/top40-v2/config.toml").raw
    expected = {
        "development": ("2020-02-03", "2023-07-01", "2020-02-03", "2023-06-30"),
        "private": ("2020-02-03", "2024-07-01", "2023-07-01", "2024-06-30"),
        "final_oos": ("2020-02-03", "2026-07-01", "2024-07-01", "2026-06-30"),
    }
    for stage, values in expected.items():
        authorized = runner_v2._authorized_window(config, stage)
        assert (
            authorized.replay_start,
            authorized.end_exclusive,
            authorized.score_start,
            authorized.score_end_inclusive,
        ) == values
        grid = runner_v2._decision_grid(authorized)
        assert grid[0] == pd.Timestamp(values[0], tz="UTC")
        assert grid[-1] == pd.Timestamp(values[1], tz="UTC") - pd.Timedelta(hours=8)

    assert runner_v2._stage_output_relative("team-01", "development") == (
        "reports-top40-v2/team-01/development"
    )
    assert runner_v2._stage_output_relative("team-01", "private") == (
        "tournament/top40-v2/private/artifacts/team-01"
    )
    assert runner_v2._stage_output_relative("team-01", "final_oos") == (
        "reports-top40-v2/team-01/final-oos"
    )


def test_metrics_score_only_the_authorized_private_window():
    loaded = load_config(_REPOSITORY_ROOT / "tournament/top40-v2/config.toml")
    config = dict(loaded.raw)
    config["statistics"] = {**config["statistics"], "bootstrap_samples": 100}
    authorized = runner_v2._authorized_window(config, "private")
    index = pd.date_range(
        authorized.replay_start,
        authorized.score_end_inclusive,
        freq="1D",
        tz="UTC",
    )
    private_start = pd.Timestamp(authorized.score_start, tz="UTC")
    returns = pd.Series(0.01, index=index, name="net_return")
    private_values = np.where(np.arange((index >= private_start).sum()) % 2, -0.0008, 0.001)
    returns.loc[private_start:] = private_values
    stressed = returns.copy()
    stressed.loc[private_start:] -= 0.00005
    btc_index = pd.date_range("2020-01-02", authorized.score_end_inclusive, freq="1D", tz="UTC")
    btc = pd.Series(
        0.01 * np.sin(np.arange(len(btc_index), dtype=float) / 11.0),
        index=btc_index,
        name="btc_return",
    )

    result = runner_v2._compute_metrics(returns, stressed, btc, config, authorized)
    expected = compute_window_metrics(returns.loc[private_start:])

    assert result["scored_window"].start == "2023-07-01"
    assert result["scored_window"].end == "2024-06-30"
    assert result["scored_window"].metrics.net_sharpe == pytest.approx(expected.net_sharpe)
    assert result["scored_window"].metrics.annualized_return == pytest.approx(
        expected.annualized_return
    )
    assert set(result["regime_sharpe"]) == {"bear", "bull", "chop", "stress"}


def test_risk_policy_reason_codes_survive_canonical_artifacts():
    events = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2024-01-01", tz="UTC")],
            "symbol": ["BTCUSDT"],
            "event_type": ["risk_policy_action"],
            "phase": ["before_rebalance"],
            "quantity": [-0.1],
            "price": [40_000.0],
            "notional": [-4_000.0],
            "fee": [2.0],
            "slippage": [1.0],
            "reason": ["position_stop"],
            "policy_id": ["team-01-base"],
        }
    )

    canonical = runner_v2._canonical_events(events)
    trades = runner_v2._trade_events(canonical)

    assert canonical.loc[0, "reason"] == "position_stop"
    assert canonical.loc[0, "policy_id"] == "team-01-base"
    assert trades["event_type"].tolist() == ["risk_policy_action"]


def test_runner_rejects_unknown_stage_before_loading_data(tmp_path: Path):
    entrypoint, config, manifest = _write_layout(tmp_path)
    with pytest.raises(ValueError, match="development, private, or final_oos"):
        runner_v2.run_team(
            tmp_path,
            "team-01",
            entrypoint.relative_to(tmp_path),
            config.relative_to(tmp_path),
            manifest.relative_to(tmp_path),
            stage="canonical_full",
            _authorization=runner_v2._ORGANIZER_RUN_AUTHORIZATION,
        )


def test_phase0_fast_path_requires_committed_exact_frozen_bytes(tmp_path: Path):
    for relative in PHASE0_FROZEN_FILES:
        source = _REPOSITORY_ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {}
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(manifest_text, encoding="utf-8")

    config = load_config(tmp_path / "tournament/top40-v2/config.toml")
    state = new_run_state(config, created_at_utc="2026-07-15T12:00:00+00:00")
    state_path = tmp_path / "tournament/top40-v2/run_state.json"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Top40 V2 Test")
    _git(tmp_path, "checkout", "-qb", "quant-portfolio-blind-top40-v2")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "common V2 inputs")
    common_commit = _git(tmp_path, "rev-parse", "HEAD")

    freeze = {
        "schema_version": 2,
        "frozen_at_utc": "2026-07-15T12:01:00+00:00",
        "branch": "quant-portfolio-blind-top40-v2",
        "common_freeze_commit": common_commit,
        "config_sha256": config.sha256,
        "shared_snapshot_manifest_path": "tournament/top40/data_manifest.json",
        "shared_snapshot_manifest_sha256": hashlib.sha256(
            manifest_text.encode("utf-8")
        ).hexdigest(),
        "frozen_files": {
            relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
            for relative in PHASE0_FROZEN_FILES
        },
    }
    freeze_path = tmp_path / "tournament/top40-v2/phase0_freeze.json"
    freeze_path.write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    state["phase"] = "research"
    state["phase0"] = {
        "path": "tournament/top40-v2/phase0_freeze.json",
        "sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
    }
    state["research_journal"] = {
        "path": "tournament/top40-v2/organizer_research_journal.jsonl",
        "genesis_sha256": "0" * 64,
        "head_sha256": "0" * 64,
        "record_count": 1,
    }
    for team in state["teams"].values():
        team["status"] = "researching"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _git(tmp_path, "add", "tournament/top40-v2/phase0_freeze.json")
    _git(tmp_path, "add", "tournament/top40-v2/run_state.json")
    _git(tmp_path, "commit", "-qm", "first-add V2 Phase 0")

    assert runner_v2._v2_phase0_allows_fast_snapshot_verification(
        tmp_path,
        manifest_path,
        manifest,
        manifest_text,
    )

    frozen_runner = tmp_path / "src/crypto_trade/tournament/runner_v2.py"
    frozen_runner.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen file changed"):
        runner_v2._v2_phase0_allows_fast_snapshot_verification(
            tmp_path,
            manifest_path,
            manifest,
            manifest_text,
        )
