"""Drive the frozen strategy through panel-derived past-only contexts and compare it, boundary by
boundary, with the offline research book. If the two disagree the offline map describes something
the frozen code does not do, and every offline number would be about the wrong strategy.

This runs my own code over my own data root. It computes no metric, journals nothing and is not an
evaluation.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from panel import DATA, Panel  # noqa: E402

CAND = HERE.parent / "candidates" / "print-size-flow" / "strategy.py"


def load_strategy(path: Path):
    spec = importlib.util.spec_from_file_location("team09_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Ctx:
    __slots__ = ("decision_time", "bars", "funding", "auxiliary", "eligible_symbols")

    def __init__(self, t, bars, elig):
        self.decision_time = t
        self.bars = bars
        self.funding = None
        self.auxiliary = {}
        self.eligible_symbols = elig


def main(limit: int | None = None) -> None:
    mod = load_strategy(CAND)
    strat = mod.build_strategy()
    p = Panel()
    bars = pd.read_parquet(DATA / "bars.parquet")
    frames = {
        s: g.reset_index(drop=True) for s, g in bars.groupby("symbol", observed=True, sort=False)
    }
    close_times = {
        s: pd.DatetimeIndex(g["open_time"] + pd.Timedelta(hours=8)).asi8
        for s, g in frames.items()
    }
    elig = p.eligible[p.d0 : p.dn]
    times = p.times
    n = len(times) if limit is None else min(limit, len(times))
    W = np.zeros((n, p.n_sym))
    ix = {s: j for j, s in enumerate(p.symbols)}
    t0 = time.time()
    for i in range(n):
        t = times[i]
        names = [p.symbols[j] for j in np.flatnonzero(elig[i])]
        sub = {}
        for s in names:
            stop = int(np.searchsorted(close_times[s], t.value, side="right"))
            sub[s] = frames[s].iloc[:stop]
        out = strat.target_weights(Ctx(t, sub, names), seed=20260804)
        if out:
            for s, w in out.items():
                W[i, ix[s]] = w
        if i and i % 500 == 0:
            print(f"  {i}/{n}  {time.time() - t0:.0f}s", flush=True)
    
    print(f"strategy replay: {n} boundaries in {time.time() - t0:.0f}s")

    import sweep as SW

    SW.init()
    from book import tranche_book

    S = SW.score(
        ("bigp", "imbsml0"),
        (1.0, 1.0),
        mod.FORMATION_BARS,
        ("ret", "size", "liq"),
        mod.NORM_BARS,
        True,
    )
    B = tranche_book(S, elig, k=mod.SLEEVE_NAMES, hold=mod.HOLD_BARS)[:n]
    # Both are compared after unit-gross normalisation, which is what the evaluator scores.
    def unit(x):
        g = np.abs(x).sum(axis=1, keepdims=True)
        return x / np.where(g > 0, g, 1.0)

    a, b = unit(W), unit(B)
    d = np.abs(a - b)
    print(f"max |dw| = {d.max():.3e}   mean |dw| = {d.mean():.3e}")
    rows = np.flatnonzero(d.max(axis=1) > 1e-9)
    print(f"boundaries differing by > 1e-9: {rows.size} of {n}")
    if rows.size:
        for r in rows[:5]:
            j = np.argmax(d[r])
            print(f"  {times[r]} {p.symbols[j]}: strategy {a[r, j]:+.6f} offline {b[r, j]:+.6f}")
    corr = np.corrcoef(a.ravel(), b.ravel())[0, 1]
    print(f"weight correlation = {corr:.8f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
