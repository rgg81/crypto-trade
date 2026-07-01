"""Worst-months forensic on the CONFIRMED iter-015 deployed book (IS-only, leak-safe).

DIAGNOSIS ONLY — this script changes NOTHING about the strategy. It decomposes the deployed
book's worst IN-SAMPLE months (< 2025-03-24) into (1) a ranked worst-month list, (2) an EXACT
additive per-sleeve attribution {XS-momentum, LTR, TSMOM directional} + an isolated VIX-brake
effect, (3) per-name attribution for the single worst 2018 and worst 2019 months, and (4) a
regime characterization (EW-69 market return, VIX level/path, cross-sectional dispersion,
prior-winner-minus-loser spread) that types each failure as CRASH (directional-beta) vs
MOMENTUM-REVERSAL (factor crash) vs DISPERSION-COLLAPSE (melt-up). It then runs a few cheap
IS-only IMPROVEMENT PROBES (does the tweak help 2018/2019 without hurting the good years?) —
probes only characterize; NO strategy change is committed.

=========================================================================================
THE DEPLOYED BOOK (iter-015, of record) — reproduced verbatim from the iter-013/015 modules
=========================================================================================
    mom = gross_norm( iter006.crash_braked_raw )        # crash-braked multi-horizon XS momentum
    ltr = gross_norm( sector_neut( -(c.shift(252)/c.shift(756)-1)/rvol ) )   # 3y-1y LT-reversal
    ts  = gross_norm( sign(c/c.shift(252)-1)/rvol )      # TSMOM directional sleeve (NOT neutral)
    neu = gross_norm( (mom + 0.5*ltr)/1.5 )              # frozen iter-011 neutral engine
    raw = (1-0.25)*neu + 0.25*ts                         # lam=0.25 directional blend
    w   = banded_book_freq(raw, delta=0.010, freq=1)     # iter-015 band + daily
    net = vol_target( w.ret_fwd - cost ) * s_vix         # VIX brake s=clip(20/VIX[t-1],0.5,1)

=========================================================================================
EXACT ADDITIVE SLEEVE ATTRIBUTION (the load-bearing decomposition)
=========================================================================================
The band is path-dependent (not cleanly splittable), but at delta=0.010 the band moves monthly
returns by <~10 bps (reconciled in-script). So attribution is done on the TARGET (pre-band)
gross-normed book, which IS exactly additive, and reconciled to the deployed banded net:

    w_tgt = raw / gross(raw) = w_mom + w_ltr + w_ts        # exact linear split (pre-band)
      w_mom = (1-lam)*(mom/1.5)/gross_A / gross_C          # gross_A = |(mom+0.5ltr)/1.5|
      w_ltr = (1-lam)*(0.5*ltr/1.5)/gross_A / gross_C      # gross_C = |raw|
      w_ts  =    lam * ts            / gross_C
    pnl_sleeve[t] = Σ_i w_sleeve[t-1,i]·ret_fwd[t,i]       # each sleeve's gross PnL, additive
    contrib_sleeve[t] = pnl_sleeve[t] · vt[t]              # common VIX-OFF vol-target scalar
    vix_effect[t]     = net_vt[t]·(s_vix[t]-1)             # incremental brake effect (isolated)
    Σ contrib_sleeve + contrib_cost + vix_effect  ==  deployed VIX-ON net    (reconciles)

Every read is IS-only (< OOS_CUTOFF); no OOS number is ever computed. Data is untouched.

Run: uv run python analysis/portfolio/tradfi/worst_months_forensic.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import universe_tradfi as ut  # noqa: E402

LAM = i13.DEPLOYED_LAM  # 0.25
DELTA = i15.CHOSEN_DELTA  # 0.010
FREQ = i15.CHOSEN_FREQ  # 1


# ---------------------------------------------------------------- sleeve target-weight split ----
def sleeve_target_weights(pn) -> dict[str, pd.DataFrame]:
    """EXACT additive split of the deployed target book w_tgt = w_mom + w_ltr + w_ts (pre-band).

    Each is the gross-normed, per-sleeve contribution to raw = (1-lam)*neutral + lam*tsmom, so the
    three panels sum to gross_norm(raw) bit-for-bit (asserted by the caller). All past-only.
    """
    mom = i11.mom_sleeve(pn)  # unit-gross crash-braked multi-horizon XS momentum
    ltr = i11.ltr_sleeve(pn)  # unit-gross 3y-1y LT-reversal
    ts = i13.tsmom_sleeve(pn)  # unit-gross TSMOM directional
    a = mom.add(ltr * i11.W_LTR, fill_value=0.0) / (1.0 + i11.W_LTR)  # (mom+0.5ltr)/1.5
    gross_a = a.abs().sum(axis=1).replace(0, np.nan)
    neu_mom = (mom / (1.0 + i11.W_LTR)).div(gross_a, axis=0).fillna(0.0)
    neu_ltr = (ltr * i11.W_LTR / (1.0 + i11.W_LTR)).div(gross_a, axis=0).fillna(0.0)
    raw = i13.combined_raw(pn, LAM)
    gross_c = raw.abs().sum(axis=1).replace(0, np.nan)
    cols = raw.columns
    w_mom = (neu_mom.reindex(columns=cols) * (1.0 - LAM)).div(gross_c, axis=0).fillna(0.0)
    w_ltr = (neu_ltr.reindex(columns=cols) * (1.0 - LAM)).div(gross_c, axis=0).fillna(0.0)
    w_ts = (ts.reindex(columns=cols) * LAM).div(gross_c, axis=0).fillna(0.0)
    return {"mom": w_mom, "ltr": w_ltr, "ts": w_ts}


def attribution(pn, ret_fwd, s_vix) -> pd.DataFrame:
    """Per-day additive attribution of the deployed VIX-ON net into {mom, ltr, ts, cost, vix}.

    Sleeves attributed on the VIX-OFF vol-targeted target book; the VIX brake isolated as the
    incremental (s_vix-1) effect. Returns a daily DataFrame whose row-sum == deployed net (IS).
    """
    parts = sleeve_target_weights(pn)
    raw = i13.combined_raw(pn, LAM)
    w_tgt = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    # exactness self-check: the three sleeve panels reconstruct the target book
    recon = parts["mom"].add(parts["ltr"], fill_value=0.0).add(parts["ts"], fill_value=0.0)
    assert np.allclose(recon.fillna(0.0).to_numpy(), w_tgt.fillna(0.0).to_numpy(), atol=1e-12), (
        "sleeve split does not reconstruct the target book"
    )
    rf = ret_fwd.reindex(columns=w_tgt.columns)
    w_lag = w_tgt.shift(1)
    pnl_pre = (w_lag * rf).sum(axis=1)
    cost_pre = ct.COST_SIDE * (w_tgt - w_tgt.shift(1)).abs().sum(axis=1)
    net_pre = (pnl_pre - cost_pre).dropna()  # pre-vol-target, VIX-off, target book
    vt = ct.vol_target_scale(net_pre)  # common VIX-off vol-target scalar
    net_vt = (net_pre * vt).dropna()
    idx = net_vt.index
    sv = s_vix.reindex(idx).fillna(1.0)
    out = pd.DataFrame(index=idx)
    for name, w in parts.items():
        out[name] = (w.shift(1) * rf).sum(axis=1).reindex(idx) * vt.reindex(idx)
    out["cost"] = -cost_pre.reindex(idx) * vt.reindex(idx)
    out["vix"] = net_vt * (sv - 1.0)
    out["net"] = out[["mom", "ltr", "ts", "cost", "vix"]].sum(axis=1)
    return out


# ---------------------------------------------------------------- regime characterization -------
def name_monthly_returns(pn) -> pd.DataFrame:
    """Per-name calendar-month total return (compounded daily open-to-open ret_fwd), IS grid."""
    rf = pn["ret_fwd"]
    return (1.0 + rf).groupby(rf.index.to_period("M")).prod() - 1.0


def prior_mom_rank(pn) -> pd.DataFrame:
    """12-1m momentum (close.shift(21)/close.shift(252)-1) sampled at each month-end (past-only)."""
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0
    return mom.groupby(mom.index.to_period("M")).last()


def month_regime(pn, vix, month: pd.Period) -> dict:
    """EW-69 market return, VIX level/path, cross-sectional dispersion + winner-loser spread."""
    rf = pn["ret_fwd"]
    m = rf[rf.index.to_period("M") == month]
    names_ret = (1.0 + m).prod() - 1.0  # per-name month return
    names_ret = names_ret.dropna()
    mkt = float(names_ret.mean())
    disp = float(names_ret.std())
    vseg = vix[vix.index.to_period("M") == month].dropna()
    # prior 12-1m momentum measured at PRIOR month-end (past-only) -> winner/loser buckets
    pm = prior_mom_rank(pn)
    prior = month - 1
    wl = np.nan
    if prior in pm.index:
        pr = pm.loc[prior].dropna()
        common = pr.index.intersection(names_ret.index)
        pr = pr.loc[common]
        rr = names_ret.loc[common]
        if len(pr) >= 10:
            n = max(3, len(pr) // 3)
            win = rr.loc[pr.nlargest(n).index].mean()
            los = rr.loc[pr.nsmallest(n).index].mean()
            wl = float(win - los)  # prior-winners minus prior-losers this month (<0 = reversal)
    return {
        "mkt": mkt,
        "disp": disp,
        "vix_mean": float(vseg.mean()) if len(vseg) else np.nan,
        "vix_max": float(vseg.max()) if len(vseg) else np.nan,
        "vix_min": float(vseg.min()) if len(vseg) else np.nan,
        "win_los": wl,
    }


def classify(reg: dict, attr_row: pd.Series) -> str:
    """Type the failure: CRASH (beta) / MOMENTUM-REVERSAL / DISPERSION-COLLAPSE (melt-up)."""
    mkt, disp, wl = reg["mkt"], reg["disp"], reg["win_los"]
    ts_bled = attr_row["ts"] < -0.003
    mom_bled = attr_row["mom"] < -0.003
    if mkt < -0.04 and ts_bled:
        return "CRASH (directional-beta: net-long TSMOM into a falling tape)"
    if not np.isnan(wl) and wl < -0.02 and mom_bled:
        return "MOMENTUM-REVERSAL (prior losers beat prior winners; XS-mom book fights it)"
    if mkt > 0.0 and disp < 0.06:
        return "DISPERSION-COLLAPSE (low-dispersion melt-up; neutral book has no spread)"
    if not np.isnan(wl) and wl < 0 and mom_bled:
        return "MOMENTUM-REVERSAL (softer; prior winners lagged)"
    return "MIXED / idiosyncratic"


# ---------------------------------------------------------------- per-name attribution ----------
def deployed_book(pn, ret_fwd, s_vix):
    """Deployed banded book (d=0.010, f=1) + the per-bar VIX-ON vol-target scalar and net series."""
    raw = i13.combined_raw(pn, LAM)
    w = i15.banded_book_freq(raw, DELTA, FREQ)  # already .shift(1)-lagged
    rf = ret_fwd.reindex(columns=w.columns)
    pnl = (w * rf).sum(axis=1)
    cost = ct.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net_pre = (pnl - cost).dropna()
    vt = ct.vol_target_scale(net_pre)
    sv = s_vix.reindex(net_pre.index).fillna(1.0)
    scal = (vt * sv).reindex(w.index)  # per-bar scalar mapping name PnL -> deployed net units
    net = (net_pre * vt * sv).dropna()
    return w, rf, scal, net


def per_name_month(pn, ret_fwd, s_vix, month: pd.Period, topn: int = 6):
    """Top-N losing names in `month` (deployed-net-unit contribution) + position + own return."""
    w, rf, scal, _ = deployed_book(pn, ret_fwd, s_vix)
    inm = w.index.to_period("M") == month
    w_m, rf_m, sc_m = w[inm], rf[inm], scal[inm]
    contrib = (w_m * rf_m).mul(sc_m, axis=0).sum(axis=0)  # per-name month contribution (net units)
    pos = w_m.mean(axis=0)  # mean held weight over the month (sign = long/short)
    own = (1.0 + rf_m).prod(axis=0) - 1.0  # name's own open-to-open month return
    tbl = pd.DataFrame({"contrib": contrib, "pos": pos, "own_ret": own}).dropna(subset=["contrib"])
    return tbl.sort_values("contrib").head(topn)


# ---------------------------------------------------------------- improvement probes ------------
def bear_gate(pn, lookback=252):
    """iter-006 EW-universe bear-state g[t] in {0,1}: 1 when trailing `lookback`-day EW ret < 0."""
    return i6.bear_state(pn["close"], lookback)


def deployed_net_variant(pn, ret_fwd, s_vix, *, lam_series=None, s_extra=None):
    """Deployed net with an optional per-bar directional fraction lam_series and/or extra brake.

    lam_series (past-only Series) replaces the constant LAM in the blend; s_extra multiplies the
    VIX-ON net (an extra outer past-only brake). Both default to the deployed identity.
    """
    if lam_series is None:
        raw = i13.combined_raw(pn, LAM)
    else:
        neu = i13.neutral_raw(pn)
        ts = i13.tsmom_sleeve(pn)
        lam = lam_series.reindex(neu.index).ffill().fillna(LAM)
        raw = neu.mul(1.0 - lam, axis=0).add(ts.mul(lam, axis=0), fill_value=0.0)
    net_1x, _ = i15.banded_net_freq(raw, ret_fwd, DELTA, FREQ, ct.COST_SIDE)
    net = net_1x * s_vix.reindex(net_1x.index).fillna(1.0)
    if s_extra is not None:
        net = net * s_extra.reindex(net.index).fillna(1.0)
    return net


def per_year(net):
    yt = i11.year_table(net)
    return {y: yt[y][0] for y in yt}, {y: yt[y][1] for y in yt}


# ---------------------------------------------------------------- main --------------------------
def main():
    ap = argparse.ArgumentParser()
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
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)

    dep = i15._deployed_net1x(pn, ret_fwd, s_vix, DELTA, FREQ)
    dep_is = ct.is_only(dep)
    monthly = dep_is.groupby(dep_is.index.to_period("M")).sum()

    print("=" * 100)
    print(
        "WORST-MONTHS FORENSIC — deployed iter-015 book (lam=0.25, band d=0.010, VIX-ON), IS-only"
    )
    print("=" * 100)
    print(
        f"  deployed IS Sharpe = {ct.msharpe(dep, ct.LO0, ct.OOS_CUTOFF):+.3f}   "
        f"IS months = {len(monthly)}   (net monthly return = sum of daily net)"
    )

    # --- (1) worst months ranked ---
    worst = monthly.sort_values().head(10)
    print("\n(1) WORST 10 IS MONTHS by deployed net monthly return:")
    print(f"    {'month':>8} {'net%':>8}  year")
    for per, val in worst.items():
        print(f"    {str(per):>8} {val * 100:>+7.2f}%  {per.year}")

    # --- attribution frame (reconcile to deployed) ---
    attr = attribution(pn, ret_fwd, s_vix)
    attr_is = attr[attr.index < ct.OOS_CUTOFF]
    attr_m = attr_is.groupby(attr_is.index.to_period("M")).sum()
    recon_gap = (attr_m["net"] - monthly.reindex(attr_m.index)).abs()
    print(
        f"\n    attribution reconciliation vs deployed banded net: "
        f"mean |gap| = {recon_gap.mean() * 100:.3f}%/mo, max = {recon_gap.max() * 100:.3f}%/mo "
        f"(band effect immaterial at d={DELTA})"
    )

    # --- per-year to confirm 2018/2019 ---
    ysh, yret = per_year(dep)
    print("\n    per-year net Sharpe / return% (IS): ")
    for y in sorted(ysh):
        tag = "  <- NEGATIVE" if ysh[y] < 0 else ""
        print(f"      {y}: Sh={ysh[y]:+.2f}  ret={yret[y]:+5.1f}%{tag}")

    # --- (2) per-sleeve attribution for the worst months ---
    print(
        "\n(2) PER-SLEEVE ATTRIBUTION (contribution to net monthly %, additive; VIX = brake):"
    )
    print(
        f"    {'month':>8} {'net%':>7} | {'XS-mom':>7} {'LTR':>7} {'TSMOM':>7} {'cost':>6} "
        f"{'VIX':>6} | bled"
    )
    focus_months = list(worst.index)
    for per in focus_months:
        if per not in attr_m.index:
            continue
        r = attr_m.loc[per]
        sleeves = {"XS-mom": r["mom"], "LTR": r["ltr"], "TSMOM": r["ts"]}
        bled = min(sleeves, key=sleeves.get)
        print(
            f"    {str(per):>8} {r['net'] * 100:>+6.2f}% | {r['mom'] * 100:>+6.2f}% "
            f"{r['ltr'] * 100:>+6.2f}% {r['ts'] * 100:>+6.2f}% {r['cost'] * 100:>+5.2f}% "
            f"{r['vix'] * 100:>+5.2f}% | {bled}"
        )

    # --- annual sleeve attribution for 2018 + 2019 ---
    print("\n    ANNUAL sleeve attribution (sum of daily contributions, %):")
    print(
        f"   {'year':>6} {'net%':>7} | {'XS-mom':>7} {'LTR':>7} {'TSMOM':>6} {'cost':>5} {'VIX':>6}"
    )
    for yr in (2018, 2019):
        ry = attr_is[attr_is.index.year == yr].sum()
        print(
            f"    {yr:>6} {ry['net'] * 100:>+6.1f}% | {ry['mom'] * 100:>+6.1f}% "
            f"{ry['ltr'] * 100:>+6.1f}% {ry['ts'] * 100:>+6.1f}% {ry['cost'] * 100:>+5.1f}% "
            f"{ry['vix'] * 100:>+5.1f}%"
        )

    # --- the single worst 2018 + worst 2019 month ---
    w2018 = monthly[[p.year == 2018 for p in monthly.index]].idxmin()
    w2019 = monthly[[p.year == 2019 for p in monthly.index]].idxmin()

    # --- (3) per-name attribution for the worst 2018 + worst 2019 month ---
    print(
        "\n(3) PER-NAME ATTRIBUTION (worst 2018 + worst 2019 month; deployed-net-unit contrib):"
    )
    for per in (w2018, w2019):
        reg = month_regime(pn, vix, per)
        tbl = per_name_month(pn, ret_fwd, s_vix, per, topn=6)
        print(
            f"\n    {per} (net {monthly.loc[per] * 100:+.2f}%,  EW-mkt {reg['mkt'] * 100:+.1f}%,  "
            f"dispersion {reg['disp'] * 100:.1f}%):"
        )
        print(f"      {'name':<10} {'contrib%':>9} {'position':>9} {'own_ret%':>9}  read")
        for name, row in tbl.iterrows():
            side = "LONG" if row["pos"] > 0 else "SHORT"
            if row["pos"] > 0 and row["own_ret"] < 0:
                read = "long a crasher"
            elif row["pos"] < 0 and row["own_ret"] > 0:
                read = "short a ripper"
            elif row["pos"] > 0:
                read = "long, mild"
            else:
                read = "short, mild"
            print(
                f"      {ut.stem(name):<10} {row['contrib'] * 100:>+8.2f}% "
                f"{side:>6}{abs(row['pos']) * 100:>4.1f}% {row['own_ret'] * 100:>+8.1f}%  {read}"
            )

    # --- (4) regime characterization + failure type for the worst months ---
    print("\n(4) REGIME CHARACTERIZATION + FAILURE TYPE (worst months):")
    print(
        f"    {'month':>8} {'net%':>7} {'EWmkt%':>7} {'disp%':>6} {'VIXmn':>6} {'VIXmx':>6} "
        f"{'W-L%':>6}  type"
    )
    for per in focus_months:
        reg = month_regime(pn, vix, per)
        typ = classify(reg, attr_m.loc[per]) if per in attr_m.index else "n/a"
        wl = reg["win_los"]
        print(
            f"    {str(per):>8} {monthly.loc[per] * 100:>+6.2f}% {reg['mkt'] * 100:>+6.1f}% "
            f"{reg['disp'] * 100:>5.1f}% {reg['vix_mean']:>6.1f} {reg['vix_max']:>6.1f} "
            f"{(wl * 100 if not np.isnan(wl) else float('nan')):>+5.1f}  {typ}"
        )

    # --- VIX firing detail in Q4-2018 (why the brake whiffed) ---
    print(
        "\n    VIX-brake path in 2018-Q4 (why moderate-VIX whiffed): "
        "s=clip(20/VIX[t-1],0.5,1) — mean scale by month"
    )
    for per in [pd.Period("2018-10"), pd.Period("2018-11"), pd.Period("2018-12")]:
        seg = s_vix[s_vix.index.to_period("M") == per]
        vseg = vix[vix.index.to_period("M") == per]
        print(
            f"      {per}: VIX mean={vseg.mean():.1f} max={vseg.max():.1f}  "
            f"brake scale mean={seg.mean():.2f} min={seg.min():.2f} "
            f"(1.00 = inert; 0.50 = max cut)"
        )

    # ============================================================ IMPROVEMENT PROBES ============
    print("\n" + "=" * 100)
    print("IMPROVEMENT PROBES (IS-only; characterize only — NO strategy change committed)")
    print("=" * 100)
    base_sh, base_ret = per_year(dep)
    goodyrs = [y for y in base_sh if y not in (2010, 2018, 2019)]

    def show(label, net):
        sh, rr = per_year(net)
        d18 = rr[2018] - base_ret[2018]
        d19 = rr[2019] - base_ret[2019]
        dgood = np.mean([rr[y] - base_ret[y] for y in goodyrs])
        npos = sum(1 for y in sh if sh[y] > 0)
        print(
            f"  {label:44} IS_Sh={ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF):+.2f}  +yrs={npos}/16 "
            f"| 2018 {base_ret[2018]:+.1f}->{rr[2018]:+.1f} (Δ{d18:+.1f})  "
            f"2019 {base_ret[2019]:+.1f}->{rr[2019]:+.1f} (Δ{d19:+.1f})  goodΔμ={dgood:+.2f}"
        )

    print(
        f"  {'DEPLOYED (baseline)':44} IS_Sh={ct.msharpe(dep, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
        f"+yrs={sum(1 for y in base_sh if base_sh[y] > 0)}/16 | "
        f"2018 {base_ret[2018]:+.1f}  2019 {base_ret[2019]:+.1f}"
    )

    # PROBE A — gate the DIRECTIONAL sleeve by the EW bear-state (cut lam in a downtrend).
    # Theory: don't stay net-long TSMOM when the market's own 12m trend is DOWN. Generalizes to
    # ALL bears (g=0 in bulls -> identity in the melt-up years the tilt was added for).
    g252 = bear_gate(pn, 252)
    for frac in (0.0, 0.5):
        lam_s = LAM * (1.0 - (1.0 - frac) * g252)  # lam -> lam*frac in bear-state
        show(
            f"A) TSMOM lam->{frac:.1f}*lam in EW-252d bear-state",
            deployed_net_variant(pn, ret_fwd, s_vix, lam_series=lam_s),
        )
    # faster gate (126d) — tests the 2018-fast vs 2019-whipsaw tension
    g126 = bear_gate(pn, 126)
    lam_s = LAM * (1.0 - g126)
    show(
        "A') TSMOM lam->0 in EW-126d bear-state (faster)",
        deployed_net_variant(pn, ret_fwd, s_vix, lam_series=lam_s),
    )

    # PROBE B — a lower VIX base (more sensitive brake). Overfit risk: tuned to 2018-Q4 mid VIX.
    for vb in (16.0, 18.0):
        s_b = i8.vix_scale(vix, base=vb, floor=0.50)
        show(
            f"B) VIX brake base {vb:.0f} (vs 20; more sensitive)",
            deployed_net_variant(pn, ret_fwd, s_b),
        )

    # PROBE C — realized-vol brake on the deployed net (Barroso-style), past-only.
    rv = dep.rolling(21).std().shift(1)
    tgt = float(ct.is_only(dep).rolling(21).std().median())
    s_rv = (tgt / rv).clip(upper=1.0).fillna(1.0)  # de-lever only when realized vol is elevated
    show(
        "C) realized-vol brake (21d, cap<=1) on net",
        deployed_net_variant(pn, ret_fwd, s_vix, s_extra=s_rv),
    )

    # PROBE D — lower the directional fraction globally (does less beta help the bears net-net?)
    for lam2 in (0.15, 0.10):
        raw2 = i13.combined_raw(pn, lam2)
        net2, _ = i15.banded_net_freq(raw2, ret_fwd, DELTA, FREQ, ct.COST_SIDE)
        show(
            f"D) global lam={lam2:.2f} (vs 0.25; less directional)",
            net2 * s_vix.reindex(net2.index).fillna(1.0),
        )

    print(
        "\n  READ: Δ2018/Δ2019 = added annual return% in the bad years; goodΔμ = mean good-year Δ%"
    )
    print("        across the 13 good years (2010/2018/2019 excluded). A fix that helps the bad")
    print(
        "        years with goodΔμ ~ 0 is generalizable; large negative goodΔμ = a bad-year hack."
    )


if __name__ == "__main__":
    main()
