"""Emit a stable digest for a bounded production CUP-50 replay."""

from __future__ import annotations

import argparse
import hashlib
import json

import pandas as pd

from crypto_trade.cup50.availability import load_unavailability_audit
from crypto_trade.cup50.replay import load_strategy_module, run_candidate, strategy_from_module
from crypto_trade.cup50.snapshot import load_snapshot


def _frame_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_json(orient="split", date_format="iso", double_precision=15).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--unavailability-audit", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--label", required=True)
    arguments = parser.parse_args()

    replay = run_candidate(
        strategy_from_module(load_strategy_module(arguments.strategy)),
        snapshot=load_snapshot(arguments.snapshot),
        start=pd.Timestamp(arguments.start),
        end=pd.Timestamp(arguments.end),
        seed=arguments.seed,
        terminal=False,
        unavailability=load_unavailability_audit(arguments.unavailability_audit),
    )
    digest = hashlib.sha256()
    digest.update(_frame_bytes(replay.raw_targets))
    digest.update(_frame_bytes(replay.risk_scalars.rename("risk_scalar").to_frame()))
    for cost, result in sorted(replay.costs.items()):
        digest.update(str(cost).encode())
        digest.update(_frame_bytes(result.returns))
        digest.update(_frame_bytes(result.events))
    print(
        json.dumps(
            {
                "boundaries": len(replay.raw_targets),
                "label": arguments.label,
                "replay_sha256": digest.hexdigest(),
                "status": "passed",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
