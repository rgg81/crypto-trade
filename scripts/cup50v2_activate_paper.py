#!/usr/bin/env python
"""Create the frozen authority record for one CUP-50 v2 paper desk.

Run once per desk, after release and before the first tick. Everything a desk needs to be exactly
one lane at exactly one centre is written here and never again: which lane, which candidate, which
centre, which release it descends from, and the digest of the source bundle it replays. After this
the desk is fail-closed -- any drift in those bytes stops it rather than silently changing what is
being measured.

Nothing here chooses a desk's lane. The lane comes from the released leaderboard, which was itself
produced under a qualification bar and a winner rule frozen before the sealed window opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from crypto_trade.cup50v2.paper import _canonical
from crypto_trade.cup50v2.trials import source_bundle_digest
from crypto_trade.cup50v2_desk.authority import Desk, repository_root

DESK_SCHEMA_VERSION = 1


def _utc(value: str) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
    if stamp != stamp.floor("8h"):
        raise ValueError(f"launch must be on the canonical 8h grid, got {stamp.isoformat()}")
    return stamp


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument(
        "--desk-id", required=True, help="winner | runner-up-1 | runner-up-2 | ensemble-eq3"
    )
    parser.add_argument("--team-id", required=True, help="the lane this desk replays")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--launch", required=True, help="first boundary, ISO-8601 UTC, 8h grid")
    parser.add_argument(
        "--kind",
        choices=("lane", "ensemble"),
        default="lane",
        help="ensemble desks have no nomination and are verified against their finalists",
    )
    arguments = parser.parse_args()

    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    launch = _utc(arguments.launch)
    released = root / "reports-cup50v2" / "leaderboard.json"
    release = json.loads(released.read_text())
    bundle = root / "tournament" / "cup50v2" / "teams" / arguments.team_id
    bundle_digest = source_bundle_digest(bundle)

    if arguments.kind == "lane":
        ranked = {str(entry.get("team_id")) for entry in release.get("entries", [])}
        if arguments.team_id not in ranked:
            raise SystemExit(
                f"release does not rank {arguments.team_id}; refusing to bind a desk to it"
            )
        nomination_path = (
            root / "tournament" / "cup50v2" / "nominations" / f"{arguments.team_id}.json"
        )
        nomination = json.loads(nomination_path.read_text())
        if bundle_digest != nomination["source_bundle_sha256"]:
            raise SystemExit(
                "the repository copy of this lane's bundle is not the one it nominated; "
                f"{bundle_digest} != {nomination['source_bundle_sha256']}"
            )
        centre = {str(k): float(v) for k, v in nomination["centre"].items()}
        nomination_digest = nomination["freeze_sha256"]
    else:
        # An ensemble has no nomination. Its identity is the manifest of finalists it is defined
        # over, and verify_lineage checks those against the release on every tick.
        manifest = json.loads((bundle / "finalists.json").read_text())
        members = [str(m["team_id"]) for m in manifest["finalists"]]
        eligible = [
            str(e["team_id"])
            for e in release.get("entries", [])
            if e.get("eligible") and e.get("valid")
        ]
        if members != eligible[:3]:
            raise SystemExit(
                f"ensemble members {members} are not the release's "
                f"top three eligible {eligible[:3]}"
            )
        centre = {}
        nomination_digest = hashlib.sha256(
            (bundle / "finalists.json").read_bytes()
        ).hexdigest()

    paper = root / "paper-cup50v2" / arguments.desk_id
    paper.mkdir(parents=True, exist_ok=True)

    # The centre is copied from the nomination, never typed. verify_lineage compares the two on
    # every tick, so a hand-edited desk.json stops the desk instead of quietly replaying a
    # candidate the tournament never ranked.
    desk_record = {
        "schema_version": DESK_SCHEMA_VERSION,
        "desk_id": arguments.desk_id,
        "team_id": arguments.team_id,
        "candidate_id": arguments.candidate_id,
        "centre": centre,
        "nomination_sha256": nomination_digest,
        "kind": arguments.kind,
    }
    Desk(**{k: v for k, v in desk_record.items() if k != "schema_version"})  # validate before write
    (paper / "desk.json").write_text(json.dumps(desk_record, indent=2, sort_keys=True) + "\n")

    body = {
        "schema_version": 1,
        "namespace": f"cup50v2-{arguments.desk_id}-paper-authority",
        "desk_id": arguments.desk_id,
        "team_id": arguments.team_id,
        "candidate_id": arguments.candidate_id,
        "release_sha256": hashlib.sha256(released.read_bytes()).hexdigest(),
        "winner_bundle_sha256": bundle_digest,
        "nomination_sha256": nomination_digest,
        "launch_time": launch.isoformat(),
        "public_data_only": True,
        "exact_replay": True,
        "git_commit": _git_commit(root),
    }
    body["lineage_sha256"] = hashlib.sha256(_canonical(body)).hexdigest()
    record = {**body, "authority_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    authority_path = paper / "authority.json"
    if authority_path.exists():
        raise SystemExit(f"{authority_path} already exists; a desk is frozen once")
    authority_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "desk_id": arguments.desk_id,
                "team_id": arguments.team_id,
                "lineage_sha256": record["lineage_sha256"],
                "launch": launch.isoformat(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
