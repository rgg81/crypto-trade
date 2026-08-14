"""Phase 3: the finalists' single holdout observation.

Each finalist gets **exactly one** observation, and it is a full declared-neighbourhood sweep over
the sealed window -- not the nominated point. The reason is section 7.2's and it does not weaken out
of sample: a nominated point is the maximum of a noisy surface, and the median over a pre-declared
neighbourhood is the estimate that does not reward having found the spike.

Why this is a separate script from ``cup20_evaluate.py``. That one is hard-wired to the in-sample
stage in four places -- ``STAGE_IN_SAMPLE``, ``is_folds``, ``IS_END`` in the decision grid, and
``adjudicate_candidate``. Parameterising it would put a switch on the scorer whose wrong setting
silently produces a well-formed vector for the wrong four years, and the whole point of
``_require_assembled_vector`` is that such a vector must be impossible to hand to the wrong
adjudicator. A separate entry point that can only ever mean "holdout" is the safer shape.

The observation is scored under amendment A7: section 8's conditions are evaluated and reported,
a miss costs points through ``holdout_compliance_factor`` rather than eliminating a finalist, and
the winner is the highest score.

Run once, after ``cup20_freeze_selection.py`` and after the holdout has been restored:

    uv run python scripts/cup20_holdout_observe.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from crypto_trade.cup20.adjudication import adjudicate_holdout_candidate  # noqa: E402
from crypto_trade.cup20.config import SEALED_END, SEALED_START, load_config  # noqa: E402
from crypto_trade.cup20.harness import (  # noqa: E402
    load_candidate_risk_policy,
    load_team_module,
    strategy_from_module,
)
from crypto_trade.cup20.journal import append_record, verify_chain  # noqa: E402
from crypto_trade.cup20.metrics import holdout_folds  # noqa: E402
from crypto_trade.cup20.runner import decision_grid, evaluator_config, run_candidate  # noqa: E402
from crypto_trade.cup20.scored_metrics import (  # noqa: E402
    STAGE_HOLDOUT,
    assemble_scored_metrics,
    neighbourhood_median,
)
from crypto_trade.cup20.snapshot import load_snapshot  # noqa: E402
from crypto_trade.cup20.sweep import load_neighbourhood, materialise_neighbourhood  # noqa: E402
from crypto_trade.cup20.trials import (  # noqa: E402
    ENTRYPOINT,
    candidate_source_digest,
)

OBSERVATION_EVENT = "holdout_observation"


def _observe_point(root: pathlib.Path, snapshot, raw, *, seed: int, grid, folds):
    """One neighbourhood point over the sealed window, through the organiser's own runner."""
    module = load_team_module(root)
    strategy = strategy_from_module(module, entry=root / ENTRYPOINT)
    policy = load_candidate_risk_policy(root)
    run = run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=seed,
        config=evaluator_config(raw["execution"]),
        risk_unit=raw["risk_unit"],
        cost_multipliers=tuple(int(v) for v in raw["execution"]["cost_multipliers"]),
        risk_policy=policy,
    )
    return assemble_scored_metrics(
        run, stage=STAGE_HOLDOUT, is_start=SEALED_START, is_end=SEALED_END, folds=folds
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="tournament/cup20/config.toml")
    parser.add_argument("--selection", default="tournament/cup20/selection-freeze.json")
    parser.add_argument("--out", default="tournament/cup20/holdout-observations.json")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()

    raw = load_config(arguments.config).raw
    freeze = json.loads(pathlib.Path(arguments.selection).read_text())
    journal_path = pathlib.Path(raw["paths"]["research_journal"])

    out = pathlib.Path(arguments.out)
    if out.exists():
        raise SystemExit(
            f"REFUSED: {out} already exists. Each finalist gets exactly ONE observation and it has "
            "already been taken; a second would be the second look the whole design forbids."
        )

    sealed_root = pathlib.Path(raw["data"]["sealed_root"])
    if not sealed_root.is_dir():
        raise SystemExit(f"REFUSED: the sealed snapshot is not at {sealed_root}; restore it first")

    snapshot = load_snapshot(sealed_root)
    grid = decision_grid(
        SEALED_START, SEALED_END, interval_hours=evaluator_config(raw["execution"]).interval_hours
    )
    folds = tuple(holdout_folds(SEALED_START, SEALED_END))
    print(
        f"sealed window [{SEALED_START}, {SEALED_END}) -- {len(grid)} decisions, {len(folds)} folds"
    )
    print(f"snapshot manifest {snapshot.manifest_sha256}\n")

    teams_root = pathlib.Path("tournament/cup20/teams")
    results = []
    for finalist in sorted(freeze["finalists"], key=lambda f: f["rank"]):
        team, candidate = finalist["team_id"], finalist["candidate_id"]
        candidate_root = teams_root / team / "candidates" / candidate

        # candidate_source_digest, not a hash of strategy.py alone: the selection freeze records
        # the BUNDLE digest over the whole candidate directory, and comparing a different
        # definition here reads as tampering when nothing has changed. It did exactly that on the
        # first run of this script.
        digest = candidate_source_digest(candidate_root)
        if digest != finalist["source_sha256"]:
            raise SystemExit(
                f"REFUSED: {team}/{candidate} source is {digest}, not the "
                f"{finalist['source_sha256']} frozen at selection. The nomination changed after "
                "the field closed."
            )

        declaration = load_neighbourhood(candidate_root)
        sweep_root = pathlib.Path(tempfile.mkdtemp(prefix=f"cup20-holdout-{team}-"))
        started = time.monotonic()
        try:
            points = materialise_neighbourhood(candidate_root, sweep_root, declaration)
            vectors = []
            for point in points:
                vectors.append(
                    _observe_point(
                        pathlib.Path(point.root),
                        snapshot,
                        raw,
                        seed=arguments.seed,
                        grid=grid,
                        folds=folds,
                    )
                )
                print(f"  {team}/{candidate}: point {len(vectors)}/{len(points)}", flush=True)
        finally:
            shutil.rmtree(sweep_root, ignore_errors=True)

        median = neighbourhood_median(vectors)
        nominee_2x_return = float(vectors[0]["double_cost_annualized_return"])
        verdict = adjudicate_holdout_candidate(
            median,
            team_id=team,
            candidate_id=candidate,
            holdout=raw["holdout"],
            trial_adjusted_confidence=1.0,
            nominated_point_double_cost_return=nominee_2x_return,
        )
        elapsed = time.monotonic() - started
        results.append(
            {
                "in_sample_rank": finalist["rank"],
                "team_id": team,
                "candidate_id": candidate,
                "in_sample_G": finalist["in_sample_G"],
                "holdout_G": verdict.score,
                "points": len(vectors),
                "section_8_conditions": dict(verdict.gates.checks),
                "section_8_misses": list(verdict.failures),
                "median": {k: float(median[k]) for k in sorted(median)},
                "nominated_point_double_cost_return": nominee_2x_return,
                "seconds": elapsed,
            }
        )
        print(
            f"  {team}/{candidate}: holdout G = {verdict.score:.3f} "
            f"({len(verdict.failures)} section 8 miss(es)) in {elapsed:.0f}s\n",
            flush=True,
        )

    results.sort(key=lambda r: r["holdout_G"], reverse=True)
    for position, row in enumerate(results, 1):
        row["holdout_rank"] = position
    payload = {
        "schema_version": "cup20-holdout-observations-v1",
        "amendment": "A7 -- section 8 conditions priced, not gating; highest score wins",
        "sealed_manifest_sha256": snapshot.manifest_sha256,
        "window": {"start": str(SEALED_START), "end": str(SEALED_END)},
        "folds": [{"name": n, "start": str(a), "end": str(b)} for n, a, b in folds],
        "seed": arguments.seed,
        "observations": results,
        "winner": results[0]["team_id"],
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    append_record(
        journal_path,
        OBSERVATION_EVENT,
        {
            "observations_path": str(out),
            "observations_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "sealed_manifest_sha256": snapshot.manifest_sha256,
            "ranking": [
                {
                    k: r[k]
                    for k in (
                        "holdout_rank",
                        "team_id",
                        "candidate_id",
                        "holdout_G",
                        "in_sample_G",
                        "section_8_misses",
                    )
                }
                for r in results
            ],
            "winner": results[0]["team_id"],
        },
    )

    print("=" * 78)
    print(f"{'':2} {'team / candidate':34s} {'holdout G':>10} {'in-sample G':>12}  §8 misses")
    for row in results:
        print(
            f"{row['holdout_rank']:2d} {row['team_id'] + '/' + row['candidate_id']:34s} "
            f"{row['holdout_G']:10.3f} {row['in_sample_G']:12.2f}  "
            f"{', '.join(row['section_8_misses']) or 'none'}"
        )
    print("=" * 78)
    print(f"\nwritten to {out}; journal now {verify_chain(journal_path)} records")


if __name__ == "__main__":
    main()
