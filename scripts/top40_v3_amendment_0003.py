#!/usr/bin/env python3
"""Closed command surface for Top40 V3 Amendment 0003."""

from __future__ import annotations

import argparse
import dataclasses
import sys

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0003_stitched as stitched


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Top40 V3 stitched public assessment")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze", help="freeze the prospective assessment layer")
    freeze.add_argument("--implementation-commit", required=True)
    commands.add_parser("validate", help="verify the frozen assessment authority")
    commands.add_parser("assess", help="create the immutable stitched public report")
    commands.add_parser("report", help="read the immutable stitched public report")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "freeze":
            provisional = stitched.freeze_activation(
                arguments.root, implementation_commit=arguments.implementation_commit
            )
            result = {
                "amendment_id": stitched.AMENDMENT_ID,
                "activation": "pending-unique-freeze-commit",
                "command": "freeze",
                "provisional_freeze": dataclasses.asdict(provisional),
                "ok": True,
            }
        elif arguments.command == "validate":
            result = stitched.validate(arguments.root)
        elif arguments.command == "assess":
            result = stitched.assess(arguments.root)
        elif arguments.command == "report":
            result = stitched.report(arguments.root)
        else:  # pragma: no cover
            raise stitched.Amendment0003StitchedError("unknown command")
    except (OSError, TypeError, ValueError, orchestrator_v3.OrchestratorError) as exc:
        error = {"error": orchestrator_v3._failure_reason(exc), "ok": False}
        sys.stderr.buffer.write(orchestrator_v3._canonical_json_bytes(error) + b"\n")
        return 2
    sys.stdout.buffer.write(orchestrator_v3._canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
