"""Create the fifteen lane directories: brief, scouting brief, access policy, empty surfaces.

Generated from :mod:`crypto_trade.tournament.v5.lanes` rather than written by hand, so a lane cannot
receive a brief that disagrees with the roster the invariants are checked against. Hand-written
lane material is how a prior edition ended up with mandates that no longer matched the code.

Each lane gets exactly four files and four empty directories, and **nothing else**. What is absent
matters more than what is present: no peer material, no prior-edition artifact, no market data, no
repository history. The materialised workspace at phase time copies from here, so anything that
should never reach a lane must never be written here.

Usage::

    uv run python scripts/top40_v5_scaffold_lanes.py --check    # verify without writing
    uv run python scripts/top40_v5_scaffold_lanes.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crypto_trade.tournament.v5 import lanes, seeds
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

LANE_DIRECTORIES = ("candidates", "outbox", "work", "feedback", "scouting")

SCOUTING_BRIEF = """# Phase S — scouting

You have the public internet and **no market data**. No repository, no prior tournament artifact,
no other team's work, and no evaluation surface. This phase exists so you can research the
professional literature on your assigned family rather than reinvent it from nothing.

Produce `scouting/THESIS.md` containing:

1. **A mechanism thesis.** What is the economic source of the return, and why should the premium
   persist specifically in Binance USD-M perpetual futures? Name who is on the other side.
2. **At least three public citations**, each with an access timestamp. Papers, practitioner
   research, exchange documentation. Say what each one establishes.
3. **A falsifier**, stated on visible development data, that you commit to before seeing a result.
4. **A declared parameter surface.** Every knob you intend to search, and its range.

That fourth item matters more than it looks. It makes your search space countable, which is what
the trial count in a deflated Sharpe is supposed to mean. This is the first edition where that
number will mean something.

This thesis is hash-bound and sealed before any market data is mounted. You cannot revise it after
seeing a result -- that is the point of preregistering it.

## What this dataset cannot support

Do not spend a trial discovering these. There is no open interest, no liquidation feed, no order
book, no spot price and therefore no true basis, no cross-venue data, no options, nothing on-chain,
and nothing below 8h resolution. Funding, OHLCV, quote volume, trade count and taker-buy volumes
are what exist.
"""

RESEARCH_BRIEF = """# Research phases

Market data is mounted. The network is gone -- you have no search, no fetch and no shell.

Your working loop is: form a hypothesis, write `outbox/candidate.py` and `outbox/RATIONALE.md`,
and receive back a standardised metric packet for the **visible** development window. Some days of
that window are sealed and you will never see them; they carry the generalization bar.

## The contract

`candidate.py` must define `build_strategy()` returning an object with:

    target_weights(context, *, seed) -> Mapping[str, float] | None

Return a mapping of symbol to signed unlevered weight, or `None` to hold current quantities. An
empty mapping requests a flat book. Only point-in-time members are tradable. The evaluator enforces
membership exits, delisting exits, participation limits and exposure caps regardless of what you
return.

## What is fixed

- Gross <= 1.0, |net| <= 0.25, per-symbol <= 0.10, participation <= 0.1% of prior-24h quote volume.
- Costs are charged at 1x, 2x and 3x, independently evaluated. A book that only survives at 1x is
  not a book.
- **You may not target volatility.** A common organizer-owned ex-ante risk unit scales every lane
  to the same ex-ante volatility, so the field is compared at equal risk.
- No network, no subprocess, no filesystem, no `eval`/`exec`, no RNG, and no state that persists
  across decisions other than what you fit from the past-only rows you are streamed.

## What ends a trial

Every material trial is journalled before market data opens, and a rejected candidate consumes its
slot. An **evaluator fault does not** -- if the organizer's code breaks, you are refunded.
"""


def _access_policy(lane: lanes.Lane) -> dict[str, object]:
    return {
        "team_id": lane.team_id,
        "family": lane.family,
        "readable": {
            "scouting": ["ACCESS-POLICY.json", "TEAM-BRIEF.md", "SCOUTING-BRIEF.md", "scouting/"],
            "research": ["the whole lane", "the team kit"],
        },
        "writable": {"scouting": ["scouting/"], "research": ["candidates/", "outbox/", "work/"]},
        "network": {"scouting": True, "research": False},
        "forbidden": [
            "any other lane",
            "any prior edition of this tournament",
            "the repository and its history",
            "the market snapshot outside the mounted decision context",
            "the sealed development blocks",
            "the historical window",
        ],
        "rationed_signal": lane.rations,
        "mandated_directional": lane.directional,
        "seed": lane.seed,
    }


def scaffold(root: Path, *, check: bool) -> list[str]:
    problems: list[str] = []
    seeds.assert_every_lane_has_a_seed([entry.seed for entry in lanes.LANES])
    lanes.assert_lane_invariants()

    for lane in lanes.LANES:
        lane_root = root / "teams" / lane.team_id
        files = {
            "TEAM-BRIEF.md": lane.brief(),
            "SCOUTING-BRIEF.md": SCOUTING_BRIEF,
            "RESEARCH-BRIEF.md": RESEARCH_BRIEF,
            "ACCESS-POLICY.json": json.dumps(_access_policy(lane), indent=2, sort_keys=True) + "\n",
        }
        if check:
            for name, expected in files.items():
                path = lane_root / name
                if not path.is_file():
                    problems.append(f"{lane.team_id}: missing {name}")
                elif path.read_text(encoding="utf-8") != expected:
                    problems.append(f"{lane.team_id}: {name} differs from the roster")
            continue

        lane_root.mkdir(parents=True, exist_ok=True)
        for name in LANE_DIRECTORIES:
            (lane_root / name).mkdir(exist_ok=True)
            keep = lane_root / name / ".gitkeep"
            if not keep.exists():
                keep.write_text("", encoding="utf-8")
        for name, body in files.items():
            (lane_root / name).write_text(body, encoding="utf-8")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--root", default=TOP40_V5_LAYOUT.tournament_root)
    arguments = parser.parse_args()

    root = Path(arguments.root)
    problems = scaffold(root, check=arguments.check)

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1

    action = "verified" if arguments.check else "scaffolded"
    print(f"{action} {len(lanes.LANES)} lanes under {root}/teams/")
    if not arguments.check:
        for lane in lanes.LANES:
            marks = []
            if lane.rations:
                marks.append(f"rations {lane.rations}")
            if lane.directional:
                marks.append("directional")
            suffix = f"  [{', '.join(marks)}]" if marks else ""
            print(f"  {lane.team_id}  {lane.title}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
