#!/usr/bin/env python3
"""Canonical organizer CLI for the Top-12 V2 tournament."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crypto_trade.tournament import orchestrator_top12_v2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate the V4 contract and activation")
    validate.add_argument("--pre-activation", action="store_true")
    commands.add_parser(
        "activate", help="run focused tests and create the one-time activation freeze"
    )
    commands.add_parser("status", help="show the lifecycle projection")

    run_is = commands.add_parser("is-run", help="accept and evaluate one structured IS trial")
    run_is.add_argument("team_id")
    run_is.add_argument("entrypoint")
    run_is.add_argument("--purpose", required=True)

    nominate = commands.add_parser("nominate", help="freeze one eligible nominee for a team")
    nominate.add_argument("team_id")
    nominate.add_argument("candidate_id")
    nominate.add_argument("certificate_path")

    retire = commands.add_parser("retire", help="retire a lane after its mandatory research")
    retire.add_argument("team_id")
    retire.add_argument("--reason", required=True)

    commands.add_parser(
        "close-is",
        help="run sealed IS confirmation and freeze at most four finalists",
    )
    commands.add_parser(
        "historical-release",
        help="consume finalist observations and atomically publish the complete championship",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(arguments.root)
    try:
        if arguments.command == "validate":
            result = orchestrator_top12_v2.validate(
                root,
                require_activation=not arguments.pre_activation,
            )
        elif arguments.command == "activate":
            result = orchestrator_top12_v2.activate(root)
        elif arguments.command == "status":
            result = orchestrator_top12_v2.status(root)
        elif arguments.command == "is-run":
            result = orchestrator_top12_v2.run_is(
                root,
                arguments.team_id,
                arguments.entrypoint,
                purpose=arguments.purpose,
            )
        elif arguments.command == "nominate":
            result = orchestrator_top12_v2.nominate(
                root,
                arguments.team_id,
                arguments.candidate_id,
                arguments.certificate_path,
            )
        elif arguments.command == "retire":
            result = orchestrator_top12_v2.retire(root, arguments.team_id, reason=arguments.reason)
        elif arguments.command == "close-is":
            result = orchestrator_top12_v2.close_is(root)
        elif arguments.command == "historical-release":
            result = orchestrator_top12_v2.historical_release(root)
        else:  # pragma: no cover - argparse owns this invariant.
            raise AssertionError(arguments.command)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"top12-v2: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
