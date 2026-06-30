"""iter-005 PROBE — IS-only forensic of candidate single-changes on the iter-003 stack.

READ-ONLY exploration. Every candidate is the iter-003 stack with EXACTLY ONE signal-layer
change, run through the SAME hysteresis band (delta=0.005) + leak-safe net_from_raw + vol-target.
The purpose is to pick the highest-EV ONE change for iter-005 from IS numbers — gross-strength
(attacks the +0.29 ceiling) AND all-weather (attacks the bull-only profile).

Candidates probed (all banded delta=0.005, sector-neutralized, inverse-vol scaled like iter-002):
  A. Single-horizon within-sector momentum at {3-1, 6-1, 12-1}m (skip-1m), + fast 1m (no skip).
  B. MULTI-HORIZON blends (equal-weight gross-normed sleeves) over horizon subsets.
  C. RESIDUAL (market-beta-stripped) within-sector momentum (Blitz-Huij-Martens style).
  D. Cross-sectional DISPERSION gate scaling iter-003 gross (all-weather attack).
  E. Within-sector LOW-VOL sleeve (positive-EV complement check — the iter-004 lesson).

Everything is sliced < OOS_CUTOFF (2025-03-24); OOS is NEVER computed (no --confirm path here).
Leak-safety: every signal uses only close.shift(>=21) and trailing rolling stats; the band + net
are the proven iter-003 leak-safe path; betas/dispersions are .shift(1)-lagged before use.

Run: uv run python analysis/portfolio/tradfi/iter_005_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_002_sector_rel as i2  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DELTA = i3.CHOSEN_DELTA  # 0.005 — identical band to iter-003 for apples-to-apples
SKIP = 21  # standard 1-month skip


def _rvol(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change().rolling(ct.VOL_WIN).std()


def mom_sleeve(pn, lookback: int, skip: int = SKIP) -> pd.DataFrame:
    """Within-sector inverse-vol momentum over (close.shift(skip)/close.shift(lookback)-1)."""
    close = pn["close"]
    mom = close.shift(skip) / close.shift(lookback) - 1.0
    raw = mom / _rvol(close)
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def fast_mom_sleeve(pn) -> pd.DataFrame:
    """Within-sector 1-month momentum, NO skip (close/close.shift(21)-1). iter-004 showed +EV."""
    close = pn["close"]
    raw = (close / close.shift(21) - 1.0) / _rvol(close)
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def resid_mom_sleeve(pn, lookback: int = 252, skip: int = SKIP, beta_win: int = 63) -> pd.DataFrame:
    """Market-beta-stripped within-sector momentum (residual momentum).

    Strip each name's market exposure from its DAILY returns using a past-only rolling beta, then
    accumulate the RESIDUAL return over the [shift(lookback), shift(skip)] window as the momentum
    signal. Idiosyncratic by construction (market crashes / dash-for-trash hit the market leg, not
    the residual), inverse-(residual)-vol scaled, then sector-neutralized.

    Leak-safe: mkt is the equal-weight cross-sectional mean daily return; beta = rolling_beta(...,
    beta_win) ends at the current bar but is .shift(1)-lagged before residualizing, so residual[t]
    uses only beta estimated through t-1. The window [shift(252), shift(21)] is all past.
    """
    close = pn["close"]
    ret = close.pct_change()
    mkt = ret.mean(axis=1)
    beta = nz.rolling_beta(ret, mkt, beta_win).shift(1)  # past-only beta
    resid = ret.sub(beta.mul(mkt, axis=0))  # idiosyncratic daily return
    cum = resid.cumsum()  # residual cumulative (log-ish) return path
    rmom = cum.shift(skip) - cum.shift(lookback)  # residual return over the skip-1m..lookback window
    rvol = resid.rolling(ct.VOL_WIN).std()  # inverse RESIDUAL-vol scaling
    raw = rmom / rvol
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def lowvol_sleeve(pn) -> pd.DataFrame:
    """Within-sector LOW-VOL: long low-realized-vol names / short high-vol names (negate rvol).

    raw = sector_neutralize( -zscore_within_nothing( rvol63 ) ). We feed -(rvol) directly so that
    the per-sector demean makes it long the lowest-vol / short the highest-vol name in each sector.
    Past-only (trailing 63d realized vol). Positive-EV check for an orthogonal complement.
    """
    close = pn["close"]
    raw = -_rvol(close)  # higher vol -> more negative -> shorted after demean
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def _gn(raw: pd.DataFrame) -> pd.DataFrame:
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


def blend(sleeves: list[pd.DataFrame]) -> pd.DataFrame:
    """Equal-weight blend of gross-normed sleeves (each unit-gross first so none dominates)."""
    idx = sleeves[0].index
    cols = sleeves[0].columns
    acc = pd.DataFrame(0.0, index=idx, columns=cols)
    for s in sleeves:
        acc = acc.add(_gn(s).reindex(index=idx, columns=cols).fillna(0.0))
    return acc / len(sleeves)


def metrics(label: str, raw: pd.DataFrame, ret_fwd: pd.DataFrame, *, scale=None):
    """Banded (delta=0.005) IS-only metric bundle. `scale` is an optional past-only gross scalar."""
    if scale is not None:
        raw = raw.mul(scale, axis=0)
    net, w = i3.banded_net(raw, ret_fwd, DELTA)
    gnet, _ = i3.banded_net(raw, ret_fwd, DELTA, cost_on=False)
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    reg = ct.regime_sharpe(ct.is_only(net))
    n_pos = sum(1 for v in reg.values() if v > 0)
    turn = ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)
    mdd = ct.maxdd(ct.is_only(net)) * 100
    return {
        "label": label, "net": sh_net, "gross": sh_gross, "drag": sh_gross - sh_net,
        "reg": reg, "n_pos": n_pos, "turn": turn, "mdd": mdd, "net_series": ct.is_only(net),
    }


def line(m):
    r = m["reg"]
    return (
        f"  {m['label']:30} net={m['net']:+.2f} gross={m['gross']:+.2f} drag={m['drag']:+.2f}  "
        f"bull={r['bull']:+.2f} bear={r['bear']:+.2f} chop={r['chop']:+.2f} ({m['n_pos']}/3)  "
        f"turn={m['turn']:.4f} mDD={m['mdd']:.0f}%"
    )


def corr(a: pd.Series, b: pd.Series) -> float:
    c = a.index.intersection(b.index)
    return float(np.corrcoef(a.loc[c], b.loc[c])[0, 1]) if len(c) > 2 else float("nan")


def main():
    base = ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, None)
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]

    print("=" * 100)
    print("iter-005 PROBE — candidate single-changes on iter-003 stack (banded d=0.005, IS-only)")
    print("=" * 100)

    # baseline reference (iter-003 == 12-1m single horizon)
    m12 = metrics("iter-003 ref (12-1m)", mom_sleeve(pn, 252), ret_fwd)
    print("  REFERENCE:")
    print(line(m12))

    # --- A. single horizons ---
    print("\n  A. SINGLE-HORIZON within-sector momentum (skip-1m) + fast 1m (no skip):")
    m3 = metrics("3-1m (63/21)", mom_sleeve(pn, 63), ret_fwd)
    m6 = metrics("6-1m (126/21)", mom_sleeve(pn, 126), ret_fwd)
    mfast = metrics("fast 1m (no skip)", fast_mom_sleeve(pn), ret_fwd)
    for m in (m3, m6, mfast):
        print(line(m))

    # sleeve net-return correlations (IS) — diversification potential
    print("\n     sleeve IS net-return correlations (lower = more diversifying):")
    print(f"       rho(3-1,6-1)={corr(m3['net_series'],m6['net_series']):+.2f}  "
          f"rho(3-1,12-1)={corr(m3['net_series'],m12['net_series']):+.2f}  "
          f"rho(6-1,12-1)={corr(m6['net_series'],m12['net_series']):+.2f}  "
          f"rho(fast,12-1)={corr(mfast['net_series'],m12['net_series']):+.2f}")

    # --- B. multi-horizon blends ---
    print("\n  B. MULTI-HORIZON blends (equal-weight gross-normed sleeves):")
    s3, s6, s12 = mom_sleeve(pn, 63), mom_sleeve(pn, 126), mom_sleeve(pn, 252)
    sfast = fast_mom_sleeve(pn)
    mb_3h = metrics("blend{3-1,6-1,12-1}", blend([s3, s6, s12]), ret_fwd)
    mb_2h = metrics("blend{6-1,12-1}", blend([s6, s12]), ret_fwd)
    mb_4h = metrics("blend{fast,3-1,6-1,12-1}", blend([sfast, s3, s6, s12]), ret_fwd)
    mb_f12 = metrics("blend{fast,12-1}", blend([sfast, s12]), ret_fwd)
    for m in (mb_2h, mb_3h, mb_4h, mb_f12):
        print(line(m))

    # --- C. residual (market-beta-stripped) momentum ---
    print("\n  C. RESIDUAL (market-beta-stripped) within-sector momentum:")
    mr12 = metrics("resid 12-1m", resid_mom_sleeve(pn, 252), ret_fwd)
    mr6 = metrics("resid 6-1m", resid_mom_sleeve(pn, 126), ret_fwd)
    mr_blend = metrics("resid blend{6-1,12-1}",
                       blend([resid_mom_sleeve(pn, 126), resid_mom_sleeve(pn, 252)]), ret_fwd)
    for m in (mr12, mr6, mr_blend):
        print(line(m))
    print(f"     rho(resid12-1, total12-1) IS net = {corr(mr12['net_series'],m12['net_series']):+.2f}")

    # --- D. cross-sectional dispersion gate on iter-003 ---
    print("\n  D. DISPERSION gate scaling iter-003 gross (all-weather attack):")
    # past-only cross-sectional dispersion: rolling std across names of daily returns, smoothed
    ret = pn["close"].pct_change()
    xs_disp = ret.std(axis=1)  # cross-sectional return dispersion per day
    disp_smooth = xs_disp.rolling(21).mean().shift(1)  # past-only ~1m smoothing
    # normalize to a 0..1+ scaler vs its own trailing median (past-only), clipped
    med = disp_smooth.rolling(252, min_periods=63).median().shift(1)
    scaler = (disp_smooth / med).clip(0.0, 1.5).fillna(0.0)
    md_gate = metrics("iter-003 x disp-gate", mom_sleeve(pn, 252), ret_fwd, scale=scaler)
    print(line(md_gate))
    # also gate the best multi-horizon blend
    md_gate_b = metrics("blend{6-1,12-1} x disp-gate", blend([s6, s12]), ret_fwd, scale=scaler)
    print(line(md_gate_b))

    # --- E. low-vol complement sleeve (positive-EV check) ---
    print("\n  E. within-sector LOW-VOL sleeve (orthogonal-complement positive-EV check):")
    mlv = metrics("low-vol standalone", lowvol_sleeve(pn), ret_fwd)
    print(line(mlv))
    mlv_blend = metrics("blend{12-1, low-vol}", blend([s12, lowvol_sleeve(pn)]), ret_fwd)
    print(line(mlv_blend))
    print(f"     rho(low-vol, 12-1) IS net = {corr(mlv['net_series'],m12['net_series']):+.2f}")

    # --- summary table sorted by net ---
    allm = [m12, m3, m6, mfast, mb_2h, mb_3h, mb_4h, mb_f12, mr12, mr6, mr_blend,
            md_gate, md_gate_b, mlv, mlv_blend]
    print("\n  " + "=" * 96)
    print("  SUMMARY (sorted by IS net Sharpe) — bar: net>=+0.30 promotable, all-weather>=2/3:")
    print("  " + "=" * 96)
    for m in sorted(allm, key=lambda x: -x["net"]):
        promo = "PROMO" if (m["net"] >= 0.30 and m["n_pos"] >= 2) else ""
        leak = "  <<LEAK?" if m["net"] > 1.0 else ""
        print(line(m) + f"  {promo}{leak}")


if __name__ == "__main__":
    main()
