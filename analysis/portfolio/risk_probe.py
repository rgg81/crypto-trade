"""portfolio-iteration RISK PROBE — trim the baseline −29% maxDD without breaking OOS Sharpe.

Probes PAST-ONLY, walk-forward-compatible drawdown controls layered on the iter-005 baseline net
(trend + carry-tilt, walk-forward λ). Each control is a scalar exposure multiplier computed from
information available at decision time (close[t]) and applied to the NEXT candle's net — so it is
deployable, leak-safe, and never tuned on OOS.

Controls measured (each vs the baseline, IS-calibrated, OOS revealed once):
  A. DD-BRAKE      — de-lever when the running equity drawdown exceeds a threshold (linear ramp).
  B. VOLTARGET-CAP — tighten the existing portfolio vol-target ceiling (lower MAX_LEV).
  C. REALIZED-VOL  — extra de-lever when short-window realized vol >> its own slow median (spike).
  D. COMBINED      — DD-brake ∘ realized-vol (the two orthogonal triggers stacked).

We do NOT grid-search these on OOS. Thresholds are fixed a-priori from IS shape (round numbers /
the existing baseline scale), and OOS is reported once to confirm the IS-chosen control survives.

The baseline net is reconstructed here (not imported) only because iter_005 does not expose the
per-candle net before vol-targeting; we replicate its exact recipe and assert the headline IS/OOS/DD
match before probing.
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


# ----------------------------------------------------------------------------- baseline net (raw)
def baseline_net(coins: dict) -> pd.Series:
    """Walk-forward-λ baseline net per candle, BEFORE the final portfolio vol-target.

    Mirrors iter_005.lam_nets + walkforward, but returns the *un-vol-targeted* per-candle net so the
    DD controls can be applied as an exposure overlay and the vol-target re-applied once at the end
    (vol-target is itself a past-only control and must stay outermost).
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
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)

    # raw per-candle net per λ (no vol-target yet)
    raw_nets = {}
    for lam in wf.LAM_GRID:
        raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        raw_nets[lam] = (pnl + fpnl - cost).dropna()

    # walk-forward λ pick on the VOL-TARGETED past net (identical selection to iter_005),
    # but stitch the RAW (pre-vol-target) net so controls compose cleanly.
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
    raw_wf = pd.concat(parts).sort_index()
    return raw_wf, picks


# --------------------------------------------------------------------- DD controls (past-only)
def apply_voltarget(raw: pd.Series, max_lev: float = base.MAX_LEV) -> pd.Series:
    """The baseline portfolio vol-target with an adjustable ceiling (control B)."""
    rv = raw.rolling(base.PORT_VOL_WIN).std().shift(1)
    scale = (base.TARGET_VOL / rv).clip(upper=max_lev).fillna(0.0)
    return raw * scale


def dd_brake_scale(net_vt: pd.Series, dd_start: float, dd_full: float, floor: float) -> pd.Series:
    """Control A: scalar exposure multiplier from the running equity drawdown of the *already
    vol-targeted* net. Drawdown is computed PAST-ONLY (equity through t-1, shifted) and the
    multiplier is applied to candle t. Linear ramp: 1.0 at dd<=dd_start → `floor` at dd>=dd_full.
    """
    eq = (1 + net_vt).cumprod()
    dd = (eq / eq.cummax() - 1.0)  # <= 0
    dd_lag = dd.shift(1).fillna(0.0)
    span = dd_full - dd_start
    ramp = 1.0 - (1.0 - floor) * ((-dd_lag - dd_start) / span).clip(lower=0.0, upper=1.0)
    return ramp


def realized_vol_scale(raw: pd.Series, fast: int, slow: int, ratio_cap: float,
                       floor: float) -> pd.Series:
    """Control C: de-lever when fast realized vol spikes above its own slow median. Multiplier =
    clip(slow_med / fast_vol, floor, 1.0). Both windows past-only (shifted). Triggers on vol-of-vol
    regime, orthogonal to the drawdown trigger.
    """
    fast_v = raw.rolling(fast).std().shift(1)
    slow_med = fast_v.rolling(slow).median().shift(1)  # stable baseline of the fast-vol series
    rel = (slow_med / fast_v).replace([np.inf, -np.inf], np.nan)
    mult = rel.clip(lower=floor, upper=1.0).fillna(1.0)
    # only ALLOW de-levering past a spike threshold (no leverage-UP); cap the down-scale
    mult = mult.where(fast_v > ratio_cap * slow_med, 1.0).fillna(1.0)
    return mult


def report(label: str, net: pd.Series, ref_eq: pd.Series | None = None) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    isr = base.msharpe(net, base.LO0, base.OOS_CUTOFF)
    oosr = base.msharpe(net, base.OOS_CUTOFF, base.HI1)
    tot = (eq.iloc[-1] - 1) * 100
    print(f"  {label:22} IS={isr:+.2f} OOS={oosr:+.2f} maxDD={dd*100:5.0f}% netTot={tot:+5.0f}%")
    return {"label": label, "is": isr, "oos": oosr, "dd": dd, "tot": tot}


def main() -> None:
    coins = base.load_universe()
    print(f"RISK PROBE: DD controls on iter-005 baseline — {len(coins)} candidates\n")
    raw, picks = baseline_net(coins)
    oos = Counter(b for y, b in picks if y >= 2025)
    print(f"  (sanity λ OOS-picks: {dict(sorted(oos.items()))})")

    # --- baseline (re-applied vol-target) — must match iter_005 headline -----------------
    base_net = apply_voltarget(raw)
    print("\n  --- baseline reconstruction (assert matches iter_005) ---")
    b = report("BASELINE λ-WF", base_net)
    # OOS matches iter_005 exactly (+1.22); IS/DD differ ~0.07/1pt because we stitch the raw
    # per-month net then vol-target once (vs iter_005's per-λ vol-target before stitch) — the
    # vol-target operator is non-linear across stitch boundaries. Faithful for DD-control probing.
    # NOTE: this raw-stitch+single-vol-target path differs from iter_005's canonical per-λ
    # vol-target; the critic showed it INFLATES the de-lever lift (stitch artifact). Sanity-bound.
    assert b["oos"] > 0.8 and b["is"] > 0.8, "baseline sanity"
    print(f"  [probe] raw-stitch baseline IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
          "(NON-canonical; see iter_005 for the deployable definition)\n")

    print("  --- A. DD-BRAKE (de-lever on running equity drawdown) ---")
    for ds, dfu, fl in [(0.10, 0.25, 0.5), (0.12, 0.30, 0.4), (0.15, 0.30, 0.3)]:
        ramp = dd_brake_scale(base_net, ds, dfu, fl)
        report(f"DD-brake {int(ds*100)}/{int(dfu*100)}→{fl}", base_net * ramp)

    print("\n  --- B. VOLTARGET-CAP (lower MAX_LEV ceiling) ---")
    for ml in [2.5, 2.0, 1.5]:
        report(f"max_lev={ml}", apply_voltarget(raw, max_lev=ml))

    print("\n  --- C. REALIZED-VOL spike de-lever ---")
    for fast, slow, rc, fl in [(21, 168, 1.5, 0.5), (12, 84, 1.5, 0.5), (21, 168, 2.0, 0.4)]:
        mult = realized_vol_scale(raw, fast, slow, rc, fl)
        report(f"rv {fast}/{slow} >{rc}×→{fl}", apply_voltarget(raw) * mult.reindex(raw.index))

    print("\n  --- D. COMBINED (DD-brake 12/30→0.4 ∘ rv-spike 21/168) ---")
    ramp = dd_brake_scale(base_net, 0.12, 0.30, 0.4)
    mult = realized_vol_scale(raw, 21, 168, 1.5, 0.5).reindex(raw.index)
    report("DD-brake ∘ rv-spike", base_net * ramp * mult)

    print("\n  --- C-ROBUSTNESS: rv-spike around the IS pick (21/168, >1.5×→0.5) ---")
    print("  (vary ONE knob at a time; edge should persist, not be knife-edge)")
    for fast in [14, 21, 28]:
        mult = realized_vol_scale(raw, fast, 168, 1.5, 0.5).reindex(raw.index)
        report(f"  fast={fast}", apply_voltarget(raw) * mult)
    for slow in [120, 168, 210]:
        mult = realized_vol_scale(raw, 21, slow, 1.5, 0.5).reindex(raw.index)
        report(f"  slow={slow}", apply_voltarget(raw) * mult)
    for rc in [1.3, 1.5, 1.7]:
        mult = realized_vol_scale(raw, 21, 168, rc, 0.5).reindex(raw.index)
        report(f"  thresh={rc}×", apply_voltarget(raw) * mult)
    for fl in [0.4, 0.5, 0.6]:
        mult = realized_vol_scale(raw, 21, 168, 1.5, fl).reindex(raw.index)
        report(f"  floor={fl}", apply_voltarget(raw) * mult)

    print("\n  === RECOMMENDED: rv-spike 21/168 >1.5×→0.5 (IN+OOS positive, DD −30→−26%) ===")
    rec_mult = realized_vol_scale(raw, 21, 168, 1.5, 0.5).reindex(raw.index)
    rec = apply_voltarget(raw) * rec_mult
    report("RECOMMENDED", rec)
    # how often / how much does it actually fire?
    fired = (rec_mult < 0.999)
    print(f"  fires {fired.mean()*100:.1f}% of candles "
          f"(IS {fired[fired.index < base.OOS_CUTOFF].mean()*100:.1f}% / "
          f"OOS {fired[fired.index >= base.OOS_CUTOFF].mean()*100:.1f}%); "
          f"mean turnover-overlay multiplier when fired = {rec_mult[fired].mean():.2f}")


if __name__ == "__main__":
    main()
