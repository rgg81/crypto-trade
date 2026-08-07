"""Pre-flight: score one reference strategy end to end on the real in-sample snapshot.

Run this BEFORE dispatching any team, and again after any change to the snapshot, the universe,
the evaluator or the scoring stack. Run from the repository root.

    uv run python scripts/cup20_readiness.py

It is not a unit test and it does not replace one. Every unit test in ``tests/cup20`` builds its
own fixture, and a fixture is exactly where a data defect cannot live: 862 of them passed while the
built snapshot held 21 decision boundaries at which ``evaluate_targets`` raised ``missing current
mark for eligible symbols`` on SUIUSDT. That raise fires on the ELIGIBLE set before a single line
of strategy code runs, so it would have crashed all twelve teams, on every candidate, at the first
backtest -- and nothing in the repository would have said so until a team hit it.

What makes this the check that catches that class: it runs the REAL snapshot through the REAL
pipeline over the FULL window, in the order a team's candidate travels it --

    run_candidate  ->  assemble_scored_metrics  ->  adjudicate_candidate

-- and fails if any stage raises. A defect that only exists in the data reaches it and nothing
else. It also re-derives the mark-coverage post-condition directly, so the specific defect above
is reported by name rather than as a stack trace 40 minutes in.

**The reference strategy is not a benchmark.** It is a load: a weekly cross-sectional reversal book
that trades both sides, turns over, and holds between rebalances, chosen because it exercises short
quantities, funding on shorts, the exposure caps and the risk unit rather than because anyone
expects it to qualify. Its metrics are printed in full so a human can see whether the numbers are
sane -- a Sharpe of 40, a drawdown of 0.0 or a trade count of 3 says the pipeline is broken even
though nothing raised. A `NOT QUALIFIED` verdict for the reference book is an ordinary outcome and
is not a failure of this check; only a raise, or an unmarkable member, is.
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20.adjudication import CandidateAdjudication, adjudicate_candidate
from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.metrics import is_folds
from crypto_trade.cup20.runner import CandidateRun, decision_grid, evaluator_config, run_candidate
from crypto_trade.cup20.scored_metrics import ScoredVector, assemble_scored_metrics
from crypto_trade.cup20.snapshot import Snapshot, load_snapshot, resolve_is_start
from crypto_trade.cup20.universe import unmarkable_member_boundaries
from crypto_trade.tournament.protocol import DecisionContext

CONFIG_PATH = Path("tournament/cup20/config.toml")
REFERENCE_SEED = 20260807

# The reference load's own two knobs. Neither is tuned and neither is policy -- they exist so the
# book trades both sides at a cadence the evaluator has to work at. Weekly, because rebalancing
# every 8h would spend the whole run inside the participation cap and say nothing about the rest of
# the pipeline; five a side, because a 20-name universe split into thirds puts each name at 1/7
# gross, below the 0.20 per-symbol cap, so the caps stay capable of binding rather than binding
# everywhere.
REFERENCE_LOOKBACK_BARS = 21
REFERENCE_SLEEVE = 5


class WeeklyCrossSectionalReversal:
    """Short last week's winners, buy last week's losers, rebalanced weekly, unit gross.

    Deliberately the dullest strategy that still exercises the whole evaluator: both sides, real
    turnover, positions carried between rebalances, and a book whose composition changes with
    membership. It reads only ``context.bars``, which is past-only by construction.
    """

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        if context.decision_time.weekday() != 0 or context.decision_time.hour != 0:
            return None  # hold; the evaluator still enforces membership and delisting exits
        returns: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            closes = context.bars.get(symbol)
            if closes is None or len(closes) <= REFERENCE_LOOKBACK_BARS:
                continue
            window = closes["close"].to_numpy(dtype=float)[-(REFERENCE_LOOKBACK_BARS + 1) :]
            if not (window > 0).all():
                continue
            returns[symbol] = float(window[-1] / window[0] - 1.0)
        if len(returns) < 2 * REFERENCE_SLEEVE:
            return {}  # too thin to take both sides; ask for a flat book rather than half of one
        ordered = sorted(returns, key=lambda symbol: (returns[symbol], symbol))
        longs = ordered[:REFERENCE_SLEEVE]
        shorts = ordered[-REFERENCE_SLEEVE:]
        weight = 1.0 / (2 * REFERENCE_SLEEVE)
        return {symbol: weight for symbol in longs} | {symbol: -weight for symbol in shorts}


def _stage(label: str, function, *arguments, **keywords):
    """Run one pipeline stage, timing it and turning any raise into a loud, attributed failure."""
    print(f"  {label:<24} ", end="", flush=True)
    started = time.monotonic()
    try:
        result = function(*arguments, **keywords)
    except SystemExit as failure:
        # A stage that already knows exactly what is wrong says so; a traceback would only bury it.
        print("FAILED\n")
        print(f"{'=' * 78}\nREADINESS FAILED at stage: {label}\n{'=' * 78}\n{failure}")
        raise
    except BaseException:
        print("RAISED\n")
        print(f"{'=' * 78}\nREADINESS FAILED at stage: {label}\n{'=' * 78}")
        traceback.print_exc()
        raise
    elapsed = time.monotonic() - started
    # Flushed, always. Redirected to a file, Python block-buffers stdout, so a stage that has
    # finished looks identical to one that has hung -- and `run_candidate` takes minutes, which is
    # exactly the window in which an organiser would go looking.
    print(f"ok   {elapsed:7.1f}s", flush=True)
    return result


def check_mark_coverage(snapshot: Snapshot) -> int:
    """The specific defect this script exists for, reported by name before it becomes a crash."""
    frame = snapshot.bars.assign(open_time=pd.to_datetime(snapshot.bars["open_time"], utc=True))
    opens = frame.pivot(index="open_time", columns="symbol", values="open").sort_index()
    marks = snapshot.mark_prices.assign(
        mark_time=pd.to_datetime(snapshot.mark_prices["mark_time"], utc=True)
    )
    published = marks.pivot(index="mark_time", columns="symbol", values="mark_price")
    aligned = published.reindex(index=opens.index, columns=opens.columns)
    offending = unmarkable_member_boundaries(
        snapshot.membership, fillable=opens.notna(), markable=aligned.notna()
    )
    if offending:
        symbols = sorted({symbol for _, symbol in offending})
        raise SystemExit(
            f"READINESS FAILED: the snapshot holds {len(offending)} (boundary, symbol) pairs the "
            f"evaluator cannot mark, across {symbols}. Every candidate would raise "
            f"'missing current mark for eligible symbols' at {offending[0][0]}. Rebuild the "
            "universe; do not dispatch teams."
        )
    return len(snapshot.membership)


def run_reference(
    snapshot: Snapshot, raw: Mapping[str, Any], *, is_start: pd.Timestamp
) -> tuple[CandidateRun, Sequence[pd.Timestamp]]:
    config = evaluator_config(raw["execution"])
    grid = decision_grid(is_start, IS_END, interval_hours=config.interval_hours)
    run = run_candidate(
        WeeklyCrossSectionalReversal(),
        snapshot,
        decision_times=grid,
        seed=REFERENCE_SEED,
        config=config,
        risk_unit=raw["risk_unit"],
        cost_multipliers=tuple(raw["execution"]["cost_multipliers"]),
    )
    return run, grid


def adjudicate(scored: ScoredVector, raw: Mapping[str, Any]) -> CandidateAdjudication:
    """Adjudicate the reference vector with the frozen floors and neutral research inputs.

    The three research-certificate inputs are not measurable from a backtest -- they come from a
    team's declared neighbourhood, its trial ledger and its sign-inversion control -- so they are
    supplied at values that pass, on purpose: this stage is being exercised for its ability to RUN
    over a real metric vector, and a synthetic failure in an input the reference book does not have
    would hide whatever the floors themselves say. ``declared_roles`` is the one that is NOT
    neutral: the book genuinely trades both sides, so it declares both, and
    ``declared_roles_match_traded_sides`` stays a live check on the vector rather than a formality.
    """
    return adjudicate_candidate(
        scored,
        team_id="reference",
        candidate_id="weekly-cross-sectional-reversal",
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=1.0,
        trial_adjusted_confidence=1.0,
        # Section 7.3's own drawdown floor. Passed explicitly because the holdout rebases this one
        # term to 0.25 while every other input keeps its 7.3 meaning; an in-sample adjudication
        # that inherited the wrong one would score on the holdout's scale without saying so.
        drawdown_floor=float(raw["floors"]["max_drawdown"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="CUP-20 pre-start readiness check")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument(
        "--json",
        default=None,
        help="also write the reference metrics and gate table to this path",
    )
    arguments = parser.parse_args()

    overall = time.monotonic()
    raw = load_config(arguments.config).raw
    snapshot_root = Path(raw["data"]["is_root"])
    print(f"CUP-20 readiness -- reference strategy end to end on {snapshot_root}\n")

    snapshot = _stage("load IS snapshot", load_snapshot, snapshot_root)
    membership_rows = _stage("mark coverage", check_mark_coverage, snapshot)
    is_start = resolve_is_start(
        snapshot.membership, target_size=int(raw["universe"]["target_size"])
    )
    boundaries = pd.to_datetime(snapshot.membership["reconstitution_time"], utc=True)
    grid_size = len(
        decision_grid(is_start, IS_END, interval_hours=int(raw["execution"]["interval_hours"]))
    )
    print(
        f"  {'snapshot':<24} {snapshot.manifest_sha256}\n"
        f"  {'window':<24} [{is_start}, {IS_END})  "
        f"{boundaries.nunique()} reconstitutions, {membership_rows} membership rows\n"
        f"  {'distinct members':<24} {snapshot.membership['symbol'].nunique()}\n"
        f"  {'decision boundaries':<24} {grid_size}\n"
        f"  {'folds':<24} "
        + ", ".join(
            f"{name} [{start.date()}, {end.date()})"
            for name, start, end in is_folds(is_start, IS_END)
        )
        + "\n"
    )

    run, _ = _stage("run_candidate", run_reference, snapshot, raw, is_start=is_start)
    scored = _stage(
        "assemble_scored_metrics",
        assemble_scored_metrics,
        run,
        stage="in_sample",
        is_start=is_start,
        is_end=IS_END,
    )
    verdict = _stage("adjudicate_candidate", adjudicate, scored, raw)

    sleeves = f"{REFERENCE_SLEEVE}x{REFERENCE_SLEEVE}"
    print(f"\n{'-' * 78}\nreference metrics (in-sample, {sleeves} weekly)\n{'-' * 78}")
    for key in sorted(scored):
        print(f"  {key:<44} {scored[key]:>14.6f}")
    print(f"\n{'-' * 78}\nhard floors\n{'-' * 78}")
    for name, passed in sorted(verdict.gates.checks.items()):
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(
        f"\n  verdict: {'QUALIFIED' if verdict.qualified else 'NOT QUALIFIED'}"
        f"  score={verdict.score if verdict.score is not None else 'n/a'}"
    )
    print(
        "\n  A NOT QUALIFIED reference book is an ordinary outcome: the load exists to exercise\n"
        "  the pipeline, not to pass the floors. Readiness is about the stages, not the verdict."
    )

    if arguments.json:
        payload = {
            "manifest_sha256": snapshot.manifest_sha256,
            "is_start": str(is_start),
            "is_end": str(IS_END),
            "decision_boundaries": grid_size,
            "metrics": {key: scored[key] for key in sorted(scored)},
            "gates": dict(sorted(verdict.gates.checks.items())),
            "qualified": verdict.qualified,
        }
        Path(arguments.json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"\nREADINESS PASSED: every stage completed. total {time.monotonic() - overall:.1f}s")


if __name__ == "__main__":
    main()
