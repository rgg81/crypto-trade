"""Sandboxed historical-target replay with organizer-owned score capture.

This worker reuses the frozen V2 strategy worker's namespace, resource, filesystem, network, and
incremental-history controls.  The only protocol extension is an organizer-reviewed adapter that
returns the exact pre-construction score observed while the original strategy constructs targets.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

import crypto_trade.tournament._strategy_worker_v2 as frozen_worker
from crypto_trade.tournament.score_adapters.team01_rdf_v1 import (
    Team01RdfScoreAdapter,
    build_adapter,
)


@dataclasses.dataclass
class _ScoreWorkerState:
    historical: Any
    adapter: Team01RdfScoreAdapter


def _initialise(
    message: Mapping[str, Any],
    *,
    bundle: Path,
    entrypoint: str,
) -> _ScoreWorkerState:
    adapter_id = message.get("score_adapter_id")
    if not isinstance(adapter_id, str):
        raise TypeError("score worker init requires score_adapter_id")
    historical = frozen_worker._initialise(
        message,
        bundle=bundle,
        entrypoint=entrypoint,
    )
    return _ScoreWorkerState(
        historical=historical,
        adapter=build_adapter(adapter_id, historical.strategy),
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
        eligible_symbols=eligible,
    )
    if adapted.weights is None:
        weights = None
    else:
        weights = {str(symbol): float(value) for symbol, value in adapted.weights.items()}
    if adapted.scores is None:
        scores = None
    else:
        scores = {item.symbol: item.score for item in adapted.scores}
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
                {
                    "type": "score_result",
                    "weights": weights,
                    "scores": scores,
                },
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
