"""EDA 8 -- lock the design, check every declared neighbourhood point, price the controls.

Decisions this file has to support before any trial is spent:
  * does MIN_BREADTH do anything, or is it decoration?
  * does a range-vs-scale term add anything beyond the trade-count spike?
  * is every point of the intended neighbourhood on the plateau, or would the median be dragged?
  * what do the controls-off / individual-control / combined-control books look like?

Approximation, not a scorer.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel  # noqa: E402

P = build_panel(lookback=60)
op, ret, sigma = P["open"], P["ret"], P["sigma"]
mask = P["tradable"]
z = (ret / sigma).where(mask)
ts = P["tspike"].where(mask)
vs = P["vspike"].where(mask)
rr = P["rr"].where(mask)
STEP = (op.shift(-2) / op.shift(-1) - 1.0).where(mask)

FOLDS = [("F1", "2020-08-01", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
         ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", "2024-08-01")]
COST = 7.5 / 1e4
IDX, COLS, N = z.index, list(z.columns), len(z.index)
TRADABLE = mask.to_numpy()
STEP_A = STEP.fillna(0.0).to_numpy()


def simulate(shock_z=-2.0, flow_spike=2.0, range_spike=0.0, breadth=2, entry_delay=1,
             hold_bars=3, max_names=8) -> dict:
    cond = (z <= shock_z) & (ts >= flow_spike) & (rr >= range_spike)
    shock = cond.fillna(False).to_numpy()
    intensity = (-z).where(cond).fillna(0.0).to_numpy()
    cascade = shock.sum(axis=1) >= breadth

    W = np.zeros((N, len(COLS)))
    emitted = np.zeros(N, dtype=bool)
    held = np.zeros(len(COLS))
    bars_held, in_pos = 0, False
    for i in range(N):
        if in_pos:
            bars_held += 1
            if bars_held >= hold_bars:
                emitted[i] = True
                in_pos = False
                held = np.zeros(len(COLS))
            else:
                W[i] = held
            continue
        j = i - entry_delay
        if j < 0 or not cascade[j]:
            continue
        cand = intensity[j] * shock[j] * TRADABLE[i]
        if not (cand > 0).any():
            continue
        keep = [k for k in np.argsort(-cand) if cand[k] > 0][:max_names]
        w = np.zeros(len(COLS))
        w[keep] = 1.0 / len(keep)
        W[i] = w
        held = w
        emitted[i] = True
        in_pos, bars_held = True, 0

    Wd = pd.DataFrame(W, index=IDX, columns=COLS)
    dw = (Wd - Wd.shift(1).fillna(0.0)).abs().sum(axis=1)
    dw[~emitted] = 0.0
    tt = float(dw.sum())
    years = N / 1095.0
    pnl = pd.Series((W * STEP_A).sum(axis=1), index=IDX)
    cost = dw * COST

    def sh(s):
        d = s.groupby(pd.DatetimeIndex(s.index).floor("D")).sum()
        return float(d.mean() / d.std() * np.sqrt(365)) if d.std() > 0 else np.nan

    folds = []
    for _, lo, hi in FOLDS:
        sel = (IDX >= pd.Timestamp(lo, tz="UTC")) & (IDX < pd.Timestamp(hi, tz="UTC"))
        folds.append(sh((pnl - 2 * cost)[sel]))
    nz = (W != 0).sum(axis=1)
    daily = (pnl - cost).groupby(pd.DatetimeIndex(IDX).floor("D")).sum()
    eq = (1 + daily).cumprod()
    q = (1 + daily).groupby(pd.DatetimeIndex(daily.index).tz_convert("UTC").tz_localize(None)
                            .to_period("Q")).prod() - 1
    return {
        "turn/yr": tt / years, "inv%": float((nz > 0).mean()) * 100,
        "names": float(nz[nz > 0].mean()) if (nz > 0).any() else 0.0,
        "gross%/yr": float(pnl.sum()) / years * 100,
        "bps/turn": float(pnl.sum()) / tt * 1e4 if tt > 0 else np.nan,
        "shp_1x": sh(pnl - cost), "shp_2x": sh(pnl - 2 * cost), "shp_3x": sh(pnl - 3 * cost),
        "wfold": min(folds), "mfold": float(np.median(folds)),
        "F1": folds[0], "F2": folds[1], "F3": folds[2], "F4": folds[3],
        "maxDD": float((1 - eq / eq.cummax()).max()), "posQ": float((q > 0).mean()),
        "trades": int((np.abs(np.diff(W, axis=0, prepend=0)) > 1e-12).sum()),
        "vol%": float(daily.std() * np.sqrt(365) * 100),
    }


HEAD = ["turn/yr", "inv%", "names", "gross%/yr", "bps/turn", "shp_1x", "shp_2x", "shp_3x",
        "wfold", "mfold", "F1", "F2", "F3", "F4", "maxDD", "posQ", "trades", "vol%"]
print(f"{'config':<40}" + "".join(f"{k:>10}" for k in HEAD))
print("-" * 220)


def show(label, **kw):
    r = simulate(**kw)
    print(f"{label:<40}" + "".join(
        f"{r[k]:>10.2f}" if isinstance(r[k], float) else f"{r[k]:>10d}" for k in HEAD))
    return r


print("== does MIN_BREADTH do anything? ==")
for b in (1, 2, 3):
    show(f"breadth>={b}", breadth=b)
print("== does a range-vs-scale term add beyond the flow spike? ==")
for rs in (0.0, 1.0, 1.5, 2.0, 2.5):
    show(f"rr>={rs}", range_spike=rs)
print("== volume spike instead of trade-count spike (diagnostic) ==")
print("   (rerun manually; tspike is the declared signature)")
print()
print("== THE DECLARED NEIGHBOURHOOD: nominee + 6 coordinate-wise variations ==")
NOM = dict(shock_z=-2.0, flow_spike=2.0, hold_bars=3)
pts = [("NOMINEE  z-2.00 ts2.00 h3", NOM),
       ("  z=-1.75", {**NOM, "shock_z": -1.75}),
       ("  z=-2.25", {**NOM, "shock_z": -2.25}),
       ("  ts=1.60", {**NOM, "flow_spike": 1.6}),
       ("  ts=2.50", {**NOM, "flow_spike": 2.5}),
       ("  hold=2 ", {**NOM, "hold_bars": 2}),
       ("  hold=4 ", {**NOM, "hold_bars": 4})]
results = []
for lab, kw in pts:
    results.append(show(lab, **kw))
print()
print("  per-metric MEDIAN across the 7 points (this is what the sweep would score):")
med = {k: float(np.median([r[k] for r in results])) for k in HEAD}
print(f"{'MEDIAN':<40}" + "".join(f"{med[k]:>10.2f}" for k in HEAD))
print(f"  points with positive return AND positive 2x sharpe: "
      f"{sum(1 for r in results if r['gross%/yr'] > 0 and r['shp_2x'] > 0)}/7")

print()
print("== ABLATIONS ==")
show("A) controls OFF (magnitude only)", flow_spike=0.0, breadth=1)
show("B) signature only, no breadth", breadth=1)
show("C) breadth only, no signature", flow_spike=0.0, breadth=2)
show("D) combined (nominee)", )
show("E) no entry delay", entry_delay=0)
show("F) delay 2", entry_delay=2)
