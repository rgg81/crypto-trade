"""Draft Amendment 0005 prospective declared-score diagnostic lifecycle."""

from __future__ import annotations

import contextlib
import fcntl
import math
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from crypto_trade.tournament import (
    amendment_v2,
    development_score_diagnostics_v5,
    runner_schema3_compat_v4,
    score_diagnostic_compat_v2,
    score_diagnostics_v2,
)
from crypto_trade.tournament.amendment_integrity_v2 import (
    atomic_write_bytes,
    ensure_owner_directory,
    git_bytes,
    git_path,
    pretty_json_bytes,
    read_repo_file,
    require_no_git_history,
    sha256_bytes,
    strict_json_object,
    unique_first_add_commit,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.research_v2 import build_trial_registration
from crypto_trade.tournament.score_adapter_protocol_v5 import ADAPTER_ID
from crypto_trade.tournament.top40_v2 import LoadedV2Config, load_config

AMENDMENT_ID = "top40-v2-amendment-0005-prospective-development-score-adapters"
AMENDMENT_ROOT = "tournament/top40-v2/amendments/0005"
DRAFT_PATH = f"{AMENDMENT_ROOT}/draft.json"
REVIEW_PATH = f"{AMENDMENT_ROOT}/REVIEW.json"
FREEZE_PATH = f"{AMENDMENT_ROOT}/freeze.json"

ELIGIBLE_TEAMS = tuple(f"team-{number:02d}" for number in range(4, 11))
EXCLUDED_TEAMS = ("team-03",)
OPT_IN_PARAMETER = "_top40_v2_score_adapter"
SEMANTIC_REVIEW_KIND = "top40-v2-score-semantic-coupling-static-review-v1"
TERMINAL_RESULT_NAME = "terminal-result.json"
_AUTHORITY_KEYS = {
    "team_id",
    "family_id",
    "candidate_id",
    "candidate_registration_sha256",
    "registration_input_path",
    "registration_commit",
    "registration_event_record_sha256",
    "registration_event_sequence",
    "trial_result_record_sha256",
    "trial_result_event_sequence",
    "strategy_sha256",
    "risk_policy_sha256",
    "source_bundle_sha256",
    "candidate_seed",
    "config_sha256",
    "score_manifest_path",
    "score_manifest_sha256",
    "score_manifest_commit",
    "semantic_coupling_review_path",
    "semantic_coupling_review_sha256",
    "semantic_coupling_review_commit",
    "snapshot_manifest_path",
    "snapshot_manifest_sha256",
    "development_target_path",
    "development_target_sha256",
    "runner_record_path",
    "runner_record_sha256",
    "amendment_freeze_sha256",
    "amendment_freeze_commit",
    "research_state_sha256",
    "research_journal_record_count",
    "research_journal_head_sha256",
}

PARENT_AUTHORITIES = {
    "amendment_0001_scientific_engine_sha256": (
        "a0b99bd2928a64a37b6b9f6d900bbd8ddfc2f2e49b87e6f6633176228bfd2d4d"
    ),
    "amendment_0002_schema3_facade_sha256": (
        "fc70dbdb752c58857c5ed60a96e497324e93b9d5dc7e6afa0692bd3e02ad21aa"
    ),
    "amendment_0004_active_runner_sha256": (
        "03006ea1ce391ef3c8da6244acb89aab19f7e63d1e0a617e2743894a575fd6cd"
    ),
    "amendment_0004_active_entrypoint_sha256": (
        "6031937952a29a1a226a778cd1bcfc2c9869559ab30465bdbebe6292c6a88377"
    ),
}

IMPLEMENTATION_FILE_PATHS = (
    "scripts/top40_v2_amendment_0005_draft.py",
    "src/crypto_trade/tournament/_score_worker_v5.py",
    "src/crypto_trade/tournament/amendment_0005_v2.py",
    "src/crypto_trade/tournament/development_score_diagnostics_v5.py",
    "src/crypto_trade/tournament/generic_score_adapter_v5.py",
    "src/crypto_trade/tournament/score_adapter_protocol_v5.py",
    "tests/tournament/test_top40_v2_amendment_0005.py",
    "tests/tournament/test_top40_v2_development_score_diagnostics_v5.py",
    "tests/tournament/test_top40_v2_score_adapter_v5.py",
    f"{AMENDMENT_ROOT}/AMENDMENT.md",
    f"{AMENDMENT_ROOT}/DRAFT-SCOPE-INCIDENT.md",
    f"{AMENDMENT_ROOT}/SCORE-ADAPTER-CONTRACT.md",
    DRAFT_PATH,
    f"{AMENDMENT_ROOT}/templates/amendment-freeze.schema.json",
    f"{AMENDMENT_ROOT}/templates/amendment-review.schema.json",
    f"{AMENDMENT_ROOT}/templates/development-score-diagnostic-reservation.schema.json",
    f"{AMENDMENT_ROOT}/templates/development-score-diagnostic-result.schema.json",
    f"{AMENDMENT_ROOT}/templates/score-adapter-manifest.schema.json",
)

_A1_MODULE = score_diagnostics_v2
_A1_MATERIALIZE = _A1_MODULE._materialize_team_tree
_A1_TARGETS_EXACT = _A1_MODULE._targets_exact
_A2_MODULE = score_diagnostic_compat_v2
_A2_RUN = _A2_MODULE.run_score_diagnostic_with_schema3_compatibility
_A4_MODULE = runner_schema3_compat_v4
_A4_RUN = _A4_MODULE.run
_A4_VERIFY = _A4_MODULE._verify_amendment_authorities

_SHA = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


class Amendment0005Error(ValueError):
    """The prospective score-diagnostic authority failed closed."""


def _regular_bytes(path: Path, label: str, *, maximum_bytes: int = 32 * 1024 * 1024) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise Amendment0005Error(f"{label} is missing or unsafe: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > maximum_bytes:
            raise Amendment0005Error(f"{label} must be a bounded single-link regular file")
        chunks: list[bytes] = []
        remaining = info.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise Amendment0005Error(f"{label} changed while read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise Amendment0005Error(f"{label} grew while read")
        final = os.fstat(descriptor)
        if (
            final.st_dev != info.st_dev
            or final.st_ino != info.st_ino
            or final.st_size != info.st_size
            or final.st_nlink != 1
            or not stat.S_ISREG(final.st_mode)
        ):
            raise Amendment0005Error(f"{label} changed while read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def verify_parent_authorities(root: str | Path) -> None:
    root_path = Path(root).resolve()
    bindings = (
        (
            _A1_MODULE,
            PARENT_AUTHORITIES["amendment_0001_scientific_engine_sha256"],
            {
                "_materialize_team_tree": _A1_MATERIALIZE,
                "_targets_exact": _A1_TARGETS_EXACT,
                **development_score_diagnostics_v5.frozen_science_helper_bindings(),
            },
            "Amendment 0001 scientific engine",
        ),
        (
            _A2_MODULE,
            PARENT_AUTHORITIES["amendment_0002_schema3_facade_sha256"],
            {"run_score_diagnostic_with_schema3_compatibility": _A2_RUN},
            "Amendment 0002 schema-3 facade",
        ),
        (
            _A4_MODULE,
            PARENT_AUTHORITIES["amendment_0004_active_runner_sha256"],
            {"run": _A4_RUN, "_verify_amendment_authorities": _A4_VERIFY},
            "Amendment 0004 active runner",
        ),
    )
    for module, expected_hash, identities, label in bindings:
        payload = _regular_bytes(Path(module.__file__).resolve(), label)
        if sha256_bytes(payload) != expected_hash:
            raise Amendment0005Error(f"{label} bytes changed")
        if any(getattr(module, name, None) is not value for name, value in identities.items()):
            raise Amendment0005Error(f"{label} callable identity changed")
    _relative, _path, active_bytes, _stat = read_repo_file(
        root_path,
        "scripts/top40_v2_tournament_active.py",
        "Amendment 0004 active entrypoint",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(active_bytes) != PARENT_AUTHORITIES["amendment_0004_active_entrypoint_sha256"]:
        raise Amendment0005Error("Amendment 0004 active entrypoint bytes changed")
    development_score_diagnostics_v5.verify_frozen_science_helper_identities()
    _A4_VERIFY()


def _read_pretty_json(root: Path, relative: str, label: str) -> tuple[Mapping[str, Any], bytes]:
    _relative, _path, payload, _stat = read_repo_file(
        root, relative, label, maximum_bytes=8 * 1024 * 1024, require_single_link=True
    )
    raw = strict_json_object(payload, label)
    if pretty_json_bytes(raw) != payload:
        raise Amendment0005Error(f"{label} must be canonical pretty JSON")
    return raw, payload


def _load_draft(root: Path) -> tuple[Mapping[str, Any], bytes]:
    draft, payload = _read_pretty_json(root, DRAFT_PATH, "Amendment 0005 draft")
    if set(draft) != {
        "schema_version",
        "amendment_id",
        "status",
        "prospective",
        "opt_in",
        "eligible_teams",
        "excluded_teams",
        "stage",
        "non_material",
        "automatic_qualification_gate",
        "evidence_kind",
        "parent_authorities",
    }:
        raise Amendment0005Error("Amendment 0005 draft has invalid keys")
    if (
        draft["schema_version"] != 1
        or draft["amendment_id"] != AMENDMENT_ID
        or draft["status"] != "draft"
        or draft["prospective"] is not True
        or draft["opt_in"] is not True
        or draft["eligible_teams"] != list(ELIGIBLE_TEAMS)
        or draft["excluded_teams"] != list(EXCLUDED_TEAMS)
        or draft["stage"] != "development"
        or draft["non_material"] is not True
        or draft["automatic_qualification_gate"] is not False
        or draft["evidence_kind"] != "declared-score-diagnostic"
        or draft["parent_authorities"] != PARENT_AUTHORITIES
    ):
        raise Amendment0005Error("Amendment 0005 draft policy differs")
    return draft, payload


def _implementation_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILE_PATHS:
        _normalized, _path, payload, _stat = read_repo_file(
            root,
            relative,
            f"Amendment 0005 implementation file {relative}",
            maximum_bytes=16 * 1024 * 1024,
            require_single_link=True,
        )
        result[relative] = sha256_bytes(payload)
    return result


def _load_freeze(root: Path) -> tuple[Mapping[str, Any], bytes, str]:
    freeze, payload = _read_pretty_json(root, FREEZE_PATH, "Amendment 0005 freeze")
    if set(freeze) != {
        "schema_version",
        "amendment_id",
        "status",
        "frozen_at_utc",
        "implementation_commit",
        "implementation_files",
        "review_path",
        "review_sha256",
        "draft_sha256",
        "parent_authorities",
        "activation_journal",
    }:
        raise Amendment0005Error("Amendment 0005 freeze has invalid keys")
    implementation_commit = freeze["implementation_commit"]
    if (
        freeze["schema_version"] != 1
        or freeze["amendment_id"] != AMENDMENT_ID
        or freeze["status"] != "frozen"
        or freeze["review_path"] != REVIEW_PATH
        or type(implementation_commit) is not str
        or _COMMIT.fullmatch(implementation_commit) is None
        or freeze["parent_authorities"] != PARENT_AUTHORITIES
    ):
        raise Amendment0005Error("Amendment 0005 freeze identity is invalid")
    if type(freeze["frozen_at_utc"]) is not str or not freeze["frozen_at_utc"].endswith("Z"):
        raise Amendment0005Error("Amendment 0005 freeze timestamp must be canonical UTC text")
    try:
        frozen_at = datetime.fromisoformat(str(freeze["frozen_at_utc"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise Amendment0005Error("Amendment 0005 freeze timestamp is invalid") from exc
    if frozen_at.tzinfo is None or frozen_at.utcoffset() != UTC.utcoffset(frozen_at):
        raise Amendment0005Error("Amendment 0005 freeze timestamp must be UTC")
    _draft, draft_bytes = _load_draft(root)
    if freeze["draft_sha256"] != sha256_bytes(draft_bytes):
        raise Amendment0005Error("Amendment 0005 freeze binds a different draft")
    hashes = _implementation_hashes(root)
    if freeze["implementation_files"] != hashes:
        raise Amendment0005Error("Amendment 0005 implementation differs from freeze")
    for relative in IMPLEMENTATION_FILE_PATHS:
        if git_bytes(
            root,
            "show",
            f"{implementation_commit}:{relative}",
            label=f"frozen Amendment 0005 file {relative}",
        ) != _regular_bytes(root / relative, f"Amendment 0005 file {relative}"):
            raise Amendment0005Error("Amendment 0005 implementation commit differs")
    review, review_bytes = _read_pretty_json(root, REVIEW_PATH, "Amendment 0005 review")
    if (
        set(review)
        != {
            "schema_version",
            "amendment_id",
            "decision",
            "implementation_commit",
            "implementation_files",
            "parent_authorities",
        }
        or freeze["review_sha256"] != sha256_bytes(review_bytes)
        or review.get("schema_version") != 1
        or review.get("amendment_id") != AMENDMENT_ID
        or review.get("decision") != "approve"
        or review.get("implementation_commit") != implementation_commit
        or review.get("implementation_files") != hashes
        or review.get("parent_authorities") != PARENT_AUTHORITIES
    ):
        raise Amendment0005Error("Amendment 0005 review/freeze binding differs")
    review_commit = unique_first_add_commit(root, REVIEW_PATH, review_bytes)
    activation = freeze["activation_journal"]
    if (
        not isinstance(activation, Mapping)
        or set(activation) != {"path", "head_sha256", "record_count"}
        or activation["path"] != TOP40_V2_LAYOUT.organizer_journal_path
        or type(activation["head_sha256"]) is not str
        or _SHA.fullmatch(activation["head_sha256"]) is None
        or type(activation["record_count"]) is not int
        or activation["record_count"] < 1
    ):
        raise Amendment0005Error("Amendment 0005 activation journal is invalid")
    freeze_commit = unique_first_add_commit(root, FREEZE_PATH, payload)
    _require_strict_ancestor(root, implementation_commit, review_commit, "implementation/review")
    _require_strict_ancestor(root, review_commit, freeze_commit, "review/freeze")
    for relative in (*IMPLEMENTATION_FILE_PATHS, REVIEW_PATH):
        expected = (
            review_bytes
            if relative == REVIEW_PATH
            else _regular_bytes(root / relative, f"Amendment 0005 freeze-tree file {relative}")
        )
        if (
            git_bytes(
                root,
                "show",
                f"{freeze_commit}:{relative}",
                label=f"Amendment 0005 freeze-tree file {relative}",
            )
            != expected
        ):
            raise Amendment0005Error(
                "Amendment 0005 freeze tree lacks reviewed implementation bytes"
            )
    journal_bytes = git_bytes(
        root,
        "show",
        f"{freeze_commit}:{TOP40_V2_LAYOUT.organizer_journal_path}",
        label="Amendment 0005 activation journal at freeze",
    )
    journal_lines = journal_bytes.splitlines()
    if len(journal_lines) != activation["record_count"]:
        raise Amendment0005Error("activation journal count differs at freeze commit")
    try:
        records = [
            strict_json_object(line, "Amendment 0005 activation journal record")
            for line in journal_lines
        ]
        last_record = records[-1]
    except IndexError as exc:
        raise Amendment0005Error("activation journal is empty at freeze commit") from exc
    if any(
        record.get("sequence") != sequence
        or type(record.get("record_sha256")) is not str
        or _SHA.fullmatch(record["record_sha256"]) is None
        for sequence, record in enumerate(records, start=1)
    ) or (
        last_record.get("record_sha256") != activation["head_sha256"]
        or last_record.get("sequence") != activation["record_count"]
    ):
        raise Amendment0005Error("activation journal head differs at freeze commit")
    return freeze, payload, freeze_commit


def amendment_status(root: str | Path) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    verify_parent_authorities(root_path)
    _draft, draft_bytes = _load_draft(root_path)
    freeze_path = root_path / FREEZE_PATH
    if not freeze_path.exists() and not freeze_path.is_symlink():
        return {
            "amendment_id": AMENDMENT_ID,
            "status": "draft",
            "execution_enabled": False,
            "draft_sha256": sha256_bytes(draft_bytes),
            "eligible_teams": list(ELIGIBLE_TEAMS),
            "stage": "development",
        }
    freeze, freeze_bytes, freeze_commit = _load_freeze(root_path)
    return {
        "amendment_id": AMENDMENT_ID,
        "status": "frozen",
        "execution_enabled": True,
        "freeze_sha256": sha256_bytes(freeze_bytes),
        "freeze_commit": freeze_commit,
        "activation_journal": freeze["activation_journal"],
        "eligible_teams": list(ELIGIBLE_TEAMS),
        "stage": "development",
    }


@contextlib.contextmanager
def _execution_lock(root: Path) -> Iterator[None]:
    path = git_path(root, "top40-v2-amendment-0005/development-score-diagnostics.lock")
    ensure_owner_directory(path.parent)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0), 0o600)
    info = os.fstat(descriptor)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        os.close(descriptor)
        raise Amendment0005Error("Amendment 0005 execution lock is unsafe")
    with os.fdopen(descriptor, "a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def _require_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise Amendment0005Error(f"{label} ancestry is invalid")


def _require_strict_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    if ancestor == descendant:
        raise Amendment0005Error(f"{label} must be strictly ordered")
    _require_ancestor(root, ancestor, descendant, label)


def _current_state_and_journal_locked(
    root: Path, config: LoadedV2Config
) -> tuple[Mapping[str, Any], bytes, Any]:
    state, state_bytes, _chain, _audit = amendment_v2._read_amended_state_locked(root, config)
    journal = amendment_v2._load_bound_research_journal(root, config, state)
    if (
        state["phase"] != "research"
        or state["administrative_hold"]["active"] is not False
        or any(
            state[field] is not None
            for field in (
                "qualification_lock",
                "finalist_cohort_lock",
                "final_oos_lock",
                "winner_freeze",
            )
        )
    ):
        raise Amendment0005Error(
            "development score diagnostics are impossible after research/private/final sealing"
        )
    return state, state_bytes, journal


def _current_state_and_journal(
    root: Path, config: LoadedV2Config
) -> tuple[Mapping[str, Any], bytes, Any]:
    with amendment_v2._state_lock(root):
        return _current_state_and_journal_locked(root, config)


def _candidate_paths(team_id: str, candidate_id: str) -> Mapping[str, str]:
    if team_id not in ELIGIBLE_TEAMS:
        raise Amendment0005Error("Amendment 0005 permits only opt-in Team04 through Team10")
    if _IDENTIFIER.fullmatch(candidate_id) is None:
        raise Amendment0005Error("candidate_id is unsafe")
    report = TOP40_V2_LAYOUT.report_root(team_id)
    evidence_dir = f"{report}/development-score-diagnostics/{candidate_id}"
    return {
        "registration_input_path": f"{report}/registration-inputs/{candidate_id}.json",
        "score_manifest_path": (
            f"{TOP40_V2_LAYOUT.team_root(team_id)}/score-adapters/{candidate_id}.json"
        ),
        "semantic_coupling_review_path": (
            f"{TOP40_V2_LAYOUT.team_root(team_id)}/score-adapters/"
            f"{candidate_id}.semantic-coupling-review.json"
        ),
        "development_target_path": f"{report}/development-runs/{candidate_id}/targets.parquet",
        "runner_record_path": f"{report}/qualification-attempts/{candidate_id}.runner-record.json",
        "reservation_path": f"{report}/score-diagnostic-reservations/{candidate_id}.json",
        "result_path": f"{evidence_dir}/{TERMINAL_RESULT_NAME}",
        "evidence_dir": evidence_dir,
    }


def _candidate_authority(
    root: Path,
    config: LoadedV2Config,
    team_id: str,
    candidate_id: str,
    *,
    state_lock_held: bool = False,
) -> tuple[dict[str, Any], Mapping[str, str]]:
    verify_parent_authorities(root)
    freeze, freeze_bytes, freeze_commit = _load_freeze(root)
    paths = _candidate_paths(team_id, candidate_id)
    if state_lock_held:
        state, state_bytes, journal = _current_state_and_journal_locked(root, config)
    else:
        state, state_bytes, journal = _current_state_and_journal(root, config)
    if state["teams"][team_id]["status"] != "researching":
        raise Amendment0005Error("candidate team is not in active research")
    activation = freeze["activation_journal"]
    activation_count = int(activation["record_count"])
    if (
        len(journal.records) < activation_count
        or journal.records[activation_count - 1]["record_sha256"] != activation["head_sha256"]
    ):
        raise Amendment0005Error("current journal does not extend the activation journal")
    accounting = journal.teams[team_id]
    registration = accounting.registrations.get(candidate_id)
    result = accounting.results.get(candidate_id)
    registration_sha = accounting.registration_sha256.get(candidate_id)
    if (
        not isinstance(registration, Mapping)
        or not isinstance(result, Mapping)
        or result.get("status") != "completed"
        or type(registration_sha) is not str
    ):
        raise Amendment0005Error("candidate lacks one completed development registration/result")
    matching_records = [
        record
        for record in journal.records
        if record["event_type"] == "trial_registration"
        and record["payload"]["team_id"] == team_id
        and record["payload"]["candidate_id"] == candidate_id
    ]
    if len(matching_records) != 1 or matching_records[0]["sequence"] <= activation_count:
        raise Amendment0005Error("preactivation registrations are outside Amendment 0005")
    parameters = registration.get("parameters")
    opt_in = parameters.get(OPT_IN_PARAMETER) if isinstance(parameters, Mapping) else None
    if not isinstance(opt_in, Mapping) or set(opt_in) != {
        "schema_version",
        "adapter_id",
        "manifest_sha256",
    }:
        raise Amendment0005Error("candidate did not preregister the exact score-adapter opt-in")
    if (
        opt_in["schema_version"] != 1
        or opt_in["adapter_id"] != ADAPTER_ID
        or type(opt_in["manifest_sha256"]) is not str
        or _SHA.fullmatch(opt_in["manifest_sha256"]) is None
    ):
        raise Amendment0005Error("candidate score-adapter opt-in is invalid")

    _reg_relative, _reg_path, reg_bytes, _reg_stat = read_repo_file(
        root,
        paths["registration_input_path"],
        "candidate registration input",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    registration_raw = strict_json_object(reg_bytes, "candidate registration input")
    if sha256_bytes(build_trial_registration(**dict(registration_raw))) != registration_sha:
        raise Amendment0005Error("registration input differs from organizer journal")
    registration_commit = unique_first_add_commit(root, paths["registration_input_path"], reg_bytes)
    _require_strict_ancestor(root, freeze_commit, registration_commit, "prospective registration")

    _manifest_relative, _manifest_path, manifest_bytes, _manifest_stat = read_repo_file(
        root,
        paths["score_manifest_path"],
        "candidate score-adapter manifest",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    manifest_sha = sha256_bytes(manifest_bytes)
    if manifest_sha != opt_in["manifest_sha256"]:
        raise Amendment0005Error("preregistered manifest SHA-256 differs")
    manifest = development_score_diagnostics_v5.parse_score_adapter_manifest(
        manifest_bytes,
        expected_team_id=team_id,
        expected_family_id=str(registration["family_id"]),
        expected_candidate_id=candidate_id,
    )
    manifest_commit = unique_first_add_commit(root, paths["score_manifest_path"], manifest_bytes)
    _require_ancestor(root, manifest_commit, registration_commit, "manifest/registration")
    if (
        git_bytes(
            root,
            "show",
            f"{registration_commit}:{paths['score_manifest_path']}",
            label="score manifest in registration tree",
        )
        != manifest_bytes
    ):
        raise Amendment0005Error("registration tree lacks exact preregistered manifest")

    semantic_relative = paths["semantic_coupling_review_path"]
    _review_relative, _review_path, semantic_review_bytes, _review_stat = read_repo_file(
        root,
        semantic_relative,
        "candidate semantic-coupling static review",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    semantic_review_sha = sha256_bytes(semantic_review_bytes)
    if semantic_review_sha != manifest.semantic_coupling_review_sha256:
        raise Amendment0005Error("semantic-coupling review differs from the preregistered manifest")
    development_score_diagnostics_v5.parse_semantic_coupling_review(
        semantic_review_bytes,
        expected_team_id=team_id,
        expected_family_id=str(registration["family_id"]),
        expected_candidate_id=candidate_id,
        expected_strategy_sha256=str(registration["strategy_sha256"]),
    )
    semantic_review_commit = unique_first_add_commit(root, semantic_relative, semantic_review_bytes)
    _require_ancestor(root, semantic_review_commit, manifest_commit, "semantic review/manifest")
    for commit, label in (
        (manifest_commit, "manifest tree"),
        (registration_commit, "registration tree"),
    ):
        if (
            git_bytes(
                root,
                "show",
                f"{commit}:{semantic_relative}",
                label=f"semantic-coupling review in {label}",
            )
            != semantic_review_bytes
        ):
            raise Amendment0005Error(f"{label} lacks the exact semantic-coupling static review")

    artifacts = result.get("artifact_hashes")
    if not isinstance(artifacts, Mapping):
        raise Amendment0005Error("completed result lacks artifact hashes")
    hashes: dict[str, str] = {}
    for key in ("development_target_path", "runner_record_path"):
        relative = paths[key]
        digest = artifacts.get(relative)
        if type(digest) is not str or _SHA.fullmatch(digest) is None:
            raise Amendment0005Error("completed result lacks canonical development artifacts")
        _normalized, _path, payload, _stat = read_repo_file(
            root, relative, f"completed candidate artifact {relative}", require_single_link=True
        )
        if sha256_bytes(payload) != digest:
            raise Amendment0005Error("completed development artifact hash differs")
        hashes[key.replace("_path", "_sha256")] = digest
    _runner_relative, _runner_path, runner_bytes, _runner_stat = read_repo_file(
        root,
        paths["runner_record_path"],
        "completed development runner record",
        maximum_bytes=4 * 1024 * 1024,
        require_single_link=True,
    )
    runner = strict_json_object(runner_bytes, "completed development runner record")
    snapshot_path = str(config.raw["paths"]["shared_snapshot_manifest"])
    _snap_relative, _snap_path, snapshot_bytes, _snap_stat = read_repo_file(
        root, snapshot_path, "shared development snapshot manifest", require_single_link=True
    )
    snapshot_sha = sha256_bytes(snapshot_bytes)
    if (
        runner.get("stage") != "development"
        or runner.get("team_id") != team_id
        or runner.get("data_manifest_sha256") != snapshot_sha
        or runner.get("config_sha256") != config.sha256
    ):
        raise Amendment0005Error("runner record is not exact completed development authority")
    result_records = [
        record
        for record in journal.records
        if record["event_type"] == "trial_result"
        and record["payload"]["team_id"] == team_id
        and record["payload"]["candidate_id"] == candidate_id
    ]
    if len(result_records) != 1:
        raise Amendment0005Error("candidate has no unique trial-result record")
    if (
        result_records[0]["sequence"] <= matching_records[0]["sequence"]
        or result_records[0]["sequence"] <= activation_count
    ):
        raise Amendment0005Error(
            "trial result is not strictly postactivation registration evidence"
        )
    authority = {
        "team_id": team_id,
        "family_id": registration["family_id"],
        "candidate_id": candidate_id,
        "candidate_registration_sha256": registration_sha,
        "registration_input_path": paths["registration_input_path"],
        "registration_commit": registration_commit,
        "registration_event_record_sha256": matching_records[0]["record_sha256"],
        "registration_event_sequence": matching_records[0]["sequence"],
        "trial_result_record_sha256": result_records[0]["record_sha256"],
        "trial_result_event_sequence": result_records[0]["sequence"],
        "strategy_sha256": registration["strategy_sha256"],
        "risk_policy_sha256": registration["risk_config_sha256"],
        "source_bundle_sha256": registration["source_bundle_sha256"],
        "candidate_seed": registration["seed"],
        "config_sha256": config.sha256,
        "score_manifest_path": paths["score_manifest_path"],
        "score_manifest_sha256": manifest_sha,
        "score_manifest_commit": manifest_commit,
        "semantic_coupling_review_path": semantic_relative,
        "semantic_coupling_review_sha256": semantic_review_sha,
        "semantic_coupling_review_commit": semantic_review_commit,
        "snapshot_manifest_path": snapshot_path,
        "snapshot_manifest_sha256": snapshot_sha,
        "development_target_path": paths["development_target_path"],
        "development_target_sha256": hashes["development_target_sha256"],
        "runner_record_path": paths["runner_record_path"],
        "runner_record_sha256": hashes["runner_record_sha256"],
        "amendment_freeze_sha256": sha256_bytes(freeze_bytes),
        "amendment_freeze_commit": freeze_commit,
        "research_state_sha256": sha256_bytes(state_bytes),
        "research_journal_record_count": len(journal.records),
        "research_journal_head_sha256": journal.records[-1]["record_sha256"],
    }
    return authority, paths


def _reservation_core(authority: Mapping[str, Any], reserved_at_utc: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event_type": "development_score_diagnostic_reserved",
        "diagnostic_kind": development_score_diagnostics_v5.DIAGNOSTIC_KIND,
        "diagnostic_id": f"development-score-{authority['team_id']}-{authority['candidate_id']}",
        "stage": "development",
        **dict(authority),
        "reserved_at_utc": reserved_at_utc,
        "non_material": True,
        "charges_team_trial_budget": False,
    }


def _ensure_safe_directory_chain(root: Path, directory: Path) -> None:
    development_score_diagnostics_v5._safe_directory_chain(root, directory)


def _load_existing_transaction(
    root: Path,
    paths: Mapping[str, str],
    reservation: Mapping[str, Any],
) -> Mapping[str, Any]:
    evidence_dir = root / paths["evidence_dir"]
    _ensure_safe_directory_chain(root, evidence_dir)
    info = os.lstat(evidence_dir)
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise Amendment0005Error("declared-score transaction directory is unsafe")
    entries = {entry.name for entry in os.scandir(evidence_dir)}
    if TERMINAL_RESULT_NAME not in entries:
        raise Amendment0005Error("declared-score transaction is incomplete")
    result, result_bytes = _read_pretty_json(
        root, paths["result_path"], "declared-score terminal result"
    )
    expected_keys = {
        "schema_version",
        "event_type",
        "diagnostic_kind",
        "diagnostic_id",
        "stage",
        "team_id",
        "candidate_id",
        "reservation_sha256",
        "authority_sha256",
        "semantic_coupling_review_sha256",
        "status",
        "failure_reason",
        "organizer_cpu_hours",
        "organizer_wall_clock_hours",
        "artifact_hashes",
        "statistics",
        "declared_score_diagnostic_only",
        "non_material",
        "charges_team_trial_budget",
        "automatic_qualification_gate",
        "result_sha256",
    }
    if set(result) != expected_keys:
        raise Amendment0005Error("declared-score terminal result has invalid keys")
    core = {key: value for key, value in result.items() if key != "result_sha256"}
    if (
        result["result_sha256"] != sha256_bytes(pretty_json_bytes(core))
        or result["schema_version"] != 1
        or result["event_type"] != "development_score_diagnostic_recorded"
        or result["diagnostic_kind"] != development_score_diagnostics_v5.DIAGNOSTIC_KIND
        or result["diagnostic_id"] != reservation["diagnostic_id"]
        or result["stage"] != "development"
        or result["team_id"] != reservation["team_id"]
        or result["candidate_id"] != reservation["candidate_id"]
        or result["reservation_sha256"] != reservation["reservation_sha256"]
        or result["authority_sha256"]
        != sha256_bytes(pretty_json_bytes({key: reservation[key] for key in _AUTHORITY_KEYS}))
        or result["semantic_coupling_review_sha256"]
        != reservation["semantic_coupling_review_sha256"]
        or result["declared_score_diagnostic_only"] is not True
        or result["non_material"] is not True
        or result["charges_team_trial_budget"] is not False
        or result["automatic_qualification_gate"] is not False
    ):
        raise Amendment0005Error("declared-score terminal result binding differs")
    status_value = result["status"]
    artifacts = result["artifact_hashes"]
    if status_value not in {"completed", "failed", "interrupted"} or not isinstance(
        artifacts, Mapping
    ):
        raise Amendment0005Error("declared-score terminal status is invalid")
    for field in ("organizer_cpu_hours", "organizer_wall_clock_hours"):
        value = result[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise Amendment0005Error("declared-score resource accounting is invalid")
    expected_artifacts = (
        set(development_score_diagnostics_v5.REQUIRED_ARTIFACT_NAMES)
        if status_value == "completed"
        else set()
    )
    if entries != expected_artifacts | {TERMINAL_RESULT_NAME}:
        raise Amendment0005Error("declared-score transaction contains missing or extra files")
    expected_hash_keys = {f"{paths['evidence_dir']}/{name}" for name in expected_artifacts}
    if set(artifacts) != expected_hash_keys:
        raise Amendment0005Error("declared-score artifact hash set differs")
    for name in expected_artifacts:
        payload = _regular_bytes(
            evidence_dir / name,
            f"declared-score transaction artifact {name}",
            maximum_bytes=128 * 1024 * 1024,
        )
        if artifacts[f"{paths['evidence_dir']}/{name}"] != sha256_bytes(payload):
            raise Amendment0005Error("declared-score transaction artifact hash differs")
    if status_value == "completed":
        summary = strict_json_object(
            _regular_bytes(evidence_dir / "diagnostic-summary.json", "diagnostic summary"),
            "diagnostic summary",
        )
        if (
            summary.get("reservation_sha256") != reservation["reservation_sha256"]
            or summary.get("semantic_coupling_review_sha256")
            != reservation["semantic_coupling_review_sha256"]
            or result["statistics"] != summary.get("statistics")
            or result["failure_reason"] is not None
        ):
            raise Amendment0005Error("declared-score completed summary differs")
    elif result["statistics"] is not None or type(result["failure_reason"]) is not str:
        raise Amendment0005Error("declared-score failed terminal result differs")
    if pretty_json_bytes(result) != result_bytes:
        raise Amendment0005Error("declared-score terminal result encoding differs")
    return result


def reserve_development_score_diagnostic(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    config = load_config(root_path / TOP40_V2_LAYOUT.config_path)
    with _execution_lock(root_path):
        authority, paths = _candidate_authority(root_path, config, team_id, candidate_id)
        for key in ("reservation_path", "result_path", "evidence_dir"):
            path = root_path / paths[key]
            if path.exists() or path.is_symlink():
                raise Amendment0005Error("development score diagnostic is one-shot")
            if key != "evidence_dir":
                require_no_git_history(root_path, paths[key])
        now = clock()
        if now.tzinfo is None:
            raise Amendment0005Error("reservation clock must be timezone-aware")
        timestamp = now.astimezone(UTC).isoformat().replace("+00:00", "Z")
        core = _reservation_core(authority, timestamp)
        reservation = {**core, "reservation_sha256": sha256_bytes(pretty_json_bytes(core))}
        reservation_bytes = pretty_json_bytes(reservation)
        path = root_path / paths["reservation_path"]
        with amendment_v2._state_lock(root_path):
            final_config = load_config(root_path / TOP40_V2_LAYOUT.config_path)
            if final_config.sha256 != config.sha256:
                raise Amendment0005Error("config changed while staging reservation")
            final_authority, _final_paths = _candidate_authority(
                root_path,
                final_config,
                team_id,
                candidate_id,
                state_lock_held=True,
            )
            if final_authority != authority:
                raise Amendment0005Error("research authority changed while staging reservation")
            if path.exists() or path.is_symlink():
                raise Amendment0005Error("development score diagnostic is one-shot")
            _ensure_safe_directory_chain(root_path, path.parent)
            atomic_write_bytes(path, reservation_bytes, mode=0o644)
        return reservation


def _load_reservation(root: Path, relative: str) -> tuple[Mapping[str, Any], bytes]:
    reservation, payload = _read_pretty_json(root, relative, "development score reservation")
    if set(reservation) != _AUTHORITY_KEYS | {
        "schema_version",
        "event_type",
        "diagnostic_kind",
        "diagnostic_id",
        "stage",
        "reserved_at_utc",
        "non_material",
        "charges_team_trial_budget",
        "reservation_sha256",
    }:
        raise Amendment0005Error("development score reservation has invalid keys")
    if (
        reservation.get("schema_version") != 1
        or reservation.get("event_type") != "development_score_diagnostic_reserved"
        or reservation.get("diagnostic_kind") != development_score_diagnostics_v5.DIAGNOSTIC_KIND
        or reservation.get("stage") != "development"
        or reservation.get("non_material") is not True
    ):
        raise Amendment0005Error("development score reservation identity is invalid")
    if reservation.get("charges_team_trial_budget") is not False:
        raise Amendment0005Error("development score reservation would charge team budget")
    for key in _AUTHORITY_KEYS | {"reservation_sha256"}:
        if key.endswith("_sha256") and (
            type(reservation[key]) is not str or _SHA.fullmatch(reservation[key]) is None
        ):
            raise Amendment0005Error("development score reservation has invalid SHA-256")
    for key in (
        "registration_commit",
        "score_manifest_commit",
        "semantic_coupling_review_commit",
        "amendment_freeze_commit",
    ):
        if type(reservation[key]) is not str or _COMMIT.fullmatch(reservation[key]) is None:
            raise Amendment0005Error("development score reservation has invalid commit binding")
    for key in (
        "candidate_seed",
        "registration_event_sequence",
        "trial_result_event_sequence",
        "research_journal_record_count",
    ):
        if type(reservation[key]) is not int or (key != "candidate_seed" and reservation[key] < 1):
            raise Amendment0005Error("development score reservation has invalid integer binding")
    supplied = reservation.get("reservation_sha256")
    core = {key: value for key, value in reservation.items() if key != "reservation_sha256"}
    if type(supplied) is not str or supplied != sha256_bytes(pretty_json_bytes(core)):
        raise Amendment0005Error("development score reservation hash is invalid")
    return reservation, payload


def _request(
    reservation: Mapping[str, Any],
) -> development_score_diagnostics_v5.DevelopmentScoreDiagnosticRequest:
    return development_score_diagnostics_v5.DevelopmentScoreDiagnosticRequest(
        diagnostic_id=str(reservation["diagnostic_id"]),
        team_id=str(reservation["team_id"]),
        family_id=str(reservation["family_id"]),
        candidate_id=str(reservation["candidate_id"]),
        registration_input_path=str(reservation["registration_input_path"]),
        registration_sha256=str(reservation["candidate_registration_sha256"]),
        registration_commit=str(reservation["registration_commit"]),
        strategy_sha256=str(reservation["strategy_sha256"]),
        risk_policy_sha256=str(reservation["risk_policy_sha256"]),
        source_bundle_sha256=str(reservation["source_bundle_sha256"]),
        candidate_seed=reservation["candidate_seed"],
        config_sha256=str(reservation["config_sha256"]),
        score_manifest_path=str(reservation["score_manifest_path"]),
        score_manifest_sha256=str(reservation["score_manifest_sha256"]),
        score_manifest_commit=str(reservation["score_manifest_commit"]),
        semantic_coupling_review_path=str(reservation["semantic_coupling_review_path"]),
        semantic_coupling_review_sha256=str(reservation["semantic_coupling_review_sha256"]),
        semantic_coupling_review_commit=str(reservation["semantic_coupling_review_commit"]),
        snapshot_manifest_path=str(reservation["snapshot_manifest_path"]),
        snapshot_manifest_sha256=str(reservation["snapshot_manifest_sha256"]),
        development_target_path=str(reservation["development_target_path"]),
        development_target_sha256=str(reservation["development_target_sha256"]),
        runner_record_path=str(reservation["runner_record_path"]),
        runner_record_sha256=str(reservation["runner_record_sha256"]),
        reservation_sha256=str(reservation["reservation_sha256"]),
    )


def run_development_score_diagnostic(
    root: str | Path,
    team_id: str,
    candidate_id: str,
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    config = load_config(root_path / TOP40_V2_LAYOUT.config_path)
    with _execution_lock(root_path):
        paths = _candidate_paths(team_id, candidate_id)
        reservation, reservation_bytes = _load_reservation(root_path, paths["reservation_path"])
        if (
            reservation["team_id"] != team_id
            or reservation["candidate_id"] != candidate_id
            or reservation["diagnostic_id"] != f"development-score-{team_id}-{candidate_id}"
        ):
            raise Amendment0005Error("reservation identity differs from derived candidate path")
        unique_first_add_commit(root_path, paths["reservation_path"], reservation_bytes)
        evidence_dir = root_path / paths["evidence_dir"]
        if evidence_dir.exists() or evidence_dir.is_symlink():
            return _load_existing_transaction(root_path, paths, reservation)
        authority, paths = _candidate_authority(root_path, config, team_id, candidate_id)
        expected = _reservation_core(authority, str(reservation["reserved_at_utc"]))
        observed = {key: value for key, value in reservation.items() if key != "reservation_sha256"}
        if observed != expected:
            raise Amendment0005Error("reservation differs from current candidate authority")
        require_no_git_history(root_path, paths["result_path"])
        verify_parent_authorities(root_path)
        request = _request(reservation)
        outcome = _A2_RUN(
            root=root_path,
            runner_call=lambda: (
                development_score_diagnostics_v5.run_reserved_development_score_diagnostic(
                    root=root_path,
                    request=request,
                )
            ),
        )
        verify_parent_authorities(root_path)
        if set(outcome) != {
            "status",
            "failure_reason",
            "organizer_cpu_hours",
            "organizer_wall_clock_hours",
            "staged_artifacts",
        }:
            raise Amendment0005Error("declared-score runner returned invalid keys")
        for field in ("organizer_cpu_hours", "organizer_wall_clock_hours"):
            value = outcome[field]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise Amendment0005Error("declared-score runner accounting is invalid")
        completed = outcome["status"] == "completed"
        stage, artifacts = development_score_diagnostics_v5.validate_staged_artifacts(
            root_path, request, outcome["staged_artifacts"], completed=completed
        )
        try:
            summary: Mapping[str, Any] | None = None
            if completed:
                summary = strict_json_object(
                    _regular_bytes(stage / "diagnostic-summary.json", "staged diagnostic summary"),
                    "staged diagnostic summary",
                )
                if (
                    summary.get("reservation_sha256") != reservation["reservation_sha256"]
                    or summary.get("semantic_coupling_review_sha256")
                    != reservation["semantic_coupling_review_sha256"]
                ):
                    raise Amendment0005Error("staged diagnostic summary binding differs")
            elif outcome["status"] not in {"failed", "interrupted"}:
                raise Amendment0005Error("declared-score runner status is invalid")
            authority_sha = sha256_bytes(pretty_json_bytes(authority))
            core = {
                "schema_version": 1,
                "event_type": "development_score_diagnostic_recorded",
                "diagnostic_kind": development_score_diagnostics_v5.DIAGNOSTIC_KIND,
                "diagnostic_id": reservation["diagnostic_id"],
                "stage": "development",
                "team_id": team_id,
                "candidate_id": candidate_id,
                "reservation_sha256": reservation["reservation_sha256"],
                "authority_sha256": authority_sha,
                "semantic_coupling_review_sha256": reservation["semantic_coupling_review_sha256"],
                "status": outcome["status"],
                "failure_reason": outcome["failure_reason"],
                "organizer_cpu_hours": outcome["organizer_cpu_hours"],
                "organizer_wall_clock_hours": outcome["organizer_wall_clock_hours"],
                "artifact_hashes": dict(artifacts),
                "statistics": None if summary is None else summary["statistics"],
                "declared_score_diagnostic_only": True,
                "non_material": True,
                "charges_team_trial_budget": False,
                "automatic_qualification_gate": False,
            }
            result = {**core, "result_sha256": sha256_bytes(pretty_json_bytes(core))}
            atomic_write_bytes(stage / TERMINAL_RESULT_NAME, pretty_json_bytes(result), mode=0o600)
            with amendment_v2._state_lock(root_path):
                final_config = load_config(root_path / TOP40_V2_LAYOUT.config_path)
                if final_config.sha256 != config.sha256:
                    raise Amendment0005Error("config changed during declared-score replay")
                final_authority, _final_paths = _candidate_authority(
                    root_path,
                    final_config,
                    team_id,
                    candidate_id,
                    state_lock_held=True,
                )
                if final_authority != authority:
                    raise Amendment0005Error(
                        "research phase/state changed during declared-score replay"
                    )
                if evidence_dir.exists() or evidence_dir.is_symlink():
                    existing = _load_existing_transaction(root_path, paths, reservation)
                    return existing
                _ensure_safe_directory_chain(root_path, evidence_dir.parent)
                os.rename(stage, evidence_dir)
                development_score_diagnostics_v5.fsync_directory(evidence_dir.parent)
                return _load_existing_transaction(root_path, paths, reservation)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
