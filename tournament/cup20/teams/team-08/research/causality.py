"""Strictly-before verification, by corruption rather than by assertion.

A change-based signal reaches back two observations, so it is more exposed to a boundary
leak than a level signal is, and the specific hazard named in the mandate is a settlement
landing exactly ON the decision timestamp. This tests both, on the real snapshot, by
corrupting rows and checking which emitted weights move:

  test 1  every funding row at or after an interior instant T0 is replaced with noise.
          Every decision at or before T0 must emit byte-identical weights.
  test 2  ONLY the funding rows whose funding_time is exactly T0 are corrupted. The
          decision at T0 must be unchanged (the settlement is not the strategy's to see);
          the decision at T0 + 8h must change (otherwise the strategy is ignoring data it
          IS entitled to, which would be a different bug).
  test 3  every BAR at or after T0 is corrupted. No decision anywhere may change, because
          the strategy reads no bar at all.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from replay import load_candidate  # noqa: E402

from crypto_trade.cup20.runner import decision_grid  # noqa: E402
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start  # noqa: E402
from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")


def targets_for(module, snapshot, grid, funding=None, bars=None):
    return generate_targets(
        module.build_strategy(),
        snapshot.bars if bars is None else bars,
        snapshot.funding if funding is None else funding,
        snapshot.membership,
        grid,
        seed=20200817,
        interval_hours=8,
    )


def main():
    candidate = sys.argv[1]
    t0 = pd.Timestamp(sys.argv[2] if len(sys.argv) > 2 else "2023-05-10T08:00:00Z")
    module = load_candidate(candidate)
    snapshot = load_snapshot("data/cup20/is")
    is_start = resolve_is_start(snapshot.membership)
    # A one-year grid around T0 keeps the test to a few minutes without weakening it.
    grid = decision_grid(t0 - pd.Timedelta(days=200), t0 + pd.Timedelta(days=30))
    grid = tuple(t for t in grid if t >= is_start)
    rng = np.random.default_rng(7)

    base = targets_for(module, snapshot, grid)

    def compare(other, label, upto=None, expect_same=True):
        idx = base.index if upto is None else base.index[base.index <= upto]
        a = base.loc[idx].fillna(0.0)
        b = other.reindex(columns=base.columns).loc[idx].fillna(0.0)
        same = a.equals(b)
        status = "PASS" if same == expect_same else "FAIL"
        print(f"  [{status}] {label}: identical={same} (expected {expect_same}) over {len(idx)} decisions")
        return same == expect_same

    ok = True
    # test 1 -- everything at or after T0
    f1 = snapshot.funding.copy()
    m1 = f1["funding_time"] >= t0
    f1.loc[m1, "funding_rate"] = rng.normal(0.02, 0.02, int(m1.sum()))
    ok &= compare(targets_for(module, snapshot, grid, funding=f1),
                  "funding corrupted at/after T0, decisions up to T0", upto=t0, expect_same=True)
    ok &= compare(targets_for(module, snapshot, grid, funding=f1),
                  "same corruption, decisions after T0 (must differ)", expect_same=False)

    # test 2 -- only the settlement landing exactly on T0.
    # ``settlement_time`` is the exact 8h grid instant; ``funding_time`` is the exchange's raw
    # event stamp and is a few milliseconds later on about half the rows, so selecting on
    # funding_time would silently test nothing on the other half.
    f2 = snapshot.funding.copy()
    m2 = f2["settlement_time"] == t0
    print(f"  (rows stamped exactly at T0: {int(m2.sum())})")
    f2.loc[m2, "funding_rate"] = rng.normal(0.05, 0.02, int(m2.sum()))
    t2 = targets_for(module, snapshot, grid, funding=f2)
    ok &= compare(t2, "T0-stamped settlement corrupted, decision AT T0", upto=t0, expect_same=True)
    ok &= compare(t2, "T0-stamped settlement corrupted, later decisions (must differ)",
                  expect_same=False)

    # test 3 -- bars
    b3 = snapshot.bars.copy()
    m3 = b3["open_time"] >= t0 - pd.Timedelta(days=400)
    for column in ("open", "high", "low", "close"):
        b3.loc[m3, column] = b3.loc[m3, column] * rng.uniform(0.5, 1.5, int(m3.sum()))
    ok &= compare(targets_for(module, snapshot, grid, bars=b3),
                  "bars corrupted throughout (strategy reads no bar)", expect_same=True)

    print("ALL CAUSALITY CHECKS PASS" if ok else "CAUSALITY CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
