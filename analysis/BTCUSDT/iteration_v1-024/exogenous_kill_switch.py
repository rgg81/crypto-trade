"""IS-ONLY: does a DETERMINISTIC exogenous-stress KILL-SWITCH lift the iter-020 trend-state book's
recent-sub-period stability? — iter-v1/024 (BTCUSDT).

CAMPAIGN WALL (iter-016/021/022 triply-confirmed): any mechanism that adds model-timing-dependent
trades is a K=5 lottery that collapses at K=20. Only DETERMINISTIC parts generalize (stateless
200-SMA trend-state direction + IS-calibrated conviction gate). iter-023 closed the "add/select more
trades by magnitude" axis (magnitude SELECTION inverts in recent sub-periods). The binding constraint
is now established as DIRECTION-CORRECTNESS at the 14d horizon: the deterministic 200-SMA trend-state
direction WHIPSAWS in the 2025-26 OOS regime (corrections/chop).

THE iter-024 HYPOTHESIS (tested here, IS-only):
  The trend-state book loses (direction whipsaws) in identifiable EXOGENOUS-stress regimes. Turning
  the book OFF (FLAT, no trade) in those regimes — DETERMINISTICALLY, binary, NO model, NO seed, NO
  magnitude sizing — REMOVES the whipsaw losses and lifts per-sub-period stability (esp. the recent
  sub-periods, the OOS-proxy). This attacks direction-correctness directly without adding any
  seed-varying trades.

  Rule: at decision time t, if STRESS(t-1) == True  ->  FLAT (skip).  else trade iter-020 stack.
  The kill-switch REMOVES candles (subset of iter-020's fire_A). It can NEVER add a trade. So unlike
  iter-021 (funding-readmit, ADDED trades -> K=20 lottery), this is purely subtractive + deterministic.

THE iter-011 FRAGILITY PRECEDENT (the critical control):
  iter-011 found a binary BULL/BEAR regime GATE was FRAGILE: it locked in a T3-inversion and DEGRADED
  stability (lifted the headline via bull beta but every stability axis got worse, and the most-recent
  IS sub-period stayed negative). A kill-switch is only worth recommending if it is GENUINELY DIFFERENT:
    (a) lifts the RECENT sub-period Sharpe (the OOS-proxy), AND
    (b) does so across a PLATEAU of thresholds (not a knife-edge single threshold), AND
    (c) the benefit is sign-consistent across MULTIPLE sub-periods (not only by removing the single
        most-recent sub-period -- that would be OOS-curve-fitting by proxy).
  If the kill only helps by deleting the one recent sub-period, or only at one knife-edge threshold,
  it is the iter-011 fragile gate in new clothes -> NULL.

EXOGENOUS-STRESS candidate regimes (all stateless/past-only columns in the parquet):
  - realized-vol state:   vol_state_z_natr_30 (z-scored NATR), vol_natr_7, vol_range_spike_24/72
  - funding stress:       |funding_rate_zscore_30|, |funding_rate_zscore_90| (extreme crowding)
  - funding flip/impulse: |btc_funding_rate_8h_impulse|
  - OI unwind:            |oi_delta_30_z90|, |btc_oi_delta_5_z30|, |oi_price_divergence_30|
  Each kill-regime is binary: STRESS if |signal| (or signal) past-only exceeds an IS-calibrated cut.

THRESHOLD-PLATEAU SCAN: each candidate is swept across a grid of cut quantiles; we report the recent3
lift vs the iter-020 ungated incumbent at EACH cut, so a knife-edge (lift at one cut, flat/negative at
neighbours) is visually distinct from a genuine plateau (lift monotone/stable across a band of cuts).

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any forward
quantity; `.shift(1)` past-only SMA200/ATR14; stress signals already past-only (features_v1) and used
with `.shift(1)` semantics (we read column[t-1] via a past-only shift); per-sub-period stress cut
quantiles trained on PAST rows only (purged by N_LABEL); OOS never read. `src/` + runner + OOS
UNTOUCHED. The kill-regime + threshold are chosen on IS sub-period evidence ONLY.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-024/exogenous_kill_switch.py
"""
# ruff: noqa: E501, N806

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-024"

N_LABEL = 42  # fixed_horizon 14d — the iter-020 baseline label
BARS_PER_YEAR = 365.0 * 3.0  # 8h candles
SUBPERIOD_DAYS = 182.5  # ~6 months -> 11 IS sub-periods
MIN_SUB_TRADES = 8
SMA_WIN = 200  # trend-state direction (deterministic)
ATR_WIN = 14  # conviction-gate normalizer
RT_COST = 0.14  # round-trip fee 0.1% + 2bps/side slippage ~ 0.14% (matches iter-018/023 proxy)
Q_STRENGTH = 0.40  # iter-020 conviction-gate quantile (the incumbent SELECTION)

# Each candidate: (column, mode). mode in:
#   "abs_high" -> STRESS if |x_past| >= cut-quantile of |x_past|   (extreme magnitude either side)
#   "high"     -> STRESS if  x_past  >= cut-quantile of  x_past    (high realized-vol state)
# Cut quantiles swept to expose plateau vs knife-edge.
CANDIDATES: tuple[tuple[str, str, str], ...] = (
    ("vol_state_z_natr_30", "high", "RVOL: high realized-vol NATR z-state"),
    ("vol_natr_7", "high", "RVOL: high NATR-7"),
    ("vol_range_spike_24", "high", "RVOL: high range-spike-24"),
    ("vol_range_spike_72", "high", "RVOL: high range-spike-72"),
    ("funding_rate_zscore_30", "abs_high", "FUND: extreme |funding z30| (crowding)"),
    ("funding_rate_zscore_90", "abs_high", "FUND: extreme |funding z90| (crowding)"),
    ("btc_funding_rate_8h_impulse", "abs_high", "FUND: large |funding impulse| (flip)"),
    ("oi_delta_30_z90", "abs_high", "OI: extreme |OI-delta z90| (build/unwind)"),
    ("btc_oi_delta_5_z30", "abs_high", "OI: extreme |OI-delta-5 z30| (fast unwind)"),
    ("oi_price_divergence_30", "abs_high", "OI: extreme |OI-price divergence|"),
)
# Plateau scan grid (fraction of candles killed grows with the quantile).
CUT_GRID = (0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days: np.ndarray) -> list[tuple[float, float]]:
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r: np.ndarray, tpy: float) -> float:
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def stability(pnl: np.ndarray, fire: np.ndarray, ot_days, bounds, tpy) -> dict:
    """Per-sub-period annualized Sharpe of the (subset-selected) book."""
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = pnl[m]
        sh.append(ann_sharpe(arr, tpy) if int(np.isfinite(arr).sum()) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent_list = [v for v in reversed(s) if np.isfinite(v)]
    allt = pnl[fire & np.isfinite(pnl)]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent1=round(float(recent_list[0]), 3) if len(recent_list) >= 1 else np.nan,
        recent2=round(float(np.mean(recent_list[:2])), 3) if len(recent_list) >= 2 else np.nan,
        recent3=round(float(np.mean(recent_list[:3])), 3) if len(recent_list) >= 3 else np.nan,
        n_pos=int(np.sum(valid > 0)),
        n_scored=int(len(valid)),
        n_trades=int(np.isfinite(pnl[fire]).sum()),
        win_rate=round(float(np.mean(pnl[fire & np.isfinite(pnl)] > 0)), 4)
        if len(allt)
        else np.nan,
    )


def past_only_quantile_threshold(x, ot_days, bounds, q):
    """Per-sub-period q-quantile of x from PAST rows only (purged by N_LABEL). Deterministic, no model,
    no seed, no OOS — identical construction to the iter-018/020/023 conviction-gate threshold."""
    thr = np.full(len(x), np.nan)
    row_idx = np.arange(len(x))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        cut = int(row_idx[tm].min()) - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = x[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def stress_mask(df, col, mode, ot_days, bounds, cut_q):
    """Binary STRESS mask: past-only signal[t-1] beyond a past-only cut quantile.
    NaN-stress (signal undefined, e.g. early OI) -> NOT stress (trade normally). This is the
    conservative default: the kill-switch only fires when the exogenous stress is DEFINED and extreme.
    """
    raw = df[col].to_numpy(float)
    sig = pd.Series(raw).shift(1).to_numpy()  # decision uses signal at t-1 (past-only)
    if mode == "abs_high":
        sig = np.abs(sig)
    thr = past_only_quantile_threshold(sig, ot_days, bounds, cut_q)
    stress = np.isfinite(sig) & np.isfinite(thr) & (sig >= thr)
    return stress


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    # --- deterministic trend-state direction + conviction-gate strength (iter-020 incumbent) ---
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    absd = np.abs(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    pnl = dir_ts * y - (RT_COST / 100.0)

    # iter-020 INCUMBENT book = trend-state direction + strength gate q40 (NO kill-switch).
    thr_str = past_only_quantile_threshold(absd, ot_days, bounds, Q_STRENGTH)
    fire_incumbent = base & np.isfinite(thr_str) & (absd >= thr_str)
    A = stability(pnl, fire_incumbent, ot_days, bounds, tpy)

    print(
        f"IS rows {len(df)}  N={N_LABEL}(14d)  SMA{SMA_WIN} ATR{ATR_WIN}  RT={RT_COST}%  "
        f"sub-periods={len(bounds)}"
    )
    print("=" * 150)
    print("INCUMBENT iter-020 (trend-state dir + strength gate q40, NO kill-switch):")
    print(
        f"  full={A['full']} frac_pos={A['frac_pos']} disp={A['dispersion']} worst={A['worst']} "
        f"recent1={A['recent1']} recent2={A['recent2']} recent3={A['recent3']} "
        f"trades={A['n_trades']} WR={A['win_rate']}"
    )
    print(
        "  per-sub: "
        + " ".join(
            f"{lab[2:7]}={v:+.2f}" if (v is not None and np.isfinite(v)) else f"{lab[2:7]}=  ·  "
            for lab, v in zip(sub_labels, A["per_sub"])
        )
    )
    print("=" * 150)

    # ============ THRESHOLD-PLATEAU SCAN across all candidates ============
    print(
        "\nTHRESHOLD-PLATEAU SCAN — recent3 Sharpe + frac_pos of the KILLED book vs incumbent recent3 "
        f"= {A['recent3']:+.3f}, frac_pos = {A['frac_pos']:.3f}"
    )
    print(
        "(kill = drop incumbent trades where STRESS@cut. retained = trades remaining. dRecent3 = lift "
        "vs incumbent. PLATEAU = lift positive + stable across band; KNIFE-EDGE = lift at one cut only.)"
    )
    print("=" * 150)
    hdr = (
        f"{'candidate':42s} {'cut':>5s} {'kill%':>6s} {'retain':>6s} {'full':>7s} "
        f"{'fpos':>5s} {'rec1':>6s} {'rec2':>6s} {'rec3':>6s} {'dRec3':>7s} {'worst':>7s}"
    )
    rows = []
    for col, mode, desc in CANDIDATES:
        print("-" * 150)
        print(hdr)
        for cut_q in CUT_GRID:
            stress = stress_mask(df, col, mode, ot_days, bounds, cut_q)
            fire_killed = fire_incumbent & ~stress  # subtractive: drop stress candles
            n_inc = int(fire_incumbent.sum())
            n_killed_out = int((fire_incumbent & stress).sum())
            kill_pct = 100.0 * n_killed_out / n_inc if n_inc else np.nan
            B = stability(pnl, fire_killed, ot_days, bounds, tpy)
            d_rec3 = (
                (B["recent3"] - A["recent3"])
                if (np.isfinite(B["recent3"]) and np.isfinite(A["recent3"]))
                else np.nan
            )
            print(
                f"{desc:42s} {cut_q:>5.2f} {kill_pct:>5.1f}% {B['n_trades']:>6d} "
                f"{B['full']!s:>7} {B['frac_pos']!s:>5} {B['recent1']!s:>6} {B['recent2']!s:>6} "
                f"{B['recent3']!s:>6} {d_rec3:>+7.3f} {B['worst']!s:>7}"
            )
            rows.append(
                dict(
                    candidate=desc,
                    column=col,
                    mode=mode,
                    cut_q=cut_q,
                    kill_pct=round(kill_pct, 2),
                    retained_trades=B["n_trades"],
                    full=B["full"],
                    frac_pos=B["frac_pos"],
                    dispersion=B["dispersion"],
                    worst=B["worst"],
                    recent1=B["recent1"],
                    recent2=B["recent2"],
                    recent3=B["recent3"],
                    d_recent3=round(d_rec3, 4) if np.isfinite(d_rec3) else np.nan,
                    win_rate=B["win_rate"],
                    incumbent_recent3=A["recent3"],
                    incumbent_frac_pos=A["frac_pos"],
                    incumbent_full=A["full"],
                )
            )
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUTDIR / "exogenous_kill_switch.csv", index=False)
    print("\n" + "=" * 150)
    print(f"Wrote: {OUTDIR / 'exogenous_kill_switch.csv'}")

    # ============ PLATEAU SUMMARY: which candidate (if any) lifts recent3 across a BAND ============
    print(
        "\nPLATEAU SUMMARY — per candidate: how many of the 6 cuts give d_recent3 > 0 (lift), and the "
        "best (cut, d_recent3). A genuine kill-switch lifts across a BAND (>=4/6) with positive worst;\n"
        "a knife-edge lifts at <=1 cut; a fragile gate (iter-011) lifts headline but NOT recent3."
    )
    print("=" * 150)
    summ = []
    for col, mode, desc in CANDIDATES:
        sub = df_out[df_out["column"] == col]
        lifts = sub["d_recent3"].dropna()
        n_lift = int((lifts > 0).sum())
        best_i = sub["d_recent3"].idxmax() if sub["d_recent3"].notna().any() else None
        best_cut = sub.loc[best_i, "cut_q"] if best_i is not None else np.nan
        best_d = sub.loc[best_i, "d_recent3"] if best_i is not None else np.nan
        best_worst = sub.loc[best_i, "worst"] if best_i is not None else np.nan
        best_fpos = sub.loc[best_i, "frac_pos"] if best_i is not None else np.nan
        verdict = (
            "PLATEAU"
            if n_lift >= 4
            else ("KNIFE-EDGE" if n_lift == 1 else ("NO-LIFT" if n_lift == 0 else "PARTIAL"))
        )
        print(
            f"  {desc:42s} lift_cuts={n_lift}/6  best(cut={best_cut},dRec3={best_d:+.3f},"
            f"worst={best_worst},fpos={best_fpos})  -> {verdict}"
        )
        summ.append(
            dict(
                candidate=desc,
                column=col,
                lift_cuts_of_6=n_lift,
                best_cut=best_cut,
                best_d_recent3=best_d,
                best_worst=best_worst,
                best_frac_pos=best_fpos,
                verdict=verdict,
            )
        )
    pd.DataFrame(summ).to_csv(OUTDIR / "kill_switch_plateau_summary.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'kill_switch_plateau_summary.csv'}")


if __name__ == "__main__":
    main()
