#!/usr/bin/env python3
"""Serial organizer controls for the Top-40 V3 post-tournament research extension."""

from __future__ import annotations

import argparse
import json
import sys

from crypto_trade.tournament import research_extension_v3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    commands.add_parser("status")
    develop = commands.add_parser("develop")
    develop.add_argument("team_id")
    develop.add_argument("candidate_id")
    develop.add_argument("--purpose", required=True)
    freeze = commands.add_parser("freeze-finalist")
    freeze.add_argument("team_id")
    freeze.add_argument("candidate_id")
    qualify = commands.add_parser("qualify")
    qualify.add_argument("team_id")
    commands.add_parser("final-release")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "validate":
            result = research_extension_v3.validate(arguments.root)
        elif arguments.command == "status":
            result = research_extension_v3.status(arguments.root)
        elif arguments.command == "develop":
            result = research_extension_v3.run_development(
                arguments.root,
                arguments.team_id,
                arguments.candidate_id,
                purpose=arguments.purpose,
            )
        elif arguments.command == "freeze-finalist":
            result = research_extension_v3.freeze_finalist(
                arguments.root, arguments.team_id, arguments.candidate_id
            )
        elif arguments.command == "qualify":
            result = research_extension_v3.run_qualifier(arguments.root, arguments.team_id)
        elif arguments.command == "final-release":
            result = research_extension_v3.run_final_release(arguments.root)
        else:  # pragma: no cover
            raise research_extension_v3.ResearchExtensionError("unknown command")
    except (OSError, TypeError, ValueError, research_extension_v3.ResearchExtensionError) as exc:
        sys.stderr.write(json.dumps({"error": f"{type(exc).__name__}: {exc}", "ok": False}) + "\n")
        return 2
    sys.stdout.write(json.dumps(result, allow_nan=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
