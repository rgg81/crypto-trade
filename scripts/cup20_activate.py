"""Freeze CUP-20 activation: bind every authority into one record, then verify it round-trips.

Run from the repository root. Every path is read out of the machine contract rather than repeated
here, so the record can only ever bind the files the contract itself points at -- and it is written
with the same relative paths, which is what ``verify_activation`` will later re-read.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_trade.cup20.activation import build_activation_record, verify_activation
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.quarantine import verify_quarantine_in_effect

CONFIG_PATH = Path("tournament/cup20/config.toml")
IMPLEMENTATION_ROOT = Path("src/crypto_trade/cup20")
DEPENDENCY_LOCK = Path("uv.lock")
PURE_CRYPTO_AUDIT = Path("tournament/cup20/private/pure-crypto-audit.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the CUP-20 activation freeze")
    parser.add_argument(
        "--test-output",
        default="tournament/cup20/activation-tests.out",
        help="the focused test run whose output is bound into the record",
    )
    parser.add_argument(
        "--quarantine-receipt",
        default="tournament/cup20/quarantine-receipt.json",
        help="read only when the sealed tree is absent, to find where quarantine moved it",
    )
    arguments = parser.parse_args()

    config = load_config(CONFIG_PATH)
    paths = config.raw["paths"]
    data = config.raw["data"]
    # A prospective amendment can land while the holdout is quarantined, and re-freezing then must
    # neither restore the holdout (which would put it back in every team's reach) nor write the
    # quarantine location into the record (which stops existing when the holdout comes back). The
    # override reads the sealed tree where it is; ``verify_quarantine_in_effect`` is what proves
    # nothing has been put at the contract path in its place, and it raises if anything has.
    sealed_root_override: Path | None = None
    if not Path(data["sealed_root"]).exists():
        receipt = verify_quarantine_in_effect(receipt_path=arguments.quarantine_receipt)
        sealed_root_override = Path(receipt["trees"]["sealed"]["quarantine_path"])
        print(f"sealed tree is quarantined; hashing it at {sealed_root_override}")
    record = build_activation_record(
        CONFIG_PATH,
        Path(config.raw["charter_path"]),
        Path(data["is_root"]),
        Path(data["sealed_root"]),
        Path(arguments.test_output),
        DEPENDENCY_LOCK,
        IMPLEMENTATION_ROOT,
        PURE_CRYPTO_AUDIT,
        sealed_root_override=sealed_root_override,
    )
    destination = Path(paths["activation_freeze"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    # Never announce a freeze that has not been read back and re-verified from disk.
    verified = verify_activation(destination, sealed_root_override=sealed_root_override)
    if verified != record:
        raise SystemExit(f"activation record at {destination} did not round-trip")
    print(f"activation frozen at {destination}")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
