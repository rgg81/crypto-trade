"""Schema-3 validator compatibility for frozen Top-40 V2 development runs."""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.tournament import (
    amended_orchestrator_compat_v3,
    amendment_v2,
    runner_v2,
    score_diagnostic_compat_v2,
    top40_v2,
)
from crypto_trade.tournament.amendment_integrity_v2 import pretty_json_bytes
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config

_AMENDMENT_0003_MODULE_SHA256 = (
    "b7c9be94aca5b4ef7a66a5f59f0a47d0cd52235474eafb576cf0dc37281c066d"
)
_AMENDMENT_0002_MODULE_SHA256 = (
    "fc70dbdb752c58857c5ed60a96e497324e93b9d5dc7e6afa0692bd3e02ad21aa"
)
_SUPPORTED_RUNNER_COMMAND = "run-window"
_MISSING = object()

_A2_MODULE = score_diagnostic_compat_v2
_A2_PATCH_LOCK = _A2_MODULE._PATCH_LOCK
_A2_FACADE_TYPE = _A2_MODULE._TournamentContractFacade
_A2_READ_STATE = _A2_MODULE._read_exact_schema3_state
_A2_CANONICAL_CONTRACT = _A2_MODULE._CANONICAL_CONTRACT
_A2_LOAD_CONFIG = _A2_MODULE._CANONICAL_LOAD_CONFIG
_A2_LEGACY_VALIDATOR = _A2_MODULE._CANONICAL_LEGACY_VALIDATOR
_A2_PHASE0_FILES = _A2_MODULE._CANONICAL_PHASE0_FROZEN_FILES

_A3_MODULE = amended_orchestrator_compat_v3
_A3_RUN = _A3_MODULE.run
_A3_LOAD_ADAPTER = _A3_MODULE._load_frozen_adapter


class RunnerSchema3CompatibilityError(ValueError):
    """The narrow frozen-runner validator boundary failed closed."""


class _DevelopmentRunAuthorization:
    """Private identity capability for the reviewed active-entrypoint path."""


_DEVELOPMENT_RUN_AUTHORIZATION = _DevelopmentRunAuthorization()


def _canonical_config(root: Path) -> LoadedV2Config:
    return top40_v2.load_config(root / TOP40_V2_LAYOUT.config_path)


def _regular_bytes(path: Path, label: str) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise RunnerSchema3CompatibilityError(f"{label} is missing or unsafe: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RunnerSchema3CompatibilityError(
                f"{label} must be a regular single-link file"
            )
        chunks: list[bytes] = []
        remaining = info.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise RunnerSchema3CompatibilityError(f"{label} changed while read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise RunnerSchema3CompatibilityError(f"{label} grew while read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _verify_amendment_authorities() -> None:
    bindings = (
        (
            _A2_MODULE,
            _AMENDMENT_0002_MODULE_SHA256,
            {
                "_PATCH_LOCK": _A2_PATCH_LOCK,
                "_TournamentContractFacade": _A2_FACADE_TYPE,
                "_read_exact_schema3_state": _A2_READ_STATE,
                "_CANONICAL_CONTRACT": _A2_CANONICAL_CONTRACT,
                "_CANONICAL_LOAD_CONFIG": _A2_LOAD_CONFIG,
                "_CANONICAL_LEGACY_VALIDATOR": _A2_LEGACY_VALIDATOR,
                "_CANONICAL_PHASE0_FROZEN_FILES": _A2_PHASE0_FILES,
            },
            "Amendment 0002 compatibility module",
        ),
        (
            _A3_MODULE,
            _AMENDMENT_0003_MODULE_SHA256,
            {"run": _A3_RUN, "_load_frozen_adapter": _A3_LOAD_ADAPTER},
            "Amendment 0003 status module",
        ),
    )
    for module, expected_sha256, identities, label in bindings:
        payload = _regular_bytes(Path(module.__file__).resolve(), label)
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise RunnerSchema3CompatibilityError(f"{label} bytes changed")
        if any(getattr(module, name, _MISSING) is not value for name, value in identities.items()):
            raise RunnerSchema3CompatibilityError(f"{label} authority changed")


def run_development_window_with_schema3_compatibility(
    *,
    root: str | Path,
    argv: Sequence[str],
    _authorization: object | None = None,
) -> int:
    """Run exactly one frozen ``run-window development`` command."""

    if _authorization is not _DEVELOPMENT_RUN_AUTHORIZATION:
        raise PermissionError(
            "development runner compatibility requires active-entrypoint authority"
        )
    values = list(argv)
    if len(values) < 4 or values[0] != "run-window" or values[1] != "development":
        raise ValueError(
            "Amendment 0004 compatibility requires exact run-window development argv"
        )
    root_path = Path(root).resolve()
    _verify_amendment_authorities()
    adapter = _A3_LOAD_ADAPTER()

    def runner_call() -> int:
        return int(adapter.run(values, root=root_path))

    expected_state_validations = 1
    with _A2_PATCH_LOCK:
        original_contract = getattr(runner_v2, "tournament_contract", _MISSING)
        legacy_validator = top40_v2.validate_run_state
        amended_validator = amendment_v2.validate_amended_run_state
        if original_contract is not _A2_CANONICAL_CONTRACT:
            raise RunnerSchema3CompatibilityError(
                "runner tournament-contract binding was already replaced"
            )
        if (
            legacy_validator is not _A2_LEGACY_VALIDATOR
            or getattr(original_contract, "validate_run_state", None)
            is not _A2_LEGACY_VALIDATOR
            or top40_v2.load_config is not _A2_LOAD_CONFIG
            or top40_v2.PHASE0_FROZEN_FILES is not _A2_PHASE0_FILES
            or amendment_v2.validate_run_state is not legacy_validator
        ):
            raise RunnerSchema3CompatibilityError(
                "runner tournament-contract authority is invalid"
            )
        config = _canonical_config(root_path)
        _A2_READ_STATE(
            root_path,
            config,
            amended_validator=amended_validator,
        )
        successful_validations = 0

        def compatible_validate_run_state(
            state: Mapping[str, Any], candidate_config: LoadedV2Config
        ) -> None:
            nonlocal successful_validations
            if successful_validations >= expected_state_validations:
                raise RunnerSchema3CompatibilityError(
                    "runner repeated amendment-aware state validation"
                )
            if (
                candidate_config.sha256 != config.sha256
                or Path(candidate_config.path).resolve() != Path(config.path).resolve()
                or candidate_config.raw != config.raw
            ):
                raise RunnerSchema3CompatibilityError(
                    "runner validator received a noncanonical V2 config"
                )
            current = _A2_READ_STATE(
                root_path,
                config,
                amended_validator=amended_validator,
            )
            amended_validator(state, candidate_config)
            if pretty_json_bytes(state) != current.payload:
                raise RunnerSchema3CompatibilityError(
                    "runner state differs from current canonical schema-3 bytes"
                )
            successful_validations += 1

        facade = _A2_FACADE_TYPE(
            load_config=_A2_LOAD_CONFIG,
            validate_run_state=compatible_validate_run_state,
            PHASE0_FROZEN_FILES=_A2_PHASE0_FILES,
        )
        result: int | None = None
        failure: BaseException | None = None
        try:
            runner_v2.tournament_contract = facade
            try:
                result = runner_call()
            except BaseException as exc:
                failure = exc
        finally:
            observed_contract = _MISSING
            restored = False
            try:
                observed_contract = getattr(runner_v2, "tournament_contract", _MISSING)
            finally:
                runner_v2.tournament_contract = original_contract
                restored = (
                    getattr(runner_v2, "tournament_contract", _MISSING)
                    is original_contract
                )
            after = _A2_READ_STATE(
                root_path,
                config,
                amended_validator=amended_validator,
            )
            if not after.payload or not restored or observed_contract is not facade:
                raise RunnerSchema3CompatibilityError(
                    "runner tournament-contract binding changed or failed restoration"
                ) from failure
            if (
                top40_v2.validate_run_state is not legacy_validator
                or amendment_v2.validate_run_state is not legacy_validator
                or amendment_v2.validate_amended_run_state is not amended_validator
            ):
                raise RunnerSchema3CompatibilityError(
                    "state validator identity changed during runner execution"
                ) from failure
            _verify_amendment_authorities()
        if failure is not None:
            raise failure.with_traceback(failure.__traceback__)
        if successful_validations != expected_state_validations:
            raise RunnerSchema3CompatibilityError(
                "completed runner call did not traverse the expected state validation"
            )
        if result is None:
            raise RunnerSchema3CompatibilityError(
                "completed development command returned no result"
            )
        return result


def _command(values: Sequence[str]) -> str | None:
    return values[0] if values else None


def _verified_amendment_delegate[T](call: Callable[[], T]) -> T:
    _verify_amendment_authorities()
    result: T | None = None
    failure: BaseException | None = None
    try:
        result = call()
    except BaseException as exc:
        failure = exc
    try:
        _verify_amendment_authorities()
    except BaseException as integrity_failure:
        raise integrity_failure from failure
    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    return result  # type: ignore[return-value]


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Use Amendment 0003 status and add compatibility only for development run-window."""

    working_root = Path.cwd().resolve()
    root_path = working_root if root is None else Path(root).resolve()
    if root_path != working_root:
        raise ValueError("active orchestration root must be the current working directory")
    values = list(sys.argv[1:] if argv is None else argv)
    command = _command(values)
    _verify_amendment_authorities()
    if command == "research-status":
        return _verified_amendment_delegate(lambda: _A3_RUN(values, root=root_path))
    if command == _SUPPORTED_RUNNER_COMMAND:
        if len(values) < 2 or values[1] != "development":
            raise ValueError(
                "Amendment 0004 permits schema-3 runner compatibility only for development"
            )
        return run_development_window_with_schema3_compatibility(
            root=root_path,
            argv=values,
            _authorization=_DEVELOPMENT_RUN_AUTHORIZATION,
        )
    if command == "run-finalist":
        raise ValueError("finalist runner compatibility is not frozen in Amendment 0004")

    def ordinary_call() -> int:
        adapter = _A3_LOAD_ADAPTER()
        return int(adapter.run(None if argv is None else values, root=root_path))

    return _verified_amendment_delegate(ordinary_call)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-active: error: {exc}", file=sys.stderr)
        return 2
