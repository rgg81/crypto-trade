"""Cutoff-aware, strategy-neutral runner for one isolated Top-40 V4 team."""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import os
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, TextIO

import numpy as np
import pandas as pd

import crypto_trade.tournament.top40_v4 as tournament_contract
from crypto_trade.tournament import (
    pure_crypto_universe_v4_r2,
    pure_crypto_universe_v6,
    source_archive_v4,
)
from crypto_trade.tournament.engine_v2 import (
    EvaluationResult,
    EvaluatorConfig,
    _normalise_bars,
    _normalise_funding,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT
from crypto_trade.tournament.metrics_v3 import (
    aggregate_daily_returns,
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext
from crypto_trade.tournament.risk_policy import risk_policy_from_dict

_CANDIDATE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_INTERVAL = pd.Timedelta(hours=8)
_REQUIRED_DATASETS = (
    "bars",
    "funding",
    "mark_prices",
    "membership",
    "contract_metadata",
)
_CANONICAL_SNAPSHOT_NAMES = frozenset(
    {
        "archive_provenance",
        "bars",
        "btc_daily_returns",
        "btc_regimes",
        "contract_metadata",
        "coverage",
        "exchange_info",
        "funding",
        "mark_prices",
        "mark_rest_provenance",
        "membership",
        "rest_provenance",
    }
)
_DATASET_BASENAMES = {name: f"{name}.parquet" for name in _REQUIRED_DATASETS}
_EVENT_COLUMNS = (
    "timestamp",
    "symbol",
    "event_type",
    "phase",
    "quantity",
    "price",
    "notional",
    "funding_rate",
    "cashflow",
    "fee",
    "slippage",
    "reason",
    "policy_id",
)
_TRADE_EVENT_TYPES = frozenset({"trade", "risk_reduction", "forced_exit", "risk_policy_action"})
_WORKER_RESPONSE_TIMEOUT_SECONDS = 300.0
_WORKER_TOTAL_TIMEOUT_SECONDS = 1_800.0
_WORKER_SHUTDOWN_TIMEOUT_SECONDS = 5.0
_MAX_WORKER_RESPONSE_BYTES = 1_048_576
_TEAM_TREE_MAX_FILE_BYTES = 2 * 1024 * 1024
_TEAM_TREE_MAX_TOTAL_BYTES = 10 * 1024 * 1024
_STAGED_CONFIG_MAX_BYTES = 64 * 1024
# Organizer-owned projections change as research is journaled; they are not executable candidate
# inputs.  Keeping them out of the bundle lets one preregistered executable tree retain the same
# identity when its registration/result rows are appended.
_MUTABLE_TEAM_OUTPUTS = frozenset(
    {"artifact_manifest.json", "submission.json", "experiments.jsonl"}
)
_TEAM_TEXT_SUFFIXES = frozenset(
    {".py", ".md", ".json", ".jsonl", ".toml", ".lock", ".txt", ".yaml", ".yml"}
)
_STAGED_CONFIG_NAMES = frozenset(
    {
        "frozen_config.json",
        "risk_policy.json",
        "strategy_config.json",
        "strategy_config.toml",
        "strategy_config.yaml",
        "strategy_config.yml",
    }
)
_LITERAL_DATE_TARGET = re.compile(
    r"(?is)(?:20\d{2}-\d{2}-\d{2}.{0,200}(?:target|weight|position|signal)|"
    r"(?:target|weight|position|signal).{0,200}20\d{2}-\d{2}-\d{2})"
)
_TARGET_FIELD = re.compile(
    r"(?:^|_)(?:targets?|weights?|positions?|signals?)(?:$|_)", re.IGNORECASE
)
_SINGLE_THREAD_ENVIRONMENT_VARIABLES = (
    "BLIS_NUM_THREADS",
    "GOTO_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OMP_THREAD_LIMIT",
    "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)
_EVALUATOR_AUTHORITY_PATHS = (
    TOP40_V4_LAYOUT.contract_source,
    "src/crypto_trade/tournament/_strategy_worker_v4.py",
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/runner_v4.py",
    "src/crypto_trade/tournament/engine_v2.py",
    "src/crypto_trade/tournament/layout_v4.py",
    "src/crypto_trade/tournament/metrics_v3.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    *(
        ("src/crypto_trade/tournament/pure_crypto_universe_v4_r2.py",)
        if TOP40_V4_LAYOUT.name.endswith("-r2")
        else ()
    ),
    "src/crypto_trade/tournament/risk_policy.py",
    "src/crypto_trade/tournament/scoring_v4.py",
    "src/crypto_trade/tournament/source_archive_v4.py",
)


class NetworkAccessError(RuntimeError):
    """Raised when team code attempts network access during a canonical run."""


class StrategySandboxError(RuntimeError):
    """Raised when the isolated strategy worker cannot start or violates its sandbox."""


class StrategyExecutionError(RuntimeError):
    """Raised when team strategy construction or target generation fails in the worker."""


def _strict_json_loads(payload: str | bytes, label: str) -> object:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON key {key}")
            result[key] = item
        return result

    def reject(value: str) -> None:
        raise ValueError(f"{label} contains nonfinite JSON value {value}")

    try:
        return json.loads(
            payload,
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is invalid JSON") from exc


class _OrganizerRunAuthorization:
    """Private identity capability for trusted organizer evaluation calls."""


_ORGANIZER_RUN_AUTHORIZATION = _OrganizerRunAuthorization()


@dataclasses.dataclass(frozen=True)
class AuthorizedWindow:
    """The only timestamps one runner invocation may evaluate or disclose."""

    stage: str
    replay_start: str
    end_exclusive: str
    score_start: str
    score_end_inclusive: str


@dataclasses.dataclass(frozen=True)
class WindowMetrics:
    """Stable metric projection stored in a stage result."""

    net_sharpe: float
    net_sortino: float
    calmar: float
    annualized_return: float
    max_drawdown: float
    positive_quarter_fraction: float


@dataclasses.dataclass(frozen=True)
class EvaluationWindow:
    """Exact scored daily window and its metrics."""

    start: str
    end: str
    metrics: WindowMetrics


@dataclasses.dataclass(frozen=True)
class TeamWindowRunResult:
    """Window-specific result which cannot accidentally carry another stage's metrics."""

    stage: str
    team_id: str
    entrypoint: str
    seed: int
    data_manifest_sha256: str
    config_sha256: str
    strategy_sha256: str
    risk_policy_sha256: str
    source_bundle_sha256: str
    dependency_lock_sha256: str
    evaluator_sha256: str
    pure_crypto_policy_sha256: str
    pure_crypto_report_sha256: str
    output_dir: str
    artifacts: Mapping[str, str]
    artifact_sha256: Mapping[str, str]
    artifact_sizes: Mapping[str, int]
    scored_window: EvaluationWindow
    double_cost_sharpe: float
    triple_cost_sharpe: float
    regime_sharpe: Mapping[str, float]
    net_sharpe_confidence_interval: tuple[float, float]
    double_cost_sharpe_confidence_interval: tuple[float, float]
    decision_count: int
    event_count: int
    trade_count: int

    def organizer_fields(self) -> dict[str, Any]:
        """Return complete fields for an organizer-owned record."""
        return {
            "stage": self.stage,
            "team_id": self.team_id,
            "entrypoint": self.entrypoint,
            "seeds": [self.seed],
            "data_manifest_sha256": self.data_manifest_sha256,
            "config_sha256": self.config_sha256,
            "strategy_sha256": self.strategy_sha256,
            "risk_policy_sha256": self.risk_policy_sha256,
            "source_bundle_sha256": self.source_bundle_sha256,
            "dependency_lock_sha256": self.dependency_lock_sha256,
            "evaluator_sha256": self.evaluator_sha256,
            "pure_crypto_policy_sha256": self.pure_crypto_policy_sha256,
            "pure_crypto_report_sha256": self.pure_crypto_report_sha256,
            "output_dir": self.output_dir,
            "scored_window": dataclasses.asdict(self.scored_window),
            "double_cost_sharpe": self.double_cost_sharpe,
            "triple_cost_sharpe": self.triple_cost_sharpe,
            "regime_sharpe": dict(self.regime_sharpe),
            "confidence_intervals": {
                "net_sharpe_95": list(self.net_sharpe_confidence_interval),
                "double_cost_sharpe_95": list(self.double_cost_sharpe_confidence_interval),
            },
            "artifacts": dict(self.artifacts),
            "artifact_sha256": dict(self.artifact_sha256),
            "artifact_sizes": dict(self.artifact_sizes),
            "decision_count": self.decision_count,
            "event_count": self.event_count,
            "trade_count": self.trade_count,
        }


@dataclasses.dataclass(frozen=True)
class _SnapshotData:
    manifest_sha256: str
    paths: Mapping[str, Path]
    file_hashes: Mapping[Path, str]
    bars: pd.DataFrame
    funding: pd.DataFrame
    mark_prices: pd.DataFrame
    membership: pd.DataFrame
    contract_metadata: pd.DataFrame


def _pure_crypto_preflight(root: Path, config: Mapping[str, Any]) -> str:
    """Run and bind the exact deterministic A6 audit report."""

    authority = config["universe"]["a6_authority"]
    for path_field, hash_field in (
        ("audit_module_path", "audit_module_sha256"),
        ("audit_dependency_path", "audit_dependency_sha256"),
    ):
        relative = authority[path_field]
        raw_path = root / relative
        path = raw_path.resolve()
        if (
            _has_symlink_component(root, raw_path)
            or not path.is_relative_to(root)
            or not path.is_file()
        ):
            raise ValueError(f"A6 {path_field} is missing or unsafe")
        if _sha256_file(path) != authority[hash_field]:
            raise ValueError(f"A6 {hash_field} differs from the configured authority")

    report_bytes = (
        pure_crypto_universe_v4_r2.audit_report_bytes(root, config)
        if TOP40_V4_LAYOUT.name.endswith("-r2")
        else pure_crypto_universe_v6.audit_report_bytes(root)
    )
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if report_sha256 != authority["audit_report_sha256"]:
        raise ValueError("A6 deterministic audit report hash differs from the V4 config")
    try:
        report = _strict_json_loads(report_bytes, "A6 deterministic audit report")
    except ValueError as exc:
        raise ValueError("A6 deterministic audit report is invalid JSON") from exc
    if not isinstance(report, Mapping):
        raise ValueError("A6 deterministic audit report must be an object")
    if (
        report.get("status") != authority["expected_audit_status"]
        or report.get("policy_id") != authority["policy_id"]
        or report.get("policy_sha256") != authority["policy_sha256"]
        or not isinstance(report.get("counts"), Mapping)
        or report["counts"].get("violations") != authority["expected_violations"]
        or report.get("violations") != []
    ):
        raise ValueError(
            "A6 deterministic audit did not prove a zero-violation pure-crypto universe"
        )
    return report_sha256


def run_team(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
    config_path: str | Path,
    manifest_path: str | Path,
    *,
    stage: str,
    _authorization: object | None = None,
    _output_relative: str | None = None,
    _candidate_id: str | None = None,
    _source_archive_relative: str | None = None,
    _source_archive_sha256: str | None = None,
) -> TeamWindowRunResult:
    """Run one organizer-authorized stage with unconditional A6 pre/post audits."""

    if _authorization is not _ORGANIZER_RUN_AUTHORIZATION:
        raise PermissionError("full-window V4 evaluation is a trusted organizer operation")
    root_path = Path(root).resolve()
    if not all(
        isinstance(value, str) and value
        for value in (_candidate_id, _source_archive_relative, _source_archive_sha256)
    ):
        raise ValueError("V4 runs require an immutable candidate source archive authority")
    capture = capture_source_bundle(root_path, team_id, entrypoint)
    archive = source_archive_v4.read_source_archive(
        root_path,
        _source_archive_relative,
        _source_archive_sha256,
        expected_team_id=team_id,
        expected_candidate_id=_candidate_id,
        expected_candidate_root=capture.candidate_root,
        expected_entrypoint=capture.entrypoint,
        expected_source_bundle_sha256=capture.sha256,
    )
    if archive.manifest_entries != capture.manifest_entries:
        raise ValueError("live candidate tree differs from its immutable source archive")
    expected_output_relative = _validated_output_relative(team_id, stage, _output_relative)
    raw_expected_output_path = root_path / expected_output_relative
    expected_output_path = raw_expected_output_path.resolve()
    if not expected_output_path.is_relative_to(root_path):
        raise ValueError("V4 output directory escapes the tournament root")
    output_existed_before = (
        raw_expected_output_path.exists() or raw_expected_output_path.is_symlink()
    )
    canonical_config_path = _resolve_root_file(root_path, config_path, "config")
    config = _load_config(canonical_config_path, team_id)
    before = _pure_crypto_preflight(root_path, config)
    result: TeamWindowRunResult | None = None
    try:
        result = _run_team_impl(
            root_path,
            team_id,
            entrypoint,
            canonical_config_path,
            manifest_path,
            stage=stage,
            _authorization=_authorization,
            _output_relative=expected_output_relative,
            _source_archive=archive,
        )
    finally:
        try:
            after = _pure_crypto_preflight(root_path, config)
        except BaseException:
            if result is not None:
                _remove_just_created_output(
                    root_path,
                    team_id,
                    stage,
                    result.output_dir,
                    expected_output_relative=expected_output_relative,
                    expected_output_path=expected_output_path,
                    output_existed_before=output_existed_before,
                )
            raise
        if after != before:
            if result is not None:
                _remove_just_created_output(
                    root_path,
                    team_id,
                    stage,
                    result.output_dir,
                    expected_output_relative=expected_output_relative,
                    expected_output_path=expected_output_path,
                    output_existed_before=output_existed_before,
                )
            raise ValueError("A6 deterministic audit authority changed during the V4 run")
    if result is None:
        raise RuntimeError("V4 runner completed without a result")
    if result.pure_crypto_report_sha256 != before:
        _remove_just_created_output(
            root_path,
            team_id,
            stage,
            result.output_dir,
            expected_output_relative=expected_output_relative,
            expected_output_path=expected_output_path,
            output_existed_before=output_existed_before,
        )
        raise ValueError("runner result is not bound to the verified A6 report")
    return result


def _remove_just_created_output(
    root: Path,
    team_id: str,
    stage: str,
    result_output_relative: str,
    *,
    expected_output_relative: str,
    expected_output_path: Path,
    output_existed_before: bool,
) -> None:
    """Remove only this invocation's newly promoted immutable output."""

    if output_existed_before:
        return
    validated = _validated_output_relative(team_id, stage, result_output_relative)
    if validated != expected_output_relative:
        raise RuntimeError("refusing to remove an unexpected V4 output directory")
    raw_path = root / validated
    if (
        raw_path.is_symlink()
        or raw_path.resolve() != expected_output_path
        or not expected_output_path.is_relative_to(root)
    ):
        raise RuntimeError("refusing to remove an unsafe V4 output directory")
    if not expected_output_path.exists():
        return
    if not expected_output_path.is_dir():
        raise RuntimeError("refusing to remove a non-directory V4 output path")
    shutil.rmtree(expected_output_path)


def _run_team_impl(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
    config_path: str | Path,
    manifest_path: str | Path,
    *,
    stage: str,
    _authorization: object | None = None,
    _output_relative: str | None = None,
    _source_archive: source_archive_v4.SourceArchive | None = None,
) -> TeamWindowRunResult:
    """Run one team against a verified frozen snapshot and publish canonical artifacts.

    Team code executes only in a namespaced worker and receives past-truncated contexts through
    ``generate_targets``.  The verified snapshot and canonical evaluator remain in the trusted
    parent. Nothing is promoted to the report directory until target generation, all three cost
    evaluator passes, metrics, and every artifact write have succeeded.
    """
    if _authorization is not _ORGANIZER_RUN_AUTHORIZATION:
        raise PermissionError(
            "full-window tournament evaluation is a trusted organizer operation; "
            f"use {TOP40_V4_LAYOUT.orchestrator_script}"
        )
    if _source_archive is None:
        raise ValueError("V4 runner requires a verified immutable source archive")
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"tournament root is not a directory: {root_path}")
    TOP40_V4_LAYOUT.require_team(team_id)

    entrypoint_path, entrypoint_relative = _resolve_team_entrypoint(root_path, team_id, entrypoint)
    risk_policy_path = _resolve_team_risk_policy(root_path, team_id, entrypoint_path)
    canonical_config_path = _resolve_root_file(root_path, config_path, "config")
    canonical_manifest_path = _resolve_root_file(root_path, manifest_path, "manifest")
    edition_manifest = tournament_contract.load_config(root=root_path).raw["data"]["manifest_path"]
    expected_manifest_path = (root_path / str(edition_manifest)).resolve()
    if canonical_manifest_path != expected_manifest_path:
        raise ValueError("manifest_path must match the edition's immutable data authority")
    initial_config_sha256 = _sha256_file(canonical_config_path)
    initial_strategy_sha256 = _sha256_file(entrypoint_path)
    initial_risk_policy_sha256 = _sha256_file(risk_policy_path)
    initial_source_bundle_sha256, initial_source_entries = source_bundle_fingerprint(
        root_path, team_id, entrypoint_relative
    )
    if (
        initial_source_bundle_sha256 != _source_archive.source_bundle_sha256
        or initial_source_entries != _source_archive.manifest_entries
    ):
        raise ValueError("runner candidate tree differs from its immutable source archive")
    initial_manifest_sha256 = _sha256_file(canonical_manifest_path)
    initial_dependency_lock_sha256 = _sha256_file(root_path / "uv.lock")
    initial_evaluator_sha256 = _evaluator_authority_sha256(root_path)
    config = _load_config(canonical_config_path, team_id)
    authorized = _authorized_window(config, stage)
    output_relative = _validated_output_relative(team_id, stage, _output_relative)
    evaluator_config = _evaluator_config(config)
    risk_policy = _risk_policy_from_archive(_source_archive)
    decision_times = _decision_grid(authorized)
    seed = int(config["research"]["strategy_seed"])

    snapshot = _load_verified_snapshot(root_path, canonical_manifest_path)
    _validate_snapshot_bounds(snapshot, config, decision_times)
    bars = snapshot.bars.loc[
        pd.to_datetime(snapshot.bars["open_time"], utc=True)
        < _as_utc_timestamp(authorized.end_exclusive)
    ].copy()
    funding = snapshot.funding.loc[
        pd.to_datetime(snapshot.funding["funding_time"], utc=True)
        < _as_utc_timestamp(authorized.end_exclusive)
    ].copy()
    mark_prices = snapshot.mark_prices.loc[
        pd.to_datetime(snapshot.mark_prices["mark_time"], utc=True)
        < _as_utc_timestamp(authorized.end_exclusive)
    ].copy()
    membership = snapshot.membership.loc[
        pd.to_datetime(snapshot.membership["reconstitution_time"], utc=True)
        < _as_utc_timestamp(authorized.end_exclusive)
    ].copy()
    raw_targets = _generate_targets_in_worker(
        root_path,
        team_id,
        entrypoint_relative,
        bars,
        funding,
        membership,
        decision_times,
        seed=seed,
        interval_hours=8,
        expected_source_bundle_sha256=initial_source_bundle_sha256,
        expected_source_entries=_source_archive.manifest_entries,
        archived_files=_source_archive.files,
    )
    targets = _canonical_targets(raw_targets, bars, decision_times)
    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=mark_prices,
        config=evaluator_config,
        risk_policy=risk_policy,
    )
    triple = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=mark_prices,
        config=evaluator_config,
        cost_multiplier=float(config["execution"]["triple_cost_multiplier"]),
        risk_policy=risk_policy,
    )

    _validate_evaluation_grids(base, stressed, triple, decision_times)
    base_daily = _canonical_daily_returns(base.returns, "base", authorized)
    stressed_daily = _canonical_daily_returns(stressed.returns, "double-cost", authorized)
    triple_daily = _canonical_daily_returns(triple.returns, "triple-cost", authorized)
    btc_daily = _btc_daily_returns(bars, config, authorized)
    metrics = _compute_metrics(
        base_daily,
        stressed_daily,
        triple_daily,
        btc_daily,
        config,
        authorized,
    )
    _verify_snapshot_files_unchanged(snapshot)
    final_source_bundle_sha256, final_source_entries = source_bundle_fingerprint(
        root_path, team_id, entrypoint_relative
    )
    if final_source_entries != _source_archive.manifest_entries:
        raise ValueError("runner candidate tree changed relative to its immutable source archive")
    final_hashes = {
        "config": _sha256_file(canonical_config_path),
        "strategy": _sha256_file(entrypoint_path),
        "risk_policy": _sha256_file(risk_policy_path),
        "source_bundle": final_source_bundle_sha256,
        "manifest": _sha256_file(canonical_manifest_path),
        "dependency_lock": _sha256_file(root_path / "uv.lock"),
        "evaluator": _evaluator_authority_sha256(root_path),
    }
    initial_hashes = {
        "config": initial_config_sha256,
        "strategy": initial_strategy_sha256,
        "risk_policy": initial_risk_policy_sha256,
        "source_bundle": initial_source_bundle_sha256,
        "manifest": initial_manifest_sha256,
        "dependency_lock": initial_dependency_lock_sha256,
        "evaluator": initial_evaluator_sha256,
    }
    changed = [name for name in initial_hashes if final_hashes[name] != initial_hashes[name]]
    if changed:
        raise ValueError(f"canonical inputs changed during team run: {changed}")
    if snapshot.manifest_sha256 != initial_manifest_sha256:
        raise ValueError("verified snapshot manifest hash differs from the runner input hash")

    artifact_paths = _publish_artifacts(
        root_path,
        team_id,
        stage=stage,
        output_relative=output_relative,
        targets=targets,
        base=base,
        stressed=stressed,
        triple=triple,
        base_daily=base_daily,
        stressed_daily=stressed_daily,
        triple_daily=triple_daily,
    )
    trades = _trade_events(base.events)
    artifact_files = {name: root_path / relative for name, relative in artifact_paths.items()}
    return TeamWindowRunResult(
        stage=stage,
        team_id=team_id,
        entrypoint=entrypoint_relative,
        seed=seed,
        data_manifest_sha256=snapshot.manifest_sha256,
        config_sha256=initial_config_sha256,
        strategy_sha256=initial_strategy_sha256,
        risk_policy_sha256=initial_risk_policy_sha256,
        source_bundle_sha256=initial_source_bundle_sha256,
        dependency_lock_sha256=initial_dependency_lock_sha256,
        evaluator_sha256=initial_evaluator_sha256,
        pure_crypto_policy_sha256=str(config["universe"]["a6_authority"]["policy_sha256"]),
        pure_crypto_report_sha256=str(config["universe"]["a6_authority"]["audit_report_sha256"]),
        output_dir=output_relative,
        artifacts=artifact_paths,
        artifact_sha256={name: _sha256_file(path) for name, path in artifact_files.items()},
        artifact_sizes={name: path.stat().st_size for name, path in artifact_files.items()},
        scored_window=metrics["scored_window"],
        double_cost_sharpe=metrics["double_cost_sharpe"],
        triple_cost_sharpe=metrics["triple_cost_sharpe"],
        regime_sharpe=metrics["regime_sharpe"],
        net_sharpe_confidence_interval=metrics["net_sharpe_confidence_interval"],
        double_cost_sharpe_confidence_interval=metrics["double_cost_sharpe_confidence_interval"],
        decision_count=len(decision_times),
        event_count=len(base.events),
        trade_count=len(trades),
    )


def _has_symlink_component(root: Path, path: Path) -> bool:
    """Return true when an existing lexical component below root is a symlink."""

    absolute = path if path.is_absolute() else root / path
    try:
        relative = absolute.relative_to(root)
    except ValueError:
        return True
    current = root
    for part in relative.parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            return True
    return False


def _resolve_team_entrypoint(root: Path, team_id: str, entrypoint: str | Path) -> tuple[Path, str]:
    raw = Path(entrypoint)
    if raw.is_absolute() or ".." in PurePosixPath(raw.as_posix()).parts:
        raise ValueError("entrypoint must be a safe path relative to the tournament root")
    relative = PurePosixPath(raw.as_posix()).as_posix()
    required_prefix = f"{TOP40_V4_LAYOUT.tournament_root}/teams/{team_id}/"
    lane_relative = PurePosixPath(relative.removeprefix(required_prefix))
    if (
        not relative.startswith(required_prefix)
        or len(lane_relative.parts) != 3
        or lane_relative.parts[0] != "candidates"
        or lane_relative.parts[2] != "strategy.py"
        or _CANDIDATE_ID.fullmatch(lane_relative.parts[1]) is None
    ):
        raise ValueError(
            f"entrypoint must be candidates/<candidate-id>/strategy.py under {required_prefix}"
        )
    raw_team_root = root / required_prefix
    if _has_symlink_component(root, raw_team_root):
        raise ValueError("team namespace cannot be a symlink")
    team_root = raw_team_root.resolve()
    if not team_root.is_relative_to(root):
        raise ValueError("team namespace escapes the tournament root")
    raw_path = root / raw
    path = raw_path.resolve()
    if (
        _has_symlink_component(root, raw_path)
        or not path.is_relative_to(team_root)
        or not path.is_file()
    ):
        raise ValueError(f"entrypoint does not exist inside {team_id} namespace: {relative}")
    return path, relative


def _resolve_team_risk_policy(root: Path, team_id: str, entrypoint: Path) -> Path:
    """Resolve the policy beside the selected candidate entrypoint.

    Top-level candidates retain the historical ``teams/<team>/risk_policy.json`` layout. Nested
    incumbent/challenger candidates bind their own adjacent policy, so selecting an entrypoint can
    never silently borrow the active top-level candidate's risk semantics.
    """

    raw_team_root = root / TOP40_V4_LAYOUT.team_root(team_id)
    if _has_symlink_component(root, raw_team_root):
        raise ValueError(f"team namespace is unsafe for {team_id}")
    team_root = raw_team_root.resolve()
    entrypoint_path = entrypoint.resolve()
    if (
        not team_root.is_relative_to(root)
        or not entrypoint_path.is_relative_to(team_root)
        or not entrypoint_path.is_file()
        or _has_symlink_component(root, entrypoint)
    ):
        raise ValueError(f"entrypoint is missing or unsafe for {team_id}")
    candidate_root = entrypoint_path.parent
    raw_path = candidate_root / "risk_policy.json"
    path = raw_path.resolve()
    if (
        not path.is_relative_to(candidate_root)
        or not path.is_relative_to(team_root)
        or not path.is_file()
        or _has_symlink_component(root, raw_path)
    ):
        raise ValueError(
            f"risk_policy.json is missing or unsafe beside the selected {team_id} entrypoint"
        )
    return path


def _resolve_root_file(root: Path, value: str | Path, label: str) -> Path:
    raw = Path(value)
    raw_path = raw if raw.is_absolute() else root / raw
    path = raw_path.resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{label} path escapes tournament root")
    if _has_symlink_component(root, raw_path) or not path.is_file():
        raise ValueError(f"{label} file does not exist: {path}")
    return path


def _risk_policy_from_archive(
    archive: source_archive_v4.SourceArchive,
):
    matches = [item for item in archive.files if item.path == "risk_policy.json"]
    if len(matches) != 1:
        raise ValueError("immutable source archive must contain exactly one risk_policy.json")
    try:
        raw = _strict_json_loads(matches[0].content, "archived risk policy")
    except ValueError as exc:
        raise ValueError(f"invalid archived risk policy: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("archived risk policy root must be a JSON object")
    return risk_policy_from_dict(raw)


@dataclasses.dataclass(frozen=True)
class _TeamTreeFile:
    relative: str
    path: Path
    size: int
    sha256: str
    staged: bool
    content: bytes


@dataclasses.dataclass(frozen=True)
class SourceBundleCapture:
    """Stable bytes and root identity for exactly one selected candidate."""

    candidate_root: str
    entrypoint: str
    sha256: str
    files: tuple[source_archive_v4.SourceFile, ...]

    @property
    def manifest_entries(self) -> tuple[dict[str, object], ...]:
        return tuple(item.manifest_entry for item in self.files)


def _stable_file_bytes(
    path: Path | str,
    *,
    dir_fd: int | None = None,
    display_name: str | None = None,
) -> bytes:
    """Read one bounded, unlinked regular file through a no-follow descriptor.

    Path-level ``stat/open/stat`` sequences are vulnerable to a symlink or FIFO substitution
    between calls.  The descriptor identity is therefore authoritative and must still match the
    final lexical directory entry after the read.
    """

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        if dir_fd is None:
            descriptor = os.open(path, flags)
        else:
            descriptor = os.open(path, flags, dir_fd=dir_fd)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > _TEAM_TREE_MAX_FILE_BYTES
            ):
                raise StrategySandboxError(
                    "team source must be one bounded, unlinked regular file: "
                    f"{display_name or Path(path).name}"
                )
            content = handle.read(_TEAM_TREE_MAX_FILE_BYTES + 1)
            after = os.fstat(handle.fileno())
        current = (
            Path(path).lstat()
            if dir_fd is None
            else os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
        )
    except StrategySandboxError:
        raise
    except OSError as exc:
        raise StrategySandboxError(
            f"cannot safely read team source file: {display_name or Path(path).name}"
        ) from exc
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_nlink,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_nlink,
    )
    current_identity = (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_nlink,
    )
    if (
        before_identity != after_identity
        or after_identity != current_identity
        or not stat.S_ISREG(current.st_mode)
        or stat.S_ISLNK(current.st_mode)
    ):
        raise StrategySandboxError(
            f"team source file changed while reading: {display_name or Path(path).name}"
        )
    if len(content) > _TEAM_TREE_MAX_FILE_BYTES:
        raise StrategySandboxError(
            f"team source text file exceeds 2 MiB: {display_name or Path(path).name}"
        )
    return content


def _directory_identity(value: os.stat_result) -> tuple[int, int]:
    if not stat.S_ISDIR(value.st_mode):
        raise StrategySandboxError("candidate source path contains a non-directory component")
    return value.st_dev, value.st_ino


class _PinnedDirectory:
    """Pin every component of an absolute directory path with no-follow descriptors."""

    def __init__(self, path: Path) -> None:
        if not path.is_absolute():
            raise StrategySandboxError("candidate source directory must be absolute")
        self.path = path
        self._fds: list[int] = []
        self._identities: list[tuple[int, int]] = []

    @staticmethod
    def _flags() -> int:
        return (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_DIRECTORY", 0)
        )

    def _open_chain(self) -> tuple[list[int], list[tuple[int, int]]]:
        descriptors: list[int] = []
        identities: list[tuple[int, int]] = []
        try:
            descriptor = os.open(self.path.anchor, self._flags())
            descriptors.append(descriptor)
            identities.append(_directory_identity(os.fstat(descriptor)))
            for component in self.path.parts[1:]:
                descriptor = os.open(component, self._flags(), dir_fd=descriptor)
                descriptors.append(descriptor)
                identities.append(_directory_identity(os.fstat(descriptor)))
        except (OSError, StrategySandboxError) as exc:
            for opened in reversed(descriptors):
                os.close(opened)
            if isinstance(exc, StrategySandboxError):
                raise
            raise StrategySandboxError(
                f"cannot pin candidate source directory: {self.path.name}"
            ) from exc
        return descriptors, identities

    def __enter__(self) -> _PinnedDirectory:
        self._fds, self._identities = self._open_chain()
        return self

    @property
    def fd(self) -> int:
        if not self._fds:
            raise RuntimeError("candidate source directory is not pinned")
        return self._fds[-1]

    def verify(self) -> None:
        descriptors, identities = self._open_chain()
        try:
            if identities != self._identities:
                raise StrategySandboxError(
                    "candidate source directory changed during source traversal"
                )
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    def __exit__(self, *_args: object) -> None:
        for descriptor in reversed(self._fds):
            os.close(descriptor)
        self._fds = []
        self._identities = []


def _timestamp_target_structure(value: object) -> bool:
    if isinstance(value, dict):
        lowered = {str(key).lower() for key in value}
        has_time = any(key in lowered for key in {"timestamp", "timestamp_utc", "date", "time"})
        # Match target concepts as field-name tokens.  A raw substring check falsely classified
        # the schema-required experiment field ``disposition`` as a position table.
        has_target = any(_TARGET_FIELD.search(key) is not None for key in lowered)
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


def _validate_team_text(relative: str, suffix: str, content: bytes) -> None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StrategySandboxError(f"team file is not UTF-8 text: {relative}") from exc
    if suffix in {".py", ".toml", ".yaml", ".yml"} and _LITERAL_DATE_TARGET.search(text):
        raise StrategySandboxError(
            f"literal timestamp-to-target/weight logic is forbidden: {relative}"
        )
    if suffix == ".json":
        try:
            parsed = _strict_json_loads(text, f"team file {relative}")
        except ValueError as exc:
            raise StrategySandboxError(f"invalid JSON team file: {relative}") from exc
        if _timestamp_target_structure(parsed):
            raise StrategySandboxError(
                f"timestamp-keyed target/weight table is forbidden: {relative}"
            )
    elif suffix == ".jsonl":
        try:
            rows = [
                _strict_json_loads(line, f"team file {relative}")
                for line in text.splitlines()
                if line.strip()
            ]
        except ValueError as exc:
            raise StrategySandboxError(f"invalid JSONL team file: {relative}") from exc
        if any(_timestamp_target_structure(row) for row in rows):
            raise StrategySandboxError(
                f"timestamp-keyed target/weight table is forbidden: {relative}"
            )


def _team_tree_files(source: Path, *, recursive: bool = True) -> list[_TeamTreeFile]:
    """Validate candidate files inside one explicitly selected root boundary.

    A top-level ``teams/team-NN/strategy.py`` candidate owns only direct regular files in that
    directory.  Its ``incumbents/`` and ``challengers/`` children are sibling candidates and must
    never perturb its identity.  A selected nested candidate owns its complete recursive tree.
    """
    source_path = source.absolute()
    files: list[_TeamTreeFile] = []
    total_size = 0

    def walk(directory_fd: int, prefix: PurePosixPath) -> None:
        nonlocal total_size
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            raise StrategySandboxError(
                "cannot enumerate pinned candidate source directory"
            ) from exc
        for name in names:
            relative = prefix / name
            relative_text = relative.as_posix()
            if relative_text in _MUTABLE_TEAM_OUTPUTS:
                continue
            try:
                current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise StrategySandboxError(
                    f"cannot inspect candidate source entry: {relative_text}"
                ) from exc
            suffix = Path(name).suffix.lower()
            if "__pycache__" in relative.parts or suffix == ".pyc":
                raise StrategySandboxError(f"generated Python cache is forbidden: {relative}")
            if stat.S_ISLNK(current.st_mode):
                raise StrategySandboxError(f"team tree cannot contain symlinks: {relative}")
            if stat.S_ISDIR(current.st_mode):
                if not recursive:
                    continue
                try:
                    child_fd = os.open(name, _PinnedDirectory._flags(), dir_fd=directory_fd)
                except OSError as exc:
                    raise StrategySandboxError(
                        f"cannot pin candidate source subdirectory: {relative_text}"
                    ) from exc
                try:
                    if _directory_identity(os.fstat(child_fd)) != _directory_identity(current):
                        raise StrategySandboxError(
                            f"candidate source subdirectory changed: {relative_text}"
                        )
                    walk(child_fd, relative)
                    final = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if _directory_identity(final) != _directory_identity(current):
                        raise StrategySandboxError(
                            f"candidate source subdirectory changed: {relative_text}"
                        )
                except OSError as exc:
                    raise StrategySandboxError(
                        f"candidate source subdirectory changed: {relative_text}"
                    ) from exc
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(current.st_mode):
                raise StrategySandboxError(f"team tree contains a non-regular file: {relative}")
            if suffix not in _TEAM_TEXT_SUFFIXES:
                raise StrategySandboxError(
                    f"opaque/prefit file type is forbidden in canonical team tree: {relative}"
                )
            content = _stable_file_bytes(
                name,
                dir_fd=directory_fd,
                display_name=relative_text,
            )
            total_size += len(content)
            if total_size > _TEAM_TREE_MAX_TOTAL_BYTES:
                raise StrategySandboxError("canonical team source tree exceeds 10 MiB")
            _validate_team_text(relative_text, suffix, content)
            # R2 separates the complete evidence archive from the executable mount.  Notes,
            # attestations, certificates, and tests remain fingerprinted evidence but can never
            # be opened by strategy code.  R1 retains its worker-visible bundle semantics.
            staged = True if not TOP40_V4_LAYOUT.name.endswith("-r2") else suffix == ".py"
            if name in _STAGED_CONFIG_NAMES and len(content) > _STAGED_CONFIG_MAX_BYTES:
                raise StrategySandboxError(f"staged strategy config exceeds 64 KiB: {relative}")
            files.append(
                _TeamTreeFile(
                    relative=relative_text,
                    path=source_path.joinpath(*relative.parts),
                    size=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                    staged=staged,
                    content=content,
                )
            )

    with _PinnedDirectory(source_path) as pinned:
        walk(pinned.fd, PurePosixPath())
        pinned.verify()
    return sorted(files, key=lambda item: item.relative)


def _team_tree_fingerprint(files: Sequence[_TeamTreeFile]) -> str:
    entries = [{"path": item.relative, "size": item.size, "sha256": item.sha256} for item in files]
    return source_archive_v4.bundle_fingerprint(entries)


def _candidate_source_boundary(
    root: Path,
    team_id: str,
    entrypoint: str | Path,
) -> tuple[Path, str, bool]:
    entrypoint_path, _relative = _resolve_team_entrypoint(root, team_id, entrypoint)
    team_root = (root / TOP40_V4_LAYOUT.team_root(team_id)).resolve()
    candidate_root = entrypoint_path.parent
    recursive = candidate_root != team_root
    candidate_root_relative = candidate_root.relative_to(root).as_posix()
    entrypoint_in_candidate = entrypoint_path.relative_to(candidate_root).as_posix()
    if "/" in entrypoint_in_candidate:
        raise ValueError("candidate entrypoint must be directly inside its stable candidate root")
    return candidate_root, candidate_root_relative, recursive


def capture_source_bundle(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
) -> SourceBundleCapture:
    """Capture exact candidate bytes with before/after traversal verification."""

    root_path = Path(root).resolve()
    source, candidate_root_relative, recursive = _candidate_source_boundary(
        root_path, team_id, entrypoint
    )
    entrypoint_path, _relative = _resolve_team_entrypoint(root_path, team_id, entrypoint)
    before = _team_tree_files(source, recursive=recursive)
    captured: list[source_archive_v4.SourceFile] = []
    for item in before:
        content = item.content
        captured.append(
            source_archive_v4.SourceFile(
                path=item.relative,
                size=item.size,
                sha256=item.sha256,
                content=content,
            )
        )
    after = _team_tree_files(source, recursive=recursive)
    before_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in before
    )
    after_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in after
    )
    if before_manifest != after_manifest:
        raise StrategySandboxError("candidate tree changed during source archive capture")
    fingerprint = _team_tree_fingerprint(before)
    return SourceBundleCapture(
        candidate_root=candidate_root_relative,
        entrypoint=entrypoint_path.relative_to(source).as_posix(),
        sha256=fingerprint,
        files=tuple(captured),
    )


def source_bundle_fingerprint(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
) -> tuple[str, tuple[dict[str, object], ...]]:
    """Hash the exact stable candidate root used by capture and worker staging."""

    capture = capture_source_bundle(root, team_id, entrypoint)
    return capture.sha256, capture.manifest_entries


class _StrategyWorkerClient:
    def __init__(self, process: subprocess.Popen[str], diagnostics: BinaryIO | None = None) -> None:
        if process.stdin is None or process.stdout is None:
            raise StrategySandboxError("strategy worker pipes were not created")
        self.process = process
        self.stdin: TextIO = process.stdin
        self.stdout: TextIO = process.stdout
        self.diagnostics = diagnostics
        self.ready = False
        self._response_buffer = b""
        self._closed = False
        self._process_group_reaped = False
        self._whole_run_deadline = time.monotonic() + _WORKER_TOTAL_TIMEOUT_SECONDS

    def _diagnostic_text(self) -> str:
        if self.diagnostics is None:
            return ""
        try:
            self.diagnostics.flush()
            self.diagnostics.seek(0)
            return self.diagnostics.read().decode("utf-8", errors="replace").strip()
        except OSError:
            return ""

    def request(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if self._closed:
            raise StrategySandboxError("strategy worker client is closed")
        try:
            encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"))
            self.stdin.write(encoded + "\n")
            self.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as exc:
            self.process.poll()
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            raise StrategySandboxError(f"strategy worker communication failed{suffix}") from exc
        response_deadline = time.monotonic() + _WORKER_RESPONSE_TIMEOUT_SECONDS
        deadline = min(response_deadline, self._whole_run_deadline)
        while b"\n" not in self._response_buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._kill_process_group()
                detail = self._diagnostic_text()
                suffix = f": {detail}" if detail else ""
                if deadline == self._whole_run_deadline:
                    raise StrategySandboxError(
                        "strategy worker exceeded the whole-run wall deadline of "
                        f"{_WORKER_TOTAL_TIMEOUT_SECONDS:g}s{suffix}"
                    )
                raise StrategySandboxError(
                    "strategy worker response timed out after "
                    f"{_WORKER_RESPONSE_TIMEOUT_SECONDS:g}s{suffix}"
                )
            readable, _, _ = select.select([self.stdout.fileno()], [], [], remaining)
            if not readable:
                continue
            try:
                chunk = os.read(self.stdout.fileno(), 65_536)
            except OSError as exc:
                raise StrategySandboxError("cannot read strategy worker response") from exc
            if not chunk:
                break
            if len(self._response_buffer) + len(chunk) > _MAX_WORKER_RESPONSE_BYTES:
                self._kill_process_group()
                raise StrategySandboxError(
                    "strategy worker response exceeded the maximum size of "
                    f"{_MAX_WORKER_RESPONSE_BYTES} bytes"
                )
            self._response_buffer += chunk
        if b"\n" in self._response_buffer:
            raw_line, self._response_buffer = self._response_buffer.split(b"\n", 1)
            try:
                line = raw_line.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise StrategySandboxError(
                    "strategy worker returned non-UTF-8 protocol data"
                ) from exc
        else:
            line = ""
        if not line:
            returncode = self.process.poll()
            if returncode is None:
                self._kill_process_group()
                returncode = self.process.returncode
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            raise StrategySandboxError(
                f"strategy worker exited without a response (status {returncode}){suffix}"
            )
        try:
            response = _strict_json_loads(line, "strategy worker response")
        except ValueError as exc:
            raise StrategySandboxError("strategy worker returned malformed protocol JSON") from exc
        if not isinstance(response, dict):
            raise StrategySandboxError("strategy worker response must be a JSON object")
        if response.get("type") == "error":
            error_type = str(response.get("error_type", "StrategyExecutionError"))
            message = str(response.get("message", "strategy worker failed"))
            if error_type == "StrategySandboxViolationError":
                if "network access" in message:
                    raise NetworkAccessError(message)
                raise StrategySandboxError(message)
            if error_type == "StrategySandboxError":
                raise StrategySandboxError(message)
            raise StrategyExecutionError(f"{error_type}: {message}")
        return response

    def initialise(self, payload: Mapping[str, Any]) -> None:
        response = self.request(payload)
        if response.get("type") != "ready":
            raise StrategySandboxError("strategy worker did not acknowledge initialization")
        self.ready = True

    def _kill_process_group(self) -> None:
        if self._process_group_reaped:
            return
        # The namespace leader may already have exited while one of its descendants remains.
        # Always target the dedicated session/process group created at launch.
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=_WORKER_SHUTDOWN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=_WORKER_SHUTDOWN_TIMEOUT_SECONDS)
        self._process_group_reaped = True

    def _close_handles(self) -> None:
        if self._closed:
            return
        self._closed = True
        for stream in (self.stdin, self.stdout, self.diagnostics):
            if stream is None:
                continue
            try:
                stream.close()
            except OSError:
                pass

    def abort(self) -> None:
        if self._closed:
            return
        self._kill_process_group()
        self._close_handles()

    def finish(self) -> None:
        if self._closed:
            raise StrategySandboxError("strategy worker was already closed")
        returncode = self.process.poll()
        if returncode is not None:
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            self.abort()
            raise StrategySandboxError(
                f"strategy worker exited before clean shutdown (status {returncode}){suffix}"
            )
        try:
            response = self.request({"type": "shutdown"})
            if response.get("type") != "bye":
                raise StrategySandboxError("strategy worker did not acknowledge shutdown")
            remaining = self._whole_run_deadline - time.monotonic()
            if remaining <= 0:
                raise StrategySandboxError("strategy worker exceeded its whole-run wall deadline")
            returncode = self.process.wait(timeout=min(_WORKER_SHUTDOWN_TIMEOUT_SECONDS, remaining))
            if returncode != 0:
                detail = self._diagnostic_text()
                suffix = f": {detail}" if detail else ""
                raise StrategySandboxError(
                    f"strategy worker exited uncleanly (status {returncode}){suffix}"
                )
            self._process_group_reaped = True
        except BaseException:
            self.abort()
            raise
        self._close_handles()


def _strategy_worker_command(
    root: Path,
    repository_parent: Path,
    bundle: Path,
    site_packages: Path,
    runtime_site_packages: Path,
    entrypoint: str,
    empty_dir: Path,
    empty_file: Path,
) -> list[str]:
    if not sys.platform.startswith("linux"):
        raise StrategySandboxError("canonical strategy workers require Linux namespaces")
    unshare = shutil.which("unshare")
    if unshare is None:
        raise StrategySandboxError("unshare is unavailable; refusing an unsandboxed team run")
    return [
        unshare,
        "--user",
        "--map-root-user",
        "--mount",
        "--net",
        "--pid",
        "--fork",
        "--kill-child=KILL",
        "--mount-proc",
        sys.executable,
        "-u",
        "-m",
        "crypto_trade.tournament._strategy_worker_v4",
        "--root",
        str(root),
        "--repository-parent",
        str(repository_parent),
        "--bundle",
        str(bundle),
        "--site-packages",
        str(site_packages),
        "--runtime-site-packages",
        str(runtime_site_packages),
        "--entrypoint",
        entrypoint,
        "--empty-dir",
        str(empty_dir),
        "--empty-file",
        str(empty_file),
    ]


def _copy_team_source_bundle(
    source: Path,
    destination: Path,
    *,
    recursive: bool = True,
    expected_fingerprint: str | None = None,
    expected_entries: Sequence[Mapping[str, object]] | None = None,
) -> str:
    before = _team_tree_files(source, recursive=recursive)
    fingerprint = _team_tree_fingerprint(before)
    manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in before
    )
    if expected_fingerprint is not None and fingerprint != expected_fingerprint:
        raise StrategySandboxError("team tree differs from the pre-run fingerprint")
    if expected_entries is not None and manifest != tuple(expected_entries):
        raise StrategySandboxError("team tree differs from the immutable source archive")
    destination.mkdir(parents=True, exist_ok=False)
    for item in before:
        if not item.staged:
            continue
        target = destination / item.relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as handle:
                handle.write(item.content)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise StrategySandboxError(
                f"cannot stage pinned team source: {item.relative}"
            ) from exc
        staged_content = _stable_file_bytes(target)
        if (
            len(staged_content) != item.size
            or hashlib.sha256(staged_content).hexdigest() != item.sha256
        ):
            raise StrategySandboxError(
                f"staged team source differs from fingerprint: {item.relative}"
            )
    after = _team_tree_files(source, recursive=recursive)
    after_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in after
    )
    if _team_tree_fingerprint(after) != fingerprint or after_manifest != manifest:
        raise StrategySandboxError("team tree changed while staging the worker bundle")
    staged = _team_tree_files(destination, recursive=True)
    staged_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in staged
    )
    expected_staged_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256}
        for item in before
        if item.staged
    )
    if (
        _team_tree_fingerprint(staged)
        != source_archive_v4.bundle_fingerprint(expected_staged_manifest)
        or staged_manifest != expected_staged_manifest
    ):
        raise StrategySandboxError("staged worker tree differs from the immutable candidate tree")
    return fingerprint


def _stage_archived_source_bundle(
    destination: Path,
    files: Sequence[source_archive_v4.SourceFile],
    *,
    expected_fingerprint: str,
    expected_entries: Sequence[Mapping[str, object]],
) -> str:
    """Materialize worker inputs from immutable archive bytes, never from the live tree."""

    manifest = tuple(item.manifest_entry for item in files)
    fingerprint = source_archive_v4.bundle_fingerprint(manifest)
    if fingerprint != expected_fingerprint or manifest != tuple(expected_entries):
        raise StrategySandboxError("archived worker source differs from frozen authority")
    destination.mkdir(parents=True, exist_ok=False)
    staged_files = tuple(
        item
        for item in files
        if not TOP40_V4_LAYOUT.name.endswith("-r2")
        or Path(item.path).suffix.lower() == ".py"
    )
    for item in staged_files:
        _validate_team_text(item.path, Path(item.path).suffix.lower(), item.content)
        target = destination / item.path
        if not target.resolve().is_relative_to(destination.resolve()):
            raise StrategySandboxError("archived worker source escapes its staging directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            if handle.write(item.content) != item.size:
                raise StrategySandboxError("short archived worker source write")
        if _sha256_file(target) != item.sha256:
            raise StrategySandboxError("materialized worker source differs from archive")
    staged = _team_tree_files(destination, recursive=True)
    staged_manifest = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in staged
    )
    expected_staged_manifest = tuple(item.manifest_entry for item in staged_files)
    if (
        staged_manifest != expected_staged_manifest
        or _team_tree_fingerprint(staged)
        != source_archive_v4.bundle_fingerprint(expected_staged_manifest)
    ):
        raise StrategySandboxError("materialized worker bundle differs from archive")
    return fingerprint


def _runner_repository_parent() -> Path:
    """Return the common Git repository whose worktrees must be hidden from team code."""
    checkout_root = Path(__file__).resolve().parents[3]
    git_marker = checkout_root / ".git"
    if git_marker.is_dir():
        common_git_dir = git_marker.resolve()
    elif git_marker.is_file():
        try:
            marker = git_marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise StrategySandboxError(f"cannot read runner Git metadata: {exc}") from exc
        prefix = "gitdir: "
        if not marker.startswith(prefix):
            raise StrategySandboxError("runner .git file does not declare a gitdir")
        raw_git_dir = Path(marker.removeprefix(prefix))
        git_dir = (
            raw_git_dir.resolve()
            if raw_git_dir.is_absolute()
            else (checkout_root / raw_git_dir).resolve()
        )
        common_dir_file = git_dir / "commondir"
        try:
            raw_common_dir = Path(common_dir_file.read_text(encoding="utf-8").strip())
        except OSError as exc:
            raise StrategySandboxError(f"cannot read runner common Git metadata: {exc}") from exc
        common_git_dir = (
            raw_common_dir.resolve()
            if raw_common_dir.is_absolute()
            else (git_dir / raw_common_dir).resolve()
        )
    else:
        raise StrategySandboxError("cannot locate the runner Git repository")
    repository_parent = common_git_dir.parent.resolve()
    if (
        common_git_dir.name != ".git"
        or not repository_parent.is_dir()
        or not checkout_root.is_relative_to(repository_parent)
    ):
        raise StrategySandboxError("runner common Git repository is not safely nested")
    return repository_parent


def _current_venv_site_packages(repository_parent: Path) -> Path:
    """Locate the active venv runtime that must survive masking the repository."""
    purelib = Path(sysconfig.get_path("purelib")).resolve()
    platlib = Path(sysconfig.get_path("platlib")).resolve()
    prefix = Path(sys.prefix).resolve()
    if purelib != platlib:
        raise StrategySandboxError("worker requires one shared purelib/platlib directory")
    if (
        not purelib.is_dir()
        or not purelib.is_relative_to(prefix)
        or not purelib.is_relative_to(repository_parent)
    ):
        raise StrategySandboxError(
            "active worker site-packages must be inside the masked repository venv"
        )
    return purelib


def _strategy_worker_environment(seed: int) -> dict[str, str]:
    if not 0 <= seed <= 2**32 - 1:
        raise StrategySandboxError("strategy seed is outside PYTHONHASHSEED's integer range")
    # Do not inherit credentials, proxy settings, cloud configuration, or loader controls from
    # the organizer. Every variable visible to team code is constructed explicitly here.
    environment = {
        "CUDA_VISIBLE_DEVICES": "",
        "HOME": "/nonexistent",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": str(seed),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "TZ": "UTC",
        "XDG_CACHE_HOME": "/nonexistent",
        "XDG_CONFIG_HOME": "/nonexistent",
    }
    for name in _SINGLE_THREAD_ENVIRONMENT_VARIABLES:
        environment[name] = "1"
    return environment


def _launch_strategy_worker(
    root: Path,
    entrypoint: str | Path,
    team_id: str,
    seed: int,
    expected_source_bundle_sha256: str | None,
    expected_source_entries: Sequence[Mapping[str, object]] | None,
    archived_files: Sequence[source_archive_v4.SourceFile] | None = None,
) -> tuple[_StrategyWorkerClient, tempfile.TemporaryDirectory[str]]:
    repository_parent = _runner_repository_parent()
    site_packages = _current_venv_site_packages(repository_parent)
    sandbox = tempfile.TemporaryDirectory(prefix=f"{TOP40_V4_LAYOUT.name}-{team_id}-")
    sandbox_root = Path(sandbox.name)
    bundle = sandbox_root / "bundle"
    runtime_site_packages = sandbox_root / "runtime-site-packages"
    empty_dir = sandbox_root / "empty-dir"
    empty_file = sandbox_root / "empty-file"
    runtime_site_packages.mkdir()
    empty_dir.mkdir()
    empty_file.touch()
    source, _candidate_root_relative, recursive = _candidate_source_boundary(
        root, team_id, entrypoint
    )
    entrypoint_path, _entrypoint_relative = _resolve_team_entrypoint(root, team_id, entrypoint)
    try:
        if archived_files is None:
            _copy_team_source_bundle(
                source,
                bundle,
                recursive=recursive,
                expected_fingerprint=expected_source_bundle_sha256,
                expected_entries=expected_source_entries,
            )
        else:
            if expected_source_bundle_sha256 is None or expected_source_entries is None:
                raise StrategySandboxError("archived staging requires complete source authority")
            _stage_archived_source_bundle(
                bundle,
                archived_files,
                expected_fingerprint=expected_source_bundle_sha256,
                expected_entries=expected_source_entries,
            )
        copied_entrypoint = entrypoint_path.relative_to(source).as_posix()
        command = _strategy_worker_command(
            root,
            repository_parent,
            bundle,
            site_packages,
            runtime_site_packages,
            copied_entrypoint,
            empty_dir,
            empty_file,
        )
        environment = _strategy_worker_environment(seed)
        try:
            process = subprocess.Popen(
                command,
                cwd=sandbox_root,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as exc:
            raise StrategySandboxError(f"cannot launch strategy namespace: {exc}") from exc
        return _StrategyWorkerClient(process), sandbox
    except BaseException:
        sandbox.cleanup()
        raise


def _json_scalar(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        timestamp = value
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        return timestamp.isoformat()
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    if isinstance(value, (str, int, bool)):
        return value
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    raise TypeError(f"unsupported strategy-context scalar type: {type(value).__name__}")


def _datetime_columns(frame: pd.DataFrame) -> list[str]:
    return [
        str(column)
        for column in frame.columns
        if isinstance(frame[column].dtype, pd.DatetimeTZDtype)
        or pd.api.types.is_datetime64_dtype(frame[column].dtype)
    ]


def _encoded_rows(frame: pd.DataFrame, columns: Sequence[str]) -> list[list[Any]]:
    return [
        [_json_scalar(value) for value in row]
        for row in frame.loc[:, list(columns)].itertuples(index=False, name=None)
    ]


def _validated_worker_weights(
    response: Mapping[str, Any], eligible: Sequence[str]
) -> dict[str, float] | None:
    if response.get("type") != "weights" or "weights" not in response:
        raise StrategySandboxError("strategy worker returned an invalid weight response")
    raw_weights = response["weights"]
    if raw_weights is None:
        return None
    if not isinstance(raw_weights, dict):
        raise StrategySandboxError("strategy worker returned an invalid weight response")
    eligible_set = set(eligible)
    weights: dict[str, float] = {}
    for symbol, raw_weight in raw_weights.items():
        if not isinstance(symbol, str) or symbol not in eligible_set:
            raise StrategySandboxError("strategy worker returned an ineligible target symbol")
        if isinstance(raw_weight, bool):
            raise StrategySandboxError("strategy worker returned a Boolean target weight")
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise StrategySandboxError("strategy worker returned a non-numeric weight") from exc
        if not np.isfinite(weight):
            raise StrategySandboxError("strategy worker returned a non-finite weight")
        weights[symbol] = weight
    return weights


class _WorkerStrategyProxy:
    """Delta-encode authoritative ``generate_targets`` contexts for one worker."""

    def __init__(
        self,
        worker: _StrategyWorkerClient,
        *,
        seed: int,
        interval_hours: int,
        bar_schema: pd.DataFrame,
        funding_schema: pd.DataFrame,
        bar_history: pd.DataFrame | None = None,
        funding_history: pd.DataFrame | None = None,
    ):
        self.worker = worker
        self.seed = seed
        self.bar_columns = tuple(str(column) for column in bar_schema.columns)
        self.funding_columns = tuple(str(column) for column in funding_schema.columns)
        self.interval = pd.Timedelta(hours=interval_hours)
        self.bar_cursors: dict[str, int] = {}
        self.funding_cursors: dict[str, int] = {}
        self.previous_decision: pd.Timestamp | None = None
        if (bar_history is None) != (funding_history is None):
            raise ValueError("canonical bar and funding histories must be supplied together")
        self.bar_history = self._group_history(bar_history, self.bar_columns, "bar")
        self.funding_history = self._group_history(funding_history, self.funding_columns, "funding")
        self.bar_times = self._history_times(self.bar_history, "open_time")
        self.funding_times = self._history_times(self.funding_history, "funding_time")
        worker.initialise(
            {
                "type": "init",
                "seed": seed,
                "interval_hours": interval_hours,
                "bar_columns": list(self.bar_columns),
                "bar_dtypes": [str(dtype) for dtype in bar_schema.dtypes],
                "bar_datetime_columns": _datetime_columns(bar_schema),
                "funding_columns": list(self.funding_columns),
                "funding_dtypes": [str(dtype) for dtype in funding_schema.dtypes],
                "funding_datetime_columns": _datetime_columns(funding_schema),
            }
        )

    @staticmethod
    def _group_history(
        history: pd.DataFrame | None,
        columns: tuple[str, ...],
        label: str,
    ) -> dict[str, pd.DataFrame] | None:
        if history is None:
            return None
        if tuple(str(column) for column in history.columns) != columns:
            raise StrategySandboxError(f"canonical {label} history schema differs")
        if "symbol" not in history.columns:
            raise StrategySandboxError(f"canonical {label} history has no symbol column")
        return {
            str(symbol): frame.reset_index(drop=True).copy(deep=True)
            for symbol, frame in history.groupby("symbol", observed=True, sort=False)
        }

    @staticmethod
    def _history_times(
        histories: dict[str, pd.DataFrame] | None, column: str
    ) -> dict[str, pd.DatetimeIndex] | None:
        if histories is None:
            return None
        result: dict[str, pd.DatetimeIndex] = {}
        for symbol, frame in histories.items():
            values = pd.DatetimeIndex(pd.to_datetime(frame[column], utc=True))
            if not values.is_monotonic_increasing:
                raise StrategySandboxError(f"canonical {column} history is not sorted")
            result[symbol] = values
        return result

    @staticmethod
    def _history_end(
        values: pd.DatetimeIndex,
        cutoff: pd.Timestamp,
        *,
        side: str,
    ) -> int:
        return int(values.searchsorted(cutoff, side=side))

    @staticmethod
    def _validate_context_boundary(
        context_frame: pd.DataFrame,
        canonical_frame: pd.DataFrame,
        length: int,
        *,
        symbol: str,
        label: str,
    ) -> None:
        if tuple(str(column) for column in context_frame.columns) != tuple(
            str(column) for column in canonical_frame.columns
        ):
            raise StrategySandboxError(f"authoritative {label} schema changed for {symbol}")
        if len(context_frame) != length:
            raise StrategySandboxError(f"authoritative {label} history length differs for {symbol}")
        if not length:
            return
        # Worker deltas come from the private canonical snapshot copy below, never from this
        # repeatedly materialized context. Boundary checks still fail closed on truncation,
        # reorder, or replacement at either edge without hashing the full prefix every decision.
        for offset in (0, length - 1):
            left = context_frame.iloc[offset]
            right = canonical_frame.iloc[offset]
            if not left.equals(right):
                raise StrategySandboxError(
                    f"authoritative {label} history boundary changed for {symbol}"
                )

    @staticmethod
    def _tail(
        frame: pd.DataFrame,
        *,
        symbol: str,
        cursor: int,
        columns: tuple[str, ...],
        label: str,
    ) -> list[list[Any]]:
        if tuple(str(column) for column in frame.columns) != columns:
            raise StrategySandboxError(f"authoritative {label} schema changed for {symbol}")
        if len(frame) < cursor:
            raise StrategySandboxError(f"authoritative {label} history shrank for {symbol}")
        return _encoded_rows(frame.iloc[cursor:], columns)

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        if seed != self.seed:
            raise StrategySandboxError("trusted target generator changed the strategy seed")
        if context.auxiliary:
            raise StrategySandboxError("worker protocol does not accept auxiliary datasets")
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")
        if self.previous_decision is not None and decision_time <= self.previous_decision:
            raise StrategySandboxError("trusted target generator emitted unordered decisions")
        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)):
            raise StrategySandboxError("trusted target generator emitted duplicate symbols")
        eligible_set = set(eligible)
        context_bar_symbols = {str(symbol) for symbol in context.bars}
        if context_bar_symbols != eligible_set:
            raise StrategySandboxError(
                "trusted bar context must contain exactly the eligible symbols"
            )
        bar_updates: dict[str, list[list[Any]]] = {}
        funding_updates: dict[str, list[list[Any]]] = {}
        if self.bar_history is not None:
            assert self.bar_times is not None
            assert self.funding_history is not None
            assert self.funding_times is not None
            closed_cutoff = decision_time - self.interval
            for symbol in eligible:
                history = self.bar_history.get(symbol)
                times = self.bar_times.get(symbol)
                if history is None or times is None:
                    raise StrategySandboxError(
                        f"eligible symbol has no canonical bar history: {symbol}"
                    )
                stop = self._history_end(times, closed_cutoff, side="right")
                self._validate_context_boundary(
                    context.bars[symbol], history, stop, symbol=symbol, label="bar"
                )
                cursor = self.bar_cursors.get(symbol, 0)
                if stop < cursor:
                    raise StrategySandboxError(f"canonical bar history shrank for {symbol}")
                update = _encoded_rows(history.iloc[cursor:stop], self.bar_columns)
                if update:
                    bar_updates[symbol] = update
                self.bar_cursors[symbol] = stop

            if tuple(str(column) for column in context.funding.columns) != self.funding_columns:
                raise StrategySandboxError("authoritative funding schema changed")
            expected_funding_rows = 0
            for symbol in eligible:
                history = self.funding_history.get(symbol)
                times = self.funding_times.get(symbol)
                if history is None or times is None:
                    continue
                stop = self._history_end(times, decision_time, side="left")
                expected_funding_rows += stop
                cursor = self.funding_cursors.get(symbol, 0)
                if stop < cursor:
                    raise StrategySandboxError(f"canonical funding history shrank for {symbol}")
                update = _encoded_rows(history.iloc[cursor:stop], self.funding_columns)
                if update:
                    funding_updates[symbol] = update
                self.funding_cursors[symbol] = stop
            if len(context.funding) != expected_funding_rows:
                raise StrategySandboxError("authoritative funding history length differs")
        else:
            for raw_symbol, frame in context.bars.items():
                symbol = str(raw_symbol)
                cursor = self.bar_cursors.get(symbol, 0)
                update = self._tail(
                    frame,
                    symbol=symbol,
                    cursor=cursor,
                    columns=self.bar_columns,
                    label="bar",
                )
                if update:
                    bar_updates[symbol] = update
                self.bar_cursors[symbol] = len(frame)
            if not context.funding.empty:
                for raw_symbol, frame in context.funding.groupby(
                    "symbol", observed=True, sort=False
                ):
                    symbol = str(raw_symbol)
                    if symbol not in eligible_set:
                        raise StrategySandboxError(
                            "trusted funding context includes an ineligible symbol"
                        )
                    cursor = self.funding_cursors.get(symbol, 0)
                    update = self._tail(
                        frame,
                        symbol=symbol,
                        cursor=cursor,
                        columns=self.funding_columns,
                        label="funding",
                    )
                    if update:
                        funding_updates[symbol] = update
                    self.funding_cursors[symbol] = len(frame)
        response = self.worker.request(
            {
                "type": "decision",
                "decision_time": decision_time.isoformat(),
                "eligible_symbols": list(eligible),
                "bars": bar_updates,
                "funding": funding_updates,
            }
        )
        self.previous_decision = decision_time
        return _validated_worker_weights(response, eligible)


def _generate_targets_in_worker(
    root: Path,
    team_id: str,
    entrypoint: str | Path,
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    decision_times: Sequence[pd.Timestamp],
    *,
    seed: int,
    interval_hours: int,
    expected_source_bundle_sha256: str | None = None,
    expected_source_entries: Sequence[Mapping[str, object]] | None = None,
    archived_files: Sequence[source_archive_v4.SourceFile] | None = None,
) -> pd.DataFrame:
    worker, sandbox = _launch_strategy_worker(
        root,
        entrypoint,
        team_id,
        seed,
        expected_source_bundle_sha256,
        expected_source_entries,
        archived_files,
    )
    try:
        canonical_bars = _normalise_bars(bars)
        canonical_funding = _normalise_funding(funding)
        bar_schema = canonical_bars.iloc[0:0]
        funding_schema = canonical_funding.iloc[0:0]
        proxy = _WorkerStrategyProxy(
            worker,
            seed=seed,
            interval_hours=interval_hours,
            bar_schema=bar_schema,
            funding_schema=funding_schema,
            bar_history=canonical_bars,
            funding_history=canonical_funding,
        )
        targets = generate_targets(
            proxy,
            bars,
            funding,
            membership,
            decision_times,
            seed=seed,
            interval_hours=interval_hours,
        )
    except BaseException:
        worker.abort()
        raise
    else:
        worker.finish()
        return targets
    finally:
        sandbox.cleanup()


def _load_config(path: Path, team_id: str) -> dict[str, Any]:
    loaded = tournament_contract.load_config(path, root=path.parents[2])
    config = dict(loaded.raw)
    if team_id not in config["teams"]:
        raise ValueError(f"{team_id} is not registered in the tournament config")
    strategy_seed = int(config["research"]["strategy_seed"])
    if not 0 <= strategy_seed <= 2**32 - 1:
        raise ValueError("research.strategy_seed must fit PYTHONHASHSEED's integer range")
    return config


def _authorized_window(config: Mapping[str, Any], stage: str) -> AuthorizedWindow:
    splits = config["splits"]
    replay_start = str(splits["is"]["start"])
    if stage in {"is", "historical_oos"}:
        score_start = str(splits[stage]["start"])
        end_exclusive = str(splits[stage]["end_exclusive"])
    else:
        raise ValueError("runner stage must be is or historical_oos")
    score_end = (_as_utc_timestamp(end_exclusive) - pd.Timedelta(days=1)).date().isoformat()
    return AuthorizedWindow(
        stage=stage,
        replay_start=replay_start,
        end_exclusive=end_exclusive,
        score_start=score_start,
        score_end_inclusive=score_end,
    )


def _evaluator_config(config: Mapping[str, Any]) -> EvaluatorConfig:
    execution = config["execution"]
    return EvaluatorConfig(
        interval_hours=8,
        initial_equity=float(execution["initial_equity_usdt"]),
        taker_fee_bps_per_side=float(execution["taker_fee_bps_per_side"]),
        slippage_bps_per_side=float(execution["slippage_bps_per_side"]),
        max_gross_exposure=float(execution["max_gross_exposure"]),
        max_abs_net_exposure=float(execution["max_abs_net_exposure"]),
        max_symbol_exposure=float(execution["max_symbol_exposure"]),
        max_bar_participation=float(execution["max_bar_participation"]),
    )


def _decision_grid(authorized: AuthorizedWindow) -> pd.DatetimeIndex:
    start = _as_utc_timestamp(authorized.replay_start)
    end = _as_utc_timestamp(authorized.end_exclusive)
    return pd.date_range(start, end, freq=_INTERVAL, inclusive="left")


def _load_verified_snapshot(root: Path, manifest_path: Path) -> _SnapshotData:
    """Verify every manifest entry directly before loading the five V4 datasets."""

    try:
        manifest_payload = _stable_binary_file_bytes(manifest_path, maximum=2 * 1024 * 1024)
        manifest = _strict_json_loads(manifest_payload, "snapshot manifest")
    except ValueError as exc:
        raise ValueError(f"cannot read snapshot manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("snapshot manifest root must be an object")
    raw_entries = manifest.get("files", manifest.get("entries"))
    if not isinstance(raw_entries, list):
        raise ValueError("snapshot manifest must contain a files or entries list")

    entries: list[tuple[Mapping[str, Any], Path]] = []
    seen_paths: set[Path] = set()
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"snapshot manifest entry {index} must be an object")
        path_value = raw_entry.get("path")
        size = raw_entry.get("size")
        sha256 = raw_entry.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError(f"snapshot manifest entry {index} has no path")
        pure_path = PurePosixPath(path_value)
        if pure_path.is_absolute() or ".." in pure_path.parts or "." in pure_path.parts:
            raise ValueError(f"unsafe snapshot path: {path_value}")
        raw_path = root / Path(*pure_path.parts)
        path = raw_path.resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"snapshot path escapes tournament root: {path_value}")
        if path in seen_paths:
            raise ValueError(f"duplicate snapshot manifest path: {path_value}")
        seen_paths.add(path)
        if _has_symlink_component(root, raw_path) or not path.is_file():
            raise ValueError(f"snapshot file does not exist: {path_value}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"snapshot entry has invalid size: {path_value}")
        if path.stat().st_size != size:
            raise ValueError(f"snapshot size mismatch: {path_value}")
        if not isinstance(sha256, str) or not _SHA256.fullmatch(sha256):
            raise ValueError(f"snapshot entry has invalid sha256: {path_value}")
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != sha256:
            raise ValueError(
                f"snapshot sha256 mismatch for {path_value}: {actual_sha256} != {sha256}"
            )
        entries.append((raw_entry, path))

    paths = {name: _resolve_dataset_entry(name, entries) for name in _REQUIRED_DATASETS}
    if len(set(paths.values())) != len(paths):
        raise ValueError("required logical datasets must resolve to distinct files")
    entry_hashes = {path: str(entry["sha256"]) for entry, path in entries}
    frames: dict[str, pd.DataFrame] = {}
    for name, path in paths.items():
        payload = _stable_binary_file_bytes(path, maximum=256 * 1024 * 1024)
        if hashlib.sha256(payload).hexdigest() != entry_hashes[path]:
            raise ValueError(f"snapshot file changed before parsing: {name}")
        frames[name] = pd.read_parquet(io.BytesIO(payload))
    return _SnapshotData(
        manifest_sha256=hashlib.sha256(manifest_payload).hexdigest(),
        paths=paths,
        file_hashes=entry_hashes,
        bars=frames["bars"],
        funding=frames["funding"],
        mark_prices=frames["mark_prices"],
        membership=frames["membership"],
        contract_metadata=frames["contract_metadata"],
    )


def _verify_snapshot_files_unchanged(snapshot: _SnapshotData) -> None:
    """Rehash every manifest-listed file after team code and before publication."""
    for path, expected_sha256 in sorted(
        snapshot.file_hashes.items(), key=lambda item: item[0].as_posix()
    ):
        if not path.is_file():
            raise ValueError(f"snapshot file disappeared during team run: {path}")
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise ValueError(f"snapshot file changed during team run: {path}")


def _resolve_dataset_entry(
    logical_name: str, entries: list[tuple[Mapping[str, Any], Path]]
) -> Path:
    explicit: list[Path] = []
    for entry, path in entries:
        values = (entry.get("dataset"), entry.get("name"))
        if any(_normalise_dataset_name(value) == logical_name for value in values):
            explicit.append(path)
    if len(explicit) > 1:
        raise ValueError(f"ambiguous explicit snapshot dataset: {logical_name}")
    if explicit:
        selected = explicit[0]
    else:
        basename = _DATASET_BASENAMES[logical_name]
        matches = [path for _, path in entries if path.name == basename]
        if len(matches) != 1:
            qualifier = "missing" if not matches else "ambiguous"
            raise ValueError(f"{qualifier} snapshot dataset: {logical_name}")
        selected = matches[0]
    if selected.suffix.lower() != ".parquet":
        raise ValueError(f"snapshot dataset {logical_name} must be Parquet")
    return selected


def _normalise_dataset_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    name = PurePosixPath(value).name.lower()
    if name.endswith(".parquet"):
        name = name[: -len(".parquet")]
    return name.replace("-", "_")


def _validate_snapshot_bounds(
    snapshot: _SnapshotData,
    config: Mapping[str, Any],
    decision_times: pd.DatetimeIndex,
) -> None:
    hard_end_exclusive = _as_utc_timestamp(config["data"]["hard_end_exclusive"])
    bars = snapshot.bars
    funding = snapshot.funding
    mark_prices = snapshot.mark_prices
    membership = snapshot.membership
    required_bars = {"open_time", "symbol", "open", "close", "quote_volume"}
    required_funding = {"funding_time", "symbol", "funding_rate", "mark_price"}
    required_mark_prices = {"mark_time", "symbol", "mark_price"}
    required_membership = {
        "reconstitution_time",
        "symbol",
        "liquidity_rank",
        "trailing_quote_volume",
    }
    for name, frame, required in (
        ("bars", bars, required_bars),
        ("funding", funding, required_funding),
        ("mark_prices", mark_prices, required_mark_prices),
        ("membership", membership, required_membership),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"snapshot {name} missing columns: {sorted(missing)}")
    if snapshot.contract_metadata.empty:
        raise ValueError("snapshot contract_metadata cannot be empty")

    bar_times = pd.to_datetime(bars["open_time"], utc=True, errors="raise")
    funding_times = pd.to_datetime(funding["funding_time"], utc=True, errors="raise")
    mark_times = pd.to_datetime(mark_prices["mark_time"], utc=True, errors="raise")
    membership_times = pd.to_datetime(membership["reconstitution_time"], utc=True, errors="raise")
    if (bar_times >= hard_end_exclusive).any():
        raise ValueError("snapshot bars cross the hard end-exclusive boundary")
    if (funding_times >= hard_end_exclusive).any():
        raise ValueError("snapshot funding crosses the hard end-exclusive boundary")
    if (mark_times >= hard_end_exclusive).any():
        raise ValueError("snapshot mark prices cross the hard end-exclusive boundary")
    if (membership_times >= hard_end_exclusive).any():
        raise ValueError("snapshot membership crosses the hard end-exclusive boundary")
    if mark_prices.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("snapshot mark prices contain duplicate boundaries")
    aligned_marks = (
        (mark_times.dt.minute == 0)
        & (mark_times.dt.second == 0)
        & (mark_times.dt.microsecond == 0)
        & (mark_times.dt.hour % 8 == 0)
    )
    if not aligned_marks.all():
        raise ValueError("snapshot mark prices must be exact 8h UTC boundaries")
    numeric_marks = pd.to_numeric(mark_prices["mark_price"], errors="raise")
    if not np.isfinite(numeric_marks.to_numpy()).all() or (numeric_marks <= 0.0).any():
        raise ValueError("snapshot mark prices must be finite and positive")
    available_bar_times = pd.DatetimeIndex(bar_times.unique()).sort_values()
    missing_decisions = decision_times.difference(available_bar_times)
    if len(missing_decisions):
        raise ValueError(
            f"snapshot has {len(missing_decisions)} decision timestamps without any bar open"
        )

    warmup_start = _as_utc_timestamp(config["data"]["warmup_start"])
    expected_btc_times = pd.date_range(
        warmup_start, hard_end_exclusive, freq=_INTERVAL, inclusive="left"
    )
    btc_times = pd.DatetimeIndex(
        bar_times.loc[bars["symbol"].astype(str).eq("BTCUSDT")]
    ).sort_values()
    if btc_times.duplicated().any() or not btc_times.equals(expected_btc_times):
        raise ValueError("BTCUSDT must have one complete 8h bar grid from warmup through cutoff")


def _canonical_targets(
    raw: pd.DataFrame, bars: pd.DataFrame, decision_times: pd.DatetimeIndex
) -> pd.DataFrame:
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("generate_targets must return a DataFrame")
    targets = raw.copy()
    targets.index = pd.to_datetime(targets.index, utc=True)
    if targets.index.duplicated().any() or not targets.index.equals(decision_times):
        raise ValueError("strategy targets must contain exactly the canonical 8h decision grid")
    if targets.columns.duplicated().any():
        raise ValueError("strategy targets contain duplicate symbols")
    bar_symbols = set(bars["symbol"].astype(str))
    if REBALANCE_INSTRUCTION_COLUMN in bar_symbols:
        raise ValueError("bars contain the reserved rebalance instruction symbol")
    targets.columns = [str(name) for name in targets.columns]
    if targets.columns.duplicated().any():
        raise ValueError("strategy targets contain duplicate symbols after normalization")
    if REBALANCE_INSTRUCTION_COLUMN in targets:
        instructions = targets.pop(REBALANCE_INSTRUCTION_COLUMN)
        if instructions.isna().any() or not pd.api.types.is_bool_dtype(instructions.dtype):
            raise ValueError("strategy rebalance instructions must be Boolean")
        instructions = instructions.astype(bool)
    else:
        # Compatibility for direct/focused generators; canonical artifacts always gain the flag.
        instructions = pd.Series(True, index=targets.index, dtype=bool)
    columns = sorted(bar_symbols | {str(name) for name in targets.columns})
    targets = targets.reindex(columns=columns, fill_value=0.0)
    targets = targets.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(targets.to_numpy()).all():
        raise ValueError("strategy targets contain NaN or infinite values")
    targets.insert(0, REBALANCE_INSTRUCTION_COLUMN, instructions.to_numpy(dtype=bool))
    targets.index.name = "timestamp"
    return targets


def _validate_evaluation_grids(
    base: EvaluationResult,
    stressed: EvaluationResult,
    triple: EvaluationResult,
    decision_times: pd.DatetimeIndex,
) -> None:
    for label, result in (
        ("base", base),
        ("double-cost", stressed),
        ("triple-cost", triple),
    ):
        if not isinstance(result, EvaluationResult):
            raise TypeError(f"{label} evaluator did not return EvaluationResult")
        for artifact_name, frame in (
            ("returns", result.returns),
            ("positions", result.positions),
        ):
            index = pd.DatetimeIndex(pd.to_datetime(frame.index, utc=True))
            if index.duplicated().any() or not index.equals(decision_times):
                raise ValueError(
                    f"{label} {artifact_name} must contain exactly the canonical 8h grid"
                )


def _canonical_daily_returns(
    returns: pd.DataFrame, label: str, authorized: AuthorizedWindow
) -> pd.Series:
    if "net_return" not in returns:
        raise ValueError(f"{label} evaluator returns are missing net_return")
    daily = aggregate_daily_returns(returns["net_return"])
    expected = pd.date_range(
        _as_utc_timestamp(authorized.replay_start),
        _as_utc_timestamp(authorized.score_end_inclusive),
        freq="1D",
    )
    if not daily.index.equals(expected):
        raise ValueError(f"{label} daily returns do not cover the canonical daily grid")
    return daily


def _btc_daily_returns(
    bars: pd.DataFrame,
    config: Mapping[str, Any],
    authorized: AuthorizedWindow,
) -> pd.Series:
    btc = bars.loc[bars["symbol"].astype(str).eq("BTCUSDT"), ["open_time", "close"]].copy()
    btc["open_time"] = pd.to_datetime(btc["open_time"], utc=True)
    btc["close"] = pd.to_numeric(btc["close"], errors="raise")
    btc = btc.sort_values("open_time").set_index("open_time")
    daily_close = btc["close"].resample("1D").last()
    if daily_close.isna().any() or (daily_close <= 0.0).any():
        raise ValueError("BTCUSDT daily closes are incomplete or invalid")
    returns = daily_close.pct_change(fill_method=None).dropna().rename("btc_return")
    expected = pd.date_range(
        _as_utc_timestamp(authorized.replay_start),
        _as_utc_timestamp(authorized.score_end_inclusive),
        freq="1D",
    )
    scored = returns.reindex(expected)
    if scored.isna().any():
        raise ValueError("BTCUSDT daily returns do not cover the scored period")
    warmup_start = _as_utc_timestamp(config["data"]["warmup_start"])
    score_end = _as_utc_timestamp(authorized.score_end_inclusive)
    return returns.loc[warmup_start:score_end]


def _compute_metrics(
    base_daily: pd.Series,
    stressed_daily: pd.Series,
    triple_daily: pd.Series,
    btc_daily: pd.Series,
    config: Mapping[str, Any],
    authorized: AuthorizedWindow,
) -> dict[str, Any]:
    score_start = _as_utc_timestamp(authorized.score_start)
    score_end = _as_utc_timestamp(authorized.score_end_inclusive)
    scored = base_daily.loc[score_start:score_end]
    stressed_scored = stressed_daily.loc[score_start:score_end]
    triple_scored = triple_daily.loc[score_start:score_end]
    labels = classify_btc_regimes(btc_daily).loc[score_start:score_end]
    if not labels.index.equals(scored.index) or labels.notna().sum() == 0:
        raise ValueError(f"BTC regime labels do not cover the exact {authorized.stage} grid")
    statistics = config["statistics"]
    interval_kwargs = {
        "samples": int(statistics["bootstrap_samples"]),
        "block_days": int(statistics["bootstrap_block_days"]),
        "seed": int(statistics["bootstrap_seed"]),
    }
    scored_metrics = compute_window_metrics(scored)
    return {
        "scored_window": EvaluationWindow(
            authorized.score_start,
            authorized.score_end_inclusive,
            WindowMetrics(**dataclasses.asdict(scored_metrics)),
        ),
        "double_cost_sharpe": compute_window_metrics(stressed_scored).net_sharpe,
        "triple_cost_sharpe": compute_window_metrics(triple_scored).net_sharpe,
        "regime_sharpe": dict(compute_regime_sharpes(scored, labels)),
        "net_sharpe_confidence_interval": sharpe_confidence_interval(scored, **interval_kwargs),
        "double_cost_sharpe_confidence_interval": sharpe_confidence_interval(
            stressed_scored, **interval_kwargs
        ),
    }


def _publish_artifacts(
    root: Path,
    team_id: str,
    *,
    stage: str,
    output_relative: str,
    targets: pd.DataFrame,
    base: EvaluationResult,
    stressed: EvaluationResult,
    triple: EvaluationResult,
    base_daily: pd.Series,
    stressed_daily: pd.Series,
    triple_daily: pd.Series,
) -> dict[str, str]:
    raw_output_dir = root / output_relative
    if _has_symlink_component(root, raw_output_dir):
        raise ValueError("report path contains a symlink")
    output_dir = raw_output_dir.resolve()
    report_parent = output_dir.parent
    if not report_parent.is_relative_to(root):
        raise ValueError("report directory escapes tournament root")
    report_parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("team report path must be a directory")
    staging = Path(tempfile.mkdtemp(prefix=f".{team_id}-", dir=report_parent))
    files = {
        "targets": "targets.parquet",
        "events": "events.parquet",
        "positions": "positions.parquet",
        "evaluator_returns": "bar_returns.csv",
        "double_cost_evaluator_returns": "double_cost_bar_returns.csv",
        "triple_cost_evaluator_returns": "triple_cost_bar_returns.csv",
        "daily_returns": "daily_returns.csv",
        "double_cost_daily_returns": "double_cost_daily_returns.csv",
        "triple_cost_daily_returns": "triple_cost_daily_returns.csv",
        "trades": "trades.csv",
    }
    try:
        _write_parquet(_indexed_frame(targets, "timestamp"), staging / files["targets"])
        events = _canonical_events(base.events)
        _write_parquet(events, staging / files["events"])
        _write_parquet(_indexed_frame(base.positions, "timestamp"), staging / files["positions"])
        _write_csv(
            _indexed_frame(base.returns, "timestamp"),
            staging / files["evaluator_returns"],
        )
        _write_csv(
            _indexed_frame(stressed.returns, "timestamp"),
            staging / files["double_cost_evaluator_returns"],
        )
        _write_csv(
            _indexed_frame(triple.returns, "timestamp"),
            staging / files["triple_cost_evaluator_returns"],
        )
        _write_csv(
            pd.DataFrame({"date": base_daily.index, "net_return": base_daily.to_numpy()}),
            staging / files["daily_returns"],
        )
        _write_csv(
            pd.DataFrame({"date": stressed_daily.index, "net_return": stressed_daily.to_numpy()}),
            staging / files["double_cost_daily_returns"],
        )
        _write_csv(
            pd.DataFrame({"date": triple_daily.index, "net_return": triple_daily.to_numpy()}),
            staging / files["triple_cost_daily_returns"],
        )
        _write_csv(_trade_events(events), staging / files["trades"])
        _promote_report_directory(staging, output_dir, allow_replace=False)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {name: f"{output_relative}/{filename}" for name, filename in files.items()}


def _stage_output_prefix(team_id: str, stage: str) -> str:
    TOP40_V4_LAYOUT.require_team(team_id)
    if stage == "is":
        return f"{TOP40_V4_LAYOUT.reports_root}/is/{team_id}/"
    if stage == "historical_oos":
        return f"{TOP40_V4_LAYOUT.tournament_root}/private/historical-oos/{team_id}/"
    raise ValueError("runner stage must be is or historical_oos")


def _historical_publication_prefix(team_id: str) -> str:
    """Canonical public namespace reserved for the atomic championship release."""

    TOP40_V4_LAYOUT.require_team(team_id)
    return f"{TOP40_V4_LAYOUT.reports_root}/historical-oos/{team_id}/"


def _validated_output_relative(team_id: str, stage: str, override: str | None) -> str:
    prefix = _stage_output_prefix(team_id, stage)
    if not isinstance(override, str) or not override:
        raise ValueError("every V4 run requires a unique organizer output path")
    pure = PurePosixPath(override)
    if (
        pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() == prefix.removesuffix("/")
        or not pure.as_posix().startswith(prefix)
    ):
        raise ValueError(f"{stage} output must remain under its canonical V4 stage prefix")
    return pure.as_posix()


def _indexed_frame(frame: pd.DataFrame, index_name: str) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.to_datetime(result.index, utc=True)
    result = result.sort_index()
    result.index.name = index_name
    return result.reset_index()


def _canonical_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy()
    for column in _EVENT_COLUMNS:
        if column not in frame:
            dtype = "datetime64[ns, UTC]" if column == "timestamp" else object
            frame[column] = pd.Series(dtype=dtype)
    frame = frame.loc[:, _EVENT_COLUMNS]
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.sort_values(
            ["timestamp", "symbol", "event_type", "phase"], kind="mergesort"
        ).reset_index(drop=True)
    return frame


def _trade_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = _canonical_events(events)
    return frame.loc[frame["event_type"].isin(_TRADE_EVENT_TYPES)].reset_index(drop=True)


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    frame.to_parquet(path, engine="pyarrow", compression="zstd", index=False)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    output = frame.copy()
    for column in output.columns:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_dtype(
            output[column].dtype
        ):
            timestamps = pd.to_datetime(output[column], utc=True)
            if column == "date":
                output[column] = timestamps.dt.strftime("%Y-%m-%d")
            else:
                output[column] = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    output.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def _promote_report_directory(staging: Path, output_dir: Path, *, allow_replace: bool) -> None:
    _fsync_report_tree(staging)
    if not output_dir.exists():
        os.replace(staging, output_dir)
        _fsync_directory(output_dir.parent)
        return
    if not allow_replace:
        raise FileExistsError(f"immutable tournament output already exists: {output_dir}")
    backup = output_dir.parent / f".{output_dir.name}-backup"
    if backup.exists():
        raise FileExistsError(f"stale report backup exists: {backup}")
    os.replace(output_dir, backup)
    _fsync_directory(output_dir.parent)
    try:
        os.replace(staging, output_dir)
        _fsync_directory(output_dir.parent)
    except BaseException:
        os.replace(backup, output_dir)
        _fsync_directory(output_dir.parent)
        raise
    shutil.rmtree(backup)
    _fsync_directory(output_dir.parent)


def _fsync_report_tree(directory: Path) -> None:
    """Durably flush one generated flat report tree before atomic promotion."""

    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("report staging path must be a regular directory")
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"report staging contains an unsafe entry: {path.name}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError(f"report staging entry is not regular: {path.name}")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    _fsync_directory(directory)


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sha256_file(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("authority path is not a regular file")
            digest = hashlib.sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot stably hash authority file: {path}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        before_identity != after_identity
        or after_identity != path_identity
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise ValueError("authority file changed while being hashed")
    return digest.hexdigest()


def _stable_binary_file_bytes(path: Path, *, maximum: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise ValueError("authority file is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot stably read authority file: {path}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        len(payload) > maximum
        or before_identity != after_identity
        or after_identity != path_identity
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise ValueError("authority file changed while being read")
    return payload


def _as_utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _evaluator_authority_sha256(root: Path) -> str:
    authority: dict[str, str] = {}
    for relative in _EVALUATOR_AUTHORITY_PATHS:
        raw_path = root / relative
        path = raw_path.resolve()
        if (
            _has_symlink_component(root, raw_path)
            or not path.is_relative_to(root)
            or not path.is_file()
        ):
            raise ValueError(f"evaluator authority is missing or unsafe: {relative}")
        authority[relative] = _sha256_file(path)
    payload = json.dumps(
        authority,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
