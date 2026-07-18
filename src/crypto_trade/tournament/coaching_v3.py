"""Deterministic train-only coaching packets for Top-40 V3.

Packets bind a canonical train runner result to one ``CandidateIdentity`` and
reuse the public qualification factory only as a frozen training target.  They
make no validation, readiness, public-qualification, or nomination claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from crypto_trade.tournament.qualification_v3 import (
    PUBLIC_CORE_FLOORS,
    PUBLIC_REGIMES,
    CandidateIdentity,
    MetricCheck,
    assess_public,
)


PACKET_SCHEMA_VERSION = "top40-v3-train-coaching-packet-v1"
TRAIN_SCORE_START = "2020-02-03"
TRAIN_SCORE_END_INCLUSIVE = "2022-06-30"
TRAIN_SEED = 20260718

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_KEY = re.compile(r"[a-z][a-z0-9_]{0,63}")
_RUNNER_KEYS = frozenset(
    {
        "stage",
        "team_id",
        "entrypoint",
        "seeds",
        "data_manifest_sha256",
        "config_sha256",
        "strategy_sha256",
        "risk_policy_sha256",
        "source_bundle_sha256",
        "dependency_lock_sha256",
        "evaluator_sha256",
        "pure_crypto_policy_sha256",
        "pure_crypto_report_sha256",
        "output_dir",
        "scored_window",
        "double_cost_sharpe",
        "regime_sharpe",
        "confidence_intervals",
        "artifacts",
        "artifact_sha256",
        "artifact_sizes",
        "decision_count",
        "event_count",
        "trade_count",
    }
)
_WINDOW_KEYS = frozenset({"start", "end", "metrics"})
_WINDOW_METRIC_KEYS = frozenset(
    {
        "net_sharpe",
        "net_sortino",
        "calmar",
        "annualized_return",
        "max_drawdown",
        "positive_quarter_fraction",
    }
)
_CONFIDENCE_KEYS = frozenset({"net_sharpe_95", "double_cost_sharpe_95"})
_ARTIFACT_KEYS = frozenset(
    {
        "targets",
        "events",
        "positions",
        "evaluator_returns",
        "double_cost_evaluator_returns",
        "daily_returns",
        "double_cost_daily_returns",
        "trades",
    }
)
_IDENTITY_BINDINGS = {
    "source_bundle_sha256": "source_bundle_sha256",
    "strategy_sha256": "strategy_sha256",
    "dependency_lock_sha256": "dependency_lock_sha256",
    "config_sha256": "config_sha256",
    "risk_policy_sha256": "risk_policy_sha256",
    "data_manifest_sha256": "data_authority_sha256",
    "evaluator_sha256": "evaluator_sha256",
}
_FLOOR_ORDER = (
    "net_sharpe",
    "annualized_return",
    "max_drawdown",
    "double_cost_sharpe",
    "positive_quarter_fraction",
    "trade_count",
    "positive_regime_count",
    "worst_regime_sharpe",
)
_ACTION_BY_GAP = {
    "net_sharpe": "alpha_sign_or_horizon",
    "annualized_return": "alpha_sign_or_horizon",
    "max_drawdown": "drawdown_risk_control",
    "double_cost_sharpe": "turnover_cost_control",
    "positive_quarter_fraction": "quarter_breadth",
    "trade_count": "execution_breadth",
    "positive_regime_count": "regime_repair",
    "worst_regime_sharpe": "regime_repair",
}


def canonical_packet_bytes(packet: Mapping[str, object]) -> bytes:
    """Return the canonical ASCII JSON bytes used for packet hashing."""

    if not isinstance(packet, Mapping):
        raise ValueError("packet must be a mapping")
    try:
        return json.dumps(
            packet,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ValueError("packet is not finite JSON-safe data") from exc


def packet_sha256(packet: Mapping[str, object]) -> str:
    """Hash a packet's canonical bytes without mutating the packet."""

    return hashlib.sha256(canonical_packet_bytes(packet)).hexdigest()


def _exact_mapping(raw: object, keys: frozenset[str], label: str) -> Mapping[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != set(keys):
        raise ValueError(f"{label} must contain exactly the frozen keys")
    return raw


def _finite(raw: object, label: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def _fraction(raw: object, label: str) -> float:
    value = _finite(raw, label)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be in [0,1]")
    return value


def _count(raw: object, label: str, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return raw


def _sha256(raw: object, label: str) -> str:
    if not isinstance(raw, str) or _SHA256.fullmatch(raw) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return raw


def _safe_relative_path(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError(f"{label} must be a POSIX relative path")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or path.as_posix() != raw
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{label} must be a normalized POSIX relative path")
    return raw


def _runner_mapping(result: object) -> Mapping[str, object]:
    if isinstance(result, Mapping):
        return _exact_mapping(result, _RUNNER_KEYS, "runner result")

    # Lazy import avoids making the coach an import-time dependency of the runner.
    from crypto_trade.tournament.runner_v3 import TeamWindowRunResult

    if type(result) is not TeamWindowRunResult:
        raise ValueError("result must be TeamWindowRunResult or its exact organizer mapping")
    return _exact_mapping(result.organizer_fields(), _RUNNER_KEYS, "runner result")


def _validate_identity_bindings(
    runner: Mapping[str, object], identity: CandidateIdentity
) -> None:
    if type(identity) is not CandidateIdentity:
        raise ValueError("identity must be an exact CandidateIdentity")
    if runner["team_id"] != identity.team_id:
        raise ValueError("runner team_id does not match candidate identity")
    for runner_field, identity_field in _IDENTITY_BINDINGS.items():
        observed = _sha256(runner[runner_field], runner_field)
        if observed != getattr(identity, identity_field):
            raise ValueError(f"runner {runner_field} does not match candidate identity")


def _validate_interval(raw: object, label: str) -> list[float]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise ValueError(f"{label} must be an exact two-value interval")
    lower = _finite(raw[0], f"{label}.lower")
    upper = _finite(raw[1], f"{label}.upper")
    if lower > upper:
        raise ValueError(f"{label} bounds are reversed")
    return [lower, upper]


def _normalize_runner_result(
    result: object, identity: CandidateIdentity
) -> dict[str, object]:
    runner = _runner_mapping(result)
    _validate_identity_bindings(runner, identity)
    if runner["stage"] != "train":
        raise ValueError("coaching packets require stage=train")

    team_id = identity.team_id
    entrypoint = _safe_relative_path(runner["entrypoint"], "entrypoint")
    entrypoint_prefix = f"tournament/top40-v3/teams/{team_id}/"
    if not entrypoint.startswith(entrypoint_prefix):
        raise ValueError("entrypoint is not bound to the result team")

    seeds = runner["seeds"]
    if (
        not isinstance(seeds, list)
        or len(seeds) != 1
        or isinstance(seeds[0], bool)
        or seeds[0] != TRAIN_SEED
    ):
        raise ValueError("train runner result must bind the frozen singleton seed")

    output_dir = _safe_relative_path(runner["output_dir"], "output_dir")
    output_prefix = f"reports-top40-v3/labs/{team_id}/"
    if not output_dir.startswith(output_prefix):
        raise ValueError("train output_dir is outside the team's lab namespace")

    window = _exact_mapping(runner["scored_window"], _WINDOW_KEYS, "scored_window")
    if window["start"] != TRAIN_SCORE_START or window["end"] != TRAIN_SCORE_END_INCLUSIVE:
        raise ValueError("scored_window is not the frozen V3 train window")
    metric_raw = _exact_mapping(window["metrics"], _WINDOW_METRIC_KEYS, "window metrics")
    window_metrics = {
        "net_sharpe": _finite(metric_raw["net_sharpe"], "net_sharpe"),
        "net_sortino": _finite(metric_raw["net_sortino"], "net_sortino"),
        "calmar": _finite(metric_raw["calmar"], "calmar"),
        "annualized_return": _finite(
            metric_raw["annualized_return"], "annualized_return"
        ),
        "max_drawdown": _fraction(metric_raw["max_drawdown"], "max_drawdown"),
        "positive_quarter_fraction": _fraction(
            metric_raw["positive_quarter_fraction"],
            "positive_quarter_fraction",
        ),
    }
    double_cost_sharpe = _finite(runner["double_cost_sharpe"], "double_cost_sharpe")

    regime_raw = _exact_mapping(
        runner["regime_sharpe"], frozenset(PUBLIC_REGIMES), "regime_sharpe"
    )
    regime_sharpe = {
        regime: _finite(regime_raw[regime], f"regime_sharpe.{regime}")
        for regime in PUBLIC_REGIMES
    }

    confidence_raw = _exact_mapping(
        runner["confidence_intervals"], _CONFIDENCE_KEYS, "confidence_intervals"
    )
    confidence_intervals = {
        "net_sharpe_95": _validate_interval(
            confidence_raw["net_sharpe_95"], "net_sharpe_95"
        ),
        "double_cost_sharpe_95": _validate_interval(
            confidence_raw["double_cost_sharpe_95"], "double_cost_sharpe_95"
        ),
    }

    artifacts_raw = _exact_mapping(runner["artifacts"], _ARTIFACT_KEYS, "artifacts")
    artifact_hash_raw = _exact_mapping(
        runner["artifact_sha256"], _ARTIFACT_KEYS, "artifact_sha256"
    )
    artifact_size_raw = _exact_mapping(
        runner["artifact_sizes"], _ARTIFACT_KEYS, "artifact_sizes"
    )
    artifacts: dict[str, str] = {}
    artifact_sha256: dict[str, str] = {}
    artifact_sizes: dict[str, int] = {}
    for name in sorted(_ARTIFACT_KEYS):
        if _SAFE_KEY.fullmatch(name) is None:
            raise AssertionError("frozen artifact key is unsafe")
        artifact_path = _safe_relative_path(artifacts_raw[name], f"artifacts.{name}")
        if not artifact_path.startswith(f"{output_dir}/"):
            raise ValueError(f"artifact {name} is outside output_dir")
        artifacts[name] = artifact_path
        artifact_sha256[name] = _sha256(
            artifact_hash_raw[name], f"artifact_sha256.{name}"
        )
        artifact_sizes[name] = _count(
            artifact_size_raw[name], f"artifact_sizes.{name}"
        )

    decision_count = _count(runner["decision_count"], "decision_count", positive=True)
    event_count = _count(runner["event_count"], "event_count")
    trade_count = _count(runner["trade_count"], "trade_count")
    if trade_count > event_count:
        raise ValueError("trade_count cannot exceed event_count")

    runner_hashes = {
        field: _sha256(runner[field], field)
        for field in (
            "data_manifest_sha256",
            "config_sha256",
            "strategy_sha256",
            "risk_policy_sha256",
            "source_bundle_sha256",
            "dependency_lock_sha256",
            "evaluator_sha256",
            "pure_crypto_policy_sha256",
            "pure_crypto_report_sha256",
        )
    }
    return {
        "entrypoint": entrypoint,
        "seeds": [TRAIN_SEED],
        "output_dir": output_dir,
        "runner_hashes": runner_hashes,
        "scored_window": {
            "start": TRAIN_SCORE_START,
            "end": TRAIN_SCORE_END_INCLUSIVE,
            "metrics": window_metrics,
        },
        "double_cost_sharpe": double_cost_sharpe,
        "regime_sharpe": regime_sharpe,
        "confidence_intervals": confidence_intervals,
        "counts": {
            "decision_count": decision_count,
            "event_count": event_count,
            "trade_count": trade_count,
        },
        "artifacts": {
            "paths": artifacts,
            "sha256": artifact_sha256,
            "sizes": artifact_sizes,
        },
    }


def _normalized_shortfall(check: MetricCheck) -> float:
    """Return the frozen directional miss divided by ``abs(floor)`` (or one).

    Passed floors are exactly zero.  A failed strict ``>`` floor adds one so
    equality remains a visible gap instead of normalizing to zero.
    """

    if check.passed:
        return 0.0
    observed = float(check.observed)
    threshold = float(check.threshold)
    scale = abs(threshold) if abs(threshold) > 0.0 else 1.0
    if check.operator == ">=":
        shortfall = (threshold - observed) / scale
    elif check.operator == "<=":
        shortfall = (observed - threshold) / scale
    elif check.operator == ">":
        # A strict boundary failure must remain an open gap at equality.
        shortfall = 1.0 + (threshold - observed) / scale
    else:  # pragma: no cover - qualification owns the frozen operator vector
        raise ValueError("qualification returned an unknown core-floor operator")
    if not math.isfinite(shortfall) or shortfall <= 0.0:
        raise ValueError("qualification returned a non-positive failed-floor shortfall")
    return float(shortfall)


def _identity_packet(identity: CandidateIdentity) -> dict[str, str]:
    return {
        "team_id": identity.team_id,
        "candidate_id": identity.candidate_id,
        "candidate_identity_sha256": identity.sha256,
        "source_bundle_sha256": identity.source_bundle_sha256,
        "strategy_sha256": identity.strategy_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "config_sha256": identity.config_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "data_authority_sha256": identity.data_authority_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
    }


def build_training_metric_packet(
    result: object,
    identity: CandidateIdentity,
) -> dict[str, object]:
    """Build one canonical JSON-safe train coaching packet.

    ``result`` may be an exact ``runner_v3.TeamWindowRunResult`` or the exact
    mapping returned by its ``organizer_fields`` method.
    """

    normalized = _normalize_runner_result(result, identity)
    metrics = normalized["scored_window"]["metrics"]
    public_metrics = {
        "net_sharpe": metrics["net_sharpe"],
        "annualized_return": metrics["annualized_return"],
        "max_drawdown": metrics["max_drawdown"],
        "double_cost_sharpe": normalized["double_cost_sharpe"],
        "positive_quarter_fraction": metrics["positive_quarter_fraction"],
        "trade_count": normalized["counts"]["trade_count"],
        "regime_sharpe": normalized["regime_sharpe"],
    }
    assessment = assess_public(
        identity,
        public_metrics,
        reproducible=True,
        data_authority=True,
        universe_compliant=True,
        causal=True,
        execution_compliant=True,
        solvent=True,
        window_complete=True,
    )

    checks: list[dict[str, object]] = []
    open_gaps: list[dict[str, object]] = []
    order = {name: index for index, name in enumerate(_FLOOR_ORDER)}
    if tuple(check.name for check in assessment.core_checks) != _FLOOR_ORDER:
        raise ValueError("qualification public core-floor order changed")
    if set(PUBLIC_CORE_FLOORS) != set(_FLOOR_ORDER):
        raise ValueError("qualification public core-floor authority changed")

    for check in assessment.core_checks:
        shortfall = _normalized_shortfall(check)
        check_packet = {
            "name": check.name,
            "observed": check.observed,
            "operator": check.operator,
            "threshold": check.threshold,
            "passed": check.passed,
            "normalized_shortfall": shortfall,
            "next_action_code": None if check.passed else _ACTION_BY_GAP[check.name],
        }
        checks.append(check_packet)
        if not check.passed:
            open_gaps.append(
                {
                    "name": check.name,
                    "normalized_shortfall": shortfall,
                    "next_action_code": _ACTION_BY_GAP[check.name],
                }
            )

    open_gaps.sort(
        key=lambda gap: (-float(gap["normalized_shortfall"]), order[str(gap["name"])])
    )
    public_core_passed = all(check.passed for check in assessment.core_checks)
    red = (
        assessment.net_sharpe <= 0.0
        or assessment.annualized_return <= 0.0
        or assessment.double_cost_sharpe <= 0.0
    )
    training_status = "RED" if red else "GREEN" if public_core_passed else "AMBER"

    packet: dict[str, object] = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_kind": "train_coaching_metric_packet",
        "stage": "train",
        "identity": _identity_packet(identity),
        "runner": {
            "entrypoint": normalized["entrypoint"],
            "seeds": normalized["seeds"],
            "output_dir": normalized["output_dir"],
            "hashes": normalized["runner_hashes"],
        },
        "scored_window": normalized["scored_window"],
        "double_cost_sharpe": normalized["double_cost_sharpe"],
        "regime_sharpe": normalized["regime_sharpe"],
        "confidence_intervals": normalized["confidence_intervals"],
        "counts": normalized["counts"],
        "artifacts": normalized["artifacts"],
        "training_assessment": {
            "status": training_status,
            "public_core_is_train_target_only": True,
            "public_core_train_target_passed": public_core_passed,
            "core_floor_checks": checks,
            "largest_open_gaps": open_gaps[:2],
            "mandatory_action_codes": (
                ["sign_inversion_cost_audit"] if training_status == "RED" else []
            ),
            "robustness_score": assessment.robustness_score,
            "robustness_score_changes_status": False,
        },
        "train_only_lifecycle": {
            "validation_status": "unknown",
            "readiness": False,
            "nomination": False,
        },
    }
    # Enforce JSON safety now rather than deferring failure to persistence.
    canonical_packet_bytes(packet)
    return packet


__all__ = [
    "PACKET_SCHEMA_VERSION",
    "TRAIN_SCORE_END_INCLUSIVE",
    "TRAIN_SCORE_START",
    "TRAIN_SEED",
    "build_training_metric_packet",
    "canonical_packet_bytes",
    "packet_sha256",
]
