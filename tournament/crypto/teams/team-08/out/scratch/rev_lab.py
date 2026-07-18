"""team-08 scratch lab — short-horizon XS reversal experiments (pre-registered grid only).

Usage (from worktree root):
  uv run python tournament/crypto/teams/team-08/out/scratch/rev_lab.py --exp e01

Writes out/scratch/results_<exp>.json and prints a table. Data access: evaluator only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament")
sys.path.insert(0, str(ROOT / "analysis"))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

OUT = ROOT / "tournament/crypto/teams/team-08/out/scratch"

VOL_WIN = 42  # pre-registered: 14d rolling std of 1-candle returns
VOL_MINP = 21


def build_weights(pn, aux, L: int, volnorm: bool, kernel: str, H: float) -> pd.DataFrame:
    close = pn["close"]
    retL = close / close.shift(L) - 1.0
    if volnorm:
        r1 = close / close.shift(1) - 1.0
        sig = r1.rolling(VOL_WIN, min_periods=VOL_MINP).std()
        base = -retL / (sig * np.sqrt(L))
    else:
        base = -retL
    base = base.replace([np.inf, -np.inf], np.nan)
    s = base.where(aux["eligibility"])

    if kernel == "rank":
        rk = s.rank(axis=1)
        n = rk.count(axis=1)
        c = rk.sub((n + 1) / 2.0, axis=0)
    elif kernel == "zclip":
        mu = s.mean(axis=1)
        sd = s.std(axis=1).replace(0.0, np.nan)
        c = s.sub(mu, axis=0).div(sd, axis=0).clip(-3.0, 3.0)
    elif kernel == "rank3":
        rk = s.rank(axis=1)
        n = rk.count(axis=1)
        c = rk.sub((n + 1) / 2.0, axis=0)
        half = ((n - 1) / 2.0).replace(0.0, np.nan)
        c = c.div(half, axis=0) ** 3
    else:
        raise ValueError(kernel)

    den = c.abs().sum(axis=1).replace(0.0, np.nan)
    w = c.div(den, axis=0).fillna(0.0)
    if H > 0:
        w = w.ewm(halflife=H, adjust=True).mean()
    return w


def run_config(pn, aux, scoring, L, volnorm, kernel, H) -> dict:
    raw = te.conform_raw(build_weights(pn, aux, L, volnorm, kernel, H), pn)
    lo, hi = tc.TRN_IS_START, tc.TRN_IS_HI

    netg, wg, pg = te.net_series(raw, pn, scoring, cost_mult=0.0, slip_mult=0.0, apply_funding=False)
    mg = te.evaluate(netg, wg, pg, lo=lo, hi=hi)
    net1, w1, p1 = te.net_series(raw, pn, scoring)
    m1 = te.evaluate(net1, w1, p1, lo=lo, hi=hi)
    net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
    m2 = te.evaluate(net2, w2, p2, lo=lo, hi=hi)

    return {
        "config": {"L": L, "volnorm": volnorm, "kernel": kernel, "H": H},
        "sharpe_gross": round(mg.sharpe, 3),
        "sharpe_1x": round(m1.sharpe, 3),
        "sharpe_2x": round(m2.sharpe, 3),
        "ann_turnover": round(m1.ann_turnover, 1),
        "maxdd_1x": round(m1.maxdd, 3),
        "total_return_1x": round(m1.total_return, 3),
        "regime_1x": {k: round(v, 2) for k, v in m1.regime_sharpe.items()},
        "breadth_ls": [m1.median_names_long, m1.median_names_short],
        "mean_net": round(m1.mean_net, 4),
        "funding_pnl": round(m1.total_funding_pnl, 4),
        "cost": round(m1.total_cost, 4),
    }


EXPS = {
    # e01: existence — L grid, raw returns, rank kernel, no smoothing
    "e01": [(L, False, "rank", 0) for L in (1, 2, 3, 6, 9)],
    # e02: vol-normalized variant, same L grid
    "e02": [(L, True, "rank", 0) for L in (1, 2, 3, 6, 9)],
    # e03/e04 configs are filled at runtime from --best (staged winners)
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--configs", default="", help="JSON list of [L,volnorm,kernel,H] overrides")
    args = ap.parse_args()

    if args.configs:
        configs = [tuple(c) for c in json.loads(args.configs)]
    else:
        configs = EXPS[args.exp]

    pn, aux, scoring = te.load_is_panels()
    rows = []
    for L, volnorm, kernel, H in configs:
        r = run_config(pn, aux, scoring, int(L), bool(volnorm), str(kernel), float(H))
        rows.append(r)
        c = r["config"]
        print(
            f"L={c['L']} vn={int(c['volnorm'])} k={c['kernel']:<5} H={c['H']:<3} | "
            f"gross {r['sharpe_gross']:+.3f}  1x {r['sharpe_1x']:+.3f}  2x {r['sharpe_2x']:+.3f} | "
            f"to {r['ann_turnover']:6.1f}  dd {r['maxdd_1x']:+.3f}  "
            f"reg {r['regime_1x']}  b {r['breadth_ls']}  f {r['funding_pnl']:+.3f} c {r['cost']:+.3f}"
        )
    (OUT / f"results_{args.exp}.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nwrote {OUT / f'results_{args.exp}.json'}")


if __name__ == "__main__":
    main()
