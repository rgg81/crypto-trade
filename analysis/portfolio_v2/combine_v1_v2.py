"""combine_v1_v2 — OOS Sharpe of running BOTH books: v1 (top-20 trend+carry) + v2 (21-40 XS-mom).

The combined Sharpe depends on the CORRELATION of the two net streams, so we MEASURE it. Both books
are vol-targeted to the same engine TARGET_VOL, so an equal-capital 50/50 blend ~= equal-risk. The v2
risk-layer de-lever is a Sharpe-invariant scalar, so we use the base (un-de-levered) v2 here — the
combined SHARPE is identical either way; only the deployed vol/DD scale changes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import numpy as np  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

OOS = e2.OOS_CUTOFF


def _norm(s):
    return s.div(s.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def stats(net, lo=OOS, hi=e2.HI1):
    s = net[(net.index >= lo) & (net.index < hi)]
    eq = (1 + s).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return e2.msharpe(net, lo, hi), dd * 100


def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    # v1 HONEST: top-20 trend+carry+walk-forward-lambda, PIT universe + slippage
    v1 = e2.run_book(pool, rank_lo=0, rank_hi=20, season=168, slip_bps_fn=e2.default_slip_bps)["net"]
    # v2: rank-21-40 XS-mom 5-way ensemble (base vol-target; de-lever is Sharpe-invariant)
    ens = _norm(sum(_norm(_xsmom(panel["close"], elig, lb)[0]) for lb in (42, 63, 84, 126, 168)) / 5)
    v2 = e2.run_book_from_signal(
        pool, ens, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps
    )["net"]

    a, b = v1.align(v2, join="inner")
    a, b = a.fillna(0.0), b.fillna(0.0)
    oos_mask = a.index >= OOS
    corr_full = float(np.corrcoef(a.values, b.values)[0, 1])
    corr_oos = float(np.corrcoef(a[oos_mask].values, b[oos_mask].values)[0, 1])

    s1, dd1 = stats(a)
    s2, dd2 = stats(b)

    print("=" * 84)
    print("COMBINED v1 (top-20 trend+carry) + v2 (21-40 XS-mom) — OOS Sharpe")
    print("=" * 84)
    print(f"  v1 top-20  OOS Sharpe = {s1:+.2f}   maxDD(OOS) {dd1:.0f}%")
    print(f"  v2 21-40   OOS Sharpe = {s2:+.2f}   maxDD(OOS) {dd2:.0f}%")
    print(f"  correlation (net):  full={corr_full:+.3f}   OOS={corr_oos:+.3f}")
    print()
    for w in (0.5, 0.4, 0.6):
        comb = w * a + (1 - w) * b
        sc, ddc = stats(comb)
        # analytic check assuming equal vol: (wS1+(1-w)S2)/sqrt(w^2+(1-w)^2+2w(1-w)rho)
        print(f"  {int(w * 100)}/{int((1 - w) * 100)} v1/v2:  OOS Sharpe = {sc:+.2f}   maxDD(OOS) {ddc:.0f}%")
    # inverse-correlation intuition line
    print(f"\n  (equal-risk diversification ratio at OOS corr {corr_oos:+.2f}: "
          f"sqrt(2/(1+rho)) = {np.sqrt(2 / (1 + corr_oos)):.2f}x on the avg-Sharpe)")


if __name__ == "__main__":
    main()
