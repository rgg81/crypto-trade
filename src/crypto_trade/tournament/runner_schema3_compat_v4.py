"""Schema-3 validator compatibility for frozen Top-40 V2 development runs."""

from __future__ import annotations

import hashlib
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
_SUPPORTED_RUNNER_COMMAND = "run-window"


class RunnerSchema3CompatibilityError(ValueError):
    """The narrow frozen-runner validator boundary failed closed."""


def _canonical_config(root: Path) -> LoadedV2Config:
    return top40_v2.load_config(root / TOP40_V2_LAYOUT.config_path)


def run_with_schema3_runner_compatibility[T](
    *,
    root: str | Path,
    runner_call: Callable[[], T],
    expected_state_validations: int = 1,
) -> T:
    """Run one frozen development window with schema-3 state validation dispatch."""

    if not callable(runner_call):
        raise TypeError("runner_call must be callable")
    if (
        isinstance(expected_state_validations, bool)
        or not isinstance(expected_state_validations, int)
        or expected_state_validations < 1
    ):
        raise ValueError("expected_state_validations must be a positive integer")
    root_path = Path(root).resolve()
    compatibility = score_diagnostic_compat_v2
    with compatibility._PATCH_LOCK:
        original_contract = runner_v2.tournament_contract
        legacy_validator = top40_v2.validate_run_state
        amended_validator = amendment_v2.validate_amended_run_state
        if original_contract is not compatibility._CANONICAL_CONTRACT:
            raise RunnerSchema3CompatibilityError(
                "runner tournament-contract binding was already replaced"
            )
        if (
            legacy_validator is not compatibility._CANONICAL_LEGACY_VALIDATOR
            or getattr(original_contract, "validate_run_state", None)
            is not compatibility._CANONICAL_LEGACY_VALIDATOR
            or top40_v2.load_config is not compatibility._CANONICAL_LOAD_CONFIG
            or top40_v2.PHASE0_FROZEN_FILES
            is not compatibility._CANONICAL_PHASE0_FROZEN_FILES
            or amendment_v2.validate_run_state is not legacy_validator
        ):
            raise RunnerSchema3CompatibilityError(
                "runner tournament-contract authority is invalid"
            )
        config = _canonical_config(root_path)
        compatibility._read_exact_schema3_state(
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
            current = compatibility._read_exact_schema3_state(
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

        facade = compatibility._TournamentContractFacade(
            load_config=compatibility._CANONICAL_LOAD_CONFIG,
            validate_run_state=compatible_validate_run_state,
            PHASE0_FROZEN_FILES=compatibility._CANONICAL_PHASE0_FROZEN_FILES,
        )
        result: T | None = None
        failure: BaseException | None = None
        try:
            runner_v2.tournament_contract = facade
            try:
                result = runner_call()
            except BaseException as exc:
                failure = exc
        finally:
            observed_contract = runner_v2.tournament_contract
            runner_v2.tournament_contract = original_contract
            restored = runner_v2.tournament_contract is original_contract
            after = compatibility._read_exact_schema3_state(
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
        if failure is not None:
            raise failure.with_traceback(failure.__traceback__)
        if successful_validations != expected_state_validations:
            raise RunnerSchema3CompatibilityError(
                "completed runner call did not traverse the expected state validation"
            )
        return result  # type: ignore[return-value]


def _command(values: Sequence[str]) -> str | None:
    return values[0] if values else None


def _verify_amendment_0003_authority() -> None:
    path = Path(amended_orchestrator_compat_v3.__file__).resolve()
    payload = amended_orchestrator_compat_v3._regular_bytes(
        path,
        "Amendment 0003 status module",
    )
    if hashlib.sha256(payload).hexdigest() != _AMENDMENT_0003_MODULE_SHA256:
        raise RunnerSchema3CompatibilityError("Amendment 0003 status bytes changed")


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Use Amendment 0003 status and add compatibility only for development run-window."""

    working_root = Path.cwd().resolve()
    root_path = working_root if root is None else Path(root).resolve()
    if root_path != working_root:
        raise ValueError("active orchestration root must be the current working directory")
    values = list(sys.argv[1:] if argv is None else argv)
    command = _command(values)
    _verify_amendment_0003_authority()
    if command == "research-status":
        return amended_orchestrator_compat_v3.run(values, root=root_path)
    adapter = amended_orchestrator_compat_v3._load_frozen_adapter()

    def call() -> int:
        return int(adapter.run(None if argv is None else values, root=root_path))
    if command == _SUPPORTED_RUNNER_COMMAND:
        if len(values) < 2 or values[1] != "development":
            raise ValueError(
                "Amendment 0004 permits schema-3 runner compatibility only for development"
            )
        return run_with_schema3_runner_compatibility(root=root_path, runner_call=call)
    if command == "run-finalist":
        raise ValueError("finalist runner compatibility is not frozen in Amendment 0004")
    return call()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-active: error: {exc}", file=sys.stderr)
        return 2
