#!/usr/bin/env python3
"""Administer Top-40 V2 amendment 0001 without calculating tournament scores."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.tournament.amendment_v2 import (
    activate_amendment_draft,
    amendment_status,
    freeze_amendment,
    integration_review_material,
    read_json_file,
    reserve_diagnostic_backfill,
    resume_amendment_hold,
    run_diagnostic_backfill,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import TEAM_IDS, LoadedV2Config, load_config

DEFAULT_CONFIG = TOP40_V2_LAYOUT.config_path


def _config(root: Path, value: str) -> LoadedV2Config:
    candidate = Path(value)
    return load_config(candidate if candidate.is_absolute() else root / candidate)


def _input(path: str, label: str) -> Mapping[str, Any]:
    raw, _payload = read_json_file(path, label)
    return raw


def _emit(payload: object) -> None:
    encoded = json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    print(encoded, end="")


def _reservation_input(path: str) -> Mapping[str, Any]:
    raw = _input(path, "diagnostic reservation input")
    expected = {
        "schema_version",
        "diagnostic_id",
        "team_id",
        "candidate_id",
    }
    if set(raw) != expected or raw.get("schema_version") != 1:
        raise ValueError("diagnostic reservation input does not match schema version 1")
    if raw.get("team_id") not in TEAM_IDS:
        raise ValueError("diagnostic reservation input has an unknown team_id")
    if not isinstance(raw.get("diagnostic_id"), str) or not isinstance(
        raw.get("candidate_id"), str
    ):
        raise ValueError("diagnostic reservation identifiers must be strings")
    return raw


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_CONFIG)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="validate and show amendment status")
    _common(status)

    draft = commands.add_parser(
        "draft-amendment",
        help="activate the additive draft and global administrative hold",
    )
    _common(draft)

    freeze = commands.add_parser(
        "freeze-amendment",
        help="freeze the exact committed review and integration bytes",
    )
    _common(freeze)

    review = commands.add_parser(
        "integration-review-material",
        help="derive the stable integration manifest and organizer review bindings",
    )
    _common(review)

    reserve = commands.add_parser(
        "reserve-diagnostic-backfill",
        help="append one organizer-private, non-material, one-shot reservation",
    )
    reserve.add_argument("reservation")
    _common(reserve)

    run_diagnostic = commands.add_parser(
        "run-diagnostic-backfill",
        help="execute one reservation with the trusted runner and record its terminal result",
    )
    run_diagnostic.add_argument("diagnostic_id")
    _common(run_diagnostic)

    resume = commands.add_parser(
        "resume-amendment",
        help="resume the run and toll the common research deadline exactly",
    )
    _common(resume)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        config = _config(root, args.config)
        if args.command == "status":
            result = amendment_status(root, config)
        elif args.command == "draft-amendment":
            result = activate_amendment_draft(
                root,
                config,
            )
        elif args.command == "freeze-amendment":
            result = freeze_amendment(root, config)
        elif args.command == "integration-review-material":
            result = integration_review_material(root, config)
        elif args.command == "reserve-diagnostic-backfill":
            request = _reservation_input(args.reservation)
            result = reserve_diagnostic_backfill(
                root,
                config,
                diagnostic_id=request["diagnostic_id"],
                team_id=request["team_id"],
                candidate_id=request["candidate_id"],
            )
        elif args.command == "run-diagnostic-backfill":
            result = run_diagnostic_backfill(
                root,
                config,
                diagnostic_id=args.diagnostic_id,
            )
        else:
            result = resume_amendment_hold(root, config)
        _emit(result)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
