#!/usr/bin/env python3
"""Closed controls for the Amendment 0002 first-journal durability addendum."""

from __future__ import annotations

import argparse
import dataclasses
import sys

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0002_durability as durability


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Top40 V3 validation-journal durability")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze", help="create the durability freeze once")
    freeze.add_argument("--implementation-commit", required=True)
    commands.add_parser("validate", help="verify the durability addendum")
    commands.add_parser(
        "initialize-journal",
        help="durably create and parent-fsync the empty validation journal",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "freeze":
            provisional = durability.freeze_durability(
                arguments.root,
                implementation_commit=arguments.implementation_commit,
            )
            result = {
                "addendum_id": durability.ADDENDUM_ID,
                "activation": "pending-unique-freeze-commit",
                "command": "freeze",
                "provisional_freeze": dataclasses.asdict(provisional),
                "ok": True,
            }
        elif arguments.command == "validate":
            result = durability.validate(arguments.root)
        elif arguments.command == "initialize-journal":
            result = durability.initialize_journal(arguments.root)
        else:  # pragma: no cover - argparse owns the command set
            raise durability.DurabilityAddendumError("unknown command")
    except (OSError, TypeError, ValueError, orchestrator_v3.OrchestratorError) as exc:
        error = {"error": orchestrator_v3._failure_reason(exc), "ok": False}
        sys.stderr.buffer.write(orchestrator_v3._canonical_json_bytes(error) + b"\n")
        return 2
    sys.stdout.buffer.write(orchestrator_v3._canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
