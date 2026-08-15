"""One paper boundary, evaluated by re-running the tournament's own evaluator over everything.

**Parity is by construction, not by comparison.** At each boundary the desk assembles a snapshot
through that boundary and re-runs :func:`crypto_trade.cup20.runner.run_candidate` over the WHOLE
window from ``IS_START`` to now, then reads the tail off the result. Next-bar-open fills, the 5 bps
taker fee, the 2.5 bps slippage per side, native per-event funding, the common risk unit and both
applications of the section 4 exposure caps are therefore not *matched* to the backtest -- they ARE
the backtest, executing the same lines of the same module against the same frozen ``[execution]``
and ``[risk_unit]`` tables.

So there is no code path here that computes a fill price, a fee, a slippage figure, a funding
payment or a position size. Every such number is lifted verbatim out of the evaluator's own
``EvaluationResult``. If one is ever computed here instead, execution has been duplicated and the
two copies can now disagree -- which is the entire failure mode this design exists to make
impossible. ``tests/cup20_desk/test_tick.py`` asserts by inspection that this module contains no
arithmetic on a price, a fee, a rate or a quantity.

Cost: one full-window evaluation per tick, measured at 410 s over the real 6525-boundary window on
this machine. That is the price of exact replay and it is worth paying against an 8-hourly grid.

**The terminal return row is discarded, and it must be.** The evaluator's last row covers the
interval that has only just opened, and it force-exits the whole book at the window's end -- an
artifact of where the window stops, not a decision. It is also the one row that is guaranteed to
change on the next tick, when the window no longer stops there. Recording it would make the
determinism check below abort on every single tick. What IS recorded at the terminal boundary is
the decision taken there: the target row, the fills executed at that boundary's open, and the book
held after them. Those are past-only and stable, which the tests demonstrate by ticking twice.

**The determinism check is the append invariance of :mod:`crypto_trade.cup20_desk.live_data`,
reused rather than restated.** Every tick replays rows it has already recorded; they must come back
bit-identical. :func:`crypto_trade.cup20_desk.live_data.append_frame` already compares a recorded
row against its refetch value by value and raises :class:`AppendInvarianceError` naming the key and
the column, so the ledgers below are appended through it under their own
:class:`~crypto_trade.cup20_desk.live_data.FrameSchema`. A changed value in an already-recorded
forward row is an append-invariance abort -- the market data was revised underneath the desk -- and
never a rounding difference to absorb.

**Phase.** The sealed holdout ended ``2026-08-01T00:00:00Z``. Boundaries from then until official
observation opens are an UNSCORED BRIDGE, and every persisted row says so. Official observation
begins at the first Monday ``00:00`` UTC strictly after the desk's FIRST successful tick, and that
instant is computed exactly once, written into ``integrity.json``, and read back from there on
every later tick. Deriving it fresh each tick would silently move it forward every week -- rows
already recorded as ``official`` would re-derive as ``bridge`` -- so the pinning is load-bearing
rather than an optimisation, and it is enforced twice: the value is read from disk when present,
and ``phase`` is a compared column of the forward ledger, so a drift in it aborts as a revision.

``is_start`` and the seam are pinned the same way and for the same reason: both decide which rows
exist and what they contain, and neither may move under a running desk.
"""

from __future__ import annotations

import dataclasses
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20.config import SEALED_END, load_config
from crypto_trade.cup20.harness import (
    load_candidate_risk_policy,
    load_team_module,
    strategy_from_module,
)
from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    evaluator_config,
    run_candidate,
)
from crypto_trade.cup20.snapshot import Snapshot, resolve_is_start
from crypto_trade.cup20.trials import ENTRYPOINT
from crypto_trade.cup20_desk.authority import (
    TOURNAMENT,
    WINNER_CANDIDATE_ID,
    WINNER_TEAM_ID,
    DeskAuthority,
    candidate_root,
    config_path,
    verify_desk_authority,
)
from crypto_trade.cup20_desk.live_data import (
    FrameSchema,
    _file_digest,
    _file_rows,
    append_frame,
    cache_manifest,
    conform_frame,
    empty_frame,
)
from crypto_trade.cup20_desk.snapshot_forward import CACHE_DIRNAME, build_forward_snapshot
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.snapshot import _utc as utc

SEAM = SEALED_END
"""The last instant the tournament scored. Everything the desk records begins here."""

BRIDGE = "bridge"
OFFICIAL = "official"
PHASES: tuple[str, str] = (BRIDGE, OFFICIAL)

MONDAY = 0
"""Weekday official observation opens on. A desk convention about when the six months start, and
deliberately NOT read from ``[universe].reconstitution_weekday`` -- the two are the same number
today by coincidence, and tying them together would make a universe-policy edit move the scored
window."""

DESK_SEED = 42
"""The seed the holdout observation was taken at (``scripts/cup20_holdout_observe.py --seed``)."""

COST_MULTIPLIER = 1
"""The desk observes the book at ordinary cost. Charging 2x and 3x as well would triple the wall
clock for numbers no forward record reads: ``run_candidate`` evaluates each multiplier
independently, and the common risk unit comes off the unscaled pass, so asking for one level
returns exactly the level-1 result the frozen list would have produced."""

SCHEMA_VERSION = "cup20-desk-tick-v1"

FILLS_CSV = "paper_fills.csv"
POSITIONS_CSV = "current_positions.csv"
FORWARD_CSV = "forward_returns.csv"
INTEGRITY_JSON = "integrity.json"
LATEST_JSON = "latest-boundary.json"
BOUNDARIES_DIRNAME = "boundaries"
LEDGER_DIRNAME = "ledger"
"""Where the append-invariant record lives. The three CSVs are RENDERINGS of these parquet
ledgers, rewritten from them on every tick: parquet preserves the float bit patterns and the
timestamp resolution a bit-identity claim depends on, and CSV is what a human and the healthcheck
read."""

_TIMESTAMP = "datetime64[ns, UTC]"

FILL_EVENT_TYPES: frozenset[str] = frozenset(
    {"trade", "risk_policy_action", "risk_reduction", "forced_exit", "conservative_settlement"}
)
"""The evaluator event types that move a quantity. ``funding``, ``mark_to_market`` and
``risk_policy_block`` are cashflows, valuations and refusals -- real, recorded in the return row,
and not fills."""

_EXECUTION_PHASE = "execution_phase"
"""The evaluator's own ``phase`` column, renamed on the way into ``paper_fills.csv``.

It carries ``rebalance`` / ``exposure_cap`` / ``delisting`` / ``terminal`` -- which stage of the
boundary produced the fill -- and would otherwise collide with the desk's ``bridge``/``official``
phase, which every persisted row is required to carry. The values are the evaluator's, untouched.
"""

_OPTIONAL_EVENT_COLUMNS = ("reason", "policy_id")
"""Columns ``EvaluationResult.events`` only has when a risk-policy event occurred somewhere in the
run. Filled with ``""`` when absent so the ledger's column set is stable across ticks."""


class DeskPinDriftError(RuntimeError):
    """Something the desk already committed to has moved.

    A pinned window (``official_start``, ``seam``, ``is_start``), or a boundary record whose replay
    no longer reproduces what was published for it. Both are the same failure in different clothes
    -- an already-published claim would have to be rewritten -- and both leave the recorded file
    exactly as it was.
    """


class TickWindowError(RuntimeError):
    """The requested boundary is not one this desk can evaluate."""


FORWARD_RETURN_SCHEMA = FrameSchema(
    name="forward_returns",
    # Exactly ``EvaluationResult.returns`` with its index named, plus the desk's phase. Declared
    # rather than inferred from the frame at hand: the columns are the frozen evaluator's output,
    # and the evaluator cannot change without ``evaluator_sha256`` changing, so a column set that
    # no longer matches means the authority check should already have refused the tick.
    columns=(
        "timestamp",
        "phase",
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
        "risk_policy_id",
        "risk_policy_turnover",
        "risk_policy_gross_scale",
        "risk_policy_drawdown",
        "risk_policy_annualized_volatility",
        "risk_policy_reasons",
    ),
    dtypes=(
        _TIMESTAMP,
        "str",
        *("float64",) * 24,
        "bool",
        *("float64",) * 2,
        "str",
        *("float64",) * 4,
        "str",
    ),
    key=("timestamp",),
    order=("timestamp",),
)

FILL_SCHEMA = FrameSchema(
    name="paper_fills",
    columns=(
        "timestamp",
        "symbol",
        "event_type",
        _EXECUTION_PHASE,
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
    ),
    dtypes=(
        _TIMESTAMP,
        "str",
        "str",
        "str",
        "str",
        *("float64",) * 7,
        "str",
        "str",
    ),
    key=("timestamp", "symbol", "event_type", _EXECUTION_PHASE),
    order=("timestamp", "symbol", "event_type", _EXECUTION_PHASE),
)

POSITION_SCHEMA = FrameSchema(
    name="current_positions",
    columns=("boundary", "symbol", "phase", "side", "weight"),
    dtypes=(_TIMESTAMP, "str", "str", "str", "float64"),
    key=("boundary", "symbol"),
    order=("boundary", "symbol"),
)


@dataclasses.dataclass(frozen=True, slots=True)
class DeskPins:
    """The three windows a desk commits to on its first successful tick and may never move."""

    official_start: pd.Timestamp
    seam: pd.Timestamp
    is_start: pd.Timestamp

    def to_dict(self) -> dict[str, str]:
        return {
            "official_start": self.official_start.isoformat(),
            "seam": self.seam.isoformat(),
            "is_start": self.is_start.isoformat(),
        }


@dataclasses.dataclass(frozen=True, slots=True)
class TickResult:
    """Everything one boundary produced, ready to persist. Nothing here was computed by the desk."""

    boundary: pd.Timestamp
    phase: str
    pins: DeskPins
    pinned: bool
    authority: DeskAuthority
    snapshot_manifest_sha256: str
    decisions: int
    rebalance: bool
    risk_scalar: float
    requested_weights: pd.Series
    executed_weights: pd.Series
    forward_returns: pd.DataFrame
    fills: pd.DataFrame
    positions: pd.DataFrame
    membership: tuple[str, ...]

    @property
    def official_start(self) -> pd.Timestamp:
        return self.pins.official_start


# ------------------------------------------------------------------------------------------------
# the phase boundary
# ------------------------------------------------------------------------------------------------


def first_official_boundary(after: object) -> pd.Timestamp:
    """First Monday ``00:00`` UTC strictly after ``after``.

    Strictly: a desk whose first tick lands exactly on a Monday midnight opens official observation
    the FOLLOWING Monday, so no boundary is ever both the first tick and the start of the scored
    window.
    """
    moment = utc(after)
    midnight = moment.normalize()
    candidate = midnight + pd.Timedelta(days=(MONDAY - midnight.weekday()) % 7)
    if candidate <= moment:
        candidate += pd.Timedelta(days=7)
    return candidate


def read_pins(desk_root: str | Path) -> DeskPins | None:
    """The windows this desk already committed to, or ``None`` before its first successful tick."""
    path = Path(desk_root) / INTEGRITY_JSON
    if not path.is_file():
        return None
    payload = json.loads(path.read_text())
    if not isinstance(payload, Mapping):
        raise DeskPinDriftError(f"{path} is not a JSON object")
    fields = tuple(field.name for field in dataclasses.fields(DeskPins))
    missing = [field for field in fields if field not in payload]
    if missing:
        raise DeskPinDriftError(
            f"{path} records no {', '.join(missing)}; the desk cannot tell which of its rows are "
            "scored, and recomputing would move the window it already published"
        )
    return DeskPins(**{field: utc(payload[field]) for field in fields})


def _require_pin(name: str, recorded: pd.Timestamp, current: pd.Timestamp) -> None:
    if recorded != current:
        raise DeskPinDriftError(
            f"{name} is pinned at {recorded} and this tick would use {current}; the desk's already "
            "published rows were produced under the pinned window, and no artifact was written"
        )


# ------------------------------------------------------------------------------------------------
# the tick
# ------------------------------------------------------------------------------------------------


def run_tick(
    boundary: object,
    *,
    desk_root: str | Path,
    authority: DeskAuthority,
    seam: object = SEAM,
    is_start: object | None = None,
    seed: int = DESK_SEED,
    repo: str | Path | None = None,
    config: str | Path | None = None,
    is_root: str | Path | None = None,
    sealed_root: str | Path | None = None,
    cache_root: str | Path | None = None,
) -> TickResult:
    """Replay the frozen winner through the tournament's evaluator and read the forward tail.

    ``authority`` is verified FIRST, before anything is read from the market or written anywhere:
    a desk running against a changed strategy, risk policy, config, selection freeze or evaluator
    is producing a record that is not comparable to the holdout result it follows, and the only
    safe thing it can do is refuse.

    ``is_start`` defaults to the tournament's own ``resolve_is_start`` over the assembled
    membership -- the same first-boundary-that-reaches-twenty rule ``scripts/cup20_evaluate.py``
    uses. It is a parameter only so a diagnostic can replay a shorter window; a desk that has
    already ticked refuses a different one, because the equity path, the risk unit and therefore
    every executed weight are functions of where the window starts.
    """
    moment = utc(boundary)
    verified = verify_desk_authority(authority, repo)

    raw = load_config(config or config_path(repo)).raw
    evaluator = evaluator_config(raw["execution"])
    interval = pd.Timedelta(hours=evaluator.interval_hours)
    if moment != moment.floor(interval):
        raise TickWindowError(
            f"{moment} is not on the {evaluator.interval_hours}h decision grid the tournament "
            "evaluates; a desk tick lands on a boundary or not at all"
        )

    root = Path(desk_root)
    pins = read_pins(root)
    seam_moment = utc(seam)
    snapshot = build_forward_snapshot(
        root,
        moment,
        cache_root=cache_root,
        is_root=is_root,
        sealed_root=sealed_root,
        config=config,
        repo=repo,
    )
    start = (
        utc(is_start)
        if is_start is not None
        else resolve_is_start(snapshot.membership, target_size=int(raw["universe"]["target_size"]))
    )
    current = DeskPins(
        official_start=pins.official_start if pins else first_official_boundary(moment),
        seam=seam_moment,
        is_start=start,
    )
    if pins is not None:
        _require_pin("seam", pins.seam, current.seam)
        _require_pin("is_start", pins.is_start, current.is_start)

    grid = decision_grid(start, moment + interval, interval_hours=evaluator.interval_hours)
    if not grid or grid[-1] != moment:
        raise TickWindowError(
            f"the decision grid from {start} does not reach {moment}; the desk cannot evaluate a "
            "boundary that is not on its own grid"
        )
    run = _replay(snapshot, grid, raw=raw, seed=seed, repo=repo)
    return _read_tail(
        run,
        boundary=moment,
        pins=current,
        pinned=pins is not None,
        snapshot=snapshot,
        authority=verified,
    )


def _replay(
    snapshot: Snapshot,
    grid: Sequence[pd.Timestamp],
    *,
    raw: Mapping[str, Any],
    seed: int,
    repo: str | Path | None,
) -> CandidateRun:
    """The frozen winner, through the organiser's own two-pass runner. The only evaluation path."""
    candidate = candidate_root(repo)
    strategy = strategy_from_module(load_team_module(candidate), entry=candidate / ENTRYPOINT)
    return run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=seed,
        config=evaluator_config(raw["execution"]),
        risk_unit=raw["risk_unit"],
        cost_multipliers=(COST_MULTIPLIER,),
        risk_policy=load_candidate_risk_policy(candidate),
    )


def _read_tail(
    run: CandidateRun,
    *,
    boundary: pd.Timestamp,
    pins: DeskPins,
    pinned: bool,
    snapshot: Snapshot,
    authority: DeskAuthority,
) -> TickResult:
    """Lift the forward rows off the evaluation. Reads and relabels; computes nothing."""
    result = run.results[COST_MULTIPLIER]
    if boundary not in result.returns.index or boundary not in result.positions.index:
        raise TickWindowError(f"the evaluation produced no row at {boundary}")
    targets = run.requested_targets.loc[boundary]
    executed = run.scaled_targets.loc[boundary]
    return TickResult(
        boundary=boundary,
        phase=_phase(boundary, pins.official_start),
        pins=pins,
        pinned=pinned,
        authority=authority,
        snapshot_manifest_sha256=snapshot.manifest_sha256,
        decisions=int(len(run.requested_targets.index)),
        rebalance=bool(targets[REBALANCE_INSTRUCTION_COLUMN]),
        risk_scalar=float(run.risk_scalars.loc[boundary]),
        requested_weights=_held(targets.drop(labels=[REBALANCE_INSTRUCTION_COLUMN])),
        executed_weights=_held(executed.drop(labels=[REBALANCE_INSTRUCTION_COLUMN])),
        forward_returns=_forward_returns(result.returns, boundary=boundary, pins=pins),
        fills=_fills(result.events, boundary=boundary, pins=pins),
        positions=_positions(result.positions.loc[boundary], boundary=boundary, pins=pins),
        membership=tuple(sorted(set(snapshot.membership["symbol"]))),
    )


def _phase(moment: pd.Timestamp, official_start: pd.Timestamp) -> str:
    return OFFICIAL if moment >= official_start else BRIDGE


def _held(weights: pd.Series) -> pd.Series:
    """The nonzero entries of one target row, in symbol order. A filter, not a computation."""
    values = weights.astype(float)
    return values.loc[values != 0.0].sort_index()


def _forward_returns(
    returns: pd.DataFrame, *, boundary: pd.Timestamp, pins: DeskPins
) -> pd.DataFrame:
    """Settled return rows from the seam onward, labelled with the phase each one falls in.

    ``< boundary`` drops the terminal row: it covers an interval that has only just opened and
    carries the window's own end-of-data force-exit, so it is neither settled nor stable. Every row
    kept is complete and, being past-only, identical on every later replay.
    """
    index = pd.DatetimeIndex(returns.index)
    tail = returns.loc[(index >= pins.seam) & (index < boundary)].copy()
    tail.index.name = "timestamp"
    frame = tail.reset_index()
    frame["phase"] = [_phase(moment, pins.official_start) for moment in frame["timestamp"]]
    return conform_frame(FORWARD_RETURN_SCHEMA, frame)


def _fills(events: pd.DataFrame, *, boundary: pd.Timestamp, pins: DeskPins) -> pd.DataFrame:
    """Quantity-moving events from the seam through the boundary, exactly as the evaluator wrote
    them.

    ``<= boundary`` keeps the fills executed AT this boundary -- they are decided from closed
    candles and filled at an open that has already printed -- while excluding the evaluator's
    terminal liquidation, which it stamps one interval past the last bar.
    """
    if events.empty:
        return empty_frame(FILL_SCHEMA)
    frame = events.rename(columns={"phase": _EXECUTION_PHASE})
    times = pd.DatetimeIndex(pd.to_datetime(frame["timestamp"], utc=True))
    keep = (
        (times >= pins.seam)
        & (times <= boundary)
        & frame["event_type"].isin(FILL_EVENT_TYPES).to_numpy()
    )
    frame = frame.loc[keep].copy()
    for column in _OPTIONAL_EVENT_COLUMNS:
        frame[column] = frame[column].fillna("") if column in frame else ""
    frame["phase"] = [_phase(utc(moment), pins.official_start) for moment in frame["timestamp"]]
    leaked = frame.loc[frame[_EXECUTION_PHASE] == "terminal"]
    if not leaked.empty:
        raise TickWindowError(
            f"{len(leaked)} end-of-window liquidation fills reached the forward record at "
            f"{boundary}; those are an artifact of where the replay stops, not decisions"
        )
    return conform_frame(FILL_SCHEMA, frame)


def _positions(weights: pd.Series, *, boundary: pd.Timestamp, pins: DeskPins) -> pd.DataFrame:
    """The book held after this boundary's execution, as the evaluator reported it.

    Weights only, and deliberately: a quantity would have to be accumulated from the fill stream,
    and accumulating a position size here is exactly the duplicated-execution defect this module
    refuses to contain. ``side`` reads the sign the evaluator already produced.
    """
    held = _held(weights)
    phase = _phase(boundary, pins.official_start)
    return conform_frame(
        POSITION_SCHEMA,
        pd.DataFrame(
            {
                "boundary": [boundary] * len(held),
                "symbol": list(held.index.astype(str)),
                "phase": [phase] * len(held),
                "side": ["LONG" if value > 0.0 else "SHORT" for value in held],
                "weight": list(held),
            }
        ),
    )


# ------------------------------------------------------------------------------------------------
# persistence
# ------------------------------------------------------------------------------------------------


def persist_tick(result: TickResult, desk_root: str | Path) -> dict[str, Path]:
    """Append the tick to the ledgers, re-render the CSVs, and bind everything in integrity.json.

    The ledger appends run first and through
    :func:`crypto_trade.cup20_desk.live_data.append_frame`, so the determinism check happens before
    any artifact of this tick is rewritten: a forward row that came back different aborts with the
    key and the column named, and the previously published files are left exactly as they were.
    """
    root = Path(desk_root)
    ledger = root / LEDGER_DIRNAME
    forward_ledger = ledger / f"{FORWARD_RETURN_SCHEMA.name}.parquet"
    fills_ledger = ledger / f"{FILL_SCHEMA.name}.parquet"
    appended = {
        FORWARD_RETURN_SCHEMA.name: append_frame(
            forward_ledger, result.forward_returns, name=FORWARD_RETURN_SCHEMA
        ),
        FILL_SCHEMA.name: append_frame(fills_ledger, result.fills, name=FILL_SCHEMA),
    }

    forward = conform_frame(FORWARD_RETURN_SCHEMA, pd.read_parquet(forward_ledger))
    fills = conform_frame(FILL_SCHEMA, pd.read_parquet(fills_ledger))
    written = {
        "forward_returns": _write_csv(forward, root / FORWARD_CSV),
        "paper_fills": _write_csv(fills, root / FILLS_CSV),
        "current_positions": _write_csv(result.positions, root / POSITIONS_CSV),
    }

    payload = _boundary_payload(result)
    records = root / BOUNDARIES_DIRNAME
    written["boundary"] = _write_boundary_record(records, result.boundary, payload)
    written["latest"] = _write_json(payload, root / LATEST_JSON)

    integrity = _integrity(
        result,
        root=root,
        published=forward,
        fills=fills,
        appended=appended,
        artifacts=written,
        # Suffixed, because the CSVs are already bound under the bare frame names and a plain
        # `{**artifacts, **ledgers}` merge silently REPLACED them: the record's two most important
        # files were bound and the two renderings were not, which is exactly backwards from what a
        # reader of `artifacts` would assume. Both are bound now, under distinct names.
        ledgers={
            f"{FORWARD_RETURN_SCHEMA.name}_ledger": forward_ledger,
            f"{FILL_SCHEMA.name}_ledger": fills_ledger,
        },
    )
    written["integrity"] = _write_json(integrity, root / INTEGRITY_JSON)
    written["forward_ledger"] = forward_ledger
    written["fills_ledger"] = fills_ledger
    return written


def _boundary_payload(result: TickResult) -> dict[str, Any]:
    """The immutable record of one boundary's decision. Every number is the evaluator's."""
    return {
        "schema_version": SCHEMA_VERSION,
        "tournament": TOURNAMENT,
        "team_id": WINNER_TEAM_ID,
        "candidate_id": WINNER_CANDIDATE_ID,
        "paper_only": True,
        "boundary": result.boundary.isoformat(),
        "phase": result.phase,
        "official_start": result.pins.official_start.isoformat(),
        "seam": result.pins.seam.isoformat(),
        "is_start": result.pins.is_start.isoformat(),
        "decisions": result.decisions,
        "rebalance": result.rebalance,
        "risk_scalar": result.risk_scalar,
        "requested_weights": {
            str(symbol): float(value) for symbol, value in result.requested_weights.items()
        },
        "executed_weights": {
            str(symbol): float(value) for symbol, value in result.executed_weights.items()
        },
        "positions": _records(result.positions),
        # This boundary's own fills. The ledger carries the history; a boundary record that
        # repeated it would grow without bound and stop being the record of one decision.
        "fills": _records(result.fills.loc[result.fills["timestamp"] == result.boundary]),
        "snapshot_manifest_sha256": result.snapshot_manifest_sha256,
        "membership": list(result.membership),
    }


def _integrity(
    result: TickResult,
    *,
    root: Path,
    published: pd.DataFrame,
    fills: pd.DataFrame,
    appended: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    ledgers: Mapping[str, Path],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "tournament": TOURNAMENT,
        "team_id": WINNER_TEAM_ID,
        "candidate_id": WINNER_CANDIDATE_ID,
        "paper_only": True,
        "boundary": result.boundary.isoformat(),
        "phase": result.phase,
        "official_start_pinned": result.pinned,
        "append_invariance": "PASS",
        "determinism": "PASS",
        "evaluation_path": "crypto_trade.cup20.runner.run_candidate",
        "terminal_return_discarded": True,
        "decisions": result.decisions,
        "snapshot_manifest_sha256": result.snapshot_manifest_sha256,
        "forward_rows": int(len(published)),
        "official_rows": int((published["phase"] == OFFICIAL).sum()),
        "bridge_rows": int((published["phase"] == BRIDGE).sum()),
        "fill_rows": int(len(fills)),
        "appended": {
            name: {"appended": item.appended, "unchanged": item.unchanged, "total": item.total}
            for name, item in appended.items()
        },
        "members": len(result.membership),
    }
    payload.update(result.pins.to_dict())
    payload.update(result.authority.to_dict())
    payload["artifacts"] = {
        name: _binding(path, root) for name, path in sorted({**artifacts, **ledgers}.items())
    }
    cache = root / CACHE_DIRNAME
    payload["cache"] = cache_manifest(cache) if cache.is_dir() else None
    return payload


def _binding(path: Path, root: Path) -> dict[str, Any]:
    """Bind one artifact by path, size, rows and SHA-256, exactly as the cache manifest does."""
    return {
        "path": path.relative_to(root).as_posix(),
        "size": path.stat().st_size,
        "rows": _file_rows(path) if path.suffix != ".csv" else _csv_rows(path),
        "sha256": _file_digest(path),
    }


def _csv_rows(path: Path) -> int:
    return max(sum(1 for line in path.read_text().splitlines() if line.strip()) - 1, 0)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {column: _scalar(row[column]) for column in frame.columns} for _, row in frame.iterrows()
    ]


def _scalar(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _write_csv(frame: pd.DataFrame, path: Path) -> Path:
    _atomic(path, frame.to_csv(index=False))
    return path


def _write_json(payload: object, path: Path) -> Path:
    _atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _write_boundary_record(directory: Path, boundary: pd.Timestamp, payload: object) -> Path:
    """Write one boundary's record once. A replay that disagrees with it aborts.

    Every input to the record is past-only at the boundary, so re-ticking the same boundary must
    reproduce it byte for byte. A difference means the market data underneath moved, which is the
    same abort the ledgers raise -- caught here for the boundaries whose rows the ledgers do not
    carry (the decision AT the terminal boundary, whose return row is deliberately discarded).
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{boundary.strftime('%Y%m%dT%H%M%SZ')}.json"
    canonical = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.is_file():
        recorded = path.read_text()
        if recorded != canonical:
            raise DeskPinDriftError(
                f"APPEND-INVARIANCE ABORT: {path} already records a different decision for "
                f"{boundary}; the recorded file was left untouched"
            )
        return path
    _atomic(path, canonical)
    return path


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text)
    os.replace(temporary, path)
