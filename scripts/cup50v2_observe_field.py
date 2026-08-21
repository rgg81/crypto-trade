#!/usr/bin/env python
"""Drive the one-shot sealed observation across every nominated point.

The order lanes are read in comes from the frozen field record, which derives it from the signing
key (A6) -- this script never chooses it. Within a lane, points are read in their frozen order.

Every point is a separate `cup50v2 observe point` invocation, so a failure is contained to one
point and the journal is the only state that carries across. On a hard interruption, run
`cup50v2 observe restart` and then this script again: completed points are skipped from the
journal, the interrupted one is resumed, and a candidate failure stays a permanent zero (A8).

Nothing here prints a score. `observe point` returns only {"status": "point-terminal"} and the
evidence goes to the private stage, which is what makes restarting safe rather than a retry.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# job, seconds elapsed, the completed subprocess
Observed = tuple[dict[str, object], float, "subprocess.CompletedProcess[str]"]


def completed_points(journal: Path) -> set[str]:
    if not journal.exists():
        return set()
    done: set[str] = set()
    for line in journal.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("event") == "point-terminal":
            done.add(str(record["payload"]["point_id"]))
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--signing-key", required=True)
    parser.add_argument("--private-stage", required=True)
    parser.add_argument("--nominations", default="tournament/cup50v2/nominations")
    parser.add_argument("--teams", default="tournament/cup50v2/teams")
    parser.add_argument("--is-root", default="data/cup50v2/is")
    parser.add_argument("--sealed-root", default="data/cup50v2/sealed")
    parser.add_argument(
        "--unavailability-audit", default="tournament/cup50v2/historical-unavailability.json"
    )
    parser.add_argument("--job-dir", default=None, help="where per-point job files are written")
    parser.add_argument("--dry-run", action="store_true", help="build every job, observe nothing")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=6,
        help=(
            "points observed at once WITHIN a lane. Lanes are still read strictly in the frozen "
            "order: the pool drains completely before the next lane starts, so the order rule in "
            "observe_point sees exactly the sequence the field froze. Safe because append_record "
            "serialises the hash chain under an flock, each point is an independent replay in its "
            "own process, and determinism across processes is what the falsifier battery checks."
        ),
    )
    arguments = parser.parse_args(argv)

    field = json.loads(Path(arguments.field).read_text())
    journal = Path(arguments.journal)
    jobs_root = Path(arguments.job_dir or (journal.parent / "jobs"))
    jobs_root.mkdir(parents=True, exist_ok=True)

    already = completed_points(journal)
    planned: list[dict[str, object]] = []
    for team_id in field["observation_order"]:          # frozen, key-derived; never re-sorted here
        disposition = field["dispositions"][team_id]
        if disposition["state"] != "nominated":
            continue
        nomination = json.loads(Path(arguments.nominations, f"{team_id}.json").read_text())
        for index, point_id in enumerate(disposition["point_ids"]):
            planned.append(
                {
                    "team_id": team_id,
                    "point_id": str(point_id),
                    "point_index": index,
                    "nomination": str(Path(arguments.nominations, f"{team_id}.json")),
                    "nomination_sha256": nomination["freeze_sha256"],
                    "strategy": str(Path(arguments.teams, team_id, "strategy.py")),
                    "source_bundle": str(Path(arguments.teams, team_id)),
                    "is_root": arguments.is_root,
                    "sealed_root": arguments.sealed_root,
                    "unavailability_audit": arguments.unavailability_audit,
                }
            )

    remaining = [job for job in planned if job["point_id"] not in already]
    print(
        f"{len(planned)} points across {len(field['observation_order'])} lanes; "
        f"{len(already)} already terminal; {len(remaining)} to observe",
        flush=True,
    )
    if arguments.dry_run:
        for job in remaining:
            (jobs_root / f"{job['point_id']}.json").write_text(json.dumps(job, indent=2))
        print(f"dry run: {len(remaining)} job files written to {jobs_root}", flush=True)
        return 0

    started = time.monotonic()
    done_count = len(already)
    failures: list[tuple[str, subprocess.CompletedProcess]] = []

    def observe(job: dict[str, object]) -> Observed:
        job_path = jobs_root / f"{job['point_id']}.json"
        job_path.write_text(json.dumps(job, indent=2))
        began = time.monotonic()
        result = subprocess.run(
            [
                "uv", "run", "cup50v2", "observe", "point",
                "--field", arguments.field,
                "--signing-key", arguments.signing_key,
                "--journal", str(journal),
                "--private-stage", arguments.private_stage,
                "--job", str(job_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return job, time.monotonic() - began, result

    by_lane: dict[str, list[dict[str, object]]] = {}
    for job in remaining:
        by_lane.setdefault(str(job["team_id"]), []).append(job)

    for team_id in field["observation_order"]:          # the barrier that keeps lane order exact
        lane = by_lane.get(team_id)
        if not lane:
            continue
        with ThreadPoolExecutor(max_workers=max(1, arguments.concurrency)) as pool:
            for job, elapsed, result in pool.map(observe, lane):
                if result.returncode != 0:
                    failures.append((str(job["point_id"]), result))
                    continue
                done_count += 1
                rate = (time.monotonic() - started) / max(1, done_count - len(already))
                left = (len(planned) - done_count) * rate / 60.0
                print(
                    f"[{done_count:3d}/{len(planned)}] {team_id} {job['point_id']} "
                    f"{elapsed:6.1f}s  eta {left:6.1f}m",
                    flush=True,
                )
        if failures:
            # An organizer fault, not a candidate failure -- observe_point journals those itself and
            # exits zero. Stop at the lane boundary rather than zeroing the rest of the field.
            point_id, result = failures[0]
            print(f"\nSTOPPED in {team_id} at {point_id}; {done_count} points terminal", flush=True)
            print(result.stdout[-2000:], flush=True)
            print(result.stderr[-4000:], file=sys.stderr, flush=True)
            return 1

    print("observation complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
