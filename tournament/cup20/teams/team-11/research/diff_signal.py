"""Diff the frozen strategy's emitted weights against the offline pipeline's, boundary by
boundary, so any disagreement is localised rather than guessed at."""

from __future__ import annotations

import importlib.util
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402
from eda_neutralise import residualise  # noqa: E402
from sweep_focus import desk_closed_mask, power_book  # noqa: E402

from crypto_trade.cup20.runner import decision_grid  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402
from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
MONDAY_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")
CANDIDATE = "tournament/cup20/teams/team-11/candidates/desk-closed-share/strategy.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("team11_candidate", CANDIDATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    aw = module.ACTIVITY_WINDOW_BARS
    vw = module.VOLATILITY_WINDOW_BARS
    phase = module.REBALANCE_PHASE_BARS
    cadence = module.REBALANCE_CADENCE_BARS
    power = module.WEIGHT_POWER
    print(f"frozen constants: aw={aw} vw={vw} phase={phase} cadence={cadence} power={power}")

    p = panel_mod.load()
    snapshot = load_snapshot("data/cup20/is")
    is_start = resolve_is_start(snapshot.membership, target_size=20)
    grid = decision_grid(is_start, IS_END, interval_hours=8)
    start_idx = int(np.where(p.times == is_start)[0][0])

    targets = generate_targets(
        module.build_strategy(), snapshot.bars, snapshot.funding, snapshot.membership,
        grid, seed=11, interval_hours=8,
    )
    reb_s = targets[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool)
    W_s = np.zeros((len(grid), len(p.symbols)))
    for c in [c for c in targets.columns if c != REBALANCE_INSTRUCTION_COLUMN]:
        W_s[:, p.symbols.index(c)] = targets[c].to_numpy(dtype=float)

    import signals as S
    sig_rank, el = S.build(p, start_idx, activity_window=aw, volatility_window=vw, quantity='volume')
    times = p.times[start_idx:]
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)
    W_o = S.power_book(sig_rank, power)
    reb_o = ((bar_index - phase) % cadence) == 0
    share_rank = sig_rank
    rv_rank = sig_rank

    print(f"rebalance rows: strategy {reb_s.sum()}  offline {reb_o.sum()}  "
          f"agree {(reb_s == reb_o).all()}")
    both = reb_s & reb_o
    diff = np.abs(W_s - W_o).sum(1)
    print(f"mean |weight diff| per rebalance row: {diff[both].mean():.6f}")
    print(f"rows with diff > 1e-9: {(diff[both] > 1e-9).sum()} of {both.sum()}")
    idx = np.where(both & (diff > 1e-9))[0]
    if len(idx):
        first = idx[0]
        print(f"\nfirst disagreement at {times[first]} (row {first}):")
        order = np.argsort(-np.abs(W_s[first] - W_o[first]))[:8]
        for j in order:
            print(f"  {p.symbols[j]:<12} strategy {W_s[first, j]:>+9.5f}  "
                  f"offline {W_o[first, j]:>+9.5f}  elig={el[first, j]} "
                  f"share_rank={share_rank[first, j]:>+7.4f} rv_rank={rv_rank[first, j]:>+7.4f}")
        print(f"\ndisagreement rows by year: "
              f"{pd.Series(times[idx]).dt.year.value_counts().sort_index().to_dict()}")
        agree_rows = np.where(both & (diff <= 1e-9))[0]
        print(f"agreeing rows: {len(agree_rows)}; "
              f"first {times[agree_rows[0]] if len(agree_rows) else None}")


if __name__ == "__main__":
    main()
