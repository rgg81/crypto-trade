#!/usr/bin/env python3
"""Read-only integrity and liveness check for the Team 09 paper desk."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.team09.authority import (
    sha256_file,
    verify_frozen_authority,
)
from crypto_trade.team09.backtest import LIVE_FORWARD_START
from crypto_trade.team09.live import _gate_frame
from crypto_trade.team09.live_data import (
    BRIDGE_START,
    _load_archive_provenance,
    current_boundary,
    verify_live_cache_manifest,
)
from crypto_trade.tournament.pure_crypto_universe_v6 import symbol_policy_violations

ROOT = Path(__file__).resolve().parents[1]
INTERVAL = pd.Timedelta(hours=8)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Team 09 paper-desk healthcheck")
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=ROOT / "paper-team09",
    )
    parser.add_argument(
        "--skip-process",
        action="store_true",
        help="omit process liveness (useful for artifact-only validation)",
    )
    return parser.parse_args()


def _canonical_sha256(payload: object) -> str:
    raw = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )


def _artifact_rows(path: Path) -> int:
    if path.suffix == ".parquet":
        return len(pd.read_parquet(path))
    if path.suffix == ".csv":
        return len(pd.read_csv(path))
    if path.name == "runs.log":
        return len(path.read_text(encoding="utf-8").splitlines())
    return 1


def _verify_artifact_bindings(
    paper: Path,
    integrity: Mapping[str, object],
) -> dict[str, Path]:
    bindings = integrity.get("artifacts")
    if not isinstance(bindings, Mapping):
        raise ValueError("integrity artifact bindings are missing")
    expected = {
        "bridge_returns",
        "forward_returns",
        "positions",
        "fills",
        "gates",
        "decision",
        "latest",
        "runs",
        "cache_manifest",
    }
    if set(bindings) != expected:
        raise ValueError(
            f"integrity artifact binding names differ: {sorted(set(bindings))}"
        )
    paths: dict[str, Path] = {}
    for label in sorted(expected):
        binding = bindings[label]
        if not isinstance(binding, Mapping):
            raise ValueError(f"artifact binding {label} is malformed")
        relative = binding.get("path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise ValueError(f"artifact binding {label} has an unsafe path")
        path = (paper / relative).resolve()
        if not path.is_relative_to(paper) or not path.is_file():
            raise FileNotFoundError(f"bound artifact is missing: {relative}")
        if path.stat().st_size != binding.get("size"):
            raise RuntimeError(f"bound artifact size drift: {relative}")
        if sha256_file(path) != binding.get("sha256"):
            raise RuntimeError(f"bound artifact hash drift: {relative}")
        if _artifact_rows(path) != binding.get("rows"):
            raise RuntimeError(f"bound artifact row-count drift: {relative}")
        paths[label] = path
    return paths


def _check_process(paper: Path, alerts: list[str], notes: list[str]) -> None:
    lock_path = paper / "engine.lock"
    if not lock_path.is_file():
        alerts.append("ENGINE DOWN: engine.lock is missing")
        return
    with lock_path.open("r+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            locked = True
        else:
            locked = False
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        raw_pid = handle.read().strip()
    if not locked:
        alerts.append("ENGINE DOWN: paper-desk lock is not held")
        return
    try:
        pid = int(raw_pid)
        cmdline = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode()
        cwd = (Path("/proc") / str(pid) / "cwd").resolve()
    except (OSError, ValueError) as exc:
        alerts.append(f"ENGINE IDENTITY BAD: {exc}")
        return
    if "run_team09_paper.py" not in cmdline or cwd != ROOT:
        alerts.append(
            f"ENGINE IDENTITY BAD: pid={pid} cwd={cwd} cmd={cmdline[:120]!r}"
        )
        return
    notes.append(f"engine alive: pid={pid}, exact worktree={cwd}")


def _assert_finite(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    values = frame.loc[:, list(columns)].apply(pd.to_numeric, errors="raise").to_numpy()
    if not np.isfinite(values).all():
        raise ValueError(f"{label} contains non-finite values")


def main() -> int:
    args = parse_args()
    paper = args.paper_dir.resolve()
    alerts: list[str] = []
    notes: list[str] = []
    attempt: Mapping[str, object] | None = None
    attempt_status: object = None

    if not args.skip_process:
        _check_process(paper, alerts, notes)

    attempt_path = paper / "attempt.json"
    if attempt_path.is_file():
        try:
            raw_attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
            if not isinstance(raw_attempt, Mapping):
                raise ValueError("attempt payload is not an object")
            attempt = raw_attempt
            attempt_status = attempt.get("status")
            if attempt_status not in {"RUNNING", "PASS", "FAIL"}:
                raise ValueError(f"attempt status is invalid: {attempt_status!r}")
            attempt_started = _utc(attempt["started_at"])
            if attempt_status == "FAIL":
                alerts.append(
                    "LATEST TICK FAILED: "
                    f"{attempt.get('boundary')} {attempt.get('error')}"
                )
            elif attempt_status == "RUNNING":
                age = pd.Timestamp.now(tz="UTC") - attempt_started
                if age > pd.Timedelta(minutes=30):
                    alerts.append(
                        f"TICK HUNG: {attempt.get('boundary')} running for {age}"
                    )
                else:
                    notes.append(
                        f"tick currently running: boundary={attempt.get('boundary')}"
                    )
        except Exception as exc:
            alerts.append(f"ATTEMPT MARKER BAD: {exc!r}")

    integrity_path = paper / "integrity.json"
    if not integrity_path.is_file():
        alerts.append(f"ARTIFACTS MISSING: {integrity_path}")
        _print_result(alerts, notes)
        return 1

    try:
        integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
        if not isinstance(integrity, Mapping):
            raise ValueError("integrity payload is not an object")
        if integrity.get("status") != "PASS":
            alerts.append(f"INTEGRITY STATUS: {integrity.get('status')!r}")
        if integrity.get("append_invariance") != "PASS":
            alerts.append("APPEND-INVARIANCE is not PASS")
        if integrity.get("paper_only") is not True:
            alerts.append("PAPER-ONLY authority is not true")

        paths = _verify_artifact_bindings(paper, integrity)
        latest = json.loads(paths["latest"].read_text(encoding="utf-8"))
        decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
        if latest != decision:
            alerts.append("PARITY RECORD DRIFT: latest and immutable decision differ")
        if _canonical_sha256(latest) != integrity.get("decision_sha256"):
            alerts.append("PARITY RECORD DRIFT: latest-boundary hash changed")

        boundary = _utc(integrity["boundary"])
        if _utc(latest["boundary"]) != boundary:
            alerts.append("BOUNDARY DRIFT: integrity and decision differ")
        now = pd.Timestamp.now(tz="UTC")
        current = current_boundary(now)
        expected = (
            current
            if now >= current + pd.Timedelta(minutes=45)
            else current - INTERVAL
        )
        if boundary < expected:
            alerts.append(
                f"DATA/ENGINE STALE: latest boundary {boundary.isoformat()} "
                f"< expected {expected.isoformat()}"
            )
        notes.append(f"latest boundary: {boundary.isoformat()}")

        authority = verify_frozen_authority()
        authority_fields = {
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
        }
        for field, expected_value in authority_fields.items():
            if integrity.get(field) != expected_value:
                alerts.append(f"AUTHORITY DRIFT: {field}")
        notes.append("frozen code/data/dependency/pure-crypto authority: PASS")

        cache = paths["cache_manifest"].parent
        cache_manifest = verify_live_cache_manifest(cache)
        if cache_manifest is None or _utc(cache_manifest["boundary"]) != boundary:
            alerts.append("CACHE BOUNDARY DRIFT: cache and paper tick differ")
        current_pointer = paper / "market-cache" / "CURRENT"
        if not current_pointer.is_file():
            alerts.append("CACHE POINTER MISSING")
        else:
            relative = current_pointer.read_text(encoding="utf-8").strip()
            if (
                not relative
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or Path(relative).parts[:1] != ("generations",)
            ):
                alerts.append("CACHE POINTER UNSAFE")
                current_cache = None
            else:
                current_cache = (
                    paper / "market-cache" / relative
                ).resolve()
            if current_cache is not None and current_cache != cache:
                if attempt_status == "RUNNING" and attempt is not None:
                    in_progress = verify_live_cache_manifest(current_cache)
                    if in_progress is not None and _utc(
                        in_progress["boundary"]
                    ) == _utc(attempt["boundary"]):
                        notes.append(
                            "verified next cache generation is awaiting paper commit"
                        )
                    else:
                        alerts.append(
                            "CACHE POINTER DRIFT: in-progress generation is wrong"
                        )
                else:
                    alerts.append(
                        "CACHE POINTER DRIFT: current generation differs from tick"
                    )

        bridge = pd.read_parquet(paths["bridge_returns"])
        if "timestamp" not in bridge or "net_return" not in bridge:
            raise ValueError("bridge return schema is incomplete")
        bridge_times = pd.to_datetime(bridge["timestamp"], utc=True, errors="raise")
        expected_times = pd.date_range(
            BRIDGE_START,
            boundary - INTERVAL,
            freq=INTERVAL,
            tz="UTC",
        )
        if not pd.DatetimeIndex(bridge_times).equals(expected_times):
            alerts.append("APPEND LOG BAD: bridge returns are not gap-free 8-hour rows")
        _assert_finite(bridge, ("net_return", "equity"), "bridge returns")
        if len(bridge) != integrity.get("stable_bridge_rows"):
            alerts.append("APPEND LOG BAD: bridge row count differs from integrity")
        notes.append(
            f"sealed returns: {len(bridge)} rows through "
            f"{expected_times.max().isoformat() if len(expected_times) else 'none'}"
        )

        forward = pd.read_csv(paths["forward_returns"])
        forward_times = (
            pd.to_datetime(forward["timestamp"], utc=True, errors="raise")
            if not forward.empty
            else pd.DatetimeIndex([], tz="UTC")
        )
        expected_forward = bridge.loc[bridge_times >= LIVE_FORWARD_START]
        if len(forward) != len(expected_forward) or not pd.DatetimeIndex(
            forward_times
        ).equals(pd.DatetimeIndex(pd.to_datetime(expected_forward["timestamp"], utc=True))):
            alerts.append("FORWARD LOG BAD: forward rows are not the exact bridge suffix")
        if not forward.empty:
            _assert_finite(forward, ("net_return", "equity"), "forward returns")
            if not np.array_equal(
                pd.to_numeric(forward["net_return"]).to_numpy(),
                pd.to_numeric(expected_forward["net_return"]).to_numpy(),
            ):
                alerts.append("FORWARD LOG BAD: net returns differ from sealed bridge")
        if len(forward) != integrity.get("forward_rows"):
            alerts.append("FORWARD LOG BAD: row count differs from integrity")
        notes.append(f"official forward observations: {len(forward)}")

        gates = pd.read_csv(paths["gates"])
        expected_gates = _gate_frame(forward)
        pd.testing.assert_frame_equal(
            gates,
            expected_gates,
            check_dtype=False,
            check_exact=False,
            rtol=1e-14,
            atol=1e-14,
        )

        positions = pd.read_csv(paths["positions"])
        required_position_columns = {
            "boundary",
            "symbol",
            "weight",
            "quantity",
            "side",
        }
        if set(positions) != required_position_columns:
            raise ValueError(f"position schema differs: {list(positions)}")
        if positions["symbol"].duplicated().any():
            raise ValueError("positions contain duplicate symbols")
        if not positions.empty:
            if not (pd.to_datetime(positions["boundary"], utc=True) == boundary).all():
                alerts.append("POSITION BOUNDARY DRIFT")
            _assert_finite(positions, ("weight", "quantity"), "positions")
            if (positions["weight"].abs() <= 1e-12).any():
                alerts.append("POSITION DUST: zero-weight rows are persisted")
            expected_sides = np.where(positions["weight"] > 0.0, "LONG", "SHORT")
            if not np.array_equal(positions["side"].to_numpy(), expected_sides):
                alerts.append("POSITION SIDE DRIFT")
        rejected = {
            symbol: symbol_policy_violations(symbol)
            for symbol in positions["symbol"].astype(str)
            if symbol_policy_violations(symbol)
        }
        if rejected:
            alerts.append(f"PURE-CRYPTO VIOLATION in held book: {rejected}")
        gross = float(positions["weight"].abs().sum())
        net = float(positions["weight"].sum())
        notes.append(
            f"held book: {len(positions)} names, gross={gross:.4f}, net={net:+.4f}"
        )

        fills = pd.read_csv(paths["fills"])
        fill_keys = ["timestamp", "symbol", "event_type", "phase"]
        if not set(fill_keys).issubset(fills):
            raise ValueError("paper fill schema is incomplete")
        if not fills.empty:
            fill_times = pd.to_datetime(fills["timestamp"], utc=True, errors="raise")
            if (fill_times > boundary).any() or fills.duplicated(fill_keys).any():
                alerts.append("FILL LOG BAD: future or duplicate boundary events")

        runs = [
            json.loads(line)
            for line in paths["runs"].read_text(encoding="utf-8").splitlines()
        ]
        run_boundaries = [_utc(row["boundary"]) for row in runs]
        if (
            len(run_boundaries) != len(set(run_boundaries))
            or run_boundaries != sorted(run_boundaries)
            or not run_boundaries
            or run_boundaries[-1] != boundary
        ):
            alerts.append("RUN LOG BAD: boundaries are duplicate, unordered, or stale")
        expected_decision_paths: set[Path] = set()
        for row, run_boundary in zip(runs, run_boundaries, strict=True):
            decision_path = (
                paper
                / "boundaries"
                / f"{run_boundary.strftime('%Y%m%dT%H%M%SZ')}.json"
            )
            expected_decision_paths.add(decision_path.resolve())
            if not decision_path.is_file():
                alerts.append(
                    f"DECISION HISTORY BAD: missing {decision_path.name}"
                )
                continue
            payload = json.loads(decision_path.read_text(encoding="utf-8"))
            if _canonical_sha256(payload) != row.get("decision_sha256"):
                alerts.append(
                    f"DECISION HISTORY BAD: hash drift at {run_boundary.isoformat()}"
                )
        actual_decision_paths = {
            path.resolve() for path in (paper / "boundaries").glob("*.json")
        }
        if actual_decision_paths != expected_decision_paths:
            alerts.append("DECISION HISTORY BAD: boundary file set differs from run log")

        diagnostics = json.loads(
            (cache / "diagnostics.json").read_text(encoding="utf-8")
        )
        if diagnostics != integrity.get("data"):
            alerts.append("CACHE DIAGNOSTIC DRIFT: integrity copy differs")
        if _utc(diagnostics["boundary"]) != boundary:
            alerts.append("CACHE DIAGNOSTIC BOUNDARY DRIFT")
        if diagnostics.get("unclassified_bridge_symbols"):
            alerts.append("UNCLASSIFIED BRIDGE CONTRACTS are present")
        archive_provenance = _load_archive_provenance(
            cache / "archive-kline-provenance.json"
        )
        if len(archive_provenance) != diagnostics.get(
            "archive_fallback_file_count"
        ):
            alerts.append("ARCHIVE PROVENANCE count differs from diagnostics")
        notes.append(
            "checksum-verified transaction archive files: "
            f"{len(archive_provenance)}"
        )
        if not diagnostics.get("current_pure_crypto_symbols"):
            alerts.append("PURE-CRYPTO CLASSIFICATION is empty")
        members = tuple(str(value) for value in diagnostics["current_membership_symbols"])
        if len(members) != 40 or len(set(members)) != 40:
            alerts.append("MEMBERSHIP BAD: current universe is not exactly 40 names")
        accounting_symbols = tuple(
            str(value) for value in diagnostics["accounting_symbols"]
        )
        if len(accounting_symbols) != len(set(accounting_symbols)):
            alerts.append("ACCOUNTING SYMBOL REGISTRY contains duplicates")
        if set(positions["symbol"].astype(str)) - set(accounting_symbols):
            alerts.append("HELD BOOK is outside the accounting symbol registry")
        notes.append(f"mark/funding accounting symbols: {len(accounting_symbols)}")
        member_violations = {
            symbol: symbol_policy_violations(symbol)
            for symbol in members
            if symbol_policy_violations(symbol)
        }
        if member_violations:
            alerts.append(f"PURE-CRYPTO VIOLATION in membership: {member_violations}")

        bars = pd.read_parquet(cache / "bars.parquet")
        forming = pd.read_parquet(cache / "forming-bars.parquet")
        marks = pd.read_parquet(cache / "mark_prices.parquet")
        latest_complete = boundary - INTERVAL
        completed_symbols = set(
            bars.loc[
                pd.to_datetime(bars["open_time"], utc=True) == latest_complete,
                "symbol",
            ].astype(str)
        )
        forming_symbols = set(
            forming.loc[
                pd.to_datetime(forming["open_time"], utc=True) == boundary,
                "symbol",
            ].astype(str)
        )
        mark_symbols = set(
            marks.loc[
                pd.to_datetime(marks["mark_time"], utc=True) == boundary,
                "symbol",
            ].astype(str)
        )
        if set(members) - completed_symbols:
            alerts.append("BAR FEED BAD: current members lack latest completed bars")
        if set(members) - forming_symbols:
            alerts.append("OPEN FEED BAD: current members lack boundary opens")
        if set(members) - mark_symbols:
            alerts.append("MARK FEED BAD: current members lack boundary marks")
        funding = pd.read_parquet(cache / "funding.parquet")
        funding_times = pd.to_datetime(funding["funding_time"], utc=True)
        if (funding_times > boundary + pd.Timedelta(seconds=1)).any():
            alerts.append("FUNDING FEED BAD: future settlements are cached")
        actual_funding_events = int(
            (funding_times.dt.floor("h") == boundary).sum()
        )
        notes.append(
            f"funding events at boundary: {actual_funding_events} "
            "(actual exchange schedule; absence is valid)"
        )
    except Exception as exc:
        alerts.append(f"HEALTHCHECK ERROR: {exc!r}")

    _print_result(alerts, notes)
    return 1 if alerts else 0


def _print_result(alerts: list[str], notes: list[str]) -> None:
    print(f"STATUS {'ALERT' if alerts else 'OK'} — Team 09 exact-replay paper desk")
    for alert in alerts:
        print(f"  ALERT: {alert}")
    for note in notes:
        print(f"  {note}")


if __name__ == "__main__":
    sys.exit(main())
