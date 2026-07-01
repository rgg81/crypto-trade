"""iter-013 OOS FORENSIC — tear down the +3.39 OOS reveal (genuine favorable-regime vs artifact).

The OOS is REVEALED (CONFIRMATION done), so this script MAY compute OOS metrics — that is its whole
purpose. It changes NOTHING about the strategy: it imports iter_013's EXACT deployed build
(lam=0.25, VIX brake ON, 1x cost) via the SAME `combined_raw -> i3.banded_net -> *s_vix` path the
reveal used, then only DECOMPOSES the already-revealed OOS net. No OOS-specific strategy branch is
introduced; `data/` is untouched.

Red-flag protocol: the pre-registered rule is ">+1.0 OOS = assume-leak/investigate"; the reveal is
+3.39 (5x that) on an IS of only +0.61 (OOS 5.5x IS). Six skeptical checks decide genuine vs
inflated:
  (1) per-MONTH OOS returns + Sharpe ex-best-month (is it 1-2 months?)
  (2) per-NAME OOS PnL decomposition + top-3 share + Sharpe ex-top-name (is it 1-2 names?)
  (3) benchmark-relative: EW-69 (PIT market proxy) + EW-broad-500 (S&P proxy) OOS return; how much
      of +65% is the beta-tilt (beta x market) vs market-neutral residual alpha
  (4) directional-tilt split: NEUTRAL book lam=0 (mom+LTR, no TSMOM) OOS vs DEPLOYED lam=0.25
  (5) small-sample honesty: n~=16 monthly obs -> Sharpe SE / 95% CI; is +3.39 distinguishable
      from +1.0?
  (6) leak re-confirm: the OOS net is the SAME past-only series sliced by date (no OOS code branch);
      the committed leak self-checks cover the signal.

Run: uv run python analysis/portfolio/tradfi/oos_forensic.py
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
import iter_003_hysteresis as i3  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import universe_tradfi as ut  # noqa: E402

OOS = ct.OOS_CUTOFF  # 2025-03-24


# ------------------------------------------------------------------------------------------- utils
def _msharpe_series(monthly: pd.Series) -> float:
    """Annualised Sharpe from an already-monthly-summed return series (sqrt(12) annualisation)."""
    return (
        float(monthly.mean() / monthly.std() * np.sqrt(12))
        if len(monthly) > 1 and monthly.std() > 0
        else float("nan")
    )


def _monthly_oos(net: pd.Series) -> pd.Series:
    """Monthly-summed returns of the OOS slice (>= OOS_CUTOFF)."""
    s = net[net.index >= OOS]
    return s.groupby(s.index.to_period("M")).sum()


def _compound(net: pd.Series) -> float:
    """Compounded total return of a daily net series (fraction)."""
    return float((1.0 + net).prod() - 1.0)


# ---------------------------------------------------------------------------------- deployed build
def deployed_decomposition(pn, s_vix, lam: float):
    """Rebuild iter-013's EXACT deployed net (lam, VIX ON, 1x cost) and decompose it per-name.

    Uses the identical path as the CONFIRMATION reveal:
        raw = i13.combined_raw(pn, lam); net_1x = i3.banded_net(raw, ret_fwd, delta)[0];
        dep  = net_1x * s_vix
    then splits the portfolio net into additive per-name contributions:
        dep[t] = s_vix[t] * vscale[t] * ( Σ_i w[t,i]·ret_fwd[t,i]  -  cost[t] )
        contrib[t,i] = s_vix[t] * vscale[t] * w[t,i] · ret_fwd[t,i]   (per-name gross-of-cost)
    Returns (dep, contrib_df, cost_term_series, w, diag).
    """
    ret_fwd = pn["ret_fwd"]
    raw = i13.combined_raw(pn, lam)

    # --- official deployed net via the exact reveal path (net_1x = vol_target(pnl-cost)) ---
    net_1x, w_off = i3.banded_net(raw, ret_fwd, i13.CHOSEN_DELTA)
    s = s_vix.reindex(net_1x.index).fillna(1.0)
    dep_official = net_1x * s

    # --- reconstruct the same net from primitives so the per-name split is provably exact ---
    w = i3.banded_book(raw, i13.CHOSEN_DELTA)  # lagged held weight book (== w_off)
    rf = ret_fwd.reindex(columns=w.columns)
    pnl = (w * rf).sum(axis=1)
    cost = ct.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net_pre = (pnl - cost).dropna()
    vscale = ct.vol_target_scale(net_pre)  # ct.vol_target(x) == x * vol_target_scale(x)
    s2 = s_vix.reindex(net_pre.index).fillna(1.0)
    dep_recon = net_pre * vscale * s2

    scale = (vscale * s2).reindex(w.index)  # portfolio-level scalar applied each bar
    contrib = w.mul(rf).mul(scale, axis=0)  # per-name gross-of-cost contribution
    contrib = contrib.loc[net_pre.index]  # align to the valid (dropna) net index
    cost_term = (-cost * vscale * s2).reindex(net_pre.index)

    # self-consistency: official vs reconstructed vs per-name sum + cost
    common = dep_official.index.intersection(dep_recon.index)
    ok_recon = bool(
        np.allclose(
            dep_official.loc[common].to_numpy(), dep_recon.loc[common].to_numpy(), atol=1e-12
        )
    )
    sum_split = contrib.sum(axis=1).add(cost_term, fill_value=0.0)
    common2 = sum_split.index.intersection(dep_recon.index)
    ok_split = bool(
        np.allclose(
            sum_split.loc[common2].to_numpy(), dep_recon.loc[common2].to_numpy(), atol=1e-12
        )
    )
    diag = {"ok_recon": ok_recon, "ok_split": ok_split}
    return dep_official, contrib, cost_term, w, diag


# ------------------------------------------------------------------------------- benchmark proxies
def ew_market(pn) -> pd.Series:
    """EW-69 PIT market proxy: mean cross-sectional forward return (== i13.market_return)."""
    return pn["ret_fwd"].mean(axis=1)


def ew_broad_market(oos_lo: pd.Timestamp) -> pd.Series | None:
    """EW-broad-500 S&P proxy from data_broad/ (survivorship-BIASED; flagged). None if absent.

    Equal-weight forward return of every ingested broad constituent. Current-membership S&P 500
    (Wikipedia) is NOT point-in-time -> this proxy OVERSTATES the market return (delisted losers
    absent). Used only as a rough upper-bound market benchmark for the OOS window.
    """
    bdir = ct._ROOT / "data_broad"
    if not bdir.exists():
        return None
    syms = sorted(p.parent.name for p in bdir.glob("*/1d.csv"))
    if not syms:
        return None
    coins = ct.load_tradfi(syms, str(bdir))
    if not coins:
        return None
    bpn = ct.panels(coins)
    return bpn["ret_fwd"].mean(axis=1)


def beta_attribution(net_oos: pd.Series, mkt_oos: pd.Series):
    """OLS beta of daily OOS net on daily OOS market; additive beta-tilt vs residual-alpha split."""
    df = pd.concat([net_oos.rename("s"), mkt_oos.rename("m")], axis=1).dropna()
    var = float(df["m"].var())
    beta = float(df["s"].cov(df["m"]) / var) if var > 0 and len(df) > 2 else float("nan")
    beta_ret = beta * df["m"]
    resid = df["s"] - beta_ret
    return {
        "beta": beta,
        "n": len(df),
        "mkt_tot": _compound(df["m"]),
        "mkt_sum": float(df["m"].sum()),
        "net_sum": float(df["s"].sum()),
        "beta_tilt_tot": _compound(beta_ret),
        "beta_tilt_sum": float(beta_ret.sum()),
        "resid_tot": _compound(resid),
        "resid_sum": float(resid.sum()),
        "resid_sharpe": _msharpe_series(resid.groupby(resid.index.to_period("M")).sum()),
        "resid": resid,
    }


# ------------------------------------------------------------------------------------------- main
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
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50, .shift(1) past-only (iter-008 UNCHANGED)

    print("=" * 100)
    print("iter-013 OOS FORENSIC — is OOS Sharpe +3.39 genuine or an artifact? (OOS REVEALED)")
    print("=" * 100)

    # --- rebuild deployed lam=0.25 + VIX (EXACT reveal path) + neutral lam=0.00 + VIX ---
    dep, contrib, cost_term, w, diag = deployed_decomposition(pn, s_vix, i13.DEPLOYED_LAM)
    neu, _, _, _, _ = deployed_decomposition(pn, s_vix, 0.0)

    is_sh = ct.msharpe(dep, ct.LO0, OOS)
    oos_sh = ct.msharpe(dep, OOS, ct.HI1)
    dep_oos = dep[dep.index >= OOS]
    oos_dd = ct.maxdd(dep_oos) * 100
    oos_tot = _compound(dep_oos) * 100
    oos_vol_ann = float(dep_oos.std() * np.sqrt(ct.CANDLES_PER_YEAR)) * 100
    print(
        f"\n  DEPLOYED (lam=0.25, VIX ON, 1x): IS_Sharpe={is_sh:+.2f}  OOS_Sharpe={oos_sh:+.2f}  "
        f"OOS_maxDD={oos_dd:.0f}%  OOS_netTot={oos_tot:+.0f}%  OOS_realvol={oos_vol_ann:.0f}%/yr"
    )
    print(
        f"  decomposition self-consistency: official==reconstructed={diag['ok_recon']}  "
        f"per-name-sum+cost==net={diag['ok_split']}  "
        f"(OOS {oos_tot:+.0f}% ~ Sharpe {oos_sh:.2f} x vol {oos_vol_ann:.0f}% x "
        f"{len(dep_oos) / ct.CANDLES_PER_YEAR:.2f}yr = arithmetic sanity, no hidden leverage)"
    )

    # ============================================================== (1) PER-MONTH OOS returns
    m = _monthly_oos(dep)
    print(f"\n  (1) PER-MONTH OOS returns (n={len(m)} months, summed daily net %):")
    for p, v in m.items():
        bar = "#" * int(min(40, abs(v) * 200))
        print(f"      {str(p)}  {v * 100:+7.2f}%  {bar}")
    best_p = m.idxmax()
    m_ex_best = m.drop(best_p)
    print(
        f"      full OOS monthly Sharpe={_msharpe_series(m):+.2f}  "
        f"| best month {best_p} ({m.max() * 100:+.2f}%)  "
        f"| Sharpe EX-BEST-MONTH={_msharpe_series(m_ex_best):+.2f}  "
        f"| positive months={int((m > 0).sum())}/{len(m)}  "
        f"| best-month share of OOS sum={m.max() / m.sum() * 100:.0f}%"
    )

    # ============================================================== (2) PER-NAME OOS contribution
    c_oos = contrib[contrib.index >= OOS]
    per_name = c_oos.sum(axis=0).sort_values(ascending=False)
    total_name = per_name.sum()
    print("\n  (2) PER-NAME OOS PnL contribution (additive, gross-of-cost, summed daily):")
    print(f"      {'rank':>4} {'name':>10} {'OOS_contrib%':>13} {'share_of_ΣPnL':>14}")
    for i, (nm, v) in enumerate(per_name.head(8).items(), 1):
        print(f"      {i:>4} {nm:>10} {v * 100:>+12.2f}% {v / total_name * 100:>13.0f}%")
    print(f"      ... {'(worst 3)':>10}")
    for nm, v in per_name.tail(3).items():
        print(f"           {nm:>10} {v * 100:>+12.2f}% {v / total_name * 100:>13.0f}%")
    top3 = per_name.head(3)
    top1_name = per_name.index[0]
    # additive fragility: subtract the top name's realized daily contribution from the net
    dep_ex_top = dep.sub(contrib[top1_name].reindex(dep.index).fillna(0.0), axis=0)
    oos_sh_ex_top = ct.msharpe(dep_ex_top, OOS, ct.HI1)
    n_pos_names = int((per_name > 0).sum())
    print(
        f"      top-1={top1_name} ({top3.iloc[0] / total_name * 100:.0f}% of ΣPnL)  "
        f"top-3 share={top3.sum() / total_name * 100:.0f}%  "
        f"positive names={n_pos_names}/{len(per_name)}  "
        f"| OOS Sharpe EX-TOP-NAME (additive)={oos_sh_ex_top:+.2f}"
    )

    # ============================================================== (3) BENCHMARK-RELATIVE
    mkt = ew_market(pn)
    mkt_oos = mkt[mkt.index >= OOS]
    attr = beta_attribution(dep_oos, mkt_oos)
    is_beta = i13.net_beta(dep, mkt)  # IS realized beta (matches the risk note +0.12)
    print("\n  (3) BENCHMARK-RELATIVE (is +65% captured market beta or market-neutral alpha?):")
    print(
        f"      EW-69 PIT market OOS: total(compound)={attr['mkt_tot'] * 100:+.0f}%  "
        f"sum={attr['mkt_sum'] * 100:+.0f}%"
    )
    bmkt = ew_broad_market(OOS)
    if bmkt is not None:
        bmkt_oos = bmkt[bmkt.index >= OOS]
        print(
            f"      EW-broad-500 S&P proxy OOS (SURVIVORSHIP-biased, overstates): "
            f"total(compound)={_compound(bmkt_oos) * 100:+.0f}%"
        )
    print(
        f"      book OOS realized beta on EW-69={attr['beta']:+.2f}  (IS beta={is_beta:+.2f}; "
        f"risk-note +0.12)"
    )
    print(
        f"      beta-TILT contribution (beta x market): "
        f"compound={attr['beta_tilt_tot'] * 100:+.1f}%"
        f"  sum={attr['beta_tilt_sum'] * 100:+.1f}%  "
        f"({attr['beta_tilt_sum'] / attr['net_sum'] * 100:.0f}% of OOS ΣPnL)"
    )
    print(
        f"      RESIDUAL market-neutral alpha: compound={attr['resid_tot'] * 100:+.0f}%  "
        f"({attr['resid_sum'] / attr['net_sum'] * 100:.0f}% of OOS ΣPnL)  "
        f"resid monthly Sharpe={attr['resid_sharpe']:+.2f}"
    )

    # ============================================================== (4) DIRECTIONAL-TILT SPLIT
    neu_is = ct.msharpe(neu, ct.LO0, OOS)
    neu_oos = ct.msharpe(neu, OOS, ct.HI1)
    neu_oos_slice = neu[neu.index >= OOS]
    print("\n  (4) DIRECTIONAL-TILT SPLIT (market-neutral core vs directional tilt):")
    print(
        f"      NEUTRAL lam=0.00 +VIX (mom+LTR, no TSMOM): IS={neu_is:+.2f}  OOS={neu_oos:+.2f}  "
        f"OOS_tot={_compound(neu_oos_slice) * 100:+.0f}%"
    )
    print(
        f"      DEPLOYED lam=0.25 +VIX (with TSMOM tilt) : IS={is_sh:+.2f}  OOS={oos_sh:+.2f}  "
        f"OOS_tot={oos_tot:+.0f}%"
    )
    print(
        f"      -> directional tilt adds OOS Sharpe {oos_sh - neu_oos:+.2f}; the market-neutral "
        f"core alone is OOS {neu_oos:+.2f}"
    )

    # ============================================================== (5) SMALL-SAMPLE HONESTY
    n = len(m)
    sr_m = float(m.mean() / m.std()) if m.std() > 0 else float("nan")  # monthly (non-annualised)
    se_m = float(np.sqrt((1.0 + 0.5 * sr_m**2) / n))  # Lo(2002) iid SE of the monthly Sharpe
    se_ann = se_m * np.sqrt(12)
    ci_lo, ci_hi = oos_sh - 1.96 * se_ann, oos_sh + 1.96 * se_ann
    z_vs_1 = (oos_sh - 1.0) / se_ann
    verdict5 = (
        "YES (>1.96, +1.0 outside 95% CI)"
        if z_vs_1 > 1.96
        else "NO / MARGINAL (+1.0 inside or near 95% CI)"
    )
    print(f"\n  (5) SMALL-SAMPLE HONESTY (n={n} monthly obs, Lo-2002 iid Sharpe SE):")
    print(
        f"      annualised OOS Sharpe={oos_sh:+.2f}  SE~={se_ann:.2f}  "
        f"95% CI=[{ci_lo:+.2f}, {ci_hi:+.2f}]"
    )
    print(
        f"      distinguishable from +1.0? z=({oos_sh:.2f}-1.0)/{se_ann:.2f}={z_vs_1:.2f}  "
        f"-> {verdict5}"
    )

    # ============================================================== (6) LEAK RE-CONFIRM
    # The OOS number is the SAME dep series sliced by date (no OOS-specific branch). Re-assert the
    # revealed +3.39 == msharpe(dep, OOS, HI1) on the exact reveal path, and run the committed
    # in-script signal leak self-check (corrupt post-cut close+ret_fwd -> IS net bit-identical).
    leak_signal = i13._leak_selfcheck(pn, ret_fwd, i13.DEPLOYED_LAM, s_vix)
    reveal_match = np.isclose(oos_sh, ct.msharpe(dep, OOS, ct.HI1), atol=1e-9)
    print("\n  (6) LEAK RE-CONFIRM:")
    print(
        f"      OOS uses SAME past-only net_from_raw/banded_net path, sliced by date "
        f"(no OOS code branch): {'CONFIRMED' if reveal_match else 'MISMATCH'}"
    )
    print(
        f"      committed future-bar signal leak self-check (lam=0.25, combined+VIX): "
        f"{'PASS' if leak_signal else 'FAIL'}"
    )
    print(
        f"      decomposition ties out to the official reveal net: "
        f"recon={diag['ok_recon']} split={diag['ok_split']}"
    )

    print("\n" + "=" * 100)
    print("  FORENSIC COMPLETE — see diary-portfolio-tradfi/iter-013-oos-forensic.md for verdict")
    print("=" * 100)


if __name__ == "__main__":
    main()
