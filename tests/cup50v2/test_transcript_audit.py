"""The transcript audit.

Prior editions policed blindness with a canary file and an access-time tripwire, both of which
detect after the fact and neither of which names what was read. A research agent writes a complete
log of every file it opened, so the log is the better record -- and it is one the organizer already
has.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_MODULE_PATH = Path("scripts/cup50v2_transcript_audit.py")
_SPEC = importlib.util.spec_from_file_location("cup50v2_transcript_audit", _MODULE_PATH)
_AUDIT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_AUDIT)
FINDING_CODE, audit_team = _AUDIT.FINDING_CODE, _AUDIT.audit_team

OWN = "/home/roberto/cup50v2-teams/team-03"


def _transcript(tmp_path: Path, *entries: dict) -> Path:
    root = tmp_path / "session"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "agent.jsonl"
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")
    return root


def _read(path: str) -> dict:
    return {"type": "tool_use", "name": "Read", "input": {"file_path": path}}


def test_an_honest_session_is_clean(tmp_path: Path) -> None:
    root = _transcript(
        tmp_path,
        _read(f"{OWN}/strategy.py"),
        _read("src/crypto_trade/cup50v2/toolkit.py"),
        {"type": "tool_use", "name": "Bash", "input": {"command": "uv run pytest"}},
    )
    report = audit_team([root], team_id="team-03", own_root=OWN)
    assert report["status"] == "clean"
    assert report["findings"] == []


def test_reading_an_earlier_edition_is_a_finding(tmp_path: Path) -> None:
    root = _transcript(tmp_path, _read("tournament/cup50/teams/team-02/strategy.py"))
    report = audit_team([root], team_id="team-03", own_root=OWN)
    assert report["status"] == "finding"
    assert report["findings"][0]["code"] == FINDING_CODE
    assert "cup50" in report["findings"][0]["matched"]


def test_reading_the_sealed_side_is_a_finding(tmp_path: Path) -> None:
    root = _transcript(tmp_path, _read("data/cup50v2/sealed/bars.parquet"))
    assert audit_team([root], team_id="team-03", own_root=OWN)["status"] == "finding"


def test_reading_another_teams_workspace_is_a_finding(tmp_path: Path) -> None:
    root = _transcript(tmp_path, _read("/home/roberto/cup50v2-teams/team-07/strategy.py"))
    report = audit_team([root], team_id="team-03", own_root=OWN)
    assert report["status"] == "finding"
    assert "team-07" in report["findings"][0]["matched"]


def test_this_tournaments_own_surfaces_are_not_findings(tmp_path: Path) -> None:
    """The audit must not fire on the toolkit every team is told to import."""
    root = _transcript(
        tmp_path,
        _read("src/crypto_trade/cup50v2/protocol.py"),
        _read("TOURNAMENT-CHARTER-CUP50-V2.md"),
        _read("tournament/cup50v2/seeds/team-03/MANDATE.md"),
        {"type": "text", "text": "from crypto_trade.cup50v2 import toolkit"},
    )
    assert audit_team([root], team_id="team-03", own_root=OWN)["status"] == "clean"


def test_a_grep_hidden_in_a_bash_command_is_found(tmp_path: Path) -> None:
    """The path need not be a Read: a shell command carries it just as well."""
    root = _transcript(
        tmp_path,
        {
            "type": "tool_use",
            "name": "Bash",
            "input": {"command": "cat ../../crypto-trade/reports-cup50v2/leaderboard.json"},
        },
    )
    assert audit_team([root], team_id="team-03", own_root=OWN)["status"] == "finding"


def test_an_unreadable_line_is_reported_rather_than_skipped(tmp_path: Path) -> None:
    root = tmp_path / "session"
    root.mkdir()
    (root / "agent.jsonl").write_text('{"ok": 1}\nnot-json\n')
    report = audit_team([root], team_id="team-03", own_root=OWN)
    assert any(item["code"] == "transcript_unreadable" for item in report["findings"])
