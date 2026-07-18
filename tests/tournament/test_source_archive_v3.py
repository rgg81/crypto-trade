from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from crypto_trade.tournament import runner_v3, source_archive_v3


def _candidate_tree(root: Path) -> tuple[Path, Path]:
    team = root / "tournament/top40-v3/teams/team-01"
    team.mkdir(parents=True)
    entrypoint = team / "strategy.py"
    entrypoint.write_text("def build_strategy(): ...\n", encoding="utf-8")
    (team / "frozen_config.json").write_text("{}\n", encoding="utf-8")
    (team / "risk_policy.json").write_text("{}\n", encoding="utf-8")
    (team / "RESEARCH-BRIEF.md").write_text("Price-only baseline.\n", encoding="utf-8")
    incumbent = team / "incumbents/incumbent-001"
    incumbent.mkdir(parents=True)
    nested_entrypoint = incumbent / "strategy.py"
    nested_entrypoint.write_text("VALUE = 1\n", encoding="utf-8")
    (incumbent / "risk_policy.json").write_text("{}\n", encoding="utf-8")
    helpers = incumbent / "helpers"
    helpers.mkdir()
    (helpers / "feature.py").write_text("VALUE = 2\n", encoding="utf-8")
    return entrypoint, nested_entrypoint


def test_top_level_candidate_excludes_nested_siblings_but_nested_candidate_is_recursive(
    tmp_path: Path,
) -> None:
    top, nested = _candidate_tree(tmp_path)
    top_relative = top.relative_to(tmp_path).as_posix()
    nested_relative = nested.relative_to(tmp_path).as_posix()

    top_before = runner_v3.capture_source_bundle(tmp_path, "team-01", top_relative)
    nested_before = runner_v3.capture_source_bundle(tmp_path, "team-01", nested_relative)

    assert top_before.candidate_root == "tournament/top40-v3/teams/team-01"
    assert {entry["path"] for entry in top_before.manifest_entries} == {
        "RESEARCH-BRIEF.md",
        "frozen_config.json",
        "risk_policy.json",
        "strategy.py",
    }
    assert {entry["path"] for entry in nested_before.manifest_entries} == {
        "helpers/feature.py",
        "risk_policy.json",
        "strategy.py",
    }

    (nested.parent / "helpers/feature.py").write_text("VALUE = 3\n", encoding="utf-8")
    top_after = runner_v3.capture_source_bundle(tmp_path, "team-01", top_relative)
    nested_after = runner_v3.capture_source_bundle(tmp_path, "team-01", nested_relative)
    assert top_after.sha256 == top_before.sha256
    assert nested_after.sha256 != nested_before.sha256


def test_archive_is_canonical_content_addressed_reusable_and_self_verifying(
    tmp_path: Path,
) -> None:
    top, _nested = _candidate_tree(tmp_path)
    capture = runner_v3.capture_source_bundle(
        tmp_path, "team-01", top.relative_to(tmp_path).as_posix()
    )
    first = source_archive_v3.write_source_archive(
        tmp_path,
        team_id="team-01",
        candidate_id="candidate-001",
        candidate_root=capture.candidate_root,
        entrypoint=capture.entrypoint,
        source_bundle_sha256=capture.sha256,
        files=capture.files,
    )
    second = source_archive_v3.write_source_archive(
        tmp_path,
        team_id="team-01",
        candidate_id="candidate-001",
        candidate_root=capture.candidate_root,
        entrypoint=capture.entrypoint,
        source_bundle_sha256=capture.sha256,
        files=capture.files,
    )

    assert second == first
    assert first.source_bundle_sha256 == capture.sha256
    assert first.manifest_entries == capture.manifest_entries
    archive_path = tmp_path / first.path
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == first.sha256
    assert first.path.endswith(f"/{first.sha256}.json")

    os.chmod(archive_path, 0o644)
    payload = bytearray(archive_path.read_bytes())
    payload[-2] ^= 1
    archive_path.write_bytes(payload)
    with pytest.raises(source_archive_v3.SourceArchiveError):
        source_archive_v3.read_source_archive(tmp_path, first.path, first.sha256)


def test_worker_staging_uses_the_same_file_manifest_as_the_archive_boundary(
    tmp_path: Path,
) -> None:
    top, _nested = _candidate_tree(tmp_path)
    capture = runner_v3.capture_source_bundle(
        tmp_path, "team-01", top.relative_to(tmp_path).as_posix()
    )
    destination = tmp_path / "staged"

    staged_sha256 = runner_v3._copy_team_source_bundle(
        top.parent,
        destination,
        recursive=False,
        expected_fingerprint=capture.sha256,
        expected_entries=capture.manifest_entries,
    )

    assert staged_sha256 == capture.sha256
    assert sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*")) == [
        "RESEARCH-BRIEF.md",
        "frozen_config.json",
        "risk_policy.json",
        "strategy.py",
    ]
    assert not (destination / "incumbents").exists()


def test_archive_rejects_non_lowercase_candidate_identity(tmp_path: Path) -> None:
    top, _nested = _candidate_tree(tmp_path)
    capture = runner_v3.capture_source_bundle(
        tmp_path, "team-01", top.relative_to(tmp_path).as_posix()
    )
    with pytest.raises(source_archive_v3.SourceArchiveError, match="lowercase"):
        source_archive_v3.build_archive_bytes(
            team_id="team-01",
            candidate_id="Candidate-001",
            candidate_root=capture.candidate_root,
            entrypoint=capture.entrypoint,
            source_bundle_sha256=capture.sha256,
            files=capture.files,
        )


def test_archive_rejects_an_intermediate_namespace_symlink(tmp_path: Path) -> None:
    top, _nested = _candidate_tree(tmp_path)
    capture = runner_v3.capture_source_bundle(
        tmp_path, "team-01", top.relative_to(tmp_path).as_posix()
    )
    real_reports = tmp_path / "real-reports"
    real_reports.mkdir()
    (tmp_path / "reports-top40-v3").symlink_to(real_reports, target_is_directory=True)

    with pytest.raises(source_archive_v3.SourceArchiveError, match="symlink"):
        source_archive_v3.write_source_archive(
            tmp_path,
            team_id="team-01",
            candidate_id="candidate-001",
            candidate_root=capture.candidate_root,
            entrypoint=capture.entrypoint,
            source_bundle_sha256=capture.sha256,
            files=capture.files,
        )
