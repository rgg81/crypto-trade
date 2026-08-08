"""EDA 14 - parity check: the frozen strategy must emit exactly the book the research sim scored.

Uses the organiser's own generate_targets so the context construction is theirs, not mine, then
compares the emitted weights against the research sim's weight matrix at every boundary.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cl, hi, index, lo, mask  # noqa: E402
from eda08_controls import sleeve_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402

from crypto_trade.cup20.runner import decision_grid  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402
from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

root = Path("tournament/cup20/teams/team-02/candidates/channel-position-ls")
spec = importlib.util.spec_from_file_location("team02_strategy", root / "strategy.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

snapshot = load_snapshot("data/cup20/is")
is_start = resolve_is_start(snapshot.membership, target_size=20)
grid = decision_grid(is_start, pd.Timestamp(snapshot.bars.open_time.max()) + pd.Timedelta(hours=8))
print("is_start", is_start, "boundaries", len(grid))

targets = generate_targets(
    module.build_strategy(), snapshot.bars, snapshot.funding, snapshot.membership,
    grid, seed=20260807,
)
reb = targets[REBALANCE_INSTRUCTION_COLUMN]
print("explicit rebalance rows:", int(reb.sum()), "of", len(targets))
rows = targets[reb].drop(columns=[REBALANCE_INSTRUCTION_COLUMN])
print("names per rebalance: min", int(rows.ne(0).sum(axis=1).min()),
      "max", int(rows.ne(0).sum(axis=1).max()))
print("gross per rebalance:", float(rows.abs().sum(axis=1).min()),
      float(rows.abs().sum(axis=1).max()))
print("net per rebalance:", float(rows.sum(axis=1).abs().max()))

u = channel_position(hi, lo, cl, module.FORMATION_BARS)
sim_w = sleeve_weights(u, 1 - u, module.SLEEVE_SIZE)
bar_index = pd.Index((index.asi8 // (8 * 3600 * 10**9)).astype(np.int64))
sim_reb = pd.Series((bar_index % module.REBALANCE_BARS)
                    == ((module.PHASE_OFFSET - 1) % module.REBALANCE_BARS), index=index)
# The research sim stamps a decision on the bar it last SAW (open_time t, close t+8h) and fills at
# open[t+8h]; the organiser stamps the same decision at the fill boundary itself. Same causal
# structure, index shifted by exactly one bar -- so parity is checked across that shift.
shift = pd.Timedelta(hours=8)
sim_rows = index[sim_reb.to_numpy()] + shift
common = rows.index.intersection(sim_rows)
print("rebalance boundary agreement:", len(common), "of", int(reb.sum()))
a = rows.reindex(index=common).reindex(columns=sim_w.columns).fillna(0.0)
b = (sim_w.reindex(index=common - shift) * 1.0).fillna(0.0)
b.index = common
b = b / b.abs().sum(axis=1).replace(0, 1).values[:, None] * a.abs().sum(axis=1).values[:, None]
diff = (a - b).abs().to_numpy()
print("max |weight difference| vs research sim:", float(np.nanmax(diff)))
bad = np.argwhere(diff > 1e-9)
print("boundaries with any disagreement:", len(set(bad[:, 0].tolist())))
