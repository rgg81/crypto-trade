"""portfolio-iteration-v2 iter-v2-005 — REGIME / FACTOR-MOMENTUM ROUTING (trend <-> XS-mom).

The robust finding across iter-001..004: TREND owns the EARLY regime (EARLY Sharpe ~+2.1) and XS-mom
owns the LATE regime (LATE +1.36), temporally separated. A fixed blend (iter-002) and an L2 ML combine
(iter-003) both LOST to the ingredients. The untried vehicle: ROUTE between them with FACTOR MOMENTUM —
hold whichever factor has been winning over a trailing window (past-only). Goal: capture EARLY from
trend AND LATE from XS-mom in one adaptive book.

Mechanism (PAST-ONLY): compute each factor's standalone per-candle net; at candle t the routing weight
on trend r[t] is set from the factors' TRAILING-W performance known at t-1 (hard switch or soft
logistic); combined_signal[t] = r[t]*trend[t] + (1-r[t])*xs[t] -> run_book_from_signal. No future info
(routing reads only past net; the engine lags the whole signal once more via w=.shift(1)).

Run:  uv run python analysis/portfolio_v2/iter_v2_005_route.py [--reveal]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402
from portfolio_v2.engine_v2 import _signals, _xsmom, build_panel  # noqa: E402

REVEAL = "--reveal" in sys.argv
EARLY_LO, EARLY_HI = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
LATE_LO, LATE_HI = pd.Timestamp("2024-01-01"), e2.OOS_CUTOFF


def era(net):
    return e2.msharpe(net, EARLY_LO, EARLY_HI), e2.msharpe(net, LATE_LO, LATE_HI)


def _norm(sig: pd.DataFrame) -> pd.DataFrame:
    """Per-candle unit-L1 normalization so trend and xs are comparable in the blend."""
    return sig.div(sig.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def line(label, res, *, show_oos=False):
    net = res["net"]
    e_, l_ = era(net)
    is_ = e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF)
    oos = f"  OOS={e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1):+.2f}" if (show_oos and REVEAL) else ""
    print(f"  {label:34} IS={is_:+.2f} EARLY={e_:+.2f} LATE={l_:+.2f} turn={res['turnover']:.3f}{oos}")
    print(f"     per-year={per_year_sharpe(net)}")


def main():
    print("=" * 100)
    print("iter-v2-005 — factor-momentum ROUTING trend<->XS-mom, rank 21-40 (OOS hidden)")
    print("=" * 100)
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    sig = _signals(panel)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    trend = _norm(sig["trend"].where(elig).fillna(0.0))
    xs, _ = _xsmom(panel["close"], elig, 84)
    xs = _norm(xs)
    idx = trend.index

    def run(sigp, **kw):
        return e2.run_book_from_signal(
            pool, sigp, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    anc = e2.run_book(pool, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps)
    res_t, res_x = run(trend), run(xs)
    line("anchor (trend+carry λ)", anc)
    line("trend-only", res_t)
    line("xs-only", res_x)
    anc_e, anc_l = era(anc["net"])
    tnet, xnet = res_t["net"], res_x["net"]

    def make_combined(window: int, hard: bool, k: float = 8.0):
        tp = tnet.rolling(window).mean().shift(1).reindex(idx).ffill()
        xp = xnet.rolling(window).mean().shift(1).reindex(idx).ffill()
        diff = (tp - xp).fillna(0.0)
        if hard:
            r = (diff >= 0).astype(float)
        else:
            scale = diff.abs().rolling(252).mean().shift(1).reindex(idx).ffill().replace(0, np.nan)
            z = (diff / scale).clip(-6, 6)
            r = pd.Series(1.0 / (1.0 + np.exp(-k * z)), index=idx).fillna(0.5)
        combined = trend.mul(r, axis=0) + xs.mul(1.0 - r, axis=0)
        lx = float((1.0 - r[(idx >= LATE_LO) & (idx < LATE_HI)]).mean())
        return combined, lx

    print("\n[routing sweep — W = factor-perf lookback]")
    best = None
    for window in (63, 126, 189):
        for hard in (True, False):
            combined, lx = make_combined(window, hard)
            res = run(combined)
            _, l_ = era(res["net"])
            line(f"route W={window} {'hard' if hard else 'soft'} (LATE->xs {lx:.0%})", res)
            if best is None or l_ > best[0]:
                best = (l_, window, hard, combined, res)

    l_, window, hard, combined, res = best
    print(
        f"\n[best LATE] route W={window} {'hard' if hard else 'soft'}: LATE={l_:+.2f} "
        f"(anchor {anc_l:+.2f}); cost stress:"
    )
    line("  default", res, show_oos=True)
    line("  2x taker", run(combined, cost_mult=2.0), show_oos=True)
    line(
        "  pessimistic slip",
        e2.run_book_from_signal(
            pool, combined, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=slip_pessimistic
        ),
        show_oos=True,
    )

    print("\n[gate read — IS + LATE only]")
    is_b = e2.msharpe(res["net"], e2.LO0, e2.OOS_CUTOFF)
    e_b, _ = era(res["net"])
    print(f"  anchor  IS +1.53  EARLY {anc_e:+.2f}  LATE {anc_l:+.2f}")
    print(
        f"  routed  IS {is_b:+.2f}  EARLY {e_b:+.2f}  LATE {l_:+.2f}  "
        f"ΔIS {is_b - 1.53:+.2f}  ΔLATE {l_ - anc_l:+.2f}"
    )
    print(f"  G_IS (routed IS >= +1.53): {'PASS' if is_b >= 1.53 else 'FAIL'}")
    print(f"  G2   (ΔLATE >= +0.20):     {'PASS' if (l_ - anc_l) >= 0.20 else 'FAIL'}")


if __name__ == "__main__":
    main()
