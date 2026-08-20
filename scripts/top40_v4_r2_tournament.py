#!/usr/bin/env python3
"""Canonical organizer CLI for the 15-team Top-40 V4 edition 2 tournament."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

from crypto_trade.tournament.layout_v4 import select_v4_layout

select_v4_layout("r2")

from crypto_trade.tournament import (  # noqa: E402
    isolation_v4,
    orchestrator_v4,
    research_runtime_v4,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate the edition-2 contract")
    validate.add_argument("--pre-activation", action="store_true")
    commands.add_parser("audit-isolation", help="verify all 15 clean-room surfaces")
    commands.add_parser("activate", help="test and freeze the edition-2 authority")
    commands.add_parser(
        "recover-pretrial",
        help="archive the exact pretrial incident, reactivate, and unblock its one retry",
    )
    commands.add_parser("status", help="show the disclosure-safe lifecycle projection")

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

    commands.add_parser("close-is", help="rank nominees and freeze at most six finalists")
    commands.add_parser(
        "historical-release",
        help="consume finalist observations and atomically publish the championship",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(arguments.root)
    try:
        # Result entrypoints own their broker lease internally, after their activation precheck.
        # Only the read-only isolation audit needs a lease supplied by this CLI. Activation is the
        # bootstrap exception: its result lock serializes it while its test child acquires broker.
        command_lease = (
            research_runtime_v4.broker_lease(root)
            if arguments.command == "audit-isolation"
            else contextlib.nullcontext()
        )
        with command_lease:
            if arguments.command == "validate":
                result = orchestrator_v4.validate(
                    root, require_activation=not arguments.pre_activation
                )
            elif arguments.command == "audit-isolation":
                result = isolation_v4.audit_surface(root)
            elif arguments.command == "activate":
                result = orchestrator_v4.activate(root)
            elif arguments.command == "recover-pretrial":
                result = orchestrator_v4.recover_pretrial(root)
            elif arguments.command == "status":
                result = orchestrator_v4.status(root)
            elif arguments.command == "is-run":
                result = orchestrator_v4.run_is(
                    root,
                    arguments.team_id,
                    arguments.entrypoint,
                    purpose=arguments.purpose,
                )
            elif arguments.command == "nominate":
                result = orchestrator_v4.nominate(
                    root,
                    arguments.team_id,
                    arguments.candidate_id,
                    arguments.certificate_path,
                )
            elif arguments.command == "retire":
                result = orchestrator_v4.retire(
                    root, arguments.team_id, reason=arguments.reason
                )
            elif arguments.command == "close-is":
                result = orchestrator_v4.close_is(root)
            elif arguments.command == "historical-release":
                result = orchestrator_v4.historical_release(root)
            else:  # pragma: no cover - argparse owns this invariant.
                raise AssertionError(arguments.command)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"top40-v4-r2: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
