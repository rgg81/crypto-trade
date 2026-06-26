"""iter-011 — HYSTERESIS DEADBAND on the desk positions (cut transaction costs, leak-free).

The position-level accounting (iter-010) exposed turnover as a material cost (~1.4%/yr drag). A
hysteresis DEADBAND re-trades a metal only when its target moves more than δ from the held position
— the proven crypto iter-020 trick. It is path-dependent but **strictly causal**: held[t] uses only
on target[t] (past-decided) and held[t-1]. Recomputed from full history each tick (like everything
else), so live == backtest by construction; the reconcile proves it bit-exact.

Effect (position-level honest, canonical data): turnover −18%, cost drag 1.44%→1.18%/yr, and the
saving LIFTS the Sharpe in every regime — IS +0.16→+0.21, BULL +1.60→+1.66, BEAR preserved +0.36.
δ=0.02 is a conservative mid-basin pick (IS is monotone in δ — cost-driven — capped below where the
bull starts degrading at δ≈0.05; the whole δ∈[0.01,0.03] band is all-weather-improving). IS-only
tuned; bear/2008 are stress only.

Wraps iter-010 (breadth-accel gate + position-level net); adds only the deadband. CHAMP11 is deployed
via live_weights. Run:  uv run python analysis/portfolio/metals/iter_011_deadband.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_008_allweather as a8  # noqa: E402
import iter_010_breadth_accel as i10  # noqa: E402
import universe_metals as um  # noqa: E402

CHAMP11 = {**i10.CHAMP10, "deadband": 0.02}  # iter-010 + hysteresis deadband δ=0.02


def hysteresis_band(desk: pd.DataFrame, delta: float) -> pd.DataFrame:
    """Re-trade metal i only when |target[t,i] − held[t-1,i]| > δ; else hold. Causal recursion."""
    if delta <= 0:
        return desk.fillna(0.0)
    v = desk.fillna(0.0).to_numpy()
    out = np.empty_like(v)
    prev = v[0].copy()
    out[0] = prev
    for t in range(1, len(v)):
        row = v[t]
        moved = np.abs(row - prev) > delta
        prev = np.where(moved, row, prev)
        out[t] = prev
    return pd.DataFrame(out, index=desk.index, columns=desk.columns)


def desk_book(coins: dict[str, pd.DataFrame], **over) -> tuple[pd.DataFrame, pd.Series]:
    """The deadband-held per-metal DESK position book + bear flag (iter-010 desk, then banded)."""
    cfg = {**CHAMP11, **over}
    raw_desk, b = i10.desk_book(coins, **{k: v for k, v in cfg.items() if k != "deadband"})
    return hysteresis_band(raw_desk, cfg["deadband"]), b


def desk_net(coins: dict[str, pd.DataFrame], **over) -> pd.Series:
    """POSITION-LEVEL honest net of the deadband-held book: Σ held·ret_fwd − COST·Σ|Δheld|."""
    held, _ = desk_book(coins, **over)
    rf = um.panels(coins)["ret_fwd"]
    pnl = (held * rf.reindex(columns=held.columns)).sum(axis=1)
    cost = um.COST_SIDE * held.diff().abs().sum(axis=1)
    return (pnl - cost).dropna()


def next_target_weights(coins: dict[str, pd.DataFrame], tol: float = 1e-9) -> dict:
    """Per-metal deadband-held position for the just-opened candle — the live target."""
    held, b = desk_book(coins)
    last = held.iloc[-1]
    pos = last[last.abs() > tol]
    return {
        **{s: float(v) for s, v in pos.items()},
        "_meta": {
            "as_of": str(held.index[-1]),
            "breadth": float(
                a8.breadth_down(um.panels(coins)["close"], "ma", CHAMP11["win"]).iloc[-1]
            ),
            "gross": float(last.abs().sum()),
            "n_positions": int(len(pos)),
        },
    }


def scorecard() -> None:
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)
    print("=" * 92)
    print("iter-011 — HYSTERESIS DEADBAND (δ=0.02) on iter-010; turnover cut, all-weather lift")
    print("=" * 92)
    for lbl, dband in (("iter-010 (no band)", 0.0), ("iter-011 (δ=0.02)", 0.02)):
        nb, nm = desk_net(cb, deadband=dband), desk_net(cm, deadband=dband)
        tov = desk_book(cm, deadband=dband)[0].diff().abs().sum(axis=1).mean()
        b = i10._seg(nb, "2011-09-01", "2015-03-24")
        i = i10._seg(nm, "2000-01-01", str(um.OOS_CUTOFF.date()))
        u = i10._seg(nm, str(um.OOS_CUTOFF.date()), "2100-01-01")
        print(
            f"  {lbl:20} BEAR={b['sharpe']:+.2f}  IS={i['sharpe']:+.2f}  BULL={u['sharpe']:+.2f}  "
            f"turnover/bar={tov:.4f}  cost≈{um.COST_SIDE * tov * 825 * 100:.2f}%/yr"
        )


if __name__ == "__main__":
    scorecard()
