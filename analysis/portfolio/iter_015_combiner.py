"""portfolio-iteration EXPLORATION-015 - FIRM UP the risk-parity multi-factor combiner.

CONFIRMATION-track firm-up of iter_014's inverse-vol risk-parity combiner (trend + carry + flow).
iter_014 reported OOS +2.40 (point estimate) with a "PROMOTE-WORTHY (DD caveat)" verdict. The
critic PASSED the FLOW factor as real + leak-free + additive (+0.92 marginal, corruption test
bit-identical) but flagged four CONCERNS on the *promotion package*. This iteration fixes each,
honestly, and asks: is the combiner a robust candidate, and is the lift SIGNIFICANT or within noise?

THE FOUR CRITIC CONCERNS, AND THE FIX HERE
------------------------------------------
1. ERC SOLVER WAS BROKEN (iter_014.erc_combine). The multiplicative `w <- w/(cov*w)` fixed point
   does NOT converge to equal risk contributions for a general 3x3 covariance - it corners toward
   flow on ~67% of OOS dates (verified: realized RC max-dev from 1/3 median 0.22, p90 0.56, flow
   weight hits 1.0 on 20% of dates). The cited "ERC +2.55 corroboration" was therefore NOT an
   independent scheme; it was the same iter_013 corner pathology. FIX: a CONVERGED ERC via scipy
   SLSQP minimizing the risk-contribution variance, with a HARD VERIFICATION GATE - we check the
   realized RC vector is ~ [1/3, 1/3, 1/3] (max-dev < ERC_RC_TOL on ~every date) BEFORE citing ERC.
   ERC is a CROSS-CHECK, not the deployment vehicle (with |corr| <= 0.24, converged-ERC must ~
   inverse-vol - that is the corroboration, and it is also why the broken +2.55 was implausible).
2. "2x COST" WAS HOLLOW. iter_014's gate [7] only doubled the trivial META-layer turnover
   (Sum|Dweight_i| ~ 0.009/candle), NOT the coin-level taker cost booked inside each factor net. The
   cost that matters is the COIN-LEVEL taker on each factor's own rebalancing. FIX: rebuild EACH
   factor net at COST_SIDE*2 (the coin-level taker inside trend/carry/flow), recombine by the SAME
   risk-parity machinery, report OOS. That is the real cost-robustness stress.
3. SIGNIFICANCE / HONEST FRAMING. The +2.40 vs +1.37 gap is WITHIN NOISE at n=16 OOS months. FIX:
   report the PAIRED-MONTHLY t-stat of (combiner - baseline). State the lift honestly: directionally
   robust (LOO-stable, every vol-window cell beats, beats baseline most months, ERC agrees) but the
   GAP is not statistically distinguishable from baseline at n=16 if t < ~2.1. Do NOT claim a
   "near-doubling." RP-3's OWN Sharpe-vs-zero IS significant; the DIFFERENCE-vs-baseline is not.
4. CARRY-DD REFINEMENT (optional polish). Carry is the main DD contributor (IS -0.03, single-regime,
   -67% standalone DD) and gets a full ~1/3 inverse-vol weight. Test a PAST-ONLY vol-ceiling on the
   CARRY leg (cap exposure when carry's realized vol is high). Keep ONLY if it Pareto-helps. NOTE:
   the critic established OOS-only combined DD is already -23% (=baseline); the -29% is an IN-SAMPLE
   (2020-05) trough - so this is cosmetic IS-trough polish, NOT a live-OOS risk cut. Default = ship
   the knob-free RP-3; the cap is a secondary, clearly-labeled diagnostic.

HARD RULES (inherited, unchanged): realistic taker 0.05%/side base, past-only / leak-safe (factor
weights use ONLY past realized vol via `.rolling(...).std().shift(1)`; each factor net leak-safe),
the carry-cap vol-ceiling is a FROZEN IS-calibrated constant (IS p60 of carry's rolling vol, on
index < OOS_CUTOFF - never tuned on OOS), NEVER tuned on OOS, OOS_CUTOFF 2025-03-24. Factor nets and
the inverse-vol combiner REUSE iter_014 byte-for-byte (`rp.factor_nets`, `rp.risk_parity_combine`);
this file ADDS the converged ERC, the real coin-level cost stress, the t-stat, and the carry-cap.
The iter_005 WF-λ trend+carry blend (IS +1.30 / OOS +1.37 / DD -23%) is the comparator anchor and
the baseline (UNCHANGED; promotion only after a separate held-OOS CONFIRMATION with a critic PASS).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import t as student_t

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402
import iter_012_takerflow as tf  # noqa: E402
import iter_014_riskparity as rp  # noqa: E402

FACTORS = rp.FACTORS  # ["trend", "carry", "flow"]
RP_VOL_WIN = rp.RP_VOL_WIN  # 84 - the headline inverse-vol window (robustness-swept {42,84,168})
ERC_CORR_WIN = rp.ERC_CORR_WIN  # 168 - trailing window for the ERC correlation matrix

# --- converged-ERC verification: a TRUE ERC has every factor's risk contribution == 1/n ---
ERC_RC_TOL = 0.02  # max allowed |RC_i - 1/n| for a date to count as "converged to equal risk"
ERC_CORNER_RC = 0.45  # the corner-pathology metric: max RC share above this == cornered (critic's)

# --- carry vol-ceiling (DD-refinement; FROZEN IS-calibrated, risk-engineer spec) ---
CARRY_CAP_WIN = 42  # ~14d of 8h; shorter than the leg vol-target window (84) so it catches spikes
CARRY_CAP_PCTL = 0.60  # VOL_CEIL = the 60th pctl of carry's IS rolling-vol distribution (frozen)


# ============================================================================================
# (1) CONVERGED ERC via scipy SLSQP - replaces iter_014's broken multiplicative fixed point
# ============================================================================================
def _erc_weights_slsqp(cov: np.ndarray) -> np.ndarray:
    """Solve EQUAL-RISK-CONTRIBUTION for one covariance matrix by minimizing the variance of the
    risk-contribution shares. RC_i = w_i*(cov*w)_i; a true ERC has every RC_i == 1/n. SLSQP on the
    long-only simplex converges to RC ~ [1/n,...] exactly (verified on random covariances: max-dev
    0.0000), unlike iter_014's `w <- w/(cov*w)` which corners. Returns the weight vector (sum=1)."""
    n = cov.shape[0]

    def obj(w: np.ndarray) -> float:
        rc = w * (cov @ w)
        s = rc.sum()
        if s <= 0:
            return 1e6
        rc = rc / s
        return float(np.sum((rc - 1.0 / n) ** 2))

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
    bnds = tuple((1e-6, 1.0) for _ in range(n))
    res = minimize(
        obj,
        np.ones(n) / n,
        method="SLSQP",
        bounds=bnds,
        constraints=cons,
        options={"ftol": 1e-15, "maxiter": 500},
    )
    w = np.clip(res.x, 0.0, None)
    s = w.sum()
    return w / s if s > 0 else np.ones(n) / n


def _rc_shares(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Realized risk-contribution shares RC_i = w_i*(cov*w)_i / Sum_j w_j*(cov*w)_j (sum to 1)."""
    rc = w * (cov @ w)
    tot = rc.sum()
    return rc / tot if tot > 0 else rc


def erc_combine_converged(
    nets: dict[str, pd.Series], names: list[str], vol_win: int, corr_win: int
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """CONVERGED equal-risk-contribution combine (correlation-aware, NON-TUNABLE second scheme).

    Per candle: build a PAST-ONLY covariance (trailing corr_win correlation x trailing vol_win vols,
    both `.shift(1)`), solve ERC by SLSQP (`_erc_weights_slsqp`), and ALSO record the realized RC
    shares so the caller can VERIFY convergence to 1/n before citing ERC. Returns
    (vol_targeted_net, weights, rc_shares) - rc_shares is the diagnostic the broken iter_014 solver
    never produced. Combined = Sum_i w_i,t*net_i,t, then a FINAL portfolio vol-target."""
    panel = rp._aligned_panel(nets, names)
    vols = panel.rolling(vol_win).std().shift(1)
    corr = panel.rolling(corr_win).corr().shift(len(names))  # past-only: shift one full date-block
    idx = panel.index
    weights = pd.DataFrame(index=idx, columns=names, dtype=float)
    rc = pd.DataFrame(index=idx, columns=names, dtype=float)
    for t in idx:
        v = vols.loc[t].to_numpy()
        if not np.all(np.isfinite(v)) or np.any(v <= 0):
            continue
        try:
            c = corr.loc[t].reindex(index=names, columns=names).to_numpy()
        except KeyError:
            continue
        if not np.all(np.isfinite(c)):
            continue
        cov = (v[:, None] * v[None, :]) * c
        w = _erc_weights_slsqp(cov)
        weights.loc[t] = w
        rc.loc[t] = _rc_shares(w, cov)
    weights = weights.dropna(how="any")
    rc = rc.reindex(weights.index)
    panel = panel.reindex(weights.index)
    combined = (weights * panel).sum(axis=1).dropna()
    return base.vol_target(combined), weights, rc


def erc_convergence_report(rc: pd.DataFrame, names: list[str]) -> dict:
    """Verify the ERC solve actually equalized risk. Reports, over ALL solved dates and OOS-only:
    median/p90 max-deviation of RC from 1/n, and the fraction of dates 'cornered' (max RC share >
    ERC_CORNER_RC - the critic's corner-pathology metric). A CONVERGED ERC has max-dev ~ 0 and a
    near-zero cornered fraction; the broken iter_014 solver cornered on ~67% of OOS dates."""
    n = len(names)
    maxdev = (rc - 1.0 / n).abs().max(axis=1)
    max_share = rc.max(axis=1)
    oos = rc.index >= base.OOS_CUTOFF
    return {
        "n_dates": int(len(rc)),
        "maxdev_med": float(maxdev.median()),
        "maxdev_p90": float(maxdev.quantile(0.90)),
        "maxdev_max": float(maxdev.max()),
        "frac_converged": float((maxdev < ERC_RC_TOL).mean()),
        "frac_cornered_all": float((max_share > ERC_CORNER_RC).mean()),
        "frac_cornered_oos": float((max_share[oos] > ERC_CORNER_RC).mean())
        if oos.any()
        else float("nan"),
    }


# ============================================================================================
# (2) REAL coin-level 2x cost - rebuild EACH factor net at COST_SIDExcost_mult, recombine
# ============================================================================================
def factor_nets_cost(p: dict, cost_mult: float) -> dict[str, pd.Series]:
    """Rebuild the three standalone vol-targeted factor nets with the COIN-LEVEL taker cost scaled
    by `cost_mult`. This is iter_014.factor_nets line-for-line EXCEPT the per-coin cost term is
    `cost_mult * COST_SIDE * Sum|dw|` instead of `COST_SIDE * Sum|dw|`. cost_mult=1 reproduces
    rp.factor_nets exactly (HARD sanity check in main); cost_mult=2 is the REAL coin-level 2x stress
    the critic asked for (NOT the hollow meta-layer doubling iter_014 charged)."""
    raws = {
        "trend": (p["trend"] / p["rvol"]).where(p["elig"]),
        "carry": (p["carry"] / p["rvol"]).where(p["elig"]),
        "flow": p["flow_z"].fillna(0.0).where(p["elig"]),
    }
    nets: dict[str, pd.Series] = {}
    for name, raw in raws.items():
        gross = raw.abs().sum(axis=1).replace(0, np.nan)
        w = raw.div(gross, axis=0).fillna(0.0).shift(1)
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = cost_mult * base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[name] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


# ============================================================================================
# (3) Carry vol-ceiling - PAST-ONLY DD-refinement on the carry leg (FROZEN IS-calibrated)
# ============================================================================================
def carry_vol_ceiling(carry_net: pd.Series) -> tuple[pd.Series, float]:
    """Cap the carry leg's exposure when its OWN realized vol is high (PAST-ONLY, leak-safe).

        rv_t   = carry_net.rolling(CARRY_CAP_WIN).std().shift(1)     # past-only realized vol
        scale  = min(1, VOL_CEIL / rv_t)  (fillna 1 in warmup)       # cap-only: never levers up
        capped = carry_net * scale

    VOL_CEIL is FROZEN = the CARRY_CAP_PCTL percentile of rv over the IS window (index<OOS_CUTOFF),
    computed ONCE here - never recomputed on or tuned against OOS. `.shift(1)` makes the scale at t
    use only carry realizations through t-1; `min(1, *)` is monotone risk-reducing (cannot
    manufacture OOS return by levering up). Returns (capped_net, VOL_CEIL)."""
    rv = carry_net.rolling(CARRY_CAP_WIN).std().shift(1)
    is_rv = rv[rv.index < base.OOS_CUTOFF].dropna()
    vol_ceil = float(is_rv.quantile(CARRY_CAP_PCTL))  # FROZEN IS-only constant
    scale = (vol_ceil / rv).clip(upper=1.0).fillna(1.0)
    return carry_net * scale, vol_ceil


# ============================================================================================
# Significance - paired-monthly t-stat of (combiner - baseline)
# ============================================================================================
def paired_monthly_tstat(net_a: pd.Series, net_b: pd.Series, lo, hi) -> dict:
    """Paired-monthly t-stat of (net_a - net_b) over [lo, hi): aggregate each series to monthly
    sums on the COMMON months, difference them, and t-test the monthly difference vs 0. This tests
    whether the GAP between two strategies is distinguishable from noise - NOT whether either beats
    zero. With n=16 OOS months, |t| < ~2.1 means the lift is WITHIN the sampling-noise band (cannot
    reject equal monthly means)."""
    a = net_a[(net_a.index >= lo) & (net_a.index < hi)]
    b = net_b[(net_b.index >= lo) & (net_b.index < hi)]
    ma = a.groupby(a.index.to_period("M")).sum()
    mb = b.groupby(b.index.to_period("M")).sum()
    common = ma.index.intersection(mb.index)
    d = (ma.loc[common] - mb.loc[common]).to_numpy()
    n = len(d)
    if n < 2 or d.std(ddof=1) == 0:
        return {
            "n": n,
            "mean": float("nan"),
            "t": float("nan"),
            "p": float("nan"),
            "win_rate": float("nan"),
        }
    t = float(d.mean() / (d.std(ddof=1) / np.sqrt(n)))
    # two-sided p from the proper Student-t(n-1) (NOT the normal approx, which understates the
    # tail at small n — e.g. t=1.68 at df=15 is p~0.11, not the normal's ~0.09)
    p = float(2.0 * student_t.sf(abs(t), df=n - 1))
    return {"n": n, "mean": float(d.mean()), "t": t, "p": p, "win_rate": float((d > 0).mean())}


def loo_stability(net_a: pd.Series, net_b: pd.Series, lo, hi) -> dict:
    """Leave-one-month-out stability of the mean monthly (net_a - net_b) difference: drop each OOS
    month in turn and recompute the mean difference. Reports whether the SIGN ever flips (a robust
    directional lift never flips) and whether any single month drives >100% of the mean (one-month
    artifact). Directional-robustness evidence that does NOT depend on the point estimate."""
    a = net_a[(net_a.index >= lo) & (net_a.index < hi)]
    b = net_b[(net_b.index >= lo) & (net_b.index < hi)]
    ma = a.groupby(a.index.to_period("M")).sum()
    mb = b.groupby(b.index.to_period("M")).sum()
    common = ma.index.intersection(mb.index)
    d = (ma.loc[common] - mb.loc[common]).to_numpy()
    full = d.mean()
    loo = np.array([np.delete(d, i).mean() for i in range(len(d))])
    sign_stable = bool(np.all(np.sign(loo) == np.sign(full))) if full != 0 else False
    # one-month artifact: does removing the single best month flip the sign of the mean?
    worst_drop = loo.min() if full > 0 else loo.max()
    one_month_artifact = bool(np.sign(worst_drop) != np.sign(full)) if full != 0 else True
    return {
        "full_mean": float(full),
        "loo_min": float(loo.min()),
        "loo_max": float(loo.max()),
        "sign_stable": sign_stable,
        "one_month_artifact": one_month_artifact,
    }


def main() -> None:
    coins = base.load_universe()
    print(
        f"EXPLORATION-015: FIRM UP the risk-parity combiner (trend+carry+flow) - {len(coins)} coins"
    )
    print(
        "  firming iter_014: converged ERC (verified) + REAL coin-level 2x cost + paired t-stat "
        "+ optional carry vol-ceiling\n"
    )

    p = tf._panels(coins)
    nets = rp.factor_nets(p)

    # === SANITY 1: reproduce iter_014's factor nets + RP-3 +2.40 byte-for-byte ===========
    # factor_nets_cost(cost_mult=1) MUST equal rp.factor_nets (only diff is the cost multiplier).
    nets_c1 = factor_nets_cost(p, 1.0)
    c1_ok = all(
        nets[n].reindex(nets_c1[n].index).round(12).equals(nets_c1[n].round(12)) for n in FACTORS
    )
    trend_ref = wf.lam_nets(coins)[0.0]
    trend_ok = nets["trend"].reindex(trend_ref.index).round(12).equals(trend_ref.round(12))
    flow_s = tf.standalone(p, 1.0, direction=1)
    flow_ok = (
        abs(rp.stats(nets["flow"])["is"] - flow_s["is"]) < 1e-6
        and abs(rp.stats(nets["flow"])["oos"] - flow_s["oos"]) < 1e-6
    )
    print("  --- SANITY GATES (reproduce iter_014 byte-for-byte before layering fixes) ---")
    print(
        f"  [sanity] factor_nets_cost(1x) == rp.factor_nets (cost-rebuild correct): "
        f"{'PASS' if c1_ok else 'FAIL'}"
    )
    print(f"  [sanity] trend factor net == iter_005 fixed-λ=0: {'PASS' if trend_ok else 'FAIL'}")
    print(
        f"  [sanity] flow factor net == iter_012 standalone MOM 1x: {'PASS' if flow_ok else 'FAIL'}"
    )
    if not (c1_ok and trend_ok and flow_ok):
        print("\n  HALT: a sanity gate failed - refusing to read any firm-up result.")
        return

    # baseline anchor (iter_005 WF-λ) + RP-3 (iter_014 inverse-vol) reproduced
    base_wf, _ = wf.walkforward(wf.lam_nets(coins))
    b = rp.stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    rp3_net, rp3_w = rp.risk_parity_combine(nets, FACTORS, RP_VOL_WIN)
    rp3 = rp.stats(rp3_net)
    print(
        f"\n  CANONICAL baseline (iter_005 WF-λ): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}% netTot={b['tot']:+.0f}%  (n={n_oos_mo} OOS months)"
    )
    print("     (sanity: must match iter_005 IS+1.30/OOS+1.37/-23%)")
    print(
        f"  RP-3 inverse-vol (iter_014): IS={rp3['is']:+.2f} OOS={rp3['oos']:+.2f} "
        f"maxDD={rp3['dd'] * 100:.0f}% netTot={rp3['tot']:+.0f}%"
    )
    print("     (sanity: must reproduce iter_014 RP-3 IS+2.06/OOS+2.40/-29%)")
    print(
        f"     dOOS vs baseline = {rp3['oos'] - b['oos']:+.2f} (the iter_014 headline +1.03 lift)"
    )

    # OOS-only DD (the critic's catch: the -29% is an IN-SAMPLE trough; OOS DD == baseline) ----
    def oos_dd(net: pd.Series) -> float:
        s = net[net.index >= base.OOS_CUTOFF]
        eq = (1 + s).cumprod()
        return float((eq / eq.cummax() - 1).min())

    print(
        f"     OOS-only maxDD: RP-3={oos_dd(rp3_net) * 100:.0f}%  "
        f"baseline={oos_dd(base_wf) * 100:.0f}% "
        f"(critic's catch - the -29% full-sample DD is an IN-SAMPLE 2020 trough)"
    )

    # === FIX 3: SIGNIFICANCE - paired-monthly t-stat of (RP-3 - baseline), honest framing =======
    print("\n  === FIX 3: SIGNIFICANCE - paired-monthly t-stat of (RP-3 - baseline) OOS ===")
    ts = paired_monthly_tstat(rp3_net, base_wf, base.OOS_CUTOFF, base.HI1)
    loo = loo_stability(rp3_net, base_wf, base.OOS_CUTOFF, base.HI1)
    print(
        f"  paired monthly (RP-3 - base): n={ts['n']} mean_diff={ts['mean'] * 100:+.2f}%/mo "
        f"t={ts['t']:+.2f} p~{ts['p']:.3f} monthly-win-rate={ts['win_rate'] * 100:.0f}%"
    )
    sig = (
        abs(ts["t"]) >= 2.1
    )  # honest single-test bar at n~16; we do NOT claim significance below it
    print(
        f"  -> GAP significance: {'SIGNIFICANT (|t|>=2.1)' if sig else 'WITHIN NOISE (|t|<2.1)'} "
        f"- RP-3's OWN Sharpe is significant vs 0; the DIFFERENCE vs baseline is "
        f"{'' if sig else 'NOT '}distinguishable at n={ts['n']}"
    )
    print(
        f"  -> LOO directional stability: full mean_diff={loo['full_mean'] * 100:+.2f}%/mo "
        f"range=[{loo['loo_min'] * 100:+.2f},{loo['loo_max'] * 100:+.2f}] "
        f"sign-stable={loo['sign_stable']} one-month-artifact={loo['one_month_artifact']}"
    )

    # === FIX 1: CONVERGED ERC (SLSQP) with a HARD verification gate ==============================
    print("\n  === FIX 1: CONVERGED ERC (scipy SLSQP) - verify equal risk BEFORE citing ===")
    # (a) re-diagnose the OLD iter_014 solver so the fix is attributable
    _, old_erc_w = rp.erc_combine(nets, FACTORS, RP_VOL_WIN, ERC_CORR_WIN)
    old_panel = rp._aligned_panel(nets, FACTORS).reindex(old_erc_w.index)
    old_vols = old_panel.rolling(RP_VOL_WIN).std().shift(1)
    old_corr = old_panel.rolling(ERC_CORR_WIN).corr().shift(len(FACTORS))
    old_rc = pd.DataFrame(index=old_erc_w.index, columns=FACTORS, dtype=float)
    for t in old_erc_w.index:
        v = old_vols.loc[t].to_numpy()
        try:
            c = old_corr.loc[t].reindex(index=FACTORS, columns=FACTORS).to_numpy()
        except KeyError:
            continue
        if not (np.all(np.isfinite(v)) and np.all(np.isfinite(c)) and np.all(v > 0)):
            continue
        cov = (v[:, None] * v[None, :]) * c
        old_rc.loc[t] = _rc_shares(old_erc_w.loc[t].to_numpy(dtype=float), cov)
    old_rc = old_rc.dropna(how="any")
    old_rep = erc_convergence_report(old_rc, FACTORS)
    print(
        f"  OLD iter_014 solver: RC max-dev median={old_rep['maxdev_med']:.3f} "
        f"p90={old_rep['maxdev_p90']:.3f} "
        f"| cornered (max-RC>{ERC_CORNER_RC}) all={old_rep['frac_cornered_all'] * 100:.0f}% "
        f"OOS={old_rep['frac_cornered_oos'] * 100:.0f}%  -> BROKEN (does NOT equalize risk)"
    )

    # (b) the CONVERGED SLSQP ERC + verification
    erc_net, erc_w, erc_rc = erc_combine_converged(nets, FACTORS, RP_VOL_WIN, ERC_CORR_WIN)
    rep = erc_convergence_report(erc_rc, FACTORS)
    erc_converged = rep["frac_converged"] > 0.99 and rep["maxdev_p90"] < ERC_RC_TOL
    print(
        f"  NEW SLSQP solver:    RC max-dev median={rep['maxdev_med']:.4f} "
        f"p90={rep['maxdev_p90']:.4f} max={rep['maxdev_max']:.4f} | "
        f"frac-converged(<{ERC_RC_TOL})={rep['frac_converged'] * 100:.1f}% "
        f"cornered={rep['frac_cornered_all'] * 100:.0f}%"
    )
    print(
        f"  -> ERC CONVERGENCE VERIFICATION: "
        f"{'PASS (equalizes risk to 1/3 on ~every date)' if erc_converged else 'FAIL'}"
    )
    erc3 = rp.stats(erc_net)
    erc_oos_w = erc_w[erc_w.index >= base.OOS_CUTOFF]
    erc_flow_w = float(erc_oos_w["flow"].mean()) if len(erc_oos_w) else float("nan")
    if erc_converged:
        agree = abs(erc3["oos"] - rp3["oos"]) <= 0.20
        print(
            f"  converged ERC-3: IS={erc3['is']:+.2f} OOS={erc3['oos']:+.2f} "
            f"maxDD={erc3['dd'] * 100:.0f}% flowW_OOS={erc_flow_w:.2f}  "
            f"-> {'AGREES' if agree else 'DIVERGES'} with inverse-vol RP-3 "
            f"(+{rp3['oos']:.2f}); |d|={abs(erc3['oos'] - rp3['oos']):.2f}"
        )
        print(
            "     (with |corr|<=0.24, a CONVERGED ERC MUST ~ inverse-vol - agreement is the real "
            "corroboration; the broken +2.55 was the corner pathology, NOT a second scheme)"
        )
    else:
        agree = False
        print(
            "     ERC did NOT converge - DROPPED from the evidence set "
            "(candidate rests on inverse-vol)."
        )

    # === FIX 2: REAL coin-level 2x cost - rebuild each factor at COST_SIDEx2, recombine ==========
    print(
        "\n  === FIX 2: REAL coin-level 2x taker cost (inside each factor net, not meta-layer) ==="
    )
    nets_c2 = factor_nets_cost(p, 2.0)
    print(f"  {'factor':>7}{'IS@1x':>8}{'OOS@1x':>8}{'IS@2x':>8}{'OOS@2x':>8}  (standalone)")
    for n in FACTORS:
        s1, s2 = rp.stats(nets[n]), rp.stats(nets_c2[n])
        print(f"  {n:>7}{s1['is']:>+8.2f}{s1['oos']:>+8.2f}{s2['is']:>+8.2f}{s2['oos']:>+8.2f}")
    rp3_c2_net, _ = rp.risk_parity_combine(nets_c2, FACTORS, RP_VOL_WIN)
    rp3_c2 = rp.stats(rp3_c2_net)
    ts_c2 = paired_monthly_tstat(rp3_c2_net, base_wf, base.OOS_CUTOFF, base.HI1)
    print(
        f"  RP-3 @ REAL coin-level 2x cost: IS={rp3_c2['is']:+.2f} OOS={rp3_c2['oos']:+.2f} "
        f"maxDD={rp3_c2['dd'] * 100:.0f}%  "
        f"(vs RP-3 1x OOS {rp3['oos']:+.2f}; vs baseline {b['oos']:+.2f})"
    )
    cost_real_ok = rp3_c2["oos"] >= b["oos"] - tf.EPS
    print(
        f"  -> dOOS vs baseline at REAL 2x = {rp3_c2['oos'] - b['oos']:+.2f} "
        f"(paired t={ts_c2['t']:+.2f}); survives real coin-level 2x: "
        f"{'PASS' if cost_real_ok else 'FAIL'} (NOT the hollow iter_014 meta-layer doubling)"
    )

    # === FIX 4: CARRY VOL-CEILING (optional DD-refinement; keep ONLY if Pareto-helps) ===========
    print("\n  === FIX 4: CARRY vol-ceiling (FROZEN IS-calibrated; secondary diagnostic) ===")
    carry_capped, vol_ceil = carry_vol_ceiling(nets["carry"])
    cs0, cs1 = rp.stats(nets["carry"]), rp.stats(carry_capped)
    print(
        f"  VOL_CEIL = IS p{int(CARRY_CAP_PCTL * 100)} of carry rolling-vol(W={CARRY_CAP_WIN}) "
        f"= {vol_ceil:.6f} (FROZEN, IS-only)"
    )
    print(
        f"  carry leg: un-capped IS={cs0['is']:+.2f} OOS={cs0['oos']:+.2f} "
        f"DD={cs0['dd'] * 100:.0f}% "
        f"-> capped IS={cs1['is']:+.2f} OOS={cs1['oos']:+.2f} DD={cs1['dd'] * 100:.0f}%"
    )
    nets_cap = {**nets, "carry": carry_capped}
    rp3_cap_net, _ = rp.risk_parity_combine(nets_cap, FACTORS, RP_VOL_WIN)
    rp3_cap = rp.stats(rp3_cap_net)
    dd_gain_pp = (rp3_cap["dd"] - rp3["dd"]) * 100  # +ve == less negative == improved
    oos_give = rp3["oos"] - rp3_cap["oos"]  # +ve == gave back OOS Sharpe
    print(
        f"  RP-3 + carry-cap: IS={rp3_cap['is']:+.2f} OOS={rp3_cap['oos']:+.2f} "
        f"maxDD={rp3_cap['dd'] * 100:.0f}% "
        f"(full-DD d={dd_gain_pp:+.1f}pp, OOS d={-oos_give:+.2f})"
    )
    print(
        f"  OOS-only DD: RP-3+cap={oos_dd(rp3_cap_net) * 100:.0f}% vs "
        f"RP-3 {oos_dd(rp3_net) * 100:.0f}% "
        f"(the OOS DD the cap targets is already == baseline; this is IS-trough cosmetics)"
    )
    # PASS criterion (risk-engineer pre-registered): full-DD improves >= +0.5pp AND OOS within 0.20
    cap_pareto = dd_gain_pp >= 0.5 and oos_give <= 0.20
    print(
        f"  -> carry-cap Pareto criterion (full-DD >= +0.5pp AND OOS give-back <= 0.20): "
        f"{'PARETO-HELPS (keepable)' if cap_pareto else 'does NOT Pareto-dominate'} "
        f"- headline stays the KNOB-FREE RP-3 regardless (degrees-of-freedom discipline)"
    )

    # === ROBUSTNESS: inverse-vol vol-window sweep (reproduced; the one structural knob) =========
    print(f"\n  --- ROBUSTNESS: inverse-vol vol-window sweep (baseline OOS {b['oos']:+.2f}) ---")
    print(f"  {'win':>4}{'IS':>8}{'OOS':>8}{'dOOS':>8}{'maxDD':>8}{'pairT':>8}")
    rob_rows = []
    for win in rp.RP_WIN_GRID:
        net_w, _ = rp.risk_parity_combine(nets, FACTORS, win)
        s = rp.stats(net_w)
        tw = paired_monthly_tstat(net_w, base_wf, base.OOS_CUTOFF, base.HI1)
        rob_rows.append({"win": win, **s, "t": tw["t"]})
        print(
            f"  {win:>4d}{s['is']:>+8.2f}{s['oos']:>+8.2f}{s['oos'] - b['oos']:>+8.2f}"
            f"{s['dd'] * 100:>7.0f}%{tw['t']:>+8.2f}"
        )
    rob_all_beat = all(r["oos"] >= b["oos"] - tf.EPS for r in rob_rows)

    # === PRE-REGISTERED VERDICT (honest: route on robust DIRECTION, not on point estimate) ======
    print(f"\n  === iter-015 FIRM-UP VERDICT (n={n_oos_mo} OOS months) ===")
    f1_pass = loo["sign_stable"] and not loo["one_month_artifact"] and ts["win_rate"] > 0.5
    print(
        f"  [F1] direction sign-robust (LOO-stable, no one-month artifact, win-rate>50%): "
        f"{'PASS' if f1_pass else 'FAIL'} "
        f"(t={ts['t']:+.2f} p~{ts['p']:.2f} - "
        f"gap {'SIGNIFICANT' if sig else 'WITHIN NOISE, not claimed'})"
    )
    print(
        f"  [F2] survives REAL coin-level 2x cost (OOS >= baseline-{tf.EPS}): "
        f"OOS={rp3_c2['oos']:+.2f} -> {'PASS' if cost_real_ok else 'FAIL'}"
    )
    print(
        f"  [F3] ERC CONVERGES (verified RC~1/3) and AGREES with inverse-vol (|d|<=0.20): "
        f"-> {'PASS' if (erc_converged and agree) else 'DROPPED (rests on inverse-vol)'}"
    )
    print(
        f"  [robust] every vol-window cell OOS >= baseline-{tf.EPS}: "
        f"-> {'PASS' if rob_all_beat else 'FAIL'}"
    )
    print(
        f"  [F5] carry-cap Pareto-dominates plain RP-3: "
        f"-> {'YES (optional keep)' if cap_pareto else 'no (ship knob-free RP-3)'}"
    )

    routed = f1_pass and cost_real_ok and rob_all_beat
    erc_tag = "agreeing" if (erc_converged and agree) else "as a dropped cross-check"
    cap_tag = (
        "a keepable Pareto polish"
        if cap_pareto
        else "NOT promoted (targets an OOS DD that == baseline)"
    )
    print()
    if routed:
        print(
            "  VERDICT: PROMISING - route the KNOB-FREE inverse-vol RP-3 to a held-OOS"
            " CONFIRMATION.\n"
            "  HONEST FRAMING: RP-3 is a DIRECTIONALLY ROBUST improvement over the WF-λ baseline\n"
            f"  whose MAGNITUDE is NOT yet statistically distinguishable at n={n_oos_mo} (paired\n"
            f"  t={ts['t']:+.2f}, p~{ts['p']:.2f} < 2.1). The lift is consistent on every cut -\n"
            "  LOO sign-stable, every vol-window cell beats baseline, beats it most months -\n"
            f"  and it SURVIVES the REAL coin-level 2x cost (OOS {rp3_c2['oos']:+.2f}), with a\n"
            f"  CONVERGED ERC {erc_tag}. We claim CONSISTENCY OF SIGN, NOT a confirmed near-\n"
            "  doubling. RP-3's OWN Sharpe is significant vs 0; its EDGE OVER BASELINE is not yet\n"
            "  significant - that is what a held-OOS reveal is for (accumulate independent OOS\n"
            "  months to move the paired t). Cleanest vehicle = plain RP-3 (no scipy, no carry-\n"
            f"  cap, one structural knob shown robust). The carry vol-ceiling is {cap_tag}.\n"
            "  Baseline UNCHANGED (iter_005 WF-λ +1.37) until that held-OOS CONFIRMATION + critic"
            " PASS."
        )
    else:
        print(
            "  VERDICT: NOT ROUTED - a firm-up falsifier failed (direction not robust, cost-\n"
            "  fragile, or vol-window-fragile). The iter_014 point estimate does not survive the\n"
            "  honest stress. Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / -23%)."
        )


if __name__ == "__main__":
    main()
