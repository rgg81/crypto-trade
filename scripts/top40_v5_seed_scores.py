"""Run the fifteen organizer seeds through the real evaluator on the real snapshot.

This is two things at once, and both are load-bearing.

It is the **readiness load**: fifteen genuinely different books driven end to end through
membership, funding, participation limits, forced exits and the risk unit. A prior edition's
readiness strategy was flat, exercised almost none of the evaluator, and six defects survived to
invalidate all twelve of that edition's trials. Fifteen seeds that each actually trade are a far
harder thing to pass.

And it produces the **calibrated threshold distribution**. Every performance number in the config
has to land in an observed gap in a measured field rather than at a round number somebody liked --
prior editions inherited their floors and discovered afterwards that the full set admitted zero of
ninety-four measured trials.

Usage::

    uv run python scripts/top40_v5_seed_scores.py --smoke          # one seed, short window
    uv run python scripts/top40_v5_seed_scores.py                  # all fifteen, full window

Writes one JSON artifact per seed into the visible reports root, plus a combined summary. Sealed
statistics are never computed here: this script only ever holds the visible index.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5 import lanes, metrics, runner, sealed, seeds
from crypto_trade.tournament.v5.engine import EvaluatorConfig, generate_targets

SNAPSHOT = Path("data/top40/snapshot-v3")
SCORED_START = pd.Timestamp("2020-08-02", tz="UTC")
SCORED_END = pd.Timestamp("2024-02-01", tz="UTC")
INTERVAL_HOURS = 8


def _load() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }


def _partition(
    start: pd.Timestamp, end: pd.Timestamp, *, interleaved_count: int = 7
) -> sealed.SealedPartition:
    """The frozen schedule on the full window; a proportionally smaller one on a smoke window.

    ``interleaved_count`` is a parameter rather than a constant because ``sealed_blocks`` correctly
    refuses to fit seven 45-day blocks into a 400-day smoke window -- and silently accepting fewer
    would make the smoke run a different experiment from the real one without saying so.
    """

    index = pd.date_range(start, end - pd.Timedelta(days=1), freq="D", tz="UTC")
    blocks = sealed.sealed_blocks(
        start=start,
        end_exclusive=end,
        block_days=45,
        stride=7,
        residues=(1, 4),
        interleaved_count=interleaved_count,
        terminal_block=True,
    )
    return sealed.partition(index, blocks, purge_days=5, embargo_days=10)


def _decision_times(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range(start, end, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="left"))


def _score_one(name: str, data: dict[str, pd.DataFrame], part, decisions, reports_root: Path):
    started = time.monotonic()
    targets = generate_targets(
        seeds.build_seed(name),
        data["bars"],
        data["funding"],
        data["membership"],
        decisions,
        seed=42,
        interval_hours=INTERVAL_HOURS,
    )
    ladder = runner.evaluate_cost_ladder(
        data["bars"],
        data["funding"],
        data["membership"],
        targets,
        mark_prices=data["mark_prices"],
        config=EvaluatorConfig(),
    )
    packet = metrics.summarize(
        ladder.base,
        part.visible,
        double_cost_returns=ladder.daily("double"),
        triple_cost_returns=ladder.daily("triple"),
        trial_count=1,
        trial_sharpe_dispersion=0.0,
        breadth_floor=6.0,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / f"seed.{name}.json").write_text(
        json.dumps(packet.as_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    elapsed = time.monotonic() - started
    print(
        f"  {name:24s} sharpe={packet.net_sharpe:+.3f} 2x={packet.double_cost_sharpe:+.3f} "
        f"gross={packet.mean_gross_exposure:.3f} breadth={packet.median_effective_breadth:.1f} "
        f"turn={packet.annualised_turnover:.1f} ruined={packet.ruined} [{elapsed / 60:.1f}m]",
        flush=True,
    )
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="one seed over a short window")
    parser.add_argument("--seed-name", default=None, help="run a single named seed")
    parser.add_argument("--out", default="reports-top40-v5/is", help="visible reports root")
    arguments = parser.parse_args()

    start, end = SCORED_START, SCORED_END
    names = [entry.seed for entry in lanes.LANES]
    interleaved = 7
    if arguments.smoke:
        end = SCORED_START + pd.Timedelta(days=400)
        names = ["timeseries_momentum"]
        interleaved = 1
    if arguments.seed_name:
        names = [arguments.seed_name]

    print(f"window {start.date()} -> {end.date()}   seeds: {len(names)}", flush=True)
    data = _load()
    print(
        f"loaded bars={len(data['bars']):,} funding={len(data['funding']):,} "
        f"membership={len(data['membership']):,}",
        flush=True,
    )

    part = _partition(start, end, interleaved_count=interleaved)
    runner.assert_windows_are_disjoint(part.visible, part.sealed)
    print(
        f"visible={len(part.visible)}d sealed={len(part.sealed)}d withheld={len(part.excluded)}d",
        flush=True,
    )

    decisions = _decision_times(start, end)
    reports_root = Path(arguments.out)
    packets = {}
    for name in names:
        try:
            packets[name] = _score_one(name, data, part, decisions, reports_root)
        except Exception as error:  # noqa: BLE001 - a seed failure must not stop the field
            print(f"  {name:24s} FAILED: {type(error).__name__}: {error}", flush=True)

    if packets:
        summary = {
            name: {
                "net_sharpe": packet.net_sharpe,
                "double_cost_sharpe": packet.double_cost_sharpe,
                "mean_gross_exposure": packet.mean_gross_exposure,
                "median_effective_breadth": packet.median_effective_breadth,
                "annualised_turnover": packet.annualised_turnover,
                "gross_edge_bps_per_turnover": packet.gross_edge_bps_per_turnover,
                "max_drawdown": packet.max_drawdown,
                "deletion_profile_p05_sharpe": packet.deletion_profile_p05_sharpe,
                "ruined": packet.ruined,
            }
            for name, packet in packets.items()
        }
        (reports_root / "seed-distribution.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(f"\nwrote {len(packets)} seed packets to {reports_root}", flush=True)

    return 0 if len(packets) == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
