"""End-to-end check that the frozen strategy.py produces exactly the book the offline sweep
scored, by streaming it through the organiser's own ``generate_targets`` and then evaluating the
resulting target frame in the offline replica.

Costs no trial: ``generate_targets`` only calls the strategy, it produces no metric.
"""

from __future__ import annotations

import importlib.util
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import fastsim  # noqa: E402
import panel as panel_mod  # noqa: E402
from sweep import fold_stats, summarise  # noqa: E402

from crypto_trade.cup20.runner import decision_grid  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402
from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
CANDIDATE = "tournament/cup20/teams/team-11/candidates/desk-closed-share/strategy.py"


def load_strategy(path: str):
    spec = importlib.util.spec_from_file_location("team11_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else CANDIDATE
    t0 = time.time()
    module = load_strategy(path)
    p = panel_mod.load()
    snapshot = load_snapshot("data/cup20/is")
    is_start = resolve_is_start(snapshot.membership, target_size=20)
    grid = decision_grid(is_start, IS_END, interval_hours=8)
    start_idx = int(np.where(p.times == is_start)[0][0])

    targets = generate_targets(
        module.build_strategy(), snapshot.bars, snapshot.funding, snapshot.membership,
        grid, seed=11, interval_hours=8,
    )
    print(f"generate_targets: {time.time() - t0:.0f}s   rows={len(targets)}")
    reb = targets[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool)
    weights = np.zeros((len(grid), len(p.symbols)))
    cols = [c for c in targets.columns if c != REBALANCE_INSTRUCTION_COLUMN]
    for c in cols:
        weights[:, p.symbols.index(c)] = targets[c].to_numpy(dtype=float)

    print(f"rebalance boundaries: {int(reb.sum())} of {len(grid)}")
    nz = (np.abs(weights) > 0).sum(1)
    print(f"names per rebalance: mean {nz[reb].mean():.2f}  min {nz[reb].min()}  "
          f"max {nz[reb].max()}")
    print(f"gross per rebalance: mean {np.abs(weights[reb]).sum(1).mean():.4f}")
    print(f"net   per rebalance: mean {weights[reb].sum(1).mean():+.2e}")

    res = fastsim.full_evaluate(p, start_idx, weights, reb)
    row = summarise(res, "frozen strategy.py")
    row.update(fold_stats(res, p.times[start_idx:]))
    for k, v in row.items():
        print(f"  {k:<16} {v}")


if __name__ == "__main__":
    main()
