"""iter-001 diagnostics — IS-ONLY forensic of the dollar-neutral XS-momentum anchor.

READ-ONLY characterization for the Critic to judge BUG vs REAL NEGATIVE. Does NOT modify the
anchor (`iter_001_xsmom.xsmom_raw` stays the pre-registered 12-1m). The negated-signal and
alt-lookback numbers are robustness CHARACTERIZATION, not anchor tuning. Every metric is sliced
strictly < OOS_CUTOFF (2025-03-24); OOS stays hidden — no post-cutoff number is computed.

Run: uv run python analysis/portfolio/tradfi/iter_001_diag.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_001_xsmom as anchor  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

CUT = ct.OOS_CUTOFF


def load_universe():
    base = ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    return ct.load_tradfi(syms, None)


def mom_raw(pn, lookback, skip, vol_win=ct.VOL_WIN):
    """Dollar-neutral inverse-vol momentum for an arbitrary (lookback, skip) — diagnostic only."""
    close = pn["close"]
    mom = close.shift(skip) / close.shift(lookback) - 1.0
    rvol = close.pct_change().rolling(vol_win).std()
    return nz.dollar_neutralize(mom / rvol)


def net_nocost(raw, ret_fwd):
    """Gross (cost-off) vol-targeted net — mirrors net_from_raw minus the turnover cost term."""
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    return ct.vol_target(pnl.dropna())


def is_sharpe(net):
    return ct.msharpe(net, ct.LO0, CUT)


def section(title):
    print("\n" + title)
    print("-" * len(title))


def main():
    coins = load_universe()
    pn = ct.panels(coins)
    raw = anchor.xsmom_raw(pn)
    ret_fwd = pn["ret_fwd"]
    net, w = ct.net_from_raw(raw, ret_fwd)

    gross = net_nocost(raw, ret_fwd)
    sh_net, sh_gross = is_sharpe(net), is_sharpe(gross)

    print("=" * 78)
    print("iter-001 DIAGNOSTICS — IS-ONLY (< 2025-03-24); OOS HIDDEN")
    print("=" * 78)
    print(f"universe ingested: {len(coins)} names  |  anchor IS_Sharpe={sh_net:+.2f}")
    print(
        f"  cost drag: gross IS_Sharpe={sh_gross:+.2f} -> net {sh_net:+.2f}  "
        f"(drag {sh_gross - sh_net:+.2f}; negative is SIGNAL-driven not cost-driven if gross<0)"
    )

    # --- 0. Data-grain characterization (weekend padding) -------------------------
    section("0. DATA GRAIN (calendar-daily vs trading-daily)")
    close = pn["close"]
    is_idx = close.index < CUT
    rr = close.pct_change()[is_idx]
    zero_frac = float((rr == 0).mean().mean())
    bars_per_yr = close[is_idx].groupby(close[is_idx].index.year).size()
    print(
        f"  bars/year (IS): min={int(bars_per_yr.min())} max={int(bars_per_yr.max())} "
        f"(252=trading-day, ~365=calendar-day)"
    )
    print(f"  zero-return-bar fraction (IS, mean over names): {zero_frac * 100:.1f}%")
    print(
        "  -> shift(252)~8.3 calendar-months (NOT 12), rolling(63)-rvol spans ~29% flat "
        "weekend bars"
    )

    # --- 1. Breadth over time -----------------------------------------------------
    section("1. BREADTH (non-NaN signal names per month, IS)")
    active = raw.notna().sum(axis=1)
    active_is = active[active.index < CUT]
    by_month = active_is.groupby(active_is.index.to_period("M")).mean()
    first20 = by_month[by_month >= 20]
    first20_date = str(first20.index[0]) if len(first20) else "never"
    n_below20 = int((by_month < 20).sum())
    print(
        f"  monthly active names: min={by_month.min():.0f}  median={by_month.median():.0f}  "
        f"max={by_month.max():.0f}  (across {len(by_month)} IS months)"
    )
    print(f"  first month with >=20 active: {first20_date}  |  months with <20 active: {n_below20}")
    print(
        "  ragged-start cohorts: 30 names from 2018-01 (signals ~2019-01 after 252d warmup); "
        "ZM/UBER/PLTR 2020-10; DELL/HPE/COHR/MRVL/NOW 2022-05"
    )

    # --- 2. Book sanity -----------------------------------------------------------
    section("2. BOOK SANITY (lagged weight book w, IS)")
    w_is = w[w.index < CUT]
    gross = w_is.abs().sum(axis=1)
    live = gross > 1e-9
    g = gross[live]
    net_dollar = w_is[live].sum(axis=1)
    maxname = w_is[live].abs().max(axis=1)
    longs = (w_is[live] > 0).sum(axis=1)
    shorts = (w_is[live] < 0).sum(axis=1)
    print(f"  mean gross sum|w|: {g.mean():.3f}  (pre-vol-target target ~1.0)")
    print(
        f"  dollar-neutrality |row sum w|: mean={net_dollar.abs().mean():.2e}  "
        f"max={net_dollar.abs().max():.2e}  (should be ~0)"
    )
    print(
        f"  max single-name |w| / gross: mean={(maxname / g).mean() * 100:.1f}%  "
        f"max={(maxname / g).max() * 100:.1f}%  (>25% = concentration pathology)"
    )
    print(f"  long count: mean={longs.mean():.1f}  short count: mean={shorts.mean():.1f}")
    conc_bad = (maxname / g).max() > 0.25
    degen = bool(g.mean() < 0.5 or net_dollar.abs().max() > 1e-3 or conc_bad)
    print(
        f"  DEGENERATE: {'YES' if degen else 'NO'}  (gross~1, neutral~0, no single name >25% gross)"
    )

    # --- 3. Per-regime + per-year + worst month -----------------------------------
    section("3. REGIME / YEAR DECOMPOSITION (IS)")
    net_is = ct.is_only(net)
    reg = ct.regime_of(net_is.index)
    rs = ct.regime_sharpe(net_is)
    for lab in ("bull", "bear", "chop"):
        sub = net_is[reg == lab]
        nm = sub.groupby(sub.index.to_period("M")).sum()
        print(
            f"  {lab:5} Sharpe={rs[lab]:+.2f}  months={len(nm)}  "
            f"netTot={(np.expm1(np.log1p(sub).sum())) * 100:+.0f}%"
        )
    print("  per-year Sharpe:")
    for yr, sub in net_is.groupby(net_is.index.year):
        nm = sub.groupby(sub.index.to_period("M")).sum()
        sh = nm.mean() / nm.std() * np.sqrt(12) if len(nm) > 1 and nm.std() > 0 else float("nan")
        print(f"    {yr}: Sharpe={sh:+.2f}  ({len(nm)} months)")
    monthly = net_is.groupby(net_is.index.to_period("M")).sum()
    print(f"  worst IS month: {monthly.idxmin()}  ret={monthly.min() * 100:+.1f}%")

    # --- 4. Sign / robustness characterization (NOT anchor tuning) ----------------
    section("4. SIGN / LOOKBACK ROBUSTNESS (diagnostic characterization ONLY)")
    neg_net, _ = ct.net_from_raw(-raw, ret_fwd)
    print(f"  anchor 12-1m (252/21/63)      IS_Sharpe={is_sharpe(net):+.2f}   [pre-registered]")
    print(
        f"  NEGATED -anchor               IS_Sharpe={is_sharpe(neg_net):+.2f}   "
        "(reversal vs momentum check)"
    )
    for name, lb, sk in (("6-1m  (126/21/63)", 126, 21), ("3-1m  ( 63/21/63)", 63, 21)):
        alt, _ = ct.net_from_raw(mom_raw(pn, lb, sk), ret_fwd)
        print(f"  alt {name}          IS_Sharpe={is_sharpe(alt):+.2f}")
    print("  (anchor STAYS 252/21/63 per brief; these only characterize robustness of the sign)")

    # --- 5. Sector / beta exposure (dollar-neutral != beta/sector-neutral) --------
    section("5. SECTOR / BETA EXPOSURE (motivates iter-002 beta / iter-003 sector)")
    # realized rough beta: regress pre-vol-target book pnl on equal-weight market fwd return.
    mkt = ret_fwd.mean(axis=1)
    book_pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    df = pd.concat([book_pnl.rename("p"), mkt.rename("m")], axis=1).dropna()
    df = df[df.index < CUT]
    beta = float(df["p"].cov(df["m"]) / df["m"].var())
    print(
        f"  realized net market-beta (book vs equal-weight universe, IS): {beta:+.3f}  "
        "(0 = beta-neutral; dollar-neutral is NOT)"
    )
    # net sector tilt: mean over IS of per-sector summed weight (in gross units, gross~1).
    sec_of = {c: ut.SECTOR_MAP.get(c) for c in w_is.columns}
    tilts = {}
    for sec in sorted(set(sec_of.values())):
        cols = [c for c in w_is.columns if sec_of[c] == sec]
        tilts[sec] = float(w_is[live][cols].sum(axis=1).mean())
    ranked = sorted(tilts.items(), key=lambda kv: -abs(kv[1]))
    print("  mean net sector tilt (fraction of ~1.0 gross; +long / -short):")
    for sec, t in ranked:
        n = sum(1 for c in sec_of.values() if c == sec)
        print(f"    {sec:9} {t:+.3f}  ({n} names)")
    top = ranked[0]
    print(f"  largest net sector tilt: {top[0]} {top[1]:+.3f}")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
