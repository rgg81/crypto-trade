#!/usr/bin/env python3
"""Closed command surface for prospective Top40 Amendment 0002."""

from __future__ import annotations

import argparse
import dataclasses
import sys

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0002_validation as validation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Top40 Amendment 0002 sealed validation")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze", help="create the prospective activation freeze once")
    freeze.add_argument("--implementation-commit", required=True)
    commands.add_parser("validate", help="verify the complete sealed-validation authority")
    commands.add_parser("status", help="show nondisclosing four-team progress")
    probe = commands.add_parser("probe", help="consume one frozen candidate's opening probe")
    probe.add_argument("team_id")
    commands.add_parser("report", help="release all fixed packets after four terminal probes")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "freeze":
            provisional = validation.freeze_activation(
                arguments.root,
                implementation_commit=arguments.implementation_commit,
            )
            result = {
                "amendment_id": validation.AMENDMENT_ID,
                "activation": "pending-unique-freeze-commit",
                "command": "freeze",
                "provisional_freeze": dataclasses.asdict(provisional),
                "ok": True,
            }
        elif arguments.command == "validate":
            result = validation.validate(arguments.root)
        elif arguments.command == "status":
            result = validation.status(arguments.root)
        elif arguments.command == "probe":
            result = validation.probe(arguments.root, arguments.team_id)
        elif arguments.command == "report":
            result = validation.report(arguments.root)
        else:  # pragma: no cover - argparse owns the command set
            raise validation.Amendment0002ValidationError("unknown command")
    except (OSError, TypeError, ValueError, orchestrator_v3.OrchestratorError) as exc:
        error = {"error": orchestrator_v3._failure_reason(exc), "ok": False}
        sys.stderr.buffer.write(orchestrator_v3._canonical_json_bytes(error) + b"\n")
        return 2
    sys.stdout.buffer.write(orchestrator_v3._canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
