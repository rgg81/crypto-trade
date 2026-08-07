"""Evaluate one frozen candidate through the organiser's own pipeline and print a coaching packet.

    uv run python scripts/cup20_evaluate.py --team team-01 --candidate baseline

Three modes, and only one of them costs anything:

* ``--check``            no market data, no metric, **no trial**. Runs the blindness scan, imports
                         ``strategy.py``, calls ``build_strategy()``, parses ``risk_policy.json``
                         and -- if you have declared one -- checks your neighbourhood coordinates
                         against the frozen source. Seconds. Run it as often as you like.
* (no flag)              the scored evaluation. Requires an accepted trial of kind ``point`` for
                         exactly this candidate state. Runs the FULL in-sample window at the frozen
                         ``[execution]`` and ``[risk_unit]`` config, at 1x, 2x and 3x cost. About
                         seven minutes.
* ``--falsification``    the section 7.1 battery: exact sign inversion + gross-edge placebo.
                         Requires an accepted trial of kind ``falsification``. One trial for both
                         halves. Roughly forty minutes at the default eight placebo permutations.

There is no short-window mode, deliberately: section 7.1 makes the window part of the material
tuple, so a shorter window is a different trial whose number is comparable to nothing. ``--check``
is what exists instead, so a trial is never spent discovering a typo.

Nothing here reads, resolves or names the sealed holdout. Your data root is ``data/cup20/is/``.

Exit codes: 0 completed, 2 refused (no accepted trial, or a blindness violation), 1 anything else.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.harness import (
    BlindnessViolationError,
    CandidateLoadError,
    check_candidate,
    evaluate_point,
    run_falsification_battery,
)
from crypto_trade.cup20.journal import accepted_trial_count
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.cup20.trials import (
    TrialNotAcceptedError,
    candidate_source_digest,
    cost_model,
    resolve_accepted_trial,
    risk_policy_digest,
)

CONFIG_PATH = Path("tournament/cup20/config.toml")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate one CUP-20 candidate and print its coaching packet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--team", required=True, help="your team id, e.g. team-01")
    parser.add_argument("--candidate", required=True, help="the candidate directory name")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify the candidate loads without evaluating it; costs no trial",
    )
    mode.add_argument(
        "--falsification",
        action="store_true",
        help="run the section 7.1 battery: exact sign inversion + gross-edge placebo",
    )
    parser.add_argument(
        "--placebo-permutations",
        type=int,
        default=8,
        help="placebo books in the falsification battery (default 8)",
    )
    parser.add_argument(
        "--trial",
        type=int,
        default=None,
        help="pin a specific accepted journal sequence instead of taking the most recent match",
    )
    parser.add_argument("--output", default=None, help="also write the packet as JSON to this path")
    parser.add_argument("--config", default=str(CONFIG_PATH), help=argparse.SUPPRESS)
    parser.add_argument("--team-root", default="tournament/cup20/teams", help=argparse.SUPPRESS)
    parser.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    arguments = parser.parse_args()

    started = time.monotonic()
    config = load_config(arguments.config)
    raw = config.raw
    workspace_root = Path(arguments.team_root) / arguments.team
    candidate_root = workspace_root / "candidates" / arguments.candidate

    try:
        source_sha256 = candidate_source_digest(candidate_root)
    except FileNotFoundError as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        raise SystemExit(2) from failure

    if arguments.check:
        try:
            report = check_candidate(
                candidate_root=candidate_root,
                workspace_root=workspace_root,
                team_id=arguments.team,
                candidate_id=arguments.candidate,
                source_sha256=source_sha256,
            )
        # KeyError alongside ValueError: ``load_declaration`` subscripts ``nominee``/``points``/
        # ``coordinates`` directly, so a neighbourhood.json missing one of them raises KeyError --
        # a team's malformed declaration, which must read as a refusal rather than a traceback.
        except (BlindnessViolationError, CandidateLoadError, ValueError, KeyError) as failure:
            print(f"REFUSED: {failure}", file=sys.stderr)
            raise SystemExit(2) from failure
        print(report.render())
        if arguments.output:
            Path(arguments.output).write_text(
                json.dumps(
                    {
                        "team_id": report.team_id,
                        "candidate_id": report.candidate_id,
                        "source_sha256": report.source_sha256,
                        "risk_policy_id": report.risk_policy_id,
                        "neighbourhood_points": report.neighbourhood_points,
                        "coordinate_violations": list(report.coordinate_violations),
                        "ok": report.ok,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
        raise SystemExit(0 if report.ok else 2)

    snapshot = load_snapshot(raw["data"]["is_root"])
    is_start = resolve_is_start(
        snapshot.membership, target_size=int(raw["universe"]["target_size"])
    )
    kind = "falsification" if arguments.falsification else "point"
    try:
        recomputed = {
            "kind": kind,
            "source_sha256": source_sha256,
            "config_sha256": config.sha256,
            "risk_policy_sha256": risk_policy_digest(candidate_root),
            "snapshot_sha256": snapshot.manifest_sha256,
            "window_start": str(is_start),
            "window_end": str(IS_END),
            "cost_model": cost_model(raw["execution"]),
        }
    except FileNotFoundError as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        raise SystemExit(2) from failure

    journal_path = arguments.journal or raw["paths"]["research_journal"]
    try:
        resolution = resolve_accepted_trial(
            journal_path,
            team_id=arguments.team,
            candidate_id=arguments.candidate,
            recomputed=recomputed,
            pinned_sequence=arguments.trial,
        )
    except TrialNotAcceptedError as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        raise SystemExit(2) from failure

    spent = accepted_trial_count(journal_path, arguments.team)
    print(
        f"running under accepted trial #{resolution.sequence} "
        f"({spent} of {raw['research']['trial_budget']} trials spent); "
        f"window [{is_start}, {IS_END}) -- this takes minutes, not seconds",
        flush=True,
    )

    try:
        if arguments.falsification:
            report = run_falsification_battery(
                snapshot=snapshot,
                raw=raw,
                candidate_root=candidate_root,
                workspace_root=workspace_root,
                team_id=arguments.team,
                candidate_id=arguments.candidate,
                seed=resolution.trial.seed,
                trial_sequence=resolution.sequence,
                is_start=is_start,
                placebo_permutations=arguments.placebo_permutations,
            )
        else:
            report = evaluate_point(
                snapshot=snapshot,
                raw=raw,
                candidate_root=candidate_root,
                workspace_root=workspace_root,
                team_id=arguments.team,
                candidate_id=arguments.candidate,
                seed=resolution.trial.seed,
                declared_roles=resolution.trial.declared_roles,
                trial_sequence=resolution.sequence,
                accepted_trials=spent,
                source_sha256=source_sha256,
                is_start=is_start,
            )
    except (BlindnessViolationError, CandidateLoadError) as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        raise SystemExit(2) from failure

    print(report.render())
    if arguments.output:
        Path(arguments.output).write_text(
            json.dumps(report.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        print(f"\npacket written to {arguments.output}")
    print(f"\ncompleted in {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    main()
