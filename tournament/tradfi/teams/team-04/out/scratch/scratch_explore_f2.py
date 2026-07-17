"""team-04 scratch — Batch F: final plateau neighbor + final spec confirmation (exp-022/023).

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
MIN_SIDE = 5


def hysteresis_weights(F: int, skip: int, q_in: float, q_stay: float) -> pd.DataFrame:
    sig = C.shift(skip) / C.shift(skip + F) - 1.0
    elig = close.notna() & np.isfinite(sig)
    ranks = sig.where(elig).rank(axis=1, method="first")
    n = ranks.notna().sum(axis=1).astype(float)
    r = ranks.to_numpy()
    nn = n.to_numpy()
    T, K = r.shape
    w = np.zeros((T, K))
    long_prev = np.zeros(K, dtype=bool)
    short_prev = np.zeros(K, dtype=bool)
    for t in range(T):
        n_t = nn[t]
        n_in = np.floor(q_in * n_t)
        if n_in < MIN_SIDE or n_t <= 0:
            long_prev[:] = False
            short_prev[:] = False
            continue
        n_stay = np.floor(q_stay * n_t)
        rt = r[t]
        valid = np.isfinite(rt)
        lng = (valid & (rt > n_t - n_in)) | (long_prev & valid & (rt > n_t - n_stay))
        sht = (valid & (rt <= n_in)) | (short_prev & valid & (rt <= n_stay))
        clash = lng & sht
        lng &= ~clash
        sht &= ~clash
        nl, ns = lng.sum(), sht.sum()
        if nl >= MIN_SIDE and ns >= MIN_SIDE:
            w[t, lng] = 1.0 / nl
            w[t, sht] = -1.0 / ns
            long_prev, short_prev = lng, sht
        else:
            long_prev[:] = False
            short_prev[:] = False
    return pd.DataFrame(w, index=ranks.index, columns=ranks.columns)


if __name__ == "__main__":
    results = []
    for exp_id, F, SK in (("exp-024", 252, 21),):
        raw = hysteresis_weights(F, SK, 0.20, 0.35)
        net1, w1, m1 = te.run_is(raw, pn)
        _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
        results.append(
            {"id": exp_id, "formation": F, "m1": m1.to_dict(), "sharpe_2x": m2.sharpe, "maxdd_2x": m2.maxdd}
        )
        if exp_id == "exp-023":
            yearly = net1.groupby(net1.index.year).apply(
                lambda s: float(s.groupby(s.index.to_period("M")).sum().mean()
                                / s.groupby(s.index.to_period("M")).sum().std() * np.sqrt(12))
                if s.groupby(s.index.to_period("M")).sum().std() > 0 else float("nan")
            )
            results[-1]["yearly_sharpe_1x"] = {int(y): round(v, 3) for y, v in yearly.items()}

    (OUT / "batchF2_results.json").write_text(json.dumps(results, indent=2))

    hdr = f"{'id':8} {'F':>4} {'shp1x':>7} {'shp2x':>7} {'maxDD':>7} {'turn':>6} {'nL':>4} {'nS':>4} {'bull':>6} {'bear':>6} {'chop':>6} {'meanNet':>8}"
    print(hdr)
    for r in results:
        m = r["m1"]
        rs = m["regime_sharpe"]
        print(
            f"{r['id']:8} {r['formation']:>4} {m['sharpe']:>7.3f} {r['sharpe_2x']:>7.3f} "
            f"{m['maxdd']:>7.3f} {m['ann_turnover']:>6.1f} {m['median_names_long']:>4.0f} "
            f"{m['median_names_short']:>4.0f} {rs['bull']:>6.2f} {rs['bear']:>6.2f} {rs['chop']:>6.2f} "
            f"{m['mean_net']:>8.4f}"
        )
    if "yearly_sharpe_1x" in results[-1]:
        print("\nexp-023 yearly Sharpe (1x):")
        print(json.dumps(results[-1]["yearly_sharpe_1x"], indent=None))
