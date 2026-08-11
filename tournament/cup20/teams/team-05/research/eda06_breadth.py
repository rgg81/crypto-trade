"""EDA 6 -- breadth as the cascade detector, and the shock-signature ablation.

EDA 5 used a market-return z-score to say "a cascade is happening". That is a regime measure and
it belongs to a different lane. A liquidation cascade is better described by what it actually is:
MANY names printing the forced-flow signature in the same 8h bar. Breadth measures the event;
the market return measures the consequence.

So the detector becomes: count the eligible members whose last bar was a shock -- a move beyond
its own recent scale, printed with a trade-count spike -- and call it a cascade when that count
crosses a threshold. The basket is then the shocked names themselves, so breadth and
diversification are the same quantity.

Approximation, not a scorer. Costs are a flat 7.5 bps/side to rank constructions; no risk unit,
no funding, no caps, no floors.
"""

from __future__ import annotations

import itertools
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
IDX = z.index
N = len(IDX)
COLS = list(z.columns)
TRADABLE = mask.to_numpy()
STEP_A = STEP.fillna(0.0).to_numpy()


def simulate(shock_z: float, flow_spike: float, breadth: int, entry_delay: int,
             hold_bars: int, max_names: int, use_signature: bool = True) -> dict:
    cond = (z <= shock_z)
    if use_signature:
        cond = cond & (ts >= flow_spike)
    shock = cond.fillna(False).to_numpy()
    intensity = (-z).where(cond).fillna(0.0).to_numpy()
    breadth_count = shock.sum(axis=1)
    cascade = breadth_count >= breadth

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
    total_turn = float(dw.sum())
    years = N / 1095.0
    pnl = pd.Series((W * STEP_A).sum(axis=1), index=IDX)
    cost = dw * COST
    gross_total = float(pnl.sum())

    def sh(s: pd.Series) -> float:
        d = s.groupby(pd.DatetimeIndex(s.index).floor("D")).sum()
        return float(d.mean() / d.std() * np.sqrt(365)) if d.std() > 0 else np.nan

    folds = []
    for _, lo, hi in FOLDS:
        sel = (IDX >= pd.Timestamp(lo, tz="UTC")) & (IDX < pd.Timestamp(hi, tz="UTC"))
        folds.append(sh((pnl - 2 * cost)[sel]))
    nz = (W != 0).sum(axis=1)
    daily = (pnl - cost).groupby(pd.DatetimeIndex(IDX).floor("D")).sum()
    eq = (1 + daily).cumprod()
    dd = float((1 - eq / eq.cummax()).max())
    return {
        "turn/yr": total_turn / years, "inv%": float((nz > 0).mean()) * 100,
        "names": float(nz[nz > 0].mean()) if (nz > 0).any() else 0.0,
        "gross%/yr": gross_total / years * 100,
        "bps/turn": gross_total / total_turn * 1e4 if total_turn > 0 else np.nan,
        "shp_1x": sh(pnl - cost), "shp_2x": sh(pnl - 2 * cost), "shp_3x": sh(pnl - 3 * cost),
        "wfold": min(folds), "mfold": float(np.median(folds)),
        "F1": folds[0], "F2": folds[1], "F3": folds[2], "F4": folds[3],
        "maxDD": dd, "eps/yr": float(emitted.sum()) / 2 / years,
        "trades": int((np.abs(np.diff(W, axis=0, prepend=0)) > 1e-12).sum()),
    }


HEAD = ["turn/yr", "inv%", "names", "gross%/yr", "bps/turn", "shp_1x", "shp_2x", "shp_3x",
        "wfold", "mfold", "F1", "F2", "F3", "F4", "maxDD", "eps/yr", "trades"]
print(f"{'config':<42}" + "".join(f"{k:>10}" for k in HEAD))
print("-" * 214)


def show(label, **kw):
    r = simulate(**kw)
    print(f"{label:<42}" + "".join(
        f"{r[k]:>10.2f}" if isinstance(r[k], float) else f"{r[k]:>10d}" for k in HEAD))
    return r


base = dict(shock_z=-2.0, flow_spike=2.0, breadth=4, entry_delay=1, hold_bars=3, max_names=8)

print("== breadth threshold ==")
for b in (2, 3, 4, 5, 6, 8):
    show(f"breadth>={b}", **{**base, "breadth": b})
print("== flow spike (THE SIGNATURE) ==")
for f in (1.0, 1.5, 2.0, 2.5, 3.0):
    show(f"ts>={f}", **{**base, "flow_spike": f})
print("== SIGNATURE OFF (magnitude only, breadth on |z| alone) ==")
for b in (2, 3, 4, 5, 6, 8):
    show(f"NO-SIG breadth>={b}", **{**base, "breadth": b, "use_signature": False})
print("== shock z ==")
for s in (-1.5, -1.75, -2.0, -2.25, -2.5):
    show(f"z<={s}", **{**base, "shock_z": s})
print("== hold ==")
for h in (2, 3, 4, 5, 6):
    show(f"hold={h}", **{**base, "hold_bars": h})
print("== entry delay ==")
for d in (0, 1, 2):
    show(f"delay={d}", **{**base, "entry_delay": d})
print("== max names ==")
for k in (4, 5, 6, 8, 10, 20):
    show(f"names<={k}", **{**base, "max_names": k})

print()
print("== coarse joint scan around the plateau (sorted by worst-fold 2x Sharpe) ==")
rows = []
for sz, fs, br, hb in itertools.product((-1.75, -2.0, -2.25), (1.5, 2.0, 2.5),
                                        (3, 4, 5), (2, 3, 4)):
    r = simulate(shock_z=sz, flow_spike=fs, breadth=br, entry_delay=1, hold_bars=hb, max_names=8)
    rows.append((f"z{sz} ts{fs} br{br} h{hb}", r))
rows.sort(key=lambda kv: -kv[1]["wfold"])
for label, r in rows[:18]:
    print(f"{label:<42}" + "".join(
        f"{r[k]:>10.2f}" if isinstance(r[k], float) else f"{r[k]:>10d}" for k in HEAD))
