"""Freeze the four desks and write the launch record. Run once.

A desk is a frozen bundle: the exact candidate source, its lane identity, and the hash of both.
After this, the engine replays those bytes and nothing else -- if the source on disk changes, the
deployment manifest stops matching and the desk refuses to publish rather than quietly replaying
something new.

The ensemble is not a special case in the manifest. It is one more frozen bundle that happens to
name the other three and combine their weights at one third each.

The forward record begins at the end of the operational embargo, 2026-09-01. Everything before
that is bridge: real out-of-sample data that existed before the desks went live, kept apart from
the official record because counting it would credit a desk with performance it never traded.

Usage::

    uv run python scripts/top40v5_paper_deploy.py --check
    uv run python scripts/top40v5_paper_deploy.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TOURNAMENT = REPO / "tournament" / "top40-v5"
PAPER = REPO / "paper-top40v5"

# Ranked on the historical window; the desk names carry the rank so a reader does not have to
# remember it, and the lane id so the lineage is never ambiguous.
DESKS = {
    "desk-1-team-14": {"lane": "team-14", "rank": 1, "kind": "individual"},
    "desk-2-team-08": {"lane": "team-08", "rank": 2, "kind": "individual"},
    "desk-3-team-09": {"lane": "team-09", "rank": 3, "kind": "individual"},
    "ensemble-eq3": {
        "lane": None,
        "rank": None,
        "kind": "ensemble",
        "members": ["team-14", "team-08", "team-09"],
        "weight_each": 1 / 3,
    },
}

OFFICIAL_START = pd.Timestamp("2026-09-01", tz="UTC")
# 365 official days before the forward record may be read.
OFFICIAL_DAYS_REQUIRED = 365


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    arguments = parser.parse_args()

    launch_path = PAPER / "launch.json"
    if launch_path.is_file() and not arguments.check:
        print(f"already deployed: {launch_path.relative_to(REPO)} exists")
        print("re-deploying would rebind the desks to different bytes; that needs an amendment")
        return 1

    release = json.loads(
        (REPO / "reports-top40-v5" / "historical" / "release.json").read_text(encoding="utf-8")
    )
    ranked = [
        r["team_id"] for r in sorted(release["rows"], key=lambda r: -r["packet"]["net_sharpe"])
    ]
    expected = [DESKS[d]["lane"] for d in ("desk-1-team-14", "desk-2-team-08", "desk-3-team-09")]
    if ranked[:3] != expected:
        print(f"lineage drift: release ranks {ranked[:3]}, deployment names {expected}")
        return 1
    print(f"release top three {ranked[:3]} matches the deployment")

    manifest: dict[str, object] = {}
    for desk, spec in DESKS.items():
        lanes_needed = [spec["lane"]] if spec["lane"] else spec["members"]
        bundle = {}
        for lane in lanes_needed:
            source = TOURNAMENT / "teams" / lane / "outbox" / "candidate.py"
            body = source.read_bytes()
            bundle[lane] = {"sha256": _sha256(body), "bytes": len(body)}
        manifest[desk] = {**{k: v for k, v in spec.items()}, "bundle": bundle}
        shown = ", ".join(f"{k} {v['sha256'][:12]}" for k, v in bundle.items())
        print(f"  {desk:16s} {shown}")

    if arguments.check:
        print("\ncheck only; nothing written")
        return 0

    for desk, spec in DESKS.items():
        root = PAPER / desk
        (root / "ledger").mkdir(parents=True, exist_ok=True)
        for lane in [spec["lane"]] if spec["lane"] else spec["members"]:
            shutil.copy2(
                TOURNAMENT / "teams" / lane / "outbox" / "candidate.py",
                root / f"frozen-{lane}.py",
            )

    (PAPER / "deployment-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    launch = {
        "launched_at": str(pd.Timestamp.now(tz="UTC")),
        "official_start": str(OFFICIAL_START),
        "official_days_required": OFFICIAL_DAYS_REQUIRED,
        "desks": sorted(DESKS),
        "activation_freeze": json.loads(
            (TOURNAMENT / "activation-freeze.json").read_text(encoding="utf-8")
        )["artifacts"]["config"],
        "capital_rule": (
            "Read ONCE after >=365 official days. Until then the rule is not readable and no "
            "provisional winner may be computed. If no desk qualifies, no capital is deployed and "
            "the edition closes without deployment -- a legal, pre-registered outcome."
        ),
        "paper_only": "no signed client, no order path; paper by construction, not configuration",
    }
    launch_path.parent.mkdir(parents=True, exist_ok=True)
    launch_path.write_text(json.dumps(launch, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\ndeployed {len(DESKS)} desks under {PAPER.relative_to(REPO)}/")
    print(
        f"official record opens {OFFICIAL_START.date()}; capital readable after "
        f"{OFFICIAL_DAYS_REQUIRED} official days"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
