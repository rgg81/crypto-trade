"""EDA 5 -- the episode architecture, and whether it can pay for its own turnover.

EDA 4 killed the obvious construction: an overlapping-slice book that re-weights every 8h turns
over ~300x a year and earns ~10 bps per unit of it, which is a book paying the exchange to be
right. The turnover is not the signal's fault -- it is arithmetic. A name held H bars in a book
renormalised every boundary costs ~2/H of turnover per invested bar no matter how good the signal
is, so a 24h horizon at an 8h cadence cannot be cheap.

The way out is to stop re-weighting. An EPISODE book enters once when a liquidity cascade fires,
holds the same quantities for H bars by returning ``None`` (which costs no turnover at all), and
exits. Turnover per episode is then ~2.0 regardless of H, and the gross edge per unit turnover is
the whole episode's return divided by 2.

This file simulates that weight path. It is an APPROXIMATION -- no risk unit, no funding, no
participation cap, no exposure caps, no floors, no ranking score. It ranks constructions so the
twelve trials are spent on questions rather than on discovery.
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

mkt_ret = ret.where(mask).mean(axis=1)
mkt_sig = mkt_ret.rolling(60, min_periods=30).std().shift(1)
mkt_z = mkt_ret / mkt_sig

# one-bar step return from the fill: holding weight w decided at boundary i earns
# op[i+2]/op[i+1] - 1 over the following bar.
STEP = (op.shift(-2) / op.shift(-1) - 1.0).where(mask)

FOLDS = [
    ("F1", "2020-08-01", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
]
COST_BPS_PER_SIDE = 7.5


def simulate(
    market_z: float,
    shock_z: float,
    flow_spike: float,
    entry_delay: int,
    hold_bars: int,
    max_names: int,
    cooldown: int,
) -> dict:
    idx = z.index
    n = len(idx)
    cols = list(z.columns)
    shock = ((z <= shock_z) & (ts >= flow_spike)).fillna(False).to_numpy()
    intensity = (-z).where((z <= shock_z) & (ts >= flow_spike)).fillna(0.0).to_numpy()
    cascade = (mkt_z <= market_z).fillna(False).to_numpy()
    tradable = mask.to_numpy()

    weights = np.zeros((n, len(cols)))
    emitted = np.zeros(n, dtype=bool)  # True where the book emits a target row
    held = np.zeros(len(cols))
    bars_held = 0
    cool = 0
    in_position = False

    for i in range(n):
        if in_position:
            bars_held += 1
            if bars_held >= hold_bars:
                weights[i] = 0.0
                emitted[i] = True  # explicit flat
                in_position = False
                held = np.zeros(len(cols))
                cool = cooldown
            else:
                weights[i] = held  # returned as None in the real strategy: no turnover
            continue
        if cool > 0:
            cool -= 1
            weights[i] = 0.0
            continue
        j = i - entry_delay
        if j < 0 or not cascade[j]:
            weights[i] = 0.0
            continue
        # names shocked on the cascade bar and still tradable now
        cand = intensity[j] * shock[j] * tradable[i]
        if not (cand > 0).any():
            weights[i] = 0.0
            continue
        order = np.argsort(-cand)
        keep = [k for k in order if cand[k] > 0][:max_names]
        w = np.zeros(len(cols))
        w[keep] = 1.0 / len(keep)
        weights[i] = w
        held = w
        emitted[i] = True
        in_position = True
        bars_held = 0

    W = pd.DataFrame(weights, index=idx, columns=cols)
    # Turnover only where a target row is emitted; holds cost nothing.
    prev = W.shift(1).fillna(0.0)
    dw = (W - prev).abs().sum(axis=1)
    dw[~emitted] = 0.0
    total_turn = float(dw.sum())
    years = n / 1095.0

    pnl = (W * STEP.fillna(0.0)).sum(axis=1)
    cost = dw * COST_BPS_PER_SIDE / 1e4
    gross_total = float(pnl.sum())

    def sharpe(series: pd.Series) -> float:
        daily = series.groupby(pd.DatetimeIndex(series.index).floor("D")).sum()
        return float(daily.mean() / daily.std() * np.sqrt(365)) if daily.std() > 0 else np.nan

    fold_s = []
    for _, lo, hi in FOLDS:
        sel = (idx >= pd.Timestamp(lo, tz="UTC")) & (idx < pd.Timestamp(hi, tz="UTC"))
        fold_s.append(sharpe((pnl - 2 * cost)[sel]))

    gross_pos = W.abs().sum(axis=1)
    return {
        "turn/yr": total_turn / years,
        "inv%": float((gross_pos > 0).mean()) * 100,
        "names": float(gross_pos[gross_pos > 0].mean() * 0 + (W != 0).sum(axis=1)[
            (W != 0).sum(axis=1) > 0].mean()),
        "gross%/yr": gross_total / years * 100,
        "bps/turn": gross_total / total_turn * 1e4 if total_turn > 0 else np.nan,
        "shp_g": sharpe(pnl),
        "shp_1x": sharpe(pnl - cost),
        "shp_2x": sharpe(pnl - 2 * cost),
        "shp_3x": sharpe(pnl - 3 * cost),
        "F1": fold_s[0], "F2": fold_s[1], "F3": fold_s[2], "F4": fold_s[3],
        "episodes/yr": float(emitted.sum()) / 2 / years,
    }


HEAD = ["turn/yr", "inv%", "names", "gross%/yr", "bps/turn", "shp_g", "shp_1x", "shp_2x",
        "shp_3x", "F1", "F2", "F3", "F4", "episodes/yr"]


def show(label: str, r: dict) -> None:
    print(f"{label:<46}" + "".join(f"{r[k]:>10.2f}" for k in HEAD))


print(f"{'config':<46}" + "".join(f"{k:>10}" for k in HEAD))
print("-" * 190)
print("== entry delay sweep (cascade mkt_z<=-1.5, z<=-2, ts>=2, 8 names, hold 3, cd 1) ==")
for d in (0, 1, 2):
    show(f"delay={d}", simulate(-1.5, -2.0, 2.0, d, 3, 8, 1))

print("== hold sweep (delay=1) ==")
for h in (2, 3, 4, 6, 9):
    show(f"hold={h}", simulate(-1.5, -2.0, 2.0, 1, h, 8, 1))

print("== market cascade threshold ==")
for m in (-1.0, -1.5, -2.0, -2.5):
    show(f"mkt_z<={m}", simulate(m, -2.0, 2.0, 1, 3, 8, 1))

print("== per-symbol shock threshold ==")
for s in (-1.0, -1.5, -2.0, -2.5):
    show(f"z<={s}", simulate(-1.5, s, 2.0, 1, 3, 8, 1))

print("== flow spike threshold (the signature) ==")
for f in (0.0, 1.0, 1.5, 2.0, 3.0, 4.0):
    show(f"ts>={f}", simulate(-1.5, -2.0, f, 1, 3, 8, 1))

print("== basket size ==")
for k in (3, 5, 8, 12, 20):
    show(f"names<={k}", simulate(-1.5, -2.0, 2.0, 1, 3, k, 1))

print("== cooldown ==")
for c in (0, 1, 3, 6):
    show(f"cooldown={c}", simulate(-1.5, -2.0, 2.0, 1, 3, 8, c))
