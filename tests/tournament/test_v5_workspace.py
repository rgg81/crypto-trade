"""Materialised workspaces, and the permission-rule shape that silently fails open."""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import runtime, workspace


@pytest.fixture
def sources(tmp_path: Path) -> dict[str, Path]:
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "RULES.md").write_text("the rules", encoding="utf-8")
    (kit / "nested").mkdir()
    (kit / "nested" / "protocol.py").write_text("# protocol", encoding="utf-8")

    lane = tmp_path / "lane-source"
    lane.mkdir()
    (lane / "TEAM-BRIEF.md").write_text("your mandate", encoding="utf-8")
    (lane / "SECRET-PEER-WORK.py").write_text("another team's candidate", encoding="utf-8")
    return {"kit": kit, "lane": lane, "root": tmp_path}


def _materialise(tmp_path: Path, sources: dict[str, Path], **overrides) -> workspace.Workspace:
    options = {
        "phase": "discovery",
        "kit_source": sources["kit"],
        "lane_files": {"TEAM-BRIEF.md": sources["lane"] / "TEAM-BRIEF.md"},
        "writable": workspace.LANE_WRITABLE,
        "network": False,
    }
    options.update(overrides)
    return workspace.materialise(tmp_path / "ws", **options)


def test_a_workspace_contains_only_the_files_that_were_named(tmp_path, sources):
    """The peer's candidate sits beside the brief in the source directory and must not come along.

    This is the whole thesis of the module. A prior edition leaked a file into fifteen lanes because
    it was present and the policy did not name it; here the policy names what is *copied*, so the
    default is exclusion.
    """

    space = _materialise(tmp_path, sources)

    names = {Path(name).name for name in space.manifest}
    assert "TEAM-BRIEF.md" in names
    assert "RULES.md" in names
    assert "SECRET-PEER-WORK.py" not in names
    assert not (space.lane / "SECRET-PEER-WORK.py").exists()


def test_materialising_refuses_a_lane_name_that_climbs_out(tmp_path, sources):
    with pytest.raises(workspace.WorkspaceError, match="traverse upward"):
        _materialise(
            tmp_path, sources, lane_files={"../escape.md": sources["lane"] / "TEAM-BRIEF.md"}
        )


def test_materialising_refuses_a_destination_that_is_not_empty(tmp_path, sources):
    """A restart must not inherit the previous attempt's files."""

    destination = tmp_path / "ws"
    destination.mkdir()
    (destination / "leftover.txt").write_text("from a previous run", encoding="utf-8")
    with pytest.raises(workspace.WorkspaceError, match="not empty"):
        _materialise(tmp_path, sources)


def test_the_exclusion_assertion_actually_flips_when_a_forbidden_file_is_present(tmp_path, sources):
    """A check that cannot fail is not a check.

    Both directions are asserted: a clean workspace passes, and the same call raises the moment the
    forbidden file is genuinely copied in.
    """

    clean = _materialise(tmp_path / "clean", sources)
    workspace.assert_workspace_excludes(clean, ["SECRET-PEER-WORK.py"])

    leaked = _materialise(
        tmp_path / "leaked",
        sources,
        lane_files={
            "TEAM-BRIEF.md": sources["lane"] / "TEAM-BRIEF.md",
            "SECRET-PEER-WORK.py": sources["lane"] / "SECRET-PEER-WORK.py",
        },
    )
    with pytest.raises(workspace.WorkspaceError, match="forbidden files"):
        workspace.assert_workspace_excludes(leaked, ["SECRET-PEER-WORK.py"])


def test_harvest_returns_declared_artifacts_and_refuses_when_one_is_missing(tmp_path, sources):
    space = _materialise(tmp_path, sources)
    (space.lane / "outbox" / "candidate.py").write_text("weights = {}", encoding="utf-8")

    produced = workspace.harvest(space, "outbox", expected=["candidate.py"])
    assert produced == {"candidate.py": b"weights = {}"}

    with pytest.raises(workspace.WorkspaceError, match="did not produce"):
        workspace.harvest(space, "outbox", expected=["candidate.py", "THESIS.md"])


def test_harvest_ignores_anything_below_the_outbox(tmp_path, sources):
    """Only the declared surface is collected, so a stray write cannot become a submission."""

    space = _materialise(tmp_path, sources)
    (space.lane / "outbox" / "candidate.py").write_text("ok", encoding="utf-8")
    nested = space.lane / "outbox" / "scratch"
    nested.mkdir()
    (nested / "draft.py").write_text("not a submission", encoding="utf-8")

    assert set(workspace.harvest(space, "outbox")) == {"candidate.py"}


def test_the_audit_notices_a_reference_to_a_forbidden_root(tmp_path, sources):
    space = _materialise(tmp_path, sources)
    produced = {
        "candidate.py": b"# adapted from /home/roberto/crypto-trade/reports-cup50v2/board.json",
        "clean.py": b"weights = rank(features)",
    }

    findings = workspace.audit_workspace(
        space, produced, forbidden_roots=["/home/roberto/crypto-trade"]
    )
    assert any("forbidden root" in finding for finding in findings)
    assert not any(finding.startswith("clean.py") for finding in findings)


def test_the_audit_does_not_accuse_a_numeric_sequence_of_being_a_path(tmp_path, sources):
    """Found by rehearsing a real lane, not by reading the regex.

    An agent wrote its ladder of lookback horizons as "24/72/168/336" in a genuine RATIONALE.md and
    the audit reported it as an absolute path outside the workspace. A false positive accuses honest
    work of a leak, and an audit nobody trusts gets ignored -- at which point it catches nothing.
    """

    space = _materialise(tmp_path, sources)
    produced = {
        "RATIONALE.md": b"Lookback ladder: 24/72/168/336 hours. Ratio 3/4/5 across regimes.",
        "leak.py": b"# copied from /home/roberto/crypto-trade/reports/board.json",
    }

    findings = workspace.audit_workspace(space, produced, forbidden_roots=[])

    assert not any(finding.startswith("RATIONALE.md") for finding in findings)
    assert any(finding.startswith("leak.py") for finding in findings)


def test_the_evaluator_can_be_confined_to_an_empty_network_namespace(tmp_path, sources):
    """Kernel-enforced, and reserved for the evaluator.

    An agent process cannot be wrapped this way -- it needs the network for its own model API, and
    an empty namespace hangs it rather than isolating it. The evaluator only reads a local snapshot
    and computes, so confining it costs nothing.
    """

    confined = workspace.network_isolated_command(["evaluate", "--candidate", "x"], network=False)
    unconfined = workspace.network_isolated_command(["evaluate", "--candidate", "x"], network=True)

    assert confined[:1] == ["unshare"] and "--net" in confined
    assert unconfined == ["evaluate", "--candidate", "x"]


def test_the_clean_environment_drops_whatever_was_not_named(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-propagate")
    monkeypatch.setenv("PATH", "/usr/bin")

    environment = workspace.clean_environment()

    assert "ANTHROPIC_API_KEY" not in environment
    assert environment["PATH"] == "/usr/bin"
    assert environment["OMP_NUM_THREADS"] == "1"


# --------------------------------------------------------------------------------------------
# The permission-rule shape. Measured on this host: the single-slash form denies nothing at all.
# --------------------------------------------------------------------------------------------


def test_a_single_slash_path_rule_is_rejected_because_it_denies_nothing():
    """The defect this guard exists for was observed, not theorised.

    A probe on this host wrote ``Read(/tmp/.../**)`` into a live settings file, launched an agent
    against it, and watched the agent read the file the rule named -- no warning, no error, no
    denial. The doubled-slash form denied the same read. A rule that looks correct and does nothing
    is the failure mode this repository loses runs to, so the malformed shape must not survive
    construction.
    """

    with pytest.raises(runtime.PhaseLaunchError, match="matches nothing"):
        runtime.assert_deny_rules_are_well_formed(["Read(/home/roberto/crypto-trade/**)"])

    runtime.assert_deny_rules_are_well_formed(["Read(//home/roberto/crypto-trade/**)"])


def test_generated_deny_rules_use_the_form_that_is_enforced(tmp_path):
    rules = runtime.deny_rules([str(tmp_path / "secret")], network=False)

    assert all(rule.startswith("Read(//") for rule in rules if rule.startswith("Read("))
    assert "Bash" in rules
    assert set(runtime.NETWORK_TOOLS).issubset(rules)


def test_a_scouting_phase_keeps_the_network_tools():
    rules = runtime.deny_rules([], network=True)

    assert not set(runtime.NETWORK_TOOLS) & set(rules)
    assert "Bash" in rules
