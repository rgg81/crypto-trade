#!/usr/bin/env python3
"""Recompute the frozen Team 09 replay or report its released golden stream."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_trade.team09.backtest import (
    load_frozen_snapshot,
    replay_summary,
    run_replay,
    verify_historical_parity,
    write_replay_artifacts,
)
from crypto_trade.team09.report import (
    generate_all_period_report,
    load_released_daily_returns,
    period_statistics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Team 09 continuous IS + historical-OOS replay. By default this "
            "regenerates the report from the hash-verified atomic release."
        )
    )
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="run the frozen strategy/evaluator from raw snapshot data before reporting",
    )
    parser.add_argument(
        "--cost-multiplier",
        type=float,
        action="append",
        dest="cost_multipliers",
        help="cost scenario to replay; repeat for several scenarios (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/team09"),
        help="output directory (default: reports/team09)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    if args.recompute:
        multipliers = args.cost_multipliers or [1.0]
        if 1.0 not in multipliers:
            raise SystemExit("--recompute must include --cost-multiplier 1")
        replay = run_replay(
            load_frozen_snapshot(),
            cost_multipliers=multipliers,
        )
        parity = verify_historical_parity(replay)
        write_replay_artifacts(replay, output_dir / "replay")
        returns = replay.daily_returns(1.0)
        source = "fresh frozen-snapshot continuous replay; golden parity PASS"
        replay_payload: dict[str, object] | None = replay_summary(replay)
        replay_payload["golden_parity"] = parity
    else:
        if args.cost_multipliers:
            raise SystemExit("--cost-multiplier requires --recompute")
        returns = load_released_daily_returns()
        source = "hash-verified atomic historical release"
        replay_payload = None

    paths = generate_all_period_report(returns, output_dir, source=source)
    output = {
        "source": source,
        "statistics": period_statistics(returns),
        "artifacts": {name: str(path) for name, path in paths.items()},
    }
    if replay_payload is not None:
        output["replay"] = replay_payload
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
