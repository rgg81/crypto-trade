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
    arguments = parser.parse_args()

    config = load_config(CONFIG_PATH)
    paths = config.raw["paths"]
    data = config.raw["data"]
    record = build_activation_record(
        CONFIG_PATH,
        Path(config.raw["charter_path"]),
        Path(data["is_root"]),
        Path(data["sealed_root"]),
        Path(arguments.test_output),
        DEPENDENCY_LOCK,
        IMPLEMENTATION_ROOT,
        PURE_CRYPTO_AUDIT,
    )
    destination = Path(paths["activation_freeze"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    # Never announce a freeze that has not been read back and re-verified from disk.
    verified = verify_activation(destination)
    if verified != record:
        raise SystemExit(f"activation record at {destination} did not round-trip")
    print(f"activation frozen at {destination}")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
