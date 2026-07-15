"""Pure, hash-bound finals assembly for the Top-40 V2 tournament.

This module deliberately performs no file I/O and no canonical evaluator run.  Callers provide
the exact bytes already bound by organizer locks.  The module verifies those bindings, constructs
the only accepted :class:`~crypto_trade.tournament.scoring_v2.FinalistPerformance` inputs, locks
the 70-point objective result once, and later combines that lock with exact finalist ballots.

DNF teams are an explicit partition of the ten-team field.  They never acquire fabricated final
OOS records, jury points, or totals.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal

from crypto_trade.tournament import scoring_v2
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.qualification import assess_development, assess_private
from crypto_trade.tournament.scoring_v2 import (
    ABSOLUTE_COMPONENT_WEIGHTS,
    RELATIVE_COMPONENT_WEIGHTS,
    FinalistPerformance,
    RoleStabilityObservations,
    WindowPerformance,
)
from crypto_trade.tournament.top40_v2 import TEAM_IDS, LoadedV2Config

_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REGIMES = ("bull", "bear", "chop", "stress")
_RUNNER_KEYS = {
    "stage",
    "team_id",
    "entrypoint",
    "seeds",
    "data_manifest_sha256",
    "config_sha256",
    "strategy_sha256",
    "risk_policy_sha256",
    "source_bundle_sha256",
    "scored_window",
    "double_cost_sharpe",
    "regime_sharpe",
    "confidence_intervals",
    "artifacts",
}
_WINDOW_METRIC_KEYS = {
    "net_sharpe",
    "net_sortino",
    "calmar",
    "annualized_return",
    "max_drawdown",
    "positive_quarter_fraction",
}
_ARTIFACT_FILENAMES = {
    "targets": "targets.parquet",
    "events": "events.parquet",
    "positions": "positions.parquet",
    "evaluator_returns": "bar_returns.csv",
    "double_cost_evaluator_returns": "double_cost_bar_returns.csv",
    "daily_returns": "daily_returns.csv",
    "double_cost_daily_returns": "double_cost_daily_returns.csv",
    "trades": "trades.csv",
}
_OBJECTIVE_STATUS = Literal["scored", "no-qualified-model"]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_json_sha256(payload: object) -> str:
    return _sha256_bytes(_canonical_json_bytes(payload))


def _exact_object(raw: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != expected:
        missing = sorted(expected - set(raw)) if isinstance(raw, Mapping) else sorted(expected)
        extra = sorted(set(raw) - expected) if isinstance(raw, Mapping) else []
        raise ValueError(f"{label} has invalid keys; missing={missing}, extra={extra}")
    return raw


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")
    return value


def _same_float(left: object, right: object, label: str) -> None:
    left_value = _finite(left, f"{label} evidence")
    right_value = _finite(right, f"{label} runner")
    if not math.isclose(left_value, right_value, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"{label} differs between qualification evidence and runner record")


def _strict_json_object(payload: bytes, label: str) -> Mapping[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"{label} contains non-finite JSON number {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        decoded = payload.decode("utf-8")
        raw = json.loads(
            decoded,
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} root must be a JSON object")
    return raw


@dataclasses.dataclass(frozen=True)
class HashBoundJson:
    """Exact JSON bytes plus the SHA-256 supplied by an immutable organizer binding."""

    payload: bytes
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise ValueError("hash-bound JSON payload must be bytes")
        _sha256(self.sha256, "hash-bound JSON sha256")
        if _sha256_bytes(self.payload) != self.sha256:
            raise ValueError("hash-bound JSON bytes differ from the expected SHA-256")

    def object(self, label: str) -> Mapping[str, Any]:
        return _strict_json_object(self.payload, label)


@dataclasses.dataclass(frozen=True)
class FinalistSourceBinding:
    """Identity and exact organizer-record hashes committed for one finalist."""

    team_id: str
    candidate_id: str
    config_sha256: str
    strategy_sha256: str
    risk_policy_sha256: str
    source_bundle_sha256: str
    data_manifest_sha256: str
    development_evidence_sha256: str
    private_sealed_record_sha256: str
    private_runner_record_sha256: str
    final_oos_runner_record_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.team_id, str) or _TEAM_ID.fullmatch(self.team_id) is None:
            raise ValueError("team_id must be team-01 through team-10")
        if (
            not isinstance(self.candidate_id, str)
            or not self.candidate_id
            or len(self.candidate_id) > 128
        ):
            raise ValueError("candidate_id must be a non-empty string of at most 128 characters")
        for field in (
            "config_sha256",
            "strategy_sha256",
            "risk_policy_sha256",
            "source_bundle_sha256",
            "data_manifest_sha256",
            "development_evidence_sha256",
            "private_sealed_record_sha256",
            "private_runner_record_sha256",
            "final_oos_runner_record_sha256",
        ):
            _sha256(getattr(self, field), field)

    def to_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def _performance_dict(performance: FinalistPerformance) -> dict[str, object]:
    return dataclasses.asdict(performance)


@dataclasses.dataclass(frozen=True)
class BoundFinalistPerformance:
    """Scoring input whose complete source chain has passed finals validation."""

    binding: FinalistSourceBinding
    performance: FinalistPerformance

    def __post_init__(self) -> None:
        if not isinstance(self.binding, FinalistSourceBinding):
            raise ValueError("binding must be FinalistSourceBinding")
        if not isinstance(self.performance, FinalistPerformance):
            raise ValueError("performance must be FinalistPerformance")
        if self.binding.team_id != self.performance.team_id:
            raise ValueError("source binding and performance team_id differ")

    def to_dict(self) -> dict[str, object]:
        return {
            "binding": self.binding.to_dict(),
            "performance": _performance_dict(self.performance),
        }

    @property
    def sha256(self) -> str:
        return _canonical_json_sha256(self.to_dict())


def _require_config(config: LoadedV2Config) -> None:
    if not isinstance(config, LoadedV2Config):
        raise ValueError("config must be a validated LoadedV2Config")
    _sha256(config.sha256, "config.sha256")
    scoring = config.raw.get("scoring")
    if not isinstance(scoring, Mapping):
        raise ValueError("config.scoring must be a table")
    expected = {
        "automatic_weight": 70.0,
        "critic_weight": 15.0,
        "user_weight": 15.0,
        "automatic_absolute_points": 50.0,
        "automatic_relative_points": 20.0,
        "rounding_decimals": 6,
        "dnf_is_not_a_submission": True,
        "zero_finalists_result": "no-qualified-model",
        "objective_lock_survives_integrity_dq": True,
    }
    if any(scoring.get(key) != value for key, value in expected.items()):
        raise ValueError("config.scoring differs from the V2 finals contract")


def _validate_evidence_identity(
    evidence: Mapping[str, Any], binding: FinalistSourceBinding, config: LoadedV2Config
) -> int:
    if (
        evidence.get("team_id") != binding.team_id
        or evidence.get("candidate_id") != binding.candidate_id
        or evidence.get("strategy_sha256") != binding.strategy_sha256
        or evidence.get("risk_policy_sha256") != binding.risk_policy_sha256
        or evidence.get("config_sha256") != binding.config_sha256
        or binding.config_sha256 != config.sha256
    ):
        raise ValueError("qualification evidence differs from the finalist identity binding")
    return _integer(evidence.get("trial_count"), "trial_count", minimum=1)


def _utc_timestamp(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")


def _expected_runner_artifacts(team_id: str, stage: str) -> dict[str, str]:
    if stage == "private":
        output = f"{TOP40_V2_LAYOUT.tournament_root}/private/artifacts/{team_id}"
    elif stage == "final_oos":
        output = f"{TOP40_V2_LAYOUT.report_root(team_id)}/final-oos"
    else:  # pragma: no cover - guarded by the two callers
        raise ValueError("finals runner stage must be private or final_oos")
    return {
        name: f"{output}/{filename}" for name, filename in _ARTIFACT_FILENAMES.items()
    }


def _runner_window(
    raw: Mapping[str, Any],
    *,
    stage: str,
    binding: FinalistSourceBinding,
    config: LoadedV2Config,
) -> tuple[WindowPerformance, float, tuple[tuple[str, float], ...]]:
    record = _exact_object(raw, _RUNNER_KEYS, f"{stage} runner record")
    splits = config.raw["splits"]
    if stage == "private":
        expected_start = str(splits["private_qualifier_start"])
        expected_end = str(splits["private_qualifier_end_inclusive"])
    else:
        expected_start = str(splits["final_oos_start"])
        expected_end = str(splits["final_oos_end_inclusive"])
    expected_entrypoint = f"{TOP40_V2_LAYOUT.team_root(binding.team_id)}/strategy.py"
    expected_seed = config.raw["research_budget"]["strategy_seed"]
    if (
        record["stage"] != stage
        or record["team_id"] != binding.team_id
        or record["entrypoint"] != expected_entrypoint
        or record["seeds"] != [expected_seed]
        or record["data_manifest_sha256"] != binding.data_manifest_sha256
        or record["config_sha256"] != binding.config_sha256
        or record["strategy_sha256"] != binding.strategy_sha256
        or record["risk_policy_sha256"] != binding.risk_policy_sha256
        or record["source_bundle_sha256"] != binding.source_bundle_sha256
    ):
        raise ValueError(f"{stage} runner record differs from the finalist identity binding")

    window = _exact_object(record["scored_window"], {"start", "end", "metrics"}, "window")
    if window["start"] != expected_start or window["end"] != expected_end:
        raise ValueError(f"{stage} runner record uses a noncanonical scored window")
    metrics = _exact_object(window["metrics"], _WINDOW_METRIC_KEYS, "window metrics")
    _finite(metrics["net_sortino"], "window metrics.net_sortino")
    performance = WindowPerformance(
        net_sharpe=_finite(metrics["net_sharpe"], "window metrics.net_sharpe"),
        annualized_return=_finite(
            metrics["annualized_return"], "window metrics.annualized_return"
        ),
        calmar=_finite(metrics["calmar"], "window metrics.calmar"),
        max_drawdown=_finite(metrics["max_drawdown"], "window metrics.max_drawdown"),
        positive_quarter_fraction=_finite(
            metrics["positive_quarter_fraction"],
            "window metrics.positive_quarter_fraction",
        ),
    )
    double_cost = _finite(record["double_cost_sharpe"], "runner double_cost_sharpe")
    regimes = _exact_object(record["regime_sharpe"], set(_REGIMES), "runner regimes")
    regime_sharpes = tuple(
        (name, _finite(regimes[name], f"runner regimes.{name}")) for name in _REGIMES
    )

    intervals = _exact_object(
        record["confidence_intervals"],
        {"net_sharpe_95", "double_cost_sharpe_95"},
        "runner confidence intervals",
    )
    for name, raw_interval in intervals.items():
        if not isinstance(raw_interval, list) or len(raw_interval) != 2:
            raise ValueError(f"runner confidence interval is invalid: {name}")
        lower = _finite(raw_interval[0], f"{name}[0]")
        upper = _finite(raw_interval[1], f"{name}[1]")
        if lower > upper:
            raise ValueError(f"runner confidence interval is invalid: {name}")

    artifacts = _exact_object(record["artifacts"], set(_ARTIFACT_FILENAMES), "runner artifacts")
    if dict(artifacts) != _expected_runner_artifacts(binding.team_id, stage):
        raise ValueError(f"{stage} runner artifact paths are noncanonical")
    return performance, double_cost, regime_sharpes


def build_finalist_performance(
    *,
    binding: FinalistSourceBinding,
    development_evidence: HashBoundJson,
    private_sealed_record: HashBoundJson,
    private_runner_record: HashBoundJson,
    final_oos_runner_record: HashBoundJson,
    config: LoadedV2Config,
) -> BoundFinalistPerformance:
    """Verify the complete finalist source chain and construct one scoring input."""

    _require_config(config)
    if not isinstance(binding, FinalistSourceBinding):
        raise ValueError("binding must be FinalistSourceBinding")
    records = (
        (development_evidence, binding.development_evidence_sha256, "development evidence"),
        (private_sealed_record, binding.private_sealed_record_sha256, "private sealed record"),
        (private_runner_record, binding.private_runner_record_sha256, "private runner record"),
        (
            final_oos_runner_record,
            binding.final_oos_runner_record_sha256,
            "final OOS runner record",
        ),
    )
    for record, expected_sha256, label in records:
        if not isinstance(record, HashBoundJson) or record.sha256 != expected_sha256:
            raise ValueError(f"{label} differs from the finalist source binding")

    development = development_evidence.object("development evidence")
    development_assessment = assess_development(
        development,
        config.qualification_thresholds,
        evidence_sha256=development_evidence.sha256,
    )
    if not development_assessment.passed:
        raise ValueError("finalist development evidence does not pass every qualification gate")
    development_trials = _validate_evidence_identity(development, binding, config)

    sealed = _exact_object(
        private_sealed_record.object("private sealed record"),
        {"schema_version", "sealed_at_utc", "evidence", "assessment"},
        "private sealed record",
    )
    if sealed["schema_version"] != 1:
        raise ValueError("private sealed record schema_version must be 1")
    _utc_timestamp(sealed["sealed_at_utc"], "sealed_at_utc")
    private_evidence = sealed["evidence"]
    if not isinstance(private_evidence, Mapping):
        raise ValueError("private sealed evidence must be a JSON object")
    private_trials = _validate_evidence_identity(private_evidence, binding, config)
    if private_trials != development_trials:
        raise ValueError("private and development trial counts differ")
    embedded_assessment = sealed["assessment"]
    if not isinstance(embedded_assessment, Mapping):
        raise ValueError("private sealed assessment must be a JSON object")
    assessment_sha = _sha256(
        embedded_assessment.get("evidence_sha256"),
        "private assessment evidence_sha256",
    )
    recomputed_private = assess_private(
        private_evidence,
        config.qualification_thresholds,
        evidence_sha256=assessment_sha,
    )
    expected_assessment = recomputed_private.to_dict(include_observations=True)
    if dict(embedded_assessment) != expected_assessment:
        raise ValueError("private sealed assessment does not match its evidence and config")
    if not recomputed_private.passed:
        raise ValueError("finalist private evidence does not pass every qualification gate")

    private_raw = private_runner_record.object("private runner record")
    private_window, private_double_cost, _private_regimes = _runner_window(
        private_raw,
        stage="private",
        binding=binding,
        config=config,
    )
    private_aggregate = private_evidence["aggregate"]
    if not isinstance(private_aggregate, Mapping):  # assess_private normally catches this
        raise ValueError("private aggregate must be a JSON object")
    for evidence_field, runner_field in (
        ("net_sharpe", "net_sharpe"),
        ("annualized_return", "annualized_return"),
        ("max_drawdown", "max_drawdown"),
        ("positive_quarter_fraction", "positive_quarter_fraction"),
    ):
        _same_float(
            private_aggregate[evidence_field],
            getattr(private_window, runner_field),
            f"private {evidence_field}",
        )
    _same_float(
        private_aggregate["double_cost_sharpe"],
        private_double_cost,
        "private double_cost_sharpe",
    )

    final_window, final_double_cost, final_regimes = _runner_window(
        final_oos_runner_record.object("final OOS runner record"),
        stage="final_oos",
        binding=binding,
        config=config,
    )
    development_aggregate = development["aggregate"]
    folds = development["folds"]
    roles = development["roles"]
    stability = development["stability"]
    if not all(isinstance(item, Mapping) for item in (development_aggregate, roles, stability)):
        raise ValueError("development evidence metric groups must be JSON objects")
    if not isinstance(folds, Sequence) or isinstance(folds, (str, bytes)):
        raise ValueError("development folds must be a sequence")
    positive_folds = sum(
        _finite(fold["net_return"], "development fold return") > 0
        for fold in folds
        if isinstance(fold, Mapping)
    )
    if positive_folds > len(folds):  # pragma: no cover - defensive, assessment validates folds
        raise AssertionError("positive fold count exceeds fold count")

    performance = FinalistPerformance(
        team_id=binding.team_id,
        development=WindowPerformance(
            net_sharpe=development_aggregate["net_sharpe"],
            annualized_return=development_aggregate["annualized_return"],
            calmar=development_aggregate["calmar"],
            max_drawdown=development_aggregate["max_drawdown"],
            positive_quarter_fraction=development_aggregate[
                "positive_quarter_fraction"
            ],
        ),
        private=private_window,
        final_oos=final_window,
        double_cost_oos_sharpe=final_double_cost,
        regime_sharpes=final_regimes,
        role_stability=RoleStabilityObservations(
            bull_long_attribution=roles["long_bull_net_return"],
            bear_short_attribution=roles["short_bear_net_return"],
            chop_combined_return=roles["combined_chop_net_return"],
            parameter_stability=stability["profitable_neighbor_fraction"],
            positive_fold_fraction=positive_folds / len(folds),
        ),
    )
    return BoundFinalistPerformance(binding=binding, performance=performance)


def _component_tuple(
    raw: Iterable[tuple[str, float]], expected: tuple[tuple[str, float], ...], label: str
) -> tuple[tuple[str, float], ...]:
    try:
        components = tuple((name, _finite(points, f"{label}.{name}")) for name, points in raw)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"{label} must contain (name, points) pairs") from exc
    if tuple(name for name, _ in components) != tuple(name for name, _ in expected):
        raise ValueError(f"{label} has invalid component names or order")
    return components


@dataclasses.dataclass(frozen=True)
class ObjectiveScoreRecord:
    """One immutable 70-point record generated by ``scoring_v2``."""

    team_id: str
    objective_rank: int
    absolute_score: float
    relative_score: float
    automatic_score: float
    absolute_components: tuple[tuple[str, float], ...]
    relative_components: tuple[tuple[str, float], ...]
    performance_sha256: str
    source_binding: FinalistSourceBinding

    def __post_init__(self) -> None:
        if not isinstance(self.source_binding, FinalistSourceBinding):
            raise ValueError("source_binding must be FinalistSourceBinding")
        if self.team_id != self.source_binding.team_id:
            raise ValueError("objective record and source binding team_id differ")
        _integer(self.objective_rank, "objective_rank", minimum=1)
        absolute = _finite(self.absolute_score, "absolute_score")
        relative = _finite(self.relative_score, "relative_score")
        automatic = _finite(self.automatic_score, "automatic_score")
        if not 0.0 <= absolute <= 50.0 or not 0.0 <= relative <= 20.0:
            raise ValueError("objective sub-scores exceed the 50 + 20 point contract")
        if not math.isclose(automatic, round(absolute + relative, 6), abs_tol=1e-9):
            raise ValueError("automatic_score does not equal the locked 50 + 20 scores")
        if not 0.0 <= automatic <= 70.0:
            raise ValueError("automatic_score must be in [0, 70]")
        absolute_components = _component_tuple(
            self.absolute_components,
            ABSOLUTE_COMPONENT_WEIGHTS,
            "absolute_components",
        )
        relative_components = _component_tuple(
            self.relative_components,
            RELATIVE_COMPONENT_WEIGHTS,
            "relative_components",
        )
        if not math.isclose(sum(value for _, value in absolute_components), absolute, abs_tol=1e-6):
            raise ValueError("absolute components do not sum to absolute_score")
        if not math.isclose(sum(value for _, value in relative_components), relative, abs_tol=1e-6):
            raise ValueError("relative components do not sum to relative_score")
        _sha256(self.performance_sha256, "performance_sha256")
        object.__setattr__(self, "absolute_components", absolute_components)
        object.__setattr__(self, "relative_components", relative_components)

    def to_dict(self) -> dict[str, object]:
        return {
            "team_id": self.team_id,
            "objective_rank": self.objective_rank,
            "absolute_score": self.absolute_score,
            "relative_score": self.relative_score,
            "automatic_score": self.automatic_score,
            "absolute_components": [list(item) for item in self.absolute_components],
            "relative_components": [list(item) for item in self.relative_components],
            "performance_sha256": self.performance_sha256,
            "source_binding": self.source_binding.to_dict(),
        }


def _cohort_partition(
    finalist_team_ids: Iterable[str], dnf_team_ids: Iterable[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    finalists = tuple(finalist_team_ids)
    dnfs = tuple(dnf_team_ids)
    if finalists != tuple(team_id for team_id in TEAM_IDS if team_id in finalists):
        raise ValueError("finalist_team_ids must be unique and in canonical team order")
    if dnfs != tuple(team_id for team_id in TEAM_IDS if team_id in dnfs):
        raise ValueError("dnf_team_ids must be unique and in canonical team order")
    if set(finalists).intersection(dnfs) or set(finalists).union(dnfs) != set(TEAM_IDS):
        raise ValueError("finalists and DNF teams must exactly partition all ten teams")
    return finalists, dnfs


@dataclasses.dataclass(frozen=True)
class ObjectiveScoreLock:
    """Deterministic objective lock; no ballot or later DQ can mutate these records."""

    status: _OBJECTIVE_STATUS
    config_sha256: str
    finalist_team_ids: tuple[str, ...]
    dnf_team_ids: tuple[str, ...]
    records: tuple[ObjectiveScoreRecord, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("objective lock schema_version must be 1")
        _sha256(self.config_sha256, "objective lock config_sha256")
        finalists, dnfs = _cohort_partition(self.finalist_team_ids, self.dnf_team_ids)
        records = tuple(self.records)
        if any(not isinstance(record, ObjectiveScoreRecord) for record in records):
            raise ValueError("objective lock records must be ObjectiveScoreRecord instances")
        if tuple(record.team_id for record in records) != finalists:
            raise ValueError("objective records must exactly match finalists in canonical order")
        if any(record.source_binding.config_sha256 != self.config_sha256 for record in records):
            raise ValueError("objective record config binding differs from the lock")
        ranks = tuple(record.objective_rank for record in records)
        if sorted(ranks) != list(range(1, len(records) + 1)):
            raise ValueError("objective ranks must be a complete unique sequence")
        expected_status = "scored" if finalists else "no-qualified-model"
        if self.status != expected_status:
            raise ValueError("objective lock status differs from its finalist cohort")
        object.__setattr__(self, "finalist_team_ids", finalists)
        object.__setattr__(self, "dnf_team_ids", dnfs)
        object.__setattr__(self, "records", records)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "config_sha256": self.config_sha256,
            "finalist_team_ids": list(self.finalist_team_ids),
            "dnf_team_ids": list(self.dnf_team_ids),
            "records": [record.to_dict() for record in self.records],
        }

    @property
    def sha256(self) -> str:
        return _canonical_json_sha256(self.to_dict())


def lock_objective_scores(
    finalists: Iterable[BoundFinalistPerformance],
    *,
    finalist_team_ids: Iterable[str],
    dnf_team_ids: Iterable[str],
    config: LoadedV2Config,
) -> ObjectiveScoreLock:
    """Create the single immutable 70-point lock for the exact finalist cohort."""

    _require_config(config)
    cohort, dnfs = _cohort_partition(finalist_team_ids, dnf_team_ids)
    bound = tuple(finalists)
    if any(not isinstance(item, BoundFinalistPerformance) for item in bound):
        raise ValueError("finalists must contain only BoundFinalistPerformance records")
    by_team = {item.performance.team_id: item for item in bound}
    if len(by_team) != len(bound):
        raise ValueError("duplicate finalist performance team_id")
    if set(by_team) != set(cohort):
        raise ValueError("performance records must exactly match the finalist cohort; DNF excluded")
    if any(item.binding.config_sha256 != config.sha256 for item in bound):
        raise ValueError("finalist performance config binding differs from the objective lock")

    ordered = tuple(by_team[team_id] for team_id in cohort)
    scored = scoring_v2.score_finalists(item.performance for item in ordered)
    expected_status = "scored" if cohort else "no-qualified-model"
    if scored.status != expected_status or len(scored.scores) != len(cohort):
        raise ValueError("scoring_v2 returned a result inconsistent with the finalist cohort")
    scored_by_team = {score.team_id: score for score in scored.scores}
    records: list[ObjectiveScoreRecord] = []
    for item in ordered:
        score = scored_by_team[item.performance.team_id]
        if (
            score.critic_score != 0.0
            or score.user_score != 0.0
            or score.integrity_disqualified
            or score.total_score != score.automatic_score
        ):
            raise ValueError("scoring_v2 objective pass unexpectedly included jury or DQ state")
        records.append(
            ObjectiveScoreRecord(
                team_id=score.team_id,
                objective_rank=score.objective_rank,
                absolute_score=score.absolute_score,
                relative_score=score.relative_score,
                automatic_score=score.automatic_score,
                absolute_components=score.absolute_components,
                relative_components=score.relative_components,
                performance_sha256=item.sha256,
                source_binding=item.binding,
            )
        )
    return ObjectiveScoreLock(
        status=expected_status,
        config_sha256=config.sha256,
        finalist_team_ids=cohort,
        dnf_team_ids=dnfs,
        records=tuple(records),
    )


def _jury_scores(
    raw: Mapping[str, object], finalist_team_ids: tuple[str, ...], label: str
) -> tuple[tuple[str, float], ...]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must be a mapping")
    if any(not isinstance(team_id, str) for team_id in raw):
        raise ValueError(f"{label} keys must be finalist team-id strings")
    if set(raw) != set(finalist_team_ids):
        missing = sorted(set(finalist_team_ids) - set(raw))
        extra = sorted(set(raw) - set(finalist_team_ids))
        raise ValueError(
            f"{label} must score every finalist exactly; missing={missing}, extra={extra}"
        )
    result: list[tuple[str, float]] = []
    for team_id in finalist_team_ids:
        score = _finite(raw[team_id], f"{label}.{team_id}")
        if not 0.0 <= score <= 15.0:
            raise ValueError(f"{label}.{team_id} must be in [0, 15]")
        result.append((team_id, score))
    return tuple(result)


@dataclasses.dataclass(frozen=True)
class FinalistBallots:
    critic: tuple[tuple[str, float], ...]
    user: tuple[tuple[str, float], ...]

    def to_dict(self) -> dict[str, object]:
        return {"critic": dict(self.critic), "user": dict(self.user)}

    @property
    def sha256(self) -> str:
        return _canonical_json_sha256(self.to_dict())


def validate_finalist_ballots(
    objective_lock: ObjectiveScoreLock,
    *,
    critic_ballot: Mapping[str, object],
    user_ballot: Mapping[str, object],
) -> FinalistBallots:
    """Require one finite 0..15 Critic and user score for every finalist, and no DNF."""

    if not isinstance(objective_lock, ObjectiveScoreLock):
        raise ValueError("objective_lock must be ObjectiveScoreLock")
    return FinalistBallots(
        critic=_jury_scores(
            critic_ballot, objective_lock.finalist_team_ids, "critic_ballot"
        ),
        user=_jury_scores(user_ballot, objective_lock.finalist_team_ids, "user_ballot"),
    )


@dataclasses.dataclass(frozen=True)
class IntegrityDisqualifications:
    reasons: tuple[tuple[str, tuple[str, ...]], ...]

    def to_dict(self) -> dict[str, object]:
        return {team_id: list(reasons) for team_id, reasons in self.reasons}

    @property
    def sha256(self) -> str:
        return _canonical_json_sha256(self.to_dict())


def validate_integrity_disqualifications(
    objective_lock: ObjectiveScoreLock,
    reasons_by_team: Mapping[str, Sequence[str]],
) -> IntegrityDisqualifications:
    """Validate a finalist-only DQ subset with auditable, nonempty unique reasons."""

    if not isinstance(objective_lock, ObjectiveScoreLock):
        raise ValueError("objective_lock must be ObjectiveScoreLock")
    if not isinstance(reasons_by_team, Mapping):
        raise ValueError("integrity disqualifications must be a mapping")
    if any(not isinstance(team_id, str) for team_id in reasons_by_team):
        raise ValueError("integrity disqualification keys must be finalist team-id strings")
    unknown = set(reasons_by_team) - set(objective_lock.finalist_team_ids)
    if unknown:
        raise ValueError(f"integrity disqualifications name non-finalists: {sorted(unknown)}")
    result: list[tuple[str, tuple[str, ...]]] = []
    for team_id in objective_lock.finalist_team_ids:
        if team_id not in reasons_by_team:
            continue
        raw_reasons = reasons_by_team[team_id]
        if isinstance(raw_reasons, (str, bytes)) or not isinstance(raw_reasons, Sequence):
            raise ValueError("integrity DQ reasons must be a sequence of nonempty strings")
        reasons = tuple(raw_reasons)
        if not reasons:
            raise ValueError("an integrity DQ entry must contain at least one reason")
        if any(
            not isinstance(reason, str)
            or not reason
            or reason != reason.strip()
            or len(reason) > 256
            for reason in reasons
        ):
            raise ValueError("integrity DQ reasons must be trimmed nonempty strings <= 256 chars")
        if len(reasons) != len(set(reasons)):
            raise ValueError("integrity DQ reasons must be unique per finalist")
        result.append((team_id, reasons))
    return IntegrityDisqualifications(tuple(result))


@dataclasses.dataclass(frozen=True)
class FinalScoreRecord:
    objective: ObjectiveScoreRecord
    rank: int | None
    critic_score: float
    user_score: float
    total_score: float | None
    integrity_disqualified: bool
    disqualification_reasons: tuple[str, ...]

    @property
    def team_id(self) -> str:
        return self.objective.team_id

    @property
    def objective_rank(self) -> int:
        return self.objective.objective_rank

    @property
    def automatic_score(self) -> float:
        return self.objective.automatic_score

    def to_dict(self) -> dict[str, object]:
        return {
            "objective": self.objective.to_dict(),
            "rank": self.rank,
            "critic_score": self.critic_score,
            "user_score": self.user_score,
            "total_score": self.total_score,
            "integrity_disqualified": self.integrity_disqualified,
            "disqualification_reasons": list(self.disqualification_reasons),
        }


@dataclasses.dataclass(frozen=True)
class FinalScoreLock:
    status: _OBJECTIVE_STATUS
    winner_team_id: str | None
    objective_lock_sha256: str
    ballots: FinalistBallots
    integrity_disqualifications: IntegrityDisqualifications
    scores: tuple[FinalScoreRecord, ...]
    schema_version: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "winner_team_id": self.winner_team_id,
            "objective_lock_sha256": self.objective_lock_sha256,
            "ballots": self.ballots.to_dict(),
            "integrity_disqualifications": self.integrity_disqualifications.to_dict(),
            "scores": [score.to_dict() for score in self.scores],
        }

    @property
    def sha256(self) -> str:
        return _canonical_json_sha256(self.to_dict())


def combine_locked_scores(
    objective_lock: ObjectiveScoreLock,
    *,
    critic_ballot: Mapping[str, object],
    user_ballot: Mapping[str, object],
    integrity_disqualifications: Mapping[str, Sequence[str]],
) -> FinalScoreLock:
    """Add ballots to locked automatic scores without invoking objective scoring again."""

    if not isinstance(objective_lock, ObjectiveScoreLock):
        raise ValueError("objective_lock must be ObjectiveScoreLock")
    ballots = validate_finalist_ballots(
        objective_lock,
        critic_ballot=critic_ballot,
        user_ballot=user_ballot,
    )
    disqualifications = validate_integrity_disqualifications(
        objective_lock, integrity_disqualifications
    )
    critic = dict(ballots.critic)
    user = dict(ballots.user)
    dq = dict(disqualifications.reasons)
    unranked: list[FinalScoreRecord] = []
    for objective in objective_lock.records:
        reasons = dq.get(objective.team_id, ())
        total = round(
            objective.automatic_score + critic[objective.team_id] + user[objective.team_id],
            6,
        )
        unranked.append(
            FinalScoreRecord(
                objective=objective,
                rank=None,
                critic_score=critic[objective.team_id],
                user_score=user[objective.team_id],
                total_score=None if reasons else total,
                integrity_disqualified=bool(reasons),
                disqualification_reasons=reasons,
            )
        )
    valid = sorted(
        (score for score in unranked if not score.integrity_disqualified),
        key=lambda score: (-float(score.total_score), score.team_id),
    )
    ranked = tuple(
        dataclasses.replace(score, rank=rank)
        for rank, score in enumerate(valid, start=1)
    )
    disqualified = tuple(
        sorted(
            (score for score in unranked if score.integrity_disqualified),
            key=lambda score: (score.objective_rank, score.team_id),
        )
    )
    return FinalScoreLock(
        status=objective_lock.status,
        winner_team_id=ranked[0].team_id if ranked else None,
        objective_lock_sha256=objective_lock.sha256,
        ballots=ballots,
        integrity_disqualifications=disqualifications,
        scores=(*ranked, *disqualified),
    )


@dataclasses.dataclass(frozen=True)
class PaperEligibilityGate:
    name: str
    observed: float | int
    operator: str
    threshold: float | int
    passed: bool


@dataclasses.dataclass(frozen=True)
class PaperEligibility:
    team_id: str
    config_sha256: str
    performance_sha256: str
    eligible: bool
    gates: tuple[PaperEligibilityGate, ...]

    def to_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def assess_paper_eligibility(
    finalist: BoundFinalistPerformance, config: LoadedV2Config
) -> PaperEligibility:
    """Apply the separately frozen paper thresholds; tournament rank is irrelevant."""

    _require_config(config)
    if not isinstance(finalist, BoundFinalistPerformance):
        raise ValueError("finalist must be BoundFinalistPerformance")
    if finalist.binding.config_sha256 != config.sha256:
        raise ValueError("finalist performance config differs from paper eligibility config")
    raw_thresholds = config.raw.get("paper_eligibility")
    expected_keys = {
        "minimum_development_net_sharpe",
        "minimum_private_net_sharpe",
        "minimum_final_oos_net_sharpe",
        "minimum_double_cost_oos_sharpe",
        "maximum_final_oos_drawdown",
        "minimum_positive_quarter_fraction",
        "minimum_worst_regime_sharpe",
        "minimum_positive_regimes",
    }
    thresholds = _exact_object(raw_thresholds, expected_keys, "config.paper_eligibility")
    performance = finalist.performance
    regime_values = tuple(value for _, value in performance.regime_sharpes)
    observations: tuple[tuple[str, float | int, str, float | int], ...] = (
        (
            "development.net_sharpe",
            performance.development.net_sharpe,
            ">=",
            _finite(
                thresholds["minimum_development_net_sharpe"],
                "minimum_development_net_sharpe",
            ),
        ),
        (
            "private.net_sharpe",
            performance.private.net_sharpe,
            ">=",
            _finite(
                thresholds["minimum_private_net_sharpe"],
                "minimum_private_net_sharpe",
            ),
        ),
        (
            "final_oos.net_sharpe",
            performance.final_oos.net_sharpe,
            ">=",
            _finite(
                thresholds["minimum_final_oos_net_sharpe"],
                "minimum_final_oos_net_sharpe",
            ),
        ),
        (
            "final_oos.double_cost_sharpe",
            performance.double_cost_oos_sharpe,
            ">=",
            _finite(
                thresholds["minimum_double_cost_oos_sharpe"],
                "minimum_double_cost_oos_sharpe",
            ),
        ),
        (
            "final_oos.max_drawdown",
            performance.final_oos.max_drawdown,
            "<=",
            _finite(
                thresholds["maximum_final_oos_drawdown"],
                "maximum_final_oos_drawdown",
            ),
        ),
        (
            "final_oos.positive_quarter_fraction",
            performance.final_oos.positive_quarter_fraction,
            ">=",
            _finite(
                thresholds["minimum_positive_quarter_fraction"],
                "minimum_positive_quarter_fraction",
            ),
        ),
        (
            "final_oos.worst_regime_sharpe",
            min(regime_values),
            ">=",
            _finite(
                thresholds["minimum_worst_regime_sharpe"],
                "minimum_worst_regime_sharpe",
            ),
        ),
        (
            "final_oos.positive_regime_count",
            sum(value > 0.0 for value in regime_values),
            ">=",
            _integer(
                thresholds["minimum_positive_regimes"],
                "minimum_positive_regimes",
            ),
        ),
    )
    gates = tuple(
        PaperEligibilityGate(
            name=name,
            observed=observed,
            operator=operator,
            threshold=threshold,
            passed=(observed >= threshold if operator == ">=" else observed <= threshold),
        )
        for name, observed, operator, threshold in observations
    )
    return PaperEligibility(
        team_id=performance.team_id,
        config_sha256=config.sha256,
        performance_sha256=finalist.sha256,
        eligible=all(gate.passed for gate in gates),
        gates=gates,
    )
