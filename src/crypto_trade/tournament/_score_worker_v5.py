"""Sandboxed generic score-boundary worker for draft Amendment 0005.

The frozen V2 worker still owns source loading, incremental history, resources, namespace,
filesystem, network, and seccomp policy.  This worker adds only the reviewed identity-hook capture
and a manifest-bound UTC schedule supplied by the organizer process.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

import pandas as pd

import crypto_trade.tournament._strategy_worker_v2 as frozen_worker
from crypto_trade.tournament.generic_score_adapter_v5 import (
    GenericScoreBoundaryAdapter,
    build_adapter,
)


@dataclasses.dataclass(frozen=True, slots=True)
class _UtcSchedule:
    anchor: pd.Timestamp
    interval: pd.Timedelta

    def contains(self, raw_timestamp: object) -> bool:
        timestamp = pd.Timestamp(raw_timestamp)
        timestamp = (
            timestamp.tz_localize("UTC")
            if timestamp.tzinfo is None
            else timestamp.tz_convert("UTC")
        )
        delta = timestamp - self.anchor
        return delta >= pd.Timedelta(0) and delta.value % self.interval.value == 0


@dataclasses.dataclass
class _ScoreWorkerState:
    historical: Any
    adapter: GenericScoreBoundaryAdapter
    schedule: _UtcSchedule


def _schedule(raw: object) -> _UtcSchedule:
    if not isinstance(raw, Mapping) or set(raw) != {
        "anchor_timestamp_utc",
        "interval_hours",
    }:
        raise ValueError("score worker requires the exact manifest UTC schedule")
    anchor_raw = raw["anchor_timestamp_utc"]
    if type(anchor_raw) is not str or not anchor_raw.endswith("Z"):
        raise ValueError("score schedule anchor must be canonical UTC text")
    anchor = pd.Timestamp(anchor_raw)
    if anchor.tzinfo is None or anchor != anchor.tz_convert("UTC"):
        raise ValueError("score schedule anchor must be UTC")
    hours = raw["interval_hours"]
    if type(hours) is not int or hours < 8 or hours % 8:
        raise ValueError("score schedule interval must be a positive multiple of eight hours")
    return _UtcSchedule(anchor=anchor, interval=pd.Timedelta(hours=hours))


def _initialise(
    message: Mapping[str, Any],
    *,
    bundle: Path,
    entrypoint: str,
) -> _ScoreWorkerState:
    adapter_id = message.get("score_adapter_id")
    if type(adapter_id) is not str:
        raise TypeError("score worker init requires score_adapter_id")
    schedule = _schedule(message.get("score_schedule_utc"))
    historical = frozen_worker._initialise(message, bundle=bundle, entrypoint=entrypoint)
    return _ScoreWorkerState(
        historical=historical,
        adapter=build_adapter(adapter_id, historical.strategy),
        schedule=schedule,
    )


def _decision(
    state: _ScoreWorkerState,
    message: Mapping[str, Any],
) -> tuple[dict[str, float] | None, dict[str, float] | None]:
    eligible = frozen_worker._string_tuple(
        message.get("eligible_symbols"), "eligible_symbols"
    )
    adapted = state.adapter.evaluate(
        lambda: frozen_worker._decision(state.historical, message),
        scheduled=state.schedule.contains(message.get("decision_time")),
        eligible_symbols=eligible,
    )
    weights = (
        None
        if adapted.weights is None
        else {str(symbol): float(value) for symbol, value in adapted.weights.items()}
    )
    scores = (
        None
        if adapted.scores is None
        else {str(symbol): float(value) for symbol, value in adapted.scores.items()}
    )
    return weights, scores


def _serve(protocol_out: TextIO, *, bundle: Path, entrypoint: str) -> int:
    state: _ScoreWorkerState | None = None
    while True:
        try:
            message = frozen_worker._read_message(sys.stdin)
            if message is None:
                return 0
            if message.get("type") == "shutdown":
                frozen_worker._send(protocol_out, {"type": "bye"})
                return 0
            if state is None:
                state = _initialise(message, bundle=bundle, entrypoint=entrypoint)
                frozen_worker._send(protocol_out, {"type": "ready"})
                continue
            weights, scores = _decision(state, message)
            frozen_worker._send(
                protocol_out,
                {"type": "score_result", "weights": weights, "scores": scores},
            )
        except BaseException as exc:
            frozen_worker._send(
                protocol_out,
                {
                    "type": "error",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
            )
            return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", required=True)
    parser.add_argument("--repository-parent", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--site-packages", required=True)
    parser.add_argument("--runtime-site-packages", required=True)
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--empty-dir", required=True)
    parser.add_argument("--empty-file", required=True)
    parser.add_argument("--test-bypass-namespace", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = Path(args.root).resolve()
    repository_parent = Path(args.repository_parent).resolve()
    bundle = Path(args.bundle).resolve()
    site_packages = Path(args.site_packages).resolve()
    runtime_site_packages = Path(args.runtime_site_packages).resolve()
    empty_dir = Path(args.empty_dir).resolve()
    empty_file = Path(args.empty_file).resolve()

    protocol_fd = os.dup(sys.stdout.fileno())
    protocol_out = os.fdopen(protocol_fd, "w", buffering=1, encoding="utf-8")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    try:
        if not args.test_bypass_namespace:
            frozen_worker._prepare_mount_namespace(
                root,
                repository_parent,
                bundle,
                site_packages,
                runtime_site_packages,
                empty_dir,
                empty_file,
            )
            strategy_site_packages = runtime_site_packages
        else:
            strategy_site_packages = site_packages
        frozen_worker._configure_strategy_runtime(
            bundle,
            site_packages,
            strategy_site_packages,
            repository_parent,
            repository_masked=not args.test_bypass_namespace,
        )
        os.chdir(bundle)
        frozen_worker._apply_worker_resource_limits()
        allowed_read_paths = frozen_worker._install_landlock(bundle, strategy_site_packages)
        frozen_worker._install_seccomp_denylist()
        frozen_worker._install_strategy_audit_policy(
            root,
            repository_parent,
            allowed_read_paths,
            repository_masked=not args.test_bypass_namespace,
        )
        return _serve(protocol_out, bundle=bundle, entrypoint=args.entrypoint)
    except BaseException as exc:
        frozen_worker._send(
            protocol_out,
            {
                "type": "error",
                "error_type": "StrategySandboxError",
                "message": str(exc),
            },
        )
        return 1
    finally:
        protocol_out.close()


if __name__ == "__main__":
    raise SystemExit(main())
