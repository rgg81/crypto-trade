from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from crypto_trade.tournament import research_v2 as research

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


@pytest.fixture
def policy() -> research.ResearchPolicy:
    return research.ResearchPolicy(
        tournament_id="top40-v2",
        team_ids=("team-01", "team-02"),
        maximum_material_configurations_per_team=80,
        maximum_cpu_hours_per_team=12.0,
        maximum_wall_clock_hours_per_team=18.0,
    )


def registration(
    candidate_id: str = "candidate-01",
    *,
    team_id: str = "team-01",
    timestamp: str = "2026-07-15T10:01:00Z",
) -> bytes:
    return research.build_trial_registration(
        timestamp_utc=timestamp,
        team_id=team_id,
        family_id="cross-sectional-carry",
        candidate_id=candidate_id,
        strategy_sha256=SHA_A,
        source_bundle_sha256=SHA_B,
        risk_config_sha256=SHA_C,
        config_sha256=SHA_D,
        parameters={"lookback": 30, "risk": {"brake": 0.12}},
        seed=20260715,
        thesis="Past-only carry dispersion should survive conservative execution costs.",
        falsifier="Reject if stitched walk-forward Sharpe is non-positive.",
    )


def result(
    registration_bytes: bytes,
    candidate_id: str = "candidate-01",
    *,
    team_id: str = "team-01",
    timestamp: str = "2026-07-15T10:02:00Z",
    cpu_hours: float = 1.25,
    wall_hours: float = 2.0,
    status: str = "completed",
) -> bytes:
    return research.build_trial_result(
        timestamp_utc=timestamp,
        team_id=team_id,
        family_id="cross-sectional-carry",
        candidate_id=candidate_id,
        registration_sha256=hashlib.sha256(registration_bytes).hexdigest(),
        status=status,
        failure_reason=None if status == "completed" else "worker stopped",
        artifact_hashes={"metrics.json": SHA_A} if status == "completed" else {},
        metrics_summary={"is": {"net_sharpe": 0.91}} if status == "completed" else {},
        cpu_hours=cpu_hours,
        wall_clock_hours=wall_hours,
    )


def genesis(policy: research.ResearchPolicy) -> bytes:
    return research.plan_genesis(
        timestamp_utc="2026-07-15T10:00:00Z", policy=policy
    ).replacement_journal_bytes


def append_registration(
    journal: bytes,
    ledger: bytes,
    event: bytes,
    policy: research.ResearchPolicy,
) -> tuple[bytes, bytes]:
    plan = research.plan_registration_append(journal, event, ledger, policy=policy)
    assert plan.expected_journal_size == len(journal)
    assert plan.expected_journal_sha256 == hashlib.sha256(journal).hexdigest()
    assert plan.expected_team_ledger_sha256 == hashlib.sha256(ledger).hexdigest()
    assert plan.team_ledger_append_bytes == event
    assert plan.replacement_team_ledger_bytes is not None
    return plan.replacement_journal_bytes, plan.replacement_team_ledger_bytes


def test_complete_journal_replay_and_exact_ledger_projection(
    policy: research.ResearchPolicy,
) -> None:
    journal = genesis(policy)
    ledger = b""
    registered = registration()
    journal, ledger = append_registration(journal, ledger, registered, policy)
    completed = result(registered)
    plan = research.plan_result_append(journal, completed, ledger, policy=policy)
    journal = plan.replacement_journal_bytes
    assert plan.replacement_team_ledger_bytes is not None
    ledger = plan.replacement_team_ledger_bytes

    state = research.validate_journal_bytes(journal, policy)
    team = state.teams["team-01"]
    assert len(state.records) == 3
    assert state.head_sha256 == plan.new_head_sha256
    assert team.material_trial_count == 1
    assert team.cpu_hours == 1.25
    assert team.wall_clock_hours == 2.0
    assert team.pending_candidate_ids == ()
    assert team.results["candidate-01"]["status"] == "completed"
    assert research.expected_team_ledger_bytes(state, "team-01") == registered + completed
    research.validate_team_ledger_bytes(ledger, state, "team-01")
    research.validate_team_ledger_bytes(b"", state, "team-02")


def test_journal_first_recovery_accepts_only_whole_record_prefixes(
    policy: research.ResearchPolicy,
) -> None:
    registered = registration()
    plan = research.plan_registration_append(genesis(policy), registered, b"", policy=policy)
    state = research.validate_journal_bytes(plan.replacement_journal_bytes, policy)

    recovery = research.plan_team_ledger_projection(b"", state, "team-01")
    assert recovery.append_bytes == registered
    assert recovery.replacement_ledger_bytes == registered
    assert recovery.journal_head_sha256 == state.head_sha256
    with pytest.raises(
        research.ResearchAccountingError, match="complete journal-authorized prefix"
    ):
        research.plan_team_ledger_projection(registered[:-1], state, "team-01")
    with pytest.raises(
        research.ResearchAccountingError, match="complete journal-authorized prefix"
    ):
        research.plan_team_ledger_projection(
            registered.replace(b"carry", b"curry"), state, "team-01"
        )


def test_noncanonical_and_malformed_team_events_fail_closed() -> None:
    canonical = registration()
    payload = json.loads(canonical)
    pretty = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(research.ResearchAccountingError, match="one bounded|not canonically"):
        research.validate_trial_registration_bytes(pretty)
    with pytest.raises(research.ResearchAccountingError, match="newline-terminated"):
        research.validate_trial_registration_bytes(canonical[:-1])
    duplicate = b'{"a":1,"a":1}\n'
    with pytest.raises(research.ResearchAccountingError, match="duplicate JSON key"):
        research.validate_trial_registration_bytes(duplicate)
    with pytest.raises(research.ResearchAccountingError, match="non-finite"):
        research.validate_trial_registration_bytes(b'{"x":NaN}\n')


def test_registration_binds_all_required_research_inputs() -> None:
    event = research.validate_trial_registration_bytes(registration())
    assert event["strategy_sha256"] == SHA_A
    assert event["source_bundle_sha256"] == SHA_B
    assert event["risk_config_sha256"] == SHA_C
    assert event["config_sha256"] == SHA_D
    assert event["parameters"]["lookback"] == 30
    assert event["seed"] == 20260715
    assert event["thesis"]
    assert event["falsifier"]


def test_result_before_registration_duplicate_and_replay_are_rejected(
    policy: research.ResearchPolicy,
) -> None:
    registered = registration()
    completed = result(registered)
    journal = genesis(policy)
    with pytest.raises(research.ResearchAccountingError, match="no prior registration"):
        research.plan_result_append(journal, completed, b"", policy=policy)

    journal, ledger = append_registration(journal, b"", registered, policy)
    with pytest.raises(research.ResearchAccountingError, match="already registered"):
        research.plan_registration_append(journal, registered, ledger, policy=policy)

    first_result = research.plan_result_append(journal, completed, ledger, policy=policy)
    assert first_result.replacement_team_ledger_bytes is not None
    with pytest.raises(research.ResearchAccountingError, match="replay"):
        research.plan_result_append(
            first_result.replacement_journal_bytes,
            completed,
            first_result.replacement_team_ledger_bytes,
            policy=policy,
        )


def test_result_must_bind_exact_registration_and_identity(
    policy: research.ResearchPolicy,
) -> None:
    registered = registration()
    journal, ledger = append_registration(genesis(policy), b"", registered, policy)
    wrong_hash_event = json.loads(result(registered))
    wrong_hash_event["registration_sha256"] = SHA_D
    wrong_hash = research.canonical_json_line(wrong_hash_event)
    with pytest.raises(research.ResearchAccountingError, match="exact registration"):
        research.plan_result_append(journal, wrong_hash, ledger, policy=policy)

    wrong_family_event = json.loads(result(registered))
    wrong_family_event["family_id"] = "different-family"
    wrong_family = research.canonical_json_line(wrong_family_event)
    with pytest.raises(research.ResearchAccountingError, match="family differs"):
        research.plan_result_append(journal, wrong_family, ledger, policy=policy)


def test_trial_and_resource_budgets_are_hard_limits() -> None:
    one_trial_policy = research.ResearchPolicy(
        tournament_id="top40-v2",
        team_ids=("team-01",),
        maximum_material_configurations_per_team=1,
        maximum_cpu_hours_per_team=12.0,
        maximum_wall_clock_hours_per_team=18.0,
    )
    first = registration()
    journal, ledger = append_registration(genesis(one_trial_policy), b"", first, one_trial_policy)
    with pytest.raises(research.ResearchAccountingError, match="material-trial budget"):
        research.plan_registration_append(
            journal, registration("candidate-02"), ledger, policy=one_trial_policy
        )

    over_cpu = result(first, cpu_hours=12.0001, wall_hours=2.0)
    with pytest.raises(research.ResearchAccountingError, match="CPU-hour budget"):
        research.plan_result_append(journal, over_cpu, ledger, policy=one_trial_policy)
    over_wall = result(first, cpu_hours=2.0, wall_hours=18.0001)
    with pytest.raises(research.ResearchAccountingError, match="wall-clock budget"):
        research.plan_result_append(journal, over_wall, ledger, policy=one_trial_policy)


def test_configured_eighty_trial_limit_is_inclusive(
    policy: research.ResearchPolicy,
) -> None:
    journal = genesis(policy)
    ledger = b""
    for number in range(1, 81):
        event = registration(f"candidate-{number:02d}")
        journal, ledger = append_registration(journal, ledger, event, policy)
    state = research.validate_journal_bytes(journal, policy)
    assert state.teams["team-01"].material_trial_count == 80
    with pytest.raises(research.ResearchAccountingError, match="material-trial budget"):
        research.plan_registration_append(
            journal, registration("candidate-81"), ledger, policy=policy
        )


def test_exact_limits_and_failed_attempts_consume_accounting(
    policy: research.ResearchPolicy,
) -> None:
    registered = registration()
    journal, ledger = append_registration(genesis(policy), b"", registered, policy)
    failed = result(
        registered,
        cpu_hours=12.0,
        wall_hours=18.0,
        status="interrupted",
    )
    plan = research.plan_result_append(journal, failed, ledger, policy=policy)
    state = research.validate_journal_bytes(plan.replacement_journal_bytes, policy)
    assert state.teams["team-01"].cpu_hours == 12.0
    assert state.teams["team-01"].wall_clock_hours == 18.0
    assert state.teams["team-01"].results["candidate-01"]["status"] == "interrupted"


def test_event_timestamps_cannot_move_behind_journal_head(
    policy: research.ResearchPolicy,
) -> None:
    earlier = registration(timestamp="2026-07-15T09:59:59Z")
    with pytest.raises(research.ResearchAccountingError, match="precedes journal head"):
        research.plan_registration_append(genesis(policy), earlier, b"", policy=policy)


def test_journal_rejects_noncanonical_encoding_hash_break_and_bad_sequence(
    policy: research.ResearchPolicy,
) -> None:
    journal = genesis(policy)
    record = json.loads(journal)
    pretty = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(
        research.ResearchAccountingError, match="one bounded|not canonically|malformed JSON"
    ):
        research.validate_journal_bytes(pretty, policy)

    tampered = journal.replace(b"top40-v2", b"top40-v3")
    with pytest.raises(research.ResearchAccountingError, match="hash chain breaks"):
        research.validate_journal_bytes(tampered, policy)

    registered = registration()
    plan = research.plan_registration_append(journal, registered, b"", policy=policy)
    lines = plan.replacement_journal_bytes.splitlines(keepends=True)
    second = json.loads(lines[1])
    second["sequence"] = 7
    core = {key: value for key, value in second.items() if key != "record_sha256"}
    second["record_sha256"] = hashlib.sha256(research.canonical_json_bytes(core)).hexdigest()
    bad_sequence = lines[0] + research.canonical_json_line(second)
    with pytest.raises(research.ResearchAccountingError, match="sequence is not contiguous"):
        research.validate_journal_bytes(bad_sequence, policy)


def test_journal_rejects_cumulative_accounting_tampering_even_when_rehashed(
    policy: research.ResearchPolicy,
) -> None:
    plan = research.plan_registration_append(genesis(policy), registration(), b"", policy=policy)
    lines = plan.replacement_journal_bytes.splitlines(keepends=True)
    second = json.loads(lines[1])
    second["payload"]["cumulative_material_trial_count"] = 2
    core = {key: value for key, value in second.items() if key != "record_sha256"}
    second["record_sha256"] = hashlib.sha256(research.canonical_json_bytes(core)).hexdigest()
    tampered = lines[0] + research.canonical_json_line(second)
    with pytest.raises(research.ResearchAccountingError, match="cumulative material-trial"):
        research.validate_journal_bytes(tampered, policy)


def test_divergent_ledger_blocks_new_plans(policy: research.ResearchPolicy) -> None:
    registered = registration()
    plan = research.plan_registration_append(genesis(policy), registered, b"", policy=policy)
    with pytest.raises(research.ResearchAccountingError, match="diverges"):
        research.plan_result_append(
            plan.replacement_journal_bytes,
            result(registered),
            b'{"invented":true}\n',
            policy=policy,
        )


def test_paths_reject_symlinks_and_validate_exact_files(
    tmp_path: Path, policy: research.ResearchPolicy
) -> None:
    journal_path = tmp_path / "journal.jsonl"
    journal_path.write_bytes(genesis(policy))
    state = research.validate_journal_path(journal_path, policy)
    ledger_path = tmp_path / "team-01.jsonl"
    ledger_path.write_bytes(b"")
    research.validate_team_ledger_path(ledger_path, state, "team-01")

    link = tmp_path / "journal-link.jsonl"
    link.symlink_to(journal_path)
    with pytest.raises(research.ResearchAccountingError, match="safe regular file"):
        research.validate_journal_path(link, policy)


def test_invalid_results_and_policy_values_are_rejected() -> None:
    with pytest.raises(research.ResearchAccountingError, match="positive integer"):
        research.ResearchPolicy("top40-v2", ("team-01",), True, 12.0, 18.0)
    with pytest.raises(research.ResearchAccountingError, match="non-empty unique"):
        research.ResearchPolicy("top40-v2", ("team-01", "team-01"), 80, 12.0, 18.0)

    registered = registration()
    completed = json.loads(result(registered))
    completed["artifact_hashes"] = {}
    with pytest.raises(research.ResearchAccountingError, match="at least one artifact"):
        research.validate_trial_result_bytes(research.canonical_json_line(completed))
    completed = json.loads(result(registered))
    completed["cpu_hours"] = -1.0
    with pytest.raises(research.ResearchAccountingError, match="finite non-negative"):
        research.validate_trial_result_bytes(research.canonical_json_line(completed))
    completed = json.loads(result(registered))
    completed["failure_reason"] = "unexpected"
    with pytest.raises(research.ResearchAccountingError, match="cannot have"):
        research.validate_trial_result_bytes(research.canonical_json_line(completed))


def test_genesis_is_policy_bound_and_plan_preconditions_are_complete(
    policy: research.ResearchPolicy,
) -> None:
    plan = research.plan_genesis(timestamp_utc="2026-07-15T10:00:00Z", policy=policy)
    assert plan.expected_journal_size == 0
    assert plan.expected_journal_sha256 == hashlib.sha256(b"").hexdigest()
    assert plan.expected_head_sha256 == research.ZERO_SHA256
    assert plan.replacement_team_ledger_bytes is None

    different = dataclasses.replace(policy, maximum_material_configurations_per_team=79)
    with pytest.raises(research.ResearchAccountingError, match="differs from policy"):
        research.validate_journal_bytes(plan.replacement_journal_bytes, different)
