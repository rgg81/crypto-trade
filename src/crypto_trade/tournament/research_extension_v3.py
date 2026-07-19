"""Outcome-blind post-tournament research controls for Top-40 V3 Teams 04 and 06."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament import (
    metrics_v3,
    orchestrator_v3,
    research_extension_v3_compat,
    runner_v3,
    top40_v3,
)

EXTENSION_ROOT = "tournament/top40-v3-research-extension"
POLICY_PATH = f"{EXTENSION_ROOT}/policy.json"
ACTIVATION_PATH = f"{EXTENSION_ROOT}/activation-freeze.json"
AMENDMENT_0001_PATH = f"{EXTENSION_ROOT}/amendments/0001/activation-freeze.json"
JOURNAL_PATH = f"{EXTENSION_ROOT}/research-journal.jsonl"
FINALIST_PATH = f"{EXTENSION_ROOT}/finalists.json"
LOCK_PATH = f"{EXTENSION_ROOT}/.result-command.lock"
REPORTS_ROOT = "reports-top40-v3-research-extension"
V3_CONFIG_PATH = "tournament/top40-v3/config.toml"
DATA_MANIFEST_PATH = "tournament/top40/data_manifest.json"
ZERO_SHA256 = "0" * 64
JOURNAL_SCHEMA = "top40-v3-post-tournament-research-journal-v1"
ACTIVATION_SCHEMA = "top40-v3-post-tournament-activation-v1"
FINALIST_SCHEMA = "top40-v3-post-tournament-finalists-v1"

_SHA256 = re.compile(r"[0-9a-f]{64}")
_TEAM_ID = re.compile(r"team-(?:04|06)")
_CANDIDATE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


class ResearchExtensionError(RuntimeError):
    """The extension authority, lifecycle, or evidence is invalid."""


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateSpec:
    team_id: str
    candidate_id: str
    candidate_root: str
    entrypoint_name: str
    parameters: Mapping[str, object]

    @property
    def entrypoint(self) -> str:
        return f"{self.candidate_root}/{self.entrypoint_name}"


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ResearchExtensionError("value is not canonical finite JSON") from exc


def _pretty_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ResearchExtensionError("value is not finite JSON") from exc


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_root(root: str | Path) -> Path:
    path = Path(root).resolve()
    if not path.is_dir():
        raise ResearchExtensionError(f"repository root does not exist: {path}")
    return path


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ResearchExtensionError(f"{label} must be a POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ResearchExtensionError(f"{label} must be a normalized relative path")
    if path.as_posix() != value:
        raise ResearchExtensionError(f"{label} is not normalized")
    return value


def _path(root: Path, relative: str) -> Path:
    relative = _safe_relative(relative, "path")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ResearchExtensionError("path escapes repository root")
    return result


def _read_bytes(root: Path, relative: str) -> bytes:
    path = _path(root, relative)
    if path.is_symlink() or not path.is_file():
        raise ResearchExtensionError(f"required regular file is missing: {relative}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ResearchExtensionError(f"cannot read {relative}: {exc}") from exc


def _read_object(root: Path, relative: str) -> Mapping[str, Any]:
    payload = _read_bytes(root, relative)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchExtensionError(f"invalid JSON object: {relative}") from exc
    if not isinstance(value, Mapping):
        raise ResearchExtensionError(f"JSON value is not an object: {relative}")
    return value


def _write_atomic(root: Path, relative: str, payload: bytes) -> None:
    path = _path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def _validate_policy(policy: Mapping[str, Any]) -> None:
    exact = {
        ("schema_version",): "top40-v3-post-tournament-research-policy-v1",
        ("study_id",): "top40-v3-post-tournament-team04-team06-r1",
        ("parent_evidence_commit",): "7d3cf661",
        ("development", "start"): "2020-02-03T00:00:00Z",
        ("development", "end_exclusive"): "2023-07-01T00:00:00Z",
        ("development", "runner_stage"): "public",
        ("historical_qualifier", "start"): "2023-07-01T00:00:00Z",
        ("historical_qualifier", "end_exclusive"): "2024-07-01T00:00:00Z",
        ("historical_qualifier", "runner_stage"): "private",
        ("historical_qualifier", "maximum_attempts_per_finalist"): 1,
        ("historical_qualifier", "feedback"): "pass-fail-only",
        ("final_oos", "start"): "2024-07-01T00:00:00Z",
        ("final_oos", "end_exclusive"): "2026-07-01T00:00:00Z",
        ("final_oos", "runner_stage"): "final_oos",
        ("final_oos", "maximum_observations_per_finalist"): 1,
        ("final_oos", "interim_disclosure"): False,
    }
    for path, expected in exact.items():
        value: object = policy
        for part in path:
            if not isinstance(value, Mapping) or part not in value:
                raise ResearchExtensionError(f"policy is missing {'.'.join(path)}")
            value = value[part]
        if value != expected:
            raise ResearchExtensionError(f"policy changed frozen field {'.'.join(path)}")
    roots = policy.get("candidate_roots")
    matrix = policy.get("candidate_matrix")
    if not isinstance(roots, Mapping) or not isinstance(matrix, Mapping):
        raise ResearchExtensionError("policy candidate authority is malformed")
    for team_id in ("team-04", "team-06"):
        root = roots.get(team_id)
        rows = matrix.get(team_id)
        if not isinstance(root, str) or not root.startswith(
            f"tournament/top40-v3/teams/{team_id}/post-tournament-"
        ):
            raise ResearchExtensionError(f"{team_id} candidate root is outside its lane")
        if not isinstance(rows, list) or len(rows) != 6:
            raise ResearchExtensionError(f"{team_id} must have exactly six declared variants")
        candidate_ids: set[str] = set()
        entrypoints: set[str] = set()
        for row in rows:
            if not isinstance(row, Mapping):
                raise ResearchExtensionError("candidate matrix row is not an object")
            candidate_id = row.get("candidate_id")
            entrypoint = row.get("entrypoint")
            parameters = row.get("parameters")
            if (
                not isinstance(candidate_id, str)
                or _CANDIDATE_ID.fullmatch(candidate_id) is None
                or not isinstance(entrypoint, str)
                or "/" in entrypoint
                or not entrypoint.endswith(".py")
                or not isinstance(parameters, Mapping)
            ):
                raise ResearchExtensionError("candidate matrix row is malformed")
            if candidate_id in candidate_ids or entrypoint in entrypoints:
                raise ResearchExtensionError("candidate matrix identity is duplicated")
            candidate_ids.add(candidate_id)
            entrypoints.add(entrypoint)
    folds = policy["development"].get("folds")
    if not isinstance(folds, list) or [row.get("name") for row in folds] != [
        "2020",
        "2021",
        "2022",
        "2023H1",
    ]:
        raise ResearchExtensionError("development folds differ from the frozen four-fold map")


def load_policy(root: str | Path = ".") -> Mapping[str, Any]:
    root_path = _safe_root(root)
    policy = _read_object(root_path, POLICY_PATH)
    _validate_policy(policy)
    return policy


def _authority_files(
    root: Path,
    activation: Mapping[str, Any],
    amendment: Mapping[str, Any],
) -> None:
    base_files = activation.get("authority_files")
    replacements = amendment.get("replacement_authority_files")
    additions = amendment.get("additional_authority_files")
    if (
        not isinstance(base_files, Mapping)
        or not isinstance(replacements, Mapping)
        or not isinstance(additions, Mapping)
    ):
        raise ResearchExtensionError("activation authority maps are malformed")
    if not set(replacements).issubset(base_files):
        raise ResearchExtensionError("amendment replaces an unknown base authority")
    if set(additions) & set(base_files):
        raise ResearchExtensionError("amendment addition collides with a base authority")
    files = {**dict(base_files), **dict(replacements), **dict(additions)}
    if not isinstance(files, Mapping) or not files:
        raise ResearchExtensionError("activation authority_files is empty")
    for relative, expected in files.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or _SHA256.fullmatch(expected) is None
        ):
            raise ResearchExtensionError("activation file binding is malformed")
        if _sha256(_read_bytes(root, relative)) != expected:
            raise ResearchExtensionError(f"activation authority changed: {relative}")


def validate(root: str | Path = ".") -> dict[str, object]:
    root_path = _safe_root(root)
    policy = load_policy(root_path)
    activation = _read_object(root_path, ACTIVATION_PATH)
    if activation.get("schema_version") != ACTIVATION_SCHEMA:
        raise ResearchExtensionError("activation freeze schema is invalid")
    if activation.get("parent_evidence_commit") != policy["parent_evidence_commit"]:
        raise ResearchExtensionError("activation parent evidence binding changed")
    policy_sha256 = _sha256(_read_bytes(root_path, POLICY_PATH))
    if activation.get("policy_sha256") != policy_sha256:
        raise ResearchExtensionError("activation policy hash changed")
    amendment = _read_object(root_path, AMENDMENT_0001_PATH)
    if (
        amendment.get("schema_version")
        != "top40-v3-post-tournament-activation-amendment-v1"
        or amendment.get("amendment_id") != "0001-pandas3-utc-metric-slice"
        or amendment.get("parent_activation_sha256")
        != _sha256(_read_bytes(root_path, ACTIVATION_PATH))
        or amendment.get("policy_sha256") != policy_sha256
    ):
        raise ResearchExtensionError("activation amendment 0001 is invalid")
    _authority_files(root_path, activation, amendment)
    config = top40_v3.load_config(_path(root_path, V3_CONFIG_PATH))
    if (
        config.raw["splits"]["validation"]["end_exclusive"]
        != policy["development"]["end_exclusive"]
        or config.raw["splits"]["private"]["start"]
        != policy["historical_qualifier"]["start"]
        or config.raw["splits"]["private"]["end_exclusive"]
        != policy["historical_qualifier"]["end_exclusive"]
        or config.raw["splits"]["final_oos"]["start"] != policy["final_oos"]["start"]
        or config.raw["splits"]["final_oos"]["end_exclusive"]
        != policy["final_oos"]["end_exclusive"]
    ):
        raise ResearchExtensionError("V3 runner windows differ from extension policy")
    return {
        "activation_sha256": _sha256(_read_bytes(root_path, ACTIVATION_PATH)),
        "activation_amendment_0001_sha256": _sha256(
            _read_bytes(root_path, AMENDMENT_0001_PATH)
        ),
        "ok": True,
        "policy_sha256": policy_sha256,
        "study_id": policy["study_id"],
    }


def _candidate_specs(policy: Mapping[str, Any]) -> tuple[CandidateSpec, ...]:
    result: list[CandidateSpec] = []
    for team_id in ("team-04", "team-06"):
        root = str(policy["candidate_roots"][team_id])
        for row in policy["candidate_matrix"][team_id]:
            result.append(
                CandidateSpec(
                    team_id=team_id,
                    candidate_id=str(row["candidate_id"]),
                    candidate_root=root,
                    entrypoint_name=str(row["entrypoint"]),
                    parameters=dict(row["parameters"]),
                )
            )
    return tuple(result)


def candidate_spec(
    policy: Mapping[str, Any], team_id: str, candidate_id: str
) -> CandidateSpec:
    if _TEAM_ID.fullmatch(team_id) is None:
        raise ResearchExtensionError("team must be team-04 or team-06")
    for spec in _candidate_specs(policy):
        if spec.team_id == team_id and spec.candidate_id == candidate_id:
            return spec
    raise ResearchExtensionError("candidate is outside the preregistered matrix")


def _validate_candidate_config(root: Path, spec: CandidateSpec) -> None:
    relative = f"{spec.candidate_root}/frozen_config.json"
    config = _read_object(root, relative)
    if (
        config.get("schema_version") != 1
        or config.get("team_id") != spec.team_id
        or config.get("candidate_id") != spec.candidate_id
        or config.get("parameters") != spec.parameters
        or not isinstance(config.get("implementation"), Mapping)
        or config["implementation"].get("entrypoint") != spec.entrypoint_name
        or not isinstance(config.get("risk_policy"), Mapping)
        or config["risk_policy"].get("path") != "risk_policy.json"
    ):
        raise ResearchExtensionError(
            "live frozen_config does not exactly select the requested matrix row"
        )


def _journal_records(root: Path) -> list[Mapping[str, Any]]:
    path = _path(root, JOURNAL_PATH)
    if not path.exists():
        return []
    if path.is_symlink() or not path.is_file():
        raise ResearchExtensionError("research journal is not a regular file")
    records: list[Mapping[str, Any]] = []
    previous = ZERO_SHA256
    for sequence, raw_line in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            record = json.loads(raw_line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchExtensionError("research journal contains invalid JSON") from exc
        if not isinstance(record, Mapping):
            raise ResearchExtensionError("research journal row is not an object")
        supplied = record.get("record_sha256")
        unsigned = dict(record)
        unsigned.pop("record_sha256", None)
        expected = _sha256(_canonical_json_bytes(unsigned))
        if (
            record.get("schema_version") != JOURNAL_SCHEMA
            or record.get("event_sequence") != sequence
            or record.get("previous_sha256") != previous
            or supplied != expected
            or _canonical_json_bytes(record) != raw_line
        ):
            raise ResearchExtensionError("research journal chain is invalid")
        records.append(record)
        previous = str(supplied)
    return records


def _append_event(root: Path, event_type: str, fields: Mapping[str, object]) -> Mapping[str, Any]:
    records = _journal_records(root)
    unsigned: dict[str, object] = {
        "accepted_at_utc": _utc_now(),
        "event_sequence": len(records) + 1,
        "event_type": event_type,
        "previous_sha256": records[-1]["record_sha256"] if records else ZERO_SHA256,
        "schema_version": JOURNAL_SCHEMA,
        **fields,
    }
    record = {**unsigned, "record_sha256": _sha256(_canonical_json_bytes(unsigned))}
    payload = _canonical_json_bytes(record) + b"\n"
    path = _path(root, JOURNAL_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "ab", closefd=True) as handle:
            if handle.write(payload) != len(payload):
                raise ResearchExtensionError("short research journal append")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        # fdopen owns the descriptor on the normal and exceptional paths.
        pass
    if _journal_records(root)[-1] != record:
        raise ResearchExtensionError("research journal append did not replay")
    return record


@contextlib.contextmanager
def _result_lock(root: Path) -> Iterator[None]:
    path = _path(root, LOCK_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ResearchExtensionError("another extension result command is active") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.fsync(descriptor)
        os.close(descriptor)
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def _result_artifact(root: Path, result: runner_v3.TeamWindowRunResult, name: str) -> Path:
    relative = result.artifacts.get(name)
    if not isinstance(relative, str):
        raise ResearchExtensionError(f"runner result lacks {name} artifact")
    path = _path(root, relative)
    if _sha256(path.read_bytes()) != result.artifact_sha256.get(name):
        raise ResearchExtensionError(f"runner artifact hash changed: {name}")
    return path


def _daily(path: Path) -> pd.Series:
    frame = pd.read_csv(path)
    if list(frame.columns) != ["date", "net_return"]:
        raise ResearchExtensionError("daily return artifact schema changed")
    index = pd.to_datetime(frame["date"], utc=True)
    values = pd.to_numeric(frame["net_return"], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ResearchExtensionError("daily return artifact contains nonfinite values")
    return pd.Series(values.to_numpy(dtype=float), index=index, name="net_return")


def _metrics_dict(values: metrics_v3.WindowMetrics) -> dict[str, float]:
    return {field.name: float(getattr(values, field.name)) for field in dataclasses.fields(values)}


def _cumulative_return(returns: pd.Series) -> float:
    return float((1.0 + returns).prod() - 1.0)


def _fold_summary(
    base: pd.Series,
    stressed: pd.Series,
    folds: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for fold in folds:
        start = pd.Timestamp(str(fold["start"]))
        end = pd.Timestamp(str(fold["end_exclusive"]))
        base_fold = base.loc[(base.index >= start) & (base.index < end)]
        stressed_fold = stressed.loc[(stressed.index >= start) & (stressed.index < end)]
        if base_fold.empty or not base_fold.index.equals(stressed_fold.index):
            raise ResearchExtensionError("development fold is incomplete")
        result.append(
            {
                "base_cumulative_return": _cumulative_return(base_fold),
                "base_metrics": _metrics_dict(metrics_v3.compute_window_metrics(base_fold)),
                "double_cost_cumulative_return": _cumulative_return(stressed_fold),
                "double_cost_metrics": _metrics_dict(
                    metrics_v3.compute_window_metrics(stressed_fold)
                ),
                "end_exclusive": str(fold["end_exclusive"]),
                "name": str(fold["name"]),
                "start": str(fold["start"]),
            }
        )
    return result


def summarize_run(
    root: str | Path,
    result: runner_v3.TeamWindowRunResult,
    *,
    policy: Mapping[str, Any],
    start: str,
    end_exclusive: str,
    include_selection: bool,
) -> dict[str, object]:
    root_path = _safe_root(root)
    base_daily = _daily(_result_artifact(root_path, result, "daily_returns"))
    stressed_daily = _daily(
        _result_artifact(root_path, result, "double_cost_daily_returns")
    )
    start_time = pd.Timestamp(start)
    end_time = pd.Timestamp(end_exclusive)
    base_daily = base_daily.loc[(base_daily.index >= start_time) & (base_daily.index < end_time)]
    stressed_daily = stressed_daily.loc[
        (stressed_daily.index >= start_time) & (stressed_daily.index < end_time)
    ]
    if base_daily.empty or not base_daily.index.equals(stressed_daily.index):
        raise ResearchExtensionError("scored daily artifacts do not cover the requested window")
    bar_frame = pd.read_csv(_result_artifact(root_path, result, "evaluator_returns"))
    bar_times = pd.to_datetime(bar_frame["timestamp"], utc=True)
    bars = bar_frame.loc[(bar_times >= start_time) & (bar_times < end_time)].copy()
    required = {
        "price_pnl",
        "funding_pnl",
        "fees",
        "slippage",
        "turnover",
        "gross_exposure",
        "long_price_pnl",
        "short_price_pnl",
        "long_funding_pnl",
        "short_funding_pnl",
        "risk_policy_turnover",
    }
    if not required.issubset(bars.columns) or bars.empty:
        raise ResearchExtensionError("bar return artifact lacks extension diagnostics")
    numeric = bars.loc[:, sorted(required)].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ResearchExtensionError("bar return diagnostics contain nonfinite values")
    years = len(base_daily) / 365.0
    turnover = float(numeric["turnover"].sum())
    gross_pnl = float((numeric["price_pnl"] + numeric["funding_pnl"]).sum())
    base_cost = float((numeric["fees"] + numeric["slippage"]).sum())
    edge_bps = float(gross_pnl / turnover * 10_000.0) if turnover > 0.0 else None
    cost_share = float(base_cost / gross_pnl) if gross_pnl > 0.0 else None
    overall = metrics_v3.compute_window_metrics(base_daily)
    stressed_overall = metrics_v3.compute_window_metrics(stressed_daily)
    trade_frame = pd.read_csv(_result_artifact(root_path, result, "trades"))
    trade_times = pd.to_datetime(trade_frame["timestamp"], utc=True)
    trade_count = int(((trade_times >= start_time) & (trade_times < end_time)).sum())
    summary: dict[str, object] = {
        "candidate_identity": {
            "config_sha256": result.config_sha256,
            "data_authority_sha256": result.data_manifest_sha256,
            "dependency_lock_sha256": result.dependency_lock_sha256,
            "entrypoint": result.entrypoint,
            "evaluator_sha256": result.evaluator_sha256,
            "risk_policy_sha256": result.risk_policy_sha256,
            "source_bundle_sha256": result.source_bundle_sha256,
            "strategy_sha256": result.strategy_sha256,
            "team_id": result.team_id,
        },
        "diagnostics": {
            "annualized_turnover": float(turnover / years),
            "average_gross_exposure": float(numeric["gross_exposure"].mean()),
            "base_cost": base_cost,
            "base_cost_share_of_positive_gross_pnl": cost_share,
            "gross_edge_per_turnover_bps": edge_bps,
            "gross_pnl": gross_pnl,
            "long_gross_pnl": float(
                (numeric["long_price_pnl"] + numeric["long_funding_pnl"]).sum()
            ),
            "risk_policy_turnover_fraction": float(
                numeric["risk_policy_turnover"].sum() / turnover
            )
            if turnover > 0.0
            else 0.0,
            "short_gross_pnl": float(
                (numeric["short_price_pnl"] + numeric["short_funding_pnl"]).sum()
            ),
            "total_one_way_turnover": turnover,
            "trade_count": trade_count,
        },
        "double_cost": {
            "cumulative_return": _cumulative_return(stressed_daily),
            "metrics": _metrics_dict(stressed_overall),
        },
        "regime_sharpe": {key: float(value) for key, value in result.regime_sharpe.items()},
        "schema_version": "top40-v3-post-tournament-run-summary-v1",
        "scored_window": {
            "base_cumulative_return": _cumulative_return(base_daily),
            "end_exclusive": end_exclusive,
            "metrics": _metrics_dict(overall),
            "start": start,
        },
        "stage": result.stage,
    }
    if include_selection:
        folds = _fold_summary(base_daily, stressed_daily, policy["development"]["folds"])
        summary["folds"] = folds
        summary["selection"] = assess_selection(summary, policy)
    return summary


def assess_selection(
    summary: Mapping[str, Any], policy: Mapping[str, Any]
) -> dict[str, object]:
    floors = policy["selection_floors"]
    metrics = summary["scored_window"]["metrics"]
    double_metrics = summary["double_cost"]["metrics"]
    diagnostics = summary["diagnostics"]
    folds = summary["folds"]
    regimes = summary["regime_sharpe"]
    edge = diagnostics["gross_edge_per_turnover_bps"]
    cost_share = diagnostics["base_cost_share_of_positive_gross_pnl"]
    fold_sharpes = [float(row["base_metrics"]["net_sharpe"]) for row in folds]
    gates = {
        "annualized_return": float(metrics["annualized_return"])
        > float(floors["minimum_annualized_return_exclusive"]),
        "annualized_turnover": float(diagnostics["annualized_turnover"])
        <= float(floors["maximum_annualized_turnover_inclusive"]),
        "base_cost_share": cost_share is not None
        and float(cost_share)
        <= float(floors["maximum_base_cost_share_of_positive_gross_pnl_inclusive"]),
        "double_cost_sharpe": float(double_metrics["net_sharpe"])
        >= float(floors["minimum_double_cost_sharpe_inclusive"]),
        "gross_edge_density": edge is not None
        and float(edge) >= float(floors["minimum_gross_edge_per_turnover_bps_inclusive"]),
        "max_drawdown": float(metrics["max_drawdown"])
        <= float(floors["maximum_drawdown_inclusive"]),
        "net_sharpe": float(metrics["net_sharpe"])
        >= float(floors["minimum_net_sharpe_inclusive"]),
        "positive_base_folds": sum(
            float(row["base_cumulative_return"]) > 0.0 for row in folds
        )
        >= int(floors["minimum_positive_base_return_folds_inclusive"]),
        "positive_double_cost_folds": sum(
            float(row["double_cost_cumulative_return"]) > 0.0 for row in folds
        )
        >= int(floors["minimum_positive_double_cost_return_folds_inclusive"]),
        "positive_quarters": float(metrics["positive_quarter_fraction"])
        >= float(floors["minimum_positive_quarter_fraction_inclusive"]),
        "positive_regimes": sum(float(value) > 0.0 for value in regimes.values())
        >= int(floors["minimum_positive_regimes_inclusive"]),
        "trade_count": int(diagnostics["trade_count"])
        >= int(floors["minimum_trade_count_inclusive"]),
        "worst_fold": min(fold_sharpes)
        >= float(floors["minimum_worst_fold_net_sharpe_inclusive"]),
        "worst_regime": min(float(value) for value in regimes.values())
        >= float(floors["minimum_worst_regime_sharpe_inclusive"]),
    }
    return {
        "gates": gates,
        "ready": all(gates.values()),
        "ranking_vector": {
            "annualized_turnover": float(diagnostics["annualized_turnover"]),
            "candidate_id": None,
            "double_cost_sharpe": float(double_metrics["net_sharpe"]),
            "gross_edge_per_turnover_bps": edge,
            "worst_fold_net_sharpe": min(fold_sharpes),
        },
    }


def _authority(
    root: Path, spec: CandidateSpec, purpose: str
) -> orchestrator_v3.CandidateAuthority:
    loaded = top40_v3.load_config(_path(root, V3_CONFIG_PATH))
    try:
        return orchestrator_v3._derive_candidate_authority(
            root, loaded, spec.team_id, spec.entrypoint, purpose
        )
    except (OSError, TypeError, ValueError, orchestrator_v3.OrchestratorError) as exc:
        raise ResearchExtensionError(f"candidate authority failed: {exc}") from exc


def _run(
    root: Path,
    authority: orchestrator_v3.CandidateAuthority,
    *,
    stage: str,
    output_relative: str,
) -> runner_v3.TeamWindowRunResult:
    try:
        with research_extension_v3_compat.utc_metric_slice_compatibility():
            return runner_v3.run_team(
                root,
                authority.team_id,
                authority.entrypoint,
                V3_CONFIG_PATH,
                DATA_MANIFEST_PATH,
                stage=stage,
                _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
                _output_relative=output_relative,
                _candidate_id=authority.candidate_id,
                _source_archive_relative=authority.source_archive_path,
                _source_archive_sha256=authority.source_archive_sha256,
            )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        raise ResearchExtensionError(f"canonical runner failed: {exc}") from exc


def _development_attempts(records: Sequence[Mapping[str, Any]], team_id: str) -> int:
    return sum(
        row.get("event_type") == "development_requested" and row.get("team_id") == team_id
        for row in records
    )


def run_development(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    *,
    purpose: str,
) -> dict[str, object]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        validate(root_path)
        policy = load_policy(root_path)
        spec = candidate_spec(policy, team_id, candidate_id)
        _validate_candidate_config(root_path, spec)
        records = _journal_records(root_path)
        if any(
            row.get("event_type") == "development_requested"
            and row.get("candidate_id") == candidate_id
            for row in records
        ):
            raise ResearchExtensionError("candidate already consumed its development attempt")
        attempts = _development_attempts(records, team_id)
        if attempts >= len(policy["candidate_matrix"][team_id]):
            raise ResearchExtensionError("team exhausted its preregistered development matrix")
        authority = _authority(root_path, spec, purpose)
        run_number = attempts + 1
        run_id = (
            f"research-extension-{team_id.replace('-', '')}-dev-{run_number:02d}-"
            f"{authority.source_bundle_sha256[:12]}"
        )
        output = f"tournament/top40-v3/private/public/{team_id}/{run_id}"
        request = _append_event(
            root_path,
            "development_requested",
            {
                "candidate_id": candidate_id,
                "entrypoint": spec.entrypoint,
                "output_path": output,
                "parameters": dict(spec.parameters),
                "purpose": purpose,
                "run_id": run_id,
                "source_archive_path": authority.source_archive_path,
                "source_archive_sha256": authority.source_archive_sha256,
                "source_bundle_sha256": authority.source_bundle_sha256,
                "team_id": team_id,
            },
        )
        try:
            result = _run(
                root_path,
                authority,
                stage=str(policy["development"]["runner_stage"]),
                output_relative=output,
            )
            summary = summarize_run(
                root_path,
                result,
                policy=policy,
                start=str(policy["development"]["start"]),
                end_exclusive=str(policy["development"]["end_exclusive"]),
                include_selection=True,
            )
            summary["candidate_id"] = candidate_id
            summary["run_id"] = run_id
            summary["selection"]["ranking_vector"]["candidate_id"] = candidate_id
            report_relative = f"{REPORTS_ROOT}/development/{team_id}/{run_id}/summary.json"
            report_payload = _pretty_json_bytes(summary)
            _write_atomic(root_path, report_relative, report_payload)
            terminal = _append_event(
                root_path,
                "development_succeeded",
                {
                    "candidate_id": candidate_id,
                    "request_record_sha256": request["record_sha256"],
                    "run_id": run_id,
                    "summary_path": report_relative,
                    "summary_sha256": _sha256(report_payload),
                    "team_id": team_id,
                },
            )
        except BaseException as exc:
            _append_event(
                root_path,
                "development_failed",
                {
                    "candidate_id": candidate_id,
                    "failure": f"{type(exc).__name__}: {exc}"[:2048],
                    "request_record_sha256": request["record_sha256"],
                    "run_id": run_id,
                    "team_id": team_id,
                },
            )
            raise
        return {
            "candidate_id": candidate_id,
            "journal_record_sha256": terminal["record_sha256"],
            "ok": True,
            "run_id": run_id,
            "selection": summary["selection"],
            "summary_path": report_relative,
            "team_id": team_id,
        }


def _successful_record(
    root: Path, team_id: str, candidate_id: str
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    records = _journal_records(root)
    matches = [
        row
        for row in records
        if row.get("event_type") == "development_succeeded"
        and row.get("team_id") == team_id
        and row.get("candidate_id") == candidate_id
    ]
    if len(matches) != 1:
        raise ResearchExtensionError("candidate lacks exactly one successful development run")
    record = matches[0]
    summary = _read_object(root, str(record["summary_path"]))
    if _sha256(_read_bytes(root, str(record["summary_path"]))) != record["summary_sha256"]:
        raise ResearchExtensionError("development summary changed after journal binding")
    return record, summary


def _finalists(root: Path) -> Mapping[str, Any]:
    path = _path(root, FINALIST_PATH)
    if not path.exists():
        return {"schema_version": FINALIST_SCHEMA, "teams": {}}
    value = _read_object(root, FINALIST_PATH)
    if value.get("schema_version") != FINALIST_SCHEMA or not isinstance(
        value.get("teams"), Mapping
    ):
        raise ResearchExtensionError("finalist registry is malformed")
    return value


def freeze_finalist(root: str | Path, team_id: str, candidate_id: str) -> dict[str, object]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        validate(root_path)
        policy = load_policy(root_path)
        spec = candidate_spec(policy, team_id, candidate_id)
        _validate_candidate_config(root_path, spec)
        registry = _finalists(root_path)
        if team_id in registry["teams"]:
            raise ResearchExtensionError("team already has its one frozen finalist")
        success, summary = _successful_record(root_path, team_id, candidate_id)
        if not summary.get("selection", {}).get("ready"):
            raise ResearchExtensionError("candidate fails at least one frozen selection floor")
        authority = _authority(root_path, spec, "post-tournament finalist identity verification")
        identity = summary["candidate_identity"]
        expected = {
            "config_sha256": authority.tournament_config_sha256,
            "data_authority_sha256": authority.data_authority_sha256,
            "dependency_lock_sha256": authority.dependency_lock_sha256,
            "entrypoint": authority.entrypoint,
            "evaluator_sha256": authority.evaluator_sha256,
            "risk_policy_sha256": authority.risk_policy_sha256,
            "source_bundle_sha256": authority.source_bundle_sha256,
            "strategy_sha256": authority.strategy_sha256,
            "team_id": authority.team_id,
        }
        if identity != expected:
            raise ResearchExtensionError("live candidate differs from its development identity")
        row = {
            "candidate_id": candidate_id,
            "development_record_sha256": success["record_sha256"],
            "entrypoint": authority.entrypoint,
            "frozen_at_utc": _utc_now(),
            "identity": expected,
            "source_archive_path": authority.source_archive_path,
            "source_archive_sha256": authority.source_archive_sha256,
        }
        updated = {
            "schema_version": FINALIST_SCHEMA,
            "teams": {**dict(registry["teams"]), team_id: row},
        }
        _write_atomic(root_path, FINALIST_PATH, _pretty_json_bytes(updated))
        event = _append_event(
            root_path,
            "finalist_frozen",
            {"candidate_id": candidate_id, "finalist": row, "team_id": team_id},
        )
        return {
            "candidate_id": candidate_id,
            "finalist_record_sha256": event["record_sha256"],
            "ok": True,
            "team_id": team_id,
        }


def _finalist_authority(root: Path, policy: Mapping[str, Any], team_id: str):
    registry = _finalists(root)
    finalist = registry["teams"].get(team_id)
    if not isinstance(finalist, Mapping):
        raise ResearchExtensionError("team has no frozen finalist")
    spec = candidate_spec(policy, team_id, str(finalist["candidate_id"]))
    _validate_candidate_config(root, spec)
    authority = _authority(root, spec, "sealed post-tournament identity verification")
    if (
        authority.source_archive_path != finalist.get("source_archive_path")
        or authority.source_archive_sha256 != finalist.get("source_archive_sha256")
        or authority.source_bundle_sha256
        != finalist.get("identity", {}).get("source_bundle_sha256")
    ):
        raise ResearchExtensionError("frozen finalist candidate tree changed")
    return finalist, authority


def run_qualifier(root: str | Path, team_id: str) -> dict[str, object]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        validate(root_path)
        policy = load_policy(root_path)
        finalist, authority = _finalist_authority(root_path, policy, team_id)
        records = _journal_records(root_path)
        if any(
            row.get("event_type") == "qualifier_requested" and row.get("team_id") == team_id
            for row in records
        ):
            raise ResearchExtensionError("team already consumed its qualifier attempt")
        run_id = (
            f"research-extension-{team_id.replace('-', '')}-qual-"
            f"{authority.source_bundle_sha256[:12]}"
        )
        output = f"tournament/top40-v3/private/private/{team_id}/{run_id}"
        request = _append_event(
            root_path,
            "qualifier_requested",
            {
                "candidate_id": authority.candidate_id,
                "output_path": output,
                "run_id": run_id,
                "team_id": team_id,
            },
        )
        try:
            result = _run(
                root_path,
                authority,
                stage=str(policy["historical_qualifier"]["runner_stage"]),
                output_relative=output,
            )
        except BaseException as exc:
            _append_event(
                root_path,
                "qualifier_failed",
                {
                    "candidate_id": authority.candidate_id,
                    "failure": f"{type(exc).__name__}: {exc}"[:2048],
                    "request_record_sha256": request["record_sha256"],
                    "run_id": run_id,
                    "team_id": team_id,
                },
            )
            raise
        metrics = result.scored_window.metrics
        gate = policy["historical_qualifier"]["gate"]
        passed = bool(
            metrics.net_sharpe > float(gate["minimum_net_sharpe_exclusive"])
            and metrics.annualized_return
            > float(gate["minimum_annualized_return_exclusive"])
            and result.double_cost_sharpe
            > float(gate["minimum_double_cost_sharpe_exclusive"])
            and metrics.max_drawdown <= float(gate["maximum_drawdown_inclusive"])
        )
        event = _append_event(
            root_path,
            "qualifier_completed",
            {
                "artifact_sha256": dict(result.artifact_sha256),
                "candidate_id": authority.candidate_id,
                "passed": passed,
                "request_record_sha256": request["record_sha256"],
                "run_id": run_id,
                "team_id": team_id,
            },
        )
        return {
            "candidate_id": finalist["candidate_id"],
            "ok": True,
            "passed": passed,
            "qualifier_record_sha256": event["record_sha256"],
            "team_id": team_id,
        }


def _qualifier_passers(root: Path) -> tuple[str, ...]:
    records = _journal_records(root)
    completed = {
        str(row["team_id"]): bool(row["passed"])
        for row in records
        if row.get("event_type") == "qualifier_completed"
    }
    finalists = _finalists(root)["teams"]
    if set(completed) != set(finalists):
        raise ResearchExtensionError("every frozen finalist needs a terminal qualifier decision")
    return tuple(sorted(team_id for team_id, passed in completed.items() if passed))


def run_final_release(root: str | Path) -> dict[str, object]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        validate(root_path)
        policy = load_policy(root_path)
        records = _journal_records(root_path)
        if any(row.get("event_type") == "final_requested" for row in records):
            raise ResearchExtensionError("historical final observation was already requested")
        passers = _qualifier_passers(root_path)
        if not passers:
            raise ResearchExtensionError("no qualifier passer is eligible for final OOS")
        request = _append_event(
            root_path,
            "final_requested",
            {"teams": list(passers)},
        )
        try:
            completed: list[tuple[str, runner_v3.TeamWindowRunResult]] = []
            for team_id in passers:
                _finalist, authority = _finalist_authority(root_path, policy, team_id)
                run_id = (
                    f"research-extension-{team_id.replace('-', '')}-final-"
                    f"{authority.source_bundle_sha256[:12]}"
                )
                output = f"tournament/top40-v3/private/final-oos/{team_id}/{run_id}"
                result = _run(
                    root_path,
                    authority,
                    stage=str(policy["final_oos"]["runner_stage"]),
                    output_relative=output,
                )
                completed.append((team_id, result))
            summaries: dict[str, object] = {}
            for team_id, result in completed:
                summary = summarize_run(
                    root_path,
                    result,
                    policy=policy,
                    start=str(policy["final_oos"]["start"]),
                    end_exclusive=str(policy["final_oos"]["end_exclusive"]),
                    include_selection=False,
                )
                summary["candidate_id"] = _finalists(root_path)["teams"][team_id][
                    "candidate_id"
                ]
                summaries[team_id] = summary
            release_relative = f"{REPORTS_ROOT}/final-oos/final-release.json"
            release_payload = _pretty_json_bytes(
                {
                    "schema_version": "top40-v3-post-tournament-final-release-v1",
                    "study_id": policy["study_id"],
                    "teams": summaries,
                }
            )
            _write_atomic(root_path, release_relative, release_payload)
            releases = {
                "release_path": release_relative,
                "release_sha256": _sha256(release_payload),
                "teams": list(passers),
            }
        except BaseException as exc:
            _append_event(
                root_path,
                "final_failed",
                {
                    "failure": f"{type(exc).__name__}: {exc}"[:2048],
                    "request_record_sha256": request["record_sha256"],
                    "teams": list(passers),
                },
            )
            raise
        event = _append_event(
            root_path,
            "final_released",
            {
                "releases": releases,
                "request_record_sha256": request["record_sha256"],
                "teams": list(passers),
            },
        )
        return {
            "final_record_sha256": event["record_sha256"],
            "ok": True,
            "releases": releases,
        }


def status(root: str | Path = ".") -> dict[str, object]:
    root_path = _safe_root(root)
    validation = validate(root_path)
    records = _journal_records(root_path)
    teams: dict[str, object] = {}
    finalists = _finalists(root_path)["teams"]
    for team_id in ("team-04", "team-06"):
        successes = [
            row
            for row in records
            if row.get("event_type") == "development_succeeded"
            and row.get("team_id") == team_id
        ]
        qualifier = next(
            (
                row
                for row in reversed(records)
                if row.get("event_type") == "qualifier_completed"
                and row.get("team_id") == team_id
            ),
            None,
        )
        teams[team_id] = {
            "development_success_count": len(successes),
            "development_candidates": [row["candidate_id"] for row in successes],
            "finalist": finalists.get(team_id, {}).get("candidate_id")
            if isinstance(finalists.get(team_id), Mapping)
            else None,
            "qualifier_completed": qualifier is not None,
            "qualifier_passed": qualifier.get("passed") if qualifier is not None else None,
        }
    return {
        **validation,
        "final_released": any(row.get("event_type") == "final_released" for row in records),
        "journal_event_count": len(records),
        "teams": teams,
    }


__all__ = [
    "ACTIVATION_PATH",
    "CandidateSpec",
    "EXTENSION_ROOT",
    "FINALIST_PATH",
    "JOURNAL_PATH",
    "POLICY_PATH",
    "REPORTS_ROOT",
    "ResearchExtensionError",
    "assess_selection",
    "candidate_spec",
    "freeze_finalist",
    "load_policy",
    "run_development",
    "run_final_release",
    "run_qualifier",
    "status",
    "summarize_run",
    "validate",
]
