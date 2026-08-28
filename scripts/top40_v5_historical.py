"""The one-shot historical observation, and the final desks.

Every candidate that cleared the sealed bar is observed here, once. The sealed stage ordered the
advancing set; **this window produces the ranking and staffs the desks**, because at 2.5 years the
standard error of an annualised Sharpe is about 0.63 against roughly 1.0 on the sealed blocks -- the
most discriminating evidence this edition has.

**It authorizes nothing.** The window is byte-identical to CUP-50 v2's released sealed window, whose
full twelve-lane leaderboard is published and whose structural findings were known to the organizer
while this edition was designed. It is not a holdout for me. Capital gates solely on the forward
record from 2026-09-01, which is the only uncontaminated evidence of any kind.

Three things the release reports because a bare Sharpe over this window would overstate what it
knows:

* **A confidence interval on every figure.** SE(Sharpe) is about 0.63 here, so differences smaller
  than that are not differences.
* **Split halves.** A candidate carried entirely by one half is labelled as such rather than
  presented as a 2.5-year result.
* **A sign-randomised null band.** A candidate whose Sharpe falls inside the central 80% of its own
  sign-randomised replays is labelled ``indistinguishable-from-null`` -- a statement the leaderboard
  cannot make on its own.

Usage::

    uv run python scripts/top40_v5_historical.py --dry-run
    uv run python scripts/top40_v5_historical.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5 import journal, metrics, orchestrator, runner, statistics
from crypto_trade.tournament.v5.engine import EvaluatorConfig, generate_targets
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from top40_v5_evaluate import INTERVAL_HOURS, REPO, SNAPSHOT, TOURNAMENT, _thresholds  # noqa: E402

HISTORICAL_START = pd.Timestamp("2024-02-01", tz="UTC")
HISTORICAL_END = pd.Timestamp("2026-08-01", tz="UTC")
SPLIT = pd.Timestamp("2025-05-01", tz="UTC")
JOURNAL = TOURNAMENT / "research-journal.jsonl"


def _cleared() -> list[tuple[str, str]]:
    return [
        (r.payload["team_id"], r.payload["candidate_id"])
        for r in journal.iter_events(JOURNAL, "sealed_evaluated")
        if r.payload["cleared"]
    ]


def _sharpe_interval(sharpe: float, days: int, confidence: float = 0.90) -> tuple[float, float]:
    """A normal interval on an annualised Sharpe. SE ~ sqrt(1/years) for a unit-Sharpe book."""

    years = max(days / metrics.ANNUALISATION_DAYS, 1e-9)
    standard_error = math.sqrt((1.0 + 0.5 * sharpe * sharpe) / years)
    critical = statistics.normal_quantile(0.5 + confidence / 2.0)
    return sharpe - critical * standard_error, sharpe + critical * standard_error


def observe(team_id: str, candidate_id: str, data, thresholds, decisions) -> dict:
    started = time.monotonic()
    path = TOURNAMENT / "teams" / team_id / "outbox" / "candidate.py"
    spec = importlib.util.spec_from_file_location(f"hist_{team_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    targets = generate_targets(
        module.build_strategy(),
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

    full = pd.date_range(
        HISTORICAL_START, HISTORICAL_END - pd.Timedelta(days=1), freq="D", tz="UTC"
    )
    first = full[full < SPLIT]
    second = full[full >= SPLIT]

    def summarise(index):
        return metrics.summarize(
            ladder.base,
            index,
            double_cost_returns=ladder.daily("double"),
            triple_cost_returns=ladder.daily("triple"),
            trial_count=1,
            trial_sharpe_dispersion=0.0,
            breadth_floor=thresholds.minimum_median_effective_breadth,
        )

    whole, half_one, half_two = summarise(full), summarise(first), summarise(second)
    daily = ladder.daily("base")
    daily = daily.loc[daily.index.isin(full)]
    low, high = orchestrator.sign_randomised_null_band(daily, draws=2000)
    interval = _sharpe_interval(whole.net_sharpe, whole.days)

    row = {
        "team_id": team_id,
        "candidate_id": candidate_id,
        "packet": whole.as_dict(),
        "first_half_sharpe": half_one.net_sharpe,
        "second_half_sharpe": half_two.net_sharpe,
        "sharpe_interval": list(interval),
        "null_band": [low, high],
        "indistinguishable_from_null": low <= whole.net_sharpe <= high,
        "carried_by_one_half": (half_one.net_sharpe > 0) != (half_two.net_sharpe > 0),
    }
    print(
        f"  {team_id:10s} sh={whole.net_sharpe:+.3f} [{interval[0]:+.2f},{interval[1]:+.2f}] "
        f"2x={whole.double_cost_sharpe:+.3f} h1={half_one.net_sharpe:+.3f} "
        f"h2={half_two.net_sharpe:+.3f} dd={whole.max_drawdown:.2f} "
        f"null=[{low:+.2f},{high:+.2f}]"
        f"{'  INDISTINGUISHABLE' if row['indistinguishable_from_null'] else ''}"
        f"{'  ONE-HALF' if row['carried_by_one_half'] else ''}"
        f" [{(time.monotonic() - started) / 60:.1f}m]",
        flush=True,
    )
    return row


def main() -> int:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    cleared = _cleared()
    if not cleared:
        print("nothing cleared the sealed bar; there is no historical observation to make")
        return 1
    if any(journal.iter_events(JOURNAL, "historical_released")):
        print("the historical window has already been released; it is a one-shot observation")
        return 1

    print(f"historical window {HISTORICAL_START.date()} -> {HISTORICAL_END.date()} (2.5y)")
    print(f"{len(cleared)} candidate(s) cleared the sealed bar\n", flush=True)
    if arguments.dry_run:
        for team_id, candidate_id in cleared:
            print(f"  would observe {team_id}:{candidate_id}")
        return 0

    # Accepted before the window is opened, so the record predates the evidence.
    journal.append(
        JOURNAL,
        "historical_accepted",
        {"candidates": [f"{t}:{c}" for t, c in cleared], "window": str(HISTORICAL_START.date())},
    )

    thresholds = _thresholds()
    data = {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }
    decisions = list(
        pd.date_range(
            HISTORICAL_START, HISTORICAL_END, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="left"
        )
    )

    rows = []
    for team_id, candidate_id in cleared:
        try:
            rows.append(observe(team_id, candidate_id, data, thresholds, decisions))
        except Exception as error:  # noqa: BLE001
            print(f"  {team_id:10s} FAULT {type(error).__name__}: {error}"[:150], flush=True)

    rows.sort(key=lambda r: r["packet"]["net_sharpe"], reverse=True)
    top = [f"{r['team_id']}:{r['candidate_id']}" for r in rows[:3]]
    desks = [{"name": n, "constituents": [n], "weights": {n: 1.0}} for n in top]
    if len(top) == 3:
        desks.append(
            {
                "name": orchestrator.ENSEMBLE_DESK,
                "constituents": top,
                "weights": {n: 1 / 3 for n in top},
            }
        )

    print(f"\nfinal ranking on the historical window ({len(rows)} observed):")
    for position, r in enumerate(rows, start=1):
        name = f"{r['team_id']}:{r['candidate_id']}"
        sharpe = r["packet"]["net_sharpe"]
        print(f"  {position}. {name:18s} sharpe {sharpe:+.3f}")
    print(f"\nfour forward desks: {[d['name'] for d in desks]}")

    payload = {
        "window": {"start": str(HISTORICAL_START), "end_exclusive": str(HISTORICAL_END)},
        "split_at": str(SPLIT),
        "rows": rows,
        "desks": desks,
        "authorizes": "nothing; capital gates on the forward record from 2026-09-01",
    }
    journal.append(JOURNAL, "historical_released", {"ranking": [r["team_id"] for r in rows]})
    out = REPO / TOP40_V5_LAYOUT.historical_release_root
    out.mkdir(parents=True, exist_ok=True)
    (out / "release.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"\nwrote {(out / 'release.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
