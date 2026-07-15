"""Pure, machine-enforced qualification gates for Top-40 V2."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REQUIRED_REGIMES = ("bull", "bear", "chop", "stress")


@dataclasses.dataclass(frozen=True)
class GateResult:
    name: str
    observed: float | int | bool
    operator: str
    threshold: float | int | bool
    passed: bool


@dataclasses.dataclass(frozen=True)
class QualificationAssessment:
    schema_version: int
    stage: str
    team_id: str
    candidate_id: str
    evidence_sha256: str
    passed: bool
    gates: tuple[GateResult, ...]

    @property
    def failed_gate_names(self) -> tuple[str, ...]:
        return tuple(gate.name for gate in self.gates if not gate.passed)

    def to_dict(self, *, include_observations: bool = True) -> dict[str, object]:
        gates: list[dict[str, object]] = []
        for gate in self.gates:
            item: dict[str, object] = {"name": gate.name, "passed": gate.passed}
            if include_observations:
                item.update(
                    {
                        "observed": gate.observed,
                        "operator": gate.operator,
                        "threshold": gate.threshold,
                    }
                )
            gates.append(item)
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "team_id": self.team_id,
            "candidate_id": self.candidate_id,
            "evidence_sha256": self.evidence_sha256,
            "passed": self.passed,
            "failed_gate_names": list(self.failed_gate_names),
            "gates": gates,
        }


def _exact_object(raw: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != expected:
        missing = sorted(expected - set(raw)) if isinstance(raw, Mapping) else sorted(expected)
        extra = sorted(set(raw) - expected) if isinstance(raw, Mapping) else []
        raise ValueError(f"{label} has invalid keys; missing={missing}, extra={extra}")
    return raw


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


def _identity(raw: Mapping[str, Any], expected_stage: str) -> tuple[str, str]:
    if raw["schema_version"] != 1 or raw["stage"] != expected_stage:
        raise ValueError(
            f"qualification evidence must use stage={expected_stage!r}, schema_version=1"
        )
    team_id = raw["team_id"]
    candidate_id = raw["candidate_id"]
    if not isinstance(team_id, str) or _TEAM_ID.fullmatch(team_id) is None:
        raise ValueError("team_id must be team-01 through team-10")
    if not isinstance(candidate_id, str) or not candidate_id or len(candidate_id) > 128:
        raise ValueError("candidate_id must be a non-empty string of at most 128 characters")
    for field in ("strategy_sha256", "risk_policy_sha256", "config_sha256"):
        value = raw[field]
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            raise ValueError(f"{field} must be 64 lowercase hexadecimal characters")
    _integer(raw["trial_count"], "trial_count", minimum=1)
    return team_id, candidate_id


def _minimum(name: str, observed: float | int, threshold: float | int) -> GateResult:
    return GateResult(name, observed, ">=", threshold, observed >= threshold)


def _positive(name: str, observed: float) -> GateResult:
    return GateResult(name, observed, ">", 0.0, observed > 0)


def _greater(name: str, observed: float, threshold: float) -> GateResult:
    return GateResult(name, observed, ">", threshold, observed > threshold)


def _maximum(name: str, observed: float, threshold: float) -> GateResult:
    return GateResult(name, observed, "<=", threshold, observed <= threshold)


def _true(name: str, observed: bool) -> GateResult:
    return GateResult(name, observed, "==", True, observed is True)


def _load_evidence(path: str | Path) -> tuple[Mapping[str, Any], str]:
    evidence_path = Path(path)
    try:
        payload = evidence_path.read_bytes()
        raw = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid qualification evidence: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("qualification evidence root must be a JSON object")
    return raw, hashlib.sha256(payload).hexdigest()


def assess_development(
    evidence: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    *,
    evidence_sha256: str,
) -> QualificationAssessment:
    """Apply every non-compensatory visible-development gate."""
    root = _exact_object(
        evidence,
        {
            "schema_version",
            "stage",
            "team_id",
            "candidate_id",
            "strategy_sha256",
            "risk_policy_sha256",
            "config_sha256",
            "trial_count",
            "aggregate",
            "folds",
            "regimes",
            "roles",
            "sleeves",
            "stability",
        },
        "development evidence",
    )
    team_id, candidate_id = _identity(root, "development")
    aggregate = _exact_object(
        root["aggregate"],
        {
            "net_sharpe",
            "annualized_return",
            "calmar",
            "max_drawdown",
            "double_cost_sharpe",
            "positive_quarter_fraction",
            "trial_adjusted_probability_positive",
        },
        "development aggregate",
    )
    development = thresholds["development"]
    gates: list[GateResult] = [
        _minimum(
            "development.net_sharpe",
            _finite(aggregate["net_sharpe"], "aggregate.net_sharpe"),
            _finite(development["minimum_net_sharpe"], "minimum_net_sharpe"),
        ),
        _greater(
            "development.annualized_return",
            _finite(aggregate["annualized_return"], "aggregate.annualized_return"),
            _finite(development["minimum_annualized_return"], "minimum_annualized_return"),
        ),
        _minimum(
            "development.calmar",
            _finite(aggregate["calmar"], "aggregate.calmar"),
            _finite(development["minimum_calmar"], "minimum_calmar"),
        ),
        _maximum(
            "development.max_drawdown",
            _fraction(aggregate["max_drawdown"], "aggregate.max_drawdown"),
            _fraction(development["maximum_drawdown"], "maximum_drawdown"),
        ),
        _minimum(
            "development.double_cost_sharpe",
            _finite(aggregate["double_cost_sharpe"], "aggregate.double_cost_sharpe"),
            _finite(development["minimum_double_cost_sharpe"], "minimum_double_cost_sharpe"),
        ),
        _minimum(
            "development.positive_quarter_fraction",
            _fraction(
                aggregate["positive_quarter_fraction"], "aggregate.positive_quarter_fraction"
            ),
            _fraction(
                development["minimum_positive_quarter_fraction"],
                "minimum_positive_quarter_fraction",
            ),
        ),
        _minimum(
            "development.trial_adjusted_probability_positive",
            _fraction(
                aggregate["trial_adjusted_probability_positive"],
                "aggregate.trial_adjusted_probability_positive",
            ),
            _fraction(
                development["minimum_trial_adjusted_probability_positive"],
                "minimum_trial_adjusted_probability_positive",
            ),
        ),
    ]

    folds = root["folds"]
    expected_folds = _integer(thresholds["walk_forward_folds"], "walk_forward_folds", minimum=2)
    if (
        not isinstance(folds, Sequence)
        or isinstance(folds, (str, bytes))
        or len(folds) != expected_folds
    ):
        raise ValueError(f"development evidence must contain exactly {expected_folds} folds")
    fold_ids: set[str] = set()
    positive_folds = 0
    for index, raw_fold in enumerate(folds):
        fold = _exact_object(raw_fold, {"fold_id", "net_return"}, f"folds[{index}]")
        fold_id = fold["fold_id"]
        if not isinstance(fold_id, str) or not fold_id or fold_id in fold_ids:
            raise ValueError("fold ids must be non-empty and unique")
        fold_ids.add(fold_id)
        positive_folds += _finite(fold["net_return"], f"folds[{index}].net_return") > 0
    gates.append(
        _minimum(
            "development.positive_folds",
            positive_folds,
            _integer(development["minimum_positive_folds"], "minimum_positive_folds"),
        )
    )

    regimes = _exact_object(root["regimes"], set(_REQUIRED_REGIMES), "regimes")
    regime_metrics: dict[str, tuple[float, float]] = {}
    for regime in _REQUIRED_REGIMES:
        item = _exact_object(
            regimes[regime], {"net_return", "net_sharpe"}, f"regimes.{regime}"
        )
        regime_metrics[regime] = (
            _finite(item["net_return"], f"regimes.{regime}.net_return"),
            _finite(item["net_sharpe"], f"regimes.{regime}.net_sharpe"),
        )
    regime_thresholds = thresholds["regimes"]
    required_positive = regime_thresholds["required_positive_return_regimes"]
    if not isinstance(required_positive, list) or any(
        regime not in _REQUIRED_REGIMES for regime in required_positive
    ):
        raise ValueError("required_positive_return_regimes is invalid")
    for regime in required_positive:
        gates.append(_positive(f"regimes.{regime}.net_return", regime_metrics[regime][0]))
    positive_sharpe_regimes = sum(metrics[1] > 0 for metrics in regime_metrics.values())
    gates.append(
        _minimum(
            "regimes.positive_sharpe_count",
            positive_sharpe_regimes,
            _integer(
                regime_thresholds["minimum_positive_sharpe_regimes"],
                "minimum_positive_sharpe_regimes",
            ),
        )
    )
    gates.append(
        _minimum(
            "regimes.worst_sharpe",
            min(metrics[1] for metrics in regime_metrics.values()),
            _finite(
                regime_thresholds["minimum_worst_regime_sharpe"],
                "minimum_worst_regime_sharpe",
            ),
        )
    )

    roles = _exact_object(
        root["roles"],
        {"long_bull_net_return", "short_bear_net_return", "combined_chop_net_return"},
        "roles",
    )
    for field, enabled_name in (
        ("long_bull_net_return", "require_long_bull_positive"),
        ("short_bear_net_return", "require_short_bear_positive"),
        ("combined_chop_net_return", "require_combined_chop_positive"),
    ):
        if regime_thresholds[enabled_name] is not True:
            raise ValueError(f"{enabled_name} must remain enabled")
        gates.append(_positive(f"roles.{field}", _finite(roles[field], f"roles.{field}")))

    sleeves = _exact_object(root["sleeves"], {"long", "short"}, "sleeves")
    sleeve_thresholds = thresholds["sleeves"]
    for side in ("long", "short"):
        metrics = _exact_object(
            sleeves[side],
            {"active_bar_fraction", "mean_gross_exposure", "executed_notional_usdt"},
            f"sleeves.{side}",
        )
        gates.extend(
            (
                _minimum(
                    f"sleeves.{side}.active_bar_fraction",
                    _fraction(
                        metrics["active_bar_fraction"],
                        f"sleeves.{side}.active_bar_fraction",
                    ),
                    _fraction(
                        sleeve_thresholds["minimum_side_active_bar_fraction"],
                        "minimum_side_active_bar_fraction",
                    ),
                ),
                _minimum(
                    f"sleeves.{side}.mean_gross_exposure",
                    _fraction(
                        metrics["mean_gross_exposure"],
                        f"sleeves.{side}.mean_gross_exposure",
                    ),
                    _fraction(
                        sleeve_thresholds["minimum_mean_side_exposure"],
                        "minimum_mean_side_exposure",
                    ),
                ),
                _minimum(
                    f"sleeves.{side}.executed_notional_usdt",
                    _finite(
                        metrics["executed_notional_usdt"],
                        f"sleeves.{side}.executed_notional_usdt",
                    ),
                    _finite(
                        sleeve_thresholds["minimum_side_executed_notional_usdt"],
                        "minimum_side_executed_notional_usdt",
                    ),
                ),
            )
        )

    stability = _exact_object(
        root["stability"],
        {
            "profitable_neighbor_fraction",
            "neighbor_median_sharpe",
            "maximum_positive_pnl_concentration",
        },
        "stability",
    )
    stability_thresholds = thresholds["stability"]
    gates.extend(
        (
            _minimum(
                "stability.profitable_neighbor_fraction",
                _fraction(
                    stability["profitable_neighbor_fraction"],
                    "stability.profitable_neighbor_fraction",
                ),
                _fraction(
                    stability_thresholds["minimum_profitable_neighbor_fraction"],
                    "minimum_profitable_neighbor_fraction",
                ),
            ),
            _minimum(
                "stability.neighbor_median_sharpe",
                _finite(
                    stability["neighbor_median_sharpe"],
                    "stability.neighbor_median_sharpe",
                ),
                _finite(
                    stability_thresholds["minimum_neighbor_median_sharpe"],
                    "minimum_neighbor_median_sharpe",
                ),
            ),
            _maximum(
                "stability.maximum_positive_pnl_concentration",
                _fraction(
                    stability["maximum_positive_pnl_concentration"],
                    "stability.maximum_positive_pnl_concentration",
                ),
                _fraction(
                    stability_thresholds["maximum_positive_pnl_concentration"],
                    "maximum_positive_pnl_concentration",
                ),
            ),
        )
    )
    return QualificationAssessment(
        schema_version=1,
        stage="development",
        team_id=team_id,
        candidate_id=candidate_id,
        evidence_sha256=evidence_sha256,
        passed=all(gate.passed for gate in gates),
        gates=tuple(gates),
    )


def assess_private(
    evidence: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    *,
    evidence_sha256: str,
) -> QualificationAssessment:
    """Apply the one-shot organizer-only private qualifier."""
    root = _exact_object(
        evidence,
        {
            "schema_version",
            "stage",
            "team_id",
            "candidate_id",
            "strategy_sha256",
            "risk_policy_sha256",
            "config_sha256",
            "trial_count",
            "aggregate",
        },
        "private evidence",
    )
    team_id, candidate_id = _identity(root, "private")
    aggregate = _exact_object(
        root["aggregate"],
        {
            "net_sharpe",
            "annualized_return",
            "max_drawdown",
            "double_cost_sharpe",
            "positive_quarter_fraction",
        },
        "private aggregate",
    )
    private = thresholds["private"]
    gates = (
        _minimum(
            "private.net_sharpe",
            _finite(aggregate["net_sharpe"], "aggregate.net_sharpe"),
            _finite(private["minimum_net_sharpe"], "minimum_net_sharpe"),
        ),
        _greater(
            "private.annualized_return",
            _finite(aggregate["annualized_return"], "aggregate.annualized_return"),
            _finite(private["minimum_annualized_return"], "minimum_annualized_return"),
        ),
        _maximum(
            "private.max_drawdown",
            _fraction(aggregate["max_drawdown"], "aggregate.max_drawdown"),
            _fraction(private["maximum_drawdown"], "maximum_drawdown"),
        ),
        _greater(
            "private.double_cost_sharpe",
            _finite(aggregate["double_cost_sharpe"], "aggregate.double_cost_sharpe"),
            _finite(private["minimum_double_cost_sharpe"], "minimum_double_cost_sharpe"),
        ),
        _minimum(
            "private.positive_quarter_fraction",
            _fraction(
                aggregate["positive_quarter_fraction"], "aggregate.positive_quarter_fraction"
            ),
            _fraction(
                private["minimum_positive_quarter_fraction"],
                "minimum_positive_quarter_fraction",
            ),
        ),
    )
    return QualificationAssessment(
        schema_version=1,
        stage="private",
        team_id=team_id,
        candidate_id=candidate_id,
        evidence_sha256=evidence_sha256,
        passed=all(gate.passed for gate in gates),
        gates=gates,
    )


def assess_qualification_file(
    path: str | Path,
    thresholds: Mapping[str, Any],
    *,
    stage: str,
) -> QualificationAssessment:
    raw, digest = _load_evidence(path)
    if stage == "development":
        return assess_development(raw, thresholds, evidence_sha256=digest)
    if stage == "private":
        return assess_private(raw, thresholds, evidence_sha256=digest)
    raise ValueError("qualification stage must be development or private")
