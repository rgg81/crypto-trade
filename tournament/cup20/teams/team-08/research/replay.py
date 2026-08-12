"""Run a frozen candidate's own strategy.py offline and score it with the team simulator.

Two jobs. First, it proves that the file that will be frozen produces the same book the
research sweeps were run on -- a plumbing bug found here costs nothing, and found at a
scored run costs a trial. Second, it is the best offline estimate available, because the
weights are the real ones rather than the sweep's vectorised stand-in.

The target generation is the organiser's own past-only streaming loop
(``tournament.engine_v2.generate_targets``), which produces weights and no metric; the
scoring underneath is this team's approximate simulator, and its numbers are never cited as
a score. Every scored number in the certificate comes from ``cup20_evaluate.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from sim import evaluate, summary  # noqa: E402

from crypto_trade.cup20.runner import decision_grid  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402
from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")


def load_candidate(candidate: str, team_root="tournament/cup20/teams/team-08/candidates"):
    path = Path(team_root) / candidate / "strategy.py"
    spec = importlib.util.spec_from_file_location(f"cand_{candidate.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_targets(candidate: str, seed: int = 20200817):
    snapshot = load_snapshot("data/cup20/is")
    is_start = resolve_is_start(snapshot.membership)
    grid = decision_grid(is_start, IS_END, interval_hours=8)
    module = load_candidate(candidate)
    return (
        generate_targets(
            module.build_strategy(),
            snapshot.bars,
            snapshot.funding,
            snapshot.membership,
            grid,
            seed=seed,
            interval_hours=8,
        ),
        snapshot,
    )


def to_panel_matrix(targets: pd.DataFrame, panel):
    symbols = list(panel["symbols"])
    index = {s: i for i, s in enumerate(symbols)}
    times = pd.DatetimeIndex(panel["times"], tz="UTC")
    reb = targets[REBALANCE_INSTRUCTION_COLUMN].reindex(times).fillna(False).to_numpy(bool)
    W = np.zeros((len(times), len(symbols)))
    cols = [c for c in targets.columns if c != REBALANCE_INSTRUCTION_COLUMN]
    aligned = targets[cols].reindex(times).fillna(0.0)
    for c in cols:
        if c in index:
            W[:, index[c]] = aligned[c].to_numpy(float)
    return W, reb


def main():
    from eda import load  # noqa: PLC0415

    candidate = sys.argv[1]
    panel, _, _ = load()
    targets, _ = raw_targets(candidate)
    W, reb = to_panel_matrix(targets, panel)
    print(f"{candidate}: {int(reb.sum())} rebalance boundaries of {len(reb)}")
    nonzero = (np.abs(W) > 0).sum(1)
    print(
        f"  names when trading: mean {nonzero[reb].mean():.2f}  "
        f"flat rows among rebalances: {(nonzero[reb] == 0).sum()}"
    )
    m = evaluate(panel, W, reb)
    s = summary(m)
    for k, v in s.items():
        print(f"  {k:<12} {v}")


if __name__ == "__main__":
    main()
