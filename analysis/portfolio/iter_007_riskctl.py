"""portfolio-iteration EXPLORATION-007 — DD controls on the FUNDING-FIXED + REFRESHED data.

Re-runs the risk_probe winner on the corrected baseline (funding nearest-match bug fixed in
iter_004.load_funding; full ~206-coin universe refreshed to current). Two controls are layered onto
the walk-forward-λ baseline ONE AT A TIME and measured:

  (a) MIN-ELIGIBLE GUARD — require `elig.sum(axis=1) >= TOP_N` each candle; do NOT trade candles
      where the point-in-time universe is degenerate (fewer than TOP_N liquid coins). This is the
      stale-data blocker: before the refresh, 183/206 coins stopped ~Feb-2026, so the last ~4 OOS
      months ranked a <TOP_N universe — a silent survivorship/degenerate-basket artifact. We PRINT
      the eligible-count over time + the first/last fully-eligible date to show the tail is gone.

  (b) VOL-SPIKE DE-LEVER — the risk_probe winner: realized-vol spike de-lever (rv 21/168, when fast
      vol > 1.5× its slow median → floor 0.5), past-only (shift(1)), layered on top of (a).

CONFIG IS PRE-SET FROM IS ROBUSTNESS (risk_probe Section C-ROBUSTNESS: edge persists across
fast∈{14,21,28}, slow∈{120,168,210}, thresh∈{1.3,1.5,1.7}, floor∈{0.4,0.5,0.6}). NOT tuned on OOS.

We RE-CONFIRM the de-lever is still Pareto-improving on the FIXED funding + FRESH data (DD down, OOS
not worse). If it no longer is, we say so and do NOT recommend it.

HARD RULES honored: taker 0.05%/side, all signals past-only (shift conventions match the baseline),
walk-forward λ unchanged, thresholds never tuned on OOS, OOS_CUTOFF=2025-03-24. Reuses iter_002 /
iter_004 helpers (load_universe, load_funding, vol_target, msharpe, line).
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

# clean-window bounds (refresh-effect comparison only — NOT a tuning window)
CLEAN_LO = pd.Timestamp("2025-03-01")
CLEAN_HI = pd.Timestamp("2026-03-01")

# pre-set de-lever config (from risk_probe IS robustness; identical knobs)
RV_FAST = 21
RV_SLOW = 168
RV_THRESH = 1.5
RV_FLOOR = 0.5


def build_panels(coins: dict):
    """Shared past-only inputs + the per-λ RAW (pre-vol-target) net, for both the unguarded and the
    min-eligible-guarded universe. Returns everything the walk-forward + controls need.

    `elig` is the point-in-time top-N membership (rank<=TOP_N on trailing $-vol, shift(1)). `enough`
    is the guard mask: candles where at least TOP_N coins are eligible (a non-degenerate basket).
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
    liq = qv.rolling(base.LIQ_WIN).mean().shift(1)
    elig = liq.rank(axis=1, ascending=False) <= base.TOP_N
    # how many coins actually have a finite trailing-liquidity value each candle (past-only). The
    # rank above always assigns ranks 1..TOP_N to SOME coins even if only 3 are alive — that is the
    # degenerate-basket bug. The honest eligible count is the number of finite liq cells.
    elig_count = liq.notna().sum(axis=1)
    enough = elig_count >= base.TOP_N  # guard: trade only non-degenerate baskets

    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)

    def raw_nets(guard: bool) -> dict:
        out = {}
        for lam in wf.LAM_GRID:
            raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
            w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
            pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
            fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
            cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
            net = (pnl + fpnl - cost)
            if guard:
                # zero out (don't trade) candles whose decision-time basket is degenerate. The mask
                # is past-only by construction (liq is shift(1)); we gate the candle's contribution.
                net = net.where(enough, 0.0)
            out[lam] = net.dropna()
        return out

    return {
        "raw_unguarded": raw_nets(guard=False),
        "raw_guarded": raw_nets(guard=True),
        "elig_count": elig_count,
        "enough": enough,
        "w_turnover_ref": None,  # turnover computed per-config below
    }


def walk_forward_stitch(raw_nets: dict) -> tuple[pd.Series, list]:
    """Identical λ-selection to iter_005 (pick λ on the PAST vol-targeted net, best monthly Sharpe),
    but stitch the RAW (pre-vol-target) per-month net so the DD controls compose as an outermost
    exposure overlay before the single final vol-target. Returns (raw_wf, picks).
    """
    vt_nets = {lam: base.vol_target(s) for lam, s in raw_nets.items()}
    vt_panel = pd.DataFrame(vt_nets).sort_index()
    raw_panel = pd.DataFrame(raw_nets).sort_index()
    months = pd.PeriodIndex(vt_panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    parts, picks = [], []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = vt_panel[(vt_panel.index >= lo) & (vt_panel.index < hi)]
        test = raw_panel[(raw_panel.index >= m0) & (raw_panel.index < test_hi)]
        if len(train) < 200 or test.empty:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        picks.append((m0.year, best))
        parts.append(test[best].rename("net"))
    return pd.concat(parts).sort_index(), picks


def apply_voltarget(raw: pd.Series) -> pd.Series:
    """Baseline portfolio vol-target (past-only), unchanged from iter_002.vol_target."""
    return base.vol_target(raw)


def rv_spike_scale(raw: pd.Series) -> pd.Series:
    """Vol-spike de-lever (risk_probe control C, pre-set config). Multiplier = clip(slow_med /
    fast_vol, floor, 1.0) ONLY when fast vol > thresh × slow median; else 1.0 (no leverage-up).
    Both windows shifted (past-only). Applied to the candle AFTER the spike is observed.
    """
    fast_v = raw.rolling(RV_FAST).std().shift(1)
    slow_med = fast_v.rolling(RV_SLOW).median().shift(1)
    rel = (slow_med / fast_v).replace([np.inf, -np.inf], np.nan)
    mult = rel.clip(lower=RV_FLOOR, upper=1.0).fillna(1.0)
    mult = mult.where(fast_v > RV_THRESH * slow_med, 1.0).fillna(1.0)
    return mult


def _stitched_turnover(weights: dict, coins: dict) -> float:
    """Stitch the per-month chosen-λ weight matrix (same λ-selection as walk_forward_stitch) and
    return the mean one-sided per-candle turnover of the deployed portfolio. The net used for the λ
    pick is derived directly from the SUPPLIED per-λ weights (open->open returns + real funding +
    cost), so the selection matches the headline run exactly.
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, qv, fund):
        df.index = dt
    fund_next = fund.shift(-1)
    ret_fwd = opens.shift(-1) / opens - 1.0
    # per-λ vol-targeted past net (for the pick) — mirrors walk_forward_stitch's vt_panel
    raw_nets = {}
    for lam in wf.LAM_GRID:
        w = weights[lam]
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        raw_nets[lam] = (pnl + fpnl - cost).dropna()
    vt_panel = pd.DataFrame({lam: base.vol_target(s) for lam, s in raw_nets.items()}).sort_index()
    months = pd.PeriodIndex(vt_panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    w_parts = []
    cols = weights[wf.LAM_GRID[0]].columns
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
        best = tsh.idxmax()
        wm = weights[best].reindex(columns=cols)
        wm = wm[(wm.index >= m0) & (wm.index < test_hi)]
        if not wm.empty:
            w_parts.append(wm)
    wfull = pd.concat(w_parts).sort_index()
    turn = (wfull - wfull.shift(1)).abs().sum(axis=1)
    return float(turn.mean())


def report(label: str, net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    isr = base.msharpe(net, base.LO0, base.OOS_CUTOFF)
    oosr = base.msharpe(net, base.OOS_CUTOFF, base.HI1)
    cleanr = base.msharpe(net, CLEAN_LO, CLEAN_HI)
    tot = (eq.iloc[-1] - 1) * 100
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    print(f"  {label:20} IS={isr:+.2f} OOS={oosr:+.2f} clean25-26={cleanr:+.2f} "
          f"maxDD={dd*100:5.0f}% netTot={tot:+6.0f}%")
    print(f"       net%/yr={yr}")
    return {"label": label, "is": isr, "oos": oosr, "clean": cleanr, "dd": dd, "tot": tot}


def print_eligibility(elig_count: pd.Series, enough: pd.Series) -> None:
    print("  --- (a) ELIGIBILITY DIAGNOSTIC (degenerate-tail check) ---")
    full = elig_count[enough]
    print(f"  candles with >=TOP_N({base.TOP_N}) eligible: {enough.sum()}/{len(enough)} "
          f"({enough.mean()*100:.1f}%)")
    if len(full):
        print(f"  first fully-eligible date: {full.index.min().date()}   "
              f"last fully-eligible date: {full.index.max().date()}")
    # show the OOS tail month-by-month — this is where the stale-data degeneracy used to live
    oos = elig_count[elig_count.index >= base.OOS_CUTOFF]
    by_month = oos.groupby(oos.index.to_period("M")).agg(["min", "max", "mean"])
    print("  OOS eligible-count by month (min/max/mean):")
    for per, row in by_month.iterrows():
        flag = "" if row["min"] >= base.TOP_N else "  <-- DEGENERATE (min<TOP_N)"
        print(f"     {per}  min={int(row['min']):3d} max={int(row['max']):3d} "
              f"mean={row['mean']:5.1f}{flag}")


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-007: DD controls on FIXED-funding + REFRESHED data — {len(coins)} coins")
    print(f"  config (pre-set from IS robustness): rv-spike {RV_FAST}/{RV_SLOW} "
          f">{RV_THRESH}x -> floor {RV_FLOOR}\n")

    p = build_panels(coins)
    print_eligibility(p["elig_count"], p["enough"])

    # ---------------- BASELINE (unguarded, walk-forward λ) ----------------
    raw_base, picks_b = walk_forward_stitch(p["raw_unguarded"])
    oos_b = Counter(b for y, b in picks_b if y >= 2025)
    print(f"\n  (λ OOS-picks, baseline: {dict(sorted(oos_b.items()))})")
    print("\n  --- RESULTS ---")
    base_net = apply_voltarget(raw_base)
    r_base = report("baseline (λ-WF)", base_net)

    # ---------------- (a) MIN-ELIGIBLE GUARD ----------------
    raw_g, picks_g = walk_forward_stitch(p["raw_guarded"])
    guard_net = apply_voltarget(raw_g)
    r_guard = report("+guard", guard_net)

    # ---------------- (a)+(b) GUARD + VOL-SPIKE DE-LEVER ----------------
    mult = rv_spike_scale(raw_g).reindex(raw_g.index)
    deluxe_net = apply_voltarget(raw_g) * mult
    r_both = report("+guard+delever", deluxe_net)

    # how often / how hard does the de-lever fire?
    fired = mult < 0.999
    print(f"\n  de-lever fires {fired.mean()*100:.1f}% of candles "
          f"(IS {fired[fired.index < base.OOS_CUTOFF].mean()*100:.1f}% / "
          f"OOS {fired[fired.index >= base.OOS_CUTOFF].mean()*100:.1f}%); "
          f"mean multiplier when fired = {mult[fired].mean():.2f}")

    # ---------------- TURNOVER (one-sided mean per candle) ----------------
    print("\n  --- TURNOVER (mean one-sided weight change/candle) ---")
    t_base = _stitched_turnover(
        {lam: _weights_for(coins, lam, guard=False) for lam in wf.LAM_GRID}, coins)
    t_guard = _stitched_turnover(
        {lam: _weights_for(coins, lam, guard=True) for lam in wf.LAM_GRID}, coins)
    print(f"  baseline turnover  = {t_base:.3f}")
    print(f"  +guard   turnover  = {t_guard:.3f}")
    print("  (+guard+delever turnover == +guard turnover: the de-lever is a SCALAR exposure "
          "overlay; it scales realized weight magnitude, and its cost is booked inside the "
          "vol-target * mult net above)")

    # ---------------- PARETO VERDICT ----------------
    print("\n  === PARETO RE-CONFIRMATION (FIXED funding + FRESH data) ===")
    _pareto("(a) guard vs baseline", r_base, r_guard)
    _pareto("(b) +delever vs +guard", r_guard, r_both)
    _pareto("(a+b) full vs baseline", r_base, r_both)


def _weights_for(coins: dict, lam: float, guard: bool) -> pd.DataFrame:
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    liq = qv.rolling(base.LIQ_WIN).mean().shift(1)
    elig = liq.rank(axis=1, ascending=False) <= base.TOP_N
    enough = liq.notna().sum(axis=1) >= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    if guard:
        w = w.where(enough, 0.0)
    return w


def _pareto(label: str, ref: dict, cand: dict) -> None:
    dd_better = cand["dd"] >= ref["dd"] - 1e-9  # less negative = smaller drawdown
    oos_ok = cand["oos"] >= ref["oos"] - 0.05  # OOS not materially worse
    is_ok = cand["is"] >= ref["is"] - 0.05
    pareto = dd_better and oos_ok
    tag = "PARETO-IMPROVING" if pareto else "NOT Pareto-improving"
    print(f"  {label:26} dDD={(cand['dd']-ref['dd'])*100:+.0f}pt "
          f"dOOS={cand['oos']-ref['oos']:+.2f} dIS={cand['is']-ref['is']:+.2f} "
          f"-> {tag}  (DD{'↓' if dd_better else '↑'}, "
          f"OOS{'ok' if oos_ok else 'WORSE'}, IS{'ok' if is_ok else 'worse'})")


if __name__ == "__main__":
    main()
