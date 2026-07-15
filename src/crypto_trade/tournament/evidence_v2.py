"""Deterministic, hash-bound qualification evidence derived from V2 runner artifacts.

Six fixed chronological slices are useful evaluation-fold diagnostics, but they do not prove that
a model was retrained without seeing each test fold.  Development evidence therefore requires a
hash-bound declared walk-forward manifest by default.  Callers may explicitly allow evaluation
folds only, in which case the returned provenance says that the evidence is not proof of true
retraining OOF.  A declaration binds fold boundaries and model bytes; it remains an auditable
organizer declaration rather than an independent reconstruction of the training process.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from statistics import NormalDist, median
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.metrics import (
    aggregate_daily_returns,
    compute_regime_sharpes,
    compute_window_metrics,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.risk_policy import load_risk_policy
from crypto_trade.tournament.top40_v2 import TEAM_IDS, LoadedV2Config, load_config

_REGIMES = ("bull", "bear", "chop", "stress")
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
_RUNNER_RECORD_KEYS = {
    "stage",
    "team_id",
    "entrypoint",
    "seeds",
    "data_manifest_sha256",
    "config_sha256",
    "strategy_sha256",
    "risk_policy_sha256",
    "source_bundle_sha256",
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
_BAR_RETURN_COLUMNS = (
    "timestamp",
    "price_pnl",
    "long_price_pnl",
    "short_price_pnl",
    "funding_pnl",
    "long_funding_pnl",
    "short_funding_pnl",
    "forced_exit_boundary_funding_pnl",
    "fees",
    "slippage",
    "net_return",
    "turnover",
    "gross_exposure",
    "net_exposure",
    "long_exposure",
    "short_exposure",
    "requested_notional",
    "unfilled_notional",
    "forced_exit_requested_notional",
    "forced_exit_unfilled_notional",
    "forced_exit_turnover",
    "conservative_settlement_notional",
    "conservative_settlement_loss",
    "terminal_unresolved_notional",
    "risk_reduction_turnover",
    "risk_cap_breach",
    "risk_cap_required_scale",
    "equity",
)
_RISK_RETURN_COLUMNS = (
    "risk_policy_id",
    "risk_policy_turnover",
    "risk_policy_gross_scale",
    "risk_policy_drawdown",
    "risk_policy_annualized_volatility",
    "risk_policy_reasons",
)
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
_TRADE_TYPES = frozenset({"trade", "risk_reduction", "forced_exit", "risk_policy_action"})
_QUANTITY_EVENT_TYPES = _TRADE_TYPES | {"conservative_settlement"}
_WINDOW_METRIC_FIELDS = (
    "net_sharpe",
    "net_sortino",
    "calmar",
    "annualized_return",
    "max_drawdown",
    "positive_quarter_fraction",
)
_SHA256 = frozenset("0123456789abcdef")
_EULER_MASCHERONI = 0.5772156649015329


@dataclasses.dataclass(frozen=True)
class BuiltQualificationEvidence:
    """Qualification-schema payload plus organizer-only derivation provenance."""

    evidence: Mapping[str, object]
    provenance: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {"evidence": dict(self.evidence), "provenance": dict(self.provenance)}


@dataclasses.dataclass(frozen=True)
class _Window:
    replay_start: pd.Timestamp
    score_start: pd.Timestamp
    score_end: pd.Timestamp
    end_exclusive: pd.Timestamp


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value).issubset(_SHA256)


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


def _safe_file(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError(f"{label} must be a repository-relative path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    lexical = root / Path(*pure.parts)
    current = root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label} contains a symlink component: {relative}")
    path = lexical.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"{label} is missing or unsafe: {relative}")
    return path


def _relative_argument(root: Path, value: str | Path, label: str) -> tuple[str, Path]:
    candidate = Path(value)
    if not candidate.is_absolute() and any(
        part in {"", ".", ".."} for part in PurePosixPath(candidate.as_posix()).parts
    ):
        raise ValueError(f"{label} must be a safe repository-relative path")
    lexical = candidate.absolute() if candidate.is_absolute() else root / candidate
    try:
        relative = lexical.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"{label} is outside the tournament root") from exc
    path = _safe_file(root, relative, label)
    if not path.is_file():
        raise ValueError(f"{label} is missing, unsafe, or outside the tournament root")
    return relative, path


def _read_json_file(root: Path, value: str | Path, label: str) -> tuple[dict[str, Any], str, str]:
    relative, path = _relative_argument(root, value, label)
    try:
        payload = path.read_bytes()
        raw = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{label} root must be a JSON object")
    return raw, relative, _sha256_bytes(payload)


def _window(config: LoadedV2Config, stage: str) -> _Window:
    splits = config.raw["splits"]
    replay_start = pd.Timestamp(str(splits["visible_development_start"]), tz="UTC")
    if stage == "development":
        score_start = replay_start
        score_end = pd.Timestamp(
            str(splits["visible_development_end_inclusive"]), tz="UTC"
        )
    elif stage == "private":
        score_start = pd.Timestamp(str(splits["private_qualifier_start"]), tz="UTC")
        score_end = pd.Timestamp(str(splits["private_qualifier_end_inclusive"]), tz="UTC")
    else:
        raise ValueError("evidence stage must be development or private")
    return _Window(replay_start, score_start, score_end, score_end + pd.Timedelta(days=1))


def _stage_output(team_id: str, stage: str) -> str:
    if stage == "development":
        return f"{TOP40_V2_LAYOUT.reports_root}/{team_id}/development"
    return f"{TOP40_V2_LAYOUT.tournament_root}/private/artifacts/{team_id}"


def _artifact_paths(
    root: Path, record: Mapping[str, Any], team_id: str, stage: str
) -> tuple[dict[str, Path], dict[str, str]]:
    artifacts = _exact_object(record["artifacts"], set(_ARTIFACT_FILENAMES), "runner artifacts")
    output = _stage_output(team_id, stage)
    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for name, filename in _ARTIFACT_FILENAMES.items():
        expected = f"{output}/{filename}"
        if artifacts[name] != expected:
            raise ValueError(f"runner artifact path for {name} is noncanonical")
        path = _safe_file(root, expected, f"runner artifact {name}")
        paths[name] = path
        hashes[name] = _sha256_bytes(path.read_bytes())
    if record.get("output_dir") != output:
        raise ValueError("runner output directory is noncanonical")
    recorded_hashes = _exact_object(
        record.get("artifact_sha256"), set(_ARTIFACT_FILENAMES), "runner artifact hashes"
    )
    recorded_sizes = _exact_object(
        record.get("artifact_sizes"), set(_ARTIFACT_FILENAMES), "runner artifact sizes"
    )
    for name, path in paths.items():
        size = recorded_sizes[name]
        if (
            recorded_hashes[name] != hashes[name]
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or size != path.stat().st_size
        ):
            raise ValueError(f"runner artifact manifest differs for {name}")
    return paths, hashes


def _read_daily(path: Path, expected: pd.DatetimeIndex, label: str) -> pd.Series:
    frame = pd.read_csv(path)
    if list(frame.columns) != ["date", "net_return"]:
        raise ValueError(f"{label} must have exact columns date,net_return")
    dates = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True, errors="raise"))
    if dates.duplicated().any() or not dates.equals(expected):
        raise ValueError(f"{label} does not cover the exact canonical daily window")
    values = pd.to_numeric(frame["net_return"], errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= -1.0).any():
        raise ValueError(f"{label} contains invalid returns")
    return pd.Series(values, index=dates, name="net_return")


def _read_bar_returns(
    path: Path,
    expected: pd.DatetimeIndex,
    label: str,
    *,
    risk_policy_id: str | None,
) -> pd.DataFrame:
    frame = pd.read_csv(path)
    expected_columns = list(
        _BAR_RETURN_COLUMNS + (_RISK_RETURN_COLUMNS if risk_policy_id is not None else ())
    )
    if list(frame.columns) != expected_columns:
        raise ValueError(f"{label} has noncanonical return columns")
    timestamps = pd.DatetimeIndex(pd.to_datetime(frame["timestamp"], utc=True, errors="raise"))
    if timestamps.duplicated().any() or not timestamps.equals(expected):
        raise ValueError(f"{label} does not cover the exact canonical 8h window")
    result = frame.copy()
    result.index = timestamps
    result = result.drop(columns="timestamp")
    numeric = [
        column
        for column in result.columns
        if column
        not in {
            "risk_cap_breach",
            "risk_policy_id",
            "risk_policy_reasons",
            "risk_policy_annualized_volatility",
        }
    ]
    result[numeric] = result[numeric].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(result[numeric].to_numpy(dtype=float)).all():
        raise ValueError(f"{label} contains non-finite values")
    if result["risk_cap_breach"].isna().any() or not pd.api.types.is_bool_dtype(
        result["risk_cap_breach"].dtype
    ):
        raise ValueError(f"{label} risk_cap_breach must be Boolean")
    if risk_policy_id is not None:
        if not result["risk_policy_id"].astype(str).eq(risk_policy_id).all():
            raise ValueError(f"{label} risk-policy identity differs")
        volatility = pd.to_numeric(result["risk_policy_annualized_volatility"], errors="raise")
        if not np.isfinite(volatility.dropna().to_numpy(dtype=float)).all():
            raise ValueError(f"{label} risk-policy volatility contains non-finite values")
    for column in ("gross_exposure", "long_exposure", "short_exposure"):
        if (result[column] < -1e-12).any():
            raise ValueError(f"{label} contains negative {column}")
    if not np.allclose(
        result["gross_exposure"],
        result["long_exposure"] + result["short_exposure"],
        rtol=0.0,
        atol=1e-10,
    ):
        raise ValueError(f"{label} exposure columns do not reconcile")
    return result


def _validate_daily_reconciliation(
    bar_returns: pd.DataFrame, daily: pd.Series, label: str
) -> None:
    derived = aggregate_daily_returns(bar_returns["net_return"])
    if not derived.index.equals(daily.index) or not np.allclose(
        derived.to_numpy(), daily.to_numpy(), rtol=0.0, atol=1e-12
    ):
        raise ValueError(f"{label} daily returns do not reconcile to bar returns")


def _read_positions(path: Path, expected: pd.DatetimeIndex, base: pd.DataFrame) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if not len(frame.columns) or frame.columns[0] != "timestamp":
        raise ValueError("positions must begin with timestamp")
    symbols = list(frame.columns[1:])
    if not symbols or symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
        raise ValueError("positions require unique, sorted symbol columns")
    timestamps = pd.DatetimeIndex(pd.to_datetime(frame["timestamp"], utc=True, errors="raise"))
    if timestamps.duplicated().any() or not timestamps.equals(expected):
        raise ValueError("positions do not cover the exact canonical 8h window")
    values = frame[symbols].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("positions contain non-finite values")
    positions = pd.DataFrame(values, index=timestamps, columns=symbols)
    long_exposure = positions.clip(lower=0.0).sum(axis=1)
    short_exposure = -positions.clip(upper=0.0).sum(axis=1)
    if not np.allclose(long_exposure, base["long_exposure"], rtol=0.0, atol=1e-10):
        raise ValueError("positions do not reconcile to long exposure")
    if not np.allclose(short_exposure, base["short_exposure"], rtol=0.0, atol=1e-10):
        raise ValueError("positions do not reconcile to short exposure")
    return positions


def _read_targets(path: Path, expected: pd.DatetimeIndex) -> None:
    frame = pd.read_parquet(path)
    if len(frame.columns) < 3 or list(frame.columns[:2]) != [
        "timestamp",
        REBALANCE_INSTRUCTION_COLUMN,
    ]:
        raise ValueError("targets must begin with timestamp and the rebalance instruction")
    symbols = list(frame.columns[2:])
    if symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
        raise ValueError("targets require unique, sorted symbol columns")
    timestamps = pd.DatetimeIndex(pd.to_datetime(frame["timestamp"], utc=True, errors="raise"))
    if timestamps.duplicated().any() or not timestamps.equals(expected):
        raise ValueError("targets do not cover the exact canonical 8h window")
    if frame[REBALANCE_INSTRUCTION_COLUMN].isna().any() or not pd.api.types.is_bool_dtype(
        frame[REBALANCE_INSTRUCTION_COLUMN].dtype
    ):
        raise ValueError("target rebalance instructions must be Boolean")
    values = frame[symbols].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("targets contain non-finite values")


def _read_events(
    path: Path,
    trades_path: Path,
    replay_start: pd.Timestamp,
    end_exclusive: pd.Timestamp,
) -> pd.DataFrame:
    events = pd.read_parquet(path)
    trades = pd.read_csv(trades_path)
    if list(events.columns) != list(_EVENT_COLUMNS) or list(trades.columns) != list(_EVENT_COLUMNS):
        raise ValueError("events and trades must use the exact canonical event columns")
    for label, frame in (("events", events), ("trades", trades)):
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        if (
            frame["timestamp"].isna().any()
            or (frame["timestamp"] < replay_start).any()
            or (frame["timestamp"] > end_exclusive).any()
        ):
            raise ValueError(f"{label} contains timestamps outside the authorized window")
        for column in (
            "quantity",
            "price",
            "notional",
            "funding_rate",
            "cashflow",
            "fee",
            "slippage",
        ):
            frame[column] = pd.to_numeric(frame[column], errors="raise")
            if not np.isfinite(frame[column].to_numpy(dtype=float)).all():
                raise ValueError(f"{label} contains non-finite {column}")
    sorted_events = events.sort_values(
        ["timestamp", "symbol", "event_type", "phase"], kind="mergesort"
    )
    if not sorted_events.index.equals(events.index):
        raise ValueError("events are not in canonical deterministic order")
    expected_trades = events.loc[events["event_type"].isin(_TRADE_TYPES)].reset_index(drop=True)
    if (
        (expected_trades["price"] <= 0.0).any()
        or (expected_trades[["fee", "slippage"]] < 0.0).any(axis=None)
        or not np.allclose(
            expected_trades["notional"],
            expected_trades["quantity"] * expected_trades["price"],
            rtol=0.0,
            atol=1e-8,
        )
    ):
        raise ValueError("canonical trade-event price/notional/cost fields do not reconcile")
    if len(expected_trades) != len(trades):
        raise ValueError("trades do not equal the canonical trade-event subset")
    for column in _EVENT_COLUMNS:
        left = expected_trades[column]
        right = trades[column]
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            if not np.allclose(left, right, rtol=0.0, atol=1e-10, equal_nan=True):
                raise ValueError("trades differ from canonical events")
        else:
            if not left.fillna("").astype(str).equals(right.fillna("").astype(str)):
                raise ValueError("trades differ from canonical events")
    return events


def _snapshot_regimes(
    root: Path, manifest_path: Path, expected_full: pd.DatetimeIndex
) -> tuple[pd.Series, dict[str, dict[str, str]]]:
    try:
        manifest_payload = manifest_path.read_bytes()
        manifest = json.loads(manifest_payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid shared snapshot manifest: {exc}") from exc
    if not isinstance(manifest, Mapping) or not isinstance(manifest.get("files"), Sequence):
        raise ValueError("shared snapshot manifest has no canonical files list")
    selected = [
        item
        for item in manifest["files"]
        if isinstance(item, Mapping) and item.get("name") in {"btc_daily_returns", "btc_regimes"}
    ]
    entries = {item["name"]: item for item in selected}
    if len(selected) != len(entries):
        raise ValueError("shared manifest contains duplicate BTC return/regime artifacts")
    if set(entries) != {"btc_daily_returns", "btc_regimes"}:
        raise ValueError("shared manifest lacks BTC return/regime artifacts")
    paths: dict[str, Path] = {}
    bindings: dict[str, dict[str, str]] = {}
    for name, entry in entries.items():
        if not _is_sha256(entry.get("sha256")):
            raise ValueError(f"shared manifest {name} hash is invalid")
        path = _safe_file(root, entry.get("path"), f"shared {name}")
        digest = _sha256_bytes(path.read_bytes())
        if digest != entry["sha256"]:
            raise ValueError(f"shared {name} differs from the snapshot manifest")
        paths[name] = path
        bindings[name] = {"path": str(entry["path"]), "sha256": digest}
    btc = pd.read_csv(paths["btc_daily_returns"])
    labels = pd.read_csv(paths["btc_regimes"])
    if list(btc.columns) != ["date", "btc_return"] or list(labels.columns) != [
        "date",
        "regime",
    ]:
        raise ValueError("BTC return/regime artifacts have noncanonical columns")
    btc_dates = pd.DatetimeIndex(pd.to_datetime(btc["date"], utc=True, errors="raise"))
    label_dates = pd.DatetimeIndex(pd.to_datetime(labels["date"], utc=True, errors="raise"))
    if not btc_dates.equals(expected_full) or not label_dates.equals(expected_full):
        raise ValueError("BTC return/regime artifacts do not cover the exact tournament window")
    btc_values = pd.to_numeric(btc["btc_return"], errors="raise").to_numpy(dtype=float)
    if not np.isfinite(btc_values).all() or (btc_values <= -1.0).any():
        raise ValueError("BTC daily returns are invalid")
    regime = labels["regime"]
    invalid = set(regime.dropna().astype(str)) - set(_REGIMES)
    if invalid:
        raise ValueError(f"BTC regime labels are invalid: {sorted(invalid)}")
    return pd.Series(regime.to_numpy(), index=label_dates, name="regime"), bindings


def _fold_slices(scored: pd.Series, fold_count: int) -> list[tuple[str, pd.Series]]:
    if fold_count != 6 or len(scored) < fold_count:
        raise ValueError("development evidence requires six non-empty chronological folds")
    return [
        (f"fold-{index}", scored.iloc[indices])
        for index, indices in enumerate(np.array_split(np.arange(len(scored)), fold_count), start=1)
    ]


def _walk_forward_provenance(
    root: Path,
    path: str | Path | None,
    *,
    team_id: str,
    candidate_id: str,
    fold_slices: Sequence[tuple[str, pd.Series]],
    stitched_sha256: str,
    allow_evaluation_folds: bool,
) -> tuple[dict[str, object], dict[str, str]]:
    statement = (
        "Fixed chronological segmentation is evaluation-fold evidence only; by itself it does "
        "not prove that fitting or model selection was repeated without each test fold."
    )
    if path is None:
        if not allow_evaluation_folds:
            raise ValueError(
                "development evidence requires a declared walk-forward manifest; "
                "set allow_evaluation_folds=True only for non-OOF diagnostics"
            )
        return (
            {
                "evidence_class": "evaluation-folds-only",
                "qualification_ready_oof": False,
                "statement": statement,
                "manifest_path": None,
                "manifest_sha256": None,
            },
            {},
        )
    raw, relative, digest = _read_json_file(root, path, "walk-forward manifest")
    if not relative.startswith(f"{TOP40_V2_LAYOUT.report_root(team_id)}/"):
        raise ValueError("walk-forward manifest must remain inside the team report namespace")
    manifest = _exact_object(
        raw,
        {
            "schema_version",
            "team_id",
            "candidate_id",
            "evidence_class",
            "stitched_daily_returns_sha256",
            "folds",
        },
        "walk-forward manifest",
    )
    if (
        manifest["schema_version"] != 1
        or manifest["team_id"] != team_id
        or manifest["candidate_id"] != candidate_id
        or manifest["evidence_class"] != "declared-retrained-out-of-fold"
        or manifest["stitched_daily_returns_sha256"] != stitched_sha256
    ):
        raise ValueError("walk-forward manifest identity or stitched-return binding is invalid")
    folds = manifest["folds"]
    if not isinstance(folds, list) or len(folds) != len(fold_slices):
        raise ValueError("walk-forward manifest must contain exactly six folds")
    model_hashes: dict[str, str] = {}
    model_paths: set[str] = set()
    for index, ((fold_id, returns), raw_fold) in enumerate(
        zip(fold_slices, folds, strict=True), start=1
    ):
        fold = _exact_object(
            raw_fold,
            {
                "fold_id",
                "training_end_inclusive",
                "test_start",
                "test_end_inclusive",
                "model_artifact_path",
                "model_artifact_sha256",
            },
            f"walk-forward fold {index}",
        )
        test_start = pd.Timestamp(fold["test_start"], tz="UTC")
        test_end = pd.Timestamp(fold["test_end_inclusive"], tz="UTC")
        training_end = pd.Timestamp(fold["training_end_inclusive"], tz="UTC")
        if (
            fold["fold_id"] != fold_id
            or test_start != returns.index[0]
            or test_end != returns.index[-1]
            or training_end != test_start - pd.Timedelta(days=1)
        ):
            raise ValueError(f"walk-forward fold boundaries are invalid for {fold_id}")
        model_relative = fold["model_artifact_path"]
        model_path = _safe_file(root, model_relative, f"{fold_id} model artifact")
        allowed = (
            f"{TOP40_V2_LAYOUT.team_root(team_id)}/",
            f"{TOP40_V2_LAYOUT.report_root(team_id)}/",
        )
        if not any(model_relative.startswith(prefix) for prefix in allowed):
            raise ValueError("walk-forward model artifacts must remain inside the team namespace")
        model_digest = _sha256_bytes(model_path.read_bytes())
        if fold["model_artifact_sha256"] != model_digest or not _is_sha256(model_digest):
            raise ValueError(f"walk-forward model hash differs for {fold_id}")
        if model_relative in model_paths:
            raise ValueError("walk-forward folds require distinct model artifact paths")
        model_paths.add(model_relative)
        model_hashes[model_relative] = model_digest
    return (
        {
            "evidence_class": "declared-retrained-out-of-fold",
            "qualification_ready_oof": True,
            "statement": statement,
            "declaration_scope": (
                "Hash-bound fold/model declaration; training execution is auditable but is not "
                "independently reconstructed by this builder."
            ),
            "manifest_path": relative,
            "manifest_sha256": digest,
        },
        model_hashes,
    )


def _parameter_neighborhood(
    root: Path,
    path: str | Path,
    *,
    team_id: str,
    candidate_id: str,
    full_daily_index: pd.DatetimeIndex,
    score_start: pd.Timestamp,
    score_end: pd.Timestamp,
) -> tuple[dict[str, float], dict[str, object], dict[str, str]]:
    raw, relative, digest = _read_json_file(root, path, "parameter-neighborhood manifest")
    required_prefix = f"{TOP40_V2_LAYOUT.report_root(team_id)}/parameter-neighborhood/"
    if not relative.startswith(required_prefix):
        raise ValueError("parameter-neighborhood manifest path is noncanonical")
    manifest = _exact_object(
        raw,
        {"schema_version", "team_id", "candidate_id", "neighbors"},
        "parameter-neighborhood manifest",
    )
    if (
        manifest["schema_version"] != 1
        or manifest["team_id"] != team_id
        or manifest["candidate_id"] != candidate_id
    ):
        raise ValueError("parameter-neighborhood manifest identity is invalid")
    neighbors = manifest["neighbors"]
    if not isinstance(neighbors, list) or len(neighbors) < 3:
        raise ValueError("parameter neighborhood requires at least three variants")
    ids: set[str] = set()
    paths: set[str] = set()
    parameter_hashes: set[str] = set()
    returns: list[float] = []
    sharpes: list[float] = []
    hashes: dict[str, str] = {}
    for index, raw_neighbor in enumerate(neighbors):
        neighbor = _exact_object(
            raw_neighbor,
            {
                "neighbor_id",
                "parameter_artifact_path",
                "parameter_artifact_sha256",
                "daily_returns_path",
                "daily_returns_sha256",
            },
            f"parameter neighbor {index}",
        )
        neighbor_id = neighbor["neighbor_id"]
        relative_path = neighbor["daily_returns_path"]
        if not isinstance(neighbor_id, str) or not neighbor_id or neighbor_id in ids:
            raise ValueError("parameter neighbor ids must be non-empty and unique")
        if not isinstance(relative_path, str) or not relative_path.startswith(required_prefix):
            raise ValueError("parameter-neighbor returns must use the canonical team report area")
        parameter_relative = neighbor["parameter_artifact_path"]
        if not isinstance(parameter_relative, str) or not parameter_relative.startswith(
            required_prefix
        ):
            raise ValueError("parameter-neighbor definitions must use the canonical report area")
        if not parameter_relative.endswith(".json") or parameter_relative == relative_path:
            raise ValueError("parameter-neighbor definitions must be distinct JSON artifacts")
        if relative_path in paths:
            raise ValueError("parameter-neighbor return paths must be unique")
        artifact = _safe_file(root, relative_path, f"parameter neighbor {neighbor_id}")
        artifact_sha = _sha256_bytes(artifact.read_bytes())
        if neighbor["daily_returns_sha256"] != artifact_sha:
            raise ValueError(f"parameter neighbor hash differs for {neighbor_id}")
        parameter_artifact = _safe_file(
            root, parameter_relative, f"parameter definition {neighbor_id}"
        )
        parameter_sha = _sha256_bytes(parameter_artifact.read_bytes())
        if neighbor["parameter_artifact_sha256"] != parameter_sha:
            raise ValueError(f"parameter definition hash differs for {neighbor_id}")
        try:
            parameters = json.loads(parameter_artifact.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"parameter definition is invalid for {neighbor_id}") from exc
        if not isinstance(parameters, Mapping) or not parameters:
            raise ValueError("parameter-neighbor definitions must be non-empty JSON objects")
        if parameter_sha in parameter_hashes:
            raise ValueError("parameter-neighbor definitions must be byte-distinct")
        daily = _read_daily(artifact, full_daily_index, f"parameter neighbor {neighbor_id}")
        scored = daily.loc[score_start:score_end]
        returns.append(float((1.0 + scored).prod() - 1.0))
        sharpes.append(float(compute_window_metrics(scored).net_sharpe))
        ids.add(neighbor_id)
        paths.add(relative_path)
        parameter_hashes.add(parameter_sha)
        hashes[relative_path] = artifact_sha
        hashes[parameter_relative] = parameter_sha
    metrics = {
        "profitable_neighbor_fraction": float(np.mean(np.asarray(returns) > 0.0)),
        "neighbor_median_sharpe": float(median(sharpes)),
    }
    provenance = {
        "manifest_path": relative,
        "manifest_sha256": digest,
        "neighbor_count": len(neighbors),
        "profitability_definition": "compounded scored-window net return > 0",
    }
    return metrics, provenance, hashes


def _positive_pnl_concentration(
    scored: pd.Series, fold_slices: Sequence[tuple[str, pd.Series]]
) -> tuple[float, dict[str, float]]:
    fold_returns = np.asarray(
        [float((1.0 + returns).prod() - 1.0) for _fold_id, returns in fold_slices]
    )
    quarter_returns = ((1.0 + scored).resample("QE").prod() - 1.0).to_numpy(dtype=float)

    def concentration(values: np.ndarray) -> float:
        positive = values[values > 0.0]
        return float(positive.max() / positive.sum()) if len(positive) else 1.0

    by_fold = concentration(fold_returns)
    by_quarter = concentration(quarter_returns)
    return max(by_fold, by_quarter), {"fold": by_fold, "quarter": by_quarter}


def trial_adjusted_probability_positive(
    daily_returns: pd.Series, trial_count: int
) -> tuple[float, dict[str, object]]:
    """Return a Deflated-Sharpe-style probability adjusted for the trial count.

    The selected strategy's non-annualized daily Sharpe is compared with the expected maximum
    null Sharpe across ``trial_count`` independent trials.  The expected maximum uses the
    Bailey/López de Prado Euler-Mascheroni approximation.  The probability then uses the
    Probabilistic Sharpe Ratio skew/kurtosis standard error.  This does not infer an effective
    number of correlated trials: the declared material-trial count is used conservatively.
    """
    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise ValueError("trial_count must be a positive integer")
    values = pd.to_numeric(daily_returns, errors="raise").to_numpy(dtype=float)
    if len(values) < 3 or not np.isfinite(values).all():
        raise ValueError("trial-adjusted probability requires at least three finite daily returns")
    standard_deviation = float(np.std(values, ddof=1))
    if standard_deviation <= 1e-15:
        probability = 1.0 if float(np.mean(values)) > 0.0 else 0.0
        return probability, {
            "method": "top40-v2-dsr-v1",
            "trial_count": trial_count,
            "daily_observations": len(values),
            "degenerate_variance": True,
        }
    observed = float(np.mean(values) / standard_deviation)
    centered = values - float(np.mean(values))
    population_scale = float(np.std(values, ddof=0))
    skewness = float(np.mean((centered / population_scale) ** 3))
    pearson_kurtosis = float(np.mean((centered / population_scale) ** 4))
    null_scale = 1.0 / math.sqrt(len(values) - 1)
    benchmark = 0.0
    if trial_count > 1:
        normal = NormalDist()
        first = normal.inv_cdf(1.0 - 1.0 / trial_count)
        second = normal.inv_cdf(1.0 - 1.0 / (trial_count * math.e))
        benchmark = null_scale * (
            (1.0 - _EULER_MASCHERONI) * first + _EULER_MASCHERONI * second
        )
    correction = (
        1.0
        - skewness * observed
        + ((pearson_kurtosis - 1.0) / 4.0) * observed * observed
    )
    if not math.isfinite(correction) or correction <= 0.0:
        raise ValueError("trial-adjusted probability has a non-positive PSR variance correction")
    statistic = (observed - benchmark) * math.sqrt(len(values) - 1) / math.sqrt(correction)
    probability = float(NormalDist().cdf(statistic))
    return probability, {
        "method": "top40-v2-dsr-v1",
        "formula": (
            "PSR versus Euler-Mascheroni expected maximum null daily Sharpe; declared material "
            "trial count; population skew and Pearson kurtosis correction"
        ),
        "trial_count": trial_count,
        "daily_observations": len(values),
        "observed_daily_sharpe": observed,
        "expected_maximum_null_daily_sharpe": benchmark,
        "skewness": skewness,
        "pearson_kurtosis": pearson_kurtosis,
    }


def _regime_metrics(scored: pd.Series, labels: pd.Series) -> dict[str, dict[str, float]]:
    aligned_labels = labels.reindex(scored.index)
    if aligned_labels.notna().sum() == 0:
        raise ValueError("BTC regimes do not cover the scored window")
    sharpes = compute_regime_sharpes(scored, aligned_labels)
    result: dict[str, dict[str, float]] = {}
    for regime in _REGIMES:
        values = scored.loc[aligned_labels.eq(regime)]
        result[regime] = {
            "net_return": float((1.0 + values).prod() - 1.0) if len(values) else 0.0,
            "net_sharpe": float(sharpes[regime]),
        }
    return result


def _daily_side_contributions(scored_bars: pd.DataFrame) -> pd.DataFrame:
    raw_long = scored_bars["long_price_pnl"] + scored_bars["long_funding_pnl"]
    raw_short = scored_bars["short_price_pnl"] + scored_bars["short_funding_pnl"]
    costs = scored_bars["fees"] + scored_bars["slippage"]
    previous_long = scored_bars["long_exposure"].shift(1, fill_value=0.0)
    previous_short = scored_bars["short_exposure"].shift(1, fill_value=0.0)
    long_activity = scored_bars["long_exposure"] + previous_long
    short_activity = scored_bars["short_exposure"] + previous_short
    activity = long_activity + short_activity
    if ((activity <= 1e-15) & (costs.abs() > 1e-12)).any():
        raise ValueError("cannot allocate execution costs to a sleeve with no side activity")
    long_share = np.divide(
        long_activity,
        activity,
        out=np.full(len(activity), 0.5, dtype=float),
        where=activity.to_numpy() > 1e-15,
    )
    long = raw_long - costs * long_share
    short = raw_short - costs * (1.0 - long_share)
    if not np.allclose(long + short, scored_bars["net_return"], rtol=0.0, atol=1e-10):
        raise ValueError("long/short PnL components do not reconcile to net return")
    rows: list[dict[str, object]] = []
    for date, group in scored_bars.assign(long=long, short=short).groupby(
        scored_bars.index.normalize(), sort=True
    ):
        wealth = 1.0
        long_contribution = 0.0
        short_contribution = 0.0
        for row in group.itertuples():
            long_contribution += wealth * float(row.long)
            short_contribution += wealth * float(row.short)
            wealth *= 1.0 + float(row.net_return)
        rows.append(
            {
                "date": date,
                "long": long_contribution,
                "short": short_contribution,
                "net_return": wealth - 1.0,
            }
        )
    daily = pd.DataFrame(rows).set_index("date")
    if not np.allclose(daily["long"] + daily["short"], daily["net_return"], atol=1e-12):
        raise ValueError("daily sleeve contributions do not reconcile")
    return daily


def _side_executed_notional(
    events: pd.DataFrame, score_start: pd.Timestamp, end_exclusive: pd.Timestamp
) -> dict[str, float]:
    quantities: dict[str, float] = {}
    totals = {"long": 0.0, "short": 0.0}
    trade_events = events.loc[events["event_type"].isin(_QUANTITY_EVENT_TYPES)].copy()
    trade_events = trade_events.sort_values(
        ["timestamp", "symbol", "event_type", "phase"], kind="mergesort"
    )
    for row in trade_events.itertuples(index=False):
        symbol = str(row.symbol)
        before = quantities.get(symbol, 0.0)
        delta = float(row.quantity)
        after = before + delta
        quantities[symbol] = 0.0 if abs(after) < 1e-12 else after
        timestamp = pd.Timestamp(row.timestamp)
        if (
            row.event_type not in _TRADE_TYPES
            or timestamp < score_start
            or timestamp >= end_exclusive
        ):
            continue
        notional = abs(float(row.notional))
        if notional <= 0.0:
            continue
        if before >= 0.0 and after >= 0.0:
            totals["long"] += notional
        elif before <= 0.0 and after <= 0.0:
            totals["short"] += notional
        else:
            path = abs(before) + abs(after)
            if path <= 1e-15:
                raise ValueError("cannot attribute a crossing trade with zero quantity path")
            if before > 0.0:
                totals["long"] += notional * abs(before) / path
                totals["short"] += notional * abs(after) / path
            else:
                totals["short"] += notional * abs(before) / path
                totals["long"] += notional * abs(after) / path
    return totals


def _verify_runner_record(
    record: Mapping[str, Any],
    *,
    root: Path,
    config: LoadedV2Config,
    team_id: str,
    stage: str,
    window: _Window,
    base_metrics: Any,
    double_cost_sharpe: float,
    regime_metrics: Mapping[str, Mapping[str, float]],
    strategy_sha256: str,
    risk_policy_sha256: str,
    source_bundle_sha256: str,
    manifest_sha256: str,
    decision_count: int,
    event_count: int,
    trade_count: int,
) -> None:
    _exact_object(record, _RUNNER_RECORD_KEYS, "runner record")
    expected_entrypoint = f"{TOP40_V2_LAYOUT.team_root(team_id)}/strategy.py"
    if (
        record["stage"] != stage
        or record["team_id"] != team_id
        or record["entrypoint"] != expected_entrypoint
        or record["seeds"] != [config.raw["research_budget"]["strategy_seed"]]
        or record["config_sha256"] != config.sha256
        or record["strategy_sha256"] != strategy_sha256
        or record["risk_policy_sha256"] != risk_policy_sha256
        or record["source_bundle_sha256"] != source_bundle_sha256
        or record["data_manifest_sha256"] != manifest_sha256
    ):
        raise ValueError("runner record candidate identity or input hashes differ")
    if (
        record["decision_count"] != decision_count
        or record["event_count"] != event_count
        or record["trade_count"] != trade_count
    ):
        raise ValueError("runner record decision/event/trade counts differ from artifacts")
    scored_window = _exact_object(record["scored_window"], {"start", "end", "metrics"}, "window")
    if scored_window["start"] != window.score_start.date().isoformat() or scored_window[
        "end"
    ] != window.score_end.date().isoformat():
        raise ValueError("runner scored window differs from the canonical stage window")
    observed_metrics = _exact_object(
        scored_window["metrics"], set(_WINDOW_METRIC_FIELDS), "runner window metrics"
    )
    for field in _WINDOW_METRIC_FIELDS:
        if not math.isclose(
            _finite(observed_metrics[field], f"runner metric {field}"),
            float(getattr(base_metrics, field)),
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError(f"runner metric differs from artifacts: {field}")
    if not math.isclose(
        _finite(record["double_cost_sharpe"], "runner double_cost_sharpe"),
        double_cost_sharpe,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise ValueError("runner double-cost Sharpe differs from artifacts")
    observed_regimes = _exact_object(record["regime_sharpe"], set(_REGIMES), "runner regimes")
    for regime in _REGIMES:
        if not math.isclose(
            _finite(observed_regimes[regime], f"runner {regime} Sharpe"),
            regime_metrics[regime]["net_sharpe"],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError(f"runner regime Sharpe differs from artifacts: {regime}")
    intervals = _exact_object(
        record["confidence_intervals"],
        {"net_sharpe_95", "double_cost_sharpe_95"},
        "runner confidence intervals",
    )
    for name, interval in intervals.items():
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or any(not math.isfinite(_finite(value, name)) for value in interval)
            or float(interval[0]) > float(interval[1])
        ):
            raise ValueError(f"runner confidence interval is invalid: {name}")


def build_qualification_evidence(
    root: str | Path,
    runner_record: Mapping[str, Any],
    *,
    candidate_id: str,
    trial_count: int,
    risk_policy_path: str | Path | None = None,
    parameter_neighborhood_manifest_path: str | Path | None = None,
    walk_forward_manifest_path: str | Path | None = None,
    allow_evaluation_folds: bool = False,
) -> BuiltQualificationEvidence:
    """Build exact development/private qualification fields from canonical runner outputs."""
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError("tournament root must be a directory")
    if not isinstance(runner_record, Mapping):
        raise ValueError("runner_record must be a mapping")
    _exact_object(runner_record, _RUNNER_RECORD_KEYS, "runner record")
    stage = runner_record.get("stage")
    team_id = runner_record.get("team_id")
    if stage not in {"development", "private"} or team_id not in TEAM_IDS:
        raise ValueError("runner record stage/team identity is invalid")
    if not isinstance(candidate_id, str) or not candidate_id or len(candidate_id) > 128:
        raise ValueError("candidate_id must be a non-empty string of at most 128 characters")
    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise ValueError("trial_count must be a positive integer")

    config_path = _safe_file(root_path, TOP40_V2_LAYOUT.config_path, "V2 config")
    config = load_config(config_path)
    maximum_trials = config.raw["research_budget"]["maximum_material_configurations_per_team"]
    if trial_count > maximum_trials:
        raise ValueError("trial_count exceeds the cumulative research budget")
    window = _window(config, str(stage))
    expected_daily = pd.date_range(window.replay_start, window.score_end, freq="1D", tz="UTC")
    expected_bars = pd.date_range(
        window.replay_start, window.end_exclusive, freq="8h", inclusive="left", tz="UTC"
    )

    strategy_relative = f"{TOP40_V2_LAYOUT.team_root(str(team_id))}/strategy.py"
    strategy_path = _safe_file(root_path, strategy_relative, "strategy source")
    strategy_sha256 = _sha256_bytes(strategy_path.read_bytes())
    canonical_risk = f"{TOP40_V2_LAYOUT.team_root(str(team_id))}/risk_policy.json"
    risk_relative, risk_path = _relative_argument(
        root_path, risk_policy_path or canonical_risk, "risk policy"
    )
    if risk_relative != canonical_risk:
        raise ValueError("risk policy path must be the canonical team risk_policy.json")
    risk_policy = load_risk_policy(risk_path)
    risk_sha256 = _sha256_bytes(risk_path.read_bytes())
    from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

    source_bundle_sha256, _source_entries = source_bundle_fingerprint(
        root_path, str(team_id), strategy_relative
    )

    manifest_relative = str(config.raw["paths"]["shared_snapshot_manifest"])
    manifest_path = _safe_file(root_path, manifest_relative, "shared snapshot manifest")
    manifest_sha256 = _sha256_bytes(manifest_path.read_bytes())
    paths, artifact_hashes = _artifact_paths(
        root_path, runner_record, str(team_id), str(stage)
    )
    base_bars = _read_bar_returns(
        paths["evaluator_returns"],
        expected_bars,
        "base bar returns",
        risk_policy_id=risk_policy.policy_id if risk_policy.enabled else None,
    )
    double_bars = _read_bar_returns(
        paths["double_cost_evaluator_returns"],
        expected_bars,
        "double-cost bar returns",
        risk_policy_id=risk_policy.policy_id if risk_policy.enabled else None,
    )
    base_daily = _read_daily(paths["daily_returns"], expected_daily, "base daily returns")
    double_daily = _read_daily(
        paths["double_cost_daily_returns"], expected_daily, "double-cost daily returns"
    )
    _validate_daily_reconciliation(base_bars, base_daily, "base")
    _validate_daily_reconciliation(double_bars, double_daily, "double-cost")
    _read_targets(paths["targets"], expected_bars)
    _read_positions(paths["positions"], expected_bars, base_bars)
    events = _read_events(
        paths["events"],
        paths["trades"],
        window.replay_start,
        window.end_exclusive,
    )

    full_tournament_index = pd.date_range(
        pd.Timestamp(str(config.raw["splits"]["visible_development_start"]), tz="UTC"),
        pd.Timestamp(str(config.raw["splits"]["final_oos_end_inclusive"]), tz="UTC"),
        freq="1D",
    )
    regime_labels, btc_bindings = _snapshot_regimes(
        root_path, manifest_path, full_tournament_index
    )
    scored = base_daily.loc[window.score_start : window.score_end]
    double_scored = double_daily.loc[window.score_start : window.score_end]
    scored_bars = base_bars.loc[
        (base_bars.index >= window.score_start) & (base_bars.index < window.end_exclusive)
    ]
    base_metrics = compute_window_metrics(scored)
    double_cost_sharpe = float(compute_window_metrics(double_scored).net_sharpe)
    regimes = _regime_metrics(scored, regime_labels)
    _verify_runner_record(
        runner_record,
        root=root_path,
        config=config,
        team_id=str(team_id),
        stage=str(stage),
        window=window,
        base_metrics=base_metrics,
        double_cost_sharpe=double_cost_sharpe,
        regime_metrics=regimes,
        strategy_sha256=strategy_sha256,
        risk_policy_sha256=risk_sha256,
        source_bundle_sha256=source_bundle_sha256,
        manifest_sha256=manifest_sha256,
        decision_count=len(expected_bars),
        event_count=len(events),
        trade_count=int(events["event_type"].isin(_TRADE_TYPES).sum()),
    )

    identity = {
        "schema_version": 1,
        "stage": stage,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "strategy_sha256": strategy_sha256,
        "risk_policy_sha256": risk_sha256,
        "config_sha256": config.sha256,
        "trial_count": trial_count,
    }
    input_hashes: dict[str, object] = {
        "config": {"path": TOP40_V2_LAYOUT.config_path, "sha256": config.sha256},
        "strategy": {"path": strategy_relative, "sha256": strategy_sha256},
        "risk_policy": {"path": risk_relative, "sha256": risk_sha256},
        "source_bundle_sha256": source_bundle_sha256,
        "shared_snapshot_manifest": {
            "path": manifest_relative,
            "sha256": manifest_sha256,
        },
        "btc_artifacts": btc_bindings,
        "runner_artifacts": {
            name: {"path": runner_record["artifacts"][name], "sha256": digest}
            for name, digest in artifact_hashes.items()
        },
        "runner_record_canonical_json": _canonical_json_sha256(runner_record),
    }

    if stage == "private":
        if (
            parameter_neighborhood_manifest_path is not None
            or walk_forward_manifest_path is not None
        ):
            raise ValueError(
                "private evidence cannot replace frozen development research manifests"
            )
        evidence: dict[str, object] = {
            **identity,
            "aggregate": {
                "net_sharpe": float(base_metrics.net_sharpe),
                "annualized_return": float(base_metrics.annualized_return),
                "max_drawdown": float(base_metrics.max_drawdown),
                "double_cost_sharpe": double_cost_sharpe,
                "positive_quarter_fraction": float(base_metrics.positive_quarter_fraction),
            },
        }
        provenance = {
            "schema_version": 1,
            "builder": "top40-v2-evidence-v1",
            "stage": stage,
            "team_id": team_id,
            "candidate_id": candidate_id,
            "score_window": {
                "start": window.score_start.date().isoformat(),
                "end_inclusive": window.score_end.date().isoformat(),
            },
            "input_sha256": input_hashes,
        }
        return BuiltQualificationEvidence(evidence, provenance)

    if parameter_neighborhood_manifest_path is None:
        raise ValueError("development evidence requires a parameter-neighborhood manifest")
    fold_count = int(config.raw["statistics"]["walk_forward_folds"])
    folds = _fold_slices(scored, fold_count)
    fold_payload = [
        {"fold_id": fold_id, "net_return": float((1.0 + values).prod() - 1.0)}
        for fold_id, values in folds
    ]
    walk_forward, model_hashes = _walk_forward_provenance(
        root_path,
        walk_forward_manifest_path,
        team_id=str(team_id),
        candidate_id=candidate_id,
        fold_slices=folds,
        stitched_sha256=artifact_hashes["daily_returns"],
        allow_evaluation_folds=allow_evaluation_folds,
    )
    neighborhood, neighborhood_provenance, neighbor_hashes = _parameter_neighborhood(
        root_path,
        parameter_neighborhood_manifest_path,
        team_id=str(team_id),
        candidate_id=candidate_id,
        full_daily_index=expected_daily,
        score_start=window.score_start,
        score_end=window.score_end,
    )
    concentration, concentration_parts = _positive_pnl_concentration(scored, folds)
    probability, probability_provenance = trial_adjusted_probability_positive(
        scored, trial_count
    )
    side_daily = _daily_side_contributions(scored_bars)
    scored_labels = regime_labels.reindex(side_daily.index)
    roles = {
        "long_bull_net_return": float(side_daily.loc[scored_labels.eq("bull"), "long"].sum()),
        "short_bear_net_return": float(side_daily.loc[scored_labels.eq("bear"), "short"].sum()),
        "combined_chop_net_return": regimes["chop"]["net_return"],
    }
    executed = _side_executed_notional(events, window.score_start, window.end_exclusive)
    active_threshold = float(config.raw["qualification"]["sleeves"]["minimum_side_exposure"])
    sleeves = {
        side: {
            "active_bar_fraction": float(
                (scored_bars[f"{side}_exposure"] >= active_threshold).mean()
            ),
            "mean_gross_exposure": float(scored_bars[f"{side}_exposure"].mean()),
            "executed_notional_usdt": float(executed[side]),
        }
        for side in ("long", "short")
    }
    evidence = {
        **identity,
        "aggregate": {
            "net_sharpe": float(base_metrics.net_sharpe),
            "annualized_return": float(base_metrics.annualized_return),
            "calmar": float(base_metrics.calmar),
            "max_drawdown": float(base_metrics.max_drawdown),
            "double_cost_sharpe": double_cost_sharpe,
            "positive_quarter_fraction": float(base_metrics.positive_quarter_fraction),
            "trial_adjusted_probability_positive": probability,
        },
        "folds": fold_payload,
        "regimes": regimes,
        "roles": roles,
        "sleeves": sleeves,
        "stability": {
            **neighborhood,
            "maximum_positive_pnl_concentration": concentration,
        },
    }
    input_hashes["walk_forward_models"] = model_hashes
    input_hashes["parameter_neighbor_returns"] = neighbor_hashes
    provenance = {
        "schema_version": 1,
        "builder": "top40-v2-evidence-v1",
        "stage": stage,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "score_window": {
            "start": window.score_start.date().isoformat(),
            "end_inclusive": window.score_end.date().isoformat(),
        },
        "input_sha256": input_hashes,
        "walk_forward": walk_forward,
        "parameter_neighborhood": neighborhood_provenance,
        "trial_adjusted_probability": probability_provenance,
        "positive_pnl_concentration": {
            "definition": "maximum positive-return share across fixed folds and quarters",
            **concentration_parts,
        },
        "role_attribution": {
            "definition": (
                "Daily equity PnL contribution; price/funding are side-native, execution costs "
                "are allocated by current-plus-prior side exposure, and intraday compounding is "
                "reconciled exactly to portfolio daily net return."
            )
        },
        "executed_notional_attribution": {
            "definition": (
                "Canonical trade-event notional follows the reconstructed signed-quantity path; "
                "cross-zero orders are split by closing/opening quantity distance."
            )
        },
    }
    return BuiltQualificationEvidence(evidence, provenance)
