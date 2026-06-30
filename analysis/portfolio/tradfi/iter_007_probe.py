"""iter-007 PROBE — PROPER PORTFOLIO OPTIMIZATION on the iter-005 alpha (IS-only).

USER DIRECTIVE (2026-06-30): escalate the toolkit — replace the iter-005 NAIVE cross-sectional
sector-demean weighting (w proportional to the demeaned alpha) with a mean-variance OPTIMIZER that
respects the covariance structure, plus a WEEKLY-rebalance variant. Grounded in the market-neutral
equity literature (see diary-portfolio-tradfi/iter-007-brief.md for citations).

The ONE thing that changes vs iter-005 is the WEIGHT-CONSTRUCTION MAP alpha -> w:

  iter-005 (naive):  w  =  gross_norm( alpha )                 # w proportional to demeaned alpha
  iter-007 (MVO):    w  =  argmax_w  alpha'w  -  lambda w'Sigma w
                            s.t.  1'w = 0            (dollar-neutral)
                                  |w_i| <= cap       (per-name box)
                                  ||w||_1 <= 1       (gross leverage budget)
                                  [optional]  beta'w = 0      (market-beta-neutral)
                                  [optional]  per-sector sum(w)=0  (sector-neutral; implies 1'w=0)

The ALPHA is held EXACTLY equal to iter-005's multi-horizon blend `mh_raw` (i5.mh_raw) so the only
difference measured is naive-proportional vs covariance-aware MVO. Sigma is a past-only rolling
Ledoit-Wolf shrinkage covariance of daily returns (trailing 252d, .shift(1)). The optimizer output
is fed through the SAME leak-safe `ct.net_from_raw` (gross-norm -> .shift(1) lag -> taker cost on
turnover -> portfolio vol-target) as iter-005, so the downstream accounting is apples-to-apples.

A transaction-cost-aware variant adds a turnover penalty  - gamma * ||w - w_prev||_1  to the
objective (the principled analog of iter-003's hysteresis no-trade band). A weekly variant solves
the optimizer every 5 trading days and HOLDS the weights between rebalances (no peeking).

LEAK-SAFETY: alpha uses close.shift(>=21) + trailing rvol (past-only, inherited from iter-005);
Sigma and beta use returns strictly < the decision bar (.shift(1)); the optimizer reads only
alpha_t / Sigma_t / beta_t (all past-priced) and w_prev (last rebalance); net_from_raw then applies
the standard one-bar execution lag. The optimizer is ONLY solved on decision dates < OOS_CUTOFF —
OOS is NEVER computed or printed.

Run: uv run python analysis/portfolio/tradfi/iter_007_probe.py
     uv run python analysis/portfolio/tradfi/iter_007_probe.py --smoke   # fast calibration
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import iter_005_multihorizon as i5  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

COV_WIN = 252  # 1y trailing window for the rolling Ledoit-Wolf covariance (T/N ~= 6 at N~40)
BETA_WIN = (
    63  # market-beta window (matches neutralize.rolling_beta default / iter-005 resid sleeve)
)
MIN_NAMES = 12  # require at least this many valid names to solve a rebalance (else carry/zero)


# --------------------------------------------------------------------------------------------------
# past-only inputs
# --------------------------------------------------------------------------------------------------
def build_inputs(pn):
    """Alpha (iter-005 mh_raw), daily returns, market proxy, past-only rolling betas."""
    alpha = i5.mh_raw(pn)  # EXACT iter-005 multi-horizon blend (sector-neutralized, past-only)
    ret = pn["close"].pct_change()
    mkt = ret.mean(axis=1)  # equal-weight market proxy (same as iter-005 residual sleeve)
    beta = nz.rolling_beta(ret, mkt, BETA_WIN).shift(1)  # past-only beta (lagged before use)
    return alpha, ret, beta


def precompute_cov(ret: pd.DataFrame, dates) -> dict:
    """Ledoit-Wolf shrinkage covariance for each rebalance date, using returns strictly < date.

    Past-only: the window is ret rows with index < date (the current bar's return is excluded —
    the explicit `.shift(1)` the task mandates). Returns {date: (names, Sigma ndarray)}.
    """
    cov: dict = {}
    idx = ret.index
    pos = {d: i for i, d in enumerate(idx)}
    for d in dates:
        i = pos[d]
        win = ret.iloc[max(0, i - COV_WIN) : i]  # rows strictly before d (past-only)
        if len(win) < COV_WIN:
            continue
        # names with a fully-populated trailing window AND finite at this bar
        good = win.columns[win.notna().all(axis=0)]
        if len(good) < MIN_NAMES:
            continue
        lw = LedoitWolf().fit(win[good].to_numpy())
        cov[d] = (list(good), lw.covariance_)
    return cov


# --------------------------------------------------------------------------------------------------
# the optimizer
# --------------------------------------------------------------------------------------------------
def solve_mvo(
    a: np.ndarray,
    sigma: np.ndarray,
    beta: np.ndarray | None,
    sector_idx: list[np.ndarray] | None,
    lam: float,
    cap: float,
    w_prev: np.ndarray | None,
    gamma: float,
) -> np.ndarray | None:
    """max a'w - lam w'Sigma w - gamma||w-w_prev||_1  s.t. neutral + box + gross-budget.

    Returns w on the SAME ordering as `a` (the rebalance-date names), or None if infeasible.
    """
    n = len(a)
    w = cp.Variable(n)
    obj = a @ w - lam * cp.quad_form(w, cp.psd_wrap(sigma))
    if gamma > 0 and w_prev is not None:
        obj = obj - gamma * cp.norm1(w - w_prev)
    cons = [cp.norm1(w) <= 1.0, cp.abs(w) <= cap]
    if sector_idx is not None:  # sector-neutral (per-bucket dollar zero) -> implies dollar-neutral
        for s in sector_idx:
            cons.append(cp.sum(w[s]) == 0)
    else:
        cons.append(cp.sum(w) == 0)  # dollar-neutral
    if beta is not None:
        cons.append(beta @ w == 0)  # market-beta-neutral
    prob = cp.Problem(cp.Maximize(obj), cons)
    for solver in (cp.CLARABEL, cp.OSQP, cp.SCS):
        try:
            prob.solve(solver=solver, verbose=False)
            if w.value is not None and prob.status in ("optimal", "optimal_inaccurate"):
                return np.asarray(w.value).ravel()
        except Exception:
            continue
    return None


def build_raw_opt(
    alpha: pd.DataFrame,
    cov: dict,
    beta: pd.DataFrame,
    *,
    lam: float,
    cap: float,
    freq: int,
    gamma: float,
    beta_neutral: bool,
    sector_neutral: bool,
) -> pd.DataFrame:
    """Assemble the daily raw-weight panel by solving the MVO on the rebalance schedule.

    `freq` = trading days between rebalances (1=daily, 5=weekly). Between rebalances the last solved
    book is HELD (ffill within IS). Only IS dates (< OOS_CUTOFF) are solved — OOS never computed.
    """
    is_dates = [d for d in alpha.index if d < ct.OOS_CUTOFF]
    rebal_dates = is_dates[::freq]
    cols = list(alpha.columns)
    cpos = {c: j for j, c in enumerate(cols)}
    out = pd.DataFrame(0.0, index=alpha.index, columns=cols)
    w_prev_full = np.zeros(len(cols))
    sector_groups: dict[str, list[str]] = {}
    if sector_neutral:
        for c in cols:
            sector_groups.setdefault(ut.SECTOR_MAP.get(c, f"__{c}"), []).append(c)

    last_solved = None
    for d in rebal_dates:
        if d not in cov:
            if last_solved is not None:
                out.loc[d] = last_solved
            continue
        names, sigma_full = cov[d]
        a = alpha.loc[d, names].to_numpy(dtype=float)
        m = np.isfinite(a)
        if m.sum() < MIN_NAMES:
            if last_solved is not None:
                out.loc[d] = last_solved
            continue
        names = [names[j] for j in range(len(names)) if m[j]]
        a = a[m]
        ii = np.array([cov[d][0].index(nm) for nm in names])
        sig = sigma_full[np.ix_(ii, ii)]
        b = beta.loc[d, names].to_numpy(dtype=float) if beta_neutral else None
        if b is not None and not np.isfinite(b).all():
            b = np.nan_to_num(b, nan=0.0)
        sect = None
        if sector_neutral:
            local = {nm: k for k, nm in enumerate(names)}
            sect = [np.array([local[c] for c in g if c in local]) for g in sector_groups.values()]
            sect = [s for s in sect if len(s) >= 2]  # singleton sectors -> already zero
        wp = np.array([w_prev_full[cpos[nm]] for nm in names]) if gamma > 0 else None
        w = solve_mvo(a, sig, b, sect, lam, cap, wp, gamma)
        if w is None:
            if last_solved is not None:
                out.loc[d] = last_solved
            continue
        full = np.zeros(len(cols))
        for nm, wv in zip(names, w):
            full[cpos[nm]] = wv
        out.loc[d] = full
        w_prev_full = full
        last_solved = full

    # hold between rebalances within IS (ffill); leaves OOS region at 0 (never solved)
    non_rebal = ~out.index.isin(rebal_dates)
    out.loc[non_rebal] = np.nan  # blank the hold days, then carry the last solved book
    out = out.ffill().fillna(0.0)
    out[out.index >= ct.OOS_CUTOFF] = 0.0
    return out


# --------------------------------------------------------------------------------------------------
# metrics (IS-only)
# --------------------------------------------------------------------------------------------------
def eval_raw(label: str, raw: pd.DataFrame, ret_fwd: pd.DataFrame, *, banded=False):
    """Run a raw-weight panel through the leak-safe net path; return IS-only metric bundle."""
    if banded:
        net, w = i3.banded_net(raw, ret_fwd, i3.CHOSEN_DELTA)
        gnet, _ = i3.banded_net(raw, ret_fwd, i3.CHOSEN_DELTA, cost_on=False)
    else:
        net, w = ct.net_from_raw(raw, ret_fwd)
        gross = raw.abs().sum(axis=1).replace(0, np.nan)
        wg = raw.div(gross, axis=0).fillna(0.0).shift(1)
        pnl = (wg * ret_fwd.reindex(columns=wg.columns)).sum(axis=1)
        gnet = ct.vol_target(pnl.dropna())
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    reg = ct.regime_sharpe(ct.is_only(net))
    n_pos = sum(1 for v in reg.values() if v > 0)
    turn = ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)
    mdd = ct.maxdd(ct.is_only(net)) * 100
    w_is = w[w.index < ct.OOS_CUTOFF]
    live = w_is.abs().sum(axis=1) > 1e-9
    n_active = float((w_is[live].abs() > 1e-9).sum(axis=1).mean()) if live.any() else float("nan")
    gross_mean = float(w_is[live].abs().sum(axis=1).mean()) if live.any() else float("nan")
    return {
        "label": label,
        "net": sh_net,
        "gross": sh_gross,
        "drag": sh_gross - sh_net,
        "reg": reg,
        "n_pos": n_pos,
        "turn": turn,
        "mdd": mdd,
        "n_active": n_active,
        "gross_w": gross_mean,
    }


def hold_weekly(raw: pd.DataFrame, freq: int = 5) -> pd.DataFrame:
    """Sample `raw` every `freq` IS trading days and HOLD between (ffill). OOS left at 0.

    Used to weekly-rebalance the NAIVE book without any optimizer (decide on the rebalance bar,
    carry the same target book until the next rebalance). Past-only: ffill never looks forward.
    """
    is_dates = [d for d in raw.index if d < ct.OOS_CUTOFF]
    rebal = set(is_dates[::freq])
    out = raw.copy()
    out.loc[[d for d in raw.index if d not in rebal]] = np.nan
    out = out.ffill().fillna(0.0)
    out[out.index >= ct.OOS_CUTOFF] = 0.0
    return out


def line(m):
    r = m["reg"]
    return (
        f"  {m['label']:34} net={m['net']:+.2f} gross={m['gross']:+.2f} drag={m['drag']:+.2f}  "
        f"bull={r['bull']:+.2f} bear={r['bear']:+.2f} chop={r['chop']:+.2f} ({m['n_pos']}/3)  "
        f"turn={m['turn']:.4f} mDD={m['mdd']:.0f}% gw={m['gross_w']:.2f}"
    )


# --------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="fast subset for scale calibration")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found.")
        return
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    alpha, ret, beta = build_inputs(pn)

    print("=" * 104)
    print("iter-007 PROBE — MVO optimizer on iter-005 alpha (Ledoit-Wolf cov, IS-only)")
    print("=" * 104)

    # ---- references: iter-005 naive demean through the SAME downstream ----
    m_naive_nb = eval_raw("iter-005 naive (no band)", alpha, ret_fwd, banded=False)
    m_naive_b = eval_raw("iter-005 naive (banded .005)", alpha, ret_fwd, banded=True)
    print("\n  REFERENCES (naive sector-demean weighting = w prop. to alpha):")
    print(line(m_naive_nb))
    print(line(m_naive_b) + "   <- iter-005 HEADLINE (+0.20)")

    # ---- (0) DAILY vs WEEKLY on the NAIVE working book (the task's rebalance-frequency lever,
    #          applied to the actual strategy rather than the optimizer) ----
    print("\n  (0) NAIVE book daily-vs-weekly (rebalance-frequency lever on the working strategy):")
    rows0 = []
    for fr, fl in ((5, "weekly"), (10, "biweekly")):
        held = hold_weekly(alpha, fr)
        rows0.append(eval_raw(f"naive {fl} (no band)", held, ret_fwd, banded=False))
        rows0.append(eval_raw(f"naive {fl} (banded.005)", held, ret_fwd, banded=True))
    for m in rows0:
        print(line(m))

    # ---- precompute covariance on all IS daily dates (reused across the sweep) ----
    is_dates = [d for d in alpha.index if d < ct.OOS_CUTOFF]
    if args.smoke:
        is_dates = is_dates[-260:]  # ~1y for fast calibration
    t0 = time.time()
    cov = precompute_cov(ret, is_dates)
    print(
        f"\n  precomputed Ledoit-Wolf cov for {len(cov)}/{len(is_dates)} IS dates "
        f"(win={COV_WIN}d, {time.time() - t0:.1f}s)"
    )
    if cov:
        d0 = sorted(cov)[len(cov) // 2]
        a0 = alpha.loc[d0, cov[d0][0]].to_numpy()
        print(
            f"  scale check @ {d0.date()}: N={len(cov[d0][0])}  "
            f"mean|alpha|={np.nanmean(np.abs(a0)):.3f}  "
            f"diag(Sigma) mean={np.diag(cov[d0][1]).mean():.2e}"
        )

    if args.smoke:
        print("\n  --- SMOKE: single MVO solve sanity (lam=50, cap=0.10, daily) ---")
        raw = build_raw_opt(
            alpha,
            cov,
            beta,
            lam=5e1,
            cap=0.10,
            freq=1,
            gamma=0.0,
            beta_neutral=False,
            sector_neutral=False,
        )
        print(line(eval_raw("MVO smoke", raw, ret_fwd)))
        # leak check: corrupting alpha AFTER a cutoff must not change earlier weights
        cut = is_dates[len(is_dates) // 2]
        alpha2 = alpha.copy()
        alpha2[alpha2.index >= cut] = alpha2[alpha2.index >= cut] * -3.0 + 99.0
        cov2 = precompute_cov(ret, [d for d in is_dates if d < cut])
        raw2 = build_raw_opt(
            alpha2,
            cov2,
            beta,
            lam=5e1,
            cap=0.10,
            freq=1,
            gamma=0.0,
            beta_neutral=False,
            sector_neutral=False,
        )
        a = raw[raw.index < cut].fillna(0.0)
        b = raw2[raw2.index < cut].fillna(0.0)
        common = a.index.intersection(b.index)
        leak_ok = np.allclose(a.loc[common].to_numpy(), b.loc[common].to_numpy(), atol=1e-9)
        print(
            f"  LEAK CHECK (corrupt alpha after {cut.date()} -> earlier w unchanged): "
            f"{'PASS' if leak_ok else 'FAIL'}"
        )
        return

    # ---- the sweep ----
    rows = []
    lam_grid = [0.0, 1e1, 5e1, 2e2, 1e3, 1e4]  # alpha-dominated (0) -> min-variance tilt (1e4)
    print("\n  --- (1) MVO lambda sweep, DAILY, dollar-neutral only, cap=0.15 ---")
    print("      (lambda 0 = pure-alpha-at-caps quantile book; large = min-variance tilt)")
    for lam in lam_grid:
        raw = build_raw_opt(
            alpha,
            cov,
            beta,
            lam=lam,
            cap=0.15,
            freq=1,
            gamma=0.0,
            beta_neutral=False,
            sector_neutral=False,
        )
        m = eval_raw(f"MVO lam={lam:>6.0f} cap=0.15 D", raw, ret_fwd)
        rows.append(m)
        print(line(m))

    print("\n  --- (1b) cap sweep at the two least-bad lambdas, DAILY ---")
    for lam in (0.0, 1e1):
        for cap in (0.05, 0.08, 0.25):
            raw = build_raw_opt(
                alpha,
                cov,
                beta,
                lam=lam,
                cap=cap,
                freq=1,
                gamma=0.0,
                beta_neutral=False,
                sector_neutral=False,
            )
            m = eval_raw(f"MVO lam={lam:>6.0f} cap={cap:.02f} D", raw, ret_fwd)
            rows.append(m)
            print(line(m))

    print("\n  --- (2) WEEKLY rebalance (hold between) — daily-vs-weekly at top lambdas ---")
    for lam in (0.0, 1e1, 5e1):
        raw = build_raw_opt(
            alpha,
            cov,
            beta,
            lam=lam,
            cap=0.15,
            freq=5,
            gamma=0.0,
            beta_neutral=False,
            sector_neutral=False,
        )
        m = eval_raw(f"MVO lam={lam:>6.0f} cap=0.15 W", raw, ret_fwd)
        rows.append(m)
        print(line(m))

    print("\n  --- (3) turnover-penalty (tcost-aware) DAILY, gamma sweep (cap=0.15, lam=10) ---")
    for gamma in (5e-3, 2e-2):
        raw = build_raw_opt(
            alpha,
            cov,
            beta,
            lam=1e1,
            cap=0.15,
            freq=1,
            gamma=gamma,
            beta_neutral=False,
            sector_neutral=False,
        )
        m = eval_raw(f"MVO lam=10 cap=0.15 g={gamma:.0e} D", raw, ret_fwd)
        rows.append(m)
        print(line(m))

    print("\n  --- (4) extra neutrality constraints (beta-/sector-neutral), lam=10 cap=0.15 ---")
    for bn, sn, tag in ((True, False, "+betaN"), (False, True, "+sectorN")):
        for freq, fl in ((1, "D"), (5, "W")):
            raw = build_raw_opt(
                alpha,
                cov,
                beta,
                lam=1e1,
                cap=0.15,
                freq=freq,
                gamma=0.0,
                beta_neutral=bn,
                sector_neutral=sn,
            )
            m = eval_raw(f"MVO lam=10 cap=0.15 {tag} {fl}", raw, ret_fwd)
            rows.append(m)
            print(line(m))

    # ---- summary ----
    print("\n  " + "=" * 100)
    print("  SUMMARY (sorted by IS net) — bar: net>=+0.30 promotable, all-weather>=2/3, >1.0=LEAK")
    print("  " + "=" * 100)
    print(line(m_naive_b) + "   <- iter-005 ref")
    for m in sorted(rows, key=lambda x: -x["net"]):
        promo = "PROMO" if (m["net"] >= 0.30 and m["n_pos"] >= 2) else ""
        leak = "  <<LEAK?" if m["net"] > 1.0 else ""
        beat = f"  d_vs_naive={m['net'] - m_naive_b['net']:+.2f}"
        print(line(m) + f"{beat}  {promo}{leak}")


if __name__ == "__main__":
    main()
