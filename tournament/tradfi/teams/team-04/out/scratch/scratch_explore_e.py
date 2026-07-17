"""team-04 scratch — Batch E: robustness blends, tail plateau edges, phase sweep (exp-017..021).

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


def mom_signal(F: int, skip: int) -> pd.DataFrame:
    return C.shift(skip) / C.shift(skip + F) - 1.0


def rank_inputs(F: int, skip: int):
    sig = mom_signal(F, skip)
    elig = close.notna() & np.isfinite(sig)
    ranks = sig.where(elig).rank(axis=1, method="first")
    n = ranks.notna().sum(axis=1).astype(float)
    return ranks, n


def tail_weights(F: int, skip: int, q: float) -> pd.DataFrame:
    ranks, n = rank_inputs(F, skip)
    n_side = np.floor(q * n)
    n_side = n_side.where(n_side >= MIN_SIDE)
    long_m = ranks.gt(n - n_side, axis=0)
    short_m = ranks.le(n_side, axis=0)
    w = pd.DataFrame(0.0, index=ranks.index, columns=ranks.columns)
    w = w.mask(long_m, 1.0).mask(short_m, -1.0)
    return w.div(n_side, axis=0).fillna(0.0)


def hysteresis_weights(F: int, skip: int, q_in: float, q_stay: float) -> pd.DataFrame:
    ranks, n = rank_inputs(F, skip)
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
        top_in = valid & (rt > n_t - n_in)
        top_stay = valid & (rt > n_t - n_stay)
        bot_in = valid & (rt <= n_in)
        bot_stay = valid & (rt <= n_stay)
        lng = top_in | (long_prev & top_stay)
        sht = bot_in | (short_prev & bot_stay)
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


def monthly_hold(w: pd.DataFrame, period: int = 21, phase: int = 0) -> pd.DataFrame:
    keep = np.zeros(len(w), dtype=bool)
    keep[phase::period] = True
    out = w.where(pd.Series(keep, index=w.index), np.nan)
    return out.ffill().fillna(0.0)


def report(exp_id: str, raw: pd.DataFrame, variant: str) -> dict:
    _, _, m1 = te.run_is(raw, pn)
    _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
    return {"id": exp_id, "variant": variant, "m1": m1.to_dict(), "sharpe_2x": m2.sharpe, "maxdd_2x": m2.maxdd}


if __name__ == "__main__":
    results = []

    # exp-017 — multi-lookback blend, EMA overlay
    blend_f = (tail_weights(126, 0, 0.20) + tail_weights(189, 0, 0.20) + tail_weights(252, 0, 0.20)) / 3.0
    results.append(report("exp-017", blend_f.ewm(halflife=5).mean(), "blendF-ema5"))

    # exp-018 — skip blend at F=252, EMA overlay
    blend_s = (tail_weights(252, 0, 0.20) + tail_weights(252, 21, 0.20)) / 2.0
    results.append(report("exp-018", blend_s.ewm(halflife=5).mean(), "blendSkip-ema5"))

    # exp-019 / exp-020 — tail-width plateau edges with hysteresis
    results.append(report("exp-019", hysteresis_weights(252, 0, 0.15, 0.30), "hyst-15/30"))
    results.append(report("exp-020", hysteresis_weights(252, 0, 0.25, 0.40), "hyst-25/40"))

    hdr = f"{'id':8} {'variant':>14} {'shp1x':>7} {'shp2x':>7} {'maxDD':>7} {'turn':>6} {'nL':>4} {'nS':>4} {'bull':>6} {'bear':>6} {'chop':>6}"
    print(hdr)
    for r in results:
        m = r["m1"]
        rs = m["regime_sharpe"]
        print(
            f"{r['id']:8} {r['variant']:>14} {m['sharpe']:>7.3f} {r['sharpe_2x']:>7.3f} "
            f"{m['maxdd']:>7.3f} {m['ann_turnover']:>6.1f} {m['median_names_long']:>4.0f} "
            f"{m['median_names_short']:>4.0f} {rs['bull']:>6.2f} {rs['bear']:>6.2f} {rs['chop']:>6.2f}"
        )

    # exp-021 — phase sweep of hold-21d (1x only)
    w0 = tail_weights(252, 0, 0.20)
    phases = []
    for ph in range(21):
        _, _, m = te.run_is(monthly_hold(w0, 21, ph), pn)
        phases.append(m.sharpe)
    arr = np.array(phases)
    phase_res = {
        "id": "exp-021",
        "per_phase_sharpe_1x": [round(x, 4) for x in phases],
        "mean": round(float(arr.mean()), 4),
        "std": round(float(arr.std()), 4),
        "min": round(float(arr.min()), 4),
        "max": round(float(arr.max()), 4),
    }
    print(f"\nexp-021 hold-21d phase sweep (1x): mean {arr.mean():.3f}  std {arr.std():.3f}  "
          f"min {arr.min():.3f}  max {arr.max():.3f}")

    results.append(phase_res)
    (OUT / "batchE_results.json").write_text(json.dumps(results, indent=2))
