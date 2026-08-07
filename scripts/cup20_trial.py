"""Record one material trial in the organiser's research journal. Run this BEFORE you evaluate.

    uv run python scripts/cup20_trial.py --team team-01 --candidate baseline
        --purpose "does 30-bar own-price momentum survive 7.5 bps a side"
        --seed 20240101 --roles long,short

Charter section 7.1: every organiser-recognised evaluation is journaled **before** market data are
opened, and acceptance consumes the trial even if the run later crashes or you abandon it. The
journal is organiser-owned and append-only; this command is the append. Teams never edit
``tournament/cup20/research-journal.jsonl`` and never run any other tool against it.

It prints the sequence number the record was given. That number is what your research certificate
cites, and it is what ``scripts/cup20_evaluate.py`` looks for before it will run anything.

``--kind neighbourhood`` additionally validates ``neighbourhood.json`` in full -- every section 6
rule and the section 6.1 coordinate rule against the frozen source -- **before** appending. A trial
is spent at acceptance and never refunded, so a declaration that could not be swept has to be
refused at the append or it costs a trial to discover.

Exit codes: 0 recorded, 2 refused (budget exhausted, or a bad declaration), 1 anything else.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.cup20.sweep import load_neighbourhood
from crypto_trade.cup20.trials import (
    TRIAL_KINDS,
    MaterialTrial,
    TrialBudgetExhaustedError,
    candidate_source_digest,
    cost_model,
    record_trial,
    risk_policy_digest,
)
from crypto_trade.cup20.variants import (
    CoordinateSubstitutionError,
    VariantIntegrityError,
)

CONFIG_PATH = Path("tournament/cup20/config.toml")


def parse_parameters(entries: list[str]) -> dict[str, Any]:
    """``--parameter formation_bars=30`` pairs, each value parsed as JSON where it parses.

    JSON first so ``30`` records as a number and ``"fast"`` as a string, and a bare word falls
    back to a string rather than failing -- the point of this field is that the journal records
    what you varied, in a form a later reader can compare, not that it enforces a schema on your
    parameter names.
    """
    parameters: dict[str, Any] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(f"--parameter expects name=value, got {entry!r}")
        name, _, raw_value = entry.partition("=")
        name = name.strip()
        if not name:
            raise SystemExit(f"--parameter expects a non-empty name, got {entry!r}")
        if name in parameters:
            raise SystemExit(f"--parameter {name} was given more than once")
        try:
            parameters[name] = json.loads(raw_value)
        except json.JSONDecodeError:
            parameters[name] = raw_value
    return parameters


def build_trial(arguments: argparse.Namespace) -> tuple[MaterialTrial, dict[str, Any]]:
    """Assemble the material tuple from the frozen authorities plus what the team declared."""
    config = load_config(arguments.config)
    raw = config.raw
    candidate_root = Path(arguments.team_root) / arguments.team / "candidates" / arguments.candidate
    # A neighbourhood trial is a claim about a declared neighbourhood, so it is checked BEFORE the
    # append rather than by the runner afterwards. Charter section 7.1 spends the trial at
    # acceptance and never refunds it, so a declaration that cannot be swept -- too few points, a
    # duplicate, no material variation, a coordinate that is not a module-level constant, a nominee
    # that disagrees with the frozen source, a literal the sweep cannot rewrite -- has to cost
    # nothing, and the only place it can cost nothing is here.
    if arguments.kind == "neighbourhood":
        load_neighbourhood(candidate_root)
    snapshot = load_snapshot(raw["data"]["is_root"])
    is_start = resolve_is_start(
        snapshot.membership, target_size=int(raw["universe"]["target_size"])
    )
    trial = MaterialTrial(
        team_id=arguments.team,
        candidate_id=arguments.candidate,
        purpose=arguments.purpose,
        kind=arguments.kind,
        source_sha256=candidate_source_digest(candidate_root),
        config_sha256=config.sha256,
        risk_policy_sha256=risk_policy_digest(candidate_root),
        snapshot_sha256=snapshot.manifest_sha256,
        seed=int(arguments.seed),
        window_start=str(is_start),
        window_end=str(IS_END),
        cost_model=cost_model(raw["execution"]),
        parameters=parse_parameters(arguments.parameter),
        declared_roles=tuple(role.strip() for role in arguments.roles.split(",") if role.strip()),
    )
    return trial, raw


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record one CUP-20 material trial before evaluating anything",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--team", required=True, help="your team id, e.g. team-01")
    parser.add_argument("--candidate", required=True, help="the candidate directory name")
    parser.add_argument(
        "--purpose",
        required=True,
        help="the question this trial answers, in one sentence; it goes in the journal",
    )
    parser.add_argument("--seed", required=True, type=int, help="the evaluation seed")
    parser.add_argument(
        "--roles",
        required=True,
        help="the sides you claim this book trades: long, short, or long,short. "
        "Declared before the numbers exist, and checked against the sides it actually traded.",
    )
    parser.add_argument(
        "--kind",
        default="point",
        choices=list(TRIAL_KINDS),
        help="point (one evaluation), neighbourhood (the declared sweep, one trial), or "
        "falsification (sign inversion + placebo, one trial)",
    )
    parser.add_argument(
        "--parameter",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="a material parameter of this trial; repeatable",
    )
    parser.add_argument("--config", default=str(CONFIG_PATH), help=argparse.SUPPRESS)
    parser.add_argument("--team-root", default="tournament/cup20/teams", help=argparse.SUPPRESS)
    parser.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    arguments = parser.parse_args()

    try:
        trial, raw = build_trial(arguments)
    except (
        ValueError,
        FileNotFoundError,
        CoordinateSubstitutionError,
        VariantIntegrityError,
    ) as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        print("Nothing was journaled.", file=sys.stderr)
        raise SystemExit(2) from failure

    journal_path = arguments.journal or raw["paths"]["research_journal"]
    budget = int(raw["research"]["trial_budget"])
    try:
        accepted = record_trial(journal_path, trial, budget=budget)
    except TrialBudgetExhaustedError as failure:
        print(f"REFUSED: {failure}", file=sys.stderr)
        raise SystemExit(2) from failure

    print(f"trial accepted  sequence #{accepted.sequence}")
    print(f"  team          {accepted.team_id}")
    print(f"  candidate     {trial.candidate_id}  ({trial.kind})")
    print(f"  purpose       {trial.purpose}")
    print(f"  source        {trial.source_sha256}")
    print(f"  fingerprint   {trial.fingerprint()}")
    print(f"  record        {accepted.record_sha256}")
    print(
        f"  budget        {accepted.spent} of {accepted.budget} spent, "
        f"{accepted.remaining} remaining"
    )
    print(f"  journal       {journal_path}")
    print()
    print("Now evaluate it:")
    print(
        f"  uv run python scripts/cup20_evaluate.py --team {trial.team_id} "
        f"--candidate {trial.candidate_id}"
    )


if __name__ == "__main__":
    main()
