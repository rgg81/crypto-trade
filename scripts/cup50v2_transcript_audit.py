#!/usr/bin/env python3
"""Audit a team agent's session transcript for reads it was not entitled to make.

Every prior edition's blindness rested on detection after the fact -- a canary file, an access-time
tripwire -- or on nothing at all. But a research agent writes a complete log of every file it opened
and every command it ran, and that log is a better record than any tripwire: it names the path, the
tool and the moment.

This is a gate, not a diagnostic. A hit is an integrity finding with a named code, confirmed
independently by the organizer before it disqualifies anyone, exactly as every other integrity code
in this lineage works. Read-only: it never edits a transcript.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

PROHIBITED = (
    re.compile(r"(?:cup|top)\d++(?!v2)"),
    re.compile(r"data/cup50v2/(?:sealed|is|acquisition)"),
    re.compile(r"tournament/cup50v2/private"),
    re.compile(r"reports-cup50v2"),
    re.compile(r"paper-cup50v2"),
    re.compile(r"briefs-|diary-|analysis/"),
    re.compile(r"ORCHESTRATOR_BRIEF"),
    re.compile(r"TOURNAMENT-CHARTER-(?!CUP50-V2)"),
)
FINDING_CODE = "transcript_prohibited_read"


def _texts(record: object) -> Iterator[str]:
    """Yield every string a record carries, without assuming a transcript schema."""
    if isinstance(record, str):
        yield record
    elif isinstance(record, dict):
        for value in record.values():
            yield from _texts(value)
    elif isinstance(record, list):
        for value in record:
            yield from _texts(value)


def audit_transcript(path: Path, *, team_id: str, own_root: str) -> list[dict[str, object]]:
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
            for text in _texts(record):
                for pattern in PROHIBITED:
                    match = pattern.search(text)
                    if match is None:
                        continue
                    findings.append(
                        {
                            "code": FINDING_CODE,
                            "team_id": team_id,
                            "line": number,
                            "matched": match.group(0),
                            "excerpt": text[max(0, match.start() - 60) : match.end() + 60],
                            "path": str(path),
                        }
                    )
            for text in _texts(record):
                other = re.search(r"cup50v2-teams/(team-\d+)", text)
                if other and other.group(1) != team_id and own_root not in text:
                    findings.append(
                        {
                            "code": FINDING_CODE,
                            "team_id": team_id,
                            "line": number,
                            "matched": other.group(0),
                            "excerpt": text[max(0, other.start() - 60) : other.end() + 60],
                            "path": str(path),
                        }
                    )
    return findings


def audit_team(roots: Sequence[Path], *, team_id: str, own_root: str) -> dict[str, object]:
    transcripts = sorted(
        {path for root in roots for path in Path(root).rglob("*.jsonl") if path.is_file()}
    )
    findings: list[dict[str, object]] = []
    for transcript in transcripts:
        findings.extend(audit_transcript(transcript, team_id=team_id, own_root=own_root))
    return {
        "schema_version": 1,
        "namespace": "cup50v2",
        "team_id": team_id,
        "transcripts_audited": [str(path) for path in transcripts],
        "status": "clean" if not findings else "finding",
        "findings": findings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--own-root", required=True, help="the team's own workspace path")
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
