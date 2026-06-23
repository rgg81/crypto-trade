"""portfolio-iteration-v2 iter-v2-010 — short-term cross-sectional REVERSAL (OOS HIDDEN).

Last clear literature lead (RESEARCH_notes #6: reversal alive in crypto; #3: momentum is 1-4wk so
SHORTER horizons reverse). Different signal class from the XS-mom baseline (medium-horizon momentum):
short-horizon (1-2 day) cross-sectional REVERSAL — SHORT recent winners / LONG recent losers. If it has
a recent (LATE) edge AND is negatively correlated with the XS-mom ensemble, it composes as a 2nd sleeve.

DISCIPLINE: OOS is HIDDEN here (the baseline's deflated significance is already moderate after ~30
revealed configs; do NOT burn more OOS). Judge on IS + EARLY/LATE + turnover + 2x-taker LATE only. If it
clears the LATE bar leak-safely, flag for a SINGLE future OOS reveal — do not reveal now.

Run:  uv run python analysis/portfolio_v2/iter_v2_010_reversal.py
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
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

EARLY_LO, EARLY_HI = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
LATE_LO = pd.Timestamp("2024-01-01")
OOS = e2.OOS_CUTOFF


def _norm(s):
    return s.div(s.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def era(net):
    return e2.msharpe(net, EARLY_LO, EARLY_HI), e2.msharpe(net, LATE_LO, OOS)


def line(label, res):
    e_, l_ = era(res["net"])
    is_ = e2.msharpe(res["net"], e2.LO0, OOS)
    print(f"  {label:30} IS={is_:+.2f} EARLY={e_:+.2f} LATE={l_:+.2f} turn={res['turnover']:.3f}")
    return l_


def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    close = panel["close"]

    def rev(k):
        # short-horizon reversal: SHORT recent winners (negate the centered k-return rank)
        mom = close / close.shift(k) - 1.0
        rk = mom.where(elig).rank(axis=1)
        n = elig.sum(axis=1)
        sig = rk.sub(n.add(1) / 2.0, axis=0).div(n, axis=0).where(elig).fillna(0.0)
        return _norm(-sig)

    ens = _norm(sum(_norm(_xsmom(close, elig, lb)[0]) for lb in (42, 63, 84, 126, 168)) / 5)

    def run(sig, **kw):
        return e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    print("=" * 96)
    print("iter-v2-010 — short-term cross-sectional REVERSAL (OOS HIDDEN), rank 21-40")
    print("=" * 96)
    print("  baseline XS-mom ensemble LATE +1.46 (turn 0.157)")
    print("\n[reversal standalone — K candles; expect HIGH turnover]")
    ens_net = run(ens)["net"]
    for k in (1, 3, 6):
        res = run(rev(k))
        line(f"reversal K={k}", res)
        line(f"reversal K={k} 2x-taker", run(rev(k), cost_mult=2.0))
        rn = res["net"]
        c = ens_net.align(rn, join="inner")
        print(f"     corr(ens, rev K={k}) = {float(np.corrcoef(c[0].values, c[1].values)[0, 1]):+.3f}")

    print("\n[combine ensemble + reversal K=3, weight sweep]")
    for w in (0.2, 0.35):
        line(f"ens*(1-{w}) + revK3*{w}", run(_norm((1 - w) * ens + w * rev(3))))

    print("\n[read — OOS HIDDEN] reversal earns a future OOS reveal ONLY if it lifts LATE leak-safely")
    print("  AND survives 2x-taker (high turnover is the risk) AND is uncorrelated with the ensemble.")


if __name__ == "__main__":
    main()
