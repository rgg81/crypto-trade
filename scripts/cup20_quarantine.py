"""Move the CUP-20 holdout out of the working tree, verify it is gone, and bring it back.

Run from the repository root. Every path except the quarantine destination is read out of the
machine contract or the receipt, so the four subcommands cannot disagree about which files they
are talking about.

    uv run python scripts/cup20_quarantine.py quarantine --quarantine-root /srv/cup20-quarantine
    uv run python scripts/cup20_quarantine.py verify
    uv run python scripts/cup20_quarantine.py verify --fast
    uv run python scripts/cup20_quarantine.py restore
    uv run python scripts/cup20_quarantine.py access-report

``quarantine`` runs BEFORE the first team starts. ``restore`` runs only AFTER the selection freeze
exists, and refuses otherwise.

``verify`` is safe to run at any point during the research phase and is the check the integrity
review re-runs afterwards. It reads both quarantined trees and compares them against the digests
the receipt recorded, re-verifies the whole activation record with the sealed root read at the
quarantine location, and checks the canary token -- so a holdout modified while out of the tree is
found DURING the research phase rather than at restore, months later, after every team has
finished. ``--fast`` drops to the original absence-only test and says so in its output; it exists
for a scripted poll, not for the record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.quarantine import (
    FAST_VERIFY_DISCLAIMER,
    quarantine_holdout,
    restore_holdout,
    sealed_access_report,
    verify_quarantine_in_effect,
    verify_quarantine_integrity,
)

CONFIG_PATH = Path("tournament/cup20/config.toml")


def _paths() -> dict[str, str]:
    config = load_config(CONFIG_PATH).raw
    root = Path(config["paths"]["tournament_root"])
    return {
        "activation": str(Path(config["paths"]["activation_freeze"])),
        "journal": str(Path(config["paths"]["research_journal"])),
        "selection_freeze": str(Path(config["paths"]["selection_freeze"])),
        "sealed_root": str(Path(config["data"]["sealed_root"])),
        "receipt": str(root / "quarantine-receipt.json"),
        "restore_stamp": str(root / "quarantine-restore.json"),
        "baseline": str(root / "sealed-access-baseline.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("quarantine", help="move the holdout out of the working tree")
    start.add_argument(
        "--quarantine-root",
        required=True,
        help="destination OUTSIDE the repository; the command refuses a path inside it",
    )
    start.add_argument(
        "--acquisition-root",
        default="data/cup20/acquisition",
        help="the un-truncated superset snapshot, quarantined alongside the sealed one",
    )
    check = sub.add_parser(
        "verify", help="assert the quarantined holdout is absent from the tree AND unchanged"
    )
    check.add_argument(
        "--fast",
        action="store_true",
        help="absence only: does not read the quarantined bytes, and says so in its output",
    )
    sub.add_parser("restore", help="verify then bring both trees back (needs the selection freeze)")
    sub.add_parser("access-report", help="which sealed files have been read since arming")

    arguments = parser.parse_args()
    paths = _paths()

    if arguments.command == "quarantine":
        receipt = quarantine_holdout(
            quarantine_root=arguments.quarantine_root,
            activation_record=paths["activation"],
            receipt_path=paths["receipt"],
            acquisition_root=arguments.acquisition_root,
            journal_path=paths["journal"],
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print(f"\nquarantined; commit {paths['receipt']} before the first team starts")
        return

    if arguments.command == "verify":
        if arguments.fast:
            verify_quarantine_in_effect(receipt_path=paths["receipt"])
            print("quarantine IS in effect: neither tree is reachable from the working tree")
            print(FAST_VERIFY_DISCLAIMER)
            return
        report = verify_quarantine_integrity(receipt_path=paths["receipt"])
        print("quarantine IS in effect: neither tree is reachable from the working tree")
        for name, digest in sorted(report["bundle_sha256"].items()):
            print(f"  {name:<12} {digest}  matches the receipt")
        print(
            f"  {'sealed manifest':<12} {report['sealed_manifest_sha256']}  matches "
            f"{report['activation_record_path']}, read at the quarantine location"
        )
        print("  canary token matches the receipt, so the review scans for the right string")
        print("\nquarantine VERIFIED: the quarantined bytes are the bytes that left the tree")
        return

    if arguments.command == "restore":
        stamp = restore_holdout(
            receipt_path=paths["receipt"],
            selection_freeze_path=paths["selection_freeze"],
            restore_stamp_path=paths["restore_stamp"],
            baseline_path=paths["baseline"],
            journal_path=paths["journal"],
        )
        print(json.dumps(stamp, indent=2, sort_keys=True))
        return

    report = sealed_access_report(paths["sealed_root"], baseline_path=paths["baseline"])
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["atime_is_recorded"]:
        print("\nWARNING: this mount does not record access times; 'accessed' means nothing here")


if __name__ == "__main__":
    main()
