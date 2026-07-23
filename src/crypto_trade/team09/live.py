"""Paper-trading projection of the exact frozen Team 09 continuous replay."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.team09.authority import (
    CANDIDATE_ID,
    sha256_file,
    verify_frozen_authority,
)
from crypto_trade.team09.backtest import (
    EVALUATOR_CONFIG,
    INTERVAL_HOURS,
    LIVE_FORWARD_START,
    Team09Replay,
    run_replay,
)
from crypto_trade.team09.live_data import LiveMarketData, exact_boundary
from crypto_trade.tournament.metrics_v3 import (
    aggregate_daily_returns,
    compute_window_metrics,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

INTERVAL = pd.Timedelta(hours=INTERVAL_HOURS)
PAPER_INITIAL_EQUITY = EVALUATOR_CONFIG.initial_equity
_QUANTITY_EVENT_TYPES = frozenset(
    {
        "trade",
        "risk_policy_action",
        "risk_reduction",
        "forced_exit",
        "conservative_settlement",
    }
)
_BOUNDARY_FILL_EVENT_TYPES = frozenset(
    {
        "trade",
        "risk_policy_action",
        "risk_reduction",
        "forced_exit",
        "conservative_settlement",
    }
)
_OPEN_EXECUTION_COST_EVENT_TYPES = frozenset(
    {"trade", "risk_policy_action", "risk_reduction"}
)


@dataclasses.dataclass(frozen=True)
class Team09PaperTick:
    boundary: pd.Timestamp
    replay: Team09Replay
    live_data: LiveMarketData
    stable_returns: pd.DataFrame
    held_weights: pd.Series
    held_quantities: pd.Series
    raw_target: pd.Series
    rebalance_instruction: bool
    boundary_fills: pd.DataFrame
    risk_scale: float
    modeled_equity_after_execution: float


def run_live_replay(
    live_data: LiveMarketData,
    *,
    boundary: object,
) -> Team09PaperTick:
    """Run the same strategy/evaluator path and discard only its forming terminal return."""

    live_boundary = exact_boundary(boundary)
    if live_data.diagnostics.boundary != live_boundary:
        raise ValueError("live-data boundary does not match the paper replay boundary")
    replay = run_replay(
        live_data.market_data,
        end_exclusive=live_boundary + INTERVAL,
        cost_multipliers=(1.0,),
    )
    result = replay.evaluation()
    if live_boundary not in replay.targets.index or live_boundary not in result.positions.index:
        raise RuntimeError("Team 09 replay did not produce the requested live boundary")
    if result.returns.index.max() != live_boundary:
        raise RuntimeError("Team 09 live replay has an unexpected terminal boundary")

    # The evaluator must have one last row to compute the boundary decision and held
    # position. Its terminal PnL/forced close is deliberately discarded because the
    # interval has only just opened.
    stable_returns = result.returns.loc[result.returns.index < live_boundary].copy()
    held_weights = _nonzero(result.positions.loc[live_boundary])
    held_quantities = _held_quantities(result.events, through=live_boundary)
    target_row = replay.targets.loc[live_boundary]
    rebalance_instruction = bool(target_row[REBALANCE_INSTRUCTION_COLUMN])
    raw_target = _nonzero(target_row.drop(labels=[REBALANCE_INSTRUCTION_COLUMN]).astype(float))
    boundary_events = _events_at(result.events, live_boundary)
    boundary_fills = boundary_events.loc[
        boundary_events["event_type"].isin(_BOUNDARY_FILL_EVENT_TYPES)
    ].copy()
    risk_scale = float(result.returns.loc[live_boundary, "risk_policy_gross_scale"])
    modeled_equity = _modeled_equity_after_execution(
        result.returns,
        boundary_events,
        boundary=live_boundary,
    )
    return Team09PaperTick(
        boundary=live_boundary,
        replay=replay,
        live_data=live_data,
        stable_returns=stable_returns,
        held_weights=held_weights,
        held_quantities=held_quantities,
        raw_target=raw_target,
        rebalance_instruction=rebalance_instruction,
        boundary_fills=boundary_fills,
        risk_scale=risk_scale,
        modeled_equity_after_execution=modeled_equity,
    )


def persist_paper_tick(
    tick: Team09PaperTick,
    paper_dir: str | Path,
) -> dict[str, Path]:
    """Atomically persist a restart-safe, append-invariant paper tick."""

    destination = Path(paper_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    bridge_path = destination / "bridge_bar_returns.parquet"
    forward_path = destination / "forward_returns.csv"
    positions_path = destination / "current_positions.csv"
    fills_path = destination / "paper_fills.csv"
    integrity_path = destination / "integrity.json"
    gates_path = destination / "gates.csv"
    latest_path = destination / "latest-boundary.json"
    cache_manifest_path = tick.live_data.cache_dir / "cache-manifest.json"

    stable_bridge = tick.stable_returns.loc[
        tick.stable_returns.index
        >= pd.Timestamp("2026-07-01T00:00:00Z")
    ].copy()
    stable_bridge.index.name = "timestamp"
    stable_bridge = stable_bridge.reset_index()
    canonical_bridge = _append_invariant_frame(
        bridge_path,
        stable_bridge,
        keys=("timestamp",),
    )
    forward = canonical_bridge.loc[
        pd.to_datetime(canonical_bridge["timestamp"], utc=True) >= LIVE_FORWARD_START
    ].copy()
    _write_csv_atomic(forward, forward_path)

    position_frame = _position_frame(tick)
    _write_csv_atomic(position_frame, positions_path)
    fills = _append_boundary_fills(tick, fills_path)
    decision_payload = _boundary_payload(tick, position_frame, fills)
    decision_path = _write_boundary_record(destination, tick.boundary, decision_payload)
    _write_json_atomic(decision_payload, latest_path)

    gate_frame = _gate_frame(forward)
    _write_csv_atomic(gate_frame, gates_path)
    authority = verify_frozen_authority()
    integrity = {
        "schema_version": "team09-paper-integrity-v2",
        "status": "PASS",
        "candidate_id": CANDIDATE_ID,
        "paper_only": True,
        "boundary": tick.boundary.isoformat(),
        "forming_terminal_return_discarded": True,
        "shared_backtest_live_path": "crypto_trade.team09.backtest.run_replay",
        "append_invariance": "PASS",
        "strategy_sha256": authority.strategy_sha256,
        "risk_policy_sha256": authority.risk_policy_sha256,
        "source_bundle_sha256": authority.source_bundle_sha256,
        "source_archive_sha256": authority.source_archive_sha256,
        "dependency_lock_sha256": authority.dependency_lock_sha256,
        "data_manifest_sha256": authority.data_manifest_sha256,
        "evaluator_authority_sha256": authority.evaluator_authority_sha256,
        "pure_crypto_policy_sha256": authority.pure_crypto_policy_sha256,
        "deployment_bundle_sha256": authority.deployment_bundle_sha256,
        "deployment_manifest_sha256": authority.deployment_manifest_sha256,
        "deployment_git_commit": authority.deployment_git_commit,
        "stable_bridge_rows": int(len(canonical_bridge)),
        "forward_rows": int(len(forward)),
        "latest_sealed_return": (
            pd.Timestamp(canonical_bridge["timestamp"].max()).isoformat()
            if not canonical_bridge.empty
            else None
        ),
        "decision_sha256": _canonical_json_sha256(decision_payload),
        "data": tick.live_data.diagnostics.to_dict(),
    }
    run_log_path = destination / "runs.log"
    _update_run_log(run_log_path, integrity)
    integrity["artifacts"] = {
        "bridge_returns": _file_binding(
            bridge_path, rows=len(canonical_bridge), root=destination
        ),
        "forward_returns": _file_binding(
            forward_path, rows=len(forward), root=destination
        ),
        "positions": _file_binding(
            position_frame, positions_path, root=destination
        ),
        "fills": _file_binding(
            fills_path, rows=_csv_rows(fills_path), root=destination
        ),
        "gates": _file_binding(
            gates_path, rows=len(gate_frame), root=destination
        ),
        "decision": _file_binding(decision_path, rows=1, root=destination),
        "latest": _file_binding(latest_path, rows=1, root=destination),
        "runs": _file_binding(
            run_log_path, rows=_text_rows(run_log_path), root=destination
        ),
        "cache_manifest": _file_binding(
            cache_manifest_path, rows=1, root=destination
        ),
    }
    _write_json_atomic(integrity, integrity_path)
    return {
        "bridge_returns": bridge_path,
        "forward_returns": forward_path,
        "positions": positions_path,
        "fills": fills_path,
        "gates": gates_path,
        "integrity": integrity_path,
        "decision": decision_path,
        "latest": latest_path,
    }


def _held_quantities(events: pd.DataFrame, *, through: pd.Timestamp) -> pd.Series:
    if events.empty:
        return pd.Series(dtype=float, name="quantity")
    timestamps = pd.to_datetime(events["timestamp"], utc=True)
    changing = events.loc[
        (timestamps <= through) & events["event_type"].isin(_QUANTITY_EVENT_TYPES)
    ].copy()
    if changing.empty:
        return pd.Series(dtype=float, name="quantity")
    quantities = changing.groupby("symbol", observed=True)["quantity"].sum()
    quantities = quantities.loc[quantities.abs() > 1e-12].sort_index()
    return quantities.rename("quantity")


def _events_at(events: pd.DataFrame, boundary: pd.Timestamp) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    timestamps = pd.to_datetime(events["timestamp"], utc=True)
    return events.loc[timestamps == boundary].reset_index(drop=True)


def _modeled_equity_after_execution(
    returns: pd.DataFrame,
    boundary_events: pd.DataFrame,
    *,
    boundary: pd.Timestamp,
) -> float:
    prior = returns.loc[returns.index < boundary]
    prior_equity = (
        PAPER_INITIAL_EQUITY if prior.empty else float(prior.iloc[-1]["equity"])
    )
    if boundary_events.empty:
        return prior_equity
    before_funding = boundary_events.loc[
        (boundary_events["event_type"] == "funding")
        & (boundary_events["phase"] == "before_rebalance"),
        "cashflow",
    ].sum()
    fills = boundary_events.loc[
        boundary_events["event_type"].isin(_OPEN_EXECUTION_COST_EVENT_TYPES)
    ]
    costs = fills["fee"].sum() + fills["slippage"].sum()
    return float(prior_equity + before_funding - costs)


def _position_frame(tick: Team09PaperTick) -> pd.DataFrame:
    symbols = sorted(tick.held_weights.index)
    return pd.DataFrame(
        {
            "boundary": [tick.boundary] * len(symbols),
            "symbol": symbols,
            "weight": [float(tick.held_weights.get(symbol, 0.0)) for symbol in symbols],
            "quantity": [
                float(tick.held_quantities.get(symbol, 0.0)) for symbol in symbols
            ],
            "side": [
                "LONG"
                if tick.held_weights.get(symbol, 0.0) > 0.0
                else "SHORT"
                for symbol in symbols
            ],
        }
    )


def _append_boundary_fills(tick: Team09PaperTick, path: Path) -> pd.DataFrame:
    fills = tick.boundary_fills.copy()
    if fills.empty:
        fills = pd.DataFrame(
            columns=[
                "timestamp",
                "symbol",
                "event_type",
                "phase",
                "quantity",
                "price",
                "notional",
                "fee",
                "slippage",
                "reason",
                "policy_id",
            ]
        )
    keep = [
        column
        for column in (
            "timestamp",
            "symbol",
            "event_type",
            "phase",
            "quantity",
            "price",
            "notional",
            "fee",
            "slippage",
            "reason",
            "policy_id",
        )
        if column in fills
    ]
    fills = fills.loc[:, keep]
    existing = pd.read_csv(path) if path.is_file() else fills.iloc[0:0].copy()
    if not existing.empty:
        existing["timestamp"] = pd.to_datetime(existing["timestamp"], utc=True)
    combined = pd.concat([existing, fills], ignore_index=True)
    if not combined.empty:
        duplicate_keys = ["timestamp", "symbol", "event_type", "phase"]
        duplicate_mask = combined.duplicated(duplicate_keys, keep=False)
        if duplicate_mask.any():
            duplicates = combined.loc[duplicate_mask].sort_values(duplicate_keys)
            for _, group in duplicates.groupby(duplicate_keys, dropna=False):
                if not _rows_equal(group.iloc[0], group.iloc[-1]):
                    raise RuntimeError(
                        "APPEND-INVARIANCE ABORT: paper fills revised a boundary event"
                    )
            combined = combined.drop_duplicates(duplicate_keys, keep="first")
        combined = combined.sort_values(duplicate_keys).reset_index(drop=True)
    _write_csv_atomic(combined, path)
    return fills


def _boundary_payload(
    tick: Team09PaperTick,
    positions: pd.DataFrame,
    fills: pd.DataFrame,
) -> dict[str, object]:
    return {
        "schema_version": "team09-paper-boundary-v1",
        "candidate_id": CANDIDATE_ID,
        "paper_only": True,
        "boundary": tick.boundary.isoformat(),
        "rebalance_instruction": tick.rebalance_instruction,
        "raw_target": {
            str(symbol): float(value)
            for symbol, value in tick.raw_target.sort_index().items()
        },
        "risk_scale": tick.risk_scale,
        "modeled_equity_after_execution": tick.modeled_equity_after_execution,
        "gross_exposure": float(tick.held_weights.abs().sum()),
        "net_exposure": float(tick.held_weights.sum()),
        "positions": _json_records(positions.drop(columns=["boundary"])),
        "fills": _json_records(fills),
        "data_boundary": tick.live_data.diagnostics.boundary.isoformat(),
        "current_membership": list(
            tick.live_data.diagnostics.current_membership_symbols
        ),
    }


def _gate_frame(forward: pd.DataFrame) -> pd.DataFrame:
    if forward.empty:
        return pd.DataFrame(
            [
                {
                    "status": "INSUFFICIENT",
                    "observations": 0,
                    "daily_observations": 0,
                    "minimum_observations": 90,
                    "cumulative_return": 0.0,
                    "net_sharpe": 0.0,
                    "max_drawdown": 0.0,
                }
            ]
        )
    values = pd.Series(
        pd.to_numeric(forward["net_return"], errors="raise").to_numpy(),
        index=pd.to_datetime(forward["timestamp"], utc=True),
        dtype=float,
        name="net_return",
    )
    daily = aggregate_daily_returns(values)
    metrics = compute_window_metrics(daily)
    observations = len(values)
    status = "INSUFFICIENT" if observations < 90 else "RUNNING"
    return pd.DataFrame(
        [
            {
                "status": status,
                "observations": observations,
                "daily_observations": len(daily),
                "minimum_observations": 90,
                "cumulative_return": float((1.0 + values).prod() - 1.0),
                "net_sharpe": metrics.net_sharpe,
                "max_drawdown": metrics.max_drawdown,
            }
        ]
    )


def _append_invariant_frame(
    path: Path,
    fresh: pd.DataFrame,
    *,
    keys: tuple[str, ...],
) -> pd.DataFrame:
    existing = pd.read_parquet(path) if path.is_file() else fresh.iloc[0:0].copy()
    if not existing.empty:
        for key in keys:
            if "time" in key:
                existing[key] = pd.to_datetime(existing[key], utc=True)
    for key in keys:
        if "time" in key:
            fresh[key] = pd.to_datetime(fresh[key], utc=True)
    overlap = existing.merge(
        fresh,
        on=list(keys),
        how="inner",
        suffixes=("_old", "_new"),
        validate="one_to_one",
    )
    value_columns = [column for column in fresh if column not in keys]
    for column in value_columns:
        old = overlap[f"{column}_old"].to_numpy()
        new = overlap[f"{column}_new"].to_numpy()
        if not _exact_array_equal(old, new):
            raise RuntimeError(
                f"APPEND-INVARIANCE ABORT: sealed paper return revised {column}"
            )
    additions = fresh.merge(
        existing.loc[:, list(keys)],
        on=list(keys),
        how="left",
        indicator=True,
    )
    additions = additions.loc[additions["_merge"] == "left_only", fresh.columns]
    result = pd.concat([existing, additions], ignore_index=True)
    result = result.sort_values(list(keys)).reset_index(drop=True)
    _write_parquet_atomic(result, path)
    return result


def _write_boundary_record(
    destination: Path,
    boundary: pd.Timestamp,
    payload: dict[str, object],
) -> Path:
    records = destination / "boundaries"
    records.mkdir(parents=True, exist_ok=True)
    name = boundary.strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = records / name
    canonical = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") != canonical:
        raise RuntimeError(
            "APPEND-INVARIANCE ABORT: boundary decision changed on replay"
        )
    if not path.is_file():
        _write_text_atomic(canonical, path)
    return path


def _update_run_log(path: Path, integrity: MappingLike) -> None:
    stable = {
        "boundary": integrity["boundary"],
        "status": integrity["status"],
        "append_invariance": integrity["append_invariance"],
        "forward_rows": integrity["forward_rows"],
        "decision_sha256": integrity["decision_sha256"],
    }
    rows: list[dict[str, object]] = []
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            payload = json.loads(raw_line)
            if not isinstance(payload, dict):
                raise ValueError("Team 09 run log contains a non-object")
            rows.append(payload)
    existing = [row for row in rows if row.get("boundary") == stable["boundary"]]
    if existing:
        prior = {key: existing[-1].get(key) for key in stable}
        if prior != stable:
            raise RuntimeError(
                "APPEND-INVARIANCE ABORT: paper run log revised a boundary"
            )
    else:
        rows.append(
            {
                "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
                **stable,
            }
        )
    text = "".join(
        json.dumps(row, allow_nan=False, sort_keys=True) + "\n" for row in rows
    )
    _write_text_atomic(text, path)


def _file_binding(
    path_or_frame: Path | pd.DataFrame,
    path: Path | None = None,
    *,
    rows: int | None = None,
    root: Path | None = None,
) -> dict[str, object]:
    file_path = path_or_frame if isinstance(path_or_frame, Path) else path
    if file_path is None:
        raise TypeError("file binding requires a path")
    row_count = len(path_or_frame) if isinstance(path_or_frame, pd.DataFrame) else rows
    if row_count is None:
        raise TypeError("file binding requires a row count")
    return {
        "path": (
            file_path.relative_to(root).as_posix()
            if root is not None
            else file_path.name
        ),
        "size": file_path.stat().st_size,
        "sha256": sha256_file(file_path),
        "rows": int(row_count),
    }


def _csv_rows(path: Path) -> int:
    return max(_text_rows(path) - 1, 0)


def _text_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _line in handle)


def _json_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    if frame.empty:
        return []
    output = frame.copy()
    for column in output:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype):
            output[column] = pd.to_datetime(output[column], utc=True).map(
                lambda value: value.isoformat()
            )
    output = output.replace({np.nan: None})
    return [
        {str(key): _json_scalar(value) for key, value in record.items()}
        for record in output.to_dict(orient="records")
    ]


def _json_scalar(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _nonzero(values: pd.Series) -> pd.Series:
    result = pd.Series(values, dtype=float)
    return result.loc[result.abs() > 1e-12].sort_index()


def _rows_equal(left: pd.Series, right: pd.Series) -> bool:
    return all(
        (pd.isna(left[column]) and pd.isna(right[column]))
        or left[column] == right[column]
        for column in left.index
    )


def _exact_array_equal(left: np.ndarray, right: np.ndarray) -> bool:
    if left.dtype.kind in "fc" or right.dtype.kind in "fc":
        return bool(np.array_equal(left, right, equal_nan=True))
    return bool(np.array_equal(left, right))


def _canonical_json_sha256(payload: object) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _write_parquet_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    frame.to_parquet(
        temporary,
        engine="pyarrow",
        compression="zstd",
        index=False,
    )
    os.replace(temporary, path)


def _write_csv_atomic(frame: pd.DataFrame, path: Path) -> None:
    output = frame.copy()
    for column in output:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype):
            output[column] = pd.to_datetime(output[column], utc=True).dt.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    output.to_csv(
        temporary,
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    )
    os.replace(temporary, path)


def _write_json_atomic(payload: object, path: Path) -> None:
    _write_text_atomic(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        path,
    )


def _write_text_atomic(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


MappingLike = dict[str, object]
