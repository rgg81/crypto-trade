"""team-08 scratch lab — OI-price confirmation experiments (pre-registered grid only).

Usage: uv run python tournament/crypto/teams/team-08/out/scratch/oi_lab.py --exp e05 \
         --configs '[["S1g0","raw",9,9,2], ...]'   # [structure, disp, L, M, H]

Active window frozen by e04: 2022-01-01 08:00 UTC. Writes results_<exp>.json.
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
ACTIVE_LO = pd.Timestamp("2022-01-01 08:00:00")  # frozen by e04
VOL_WIN, VOL_MINP = 42, 21
ZWIN, ZMINP = 90, 45
MIN_NAMES = 10  # A2 guard: rows with fewer scored names are flat


def build_weights(pn, aux, structure, disp, L, M, H, gate_off=False) -> pd.DataFrame:
    close = pn["close"]
    elig = aux["eligibility"]
    oi = aux["oi"].where(aux["oi"] > 0)
    log_oi = np.log(oi)
    doi = log_oi - log_oi.shift(M)

    retL = close / close.shift(L) - 1.0
    if disp == "z":
        r1 = close / close.shift(1) - 1.0
        sig = r1.rolling(VOL_WIN, min_periods=VOL_MINP).std()
        d = (retL / (sig * np.sqrt(L))).clip(-3.0, 3.0)
    else:
        d = retL

    if structure in ("S1g0", "S1gm1"):
        s = d.where(elig & doi.notna())
        rk = s.rank(axis=1)
        n = rk.count(axis=1)
        c = rk.sub((n + 1) / 2.0, axis=0)
        if gate_off:
            score = c
        elif structure == "S1g0":
            score = c * (doi > 0).astype(float)
        else:
            score = c * np.sign(doi)
        n_scored = n
    elif structure == "S2":
        zden = doi.rolling(ZWIN, min_periods=ZMINP).std().replace(0.0, np.nan)
        zdoi = (doi / zden).clip(-3.0, 3.0)
        if disp != "z":
            r1 = close / close.shift(1) - 1.0
            sig = r1.rolling(VOL_WIN, min_periods=VOL_MINP).std()
            zr = (retL / (sig * np.sqrt(L))).clip(-3.0, 3.0)
        else:
            zr = d
        p = zr if gate_off else zr * zdoi
        s = p.where(elig & zdoi.notna() & zr.notna())
        score = s.sub(s.mean(axis=1), axis=0)
        n_scored = s.count(axis=1)
    else:
        raise ValueError(structure)

    score = score.where(pd.DataFrame(
        np.repeat((n_scored >= MIN_NAMES).to_numpy()[:, None], score.shape[1], axis=1),
        index=score.index, columns=score.columns))
    den = score.abs().sum(axis=1).replace(0.0, np.nan)
    w = score.div(den, axis=0).fillna(0.0)
    if H > 0:
        w = w.ewm(halflife=H, adjust=True).mean()
    return w


def run_config(pn, aux, scoring, structure, disp, L, M, H, gate_off=False) -> dict:
    raw = te.conform_raw(build_weights(pn, aux, structure, disp, L, M, H, gate_off), pn)
    lo_f, hi = tc.TRN_IS_START, tc.TRN_IS_HI

    net1, w1, p1 = te.net_series(raw, pn, scoring)
    m1a = te.evaluate(net1, w1, p1, lo=ACTIVE_LO, hi=hi)   # active window (falsifier metric)
    m1f = te.evaluate(net1, w1, p1, lo=lo_f, hi=hi)        # full window (board metric)
    net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
    m2a = te.evaluate(net2, w2, p2, lo=ACTIVE_LO, hi=hi)
    netg, wg, pg = te.net_series(raw, pn, scoring, cost_mult=0.0, slip_mult=0.0,
                                 apply_funding=False)
    mga = te.evaluate(netg, wg, pg, lo=ACTIVE_LO, hi=hi)

    return {
        "config": {"structure": structure, "disp": disp, "L": L, "M": M, "H": H,
                   "gate_off": gate_off},
        "act_gross": round(mga.sharpe, 3),
        "act_1x": round(m1a.sharpe, 3),
        "act_2x": round(m2a.sharpe, 3),
        "full_1x": round(m1f.sharpe, 3),
        "ann_turnover": round(m1a.ann_turnover, 1),
        "maxdd_act_1x": round(m1a.maxdd, 3),
        "regime_act_1x": {k: round(v, 2) for k, v in m1a.regime_sharpe.items()},
        "breadth_ls": [m1a.median_names_long, m1a.median_names_short],
        "mean_net": round(m1a.mean_net, 4),
        "funding_pnl_act": round(m1a.total_funding_pnl, 4),
        "cost_act": round(m1a.total_cost, 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--configs", required=True,
                    help='JSON list of [structure, disp, L, M, H] or [..., gate_off]')
    args = ap.parse_args()
    configs = json.loads(args.configs)

    pn, aux, scoring = te.load_is_panels()
    rows = []
    for cfg in configs:
        structure, disp, L, M, H = cfg[:5]
        gate_off = bool(cfg[5]) if len(cfg) > 5 else False
        r = run_config(pn, aux, scoring, structure, disp, int(L), int(M), float(H), gate_off)
        rows.append(r)
        c = r["config"]
        tag = " GATE-OFF" if gate_off else ""
        print(
            f"{c['structure']:<5} d={c['disp']:<3} L={c['L']:<2} M={c['M']:<2} H={c['H']:<3}{tag} | "
            f"actG {r['act_gross']:+.3f}  act1x {r['act_1x']:+.3f}  act2x {r['act_2x']:+.3f}  "
            f"full1x {r['full_1x']:+.3f} | to {r['ann_turnover']:6.1f}  dd {r['maxdd_act_1x']:+.3f}  "
            f"reg {r['regime_act_1x']}  b {r['breadth_ls']}  f {r['funding_pnl_act']:+.3f}"
        )
    (OUT / f"results_{args.exp}.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nwrote {OUT / f'results_{args.exp}.json'}")


if __name__ == "__main__":
    main()
