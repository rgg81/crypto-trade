#!/usr/bin/env python3
"""Audit a lane's session transcript for accesses it was not entitled to make.

Every prior edition's blindness rested on detection after the fact -- a canary file, an access-time
tripwire -- or on nothing at all. A research agent writes a complete log of every file it opened and
every command it ran, and that log is a better record than any tripwire: it names the tool, the
path, and the moment.

Two things this audit had to learn the hard way, both recorded because the mistakes are the useful
part. It must read *this lane's* transcript and not the organizer's, which contains every lane's
material by construction. And it must read what the agent *tried to reach* -- tool-use inputs --
rather than every string in the record, because a brief that lists the forbidden paths by name is
not an attempt to open them, and a gate that cannot tell those apart flags the lanes for reading
their own instructions.

This is a gate, not a diagnostic. A hit is an integrity finding with a named code, confirmed
independently by the organizer before it disqualifies anyone. Read-only: it never edits a
transcript.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

# This edition's own checkout is named for the tournament it hosts, so the repository path contains
# the token the audit hunts for. Same exemption as the clean-room scan: one exact literal.
OWN_WORKTREE = "quant-portfolio-blind-top50-v2"

PROHIBITED = (
    re.compile(r"\b(?:cup|top)\d++(?!v2)"),
    re.compile(r"data/cup50v2/(?:sealed|is|acquisition)"),
    re.compile(r"tournament/cup50v2/private"),
    re.compile(r"reports-cup50v2"),
    re.compile(r"paper-cup50v2"),
    re.compile(r"briefs-|diary-|analysis/"),
    re.compile(r"ORCHESTRATOR_BRIEF"),
)
FINDING_CODE = "transcript_prohibited_read"
TEAM_MARKER = re.compile(r"You are (?:resuming )?(team-\d{2})")

# The tools that actually reach for something, and the fields naming what they reach for.
ACCESS_TOOLS = {
    "Read": ("file_path",),
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "NotebookEdit": ("notebook_path",),
    "Glob": ("path", "pattern"),
    "Grep": ("path", "pattern", "glob"),
    "Bash": ("command",),
}


def access_attempts(record: object) -> Iterator[tuple[str, str]]:
    """Yield only what this agent tried to reach: tool name and the argument naming the target."""
    if not isinstance(record, dict):
        return
    message = record.get("message")
    blocks = message.get("content") if isinstance(message, dict) else None
    if not isinstance(blocks, list):
        return
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        fields = ACCESS_TOOLS.get(str(block.get("name")))
        payload = block.get("input")
        if not fields or not isinstance(payload, dict):
            continue
        for field in fields:
            value = payload.get(field)
            if isinstance(value, str) and value:
                yield str(block.get("name")), value


def discover_transcripts(roots: Sequence[Path], team_id: str) -> list[Path]:
    """Transcripts belonging to this lane alone, identified by the dispatch that opens them."""
    matched: list[Path] = []
    for root in roots:
        for path in Path(root).rglob("subagents/*.jsonl"):
            if not path.is_file():
                continue
            try:
                head = path.read_text(errors="ignore")[:8000]
            except OSError:
                continue
            if set(TEAM_MARKER.findall(head)) == {team_id}:
                matched.append(path)
    return sorted(set(matched))


def audit_transcript(path: Path, *, team_id: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    with path.open() as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                findings.append(
                    {"code": "transcript_unreadable", "line": number, "path": str(path)}
                )
                continue
            for tool, raw in access_attempts(record):
                text = raw.replace(OWN_WORKTREE, "<this-worktree>")
                hits = [m.group(0) for m in (p.search(text) for p in PROHIBITED) if m]
                other = re.search(r"cup50v2-teams/(team-\d+)", text)
                if other and other.group(1) != team_id:
                    hits.append(other.group(0))
                for hit in hits:
                    findings.append(
                        {
                            "code": FINDING_CODE,
                            "team_id": team_id,
                            "line": number,
                            "tool": tool,
                            "matched": hit,
                            "attempt": raw[:300],
                            "path": str(path),
                        }
                    )
    return findings


def audit_team(roots: Sequence[Path], *, team_id: str, own_root: str) -> dict[str, object]:
    transcripts = discover_transcripts(roots, team_id)
    body: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "team_id": team_id,
        "own_root": own_root,
        "transcripts_audited": [str(path) for path in transcripts],
    }
    if not transcripts:
        return {
            **body,
            "status": "no-transcript",
            "findings": [
                {
                    "code": "transcript_missing",
                    "team_id": team_id,
                    "detail": "no subagent transcript identifies this lane",
                }
            ],
        }
    findings: list[dict[str, object]] = []
    for transcript in transcripts:
        findings.extend(audit_transcript(transcript, team_id=team_id))
    return {**body, "status": "clean" if not findings else "finding", "findings": findings}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--own-root", required=True, help="the lane's own workspace path")
    parser.add_argument("--transcript-root", action="append", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)

    report = audit_team(
        arguments.transcript_root, team_id=arguments.team_id, own_root=arguments.own_root
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.write_text(payload)
    print(payload, end="")
    # A finding is reported, never acted on here: the organizer confirms it independently.
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
