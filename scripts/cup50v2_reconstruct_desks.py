#!/usr/bin/env python
"""Replay each desk once: establish its launch state and capture its return series.

Two things need the same expensive replay, so it happens once.

The launch state is what makes the forward desk a continuation rather than a fresh start -- a
strategy carrying smoothed targets, open positions and warm-up state must resume from where the
tournament left it, not from flat.

The parity target is the leaderboard's own published centre score for that lane. Reproducing it
now, from the frozen bundle at the frozen centre, is a real check: it proves the desk about to run
forward is the same object the tournament ranked. For the ensemble there is no published score of
its own, so its parity rests on its three members each reproducing theirs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from crypto_trade.cup50v2.availability import load_unavailability_audit
from crypto_trade.cup50v2.config import IS_START, OOS_END, OOS_START
from crypto_trade.cup50v2.replay import (
    apply_strategy_parameters,
    load_strategy_module,
    run_candidate,
    strategy_from_module,
)
from crypto_trade.cup50v2.scoring import _daily_frame, round_half_even, score_point
from crypto_trade.cup50v2.snapshot import load_snapshot, stitch_snapshots
from crypto_trade.cup50v2_desk.authority import load_desk, repository_root

# Set before any bundle is loaded. A frozen bundle's digest is hashed file by file and
# the desk re-verifies it on every tick, so a stray .pyc written into a bundle stops a
# desk days later and looks like tampering. Nothing here needs bytecode caching.
sys.dont_write_bytecode = True

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")


def _daily(returns: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Daily net returns exactly as the tournament computes them.

    Reusing the scorer's own _daily_frame rather than recompounding by hand: the return series a
    tearsheet reports and the series the leaderboard scored should be the same object, and the
    quickest way to guarantee that is to call the same function. It also knows the frame's schema,
    which a hand-rolled version got wrong -- costs[n].returns is a DataFrame of net_return,
    gross_return and gross_exposure, not a Series.
    """
    frame = _daily_frame(returns, start, end)
    series = pd.Series(
        frame["net_return"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(frame.index, name="date"),
        name="net_return",
    )
    return series


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--desk", action="append", default=None)
    parser.add_argument("--seed", type=int, default=2)
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    desk_ids = tuple(arguments.desk) if arguments.desk else DESKS

    release = json.loads((root / "reports-cup50v2" / "release.json").read_text())
    published = {
        str(entry["team_id"]): float(entry["centre_score"])
        for entry in release["leaderboard"]["entries"]
    }
    sealed_snapshot = load_snapshot(root / "data" / "cup50v2" / "sealed")
    snapshot = stitch_snapshots(
        load_snapshot(root / "data" / "cup50v2" / "is"),
        sealed_snapshot,
    )
    # score_point scores the sealed window and needs its regime labels, which were computed at
    # build time from the equal-weight member index and frozen into the sealed manifest.
    regime_labels = dict(sealed_snapshot.regime_labels)
    audit = load_unavailability_audit(
        root / "tournament" / "cup50v2" / "historical-unavailability.json"
    )

    outcomes = []
    for desk_id in desk_ids:
        desk = load_desk(desk_id, root)
        bundle = root / "tournament" / "cup50v2" / "teams" / desk.team_id
        strategy = strategy_from_module(load_strategy_module(bundle / "strategy.py"))
        if desk.centre:
            apply_strategy_parameters(strategy, dict(desk.centre))
        replay = run_candidate(
            strategy,
            snapshot=snapshot,
            start=IS_START,
            end=OOS_END,
            seed=arguments.seed,
            terminal=False,
            unavailability=audit,
            record_events=False,
        )
        score = float(score_point(replay.costs, regime_labels=regime_labels).score)
        expected = published.get(desk.team_id)
        parity = True
        if expected is not None:
            # Compare like for like. The leaderboard publishes the score after the tournament's own
            # round-half-even at 1e-6, so comparing an unrounded replay against it fails on the
            # eleventh decimal while the two are in fact the same number. Rounding here with the
            # tournament's own function is the comparison; a tolerance would have been a guess.
            parity = round_half_even(score) == round_half_even(expected)
            if not parity:
                raise SystemExit(
                    f"{desk_id}: replay does not reproduce the published centre score; "
                    f"{round_half_even(score)!r} != {round_half_even(expected)!r}"
                )

        paper = root / "paper-cup50v2" / desk_id
        paper.mkdir(parents=True, exist_ok=True)
        authority = json.loads((paper / "authority.json").read_text())

        # One cost multiplier is the desk's operating basis: 1x is the realistic live cost.
        realistic = replay.costs[1]
        daily = _daily(realistic.returns, IS_START, OOS_END)
        ledger = paper / "ledger"
        ledger.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame({"date": daily.index, "net_return": daily.to_numpy()})
        frame.to_parquet(ledger / "historical_daily_returns.parquet", index=False)

        reconstruction = {
            "schema_version": 1,
            "namespace": "cup50v2-paper-reconstruction",
            "desk_id": desk_id,
            "team_id": desk.team_id,
            "candidate_id": desk.candidate_id,
            "parity": bool(parity),
            "centre_score_is_not_comparable": (
                "A sealed-window score for a book whose members were chosen using those same "
                "sealed results is in-sample with respect to its own selection. It is not "
                "evidence against a lane that was scored blind."
            ) if expected is None else None,
            "parity_basis": (
                "reproduces the released centre score for this lane"
                if expected is not None
                else "no published score of its own; parity rests on its three members"
            ),
            "centre_score": score,
            "published_centre_score": expected,
            "cost_multiplier": 1,
            "decision_time": OOS_END.isoformat(),
            "equity": float(realistic.final_state.equity),
            "quantities": {
                str(k): float(v) for k, v in dict(realistic.final_state.quantities).items()
            },
            "lineage_sha256": authority["lineage_sha256"],
            "nomination_sha256": desk.nomination_sha256,
            "historical_days": int(len(daily)),
            "in_sample_days": int((daily.index < OOS_START).sum()),
            "sealed_days": int((daily.index >= OOS_START).sum()),
        }
        (paper / "reconstruction.json").write_text(
            json.dumps(reconstruction, indent=2, sort_keys=True) + "\n"
        )
        outcomes.append(
            {
                "desk": desk_id,
                "team": desk.team_id,
                "score": round(score, 6),
                "published": expected,
                "parity": parity,
                "equity": round(float(realistic.final_state.equity), 2),
                "days": int(len(daily)),
            }
        )
        print(json.dumps(outcomes[-1], sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
