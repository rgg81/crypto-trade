"""team-04 scratch — Batch A: plain CS 12-1 momentum core grid (exp-001..exp-009).

Pre-registered in experiments.jsonl BEFORE this run. Signal uses team_view + aux ONLY.
Results dumped to out/scratch/batchA_results.json (numbers come from te.run_is Metrics).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "analysis/portfolio/tradfi")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from tournament import engine as te  # noqa: E402

OUT = Path("tournament/tradfi/teams/team-04/out/scratch")
OUT.mkdir(parents=True, exist_ok=True)

pn, aux = te.load_is_panels()
view = te.team_view(pn)
close = view["close"]
C = close.ffill()  # causal: past values only


def mom_signal(formation: int, skip: int) -> pd.DataFrame:
    return C.shift(skip) / C.shift(skip + formation) - 1.0


def tail_weights(sig: pd.DataFrame, q: float, min_side: int = 5) -> pd.DataFrame:
    elig = close.notna() & np.isfinite(sig)
    s = sig.where(elig)
    ranks = s.rank(axis=1, method="first")  # 1..N, deterministic (column order)
    n = ranks.notna().sum(axis=1).astype(float)
    n_side = np.floor(q * n)
    n_side = n_side.where(n_side >= min_side)  # NaN => flat row
    long_m = ranks.gt(n - n_side, axis=0)
    short_m = ranks.le(n_side, axis=0)
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    w = w.mask(long_m, 1.0).mask(short_m, -1.0)
    return w.div(n_side, axis=0).fillna(0.0)


def run_config(exp_id: str, formation: int, skip: int, q: float) -> dict:
    raw = tail_weights(mom_signal(formation, skip), q)
    _, _, m1 = te.run_is(raw, pn)
    _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
    return {
        "id": exp_id,
        "formation": formation,
        "skip": skip,
        "q": q,
        "m1": m1.to_dict(),
        "sharpe_2x": m2.sharpe,
        "maxdd_2x": m2.maxdd,
    }


if __name__ == "__main__":
    grid = []
    i = 1
    for F in (126, 189, 252):
        for Q in (0.20, 0.30, 0.40):
            grid.append((f"exp-{i:03d}", F, 21, Q))
            i += 1

    results = [run_config(*g) for g in grid]
    (OUT / "batchA_results.json").write_text(json.dumps(results, indent=2))

    hdr = f"{'id':8} {'F':>4} {'q':>5} {'shp1x':>7} {'shp2x':>7} {'maxDD':>7} {'turn':>6} {'nL':>4} {'nS':>4} {'bull':>6} {'bear':>6} {'chop':>6}"
    print(hdr)
    for r in results:
        m = r["m1"]
        rs = m["regime_sharpe"]
        print(
            f"{r['id']:8} {r['formation']:>4} {r['q']:>5} {m['sharpe']:>7.3f} {r['sharpe_2x']:>7.3f} "
            f"{m['maxdd']:>7.3f} {m['ann_turnover']:>6.1f} {m['median_names_long']:>4.0f} "
            f"{m['median_names_short']:>4.0f} {rs['bull']:>6.2f} {rs['bear']:>6.2f} {rs['chop']:>6.2f}"
        )
