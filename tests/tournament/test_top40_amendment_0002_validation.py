from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_trade.tournament import lab_v3, source_archive_v3
from crypto_trade.tournament import top40_amendment_0002_validation as validation
from crypto_trade.tournament.qualification_v3 import CandidateIdentity

ROOT = Path(__file__).parents[2]
HASH = "a" * 64


def _identity(team_id: str = "team-04", candidate_id: str = "candidate-v1") -> CandidateIdentity:
    offsets = tuple(
        hashlib.sha256(f"identity-field-{index}".encode()).hexdigest() for index in range(7)
    )
    return CandidateIdentity(
        team_id=team_id,
        candidate_id=candidate_id,
        source_bundle_sha256=offsets[0],
        strategy_sha256=offsets[1],
        dependency_lock_sha256=offsets[2],
        config_sha256=offsets[3],
        risk_policy_sha256=offsets[4],
        data_authority_sha256=offsets[5],
        evaluator_sha256=offsets[6],
    )


def _archive(identity: CandidateIdentity) -> source_archive_v3.SourceArchive:
    config = json.dumps(
        {
            "schema_version": 1,
            "team_id": identity.team_id,
            "candidate_id": identity.candidate_id,
            "seed": 20260718,
            "implementation": {"entrypoint": "strategy.py"},
        },
        sort_keys=True,
    ).encode()
    contents = {
        "frozen_config.json": config,
        "risk_policy.json": b"{}\n",
        "strategy.py": b"def build_strategy():\n    return object()\n",
    }
    files = tuple(
        source_archive_v3.SourceFile(
            path=path,
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            content=content,
        )
        for path, content in sorted(contents.items())
    )
    bundle = source_archive_v3.bundle_fingerprint(item.manifest_entry for item in files)
    return source_archive_v3.SourceArchive(
        path=f"reports-top40-v3/source-archives/sha256/{HASH}.json",
        sha256=HASH,
        team_id=identity.team_id,
        candidate_id=identity.candidate_id,
        candidate_root=f"tournament/top40-v3/teams/{identity.team_id}/original",
        entrypoint="strategy.py",
        source_bundle_sha256=bundle,
        files=files,
    )


def _candidate(identity: CandidateIdentity | None = None) -> validation.CohortCandidate:
    identity = identity or _identity()
    archive = _archive(identity)
    # Packet construction tests do not ask archive hashes to equal the synthetic identity.
    return validation.CohortCandidate(
        rank=1,
        identity=identity,
        entrypoint=f"tournament/top40-v3/teams/{identity.team_id}/original/strategy.py",
        train_run_id="v3-train-1",
        train_metric_packet_path="reports-top40-v3/labs/train/metric_packet.json",
        train_metric_packet_sha256=HASH,
        source_archive_path=archive.path,
        source_archive_sha256=archive.sha256,
        source_archive=archive,
    )


def _accepted_event(
    state: validation.ValidationJournalState,
    identity: CandidateIdentity,
) -> dict[str, object]:
    _next, authorization = lab_v3.authorize_validation_probe(
        state.ledger, identity, round_name="opening"
    )
    staging_root = (
        f"tournament/top40-v3/teams/{identity.team_id}/.sealed-validation/{identity.sha256}"
    )
    run_id = f"v3-{identity.team_id.replace('-', '')}-validation-000001-{identity.sha256[:12]}"
    output = f"tournament/top40-v3/private/validation/{identity.team_id}/{run_id}"
    return {
        "event_type": "probe_accepted",
        "team_id": identity.team_id,
        "run_id": run_id,
        "candidate_id": identity.candidate_id,
        "candidate_identity_sha256": identity.sha256,
        "accepted_at_utc": "2026-07-18T22:00:01Z",
        "authorization": validation._authorization_mapping(authorization),
        "cohort_freeze_sha256": validation.COHORT_FREEZE_SHA256,
        "train_metric_packet_path": "reports-top40-v3/labs/example/metric_packet.json",
        "train_metric_packet_sha256": HASH,
        "original_source_archive_path": f"reports-top40-v3/source-archives/sha256/{HASH}.json",
        "original_source_archive_sha256": HASH,
        "staging_source_archive_path": f"reports-top40-v3/source-archives/sha256/{'b' * 64}.json",
        "staging_source_archive_sha256": "b" * 64,
        "staging_candidate_root": staging_root,
        "staging_entrypoint": f"{staging_root}/strategy.py",
        "source_bundle_sha256": identity.source_bundle_sha256,
        "strategy_sha256": identity.strategy_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "config_sha256": identity.config_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "data_authority_sha256": identity.data_authority_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
        "seed": 20260718,
        "validation_window": dict(validation.VALIDATION_WINDOW),
        "output_path": output,
        "replay_output_path": f"{output}-exact-replay",
    }


def _terminal_event(request: dict[str, object]) -> dict[str, object]:
    output = str(request["output_path"])
    return {
        "event_type": "succeeded",
        "team_id": request["team_id"],
        "run_id": request["run_id"],
        "candidate_id": request["candidate_id"],
        "candidate_identity_sha256": request["candidate_identity_sha256"],
        "request_sha256": request["record_sha256"],
        "completed_at_utc": "2026-07-18T22:00:01Z",
        "cpu_seconds": 1.0,
        "wall_seconds": 2.0,
        "gate_vector": {"validation_exact_replay": True},
        "aggregate_packet_path": f"{output}/aggregate_packet.json",
        "aggregate_packet_sha256": HASH,
        "artifact_hashes": {f"{output}/aggregate_packet.json": HASH},
        "failure_reason": None,
    }


def test_live_cohort_reconstructs_exact_four_green_identities() -> None:
    cohort = validation.load_cohort(ROOT)

    assert [candidate.identity.team_id for candidate in cohort.candidates] == [
        "team-06",
        "team-05",
        "team-04",
        "team-09",
    ]
    assert [candidate.rank for candidate in cohort.candidates] == [1, 2, 3, 4]
    assert cohort.file_sha256 == validation.COHORT_FREEZE_SHA256


def test_journal_consumes_authorization_before_terminal_and_rejects_reuse(
    tmp_path: Path,
) -> None:
    (tmp_path / "tournament/top40-v3").mkdir(parents=True)
    state = validation.replay_validation_journal_bytes(b"")
    identity = _identity()
    state = validation._append_journal_event(tmp_path, _accepted_event(state, identity))

    assert len(state.pending_request_sha256s) == 1
    assert len(state.ledger.probe_authorizations) == 1
    request = dict(state.records[-1])
    state = validation._append_journal_event(tmp_path, _terminal_event(request))
    assert not state.pending_request_sha256s

    with pytest.raises(ValueError, match="second validation observation"):
        validation._append_journal_event(tmp_path, _accepted_event(state, identity))


def test_journal_rejects_truncation_and_hash_tampering(tmp_path: Path) -> None:
    (tmp_path / "tournament/top40-v3").mkdir(parents=True)
    state = validation._append_journal_event(
        tmp_path,
        _accepted_event(validation.replay_validation_journal_bytes(b""), _identity()),
    )
    payload = (tmp_path / validation.VALIDATION_JOURNAL_PATH).read_bytes()

    with pytest.raises(validation.Amendment0002ValidationError, match="truncated"):
        validation.replay_validation_journal_bytes(payload[:-1])
    changed = payload.replace(b'"seed":20260718', b'"seed":20260719')
    with pytest.raises(validation.Amendment0002ValidationError, match="window or seed"):
        validation.replay_validation_journal_bytes(changed)
    assert state.records[-1]["authorization"]["team_total_probe_number"] == 1


def test_four_terminals_require_a_durable_single_release(tmp_path: Path) -> None:
    (tmp_path / "tournament/top40-v3").mkdir(parents=True)
    state = validation.replay_validation_journal_bytes(b"")
    for team_id in ("team-04", "team-05", "team-06", "team-09"):
        identity = _identity(team_id, f"candidate-{team_id[-2:]}")
        state = validation._append_journal_event(tmp_path, _accepted_event(state, identity))
        state = validation._append_journal_event(tmp_path, _terminal_event(dict(state.records[-1])))
    terminal_head = state.head_sha256
    state = validation._append_journal_event(
        tmp_path,
        {
            "event_type": "packet_released",
            "released_at_utc": "2026-07-18T22:00:02Z",
            "cohort_freeze_sha256": validation.COHORT_FREEZE_SHA256,
            "terminal_journal_head_sha256": terminal_head,
            "packet_sha256_by_team": {
                team_id: HASH for team_id in ("team-04", "team-05", "team-06", "team-09")
            },
        },
    )

    assert state.release_record is not None
    with pytest.raises(validation.Amendment0002ValidationError, match="only once"):
        validation._append_journal_event(
            tmp_path,
            {
                "event_type": "packet_released",
                "released_at_utc": "2026-07-18T22:00:03Z",
                "cohort_freeze_sha256": validation.COHORT_FREEZE_SHA256,
                "terminal_journal_head_sha256": terminal_head,
                "packet_sha256_by_team": {
                    team_id: HASH for team_id in ("team-04", "team-05", "team-06", "team-09")
                },
            },
        )


def test_packet_is_fixed_aggregate_only() -> None:
    identity = _identity()
    candidate = _candidate(identity)
    _ledger, authorization = lab_v3.authorize_validation_probe(
        lab_v3.new_validation_ledger(), identity, round_name="opening"
    )
    fields = {
        "scored_window": {
            "start": "2022-07-01",
            "end": "2023-06-30",
            "metrics": {
                "net_sharpe": 1.1,
                "net_sortino": 1.2,
                "calmar": 1.3,
                "annualized_return": 0.2,
                "max_drawdown": 0.1,
                "positive_quarter_fraction": 0.75,
            },
        },
        "double_cost_sharpe": 0.8,
        "regime_sharpe": {"bull": 1.0, "bear": 0.2, "chop": 0.4, "stress": -0.1},
        "confidence_intervals": {
            "net_sharpe_95": [0.5, 1.7],
            "double_cost_sharpe_95": [0.2, 1.4],
        },
    }
    packet = validation.build_validation_aggregate_packet(
        fields,
        candidate,
        authorization,
        activation=validation.ActivationAuthority(
            freeze_file_sha256=HASH,
            freeze_commit="a" * 40,
            record_sha256="b" * 64,
            implementation_commit="c" * 40,
            cohort_freeze_sha256=validation.COHORT_FREEZE_SHA256,
            cohort_freeze_commit=validation.COHORT_FREEZE_COMMIT,
        ),
        artifact_aggregates={
            "validation_trade_count": 1234,
            "cumulative_net_return": 0.2,
            "cumulative_double_cost_return": 0.15,
            "quarter_returns": {
                "2022Q3": 0.1,
                "2022Q4": 0.0,
                "2023Q1": 0.05,
                "2023Q2": 0.04,
            },
        },
        evidence_manifest_sha256="d" * 64,
    )
    encoded = validation._canonical_bytes(packet)

    assert packet["validation_aggregates"]["trade_count"] == 1234
    assert packet["readiness"]["validation_positive"] is True
    for forbidden in (b"targets", b"positions", b"daily_returns", b"trades.csv", b"output_dir"):
        assert forbidden not in encoded


def test_validation_only_aggregates_slice_full_replay_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "tournament/top40-v3/private/validation/team-04/run"
    output.mkdir(parents=True)
    (output / "trades.csv").write_text(
        "timestamp,symbol\n"
        "2022-06-30T00:00:00Z,BTCUSDT\n"
        "2022-07-01T00:00:00Z,ETHUSDT\n"
        "2023-06-30T16:00:00Z,SOLUSDT\n"
        "2023-07-01T00:00:00Z,BTCUSDT\n"
    )
    dates = []
    start = __import__("datetime").date(2022, 7, 1)
    for offset in range(365):
        day = start + __import__("datetime").timedelta(days=offset)
        dates.append(f"{day.isoformat()},0.001\n")
    daily = "date,net_return\n" + "".join(dates)
    (output / "daily_returns.csv").write_text(daily)
    (output / "double_cost_daily_returns.csv").write_text(daily)
    relative = output.relative_to(tmp_path).as_posix()
    result = SimpleNamespace(
        artifacts={
            "trades": f"{relative}/trades.csv",
            "daily_returns": f"{relative}/daily_returns.csv",
            "double_cost_daily_returns": f"{relative}/double_cost_daily_returns.csv",
        }
    )

    aggregate = validation._validation_artifact_aggregates(tmp_path, result)

    assert aggregate["validation_trade_count"] == 2
    assert set(aggregate["quarter_returns"]) == {"2022Q3", "2022Q4", "2023Q1", "2023Q2"}


def test_archive_rehydration_ignores_mutable_team_tree(tmp_path: Path) -> None:
    original_identity = _identity()
    archive = _archive(original_identity)
    identity = dataclasses.replace(
        original_identity,
        source_bundle_sha256=archive.source_bundle_sha256,
        strategy_sha256=hashlib.sha256(
            next(item.content for item in archive.files if item.path == "strategy.py")
        ).hexdigest(),
        risk_policy_sha256=hashlib.sha256(
            next(item.content for item in archive.files if item.path == "risk_policy.json")
        ).hexdigest(),
    )
    candidate = dataclasses.replace(_candidate(identity), source_archive=archive)
    team_root = tmp_path / "tournament/top40-v3/teams/team-04"
    team_root.mkdir(parents=True)
    poison = team_root / "strategy.py"
    poison.write_text("raise RuntimeError('mutable poison')\n")

    staging_root, staging_entrypoint, derived = validation._rehydrate_candidate(tmp_path, candidate)

    assert poison.read_text() == "raise RuntimeError('mutable poison')\n"
    assert derived.source_bundle_sha256 == archive.source_bundle_sha256
    assert Path(tmp_path / staging_entrypoint).read_bytes() == next(
        item.content for item in archive.files if item.path == "strategy.py"
    )
    validation._remove_staging(tmp_path, staging_root)


def test_cli_has_no_train_private_or_final_command() -> None:
    script = (ROOT / validation.ACTIVE_SCRIPT_PATH).read_text()
    assert 'add_parser("probe"' in script
    assert 'add_parser("report"' in script
    assert 'add_parser("train"' not in script
    assert 'add_parser("private"' not in script
    assert 'add_parser("final"' not in script


def test_current_base_command_omits_only_obsolete_pretournament_bundle_file() -> None:
    assert (
        validation.OBSOLETE_PRETOURNAMENT_BUNDLE_TEST in validation.phase0_v3.TARGETED_TEST_COMMAND
    )
    assert validation.OBSOLETE_PRETOURNAMENT_BUNDLE_TEST not in validation.BASE_TEST_COMMAND
    assert len(validation.BASE_TEST_COMMAND) == len(validation.phase0_v3.TARGETED_TEST_COMMAND) - 1
    assert validation.amendment_0001.UTC_TEST_PATH in validation.PARENT_AMENDMENT_TEST_COMMAND
    assert (
        validation.amendment_0001.INTEGRATION_TEST_PATH
        not in validation.PARENT_AMENDMENT_TEST_COMMAND
    )
