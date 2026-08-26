"""The runtime seam, and the live boundary probe that guards every launch."""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import runtime, workspace


@pytest.fixture
def space(tmp_path: Path) -> workspace.Workspace:
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "RULES.md").write_text("rules", encoding="utf-8")
    brief = tmp_path / "TEAM-BRIEF.md"
    brief.write_text("mandate", encoding="utf-8")
    return workspace.materialise(
        tmp_path / "ws",
        phase="discovery",
        kit_source=kit,
        lane_files={"TEAM-BRIEF.md": brief},
        writable=workspace.LANE_WRITABLE,
        network=False,
    )


def _request(space: workspace.Workspace, **overrides) -> runtime.PhaseRequest:
    options = {
        "lane": "team-01",
        "phase": "discovery",
        "prompt": "do the work",
        "workspace": space,
        "forbidden_roots": (),
        "allowed_tools": runtime.RESEARCH_TOOLS,
    }
    options.update(overrides)
    return runtime.PhaseRequest(**options)


def test_the_scripted_runtime_satisfies_the_protocol_the_orchestrator_depends_on(space):
    """The seam is the point: the orchestrator must never name a specific CLI."""

    scripted = runtime.ScriptedRuntime(lambda request: 0)
    assert isinstance(scripted, runtime.AgentRuntime)


def test_a_receipt_records_what_the_phase_produced(space):
    def script(request: runtime.PhaseRequest) -> int:
        (request.workspace.lane / "outbox" / "candidate.py").write_text("w = {}", encoding="utf-8")
        return 0

    receipt = runtime.ScriptedRuntime(script).launch(_request(space))

    assert receipt.succeeded
    assert set(receipt.produced) == {"candidate.py"}
    assert receipt.runtime == "scripted"
    assert receipt.duration_seconds >= 0.0


def test_a_phase_that_raises_is_reported_not_propagated(space):
    """An organizer-side fault must become a recorded receipt, never an exception that unwinds the
    run. V4-R9 charged eighty-six trials to teams because one evaluator error escaped."""

    def script(request: runtime.PhaseRequest) -> int:
        raise ValueError("the evaluator fell over")

    receipt = runtime.ScriptedRuntime(script).launch(_request(space))

    assert not receipt.succeeded
    assert receipt.exit_code == 1
    assert receipt.produced == {}


def test_receipts_are_serialisable_for_the_journal(space):
    receipt = runtime.ScriptedRuntime(lambda request: 0).launch(_request(space))
    payload = receipt.as_dict()

    assert payload["lane"] == "team-01"
    assert payload["phase"] == "discovery"
    assert isinstance(payload["produced"], dict)


# --------------------------------------------------------------------------------------------
# The boundary probe. Both halves must be checked, because either alone calls a broken sandbox
# healthy: one that denies everything starves the lane, one that denies nothing exposes the field.
# --------------------------------------------------------------------------------------------


def _probe_runtime(step1: str, step2: str) -> runtime.ScriptedRuntime:
    def script(request: runtime.PhaseRequest) -> int:
        report = request.workspace.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT
        report.write_text(f"step1: {step1}\nstep2: {step2}\n", encoding="utf-8")
        return 0

    return runtime.ScriptedRuntime(script)


def _run_probe(space: workspace.Workspace, agent_runtime) -> dict[str, bool]:
    return runtime.boundary_probe(
        agent_runtime,
        space,
        lane="team-01",
        inside=space.kit / "RULES.md",
        outside=Path("/home/roberto/crypto-trade/CLAUDE.md"),
        forbidden_roots=["/home/roberto/crypto-trade"],
    )


def test_a_healthy_sandbox_passes_the_probe(space):
    observed = _run_probe(space, _probe_runtime("ALLOWED", "DENIED"))

    assert observed == {runtime.PROBE_ALLOWED: True, runtime.PROBE_DENIED: True}
    runtime.assert_boundary_probe_passed(observed)


def test_the_probe_leaves_nothing_behind_for_the_harvest_to_collect(space):
    """Found by running the real runtime, not by reading the code.

    The first version wrote its report into ``outbox/``, and a live end-to-end check harvested
    ``boundary.txt`` beside a genuine ``candidate.py`` -- an organizer artifact entering
    selection as if a team had submitted it. The probe now writes to its own directory and clears
    up after itself, and the harvest must see only what the lane actually produced.
    """

    _run_probe(space, _probe_runtime("ALLOWED", "DENIED"))
    (space.lane / "outbox" / "candidate.py").write_text("w = {}", encoding="utf-8")

    assert set(workspace.harvest(space, "outbox")) == {"candidate.py"}
    assert not (space.lane / workspace.PROBE_DIRECTORY / runtime.PROBE_REPORT).exists()


def test_a_sandbox_that_denies_nothing_fails_the_probe(space):
    """The observed failure: the deny rule was malformed, so the outside read succeeded."""

    observed = _run_probe(space, _probe_runtime("ALLOWED", "ALLOWED"))

    with pytest.raises(runtime.PhaseLaunchError, match="deny rules are not in force"):
        runtime.assert_boundary_probe_passed(observed)


def test_a_sandbox_that_denies_everything_also_fails_the_probe(space):
    """Checking only the denial would call this healthy; it starves the lane instead."""

    observed = _run_probe(space, _probe_runtime("DENIED", "DENIED"))

    with pytest.raises(runtime.PhaseLaunchError, match="read its own workspace"):
        runtime.assert_boundary_probe_passed(observed)


def test_a_probe_that_writes_no_report_is_a_failure_not_a_pass(space):
    """Absence of evidence must not read as evidence of a boundary."""

    silent = runtime.ScriptedRuntime(lambda request: 0)

    with pytest.raises(runtime.PhaseLaunchError, match="produced no report"):
        _run_probe(space, silent)


def test_the_claude_command_carries_the_flags_isolation_depends_on(space, monkeypatch):
    """``--no-session-persistence`` is load-bearing: a persisted session would carry one lane's
    context into the next launch, which is exactly the blindness the edition rests on."""

    monkeypatch.setattr(runtime.shutil, "which", lambda name: "/usr/bin/claude")
    claude = runtime.ClaudeCodeRuntime()
    request = _request(space, forbidden_roots=("/home/roberto/crypto-trade",))
    settings = space.root.parent / "settings.json"
    settings.write_text("{}", encoding="utf-8")

    command = claude.command(request, settings)

    assert "--no-session-persistence" in command
    assert "--output-format" in command and "json" in command
    assert "Bash" not in command[command.index("--allowedTools") + 1 :]


def test_an_unavailable_runtime_fails_at_construction_not_at_launch(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda name: None)

    with pytest.raises(runtime.PhaseLaunchError, match="not found"):
        runtime.ClaudeCodeRuntime("definitely-not-installed")
