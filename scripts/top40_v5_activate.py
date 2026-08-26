"""Activate the edition: bind every artifact a later claim will rest on.

Single-shot. After this, changes require a prospective append-only amendment made before the
affected data are accessed, and the hash-chained journal makes one written after the fact visible
as such.

Everything is checked before anything is written, so a refused activation leaves no partial freeze
for a later run to mistake for a real one.

Usage::

    uv run python scripts/top40_v5_activate.py --check    # verify readiness, write nothing
    uv run python scripts/top40_v5_activate.py            # bind the edition
    uv run python scripts/top40_v5_activate.py --validate # re-verify an existing freeze
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crypto_trade.tournament.v5 import activation, journal
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]
TOURNAMENT = REPO / TOP40_V5_LAYOUT.tournament_root

ARTIFACTS = {
    "charter": REPO / "TOURNAMENT-CHARTER-TOP40-V5.md",
    "config": TOURNAMENT / "config.toml",
    "snapshot_manifest": TOURNAMENT / "data-manifest.json",
    "snapshot_preflight": TOURNAMENT / "snapshot-preflight.json",
    "calibration_report": TOURNAMENT / "calibration-report.json",
    "dependency_lock": REPO / "uv.lock",
    "evaluator": REPO / "src" / "crypto_trade" / "tournament" / "v5" / "engine.py",
    "mutation_ledger": TOURNAMENT / "mutation-ledger.json",
    "adversarial_review": TOURNAMENT / "adversarial-review.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify readiness without writing")
    parser.add_argument("--validate", action="store_true", help="re-verify an existing freeze")
    arguments = parser.parse_args()

    freeze_path = TOURNAMENT / "activation-freeze.json"
    journal_path = TOURNAMENT / "research-journal.jsonl"

    missing = [name for name, path in ARTIFACTS.items() if not path.is_file()]
    if missing:
        print(f"missing artifacts: {missing}")
        return 1

    if arguments.validate:
        findings = activation.validate(
            ARTIFACTS, tournament_root=TOURNAMENT, freeze_path=freeze_path
        )
        if findings:
            print(f"{len(findings)} finding(s) since activation:")
            for finding in findings:
                print(f"  {finding}")
            return 1
        print("freeze validates: every bound artifact is unchanged")
        return 0

    if arguments.check:
        print("artifacts present:")
        for name, path in sorted(ARTIFACTS.items()):
            print(f"  {name:20s} {path.relative_to(REPO)}")
        print(f"\nfreeze: {'ALREADY EXISTS' if freeze_path.is_file() else 'not yet written'}")
        return 0

    if not journal_path.is_file():
        journal.initialize(journal_path)

    frozen = activation.freeze(
        ARTIFACTS,
        tournament_root=TOURNAMENT,
        journal_path=journal_path,
        destination=freeze_path,
    )

    print("ACTIVATED\n")
    print(f"freeze sha256   {frozen.sha256()}")
    print(f"journal head    {frozen.journal_head[:16]}")
    print(f"artifacts       {len(frozen.artifacts)}")
    print(f"lane surfaces   {len(frozen.lane_surfaces)}")
    print(f"numbers bound   {len(frozen.numeric_provenance)}")
    print(f"\nwrote {freeze_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
