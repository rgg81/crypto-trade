"""portfolio-iteration EXPLORATION-009 — per-coin |weight| CAPS on the CANONICAL net.

The quant-critic flagged concentration in the iter_005 walk-forward-λ baseline: the top-3 winner
coins supply 25.6% of OOS gross-positive PnL (ETH alone +12.2%). A per-coin |weight| cap forces
the gross-normalized book to spread across more names; it MAY trim the -23% maxDD. This iteration
adds ONE thing — a cap — and measures it on the EXACT canonical net.

CANONICAL ORDERING (iter_005, replicated byte-for-byte here):
  per-coin raw = (((1-λ)·trend + λ·carry) / rvol).where(elig)   # inverse-vol, eligibility-masked
  gross-normalize -> shift(1) -> pnl + funding_pnl - cost
  VOL-TARGET PER-λ  (base.vol_target on each λ's net SEPARATELY)
  walk-forward: pick λ on PAST vol-targeted monthly Sharpe, STITCH the already-vol-targeted test net

The ONLY change vs iter_005 is: between forming `raw` and the gross-normalize, clip the
gross-normalized per-coin weight to ±cap and renormalize gross to 1 (iterated to convergence so the
cap is actually binding). cap=inf is an exact no-op and MUST byte-reproduce iter_005's per-λ nets
(verified at startup before any capped number is trusted).

We ROBUSTNESS-sweep cap in {0.10, 0.15, 0.20, 0.25, inf}. We do NOT OOS-pick a cap: a real
diversification benefit should help (or at least not hurt) across the range. For each cap we report
IS / OOS / maxDD / per-year / turnover and a concentration metric (top-3-coin share of |PnL| and
mean effective-N = 1 / sum(w_i^2)) vs the canonical (cap=inf) baseline.

HARD RULES honored: taker 0.05%/side, all signals past-only (shift conventions identical to the
baseline), per-λ vol-target then stitch (NOT the iter_007 raw-stitch trap), λ walk-forward
unchanged, cap never tuned on OOS, OOS_CUTOFF=2025-03-24. Reuses iter_002 / iter_004 / iter_005
helpers (load_universe, load_funding, vol_target, msharpe, line, LAM_GRID, walkforward shape).
"""

from __future__ import annotations

import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

CAP_GRID = [0.10, 0.15, 0.20, 0.25, float("inf")]
_CLIP_ITERS = 50  # clip<->renormalize passes; converges fast (monotone shrink toward the cap)


def cap_renormalize(raw: pd.DataFrame, cap: float) -> pd.DataFrame:
    """Gross-normalize the per-coin raw weights to 1, clip |w_i| to `cap`, renormalize gross to 1,
    repeat until the clip is a no-op (the cap is then actually binding). All operations are within a
    single candle (row-wise) and use only same-candle quantities — no time leakage introduced.

    cap=inf returns the plain gross-normalized weights == iter_005's `raw.div(gross)` EXACTLY (the
    clip is a no-op and the loop breaks on the first pass), so the no-cap branch byte-reproduces the
    canonical baseline.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0)
    if not np.isfinite(cap):
        return w
    for _ in range(_CLIP_ITERS):
        clipped = w.clip(lower=-cap, upper=cap)
        new_gross = clipped.abs().sum(axis=1).replace(0, np.nan)
        w_next = clipped.div(new_gross, axis=0)
        # converged when no weight exceeds the cap (renormalize can't push any back over it)
        if float((w_next.abs() > cap + 1e-12).to_numpy().sum()) == 0:
            return w_next
        w = w_next
    return w


def cap_nets(coins: dict, cap: float) -> tuple[dict, dict]:
    """Per-λ vol-targeted nets AND per-λ deployed weight matrices for a given cap. Mirrors
    iter_005.lam_nets EXACTLY except for the cap_renormalize step inserted before shift(1).
    Returns ({lam: vt_net}, {lam: weights}).
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)
    nets, weights = {}, {}
    for lam in wf.LAM_GRID:
        raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
        w = cap_renormalize(raw, cap).fillna(0.0).shift(1)
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
        weights[lam] = w
    return nets, weights


def walkforward_picks(nets: dict) -> tuple[pd.Series, list]:
    """Identical to iter_005.walkforward — pick λ on the PAST vol-targeted monthly Sharpe, then
    stitch the already-vol-targeted test-month net. Returned series IS the deployable canonical net.
    """
    return wf.walkforward(nets)


def stitched_weights(nets: dict, weights: dict) -> pd.DataFrame:
    """Stitch the per-month chosen-λ DEPLOYED weight matrix using the SAME λ-selection as the net
    walk-forward (pick on PAST vol-targeted monthly Sharpe). Used for turnover + concentration so
    those diagnostics describe exactly the book that produced the headline net.
    """
    panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    cols = weights[wf.LAM_GRID[0]].columns
    parts = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= lo) & (panel.index < hi)]
        if len(train) < 200:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        wm = weights[best].reindex(columns=cols)
        wm = wm[(wm.index >= m0) & (wm.index < test_hi)]
        if not wm.empty:
            parts.append(wm)
    return pd.concat(parts).sort_index()


def per_coin_pnl(coins: dict, wfull: pd.DataFrame) -> pd.DataFrame:
    """Per-coin realized PnL contribution (price + funding - cost) of the stitched deployed book,
    so concentration is measured on the SAME weights that drove the net.
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, qv, fund):
        df.index = dt
    ret_fwd = (opens.shift(-1) / opens - 1.0).reindex(index=wfull.index, columns=wfull.columns)
    fund_next = fund.shift(-1).reindex(index=wfull.index, columns=wfull.columns)
    price_pnl = wfull * ret_fwd
    fund_pnl = -(wfull * fund_next)
    cost = base.COST_SIDE * (wfull - wfull.shift(1)).abs()
    return (price_pnl + fund_pnl - cost).fillna(0.0)


def concentration_metrics(coins: dict, wfull: pd.DataFrame, lo, hi) -> dict:
    """Top-3-coin share of |PnL| and mean effective-N (1/sum w_i^2 of the gross-normalized book) on
    [lo, hi). Effective-N is computed on the gross-normalized weights (sum|w|=1) so it is a clean
    diversification count regardless of the cap.
    """
    pnl = per_coin_pnl(coins, wfull)
    win = pnl[(pnl.index >= lo) & (pnl.index < hi)]
    coin_abs = win.abs().sum(axis=0).sort_values(ascending=False)
    total_abs = coin_abs.sum()
    top3 = float(coin_abs.head(3).sum() / total_abs) if total_abs > 0 else float("nan")
    top3_names = list(coin_abs.head(3).index)
    # mean effective-N on candles that actually hold a position
    wwin = wfull[(wfull.index >= lo) & (wfull.index < hi)]
    g = wwin.abs().sum(axis=1)
    held = g > 1e-9
    eff_n = 1.0 / (wwin[held].pow(2).sum(axis=1))
    mean_eff_n = float(eff_n.replace([np.inf, -np.inf], np.nan).dropna().mean())
    return {"top3_share": top3, "top3_names": top3_names, "eff_n": mean_eff_n}


def turnover(wfull: pd.DataFrame, lo, hi) -> float:
    w = wfull[(wfull.index >= lo) & (wfull.index < hi)]
    return float((w - w.shift(1)).abs().sum(axis=1).mean())


def verify_no_cap_reproduces(coins: dict) -> bool:
    """cap=inf per-λ nets MUST equal iter_005.lam_nets EXACTLY. Verified before any capped number is
    reported — guards against a framework drift that would invalidate the comparison.
    """
    ref = wf.lam_nets(coins)
    mine, _ = cap_nets(coins, float("inf"))
    ok = True
    for lam in wf.LAM_GRID:
        a, b = ref[lam].align(mine[lam], join="outer")
        diff = float((a.fillna(0) - b.fillna(0)).abs().max())
        flag = "OK" if diff < 1e-12 else "MISMATCH"
        if diff >= 1e-12:
            ok = False
        print(f"     λ={lam:<4} max|Δnet| = {diff:.2e}  {flag}")
    return ok


def report_row(label: str, net: pd.Series, conc_is: dict, conc_oos: dict,
               turn_is: float, turn_oos: float) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    isr = base.msharpe(net, base.LO0, base.OOS_CUTOFF)
    oosr = base.msharpe(net, base.OOS_CUTOFF, base.HI1)
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    print(f"  {label:14} IS={isr:+.2f} OOS={oosr:+.2f} maxDD={dd*100:5.0f}% "
          f"netTot={(eq.iloc[-1]-1)*100:+5.0f}%")
    print(f"     net%/yr={yr}")
    print(f"     turnover IS/OOS = {turn_is:.3f}/{turn_oos:.3f}   "
          f"effN IS/OOS = {conc_is['eff_n']:.1f}/{conc_oos['eff_n']:.1f}   "
          f"top3|PnL| IS/OOS = {conc_is['top3_share']*100:.1f}%/{conc_oos['top3_share']*100:.1f}%")
    print(f"     OOS top-3 coins by |PnL|: {conc_oos['top3_names']}")
    return {"label": label, "is": isr, "oos": oosr, "dd": dd,
            "effN_oos": conc_oos["eff_n"], "top3_oos": conc_oos["top3_share"]}


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-009: per-coin |weight| caps on the CANONICAL net — {len(coins)} candidates")
    print(f"  cap grid {CAP_GRID}  (cap=inf == iter_005 baseline)\n")

    print("  --- NO-CAP REPRODUCTION CHECK (cap=inf must byte-match iter_005.lam_nets) ---")
    if not verify_no_cap_reproduces(coins):
        print("  !!! cap=inf does NOT reproduce iter_005 — framework drift; capped numbers NOT "
              "trustworthy. ABORTING.")
        return
    print("  reproduction OK — capped numbers are on the canonical net.\n")

    print("  --- ROBUSTNESS SWEEP (cap NEVER OOS-picked) ---")
    rows = []
    baseline = None
    for cap in CAP_GRID:
        nets, weights = cap_nets(coins, cap)
        net, picks = walkforward_picks(nets)
        wfull = stitched_weights(nets, weights)
        conc_is = concentration_metrics(coins, wfull, base.LO0, base.OOS_CUTOFF)
        conc_oos = concentration_metrics(coins, wfull, base.OOS_CUTOFF, base.HI1)
        turn_is = turnover(wfull, base.LO0, base.OOS_CUTOFF)
        turn_oos = turnover(wfull, base.OOS_CUTOFF, base.HI1)
        label = "cap=inf (base)" if not np.isfinite(cap) else f"cap={cap:.2f}"
        oos_picks = Counter(b for y, b in picks if y >= 2025)
        print(f"  [λ OOS-picks {label}: {dict(sorted(oos_picks.items()))}]")
        row = report_row(label, net, conc_is, conc_oos, turn_is, turn_oos)
        if not np.isfinite(cap):
            baseline = row
        rows.append((cap, row))
        print()

    print("  === PARETO VERDICT vs canonical (cap=inf) baseline ===")
    print(f"  baseline: IS={baseline['is']:+.2f} OOS={baseline['oos']:+.2f} "
          f"maxDD={baseline['dd']*100:.0f}% effN_oos={baseline['effN_oos']:.1f} "
          f"top3_oos={baseline['top3_oos']*100:.1f}%")
    for cap, row in rows:
        if not np.isfinite(cap):
            continue
        d_oos = row["oos"] - baseline["oos"]
        d_dd = (row["dd"] - baseline["dd"]) * 100  # >0 means smaller (less negative) DD = better
        d_effn = row["effN_oos"] - baseline["effN_oos"]
        d_top3 = (row["top3_oos"] - baseline["top3_oos"]) * 100
        less_conc = d_effn > 0 or d_top3 < 0
        dd_better = d_dd > -1e-9
        oos_ok = d_oos >= -0.05  # OOS not materially worse
        pareto = less_conc and dd_better and oos_ok
        verdict = "PARETO/near-Pareto WIN" if pareto else (
            "diversifies but COSTS OOS" if less_conc and not oos_ok else "no clear benefit")
        print(f"  cap={cap:.2f}: dOOS={d_oos:+.2f} dDD={d_dd:+.0f}pt "
              f"dEffN={d_effn:+.1f} dTop3={d_top3:+.1f}pt -> {verdict}")


if __name__ == "__main__":
    main()
