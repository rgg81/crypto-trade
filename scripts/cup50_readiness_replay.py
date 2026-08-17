"""Run and summarize the non-promoteable full-IS CUP-50 readiness strategy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from crypto_trade.cup50.availability import load_unavailability_audit
from crypto_trade.cup50.config import IS_START, OOS_START
from crypto_trade.cup50.replay import load_strategy_module, run_candidate, strategy_from_module
from crypto_trade.cup50.snapshot import load_snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--unavailability-audit", required=True)
    arguments = parser.parse_args()

    snapshot = load_snapshot(arguments.snapshot)
    strategy = strategy_from_module(load_strategy_module(arguments.strategy))
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=IS_START,
        end=OOS_START,
        seed=0,
        terminal=False,
        unavailability=load_unavailability_audit(arguments.unavailability_audit),
    )
    hashes = {
        str(cost): hashlib.sha256(
            result.returns.to_json(
                orient="split", date_format="iso", double_precision=15
            ).encode()
        ).hexdigest()
        for cost, result in replay.costs.items()
    }
    summary = {
        "status": "passed",
        "strategy_sha256": hashlib.sha256(Path(arguments.strategy).read_bytes()).hexdigest(),
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "boundaries": len(replay.raw_targets),
        "all_flat": all(
            float(result.returns["gross_exposure"].max()) == 0.0
            for result in replay.costs.values()
        ),
        "return_sha256": hashes,
    }
    if not summary["all_flat"]:
        raise RuntimeError("flat readiness strategy produced exposure")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
