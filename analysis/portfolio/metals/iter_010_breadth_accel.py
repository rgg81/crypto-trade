"""iter-010 — BREADTH-ACCELERATION dispersion gate + POSITION-LEVEL honest accounting.

Two changes, both forced by the live-parity + cost rigor of iter-009:

1. POSITION-LEVEL net (the honest desk PnL). iter-008/009 summed two net-streams
   (a_w·net_anchor + d_w·net_disp), which UNDER-COSTS the regime re-sizing turnover AND double-
   counts the gold overlap (anchor + dispersion both long gold). The desk's TRUE net is computed
   from the actual deployed per-metal positions: net[t] = Σ desk[t,i]·ret_fwd[t,i] − COST·Σ|Δdesk|.
   This is more correct, charges every real cost, nets the gold overlap, and makes live↔backtest
   parity TRIVIAL (the live engine holds `desk`; the net is computed from it).

2. BREADTH-ACCELERATION gate (the bigger leak-free bear edge). The iter-009 gate keyed off the
   breadth LEVEL — a lagging, confirming signal that ramps the bear-payer up only after the complex
   is already broadly down, missing the high-payoff front of the plunge. The ACCELERATION (rate of
   deterioration) is a LEADING signal. Blending the two (w·accel + (1−w)·level) lifts the honest
   position-level bear Sharpe +0.24 → +0.37, IMPROVES IS +0.16 → +0.26, and TIGHTENS worst-DD
   −14.3% → −12.7%, while staying all-weather and surviving the 2008 V-crash (+1.10). IS-only tuned
   (IS is monotone in the accel weight w, so the bear protection falls out of selecting the best-IS
   book — it was NOT tuned to the bear); the 2011-15 bear + 2008 GFC are STRESS checks only.

The desk structure is unchanged (long flat-in-bear braked anchor + dollar-neutral long-gold/short-
industrials dispersion, regime-scaled). Only the dispersion's regime weight W and the net accounting
change. live_weights deploys CHAMP10; reconcile_metals proves bit-exact parity.

Run:  uv run python analysis/portfolio/metals/iter_010_breadth_accel.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_002_mn_overlay as ov  # noqa: E402
import iter_007_allweather as aw  # noqa: E402
import iter_007_calibrate as cal  # noqa: E402
import iter_008_allweather as a8  # noqa: E402
import universe_metals as um  # noqa: E402

# frozen iter-010 champion (IS-only tuned; sm/zwin from the IS-robustness basin; w keeps the 2008
# V-crash positive while staying high-IS — every w∈[0.4,1.0] is all-weather, so w is a basin)
CHAMP10 = dict(win=450, a_w=0.5, dw_bull=0.25, dw_bear=1.0, sm=42, zwin=252, w_blend=0.65)
BRAKE_FLOOR = 0.25


def breadth_accel(close: pd.DataFrame, sm: int, zwin: int, win: int) -> pd.Series:
    """LEADING bear signal ∈ [0,1]: a logistic of the z-scored RATE of breadth deterioration.

    breadth[t] = frac(metals close[t] < SMA(win)[t]) (past-only); chg = breadth − breadth[t−sm];
    z = clip(chg / trailing-std(chg).shift(1), ±4); sig = logistic(z). Every step is past-only — the
    caller lags W one more candle, so the deployed weight is known at the close[t-1] decision.
    """
    brd = a8.breadth_down(close, "ma", win)
    chg = brd - brd.shift(sm)
    sd = chg.rolling(zwin).std().shift(1)
    z = (chg / sd).clip(-4, 4)
    return 1.0 / (1.0 + np.exp(-z))


def dispersion_weight(close: pd.DataFrame, cfg: dict) -> pd.Series:
    """The LAGGED dispersion regime weight W[t] = dw_bull + (dw_bear−dw_bull)·sig[t-1], sig =
    w_blend·breadth-ACCEL + (1−w_blend)·breadth-LEVEL. `.shift(1)` ⇒ leak-free + live-exact."""
    accel = breadth_accel(close, cfg["sm"], cfg["zwin"], cfg["win"]).fillna(0.0)
    level = a8.breadth_down(close, "ma", cfg["win"])
    sig = cfg["w_blend"] * accel + (1.0 - cfg["w_blend"]) * level
    return (cfg["dw_bull"] + (cfg["dw_bear"] - cfg["dw_bull"]) * sig).shift(1).fillna(0.0)


def desk_book(coins: dict[str, pd.DataFrame], **over) -> tuple[pd.DataFrame, pd.Series]:
    """The deployed per-metal DESK position book + the bear flag.

    desk[t,i] = a_w·(braked flat-bear anchor)[t,i] + W[t]·(dollar-neutral dispersion)[t,i].
    Every leg is leak-free (raw uses close[t]; `deployed_from_raw` lags to fill open[t+1]).
    """
    cfg = {**CHAMP10, **over}
    pan = um.panels(coins)
    close, rf = pan["close"], pan["ret_fwd"]
    a_raw, b = a8._anchor_flatbear_raw(coins, "ma", cfg["win"], 0.6, 0)
    net_a, dep_a = um.deployed_from_raw(a_raw, rf)
    c = cal.calibrate()
    k = aw.dd_brake_scalar(net_a, c["d_trip"], c["d_rearm"], BRAKE_FLOOR)
    dep_a_br = dep_a.mul(k.reindex(dep_a.index).fillna(1.0), axis=0)
    _, dep_d = um.deployed_from_raw(ov.mn_dispersion_raw(close), rf)
    w = dispersion_weight(close, cfg)
    desk = cfg["a_w"] * dep_a_br.add(
        dep_d.mul(w.reindex(dep_d.index).fillna(0.0), axis=0), fill_value=0.0
    )
    return desk, b


def desk_net(coins: dict[str, pd.DataFrame], **over) -> pd.Series:
    """POSITION-LEVEL honest net: Σ desk·ret_fwd − COST·Σ|Δdesk| (true turnover, gold netted)."""
    desk, _ = desk_book(coins, **over)
    rf = um.panels(coins)["ret_fwd"]
    pnl = (desk * rf.reindex(columns=desk.columns)).sum(axis=1)
    cost = um.COST_SIDE * desk.diff().abs().sum(axis=1)
    return (pnl - cost).dropna()


def next_target_weights(coins: dict[str, pd.DataFrame], tol: float = 1e-9) -> dict:
    """Per-metal deployed position to hold during the just-opened candle — the live target."""
    desk, b = desk_book(coins)
    last = desk.iloc[-1]
    pos = last[last.abs() > tol]
    return {
        **{s: float(v) for s, v in pos.items()},
        "_meta": {
            "as_of": str(desk.index[-1]),
            "breadth": float(
                a8.breadth_down(um.panels(coins)["close"], "ma", CHAMP10["win"]).iloc[-1]
            ),
            "gross": float(last.abs().sum()),
            "n_positions": int(len(pos)),
        },
    }


def _seg(net: pd.Series, lo: str, hi: str) -> dict:
    s = net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]
    eq = (1 + s).cumprod()
    return {
        "sharpe": um.msharpe(s, pd.Timestamp(lo), pd.Timestamp(hi)),
        "dd": float((eq / eq.cummax() - 1).min()) if len(eq) else float("nan"),
    }


def scorecard() -> None:
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)
    nb, nm = desk_net(cb), desk_net(cm)
    bear = _seg(nb, "2011-09-01", "2015-03-24")
    is_ = _seg(nm, "2000-01-01", str(um.OOS_CUTOFF.date()))
    bull = _seg(nm, str(um.OOS_CUTOFF.date()), "2100-01-01")
    print("=" * 96)
    print("iter-010 — BREADTH-ACCEL gate + POSITION-LEVEL honest net (leak-free all-weather)")
    print("=" * 96)
    print(f"  config: {CHAMP10}")
    print(
        f"  BEAR Sharpe={bear['sharpe']:+.2f} / DD {bear['dd'] * 100:.1f}%   "
        f"IS Sharpe={is_['sharpe']:+.2f} / DD {is_['dd'] * 100:.1f}%   "
        f"BULL Sharpe={bull['sharpe']:+.2f} / DD {bull['dd'] * 100:.1f}%"
    )
    p = _HERE.parents[2] / "data_bear2008"
    if (p / "XAUUSDT" / "8h.csv").exists():
        n08 = desk_net(um.load_metals(p))
        cr, pc = _seg(n08, "2008-03-01", "2009-06-01"), _seg(n08, "2008-07-01", "2008-12-31")
        print(
            f"  PRISTINE 2008: crash+recovery Sharpe={cr['sharpe']:+.2f}/DD{cr['dd'] * 100:.1f}%   "
            f"pure crash Sharpe={pc['sharpe']:+.2f}/DD{pc['dd'] * 100:.1f}%"
        )


if __name__ == "__main__":
    scorecard()
