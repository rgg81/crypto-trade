from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import _strategy_worker_v3, runner_v3
from crypto_trade.tournament.engine_v2 import EvaluationResult
from crypto_trade.tournament.top40_v3 import load_config

ROOT = Path(__file__).parents[2]
CONFIG_PATH = ROOT / "tournament/top40-v3/config.toml"
MANIFEST_PATH = ROOT / "tournament/top40/data_manifest.json"
ENTRYPOINT = ROOT / "tournament/top40-v3/teams/team-01/strategy.py"
HASH_A = "a" * 64
ARCHIVE_SHA = "c" * 64


def _archive_authority(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    capture = SimpleNamespace(
        candidate_root="tournament/top40-v3/teams/team-01",
        entrypoint="strategy.py",
        sha256=HASH_A,
        manifest_entries=(),
    )
    archive = SimpleNamespace(
        team_id="team-01",
        candidate_id="candidate-001",
        candidate_root=capture.candidate_root,
        entrypoint=capture.entrypoint,
        source_bundle_sha256=HASH_A,
        manifest_entries=(),
    )
    monkeypatch.setattr(runner_v3, "capture_source_bundle", lambda *_args: capture)
    monkeypatch.setattr(
        runner_v3.source_archive_v3,
        "read_source_archive",
        lambda *_args, **_kwargs: archive,
    )
    return {
        "_candidate_id": "candidate-001",
        "_source_archive_relative": (
            f"reports-top40-v3/source-archives/sha256/{ARCHIVE_SHA}.json"
        ),
        "_source_archive_sha256": ARCHIVE_SHA,
    }


def _config() -> dict[str, object]:
    return deepcopy(dict(load_config(CONFIG_PATH).raw))


def test_exact_stage_windows_replay_from_train_and_score_only_authorized_stage():
    config = _config()
    expected = {
        "train": ("2022-07-01T00:00:00Z", "2020-02-03T00:00:00Z", "2022-06-30"),
        "validation": ("2023-07-01T00:00:00Z", "2022-07-01T00:00:00Z", "2023-06-30"),
        "public": ("2023-07-01T00:00:00Z", "2020-02-03T00:00:00Z", "2023-06-30"),
        "private": ("2024-07-01T00:00:00Z", "2023-07-01T00:00:00Z", "2024-06-30"),
        "final_oos": ("2026-07-01T00:00:00Z", "2024-07-01T00:00:00Z", "2026-06-30"),
    }
    for stage, (end_exclusive, score_start, score_end) in expected.items():
        window = runner_v3._authorized_window(config, stage)
        assert window.replay_start == "2020-02-03T00:00:00Z"
        assert window.end_exclusive == end_exclusive
        assert window.score_start == score_start
        assert window.score_end_inclusive == score_end
        grid = runner_v3._decision_grid(window)
        assert grid[0] == pd.Timestamp("2020-02-03T00:00:00Z")
        assert grid[-1] == pd.Timestamp(end_exclusive) - pd.Timedelta(hours=8)

    with pytest.raises(ValueError, match="train, validation, public, private, or final_oos"):
        runner_v3._authorized_window(config, "development")


@pytest.mark.parametrize(
    ("stage", "relative", "private"),
    (
        ("train", "reports-top40-v3/labs/team-01/lab-000001", False),
        ("validation", "tournament/top40-v3/private/validation/team-01/probe-01", True),
        ("public", "tournament/top40-v3/private/public/team-01/nominee-01", True),
        ("private", "tournament/top40-v3/private/private/team-01/nominee-01", True),
        ("final_oos", "tournament/top40-v3/private/final-oos/team-01/nominee-01", True),
    ),
)
def test_stage_outputs_are_unique_v3_paths_and_sealed_when_required(stage, relative, private):
    assert runner_v3._validated_output_relative("team-01", stage, relative) == relative
    if private:
        assert relative.startswith("tournament/top40-v3/private/")
    else:
        assert relative.startswith("reports-top40-v3/labs/team-01/")
    assert "top40-v2" not in relative


def test_final_publication_namespace_is_v3_only_and_separate_from_raw_artifacts():
    raw_prefix = runner_v3._stage_output_prefix("team-01", "final_oos")
    publication_prefix = runner_v3._final_publication_prefix("team-01")

    assert raw_prefix == "tournament/top40-v3/private/final-oos/team-01/"
    assert publication_prefix == "reports-top40-v3/results/final-oos/team-01/"
    assert raw_prefix != publication_prefix


def test_candidate_risk_policy_is_resolved_adjacent_to_selected_entrypoint(tmp_path: Path):
    team_root = tmp_path / "tournament/top40-v3/teams/team-04"
    team_root.mkdir(parents=True)
    top_entrypoint = team_root / "strategy.py"
    top_risk = team_root / "risk_policy.json"
    top_entrypoint.write_text("def build_strategy(): ...\n", encoding="utf-8")
    top_risk.write_text("{}\n", encoding="utf-8")

    incumbent = team_root / "incumbents/team-04-utc-reference-001-v3-port"
    incumbent.mkdir(parents=True)
    nested_entrypoint = incumbent / "strategy.py"
    nested_risk = incumbent / "risk_policy.json"
    nested_entrypoint.write_text("def build_strategy(): ...\n", encoding="utf-8")
    nested_risk.write_text('{"candidate": "utc"}\n', encoding="utf-8")

    assert runner_v3._resolve_team_risk_policy(
        tmp_path, "team-04", top_entrypoint
    ) == top_risk.resolve()
    assert runner_v3._resolve_team_risk_policy(
        tmp_path, "team-04", nested_entrypoint
    ) == nested_risk.resolve()


def test_nested_candidate_cannot_borrow_team_root_risk_policy(tmp_path: Path):
    team_root = tmp_path / "tournament/top40-v3/teams/team-05"
    incumbent = team_root / "incumbents/team05-crtr-ab-dd-v3-port"
    incumbent.mkdir(parents=True)
    entrypoint = incumbent / "strategy.py"
    entrypoint.write_text("def build_strategy(): ...\n", encoding="utf-8")
    (team_root / "risk_policy.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="beside the selected team-05 entrypoint"):
        runner_v3._resolve_team_risk_policy(tmp_path, "team-05", entrypoint)


def test_candidate_local_risk_policy_is_part_of_staged_source_bundle(tmp_path: Path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "strategy.py").write_text("def build_strategy(): ...\n", encoding="utf-8")
    (candidate / "risk_policy.json").write_text("{}\n", encoding="utf-8")

    files = runner_v3._team_tree_files(candidate)
    risk_file = next(item for item in files if item.relative == "risk_policy.json")

    assert risk_file.staged is True
    assert risk_file.sha256 == hashlib.sha256(b"{}\n").hexdigest()


def test_authorized_runner_refuses_to_start_without_source_archive_authority():
    with pytest.raises(ValueError, match="immutable candidate source archive"):
        runner_v3.run_team(
            ROOT,
            "team-01",
            ENTRYPOINT.relative_to(ROOT),
            CONFIG_PATH.relative_to(ROOT),
            MANIFEST_PATH.relative_to(ROOT),
            stage="train",
            _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
            _output_relative="reports-top40-v3/labs/team-01/missing-archive",
        )


def test_v3_snapshot_loader_directly_verifies_manifest_files_and_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    entries: list[dict[str, object]] = []
    for name in runner_v3._REQUIRED_DATASETS:
        path = snapshot_dir / f"{name}.parquet"
        content = f"fixture-{name}\n".encode()
        path.write_bytes(content)
        entries.append(
            {
                "dataset": name,
                "path": path.relative_to(tmp_path).as_posix(),
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    manifest_path = tmp_path / "data_manifest.json"
    manifest_path.write_text(json.dumps({"files": entries}), encoding="utf-8")
    monkeypatch.setattr(
        runner_v3.pd,
        "read_parquet",
        lambda path: pd.DataFrame({"source": [Path(path).name]}),
    )

    loaded = runner_v3._load_verified_snapshot(tmp_path, manifest_path)

    assert set(loaded.paths) == set(runner_v3._REQUIRED_DATASETS)
    assert not hasattr(runner_v3, "_invoke_snapshot_verifier")
    tampered = loaded.paths["bars"]
    original = tampered.read_bytes()
    tampered.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    with pytest.raises(ValueError, match="snapshot sha256 mismatch"):
        runner_v3._load_verified_snapshot(tmp_path, manifest_path)


@pytest.mark.parametrize(
    ("stage", "relative"),
    (
        ("train", None),
        ("train", "reports-top40-v3/labs/team-01"),
        ("train", "reports-top40-v3/labs/team-02/stolen"),
        ("train", "reports-top40-v2/labs/team-01/stale"),
        ("validation", "reports-top40-v3/labs/team-01/probe"),
        ("private", "tournament/top40-v3/private/private/team-01/../escape"),
        ("final_oos", "/tmp/escape"),
    ),
)
def test_output_path_contract_fails_closed(stage, relative):
    with pytest.raises(ValueError, match="unique organizer|canonical V3 stage prefix"):
        runner_v3._validated_output_relative("team-01", stage, relative)


def test_prior_lab_directory_is_never_overwritten(tmp_path: Path):
    output = tmp_path / "reports-top40-v3/labs/team-01/lab-000001"
    output.mkdir(parents=True)
    marker = output / "immutable.txt"
    marker.write_text("first\n", encoding="utf-8")
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "immutable.txt").write_text("replacement\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        runner_v3._promote_report_directory(staging, output, allow_replace=False)
    assert marker.read_text(encoding="utf-8") == "first\n"


def _audit_bytes(config: dict[str, object], *, status: str = "passed", violations: int = 0) -> bytes:
    authority = config["universe"]["a6_authority"]
    return (json.dumps(
        {
            "status": status,
            "policy_id": authority["policy_id"],
            "policy_sha256": authority["policy_sha256"],
            "counts": {"violations": violations},
            "violations": [] if violations == 0 else ["not-pure"],
        },
        sort_keys=True,
    ) + "\n").encode("utf-8")


def test_a6_preflight_requires_configured_deterministic_zero_violation_report(monkeypatch):
    config = _config()
    payload = _audit_bytes(config)
    config["universe"]["a6_authority"]["audit_report_sha256"] = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(runner_v3.pure_crypto_universe_v6, "audit_report_bytes", lambda _root: payload)

    assert runner_v3._pure_crypto_preflight(ROOT, config) == hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize(("status", "violations"), (("failed", 0), ("passed", 1)))
def test_a6_preflight_rejects_failure_or_any_violation(monkeypatch, status, violations):
    config = _config()
    payload = _audit_bytes(config, status=status, violations=violations)
    config["universe"]["a6_authority"]["audit_report_sha256"] = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(runner_v3.pure_crypto_universe_v6, "audit_report_bytes", lambda _root: payload)

    with pytest.raises(ValueError, match="zero-violation pure-crypto"):
        runner_v3._pure_crypto_preflight(ROOT, config)


def test_run_wrapper_audits_before_and_after_even_when_execution_fails(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(runner_v3, "_load_config", lambda _path, _team: {"config": True})

    def audit(_root, _config):
        calls.append("audit")
        return HASH_A

    monkeypatch.setattr(runner_v3, "_pure_crypto_preflight", audit)
    monkeypatch.setattr(
        runner_v3,
        "_run_team_impl",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("strategy failed")),
    )

    with pytest.raises(RuntimeError, match="strategy failed"):
        runner_v3.run_team(
            ROOT,
            "team-01",
            ENTRYPOINT.relative_to(ROOT),
            CONFIG_PATH.relative_to(ROOT),
            MANIFEST_PATH.relative_to(ROOT),
            stage="train",
            _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
            _output_relative="reports-top40-v3/labs/team-01/lab-000001",
            **_archive_authority(monkeypatch),
        )
    assert calls == ["audit", "audit"]


def test_run_wrapper_binds_success_result_to_both_identical_audits(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(runner_v3, "_load_config", lambda _path, _team: {"config": True})
    monkeypatch.setattr(
        runner_v3,
        "_pure_crypto_preflight",
        lambda _root, _config: calls.append("audit") or HASH_A,
    )
    expected = SimpleNamespace(pure_crypto_report_sha256=HASH_A)
    monkeypatch.setattr(runner_v3, "_run_team_impl", lambda *_args, **_kwargs: expected)

    result = runner_v3.run_team(
        ROOT,
        "team-01",
        ENTRYPOINT.relative_to(ROOT),
        CONFIG_PATH.relative_to(ROOT),
        MANIFEST_PATH.relative_to(ROOT),
        stage="train",
        _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
        _output_relative="reports-top40-v3/labs/team-01/lab-000002",
        **_archive_authority(monkeypatch),
    )
    assert result is expected
    assert calls == ["audit", "audit"]


@pytest.mark.parametrize(
    ("post_mode", "message"),
    (
        ("fails", "post-A6 audit failed"),
        ("differs", "A6 deterministic audit authority changed"),
    ),
)
def test_post_a6_failure_removes_only_the_newly_promoted_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    post_mode: str,
    message: str,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("fixture = true\n", encoding="utf-8")
    output_relative = "reports-top40-v3/labs/team-01/lab-a6-rollback"
    output_path = tmp_path / output_relative
    calls = 0

    def audit(_root, _config):
        nonlocal calls
        calls += 1
        if calls == 1:
            return HASH_A
        if post_mode == "fails":
            raise ValueError("post-A6 audit failed")
        return "b" * 64

    def execute(*_args, **_kwargs):
        output_path.mkdir(parents=True)
        (output_path / "artifact.txt").write_text("new\n", encoding="utf-8")
        return SimpleNamespace(
            pure_crypto_report_sha256=HASH_A,
            output_dir=output_relative,
        )

    monkeypatch.setattr(runner_v3, "_load_config", lambda *_args: {"fixture": True})
    monkeypatch.setattr(runner_v3, "_pure_crypto_preflight", audit)
    monkeypatch.setattr(runner_v3, "_run_team_impl", execute)

    with pytest.raises(ValueError, match=message):
        runner_v3.run_team(
            tmp_path,
            "team-01",
            "unused-entrypoint.py",
            config_path,
            "unused-manifest.json",
            stage="train",
            _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
            _output_relative=output_relative,
            **_archive_authority(monkeypatch),
        )

    assert calls == 2
    assert not output_path.exists()


def test_post_a6_failure_never_removes_a_preexisting_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("fixture = true\n", encoding="utf-8")
    output_relative = "reports-top40-v3/labs/team-01/lab-preexisting"
    output_path = tmp_path / output_relative
    output_path.mkdir(parents=True)
    marker = output_path / "immutable.txt"
    marker.write_text("keep\n", encoding="utf-8")
    audits = iter((HASH_A, "b" * 64))
    monkeypatch.setattr(runner_v3, "_load_config", lambda *_args: {"fixture": True})
    monkeypatch.setattr(
        runner_v3,
        "_pure_crypto_preflight",
        lambda *_args: next(audits),
    )
    monkeypatch.setattr(
        runner_v3,
        "_run_team_impl",
        lambda *_args, **_kwargs: SimpleNamespace(
            pure_crypto_report_sha256=HASH_A,
            output_dir=output_relative,
        ),
    )

    with pytest.raises(ValueError, match="A6 deterministic audit authority changed"):
        runner_v3.run_team(
            tmp_path,
            "team-01",
            "unused-entrypoint.py",
            config_path,
            "unused-manifest.json",
            stage="train",
            _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
            _output_relative=output_relative,
            **_archive_authority(monkeypatch),
        )

    assert marker.read_text(encoding="utf-8") == "keep\n"


def _snapshot(manifest_sha256: str) -> runner_v3._SnapshotData:
    boundaries = pd.DatetimeIndex(
        [
            "2020-02-03T00:00:00Z",
            "2022-07-01T00:00:00Z",
            "2023-07-01T00:00:00Z",
            "2024-07-01T00:00:00Z",
            "2026-06-30T16:00:00Z",
        ]
    )
    bars = pd.DataFrame(
        {
            "open_time": boundaries,
            "symbol": "BTCUSDT",
            "open": np.arange(len(boundaries), dtype=float) + 10_000.0,
            "close": np.arange(len(boundaries), dtype=float) + 10_001.0,
            "quote_volume": 1_000_000.0,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": boundaries,
            "symbol": "BTCUSDT",
            "funding_rate": 0.0001,
            "mark_price": 10_000.0,
        }
    )
    marks = pd.DataFrame(
        {"mark_time": boundaries, "symbol": "BTCUSDT", "mark_price": 10_000.0}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": boundaries,
            "symbol": "BTCUSDT",
            "liquidity_rank": 1,
            "trailing_quote_volume": 1_000_000.0,
        }
    )
    return runner_v3._SnapshotData(
        manifest_sha256=manifest_sha256,
        paths={},
        file_hashes={},
        bars=bars,
        funding=funding,
        mark_prices=marks,
        membership=membership,
        contract_metadata=pd.DataFrame({"symbol": ["BTCUSDT"]}),
    )


def _evaluation(index: pd.DatetimeIndex) -> EvaluationResult:
    return EvaluationResult(
        returns=pd.DataFrame({"net_return": np.zeros(len(index))}, index=index),
        positions=pd.DataFrame({"BTCUSDT": np.zeros(len(index))}, index=index),
        events=pd.DataFrame(),
    )


@pytest.mark.parametrize(
    ("stage", "end_exclusive", "output"),
    (
        ("train", "2022-07-01T00:00:00Z", "reports-top40-v3/labs/team-01/lab-cutoff"),
        ("validation", "2023-07-01T00:00:00Z", "tournament/top40-v3/private/validation/team-01/probe-cutoff"),
        ("public", "2023-07-01T00:00:00Z", "tournament/top40-v3/private/public/team-01/public-cutoff"),
        ("private", "2024-07-01T00:00:00Z", "tournament/top40-v3/private/private/team-01/private-cutoff"),
        ("final_oos", "2026-07-01T00:00:00Z", "tournament/top40-v3/private/final-oos/team-01/final-cutoff"),
    ),
)
def test_mocked_run_never_streams_rows_beyond_stage_cutoff(
    monkeypatch, stage, end_exclusive, output
):
    manifest_sha = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    snapshot = _snapshot(manifest_sha)
    observed: list[pd.Timestamp] = []
    audit_hash = _config()["universe"]["a6_authority"]["audit_report_sha256"]
    monkeypatch.setattr(runner_v3, "_pure_crypto_preflight", lambda *_args: audit_hash)
    monkeypatch.setattr(runner_v3, "source_bundle_fingerprint", lambda *_args: (HASH_A, ()))
    monkeypatch.setattr(runner_v3, "_load_verified_snapshot", lambda *_args: snapshot)
    monkeypatch.setattr(runner_v3, "_validate_snapshot_bounds", lambda *_args: None)

    def generate(_root, _team, _entrypoint, bars, funding, membership, decisions, **_kwargs):
        cutoff = pd.Timestamp(end_exclusive)
        for frame, column in (
            (bars, "open_time"),
            (funding, "funding_time"),
            (membership, "reconstitution_time"),
        ):
            assert (pd.to_datetime(frame[column], utc=True) < cutoff).all()
        assert (decisions < cutoff).all()
        observed.append(decisions[-1])
        return pd.DataFrame({"BTCUSDT": 0.0}, index=decisions)

    def evaluate(bars, funding, membership, targets, *, mark_prices, config, risk_policy):
        del config, risk_policy
        cutoff = pd.Timestamp(end_exclusive)
        for frame, column in (
            (bars, "open_time"),
            (funding, "funding_time"),
            (membership, "reconstitution_time"),
            (mark_prices, "mark_time"),
        ):
            assert (pd.to_datetime(frame[column], utc=True) < cutoff).all()
        return _evaluation(targets.index), _evaluation(targets.index)

    def metrics(_base, _stressed, _btc, _config, authorized):
        return {
            "scored_window": runner_v3.EvaluationWindow(
                authorized.score_start,
                authorized.score_end_inclusive,
                runner_v3.WindowMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ),
            "double_cost_sharpe": 0.0,
            "regime_sharpe": {name: 0.0 for name in ("bull", "bear", "chop", "stress")},
            "net_sharpe_confidence_interval": (0.0, 0.0),
            "double_cost_sharpe_confidence_interval": (0.0, 0.0),
        }

    monkeypatch.setattr(runner_v3, "_generate_targets_in_worker", generate)
    monkeypatch.setattr(runner_v3, "evaluate_base_and_double_cost", evaluate)
    monkeypatch.setattr(runner_v3, "_btc_daily_returns", lambda *_args: pd.Series(dtype=float))
    monkeypatch.setattr(runner_v3, "_compute_metrics", metrics)
    monkeypatch.setattr(runner_v3, "_publish_artifacts", lambda *_args, **_kwargs: {})

    result = runner_v3.run_team(
        ROOT,
        "team-01",
        ENTRYPOINT.relative_to(ROOT),
        CONFIG_PATH.relative_to(ROOT),
        MANIFEST_PATH.relative_to(ROOT),
        stage=stage,
        _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
        _output_relative=output,
        **_archive_authority(monkeypatch),
    )

    assert observed == [pd.Timestamp(end_exclusive) - pd.Timedelta(hours=8)]
    assert result.stage == stage
    assert result.seed == 20260718
    assert result.output_dir == output
    assert result.data_manifest_sha256 == manifest_sha
    assert result.dependency_lock_sha256 == hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert len(result.evaluator_sha256) == 64
    assert result.pure_crypto_report_sha256 == audit_hash


def test_worker_command_uses_only_v3_worker_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_v3.sys, "platform", "linux")
    monkeypatch.setattr(runner_v3.shutil, "which", lambda _name: "/usr/bin/unshare")
    command = runner_v3._strategy_worker_command(
        tmp_path,
        tmp_path.parent,
        tmp_path / "bundle",
        tmp_path / "site",
        tmp_path / "runtime",
        "strategy.py",
        tmp_path / "empty-dir",
        tmp_path / "empty-file",
    )

    assert "crypto_trade.tournament._strategy_worker_v3" in command
    assert "crypto_trade.tournament._strategy_worker_v2" not in command


def test_worker_masks_predecessor_and_every_v3_private_or_report_namespace(tmp_path):
    sensitive = set(_strategy_worker_v3._sensitive_paths(tmp_path))

    assert (tmp_path / "data").absolute() in sensitive
    assert (tmp_path / "reports-top40-v2").absolute() in sensitive
    assert (tmp_path / "tournament/top40-v2").absolute() in sensitive
    assert (tmp_path / "reports-top40-v3").absolute() in sensitive
    assert (tmp_path / "tournament/top40-v3").absolute() in sensitive


def test_runner_has_no_predecessor_layout_contract_or_worker_authority():
    source = (ROOT / "src/crypto_trade/tournament/runner_v3.py").read_text(encoding="utf-8")

    assert "top40_v2 as tournament_contract" not in source
    assert "TOP40_V2_LAYOUT" not in source
    assert "_strategy_worker_v2" not in source
    assert "research_budget" not in source
    assert "engine_v2" in source
