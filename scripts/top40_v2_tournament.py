#!/usr/bin/env python3
"""Lifecycle controls for the isolated Top-40 V2 qualification tournament."""

from __future__ import annotations

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import resource
import subprocess
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.qualification import (
    QualificationAssessment,
    assess_development,
    assess_private,
)
from crypto_trade.tournament.research_v2 import (
    JournalState,
    ResearchPolicy,
    build_trial_registration,
    build_trial_result,
    plan_genesis,
    plan_registration_append,
    plan_result_append,
    plan_team_ledger_projection,
    validate_journal_bytes,
    validate_team_ledger_bytes,
    validate_trial_registration_bytes,
    validate_trial_result_bytes,
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
FINAL_OOS_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/final_oos_lock.json"
OBJECTIVE_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/objective_lock.json"
CRITIC_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/critic_lock.json"
CRITIC_CONFIRMATION_LOCK_PATH = (
    f"{TOP40_V2_LAYOUT.tournament_root}/critic_confirmation_lock.json"
)
USER_BALLOT_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/user_ballot_lock.json"
SELECTION_LOCK_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/selection_lock.json"
WINNER_FREEZE_PATH = f"{TOP40_V2_LAYOUT.tournament_root}/winner_freeze.json"
PRIVATE_ROOT = f"{TOP40_V2_LAYOUT.tournament_root}/private"
RESEARCH_JOURNAL_PATH = TOP40_V2_LAYOUT.organizer_journal_path
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


def _journal_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _research_policy(config: LoadedV2Config) -> ResearchPolicy:
    budget = config.raw["research_budget"]
    return ResearchPolicy(
        tournament_id=TOP40_V2_LAYOUT.name,
        team_ids=TEAM_IDS,
        maximum_material_configurations_per_team=int(
            budget["maximum_material_configurations_per_team"]
        ),
        maximum_cpu_hours_per_team=float(budget["maximum_cpu_hours_per_team"]),
        maximum_wall_clock_hours_per_team=float(
            budget["maximum_wall_clock_hours_per_team"]
        ),
    )


def _research_binding(journal: JournalState) -> dict[str, object]:
    return {
        "path": RESEARCH_JOURNAL_PATH,
        "genesis_sha256": journal.genesis_sha256,
        "head_sha256": journal.head_sha256,
        "record_count": len(journal.records),
    }


def _trial_ledger(root: Path, team_id: str) -> Path:
    return root / TOP40_V2_LAYOUT.team_root(team_id) / "experiments.jsonl"


def _safe_regular_bytes(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} is missing or unsafe")
    return path.read_bytes()


def _load_research_journal(
    root: Path,
    config: LoadedV2Config,
    state: dict[str, Any],
    *,
    recover_projection: bool,
) -> JournalState:
    """Validate journal authority and exact per-team projections.

    Journal publication intentionally precedes the derived state/ledger projections.  Recovery
    is accepted only when the old state head is an exact prefix of the valid hash chain and each
    team ledger is a complete record prefix of the journal-authorized bytes.
    """
    policy = _research_policy(config)
    journal_path = root / RESEARCH_JOURNAL_PATH
    journal = validate_journal_bytes(
        _safe_regular_bytes(journal_path, "organizer research journal"), policy
    )
    binding = state.get("research_journal")
    if not isinstance(binding, Mapping) or binding.get("path") != RESEARCH_JOURNAL_PATH:
        raise ValueError("run state has no canonical organizer-journal binding")
    if binding.get("genesis_sha256") != journal.genesis_sha256:
        raise ValueError("organizer journal genesis differs from run state")
    expected_binding = _research_binding(journal)
    if dict(binding) != expected_binding:
        count = binding.get("record_count")
        old_head = binding.get("head_sha256")
        prefix_is_exact = (
            isinstance(count, int)
            and not isinstance(count, bool)
            and 1 <= count <= len(journal.records)
            and journal.records[count - 1].get("record_sha256") == old_head
        )
        if not recover_projection or not prefix_is_exact:
            raise ValueError("run-state journal head differs from organizer journal")
        state["research_journal"] = expected_binding

    for team_id in TEAM_IDS:
        ledger_path = _trial_ledger(root, team_id)
        ledger_bytes = _safe_regular_bytes(ledger_path, f"{team_id} trial ledger")
        try:
            validate_team_ledger_bytes(ledger_bytes, journal, team_id)
        except ValueError:
            if not recover_projection:
                raise
            projection = plan_team_ledger_projection(ledger_bytes, journal, team_id)
            if (
                len(ledger_bytes) != projection.expected_current_size
                or _sha256_bytes(ledger_bytes) != projection.expected_current_sha256
            ):
                raise ValueError(f"{team_id} ledger changed during recovery")
            _atomic_write_bytes(ledger_path, projection.replacement_ledger_bytes)
            validate_team_ledger_bytes(
                _safe_regular_bytes(ledger_path, f"{team_id} trial ledger"),
                journal,
                team_id,
            )
        derived_count = journal.teams[team_id].material_trial_count
        team = _team(state, team_id)
        if team.get("trial_count") != derived_count:
            if not recover_projection or not (
                isinstance(team.get("trial_count"), int)
                and not isinstance(team.get("trial_count"), bool)
                and 0 <= team["trial_count"] <= derived_count
            ):
                raise ValueError(f"{team_id} trial count differs from organizer journal")
            team["trial_count"] = derived_count
    return journal


def _publish_research_append(
    root: Path,
    config: LoadedV2Config,
    state: dict[str, Any],
    plan: Any,
) -> JournalState:
    journal_path = root / RESEARCH_JOURNAL_PATH
    current_journal = _safe_regular_bytes(journal_path, "organizer research journal")
    if (
        len(current_journal) != plan.expected_journal_size
        or _sha256_bytes(current_journal) != plan.expected_journal_sha256
    ):
        raise ValueError("organizer journal changed before append publication")
    if plan.team_id is None or plan.replacement_team_ledger_bytes is None:
        raise ValueError("research event append is missing its team-ledger projection")
    ledger_path = _trial_ledger(root, plan.team_id)
    current_ledger = _safe_regular_bytes(ledger_path, f"{plan.team_id} trial ledger")
    if (
        len(current_ledger) != plan.expected_team_ledger_size
        or _sha256_bytes(current_ledger) != plan.expected_team_ledger_sha256
    ):
        raise ValueError("team trial ledger changed before append publication")
    _atomic_write_bytes(journal_path, plan.replacement_journal_bytes)
    try:
        _atomic_write_bytes(ledger_path, plan.replacement_team_ledger_bytes)
    except BaseException:
        _atomic_write_bytes(journal_path, current_journal)
        raise
    journal = validate_journal_bytes(plan.replacement_journal_bytes, _research_policy(config))
    validate_team_ledger_bytes(plan.replacement_team_ledger_bytes, journal, plan.team_id)
    state["research_journal"] = _research_binding(journal)
    _team(state, plan.team_id)["trial_count"] = journal.teams[
        plan.team_id
    ].material_trial_count
    return journal


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


def _registration_input(raw: Mapping[str, Any]) -> bytes:
    fields = {
        "timestamp_utc",
        "team_id",
        "family_id",
        "candidate_id",
        "strategy_sha256",
        "source_bundle_sha256",
        "risk_config_sha256",
        "config_sha256",
        "parameters",
        "seed",
        "thesis",
        "falsifier",
    }
    normalized = dict(raw)
    if set(normalized) == fields | {"schema_version", "event_type"}:
        if normalized.pop("schema_version") != 2 or normalized.pop("event_type") != (
            "trial_registration"
        ):
            raise ValueError("trial registration schema_version/event_type is invalid")
    if set(normalized) != fields:
        raise ValueError("trial registration input has invalid fields")
    try:
        return build_trial_registration(**normalized)
    except TypeError as exc:
        raise ValueError(f"trial registration input is invalid: {exc}") from exc


def _result_input(raw: Mapping[str, Any]) -> bytes:
    fields = {
        "timestamp_utc",
        "team_id",
        "family_id",
        "candidate_id",
        "registration_sha256",
        "status",
        "failure_reason",
        "artifact_hashes",
        "metrics_summary",
        "cpu_hours",
        "wall_clock_hours",
    }
    normalized = dict(raw)
    if set(normalized) == fields | {"schema_version", "event_type"}:
        if normalized.pop("schema_version") != 2 or normalized.pop("event_type") != (
            "trial_result"
        ):
            raise ValueError("trial result schema_version/event_type is invalid")
    if set(normalized) != fields:
        raise ValueError("trial result input has invalid fields")
    try:
        return build_trial_result(**normalized)
    except TypeError as exc:
        raise ValueError(f"trial result input is invalid: {exc}") from exc


def _current_candidate_hashes(
    root: Path, team_id: str
) -> tuple[str, str, str]:
    from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

    team_root = root / TOP40_V2_LAYOUT.team_root(team_id)
    strategy = team_root / "strategy.py"
    risk = team_root / "risk_policy.json"
    strategy_sha256 = _sha256_bytes(_safe_regular_bytes(strategy, "strategy.py"))
    risk_sha256 = _sha256_bytes(_safe_regular_bytes(risk, "risk_policy.json"))
    load_risk_policy(risk)
    source_sha256, _entries = source_bundle_fingerprint(
        root,
        team_id,
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
    )
    return strategy_sha256, risk_sha256, source_sha256


def _verify_registration_inputs(
    root: Path,
    config: LoadedV2Config,
    team_id: str,
    event: Mapping[str, Any],
) -> None:
    if event.get("team_id") != team_id:
        raise ValueError("trial registration team_id differs from the command")
    families = _read_families(_family_ledger(root, team_id))
    if event.get("family_id") not in {family.get("family_id") for family in families}:
        raise ValueError("trial registration requires a registered mechanism family")
    strategy_sha256, risk_sha256, source_sha256 = _current_candidate_hashes(root, team_id)
    if (
        event.get("strategy_sha256") != strategy_sha256
        or event.get("risk_config_sha256") != risk_sha256
        or event.get("source_bundle_sha256") != source_sha256
        or event.get("config_sha256") != config.sha256
    ):
        raise ValueError("trial registration input hashes differ from the current candidate")
    registered = datetime.fromisoformat(str(event["timestamp_utc"]).replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(
        str(config.raw["research_budget"]["deadline_utc"]).replace("Z", "+00:00")
    )
    if registered > deadline:
        raise ValueError("trial registration is after the frozen research deadline")


def _verify_result_artifacts(root: Path, event: Mapping[str, Any]) -> None:
    if event.get("status") != "completed":
        return
    artifacts = event.get("artifact_hashes")
    if not isinstance(artifacts, Mapping):
        raise ValueError("completed trial artifact hashes are malformed")
    for relative, expected_sha256 in artifacts.items():
        if not isinstance(relative, str):
            raise ValueError("trial artifact names must be repository-relative paths")
        pure = Path(relative)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise ValueError("trial artifact names must be safe repository-relative paths")
        path = (root / pure).resolve()
        if not path.is_relative_to(root):
            raise ValueError("trial artifact path escapes the repository")
        payload = _safe_regular_bytes(path, f"trial artifact {relative}")
        if _sha256_bytes(payload) != expected_sha256:
            raise ValueError(f"trial artifact hash differs: {relative}")


def _register_trial(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, _payload = _read_json(args.registration, "trial registration")
    event_bytes = _registration_input(raw)
    event = validate_trial_registration_bytes(event_bytes, _research_policy(config))
    if event["team_id"] != args.team_id:
        raise ValueError("trial registration team_id differs from the command")
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, args.team_id)
        if team["status"] != "researching":
            raise ValueError(f"{args.team_id} cannot register a trial in {team['status']!r}")
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        _verify_registration_inputs(root, config, args.team_id, event)
        ledger = _safe_regular_bytes(
            _trial_ledger(root, args.team_id), f"{args.team_id} trial ledger"
        )
        plan = plan_registration_append(
            journal.journal_bytes,
            event_bytes,
            ledger,
            policy=_research_policy(config),
        )
        journal = _publish_research_append(root, config, state, plan)
        accounting = journal.teams[args.team_id]
    _emit(
        {
            "event": "trial_registered",
            "team_id": args.team_id,
            "candidate_id": event["candidate_id"],
            "registration_sha256": _sha256_bytes(event_bytes),
            "material_trial_count": accounting.material_trial_count,
            "remaining_material_trials": (
                config.raw["research_budget"]["maximum_material_configurations_per_team"]
                - accounting.material_trial_count
            ),
        },
        args.json_out,
    )
    return 0


def _record_trial_result(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, _payload = _read_json(args.result, "trial result")
    event_bytes = _result_input(raw)
    event = validate_trial_result_bytes(event_bytes, _research_policy(config))
    if event["team_id"] != args.team_id:
        raise ValueError("trial result team_id differs from the command")
    _verify_result_artifacts(root, event)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, args.team_id)
        if team["status"] != "researching":
            raise ValueError(f"{args.team_id} cannot record a trial in {team['status']!r}")
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        families = _read_families(_family_ledger(root, args.team_id))
        if event["family_id"] not in {family.get("family_id") for family in families}:
            raise ValueError("trial result names an unregistered mechanism family")
        ledger = _safe_regular_bytes(
            _trial_ledger(root, args.team_id), f"{args.team_id} trial ledger"
        )
        plan = plan_result_append(
            journal.journal_bytes,
            event_bytes,
            ledger,
            policy=_research_policy(config),
        )
        journal = _publish_research_append(root, config, state, plan)
        accounting = journal.teams[args.team_id]
    _emit(
        {
            "event": "trial_result_recorded",
            "team_id": args.team_id,
            "candidate_id": event["candidate_id"],
            "status": event["status"],
            "material_trial_count": accounting.material_trial_count,
            "cumulative_cpu_hours": accounting.cpu_hours,
            "cumulative_wall_clock_hours": accounting.wall_clock_hours,
        },
        args.json_out,
    )
    return 0


def _research_status(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    with _edit_state(root, config) as state:
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        selected = TEAM_IDS if args.team_id is None else (args.team_id,)
        teams = {
            team_id: {
                "material_trial_count": journal.teams[team_id].material_trial_count,
                "cpu_hours": journal.teams[team_id].cpu_hours,
                "wall_clock_hours": journal.teams[team_id].wall_clock_hours,
                "pending_candidate_ids": list(
                    journal.teams[team_id].pending_candidate_ids
                ),
            }
            for team_id in selected
        }
    _emit(
        {
            "journal_head_sha256": journal.head_sha256,
            "journal_record_count": len(journal.records),
            "teams": teams,
        },
        args.json_out,
    )
    return 0


def _next_journal_timestamp(journal: JournalState) -> str:
    now = datetime.now(UTC)
    previous = datetime.fromisoformat(journal.last_timestamp_utc.replace("Z", "+00:00"))
    return max(now, previous).isoformat().replace("+00:00", "Z")


def _run_reservation_path(root: Path, team_id: str, stage: str, candidate_id: str) -> Path:
    if stage == "development":
        return (
            root
            / TOP40_V2_LAYOUT.report_root(team_id)
            / "run-reservations"
            / f"{candidate_id}.json"
        )
    if stage == "private":
        return root / PRIVATE_ROOT / "run-reservations" / f"{team_id}.json"
    raise ValueError("run reservation stage must be development or private")


def _reserve_window_run(
    root: Path,
    config: LoadedV2Config,
    *,
    team_id: str,
    stage: str,
    candidate_id: str,
) -> tuple[dict[str, Any], str]:
    reservation_path = _run_reservation_path(root, team_id, stage, candidate_id)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, team_id)
        expected_status = "researching" if stage == "development" else (
            "qualifier_candidate_frozen"
        )
        if team["status"] != expected_status:
            raise ValueError(f"{stage} run requires team status {expected_status}")
        if stage == "private" and team["private_attempts"] != 0:
            raise ValueError(f"{team_id} already consumed its private ticket")
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        accounting = journal.teams[team_id]
        registration = accounting.registrations.get(candidate_id)
        if not isinstance(registration, Mapping):
            raise ValueError("window run requires an exact candidate preregistration")
        if stage == "development":
            if candidate_id in accounting.results:
                raise ValueError("development candidate already has a terminal trial result")
        else:
            candidate = team.get("qualifier_candidate")
            if (
                not isinstance(candidate, Mapping)
                or candidate.get("candidate_id") != candidate_id
                or candidate_id not in accounting.results
                or accounting.results[candidate_id].get("status") != "completed"
            ):
                raise ValueError("private run differs from the frozen development candidate")
        _verify_candidate_registration_matches_current(
            root, config, team_id, registration
        )
        strategy_sha256, risk_sha256, source_sha256 = _current_candidate_hashes(
            root, team_id
        )
        reservation = {
            "schema_version": 1,
            "tournament": TOP40_V2_LAYOUT.name,
            "stage": stage,
            "team_id": team_id,
            "candidate_id": candidate_id,
            "reserved_at_utc": _now(),
            "config_sha256": config.sha256,
            "strategy_sha256": strategy_sha256,
            "risk_policy_sha256": risk_sha256,
            "source_bundle_sha256": source_sha256,
            "registration_sha256": accounting.registration_sha256[candidate_id],
            "organizer_journal_head_sha256": journal.head_sha256,
            "private_attempt_number": 1 if stage == "private" else None,
        }
        reservation_sha256 = _first_add_json(reservation_path, reservation)
    return reservation, reservation_sha256


def _archive_development_artifacts(
    root: Path, team_id: str, candidate_id: str, result: Any
) -> dict[str, str]:
    archive = (
        root
        / TOP40_V2_LAYOUT.report_root(team_id)
        / "development-runs"
        / candidate_id
    )
    hashes: dict[str, str] = {}
    for name, relative in result.artifacts.items():
        source = root / relative
        destination = archive / source.name
        payload = _safe_regular_bytes(source, f"development artifact {name}")
        _publish_immutable_bytes(destination, payload, f"development artifact {name}")
        hashes[destination.relative_to(root).as_posix()] = _sha256_bytes(payload)
    return hashes


def _append_generated_trial_result(
    root: Path,
    config: LoadedV2Config,
    *,
    team_id: str,
    event_bytes: bytes,
) -> JournalState:
    event = validate_trial_result_bytes(event_bytes, _research_policy(config))
    if event["team_id"] != team_id:
        raise ValueError("generated trial result has the wrong team identity")
    _verify_result_artifacts(root, event)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        if _team(state, team_id)["status"] != "researching":
            raise ValueError("generated development result requires a researching team")
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        ledger = _safe_regular_bytes(
            _trial_ledger(root, team_id), f"{team_id} trial ledger"
        )
        plan = plan_result_append(
            journal.journal_bytes,
            event_bytes,
            ledger,
            policy=_research_policy(config),
        )
        return _publish_research_append(root, config, state, plan)


def _resource_snapshot() -> tuple[float, float]:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime, time.monotonic()


def _resource_delta(before: tuple[float, float]) -> tuple[float, float]:
    after_cpu, after_wall = _resource_snapshot()
    return max(0.0, (after_cpu - before[0]) / 3600.0), max(
        0.0, (after_wall - before[1]) / 3600.0
    )


def _mark_private_execution_failure(
    root: Path,
    config: LoadedV2Config,
    *,
    team_id: str,
    candidate_id: str,
    reservation_sha256: str,
    reason: str,
) -> None:
    sealed_path = root / PRIVATE_ROOT / f"{team_id}.json"
    sealed = {
        "schema_version": 1,
        "sealed_at_utc": _now(),
        "team_id": team_id,
        "candidate_id": candidate_id,
        "passed": False,
        "failure_code": "private-run-execution-failed",
        "failure_reason": reason,
        "reservation_sha256": reservation_sha256,
    }
    sealed_sha256 = _first_add_json(sealed_path, sealed)
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, team_id)
        if team["status"] != "qualifier_candidate_frozen" or team["private_attempts"] != 0:
            raise ValueError("private failure cannot be applied to the current team state")
        team["private_attempts"] = 1
        team["private_result"] = {
            "schema_version": 1,
            "stage": "private",
            "team_id": team_id,
            "passed": False,
            "failed_gate_names": ["private.runner_execution"],
            "feedback_mode": "pass-fail-only",
            "sealed_record_path": sealed_path.relative_to(root).as_posix(),
            "sealed_record_sha256": sealed_sha256,
        }
        team["status"] = "dnf"
        team["dnf"] = {
            "reason_code": "private-run-execution-failed",
            "reason": "the one-shot private evaluator run failed",
            "recorded_at_utc": _now(),
        }


def _run_window(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.runner_v2 import (
        _ORGANIZER_RUN_AUTHORIZATION,
        run_team,
    )

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    team_id = args.team_id
    stage = args.stage
    candidate_id = args.candidate_id
    _reservation, reservation_sha256 = _reserve_window_run(
        root,
        config,
        team_id=team_id,
        stage=stage,
        candidate_id=candidate_id,
    )
    usage = _resource_snapshot()
    try:
        result = run_team(
            root,
            team_id,
            f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
            TOP40_V2_LAYOUT.config_path,
            str(config.raw["paths"]["shared_snapshot_manifest"]),
            stage=stage,
            _authorization=_ORGANIZER_RUN_AUTHORIZATION,
        )
    except BaseException as exc:
        cpu_hours, wall_hours = _resource_delta(usage)
        reason = f"{type(exc).__name__}: {exc}"[:8000]
        if stage == "development":
            with _edit_state(root, config) as state:
                journal = _load_research_journal(
                    root, config, state, recover_projection=True
                )
                accounting, registration, _existing, registration_sha256 = (
                    journal.teams[team_id],
                    journal.teams[team_id].registrations[candidate_id],
                    journal.teams[team_id].results.get(candidate_id),
                    journal.teams[team_id].registration_sha256[candidate_id],
                )
                if candidate_id in accounting.results:
                    raise ValueError("failed run candidate already has a terminal result") from exc
                event_bytes = build_trial_result(
                    timestamp_utc=_next_journal_timestamp(journal),
                    team_id=team_id,
                    family_id=str(registration["family_id"]),
                    candidate_id=candidate_id,
                    registration_sha256=registration_sha256,
                    status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                    failure_reason=reason,
                    artifact_hashes={},
                    metrics_summary={},
                    cpu_hours=cpu_hours,
                    wall_clock_hours=wall_hours,
                )
            _append_generated_trial_result(
                root, config, team_id=team_id, event_bytes=event_bytes
            )
        else:
            _mark_private_execution_failure(
                root,
                config,
                team_id=team_id,
                candidate_id=candidate_id,
                reservation_sha256=reservation_sha256,
                reason=reason,
            )
        raise

    cpu_hours, wall_hours = _resource_delta(usage)
    runner_record = result.organizer_fields()
    runner_path = root / _canonical_runner_record_path(
        team_id,
        stage,
        candidate_id=candidate_id if stage == "development" else None,
    )
    runner_sha256 = _publish_immutable_bytes(
        runner_path, _json_bytes(runner_record), f"{stage} runner record"
    )
    if stage == "development":
        artifact_hashes = _archive_development_artifacts(
            root, team_id, candidate_id, result
        )
        artifact_hashes[runner_path.relative_to(root).as_posix()] = runner_sha256
        with _edit_state(root, config) as state:
            journal = _load_research_journal(
                root, config, state, recover_projection=True
            )
            accounting = journal.teams[team_id]
            registration = accounting.registrations[candidate_id]
            registration_sha256 = accounting.registration_sha256[candidate_id]
            event_bytes = build_trial_result(
                timestamp_utc=_next_journal_timestamp(journal),
                team_id=team_id,
                family_id=str(registration["family_id"]),
                candidate_id=candidate_id,
                registration_sha256=registration_sha256,
                status="completed",
                failure_reason=None,
                artifact_hashes=artifact_hashes,
                metrics_summary=runner_record,
                cpu_hours=cpu_hours,
                wall_clock_hours=wall_hours,
            )
        journal = _append_generated_trial_result(
            root, config, team_id=team_id, event_bytes=event_bytes
        )
        _emit(
            {
                "stage": stage,
                "team_id": team_id,
                "candidate_id": candidate_id,
                "runner_record_path": runner_path.relative_to(root).as_posix(),
                "runner_record_sha256": runner_sha256,
                "journal_head_sha256": journal.head_sha256,
                "cpu_hours": cpu_hours,
                "wall_clock_hours": wall_hours,
            },
            args.json_out,
        )
        return 0

    assessment_args = argparse.Namespace(
        team_id=team_id,
        runner_record=str(runner_path),
        config=args.config,
        json_out=args.json_out,
    )
    return _record_private_assessment(assessment_args)


def _reserve_finalist_run(
    root: Path, config: LoadedV2Config, team_id: str
) -> tuple[str, str]:
    reservation_path = root / PRIVATE_ROOT / "final-oos-reservations" / f"{team_id}.json"
    with _edit_state(root, config) as state:
        _require_phase(state, "finalist_cohort_frozen")
        cohort_sha256 = _verify_file_binding(
            root,
            state["finalist_cohort_lock"],
            TOP40_V2_LAYOUT.finalist_cohort_lock_path,
            "finalist cohort lock",
        )
        finalist_ids = state["finalist_cohort_lock"].get("finalist_team_ids")
        if not isinstance(finalist_ids, list) or team_id not in finalist_ids:
            raise ValueError(f"{team_id} is not in the locked finalist cohort")
        team = _team(state, team_id)
        if team["status"] != "finalist_frozen" or not isinstance(
            team.get("finalist_freeze"), Mapping
        ):
            raise ValueError("final-OOS run requires an unused finalist freeze")
        _verify_qualified_candidate(root, team_id, team)
        freeze = team["finalist_freeze"]
        candidate = team["qualifier_candidate"]
        if any(
            freeze.get(field) != candidate.get(field)
            for field in (
                "candidate_id",
                "strategy_sha256",
                "risk_policy_sha256",
                "source_bundle_sha256",
            )
        ):
            raise ValueError("finalist source freeze differs from the qualified candidate")
        reservation = {
            "schema_version": 1,
            "tournament": TOP40_V2_LAYOUT.name,
            "stage": "final_oos",
            "team_id": team_id,
            "candidate_id": candidate["candidate_id"],
            "reserved_at_utc": _now(),
            "organizer_reveal_number": 1,
            "internal_replay_count": config.raw["final_oos"][
                "deterministic_internal_replays"
            ],
            "cohort_lock_sha256": cohort_sha256,
            "config_sha256": config.sha256,
            "strategy_sha256": candidate["strategy_sha256"],
            "risk_policy_sha256": candidate["risk_policy_sha256"],
            "source_bundle_sha256": candidate["source_bundle_sha256"],
        }
        reservation_sha256 = _first_add_json(reservation_path, reservation)
        team["status"] = "canonical_running"
        team["canonical_result"] = {
            "status": "reserved",
            "reservation_path": reservation_path.relative_to(root).as_posix(),
            "reservation_sha256": reservation_sha256,
        }
    return str(reservation["candidate_id"]), reservation_sha256


def _replay_records_match(first: Any, second: Any) -> bool:
    first_record = first.organizer_fields()
    second_record = second.organizer_fields()
    for record in (first_record, second_record):
        record.pop("output_dir", None)
        record.pop("artifacts", None)
    return first_record == second_record


def _promote_final_replay(root: Path, team_id: str, result: Any) -> Any:
    canonical_relative = f"{TOP40_V2_LAYOUT.report_root(team_id)}/final-oos"
    canonical = root / canonical_relative
    if canonical.exists() or canonical.is_symlink():
        raise ValueError("canonical final-OOS output already exists")
    canonical.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{team_id}-final-", dir=canonical.parent))
    artifacts: dict[str, str] = {}
    try:
        for name, relative in result.artifacts.items():
            source = root / relative
            destination = staging / source.name
            _atomic_write_bytes(
                destination, _safe_regular_bytes(source, f"final replay artifact {name}")
            )
            artifacts[name] = f"{canonical_relative}/{source.name}"
        os.replace(staging, canonical)
    except BaseException:
        if staging.exists():
            for path in staging.iterdir():
                path.unlink(missing_ok=True)
            staging.rmdir()
        raise
    artifact_paths = {name: root / relative for name, relative in artifacts.items()}
    return dataclasses.replace(
        result,
        output_dir=canonical_relative,
        artifacts=artifacts,
        artifact_sha256={
            name: _sha256_bytes(path.read_bytes()) for name, path in artifact_paths.items()
        },
        artifact_sizes={name: path.stat().st_size for name, path in artifact_paths.items()},
    )


def _run_finalist(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.runner_v2 import (
        _ORGANIZER_RUN_AUTHORIZATION,
        run_team,
    )

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    team_id = args.team_id
    candidate_id, reservation_sha256 = _reserve_finalist_run(root, config, team_id)
    replay_results: list[Any] = []
    try:
        replay_count = int(config.raw["final_oos"]["deterministic_internal_replays"])
        for replay_number in range(1, replay_count + 1):
            replay_relative = (
                f"{PRIVATE_ROOT}/final-replays/{team_id}/replay-{replay_number}"
            )
            replay_results.append(
                run_team(
                    root,
                    team_id,
                    f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
                    TOP40_V2_LAYOUT.config_path,
                    str(config.raw["paths"]["shared_snapshot_manifest"]),
                    stage="final_oos",
                    _authorization=_ORGANIZER_RUN_AUTHORIZATION,
                    _output_relative=replay_relative,
                )
            )
        if replay_count != 2 or not _replay_records_match(
            replay_results[0], replay_results[1]
        ):
            raise ValueError("deterministic final-OOS replay records or artifacts differ")
        canonical_result = _promote_final_replay(root, team_id, replay_results[0])
        runner_record = canonical_result.organizer_fields()
        runner_path = root / _canonical_runner_record_path(team_id, "final_oos")
        runner_sha256 = _publish_immutable_bytes(
            runner_path, _json_bytes(runner_record), "final-OOS runner record"
        )
        replay_bindings = [
            {
                "output_dir": result.output_dir,
                "artifact_sha256": dict(result.artifact_sha256),
                "artifact_sizes": dict(result.artifact_sizes),
            }
            for result in replay_results
        ]
        with _edit_state(root, config) as state:
            _require_phase(state, "finalist_cohort_frozen")
            team = _team(state, team_id)
            current = team.get("canonical_result")
            if team["status"] != "canonical_running" or not isinstance(current, Mapping):
                raise ValueError("final-OOS reservation state changed during evaluation")
            if current.get("reservation_sha256") != reservation_sha256:
                raise ValueError("final-OOS reservation binding changed during evaluation")
            team["canonical_result"] = {
                "status": "complete",
                "candidate_id": candidate_id,
                "completed_at_utc": _now(),
                "reservation_sha256": reservation_sha256,
                "runner_record_path": runner_path.relative_to(root).as_posix(),
                "runner_record_sha256": runner_sha256,
                "replay_outputs_match": True,
                "internal_replays": replay_bindings,
            }
            team["status"] = "canonical_complete"
    except BaseException as exc:
        with _edit_state(root, config) as state:
            team = _team(state, team_id)
            if team["status"] == "canonical_running":
                team["status"] = "canonical_failed"
                team["canonical_result"] = {
                    "status": "failed",
                    "candidate_id": candidate_id,
                    "failed_at_utc": _now(),
                    "reservation_sha256": reservation_sha256,
                    "failure": f"{type(exc).__name__}: {exc}"[:8000],
                }
        raise
    _emit(
        {
            "stage": "final_oos",
            "team_id": team_id,
            "candidate_id": candidate_id,
            "runner_record_path": runner_path.relative_to(root).as_posix(),
            "runner_record_sha256": runner_sha256,
            "internal_replays_match": True,
        },
        args.json_out,
    )
    return 0


def _lock_final_oos(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    lock_path = root / FINAL_OOS_LOCK_PATH
    created = False
    finalist_ids: list[str] = []
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "finalist_cohort_frozen")
            cohort_sha256 = _verify_file_binding(
                root,
                state["finalist_cohort_lock"],
                TOP40_V2_LAYOUT.finalist_cohort_lock_path,
                "finalist cohort lock",
            )
            raw_ids = state["finalist_cohort_lock"].get("finalist_team_ids")
            if not isinstance(raw_ids, list) or not raw_ids:
                raise ValueError("final-OOS lock requires a nonempty finalist cohort")
            finalist_ids = list(raw_ids)
            results: dict[str, object] = {}
            for team_id in finalist_ids:
                team = _team(state, team_id)
                if team["status"] != "canonical_complete" or not isinstance(
                    team.get("canonical_result"), Mapping
                ):
                    raise ValueError(f"final-OOS result is incomplete for {team_id}")
                result = team["canonical_result"]
                expected_path = _canonical_runner_record_path(team_id, "final_oos")
                if result.get("runner_record_path") != expected_path:
                    raise ValueError(f"final-OOS runner path is noncanonical for {team_id}")
                record_path = root / expected_path
                if (
                    not record_path.is_file()
                    or record_path.is_symlink()
                    or _sha256_bytes(record_path.read_bytes())
                    != result.get("runner_record_sha256")
                    or result.get("replay_outputs_match") is not True
                ):
                    raise ValueError(f"final-OOS runner binding is invalid for {team_id}")
                results[team_id] = result
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "config_sha256": config.sha256,
                "cohort_lock_sha256": cohort_sha256,
                "finalist_team_ids": finalist_ids,
                "organizer_reveals_per_finalist": 1,
                "deterministic_internal_replays": 2,
                "results": results,
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["final_oos_lock"] = {
                "path": FINAL_OOS_LOCK_PATH,
                "sha256": digest,
                "finalist_team_ids": finalist_ids,
            }
            state["phase"] = "oos_revealed"
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": "oos_revealed",
            "finalist_team_ids": finalist_ids,
            "final_oos_lock": FINAL_OOS_LOCK_PATH,
        },
        args.json_out,
    )
    return 0


def _hash_bound_file(root: Path, relative: str, expected_sha256: str, label: str) -> Any:
    from crypto_trade.tournament.finals_v2 import HashBoundJson

    path = root / relative
    payload = _safe_regular_bytes(path, label)
    if _sha256_bytes(payload) != expected_sha256:
        raise ValueError(f"{label} differs from its immutable binding")
    return HashBoundJson(payload, expected_sha256)


def _build_locked_finalist(
    root: Path, config: LoadedV2Config, state: Mapping[str, Any], team_id: str
) -> Any:
    from crypto_trade.tournament.finals_v2 import (
        FinalistSourceBinding,
        build_finalist_performance,
    )

    team = _team(state, team_id)
    candidate = team.get("qualifier_candidate")
    private = team.get("private_result")
    final = team.get("canonical_result")
    if not all(isinstance(item, Mapping) for item in (candidate, private, final)):
        raise ValueError(f"finalist source bindings are incomplete for {team_id}")
    final_path = str(final.get("runner_record_path"))
    final_record, final_payload = _read_json(root / final_path, "final-OOS runner record")
    manifest_sha256 = _nonempty_text(
        final_record.get("data_manifest_sha256"), "data_manifest_sha256"
    )
    binding = FinalistSourceBinding(
        team_id=team_id,
        candidate_id=str(candidate["candidate_id"]),
        config_sha256=config.sha256,
        strategy_sha256=str(candidate["strategy_sha256"]),
        risk_policy_sha256=str(candidate["risk_policy_sha256"]),
        source_bundle_sha256=str(candidate["source_bundle_sha256"]),
        data_manifest_sha256=manifest_sha256,
        development_evidence_sha256=str(candidate["development_evidence_sha256"]),
        private_sealed_record_sha256=str(private["sealed_record_sha256"]),
        private_runner_record_sha256=str(private["runner_record_sha256"]),
        final_oos_runner_record_sha256=str(final["runner_record_sha256"]),
    )
    if _sha256_bytes(final_payload) != binding.final_oos_runner_record_sha256:
        raise ValueError(f"final-OOS runner record changed for {team_id}")
    return build_finalist_performance(
        binding=binding,
        development_evidence=_hash_bound_file(
            root,
            str(candidate["development_evidence_path"]),
            binding.development_evidence_sha256,
            "development qualification evidence",
        ),
        private_sealed_record=_hash_bound_file(
            root,
            str(private["sealed_record_path"]),
            binding.private_sealed_record_sha256,
            "private sealed record",
        ),
        private_runner_record=_hash_bound_file(
            root,
            str(private["runner_record_path"]),
            binding.private_runner_record_sha256,
            "private runner record",
        ),
        final_oos_runner_record=_hash_bound_file(
            root,
            final_path,
            binding.final_oos_runner_record_sha256,
            "final-OOS runner record",
        ),
        config=config,
    )


def _objective_inputs(
    root: Path, config: LoadedV2Config, state: Mapping[str, Any]
) -> tuple[list[Any], list[str], list[str]]:
    cohort = state.get("finalist_cohort_lock")
    if not isinstance(cohort, Mapping) or not isinstance(
        cohort.get("finalist_team_ids"), list
    ):
        raise ValueError("finalist cohort binding is missing")
    finalist_ids = list(cohort["finalist_team_ids"])
    dnf_ids = [team_id for team_id in TEAM_IDS if team_id not in finalist_ids]
    finalists = [
        _build_locked_finalist(root, config, state, team_id) for team_id in finalist_ids
    ]
    return finalists, finalist_ids, dnf_ids


def _lock_objective(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.finals_v2 import lock_objective_scores

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    lock_path = root / OBJECTIVE_LOCK_PATH
    created = False
    objective: Any = None
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "oos_revealed")
            cohort_sha256 = _verify_file_binding(
                root,
                state["finalist_cohort_lock"],
                TOP40_V2_LAYOUT.finalist_cohort_lock_path,
                "finalist cohort lock",
            )
            final_oos_sha256 = _verify_file_binding(
                root, state["final_oos_lock"], FINAL_OOS_LOCK_PATH, "final-OOS lock"
            )
            finalists, finalist_ids, dnf_ids = _objective_inputs(root, config, state)
            objective = lock_objective_scores(
                finalists,
                finalist_team_ids=finalist_ids,
                dnf_team_ids=dnf_ids,
                config=config,
            )
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "cohort_lock_sha256": cohort_sha256,
                "final_oos_lock_sha256": final_oos_sha256,
                "objective_score_sha256": objective.sha256,
                "objective": objective.to_dict(),
                "bound_performances": [item.to_dict() for item in finalists],
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["objective_lock"] = {
                "path": OBJECTIVE_LOCK_PATH,
                "sha256": digest,
                "objective_score_sha256": objective.sha256,
            }
            state["phase"] = "objective_locked"
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": "objective_locked",
            "objective_lock": OBJECTIVE_LOCK_PATH,
            "status": objective.status,
            "records": [record.to_dict() for record in objective.records],
        },
        args.json_out,
    )
    return 0


def _recompute_objective(
    root: Path, config: LoadedV2Config, state: Mapping[str, Any]
) -> tuple[Any, list[Any]]:
    from crypto_trade.tournament.finals_v2 import lock_objective_scores

    _verify_file_binding(
        root, state.get("objective_lock"), OBJECTIVE_LOCK_PATH, "objective lock"
    )
    raw, _payload = _read_json(root / OBJECTIVE_LOCK_PATH, "objective lock")
    if set(raw) != {
        "schema_version",
        "tournament",
        "locked_at_utc",
        "cohort_lock_sha256",
        "final_oos_lock_sha256",
        "objective_score_sha256",
        "objective",
        "bound_performances",
    }:
        raise ValueError("objective lock schema is invalid")
    finalists, finalist_ids, dnf_ids = _objective_inputs(root, config, state)
    objective = lock_objective_scores(
        finalists,
        finalist_team_ids=finalist_ids,
        dnf_team_ids=dnf_ids,
        config=config,
    )
    if (
        raw.get("objective_score_sha256") != objective.sha256
        or _json_bytes(raw.get("objective")) != _json_bytes(objective.to_dict())
        or _json_bytes(raw.get("bound_performances"))
        != _json_bytes([item.to_dict() for item in finalists])
    ):
        raise ValueError("objective lock differs from canonical finalist evidence")
    return objective, finalists


def _finite_score(value: Any, label: str, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not 0.0 <= score <= maximum:
        raise ValueError(f"{label} must be in [0, {maximum:g}]")
    return score


def _critic_ballot(
    root: Path,
    config: LoadedV2Config,
    objective: Any,
    raw: Mapping[str, Any],
) -> dict[str, object]:
    from crypto_trade.tournament.finals_v2 import ALLOWED_INTEGRITY_DQ_CODES

    if set(raw) != {"schema_version", "scores", "reviews", "dq_findings"} or raw.get(
        "schema_version"
    ) != 1:
        raise ValueError("Critic ballot schema is invalid")
    finalist_ids = tuple(objective.finalist_team_ids)
    scores = raw["scores"]
    reviews = raw["reviews"]
    findings = raw["dq_findings"]
    if not isinstance(scores, Mapping) or set(scores) != set(finalist_ids):
        raise ValueError("Critic ballot must score every finalist exactly")
    if not isinstance(reviews, Mapping) or set(reviews) != set(finalist_ids):
        raise ValueError("Critic ballot must review every finalist exactly")
    categories = tuple(config.raw["critic"]["category_order"])
    normalized_scores: dict[str, object] = {}
    normalized_reviews: dict[str, str] = {}
    totals: dict[str, float] = {}
    for team_id in finalist_ids:
        category_scores = scores[team_id]
        if not isinstance(category_scores, Mapping) or set(category_scores) != set(categories):
            raise ValueError(f"Critic categories are incomplete for {team_id}")
        normalized = {
            category: _finite_score(
                category_scores[category],
                f"critic.{team_id}.{category}",
                float(config.raw["critic"]["points_per_category"]),
            )
            for category in categories
        }
        review = _nonempty_text(reviews[team_id], f"reviews.{team_id}", maximum=20_000)
        normalized_scores[team_id] = normalized
        normalized_reviews[team_id] = review
        totals[team_id] = round(sum(normalized.values()), 6)
    if not isinstance(findings, Mapping):
        raise ValueError("Critic dq_findings must be a finalist mapping")
    unknown = set(findings) - set(finalist_ids)
    if unknown:
        raise ValueError(f"Critic findings name non-finalists: {sorted(unknown)}")
    normalized_findings: dict[str, list[dict[str, str]]] = {}
    for team_id, rows in findings.items():
        if not isinstance(rows, list) or not rows:
            raise ValueError("each Critic DQ finding list must be nonempty")
        normalized_rows: list[dict[str, str]] = []
        seen_codes: set[str] = set()
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {
                "code",
                "evidence_path",
                "evidence_sha256",
            }:
                raise ValueError("Critic DQ finding schema is invalid")
            code = row["code"]
            if code not in ALLOWED_INTEGRITY_DQ_CODES or code in seen_codes:
                raise ValueError("Critic DQ code is noncanonical or duplicated")
            evidence_path = _nonempty_text(row["evidence_path"], "evidence_path")
            unresolved = root / evidence_path
            path = unresolved.resolve()
            if not path.is_relative_to(root) or unresolved.is_symlink():
                raise ValueError("Critic DQ evidence path escapes the repository or is a symlink")
            evidence_sha256 = _nonempty_text(row["evidence_sha256"], "evidence_sha256")
            if _sha256_bytes(_safe_regular_bytes(path, "Critic DQ evidence")) != (
                evidence_sha256
            ):
                raise ValueError("Critic DQ evidence hash differs")
            normalized_rows.append(
                {
                    "code": code,
                    "evidence_path": evidence_path,
                    "evidence_sha256": evidence_sha256,
                }
            )
            seen_codes.add(code)
        normalized_findings[team_id] = normalized_rows
    return {
        "scores": normalized_scores,
        "totals": totals,
        "reviews": normalized_reviews,
        "dq_findings": normalized_findings,
    }


def _lock_critic(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    ballot, _payload = _read_json(args.ballot, "Critic ballot")
    lock_path = root / CRITIC_LOCK_PATH
    created = False
    normalized: dict[str, object] = {}
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "objective_locked")
            objective, _finalists = _recompute_objective(root, config, state)
            objective_sha256 = _verify_file_binding(
                root, state["objective_lock"], OBJECTIVE_LOCK_PATH, "objective lock"
            )
            normalized = _critic_ballot(root, config, objective, ballot)
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "objective_lock_sha256": objective_sha256,
                **normalized,
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["critic_lock"] = {"path": CRITIC_LOCK_PATH, "sha256": digest}
            state["phase"] = "critic_locked"
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": "critic_locked",
            "critic_lock": CRITIC_LOCK_PATH,
            "totals": normalized["totals"],
            "proposed_dq_team_ids": sorted(normalized["dq_findings"]),
        },
        args.json_out,
    )
    return 0


def _lock_critic_confirmations(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, _payload = _read_json(args.confirmation, "Critic confirmation")
    if set(raw) != {"schema_version", "authority", "confirmations", "notes"} or raw.get(
        "schema_version"
    ) != 1:
        raise ValueError("Critic confirmation schema is invalid")
    authority = _nonempty_text(raw["authority"], "confirmation authority", maximum=1000)
    notes = _nonempty_text(raw["notes"], "confirmation notes", maximum=20_000)
    lock_path = root / CRITIC_CONFIRMATION_LOCK_PATH
    created = False
    terminal_phase = "dq_confirmed"
    confirmed: dict[str, list[str]] = {}
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "critic_locked")
            objective, _finalists = _recompute_objective(root, config, state)
            critic_sha256 = _verify_file_binding(
                root, state["critic_lock"], CRITIC_LOCK_PATH, "Critic lock"
            )
            critic, _critic_payload = _read_json(root / CRITIC_LOCK_PATH, "Critic lock")
            proposed = critic.get("dq_findings")
            if not isinstance(proposed, Mapping):
                raise ValueError("Critic lock findings are malformed")
            confirmations = raw["confirmations"]
            if not isinstance(confirmations, Mapping):
                raise ValueError("Critic confirmations must be a mapping")
            unknown = set(confirmations) - set(objective.finalist_team_ids)
            if unknown:
                raise ValueError(f"confirmations name non-finalists: {sorted(unknown)}")
            for team_id, codes in confirmations.items():
                if not isinstance(codes, list) or not codes or len(codes) != len(set(codes)):
                    raise ValueError("confirmed DQ codes must be a nonempty unique list")
                proposed_codes = {
                    finding["code"] for finding in proposed.get(team_id, [])
                }
                if not set(codes).issubset(proposed_codes):
                    raise ValueError("confirmation cites a code not proposed by the Critic")
                confirmed[team_id] = list(codes)
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "critic_lock_sha256": critic_sha256,
                "authority": authority,
                "notes": notes,
                "confirmed_disqualifications": confirmed,
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["critic_confirmation_lock"] = {
                "path": CRITIC_CONFIRMATION_LOCK_PATH,
                "sha256": digest,
                "confirmed_disqualifications": confirmed,
            }
            if objective.finalist_team_ids and set(confirmed) == set(
                objective.finalist_team_ids
            ):
                terminal_phase = "integrity_review_required"
            state["phase"] = terminal_phase
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": terminal_phase,
            "critic_confirmation_lock": CRITIC_CONFIRMATION_LOCK_PATH,
            "confirmed_disqualifications": confirmed,
        },
        args.json_out,
    )
    return 0


def _lock_user_ballot(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    raw, _payload = _read_json(args.ballot, "user ballot")
    if set(raw) != {"schema_version", "scores", "rationales"} or raw.get(
        "schema_version"
    ) != 1:
        raise ValueError("user ballot schema is invalid")
    lock_path = root / USER_BALLOT_LOCK_PATH
    created = False
    scores: dict[str, float] = {}
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "dq_confirmed")
            objective, _finalists = _recompute_objective(root, config, state)
            confirmation_sha256 = _verify_file_binding(
                root,
                state["critic_confirmation_lock"],
                CRITIC_CONFIRMATION_LOCK_PATH,
                "Critic confirmation lock",
            )
            raw_scores = raw["scores"]
            rationales = raw["rationales"]
            if not isinstance(raw_scores, Mapping) or set(raw_scores) != set(
                objective.finalist_team_ids
            ):
                raise ValueError("user ballot must score every original finalist exactly")
            if not isinstance(rationales, Mapping) or set(rationales) != set(
                objective.finalist_team_ids
            ):
                raise ValueError("user ballot must explain every original finalist exactly")
            scores = {
                team_id: _finite_score(raw_scores[team_id], f"user.{team_id}", 15.0)
                for team_id in objective.finalist_team_ids
            }
            normalized_rationales = {
                team_id: _nonempty_text(
                    rationales[team_id], f"rationales.{team_id}", maximum=20_000
                )
                for team_id in objective.finalist_team_ids
            }
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "critic_confirmation_lock_sha256": confirmation_sha256,
                "scores": scores,
                "rationales": normalized_rationales,
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["user_ballot_lock"] = {
                "path": USER_BALLOT_LOCK_PATH,
                "sha256": digest,
            }
            state["phase"] = "user_locked"
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {"phase": "user_locked", "user_ballot_lock": USER_BALLOT_LOCK_PATH, "scores": scores},
        args.json_out,
    )
    return 0


def _lock_selection(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.finals_v2 import (
        assess_paper_eligibility,
        combine_locked_scores,
    )

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    lock_path = root / SELECTION_LOCK_PATH
    created = False
    final_scores: Any = None
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "user_locked")
            objective, finalists = _recompute_objective(root, config, state)
            objective_sha256 = _verify_file_binding(
                root, state["objective_lock"], OBJECTIVE_LOCK_PATH, "objective lock"
            )
            critic_sha256 = _verify_file_binding(
                root, state["critic_lock"], CRITIC_LOCK_PATH, "Critic lock"
            )
            confirmation_sha256 = _verify_file_binding(
                root,
                state["critic_confirmation_lock"],
                CRITIC_CONFIRMATION_LOCK_PATH,
                "Critic confirmation lock",
            )
            user_sha256 = _verify_file_binding(
                root, state["user_ballot_lock"], USER_BALLOT_LOCK_PATH, "user ballot lock"
            )
            critic, _ = _read_json(root / CRITIC_LOCK_PATH, "Critic lock")
            confirmation, _ = _read_json(
                root / CRITIC_CONFIRMATION_LOCK_PATH, "Critic confirmation lock"
            )
            user, _ = _read_json(root / USER_BALLOT_LOCK_PATH, "user ballot lock")
            critic_totals = critic.get("totals")
            user_scores = user.get("scores")
            disqualifications = confirmation.get("confirmed_disqualifications")
            if not all(
                isinstance(item, Mapping)
                for item in (critic_totals, user_scores, disqualifications)
            ):
                raise ValueError("locked ballot or DQ records are malformed")
            final_scores = combine_locked_scores(
                objective,
                critic_ballot=critic_totals,
                user_ballot=user_scores,
                integrity_disqualifications=disqualifications,
            )
            if final_scores.status == "integrity-review-required":
                raise ValueError("all finalists are DQed; manual integrity review is required")
            paper = {
                finalist.binding.team_id: assess_paper_eligibility(
                    finalist, config
                ).to_dict()
                for finalist in finalists
            }
            dnf_appendix = {
                team_id: state["teams"][team_id]["dnf"]
                for team_id in objective.dnf_team_ids
            }
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "locked_at_utc": _now(),
                "objective_lock_sha256": objective_sha256,
                "critic_lock_sha256": critic_sha256,
                "critic_confirmation_lock_sha256": confirmation_sha256,
                "user_ballot_lock_sha256": user_sha256,
                "final_scores": final_scores.to_dict(),
                "paper_eligibility": paper,
                "dnf_appendix": dnf_appendix,
            }
            digest = _first_add_json(lock_path, payload)
            created = True
            state["selection_lock"] = {
                "path": SELECTION_LOCK_PATH,
                "sha256": digest,
                "winner_team_id": final_scores.winner_team_id,
            }
            state["phase"] = "selection_locked"
    except Exception:
        if created:
            lock_path.unlink(missing_ok=True)
        raise
    _emit(
        {
            "phase": "selection_locked",
            "selection_lock": SELECTION_LOCK_PATH,
            "winner_team_id": final_scores.winner_team_id,
            "scores": [score.to_dict() for score in final_scores.scores],
        },
        args.json_out,
    )
    return 0


def _next_eight_hour_boundary(value: datetime) -> datetime:
    normalized = value.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    hours = 8 - (normalized.hour % 8)
    if value == normalized and normalized.hour % 8 == 0:
        hours = 8
    return normalized + timedelta(hours=hours)


def _freeze_winner(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    freeze_path = root / WINNER_FREEZE_PATH
    paper_genesis_path = root / TOP40_V2_LAYOUT.tournament_root / "paper_journal_genesis.json"
    created_freeze = False
    created_genesis = False
    payload: dict[str, object] = {}
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "selection_locked")
            selection_sha256 = _verify_file_binding(
                root, state["selection_lock"], SELECTION_LOCK_PATH, "selection lock"
            )
            winner_team_id = state["selection_lock"].get("winner_team_id")
            if winner_team_id not in TEAM_IDS:
                raise ValueError("selection lock has no valid winner")
            team = _team(state, str(winner_team_id))
            if team["status"] != "canonical_complete":
                raise ValueError("winner has no complete canonical final-OOS result")
            _verify_qualified_candidate(root, str(winner_team_id), team)
            frozen_at = datetime.now(UTC)
            paper_start = _next_eight_hour_boundary(frozen_at)
            paper_genesis = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "winner_team_id": winner_team_id,
                "selection_lock_sha256": selection_sha256,
                "created_at_utc": frozen_at.isoformat(),
                "paper_start_boundary_utc": paper_start.isoformat(),
                "live_orders_enabled": False,
            }
            paper_genesis_sha256 = _first_add_json(paper_genesis_path, paper_genesis)
            created_genesis = True
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "frozen_at_utc": frozen_at.isoformat(),
                "winner_team_id": winner_team_id,
                "selection_lock_sha256": selection_sha256,
                "finalist_freeze": team["finalist_freeze"],
                "canonical_result": team["canonical_result"],
                "paper_start_boundary_utc": paper_start.isoformat(),
                "quarantine_boundaries": 3,
                "paper_journal_genesis_path": paper_genesis_path.relative_to(root).as_posix(),
                "paper_journal_genesis_sha256": paper_genesis_sha256,
                "live_orders_enabled": False,
            }
            digest = _first_add_json(freeze_path, payload)
            created_freeze = True
            state["winner_freeze"] = {
                "path": WINNER_FREEZE_PATH,
                "sha256": digest,
                "winner_team_id": winner_team_id,
                "live_orders_enabled": False,
            }
            state["phase"] = "paper_frozen"
    except Exception:
        if created_freeze:
            freeze_path.unlink(missing_ok=True)
        if created_genesis:
            paper_genesis_path.unlink(missing_ok=True)
        raise
    _emit(payload, args.json_out)
    return 0


def _verify_winner_freeze(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    state = read_run_state(root, config)
    _require_phase(state, "paper_frozen")
    digest = _verify_file_binding(
        root, state["winner_freeze"], WINNER_FREEZE_PATH, "winner freeze"
    )
    raw, _payload = _read_json(root / WINNER_FREEZE_PATH, "winner freeze")
    if raw.get("live_orders_enabled") is not False:
        raise ValueError("winner freeze must keep live orders disabled")
    genesis_path = raw.get("paper_journal_genesis_path")
    genesis_sha256 = raw.get("paper_journal_genesis_sha256")
    if not isinstance(genesis_path, str) or not isinstance(genesis_sha256, str):
        raise ValueError("winner freeze paper-journal binding is malformed")
    if _sha256_bytes(_safe_regular_bytes(root / genesis_path, "paper journal genesis")) != (
        genesis_sha256
    ):
        raise ValueError("paper journal genesis differs from winner freeze")
    _emit(
        {
            "valid": True,
            "winner_team_id": raw.get("winner_team_id"),
            "winner_freeze_sha256": digest,
            "live_orders_enabled": False,
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
    from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

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
    source_bundle_sha256, _source_entries = source_bundle_fingerprint(
        root,
        team_id,
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
    )
    return {
        "candidate_id": candidate_id,
        "strategy_sha256": strategy_sha256,
        "risk_policy_sha256": risk_sha256,
        "source_bundle_sha256": source_bundle_sha256,
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
    include = args.stage == "development"
    _emit(_assessment_output(assessment, include_observations=include), args.json_out)
    return 0 if assessment.passed else 1


def _completed_candidate(
    journal: JournalState, team_id: str, candidate_id: str
) -> tuple[Any, Mapping[str, Any], Mapping[str, Any], str]:
    accounting = journal.teams[team_id]
    registration = accounting.registrations.get(candidate_id)
    result = accounting.results.get(candidate_id)
    registration_sha256 = accounting.registration_sha256.get(candidate_id)
    if not isinstance(registration, Mapping):
        raise ValueError("qualification candidate was not preregistered")
    if not isinstance(result, Mapping) or result.get("status") != "completed":
        raise ValueError("qualification candidate has no completed organizer-journal result")
    if not isinstance(registration_sha256, str):
        raise ValueError("qualification candidate registration hash is missing")
    return accounting, registration, result, registration_sha256


def _verify_candidate_registration_matches_current(
    root: Path,
    config: LoadedV2Config,
    team_id: str,
    registration: Mapping[str, Any],
) -> None:
    strategy_sha256, risk_sha256, source_sha256 = _current_candidate_hashes(root, team_id)
    if (
        registration.get("strategy_sha256") != strategy_sha256
        or registration.get("risk_config_sha256") != risk_sha256
        or registration.get("source_bundle_sha256") != source_sha256
        or registration.get("config_sha256") != config.sha256
    ):
        raise ValueError("current candidate differs from its exact preregistration")


def _derive_qualification_evidence(
    root: Path,
    runner_record: Mapping[str, Any],
    *,
    team_id: str,
    stage: str,
    candidate_id: str,
    trial_count: int,
    parameter_neighborhood_manifest: str | None = None,
    walk_forward_manifest: str | None = None,
) -> Any:
    from crypto_trade.tournament.evidence_v2 import build_qualification_evidence

    if runner_record.get("team_id") != team_id or runner_record.get("stage") != stage:
        raise ValueError("runner record stage/team differs from the qualification command")
    return build_qualification_evidence(
        root,
        runner_record,
        candidate_id=candidate_id,
        trial_count=trial_count,
        parameter_neighborhood_manifest_path=parameter_neighborhood_manifest,
        walk_forward_manifest_path=walk_forward_manifest,
    )


def _publish_immutable_bytes(path: Path, payload: bytes, label: str) -> str:
    if path.is_symlink():
        raise ValueError(f"{label} cannot be a symlink")
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise ValueError(f"refusing to replace immutable {label}")
    else:
        _atomic_write_bytes(path, payload)
    return _sha256_bytes(payload)


def _canonical_runner_record_path(
    team_id: str, stage: str, *, candidate_id: str | None = None
) -> str:
    if stage == "development":
        if not candidate_id:
            raise ValueError("development runner record requires candidate_id")
        return (
            f"{TOP40_V2_LAYOUT.report_root(team_id)}/qualification-attempts/"
            f"{candidate_id}.runner-record.json"
        )
    if stage == "private":
        return f"{PRIVATE_ROOT}/artifacts/{team_id}/runner_record.json"
    if stage == "final_oos":
        return f"{TOP40_V2_LAYOUT.report_root(team_id)}/final-oos/runner_record.json"
    raise ValueError("runner-record stage is invalid")


def _record_development_assessment(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    runner_record, runner_payload = _read_json(args.runner_record, "development runner record")
    assessment: QualificationAssessment | None = None
    output: dict[str, object] = {}
    with _edit_state(root, config) as state:
        _require_phase(state, "research")
        team = _team(state, args.team_id)
        if team["status"] not in {"pending_phase0", "researching"}:
            raise ValueError(f"development assessment is closed for {args.team_id}")
        if team["family_count"] < 1 or team["active_family_id"] is None:
            raise ValueError("development assessment requires a preregistered mechanism family")
        journal = _load_research_journal(
            root, config, state, recover_projection=True
        )
        accounting, registration, _result, registration_sha256 = _completed_candidate(
            journal, args.team_id, args.candidate_id
        )
        _verify_candidate_registration_matches_current(
            root, config, args.team_id, registration
        )
        built = _derive_qualification_evidence(
            root,
            runner_record,
            team_id=args.team_id,
            stage="development",
            candidate_id=args.candidate_id,
            trial_count=accounting.material_trial_count,
            parameter_neighborhood_manifest=args.parameter_neighborhood_manifest,
            walk_forward_manifest=args.walk_forward_manifest,
        )
        if Path(args.runner_record).read_bytes() != runner_payload:
            raise ValueError("development runner record changed during evidence derivation")
        raw = dict(built.evidence)
        payload = _json_bytes(raw)
        assessment = _assessment(raw, payload, config, "development")
        bindings = _identity_bindings(root, config, args.team_id, raw)
        if bindings["trial_count"] != accounting.material_trial_count:
            raise ValueError("development evidence trial count differs from organizer journal")
        output = _assessment_output(assessment, include_observations=True)
        previous = team["development_assessment"]
        if (
            isinstance(previous, Mapping)
            and previous.get("evidence_sha256") == assessment.evidence_sha256
        ):
            _emit(previous, args.json_out)
            return 0 if previous.get("passed") is True else 1
        provenance_payload = _json_bytes(built.provenance)
        runner_canonical = _json_bytes(runner_record)
        runner_path = root / _canonical_runner_record_path(
            args.team_id, "development", candidate_id=args.candidate_id
        )
        runner_sha256 = _publish_immutable_bytes(
            runner_path, runner_canonical, "development runner record"
        )
        attempts_root = (
            root
            / TOP40_V2_LAYOUT.report_root(args.team_id)
            / "qualification-attempts"
        )
        attempt_path = attempts_root / f"{args.candidate_id}.json"
        attempt_payload = _json_bytes(
            {
                "schema_version": 1,
                "evidence": raw,
                "provenance": built.provenance,
                "assessment": assessment.to_dict(include_observations=True),
                "runner_record_path": runner_path.relative_to(root).as_posix(),
                "runner_record_sha256": runner_sha256,
                "organizer_journal_head_sha256": journal.head_sha256,
                "registration_sha256": registration_sha256,
            }
        )
        attempt_sha256 = _publish_immutable_bytes(
            attempt_path, attempt_payload, "development qualification attempt"
        )
        record = {
            **output,
            "recorded_at_utc": _now(),
            "provenance_sha256": _sha256_bytes(provenance_payload),
            "attempt_path": attempt_path.relative_to(root).as_posix(),
            "attempt_sha256": attempt_sha256,
            "organizer_journal_head_sha256": journal.head_sha256,
        }
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
                "development_provenance_sha256": _sha256_bytes(provenance_payload),
                "development_attempt_path": attempt_path.relative_to(root).as_posix(),
                "development_attempt_sha256": attempt_sha256,
                "development_runner_record_path": runner_path.relative_to(root).as_posix(),
                "development_runner_record_sha256": runner_sha256,
                "registration_sha256": registration_sha256,
                "organizer_journal_head_sha256": journal.head_sha256,
            }
            team["status"] = "qualifier_candidate_frozen"
    if assessment is None:
        raise AssertionError("development assessment was not created")
    _emit(output, args.json_out)
    return 0 if assessment.passed else 1


def _record_private_assessment(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    config = _config(root, args.config)
    runner_record, runner_payload = _read_json(args.runner_record, "private runner record")
    assessment: QualificationAssessment | None = None
    public: dict[str, object] = {}
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
            if not isinstance(candidate, Mapping):
                raise ValueError("private candidate freeze is missing")
            journal = _load_research_journal(
                root, config, state, recover_projection=True
            )
            accounting, registration, _result, registration_sha256 = _completed_candidate(
                journal, args.team_id, str(candidate.get("candidate_id"))
            )
            _verify_candidate_registration_matches_current(
                root, config, args.team_id, registration
            )
            built = _derive_qualification_evidence(
                root,
                runner_record,
                team_id=args.team_id,
                stage="private",
                candidate_id=str(candidate.get("candidate_id")),
                trial_count=accounting.material_trial_count,
            )
            if Path(args.runner_record).read_bytes() != runner_payload:
                raise ValueError("private runner record changed during evidence derivation")
            raw = dict(built.evidence)
            payload = _json_bytes(raw)
            assessment = _assessment(raw, payload, config, "private")
            bindings = _identity_bindings(root, config, args.team_id, raw)
            if any(
                candidate.get(field) != bindings[field]
                for field in (
                    "candidate_id",
                    "strategy_sha256",
                    "risk_policy_sha256",
                    "source_bundle_sha256",
                    "config_sha256",
                    "trial_count",
                )
            ) or candidate.get("registration_sha256") != registration_sha256:
                raise ValueError("private evidence differs from the frozen development candidate")
            public = _assessment_output(assessment, include_observations=False)
            runner_path = root / _canonical_runner_record_path(args.team_id, "private")
            runner_sha256 = _publish_immutable_bytes(
                runner_path, _json_bytes(runner_record), "private runner record"
            )
            sealed = {
                "schema_version": 1,
                "sealed_at_utc": _now(),
                "evidence": raw,
                "provenance": built.provenance,
                "assessment": assessment.to_dict(include_observations=True),
                "runner_record_path": runner_path.relative_to(root).as_posix(),
                "runner_record_sha256": runner_sha256,
                "organizer_journal_head_sha256": journal.head_sha256,
                "registration_sha256": registration_sha256,
            }
            sealed_sha256 = _first_add_json(sealed_path, sealed)
            created_sealed = True
            result = {
                **public,
                "sealed_record_path": sealed_path.relative_to(root).as_posix(),
                "sealed_record_sha256": sealed_sha256,
                "runner_record_path": runner_path.relative_to(root).as_posix(),
                "runner_record_sha256": runner_sha256,
                "organizer_journal_head_sha256": journal.head_sha256,
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
    if assessment is None:
        raise AssertionError("private assessment was not created")
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
            journal = _load_research_journal(
                root, config, state, recover_projection=True
            )
            pending = {
                team_id: list(journal.teams[team_id].pending_candidate_ids)
                for team_id in TEAM_IDS
                if journal.teams[team_id].pending_candidate_ids
            }
            if pending:
                raise ValueError(
                    f"qualification cannot close with unterminated trial registrations: {pending}"
                )
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
                "research_journal": _research_binding(journal),
                "qualified_team_ids": list(qualified),
                "dnf_team_ids": [team_id for team_id in TEAM_IDS if team_id not in qualified],
                "teams": _qualification_summary(state),
                "research_accounting": {
                    team_id: {
                        "material_trial_count": journal.teams[
                            team_id
                        ].material_trial_count,
                        "cpu_hours": journal.teams[team_id].cpu_hours,
                        "wall_clock_hours": journal.teams[team_id].wall_clock_hours,
                    }
                    for team_id in TEAM_IDS
                },
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
    from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

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
    source_bundle_sha256, _entries = source_bundle_fingerprint(
        root,
        team_id,
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
    )
    if candidate.get("source_bundle_sha256") != source_bundle_sha256:
        raise ValueError(f"qualified source bundle changed after development freeze: {team_id}")
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
    for path_field, sha_field, label in (
        (
            "development_attempt_path",
            "development_attempt_sha256",
            "development qualification attempt",
        ),
        (
            "development_runner_record_path",
            "development_runner_record_sha256",
            "development runner record",
        ),
    ):
        relative = candidate.get(path_field)
        if not isinstance(relative, str):
            raise ValueError(f"{label} binding is missing for {team_id}")
        path = root / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or candidate.get(sha_field) != _sha256_bytes(path.read_bytes())
        ):
            raise ValueError(f"{label} changed after qualification: {team_id}")
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
    from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

    root = Path.cwd().resolve()
    config = _config(root, args.config)
    cohort_path = root / TOP40_V2_LAYOUT.finalist_cohort_lock_path
    created_lock = False
    finalists: tuple[str, ...] = ()
    terminal_phase = "finalist_cohort_frozen"
    try:
        with _edit_state(root, config) as state:
            _require_phase(state, "qualification_closed")
            journal = _load_research_journal(
                root, config, state, recover_projection=False
            )
            qualification_sha256 = _verify_file_binding(
                root, state["qualification_lock"], QUALIFICATION_LOCK_PATH, "qualification lock"
            )
            if not all_teams_terminal_for_qualification(state):
                raise ValueError("the finalist cohort requires ten terminal qualification records")
            finalists = finalist_team_ids(state)
            source_manifests: dict[str, object] = {}
            for team_id in finalists:
                _verify_qualified_candidate(root, team_id, state["teams"][team_id])
                source_sha256, entries = source_bundle_fingerprint(
                    root,
                    team_id,
                    f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py",
                )
                source_manifests[team_id] = {
                    "source_bundle_sha256": source_sha256,
                    "entries": list(entries),
                }
            payload = {
                "schema_version": 1,
                "tournament": TOP40_V2_LAYOUT.name,
                "config_sha256": config.sha256,
                "qualification_lock_sha256": qualification_sha256,
                "research_journal": _research_binding(journal),
                "locked_at_utc": _now(),
                "finalist_team_ids": list(finalists),
                "dnf_team_ids": [team_id for team_id in TEAM_IDS if team_id not in finalists],
                "finalist_source_manifests": source_manifests,
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
                    team = state["teams"][team_id]
                    candidate = team["qualifier_candidate"]
                    team["finalist_freeze"] = {
                        "cohort_lock_path": TOP40_V2_LAYOUT.finalist_cohort_lock_path,
                        "cohort_lock_sha256": digest,
                        "candidate_id": candidate["candidate_id"],
                        "strategy_sha256": candidate["strategy_sha256"],
                        "risk_policy_sha256": candidate["risk_policy_sha256"],
                        "source_bundle_sha256": candidate["source_bundle_sha256"],
                        "source_manifest": source_manifests[team_id],
                    }
                    team["status"] = "finalist_frozen"
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
    journal = _load_research_journal(
        root, config, state, recover_projection=False
    )
    if len(journal.records) != 1 or any(
        journal.teams[team_id].material_trial_count != 0 for team_id in TEAM_IDS
    ):
        raise ValueError("Phase 0 requires a pristine genesis-only research journal")
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
    journal_path = root / RESEARCH_JOURNAL_PATH
    if (journal_path.exists() or journal_path.is_symlink()) and not args.force:
        raise ValueError("V2 organizer journal already exists; use --force only for a reset")
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
    genesis = plan_genesis(timestamp_utc=_journal_now(), policy=_research_policy(config))
    _atomic_write_bytes(journal_path, genesis.replacement_journal_bytes)
    journal = validate_journal_bytes(
        genesis.replacement_journal_bytes, _research_policy(config)
    )
    state["research_journal"] = _research_binding(journal)
    validate_run_state(state, config)
    _atomic_write_json(state_path, state)
    _emit(
        {
            "initialized": len(TEAM_IDS),
            "phase": state["phase"],
            "state_path": TOP40_V2_LAYOUT.state_path,
            "research_journal_path": RESEARCH_JOURNAL_PATH,
            "research_journal_genesis_sha256": journal.genesis_sha256,
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
    _common_config(assess)

    register = commands.add_parser("register-family", help="register the initial mechanism family")
    register.add_argument("team_id", choices=TEAM_IDS)
    register.add_argument("registration")
    _common_config(register)

    pivot = commands.add_parser("pivot-team", help="register a documented mechanism pivot")
    pivot.add_argument("team_id", choices=TEAM_IDS)
    pivot.add_argument("registration")
    _common_config(pivot)

    register_trial = commands.add_parser(
        "register-trial", help="preregister one material candidate in the organizer journal"
    )
    register_trial.add_argument("team_id", choices=TEAM_IDS)
    register_trial.add_argument("registration")
    _common_config(register_trial)

    trial_result = commands.add_parser(
        "record-trial-result", help="append one terminal material-trial result"
    )
    trial_result.add_argument("team_id", choices=TEAM_IDS)
    trial_result.add_argument("result")
    _common_config(trial_result)

    research_status = commands.add_parser(
        "research-status", help="validate journal projections and report consumed budgets"
    )
    research_status.add_argument("team_id", choices=TEAM_IDS, nargs="?")
    _common_config(research_status)

    run_window = commands.add_parser(
        "run-window",
        help="reserve and execute one organizer-owned development or private window",
    )
    run_window.add_argument("stage", choices=("development", "private"))
    run_window.add_argument("team_id", choices=TEAM_IDS)
    run_window.add_argument("candidate_id")
    _common_config(run_window)

    development = commands.add_parser(
        "record-development-assessment",
        help="derive and record a visible development gate assessment from runner artifacts",
    )
    development.add_argument("team_id", choices=TEAM_IDS)
    development.add_argument("runner_record")
    development.add_argument("--candidate-id", required=True)
    development.add_argument("--parameter-neighborhood-manifest", required=True)
    development.add_argument("--walk-forward-manifest", required=True)
    _common_config(development)

    private = commands.add_parser(
        "record-private-assessment",
        help="derive, consume, and seal the team's one private ticket from runner artifacts",
    )
    private.add_argument("team_id", choices=TEAM_IDS)
    private.add_argument("runner_record")
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

    finalist = commands.add_parser(
        "run-finalist", help="consume one organizer reveal and run two sealed deterministic replays"
    )
    finalist.add_argument("team_id", choices=TEAM_IDS)
    _common_config(finalist)

    final_oos = commands.add_parser(
        "lock-final-oos", help="lock every finalist canonical result before scoring"
    )
    _common_config(final_oos)

    objective = commands.add_parser(
        "lock-objective", help="lock the canonical 70-point automatic score"
    )
    _common_config(objective)

    critic = commands.add_parser(
        "lock-critic", help="lock the complete category-level Critic ballot"
    )
    critic.add_argument("ballot")
    _common_config(critic)

    confirmations = commands.add_parser(
        "lock-critic-confirmations", help="independently confirm proposed integrity DQs"
    )
    confirmations.add_argument("confirmation")
    _common_config(confirmations)

    user = commands.add_parser(
        "lock-user-ballot", help="lock one 0..15 score for every original finalist"
    )
    user.add_argument("ballot")
    _common_config(user)

    selection = commands.add_parser(
        "lock-selection", help="combine locked scores, DQs, and paper eligibility"
    )
    _common_config(selection)

    winner = commands.add_parser(
        "freeze-winner", help="freeze the selected candidate for prospective paper observation"
    )
    _common_config(winner)

    verify_winner = commands.add_parser(
        "verify-winner-freeze", help="verify winner and paper-journal bindings"
    )
    _common_config(verify_winner)
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
        "register-trial": _register_trial,
        "record-trial-result": _record_trial_result,
        "research-status": _research_status,
        "run-window": _run_window,
        "record-development-assessment": _record_development_assessment,
        "record-private-assessment": _record_private_assessment,
        "withdraw-team": _withdraw_team,
        "close-qualification": _close_qualification,
        "lock-finalist-cohort": _lock_finalist_cohort,
        "run-finalist": _run_finalist,
        "lock-final-oos": _lock_final_oos,
        "lock-objective": _lock_objective,
        "lock-critic": _lock_critic,
        "lock-critic-confirmations": _lock_critic_confirmations,
        "lock-user-ballot": _lock_user_ballot,
        "lock-selection": _lock_selection,
        "freeze-winner": _freeze_winner,
        "verify-winner-freeze": _verify_winner_freeze,
    }
    try:
        return dispatch[args.command](args)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
