"""portfolio-iteration EXPLORATION-016 — FUNDING-ACCELERATION factor (2nd-order funding dynamics).

ONE new STRUCTURAL change to the canonical iter_005 baseline (walk-forward-λ trend+carry, honest
IS +1.30 / OOS +1.37 / maxDD -23%). The book already trades the funding LEVEL (CARRY = -sign of the
trailing-9 funding mean: short coins paying high positive funding, long coins paying negative). This
iteration asks whether the funding's DYNAMICS — its change / slope, a SECOND-order signal distinct
from the level — carries independent, orthogonal edge.

CRYPTO-NATIVE RATIONALE (quant-researcher):
  Perp funding is a real-time crowding gauge. The LEVEL says "longs are currently crowded" (carry
  fades it once). The CHANGE says something the level cannot: a coin can sit at a HIGH positive
  funding level (carry is already short) while funding is FALLING (longs unwinding, de-crowding) —
  or at a LOW/negative level while funding is RISING fast (the crowd is piling back in, a squeeze
  building). Those two states are INVISIBLE to a level-only signal but are exactly where the
  reflexive funding<->price feedback turns.

  The mechanism is a hypothesis with two candidate signs; the DATA picks the sign by IS, NOT OOS:
    (A) FADE-THE-CROWD (contrarian): funding RISING fast == crowd piling into longs == squeeze
        building == get SHORT early, ahead of the unwind. sign = -Δfunding.
    (B) MOMENTUM: funding RISING == trend/positioning confirming == ride it LONG. sign = +Δfunding.
  We build the literal sign flip and print BOTH; the IS-better sign is the deployed one.

  THE KEY ORTHOGONALITY QUESTION (the whole point of this iteration): is the acceleration just the
  carry LEVEL re-skinned? A pure trending-up funding path has level and slope co-moving, so a naive
  Δ could be ~collinear with carry. We MEASURE corr(accel, carry) on IS; if it is high (>= 0.50 in
  magnitude) the factor is REDUNDANT with the book's existing carry leg and is REJECTED (gate [4]).
  We ALSO residual-orthogonalize the accel net against ALL THREE existing factor nets (trend, carry,
  flow) and report the residual standalone Sharpe — a factor that is spanned by the book collapses.

SIGNAL CONSTRUCTION (per coin-candle t, ALL inputs known at close[t], PAST-ONLY):
  Two forms are built and compared (form chosen by mechanism + IS, never OOS):
    DIFF  : accel_raw[t] = f_mean[t] - f_mean[t - DIFF_LAG]    (slope of the trailing funding mean)
            f_mean[t]    = funding.rolling(MEAN_WIN).mean()     (de-noise; single prints are noise)
    MACD  : accel_raw[t] = funding.rolling(SHORT_WIN).mean() - funding.rolling(LONG_WIN).mean()
            (short-vs-long funding mean; rising funding => short MA above long MA, sign-equivalent
             to a slope but smoother and self-normalizing in cadence)
  Both are completed-candle, trailing-only. The raw acceleration is then cross-sectionally z-scored
  across the ELIGIBLE PIT top-20 at t (row-demean / row-std, axis=1 same-time only — no time leak),
  IDENTICAL transform to iter_012's flow_z, so the factor is scale-comparable to flow and sized by
  the z-score itself (its risk-normalizing transform; no extra /rvol). The weight lag is applied by
  `w = raw...shift(1)` (mirrors trend/carry/flow): a signal built from close[t] info trades the
  open[t+1]->open[t+2] return. Funding accrual on the held leg is booked `fund.shift(-1)`.

HEADLINE CHOICES (justified; the form/window sweep prints the alternatives):
  - DIFF form is headline (the most literal reading of "the change of funding"); MACD printed as a
    cross-check (the two are sign-equivalent — a rising trailing mean has short-MA > long-MA).
  - MEAN_WIN = 9 candles == iter_004's carry M_FUND (~3d of 8h): same de-noising window the carry
    LEVEL uses, so accel is the *slope of the very series carry takes the level of* — the cleanest
    apples-to-apples test of "level vs change". DIFF_LAG = 9 (one mean-window back: a clean
    one-window slope). Both sit on a {6,9,15} robustness grid so neither is a tuned single cell.
  - cross-sectional Z-SCORE transform: dollar-neutral by construction (row-demeaned), scale-matched
    to trend (mean-sign in [-1,1]) and flow (z-score) so a fixed standalone build is comparable.

CONSTRUCTION (mirrors iter_012 / iter_014 EXACTLY; reuses tf._panels for the shared past-only inputs
so the PIT top-20 universe, trend, carry, flow, rvol, elig, ret_fwd, fund_next are BYTE-IDENTICAL to
the canonical book). The standalone accel net flows through the IDENTICAL gross-normalize -> lag ->
real-funding+taker-cost -> per-candle vol-target machinery the other factors use.

NO-CHEATING: the DIRECTION is IS+mechanism-picked (not OOS); windows are robustness-swept over a
fixed grid, NEVER walk-forwarded, NEVER OOS-tuned; taker 0.05%/side both sides + a 2x cost stress
on the standalone (a gross-only / turnover-eaten edge is a REJECT); OOS_CUTOFF=2025-03-24 fixed;
carry / flow / trend nets and the baseline WF-λ are reused byte-for-byte and UNCHANGED.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_012_takerflow as tf  # noqa: E402
import iter_014_riskparity as rp  # noqa: E402

# --- signal knobs (structural; robustness-checked, NEVER OOS-tuned) ---
MEAN_WIN = 9  # trailing funding-mean de-noise window (== iter_004 carry M_FUND, ~3d of 8h)
DIFF_LAG = 9  # slope lag for the DIFF form (one mean-window back: a clean one-window slope)
SHORT_WIN = 6  # MACD short funding-mean window (cross-check form)
LONG_WIN = 21  # MACD long funding-mean window (cross-check form)

# --- robustness grids ---
MEAN_WIN_GRID = [6, 9, 15]  # de-noise-window sweep (headline 9 is one cell, not a tuned pick)
EPS = 0.05  # materiality band (same as iter_008/011/012)


def build_accel_z(
    fund: pd.DataFrame,
    elig: pd.DataFrame,
    mean_win: int,
    diff_lag: int,
    direction: int = 1,
) -> pd.DataFrame:
    """Cross-sectional z-score of the trailing funding SLOPE (DIFF form), PAST-ONLY.

    f_mean[t]   = funding.rolling(mean_win).mean()          (completed candle t, known at close[t])
    accel[t]    = f_mean[t] - f_mean[t - diff_lag]          (slope of the trailing funding mean)
    accel_z[t,c]= (accel - rowmean) / rowstd  over the ELIGIBLE cross-section at t (same-time only)
    direction = +1 momentum (long rising-funding), -1 fade-the-crowd (the sign flip; both printed).

    The weight lag is applied later via `.shift(1)`; nothing here uses future data (z-score rowstats
    are same-row cross-section, the mean is trailing, the diff looks strictly backward).
    """
    f_mean = fund.rolling(mean_win).mean()
    accel = f_mean - f_mean.shift(diff_lag)
    sm = accel.where(elig)  # restrict the cross-section to eligible coins for the row-stats
    row_mean = sm.mean(axis=1)
    row_std = sm.std(axis=1)
    z = sm.sub(row_mean, axis=0).div(row_std.replace(0, np.nan), axis=0)
    return (direction * z).where(elig)


def build_macd_z(
    fund: pd.DataFrame,
    elig: pd.DataFrame,
    short_win: int,
    long_win: int,
    direction: int = 1,
) -> pd.DataFrame:
    """Cross-sectional z-score of the MACD form (short funding-mean minus long funding-mean),
    PAST-ONLY. Sign-equivalent to a slope: a rising trailing funding mean has short-MA > long-MA.
    Smoother + self-normalizing in cadence than a fixed-lag diff. Same z-score + lag chain.
    """
    accel = fund.rolling(short_win).mean() - fund.rolling(long_win).mean()
    sm = accel.where(elig)
    row_mean = sm.mean(axis=1)
    row_std = sm.std(axis=1)
    z = sm.sub(row_mean, axis=0).div(row_std.replace(0, np.nan), axis=0)
    return (direction * z).where(elig)


def _panels(coins: dict) -> dict:
    """Shared past-only inputs — reuse tf._panels (trend/carry/flow/rvol/elig/ret_fwd/fund_next on
    the BYTE-IDENTICAL PIT top-20 universe) and ADD the funding-acceleration signals. We re-load the
    raw funding panel here (tf._panels keeps fund_next but not the raw fund needed for the rolling
    mean/slope) the SAME way iter_004/iter_005 do, so the funding alignment is identical.
    """
    p = tf._panels(coins)
    opens = p["_opens"]
    # raw funding on the shared dt index (nearest-match loader, identical to iter_004/005).
    # tf._panels already converted _opens.index to datetime64[ms]; `.astype("int64")` recovers the
    # ORIGINAL ms epoch the funding loader expects (the tolerance is in ms) — NO extra /1e6.
    ms_index = opens.index.astype("int64")
    fund = f4.load_funding(ms_index, list(coins.keys()))
    fund.index = opens.index
    fund = fund.reindex(index=opens.index, columns=opens.columns)
    elig = p["elig"]
    p["_fund"] = fund
    p["accel_z"] = build_accel_z(fund, elig, MEAN_WIN, DIFF_LAG, direction=1)
    p["macd_z"] = build_macd_z(fund, elig, SHORT_WIN, LONG_WIN, direction=1)
    return p


def standalone(p: dict, cost_mult: float, direction: int = 1, key: str = "accel_z") -> dict:
    """Build the acceleration signal as a self-contained cross-sectional factor (z-score, gross-
    normalized, lagged, real funding + taker cost at cost_mult×, per-candle vol-targeted) — directly
    comparable to the baseline and the other factors. direction flips the sign (momentum vs fade).
    """
    z = p[key].fillna(0.0)
    sig = z if direction == 1 else -z
    raw = sig.where(p["elig"])
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = base.vol_target((pnl + fpnl - cost).dropna())
    gross_net = base.vol_target((pnl + fpnl).dropna())  # pre-cost (cost honesty diagnostic)
    s = rp.stats(net)
    s["turn"] = float((w - w.shift(1)).abs().sum(axis=1).mean())
    s["gross_is"] = base.msharpe(gross_net, base.LO0, base.OOS_CUTOFF)
    s["gross_oos"] = base.msharpe(gross_net, base.OOS_CUTOFF, base.HI1)
    return s


def standalone_net(p: dict, direction: int = 1, key: str = "accel_z") -> pd.Series:
    """The standalone accel NET return series (1× taker, real funding, NOT vol-targeted) — used by
    the residual-orthogonality diagnostic so it shares the other factors' raw-return space.
    """
    z = p[key].fillna(0.0)
    sig = z if direction == 1 else -z
    raw = sig.where(p["elig"])
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return (pnl + fpnl - cost).dropna()


def carry_net_raw(p: dict) -> pd.Series:
    """The CARRY factor NET (1× taker, real funding, NOT vol-targeted) in the same raw-return space.
    Carry = -sign(trailing-9 funding mean), inverse-vol sized — the λ=1 leg of the canonical blend
    (== iter_014.factor_nets['carry'] before its vol-target). Used by the residual diagnostic so the
    accel net is regressed against the LEVEL signal it must be distinct from.
    """
    raw = (p["carry"] / p["rvol"]).where(p["elig"])
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return (pnl + fpnl - cost).dropna()


def orthogonality(p: dict, other_key: str, accel_key: str = "accel_z") -> float:
    """Pooled cross-coin Pearson corr(accel_z, <other signal>) over IS ELIGIBLE cells. THE key
    number for `carry`: if |corr to carry| is high the factor is the LEVEL re-skinned (REDUNDANT,
    gate [4] threshold |corr| < 0.50). `other_key` is a per-coin signal panel (trend/carry/accel_z/
    macd_z); for trend/carry it is masked to eligible cells (those panels are dense).
    """
    fl = p[accel_key]
    ot = p[other_key].where(p["elig"])
    is_mask = fl.index < base.OOS_CUTOFF
    a = fl[is_mask].to_numpy().ravel()
    b = ot[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def net_correlations(p: dict, accel_net: pd.Series) -> dict:
    """Correlation of the accel standalone NET series to the trend / carry / flow factor NETS (over
    IS, common dates). The orthogonality the combiner cares about is at the NET level (does the
    factor's P&L stream co-move with the book's), complementing the per-cell signal corr above.
    """
    nets = rp.factor_nets(
        p
    )  # trend, carry, flow standalone vol-targeted nets (byte-identical book)
    out = {}
    av = base.vol_target(accel_net)  # put accel on the same vol-target footing as the factor nets
    for n in ["trend", "carry", "flow"]:
        df = pd.DataFrame({"a": av, "b": nets[n]}).dropna()
        df = df[df.index < base.OOS_CUTOFF]
        out[n] = float(df["a"].corr(df["b"])) if len(df) > 2 else float("nan")
    return out


def residual_orthogonality(p: dict, direction: int) -> dict:
    """Regress the standalone accel net on the trend, carry AND flow factor nets jointly (IS-fit
    OLS, applied to the whole series) and report the RESIDUAL OOS Sharpe. If accel were spanned by
    the existing 3-factor book — especially by carry (the LEVEL) — its net would be explained away
    and the residual would collapse. A residual that stays materially positive OOS proves the factor
    is INDEPENDENTLY additive, NOT carry/trend/flow re-stacked.

    Betas fit on IS ONLY (no OOS peek); the same IS-fit betas applied to the OOS residual.
    """
    accel = standalone_net(p, direction=direction)
    nets = rp.factor_nets(p)
    df = pd.DataFrame(
        {
            "accel": accel,
            "trend": nets["trend"],
            "carry": nets["carry"],
            "flow": nets["flow"],
        }
    ).dropna()
    is_df = df[df.index < base.OOS_CUTOFF]
    y = is_df["accel"].to_numpy()
    x = is_df[["trend", "carry", "flow"]].to_numpy()
    x1 = np.column_stack([np.ones(len(x)), x])  # intercept + 3 factor nets
    beta, *_ = np.linalg.lstsq(x1, y, rcond=None)  # IS-fit OLS
    xall = df[["trend", "carry", "flow"]].to_numpy()
    pred = beta[0] + xall @ beta[1:]
    resid = pd.Series(df["accel"].to_numpy() - pred, index=df.index)
    # carry-only beta (the single most important redundancy check)
    yc, cc = is_df["accel"], is_df["carry"]
    var_c = float((cc**2).mean() - cc.mean() ** 2)
    cov_c = float((yc * cc).mean() - yc.mean() * cc.mean())
    beta_carry_only = cov_c / var_c if var_c > 0 else 0.0
    return {
        "beta_trend": float(beta[1]),
        "beta_carry": float(beta[2]),
        "beta_flow": float(beta[3]),
        "beta_carry_only": beta_carry_only,
        "raw_is": base.msharpe(df["accel"], base.LO0, base.OOS_CUTOFF),
        "raw_oos": base.msharpe(df["accel"], base.OOS_CUTOFF, base.HI1),
        "resid_is": base.msharpe(resid, base.LO0, base.OOS_CUTOFF),
        "resid_oos": base.msharpe(resid, base.OOS_CUTOFF, base.HI1),
    }


def coverage(p: dict) -> dict:
    """Coverage diagnostic for the dense always-on factor: fraction of eligible cells carrying a
    finite accel_z (after the MEAN_WIN + DIFF_LAG warmup), IS vs OOS, + median active coins/candle.
    A dense cross-sectional tilt — no vol-target degeneracy risk (cf. iter_011's sparse -99%).
    """
    finite = p["accel_z"].notna() & p["elig"]
    elig = p["elig"]
    is_m = elig.index < base.OOS_CUTOFF
    oos_m = elig.index >= base.OOS_CUTOFF
    is_cov = finite[is_m].sum().sum() / max(int(elig[is_m].sum().sum()), 1)
    oos_cov = finite[oos_m].sum().sum() / max(int(elig[oos_m].sum().sum()), 1)
    med_active = float(finite.sum(axis=1)[finite.sum(axis=1) > 0].median())
    return {"is_cov": is_cov, "oos_cov": oos_cov, "med_active": med_active}


def window_sweep(p: dict, direction: int) -> list:
    """De-noise-window robustness: rebuild accel_z per MEAN_WIN (DIFF_LAG = the same window: a clean
    one-window slope) and report standalone IS/OOS + corr-to-carry. If only the 9-cell has an edge
    and the others are flat/negative, the headline is a tuned cell -> downgrade. Reuses the fixed
    elig / fund panels (only the window changes).
    """
    rows = []
    for win in MEAN_WIN_GRID:
        az = build_accel_z(p["_fund"], p["elig"], win, win, direction=direction)
        pv = {**p, "accel_z": az}
        corr_ca = orthogonality(pv, "carry")
        sa = standalone(pv, 1.0, direction=direction)
        rows.append({"win": win, "corr_carry": corr_ca, **sa})
    return rows


def main() -> None:
    coins = base.load_universe()
    print(
        f"EXPLORATION-016: FUNDING-ACCELERATION factor (2nd-order funding dynamics) — {len(coins)}"
        " coins"
    )
    print(
        f"  signal: accel_z = xsec z-score of [funding.rolling({MEAN_WIN}).mean() diff over "
        f"{DIFF_LAG}]; tested BOTH dirs (fade-crowd vs momentum)\n"
    )

    p = _panels(coins)

    # --- HARD SANITY: the raw funding panel underlying the acceleration must reproduce the BOOK's
    # carry signal byte-for-byte (carry = -sign(fund.rolling(M_FUND).mean())). This proves the
    # funding alignment is IDENTICAL to iter_004/005 — i.e. accel is the SLOPE of the very series
    # carry takes the LEVEL of (the cleanest leak-safe level-vs-change test). If it diverges, the
    # ms-epoch alignment is wrong and every accel number is on a mis-aligned funding panel — halt.
    carry_check = -np.sign(p["_fund"].rolling(f4.M_FUND).mean())
    carry_diff = float(
        np.nanmax((carry_check.fillna(0.0) - p["carry"].fillna(0.0)).abs().to_numpy())
    )
    carry_repro = carry_diff < 1e-9
    print(
        f"  [sanity] _fund reproduces the book carry signal (max|Δ|={carry_diff:.1e}): "
        f"{'PASS' if carry_repro else 'FAIL'}"
    )
    if not carry_repro:
        print("  HALT: funding panel mis-aligned vs the book — refusing to read any accel result.")
        return

    # --- coverage (dense factor, not an event flag) ---
    cv = coverage(p)
    print(
        f"  COVERAGE (dense): IS finite-accel_z fraction of eligible={cv['is_cov']:.2f}  "
        f"OOS={cv['oos_cov']:.2f}  median active coins/candle={cv['med_active']:.0f}\n"
    )

    # --- mechanism / orthogonality: is the CHANGE just the LEVEL (carry) re-skinned? ---
    corr_ca = orthogonality(p, "carry")
    corr_tr = orthogonality(p, "trend")
    corr_fl = orthogonality(p, "flow_z")
    corr_macd = orthogonality(p, "macd_z")  # DIFF vs MACD form agreement
    carry_ok = np.isfinite(corr_ca) and abs(corr_ca) < 0.50
    print("  --- MECHANISM / ORTHOGONALITY (IS signal-level, eligible cells) ---")
    print(
        f"  corr(accel_z, CARRY) = {corr_ca:+.3f}  -> "
        f"{'PASS (|corr|<0.50, distinct from LEVEL)' if carry_ok else 'FAIL (>=0.50, redundant)'}"
    )
    print(f"  corr(accel_z, trend) = {corr_tr:+.3f}   corr(accel_z, flow) = {corr_fl:+.3f}")
    print(f"  corr(accel_z DIFF, accel_z MACD form) = {corr_macd:+.3f}  (form agreement)\n")

    # --- STANDALONE both directions + cost honesty (1× and 2× taker) ---
    print("  --- STANDALONE accel_z cross-sectional factor (BOTH directions, cost honesty) ---")
    print(f"  {'':22}{'IS':>7}{'OOS':>7}{'maxDD':>7}{'netTot':>8}{'turn':>7}")
    sa_mom1 = standalone(p, 1.0, direction=1)
    sa_mom2 = standalone(p, 2.0, direction=1)
    sa_fade1 = standalone(p, 1.0, direction=-1)
    sa_fade2 = standalone(p, 2.0, direction=-1)
    print(
        f"  {'MOMENTUM(+accel) 1x':22}{sa_mom1['is']:>+7.2f}{sa_mom1['oos']:>+7.2f}"
        f"{sa_mom1['dd'] * 100:>6.0f}%{sa_mom1['tot']:>+7.0f}%{sa_mom1['turn']:>7.3f}"
    )
    print(
        f"  {'MOMENTUM(+accel) 2x':22}{sa_mom2['is']:>+7.2f}{sa_mom2['oos']:>+7.2f}"
        f"{sa_mom2['dd'] * 100:>6.0f}%{sa_mom2['tot']:>+7.0f}%{sa_mom2['turn']:>7.3f}"
    )
    print(
        f"  {'FADE-CROWD(-accel) 1x':22}{sa_fade1['is']:>+7.2f}{sa_fade1['oos']:>+7.2f}"
        f"{sa_fade1['dd'] * 100:>6.0f}%{sa_fade1['tot']:>+7.0f}%{sa_fade1['turn']:>7.3f}"
    )
    print(
        f"  {'FADE-CROWD(-accel) 2x':22}{sa_fade2['is']:>+7.2f}{sa_fade2['oos']:>+7.2f}"
        f"{sa_fade2['dd'] * 100:>6.0f}%{sa_fade2['tot']:>+7.0f}%{sa_fade2['turn']:>7.3f}"
    )
    # MACD-form cross-check (headline direction picked just below)
    pv_macd = {**p, "accel_z": p["macd_z"]}
    mom_dir = sa_mom1["is"] >= sa_fade1["is"]  # direction the data picks (IS, NOT OOS)
    direction = 1 if mom_dir else -1
    sa_macd = standalone(pv_macd, 1.0, direction=direction, key="accel_z")
    print(
        f"  {'MACD-form 1x (picked)':22}{sa_macd['is']:>+7.2f}{sa_macd['oos']:>+7.2f}"
        f"{sa_macd['dd'] * 100:>6.0f}%{sa_macd['tot']:>+7.0f}%{sa_macd['turn']:>7.3f}"
    )
    picked = sa_mom1 if mom_dir else sa_fade1
    print(f"     picked net%/yr={picked['yr']}")
    dir_label = (
        "MOMENTUM (+accel, long rising-funding)"
        if mom_dir
        else "FADE-CROWD (-accel, short rising-funding)"
    )
    print(f"     direction picked by data (IS): {dir_label}\n")

    # --- NET-level correlation of the picked direction to trend / carry / flow NETS ---
    accel_net = standalone_net(p, direction=direction)
    ncorr = net_correlations(p, accel_net)
    print("  --- NET-RETURN correlation of accel factor to the book's factor NETS (IS) ---")
    print(
        f"  corr(accel net, trend net)={ncorr['trend']:+.2f}  "
        f"corr(accel net, CARRY net)={ncorr['carry']:+.2f}  "
        f"corr(accel net, flow net)={ncorr['flow']:+.2f}"
    )
    net_carry_ok = np.isfinite(ncorr["carry"]) and abs(ncorr["carry"]) < 0.50
    net_carry_tag = (
        "< 0.50 (P&L stream distinct from the carry leg)"
        if net_carry_ok
        else ">= 0.50 (P&L co-moves with carry — REDUNDANT)"
    )
    print(f"  -> NET corr to CARRY {net_carry_tag}\n")

    # --- residual orthogonality vs the existing 3 factors (carry is the redundancy risk) ---
    ro = residual_orthogonality(p, direction)
    resid_ok = ro["resid_oos"] > 0.30 and ro["resid_oos"] >= ro["raw_oos"] - tf.EPS
    resid_tag = (
        "independently additive (NOT spanned by trend/carry/flow)"
        if resid_ok
        else "spanned by the existing book (redundant)"
    )
    print("  --- RESIDUAL ORTHOGONALITY (accel net regressed on trend+carry+flow nets; IS OLS) ---")
    print(
        f"  betas: trend={ro['beta_trend']:+.2f} carry={ro['beta_carry']:+.2f} "
        f"flow={ro['beta_flow']:+.2f}  (carry-only beta={ro['beta_carry_only']:+.2f})"
    )
    print(
        f"  raw accel IS/OOS={ro['raw_is']:+.2f}/{ro['raw_oos']:+.2f}  "
        f"-> RESIDUAL IS/OOS={ro['resid_is']:+.2f}/{ro['resid_oos']:+.2f}"
    )
    print(f"     {resid_tag}\n")

    # --- de-noise-window robustness (prove the headline 9 is not a tuned cell) ---
    print("  --- DE-NOISE-WINDOW ROBUSTNESS (picked direction; standalone + corr-to-carry) ---")
    print(f"  {'win':>4} {'corrCarry':>9} {'sa_IS':>7} {'sa_OOS':>7} {'maxDD':>7} {'turn':>7}")
    sweep = window_sweep(p, direction)
    for r in sweep:
        print(
            f"  {r['win']:>4d} {r['corr_carry']:>+9.3f} {r['is']:>+7.2f} {r['oos']:>+7.2f} "
            f"{r['dd'] * 100:>6.0f}% {r['turn']:>7.3f}"
        )
    sweep_pos = all(r["is"] > 0 and r["oos"] > 0 for r in sweep)
    sweep_carry_ok = all(abs(r["corr_carry"]) < 0.50 for r in sweep if np.isfinite(r["corr_carry"]))
    print()

    # --- baseline anchor for context (UNCHANGED) ---
    base_wf, _ = tf.wf.walkforward(tf.wf.lam_nets(coins))
    b = rp.stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    print(
        f"  CANONICAL baseline (iter_005 WF-λ, UNCHANGED): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}%  (n={n_oos_mo} OOS months)\n"
    )

    # --- carry standalone (the factor accel must be distinct FROM), for the comparison table ---
    carry_s = rp.stats(rp.factor_nets(p)["carry"])
    print(
        f"  CARRY standalone (the LEVEL factor in the book): IS={carry_s['is']:+.2f} "
        f"OOS={carry_s['oos']:+.2f} maxDD={carry_s['dd'] * 100:.0f}%  (accel must be DISTINCT)\n"
    )

    # --- PRE-REGISTERED FALSIFIER VERDICT ---
    cost_ok = (
        picked["is"] > 0
        and picked["oos"] > 0
        and (
            sa_mom2["is"] > 0 and sa_mom2["oos"] > 0
            if mom_dir
            else sa_fade2["is"] > 0 and sa_fade2["oos"] > 0
        )
    )
    standalone_edge = picked["is"] > 0 and picked["oos"] > 0
    edge_material = picked["oos"] >= 0.30  # a real standalone factor, not noise around zero

    print(f"  === PRE-REGISTERED FALSIFIER VERDICT (n={n_oos_mo} OOS months) ===")
    print(
        f"  [1] standalone net-positive IS AND OOS (picked dir): "
        f"IS={picked['is']:+.2f} OOS={picked['oos']:+.2f} -> "
        f"{'PASS' if standalone_edge else 'FAIL'}"
    )
    print(
        f"  [2] standalone OOS >= +0.30 (a real factor, above the n={n_oos_mo}mo noise floor): "
        f"{picked['oos']:+.2f} -> {'PASS' if edge_material else 'FAIL'}"
    )
    print(
        f"  [3] cost-honest: net-positive at 1× AND 2× taker (not gross-only/turnover-eaten): "
        f"{'PASS' if cost_ok else 'FAIL'}"
    )
    print(
        f"  [4] DISTINCT from CARRY: |corr(accel_z, carry)| < 0.50 (signal) AND "
        f"|corr(accel net, carry net)| < 0.50 (P&L): "
        f"sig={corr_ca:+.3f} net={ncorr['carry']:+.2f} -> "
        f"{'PASS' if (carry_ok and net_carry_ok) else 'FAIL (redundant with the LEVEL)'}"
    )
    print(
        f"  [5] residual-additive vs trend+carry+flow (resid OOS > +0.30 AND not collapsed): "
        f"resid OOS={ro['resid_oos']:+.2f} -> {'PASS' if resid_ok else 'FAIL'}"
    )
    print(
        f"  [6] robust across the de-noise window (every cell IS+OOS>0 AND |corr-carry|<0.50): "
        f"-> {'PASS' if (sweep_pos and sweep_carry_ok) else 'FAIL'}"
    )

    distinct_from_carry = carry_ok and net_carry_ok
    real_edge = standalone_edge and edge_material and cost_ok
    orthogonal_additive = distinct_from_carry and resid_ok
    print()
    if real_edge and orthogonal_additive and sweep_pos and sweep_carry_ok:
        print(
            "  VERDICT: ORTHOGONAL CANDIDATE FACTOR — funding-acceleration is a real standalone\n"
            "  edge (positive IS+OOS, cost-honest at 2×), DISTINCT from the carry LEVEL (low\n"
            "  signal AND net corr to carry), and residual-additive vs the trend+carry+flow book.\n"
            "  2nd-order funding dynamics carry independent crowding signal the level cannot see.\n"
            "  Recommend PROMOTE to a walk-forward / held-OOS CONFIRMATION before the combiner.\n"
            "  Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / -23%) until that reveal."
        )
    elif real_edge and not distinct_from_carry:
        print(
            "  VERDICT: REJECT — REDUNDANT WITH CARRY. The acceleration HAS a standalone edge,\n"
            "  but it is COLLINEAR with the funding LEVEL in the book (|corr to carry| >= 0.50).\n"
            "  The 'change' is not independent of the 'level' on this universe — it would double-\n"
            "  count the carry leg's risk, not add a new factor. Baseline UNCHANGED."
        )
    elif real_edge and distinct_from_carry and not resid_ok:
        print(
            "  VERDICT: REJECT — SPANNED BY THE BOOK. Low pairwise corr to carry, but the accel\n"
            "  net is explained away by the JOINT trend+carry+flow regression (resid collapses).\n"
            "  Not independently additive — no new info for the combiner. Baseline UNCHANGED."
        )
    else:
        print(
            "  VERDICT: REJECT — NO STANDALONE EDGE (or cost-eaten / window-fragile). The funding\n"
            "  dynamics do not carry a usable factor on this universe at realistic taker cost.\n"
            "  Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / -23%)."
        )


if __name__ == "__main__":
    main()
