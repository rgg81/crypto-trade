"""One phase, one lane: the ordering, the lease, and idempotent restart."""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import broker, isolation, journal, runtime, workspace

TOURNAMENT_ROOT = "/srv/tournament"
TEAM = "team-07"
KIT_ROOT = "tournament/top40-v5/team-kit"


@pytest.fixture
def bench(tmp_path: Path):
    """A lane's source material, a journal, and the roots a phase is measured against."""

    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "RULES.md").write_text("submissions go to lane/outbox/", encoding="utf-8")

    lane_source = tmp_path / "lane-source"
    lane_source.mkdir()
    (lane_source / "TEAM-BRIEF.md").write_text("mandate: funding carry", encoding="utf-8")

    peer = tmp_path / "peer"
    peer.mkdir()
    (peer / "PEER-CANDIDATE.py").write_text("another team's work", encoding="utf-8")

    journal_path = tmp_path / "research-journal.jsonl"
    journal.initialize(journal_path)

    return {
        "root": tmp_path,
        "kit": kit,
        "lane_files": {"TEAM-BRIEF.md": lane_source / "TEAM-BRIEF.md"},
        "peer": peer,
        "journal": journal_path,
    }


def _profile() -> isolation.PermissionProfile:
    return isolation.offline_profile(
        TOURNAMENT_ROOT, f"teams/{TEAM}", KIT_ROOT, toolchain_root="/opt/toolchain"
    )


def _healthy_runtime(artifacts: dict[str, str] | None = None) -> runtime.ScriptedRuntime:
    """Passes the boundary probe, then writes the named artifacts."""

    payload = (
        artifacts if artifacts is not None else {"candidate.py": "w = {}", "RATIONALE.md": "x"}
    )

    def script(request: runtime.PhaseRequest) -> int:
        if request.phase == "boundary-probe":
            report = request.workspace.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT
            report.write_text("step1: ALLOWED\nstep2: DENIED\n", encoding="utf-8")
            return 0
        surface = "scouting" if request.phase == isolation.SCOUTING_PHASE else "outbox"
        for name, body in payload.items():
            (request.workspace.lane / surface / name).write_text(body, encoding="utf-8")
        return 0

    return runtime.ScriptedRuntime(script)


def _run(bench, agent_runtime, *, phase="discovery", prompt="do the work", suffix="a"):
    return broker.run_phase(
        agent_runtime,
        _profile(),
        team_id=TEAM,
        phase=phase,
        prompt=prompt,
        workspace_root=bench["root"] / f"ws-{suffix}",
        kit_source=bench["kit"],
        lane_files=bench["lane_files"],
        forbidden_roots=[str(bench["peer"])],
        forbidden_filenames=["PEER-CANDIDATE.py"],
        journal_path=bench["journal"],
        tournament_root=TOURNAMENT_ROOT,
        probe_inside="lane/TEAM-BRIEF.md",
        probe_outside=bench["peer"] / "PEER-CANDIDATE.py",
    )


def test_a_healthy_phase_produces_its_artifacts_and_journals_completion(bench):
    outcome = _run(bench, _healthy_runtime())

    assert outcome.usable
    assert set(outcome.produced) == {"candidate.py", "RATIONALE.md"}
    assert outcome.audit_findings == ()
    broker.assert_required_artifacts(outcome)

    launches = list(journal.iter_events(bench["journal"], "phase_launched"))
    assert [record.payload["status"] for record in launches] == ["started", "completed"]


def test_the_launch_is_journalled_before_the_process_starts(bench):
    """A record written afterwards can only describe what somebody believed happened."""

    def script(request: runtime.PhaseRequest) -> int:
        if request.phase == "boundary-probe":
            report = request.workspace.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT
            report.write_text("step1: ALLOWED\nstep2: DENIED\n", encoding="utf-8")
            return 0
        # A phase that dies mid-run must still have left evidence that it began.
        raise RuntimeError("killed mid-phase")

    outcome = _run(bench, runtime.ScriptedRuntime(script))

    assert not outcome.usable
    statuses = [
        record.payload["status"]
        for record in journal.iter_events(bench["journal"], "phase_launched")
    ]
    assert statuses == ["started", "failed"]


def test_a_phase_will_not_launch_when_the_boundary_probe_fails(bench):
    """The deny rules are not evidence until they have been watched working."""

    def script(request: runtime.PhaseRequest) -> int:
        report = request.workspace.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT
        report.write_text("step1: ALLOWED\nstep2: ALLOWED\n", encoding="utf-8")
        return 0

    with pytest.raises(runtime.PhaseLaunchError, match="not in force"):
        _run(bench, runtime.ScriptedRuntime(script))

    # Nothing was journalled, because nothing was launched.
    assert list(journal.iter_events(bench["journal"], "phase_launched")) == []


def test_a_forbidden_file_in_the_lane_stops_the_phase_before_it_runs(bench):
    with pytest.raises(workspace.WorkspaceError, match="forbidden files"):
        broker.run_phase(
            _healthy_runtime(),
            _profile(),
            team_id=TEAM,
            phase="discovery",
            prompt="do the work",
            workspace_root=bench["root"] / "ws-leak",
            kit_source=bench["kit"],
            lane_files={
                "TEAM-BRIEF.md": bench["lane_files"]["TEAM-BRIEF.md"],
                "PEER-CANDIDATE.py": bench["peer"] / "PEER-CANDIDATE.py",
            },
            forbidden_roots=[str(bench["peer"])],
            forbidden_filenames=["PEER-CANDIDATE.py"],
            journal_path=bench["journal"],
            tournament_root=TOURNAMENT_ROOT,
            probe_inside="lane/TEAM-BRIEF.md",
            probe_outside=bench["peer"] / "PEER-CANDIDATE.py",
        )


def test_an_audit_finding_is_surfaced_without_discarding_the_work(bench):
    """A mechanical string match is evidence of a possible read, not proof of one.

    Throwing away a lane's trial on that basis would be its own kind of error, so the finding is
    recorded for organizer review and the artifacts survive.
    """

    peer = str(bench["peer"])
    agent = _healthy_runtime(
        {"candidate.py": f"# see {peer}/PEER-CANDIDATE.py", "RATIONALE.md": "x"}
    )

    outcome = _run(bench, agent)

    assert outcome.audit_findings
    assert outcome.usable
    assert "candidate.py" in outcome.produced


# -- restart --------------------------------------------------------------------------------


def test_a_completed_phase_is_recognised_and_not_re_run(bench):
    """V4 accumulated nine restarts, and the damage was the re-execution, not the crash."""

    first = _run(bench, _healthy_runtime(), suffix="a")
    assert first.usable and not first.skipped

    second = _run(bench, _healthy_runtime(), suffix="b")
    assert second.skipped
    assert not (bench["root"] / "ws-b").exists()


def test_a_changed_prompt_is_a_different_phase(bench):
    """A changed mandate must not inherit the previous one's completion."""

    _run(bench, _healthy_runtime(), prompt="original mandate", suffix="a")
    repeated = _run(bench, _healthy_runtime(), prompt="revised mandate", suffix="b")

    assert not repeated.skipped
    assert broker.phase_fingerprint(TEAM, "discovery", "a") != broker.phase_fingerprint(
        TEAM, "discovery", "b"
    )


def test_a_failed_phase_is_not_treated_as_completed(bench):
    """Only completion is idempotent. A failure must be retryable."""

    def failing(request: runtime.PhaseRequest) -> int:
        if request.phase == "boundary-probe":
            report = request.workspace.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT
            report.write_text("step1: ALLOWED\nstep2: DENIED\n", encoding="utf-8")
            return 0
        return 1

    _run(bench, runtime.ScriptedRuntime(failing), suffix="a")
    retried = _run(bench, _healthy_runtime(), suffix="b")

    assert not retried.skipped
    assert retried.usable


# -- required artifacts and the lease ----------------------------------------------------------


def test_a_phase_missing_a_required_artifact_is_refused(bench):
    outcome = _run(bench, _healthy_runtime({"candidate.py": "w = {}"}))

    with pytest.raises(broker.BrokerError, match="RATIONALE.md"):
        broker.assert_required_artifacts(outcome)


def test_the_lane_lease_admits_one_holder_at_a_time():
    lease = broker.LaneLease()
    lease.acquire("team-01")

    with pytest.raises(broker.BrokerError, match="already holds"):
        lease.acquire("team-02")

    lease.release("team-01")
    lease.acquire("team-02")
    assert lease.holder == "team-02"


def test_releasing_a_lease_you_do_not_hold_is_refused():
    lease = broker.LaneLease()
    lease.acquire("team-01")

    with pytest.raises(broker.BrokerError, match="does not hold"):
        lease.release("team-02")


def test_the_lease_is_released_when_its_block_exits():
    with broker.LaneLease() as lease:
        lease.acquire("team-01")
    assert lease.holder is None


def test_an_unknown_phase_is_refused(bench):
    with pytest.raises(broker.BrokerError, match="unknown phase"):
        _run(bench, _healthy_runtime(), phase="freestyle")
