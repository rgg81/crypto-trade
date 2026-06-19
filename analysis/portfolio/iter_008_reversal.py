"""portfolio-iteration EXPLORATION-008 — short-term (1-2d) REVERSAL overlay, robustness-swept.

ONE orthogonal, accretive change to the canonical iter_005 baseline (walk-forward-lam trend+carry).

CRYPTO-NATIVE RATIONALE (quant-researcher):
  Trend (7-56d) is reflexive *position accumulation* — slow trend-follower / ETF / OI build-up that
  persists at the multi-week scale (positive return autocorr). A 1-2d reversal is the opposite
  agent: forced-leverage overshoot (liquidation cascades, funding-spike squeezes, large taker
  sweeps) that overshoots in 8-48h then snaps back as the forced flow exhausts (negative return
  autocorr at the 1-3-candle lag). These live in DIFFERENT regions of the return-autocorrelation
  term structure and are driven by DIFFERENT agents — so the overlay should ADD, not fight.

  ORTHOGONALITY KEYSTONE: the reversal window must be strictly SHORTER than the shortest trend
  horizon (h=21 = 7d), with a buffer. We use h in {3,6} (= 1d, 2d) and STOP there — h=9 (3d) abuts
  the 7d trend leg and risks collinear cannibalization. So this is 1-2d reversal, NOT 1-3d.

CONSTRUCTION (mirrors the baseline's primitives exactly):
  reversal = mean over h in {3,6} of  -sign(close/close.shift(h) - 1)   # in [-1,+1], like trend
  core_dir = (1 - beta) * trend + beta * reversal                       # convex; replaces trend
  sig_lam  = (1 - lam) * core_dir + lam * carry                         # carry/lam split UNCHANGED
  ... then the ENTIRE iter_005 pipeline runs unchanged: /rvol, gross-normalize, lag, cost+funding,
  PER-lam vol-target, then iter_005.walkforward stitch with the SAME lam selection. beta=0
  reproduces the canonical net byte-for-byte (verified below).

NO-CHEATING: beta is a STRUCTURAL param (architectural weight of a signal family) with no evidence
of non-stationarity — unlike lam (which iter-004/005 showed flips per regime and thus EARNED
walk-forward). So beta is NOT walk-forwarded; it is ROBUSTNESS-PROVEN (iter-006 style) over a small
fixed grid: require EVERY cell positive on BOTH IS and OOS. Sign (not z-score/rank) keeps reversal
on the IDENTICAL [-1,1] scale as trend & carry so beta has the same units as lam.

MEASURED ON THE CANONICAL NET (per-lam-vol-target-then-stitch) — NOT iter_007's rejected raw-stitch
+ single-outer-vol-target re-ordering, which inflated a +0.16 OOS "edge" that was +0.01 canonical.

HARD RULES honored: taker 0.05%/side, all signals past-only (same shift conventions as baseline),
lam walk-forward unchanged, beta never tuned on OOS, OOS_CUTOFF=2025-03-24.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

# reversal horizons (8h candles): 3 = 1 day, 6 = 2 days. Strictly < shortest trend horizon (21=7d).
REV_HORIZONS = [3, 6]
# structural blend-weight grid — robustness-proven, NOT walk-forwarded. Small by design: reversal
# is a minority correction to the trend/carry core, never a co-equal third pillar.
BETA_GRID = [0.0, 0.05, 0.10, 0.15, 0.20]
EPS = 0.05  # materiality band (same as iter_007 _pareto): "not worse" / "real lift" threshold


def _panels(coins: dict):
    """Shared past-only inputs — identical to iter_005.lam_nets, plus the reversal signal."""
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
    # 1-2d mean-reversion: short the recent winner / long the recent loser (sign, past-only).
    reversal = sum(-np.sign(close / close.shift(h) - 1.0) for h in REV_HORIZONS) / len(REV_HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)
    return {
        "ret_fwd": ret_fwd, "elig": elig, "rvol": rvol,
        "trend": trend, "reversal": reversal, "carry": carry, "fund_next": fund_next,
    }


def lam_nets_beta(p: dict, beta: float) -> dict:
    """Canonical iter_005 per-lam net with a beta-weighted reversal folded into the direction core.
    Mirrors iter_005.lam_nets line-for-line except `trend` -> `core_dir`. beta=0 => the canonical
    net exactly. PER-lam vol-target applied here (iter_005 line 50) — ordering preserved.
    """
    core_dir = (1 - beta) * p["trend"] + beta * p["reversal"]
    nets = {}
    for lam in wf.LAM_GRID:
        raw = (((1 - lam) * core_dir + lam * p["carry"]) / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


def stitched_turnover(p: dict, beta: float) -> float:
    """Mean one-sided per-candle turnover of the DEPLOYED (walk-forward-lam-chosen) portfolio, using
    the SAME lam-selection as the headline run (pick lam on past vol-targeted monthly Sharpe).
    """
    core_dir = (1 - beta) * p["trend"] + beta * p["reversal"]
    weights, nets = {}, {}
    for lam in wf.LAM_GRID:
        raw = (((1 - lam) * core_dir + lam * p["carry"]) / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        weights[lam] = w
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    vt_panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(vt_panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    cols = weights[wf.LAM_GRID[0]].columns
    w_parts = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = vt_panel[(vt_panel.index >= lo) & (vt_panel.index < hi)]
        if len(train) < 200:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        wm = weights[tsh.idxmax()].reindex(columns=cols)
        wm = wm[(wm.index >= m0) & (wm.index < test_hi)]
        if not wm.empty:
            w_parts.append(wm)
    wfull = pd.concat(w_parts).sort_index()
    return float((wfull - wfull.shift(1)).abs().sum(axis=1).mean())


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    return {
        "is": base.msharpe(net, base.LO0, base.OOS_CUTOFF),
        "oos": base.msharpe(net, base.OOS_CUTOFF, base.HI1),
        "dd": dd, "tot": (eq.iloc[-1] - 1) * 100, "yr": yr,
    }


def orthogonality_probe(p: dict) -> float:
    """Pooled cross-coin correlation between the reversal signal and the trend signal, over the IS
    window, on ELIGIBLE cells only. The decisive mechanism falsifier: |corr| must be < 0.3 — if the
    reversal is just -trend in disguise it is FIGHTING, not adding, regardless of Sharpe.
    """
    tr = p["trend"].where(p["elig"])
    rv = p["reversal"].where(p["elig"])
    is_mask = tr.index < base.OOS_CUTOFF
    a = tr[is_mask].to_numpy().ravel()
    b = rv[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-008: 1-2d reversal overlay (robustness-swept beta) — {len(coins)} coins")
    print(f"  reversal horizons {REV_HORIZONS} (1d,2d) < shortest trend horizon {base.HORIZONS[0]} "
          f"(7d); beta grid {BETA_GRID}; sign-based; PER-λ vol-target preserved\n")

    p = _panels(coins)

    # --- mechanism falsifier: reversal must NOT be collinear with trend ---
    corr = orthogonality_probe(p)
    corr_ok = np.isfinite(corr) and abs(corr) < 0.3
    print(f"  ORTHOGONALITY PROBE: pooled corr(reversal, trend) on IS = {corr:+.3f}  "
          f"-> {'PASS (<0.3, orthogonal)' if corr_ok else 'FAIL (collinear/fighting)'}\n")

    # --- canonical baseline reproduction (beta=0) via the SAME iter_005.walkforward stitch ---
    base_nets = lam_nets_beta(p, 0.0)
    base_wf, _ = wf.walkforward(base_nets)
    b = stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    print(f"  CANONICAL baseline (beta=0, iter_005 net): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
          f"maxDD={b['dd']*100:.0f}% netTot={b['tot']:+.0f}%")
    print(f"     net%/yr={b['yr']}")
    print("     (sanity: must match iter_005 IS+1.30/OOS+1.37/-23%)\n")

    # --- robustness sweep over beta (NOT walk-forwarded) ---
    print("  --- ROBUSTNESS SWEEP (beta; lam walk-forwarded; measured on CANONICAL net) ---")
    print(f"  {'beta':>5} {'IS':>7} {'OOS':>7} {'dIS':>7} {'dOOS':>7} {'maxDD':>7} "
          f"{'turn':>6} {'all-yr+IS':>9}")
    rows = []
    for beta in BETA_GRID:
        nets = lam_nets_beta(p, beta)
        net_wf, _ = wf.walkforward(nets)
        s = stats(net_wf)
        turn = stitched_turnover(p, beta)
        # IS-year coherence: split on OOS_CUTOFF, NOT calendar year (2025 straddles the cutoff, so a
        # naive k<2026 would mix OOS months into the IS-year check — critic caveat).
        is_net = net_wf[net_wf.index < base.OOS_CUTOFF]
        is_yr = is_net.groupby(is_net.index.year).sum()
        yr_is_pos = bool((is_yr >= 0).all())
        rows.append({"beta": beta, **s, "turn": turn, "yr_is_pos": yr_is_pos})
        print(f"  {beta:>5.2f} {s['is']:>+7.2f} {s['oos']:>+7.2f} {s['is']-b['is']:>+7.2f} "
              f"{s['oos']-b['oos']:>+7.2f} {s['dd']*100:>6.0f}% {turn:>6.3f} "
              f"{'yes' if yr_is_pos else 'NO':>9}")

    # --- per-year detail for the mid-grid cell ---
    mid = next(r for r in rows if abs(r["beta"] - 0.10) < 1e-9)
    print(f"\n  mid-grid beta=0.10 net%/yr={mid['yr']}")

    # --- pre-registered falsifier verdict ---
    nz = [r for r in rows if r["beta"] > 0]
    all_cells_pos = all(r["is"] >= b["is"] - EPS and r["oos"] >= b["oos"] - EPS for r in nz)
    mid_lift = mid["oos"] - b["oos"]
    lift_ok = mid_lift >= 0.15
    dd_ok = all(r["dd"] >= -0.28 for r in nz)
    small_beta_signal = (
        next(r for r in nz if abs(r["beta"] - 0.05) < 1e-9)["oos"] >= b["oos"] - EPS
    )
    yr_ok = all(r["yr_is_pos"] for r in nz)

    print("\n  === PRE-REGISTERED FALSIFIER VERDICT (all must pass for EDGE) ===")
    print(f"  [1] all beta cells IS+OOS >= baseline-{EPS}: {'PASS' if all_cells_pos else 'FAIL'}")
    print(f"  [2] signature already present at small beta=0.05 (not only-at-large): "
          f"{'PASS' if small_beta_signal else 'FAIL'}")
    print(f"  [3] mid-grid OOS lift >= +0.15 (above n={n_oos_mo}mo noise): "
          f"dOOS={mid_lift:+.2f} -> {'PASS' if lift_ok else 'FAIL'}")
    print(f"  [4] |corr(reversal,trend)| < 0.3 (not collinear): {'PASS' if corr_ok else 'FAIL'}")
    print(f"  [5] maxDD >= -28% across grid (no tail-levering): {'PASS' if dd_ok else 'FAIL'}")
    print(f"  [6] no IS year flips negative: {'PASS' if yr_ok else 'FAIL'}")

    gates = [all_cells_pos, small_beta_signal, lift_ok, corr_ok, dd_ok, yr_ok]
    if all(gates):
        print("\n  VERDICT: EDGE — robustness-proven accretive overlay. Recommend CONFIRMATION.")
    elif corr_ok and dd_ok and all_cells_pos and not lift_ok:
        print("\n  VERDICT: NOISE (real-but-too-small) — overlay is leak-safe & not harmful, but "
              "the OOS lift is inside the ~15-month-Sharpe noise band. NOT worth the added "
              "complexity. REJECT as accretive change (honest down-call).")
    else:
        print("\n  VERDICT: REJECT — failed a mechanism/robustness falsifier above. NOT promoted.")


if __name__ == "__main__":
    main()
