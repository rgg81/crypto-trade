"""Validation and scoring contract for the ten-team Top-40 tournament.

The score is deliberately cohort-relative.  It always identifies the best valid frozen
submission, while hard disqualification is reserved for measurement-integrity failures.  A
separate, pre-registered paper-eligibility rule prevents the tournament rank from being confused
with permission to risk capital.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

IS_START = "2020-02-03"
IS_END = "2024-06-30"
OOS_START = "2024-07-01"
OOS_END = "2026-06-30"

MIN_SIDE_EXPOSURE = 0.01
MIN_SIDE_ACTIVE_BAR_FRACTION = 0.05
MIN_MEAN_SIDE_EXPOSURE = 0.005
MIN_SIDE_EXECUTED_NOTIONAL_USDT = 1_000.0

REQUIRED_REGIMES = frozenset({"bull", "bear", "chop", "stress"})
REQUIRED_CONFIDENCE_INTERVALS = frozenset(
    {
        "is_net_sharpe_95",
        "public_oos_net_sharpe_95",
        "double_cost_oos_net_sharpe_95",
    }
)
EVALUATOR_SOURCE_PATHS = (
    "src/crypto_trade/__init__.py",
    "src/crypto_trade/tournament/__init__.py",
    "src/crypto_trade/tournament/data.py",
    "src/crypto_trade/tournament/engine.py",
    "src/crypto_trade/tournament/metrics.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/runner.py",
    "src/crypto_trade/tournament/_strategy_worker.py",
    "src/crypto_trade/tournament/top40.py",
)
HARD_COMPLIANCE_CHECKS = (
    "public_binance_only",
    "point_in_time_top40",
    "closed_data_only",
    "next_bar_execution",
    "fees_and_slippage_charged",
    "funding_cashflows_charged",
    "long_and_short_enabled",
    "double_cost_rerun",
    "corrupt_future_test",
    "append_invariance_test",
    "deterministic_rerun",
)

CANONICAL_CONFIG_PATH = "tournament/top40/config.toml"
CANONICAL_MANIFEST_PATH = "tournament/top40/data_manifest.json"
PHASE0_FREEZE_PATH = "tournament/top40/phase0_freeze.json"
RUN_STATE_PATH = "tournament/top40/run_state.json"
PHASE0_POLICY_PATH = "tournament/top40/PHASE0-POLICY.md"
CRITIC_SCORES_PATH = "tournament/top40/critic_scores.json"
CRITIC_ADJUDICATIONS_PATH = "tournament/top40/critic_adjudications.json"
CRITIC_LOCK_PATH = "tournament/top40/critic_lock.json"
OBJECTIVE_LOCK_PATH = "tournament/top40/objective_lock.json"
CRITIC_CONFIRMATIONS_PATH = "tournament/top40/critic_confirmations.json"
CRITIC_CONFIRMATION_LOCK_PATH = "tournament/top40/critic_confirmation_lock.json"
USER_SCORES_PATH = "tournament/top40/user_scores.json"
USER_BALLOT_LOCK_PATH = "tournament/top40/user_ballot_lock.json"
FINAL_SCORE_PATH = "tournament/top40/leaderboard.json"
WINNER_FREEZE_PATH = "tournament/top40/winner_freeze.json"
ROOT_DEPENDENCY_LOCK_PATH = "uv.lock"
ORCHESTRATOR_SCRIPT_PATH = "scripts/top40_tournament.py"
TOURNAMENT_BRANCH = "quant-portfolio-blind-top40"
RUN_PHASES = (
    "research",
    "cohort_frozen",
    "objective_locked",
    "critic_locked",
    "dq_confirmed",
    "user_locked",
    "paper_frozen",
)
CRITIC_INTEGRITY_DQ_CODES = frozenset(
    {
        "critic_evaluator_tampering",
        "critic_false_provenance",
        "critic_future_data",
        "critic_future_membership",
        "critic_missing_costs",
        "critic_non_binance_input",
        "critic_omitted_funding",
        "critic_post_freeze_mutation",
        "critic_same_bar_leakage",
        "critic_wrong_funding_sign",
        "critic_failed_deterministic_rerun",
    }
)
METHODOLOGY_PATHS = (
    "TOURNAMENT-CHARTER-TOP40.md",
    ".claude/agents/top40-quant-engineer.md",
    ".claude/agents/top40-quant-researcher.md",
    ".claude/agents/top40-tournament-critic.md",
    ".claude/commands/top40-tournament.md",
    "tournament/top40/PHASE0-POLICY.md",
    "tournament/top40/METHODOLOGY-DISTILLATION.md",
    "tournament/top40/templates/experiment-event.schema.json",
    "tournament/top40/templates/critic-adjudications.json",
    "tournament/top40/templates/submission.json",
)

REQUIRED_ARTIFACTS = frozenset(
    {
        "artifact_manifest",
        "ablations",
        "audit_report",
        "btc_daily_returns",
        "compliance_evidence",
        "daily_returns",
        "data_manifest",
        "dependency_lock",
        "double_cost_daily_returns",
        "double_cost_evaluator_returns",
        "events",
        "evaluator_returns",
        "frozen_config",
        "feature_lineage",
        "positions",
        "provenance",
        "reproduce_command",
        "research_brief",
        "strategy_source",
        "targets",
        "team_source_manifest",
        "trades",
        "trial_ledger",
    }
)

_FROZEN_TEAM_ARTIFACTS = frozenset(
    {
        "audit_report",
        "ablations",
        "compliance_evidence",
        "dependency_lock",
        "feature_lineage",
        "frozen_config",
        "provenance",
        "research_brief",
        "strategy_source",
        "team_source_manifest",
        "trial_ledger",
    }
)

# Seventy points are deterministic.  The Critic and user each contribute fifteen points.
AUTOMATED_WEIGHTS: dict[str, float] = {
    "oos_net_sharpe": 12.0,
    "oos_net_sortino": 4.0,
    "oos_calmar": 5.0,
    "oos_annualized_return": 3.0,
    "oos_max_drawdown": 4.0,
    "is_net_sharpe": 5.0,
    "is_calmar": 3.0,
    "generalization_coherence": 7.0,
    "positive_quarter_fraction": 5.0,
    "worst_regime_sharpe": 8.0,
    "positive_regime_fraction": 4.0,
    "double_cost_sharpe": 7.0,
    "cost_sharpe_retention": 3.0,
}
assert math.isclose(sum(AUTOMATED_WEIGHTS.values()), 70.0)


@dataclasses.dataclass(frozen=True)
class WindowMetrics:
    net_sharpe: float
    net_sortino: float
    calmar: float
    annualized_return: float
    max_drawdown: float
    positive_quarter_fraction: float


@dataclasses.dataclass(frozen=True)
class EvaluationWindow:
    start: str
    end: str
    metrics: WindowMetrics


@dataclasses.dataclass(frozen=True)
class Submission:
    team_id: str
    strategy_name: str
    freeze_commit: str
    data_manifest_sha256: str
    evaluator_sha256: str
    config_sha256: str
    strategy_sha256: str
    dependency_lock_sha256: str
    artifact_manifest_sha256: str
    entrypoint: str
    seeds: tuple[int, ...]
    trial_count: int
    in_sample: EvaluationWindow
    public_oos: EvaluationWindow
    double_cost_oos_sharpe: float
    regime_sharpe: Mapping[str, float]
    confidence_intervals: Mapping[str, tuple[float, float]]
    compliance: Mapping[str, bool]
    artifacts: Mapping[str, str]


@dataclasses.dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    disqualifying: bool = True


@dataclasses.dataclass(frozen=True)
class TeamScore:
    team_id: str
    valid: bool
    rank: int | None
    objective_rank: int | None
    automatic_score: float | None
    critic_score: float | None
    user_score: float | None
    total_score: float | None
    paper_eligible: bool
    disqualification_reasons: tuple[str, ...] = ()


def canonical_artifact_paths(team_id: str) -> dict[str, str]:
    """Return the only artifact namespace accepted for a canonical team run."""
    team_root = f"tournament/top40/teams/{team_id}"
    report_root = f"reports-top40/{team_id}"
    return {
        "artifact_manifest": f"{team_root}/artifact_manifest.json",
        "ablations": f"{team_root}/ablations.json",
        "audit_report": f"{team_root}/qe_report.md",
        "btc_daily_returns": "reports-top40/common/btc_daily_returns.csv",
        "compliance_evidence": f"{team_root}/compliance.json",
        "daily_returns": f"{report_root}/daily_returns.csv",
        "data_manifest": CANONICAL_MANIFEST_PATH,
        "dependency_lock": f"{team_root}/uv.lock",
        "double_cost_daily_returns": f"{report_root}/double_cost_daily_returns.csv",
        "double_cost_evaluator_returns": f"{report_root}/double_cost_bar_returns.csv",
        "events": f"{report_root}/events.parquet",
        "evaluator_returns": f"{report_root}/bar_returns.csv",
        "frozen_config": f"{team_root}/frozen_config.json",
        "feature_lineage": f"{team_root}/feature_lineage.json",
        "positions": f"{report_root}/positions.parquet",
        "provenance": f"{team_root}/provenance.md",
        "reproduce_command": (
            "uv run python scripts/top40_tournament.py validate "
            f"tournament/top40/teams/{team_id}/submission.json"
        ),
        "research_brief": f"{team_root}/research_brief.md",
        "strategy_source": f"{team_root}/strategy.py",
        "team_source_manifest": f"{team_root}/team_source_manifest.json",
        "targets": f"{report_root}/targets.parquet",
        "trades": f"{report_root}/trades.csv",
        "trial_ledger": f"{team_root}/experiments.jsonl",
    }


def _finite_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _metrics(raw: Mapping[str, Any], prefix: str) -> WindowMetrics:
    return WindowMetrics(
        net_sharpe=_finite_float(raw["net_sharpe"], f"{prefix}.net_sharpe"),
        net_sortino=_finite_float(raw["net_sortino"], f"{prefix}.net_sortino"),
        calmar=_finite_float(raw["calmar"], f"{prefix}.calmar"),
        annualized_return=_finite_float(raw["annualized_return"], f"{prefix}.annualized_return"),
        max_drawdown=_finite_float(raw["max_drawdown"], f"{prefix}.max_drawdown"),
        positive_quarter_fraction=_finite_float(
            raw["positive_quarter_fraction"], f"{prefix}.positive_quarter_fraction"
        ),
    )


def _window(raw: Mapping[str, Any], prefix: str) -> EvaluationWindow:
    return EvaluationWindow(
        start=str(raw["start"]),
        end=str(raw["end"]),
        metrics=_metrics(raw["metrics"], f"{prefix}.metrics"),
    )


def submission_from_dict(raw: Mapping[str, Any]) -> Submission:
    """Parse a submission dictionary, rejecting missing or malformed scalar fields."""
    try:
        regimes = {
            str(name): _finite_float(value, f"regime_sharpe.{name}")
            for name, value in raw["regime_sharpe"].items()
        }
        compliance = raw["compliance"]
        if not isinstance(compliance, dict) or any(
            not isinstance(value, bool) for value in compliance.values()
        ):
            raise ValueError("compliance values must be JSON booleans")
        seeds = tuple(int(seed) for seed in raw["seeds"])
        confidence_intervals = {
            str(name): (
                _finite_float(bounds[0], f"confidence_intervals.{name}[0]"),
                _finite_float(bounds[1], f"confidence_intervals.{name}[1]"),
            )
            for name, bounds in raw["confidence_intervals"].items()
        }
        artifacts = raw["artifacts"]
        if not isinstance(artifacts, dict) or any(
            not isinstance(name, str) or not isinstance(value, str)
            for name, value in artifacts.items()
        ):
            raise ValueError("artifacts must map string names to string paths/commands")
        return Submission(
            team_id=str(raw["team_id"]),
            strategy_name=str(raw["strategy_name"]),
            freeze_commit=str(raw["freeze_commit"]),
            data_manifest_sha256=str(raw["data_manifest_sha256"]),
            evaluator_sha256=str(raw["evaluator_sha256"]),
            config_sha256=str(raw["config_sha256"]),
            strategy_sha256=str(raw["strategy_sha256"]),
            dependency_lock_sha256=str(raw["dependency_lock_sha256"]),
            artifact_manifest_sha256=str(raw["artifact_manifest_sha256"]),
            entrypoint=str(raw["entrypoint"]),
            seeds=seeds,
            trial_count=int(raw["trial_count"]),
            in_sample=_window(raw["in_sample"], "in_sample"),
            public_oos=_window(raw["public_oos"], "public_oos"),
            double_cost_oos_sharpe=_finite_float(
                raw["double_cost_oos_sharpe"], "double_cost_oos_sharpe"
            ),
            regime_sharpe=regimes,
            confidence_intervals=confidence_intervals,
            compliance={str(k): v for k, v in compliance.items()},
            artifacts=dict(artifacts),
        )
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid tournament submission: {exc}") from exc


def load_submission(path: str | Path) -> Submission:
    """Load one frozen submission JSON file."""
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError("submission root must be a JSON object")
    return submission_from_dict(raw)


def validate_submission(submission: Submission) -> tuple[ValidationIssue, ...]:
    """Return every contract violation; only integrity failures are disqualifying."""
    issues: list[ValidationIssue] = []
    if not re.fullmatch(r"team-(?:0[1-9]|10)", submission.team_id):
        issues.append(ValidationIssue("team_id", "team_id must be team-01 through team-10"))
    if not submission.strategy_name.strip():
        issues.append(ValidationIssue("strategy_name", "strategy_name cannot be blank"))
    if not re.fullmatch(r"[0-9a-f]{7,40}", submission.freeze_commit):
        issues.append(ValidationIssue("freeze_commit", "freeze_commit must be a Git SHA"))
    if not re.fullmatch(r"[0-9a-f]{64}", submission.data_manifest_sha256):
        issues.append(
            ValidationIssue("data_manifest", "data_manifest_sha256 must be 64 lowercase hex chars")
        )
    for field_name in (
        "evaluator_sha256",
        "config_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "artifact_manifest_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", getattr(submission, field_name)):
            issues.append(
                ValidationIssue(field_name, f"{field_name} must be 64 lowercase hex chars")
            )
    team_root = f"tournament/top40/teams/{submission.team_id}/"
    if (
        not _safe_relative_path(submission.entrypoint)
        or not submission.entrypoint.startswith(team_root)
        or not submission.entrypoint.endswith(".py")
    ):
        issues.append(
            ValidationIssue("entrypoint", f"entrypoint must be a Python file under {team_root}")
        )
    if not submission.seeds or len(submission.seeds) != len(set(submission.seeds)):
        issues.append(ValidationIssue("seeds", "seeds must be a non-empty unique integer list"))
    if submission.trial_count < 1:
        issues.append(
            ValidationIssue("trial_count", "trial_count must include every attempted run")
        )

    expected_windows = (
        ("in_sample", submission.in_sample, IS_START, IS_END),
        ("public_oos", submission.public_oos, OOS_START, OOS_END),
    )
    for name, window, expected_start, expected_end in expected_windows:
        if (window.start, window.end) != (expected_start, expected_end):
            issues.append(
                ValidationIssue(
                    f"{name}_window",
                    f"{name} must cover {expected_start} through {expected_end}",
                )
            )
        metrics = window.metrics
        if not 0.0 <= metrics.max_drawdown <= 1.0:
            issues.append(
                ValidationIssue(
                    f"{name}_max_drawdown",
                    "max_drawdown must be a magnitude in [0, 1]",
                )
            )
        if not 0.0 <= metrics.positive_quarter_fraction <= 1.0:
            issues.append(
                ValidationIssue(f"{name}_quarters", "positive_quarter_fraction must be in [0, 1]")
            )
        if metrics.annualized_return < -1.0:
            issues.append(
                ValidationIssue(f"{name}_return", "annualized_return cannot be below -100%")
            )

    missing_regimes = REQUIRED_REGIMES - set(submission.regime_sharpe)
    extra_regimes = set(submission.regime_sharpe) - REQUIRED_REGIMES
    if missing_regimes or extra_regimes:
        issues.append(
            ValidationIssue(
                "regimes",
                f"regime_sharpe must contain exactly {sorted(REQUIRED_REGIMES)}; "
                f"missing={sorted(missing_regimes)}, extra={sorted(extra_regimes)}",
            )
        )
    missing_intervals = REQUIRED_CONFIDENCE_INTERVALS - set(submission.confidence_intervals)
    extra_intervals = set(submission.confidence_intervals) - REQUIRED_CONFIDENCE_INTERVALS
    if missing_intervals or extra_intervals:
        issues.append(
            ValidationIssue(
                "confidence_intervals",
                "confidence_intervals must contain exactly "
                f"{sorted(REQUIRED_CONFIDENCE_INTERVALS)}",
            )
        )
    for name, (lower, upper) in submission.confidence_intervals.items():
        if lower > upper:
            issues.append(
                ValidationIssue(f"confidence_intervals.{name}", "lower bound exceeds upper")
            )

    for check in HARD_COMPLIANCE_CHECKS:
        if submission.compliance.get(check) is not True:
            issues.append(ValidationIssue(check, f"hard compliance check failed: {check}"))

    missing_artifacts = REQUIRED_ARTIFACTS - set(submission.artifacts)
    extra_artifacts = set(submission.artifacts) - REQUIRED_ARTIFACTS
    if missing_artifacts:
        issues.append(
            ValidationIssue("artifacts", f"missing required artifacts: {sorted(missing_artifacts)}")
        )
    if extra_artifacts:
        issues.append(
            ValidationIssue("artifacts", f"unexpected artifacts: {sorted(extra_artifacts)}")
        )
    for name, value in submission.artifacts.items():
        if not value.strip():
            issues.append(ValidationIssue(f"artifacts.{name}", "artifact value cannot be blank"))
        if name != "reproduce_command" and not _safe_relative_path(value):
            issues.append(
                ValidationIssue(
                    f"artifacts.{name}",
                    "artifact path must be relative and cannot contain parent traversal",
                )
            )
        if name == "btc_daily_returns" and value != "reports-top40/common/btc_daily_returns.csv":
            issues.append(
                ValidationIssue(
                    "artifacts.btc_daily_returns",
                    "all teams must use reports-top40/common/btc_daily_returns.csv",
                )
            )
        if (
            name
            not in {
                "btc_daily_returns",
                "data_manifest",
                "reproduce_command",
            }
            and not value.startswith(team_root)
            and not value.startswith(f"reports-top40/{submission.team_id}/")
        ):
            issues.append(
                ValidationIssue(
                    f"artifacts.{name}",
                    f"artifact must stay in the {submission.team_id} namespace",
                )
            )
    expected_artifacts = canonical_artifact_paths(submission.team_id)
    for name, expected in expected_artifacts.items():
        reported = submission.artifacts.get(name)
        if reported is not None and reported != expected:
            issues.append(
                ValidationIssue(
                    f"artifacts.{name}",
                    f"canonical artifact must be {expected}",
                )
            )
    if submission.artifacts.get("strategy_source") != submission.entrypoint:
        issues.append(ValidationIssue("strategy_source", "strategy_source must equal entrypoint"))
    if submission.artifacts.get("data_manifest") != "tournament/top40/data_manifest.json":
        issues.append(
            ValidationIssue(
                "data_manifest",
                "all teams must use tournament/top40/data_manifest.json",
            )
        )
    return tuple(issues)


def verify_phase0_freeze(*, root: str | Path) -> tuple[ValidationIssue, ...]:
    """Verify the live common evaluator/data bytes against the Phase-0 freeze.

    The function reports common tournament faults to its caller.  CLI validation and scoring
    treat any returned issue as a tournament-level abort, never as ten team disqualifications.
    """
    from crypto_trade.tournament.data import sha256_manifest
    from crypto_trade.tournament.snapshot import verify_snapshot_manifest

    root_path = Path(root).resolve()
    issues: list[ValidationIssue] = []
    freeze = _read_json_object(root_path / PHASE0_FREEZE_PATH, "phase0_freeze", issues)
    state = _read_json_object(root_path / RUN_STATE_PATH, "run_state", issues)
    if freeze is None or state is None:
        return tuple(issues)

    issues.extend(_validate_run_state_phase(state))
    try:
        frozen_at = pd.Timestamp(freeze["frozen_at_utc"])
        if frozen_at.tzinfo is None or frozen_at.utcoffset() != pd.Timedelta(0):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        issues.append(
            ValidationIssue("frozen_at_utc", "Phase-0 freeze timestamp must be timezone-aware UTC")
        )
    common_commit = freeze.get("common_freeze_commit")
    if not isinstance(common_commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", common_commit):
        issues.append(
            ValidationIssue("common_freeze_commit", "Phase-0 common freeze commit is invalid")
        )
        common_commit = None

    frozen_branch = freeze.get("branch")
    if frozen_branch != TOURNAMENT_BRANCH:
        issues.append(ValidationIssue("branch", f"Phase-0 branch must be {TOURNAMENT_BRANCH}"))
    branch_result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root_path,
        check=False,
        capture_output=True,
        text=True,
    )
    if branch_result.returncode != 0 or branch_result.stdout.strip() != TOURNAMENT_BRANCH:
        issues.append(ValidationIssue("branch", f"current branch must remain {TOURNAMENT_BRANCH}"))

    for field in (
        "common_freeze_commit",
        "data_manifest_sha256",
        "evaluator_sha256",
        "methodology_sha256",
        "config_sha256",
        "orchestrator_sha256",
    ):
        if state.get(field) != freeze.get(field):
            issues.append(
                ValidationIssue(
                    f"run_state.{field}",
                    f"run_state {field} differs from phase0_freeze.json",
                )
            )

    manifest_path = root_path / CANONICAL_MANIFEST_PATH
    config_path = root_path / CANONICAL_CONFIG_PATH
    policy_path = root_path / PHASE0_POLICY_PATH
    root_lock_path = root_path / ROOT_DEPENDENCY_LOCK_PATH
    orchestrator_path = root_path / ORCHESTRATOR_SCRIPT_PATH
    manifest: dict[str, Any] | None = None
    try:
        manifest = verify_snapshot_manifest(manifest_path)
    except (OSError, TypeError, ValueError) as exc:
        issues.append(ValidationIssue("snapshot_manifest", str(exc)))

    current_hashes: dict[str, str] = {}
    for field, path in (
        ("data_manifest_sha256", manifest_path),
        ("config_sha256", config_path),
        ("phase0_policy_sha256", policy_path),
        ("root_dependency_lock_sha256", root_lock_path),
        ("orchestrator_sha256", orchestrator_path),
    ):
        if not path.is_file() or path.is_symlink():
            issues.append(ValidationIssue(field, f"frozen common file is missing/unsafe: {path}"))
        else:
            current_hashes[field] = _sha256_file(path)

    evaluator_paths = [root_path / relative for relative in EVALUATOR_SOURCE_PATHS]
    if any(not path.is_file() or path.is_symlink() for path in evaluator_paths):
        issues.append(
            ValidationIssue("evaluator_sha256", "evaluator source file is missing/unsafe")
        )
    else:
        current_hashes["evaluator_sha256"] = sha256_manifest(evaluator_paths, root=root_path)[0]

    methodology_paths = [root_path / relative for relative in METHODOLOGY_PATHS]
    if any(not path.is_file() or path.is_symlink() for path in methodology_paths):
        issues.append(
            ValidationIssue("methodology_sha256", "team-visible methodology file is missing/unsafe")
        )
    else:
        current_hashes["methodology_sha256"] = sha256_manifest(methodology_paths, root=root_path)[0]

    frozen_git_paths = [
        CANONICAL_MANIFEST_PATH,
        CANONICAL_CONFIG_PATH,
        PHASE0_POLICY_PATH,
        ROOT_DEPENDENCY_LOCK_PATH,
        ORCHESTRATOR_SCRIPT_PATH,
        *EVALUATOR_SOURCE_PATHS,
        *METHODOLOGY_PATHS,
    ]
    if manifest is not None:
        files = manifest.get("files", [])
        logical = {
            entry.get("name"): entry
            for entry in files
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        }
        expected_btc = {
            "btc_daily_returns": (
                "btc_daily_returns_sha256",
                "reports-top40/common/btc_daily_returns.csv",
            ),
            "btc_regimes": (
                "btc_regimes_sha256",
                "reports-top40/common/btc_regimes.csv",
            ),
        }
        for logical_name, (field, expected_path) in expected_btc.items():
            entry = logical.get(logical_name)
            if not isinstance(entry, dict) or entry.get("path") != expected_path:
                issues.append(
                    ValidationIssue(field, f"manifest {logical_name} path must be {expected_path}")
                )
                continue
            current_hashes[field] = str(entry.get("sha256", ""))
            frozen_git_paths.append(expected_path)

        sources = manifest.get("sources")
        if not isinstance(sources, dict):
            issues.append(ValidationIssue("snapshot_builder_sha256", "manifest sources missing"))
        else:
            builder_relative = sources.get("builder_path")
            expected_builder = "src/crypto_trade/tournament/snapshot.py"
            if builder_relative != expected_builder:
                issues.append(
                    ValidationIssue(
                        "snapshot_builder_sha256",
                        f"snapshot builder path must be {expected_builder}",
                    )
                )
            else:
                builder_path = root_path / expected_builder
                if not builder_path.is_file() or builder_path.is_symlink():
                    issues.append(
                        ValidationIssue(
                            "snapshot_builder_sha256", "snapshot builder is missing/unsafe"
                        )
                    )
                else:
                    current_hashes["snapshot_builder_sha256"] = _sha256_file(builder_path)
                    frozen_git_paths.append(expected_builder)
                if sources.get("builder_sha256") != freeze.get("snapshot_builder_sha256"):
                    issues.append(
                        ValidationIssue(
                            "snapshot_builder_sha256",
                            "manifest builder hash differs from phase0_freeze.json",
                        )
                    )

    for field, current in current_hashes.items():
        frozen = freeze.get(field)
        if not isinstance(frozen, str) or current != frozen:
            issues.append(
                ValidationIssue(field, f"current {field} differs from phase0_freeze.json")
            )

    if not (root_path / ".git").exists():
        issues.append(
            ValidationIssue("common_freeze_commit", "tournament root is not a Git worktree")
        )
    elif common_commit is not None:
        issues.extend(
            _verify_git_frozen_files(
                root_path,
                common_commit,
                frozen_git_paths,
                issue_code="common_freeze_commit",
            )
        )
        record_commit = _phase0_record_commit(root_path, common_commit, issues)
        if record_commit is not None:
            record_ancestor = subprocess.run(
                ["git", "merge-base", "--is-ancestor", common_commit, record_commit],
                cwd=root_path,
                check=False,
                capture_output=True,
            )
            if record_ancestor.returncode != 0 or record_commit == common_commit:
                issues.append(
                    ValidationIssue(
                        "phase0_record_commit",
                        "Phase-0 record commit must be a later descendant of the common commit",
                    )
                )
    return tuple(issues)


def verify_team_freeze(
    team_id: str,
    freeze_commit: str,
    entrypoint: str,
    artifacts: Mapping[str, str],
    *,
    root: str | Path,
) -> tuple[ValidationIssue, ...]:
    """Verify every executable and audit input against one team's Git freeze commit."""
    root_path = Path(root).resolve()
    issues: list[ValidationIssue] = []
    if not re.fullmatch(r"team-(?:0[1-9]|10)", team_id):
        return (ValidationIssue("team_id", "team_id must be team-01 through team-10"),)
    if not (root_path / ".git").exists():
        return (ValidationIssue("freeze_commit", "tournament root is not a Git worktree"),)
    if not re.fullmatch(r"[0-9a-f]{7,40}", freeze_commit):
        return (ValidationIssue("freeze_commit", "freeze_commit must be a Git SHA"),)

    expected = canonical_artifact_paths(team_id)
    if entrypoint != expected["strategy_source"]:
        issues.append(
            ValidationIssue(
                "entrypoint", f"frozen entrypoint must be {expected['strategy_source']}"
            )
        )
    frozen_paths: list[str] = []
    for name in sorted(_FROZEN_TEAM_ARTIFACTS):
        relative = artifacts.get(name)
        if relative is None:
            issues.append(ValidationIssue(f"artifacts.{name}", "frozen artifact is missing"))
        elif relative != expected[name]:
            issues.append(
                ValidationIssue(f"artifacts.{name}", f"frozen artifact must be {expected[name]}")
            )
        else:
            frozen_paths.append(relative)

    team_lock = artifacts.get("dependency_lock")
    root_lock = root_path / ROOT_DEPENDENCY_LOCK_PATH
    if team_lock is not None:
        team_lock_path = root_path / team_lock
        if (
            not team_lock_path.is_file()
            or team_lock_path.is_symlink()
            or not root_lock.is_file()
            or root_lock.is_symlink()
        ):
            issues.append(
                ValidationIssue(
                    "dependency_lock_sha256",
                    "root/team dependency lock is missing/unsafe",
                )
            )
        elif team_lock_path.read_bytes() != root_lock.read_bytes():
            issues.append(
                ValidationIssue(
                    "dependency_lock_sha256", "team uv.lock must be byte-identical to root uv.lock"
                )
            )

    team_prefix = f"tournament/top40/teams/{team_id}"
    mutable_outputs = {
        f"{team_prefix}/artifact_manifest.json",
        f"{team_prefix}/submission.json",
    }
    current_files: set[str] = set()
    team_path = root_path / team_prefix
    if team_path.is_dir() and not team_path.is_symlink():
        for path in team_path.rglob("*"):
            relative = path.relative_to(root_path).as_posix()
            relative_path = PurePosixPath(relative)
            if "__pycache__" in relative_path.parts or relative_path.suffix == ".pyc":
                issues.append(
                    ValidationIssue(
                        "team_bundle", f"generated Python cache must be absent: {relative}"
                    )
                )
            elif path.is_symlink():
                issues.append(
                    ValidationIssue("team_bundle", f"team symlink is forbidden: {relative}")
                )
            elif path.is_dir():
                continue
            elif not path.is_file() or not path.resolve().is_relative_to(team_path):
                issues.append(ValidationIssue("team_bundle", f"non-regular team path: {relative}"))
            elif relative not in mutable_outputs:
                current_files.add(relative)
    else:
        issues.append(
            ValidationIssue("team_bundle", f"team namespace is missing/unsafe: {team_prefix}")
        )

    committed_files = _git_team_file_paths(
        root_path,
        freeze_commit,
        team_prefix,
        mutable_outputs,
        issues,
    )
    if current_files != committed_files:
        issues.append(
            ValidationIssue(
                "team_bundle",
                "working and frozen team file sets differ: "
                f"working_only={sorted(current_files - committed_files)}, "
                f"frozen_only={sorted(committed_files - current_files)}",
            )
        )
    source_manifest = artifacts.get("team_source_manifest")
    if isinstance(source_manifest, str):
        issues.extend(
            _verify_team_source_manifest(
                root_path,
                team_id,
                freeze_commit,
                source_manifest,
                mutable_outputs,
            )
        )
    frozen_paths.extend(sorted(current_files))
    issues.extend(
        _verify_git_frozen_files(
            root_path,
            freeze_commit,
            sorted(set(frozen_paths)),
            issue_code="freeze_commit",
        )
    )

    phase0 = _read_json_object(root_path / PHASE0_FREEZE_PATH, "phase0_freeze", issues)
    common_commit = phase0.get("common_freeze_commit") if phase0 is not None else None
    if isinstance(common_commit, str):
        record_commit = _phase0_record_commit(root_path, common_commit, issues)
        required_ancestor = record_commit or common_commit
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", required_ancestor, freeze_commit],
            cwd=root_path,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            issues.append(
                ValidationIssue(
                    "freeze_commit",
                    "team freeze commit does not descend from the Phase-0 record commit",
                )
            )
        elif record_commit is not None:
            frozen_phase0 = subprocess.run(
                ["git", "show", f"{freeze_commit}:{PHASE0_FREEZE_PATH}"],
                cwd=root_path,
                check=False,
                capture_output=True,
            )
            if (
                frozen_phase0.returncode != 0
                or frozen_phase0.stdout != (root_path / PHASE0_FREEZE_PATH).read_bytes()
            ):
                issues.append(
                    ValidationIssue(
                        "freeze_commit",
                        "team freeze does not contain the identical Phase-0 record bytes",
                    )
                )
    return tuple(issues)


def verify_canonical_artifacts(
    submission: Submission, *, root: str | Path
) -> tuple[ValidationIssue, ...]:
    """Recompute every scored metric from canonical daily-return artifacts.

    The official leaderboard CLI calls this after structural validation.  It prevents a team from
    gaining rank by editing scalar metrics in ``submission.json`` while leaving evaluator outputs
    unchanged.
    """
    from crypto_trade.tournament.data import sha256_manifest
    from crypto_trade.tournament.metrics import (
        aggregate_daily_returns,
        classify_btc_regimes,
        compute_regime_sharpes,
        compute_window_metrics,
        sharpe_confidence_interval,
    )

    issues: list[ValidationIssue] = []
    root_path = Path(root).resolve()
    missing_artifacts = REQUIRED_ARTIFACTS - set(submission.artifacts)
    if missing_artifacts:
        return (
            ValidationIssue(
                "artifacts", f"missing required artifacts: {sorted(missing_artifacts)}"
            ),
        )
    artifact_manifest = submission.artifacts.get("artifact_manifest")
    if artifact_manifest is None or not _safe_relative_path(artifact_manifest):
        return (
            ValidationIssue(
                "artifact_manifest",
                "artifact manifest path must be safe and relative to the tournament root",
            ),
        )
    if (root_path / ".git").exists():
        issues.extend(
            verify_team_freeze(
                submission.team_id,
                submission.freeze_commit,
                submission.entrypoint,
                submission.artifacts,
                root=root_path,
            )
        )
        if issues:
            return tuple(issues)
    artifact_paths: list[Path] = []
    for name, artifact in submission.artifacts.items():
        if name in {"artifact_manifest", "reproduce_command"}:
            continue
        path = (root_path / artifact).resolve()
        if not path.is_relative_to(root_path):
            issues.append(
                ValidationIssue(f"artifacts.{name}", f"artifact path escapes root: {artifact}")
            )
        elif not path.is_file():
            issues.append(
                ValidationIssue(f"artifacts.{name}", f"artifact file does not exist: {artifact}")
            )
        else:
            artifact_paths.append(path)
    if issues:
        return tuple(issues)
    computed_manifest_sha, manifest_entries = sha256_manifest(artifact_paths, root=root_path)
    if computed_manifest_sha != submission.artifact_manifest_sha256:
        issues.append(
            ValidationIssue(
                "artifact_manifest_sha256",
                f"reported {submission.artifact_manifest_sha256} != canonical "
                f"{computed_manifest_sha}",
            )
        )
    manifest_path = (root_path / artifact_manifest).resolve()
    if not manifest_path.is_file():
        issues.append(ValidationIssue("artifact_manifest", "artifact manifest JSON does not exist"))
    else:
        try:
            with manifest_path.open(encoding="utf-8") as handle:
                reported_entries = json.load(handle)
            if reported_entries != manifest_entries:
                issues.append(
                    ValidationIssue(
                        "artifact_manifest", "artifact manifest entries do not match files"
                    )
                )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(ValidationIssue("artifact_manifest", str(exc)))
    if issues:
        return tuple(issues)
    config_path = root_path / "tournament/top40/config.toml"
    if not config_path.is_file():
        return (ValidationIssue("config_sha256", "common config file is missing"),)
    hash_checks = {
        "strategy_sha256": _sha256_file(root_path / submission.entrypoint),
        "dependency_lock_sha256": _sha256_file(root_path / submission.artifacts["dependency_lock"]),
        "config_sha256": _sha256_file(config_path),
        "data_manifest_sha256": _sha256_file(root_path / submission.artifacts["data_manifest"]),
    }
    evaluator_paths = [root_path / path for path in EVALUATOR_SOURCE_PATHS]
    if any(not path.is_file() for path in evaluator_paths):
        issues.append(ValidationIssue("evaluator_sha256", "evaluator source file is missing"))
    else:
        hash_checks["evaluator_sha256"] = sha256_manifest(evaluator_paths, root=root_path)[0]
    for field_name, computed_hash in hash_checks.items():
        reported_hash = getattr(submission, field_name)
        if reported_hash != computed_hash:
            issues.append(
                ValidationIssue(
                    field_name,
                    f"reported {reported_hash} != canonical {computed_hash}",
                )
            )
    if issues:
        return tuple(issues)
    try:
        base = _read_daily_artifact(
            submission.artifacts["daily_returns"], root=root, value_column="net_return"
        )
        stressed = _read_daily_artifact(
            submission.artifacts["double_cost_daily_returns"],
            root=root,
            value_column="net_return",
        )
        btc = _read_daily_artifact(
            submission.artifacts["btc_daily_returns"], root=root, value_column="btc_return"
        )
        base_bar_frame = _read_return_frame(
            submission.artifacts["evaluator_returns"], root=root, require_side_attribution=True
        )
        base_bars = base_bar_frame["net_return"]
        stressed_bars = _read_return_frame(
            submission.artifacts["double_cost_evaluator_returns"],
            root=root,
            require_side_attribution=False,
        )["net_return"]
        targets = _read_targets_artifact(submission.artifacts["targets"], root=root)
        trades = _read_trades_artifact(submission.artifacts["trades"], root=root)
    except (KeyError, OSError, ValueError) as exc:
        return (ValidationIssue("canonical_artifacts", str(exc)),)

    for window_name, window_targets in (
        ("in_sample", targets.loc[IS_START:IS_END]),
        ("public_oos", targets.loc[OOS_START:OOS_END]),
    ):
        values = window_targets.to_numpy()
        if not (values > 1e-10).any() or not (values < -1e-10).any():
            issues.append(
                ValidationIssue(
                    "long_and_short_enabled",
                    f"{window_name} must contain nontrivial positive and negative targets",
                )
            )
    for window_name, start, end in (
        ("in_sample", IS_START, IS_END),
        ("public_oos", OOS_START, OOS_END),
    ):
        bars = base_bar_frame.loc[start:end]
        window_trades = trades.loc[start:end]
        for side in ("long", "short"):
            exposure = bars[f"{side}_exposure"]
            active_fraction = float((exposure >= MIN_SIDE_EXPOSURE).mean())
            mean_exposure = float(exposure.mean())
            if (
                active_fraction < MIN_SIDE_ACTIVE_BAR_FRACTION
                or mean_exposure < MIN_MEAN_SIDE_EXPOSURE
            ):
                issues.append(
                    ValidationIssue(
                        "long_and_short_enabled",
                        f"{window_name} {side} realized exposure is immaterial: "
                        f"active_fraction={active_fraction:.6f}, mean={mean_exposure:.6f}",
                    )
                )
        bought = float(window_trades["notional"].clip(lower=0.0).sum())
        sold = float(-window_trades["notional"].clip(upper=0.0).sum())
        if min(bought, sold) < MIN_SIDE_EXECUTED_NOTIONAL_USDT:
            issues.append(
                ValidationIssue(
                    "long_and_short_enabled",
                    f"{window_name} requires at least {MIN_SIDE_EXECUTED_NOTIONAL_USDT:.0f} USDT "
                    f"of executed buy and sell notional; observed buy={bought:.6f}, "
                    f"sell={sold:.6f}",
                )
            )
    if issues:
        return tuple(issues)

    expected_start = pd.Timestamp(IS_START, tz="UTC")
    expected_end = pd.Timestamp(OOS_END, tz="UTC")
    for name, series in (("daily_returns", base), ("double_cost_daily_returns", stressed)):
        expected_index = pd.date_range(expected_start, expected_end, freq="1D", tz="UTC")
        if not series.index.equals(expected_index):
            issues.append(
                ValidationIssue(
                    name,
                    f"{name} must contain exactly one row for every UTC date "
                    f"from {IS_START} through {OOS_END}",
                )
            )
    if not btc.index.equals(base.index):
        issues.append(
            ValidationIssue("btc_daily_returns", "BTC dates must exactly match base return dates")
        )
    derived_base = aggregate_daily_returns(base_bars).reindex(base.index, fill_value=0.0)
    derived_stressed = aggregate_daily_returns(stressed_bars).reindex(
        stressed.index, fill_value=0.0
    )
    expected_bar_index = pd.date_range(
        pd.Timestamp(IS_START, tz="UTC"),
        pd.Timestamp(OOS_END, tz="UTC") + pd.Timedelta(hours=16),
        freq="8h",
    )
    for name, series in (
        ("evaluator_returns", base_bars),
        ("double_cost_evaluator_returns", stressed_bars),
    ):
        if not series.index.equals(expected_bar_index):
            issues.append(
                ValidationIssue(
                    name,
                    f"{name} must contain every canonical 8h timestamp across both windows",
                )
            )
    if not np.allclose(base.to_numpy(), derived_base.to_numpy(), rtol=1e-12, atol=1e-12):
        issues.append(
            ValidationIssue(
                "daily_returns",
                "daily_returns do not compound from canonical evaluator bar returns",
            )
        )
    if not np.allclose(stressed.to_numpy(), derived_stressed.to_numpy(), rtol=1e-12, atol=1e-12):
        issues.append(
            ValidationIssue(
                "double_cost_daily_returns",
                "double-cost daily returns do not compound from evaluator bar returns",
            )
        )
    if issues:
        return tuple(issues)

    is_returns = base.loc[IS_START:IS_END]
    oos_returns = base.loc[OOS_START:OOS_END]
    stress_oos = stressed.loc[OOS_START:OOS_END]
    computed_is = compute_window_metrics(is_returns)
    computed_oos = compute_window_metrics(oos_returns)
    computed_stress_sharpe = compute_window_metrics(stress_oos).net_sharpe
    labels = classify_btc_regimes(btc).loc[OOS_START:OOS_END]
    computed_regimes = compute_regime_sharpes(oos_returns, labels)
    computed_intervals = {
        "is_net_sharpe_95": sharpe_confidence_interval(is_returns),
        "public_oos_net_sharpe_95": sharpe_confidence_interval(oos_returns),
        "double_cost_oos_net_sharpe_95": sharpe_confidence_interval(stress_oos),
    }

    for prefix, reported, computed in (
        ("in_sample", submission.in_sample.metrics, computed_is),
        ("public_oos", submission.public_oos.metrics, computed_oos),
    ):
        for field in dataclasses.fields(WindowMetrics):
            reported_value = getattr(reported, field.name)
            computed_value = getattr(computed, field.name)
            if not math.isclose(reported_value, computed_value, rel_tol=1e-9, abs_tol=1e-9):
                issues.append(
                    ValidationIssue(
                        f"{prefix}.{field.name}",
                        f"reported {reported_value} != canonical {computed_value}",
                    )
                )
    if not math.isclose(
        submission.double_cost_oos_sharpe,
        computed_stress_sharpe,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        issues.append(
            ValidationIssue(
                "double_cost_oos_sharpe",
                f"reported {submission.double_cost_oos_sharpe} != canonical "
                f"{computed_stress_sharpe}",
            )
        )
    for regime, computed_value in computed_regimes.items():
        reported_value = submission.regime_sharpe[regime]
        if not math.isclose(reported_value, computed_value, rel_tol=1e-9, abs_tol=1e-9):
            issues.append(
                ValidationIssue(
                    f"regime_sharpe.{regime}",
                    f"reported {reported_value} != canonical {computed_value}",
                )
            )
    for name, computed_bounds in computed_intervals.items():
        reported_bounds = submission.confidence_intervals[name]
        if any(
            not math.isclose(reported, computed, rel_tol=1e-9, abs_tol=1e-9)
            for reported, computed in zip(reported_bounds, computed_bounds, strict=True)
        ):
            issues.append(
                ValidationIssue(
                    f"confidence_intervals.{name}",
                    f"reported {reported_bounds} != canonical {computed_bounds}",
                )
            )
    return tuple(issues)


def _read_daily_artifact(artifact: str, *, root: str | Path, value_column: str) -> pd.Series:
    import pandas as pd

    root_path = Path(root).resolve()
    path = (root_path / artifact).resolve()
    if not path.is_relative_to(root_path):
        raise ValueError(f"artifact path escapes tournament root: {artifact}")
    frame = pd.read_csv(path)
    required = {"date", value_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{artifact} missing columns: {sorted(missing)}")
    dates = pd.to_datetime(frame["date"], utc=True)
    if dates.duplicated().any():
        raise ValueError(f"{artifact} contains duplicate dates")
    values = pd.to_numeric(frame[value_column], errors="raise")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError(f"{artifact} contains non-finite values")
    return pd.Series(values.to_numpy(), index=dates, name=value_column).sort_index()


def _read_return_frame(
    artifact: str, *, root: str | Path, require_side_attribution: bool
) -> pd.DataFrame:
    root_path = Path(root).resolve()
    path = (root_path / artifact).resolve()
    if not path.is_relative_to(root_path):
        raise ValueError(f"artifact path escapes tournament root: {artifact}")
    frame = pd.read_csv(path)
    required = {"timestamp", "net_return", "price_pnl", "funding_pnl", "fees", "slippage"}
    if require_side_attribution:
        required |= {
            "long_price_pnl",
            "short_price_pnl",
            "long_funding_pnl",
            "short_funding_pnl",
            "long_exposure",
            "short_exposure",
        }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{artifact} missing columns: {sorted(missing)}")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True)
    if timestamps.duplicated().any() or timestamps.isna().any():
        raise ValueError(f"{artifact} contains duplicate or invalid timestamps")
    numeric = frame.loc[:, sorted(required - {"timestamp"})].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{artifact} contains non-finite returns")
    reconciled = (
        numeric["price_pnl"] + numeric["funding_pnl"] - numeric["fees"] - numeric["slippage"]
    )
    if not np.allclose(numeric["net_return"], reconciled, rtol=1e-12, atol=1e-12):
        raise ValueError(f"{artifact} net returns do not reconcile to PnL and costs")
    if require_side_attribution:
        if not np.allclose(
            numeric["long_price_pnl"] + numeric["short_price_pnl"],
            numeric["price_pnl"],
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"{artifact} long/short price PnL attribution does not reconcile")
        if not np.allclose(
            numeric["long_funding_pnl"] + numeric["short_funding_pnl"],
            numeric["funding_pnl"],
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"{artifact} long/short funding attribution does not reconcile")
        if (numeric[["long_exposure", "short_exposure"]] < -1e-12).any().any():
            raise ValueError(f"{artifact} side exposures must be non-negative")
    numeric.index = timestamps
    numeric.index.name = "timestamp"
    return numeric.sort_index()


def _read_return_artifact(artifact: str, *, root: str | Path) -> pd.Series:
    return _read_return_frame(artifact, root=root, require_side_attribution=False)["net_return"]


def _read_trades_artifact(artifact: str, *, root: str | Path) -> pd.DataFrame:
    root_path = Path(root).resolve()
    path = (root_path / artifact).resolve()
    if not path.is_relative_to(root_path):
        raise ValueError(f"artifact path escapes tournament root: {artifact}")
    frame = pd.read_csv(path)
    required = {"timestamp", "event_type", "notional"}
    missing = required - set(frame)
    if missing:
        raise ValueError(f"{artifact} missing columns: {sorted(missing)}")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    notionals = pd.to_numeric(frame["notional"], errors="raise")
    if timestamps.isna().any() or not np.isfinite(notionals.to_numpy()).all():
        raise ValueError(f"{artifact} contains invalid trade timestamps/notionals")
    allowed = {"trade", "risk_reduction", "forced_exit"}
    if not frame["event_type"].isin(allowed).all():
        raise ValueError(f"{artifact} contains non-execution events")
    result = pd.DataFrame(
        {
            "event_type": frame["event_type"].astype(str).to_numpy(),
            "notional": notionals.to_numpy(),
        },
        index=timestamps,
    )
    result.index.name = "timestamp"
    return result.sort_index(kind="mergesort")


def _read_targets_artifact(artifact: str, *, root: str | Path) -> pd.DataFrame:
    root_path = Path(root).resolve()
    path = (root_path / artifact).resolve()
    if not path.is_relative_to(root_path):
        raise ValueError(f"artifact path escapes tournament root: {artifact}")
    frame = pd.read_parquet(path)
    if (
        "timestamp" not in frame.columns
        or REBALANCE_INSTRUCTION_COLUMN not in frame.columns
        or len(frame.columns) < 3
    ):
        raise ValueError(
            f"{artifact} must contain timestamp, Boolean rebalance instructions, "
            "and symbol target columns"
        )
    timestamps = pd.to_datetime(frame.pop("timestamp"), utc=True, errors="raise")
    if timestamps.duplicated().any() or timestamps.isna().any():
        raise ValueError(f"{artifact} contains duplicate or invalid timestamps")
    instructions = frame.pop(REBALANCE_INSTRUCTION_COLUMN)
    if instructions.isna().any() or not pd.api.types.is_bool_dtype(instructions.dtype):
        raise ValueError(f"{artifact} rebalance instructions must be Boolean")
    numeric = frame.apply(pd.to_numeric, errors="raise")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{artifact} contains non-finite targets")
    numeric.index = timestamps
    numeric = numeric.sort_index()
    expected = pd.date_range(
        pd.Timestamp(IS_START, tz="UTC"),
        pd.Timestamp(OOS_END, tz="UTC") + pd.Timedelta(hours=16),
        freq="8h",
    )
    if not numeric.index.equals(expected):
        raise ValueError(f"{artifact} must contain the exact canonical 8h target grid")
    return numeric


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


_TEAM_TEXT_SUFFIXES = frozenset(
    {".py", ".md", ".json", ".jsonl", ".toml", ".lock", ".txt", ".yaml", ".yml"}
)
TEAM_SOURCE_POLICY = "source-text-config-only-no-timestamp-target-lookups"
_LITERAL_DATE_TARGET = re.compile(
    r"(?is)(?:20\d{2}-\d{2}-\d{2}.{0,200}(?:target|weight|position|signal)|"
    r"(?:target|weight|position|signal).{0,200}20\d{2}-\d{2}-\d{2})"
)


def _timestamp_target_structure(value: object) -> bool:
    if isinstance(value, dict):
        lowered = {str(key).lower() for key in value}
        has_time = any(key in lowered for key in {"timestamp", "timestamp_utc", "date", "time"})
        has_target = any(
            any(token in key for token in ("target", "weight", "position", "signal"))
            for key in lowered
        )
        if has_time and has_target:
            return True
        for key, nested in value.items():
            if re.fullmatch(r"20\d{2}-\d{2}-\d{2}(?:[T ].*)?", str(key)) and isinstance(
                nested, (dict, list, int, float)
            ):
                return True
            if _timestamp_target_structure(nested):
                return True
    elif isinstance(value, list):
        return any(_timestamp_target_structure(item) for item in value)
    return False


def _verify_team_source_manifest(
    root: Path,
    team_id: str,
    freeze_commit: str,
    manifest_relative: str,
    mutable_outputs: set[str],
) -> list[ValidationIssue]:
    """Bind every non-self frozen team file and reject opaque/precomputed executable state."""
    issues: list[ValidationIssue] = []
    team_prefix = f"tournament/top40/teams/{team_id}"
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", freeze_commit, "--", team_prefix],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if listing.returncode != 0:
        return [ValidationIssue("team_source_manifest", "cannot inspect frozen team Git tree")]
    entries: list[dict[str, object]] = []
    total_size = 0
    for raw in listing.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split()
            relative = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            issues.append(ValidationIssue("team_source_manifest", "invalid frozen Git tree entry"))
            continue
        if relative in mutable_outputs or relative == manifest_relative:
            continue
        if kind != "blob" or mode != "100644":
            issues.append(
                ValidationIssue(
                    "team_source_manifest",
                    f"only non-executable regular source/text files are allowed: {relative}",
                )
            )
            continue
        content = subprocess.run(
            ["git", "cat-file", "blob", oid],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if content.returncode != 0:
            issues.append(
                ValidationIssue("team_source_manifest", f"cannot read frozen blob: {relative}")
            )
            continue
        suffix = PurePosixPath(relative).suffix.lower()
        if suffix not in _TEAM_TEXT_SUFFIXES:
            issues.append(
                ValidationIssue(
                    "team_source_manifest",
                    f"opaque/prefit file type is forbidden in canonical team tree: {relative}",
                )
            )
            continue
        try:
            text = content.stdout.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(
                ValidationIssue(
                    "team_source_manifest", f"canonical team file is not UTF-8 text: {relative}"
                )
            )
            continue
        size = len(content.stdout)
        total_size += size
        if size > 2 * 1024 * 1024:
            issues.append(
                ValidationIssue(
                    "team_source_manifest", f"canonical team text file exceeds 2 MiB: {relative}"
                )
            )
        if suffix in {".py", ".toml", ".yaml", ".yml"} and _LITERAL_DATE_TARGET.search(text):
            issues.append(
                ValidationIssue(
                    "team_source_manifest",
                    f"literal timestamp-to-target/weight logic is forbidden: {relative}",
                )
            )
        if suffix == ".json":
            try:
                parsed_json = json.loads(text)
            except json.JSONDecodeError:
                issues.append(
                    ValidationIssue("team_source_manifest", f"invalid JSON source: {relative}")
                )
            else:
                if _timestamp_target_structure(parsed_json):
                    issues.append(
                        ValidationIssue(
                            "team_source_manifest",
                            f"timestamp-keyed target/weight table is forbidden: {relative}",
                        )
                    )
        elif suffix == ".jsonl":
            try:
                rows = [json.loads(line) for line in text.splitlines() if line]
            except json.JSONDecodeError:
                issues.append(
                    ValidationIssue("team_source_manifest", f"invalid JSONL source: {relative}")
                )
            else:
                if any(_timestamp_target_structure(row) for row in rows):
                    issues.append(
                        ValidationIssue(
                            "team_source_manifest",
                            f"timestamp-keyed target/weight table is forbidden: {relative}",
                        )
                    )
        entries.append(
            {
                "path": relative,
                "git_mode": mode,
                "git_blob_oid": oid,
                "size": size,
                "sha256": hashlib.sha256(content.stdout).hexdigest(),
            }
        )
    if total_size > 10 * 1024 * 1024:
        issues.append(
            ValidationIssue("team_source_manifest", "canonical team source tree exceeds 10 MiB")
        )
    expected = {
        "schema_version": 1,
        "team_id": team_id,
        "prefit_state_policy": TEAM_SOURCE_POLICY,
        "entries": sorted(entries, key=lambda entry: str(entry["path"])),
    }
    path = root / manifest_relative
    try:
        observed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(ValidationIssue("team_source_manifest", f"invalid manifest JSON: {exc}"))
    else:
        if observed != expected:
            issues.append(
                ValidationIssue(
                    "team_source_manifest",
                    "team source manifest differs from the complete frozen Git tree",
                )
            )
    return issues


def _read_json_object(
    path: Path,
    label: str,
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(ValidationIssue(label, f"invalid {label} JSON: {exc}"))
        return None
    if not isinstance(raw, dict):
        issues.append(ValidationIssue(label, f"{label} must be a JSON object"))
        return None
    return raw


def _validate_run_state_phase(state: Mapping[str, Any]) -> list[ValidationIssue]:
    """Enforce the one-way lifecycle implied by the organizer-owned team records."""
    issues: list[ValidationIssue] = []
    phase = state.get("phase")
    if phase not in RUN_PHASES:
        return [
            ValidationIssue(
                "run_state.phase",
                f"run_state phase must be one of {list(RUN_PHASES)} after Phase-0",
            )
        ]
    teams = state.get("teams")
    expected = {f"team-{number:02d}" for number in range(1, 11)}
    if not isinstance(teams, dict) or set(teams) != expected:
        return [
            ValidationIssue(
                "run_state.teams", "run_state must contain exactly team-01 through team-10"
            )
        ]

    champion_count = 0
    completed_count = 0
    for team_id in sorted(expected):
        team = teams[team_id]
        if not isinstance(team, dict):
            issues.append(
                ValidationIssue(f"run_state.{team_id}", "team state must be a JSON object")
            )
            continue
        champion = team.get("champion")
        canonical = team.get("canonical_run")
        if champion is not None and not isinstance(champion, dict):
            issues.append(
                ValidationIssue(
                    f"run_state.{team_id}.champion",
                    "champion must be null or a frozen champion record",
                )
            )
        elif isinstance(champion, dict):
            champion_count += 1
        if canonical == "complete":
            completed_count += 1
            if not isinstance(champion, dict):
                issues.append(
                    ValidationIssue(
                        f"run_state.{team_id}.canonical_run",
                        "a canonical run cannot complete before its champion is frozen",
                    )
                )
        elif canonical not in {"pending", "running", "failed"}:
            issues.append(
                ValidationIssue(
                    f"run_state.{team_id}.canonical_run",
                    "canonical_run has an invalid status",
                )
            )

    if phase == "research" and (champion_count >= 10 or completed_count != 0):
        issues.append(
            ValidationIssue(
                "run_state.phase",
                "research phase requires fewer than ten champions and no canonical completions",
            )
        )
    elif phase == "cohort_frozen" and (champion_count != 10 or completed_count >= 10):
        issues.append(
            ValidationIssue(
                "run_state.phase",
                "cohort_frozen requires ten champions and fewer than ten completed reruns",
            )
        )
    elif phase in {
        "objective_locked",
        "critic_locked",
        "dq_confirmed",
        "user_locked",
        "paper_frozen",
    } and (champion_count != 10 or completed_count != 10):
        issues.append(
            ValidationIssue(
                "run_state.phase",
                f"{phase} requires ten frozen and canonically completed champions",
            )
        )
    if phase in {
        "objective_locked",
        "critic_locked",
        "dq_confirmed",
        "user_locked",
        "paper_frozen",
    }:
        objective_lock = state.get("objective_lock")
        if not isinstance(objective_lock, dict) or set(objective_lock) != {
            "path",
            "sha256",
            "cohort_sha256",
            "locked_at_utc",
        }:
            issues.append(
                ValidationIssue(
                    "run_state.objective_lock",
                    f"{phase} requires the complete immutable objective-lock record",
                )
            )
    if phase in {"critic_locked", "dq_confirmed", "user_locked", "paper_frozen"}:
        critic_lock = state.get("critic_lock")
        if not isinstance(critic_lock, dict) or set(critic_lock) != {
            "path",
            "sha256",
            "cohort_sha256",
            "locked_at_utc",
        }:
            issues.append(
                ValidationIssue(
                    "run_state.critic_lock",
                    "critic_locked phase requires the complete immutable Critic lock record",
                )
            )
    if phase in {"dq_confirmed", "user_locked", "paper_frozen"}:
        confirmation_lock = state.get("critic_confirmation_lock")
        if not isinstance(confirmation_lock, dict) or set(confirmation_lock) != {
            "path",
            "sha256",
            "cohort_sha256",
            "locked_at_utc",
        }:
            issues.append(
                ValidationIssue(
                    "run_state.critic_confirmation_lock",
                    f"{phase} requires the complete independent DQ-confirmation lock",
                )
            )
    if phase in {"user_locked", "paper_frozen"}:
        user_lock = state.get("user_ballot_lock")
        if not isinstance(user_lock, dict) or set(user_lock) != {
            "path",
            "sha256",
            "locked_at_utc",
        }:
            issues.append(
                ValidationIssue(
                    "run_state.user_ballot_lock",
                    f"{phase} requires the complete immutable user-ballot lock",
                )
            )
    if phase == "paper_frozen":
        winner_freeze = state.get("winner_freeze")
        if not isinstance(winner_freeze, dict) or set(winner_freeze) != {
            "path",
            "sha256",
            "winner_team_id",
            "winner_freeze_commit",
            "selection_record_commit",
            "frozen_at_utc",
            "forward_paper_start_utc",
        }:
            issues.append(
                ValidationIssue(
                    "run_state.winner_freeze",
                    "paper_frozen phase requires the complete immutable winner-freeze record",
                )
            )
    return issues


def _phase0_record_commit(
    root: Path,
    common_commit: str,
    issues: list[ValidationIssue],
) -> str | None:
    """Return the unique first-add record commit whose sole parent is the common freeze."""
    freeze_path = root / PHASE0_FREEZE_PATH
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", PHASE0_FREEZE_PATH],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout.strip():
        issues.append(
            ValidationIssue(
                "phase0_record_commit",
                "phase0_freeze.json must be tracked, committed, and clean",
            )
        )
        return None
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", PHASE0_FREEZE_PATH],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    commits = [line for line in log.stdout.splitlines() if line]
    if log.returncode != 0 or len(commits) != 1 or not re.fullmatch(r"[0-9a-f]{40,64}", commits[0]):
        issues.append(
            ValidationIssue(
                "phase0_record_commit",
                "phase0_freeze.json must be added once and never modified in Git history",
            )
        )
        return None
    commit = commits[0]
    resolved_common = subprocess.run(
        ["git", "rev-parse", f"{common_commit}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", commit],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if (
        parents.returncode != 0
        or not re.fullmatch(r"[0-9a-f]{40,64}", resolved_common)
        or parents.stdout.strip().split() != [commit, resolved_common]
    ):
        issues.append(
            ValidationIssue(
                "phase0_record_commit",
                "Phase-0 record commit must have the exact common freeze commit as its sole parent",
            )
        )
        return None
    added = subprocess.run(
        [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            commit,
            "--",
            PHASE0_FREEZE_PATH,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if added.returncode != 0 or added.stdout.strip() != f"A\t{PHASE0_FREEZE_PATH}":
        issues.append(
            ValidationIssue(
                "phase0_record_commit",
                "Phase-0 record path was not first-added in its unique record commit",
            )
        )
        return None
    frozen = subprocess.run(
        ["git", "show", f"{commit}:{PHASE0_FREEZE_PATH}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if (
        frozen.returncode != 0
        or not freeze_path.is_file()
        or freeze_path.is_symlink()
        or frozen.stdout != freeze_path.read_bytes()
    ):
        issues.append(
            ValidationIssue(
                "phase0_record_commit",
                "current phase0_freeze.json bytes differ from its record commit",
            )
        )
        return None
    return commit


def _verify_git_frozen_files(
    root: Path,
    commit: str,
    relative_paths: Iterable[str],
    *,
    issue_code: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    commit_check = subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if commit_check.returncode != 0:
        return [ValidationIssue(issue_code, f"Git commit does not exist: {commit}")]
    for relative in sorted(set(relative_paths)):
        if not _safe_relative_path(relative):
            issues.append(ValidationIssue(issue_code, f"unsafe frozen path: {relative}"))
            continue
        current_path = root / relative
        if not current_path.is_file() or current_path.is_symlink():
            issues.append(
                ValidationIssue(issue_code, f"working frozen file is missing/unsafe: {relative}")
            )
            continue
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            issues.append(
                ValidationIssue(issue_code, f"{relative} is absent from freeze commit {commit}")
            )
        elif hashlib.sha256(result.stdout).hexdigest() != _sha256_file(current_path):
            issues.append(
                ValidationIssue(
                    issue_code,
                    f"working artifact differs from {commit}:{relative}",
                )
            )
    return issues


def _git_team_file_paths(
    root: Path,
    commit: str,
    team_prefix: str,
    mutable_outputs: set[str],
    issues: list[ValidationIssue],
) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", commit, "--", team_prefix],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        issues.append(ValidationIssue("freeze_commit", f"cannot inspect Git commit {commit}"))
        return set()
    paths: set[str] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode, object_type, _object_id = metadata.decode("ascii").split(" ", 2)
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            issues.append(
                ValidationIssue("team_bundle", "team freeze contains an invalid Git tree entry")
            )
            continue
        pure = PurePosixPath(path)
        if "__pycache__" in pure.parts or pure.suffix == ".pyc":
            issues.append(
                ValidationIssue("team_bundle", f"generated Python cache is committed: {path}")
            )
            continue
        if mode == "120000" or object_type != "blob":
            issues.append(
                ValidationIssue("team_bundle", f"non-regular Git object in team freeze: {path}")
            )
            continue
        if path not in mutable_outputs:
            paths.add(path)
    return paths


def _average_percentile(
    values: Mapping[str, float], higher_is_better: bool = True
) -> dict[str, float]:
    """Return [0, 1] cohort percentiles with average ranks for exact ties."""
    if not values:
        return {}
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=not higher_is_better)
    if len(ordered) == 1:
        return {ordered[0][0]: 0.5}
    result: dict[str, float] = {}
    index = 0
    while index < len(ordered):
        stop = index + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[index][1]:
            stop += 1
        average_position = (index + stop - 1) / 2
        percentile = average_position / (len(ordered) - 1)
        for tied_index in range(index, stop):
            result[ordered[tied_index][0]] = percentile
        index = stop
    return result


def _raw_components(submission: Submission) -> dict[str, float]:
    is_metrics = submission.in_sample.metrics
    oos_metrics = submission.public_oos.metrics
    regime_values = tuple(submission.regime_sharpe[name] for name in sorted(REQUIRED_REGIMES))
    return {
        "oos_net_sharpe": oos_metrics.net_sharpe,
        "oos_net_sortino": oos_metrics.net_sortino,
        "oos_calmar": oos_metrics.calmar,
        "oos_annualized_return": oos_metrics.annualized_return,
        "oos_max_drawdown": oos_metrics.max_drawdown,
        "is_net_sharpe": is_metrics.net_sharpe,
        "is_calmar": is_metrics.calmar,
        "generalization_coherence": min(is_metrics.net_sharpe, oos_metrics.net_sharpe)
        - 0.25 * abs(is_metrics.net_sharpe - oos_metrics.net_sharpe),
        "positive_quarter_fraction": min(
            is_metrics.positive_quarter_fraction, oos_metrics.positive_quarter_fraction
        ),
        "worst_regime_sharpe": min(regime_values),
        "positive_regime_fraction": sum(value > 0.0 for value in regime_values)
        / len(regime_values),
        "double_cost_sharpe": submission.double_cost_oos_sharpe,
        "cost_sharpe_retention": _sharpe_retention(
            oos_metrics.net_sharpe, submission.double_cost_oos_sharpe
        ),
    }


def _sharpe_retention(base: float, stressed: float) -> float:
    """Return scale-free stressed Sharpe retention with sensible negative-Sharpe ordering."""
    if base != 0.0:
        return 1.0 + (stressed - base) / abs(base)
    if stressed > 0.0:
        return 1.0
    if stressed < 0.0:
        return -1.0
    return 1.0


def _bounded_jury_score(score: float, name: str) -> float:
    result = _finite_float(score, name)
    if not 0.0 <= result <= 15.0:
        raise ValueError(f"{name} must be in [0, 15]")
    return result


def _paper_eligible(submission: Submission) -> bool:
    """Mechanical paper-trade nomination; this is not a tournament disqualification rule."""
    is_metrics = submission.in_sample.metrics
    oos_metrics = submission.public_oos.metrics
    regimes = tuple(submission.regime_sharpe.values())
    return (
        is_metrics.net_sharpe >= 0.75
        and oos_metrics.net_sharpe >= 1.0
        and submission.double_cost_oos_sharpe >= 0.5
        and oos_metrics.max_drawdown <= 0.30
        and oos_metrics.positive_quarter_fraction >= 0.625
        and min(regimes) >= -0.25
        and sum(value > 0.0 for value in regimes) >= 3
    )


def score_tournament(
    submissions: Iterable[Submission],
    critic_scores: Mapping[str, float] | None = None,
    user_scores: Mapping[str, float] | None = None,
    extra_issues: Mapping[str, Iterable[ValidationIssue]] | None = None,
    critic_issues: Mapping[str, Iterable[ValidationIssue]] | None = None,
) -> tuple[TeamScore, ...]:
    """Validate, rank, and score frozen submissions.

    The objective cohort is fixed from mechanically valid submissions before Critic findings are
    applied.  A later Critic integrity DQ therefore cannot change any team's 70-point automatic
    score or objective rank.  Mechanically invalid teams have no objective score; Critic-DQ teams
    retain their locked objective score/rank for auditability but cannot receive a final rank.
    """
    submission_list = list(submissions)
    team_ids = [submission.team_id for submission in submission_list]
    if len(team_ids) != len(set(team_ids)):
        raise ValueError("duplicate team_id in tournament submissions")
    critic_scores = critic_scores or {}
    user_scores = user_scores or {}
    extra_issues = extra_issues or {}
    critic_issues = critic_issues or {}
    unknown_critic_teams = set(critic_issues) - set(team_ids)
    if unknown_critic_teams:
        raise ValueError(f"Critic issues name unknown teams: {sorted(unknown_critic_teams)}")

    mechanical_issues_by_team = {
        submission.team_id: validate_submission(submission)
        + tuple(extra_issues.get(submission.team_id, ()))
        for submission in submission_list
    }
    objective_cohort = [
        submission
        for submission in submission_list
        if not mechanical_issues_by_team[submission.team_id]
    ]
    raw = {submission.team_id: _raw_components(submission) for submission in objective_cohort}
    percentiles: dict[str, dict[str, float]] = {}
    for component in AUTOMATED_WEIGHTS:
        component_values = {team: values[component] for team, values in raw.items()}
        percentiles[component] = _average_percentile(
            component_values,
            higher_is_better=component != "oos_max_drawdown",
        )

    automatic_scores: dict[str, float] = {}
    for submission in objective_cohort:
        team_id = submission.team_id
        automatic_scores[team_id] = round(
            sum(
                AUTOMATED_WEIGHTS[component] * percentiles[component][team_id]
                for component in AUTOMATED_WEIGHTS
            ),
            6,
        )
    objective_order = sorted(
        objective_cohort,
        key=lambda submission: (-automatic_scores[submission.team_id], submission.team_id),
    )
    objective_ranks = {
        submission.team_id: rank for rank, submission in enumerate(objective_order, start=1)
    }

    scored: list[TeamScore] = []
    critic_disqualified: list[TeamScore] = []
    for submission in objective_cohort:
        team_id = submission.team_id
        automatic = automatic_scores[team_id]
        findings = tuple(critic_issues.get(team_id, ()))
        critic = _bounded_jury_score(critic_scores.get(team_id, 0.0), f"critic_scores.{team_id}")
        user = _bounded_jury_score(user_scores.get(team_id, 0.0), f"user_scores.{team_id}")
        if findings:
            critic_disqualified.append(
                TeamScore(
                    team_id=team_id,
                    valid=False,
                    rank=None,
                    objective_rank=objective_ranks[team_id],
                    automatic_score=automatic,
                    critic_score=critic,
                    user_score=user,
                    total_score=None,
                    paper_eligible=False,
                    disqualification_reasons=tuple(issue.message for issue in findings),
                )
            )
            continue
        scored.append(
            TeamScore(
                team_id=team_id,
                valid=True,
                rank=None,
                objective_rank=objective_ranks[team_id],
                automatic_score=automatic,
                critic_score=critic,
                user_score=user,
                total_score=round(automatic + critic + user, 6),
                paper_eligible=_paper_eligible(submission),
            )
        )

    scored.sort(key=lambda score: (-float(score.total_score), score.team_id))
    ranked = [dataclasses.replace(score, rank=index) for index, score in enumerate(scored, start=1)]
    ranked.extend(sorted(critic_disqualified, key=lambda score: int(score.objective_rank or 0)))
    for submission in submission_list:
        issues = mechanical_issues_by_team[submission.team_id]
        if issues:
            ranked.append(
                TeamScore(
                    team_id=submission.team_id,
                    valid=False,
                    rank=None,
                    objective_rank=None,
                    automatic_score=None,
                    critic_score=None,
                    user_score=None,
                    total_score=None,
                    paper_eligible=False,
                    disqualification_reasons=tuple(issue.message for issue in issues),
                )
            )
    return tuple(ranked)


def score_as_dict(score: TeamScore) -> dict[str, Any]:
    """Convert a score to a JSON-serializable object."""
    return dataclasses.asdict(score)
