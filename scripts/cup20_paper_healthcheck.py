#!/usr/bin/env python3
"""Read-only integrity and liveness check for the CUP-20 winner's paper desk.

Operational, not observational: everything here is a question with a yes/no answer about whether
the record can still be trusted. Forward PnL is not one of them -- that is the experiment's result
and lives in ``scripts/cup20_paper_digest.py``. Nothing in this script writes to the desk.

**Every artifact is bound by path, size, row count and SHA-256, and so is every cache file.** The
bindings come from the tick's own ``integrity.json``, which is the record of what the desk actually
published; recomputing them here and comparing is what makes a later edit to a published file
visible. Two things are bound rather than one, and the distinction is load-bearing (operational
fact 6): ``ledger/*.parquet`` is the append-invariant RECORD, and the CSVs are RENDERINGS of it,
rewritten from the ledgers on every tick. So the ledgers are bound, the CSVs are bound, and -- the
part a binding alone cannot give -- the CSVs are re-rendered from the ledgers here and compared. A
desk that rendered its CSV from something other than its ledger would bind the wrong bytes
perfectly; only the cross-check catches that.

``desk/snapshot/`` is deliberately not checked. It is a work product reassembled on every tick and
legitimately grows with the window (fact 7); the ledgers, the CSVs, ``boundaries/``,
``latest-boundary.json`` and ``integrity.json`` are the record.

Prints ``STATUS OK`` or ``STATUS ALERT`` followed by one line per finding, each opening with a
named failure class from :data:`FAILURE_CLASSES`. Exits non-zero on any alert.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# `run_cup20_paper` is a repository-root module, imported for the freshness rule: a second copy
# of "which boundary should have been published by now" would drift from the one the engine
# actually uses, and the healthcheck would then alert on boundaries the runner was right to skip.
import run_cup20_paper as runner  # noqa: E402

from crypto_trade.cup20.config import SEALED_END  # noqa: E402
from crypto_trade.cup20_desk.authority import (  # noqa: E402
    AUTHORITY_FIELDS,
    current_desk_authority,
)
from crypto_trade.cup20_desk.live_data import (  # noqa: E402
    CacheDriftError,
    conform_frame,
    verify_cache_manifest,
)
from crypto_trade.cup20_desk.snapshot_forward import CACHE_DIRNAME  # noqa: E402
from crypto_trade.cup20_desk.tick import (  # noqa: E402
    BOUNDARIES_DIRNAME,
    BRIDGE,
    FILL_SCHEMA,
    FORWARD_RETURN_SCHEMA,
    LEDGER_DIRNAME,
    OFFICIAL,
)

ENGINE_DOWN = "ENGINE DOWN"
ENGINE_IDENTITY = "ENGINE IDENTITY BAD"
AUTHORITY_DRIFT = "AUTHORITY DRIFT"
PIN_DRIFT = "PIN DRIFT"
APPEND_INVARIANCE_ABORT = "APPEND-INVARIANCE ABORT"
CACHE_DRIFT = "CACHE DRIFT"
STALE_BOUNDARY = "STALE BOUNDARY"
LEDGER_CSV_MISMATCH = "LEDGER/CSV MISMATCH"
ARTIFACT_DRIFT = "ARTIFACT DRIFT"
ARTIFACTS_MISSING = "ARTIFACTS MISSING"
TICK_FAILED = "LATEST TICK FAILED"
TICK_HUNG = "TICK HUNG"
HEALTHCHECK_ERROR = "HEALTHCHECK ERROR"

FAILURE_CLASSES: tuple[str, ...] = (
    ENGINE_DOWN,
    ENGINE_IDENTITY,
    AUTHORITY_DRIFT,
    PIN_DRIFT,
    APPEND_INVARIANCE_ABORT,
    CACHE_DRIFT,
    STALE_BOUNDARY,
    LEDGER_CSV_MISMATCH,
    ARTIFACT_DRIFT,
    ARTIFACTS_MISSING,
    TICK_FAILED,
    TICK_HUNG,
    HEALTHCHECK_ERROR,
)

STALE_GRACE = pd.Timedelta(minutes=75)
"""Allowed on top of the runner's publication lag before a missing boundary is an alert. One tick
is a full-window replay measured at ~410 s, and the wide-cross-section fetch that precedes it adds
minutes more; the grace is what separates "the engine is working on it" from "the engine is gone".
"""

HUNG_AFTER = pd.Timedelta(minutes=90)
"""How long a RUNNING attempt may stand before it is reported as hung rather than in progress."""

BOUNDARY_ARTIFACTS: tuple[str, ...] = (
    "boundary",
    "current_positions",
    "forward_returns",
    "latest",
    "paper_fills",
)
LEDGER_ARTIFACTS: tuple[str, ...] = ("forward_returns_ledger", "paper_fills_ledger")

LEDGERS: Mapping[str, Any] = {
    "forward_returns": FORWARD_RETURN_SCHEMA,
    "paper_fills": FILL_SCHEMA,
}
"""The renderings, paired with the ledger schema each one must render."""

MONDAY = 0


@dataclasses.dataclass(frozen=True, slots=True)
class Report:
    """What the desk looks like right now: named failures first, then what was verified."""

    desk_root: Path
    alerts: tuple[str, ...]
    notes: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.alerts

    def render(self) -> str:
        lines = [
            f"STATUS {'OK' if self.ok else 'ALERT'} - CUP-20 winner exact-replay paper desk "
            f"({self.desk_root})"
        ]
        lines.extend(f"  ALERT: {alert}" for alert in self.alerts)
        lines.extend(f"  {note}" for note in self.notes)
        return "\n".join(lines)


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> int:
    """Row count the same way the tick's own binding counts it, per format."""
    if path.suffix == ".parquet":
        return int(len(pd.read_parquet(path)))
    if path.suffix == ".csv":
        return max(len([line for line in path.read_text().splitlines() if line.strip()]) - 1, 0)
    payload = json.loads(path.read_text())
    return len(payload) if isinstance(payload, list | Mapping) else 1


def _safe_relative(root: Path, relative: object) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError(f"artifact binding has an unsafe path: {relative!r}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"artifact binding escapes the desk: {relative!r}")
    return path


class _Findings:
    """An ordered alert/note collector, so every check can report without early-returning."""

    def __init__(self) -> None:
        self.alerts: list[str] = []
        self.notes: list[str] = []

    def alert(self, failure_class: str, detail: str) -> None:
        self.alerts.append(f"{failure_class}: {detail}")

    def note(self, detail: str) -> None:
        self.notes.append(detail)


# ------------------------------------------------------------------------------------------------
# the checks
# ------------------------------------------------------------------------------------------------


def check_desk(
    desk_root: str | Path,
    *,
    now: object | None = None,
    check_process: bool = True,
    lag_seconds: int = runner.DEFAULT_LAG_SECONDS,
    seam: object | None = None,
    repo: str | Path | None = None,
) -> Report:
    """Every operational check, in one read-only pass. Never raises; it reports.

    ``seam`` defaults to the tournament's own ``SEALED_END`` and is a parameter only so a
    diagnostic can check a desk built on a different recorded window.
    """
    root = Path(desk_root).resolve()
    moment = _utc(now) if now is not None else pd.Timestamp.now(tz="UTC")
    found = _Findings()

    if check_process:
        _check_engine(root, found)
    attempt = _check_attempt(root, moment, found)

    integrity_path = root / "integrity.json"
    if not integrity_path.is_file():
        found.alert(
            ARTIFACTS_MISSING, f"{integrity_path} does not exist; the desk has never ticked"
        )
        return Report(desk_root=root, alerts=tuple(found.alerts), notes=tuple(found.notes))

    try:
        integrity = json.loads(integrity_path.read_text())
        if not isinstance(integrity, Mapping):
            raise ValueError("integrity.json is not a JSON object")
    except Exception as exc:  # noqa: BLE001 - a healthcheck must never take the desk down
        found.alert(HEALTHCHECK_ERROR, f"integrity.json is unreadable: {type(exc).__name__}: {exc}")
        return Report(desk_root=root, alerts=tuple(found.alerts), notes=tuple(found.notes))

    # Each check is guarded on its own. One that raises is itself a finding, and the ones after it
    # still run: an operator reading this needs every problem the desk has, not the first one.
    _guard(found, lambda: _check_status(integrity, found))
    paths = _guard(found, lambda: _check_bindings(root, integrity, found)) or {}
    _guard(found, lambda: _check_ledgers(root, integrity, found))
    _guard(found, lambda: _check_renderings(root, paths, found))
    _guard(
        found,
        lambda: _check_pins(root, integrity, _utc(seam if seam is not None else SEALED_END), found),
    )
    _guard(found, lambda: _check_authority(integrity, repo, found))
    _guard(found, lambda: _check_cache(root, integrity, attempt, found))
    _guard(found, lambda: _check_freshness(integrity, moment, lag_seconds, found))
    return Report(desk_root=root, alerts=tuple(found.alerts), notes=tuple(found.notes))


def _guard(found: _Findings, check):
    """Run one check. A check that raises becomes a named finding rather than an exit."""
    try:
        return check()
    except Exception as exc:  # noqa: BLE001 - a healthcheck must never take the desk down
        found.alert(HEALTHCHECK_ERROR, f"{type(exc).__name__}: {exc}")
        return None


def _check_engine(root: Path, found: _Findings) -> None:
    """A held ``flock`` is the authoritative liveness signal; a lock file alone is not.

    ``flock`` lives on an open file description and the kernel releases it when the holder dies, so
    a lock file nobody holds means the engine is gone -- and the pid written inside it is stale and
    must never be believed on its own.
    """
    path = root / runner.ENGINE_LOCK
    if not path.is_file():
        found.alert(ENGINE_DOWN, f"{path} is missing; no engine has ever held this desk")
        return
    with path.open("r+", encoding="utf-8") as handle:
        try:
            runner.fcntl.flock(handle.fileno(), runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)
        except BlockingIOError:
            held = True
        else:
            held = False
            runner.fcntl.flock(handle.fileno(), runner.fcntl.LOCK_UN)
        raw = handle.read().strip()
    if not held:
        found.alert(ENGINE_DOWN, f"{path} exists but nobody holds it; the engine is not running")
        return
    try:
        pid = int(raw)
        command = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        working = (Path("/proc") / str(pid) / "cwd").resolve()
    except (OSError, ValueError) as exc:
        found.alert(ENGINE_IDENTITY, f"the lock holder cannot be identified: {exc}")
        return
    if "run_cup20_paper.py" not in command or working != ROOT:
        found.alert(
            ENGINE_IDENTITY, f"pid={pid} cwd={working} cmd={command[:120]!r} is not this desk"
        )
        return
    found.note(f"engine alive: pid={pid} worktree={working}")


def _check_attempt(root: Path, now: pd.Timestamp, found: _Findings) -> Mapping[str, Any] | None:
    path = root / runner.ATTEMPT_JSON
    if not path.is_file():
        return None
    try:
        attempt = json.loads(path.read_text())
        if not isinstance(attempt, Mapping):
            raise ValueError("attempt.json is not a JSON object")
        status = attempt.get("status")
        if status not in {"RUNNING", "PASS", "FAIL"}:
            raise ValueError(f"attempt status is invalid: {status!r}")
        if status == "FAIL":
            found.alert(TICK_FAILED, f"{attempt.get('boundary')}: {attempt.get('error')}")
        elif status == "RUNNING":
            age = now - _utc(attempt["started_at"])
            if age > HUNG_AFTER:
                found.alert(TICK_HUNG, f"{attempt.get('boundary')} has been running for {age}")
            else:
                found.note(f"tick in progress: boundary={attempt.get('boundary')} age={age}")
        return attempt
    except Exception as exc:  # noqa: BLE001
        found.alert(HEALTHCHECK_ERROR, f"attempt marker is unreadable: {exc}")
        return None


def _check_status(integrity: Mapping[str, Any], found: _Findings) -> None:
    if integrity.get("status") != "PASS":
        found.alert(ARTIFACT_DRIFT, f"integrity status is {integrity.get('status')!r}, not PASS")
    if integrity.get("paper_only") is not True:
        found.alert(ARTIFACT_DRIFT, "the desk no longer declares itself paper-only")
    if integrity.get("append_invariance") != "PASS":
        found.alert(APPEND_INVARIANCE_ABORT, "the last tick did not record append invariance PASS")
    if integrity.get("determinism") != "PASS":
        found.alert(APPEND_INVARIANCE_ABORT, "the last tick did not record determinism PASS")
    found.note(
        f"members at the last boundary: {integrity.get('members')} "
        f"(snapshot manifest {str(integrity.get('snapshot_manifest_sha256'))[:16]})"
    )


def _check_bindings(root: Path, integrity: Mapping[str, Any], found: _Findings) -> dict[str, Path]:
    """Bind every published artifact by path, size, row count and SHA-256.

    A drifted ledger is reported as an append-invariance abort rather than as artifact drift: the
    ledgers are the append-only record, and a record whose recorded bytes changed is the failure
    the whole desk is built to make loud.
    """
    bindings = integrity.get("artifacts")
    if not isinstance(bindings, Mapping):
        raise ValueError("integrity.json binds no artifacts")
    expected = set(BOUNDARY_ARTIFACTS) | set(LEDGER_ARTIFACTS)
    if set(bindings) != expected:
        found.alert(
            ARTIFACT_DRIFT,
            f"the bound artifact set is {sorted(bindings)}, expected {sorted(expected)}",
        )
    paths: dict[str, Path] = {}
    for label in sorted(set(bindings) & expected):
        binding = bindings[label]
        failure = APPEND_INVARIANCE_ABORT if label in LEDGER_ARTIFACTS else ARTIFACT_DRIFT
        if not isinstance(binding, Mapping):
            found.alert(ARTIFACT_DRIFT, f"{label} binding is malformed")
            continue
        path = _safe_relative(root, binding.get("path"))
        if not path.is_file():
            found.alert(failure, f"bound artifact is missing: {binding.get('path')}")
            continue
        paths[label] = path
        size = path.stat().st_size
        if size != binding.get("size"):
            found.alert(
                failure,
                f"{binding['path']} is {size} bytes, integrity binds {binding.get('size')}",
            )
        rows = _rows(path)
        if rows != binding.get("rows"):
            found.alert(
                failure,
                f"{binding['path']} holds {rows} rows, integrity binds {binding.get('rows')}",
            )
        if _digest(path) != binding.get("sha256"):
            found.alert(failure, f"{binding['path']} does not match its bound SHA-256")
    found.note(f"artifacts bound and verified: {len(paths)}")
    return paths


def _check_ledgers(root: Path, integrity: Mapping[str, Any], found: _Findings) -> None:
    """The append-only record: readable in its declared schema, unique and ordered on its key."""
    for name, schema in LEDGERS.items():
        path = root / LEDGER_DIRNAME / f"{name}.parquet"
        if not path.is_file():
            found.alert(APPEND_INVARIANCE_ABORT, f"the {name} ledger is missing: {path}")
            continue
        frame = conform_frame(schema, pd.read_parquet(path))
        key = list(schema.key)
        if frame.duplicated(key).any():
            found.alert(APPEND_INVARIANCE_ABORT, f"the {name} ledger holds duplicate {schema.key}")
        ordered = frame.sort_values(list(schema.order), kind="stable").reset_index(drop=True)
        if not ordered.equals(frame):
            found.alert(
                APPEND_INVARIANCE_ABORT, f"the {name} ledger is not in {schema.order} order"
            )
    forward = conform_frame(
        FORWARD_RETURN_SCHEMA, pd.read_parquet(root / LEDGER_DIRNAME / "forward_returns.parquet")
    )
    for label, expected in (
        ("forward_rows", len(forward)),
        ("official_rows", int((forward["phase"] == OFFICIAL).sum())),
        ("bridge_rows", int((forward["phase"] == BRIDGE).sum())),
    ):
        if integrity.get(label) != expected:
            found.alert(
                APPEND_INVARIANCE_ABORT,
                f"integrity records {label}={integrity.get(label)}, the ledger holds {expected}",
            )
    found.note(
        f"forward ledger: {len(forward)} rows "
        f"({int((forward['phase'] == OFFICIAL).sum())} official, "
        f"{int((forward['phase'] == BRIDGE).sum())} bridge)"
    )


def _check_renderings(root: Path, paths: Mapping[str, Path], found: _Findings) -> None:
    """Re-render each CSV from its ledger and require the published file to be exactly that.

    This is the only check that can catch a CSV that is internally consistent -- bound correctly,
    the right size, the right row count -- and simply not what the ledger says. The rendering is
    the tick's own (``conform_frame`` then ``DataFrame.to_csv(index=False)``), so agreement is
    byte-for-byte rather than approximate.
    """
    for name, schema in LEDGERS.items():
        ledger = root / LEDGER_DIRNAME / f"{name}.parquet"
        rendering = paths.get(name)
        if rendering is None or not ledger.is_file():
            continue
        expected = conform_frame(schema, pd.read_parquet(ledger)).to_csv(index=False)
        if rendering.read_text() != expected:
            found.alert(
                LEDGER_CSV_MISMATCH,
                f"{rendering.name} is not a faithful rendering of {ledger.name}; the ledger is the "
                "record and the CSV disagrees with it",
            )
    _check_positions(root, paths, found)


def _check_positions(root: Path, paths: Mapping[str, Path], found: _Findings) -> None:
    """``current_positions.csv`` has no ledger; its record is the boundary's own immutable file."""
    published = paths.get("current_positions")
    latest = paths.get("latest")
    if published is None or latest is None:
        return
    payload = json.loads(latest.read_text())
    recorded = [
        (
            _utc(row["boundary"]).isoformat(),
            str(row["symbol"]),
            str(row["phase"]),
            str(row["side"]),
            float(row["weight"]),
        )
        for row in payload.get("positions", [])
    ]
    frame = pd.read_csv(published, float_precision="round_trip")
    rendered = [
        (
            _utc(row.boundary).isoformat(),
            str(row.symbol),
            str(row.phase),
            str(row.side),
            float(row.weight),
        )
        for row in frame.itertuples()
    ]
    if rendered != recorded:
        found.alert(
            LEDGER_CSV_MISMATCH,
            f"{published.name} disagrees with the positions recorded in {latest.name}",
        )


def _check_pins(
    root: Path, integrity: Mapping[str, Any], seam: pd.Timestamp, found: _Findings
) -> None:
    """``official_start``, ``seam`` and ``is_start`` may never move once the desk has published.

    They decide which rows exist and what phase they carry, so they are checked from three
    independent directions: against the tournament's own sealed end, against every boundary record
    the desk has ever written, and against the phase label on every forward row.
    """
    fields = ("official_start", "seam", "is_start")
    missing = [field for field in fields if field not in integrity]
    if missing:
        found.alert(PIN_DRIFT, f"integrity.json records no {', '.join(missing)}")
        return
    pins = {field: _utc(integrity[field]) for field in fields}
    if pins["seam"] != seam:
        found.alert(
            PIN_DRIFT,
            f"seam is pinned at {pins['seam'].isoformat()}, but the tournament sealed at "
            f"{seam.isoformat()}",
        )
    if pins["official_start"].weekday() != MONDAY or pins["official_start"] != (
        pins["official_start"].normalize()
    ):
        found.alert(
            PIN_DRIFT,
            f"official_start {pins['official_start'].isoformat()} is not a Monday 00:00 UTC",
        )
    if pins["is_start"] >= pins["seam"]:
        found.alert(PIN_DRIFT, "is_start is not before the seam")

    records = sorted((root / BOUNDARIES_DIRNAME).glob("*.json"))
    for record in records:
        payload = json.loads(record.read_text())
        for field in fields:
            if _utc(payload[field]) != pins[field]:
                found.alert(
                    PIN_DRIFT,
                    f"{record.name} was published with {field}={payload[field]}, integrity now "
                    f"pins {pins[field].isoformat()}",
                )
    forward = conform_frame(
        FORWARD_RETURN_SCHEMA, pd.read_parquet(root / LEDGER_DIRNAME / "forward_returns.parquet")
    )
    if not forward.empty:
        if forward["timestamp"].min() < pins["seam"]:
            found.alert(PIN_DRIFT, "the forward ledger holds a row before the pinned seam")
        expected = (
            forward["timestamp"].ge(pins["official_start"]).map({True: OFFICIAL, False: BRIDGE})
        )
        disagree = forward.loc[forward["phase"].to_numpy() != expected.to_numpy()]
        if not disagree.empty:
            found.alert(
                PIN_DRIFT,
                f"{len(disagree)} forward rows carry a phase the pinned official_start "
                f"{pins['official_start'].isoformat()} does not produce, e.g. "
                f"{disagree.iloc[0]['timestamp']}",
            )
    found.note(
        f"pins: is_start={pins['is_start'].isoformat()} seam={pins['seam'].isoformat()} "
        f"official_start={pins['official_start'].isoformat()} "
        f"({len(records)} boundary records agree)"
    )


def _check_authority(
    integrity: Mapping[str, Any], repo: str | Path | None, found: _Findings
) -> None:
    authority = current_desk_authority(repo)
    for field in AUTHORITY_FIELDS:
        recorded = integrity.get(field)
        actual = getattr(authority, field)
        if recorded != actual:
            found.alert(
                AUTHORITY_DRIFT,
                f"{field} is {actual} on disk, the desk published {recorded!r}",
            )
    found.note("deployment authority: strategy, risk policy, config, freeze and evaluator agree")


def _check_cache(
    root: Path,
    integrity: Mapping[str, Any],
    attempt: Mapping[str, Any] | None,
    found: _Findings,
) -> None:
    """The cache manifest bound by the last successful tick, re-verified file by file.

    A cache that has GROWN since that tick is not drift: the runner refreshes before it replays, so
    a tick that is running now -- or one that failed after refreshing -- legitimately leaves more
    rows on disk than the last published binding names. That case is checked for shrinkage and
    reported as a note. Anything else is drift.
    """
    manifest = integrity.get("cache")
    cache = root / CACHE_DIRNAME
    if manifest is None:
        if cache.is_dir() and any(cache.iterdir()):
            found.alert(CACHE_DRIFT, "the desk holds a cache its integrity record does not bind")
        return
    try:
        verify_cache_manifest(cache, manifest)
    except CacheDriftError as exc:
        if _cache_may_be_ahead(integrity, attempt):
            shrunk = _cache_shrank(cache, manifest)
            if shrunk:
                found.alert(CACHE_DRIFT, f"bound cache rows disappeared: {shrunk}")
            else:
                found.note("cache is ahead of the last published binding (a tick is in flight)")
        else:
            found.alert(CACHE_DRIFT, str(exc))
        return
    found.note(f"cache manifest: {len(manifest.get('files', []))} files verified")


def _cache_may_be_ahead(integrity: Mapping[str, Any], attempt: Mapping[str, Any] | None) -> bool:
    if attempt is None:
        return False
    if attempt.get("status") == "RUNNING":
        return True
    return attempt.get("status") == "FAIL" and attempt.get("boundary") != integrity.get("boundary")


def _cache_shrank(cache: Path, manifest: Mapping[str, Any]) -> list[str]:
    lost: list[str] = []
    for entry in manifest.get("files", []):
        if not isinstance(entry, Mapping):
            continue
        path = cache / str(entry.get("path"))
        if not path.is_file():
            lost.append(f"{entry.get('path')} is missing")
            continue
        bound = entry.get("rows")
        if isinstance(bound, int) and _rows(path) < bound:
            lost.append(f"{entry.get('path')} fell from {bound} rows")
    return lost


def _check_freshness(
    integrity: Mapping[str, Any], now: pd.Timestamp, lag_seconds: int, found: _Findings
) -> None:
    boundary = _utc(integrity["boundary"])
    due = runner.ready_boundary(now - STALE_GRACE, lag_seconds)
    if boundary < due:
        found.alert(
            STALE_BOUNDARY,
            f"the newest published boundary is {boundary.isoformat()}, but {due.isoformat()} has "
            f"been ready for longer than the {STALE_GRACE} grace",
        )
    found.note(
        f"latest published boundary: {boundary.isoformat()} (phase {integrity.get('phase')})"
    )


# ------------------------------------------------------------------------------------------------
# entry point
# ------------------------------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CUP-20 winner paper-desk healthcheck")
    parser.add_argument("--desk-dir", type=Path, default=ROOT / runner.DEFAULT_DESK_DIR)
    parser.add_argument("--now", help="evaluate freshness against this UTC instant")
    parser.add_argument(
        "--skip-process",
        action="store_true",
        help="omit the liveness check, for artifact-only validation",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = check_desk(
        args.desk_dir,
        now=args.now,
        check_process=not args.skip_process,
    )
    print(report.render(), flush=True)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
