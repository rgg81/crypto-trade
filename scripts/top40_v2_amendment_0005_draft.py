#!/usr/bin/env python3
"""Draft-only entrypoint for prospective Top-40 V2 declared-score diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_trade.tournament.amendment_0005_v2 import (
    amendment_status,
    reserve_development_score_diagnostic,
    run_development_score_diagnostic,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="validate draft/frozen Amendment 0005 authority")
    for name, help_text in (
        (
            "reserve-development-score-diagnostic",
            "reserve one prospective completed candidate's declared-score diagnostic",
        ),
        (
            "run-development-score-diagnostic",
            "run one committed declared-score reservation against development data",
        ),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("team_id")
        command.add_argument("candidate_id")
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        if args.command == "status":
            result = amendment_status(root)
        elif args.command == "reserve-development-score-diagnostic":
            result = reserve_development_score_diagnostic(root, args.team_id, args.candidate_id)
        else:
            result = run_development_score_diagnostic(root, args.team_id, args.candidate_id)
        print(json.dumps(result, allow_nan=False, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
