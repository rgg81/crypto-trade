"""Prospective superset dispatcher for active Amendment 0005 integration."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from crypto_trade.tournament import amendment_0005_v2, amendment_0006_v2

_A5_MODULE = amendment_0005_v2
_A5_STATUS = _A5_MODULE.amendment_status
_A5_RESERVE = _A5_MODULE.reserve_development_score_diagnostic
_A5_RUN = _A5_MODULE.run_development_score_diagnostic
_A5_ACTIVE_GUARD = _A5_MODULE._active_integration_guard
_A5_AUTHORIZATION = _A5_MODULE._ACTIVE_INTEGRATION_AUTHORIZATION
_A6_RUN = amendment_0006_v2.run

STATUS_COMMAND = "amendment-0005-status"
RESERVE_COMMAND = "amendment-0005-reserve-development-score-diagnostic"
RUN_COMMAND = "amendment-0005-run-development-score-diagnostic"
AMENDMENT_0005_COMMANDS = (STATUS_COMMAND, RESERVE_COMMAND, RUN_COMMAND)


class Amendment0005IntegrationError(ValueError):
    """The reviewed Amendment 0005 integration dispatcher failed closed."""


def _a5_arguments(values: list[str]) -> tuple[str, str] | None:
    command = values[0]
    if command == STATUS_COMMAND:
        if len(values) != 1:
            raise Amendment0005IntegrationError(f"{STATUS_COMMAND} accepts no arguments")
        return None
    if len(values) != 3:
        raise Amendment0005IntegrationError(f"{command} requires exactly TEAM_ID and CANDIDATE_ID")
    return values[1], values[2]


def _print_result(result: Mapping[str, object]) -> None:
    print(json.dumps(result, allow_nan=False, indent=2, sort_keys=True))


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Dispatch A5 commands and delegate every other argv unchanged to frozen A6."""

    values = list(sys.argv[1:] if argv is None else argv)
    root_path = Path.cwd().resolve() if root is None else Path(root).resolve()
    command = values[0] if values else None
    with _A5_ACTIVE_GUARD(root_path, _authorization=_A5_AUTHORIZATION):
        if command not in AMENDMENT_0005_COMMANDS:
            return int(_A6_RUN(argv, root=root_path))
        arguments = _a5_arguments(values)
        if command == STATUS_COMMAND:
            result = _A5_STATUS(root_path)
        elif command == RESERVE_COMMAND:
            if arguments is None:
                raise Amendment0005IntegrationError("reserve arguments are missing")
            result = _A5_RESERVE(
                root_path,
                *arguments,
                _authorization=_A5_AUTHORIZATION,
            )
        else:
            if arguments is None:
                raise Amendment0005IntegrationError("run arguments are missing")
            result = _A5_RUN(
                root_path,
                *arguments,
                _authorization=_A5_AUTHORIZATION,
            )
        _print_result(result)
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-amendment-0005: error: {exc}", file=sys.stderr)
        return 2
