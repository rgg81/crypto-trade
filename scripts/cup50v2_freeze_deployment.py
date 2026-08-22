#!/usr/bin/env python
"""Bind every byte a desk depends on, once, before its first tick.

verify_deployment re-checks these digests on every tick for six months. What belongs here is
everything whose change would alter what the desk does: the evaluator, the desk engine, the frozen
strategy bundle, the tournament config, and the release the desk descends from. What does not
belong is anything the desk writes -- a manifest that bound its own output would fail on the first
tick that produced any.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from crypto_trade.cup50v2_desk.authority import (  # noqa: E402
    build_deployment_manifest,
    load_desk,
    repository_root,
)

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")


def artifacts(root: Path, team_id: str) -> list[Path]:
    found: list[Path] = []
    found += sorted((root / "src" / "crypto_trade" / "cup50v2").glob("*.py"))
    found += sorted((root / "src" / "crypto_trade" / "cup50v2_desk").glob("*.py"))
    found += sorted(
        path for path in (root / "tournament" / "cup50v2" / "teams" / team_id).rglob("*")
        if path.is_file()
    )
    found += [
        root / "tournament" / "cup50v2" / "config.toml",
        root / "tournament" / "cup50v2" / "risk-policy.json",
        root / "tournament" / "cup50v2" / "historical-asset-classification.json",
        root / "tournament" / "cup50v2" / "historical-unavailability.json",
        root / "reports-cup50v2" / "leaderboard.json",
        root / "reports-cup50v2" / "release.json",
        root / "run_cup50v2_paper.py",
    ]
    return [path for path in found if path.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--desk", action="append", default=None)
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    for desk_id in tuple(arguments.desk) if arguments.desk else DESKS:
        desk = load_desk(desk_id, root)
        record = build_deployment_manifest(
            desk, artifacts(root, desk.team_id), root=root, git_commit=commit
        )
        print(f"{desk_id:<14} {len(record['artifacts']):>3} artifacts  "
              f"lineage {record['lineage_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
