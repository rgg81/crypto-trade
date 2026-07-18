#!/usr/bin/env python3
"""Closed activation surface for prospective Top40 Amendment 0001."""

from __future__ import annotations

import argparse
import dataclasses
import sys

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0001_integration as integration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Top40 Amendment 0001 controls")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser(
        "freeze", help="create the provisional Amendment 0001 integration freeze once"
    )
    freeze.add_argument("--implementation-commit", required=True)
    commands.add_parser("validate", help="validate parent and amendment activation")
    commands.add_parser("status", help="show nondisclosing amendment-aware status")
    train = commands.add_parser("train", help="run one amended transparent train laboratory")
    train.add_argument("team_id")
    train.add_argument("entrypoint")
    train.add_argument("--purpose", default="organizer train laboratory evaluation")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "freeze":
            provisional = integration.freeze_integration(
                arguments.root,
                implementation_commit=arguments.implementation_commit,
            )
            result = {
                "amendment_id": integration.AMENDMENT_ID,
                "activation": "pending-unique-freeze-commit",
                "command": "freeze",
                "provisional_freeze": dataclasses.asdict(provisional),
                "ok": True,
            }
        elif arguments.command == "validate":
            result = integration.validate(arguments.root)
        elif arguments.command == "status":
            result = integration.status(arguments.root)
        elif arguments.command == "train":
            result = integration.train(
                arguments.root,
                arguments.team_id,
                arguments.entrypoint,
                purpose=arguments.purpose,
            )
        else:  # pragma: no cover - argparse owns the closed command set
            raise integration.Amendment0001IntegrationError("unknown amendment command")
    except (OSError, TypeError, ValueError, orchestrator_v3.OrchestratorError) as exc:
        error = {"error": orchestrator_v3._failure_reason(exc), "ok": False}
        sys.stderr.buffer.write(orchestrator_v3._canonical_json_bytes(error) + b"\n")
        return 2
    sys.stdout.buffer.write(orchestrator_v3._canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
