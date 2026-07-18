from __future__ import annotations

import copy
import hashlib
import json
import stat
from pathlib import Path

import pytest

from crypto_trade.tournament import phase0_v3 as phase0


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_config(
    root: Path,
    *,
    report_sha256: str,
    module_sha256: str,
    dependency_sha256: str,
    manifest_sha256: str,
) -> None:
    config = f'''[universe.a6_authority]
policy_id = "fixture-pure-crypto-policy-v1"
policy_sha256 = "{'a' * 64}"
audit_module_path = "src/crypto_trade/tournament/pure_crypto_universe_v6.py"
audit_module_sha256 = "{module_sha256}"
audit_dependency_path = "src/crypto_trade/tournament/amendment_integrity_v2.py"
audit_dependency_sha256 = "{dependency_sha256}"
audit_report_sha256 = "{report_sha256}"
data_manifest_path = "tournament/top40/data_manifest.json"
data_manifest_sha256 = "{manifest_sha256}"
membership_sha256 = "{'b' * 64}"
contract_metadata_sha256 = "{'c' * 64}"
exchange_info_sha256 = "{'d' * 64}"
required_before_and_after_every_result_command = true
expected_contract_metadata_symbols = 667
expected_distinct_membership_symbols = 321
expected_membership_rows = 12866
expected_violations = 0
expected_audit_status = "passed"
'''
    (root / "tournament/top40-v3/config.toml").write_text(config, encoding="utf-8")


def _a6_report(manifest_sha256: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "amendment_id": "fixture-a6",
        "policy_id": "fixture-pure-crypto-policy-v1",
        "policy_sha256": "a" * 64,
        "status": "passed",
        "authorities": {
            "data_manifest": {
                "path": "tournament/top40/data_manifest.json",
                "sha256": manifest_sha256,
            },
            "contract_metadata": {"path": "fixture/contracts.json", "sha256": "c" * 64},
            "exchange_info": {"path": "fixture/exchange.json", "sha256": "d" * 64},
            "membership": {"path": "fixture/membership.csv", "sha256": "b" * 64},
        },
        "counts": {
            "contract_metadata_symbols": 667,
            "membership_symbols": 321,
            "membership_rows": 12866,
            "violations": 0,
        },
        "accepted_symbol_sets": {},
        "classifications": {},
        "archive_only_symbols": [],
        "violations": [],
    }


def _fixture_repository(root: Path) -> tuple[Path, bytes]:
    root.mkdir(parents=True)
    for relative in phase0.canonical_scope_paths():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(f"fixture: {relative}\n", encoding="utf-8")

    module = b"# fixture A6 module\n"
    dependency = b"# fixture A6 dependency\n"
    manifest = b'{"fixture":true}\n'
    (root / "src/crypto_trade/tournament/pure_crypto_universe_v6.py").write_bytes(module)
    (root / "src/crypto_trade/tournament/amendment_integrity_v2.py").write_bytes(dependency)
    (root / "tournament/top40/data_manifest.json").write_bytes(manifest)

    report = phase0.pretty_json_bytes(_a6_report(_sha256(manifest)))
    _write_config(
        root,
        report_sha256=_sha256(report),
        module_sha256=_sha256(module),
        dependency_sha256=_sha256(dependency),
        manifest_sha256=_sha256(manifest),
    )

    incumbent = (
        root
        / "tournament/top40-v3/teams/team-04/incumbents/fixture-candidate/candidate_variant.py"
    )
    incumbent.parent.mkdir(parents=True)
    incumbent.write_text("CANDIDATE = 'fixture'\n", encoding="utf-8")
    (root / "tournament/top40-v3/EXTRA-FROZEN-NOTE.md").write_text(
        "# Discovered authority\n",
        encoding="utf-8",
    )
    return root, report


def _evidence(root: Path) -> tuple[dict[str, object], bytes]:
    entries = phase0.build_scope_entries(root)
    output = b"fixture targeted tests: 41 passed\n"
    evidence = phase0.create_targeted_test_evidence(
        scope_head_sha256=str(entries[-1]["entry_sha256"]),
        output_bytes=output,
        collected=41,
    )
    return evidence, output


def _record(root: Path, report: bytes) -> tuple[dict[str, object], bytes]:
    evidence, output = _evidence(root)
    record = phase0.create_phase0_record(
        root,
        test_evidence=evidence,
        test_output_bytes=output,
        a6_report_bytes=report,
    )
    return record, output


def test_scope_freezes_infrastructure_and_excludes_mutable_candidate_lanes(tmp_path: Path) -> None:
    root, _ = _fixture_repository(tmp_path / "repo")

    paths = phase0.canonical_scope_paths(root)

    assert "tournament/top40-v3/INCUMBENT-CHALLENGER-POLICY.md" in paths
    assert "tournament/top40-v3/RESEARCH-SCOUTING-2026.md" in paths
    assert "tournament/top40-v3/EXTRA-FROZEN-NOTE.md" in paths
    assert (
        "tournament/top40-v3/teams/team-04/incumbents/fixture-candidate/"
        "candidate_variant.py"
    ) not in paths
    assert "tests/tournament/test_v3_team_bundles.py" in paths
    assert "src/crypto_trade/tournament/journal_v3.py" in paths
    assert "src/crypto_trade/tournament/metrics_v3.py" in paths
    assert "src/crypto_trade/tournament/sandbox_canary_v3.py" in paths
    assert "tests/tournament/test_sandbox_canary_v3.py" in paths
    assert "src/crypto_trade/tournament/source_archive_v3.py" in paths
    assert "tests/tournament/test_source_archive_v3.py" in paths
    assert (
        "tournament/top40-v3/teams/team-01/fixtures/sandbox-canary/strategy.py"
        in paths
    )
    assert "src/crypto_trade/tournament/amended_orchestrator_compat_v3.py" not in paths
    assert "tests/tournament/test_metrics_v3.py" in phase0.REQUIRED_TARGETED_TESTS
    assert "tests/tournament/test_source_archive_v3.py" in phase0.REQUIRED_TARGETED_TESTS
    assert phase0.REQUIRED_TARGETED_TESTS[0] == "tests/tournament/test_sandbox_canary_v3.py"
    assert "uv.lock" in paths
    assert "tournament/top40/data_manifest.json" in paths
    assert phase0.PHASE0_RECORD_PATH not in paths
    assert not any(path.startswith("tournament/top40-v3/results/") for path in paths)
    assert not any(path.startswith("tournament/top40-v3/journals/") for path in paths)
    assert not any("snapshot-v1" in path for path in paths)
    for number in range(1, 11):
        team_test = (
            f"tournament/top40-v3/teams/team-{number:02d}/"
            f"test_team{number:02d}_strategy.py"
        )
        assert team_test not in paths
        assert team_test in phase0.REQUIRED_TARGETED_TESTS
        assert f"tournament/top40-v3/teams/team-{number:02d}/test_strategy.py" not in paths


def test_record_and_hash_chain_are_deterministic(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")

    first, output = _record(root, report)
    second, _ = _record(root, report)
    authority = phase0.verify_phase0_record(root, first, test_output_bytes=output)

    assert first == second
    entries = first["scope_entries"]
    assert [entry["path"] for entry in entries] == sorted(entry["path"] for entry in entries)
    assert entries[0]["previous_sha256"] == phase0.GENESIS_SHA256
    for previous, current in zip(entries[:-1], entries[1:], strict=True):
        assert current["previous_sha256"] == previous["entry_sha256"]
    assert first["scope_head_sha256"] == entries[-1]["entry_sha256"]
    assert authority.record_sha256 == first["record_sha256"]
    assert authority.scope_file_count == len(entries)


def test_verify_rejects_scoped_byte_drift_and_missing_file(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")
    record, output = _record(root, report)
    playbook = root / "tournament/top40-v3/TEAM-PLAYBOOK.md"
    playbook.write_text(playbook.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")

    with pytest.raises(ValueError, match="scoped bytes changed"):
        phase0.verify_phase0_record(root, record, test_output_bytes=output)

    root, _ = _fixture_repository(tmp_path / "missing")
    (root / "uv.lock").unlink()
    with pytest.raises(ValueError, match="scoped file is missing"):
        phase0.build_scope_entries(root)


def test_scope_rejects_symlink_escape_duplicates_and_discovered_binary(tmp_path: Path) -> None:
    root, _ = _fixture_repository(tmp_path / "symlink")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    architecture = root / "tournament/top40-v3/ARCHITECTURE.md"
    architecture.unlink()
    architecture.symlink_to(outside)
    with pytest.raises(ValueError, match="rejects symlink"):
        phase0.build_scope_entries(root)

    root, _ = _fixture_repository(tmp_path / "paths")
    with pytest.raises(ValueError, match="unsafe path"):
        phase0.build_scope_entries(root, ["../escape"])
    with pytest.raises(ValueError, match="duplicate paths"):
        phase0.build_scope_entries(root, ["uv.lock", "uv.lock"])

    rogue = root / "src/crypto_trade/tournament/rogue_v3.py"
    rogue.write_bytes(b"\xff\x00")
    with pytest.raises(ValueError, match="not UTF-8 text|contains NUL"):
        phase0.build_scope_entries(root)


def test_candidate_iteration_does_not_drift_global_phase0_authority(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")
    record, output = _record(root, report)
    candidate = (
        root
        / "tournament/top40-v3/teams/team-04/incumbents/fixture-candidate/"
        "candidate_variant.py"
    )

    candidate.write_text("CANDIDATE = 'repaired-after-train'\n", encoding="utf-8")

    assert phase0.verify_phase0_record(root, record, test_output_bytes=output)


def test_test_evidence_is_exact_scope_bound_and_all_passing(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")
    evidence, output = _evidence(root)
    assert evidence["command"] == list(phase0.TARGETED_TEST_COMMAND)
    assert evidence["command"][:8] == [
        "env",
        "PYTHONPATH=src",
        "PYTHONDONTWRITEBYTECODE=1",
        "uv",
        "run",
        "--frozen",
        "pytest",
        "-q",
    ]
    assert any(
        path.endswith("test_team04_utc_incumbent.py") for path in evidence["test_files"]
    )
    assert any(
        path.endswith("test_team05_crtr_ab_dd_incumbent.py") for path in evidence["test_files"]
    )
    assert any(
        path.endswith("test_team07_two_tape_incumbent.py") for path in evidence["test_files"]
    )
    assert any(
        path.endswith("test_team09_drp_incumbent.py") for path in evidence["test_files"]
    )

    fake = dict(evidence)
    fake["passed"] = 40
    with pytest.raises(ValueError, match="not complete and all-passing"):
        phase0.create_phase0_record(
            root,
            test_evidence=fake,
            test_output_bytes=output,
            a6_report_bytes=report,
        )

    with pytest.raises(ValueError, match="output differs"):
        phase0.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=b"fabricated output\n",
            a6_report_bytes=report,
        )

    unexpected = dict(evidence)
    unexpected["organizer_claim"] = True
    with pytest.raises(ValueError, match="unexpected record keys"):
        phase0.create_phase0_record(
            root,
            test_evidence=unexpected,
            test_output_bytes=output,
            a6_report_bytes=report,
        )


def test_a6_is_config_scope_and_zero_violation_bound(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "config")
    config_path = root / "tournament/top40-v3/config.toml"
    config = config_path.read_text(encoding="utf-8")
    module = root / "src/crypto_trade/tournament/pure_crypto_universe_v6.py"
    config_path.write_text(
        config.replace(_sha256(module.read_bytes()), "e" * 64),
        encoding="utf-8",
    )
    evidence, output = _evidence(root)
    with pytest.raises(ValueError, match="A6 scoped authority differs"):
        phase0.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=report,
        )

    root, report = _fixture_repository(tmp_path / "unexpected-config")
    config_path = root / "tournament/top40-v3/config.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8") + "unexpected_key = true\n",
        encoding="utf-8",
    )
    evidence, output = _evidence(root)
    with pytest.raises(ValueError, match="unexpected record keys"):
        phase0.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=report,
        )

    root, report = _fixture_repository(tmp_path / "violations")
    parsed = json.loads(report)
    parsed["counts"]["violations"] = 1
    parsed["violations"] = ["fixture violation"]
    evidence, output = _evidence(root)
    with pytest.raises(ValueError, match="zero-violation pass"):
        phase0.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=phase0.pretty_json_bytes(parsed),
        )

    duplicate_report = report.replace(
        b'"schema_version": 1,',
        b'"schema_version": 1,\n  "schema_version": 1,',
    )
    with pytest.raises(ValueError, match="duplicate key"):
        phase0.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=duplicate_report,
        )


def test_verify_rejects_record_and_chain_tampering(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")
    record, output = _record(root, report)

    unexpected = copy.deepcopy(record)
    unexpected["extra"] = "not allowed"
    with pytest.raises(ValueError, match="unexpected record keys"):
        phase0.verify_phase0_record(root, unexpected, test_output_bytes=output)

    bad_record_hash = copy.deepcopy(record)
    bad_record_hash["record_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="record SHA-256 is invalid"):
        phase0.verify_phase0_record(root, bad_record_hash, test_output_bytes=output)

    bad_chain = copy.deepcopy(record)
    bad_chain["a6_audit"]["entry_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="A6 chain link is invalid"):
        phase0.verify_phase0_record(root, bad_chain, test_output_bytes=output)


def test_writer_is_canonical_read_only_and_never_overwrites(tmp_path: Path) -> None:
    root, report = _fixture_repository(tmp_path / "repo")
    record, _ = _record(root, report)

    destination = phase0.write_phase0_record(root, record)

    assert destination == root / phase0.PHASE0_RECORD_PATH
    assert destination.read_bytes() == phase0.pretty_json_bytes(record)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o444
    with pytest.raises(ValueError, match="cannot be overwritten"):
        phase0.write_phase0_record(root, record)
