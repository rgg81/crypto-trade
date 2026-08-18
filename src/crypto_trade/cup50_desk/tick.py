"""One CUP-50 paper boundary, produced by the frozen tournament evaluator itself."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20_desk.live_data import FrameSchema, append_frame
from crypto_trade.cup50.availability import load_unavailability_audit
from crypto_trade.cup50.config import IS_START, OOS_END
from crypto_trade.cup50.replay import (
    REBALANCE_COLUMN,
    apply_strategy_parameters,
    load_strategy_module,
    run_candidate,
    scale_targets,
    strategy_from_module,
)
from crypto_trade.cup50_desk.authority import (
    paper_root,
    repository_root,
    sha256_file,
    verify_deployment,
    verify_lineage,
    winner_bundle,
)
from crypto_trade.cup50_desk.snapshot_forward import build_forward_snapshot

INTERVAL = pd.Timedelta(hours=8)
NORMAL_COST = 1
SEED = 2
HISTORICAL_PREFIX = "historical-prefix.parquet"
LEDGER_DIRNAME = "ledger"
BOUNDARIES_DIRNAME = "boundaries"
FORWARD_RETURNS = "forward_returns"
EVENTS = "events"
POSITIONS = "positions"
TARGETS = "targets"
INTEGRITY = "integrity.json"
LATEST = "latest-boundary.json"

_TIMESTAMP = "datetime64[ns, UTC]"

RETURN_SCHEMA = FrameSchema(
    name=FORWARD_RETURNS,
    columns=(
        "decision_time",
        "right_boundary",
        "phase",
        "price_return",
        "funding_return",
        "gross_return",
        "fees_slippage",
        "net_return",
        "turnover",
        "gross_exposure",
        "equity",
    ),
    dtypes=(_TIMESTAMP, _TIMESTAMP, "str", *("float64",) * 8),
    key=("decision_time",),
    order=("decision_time",),
)

EVENT_SCHEMA = FrameSchema(
    name=EVENTS,
    columns=(
        "timestamp",
        "symbol",
        "event_type",
        "event_sequence",
        "phase",
        "notional",
    ),
    dtypes=(_TIMESTAMP, "str", "str", "int64", "str", "float64"),
    key=("timestamp", "symbol", "event_type", "event_sequence"),
    order=("timestamp", "symbol", "event_type", "event_sequence"),
)

POSITION_SCHEMA = FrameSchema(
    name=POSITIONS,
    columns=("boundary", "phase", "symbol", "quantity"),
    dtypes=(_TIMESTAMP, "str", "str", "float64"),
    key=("boundary", "symbol"),
    order=("boundary", "symbol"),
)

TARGET_SCHEMA = FrameSchema(
    name=TARGETS,
    columns=(
        "decision_time",
        "phase",
        "symbol",
        "rebalance",
        "raw_target",
        "scaled_target",
    ),
    dtypes=(_TIMESTAMP, "str", "str", "bool", "float64", "float64"),
    key=("decision_time", "symbol"),
    order=("decision_time", "symbol"),
)


class HistoricalParityError(RuntimeError):
    """The live replay does not reproduce the frozen 8-hour historical stream exactly."""


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("paper boundary must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def _phase(decision: pd.Timestamp, launch: pd.Timestamp) -> str:
    return "official" if decision >= launch else "bridge"


def _atomic_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _json(path: Path, payload: object) -> None:
    _atomic_text(path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _historical_stream(replay: Any) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for multiplier in (1, 2, 3):
        frame = replay.costs[multiplier].returns.loc[
            replay.costs[multiplier].returns.index < OOS_END
        ].reset_index()
        frame.insert(1, "cost_multiplier", multiplier)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True).sort_values(
        ["cost_multiplier", "decision_time"], ignore_index=True
    )


def verify_historical_prefix(replay: Any, path: Path) -> str:
    expected = pd.read_parquet(path)
    observed = _historical_stream(replay)
    expected = expected.loc[:, observed.columns]
    try:
        pd.testing.assert_frame_equal(
            observed,
            expected,
            check_exact=True,
            check_dtype=True,
            check_like=False,
        )
    except AssertionError as exc:
        raise HistoricalParityError(f"frozen historical prefix changed: {exc}") from exc
    return sha256_file(path)


def replay_winner(snapshot: Any, *, root: Path) -> Any:
    nomination = json.loads(
        (root / "tournament" / "cup50" / "nominations" / "team-02.json").read_text()
    )
    strategy = strategy_from_module(load_strategy_module(winner_bundle(root) / "strategy.py"))
    apply_strategy_parameters(strategy, nomination["centre"])
    audit = load_unavailability_audit(
        root / "tournament" / "cup50" / "organizer-recovery-unavailability.json"
    )
    return run_candidate(
        strategy,
        snapshot=snapshot,
        start=IS_START,
        end=snapshot.window_end,
        seed=SEED,
        terminal=False,
        unavailability=audit,
        record_events=True,
    )


def _return_rows(
    result: Any, launch: pd.Timestamp, boundary: pd.Timestamp
) -> pd.DataFrame:
    """Return only settled, append-stable intervals.

    The evaluator's row at ``boundary`` is its terminal row.  With no next transaction bar in
    the half-open snapshot it prices that interval at the current bar's close; the following
    replay correctly prices the same interval at the next bar's open.  CUP-20 therefore withholds
    the terminal row until the following tick, and CUP-50 must do the same.  Publishing it here
    would guarantee an append-invariance failure on every healthy next boundary.
    """
    index = pd.DatetimeIndex(result.returns.index)
    frame = result.returns.loc[(index >= OOS_END) & (index < boundary)].reset_index()
    frame.insert(
        2,
        "phase",
        frame["decision_time"].map(lambda value: _phase(pd.Timestamp(value), launch)),
    )
    return frame.loc[:, RETURN_SCHEMA.columns]


def _event_rows(
    result: Any, launch: pd.Timestamp, boundary: pd.Timestamp | None = None
) -> pd.DataFrame:
    if result.events.empty:
        return pd.DataFrame(columns=EVENT_SCHEMA.columns)
    frame = result.events.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    if boundary is not None:
        # Events after the current decision belong to the evaluator's terminal interval.  Like
        # its return row, they are not stable until the next replay supplies the following open.
        frame = frame.loc[frame["timestamp"] <= boundary].copy()
    left = frame["timestamp"].dt.ceil("8h") - INTERVAL
    trade_like = frame["event_type"].isin({"trade", "risk_reduction"})
    left.loc[trade_like] = frame.loc[trade_like, "timestamp"].dt.floor("8h")
    frame = frame.loc[left >= OOS_END].copy()
    left = left.loc[frame.index]
    frame["phase"] = left.map(lambda value: _phase(pd.Timestamp(value), launch))
    frame["event_sequence"] = frame.groupby(
        ["timestamp", "symbol", "event_type"], sort=False
    ).cumcount()
    return frame.loc[:, EVENT_SCHEMA.columns]


def _position_rows(result: Any, boundary: pd.Timestamp, phase: str) -> pd.DataFrame:
    quantities: Mapping[str, float] = result.final_state.quantities
    rows = [
        {"boundary": boundary, "phase": phase, "symbol": symbol, "quantity": quantity}
        for symbol, quantity in sorted(quantities.items())
    ]
    if not rows:
        rows.append(
            {"boundary": boundary, "phase": phase, "symbol": "__FLAT__", "quantity": 0.0}
        )
    return pd.DataFrame(rows, columns=POSITION_SCHEMA.columns)


def _target_rows(replay: Any, launch: pd.Timestamp) -> pd.DataFrame:
    raw = replay.raw_targets.loc[replay.raw_targets.index >= OOS_END]
    scaled = scale_targets(replay.raw_targets, replay.risk_scalars).loc[raw.index]
    symbols = [column for column in raw if column != REBALANCE_COLUMN]
    rows: list[dict[str, object]] = []
    for decision in raw.index:
        phase = _phase(pd.Timestamp(decision), launch)
        rebalance = bool(raw.at[decision, REBALANCE_COLUMN])
        rows.append(
            {
                "decision_time": decision,
                "phase": phase,
                "symbol": "__CONTROL__",
                "rebalance": rebalance,
                "raw_target": 0.0,
                "scaled_target": 0.0,
            }
        )
        for symbol in symbols:
            raw_value = raw.at[decision, symbol]
            scaled_value = scaled.at[decision, symbol]
            if pd.isna(raw_value) and pd.isna(scaled_value):
                continue
            rows.append(
                {
                    "decision_time": decision,
                    "phase": phase,
                    "symbol": symbol,
                    "rebalance": rebalance,
                    "raw_target": 0.0 if pd.isna(raw_value) else float(raw_value),
                    "scaled_target": 0.0 if pd.isna(scaled_value) else float(scaled_value),
                }
            )
    return pd.DataFrame(rows, columns=TARGET_SCHEMA.columns)


def _artifact_binding(path: Path, paper: Path) -> dict[str, object]:
    if path.suffix == ".parquet":
        rows: int | None = len(pd.read_parquet(path))
    elif path.suffix == ".csv":
        rows = len(pd.read_csv(path))
    else:
        rows = None
    return {
        "path": path.relative_to(paper).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
        "rows": rows,
    }


def persist_tick(
    *,
    boundary: object,
    generation: Path,
    membership: pd.DataFrame,
    root: str | Path | None = None,
) -> Mapping[str, Any]:
    base = Path(root).resolve() if root is not None else repository_root()
    paper = paper_root(base)
    deployment = verify_deployment(base)
    lineage = verify_lineage(base)
    launch = _utc(lineage["authority"]["launch_time"])
    decision = _utc(boundary)
    if decision < launch or decision != decision.floor("8h"):
        raise ValueError(f"paper observation cannot publish boundary {decision}")
    snapshot = build_forward_snapshot(generation, membership, decision, root=base)
    replay = replay_winner(snapshot, root=base)
    prefix_path = paper / HISTORICAL_PREFIX
    prefix_sha = verify_historical_prefix(replay, prefix_path)
    normal = replay.costs[NORMAL_COST]
    reconstruction = lineage["reconstruction"]
    historical = normal.returns.loc[normal.returns.index < OOS_END]
    if float(historical.iloc[-1]["equity"]) != float(reconstruction["equity"]):
        raise HistoricalParityError("historical seam equity differs from reconstruction")

    phase = _phase(decision, launch)
    ledgers = paper / LEDGER_DIRNAME
    ledgers.mkdir(parents=True, exist_ok=True)
    returns = _return_rows(normal, launch, decision)
    events = _event_rows(normal, launch, decision)
    positions = _position_rows(normal, decision, phase)
    targets = _target_rows(replay, launch)
    paths = {
        FORWARD_RETURNS: ledgers / f"{FORWARD_RETURNS}.parquet",
        EVENTS: ledgers / f"{EVENTS}.parquet",
        POSITIONS: ledgers / f"{POSITIONS}.parquet",
        TARGETS: ledgers / f"{TARGETS}.parquet",
    }
    append_frame(paths[FORWARD_RETURNS], returns, name=RETURN_SCHEMA)
    append_frame(paths[EVENTS], events, name=EVENT_SCHEMA)
    append_frame(paths[POSITIONS], positions, name=POSITION_SCHEMA)
    append_frame(paths[TARGETS], targets, name=TARGET_SCHEMA)
    for name, path in paths.items():
        pd.read_parquet(path).to_csv(
            paper / f"{name}.csv", index=False, lineterminator="\n", float_format="%.17g"
        )
    current_positions = positions.loc[positions["symbol"] != "__FLAT__"].copy()
    current_positions.to_csv(
        paper / "current_positions.csv",
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    )

    active = membership.loc[
        pd.to_datetime(membership["reconstitution_time"], utc=True) <= decision
    ]
    active_boundary = pd.Timestamp(active["reconstitution_time"].max())
    members = tuple(
        active.loc[active["reconstitution_time"] == active_boundary]
        .sort_values(["liquidity_rank", "symbol"])["symbol"]
        .astype(str)
    )
    settled_decision = decision - INTERVAL
    latest_return = returns.loc[returns["decision_time"] == settled_decision].iloc[0]
    current_decision = normal.returns.loc[decision]
    boundary_record: dict[str, Any] = {
        "schema_version": 2,
        "namespace": "cup50-team02-paper-boundary",
        "boundary": decision.isoformat(),
        "right_boundary": (decision + INTERVAL).isoformat(),
        "phase": phase,
        "lineage_sha256": lineage["authority"]["lineage_sha256"],
        "deployment_sha256": deployment["manifest_sha256"],
        "cache_generation_sha256": generation.name,
        "snapshot_sha256": snapshot.manifest_sha256,
        "historical_prefix_sha256": prefix_sha,
        "historical_parity": True,
        "append_invariant": True,
        "public_data_only": True,
        "membership_boundary": active_boundary.isoformat(),
        "membership_count": len(members),
        "members": list(members),
        "settled_through": decision.isoformat(),
        "latest_settled_decision_time": settled_decision.isoformat(),
        "equity": float(latest_return["equity"]),
        "latest_settled_net_return": float(latest_return["net_return"]),
        # Exposure and turnover are decided at this boundary and do not depend on the terminal
        # interval's eventual endpoint price.  The terminal PnL itself is deliberately withheld.
        "gross_exposure": float(current_decision["gross_exposure"]),
        "turnover": float(current_decision["turnover"]),
        "position_count": len(normal.final_state.quantities),
        "positions": dict(sorted(normal.final_state.quantities.items())),
    }
    boundary_record["record_sha256"] = hashlib.sha256(
        json.dumps(
            boundary_record, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    boundary_path = paper / BOUNDARIES_DIRNAME / f"{decision.strftime('%Y%m%dT%H%M%SZ')}.json"
    if boundary_path.exists():
        if json.loads(boundary_path.read_text()) != boundary_record:
            raise RuntimeError(f"immutable boundary record drifted: {boundary_path}")
    else:
        _json(boundary_path, boundary_record)
    _json(paper / LATEST, boundary_record)

    artifact_paths = {
        **paths,
        "current_positions": paper / "current_positions.csv",
        "latest": paper / LATEST,
        "cache_manifest": generation / "cache-manifest.json",
        "historical_prefix": prefix_path,
        "deployment": paper / "deployment-manifest.json",
    }
    bindings: dict[str, dict[str, object]] = {}
    for label, path in artifact_paths.items():
        if path.is_relative_to(paper):
            bindings[label] = _artifact_binding(path, paper)
        else:
            bindings[label] = {
                "path": str(path),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
                "rows": None,
                "external": True,
            }
    integrity = {
        "schema_version": 1,
        "namespace": "cup50-team02-paper-integrity",
        "status": "PASS",
        "lineage_sha256": lineage["authority"]["lineage_sha256"],
        "latest_boundary": decision.isoformat(),
        "right_boundary": (decision + INTERVAL).isoformat(),
        "membership_count": len(members),
        "historical_parity": True,
        "append_invariance": True,
        "public_data_only": True,
        "artifacts": bindings,
    }
    integrity["integrity_sha256"] = hashlib.sha256(
        json.dumps(integrity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _json(paper / INTEGRITY, integrity)
    return boundary_record
