"""Narrow schema-v3 compatibility boundary for organizer score diagnostics.

The frozen V2 runner knows only the legacy schema-v2 run-state validator.  Amendment 0001 keeps
all legacy fields in its schema-v3 state and validates an exact schema-v2 projection, so score
diagnostics need only a validator dispatch at the runner's existing Phase-0 boundary.  This
module does not replace, project, or write the canonical state and does not bypass any of the
runner's remaining Phase-0 checks.
"""

from __future__ import annotations

import dataclasses
import math
import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from crypto_trade.tournament import amendment_v2, runner_v2, top40_v2
from crypto_trade.tournament.amendment_integrity_v2 import (
    pretty_json_bytes,
    read_repo_file,
    sha256_bytes,
    strict_json_object,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config

_RESULT_FIELDS = frozenset(
    {
        "status",
        "failure_reason",
        "organizer_cpu_hours",
        "organizer_wall_clock_hours",
    }
)
_PATCH_LOCK = threading.RLock()
_CANONICAL_CONTRACT = top40_v2
_CANONICAL_LOAD_CONFIG = top40_v2.load_config
_CANONICAL_LEGACY_VALIDATOR = top40_v2.validate_run_state
_CANONICAL_PHASE0_FROZEN_FILES = top40_v2.PHASE0_FROZEN_FILES


class ScoreDiagnosticCompatibilityError(ValueError):
    """The reviewed compatibility boundary could not prove its invariants."""


@dataclasses.dataclass(frozen=True, slots=True)
class _StateSnapshot:
    payload: bytes
    sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class _TournamentContractFacade:
    """The exact three tournament-contract attributes used by the frozen snapshot path."""

    load_config: Callable[[str | Path], LoadedV2Config]
    validate_run_state: Callable[[Mapping[str, Any], LoadedV2Config], None]
    PHASE0_FROZEN_FILES: object


def _load_canonical_config(root: Path) -> LoadedV2Config:
    return top40_v2.load_config(root / TOP40_V2_LAYOUT.config_path)


def _read_exact_schema3_state(
    root: Path,
    config: LoadedV2Config,
    *,
    amended_validator: Callable[[Mapping[str, Any], LoadedV2Config], None],
) -> _StateSnapshot:
    _relative, _path, payload, _stat = read_repo_file(
        root,
        TOP40_V2_LAYOUT.state_path,
        "schema-v3 score-diagnostic run state",
        maximum_bytes=32 * 1024 * 1024,
        require_single_link=True,
    )
    state = strict_json_object(payload, "schema-v3 score-diagnostic run state")
    if (
        state.get("schema_version") != amendment_v2.AMENDMENT_STATE_SCHEMA_VERSION
        or state.get("state_schema") != amendment_v2.AMENDMENT_STATE_SCHEMA_ID
    ):
        raise ScoreDiagnosticCompatibilityError(
            "score diagnostics require the exact amendment-aware schema-v3 state"
        )
    if pretty_json_bytes(state) != payload:
        raise ScoreDiagnosticCompatibilityError(
            "amendment-aware run state is not canonical pretty JSON"
        )
    amended_validator(state, config)
    return _StateSnapshot(payload=payload, sha256=sha256_bytes(payload))


def _finite_nonnegative_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScoreDiagnosticCompatibilityError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ScoreDiagnosticCompatibilityError(f"{label} must be finite and nonnegative")
    return result


def _validate_runner_result(raw: object) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != set(_RESULT_FIELDS):
        raise ScoreDiagnosticCompatibilityError(
            "trusted score-diagnostic runner returned an invalid field set"
        )
    status = raw["status"]
    failure = raw["failure_reason"]
    if status not in {"completed", "failed", "interrupted"}:
        raise ScoreDiagnosticCompatibilityError(
            "trusted score-diagnostic runner returned an invalid status"
        )
    if status == "completed":
        if failure is not None:
            raise ScoreDiagnosticCompatibilityError(
                "completed score diagnostics cannot contain a failure reason"
            )
    elif (
        not isinstance(failure, str)
        or not failure.strip()
        or failure != failure.strip()
        or len(failure) > 8000
    ):
        raise ScoreDiagnosticCompatibilityError(
            "failed or interrupted score diagnostics require a bounded failure reason"
        )
    return {
        "status": status,
        "failure_reason": failure,
        "organizer_cpu_hours": _finite_nonnegative_number(
            raw["organizer_cpu_hours"], "organizer_cpu_hours"
        ),
        "organizer_wall_clock_hours": _finite_nonnegative_number(
            raw["organizer_wall_clock_hours"], "organizer_wall_clock_hours"
        ),
    }


def run_score_diagnostic_with_schema3_compatibility(
    *,
    root: str | Path,
    runner_call: Callable[[], object],
) -> Mapping[str, Any]:
    """Invoke the existing reserved runner under one validated in-memory facade.

    ``runner_call`` must perform the existing ``run_reserved_score_diagnostic`` invocation.  The
    callable form keeps reservation and private-output authority in the amendment lifecycle; this
    boundary changes only the frozen runner's local view of the run-state validator.
    """

    if not callable(runner_call):
        raise TypeError("runner_call must be callable")
    root_path = Path(root).resolve()
    with _PATCH_LOCK:
        original_contract = runner_v2.tournament_contract
        legacy_validator = top40_v2.validate_run_state
        amended_validator = amendment_v2.validate_amended_run_state
        if original_contract is not _CANONICAL_CONTRACT:
            raise ScoreDiagnosticCompatibilityError(
                "runner tournament-contract binding was already replaced"
            )
        if (
            legacy_validator is not _CANONICAL_LEGACY_VALIDATOR
            or getattr(original_contract, "validate_run_state", None)
            is not _CANONICAL_LEGACY_VALIDATOR
            or top40_v2.load_config is not _CANONICAL_LOAD_CONFIG
            or top40_v2.PHASE0_FROZEN_FILES is not _CANONICAL_PHASE0_FROZEN_FILES
        ):
            raise ScoreDiagnosticCompatibilityError(
                "runner legacy tournament-contract identity is invalid"
            )
        if getattr(amendment_v2, "validate_run_state", None) is not legacy_validator:
            raise ScoreDiagnosticCompatibilityError(
                "amendment legacy projection validator identity is invalid"
            )

        config = _load_canonical_config(root_path)
        before = _read_exact_schema3_state(
            root_path,
            config,
            amended_validator=amended_validator,
        )

        successful_state_validations = 0

        def compatible_validate_run_state(
            state: Mapping[str, Any], candidate_config: LoadedV2Config
        ) -> None:
            nonlocal successful_state_validations
            if successful_state_validations:
                raise ScoreDiagnosticCompatibilityError(
                    "runner repeated amendment-aware state validation"
                )
            if not isinstance(state, Mapping):
                raise ScoreDiagnosticCompatibilityError(
                    "runner loaded a non-mapping amendment-aware state"
                )
            if (
                state.get("schema_version") != amendment_v2.AMENDMENT_STATE_SCHEMA_VERSION
                or state.get("state_schema") != amendment_v2.AMENDMENT_STATE_SCHEMA_ID
            ):
                raise ScoreDiagnosticCompatibilityError(
                    "runner did not load the exact amendment-aware schema-v3 state"
                )
            if (
                candidate_config.sha256 != config.sha256
                or Path(candidate_config.path).resolve() != Path(config.path).resolve()
                or candidate_config.raw != config.raw
            ):
                raise ScoreDiagnosticCompatibilityError(
                    "runner validator received a noncanonical V2 config"
                )
            amended_validator(state, candidate_config)
            if pretty_json_bytes(state) != before.payload:
                raise ScoreDiagnosticCompatibilityError(
                    "runner loaded state bytes different from the validated schema-v3 state"
                )
            successful_state_validations += 1

        facade = _TournamentContractFacade(
            load_config=_CANONICAL_LOAD_CONFIG,
            validate_run_state=compatible_validate_run_state,
            PHASE0_FROZEN_FILES=_CANONICAL_PHASE0_FROZEN_FILES,
        )

        raw_result: object
        try:
            runner_v2.tournament_contract = facade
            try:
                raw_result = runner_call()
            finally:
                observed_contract = runner_v2.tournament_contract
                runner_v2.tournament_contract = original_contract
                if runner_v2.tournament_contract is not original_contract:
                    raise ScoreDiagnosticCompatibilityError(
                        "runner tournament-contract identity could not be restored"
                    )
                if observed_contract is not facade:
                    raise ScoreDiagnosticCompatibilityError(
                        "runner tournament-contract binding changed during diagnostics"
                    )
                if (
                    top40_v2.validate_run_state is not legacy_validator
                    or amendment_v2.validate_run_state is not legacy_validator
                    or amendment_v2.validate_amended_run_state is not amended_validator
                ):
                    raise ScoreDiagnosticCompatibilityError(
                        "state validator identity changed during diagnostics"
                    )
        finally:
            after = _read_exact_schema3_state(
                root_path,
                config,
                amended_validator=amended_validator,
            )
            if after.payload != before.payload or after.sha256 != before.sha256:
                raise ScoreDiagnosticCompatibilityError(
                    "canonical amendment-aware run state changed during diagnostics"
                )

        result = _validate_runner_result(raw_result)
        if result["status"] == "completed" and successful_state_validations != 1:
            raise ScoreDiagnosticCompatibilityError(
                "completed diagnostics did not traverse the frozen Phase-0 state validator"
            )
        return result
