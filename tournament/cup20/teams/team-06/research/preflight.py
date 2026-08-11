"""Team 06 -- run the FROZEN strategy through the organiser's own target generator, then score it
with the offline lab.

This is not a scorer and its numbers are never reported as scores. What it buys is that the signal
under test is byte-identical to the frozen candidate's -- ``generate_targets`` is the organiser's
own past-only streamer -- so a trial is never spent discovering that the lab and the candidate
disagreed about the signal. Only the evaluation half is approximate.

    uv run python .../preflight.py <candidate-dir> [KEY=VALUE ...]

KEY=VALUE overrides rewrite the module-level constants after import, which is exactly what the
neighbourhood sweep does to the frozen file, so a coordinate can be explored offline for free.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from lab import evaluate, line  # noqa: E402
from signals import load_panel  # noqa: E402

from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

IS_START = pd.Timestamp("2020-08-17", tz="UTC")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")


def load_module(candidate: str):
    path = Path("tournament/cup20/teams/team-06/candidates") / candidate / "strategy.py"
    spec = importlib.util.spec_from_file_location(f"team06_{candidate.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    candidate = sys.argv[1]
    overrides = {}
    for entry in sys.argv[2:]:
        name, _, raw = entry.partition("=")
        overrides[name] = float(raw) if "." in raw else int(raw)
    module = load_module(candidate)
    for name, value in overrides.items():
        if not hasattr(module, name):
            raise SystemExit(f"{candidate}/strategy.py has no module-level {name}")
        setattr(module, name, value)

    bars = pd.read_parquet("data/cup20/is/bars.parquet")
    funding_raw = pd.read_parquet("data/cup20/is/funding.parquet")
    membership = pd.read_parquet("data/cup20/is/membership.parquet")
    grid = pd.date_range(IS_START, IS_END, freq="8h", inclusive="left")

    targets = generate_targets(
        module.build_strategy(), bars, funding_raw, membership, list(grid), seed=20200817
    )
    panel = load_panel()
    acted = targets[REBALANCE_INSTRUCTION_COLUMN].astype(bool).to_numpy()
    weights = (
        targets.drop(columns=[REBALANCE_INSTRUCTION_COLUMN])
        .reindex(columns=panel["opens"].columns)
        .astype(float)
    )
    filled = weights.fillna(0.0).to_numpy().copy()
    filled[~acted, :] = float("nan")
    weights = pd.DataFrame(filled, index=weights.index, columns=weights.columns)
    gross = weights.abs().sum(axis=1)
    weights = weights.div(gross.where(gross > 0), axis=0)

    metrics = evaluate(weights, panel["opens"], panel["funding"])
    tag = f"{candidate} " + " ".join(f"{k}={v}" for k, v in overrides.items())
    print(line(tag[:44], metrics), flush=True)


if __name__ == "__main__":
    main()
