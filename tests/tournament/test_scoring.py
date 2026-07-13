from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.data import sha256_manifest
from crypto_trade.tournament.metrics import (
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.top40 import (
    EVALUATOR_SOURCE_PATHS,
    HARD_COMPLIANCE_CHECKS,
    IS_START,
    METHODOLOGY_PATHS,
    ORCHESTRATOR_SCRIPT_PATH,
    TOURNAMENT_BRANCH,
    ValidationIssue,
    _read_targets_artifact,
    _sharpe_retention,
    _timestamp_target_structure,
    _validate_run_state_phase,
    canonical_artifact_paths,
    score_tournament,
    submission_from_dict,
    validate_submission,
    verify_canonical_artifacts,
    verify_phase0_freeze,
    verify_team_freeze,
)


def _raw(team_id: str, sharpe: float = 1.0) -> dict:
    metrics = {
        "net_sharpe": sharpe,
        "net_sortino": sharpe * 1.2,
        "calmar": sharpe,
        "annualized_return": 0.15 * sharpe,
        "max_drawdown": 0.15,
        "positive_quarter_fraction": 0.75,
    }
    return {
        "team_id": team_id,
        "strategy_name": f"strategy-{team_id}",
        "freeze_commit": "abcdef1",
        "data_manifest_sha256": "a" * 64,
        "evaluator_sha256": "b" * 64,
        "config_sha256": "c" * 64,
        "strategy_sha256": "d" * 64,
        "dependency_lock_sha256": "e" * 64,
        "artifact_manifest_sha256": "f" * 64,
        "entrypoint": f"tournament/top40/teams/{team_id}/strategy.py",
        "seeds": [42],
        "trial_count": 4,
        "in_sample": {"start": IS_START, "end": "2024-06-30", "metrics": metrics},
        "public_oos": {
            "start": "2024-07-01",
            "end": "2026-06-30",
            "metrics": copy.deepcopy(metrics),
        },
        "double_cost_oos_sharpe": sharpe - 0.2,
        "regime_sharpe": {
            "bull": sharpe,
            "bear": sharpe - 0.1,
            "chop": sharpe - 0.2,
            "stress": sharpe - 0.15,
        },
        "confidence_intervals": {
            "is_net_sharpe_95": [sharpe - 0.2, sharpe + 0.2],
            "public_oos_net_sharpe_95": [sharpe - 0.2, sharpe + 0.2],
            "double_cost_oos_net_sharpe_95": [sharpe - 0.4, sharpe],
        },
        "compliance": {check: True for check in HARD_COMPLIANCE_CHECKS},
        "artifacts": canonical_artifact_paths(team_id),
    }


def test_config_has_exactly_ten_unique_teams_and_fixed_weights():
    config_path = Path(__file__).parents[2] / "tournament" / "top40" / "config.toml"
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    assert config["teams"] == [f"team-{number:02d}" for number in range(1, 11)]
    assert len(set(config["teams"])) == 10
    assert config["scoring"] == {
        "automatic_weight": 70.0,
        "critic_weight": 15.0,
        "user_weight": 15.0,
        "winner_required_when_any_submission_is_valid": True,
        "performance_can_be_disqualified": False,
    }


def test_valid_submission_has_no_issues():
    submission = submission_from_dict(_raw("team-01"))
    assert validate_submission(submission) == ()


def test_string_compliance_boolean_is_rejected_instead_of_truthy_cast():
    raw = _raw("team-01")
    raw["compliance"]["public_binance_only"] = "false"
    with pytest.raises(ValueError, match="JSON booleans"):
        submission_from_dict(raw)


def test_team_artifact_cannot_point_into_another_team_namespace():
    raw = _raw("team-01")
    raw["artifacts"]["daily_returns"] = "reports-top40/team-02/daily.csv"
    issues = validate_submission(submission_from_dict(raw))
    assert any(issue.code == "artifacts.daily_returns" for issue in issues)


def test_team_artifact_cannot_traverse_into_another_namespace():
    raw = _raw("team-01")
    raw["artifacts"]["daily_returns"] = "reports-top40/team-01/../team-02/daily.csv"
    issues = validate_submission(submission_from_dict(raw))
    assert any(issue.code == "artifacts.daily_returns" for issue in issues)


def test_missing_or_traversing_artifact_manifest_is_reported_without_key_error(tmp_path):
    missing = _raw("team-01")
    missing["artifacts"].pop("artifact_manifest")
    submission = submission_from_dict(missing)
    assert any(issue.code == "artifacts" for issue in validate_submission(submission))
    assert any(
        issue.code == "artifacts" for issue in verify_canonical_artifacts(submission, root=tmp_path)
    )

    traversal = _raw("team-01")
    traversal["artifacts"]["artifact_manifest"] = "../artifact_manifest.json"
    submission = submission_from_dict(traversal)
    assert any(
        issue.code == "artifacts.artifact_manifest" for issue in validate_submission(submission)
    )
    assert any(
        issue.code == "artifact_manifest"
        for issue in verify_canonical_artifacts(submission, root=tmp_path)
    )


def test_non_string_artifact_manifest_is_rejected_during_parsing():
    raw = _raw("team-01")
    raw["artifacts"]["artifact_manifest"] = {"path": "manifest.json"}
    with pytest.raises(ValueError, match="artifacts must map string"):
        submission_from_dict(raw)


def test_integrity_failure_disqualifies_but_low_performance_does_not():
    low = submission_from_dict(_raw("team-01", sharpe=-2.0))
    broken_raw = _raw("team-02")
    broken_raw["compliance"]["funding_cashflows_charged"] = False
    broken = submission_from_dict(broken_raw)
    scores = score_tournament([low, broken])
    assert scores[0].team_id == "team-01"
    assert scores[0].valid and scores[0].rank == 1
    assert not scores[1].valid
    assert "funding_cashflows_charged" in " ".join(scores[1].disqualification_reasons)


def test_scores_blend_objective_critic_and_user_and_rank_every_valid_team():
    weaker = submission_from_dict(_raw("team-01", sharpe=0.8))
    stronger = submission_from_dict(_raw("team-02", sharpe=1.5))
    scores = score_tournament(
        [weaker, stronger],
        critic_scores={"team-01": 15, "team-02": 14},
        user_scores={"team-01": 10, "team-02": 15},
    )
    assert [score.rank for score in scores] == [1, 2]
    assert scores[0].team_id == "team-02"
    assert scores[0].automatic_score > scores[1].automatic_score
    assert scores[0].total_score <= 100


def test_critic_dq_preserves_precritic_objective_scores_and_ranks():
    submissions = [
        submission_from_dict(_raw("team-01", sharpe=0.8)),
        submission_from_dict(_raw("team-02", sharpe=1.1)),
        submission_from_dict(_raw("team-03", sharpe=1.5)),
    ]
    baseline = {score.team_id: score for score in score_tournament(submissions)}
    finding = ValidationIssue("critic_future_data", "proven timestamp leakage")

    adjudicated = {
        score.team_id: score
        for score in score_tournament(
            submissions,
            critic_scores={team: 10.0 for team in baseline},
            user_scores={team: 10.0 for team in baseline},
            critic_issues={"team-02": (finding,)},
        )
    }

    for team_id in baseline:
        assert adjudicated[team_id].automatic_score == baseline[team_id].automatic_score
        assert adjudicated[team_id].objective_rank == baseline[team_id].objective_rank
    disqualified = adjudicated["team-02"]
    assert not disqualified.valid
    assert disqualified.rank is None
    assert disqualified.automatic_score is not None
    assert disqualified.objective_rank is not None
    assert disqualified.total_score is None
    assert disqualified.disqualification_reasons == ("proven timestamp leakage",)


def test_cost_sharpe_retention_is_scale_free_and_handles_negative_bases():
    assert _sharpe_retention(2.0, 1.0) == pytest.approx(0.5)
    assert _sharpe_retention(1.0, 0.5) == pytest.approx(0.5)
    assert _sharpe_retention(-1.0, -0.8) > _sharpe_retention(-1.0, -1.2)


def test_run_state_accepts_only_forward_phase_consistent_lifecycle():
    teams = {
        f"team-{number:02d}": {"champion": None, "canonical_run": "pending"}
        for number in range(1, 11)
    }
    assert _validate_run_state_phase({"phase": "research", "teams": teams}) == []
    for team in teams.values():
        team["champion"] = {"freeze_commit": "a" * 40}
    assert _validate_run_state_phase({"phase": "research", "teams": teams})
    assert _validate_run_state_phase({"phase": "cohort_frozen", "teams": teams}) == []
    for team in teams.values():
        team["canonical_run"] = "complete"
    assert _validate_run_state_phase({"phase": "cohort_frozen", "teams": teams})
    objective_lock = {
        "path": "tournament/top40/objective_lock.json",
        "sha256": "0" * 64,
        "cohort_sha256": "b" * 64,
        "locked_at_utc": "2026-07-13T11:00:00+00:00",
    }
    assert (
        _validate_run_state_phase(
            {"phase": "objective_locked", "teams": teams, "objective_lock": objective_lock}
        )
        == []
    )
    assert _validate_run_state_phase({"phase": "critic_locked", "teams": teams})
    critic_lock = {
        "path": "tournament/top40/critic_lock.json",
        "sha256": "a" * 64,
        "cohort_sha256": "b" * 64,
        "locked_at_utc": "2026-07-13T12:00:00+00:00",
    }
    assert (
        _validate_run_state_phase(
            {
                "phase": "critic_locked",
                "teams": teams,
                "objective_lock": objective_lock,
                "critic_lock": critic_lock,
            }
        )
        == []
    )
    assert _validate_run_state_phase(
        {"phase": "paper_frozen", "teams": teams, "critic_lock": critic_lock}
    )
    winner_freeze = {
        "path": "tournament/top40/winner_freeze.json",
        "sha256": "c" * 64,
        "winner_team_id": "team-01",
        "winner_freeze_commit": "d" * 40,
        "selection_record_commit": "e" * 40,
        "frozen_at_utc": "2026-07-13T12:01:00+00:00",
        "forward_paper_start_utc": "2026-07-13T16:00:00+00:00",
    }
    confirmation_lock = {
        "path": "tournament/top40/critic_confirmation_lock.json",
        "sha256": "1" * 64,
        "cohort_sha256": "b" * 64,
        "locked_at_utc": "2026-07-13T12:10:00+00:00",
    }
    user_lock = {
        "path": "tournament/top40/user_ballot_lock.json",
        "sha256": "2" * 64,
        "locked_at_utc": "2026-07-13T12:20:00+00:00",
    }
    assert (
        _validate_run_state_phase(
            {
                "phase": "paper_frozen",
                "teams": teams,
                "objective_lock": objective_lock,
                "critic_lock": critic_lock,
                "critic_confirmation_lock": confirmation_lock,
                "user_ballot_lock": user_lock,
                "winner_freeze": winner_freeze,
            }
        )
        == []
    )


def test_mechanically_strong_result_is_paper_eligible_without_critic_veto():
    submission = submission_from_dict(_raw("team-01", sharpe=1.4))
    score = score_tournament([submission], critic_scores={"team-01": 0})[0]
    assert score.valid and score.rank == 1
    assert score.paper_eligible


def test_target_artifact_requires_boolean_rebalance_instructions(tmp_path: Path):
    relative = "reports-top40/team-01/targets.parquet"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    pd.DataFrame(
        {
            "timestamp": [pd.Timestamp(IS_START, tz="UTC")],
            REBALANCE_INSTRUCTION_COLUMN: [1],
            "BTCUSDT": [0.0],
        }
    ).to_parquet(path, index=False)

    with pytest.raises(ValueError, match="instructions must be Boolean"):
        _read_targets_artifact(relative, root=tmp_path)


def test_timestamp_keyed_target_tables_are_rejected_as_prefit_state():
    assert _timestamp_target_structure({"2025-01-01T00:00:00Z": {"BTCUSDT": 0.1, "ETHUSDT": -0.1}})
    assert _timestamp_target_structure(
        {"timestamp": "2025-01-01T00:00:00Z", "target_weights": {"BTCUSDT": 0.1}}
    )
    assert not _timestamp_target_structure({"lookback": 30, "gross_target": 0.8})
    assert not _timestamp_target_structure(
        {
            "timestamp_utc": "2025-01-01T00:00:00Z",
            "disposition": "IS-falsified",
        }
    )


def test_canonical_artifacts_are_hashed_and_scalar_metrics_are_recomputed(tmp_path):
    raw = _raw("team-01")
    dates = pd.date_range(IS_START, "2026-06-30", freq="D", tz="UTC")
    base = pd.Series(0.0003 + np.sin(np.arange(len(dates))) * 0.002, index=dates)
    stressed = base - 0.00005
    btc = pd.Series(0.0002 + np.sin(np.arange(len(dates)) / 10) * 0.01, index=dates)
    raw["in_sample"]["metrics"] = dataclasses.asdict(
        compute_window_metrics(base.loc[IS_START:"2024-06-30"])
    )
    raw["public_oos"]["metrics"] = dataclasses.asdict(
        compute_window_metrics(base.loc["2024-07-01":"2026-06-30"])
    )
    raw["double_cost_oos_sharpe"] = compute_window_metrics(
        stressed.loc["2024-07-01":"2026-06-30"]
    ).net_sharpe
    labels = classify_btc_regimes(btc).loc["2024-07-01":"2026-06-30"]
    raw["regime_sharpe"] = dict(compute_regime_sharpes(base.loc["2024-07-01":"2026-06-30"], labels))
    raw["confidence_intervals"] = {
        "is_net_sharpe_95": list(sharpe_confidence_interval(base.loc[IS_START:"2024-06-30"])),
        "public_oos_net_sharpe_95": list(
            sharpe_confidence_interval(base.loc["2024-07-01":"2026-06-30"])
        ),
        "double_cost_oos_net_sharpe_95": list(
            sharpe_confidence_interval(stressed.loc["2024-07-01":"2026-06-30"])
        ),
    }

    config_path = tmp_path / "tournament/top40/config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("schema_version = 1\n", encoding="utf-8")
    evaluator_paths = []
    for relative in EVALUATOR_SOURCE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"canonical evaluator {relative}\n", encoding="utf-8")
        evaluator_paths.append(path)

    artifact_files = []
    for name, relative in raw["artifacts"].items():
        if name in {"artifact_manifest", "reproduce_command"}:
            continue
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "daily_returns":
            pd.DataFrame({"date": dates, "net_return": base.to_numpy()}).to_csv(path, index=False)
        elif name == "double_cost_daily_returns":
            pd.DataFrame({"date": dates, "net_return": stressed.to_numpy()}).to_csv(
                path, index=False
            )
        elif name == "btc_daily_returns":
            pd.DataFrame({"date": dates, "btc_return": btc.to_numpy()}).to_csv(path, index=False)
        elif name == "evaluator_returns":
            timestamps = pd.date_range(dates.min(), dates.max() + pd.Timedelta(hours=16), freq="8h")
            bar_returns = np.zeros(len(timestamps))
            bar_returns[::3] = base.to_numpy()
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "net_return": bar_returns,
                    "price_pnl": bar_returns,
                    "long_price_pnl": bar_returns / 2,
                    "short_price_pnl": bar_returns / 2,
                    "funding_pnl": 0.0,
                    "long_funding_pnl": 0.0,
                    "short_funding_pnl": 0.0,
                    "long_exposure": 0.05,
                    "short_exposure": 0.05,
                    "fees": 0.0,
                    "slippage": 0.0,
                }
            ).to_csv(path, index=False)
        elif name == "double_cost_evaluator_returns":
            timestamps = pd.date_range(dates.min(), dates.max() + pd.Timedelta(hours=16), freq="8h")
            bar_returns = np.zeros(len(timestamps))
            bar_returns[::3] = stressed.to_numpy()
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "net_return": bar_returns,
                    "price_pnl": bar_returns,
                    "funding_pnl": 0.0,
                    "fees": 0.0,
                    "slippage": 0.0,
                }
            ).to_csv(path, index=False)
        elif name == "targets":
            timestamps = pd.date_range(dates.min(), dates.max() + pd.Timedelta(hours=16), freq="8h")
            target = np.where(np.arange(len(timestamps)) % 2 == 0, 0.05, -0.05)
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    REBALANCE_INSTRUCTION_COLUMN: np.arange(len(timestamps)) % 3 != 1,
                    "BTCUSDT": target,
                    "ETHUSDT": -target,
                }
            ).to_parquet(path, index=False)
        elif name == "trades":
            trade_times = pd.date_range(dates.min(), dates.max(), freq="30D")
            notionals = np.where(np.arange(len(trade_times)) % 2 == 0, 2_000.0, -2_000.0)
            pd.DataFrame(
                {
                    "timestamp": trade_times,
                    "event_type": "trade",
                    "notional": notionals,
                }
            ).to_csv(path, index=False)
        else:
            path.write_text(f"canonical {name}\n", encoding="utf-8")
        artifact_files.append(path)
    raw["strategy_sha256"] = hashlib.sha256((tmp_path / raw["entrypoint"]).read_bytes()).hexdigest()
    raw["dependency_lock_sha256"] = hashlib.sha256(
        (tmp_path / raw["artifacts"]["dependency_lock"]).read_bytes()
    ).hexdigest()
    raw["config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    raw["data_manifest_sha256"] = hashlib.sha256(
        (tmp_path / raw["artifacts"]["data_manifest"]).read_bytes()
    ).hexdigest()
    raw["evaluator_sha256"] = sha256_manifest(evaluator_paths, root=tmp_path)[0]
    digest, entries = sha256_manifest(artifact_files, root=tmp_path)
    raw["artifact_manifest_sha256"] = digest
    manifest_path = tmp_path / raw["artifacts"]["artifact_manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(entries), encoding="utf-8")

    submission = submission_from_dict(raw)
    assert verify_canonical_artifacts(submission, root=tmp_path) == ()

    tampered = copy.deepcopy(raw)
    tampered["public_oos"]["metrics"]["net_sharpe"] += 1.0
    issues = verify_canonical_artifacts(submission_from_dict(tampered), root=tmp_path)
    assert any(issue.code == "public_oos.net_sharpe" for issue in issues)

    bar_path = tmp_path / raw["artifacts"]["evaluator_returns"]
    attributed = pd.read_csv(bar_path)
    attributed["short_exposure"] = 1e-12
    attributed.to_csv(bar_path, index=False)
    digest, entries = sha256_manifest(artifact_files, root=tmp_path)
    immaterial_side = copy.deepcopy(raw)
    immaterial_side["artifact_manifest_sha256"] = digest
    manifest_path.write_text(json.dumps(entries), encoding="utf-8")
    issues = verify_canonical_artifacts(submission_from_dict(immaterial_side), root=tmp_path)
    assert any(
        issue.code == "long_and_short_enabled" and "short realized exposure" in issue.message
        for issue in issues
    )
    attributed["short_exposure"] = 0.05
    attributed.to_csv(bar_path, index=False)

    target_path = tmp_path / raw["artifacts"]["targets"]
    one_sided = pd.read_parquet(target_path)
    symbol_columns = one_sided.columns.difference(["timestamp", REBALANCE_INSTRUCTION_COLUMN])
    # True instruction flags are positive numerically, but are metadata and cannot satisfy the
    # long-side compliance check when every actual symbol target is short.
    one_sided.loc[:, symbol_columns] = -one_sided.loc[:, symbol_columns].abs()
    one_sided.to_parquet(target_path, index=False)
    digest, entries = sha256_manifest(artifact_files, root=tmp_path)
    one_sided_raw = copy.deepcopy(raw)
    one_sided_raw["artifact_manifest_sha256"] = digest
    manifest_path.write_text(json.dumps(entries), encoding="utf-8")
    issues = verify_canonical_artifacts(submission_from_dict(one_sided_raw), root=tmp_path)
    assert any(issue.code == "long_and_short_enabled" for issue in issues)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_canonical_manifest_fast_verifier_hashes_every_frozen_file(tmp_path: Path):
    import crypto_trade.tournament.top40 as top40

    canonical = _write(tmp_path, "data/top40/snapshot-v1/bars.parquet", "frozen bytes")
    manifest_path = _write(
        tmp_path,
        "tournament/top40/data_manifest.json",
        json.dumps(
            {
                "files": [
                    {
                        "name": "bars",
                        "path": "data/top40/snapshot-v1/bars.parquet",
                        "sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
                        "size": canonical.stat().st_size,
                    }
                ]
            },
            sort_keys=True,
        )
        + "\n",
    )

    parsed = top40._verify_canonical_manifest_files(manifest_path, tmp_path)
    assert parsed["files"][0]["name"] == "bars"
    canonical.write_text("mutated bytes", encoding="utf-8")
    with pytest.raises(ValueError, match="size differs|SHA-256 differs"):
        top40._verify_canonical_manifest_files(manifest_path, tmp_path)


def test_phase0_verifier_pins_common_bytes_and_frozen_git_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import crypto_trade.tournament.top40 as top40

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Top40 Test")
    _git(tmp_path, "checkout", "-qb", TOURNAMENT_BRANCH)
    manifest_path = _write(tmp_path, "tournament/top40/data_manifest.json", "{}\n")
    config_path = _write(tmp_path, "tournament/top40/config.toml", "schema_version = 1\n")
    policy_path = _write(tmp_path, "tournament/top40/PHASE0-POLICY.md", "policy\n")
    root_lock = _write(tmp_path, "uv.lock", "frozen dependencies\n")
    orchestrator = _write(tmp_path, ORCHESTRATOR_SCRIPT_PATH, "# frozen CLI\n")
    builder = _write(
        tmp_path,
        "src/crypto_trade/tournament/snapshot.py",
        "# frozen builder\n",
    )
    evaluator_paths = [
        _write(tmp_path, relative, f"# frozen {relative}\n") for relative in EVALUATOR_SOURCE_PATHS
    ]
    methodology_paths = [
        _write(tmp_path, relative, f"frozen methodology {relative}\n")
        for relative in METHODOLOGY_PATHS
    ]
    btc_returns = _write(
        tmp_path, "reports-top40/common/btc_daily_returns.csv", "date,btc_return\n"
    )
    btc_regimes = _write(tmp_path, "reports-top40/common/btc_regimes.csv", "date,regime\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "common freeze")
    common_commit = _git(tmp_path, "rev-parse", "HEAD")
    evaluator_sha = sha256_manifest(evaluator_paths, root=tmp_path)[0]
    manifest = {
        "files": [
            {
                "name": "btc_daily_returns",
                "path": "reports-top40/common/btc_daily_returns.csv",
                "sha256": hashlib.sha256(btc_returns.read_bytes()).hexdigest(),
            },
            {
                "name": "btc_regimes",
                "path": "reports-top40/common/btc_regimes.csv",
                "sha256": hashlib.sha256(btc_regimes.read_bytes()).hexdigest(),
            },
        ],
        "sources": {
            "builder_path": "src/crypto_trade/tournament/snapshot.py",
            "builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        },
    }
    monkeypatch.setattr(
        top40,
        "_verify_canonical_manifest_files",
        lambda _path, _root: manifest,
    )
    freeze = {
        "frozen_at_utc": "2026-07-13T00:00:00+00:00",
        "branch": TOURNAMENT_BRANCH,
        "common_freeze_commit": common_commit,
        "data_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "evaluator_sha256": evaluator_sha,
        "methodology_sha256": sha256_manifest(methodology_paths, root=tmp_path)[0],
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "btc_daily_returns_sha256": hashlib.sha256(btc_returns.read_bytes()).hexdigest(),
        "btc_regimes_sha256": hashlib.sha256(btc_regimes.read_bytes()).hexdigest(),
        "phase0_policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "snapshot_builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        "root_dependency_lock_sha256": hashlib.sha256(root_lock.read_bytes()).hexdigest(),
        "orchestrator_sha256": hashlib.sha256(orchestrator.read_bytes()).hexdigest(),
    }
    _write(
        tmp_path,
        "tournament/top40/phase0_freeze.json",
        json.dumps(freeze) + "\n",
    )
    _write(
        tmp_path,
        "tournament/top40/run_state.json",
        json.dumps(
            {
                "phase": "research",
                "teams": {
                    f"team-{number:02d}": {
                        "champion": None,
                        "canonical_run": "pending",
                    }
                    for number in range(1, 11)
                },
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
        )
        + "\n",
    )
    _git(tmp_path, "add", "tournament/top40/phase0_freeze.json")
    _git(tmp_path, "add", "tournament/top40/run_state.json")
    _git(tmp_path, "commit", "-qm", "Phase-0 record")

    assert verify_phase0_freeze(root=tmp_path) == ()
    config_path.write_text("schema_version = 2\n", encoding="utf-8")
    issues = verify_phase0_freeze(root=tmp_path)
    assert any(issue.code == "config_sha256" for issue in issues)
    assert any(issue.code == "common_freeze_commit" for issue in issues)

    config_path.write_text("schema_version = 1\n", encoding="utf-8")
    orchestrator.write_text("# mutated CLI\n", encoding="utf-8")
    issues = verify_phase0_freeze(root=tmp_path)
    assert any(issue.code == "orchestrator_sha256" for issue in issues)
    assert any(
        issue.code == "common_freeze_commit" and ORCHESTRATOR_SCRIPT_PATH in issue.message
        for issue in issues
    )


def test_team_freeze_covers_helpers_audit_inputs_and_frozen_root_lock(tmp_path: Path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Top40 Test")
    _write(tmp_path, "uv.lock", "frozen dependencies\n")
    _git(tmp_path, "add", "uv.lock")
    _git(tmp_path, "commit", "-qm", "common")
    common_commit = _git(tmp_path, "rev-parse", "HEAD")
    _write(
        tmp_path,
        "tournament/top40/phase0_freeze.json",
        json.dumps({"common_freeze_commit": common_commit}) + "\n",
    )
    _git(tmp_path, "add", "tournament/top40/phase0_freeze.json")
    _git(tmp_path, "commit", "-qm", "Phase-0 record")
    artifacts = canonical_artifact_paths("team-01")
    for name in (
        "strategy_source",
        "audit_report",
        "research_brief",
        "provenance",
        "feature_lineage",
        "ablations",
        "frozen_config",
        "trial_ledger",
        "compliance_evidence",
    ):
        suffix = Path(artifacts[name]).suffix
        content = "{}\n" if suffix in {".json", ".jsonl"} else f"frozen {name}\n"
        _write(tmp_path, artifacts[name], content)
    _write(tmp_path, artifacts["dependency_lock"], "frozen dependencies\n")
    helper = _write(
        tmp_path,
        "tournament/top40/teams/team-01/helper.py",
        "VALUE = 1\n",
    )
    team_root = tmp_path / "tournament/top40/teams/team-01"
    source_manifest = tmp_path / artifacts["team_source_manifest"]
    entries = []
    for path in sorted(team_root.rglob("*"), key=lambda item: item.as_posix()):
        if path == source_manifest or not path.is_file():
            continue
        entries.append(
            {
                "path": path.relative_to(tmp_path).as_posix(),
                "git_mode": "100644",
                "git_blob_oid": _git(tmp_path, "hash-object", str(path)),
                "size": len(path.read_bytes()),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    _write(
        tmp_path,
        artifacts["team_source_manifest"],
        json.dumps(
            {
                "schema_version": 1,
                "team_id": "team-01",
                "prefit_state_policy": "source-text-config-only-no-timestamp-target-lookups",
                "entries": entries,
            }
        )
        + "\n",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "team freeze")
    team_commit = _git(tmp_path, "rev-parse", "HEAD")

    assert (
        verify_team_freeze(
            "team-01",
            team_commit,
            artifacts["strategy_source"],
            artifacts,
            root=tmp_path,
        )
        == ()
    )
    helper.write_text("VALUE = 2\n", encoding="utf-8")
    issues = verify_team_freeze(
        "team-01",
        team_commit,
        artifacts["strategy_source"],
        artifacts,
        root=tmp_path,
    )
    assert any(issue.code == "freeze_commit" and "helper.py" in issue.message for issue in issues)

    helper.write_text("VALUE = 1\n", encoding="utf-8")
    opaque = tmp_path / "tournament/top40/teams/team-01/model.pkl"
    opaque.write_bytes(b"opaque fitted state")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "forbidden opaque model")
    opaque_commit = _git(tmp_path, "rev-parse", "HEAD")
    issues = verify_team_freeze(
        "team-01",
        opaque_commit,
        artifacts["strategy_source"],
        artifacts,
        root=tmp_path,
    )
    assert any("opaque/prefit file type is forbidden" in issue.message for issue in issues)
