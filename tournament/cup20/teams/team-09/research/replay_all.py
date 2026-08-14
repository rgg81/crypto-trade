"""Replay every candidate directory's frozen strategy through the offline simulator.

Exact, not approximate: it drives the same ``strategy.py`` the organiser will import, over
past-only contexts built from the data root, and scores the resulting weight matrix with the
offline replica of the two-pass evaluation. Used to know what to expect from a trial before
spending it, and to check that each ablation changed what it was supposed to change.
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
from book import G, score_book  # noqa: E402
from ic import fold_edges  # noqa: E402
from panel import DATA, Panel  # noqa: E402
from sim import Sim  # noqa: E402

CAND = HERE.parent / "candidates"


class Ctx:
    __slots__ = ("decision_time", "bars", "funding", "auxiliary", "eligible_symbols")

    def __init__(self, t, bars, elig):
        self.decision_time, self.bars, self.eligible_symbols = t, bars, elig
        self.funding, self.auxiliary = None, {}


def replay(path: Path, p: Panel, frames, close_times) -> np.ndarray:
    spec = importlib.util.spec_from_file_location(f"cand_{path.parent.name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    strat = mod.build_strategy()
    elig = p.eligible[p.d0 : p.dn]
    W = np.zeros((len(p.times), p.n_sym))
    ix = {s: j for j, s in enumerate(p.symbols)}
    for i, t in enumerate(p.times):
        names = [p.symbols[j] for j in np.flatnonzero(elig[i])]
        sub = {
            s: frames[s].iloc[: int(np.searchsorted(close_times[s], t.value, side="right"))]
            for s in names
        }
        out = strat.target_weights(Ctx(t, sub, names), seed=17)
        if out:
            for s, w in out.items():
                W[i, ix[s]] = w
    return W


def main() -> None:
    p = Panel()
    sim = Sim(p)
    fe = fold_edges(p.times)
    bars = pd.read_parquet(DATA / "bars.parquet")
    frames = {
        s: g.reset_index(drop=True) for s, g in bars.groupby("symbol", observed=True, sort=False)
    }
    close_times = {
        s: pd.DatetimeIndex(g["open_time"] + pd.Timedelta(hours=8)).asi8 for s, g in frames.items()
    }
    rows = []
    for d in sorted(CAND.iterdir()):
        if not (d / "strategy.py").is_file():
            continue
        t0 = time.time()
        W = replay(d / "strategy.py", p, frames, close_times)
        r = score_book(sim, W, fe)
        r["G"] = G(r)
        r["candidate"] = d.name
        r["secs"] = round(time.time() - t0, 1)
        rows.append(r)
        print(f"  {d.name}: {r['secs']}s", flush=True)
    df = pd.DataFrame(rows)
    cols = [
        "candidate", "sharpe1", "sharpe2", "sharpe3", "ann1", "vol", "dd1", "dd2", "turn",
        "edge_bps", "cost_share", "trades", "f1", "f2", "f3", "f4", "worst_fold", "median_fold",
        "pq2", "calmar2", "G", "long_gross", "short_gross",
    ]
    pd.set_option("display.width", 320)
    print(df[cols].round(4).to_string(index=False))
    df.to_csv(HERE / "ablation_offline.csv", index=False)


if __name__ == "__main__":
    main()
