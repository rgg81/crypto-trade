#!/usr/bin/env python3
"""Administer Top-40 V2 Amendment 0002 score-diagnostic compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_trade.tournament.amendment_0002_v2 import (
    correction_review_material,
    correction_status,
    freeze_correction,
    run_core_retry,
    run_reference_diagnostic,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config, load_config


def _config(root: Path, value: str) -> LoadedV2Config:
    path = Path(value)
    return load_config(path if path.is_absolute() else root / path)


def _emit(payload: object) -> None:
    print(json.dumps(payload, allow_nan=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("review-material", "derive the exact immutable review bindings"),
        ("freeze-correction", "freeze the committed compatibility review"),
        ("run-core-retry", "execute the sole infrastructure-corrective core retry"),
        ("run-reference", "execute the existing reference reservation compatibly"),
        ("status", "validate and show Amendment 0002 status"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--config", default=TOP40_V2_LAYOUT.config_path)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        config = _config(root, args.config)
        if args.command == "review-material":
            result = correction_review_material(root, config)
        elif args.command == "freeze-correction":
            result = freeze_correction(root, config)
        elif args.command == "run-core-retry":
            result = run_core_retry(root, config)
        elif args.command == "run-reference":
            result = run_reference_diagnostic(root, config)
        else:
            result = correction_status(root, config)
        _emit(result)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
