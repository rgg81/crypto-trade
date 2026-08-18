#!/usr/bin/env python3
"""Freeze the winner's exact historical 8-hour stream for live-prefix parity checks."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from crypto_trade.cup50.availability import load_unavailability_audit
from crypto_trade.cup50.config import IS_START, OOS_END
from crypto_trade.cup50.replay import (
    apply_strategy_parameters,
    load_strategy_module,
    run_candidate,
    strategy_from_module,
)
from crypto_trade.cup50.scoring import score_point
from crypto_trade.cup50.snapshot import load_snapshot, stitch_snapshots
from crypto_trade.cup50_desk.authority import (
    paper_root,
    repository_root,
    verify_lineage,
    winner_bundle,
)
from crypto_trade.cup50_desk.tick import HISTORICAL_PREFIX, _historical_stream


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze Team-02 exact historical prefix")
    parser.add_argument("--verify", action="store_true", help="verify an existing prefix")
    args = parser.parse_args()
    root = repository_root()
    lineage = verify_lineage(root)
    nomination = lineage["nomination"]
    strategy = strategy_from_module(load_strategy_module(winner_bundle(root) / "strategy.py"))
    apply_strategy_parameters(strategy, nomination["centre"])
    snapshot = stitch_snapshots(
        load_snapshot(root / "data" / "cup50" / "is"),
        load_snapshot(root / "data" / "cup50" / "sealed"),
    )
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=IS_START,
        end=OOS_END,
        seed=2,
        terminal=False,
        unavailability=load_unavailability_audit(
            root / "tournament" / "cup50" / "organizer-recovery-unavailability.json"
        ),
        record_events=False,
    )
    expected_score = float(lineage["reconstruction"]["centre_score"])
    score = score_point(replay.costs).score
    if score != expected_score:
        raise ValueError(f"winner score parity failed: {score!r} != {expected_score!r}")
    stream = _historical_stream(replay)
    destination = paper_root(root) / HISTORICAL_PREFIX
    if destination.exists():
        if not args.verify:
            raise FileExistsError(destination)
        existing = pd.read_parquet(destination)
        pd.testing.assert_frame_equal(stream, existing, check_exact=True, check_dtype=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        stream.to_parquet(destination, index=False)
    print(
        json.dumps(
            {
                "path": str(destination),
                "rows": len(stream),
                "score": score,
                "equity": float(replay.costs[1].final_state.equity),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
