"""Contract, configuration, and state invariants for Top-40 V2."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
import tomllib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT, TournamentLayout

TEAM_IDS = TOP40_V2_LAYOUT.team_ids
RUN_PHASES = (
    "phase0_pending",
    "research",
    "qualification_closed",
    "finalist_cohort_frozen",
    "oos_revealed",
    "objective_locked",
    "critic_locked",
    "dq_confirmed",
    "user_locked",
    "paper_frozen",
    "no_qualified_model",
)
TEAM_STATUSES = (
    "pending_phase0",
    "researching",
    "qualifier_candidate_frozen",
    "qualified",
    "dnf",
    "finalist_frozen",
    "canonical_running",
    "canonical_complete",
)
TERMINAL_QUALIFICATION_STATUSES = frozenset({"qualified", "dnf"})
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclasses.dataclass(frozen=True)
class LoadedV2Config:
    path: Path
    sha256: str
    raw: Mapping[str, Any]

    @property
    def qualification_thresholds(self) -> dict[str, object]:
        qualification = self.raw["qualification"]
        return {
            "development": qualification["development"],
            "private": qualification["private"],
            "regimes": qualification["regimes"],
            "sleeves": qualification["sleeves"],
            "stability": qualification["stability"],
            "walk_forward_folds": self.raw["statistics"]["walk_forward_folds"],
        }


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _fraction(value: Any, label: str) -> float:
    result = _finite(value, label)
    if not 0 <= result <= 1:
        raise ValueError(f"{label} must be in [0,1]")
    return result


def _utc_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} must be timezone-aware UTC")
    return parsed


def _date(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc


def _require_keys(raw: Mapping[str, Any], keys: Sequence[str], label: str) -> None:
    missing = [key for key in keys if key not in raw]
    if missing:
        raise ValueError(f"{label} missing keys: {missing}")


def _validate_config(raw: Mapping[str, Any], layout: TournamentLayout) -> None:
    _require_keys(
        raw,
        (
            "schema_version",
            "name",
            "branch",
            "teams",
            "paths",
            "data",
            "splits",
            "execution",
            "risk_policy",
            "regimes",
            "statistics",
            "qualification",
            "research_budget",
            "scoring",
            "paper_eligibility",
        ),
        "config",
    )
    if raw["schema_version"] != 2 or raw["name"] != layout.name or raw["branch"] != layout.branch:
        raise ValueError("config identity differs from the Top-40 V2 layout")
    if tuple(raw["teams"]) != layout.team_ids:
        raise ValueError("config teams must contain team-01 through team-10 in order")

    paths = raw["paths"]
    if not isinstance(paths, Mapping):
        raise ValueError("config.paths must be a table")
    if (
        _safe_relative(paths.get("tournament_root"), "paths.tournament_root")
        != layout.tournament_root
    ):
        raise ValueError("paths.tournament_root differs from the V2 layout")
    if _safe_relative(paths.get("reports_root"), "paths.reports_root") != layout.reports_root:
        raise ValueError("paths.reports_root differs from the V2 layout")
    _safe_relative(paths.get("shared_snapshot_manifest"), "paths.shared_snapshot_manifest")
    _safe_relative(paths.get("snapshot_dir"), "paths.snapshot_dir")

    data = raw["data"]
    if not isinstance(data, Mapping) or (
        data.get("source") != "binance-public-usdm"
        or data.get("transaction_interval") != "8h"
        or data.get("hard_end_exclusive") != "2026-07-01"
        or data.get("snapshot_binding") != "shared-immutable-v1-by-sha256"
    ):
        raise ValueError("config.data differs from the V2 common-data contract")

    splits = raw["splits"]
    if not isinstance(splits, Mapping):
        raise ValueError("config.splits must be a table")
    development_start = _date(splits.get("visible_development_start"), "development start")
    development_end = _date(
        splits.get("visible_development_end_inclusive"), "development end"
    )
    private_start = _date(splits.get("private_qualifier_start"), "private start")
    private_end = _date(
        splits.get("private_qualifier_end_inclusive"), "private end"
    )
    oos_start = _date(splits.get("final_oos_start"), "final OOS start")
    oos_end = _date(splits.get("final_oos_end_inclusive"), "final OOS end")
    one_day = (private_start - development_end).days
    next_private = (oos_start - private_end).days
    hard_end = _date(data["hard_end_exclusive"], "hard end")
    if (
        development_start >= development_end
        or one_day != 1
        or private_start >= private_end
        or next_private != 1
        or oos_start >= oos_end
        or (hard_end - oos_end).days != 1
    ):
        raise ValueError("development, private, and OOS windows must be ordered and contiguous")
    if (
        splits.get("private_qualifier_feedback") != "pass-fail-only"
        or splits.get("team_oos_visibility_before_finalist_lock") is not False
    ):
        raise ValueError("private/OOS visibility controls cannot be weakened")

    execution = raw["execution"]
    if not isinstance(execution, Mapping) or (
        execution.get("base_interval") != "8h"
        or _finite(execution.get("double_cost_multiplier"), "double_cost_multiplier") != 2
        or execution.get("funding_at_rebalance_order")
        != "funding-on-carried-position-then-risk-then-rebalance"
    ):
        raise ValueError("config.execution differs from the V2 execution contract")
    for name in (
        "initial_equity_usdt",
        "taker_fee_bps_per_side",
        "slippage_bps_per_side",
        "max_gross_exposure",
        "max_abs_net_exposure",
        "max_symbol_exposure",
        "max_bar_participation",
    ):
        if _finite(execution.get(name), f"execution.{name}") < 0:
            raise ValueError(f"execution.{name} cannot be negative")
    if _integer(execution.get("annualization_days"), "annualization_days", minimum=1) != 365:
        raise ValueError("annualization_days must be 365")

    risk = raw["risk_policy"]
    if not isinstance(risk, Mapping) or (
        risk.get("schema_version") != 1
        or risk.get("organizer_owned_execution") is not True
        or risk.get("intrabar_stop_fills_allowed") is not False
        or risk.get("close_confirmed_stop_execution") != "next-open"
        or risk.get("risk_actions_pay_normal_costs") is not True
        or risk.get("risk_actions_share_participation_capacity") is not True
    ):
        raise ValueError("config.risk_policy weakens the V2 risk contract")

    statistics = raw["statistics"]
    if not isinstance(statistics, Mapping):
        raise ValueError("config.statistics must be a table")
    _integer(statistics.get("bootstrap_samples"), "bootstrap_samples", minimum=100)
    _integer(statistics.get("bootstrap_block_days"), "bootstrap_block_days", minimum=1)
    _integer(statistics.get("walk_forward_folds"), "walk_forward_folds", minimum=2)

    qualification = raw["qualification"]
    if not isinstance(qualification, Mapping):
        raise ValueError("config.qualification must be a table")
    for section in ("development", "private", "regimes", "sleeves", "stability"):
        if not isinstance(qualification.get(section), Mapping):
            raise ValueError(f"qualification.{section} must be a table")
    development = qualification["development"]
    if (
        _finite(development.get("minimum_net_sharpe"), "minimum_net_sharpe") < 0.75
        or _finite(development.get("minimum_calmar"), "minimum_calmar") < 0.4
        or _fraction(development.get("maximum_drawdown"), "maximum_drawdown") > 0.30
        or _finite(development.get("minimum_double_cost_sharpe"), "minimum_double_cost_sharpe")
        < 0.35
        or _fraction(
            development.get("minimum_trial_adjusted_probability_positive"),
            "minimum_trial_adjusted_probability_positive",
        )
        < 0.90
    ):
        raise ValueError("development qualification thresholds cannot be weaker than the charter")
    private = qualification["private"]
    if (
        _finite(private.get("minimum_net_sharpe"), "private minimum_net_sharpe") < 0.50
        or _fraction(private.get("maximum_drawdown"), "private maximum_drawdown") > 0.30
        or _integer(private.get("maximum_attempts"), "private maximum_attempts", minimum=1) != 1
    ):
        raise ValueError("private qualification thresholds cannot be weaker than the charter")

    research = raw["research_budget"]
    if not isinstance(research, Mapping):
        raise ValueError("config.research_budget must be a table")
    if (
        _integer(
            research.get("maximum_material_configurations_per_team"),
            "maximum_material_configurations_per_team",
            minimum=1,
        )
        > 80
        or _integer(
            research.get("maximum_mechanism_pivots_per_team"),
            "maximum_mechanism_pivots_per_team",
        )
        > 2
        or _integer(
            research.get("maximum_private_qualifier_attempts_per_team"),
            "maximum_private_qualifier_attempts_per_team",
            minimum=1,
        )
        != 1
        or _integer(
            research.get("maximum_final_oos_views_per_team"),
            "maximum_final_oos_views_per_team",
        )
        != 0
    ):
        raise ValueError("research budgets exceed the V2 charter")
    _utc_timestamp(research.get("deadline_utc"), "research deadline")

    scoring = raw["scoring"]
    if not isinstance(scoring, Mapping):
        raise ValueError("config.scoring must be a table")
    weights = tuple(
        _finite(scoring.get(name), f"scoring.{name}")
        for name in ("automatic_weight", "critic_weight", "user_weight")
    )
    if not math.isclose(sum(weights), 100) or weights != (70.0, 15.0, 15.0):
        raise ValueError("final score weights must remain 70 automatic + 15 Critic + 15 user")
    automatic_parts = (
        _finite(scoring.get("automatic_absolute_points"), "automatic_absolute_points"),
        _finite(scoring.get("automatic_relative_points"), "automatic_relative_points"),
    )
    if automatic_parts != (50.0, 20.0) or not math.isclose(sum(automatic_parts), 70):
        raise ValueError("automatic score must remain 50 absolute + 20 relative")
    if (
        scoring.get("require_is_qualification") is not True
        or scoring.get("dnf_is_not_a_submission") is not True
        or scoring.get("zero_finalists_result") != "no-qualified-model"
    ):
        raise ValueError("scoring cannot bypass qualification or fabricate DNF submissions")


def load_config(
    path: str | Path = TOP40_V2_LAYOUT.config_path,
    *,
    layout: TournamentLayout = TOP40_V2_LAYOUT,
) -> LoadedV2Config:
    config_path = Path(path)
    try:
        payload = config_path.read_bytes()
        raw = tomllib.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid Top-40 V2 config: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Top-40 V2 config root must be a table")
    _validate_config(raw, layout)
    return LoadedV2Config(config_path, hashlib.sha256(payload).hexdigest(), raw)


def canonical_team_artifacts(team_id: str) -> dict[str, str]:
    team_root = TOP40_V2_LAYOUT.team_root(team_id)
    report_root = TOP40_V2_LAYOUT.report_root(team_id)
    return {
        "family_ledger": f"{team_root}/families.jsonl",
        "trial_ledger": f"{team_root}/experiments.jsonl",
        "research_brief": f"{team_root}/research_brief.md",
        "provenance": f"{team_root}/provenance.md",
        "feature_lineage": f"{team_root}/feature_lineage.json",
        "ablations": f"{team_root}/ablations.json",
        "strategy_source": f"{team_root}/strategy.py",
        "frozen_config": f"{team_root}/frozen_config.json",
        "risk_policy": f"{team_root}/risk_policy.json",
        "parameter_neighborhood": f"{team_root}/parameter_neighborhood.json",
        "development_evidence": f"{report_root}/development_qualification_evidence.json",
        "private_sealed_record": f"{TOP40_V2_LAYOUT.tournament_root}/private/{team_id}.json",
        "final_submission": f"{team_root}/submission.json",
    }


def new_run_state(
    config: LoadedV2Config, *, created_at_utc: str | None = None
) -> dict[str, object]:
    created = created_at_utc or datetime.now(UTC).isoformat()
    _utc_timestamp(created, "created_at_utc")
    teams = {
        team_id: {
            "status": "pending_phase0",
            "active_family_id": None,
            "family_count": 0,
            "pivot_count": 0,
            "trial_count": 0,
            "development_assessment": None,
            "qualifier_candidate": None,
            "private_attempts": 0,
            "private_result": None,
            "dnf": None,
            "finalist_freeze": None,
            "canonical_result": None,
        }
        for team_id in TEAM_IDS
    }
    return {
        "schema_version": 2,
        "tournament": TOP40_V2_LAYOUT.name,
        "phase": "phase0_pending",
        "created_at_utc": created,
        "config_path": TOP40_V2_LAYOUT.config_path,
        "config_sha256": config.sha256,
        "phase0": None,
        "qualification_lock": None,
        "finalist_cohort_lock": None,
        "objective_lock": None,
        "critic_lock": None,
        "critic_confirmation_lock": None,
        "user_ballot_lock": None,
        "winner_freeze": None,
        "teams": teams,
    }


def validate_run_state(state: Mapping[str, Any], config: LoadedV2Config) -> None:
    required = {
        "schema_version",
        "tournament",
        "phase",
        "created_at_utc",
        "config_path",
        "config_sha256",
        "phase0",
        "qualification_lock",
        "finalist_cohort_lock",
        "objective_lock",
        "critic_lock",
        "critic_confirmation_lock",
        "user_ballot_lock",
        "winner_freeze",
        "teams",
    }
    if set(state) != required or state.get("schema_version") != 2:
        raise ValueError("run state has an invalid schema")
    if state.get("tournament") != TOP40_V2_LAYOUT.name or state.get("phase") not in RUN_PHASES:
        raise ValueError("run state identity or phase is invalid")
    _utc_timestamp(state.get("created_at_utc"), "run_state.created_at_utc")
    if (
        state.get("config_path") != TOP40_V2_LAYOUT.config_path
        or state.get("config_sha256") != config.sha256
    ):
        raise ValueError("run state is not bound to the current V2 config")
    teams = state.get("teams")
    if not isinstance(teams, Mapping) or set(teams) != set(TEAM_IDS):
        raise ValueError("run state must contain all ten teams exactly once")
    expected_team_keys = {
        "status",
        "active_family_id",
        "family_count",
        "pivot_count",
        "trial_count",
        "development_assessment",
        "qualifier_candidate",
        "private_attempts",
        "private_result",
        "dnf",
        "finalist_freeze",
        "canonical_result",
    }
    research = config.raw["research_budget"]
    for team_id in TEAM_IDS:
        team = teams[team_id]
        if not isinstance(team, Mapping) or set(team) != expected_team_keys:
            raise ValueError(f"run state team record is malformed for {team_id}")
        if team["status"] not in TEAM_STATUSES:
            raise ValueError(f"invalid team status for {team_id}")
        family_count = _integer(team["family_count"], f"{team_id}.family_count")
        pivots = _integer(team["pivot_count"], f"{team_id}.pivot_count")
        trials = _integer(team["trial_count"], f"{team_id}.trial_count")
        private_attempts = _integer(team["private_attempts"], f"{team_id}.private_attempts")
        if family_count > pivots + 1 or pivots > research["maximum_mechanism_pivots_per_team"]:
            raise ValueError(f"family/pivot accounting exceeds the budget for {team_id}")
        if trials > research["maximum_material_configurations_per_team"]:
            raise ValueError(f"trial accounting exceeds the budget for {team_id}")
        if private_attempts > research["maximum_private_qualifier_attempts_per_team"]:
            raise ValueError(f"private qualifier attempts exceed the budget for {team_id}")
        if team["status"] == "dnf" and not isinstance(team["dnf"], Mapping):
            raise ValueError(f"DNF team {team_id} requires a DNF record")
        if team["status"] == "qualified" and not isinstance(team["private_result"], Mapping):
            raise ValueError(f"qualified team {team_id} requires a private result")


def read_run_state(root: str | Path, config: LoadedV2Config) -> dict[str, Any]:
    path = Path(root) / TOP40_V2_LAYOUT.state_path
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Top-40 V2 run state: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Top-40 V2 run state root must be a JSON object")
    validate_run_state(raw, config)
    return raw


def all_teams_terminal_for_qualification(state: Mapping[str, Any]) -> bool:
    teams = state.get("teams")
    return isinstance(teams, Mapping) and all(
        isinstance(teams.get(team_id), Mapping)
        and teams[team_id].get("status") in TERMINAL_QUALIFICATION_STATUSES
        for team_id in TEAM_IDS
    )


def finalist_team_ids(state: Mapping[str, Any]) -> tuple[str, ...]:
    teams = state.get("teams")
    if not isinstance(teams, Mapping):
        raise ValueError("run state teams are missing")
    return tuple(
        team_id
        for team_id in TEAM_IDS
        if isinstance(teams.get(team_id), Mapping) and teams[team_id].get("status") == "qualified"
    )


def sha256_json(payload: object) -> str:
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()
