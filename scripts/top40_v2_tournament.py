#!/usr/bin/env python3
"""Lifecycle controls for the isolated Top-40 V2 qualification tournament."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.qualification import (
    QualificationAssessment,
    assess_development,
    assess_private,
)
from crypto_trade.tournament.risk_policy import load_risk_policy
from crypto_trade.tournament.top40_v2 import (
    PHASE0_FROZEN_FILES,
    TEAM_IDS,
    LoadedV2Config,
    all_teams_terminal_for_qualification,
    finalist_team_ids,
    load_config,
    new_run_state,
    read_run_state,
    validate_run_state,
)

DEFAULT_CONFIG = TOP40_V2_LAYOUT.config_path
QUALIFICATION_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/qualification_lock.json"
PRIVATE_ROOT = f"{TOP40_V2_LAYOUT.tournament_root}/private"
_FAMILY_KEYS = {
    "schema_version",
    "team_id",
    "family_id",
    "parent_family_id",
    "registered_at_utc",
    "mechanism",
    "economic_thesis",
    "expected_regime_roles",
    "falsifier",
    "parameter_ranges",
    "selection_metric",
    "risk_policy_plan",
}
_REGIME_ROLE_KEYS = {"bull", "bear", "chop", "stress", "long_sleeve", "short_sleeve"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_write_json(path: Path, payload: object) -> None:
    _atomic_write_bytes(path, _json_bytes(payload))


def _first_add_json(path: Path, payload: object) -> str:
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to replace immutable lock: {path}")
    root = Path.cwd().resolve()
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("immutable locks must remain inside the tournament repository") from exc
    repository = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if repository.returncode == 0 and repository.stdout.strip() == "true":
        history = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if history.returncode or history.stdout.strip():
            raise ValueError(f"immutable lock path already exists in Git history: {relative}")
    encoded = _json_bytes(payload)
    _atomic_write_bytes(path, encoded)
    return _sha256_bytes(encoded)


def _read_json(path: str | Path, label: str) -> tuple[dict[str, Any], bytes]:
    source = Path(path)
    try:
        payload = source.read_bytes()
        raw = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{label} root must be a JSON object")
    return raw, payload


def _config(root: Path, path: str) -> LoadedV2Config:
    candidate = Path(path)
    return load_config(candidate if candidate.is_absolute() else root / candidate)


def _state_path(root: Path) -> Path:
    return root / TOP40_V2_LAYOUT.state_path


def _state_lock_path(root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "top40-v2-run-state.lock"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        path = Path(result.stdout.strip())
        return path if path.is_absolute() else root / path
    return root / TOP40_V2_LAYOUT.state_lock_path


@contextmanager
def _edit_state(root: Path, config: LoadedV2Config) -> Iterator[dict[str, Any]]:
    """Serialize one validated state transition and commit it atomically."""
    lock_path = _state_lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = read_run_state(root, config)
        yield state
        validate_run_state(state, config)
        _atomic_write_json(_state_path(root), state)


def _emit(payload: object, json_out: str | None = None) -> None:
    encoded = json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    if json_out:
        Path(json_out).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


def _require_phase(state: Mapping[str, Any], *allowed: str) -> None:
    if state.get("phase") not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"command requires run phase {choices}; found {state.get('phase')!r}")


def _team(state: Mapping[str, Any], team_id: str) -> dict[str, Any]:
    TOP40_V2_LAYOUT.require_team(team_id)
    teams = state.get("teams")
    if not isinstance(teams, dict) or not isinstance(teams.get(team_id), dict):
        raise ValueError(f"run state is missing {team_id}")
    return teams[team_id]


def _nonempty_text(value: Any, label: str, *, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"{label} must contain at most {maximum} characters")
    return value


def _utc_timestamp(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} must be timezone-aware UTC")
    return text


def _validate_family_registration(
    raw: Mapping[str, Any], *, team_id: str, expected_parent: str | None
) -> dict[str, Any]:
    if set(raw) != _FAMILY_KEYS:
        missing = sorted(_FAMILY_KEYS - set(raw))
        extra = sorted(set(raw) - _FAMILY_KEYS)
        raise ValueError(f"family registration has invalid keys; missing={missing}, extra={extra}")
    if raw["schema_version"] != 1 or raw["team_id"] != team_id:
        raise ValueError("family registration identity is invalid")
    family_id = _nonempty_text(raw["family_id"], "family_id", maximum=128)
    if raw["parent_family_id"] != expected_parent:
        raise ValueError(f"parent_family_id must equal {expected_parent!r}")
    _utc_timestamp(raw["registered_at_utc"], "registered_at_utc")
    for field in (
        "mechanism",
        "economic_thesis",
        "falsifier",
        "selection_metric",
        "risk_policy_plan",
    ):
        _nonempty_text(raw[field], field)
    roles = raw["expected_regime_roles"]
    if not isinstance(roles, Mapping) or set(roles) != _REGIME_ROLE_KEYS:
        raise ValueError("expected_regime_roles must contain all six canonical roles exactly")
    for role, value in roles.items():
        _nonempty_text(value, f"expected_regime_roles.{role}")
    parameters = raw["parameter_ranges"]
    if not isinstance(parameters, Mapping) or not parameters:
        raise ValueError("parameter_ranges must be a non-empty JSON object")
    # Normalize only the mapping type; the submitted values remain byte-for-byte meaningful JSON.
    normalized = dict(raw)
    normalized["family_id"] = family_id
    return normalized


def _family_ledger(root: Path, team_id: str) -> Path:
    return root / TOP40_V2_LAYOUT.team_root(team_id) / "families.jsonl"


def _read_families(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_bytes().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid family ledger line {number}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"family ledger line {number} must be a JSON object")
        rows.append(raw)
    ids = [row.get("family_id") for row in rows]
    if any(not isinstance(value, str) for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("family ledger contains invalid or duplicate family ids")
    return rows


def _append_family(path: Path, raw: Mapping[str, Any]) -> bytes:
    previous = path.read_bytes() if path.exists() else b""
    if previous and not previous.endswith(b"\n"):
        raise ValueError("family ledger must end with a newline")
    encoded = json.dumps(
        raw, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8") + b"\n"
    _atomic_write_bytes(path, previous + encoded)
    return previous


def _register_family(args: argparse.Namespace, *, pivot: bool) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, _payload = _read_json(args.registration, "family registration")
    ledger_path = _family_ledger(root, args.team_id)
    old_ledger: bytes | None = None
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "research")
            team = _team(state, args.team_id)
            if team["status"] not in {"pending_phase0", "researching"}:
                raise ValueError(f"{args.team_id} cannot register a family in {team['status']!r}")
            families = _read_families(ledger_path)
            if len(families) != team["family_count"]:
                raise ValueError("family ledger and run-state counts differ")
            expected_parent = team["active_family_id"] if pivot else None
            if pivot:
                if team["family_count"] < 1 or expected_parent is None:
                    raise ValueError("a pivot requires an existing active mechanism family")
                maximum = config.raw["research_budget"]["maximum_mechanism_pivots_per_team"]
                if team["pivot_count"] >= maximum:
                    raise ValueError(f"{args.team_id} exhausted its mechanism-pivot budget")
            elif team["family_count"] != 0:
                raise ValueError("the initial family already exists; use pivot-team")
            registration = _validate_family_registration(
                raw, team_id=args.team_id, expected_parent=expected_parent
            )
            if registration["family_id"] in {item["family_id"] for item in families}:
                raise ValueError("family_id has already been registered")
            team["status"] = "researching"
            team["active_family_id"] = registration["family_id"]
            team["family_count"] += 1
            if pivot:
                team["pivot_count"] += 1
            validate_run_state(state, config)
            old_ledger = _append_family(ledger_path, registration)
    except Exception:
        if old_ledger is not None:
            _atomic_write_bytes(ledger_path, old_ledger)
        raise
    _emit(
        {
            "team_id": args.team_id,
            "family_id": raw["family_id"],
            "event": "pivoted" if pivot else "registered",
        },
        args.json_out,
    )
    return 0


def _assessment(
    raw: Mapping[str, Any], payload: bytes, config: LoadedV2Config, stage: str
) -> QualificationAssessment:
    if raw.get("config_sha256") != config.sha256:
        raise ValueError("qualification evidence is not bound to the current V2 config")
    digest = _sha256_bytes(payload)
    if stage == "development":
        return assess_development(raw, config.qualification_thresholds, evidence_sha256=digest)
    if stage == "private":
        return assess_private(raw, config.qualification_thresholds, evidence_sha256=digest)
    raise ValueError("qualification stage must be development or private")


def _identity_bindings(
    root: Path,
    config: LoadedV2Config,
    team_id: str,
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    if raw.get("team_id") != team_id:
        raise ValueError("qualification evidence team_id differs from the command")
    candidate_id = _nonempty_text(raw.get("candidate_id"), "candidate_id", maximum=128)
    trial_count = raw.get("trial_count")
    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise ValueError("trial_count must be a positive integer")
    maximum = config.raw["research_budget"]["maximum_material_configurations_per_team"]
    if trial_count > maximum:
        raise ValueError(f"trial_count exceeds the cumulative budget of {maximum}")
    team_root = root / TOP40_V2_LAYOUT.team_root(team_id)
    strategy_path = team_root / "strategy.py"
    risk_path = team_root / "risk_policy.json"
    try:
        strategy_sha256 = _sha256_bytes(strategy_path.read_bytes())
        risk_payload = risk_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"candidate source is incomplete: {exc}") from exc
    load_risk_policy(risk_path)
    risk_sha256 = _sha256_bytes(risk_payload)
    if raw.get("strategy_sha256") != strategy_sha256:
        raise ValueError("qualification evidence strategy_sha256 differs from strategy.py")
    if raw.get("risk_policy_sha256") != risk_sha256:
        raise ValueError("qualification evidence risk_policy_sha256 differs from risk_policy.json")
    return {
        "candidate_id": candidate_id,
        "strategy_sha256": strategy_sha256,
        "risk_policy_sha256": risk_sha256,
        "config_sha256": config.sha256,
        "trial_count": trial_count,
    }


def _assessment_output(
    assessment: QualificationAssessment, *, include_observations: bool
) -> dict[str, object]:
    result = assessment.to_dict(include_observations=include_observations)
    if assessment.stage == "private" and not include_observations:
        result["feedback_mode"] = "pass-fail-only"
    return result


def _assess_qualification(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, payload = _read_json(args.evidence, "qualification evidence")
    assessment = _assessment(raw, payload, config, args.stage)
    include = args.stage == "development" or args.include_private_observations
    _emit(_assessment_output(assessment, include_observations=include), args.json_out)
    return 0 if assessment.passed else 1


def _record_development_assessment(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, payload = _read_json(args.evidence, "development qualification evidence")
    assessment = _assessment(raw, payload, config, "development")
    bindings = _identity_bindings(root, config, args.team_id, raw)
    output = _assessment_output(assessment, include_observations=True)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, args.team_id)
        if team["status"] not in {"pending_phase0", "researching"}:
            raise ValueError(f"development assessment is closed for {args.team_id}")
        if team["family_count"] < 1 or team["active_family_id"] is None:
            raise ValueError("development assessment requires a preregistered mechanism family")
        previous = team["development_assessment"]
        if (
            isinstance(previous, Mapping)
            and previous.get("evidence_sha256") == assessment.evidence_sha256
        ):
            _emit(previous, args.json_out)
            return 0 if previous.get("passed") is True else 1
        if bindings["trial_count"] <= team["trial_count"]:
            raise ValueError("a new assessment must advance the cumulative trial count")
        record = {**output, "recorded_at_utc": _now()}
        team["trial_count"] = bindings["trial_count"]
        team["development_assessment"] = record
        if assessment.passed:
            canonical = root / TOP40_V2_LAYOUT.report_root(args.team_id) / (
                "development_qualification_evidence.json"
            )
            if canonical.is_symlink():
                raise ValueError("canonical development evidence path cannot be a symlink")
            if canonical.exists() and canonical.read_bytes() != payload:
                raise ValueError("refusing to replace canonical passing development evidence")
            _atomic_write_bytes(canonical, payload)
            team["qualifier_candidate"] = {
                **bindings,
                "development_evidence_path": canonical.relative_to(root).as_posix(),
                "development_evidence_sha256": assessment.evidence_sha256,
            }
            team["status"] = "qualifier_candidate_frozen"
    _emit(output, args.json_out)
    return 0 if assessment.passed else 1


def _record_private_assessment(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, payload = _read_json(args.evidence, "private qualification evidence")
    assessment = _assessment(raw, payload, config, "private")
    bindings = _identity_bindings(root, config, args.team_id, raw)
    public = _assessment_output(assessment, include_observations=False)
    sealed_path = root / PRIVATE_ROOT / f"{args.team_id}.json"
    created_sealed = False
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "research")
            team = _team(state, args.team_id)
            if team["status"] != "qualifier_candidate_frozen":
                raise ValueError(
                    "private assessment requires a passing frozen development candidate"
                )
            if team["private_attempts"] != 0:
                raise ValueError(f"{args.team_id} already consumed its one private ticket")
            candidate = team["qualifier_candidate"]
            if not isinstance(candidate, Mapping) or any(
                candidate.get(field) != bindings[field]
                for field in (
                    "candidate_id",
                    "strategy_sha256",
                    "risk_policy_sha256",
                    "config_sha256",
                    "trial_count",
                )
            ):
                raise ValueError("private evidence differs from the frozen development candidate")
            sealed = {
                "schema_version": 1,
                "sealed_at_utc": _now(),
                "evidence": raw,
                "assessment": assessment.to_dict(include_observations=True),
            }
            sealed_sha256 = _first_add_json(sealed_path, sealed)
            created_sealed = True
            result = {
                **public,
                "sealed_record_path": sealed_path.relative_to(root).as_posix(),
                "sealed_record_sha256": sealed_sha256,
            }
            team["private_attempts"] = 1
            team["private_result"] = result
            if assessment.passed:
                team["status"] = "qualified"
            else:
                team["status"] = "dnf"
                team["dnf"] = {
                    "reason_code": "private-qualification-failed",
                    "reason": "one-shot private qualification failed",
                    "recorded_at_utc": _now(),
                }
    except Exception:
        if created_sealed:
            sealed_path.unlink(missing_ok=True)
        raise
    _emit(public, args.json_out)
    return 0 if assessment.passed else 1


def _withdraw_team(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    reason = _nonempty_text(args.reason, "reason", maximum=1000)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, args.team_id)
        if team["status"] in {"qualified", "dnf", "finalist_frozen"}:
            raise ValueError(f"cannot withdraw {args.team_id} from {team['status']!r}")
        previous_status = team["status"]
        team["status"] = "dnf"
        team["dnf"] = {
            "reason_code": "withdrawn",
            "reason": reason,
            "previous_status": previous_status,
            "recorded_at_utc": _now(),
        }
    _emit({"team_id": args.team_id, "status": "dnf", "reason": reason}, args.json_out)
    return 0


def _qualification_summary(state: Mapping[str, Any]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for team_id in TEAM_IDS:
        team = state["teams"][team_id]
        private = team["private_result"]
        dnf = team["dnf"]
        candidate = team["qualifier_candidate"]
        summary[team_id] = {
            "status": team["status"],
            "candidate_id": (
                candidate.get("candidate_id") if isinstance(candidate, Mapping) else None
            ),
            "development_passed": bool(
                isinstance(team["development_assessment"], Mapping)
                and team["development_assessment"].get("passed") is True
            ),
            "private_passed": (
                private.get("passed") if isinstance(private, Mapping) else None
            ),
            "dnf_reason_code": (
                dnf.get("reason_code") if isinstance(dnf, Mapping) else None
            ),
        }
    return summary


def _close_qualification(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    lock_path = root / QUALIFICATION_LOCK_PATH
    created_lock = False
    qualified: tuple[str, ...] = ()
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "research")
            for team_id in TEAM_IDS:
                team = _team(state, team_id)
                if team["status"] in {"qualified", "dnf"}:
                    continue
                previous_status = team["status"]
                team["status"] = "dnf"
                team["dnf"] = {
                    "reason_code": "qualification-closed-unqualified",
                    "reason": "qualification closed before the team qualified",
                    "previous_status": previous_status,
                    "recorded_at_utc": _now(),
                }
            if not all_teams_terminal_for_qualification(state):
                raise ValueError("qualification cannot close until every team is qualified or DNF")
            qualified = finalist_team_ids(state)
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "config_sha256": config.sha256,
                "closed_at_utc": _now(),
                "qualified_team_ids": list(qualified),
                "dnf_team_ids": [team_id for team_id in TEAM_IDS if team_id not in qualified],
                "teams": _qualification_summary(state),
            }
            digest = _first_add_json(lock_path, payload)
            created_lock = True
            state["qualification_lock"] = {
                "path": lock_path.relative_to(root).as_posix(),
                "sha256": digest,
            }
            state["phase"] = "qualification_closed"
    except Exception:
        if created_lock:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": "qualification_closed",
            "qualified_team_ids": list(qualified),
            "qualification_lock": lock_path.relative_to(root).as_posix(),
        },
        args.json_out,
    )
    return 0


def _verify_file_binding(root: Path, binding: Any, expected_path: str, label: str) -> str:
    if not isinstance(binding, Mapping) or binding.get("path") != expected_path:
        raise ValueError(f"{label} state binding is missing or noncanonical")
    path = root / expected_path
    try:
        digest = _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ValueError(f"{label} is missing: {exc}") from exc
    if binding.get("sha256") != digest:
        raise ValueError(f"{label} bytes differ from the run-state binding")
    return digest


def _verify_qualified_candidate(root: Path, team_id: str, team: Mapping[str, Any]) -> None:
    candidate = team.get("qualifier_candidate")
    private = team.get("private_result")
    if not isinstance(candidate, Mapping) or not isinstance(private, Mapping):
        raise ValueError(f"qualified candidate bindings are missing for {team_id}")
    team_root = root / TOP40_V2_LAYOUT.team_root(team_id)
    strategy_path = team_root / "strategy.py"
    risk_path = team_root / "risk_policy.json"
    try:
        strategy_sha256 = _sha256_bytes(strategy_path.read_bytes())
        risk_sha256 = _sha256_bytes(risk_path.read_bytes())
    except OSError as exc:
        raise ValueError(f"qualified candidate source is missing for {team_id}: {exc}") from exc
    load_risk_policy(risk_path)
    if candidate.get("strategy_sha256") != strategy_sha256:
        raise ValueError(f"qualified strategy changed after development freeze: {team_id}")
    if candidate.get("risk_policy_sha256") != risk_sha256:
        raise ValueError(f"qualified risk policy changed after development freeze: {team_id}")
    expected_development_path = (
        f"{TOP40_V2_LAYOUT.report_root(team_id)}/development_qualification_evidence.json"
    )
    if candidate.get("development_evidence_path") != expected_development_path:
        raise ValueError(f"development evidence path is noncanonical for {team_id}")
    development_path = root / expected_development_path
    if (
        not development_path.is_file()
        or development_path.is_symlink()
        or candidate.get("development_evidence_sha256")
        != _sha256_bytes(development_path.read_bytes())
    ):
        raise ValueError(f"development evidence changed after qualification: {team_id}")
    expected_private_path = f"{PRIVATE_ROOT}/{team_id}.json"
    if private.get("sealed_record_path") != expected_private_path:
        raise ValueError(f"private sealed-record path is noncanonical for {team_id}")
    private_path = root / expected_private_path
    if (
        not private_path.is_file()
        or private_path.is_symlink()
        or private.get("sealed_record_sha256") != _sha256_bytes(private_path.read_bytes())
    ):
        raise ValueError(f"private sealed record changed after qualification: {team_id}")


def _lock_finalist_cohort(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    cohort_path = root / TOP40_V2_LAYOUT.finalist_cohort_lock_path
    created_lock = False
    finalists: tuple[str, ...] = ()
    terminal_phase = "finalist_cohort_frozen"
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "qualification_closed")
            qualification_sha256 = _verify_file_binding(
                root, state["qualification_lock"], QUALIFICATION_LOCK_PATH, "qualification lock"
            )
            if not all_teams_terminal_for_qualification(state):
                raise ValueError("the finalist cohort requires ten terminal qualification records")
            finalists = finalist_team_ids(state)
            for team_id in finalists:
                _verify_qualified_candidate(root, team_id, state["teams"][team_id])
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "config_sha256": config.sha256,
                "qualification_lock_sha256": qualification_sha256,
                "locked_at_utc": _now(),
                "finalist_team_ids": list(finalists),
                "dnf_team_ids": [team_id for team_id in TEAM_IDS if team_id not in finalists],
                "teams": {
                    team_id: {
                        "qualification_status": state["teams"][team_id]["status"],
                        "qualifier_candidate": state["teams"][team_id]["qualifier_candidate"],
                        "private_result": state["teams"][team_id]["private_result"],
                        "dnf": state["teams"][team_id]["dnf"],
                    }
                    for team_id in TEAM_IDS
                },
            }
            digest = _first_add_json(cohort_path, payload)
            created_lock = True
            state["finalist_cohort_lock"] = {
                "path": TOP40_V2_LAYOUT.finalist_cohort_lock_path,
                "sha256": digest,
                "finalist_team_ids": list(finalists),
            }
            if finalists:
                for team_id in finalists:
                    state["teams"][team_id]["status"] = "finalist_frozen"
            else:
                terminal_phase = "no_qualified_model"
            state["phase"] = terminal_phase
    except Exception:
        if created_lock:
            cohort_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": terminal_phase,
            "finalist_team_ids": list(finalists),
            "finalist_cohort_lock": TOP40_V2_LAYOUT.finalist_cohort_lock_path,
        },
        args.json_out,
    )
    return 0


def _validate_config_command(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    _emit(
        {
            "valid": True,
            "tournament": TOP40_V2_LAYOUT.name,
            "config_path": TOP40_V2_LAYOUT.config_path,
            "config_sha256": config.sha256,
            "teams": list(TEAM_IDS),
        },
        args.json_out,
    )
    return 0


def _git_output(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"git {' '.join(arguments)} failed") from exc
    return result.stdout.strip()


def _phase0_frozen_hashes(root: Path, common_commit: str) -> dict[str, str]:
    frozen_paths = PHASE0_FROZEN_FILES
    excluded = {TOP40_V2_LAYOUT.state_path, TOP40_V2_LAYOUT.phase0_freeze_path}
    if excluded & set(frozen_paths):
        raise ValueError("mutable state or Phase-0 record cannot be a frozen common input")
    hashes: dict[str, str] = {}
    dirty = _git_output(root, "status", "--porcelain", "--", *frozen_paths)
    if dirty:
        raise ValueError("commit every Phase-0 frozen input before freezing the tournament")
    for relative in frozen_paths:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Phase-0 frozen input is missing or unsafe: {relative}")
        try:
            committed = subprocess.run(
                ["git", "show", f"{common_commit}:{relative}"],
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError(f"Phase-0 frozen input is not committed: {relative}") from exc
        current = path.read_bytes()
        if committed != current:
            raise ValueError(f"Phase-0 frozen input differs from {common_commit}: {relative}")
        hashes[relative] = _sha256_bytes(current)
    return hashes


def _pristine_phase0_team(team: Mapping[str, Any]) -> bool:
    return bool(
        team.get("status") == "pending_phase0"
        and team.get("active_family_id") is None
        and team.get("family_count") == 0
        and team.get("pivot_count") == 0
        and team.get("trial_count") == 0
        and team.get("development_assessment") is None
        and team.get("qualifier_candidate") is None
        and team.get("private_attempts") == 0
        and team.get("private_result") is None
        and team.get("dnf") is None
        and team.get("finalist_freeze") is None
        and team.get("canonical_result") is None
    )


def _freeze_phase0(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.snapshot import verify_snapshot_manifest

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    branch = _git_output(root, "branch", "--show-current")
    if branch != TOP40_V2_LAYOUT.branch:
        raise ValueError(f"Phase 0 may freeze only on branch {TOP40_V2_LAYOUT.branch}")
    freeze_path = root / TOP40_V2_LAYOUT.phase0_freeze_path
    if freeze_path.exists() or freeze_path.is_symlink():
        raise ValueError("Phase 0 is single-shot; phase0_freeze.json already exists")
    state = read_run_state(root, config)
    _require_phase(state, "phase0_pending")
    if state["phase0"] is not None or any(
        not _pristine_phase0_team(_team(state, team_id)) for team_id in TEAM_IDS
    ):
        raise ValueError("Phase 0 requires ten pristine pending team records")
    if _git_output(root, "status", "--porcelain"):
        raise ValueError("commit the pristine V2 namespace and every common input before Phase 0")
    common_commit = _git_output(root, "rev-parse", "HEAD")
    if len(common_commit) != 40 or any(
        character not in "0123456789abcdef" for character in common_commit
    ):
        raise ValueError("Phase-0 common commit must be a full SHA-1 commit id")
    frozen_files = _phase0_frozen_hashes(root, common_commit)
    manifest_relative = config.raw["paths"]["shared_snapshot_manifest"]
    manifest_path = root / manifest_relative
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("the shared snapshot manifest is missing or unsafe")
    manifest_payload = manifest_path.read_bytes()
    manifest_dirty = _git_output(root, "status", "--porcelain", "--", manifest_relative)
    if manifest_dirty:
        raise ValueError("commit the shared snapshot manifest before Phase 0")
    try:
        committed_manifest = subprocess.run(
            ["git", "show", f"{common_commit}:{manifest_relative}"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("the shared snapshot manifest is not committed") from exc
    if committed_manifest != manifest_payload:
        raise ValueError("the shared snapshot manifest differs from the common commit")
    # This is intentionally the full provenance/file audit. The runner may use its Phase-0
    # fast path only because these exact manifest bytes were exhaustively verified here.
    verify_snapshot_manifest(manifest_path)
    created_freeze = False
    payload: dict[str, object] = {}
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "phase0_pending")
            if state["phase0"] is not None or any(
                not _pristine_phase0_team(_team(state, team_id)) for team_id in TEAM_IDS
            ):
                raise ValueError("Phase 0 requires ten pristine pending team records")
            payload = {
                "schema_version": 2,
                "frozen_at_utc": _now(),
                "branch": TOP40_V2_LAYOUT.branch,
                "common_freeze_commit": common_commit,
                "config_sha256": config.sha256,
                "shared_snapshot_manifest_path": manifest_relative,
                "shared_snapshot_manifest_sha256": _sha256_bytes(manifest_payload),
                "frozen_files": frozen_files,
            }
            freeze_sha256 = _first_add_json(freeze_path, payload)
            created_freeze = True
            state["phase0"] = {
                "path": TOP40_V2_LAYOUT.phase0_freeze_path,
                "sha256": freeze_sha256,
            }
            state["phase"] = "research"
            for team_id in TEAM_IDS:
                state["teams"][team_id]["status"] = "researching"
    except Exception:
        if created_freeze:
            freeze_path.unlink(missing_ok=True)
        raise
    _emit(payload, args.json_out)
    return 0


def _init_teams(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    state_path = _state_path(root)
    if state_path.exists() and not args.force:
        raise ValueError("V2 run state already exists; use --force only for a deliberate reset")
    template_path = root / TOP40_V2_LAYOUT.tournament_root / "templates/risk-policy.json"
    risk_template, _ = _read_json(template_path, "risk-policy template")
    for team_id in TEAM_IDS:
        team_root = root / TOP40_V2_LAYOUT.team_root(team_id)
        report_root = root / TOP40_V2_LAYOUT.report_root(team_id)
        team_root.mkdir(parents=True, exist_ok=True)
        report_root.mkdir(parents=True, exist_ok=True)
        risk_path = team_root / "risk_policy.json"
        if args.force or not risk_path.exists():
            policy = json.loads(json.dumps(risk_template))
            policy["policy_id"] = f"{team_id}-base"
            _atomic_write_json(risk_path, policy)
        load_risk_policy(risk_path)
        bootstrap = team_root / "BOOTSTRAP.md"
        if args.force or not bootstrap.exists():
            bootstrap.write_text(
                f"# {team_id} · Top-40 V2\n\n"
                "Status: `PENDING_PHASE0`\n\n"
                "Negative research is evidence, not a submission. Work only inside this V2 "
                "namespace and the visible-development data boundary.\n",
                encoding="utf-8",
            )
        for ledger_name in ("families.jsonl", "experiments.jsonl"):
            ledger = team_root / ledger_name
            if args.force or not ledger.exists():
                _atomic_write_bytes(ledger, b"")
    (root / PRIVATE_ROOT).mkdir(parents=True, exist_ok=True)
    state = new_run_state(config)
    _atomic_write_json(state_path, state)
    _emit(
        {
            "initialized": len(TEAM_IDS),
            "phase": state["phase"],
            "state_path": TOP40_V2_LAYOUT.state_path,
        },
        args.json_out,
    )
    return 0


def _validate_risk_policy(args: argparse.Namespace) -> int:
    policy = load_risk_policy(args.policy)
    _emit(
        {
            "valid": True,
            "schema_version": policy.schema_version,
            "policy_id": policy.policy_id,
            "enabled": policy.enabled,
        },
        args.json_out,
    )
    return 0


def _common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json-out")


def _common_config(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    _common_output(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate_config = commands.add_parser(
        "validate-config", help="validate the immutable V2 contract"
    )
    _common_config(validate_config)

    init = commands.add_parser("init-teams", help="create ten isolated V2 namespaces")
    _common_config(init)
    init.add_argument("--force", action="store_true")

    freeze = commands.add_parser(
        "freeze-phase0", help="first-add the committed common-input and shared-snapshot freeze"
    )
    _common_config(freeze)

    risk = commands.add_parser("validate-risk-policy", help="validate a declarative risk policy")
    risk.add_argument("policy")
    _common_output(risk)

    assess = commands.add_parser("assess-qualification", help="apply non-compensatory gates")
    assess.add_argument("stage", choices=("development", "private"))
    assess.add_argument("evidence")
    assess.add_argument(
        "--include-private-observations",
        action="store_true",
        help="organizer-only: include sealed private metrics and thresholds",
    )
    _common_config(assess)

    register = commands.add_parser("register-family", help="register the initial mechanism family")
    register.add_argument("team_id", choices=TEAM_IDS)
    register.add_argument("registration")
    _common_config(register)

    pivot = commands.add_parser("pivot-team", help="register a documented mechanism pivot")
    pivot.add_argument("team_id", choices=TEAM_IDS)
    pivot.add_argument("registration")
    _common_config(pivot)

    development = commands.add_parser(
        "record-development-assessment", help="record a visible development gate assessment"
    )
    development.add_argument("team_id", choices=TEAM_IDS)
    development.add_argument("evidence")
    _common_config(development)

    private = commands.add_parser(
        "record-private-assessment", help="consume and seal the team's one private ticket"
    )
    private.add_argument("team_id", choices=TEAM_IDS)
    private.add_argument("evidence")
    _common_config(private)

    withdraw = commands.add_parser("withdraw-team", help="finish an unresolved team as DNF")
    withdraw.add_argument("team_id", choices=TEAM_IDS)
    withdraw.add_argument("--reason", required=True)
    _common_config(withdraw)

    close = commands.add_parser(
        "close-qualification", help="convert unresolved teams to DNF and lock qualification"
    )
    _common_config(close)

    cohort = commands.add_parser(
        "lock-finalist-cohort", help="first-add the qualified finalist cohort before OOS"
    )
    _common_config(cohort)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "validate-config": _validate_config_command,
        "init-teams": _init_teams,
        "freeze-phase0": _freeze_phase0,
        "validate-risk-policy": _validate_risk_policy,
        "assess-qualification": _assess_qualification,
        "register-family": lambda value: _register_family(value, pivot=False),
        "pivot-team": lambda value: _register_family(value, pivot=True),
        "record-development-assessment": _record_development_assessment,
        "record-private-assessment": _record_private_assessment,
        "withdraw-team": _withdraw_team,
        "close-qualification": _close_qualification,
        "lock-finalist-cohort": _lock_finalist_cohort,
    }
    try:
        return dispatch[args.command](args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
