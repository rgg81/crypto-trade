"""Preload the frozen A5 score protocol, then run the frozen V2 strategy worker.

The editable tournament package lives inside the repository hidden by the frozen worker's mount
namespace.  Candidate strategies may nevertheless import the reviewed A5 identity hook because
this wrapper loads and verifies that exact organizer module before the repository is masked.  It
adds no import path, filesystem allowance, strategy protocol, or candidate-controlled fallback.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

from crypto_trade.tournament import _strategy_worker_v2 as frozen_worker
from crypto_trade.tournament import score_adapter_protocol_v5 as protocol

_FROZEN_WORKER_RELATIVE = "src/crypto_trade/tournament/_strategy_worker_v2.py"
_FROZEN_WORKER_SHA256 = "fff67076592e337adb721b72c4c77326c3e40e396ba57217c387a8b5f58f2b5d"
_FROZEN_WORKER_SIZE = 46_620
_PRELOAD_WORKER_RELATIVE = "src/crypto_trade/tournament/_strategy_worker_preload_v7.py"
_PROTOCOL_RELATIVE = "src/crypto_trade/tournament/score_adapter_protocol_v5.py"
_PROTOCOL_SHA256 = "8f8f5db3be3069cce7c7c0605fb15b31c4f28af7c2e0f2e24d79d861a65ae4ff"
_PROTOCOL_SIZE = 1_037
_PROTOCOL_MODULE_NAME = "crypto_trade.tournament.score_adapter_protocol_v5"
_WORKER_MODULE_NAME = "crypto_trade.tournament._strategy_worker_v2"
_TOURNAMENT_PACKAGE_NAME = "crypto_trade.tournament"
_EXPECTED_PROTOCOL_CONSTANTS = {
    "ADAPTER_ID": "top40-v2-declared-score-boundary-v1",
    "CAPTURE_BOUNDARY": "candidate-declared-post-transform-pre-selection-weight-cap-risk",
    "HOOK_QUALNAME": "strategy.score_boundary",
}

_FROZEN_MAIN = frozen_worker.main
_PROTOCOL_SCORE_BOUNDARY = protocol.score_boundary


class StrategyWorkerPreloadError(RuntimeError):
    """The reviewed organizer preload boundary failed closed."""


def _root_argument(values: list[str] | None = None) -> Path:
    arguments = list(sys.argv[1:] if values is None else values)
    positions = [index for index, value in enumerate(arguments) if value == "--root"]
    if len(positions) != 1 or positions[0] + 1 >= len(arguments):
        raise StrategyWorkerPreloadError("worker requires exactly one paired --root argument")
    root = Path(arguments[positions[0] + 1]).resolve()
    if not root.is_dir():
        raise StrategyWorkerPreloadError("worker root is not a directory")
    return root


def _bound_regular_bytes(
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> None:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise StrategyWorkerPreloadError(f"cannot open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size != expected_size
        ):
            raise StrategyWorkerPreloadError(
                f"{label} is not the expected single-link regular file"
            )
        remaining = expected_size
        digest = hashlib.sha256()
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise StrategyWorkerPreloadError(f"{label} changed while read")
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise StrategyWorkerPreloadError(f"{label} grew while read")
        after = os.fstat(descriptor)
        if (
            after.st_dev != before.st_dev
            or after.st_ino != before.st_ino
            or after.st_mode != before.st_mode
            or after.st_nlink != before.st_nlink
            or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_ctime_ns != before.st_ctime_ns
            or digest.hexdigest() != expected_sha256
        ):
            raise StrategyWorkerPreloadError(f"{label} differs from frozen authority")
    finally:
        os.close(descriptor)


def _verify_loaded_identities() -> None:
    tournament_package = sys.modules.get(_TOURNAMENT_PACKAGE_NAME)
    if (
        sys.modules.get(_PROTOCOL_MODULE_NAME) is not protocol
        or sys.modules.get(_WORKER_MODULE_NAME) is not frozen_worker
        or tournament_package is None
        or getattr(tournament_package, "score_adapter_protocol_v5", None) is not protocol
    ):
        raise StrategyWorkerPreloadError("preloaded organizer module identity changed")
    if frozen_worker.main is not _FROZEN_MAIN:
        raise StrategyWorkerPreloadError("frozen strategy-worker main identity changed")
    if protocol.score_boundary is not _PROTOCOL_SCORE_BOUNDARY:
        raise StrategyWorkerPreloadError("A5 score-boundary identity changed")
    if any(
        getattr(protocol, name, None) != expected
        for name, expected in _EXPECTED_PROTOCOL_CONSTANTS.items()
    ):
        raise StrategyWorkerPreloadError("A5 score protocol constants changed")


def _verify_preload(root: Path) -> None:
    expected_worker = (root / _FROZEN_WORKER_RELATIVE).resolve()
    expected_preload_worker = (root / _PRELOAD_WORKER_RELATIVE).resolve()
    expected_protocol = (root / _PROTOCOL_RELATIVE).resolve()
    worker_file = getattr(frozen_worker, "__file__", None)
    protocol_file = getattr(protocol, "__file__", None)
    if (
        Path(__file__).resolve() != expected_preload_worker
        or type(worker_file) is not str
        or type(protocol_file) is not str
        or Path(worker_file).resolve() != expected_worker
        or Path(protocol_file).resolve() != expected_protocol
    ):
        raise StrategyWorkerPreloadError("loaded organizer module path differs from repository")
    _bound_regular_bytes(
        expected_worker,
        expected_size=_FROZEN_WORKER_SIZE,
        expected_sha256=_FROZEN_WORKER_SHA256,
        label="frozen V2 strategy worker",
    )
    _bound_regular_bytes(
        expected_protocol,
        expected_size=_PROTOCOL_SIZE,
        expected_sha256=_PROTOCOL_SHA256,
        label="frozen A5 score protocol",
    )
    _verify_loaded_identities()


def _send_preflight_error(error: BaseException) -> None:
    payload: dict[str, Any] = {
        "type": "error",
        "error_type": "StrategySandboxError",
        "message": f"A7 worker preload failed: {error}",
    }
    sys.stdout.write(json.dumps(payload, allow_nan=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    try:
        root = _root_argument()
        _verify_preload(root)
    except BaseException as exc:
        _send_preflight_error(exc)
        return 1

    result: int | None = None
    failure: BaseException | None = None
    try:
        result = int(_FROZEN_MAIN())
    except BaseException as exc:
        failure = exc

    try:
        _verify_loaded_identities()
    except BaseException as integrity_failure:
        raise integrity_failure from failure
    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    if result is None:
        raise StrategyWorkerPreloadError("frozen strategy worker returned no result")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
