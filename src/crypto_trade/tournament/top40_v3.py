"""Fail-closed configuration and run-state contract for Top-40 V3.

This module is a fresh V3 authority.  It deliberately depends only on the generation-neutral
layout type and the V3 layout; no earlier tournament state or lifecycle code is imported.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament.layout import TournamentLayout
from crypto_trade.tournament.layout_v3 import TOP40_V3_LAYOUT

TEAM_IDS = TOP40_V3_LAYOUT.team_ids
RUN_PHASES = (
    "policy_defined",
    "lab_open",
    "ordinary_probes_closed",
    "comeback_lab",
    "nominations_locked",
    "public_ranked",
    "private_complete",
    "final_revealed",
    "closed",
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_CONFIG_SEMANTIC_SHA256 = "7356bf37e61a20088ca593db990421418ce097bffc0296041c36c0c20568ace4"
_ROBUSTNESS_FORMULA = (
    "25*C((net_sharpe-0.75)/0.75) + 15*C(annualized_return/0.30) + "
    "15*C((0.30-max_drawdown)/0.20) + "
    "15*C((double_cost_sharpe-0.35)/0.65) + "
    "15*C((positive_quarter_fraction-0.50)/0.25) + "
    "10*(positive_regime_count/4) + "
    "5*C((worst_regime_sharpe+0.75)/1.50)"
)
_A6_AUTHORITY = {
    "policy_id": "top40-v2-pure-crypto-usdt-perpetual-v1",
    "policy_sha256": "2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350",
    "audit_module_path": "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "audit_module_sha256": "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192",
    "audit_dependency_path": "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "audit_dependency_sha256": "e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab",
    "audit_report_sha256": "b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b",
    "data_manifest_path": "tournament/top40/data_manifest.json",
    "data_manifest_sha256": "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3",
    "membership_sha256": "f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14",
    "contract_metadata_sha256": "0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243",
    "exchange_info_sha256": "aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64",
    "required_before_and_after_every_result_command": True,
    "expected_contract_metadata_symbols": 667,
    "expected_distinct_membership_symbols": 321,
    "expected_membership_rows": 12866,
    "expected_violations": 0,
    "expected_audit_status": "passed",
}
_EXACT_WINDOWS = {
    "train": {
        "start": "2020-02-03T00:00:00Z",
        "end_exclusive": "2022-07-01T00:00:00Z",
        "raw_data_visible_to_teams": True,
        "feedback": "full-standardized-metric-packet",
    },
    "validation": {
        "start": "2022-07-01T00:00:00Z",
        "end_exclusive": "2023-07-01T00:00:00Z",
        "raw_data_visible_to_teams": False,
        "feedback": "fixed-aggregate-packet-only",
    },
    "private": {
        "start": "2023-07-01T00:00:00Z",
        "end_exclusive": "2024-07-01T00:00:00Z",
        "raw_data_visible_to_teams": False,
        "feedback": "single-gate-decision-after-public-selection",
    },
    "final_oos": {
        "start": "2024-07-01T00:00:00Z",
        "end_exclusive": "2026-07-01T00:00:00Z",
        "raw_data_visible_to_teams": False,
        "feedback": "one-simultaneous-final-reveal",
    },
}
_WRITE_PATHS = {
    "tournament_root": "tournament/top40-v3",
    "reports_root": "reports-top40-v3",
    "team_root": "tournament/top40-v3/teams",
    "lab_reports_root": "reports-top40-v3/labs",
    "organizer_lab_journal": "tournament/top40-v3/organizer-lab-journal.jsonl",
    "validation_probe_journal": "tournament/top40-v3/validation-probe-journal.jsonl",
    "nomination_registry": "tournament/top40-v3/nomination-registry.jsonl",
    "stage_transition_journal": "tournament/top40-v3/stage-transitions.jsonl",
    "result_root": "reports-top40-v3/results",
}
_READ_PATHS = {
    "snapshot_dir": "data/top40/snapshot-v1",
    "shared_snapshot_manifest": "tournament/top40/data_manifest.json",
}
_GLOBAL_LOCK_NAMES = (
    "infrastructure",
    "schedule",
    "metric_schema",
    "diagnostic_rubric",
    "nomination_registry",
    "public_qualification",
    "private_qualification",
    "final_reveal",
)
_JOURNAL_BINDING_FIELDS = [
    "schema_version",
    "event_sequence",
    "previous_sha256",
    "record_sha256",
    "event_type",
    "team_id",
    "run_sequence",
    "run_id",
    "candidate_id",
    "parent_candidate_id",
    "purpose",
    "accepted_at_utc",
    "source_bundle_sha256",
    "source_archive_path",
    "source_archive_sha256",
    "strategy_sha256",
    "dependency_lock_sha256",
    "config_sha256",
    "risk_policy_sha256",
    "data_authority_sha256",
    "evaluator_sha256",
    "seed",
    "material_parameters",
    "train_window",
    "cost_model",
    "output_path",
    "cumulative_material_trial_count",
    "request_sha256",
    "completed_at_utc",
    "cpu_seconds",
    "wall_seconds",
    "gate_vector",
    "metric_packet_sha256",
    "artifact_hashes",
    "failure_reason",
]


@dataclasses.dataclass(frozen=True)
class LoadedV3Config:
    """A parsed configuration that passed the exact V3 policy contract."""

    path: Path
    sha256: str
    raw: Mapping[str, Any]

    @property
    def opening_probe_limit(self) -> int:
        return int(self.raw["validation"]["maximum_opening_probes_per_team"])

    @property
    def comeback_probe_limit(self) -> int:
        return int(self.raw["validation"]["maximum_comeback_probes_per_eligible_team"])

    @property
    def total_probe_limit(self) -> int:
        return int(self.raw["validation"]["maximum_total_probes_when_comeback_triggers"])


def _at(raw: Mapping[str, Any], path: Sequence[str], label: str) -> Any:
    value: Any = raw
    for part in path:
        if not isinstance(value, Mapping) or part not in value:
            raise ValueError(f"V3 config {label} is missing")
        value = value[part]
    return value


def _expect(raw: Mapping[str, Any], path: Sequence[str], expected: Any, label: str) -> None:
    value = _at(raw, path, label)
    if type(value) is not type(expected) or value != expected:  # exact bool/int distinction
        raise ValueError(f"V3 config {label} differs from the frozen contract")


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


def _semantic_sha256(raw: Mapping[str, Any]) -> str:
    try:
        payload = json.dumps(
            raw,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("V3 config is not canonically serializable") from exc
    return hashlib.sha256(payload).hexdigest()


def _validate_config(
    raw: Mapping[str, Any], layout: TournamentLayout = TOP40_V3_LAYOUT
) -> None:
    """Validate every current V3 policy byte semantically and important rules explicitly."""

    if layout != TOP40_V3_LAYOUT:
        raise ValueError("V3 config requires the canonical V3 layout")
    if not isinstance(raw, Mapping):
        raise ValueError("V3 config root must be a table")

    _expect(raw, ("schema_version",), 3, "schema version")
    _expect(raw, ("name",), layout.name, "identity")
    _expect(raw, ("policy_status",), "active", "policy status")
    _expect(raw, ("charter_path",), "TOURNAMENT-CHARTER-TOP40-V3.md", "charter path")
    _expect(raw, ("teams",), list(layout.team_ids), "ten-team field")

    _expect(raw, ("lifecycle", "v2_is_immutable"), True, "immutable predecessor rule")
    _expect(raw, ("lifecycle", "inherit_v2_state"), False, "fresh-state rule")
    _expect(raw, ("lifecycle", "reuse_snapshot_read_only"), True, "snapshot read-only rule")

    paths = _at(raw, ("paths",), "path layout")
    if not isinstance(paths, Mapping) or set(paths) != set(_WRITE_PATHS) | set(_READ_PATHS):
        raise ValueError("V3 config path layout has missing or unexpected paths")
    for key, expected in _WRITE_PATHS.items():
        _expect(raw, ("paths", key), expected, f"fresh V3 write path {key}")
        value = _safe_relative(paths[key], f"paths.{key}")
        if not value.startswith(("tournament/top40-v3", "reports-top40-v3")):
            raise ValueError(f"paths.{key} is not isolated in the V3 write namespace")
    for key, expected in _READ_PATHS.items():
        _expect(raw, ("paths", key), expected, f"shared snapshot read path {key}")
        _safe_relative(paths[key], f"paths.{key}")

    _expect(raw, ("data", "warmup_start"), "2020-01-01T00:00:00Z", "warm-up boundary")
    _expect(raw, ("data", "hard_end_exclusive"), "2026-07-01T00:00:00Z", "hard data end")
    _expect(raw, ("splits",), _EXACT_WINDOWS, "four exact windows")

    _expect(raw, ("universe", "size"), 40, "universe size")
    _expect(raw, ("universe", "membership_path"), _READ_PATHS["snapshot_dir"] + "/membership.parquet", "membership authority")
    _expect(raw, ("universe", "eligibility_mode"), "fail-closed-a6-native-crypto", "native-crypto mode")
    _expect(raw, ("universe", "allowed_economic_exposure"), "native-crypto-only", "economic exposure")
    _expect(raw, ("universe", "unknown_classification_is_ineligible"), True, "unknown classification policy")
    _expect(raw, ("universe", "a6_authority"), _A6_AUTHORITY, "A6 pure-crypto authority")

    _expect(
        raw,
        ("execution",),
        {
            "base_interval": "8h",
            "initial_equity_usdt": 100000.0,
            "taker_fee_bps_per_side": 5.0,
            "slippage_bps_per_side": 2.5,
            "max_gross_exposure": 1.0,
            "max_abs_net_exposure": 0.25,
            "max_symbol_exposure": 0.10,
            "max_bar_participation": 0.001,
            "double_cost_multiplier": 2.0,
            "annualization_days": 365,
            "fill_timing": "next-executable-open",
            "funding_at_rebalance_order": "funding-on-carried-position-then-rebalance",
        },
        "execution contract",
    )

    _expect(raw, ("labs", "strategy_seed"), 20260718, "strategy seed")
    _expect(raw, ("labs", "append_before_metric_release"), True, "lab pre-disclosure logging")
    _expect(raw, ("labs", "material_trial_counter_never_resets"), True, "lab multiplicity")
    _expect(raw, ("labs", "full_standardized_metric_packet"), True, "full train metrics")
    _expect(raw, ("labs", "log_success_failure_and_abort"), True, "train terminal accounting")
    _expect(
        raw,
        ("labs", "exact_train_replay_mode"),
        "not-activated-every-invocation-counts-as-material-trial",
        "train replay activation boundary",
    )
    _expect(
        raw,
        ("labs", "required_journal_bindings", "fields"),
        _JOURNAL_BINDING_FIELDS,
        "exact train journal bindings",
    )

    _expect(raw, ("validation", "maximum_opening_probes_per_team"), 3, "opening probe limit")
    _expect(raw, ("validation", "maximum_comeback_probes_per_eligible_team"), 2, "comeback probe limit")
    _expect(raw, ("validation", "maximum_total_probes_when_comeback_triggers"), 5, "total probe limit")
    _expect(raw, ("validation", "counter_is_organizer_owned_append_only"), True, "probe ledger")
    _expect(raw, ("validation", "counter_consumed_on_accepted_request"), True, "probe consumption")
    _expect(raw, ("validation", "fixed_aggregate_packet_only"), True, "sealed validation feedback")

    for window in ("train", "validation"):
        for metric in ("net_sharpe", "annualized_return", "double_cost_sharpe"):
            _expect(
                raw,
                ("candidate", "readiness", f"minimum_{window}_{metric}_exclusive"),
                0.0,
                f"positive {window} {metric}",
            )
    _expect(raw, ("candidate", "maximum_formal_nominees_per_team"), 1, "nomination limit")
    _expect(raw, ("candidate", "nominee_must_exactly_match_a_probed_candidate"), True, "nominee probe binding")
    _expect(raw, ("candidate", "nominee_must_pass_public_core"), True, "nominee public-core eligibility")
    _expect(raw, ("candidate", "post_lock_changes_allowed"), False, "nominee immutability")

    _expect(
        raw,
        ("qualification", "public", "core"),
        {
            "minimum_net_sharpe_inclusive": 0.75,
            "minimum_annualized_return_exclusive": 0.0,
            "maximum_drawdown_inclusive": 0.30,
            "minimum_double_cost_sharpe_inclusive": 0.35,
            "minimum_positive_quarter_fraction_inclusive": 0.50,
            "minimum_executed_trades_inclusive": 1000,
            "minimum_positive_regime_count_inclusive": 2,
            "regime_count": 4,
            "minimum_worst_regime_sharpe_inclusive": -0.75,
            "missing_or_nonfinite_is_failure": True,
        },
        "public performance floors",
    )
    _expect(raw, ("ranking", "robustness", "formula"), _ROBUSTNESS_FORMULA, "robustness formula")
    _expect(raw, ("ranking", "robustness", "advance_count"), 4, "top-four advancement")
    _expect(raw, ("ranking", "robustness", "advance_all_when_fewer"), True, "short-field advancement")
    _expect(raw, ("ranking", "robustness", "score_is_additional_veto"), False, "robustness non-veto")

    for field in ("veto", "affects_public_core", "affects_robustness_rank", "affects_private_gate"):
        _expect(raw, ("diagnostics", field), False, f"diagnostic non-veto {field}")
    _expect(raw, ("diagnostics", "computed_scored_and_disclosed"), True, "diagnostic disclosure")

    _expect(raw, ("comeback", "grants_additional_validation_probes"), 2, "comeback probe grant")
    _expect(raw, ("comeback", "maximum_rounds"), 1, "comeback round limit")
    _expect(raw, ("comeback", "lowers_or_changes_floors_costs_windows_gates_or_ranking"), False, "comeback fixed standards")

    private = _at(raw, ("qualification", "private"), "private gate")
    if not isinstance(private, Mapping):
        raise ValueError("V3 config private gate must be a table")
    for metric in ("net_sharpe", "annualized_return", "double_cost_sharpe"):
        _expect(raw, ("qualification", "private", f"minimum_{metric}_exclusive"), 0.0, f"positive private {metric}")
    _expect(raw, ("qualification", "private", "maximum_drawdown_inclusive"), 0.35, "private drawdown")
    _expect(raw, ("qualification", "private", "annualized_return_is_veto"), True, "private annual-return veto")
    _expect(raw, ("qualification", "private", "per_regime_metrics_are_veto"), False, "private regime non-veto")

    _expect(raw, ("final_oos", "observations_per_finalist"), 1, "single final observation")
    _expect(raw, ("final_oos", "simultaneous_complete_release"), True, "simultaneous final reveal")
    _expect(raw, ("final_oos", "interim_disclosure_allowed"), False, "final nondisclosure")
    _expect(raw, ("final_oos", "repair_or_replacement_allowed"), False, "final immutability")

    if _semantic_sha256(raw) != _CONFIG_SEMANTIC_SHA256:
        raise ValueError("V3 config differs from the complete frozen semantic contract")


def _path_has_suffix(path: Path, relative: str) -> bool:
    expected = PurePosixPath(relative).parts
    actual = PurePosixPath(path.as_posix()).parts
    return len(actual) >= len(expected) and actual[-len(expected) :] == expected


def load_config(
    path: str | Path = TOP40_V3_LAYOUT.config_path,
    *,
    layout: TournamentLayout = TOP40_V3_LAYOUT,
) -> LoadedV3Config:
    """Load only a canonical-layout V3 config and bind its exact bytes."""

    if layout != TOP40_V3_LAYOUT:
        raise ValueError("V3 config requires the canonical V3 layout")
    config_path = Path(path)
    if config_path.is_dir():
        config_path = config_path / layout.config_path
    if not _path_has_suffix(config_path, layout.config_path):
        raise ValueError("V3 config path is outside the canonical V3 layout")
    try:
        payload = config_path.read_bytes()
        raw = tomllib.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid Top-40 V3 config: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Top-40 V3 config root must be a table")
    _validate_config(raw, layout)
    return LoadedV3Config(config_path, hashlib.sha256(payload).hexdigest(), raw)


def _utc_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be timezone-aware UTC")
    return parsed


def _counter(value: Any, label: str, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} exceeds its V3 limit of {maximum}")
    return value


def _validate_hash_lock(value: Any, label: str, *, include_path: bool) -> None:
    required = {"sha256", "locked_at_utc"} | ({"path"} if include_path else {"candidate_id"})
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError(f"{label} is malformed")
    if not isinstance(value["sha256"], str) or _SHA256.fullmatch(value["sha256"]) is None:
        raise ValueError(f"{label}.sha256 is invalid")
    _utc_timestamp(value["locked_at_utc"], f"{label}.locked_at_utc")
    if include_path:
        path = _safe_relative(value["path"], f"{label}.path")
        if not path.startswith(("tournament/top40-v3", "reports-top40-v3")):
            raise ValueError(f"{label}.path is outside the V3 namespace")
    elif not isinstance(value["candidate_id"], str) or not value["candidate_id"]:
        raise ValueError(f"{label}.candidate_id is invalid")


def new_run_state(
    config: LoadedV3Config, *, created_at_utc: str | None = None
) -> dict[str, object]:
    """Create a clean V3 state with no imported counters, locks, or nominees."""

    if not isinstance(config, LoadedV3Config):
        raise ValueError("config must be a validated LoadedV3Config")
    created = created_at_utc or datetime.now(UTC).isoformat()
    _utc_timestamp(created, "created_at_utc")
    teams = {
        team_id: {
            "lab_run_count": 0,
            "material_trial_count": 0,
            "opening_probe_count": 0,
            "comeback_probe_count": 0,
            "validation_probe_count": 0,
            "probe_locks": [],
            "nomination_count": 0,
            "nominee_lock": None,
            "private_run_count": 0,
            "final_oos_observation_count": 0,
        }
        for team_id in TEAM_IDS
    }
    return {
        "schema_version": 1,
        "tournament": TOP40_V3_LAYOUT.name,
        "phase": "policy_defined",
        "created_at_utc": created,
        "config_path": TOP40_V3_LAYOUT.config_path,
        "config_sha256": config.sha256,
        "locks": {name: None for name in _GLOBAL_LOCK_NAMES},
        "teams": teams,
    }


def validate_run_state(state: Mapping[str, Any], config: LoadedV3Config) -> None:
    """Validate the minimal append-only counters and locks of a V3 run state."""

    if not isinstance(config, LoadedV3Config):
        raise ValueError("config must be a validated LoadedV3Config")
    required = {
        "schema_version",
        "tournament",
        "phase",
        "created_at_utc",
        "config_path",
        "config_sha256",
        "locks",
        "teams",
    }
    if not isinstance(state, Mapping) or set(state) != required or state.get("schema_version") != 1:
        raise ValueError("V3 run state has an invalid schema")
    if state.get("tournament") != TOP40_V3_LAYOUT.name or state.get("phase") not in RUN_PHASES:
        raise ValueError("V3 run state identity or phase is invalid")
    _utc_timestamp(state.get("created_at_utc"), "run_state.created_at_utc")
    if state.get("config_path") != TOP40_V3_LAYOUT.config_path or state.get("config_sha256") != config.sha256:
        raise ValueError("V3 run state is not bound to the current V3 config")

    locks = state.get("locks")
    # JSON objects are unordered, and the canonical state writer sorts their keys.  Require the
    # exact lock-name set while allowing the decoded mapping's iteration order to differ.
    if not isinstance(locks, Mapping) or set(locks) != set(_GLOBAL_LOCK_NAMES):
        raise ValueError("V3 run state has noncanonical global locks")
    for name in _GLOBAL_LOCK_NAMES:
        if locks[name] is not None:
            _validate_hash_lock(locks[name], f"locks.{name}", include_path=True)

    teams = state.get("teams")
    if not isinstance(teams, Mapping) or tuple(teams) != TEAM_IDS:
        raise ValueError("V3 run state must contain exactly the ten canonical teams")
    team_fields = {
        "lab_run_count",
        "material_trial_count",
        "opening_probe_count",
        "comeback_probe_count",
        "validation_probe_count",
        "probe_locks",
        "nomination_count",
        "nominee_lock",
        "private_run_count",
        "final_oos_observation_count",
    }
    for team_id in TEAM_IDS:
        team = teams[team_id]
        if not isinstance(team, Mapping) or set(team) != team_fields:
            raise ValueError(f"V3 run state {team_id} has an invalid schema")
        lab_runs = _counter(team["lab_run_count"], f"{team_id}.lab_run_count")
        trials = _counter(team["material_trial_count"], f"{team_id}.material_trial_count")
        if trials > lab_runs:
            raise ValueError(f"{team_id}.material_trial_count exceeds logged lab runs")
        opening = _counter(team["opening_probe_count"], f"{team_id}.opening_probe_count", config.opening_probe_limit)
        comeback = _counter(team["comeback_probe_count"], f"{team_id}.comeback_probe_count", config.comeback_probe_limit)
        total = _counter(team["validation_probe_count"], f"{team_id}.validation_probe_count", config.total_probe_limit)
        if total != opening + comeback:
            raise ValueError(f"{team_id}.validation_probe_count does not equal opening plus comeback probes")

        probe_locks = team["probe_locks"]
        if not isinstance(probe_locks, list) or len(probe_locks) != total:
            raise ValueError(f"{team_id}.probe_locks do not bind every consumed probe")
        opening_locks = 0
        comeback_locks = 0
        seen: set[tuple[str, str]] = set()
        for index, lock in enumerate(probe_locks):
            if not isinstance(lock, Mapping) or set(lock) != {"candidate_id", "sha256", "locked_at_utc", "round"}:
                raise ValueError(f"{team_id}.probe_locks[{index}] is malformed")
            core_lock = {key: lock[key] for key in ("candidate_id", "sha256", "locked_at_utc")}
            _validate_hash_lock(core_lock, f"{team_id}.probe_locks[{index}]", include_path=False)
            if lock["round"] == "opening":
                opening_locks += 1
            elif lock["round"] == "comeback":
                comeback_locks += 1
            else:
                raise ValueError(f"{team_id}.probe_locks[{index}].round is invalid")
            identity = (str(lock["candidate_id"]), str(lock["sha256"]))
            if identity in seen:
                raise ValueError(f"{team_id}.probe_locks contains a duplicate consumed probe")
            seen.add(identity)
        if (opening_locks, comeback_locks) != (opening, comeback):
            raise ValueError(f"{team_id}.probe lock rounds disagree with probe counters")

        nominations = _counter(team["nomination_count"], f"{team_id}.nomination_count", 1)
        nominee_lock = team["nominee_lock"]
        if nominations == 0 and nominee_lock is not None:
            raise ValueError(f"{team_id}.nominee_lock exists without a nomination")
        if nominations == 1:
            _validate_hash_lock(nominee_lock, f"{team_id}.nominee_lock", include_path=False)
            nominee_identity = (str(nominee_lock["candidate_id"]), str(nominee_lock["sha256"]))
            if nominee_identity not in seen:
                raise ValueError(f"{team_id}.nominee_lock is not bound to a consumed probe")

        private_runs = _counter(team["private_run_count"], f"{team_id}.private_run_count", 1)
        final_observations = _counter(
            team["final_oos_observation_count"], f"{team_id}.final_oos_observation_count", 1
        )
        if private_runs > nominations:
            raise ValueError(f"{team_id} has a private run without a formal nominee")
        if final_observations > private_runs:
            raise ValueError(f"{team_id} has a final observation without a private run")


__all__ = [
    "LoadedV3Config",
    "RUN_PHASES",
    "TEAM_IDS",
    "load_config",
    "new_run_state",
    "validate_run_state",
]
