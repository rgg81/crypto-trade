"""Fail-closed qualification assessments for Top-40 V3.

The module accepts simple metric mappings, but every result is bound to one immutable candidate
identity.  Assessment objects are factory-created and revalidated before ranking so callers cannot
construct an eligible result by supplying an incomplete check vector or arbitrary score fields.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Mapping
from types import MappingProxyType

TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 11))
PUBLIC_REGIMES = ("bull", "bear", "chop", "stress")
PUBLIC_ADVANCE_COUNT = 4

PUBLIC_CORE_FLOORS = MappingProxyType(
    {
        "net_sharpe": 0.75,
        "annualized_return": 0.0,
        "max_drawdown": 0.30,
        "double_cost_sharpe": 0.35,
        "positive_quarter_fraction": 0.50,
        "trade_count": 1_000,
        "positive_regime_count": 2,
        "worst_regime_sharpe": -0.75,
    }
)
PRIVATE_CORE_FLOORS = MappingProxyType(
    {
        "net_sharpe": 0.0,
        "annualized_return": 0.0,
        "max_drawdown": 0.35,
        "double_cost_sharpe": 0.0,
    }
)

_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PUBLIC_METRIC_KEYS = {
    "net_sharpe",
    "annualized_return",
    "max_drawdown",
    "double_cost_sharpe",
    "positive_quarter_fraction",
    "trade_count",
    "regime_sharpe",
}
_PRIVATE_METRIC_KEYS = {
    "net_sharpe",
    "annualized_return",
    "max_drawdown",
    "double_cost_sharpe",
}
_HARD_CHECK_NAMES = (
    "reproducible",
    "data_authority",
    "universe_compliant",
    "causal",
    "execution_compliant",
    "solvent",
    "window_complete",
)


def _canonical_sha256(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


@dataclasses.dataclass(frozen=True)
class CandidateIdentity:
    """The exact executable and authority identity used at every V3 stage."""

    team_id: str
    candidate_id: str
    source_bundle_sha256: str
    strategy_sha256: str
    dependency_lock_sha256: str
    config_sha256: str
    risk_policy_sha256: str
    data_authority_sha256: str
    evaluator_sha256: str

    def __post_init__(self) -> None:
        if self.team_id not in TEAM_IDS:
            raise ValueError("team_id must be one of the ten frozen V3 team IDs")
        if not isinstance(self.candidate_id, str) or _IDENTIFIER.fullmatch(self.candidate_id) is None:
            raise ValueError("candidate_id must be a safe nonempty identifier")
        for field in (
            "source_bundle_sha256",
            "strategy_sha256",
            "dependency_lock_sha256",
            "config_sha256",
            "risk_policy_sha256",
            "data_authority_sha256",
            "evaluator_sha256",
        ):
            _require_sha256(getattr(self, field), field)

    @property
    def sha256(self) -> str:
        return _canonical_sha256(
            {
                "candidate_id": self.candidate_id,
                "config_sha256": self.config_sha256,
                "data_authority_sha256": self.data_authority_sha256,
                "dependency_lock_sha256": self.dependency_lock_sha256,
                "evaluator_sha256": self.evaluator_sha256,
                "risk_policy_sha256": self.risk_policy_sha256,
                "source_bundle_sha256": self.source_bundle_sha256,
                "strategy_sha256": self.strategy_sha256,
                "team_id": self.team_id,
            }
        )


@dataclasses.dataclass(frozen=True)
class StructuralChecks:
    """Exact structural hard-gate facts supplied by an organizer-owned adapter."""

    reproducible: bool
    data_authority: bool
    universe_compliant: bool
    causal: bool
    execution_compliant: bool
    solvent: bool
    window_complete: bool

    def __post_init__(self) -> None:
        for field in _HARD_CHECK_NAMES:
            if type(getattr(self, field)) is not bool:
                raise ValueError(f"{field} must be a Boolean")

    @property
    def passed(self) -> bool:
        return all(getattr(self, name) for name in _HARD_CHECK_NAMES)

    @property
    def failed_names(self) -> tuple[str, ...]:
        return tuple(name for name in _HARD_CHECK_NAMES if not getattr(self, name))


@dataclasses.dataclass(frozen=True, init=False)
class MetricCheck:
    """One factory-created core-floor result."""

    name: str
    observed: float | int
    operator: str
    threshold: float | int
    passed: bool

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("MetricCheck objects are created only by qualification factories")


@dataclasses.dataclass(frozen=True, init=False)
class PublicAssessment:
    """Identity-bound public eligibility and robustness-ranking inputs."""

    identity: CandidateIdentity
    structural_checks: StructuralChecks
    core_checks: tuple[MetricCheck, ...]
    robustness_score: float
    net_sharpe: float
    annualized_return: float
    max_drawdown: float
    double_cost_sharpe: float
    positive_quarter_fraction: float
    trade_count: int
    regime_sharpe: tuple[float, ...]

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("PublicAssessment objects are created only by assess_public")

    @property
    def positive_regime_count(self) -> int:
        validate_public_assessment(self)
        return sum(value > 0.0 for value in self.regime_sharpe)

    @property
    def worst_regime_sharpe(self) -> float:
        validate_public_assessment(self)
        return min(self.regime_sharpe)

    @property
    def eligible(self) -> bool:
        validate_public_assessment(self)
        return self.structural_checks.passed and all(check.passed for check in self.core_checks)

    @property
    def failed_core_floor_names(self) -> tuple[str, ...]:
        validate_public_assessment(self)
        return tuple(check.name for check in self.core_checks if not check.passed)


@dataclasses.dataclass(frozen=True, init=False)
class PrivateAssessment:
    """Identity-bound private-stage eligibility without a regime veto."""

    identity: CandidateIdentity
    structural_checks: StructuralChecks
    core_checks: tuple[MetricCheck, ...]
    net_sharpe: float
    annualized_return: float
    max_drawdown: float
    double_cost_sharpe: float

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("PrivateAssessment objects are created only by assess_private")

    @property
    def eligible(self) -> bool:
        validate_private_assessment(self)
        return self.structural_checks.passed and all(check.passed for check in self.core_checks)

    @property
    def failed_core_floor_names(self) -> tuple[str, ...]:
        validate_private_assessment(self)
        return tuple(check.name for check in self.core_checks if not check.passed)


def _new_instance(cls: type[object], **fields: object):
    instance = object.__new__(cls)
    for name, value in fields.items():
        object.__setattr__(instance, name, value)
    return instance


def _new_metric_check(
    name: str,
    observed: float | int,
    operator: str,
    threshold: float | int,
    passed: bool,
) -> MetricCheck:
    return _new_instance(
        MetricCheck,
        name=name,
        observed=observed,
        operator=operator,
        threshold=threshold,
        passed=passed,
    )


def _exact_mapping(
    raw: object,
    expected_keys: set[str] | frozenset[str],
    label: str,
) -> Mapping[str, object]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must be a mapping")
    actual_keys = set(raw)
    if actual_keys != set(expected_keys):
        missing = sorted(set(expected_keys) - actual_keys)
        extra = sorted(actual_keys - set(expected_keys), key=repr)
        raise ValueError(f"{label} has invalid keys; missing={missing}, extra={extra}")
    return raw


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _fraction(value: object, label: str) -> float:
    result = _finite(value, label)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be in [0,1]")
    return result


def _integer(value: object, label: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be at most {maximum}")
    return value


def _structural_checks(
    *,
    reproducible: bool,
    data_authority: bool,
    universe_compliant: bool,
    causal: bool,
    execution_compliant: bool,
    solvent: bool,
    window_complete: bool,
) -> StructuralChecks:
    return StructuralChecks(
        reproducible=reproducible,
        data_authority=data_authority,
        universe_compliant=universe_compliant,
        causal=causal,
        execution_compliant=execution_compliant,
        solvent=solvent,
        window_complete=window_complete,
    )


def _minimum(name: str, observed: float | int, threshold: float | int) -> MetricCheck:
    return _new_metric_check(name, observed, ">=", threshold, observed >= threshold)


def _strict_positive(name: str, observed: float) -> MetricCheck:
    return _new_metric_check(name, observed, ">", 0.0, observed > 0.0)


def _maximum(name: str, observed: float, threshold: float) -> MetricCheck:
    return _new_metric_check(name, observed, "<=", threshold, observed <= threshold)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def robustness_score(
    *,
    net_sharpe: float,
    annualized_return: float,
    max_drawdown: float,
    double_cost_sharpe: float,
    positive_quarter_fraction: float,
    positive_regime_count: int,
    worst_regime_sharpe: float,
) -> float:
    """Return the frozen 0-100 V3 robustness score without adding an eligibility cutoff."""

    checked_net_sharpe = _finite(net_sharpe, "net_sharpe")
    checked_annualized_return = _finite(annualized_return, "annualized_return")
    checked_max_drawdown = _fraction(max_drawdown, "max_drawdown")
    checked_double_cost_sharpe = _finite(double_cost_sharpe, "double_cost_sharpe")
    checked_positive_quarters = _fraction(
        positive_quarter_fraction,
        "positive_quarter_fraction",
    )
    checked_positive_regimes = _integer(
        positive_regime_count,
        "positive_regime_count",
        maximum=len(PUBLIC_REGIMES),
    )
    checked_worst_regime = _finite(worst_regime_sharpe, "worst_regime_sharpe")
    return (
        25.0 * _clamp((checked_net_sharpe - 0.75) / 0.75)
        + 15.0 * _clamp(checked_annualized_return / 0.30)
        + 15.0 * _clamp((0.30 - checked_max_drawdown) / 0.20)
        + 15.0 * _clamp((checked_double_cost_sharpe - 0.35) / 0.65)
        + 15.0 * _clamp((checked_positive_quarters - 0.50) / 0.25)
        + 10.0 * (checked_positive_regimes / len(PUBLIC_REGIMES))
        + 5.0 * _clamp((checked_worst_regime + 0.75) / 1.50)
    )


def _public_core_checks(
    *,
    net_sharpe: float,
    annualized_return: float,
    max_drawdown: float,
    double_cost_sharpe: float,
    positive_quarter_fraction: float,
    trade_count: int,
    regime_sharpe: tuple[float, ...],
) -> tuple[MetricCheck, ...]:
    positive_regime_count = sum(value > 0.0 for value in regime_sharpe)
    worst_regime_sharpe = min(regime_sharpe)
    return (
        _minimum("net_sharpe", net_sharpe, PUBLIC_CORE_FLOORS["net_sharpe"]),
        _strict_positive("annualized_return", annualized_return),
        _maximum("max_drawdown", max_drawdown, PUBLIC_CORE_FLOORS["max_drawdown"]),
        _minimum(
            "double_cost_sharpe",
            double_cost_sharpe,
            PUBLIC_CORE_FLOORS["double_cost_sharpe"],
        ),
        _minimum(
            "positive_quarter_fraction",
            positive_quarter_fraction,
            PUBLIC_CORE_FLOORS["positive_quarter_fraction"],
        ),
        _minimum("trade_count", trade_count, PUBLIC_CORE_FLOORS["trade_count"]),
        _minimum(
            "positive_regime_count",
            positive_regime_count,
            PUBLIC_CORE_FLOORS["positive_regime_count"],
        ),
        _minimum(
            "worst_regime_sharpe",
            worst_regime_sharpe,
            PUBLIC_CORE_FLOORS["worst_regime_sharpe"],
        ),
    )


def _private_core_checks(
    *,
    net_sharpe: float,
    annualized_return: float,
    max_drawdown: float,
    double_cost_sharpe: float,
) -> tuple[MetricCheck, ...]:
    return (
        _strict_positive("net_sharpe", net_sharpe),
        _strict_positive("annualized_return", annualized_return),
        _strict_positive("double_cost_sharpe", double_cost_sharpe),
        _maximum("max_drawdown", max_drawdown, PRIVATE_CORE_FLOORS["max_drawdown"]),
    )


def validate_public_assessment(assessment: PublicAssessment) -> None:
    """Fail closed unless an assessment contains the exact factory-produced invariant vector."""

    if type(assessment) is not PublicAssessment:
        raise ValueError("assessment must be an exact PublicAssessment")
    if not isinstance(assessment.identity, CandidateIdentity):
        raise ValueError("public assessment identity is invalid")
    if not isinstance(assessment.structural_checks, StructuralChecks):
        raise ValueError("public assessment structural checks are invalid")
    net_sharpe = _finite(assessment.net_sharpe, "assessment.net_sharpe")
    annualized_return = _finite(
        assessment.annualized_return,
        "assessment.annualized_return",
    )
    max_drawdown = _fraction(assessment.max_drawdown, "assessment.max_drawdown")
    double_cost_sharpe = _finite(
        assessment.double_cost_sharpe,
        "assessment.double_cost_sharpe",
    )
    positive_quarter_fraction = _fraction(
        assessment.positive_quarter_fraction,
        "assessment.positive_quarter_fraction",
    )
    trade_count = _integer(assessment.trade_count, "assessment.trade_count")
    if not isinstance(assessment.regime_sharpe, tuple) or len(assessment.regime_sharpe) != len(
        PUBLIC_REGIMES
    ):
        raise ValueError("public assessment must contain the exact four-regime vector")
    regime_sharpe = tuple(
        _finite(value, f"assessment.regime_sharpe.{regime}")
        for regime, value in zip(PUBLIC_REGIMES, assessment.regime_sharpe, strict=True)
    )
    expected_checks = _public_core_checks(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
        positive_quarter_fraction=positive_quarter_fraction,
        trade_count=trade_count,
        regime_sharpe=regime_sharpe,
    )
    if assessment.core_checks != expected_checks:
        raise ValueError("public assessment core-check vector is not canonical")
    expected_score = robustness_score(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
        positive_quarter_fraction=positive_quarter_fraction,
        positive_regime_count=sum(value > 0.0 for value in regime_sharpe),
        worst_regime_sharpe=min(regime_sharpe),
    )
    if assessment.robustness_score != expected_score:
        raise ValueError("public assessment robustness score is not canonical")


def validate_private_assessment(assessment: PrivateAssessment) -> None:
    """Fail closed unless a private assessment contains the exact factory invariant vector."""

    if type(assessment) is not PrivateAssessment:
        raise ValueError("assessment must be an exact PrivateAssessment")
    if not isinstance(assessment.identity, CandidateIdentity):
        raise ValueError("private assessment identity is invalid")
    if not isinstance(assessment.structural_checks, StructuralChecks):
        raise ValueError("private assessment structural checks are invalid")
    net_sharpe = _finite(assessment.net_sharpe, "assessment.net_sharpe")
    annualized_return = _finite(
        assessment.annualized_return,
        "assessment.annualized_return",
    )
    max_drawdown = _fraction(assessment.max_drawdown, "assessment.max_drawdown")
    double_cost_sharpe = _finite(
        assessment.double_cost_sharpe,
        "assessment.double_cost_sharpe",
    )
    expected_checks = _private_core_checks(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
    )
    if assessment.core_checks != expected_checks:
        raise ValueError("private assessment core-check vector is not canonical")


def assess_public(
    identity: CandidateIdentity,
    metrics: Mapping[str, object],
    *,
    reproducible: bool,
    data_authority: bool,
    universe_compliant: bool,
    causal: bool,
    execution_compliant: bool,
    solvent: bool,
    window_complete: bool,
) -> PublicAssessment:
    """Assess an identity-bound public metric mapping under the frozen V3 policy."""

    if not isinstance(identity, CandidateIdentity):
        raise ValueError("identity must be a CandidateIdentity")
    root = _exact_mapping(metrics, _PUBLIC_METRIC_KEYS, "public metrics")
    regime_raw = _exact_mapping(root["regime_sharpe"], set(PUBLIC_REGIMES), "regime_sharpe")
    net_sharpe = _finite(root["net_sharpe"], "net_sharpe")
    annualized_return = _finite(root["annualized_return"], "annualized_return")
    max_drawdown = _fraction(root["max_drawdown"], "max_drawdown")
    double_cost_sharpe = _finite(root["double_cost_sharpe"], "double_cost_sharpe")
    positive_quarter_fraction = _fraction(
        root["positive_quarter_fraction"],
        "positive_quarter_fraction",
    )
    trade_count = _integer(root["trade_count"], "trade_count")
    regime_sharpe = tuple(
        _finite(regime_raw[regime], f"regime_sharpe.{regime}") for regime in PUBLIC_REGIMES
    )
    checks = _public_core_checks(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
        positive_quarter_fraction=positive_quarter_fraction,
        trade_count=trade_count,
        regime_sharpe=regime_sharpe,
    )
    score = robustness_score(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
        positive_quarter_fraction=positive_quarter_fraction,
        positive_regime_count=sum(value > 0.0 for value in regime_sharpe),
        worst_regime_sharpe=min(regime_sharpe),
    )
    assessment = _new_instance(
        PublicAssessment,
        identity=identity,
        structural_checks=_structural_checks(
            reproducible=reproducible,
            data_authority=data_authority,
            universe_compliant=universe_compliant,
            causal=causal,
            execution_compliant=execution_compliant,
            solvent=solvent,
            window_complete=window_complete,
        ),
        core_checks=checks,
        robustness_score=score,
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
        positive_quarter_fraction=positive_quarter_fraction,
        trade_count=trade_count,
        regime_sharpe=regime_sharpe,
    )
    validate_public_assessment(assessment)
    return assessment


def rank_public_assessments(
    assessments: Mapping[str, PublicAssessment],
) -> tuple[str, ...]:
    """Return eligible team IDs in frozen ranking order, with exactly one entry per team."""

    if not isinstance(assessments, Mapping):
        raise ValueError("assessments must be a mapping keyed by team_id")
    for team_id, assessment in assessments.items():
        if team_id not in TEAM_IDS:
            raise ValueError("assessment keys must be frozen V3 team IDs")
        validate_public_assessment(assessment)
        if team_id != assessment.identity.team_id:
            raise ValueError("assessment key must match identity.team_id")
    return tuple(
        sorted(
            (team_id for team_id, item in assessments.items() if item.eligible),
            key=lambda team_id: (
                -assessments[team_id].robustness_score,
                assessments[team_id].max_drawdown,
                -assessments[team_id].double_cost_sharpe,
                -min(assessments[team_id].regime_sharpe),
                team_id,
            ),
        )
    )


def select_public_cohort(
    assessments: Mapping[str, PublicAssessment],
) -> tuple[str, ...]:
    """Return the frozen top-four public cohort, or every passer when fewer than four pass."""

    return rank_public_assessments(assessments)[:PUBLIC_ADVANCE_COUNT]


def assess_private(
    identity: CandidateIdentity,
    metrics: Mapping[str, object],
    *,
    reproducible: bool,
    data_authority: bool,
    universe_compliant: bool,
    causal: bool,
    execution_compliant: bool,
    solvent: bool,
    window_complete: bool,
) -> PrivateAssessment:
    """Assess an identity-bound V3 private stage without any per-regime veto."""

    if not isinstance(identity, CandidateIdentity):
        raise ValueError("identity must be a CandidateIdentity")
    root = _exact_mapping(metrics, _PRIVATE_METRIC_KEYS, "private metrics")
    net_sharpe = _finite(root["net_sharpe"], "net_sharpe")
    annualized_return = _finite(root["annualized_return"], "annualized_return")
    max_drawdown = _fraction(root["max_drawdown"], "max_drawdown")
    double_cost_sharpe = _finite(root["double_cost_sharpe"], "double_cost_sharpe")
    checks = _private_core_checks(
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
    )
    assessment = _new_instance(
        PrivateAssessment,
        identity=identity,
        structural_checks=_structural_checks(
            reproducible=reproducible,
            data_authority=data_authority,
            universe_compliant=universe_compliant,
            causal=causal,
            execution_compliant=execution_compliant,
            solvent=solvent,
            window_complete=window_complete,
        ),
        core_checks=checks,
        net_sharpe=net_sharpe,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        double_cost_sharpe=double_cost_sharpe,
    )
    validate_private_assessment(assessment)
    return assessment
