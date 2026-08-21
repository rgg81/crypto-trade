#!/usr/bin/env python3
"""Re-run the falsification battery, strengthened, against every frozen candidate.

The independent critic found the original battery weaker than the charter claims it to be. It
corrupted only `close`, so a lane trading volume share, taker flow or funding could have reached
forward through a column the test never touched. It asserted the prefix was unchanged but never that
the suffix moved, so a constant or inert book passed trivially and the evidence could not tell the
difference. And it compared two runs inside one process, which share a hash seed -- leaving
untouched the exact defect a lane found in an organizer seed, a float sum accumulated over set
iteration.

This does not re-open any nomination. The binding is source, centre and points, and none of those
change. It adds evidence the nominations should have carried, before the sealed window opens.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NOMINATIONS = REPO / "tournament/cup50v2/nominations"
OUT = REPO / "tournament/cup50v2/private/falsifiers"
WORKSPACES = Path("/home/roberto/cup50v2-teams")

WORKER = r"""
import hashlib, json, sys
import pandas as pd
from crypto_trade.cup50v2 import falsifiers
from crypto_trade.cup50v2.availability import load_unavailability_audit
from crypto_trade.cup50v2.config import IS_START, OOS_START
from crypto_trade.cup50v2.replay import (
    apply_strategy_parameters, decision_grid, generate_targets,
    load_strategy_module, strategy_from_module,
)
from crypto_trade.cup50v2.snapshot import load_snapshot

bundle, seed, mode = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
snapshot = load_snapshot("data/cup50v2/is")
unavailability = load_unavailability_audit("tournament/cup50v2/is-unavailability.json")
decisions = decision_grid(IS_START, OOS_START)
centre = json.loads((bundle / "parameters.json").read_text())["centre"]

def stream(bars):
    strategy = strategy_from_module(load_strategy_module(bundle / "strategy.py"))
    apply_strategy_parameters(strategy, centre)
    return generate_targets(
        strategy, bars=bars, funding=snapshot.funding, auxiliary={},
        membership=snapshot.membership, decision_times=decisions, seed=seed,
        unavailability=unavailability,
    )

if mode == "digest":
    print(falsifiers.target_stream_digest(stream(snapshot.bars)))
else:
    key = Path("tournament/cup50v2/private/falsifier.key").read_bytes()
    cuts = falsifiers.corruption_cut_points(decisions, key=key, count=6)
    outcome = falsifiers.future_corruption(stream, snapshot.bars, cut_points=cuts)
    print(json.dumps({"name": outcome.name, "passed": outcome.passed,
                      "detail": outcome.detail, "evidence": outcome.evidence}, default=str))
"""


def run(bundle: Path, seed: int, mode: str, hash_seed: int) -> str:
    script = REPO / "tournament/cup50v2/private/_falsifier_worker.py"
    script.write_text("from pathlib import Path\n" + WORKER)
    env = {
        **os.environ,
        "PYTHONHASHSEED": str(hash_seed),
        "CUP50V2_SANDBOX": "network-none-read-only",
    }
    result = subprocess.run(
        ["uv", "run", "python", str(script), str(bundle), str(seed), mode],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(f"{bundle.name} {mode}: {result.stderr[-2000:]}")
    return result.stdout.strip().splitlines()[-1]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    teams = sys.argv[1:] or sorted(p.stem for p in NOMINATIONS.glob("*.json"))
    for team in teams:
        nomination = json.loads((NOMINATIONS / f"{team}.json").read_text())
        bundle = WORKSPACES / team / "candidates" / nomination["candidate_id"]
        seed = int(team.split("-")[1])
        # Determinism across three hash seeds, in separate processes.
        digests = {hs: run(bundle, seed, "digest", hs) for hs in (0, 1, 8675309)}
        agree = len(set(digests.values())) == 1
        corruption = json.loads(run(bundle, seed, "corrupt", 0))
        report = {
            "schema_version": 1,
            "namespace": "cup50v2",
            "team_id": team,
            "candidate_id": nomination["candidate_id"],
            "source_bundle_sha256": nomination["source_bundle_sha256"],
            "determinism": {
                "passed": agree,
                "hash_seeds": sorted(digests),
                "digests": {str(k): v for k, v in digests.items()},
                "detail": "three independent processes under different hash seeds"
                + (" agree" if agree else " DIVERGED"),
            },
            "future_corruption": corruption,
        }
        (OUT / f"{team}.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(
            json.dumps(
                {
                    "team": team,
                    "determinism": agree,
                    "corruption_passed": corruption["passed"],
                    "responsive_cuts": corruption["evidence"].get(
                        "cut_points_with_a_responsive_suffix"
                    ),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
