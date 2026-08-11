"""EDA 9 -- flatten the surface, because the median of the plateau is what gets scored.

EDA 8's design has a good nominee (worst 2x fold +0.61) and a bad plateau (median worst fold
-0.22). With ~30 episodes a year a one-year fold Sharpe rests on ~30 bets, so any parameter move
that drops a handful of them flips a fold negative. Three architectural changes could raise the
number of bets without raising the turnover per bet:

  R) REFRESH -- a new cascade while holding replaces the basket and restarts the clock, instead of
     being ignored. Costs only the basket difference, not a round trip.
  T) TAPER   -- exit in two halves rather than one, which makes the holding-window axis smooth
     instead of a cliff. Total turnover is unchanged: 1.0 in, 0.5 + 0.5 out.
  W) WEIGHT  -- size by shock intensity rather than equal weight.

Each is scored on the MEDIAN of a seven-point coordinate star, not on its own best point, because
the median is the thing the tournament reads.

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
STEP = (op.shift(-2) / op.shift(-1) - 1.0).where(mask)
FOLDS = [("F1", "2020-08-01", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
         ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", "2024-08-01")]
COST = 7.5 / 1e4
IDX, COLS, N = z.index, list(z.columns), len(z.index)
TRADABLE = mask.to_numpy()
STEP_A = STEP.fillna(0.0).to_numpy()
FOLD_SEL = [((IDX >= pd.Timestamp(lo, tz="UTC")) & (IDX < pd.Timestamp(hi, tz="UTC")))
            for _, lo, hi in FOLDS]


def simulate(shock_z=-2.0, flow_spike=2.0, breadth=2, hold_bars=3, max_names=8,
             refresh=False, taper=False, intensity_weight=False, entry_delay=1) -> dict:
    cond = (z <= shock_z) & (ts >= flow_spike)
    shock = cond.fillna(False).to_numpy()
    inten = (-z).where(cond).fillna(0.0).to_numpy()
    cascade = shock.sum(axis=1) >= breadth

    W = np.zeros((N, len(COLS)))
    emitted = np.zeros(N, dtype=bool)
    held = np.zeros(len(COLS))
    age, in_pos = 0, False
    total_life = hold_bars + (2 if taper else 0)

    def basket(j: int, i: int) -> np.ndarray | None:
        cand = inten[j] * shock[j] * TRADABLE[i]
        if not (cand > 0).any():
            return None
        keep = [k for k in np.argsort(-cand) if cand[k] > 0][:max_names]
        w = np.zeros(len(COLS))
        if intensity_weight:
            w[keep] = cand[keep]
            w /= w.sum()
        else:
            w[keep] = 1.0 / len(keep)
        return w

    for i in range(N):
        j = i - entry_delay
        fires = j >= 0 and cascade[j]
        if in_pos and refresh and fires:
            b = basket(j, i)
            if b is not None:
                W[i] = b
                held, age, emitted[i] = b, 0, True
                continue
        if in_pos:
            age += 1
            if age >= total_life:
                emitted[i] = True
                in_pos, held = False, np.zeros(len(COLS))
            elif taper and age >= hold_bars:
                W[i] = held * 0.5
                emitted[i] = True
            else:
                W[i] = held
            continue
        if not fires:
            continue
        b = basket(j, i)
        if b is None:
            continue
        W[i] = b
        held, age, in_pos, emitted[i] = b, 0, True, True

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

    folds = [sh((pnl - 2 * cost)[sel]) for sel in FOLD_SEL]
    nz = (W != 0).sum(axis=1)
    daily = (pnl - cost).groupby(pd.DatetimeIndex(IDX).floor("D")).sum()
    eq = (1 + daily).cumprod()
    q = (1 + daily).groupby(pd.DatetimeIndex(daily.index).tz_convert("UTC").tz_localize(None)
                            .to_period("Q")).prod() - 1
    return {
        "turn/yr": tt / years, "inv%": float((nz > 0).mean()) * 100,
        "gross%/yr": float(pnl.sum()) / years * 100,
        "bps/turn": float(pnl.sum()) / tt * 1e4 if tt > 0 else np.nan,
        "shp_2x": sh(pnl - 2 * cost), "wfold": min(folds), "mfold": float(np.median(folds)),
        "F1": folds[0], "F2": folds[1], "F3": folds[2], "F4": folds[3],
        "maxDD": float((1 - eq / eq.cummax()).max()), "posQ": float((q > 0).mean()),
        "trades": int((np.abs(np.diff(W, axis=0, prepend=0)) > 1e-12).sum()),
        "vol%": float(daily.std() * np.sqrt(365) * 100),
    }


KEYS = ["turn/yr", "inv%", "gross%/yr", "bps/turn", "shp_2x", "wfold", "mfold",
        "F1", "F2", "F3", "F4", "maxDD", "posQ", "trades", "vol%"]


def star(nom: dict, coords: dict, **arch) -> tuple[dict, dict, int]:
    """Nominee plus one point above and below on each declared coordinate."""
    pts = [simulate(**{**nom, **arch})]
    for name, (lo, hi) in coords.items():
        pts.append(simulate(**{**nom, **arch, name: lo}))
        pts.append(simulate(**{**nom, **arch, name: hi}))
    med = {k: float(np.median([p[k] for p in pts])) for k in KEYS}
    pos = sum(1 for p in pts if p["gross%/yr"] > 0 and p["shp_2x"] > 0)
    return pts[0], med, pos


NOM = dict(shock_z=-2.0, flow_spike=2.0, breadth=2, hold_bars=3)
COORDS_A = {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "hold_bars": (2, 4)}
COORDS_B = {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "breadth": (1, 3)}

print(f"{'architecture / row':<44}" + "".join(f"{k:>10}" for k in KEYS))
print("-" * 200)
for label, arch in [
    ("plain", {}),
    ("REFRESH", dict(refresh=True)),
    ("TAPER", dict(taper=True)),
    ("REFRESH+TAPER", dict(refresh=True, taper=True)),
    ("REFRESH+TAPER+WEIGHT", dict(refresh=True, taper=True, intensity_weight=True)),
    ("REFRESH+WEIGHT", dict(refresh=True, intensity_weight=True)),
]:
    for cname, coords in (("star{z,ts,hold}", COORDS_A), ("star{z,ts,breadth}", COORDS_B)):
        nomr, med, pos = star(NOM, coords, **arch)
        if cname.startswith("star{z,ts,h"):
            print(f"{label + '  NOMINEE':<44}"
                  + "".join(f"{nomr[k]:>10.2f}" if isinstance(nomr[k], float)
                            else f"{nomr[k]:>10d}" for k in KEYS))
        print(f"{'   median ' + cname:<44}"
              + "".join(f"{med[k]:>10.2f}" for k in KEYS) + f"   pos={pos}/7")
