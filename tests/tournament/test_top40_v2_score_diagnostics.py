"""Focused deterministic tests for amendment-0001 score diagnostics."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament.amendment_integrity_v2 import (
    PRIVATE_ARTIFACT_GIT_PATH,
    git_path,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.research_v2 import build_trial_registration
from crypto_trade.tournament.score_diagnostics_v2 import (
    FAMILY_ID,
    REQUIRED_PRIVATE_ARTIFACT_NAMES,
    ScoreDiagnosticRequest,
    _average_ranks,
    _label_score_panel,
    _publish_private_artifacts,
    _spearman,
    _targets_exact,
    materialized_historical_source,
    run_reserved_score_diagnostic,
    trusted_boolean_verdict,
)
from crypto_trade.tournament.top40_v2 import LoadedV2Config

_SHA = "0" * 64


def test_average_tie_ranks_and_spearman_are_frozen() -> None:
    assert _average_ranks([3.0, 1.0, 1.0, 2.0]).tolist() == [4.0, 1.5, 1.5, 3.0]
    assert _spearman([1.0, 1.0, 2.0], [1.0, 2.0, 3.0]) == pytest.approx(
        np.sqrt(3.0) / 2.0
    )
    assert _spearman([1.0, 1.0], [2.0, 3.0]) is None
    assert _spearman([1.0], [2.0]) is None


def test_label_is_open_to_next_daily_open_and_purges_fold_boundary() -> None:
    included = pd.Timestamp("2020-08-30T00:00:00Z")
    purged = pd.Timestamp("2020-08-31T00:00:00Z")
    symbols = ("AUSDT", "BUSDT", "CUSDT")
    scores = pd.DataFrame(
        [
            {"decision_time": timestamp, "symbol": symbol, "score": score}
            for timestamp in (included, purged)
            for symbol, score in zip(symbols, (-1.0, 0.0, 1.0), strict=True)
        ]
    )
    opens = {
        "AUSDT": (100.0, 90.0),
        "BUSDT": (100.0, 100.0),
        "CUSDT": (100.0, 110.0),
    }
    rows: list[dict[str, object]] = []
    for timestamp in (included, included + pd.Timedelta(days=1), purged + pd.Timedelta(days=1)):
        for symbol in symbols:
            if timestamp == included:
                value = opens[symbol][0]
            elif timestamp == included + pd.Timedelta(days=1):
                value = opens[symbol][1]
            else:
                value = 100.0
            rows.append({"open_time": timestamp, "symbol": symbol, "open": value})
    panel, statistics = _label_score_panel(scores, pd.DataFrame(rows))

    assert set(panel["decision_time"]) == {included}
    assert panel.set_index("symbol")["forward_return"].to_dict() == pytest.approx(
        {"AUSDT": -0.1, "BUSDT": 0.0, "CUSDT": 0.1}
    )
    assert statistics["pooled_next_day_score_ic"] == pytest.approx(1.0)
    assert statistics["fold_score_ic"]["F1"] == pytest.approx(1.0)
    assert all(statistics["fold_score_ic"][fold] is None for fold in ("F2", "F3", "F4", "F5", "F6"))
    assert statistics["fold_daily_ic_counts"] == {
        "F1": 1,
        "F2": 0,
        "F3": 0,
        "F4": 0,
        "F5": 0,
        "F6": 0,
    }
    assert statistics["purged_fold_boundary_decision_count"] == 1


def _target_frame(value: float) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True],
            "AUSDT": [value],
        },
        index=pd.DatetimeIndex(["2020-02-03T00:00:00Z"], name="timestamp"),
    )
    return frame


def test_target_equivalence_is_bitwise_and_preserves_signed_zero() -> None:
    assert _targets_exact(_target_frame(0.25), _target_frame(0.25))
    adjacent = np.nextafter(np.float64(0.25), np.float64(1.0))
    assert not _targets_exact(_target_frame(0.25), _target_frame(float(adjacent)))
    assert not _targets_exact(_target_frame(0.0), _target_frame(-0.0))


def _summary(*, pooled: float | None, folds: list[float | None]) -> bytes:
    fold_counts = [0 if value is None else 1 for value in folds]
    payload = {
        "schema_version": 1,
        "diagnostic_id": "team01-rdf-ref",
        "reservation_sha256": "a" * 64,
        "status": "completed",
        "replay": {
            "replay_targets_identical": True,
            "replay_scores_identical": True,
            "canonical_targets_replay_1_exact": True,
            "canonical_targets_replay_2_exact": True,
        },
        "score_ic": {
            "pooled_ic": pooled,
            "fold_ics": folds,
            "daily_ic_count": sum(fold_counts),
            "fold_daily_ic_counts": fold_counts,
        },
    }
    return json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode() + b"\n"


def test_trusted_verdict_discloses_booleans_only() -> None:
    folds = [0.1, 0.2, 0.3, 0.4, -0.1, None]
    verdict = trusted_boolean_verdict(_summary(pooled=0.05, folds=folds))
    assert verdict == {
        "canonical_targets_exact": True,
        "deterministic_replays_passed": True,
        "four_of_six_fold_ics_positive": True,
        "pooled_ic_positive": True,
        "score_ic_gate_passed": True,
    }
    assert all(type(value) is bool for value in verdict.values())
    assert "0.05" not in json.dumps(verdict)


def test_trusted_verdict_rejects_noncanonical_or_inconsistent_private_summary() -> None:
    canonical = _summary(
        pooled=0.05,
        folds=[0.1, 0.2, 0.3, 0.4, -0.1, None],
    )
    with pytest.raises(ValueError, match="canonical"):
        trusted_boolean_verdict(canonical.rstrip())

    raw = json.loads(canonical)
    raw["score_ic"]["fold_daily_ic_counts"][-1] = 1
    raw["score_ic"]["daily_ic_count"] += 1
    inconsistent = json.dumps(
        raw, allow_nan=False, indent=2, sort_keys=True
    ).encode() + b"\n"
    with pytest.raises(ValueError, match="availability"):
        trusted_boolean_verdict(inconsistent)


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


def test_historical_tree_comes_from_unique_registration_commit(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Score Test")
    _git(root, "commit", "--allow-empty", "-m", "repository genesis")
    team = root / "tournament/top40-v2/teams/team-01"
    team.mkdir(parents=True)
    strategy = team / "strategy.py"
    strategy.write_text(
        "class ResidualDriftFundingStrategy:\n"
        "    def target_weights(self, context, *, seed): return {}\n"
        "def build_strategy(): return ResidualDriftFundingStrategy()\n",
        encoding="utf-8",
    )
    risk = team / "risk_policy.json"
    risk.write_text('{"policy_id":"historical"}\n', encoding="utf-8")
    files = runner_v2._team_tree_files(team)
    source_sha = runner_v2._team_tree_fingerprint(files)
    strategy_sha = hashlib.sha256(strategy.read_bytes()).hexdigest()
    risk_sha = hashlib.sha256(risk.read_bytes()).hexdigest()
    config_sha = "b" * 64
    raw_registration = {
        "timestamp_utc": "2026-07-15T20:00:00Z",
        "team_id": "team-01",
        "family_id": FAMILY_ID,
        "candidate_id": "historical-cell",
        "strategy_sha256": strategy_sha,
        "source_bundle_sha256": source_sha,
        "risk_config_sha256": risk_sha,
        "config_sha256": config_sha,
        "parameters": {"cell": 1},
        "seed": 20260801,
        "thesis": "deterministic historical source",
        "falsifier": "reject on mismatch",
    }
    registration_line = build_trial_registration(**raw_registration)
    registration_path = root / (
        "reports-top40-v2/team-01/registration-inputs/historical-cell.json"
    )
    registration_path.parent.mkdir(parents=True)
    registration_path.write_text(
        json.dumps(raw_registration, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "register historical cell")

    request = ScoreDiagnosticRequest(
        diagnostic_id="historical-cell-score",
        team_id="team-01",
        family_id=FAMILY_ID,
        candidate_id="historical-cell",
        registration_sha256=hashlib.sha256(registration_line).hexdigest(),
        strategy_sha256=strategy_sha,
        risk_policy_sha256=risk_sha,
        source_bundle_sha256=source_sha,
        candidate_seed=20260801,
        config_sha256=config_sha,
        snapshot_manifest_path="tournament/top40/data_manifest.json",
        snapshot_manifest_sha256=_SHA,
        development_target_path=(
            "reports-top40-v2/team-01/development-runs/historical-cell/targets.parquet"
        ),
        development_target_sha256=_SHA,
        runner_record_path=(
            "reports-top40-v2/team-01/qualification-attempts/"
            "historical-cell.runner-record.json"
        ),
        runner_record_sha256=_SHA,
    )
    config = LoadedV2Config(root / "config.toml", config_sha, {})
    with materialized_historical_source(root, config, request) as historical:
        assert historical.entrypoint.read_bytes() == strategy.read_bytes()
        assert historical.binding.strategy_sha256 == strategy_sha
        assert historical.binding.source_bundle_sha256 == source_sha
        assert len(historical.binding.registration_commit) == 40


def test_reserved_api_returns_only_terminal_accounting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = LoadedV2Config(tmp_path / "config.toml", "c" * 64, {})
    monkeypatch.setattr(
        "crypto_trade.tournament.score_diagnostics_v2.load_v2_config", lambda _path: config
    )
    monkeypatch.setattr(
        "crypto_trade.tournament.score_diagnostics_v2.run_score_diagnostic",
        lambda *_args, **_kwargs: object(),
    )
    reservation = {
        "record_sha256": "d" * 64,
        "payload": {
            "diagnostic_id": "reserved-score",
            "team_id": "team-01",
            "candidate_id": "candidate",
            "candidate_registration_sha256": "e" * 64,
            "strategy_sha256": "f" * 64,
            "source_bundle_sha256": "1" * 64,
            "risk_policy_sha256": "2" * 64,
            "config_sha256": config.sha256,
            "candidate_seed": 20260801,
            "runner_seed": 20260801,
            "snapshot_manifest_path": "tournament/top40/data_manifest.json",
            "snapshot_manifest_sha256": "3" * 64,
            "development_target_path": "unused",
            "development_target_sha256": "4" * 64,
            "runner_record_path": "unused",
            "runner_record_sha256": "5" * 64,
        },
    }
    result = run_reserved_score_diagnostic(
        root=tmp_path,
        reservation=reservation,
        private_output_dir=tmp_path / "private",
    )
    assert set(result) == {
        "status",
        "failure_reason",
        "organizer_cpu_hours",
        "organizer_wall_clock_hours",
    }
    assert result["status"] == "completed"
    assert result["failure_reason"] is None


def test_private_artifact_set_is_atomic_and_exactly_idempotent(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init")
    request = SimpleNamespace(team_id="team-01", diagnostic_id="atomic-score")
    final = (
        git_path(root, PRIVATE_ARTIFACT_GIT_PATH)
        / request.team_id
        / request.diagnostic_id
    )
    artifacts = {
        name: f"private-{name}\n".encode() for name in REQUIRED_PRIVATE_ARTIFACT_NAMES
    }

    hashes = _publish_private_artifacts(root, request, artifacts, final)

    assert set(final.iterdir()) == {
        final / name for name in REQUIRED_PRIVATE_ARTIFACT_NAMES
    }
    assert all((final / name).stat().st_mode & 0o777 == 0o600 for name in artifacts)
    assert _publish_private_artifacts(root, request, artifacts, final) == hashes


def test_private_artifact_publication_cleans_pre_rename_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init")
    request = SimpleNamespace(team_id="team-01", diagnostic_id="interrupted-score")
    final = (
        git_path(root, PRIVATE_ARTIFACT_GIT_PATH)
        / request.team_id
        / request.diagnostic_id
    )
    artifacts = {
        name: f"private-{name}\n".encode() for name in REQUIRED_PRIVATE_ARTIFACT_NAMES
    }

    def interrupted_rename(_source: Path, _destination: Path) -> None:
        raise OSError("synthetic interruption before directory rename")

    monkeypatch.setattr(
        "crypto_trade.tournament.score_diagnostics_v2.os.rename",
        interrupted_rename,
    )
    with pytest.raises(OSError, match="synthetic interruption"):
        _publish_private_artifacts(root, request, artifacts, final)

    assert not final.exists()
    assert not list(final.parent.glob(f".{request.diagnostic_id}.publishing-*"))
