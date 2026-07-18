"""team-05 scratch lab — cross-sectional taker-flow imbalance experiments.

Scratch-only (out/scratch/ is excluded from the harness scan); imports the evaluator as
authorized for scratch analysis. All data access goes through te.load_is_panels().

Usage:
  uv run python tournament/crypto/teams/team-05/out/scratch/flow_lab.py e01
"""

from __future__ import annotations

import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

OUT = "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-05/out/scratch"

# Split-half diagnostic boundaries (pre-registered in brief §6.5 as diagnostics only)
H1_LO, H1_HI = tc.TRN_IS_START, pd.Timestamp("2022-04-01")
H2_LO, H2_HI = pd.Timestamp("2022-04-01"), tc.TRN_IS_HI


def tbr_signal(pn: dict, W: int) -> pd.DataFrame:
    """Volume-weighted aggressive-buy share over trailing W candles, minus 0.5."""
    mp = int(math.ceil(0.75 * W))
    num = pn["taker_buy_quote_volume"].rolling(W, min_periods=mp).sum()
    den = pn["quote_volume"].rolling(W, min_periods=mp).sum()
    ratio = num / den.where(den > 0)
    return ratio - 0.5


def rank_weights(sig: pd.DataFrame, elig: pd.DataFrame, sign: int) -> pd.DataFrame:
    """Demeaned percentile ranks across eligible non-NaN names; NaN/inelig -> 0."""
    masked = sig.where(elig)
    r = masked.rank(axis=1, pct=True)
    w = r.sub(r.mean(axis=1), axis=0)
    return (sign * w).fillna(0.0)


def sharpen_quantile(w: pd.DataFrame, q: float) -> pd.DataFrame:
    """Keep only the top/bottom q fraction of each row's active names (by weight), re-demean."""
    active = w != 0.0
    r = w.where(active).rank(axis=1, pct=True)
    keep = (r <= q) | (r >= 1.0 - q)
    out = w.where(keep & active, 0.0)
    # re-demean over kept names so the raw book stays sum-zero
    n_keep = (out != 0.0).sum(axis=1).replace(0, np.nan)
    adj = out.sum(axis=1) / n_keep
    out = out.sub(adj, axis=0).where(out != 0.0, 0.0)
    return out.fillna(0.0)


def smooth_ema(w: pd.DataFrame, halflife: float) -> pd.DataFrame:
    return w.ewm(halflife=halflife, adjust=False).mean()


def score(raw: pd.DataFrame, pn: dict, scoring: dict) -> dict:
    raw = te.conform_raw(raw, pn)
    net1, w1, p1 = te.net_series(raw, pn, scoring)
    m1 = te.evaluate(net1, w1, p1, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
    m2 = te.evaluate(net2, w2, p2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    return {
        "sharpe_1x": round(m1.sharpe, 3),
        "sharpe_2x": round(m2.sharpe, 3),
        "maxdd_1x": round(m1.maxdd, 3),
        "ann_turnover": round(m1.ann_turnover, 1),
        "med_long": m1.median_names_long,
        "med_short": m1.median_names_short,
        "mean_net": round(m1.mean_net, 4),
        "fund_pnl": round(m1.total_funding_pnl, 4),
        "cost": round(m1.total_cost, 4),
        "totret_1x": round(m1.total_return, 3),
        "sh_bull": round(m1.regime_sharpe.get("bull", float("nan")), 2),
        "sh_bear": round(m1.regime_sharpe.get("bear", float("nan")), 2),
        "sh_chop": round(m1.regime_sharpe.get("chop", float("nan")), 2),
        "sh_half1": round(te.msharpe(net1, H1_LO, H1_HI), 3),
        "sh_half2": round(te.msharpe(net1, H2_LO, H2_HI), 3),
        "n_months": m1.n_months,
    }


def run_e01(pn, aux, scoring):
    """Pre-registered hypothesis map: H1 sign=+1 W in {6,12,21,42}; H2 sign=-1 W in
    {63,90,126,180,270}. Linear demeaned ranks, no smoothing. Also prints the OPPOSITE
    sign per cell for honesty/diagnostics (never selectable, per brief discipline)."""
    elig = aux["eligibility"]
    rows = []
    grid = [(+1, w) for w in (6, 12, 21, 42)] + [(-1, w) for w in (63, 90, 126, 180, 270)]
    for sign, W in grid:
        sig = tbr_signal(pn, W)
        res = score(rank_weights(sig, elig, sign), pn, scoring)
        res_opp = score(rank_weights(sig, elig, -sign), pn, scoring)
        band = "H1-cont" if sign > 0 else "H2-fade"
        rows.append(
            {"band": band, "sign": sign, "W": W, **res, "opp_sharpe_1x": res_opp["sharpe_1x"]}
        )
        print(f"[{band} W={W:3d}] {rows[-1]}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/results_e01.csv", index=False)
    print(df.to_string(index=False))


def run_e02(pn, aux, scoring):
    """Densify around the selected plateau: W in {15,18,21,27,33} sign=+1 linear ranks.
    DIAGNOSTIC ONLY: verifies plateau smoothness around the e01-selected W=21; does NOT
    re-select W (brief section 6 rule 3 selected on the e01 grid)."""
    elig = aux["eligibility"]
    rows = []
    for W in (15, 18, 21, 27, 33):
        res = score(rank_weights(tbr_signal(pn, W), elig, +1), pn, scoring)
        rows.append({"W": W, **res})
        print(f"[e02 W={W:3d}] {rows[-1]}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/results_e02.csv", index=False)


def run_e03(pn, aux, scoring):
    """Weight sharpening at selected W=21: top/bottom quantile q in {0.25, 0.33} vs linear.
    Adoption rule (brief 6.4a): improves BOTH tiers at W=21 AND same direction at W=12 and
    W=42 AND breadth >= floor."""
    elig = aux["eligibility"]
    rows = []
    for W in (12, 21, 42):
        base = rank_weights(tbr_signal(pn, W), elig, +1)
        rows.append({"W": W, "variant": "linear", **score(base, pn, scoring)})
        print(f"[e03 W={W} linear] {rows[-1]}", flush=True)
        for q in (0.25, 0.33):
            res = score(sharpen_quantile(base, q), pn, scoring)
            rows.append({"W": W, "variant": f"q{q}", **res})
            print(f"[e03 W={W} q={q}] {rows[-1]}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/results_e03.csv", index=False)


def run_e04(pn, aux, scoring):
    """EMA smoothing of final weights at selected W=21: halflife in {3,6,12}.
    Adoption rule (brief 6.4b): improves BOTH tiers at W=21 AND same direction at W=12/42."""
    elig = aux["eligibility"]
    rows = []
    for W in (12, 21, 42):
        base = rank_weights(tbr_signal(pn, W), elig, +1)
        rows.append({"W": W, "hl": 0, **score(base, pn, scoring)})
        print(f"[e04 W={W} hl=0] {rows[-1]}", flush=True)
        for hl in (3, 6, 12):
            res = score(smooth_ema(base, hl), pn, scoring)
            rows.append({"W": W, "hl": hl, **res})
            print(f"[e04 W={W} hl={hl}] {rows[-1]}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/results_e04.csv", index=False)


def run_e05(pn, aux, scoring):
    """Robustness diagnostics at the frozen config (no selection feedback):
    (a) min_periods 0.5W vs 0.75W; (b) base-volume TBR vs quote TBR; (c) rank without
    eligibility gate (engine still masks); (d) flow-vs-momentum rank correlation."""
    import math as _m

    elig = aux["eligibility"]
    W = 21
    rows = []

    base_sig = tbr_signal(pn, W)
    rows.append({"variant": "frozen(q,0.75W,eliggate)",
                 **score(rank_weights(base_sig, elig, +1), pn, scoring)})
    print(f"[e05 frozen] {rows[-1]}", flush=True)

    mp5 = int(_m.ceil(0.5 * W))
    num = pn["taker_buy_quote_volume"].rolling(W, min_periods=mp5).sum()
    den = pn["quote_volume"].rolling(W, min_periods=mp5).sum()
    sig_mp5 = num / den.where(den > 0) - 0.5
    rows.append({"variant": "mp=0.5W", **score(rank_weights(sig_mp5, elig, +1), pn, scoring)})
    print(f"[e05 mp0.5] {rows[-1]}", flush=True)

    mp = int(_m.ceil(0.75 * W))
    numv = pn["taker_buy_volume"].rolling(W, min_periods=mp).sum()
    denv = pn["volume"].rolling(W, min_periods=mp).sum()
    sig_v = numv / denv.where(denv > 0) - 0.5
    rows.append({"variant": "base-vol TBR", **score(rank_weights(sig_v, elig, +1), pn, scoring)})
    print(f"[e05 basevol] {rows[-1]}", flush=True)

    r_all = base_sig.rank(axis=1, pct=True)
    w_all = (r_all.sub(r_all.mean(axis=1), axis=0)).fillna(0.0)
    rows.append({"variant": "no-elig-gate-rank", **score(w_all, pn, scoring)})
    print(f"[e05 noelig] {rows[-1]}", flush=True)

    # (d) informational: cross-sectional corr of flow rank vs trailing-21-candle return rank
    mom = pn["close"] / pn["close"].shift(W) - 1.0
    fr = base_sig.where(elig).rank(axis=1, pct=True)
    mr = mom.where(elig).rank(axis=1, pct=True)
    xcorr = fr.corrwith(mr, axis=1).mean()
    print(f"[e05 diag] mean XS corr(flow rank, {W}-candle momentum rank) = {xcorr:.3f}",
          flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/results_e05.csv", index=False)
    with open(f"{OUT}/results_e05_diag.txt", "w") as f:
        f.write(f"mean_xs_corr_flow_vs_mom_{W} = {xcorr:.4f}\n")


def run_e06(pn, aux, scoring):
    """Final frozen-config confirmation, exactly as the QE SPEC will state it. Full metric
    dump at both tiers + per-regime + split-half + yearly Sharpe."""
    elig = aux["eligibility"]
    raw = rank_weights(tbr_signal(pn, 21), elig, +1)
    res = score(raw, pn, scoring)
    print(f"[e06 FROZEN W=21 linear no-smooth] {res}", flush=True)
    rawc = te.conform_raw(raw, pn)
    net1, w1, p1 = te.net_series(rawc, pn, scoring)
    for y in range(2020, 2025):
        lo, hi = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")
        hi = min(hi, tc.TRN_IS_HI)
        print(f"  {y}: msharpe={te.msharpe(net1, lo, hi):.3f}", flush=True)
    pd.DataFrame([res]).to_csv(f"{OUT}/results_e06.csv", index=False)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "e01"
    pn, aux, scoring = te.load_is_panels()
    print(f"panels loaded: {pn['open'].shape[0]} candles x {pn['open'].shape[1]} symbols",
          flush=True)
    runners = {"e01": run_e01, "e02": run_e02, "e03": run_e03, "e04": run_e04,
               "e05": run_e05, "e06": run_e06}
    if which not in runners:
        raise SystemExit(f"unknown experiment {which}")
    runners[which](pn, aux, scoring)


if __name__ == "__main__":
    main()
