"""team-04 scratch — Batch B (skip axis) + Batch C (weighting scheme), exp-010..exp-013.

Pre-registered in experiments.jsonl BEFORE this run. Signals from team_view + aux ONLY.
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
C = close.ffill()


def mom_signal(formation: int, skip: int) -> pd.DataFrame:
    return C.shift(skip) / C.shift(skip + formation) - 1.0


def eligible(sig: pd.DataFrame) -> pd.DataFrame:
    return close.notna() & np.isfinite(sig)


def tail_weights(sig: pd.DataFrame, q: float, min_side: int = 5) -> pd.DataFrame:
    s = sig.where(eligible(sig))
    ranks = s.rank(axis=1, method="first")
    n = ranks.notna().sum(axis=1).astype(float)
    n_side = np.floor(q * n)
    n_side = n_side.where(n_side >= min_side)
    long_m = ranks.gt(n - n_side, axis=0)
    short_m = ranks.le(n_side, axis=0)
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    w = w.mask(long_m, 1.0).mask(short_m, -1.0)
    return w.div(n_side, axis=0).fillna(0.0)


def rank_linear_weights(sig: pd.DataFrame, min_names: int = 10) -> pd.DataFrame:
    """Centered-rank weights across the full eligible cross-section (demeaned by construction)."""
    s = sig.where(eligible(sig))
    ranks = s.rank(axis=1, method="first")
    n = ranks.notna().sum(axis=1).astype(float)
    w = ranks.sub((n + 1.0) / 2.0, axis=0)
    w = w.where(n >= min_names)  # too-thin cross-section => flat
    return w.fillna(0.0)


def report(exp_id: str, raw: pd.DataFrame, extra: dict) -> dict:
    _, _, m1 = te.run_is(raw, pn)
    _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
    return {"id": exp_id, **extra, "m1": m1.to_dict(), "sharpe_2x": m2.sharpe, "maxdd_2x": m2.maxdd}


if __name__ == "__main__":
    results = []
    # exp-010 / exp-011 — skip axis at F=252, q=0.20
    for exp_id, skip in (("exp-010", 0), ("exp-011", 10)):
        results.append(report(exp_id, tail_weights(mom_signal(252, skip), 0.20), {"skip": skip}))

    # exp-012 — rank-linear full cross-section, F=252, skip=21
    results.append(report("exp-012", rank_linear_weights(mom_signal(252, 21)), {"scheme": "rank-linear"}))

    # exp-013 — vol-scaled momentum tails, F=252, skip=21, q=0.20
    ret = C.pct_change()
    vol63 = ret.rolling(63).std()
    sig_vs = mom_signal(252, 21) / vol63
    results.append(report("exp-013", tail_weights(sig_vs, 0.20), {"scheme": "vol-scaled mom"}))

    (OUT / "batchBC_results.json").write_text(json.dumps(results, indent=2))

    hdr = f"{'id':8} {'variant':>16} {'shp1x':>7} {'shp2x':>7} {'maxDD':>7} {'turn':>6} {'nL':>4} {'nS':>4} {'bull':>6} {'bear':>6} {'chop':>6}"
    print(hdr)
    for r in results:
        m = r["m1"]
        rs = m["regime_sharpe"]
        variant = str(r.get("skip", r.get("scheme")))
        print(
            f"{r['id']:8} {variant:>16} {m['sharpe']:>7.3f} {r['sharpe_2x']:>7.3f} "
            f"{m['maxdd']:>7.3f} {m['ann_turnover']:>6.1f} {m['median_names_long']:>4.0f} "
            f"{m['median_names_short']:>4.0f} {rs['bull']:>6.2f} {rs['bear']:>6.2f} {rs['chop']:>6.2f}"
        )
