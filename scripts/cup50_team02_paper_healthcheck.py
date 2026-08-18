#!/usr/bin/env python3
"""Read-only integrity, parity, liveness and pure-universe check for Team 02."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from crypto_trade.cup50_desk.authority import (
    paper_root,
    repository_root,
    sha256_file,
    verify_deployment,
)
from crypto_trade.cup50_desk.live_data import verify_generation_chain
from crypto_trade.cup50_desk.schedule import ready_boundary
from crypto_trade.cup50_desk.tick import FORWARD_RETURNS, INTEGRITY, LATEST


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("healthcheck timestamps must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def _canonical_sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _check_process(paper: Path, alerts: list[str], notes: list[str]) -> None:
    path = paper / "engine.lock"
    if not path.is_file():
        alerts.append("ENGINE DOWN: engine.lock is missing")
        return
    with path.open("r+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            held = True
        else:
            held = False
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.seek(0)
        raw_pid = handle.read().strip()
    if not held:
        alerts.append("ENGINE DOWN: engine lock is not held")
        return
    try:
        pid = int(raw_pid)
        cmdline = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        cwd = (Path("/proc") / str(pid) / "cwd").resolve()
    except (OSError, ValueError) as exc:
        alerts.append(f"ENGINE IDENTITY BAD: {exc}")
        return
    if "run_cup50_team02_paper.py" not in cmdline or cwd != repository_root():
        alerts.append(f"ENGINE IDENTITY BAD: pid={pid} cwd={cwd} cmd={cmdline[:140]!r}")
        return
    notes.append(f"engine alive: pid={pid}, exact worktree={cwd}")


def _rows(path: Path) -> int | None:
    if path.suffix == ".parquet":
        return len(pd.read_parquet(path))
    if path.suffix == ".csv":
        return len(pd.read_csv(path))
    return None


def _verify_bindings(paper: Path, integrity: Mapping[str, object]) -> None:
    bindings = integrity.get("artifacts")
    if not isinstance(bindings, Mapping) or not bindings:
        raise ValueError("integrity artifact bindings are missing")
    for label, raw in bindings.items():
        if not isinstance(raw, Mapping):
            raise ValueError(f"artifact binding {label} is malformed")
        relative = raw.get("path")
        if raw.get("external") is True:
            path = Path(str(relative)).resolve()
            if not path.is_relative_to(paper):
                raise ValueError(f"external artifact {label} is outside the paper root")
        else:
            candidate = Path(str(relative))
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError(f"artifact binding {label} has unsafe path")
            path = (paper / candidate).resolve()
            if not path.is_relative_to(paper):
                raise ValueError(f"artifact binding {label} escapes paper root")
        if not path.is_file():
            raise FileNotFoundError(f"bound artifact is missing: {path}")
        if path.stat().st_size != raw.get("size") or sha256_file(path) != raw.get("sha256"):
            raise RuntimeError(f"bound artifact drift: {label}")
        if _rows(path) != raw.get("rows"):
            raise RuntimeError(f"bound artifact row-count drift: {label}")


def health_status(*, skip_process: bool = False) -> tuple[list[str], list[str], dict[str, object]]:
    root = repository_root()
    paper = paper_root(root)
    alerts: list[str] = []
    notes: list[str] = []
    stats: dict[str, object] = {}
    now = pd.Timestamp.now(tz="UTC")
    try:
        deployment = verify_deployment(root)
        notes.append(f"deployment authority: {deployment['manifest_sha256']}")
    except Exception as exc:
        alerts.append(f"DEPLOYMENT AUTHORITY FAILED: {exc}")
    if not skip_process:
        _check_process(paper, alerts, notes)

    authority = json.loads((paper / "authority.json").read_text())
    launch = _utc(authority["launch_time"])
    expected = ready_boundary(now)
    attempt_path = paper / "attempt.json"
    if attempt_path.is_file():
        try:
            attempt = json.loads(attempt_path.read_text())
            if attempt.get("status") == "FAIL":
                alerts.append(
                    f"LATEST TICK FAILED: {attempt.get('boundary')} {attempt.get('error')}"
                )
            elif attempt.get("status") == "RUNNING":
                age = now - _utc(attempt["started_at"])
                if age > pd.Timedelta(hours=2):
                    alerts.append(f"TICK HUNG: {attempt.get('boundary')} for {age}")
                else:
                    notes.append(f"tick running: {attempt.get('boundary')}")
        except Exception as exc:
            alerts.append(f"ATTEMPT MARKER BAD: {exc}")

    integrity_path = paper / INTEGRITY
    if not integrity_path.is_file():
        first_ready = launch + pd.Timedelta(hours=8, minutes=25)
        if now < first_ready:
            notes.append(f"awaiting first completed launch interval; ready after {first_ready}")
            stats.update({"status": "WAITING", "official_observations": 0, "forward_days": 0})
            return alerts, notes, stats
        alerts.append("ARTIFACTS MISSING: first paper boundary is overdue")
        return alerts, notes, stats
    try:
        integrity = json.loads(integrity_path.read_text())
        digest = integrity.get("integrity_sha256")
        body = {key: value for key, value in integrity.items() if key != "integrity_sha256"}
        if digest != _canonical_sha(body):
            raise ValueError("integrity record digest mismatch")
        if integrity.get("status") != "PASS":
            raise ValueError(f"integrity status is {integrity.get('status')!r}")
        for field in ("historical_parity", "append_invariance", "public_data_only"):
            if integrity.get(field) is not True:
                raise ValueError(f"{field} is not PASS")
        if int(integrity.get("membership_count", 0)) != 50:
            raise ValueError("dynamic membership is not exactly 50")
        _verify_bindings(paper, integrity)
        chain = verify_generation_chain(paper / "market-cache")
        notes.append(f"cache generations verified: {len(chain)}")
        latest = json.loads((paper / LATEST).read_text())
        boundary = _utc(latest["boundary"])
        if boundary < min(expected, now.floor("8h") - pd.Timedelta(hours=8)):
            alerts.append(f"STALE BOUNDARY: latest={boundary} expected={expected}")
        if latest.get("historical_parity") is not True or latest.get("membership_count") != 50:
            raise ValueError("latest boundary parity/membership failed")
        members = latest.get("members")
        if not isinstance(members, list) or len(members) != len(set(members)) or len(members) != 50:
            raise ValueError("latest member roster is malformed")
        returns = pd.read_parquet(paper / "ledger" / f"{FORWARD_RETURNS}.parquet")
        returns["decision_time"] = pd.to_datetime(returns["decision_time"], utc=True)
        official = returns.loc[returns["decision_time"] >= launch]
        wealth = (
            float((1.0 + official["net_return"].astype(float)).prod())
            if len(official)
            else 1.0
        )
        path = (1.0 + official["net_return"].astype(float)).cumprod()
        drawdown = 1.0 - path / path.cummax() if len(path) else pd.Series(dtype=float)
        annualized_volatility = (
            float(official["net_return"].astype(float).std(ddof=1) * math.sqrt(3 * 365))
            if len(official) > 1
            else 0.0
        )
        stats.update(
            {
                "status": (
                    "FAILED" if alerts else ("INSUFFICIENT" if len(official) < 90 else "HEALTHY")
                ),
                "latest_boundary": boundary.isoformat(),
                "right_boundary": latest["right_boundary"],
                "membership_count": 50,
                "equity": float(latest["equity"]),
                "official_observations": len(official),
                "official_return": wealth - 1.0,
                "maximum_drawdown": float(drawdown.max()) if len(drawdown) else 0.0,
                "annualized_volatility": annualized_volatility,
                "mean_turnover": float(official["turnover"].mean()) if len(official) else 0.0,
                "mean_gross_exposure": (
                    float(official["gross_exposure"].mean()) if len(official) else 0.0
                ),
                "maximum_absolute_interval_return": (
                    float(official["net_return"].abs().max()) if len(official) else 0.0
                ),
                "forward_days": int(max(pd.Timedelta(0), now - launch) / pd.Timedelta(days=1)),
                "position_count": int(latest["position_count"]),
            }
        )
    except Exception as exc:
        alerts.append(f"INTEGRITY CHECK FAILED: {exc}")
    return alerts, notes, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="CUP-50 Team-02 paper healthcheck")
    parser.add_argument("--skip-process", action="store_true")
    args = parser.parse_args()
    alerts, notes, stats = health_status(skip_process=args.skip_process)
    verdict = "FAILED" if alerts else str(stats.get("status", "HEALTHY"))
    print(f"CUP-50 Team-02 paper desk: {verdict}")
    for note in notes:
        print(f"  OK: {note}")
    for alert in alerts:
        print(f"  ALERT: {alert}")
    for key, value in stats.items():
        if key != "status":
            print(f"  {key}: {value}")
    return 1 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
