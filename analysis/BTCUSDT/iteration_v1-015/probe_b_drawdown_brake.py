"""PROBE B (iter-v1/015, BTCUSDT, IS-ONLY) — R2 drawdown brake (path-dependent, regime-AGNOSTIC).

HYPOTHESIS (user candidate #2): a per-strategy cumulative-equity drawdown brake — de-lever new
trades after the book's OWN equity falls below its running peak — is REGIME-BLIND. It reacts to
REALIZED losses, not to a regime LABEL. This is the structural reason it CANNOT make the iter-012
mistake: iter-012's 200-SMA de-lever cut size in down-trends, but the OOS losses were WITHIN the
up-trend, so it protected nothing. The drawdown brake instead cuts size precisely when the book is
ALREADY bleeding — wherever that bleed comes from (up-trend, down-trend, chop). The question this
probe answers IS-only: does an equity-drawdown brake (a) reduce pooled-book drawdown, and (b) do so
by cutting size during the SAME losing episodes that recur OOS (the negative sub-periods), without
gutting the recovery?

This is the EXISTING R2 primitive (`risk_drawdown_scale_enabled` / `risk_drawdown_trigger_pct` /
`risk_drawdown_scale_floor` / `risk_drawdown_scale_anchor_pct`), currently OFF. I simulate it
faithfully: walk the chronological trade stream, maintain cumulative weighted PnL + running peak,
and scale each NEW trade's weight by a linear factor from 1.0 (at the trigger DD) down to floor
(at the anchor DD). The scaling is applied to the NEXT trade's size — strictly causal/path-only.

R2 is in PERCENTAGE-OF-PEAK-EQUITY terms in the live engine, but the book is additive (weighted_pnl
in cum-pct points, no compounding base). I therefore simulate R2 on the ADDITIVE cum-pnl drawdown in
cum-pct points (matching backtest weighted_pnl accounting), with the trigger/anchor expressed in the
SAME cum-pct-point units. This is the honest IS simulation of the additive backtest book; I also
report the % interpretation for the live-parity note.

WHAT THIS PROBE MEASURES (IS-only):
  (1) A trigger x anchor x floor grid: pooled Sharpe + maxDD + trade-rate-retained + fire-rate.
  (2) The chosen-config equity curve OFF vs ON (maxDD, longest-DD, recovery).
  (3) WHERE the brake fires by sub-period — does it concentrate de-levering in the negative
      (recurring-OOS) sub-periods? (the generalization-alignment check)
  (4) Seed robustness of the chosen config (pooled Sharpe lift + DD reduction across 5 seeds).

OOS-VIGILANCE: IS-only frame; the brake state is path-dependent on PAST trades only (the scaling
applied to trade k uses cum-PnL through trade k-1). No forward info.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-015/probe_b_drawdown_brake.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _harness import (  # noqa: E402
    ATR_COLUMN,
    BASE_PARAMS,
    ITER009_FEATURES,
    N_LABEL,
    OOS_CUTOFF_MS,
    SEEDS,
    SYMBOL,
    expanding_wf_with_margin,
    fwd_return,
    letrun,
    load_is_frame,
    pooled_ann_sharpe,
    proxy_maxdd,
    sub_period_label,
)

PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-015"
ATR_SL = 1.45


def apply_drawdown_brake(rets_ordered, trigger, anchor, floor):
    """Path-only R2 drawdown brake on an ordered (chronological) per-trade net-return stream.

    For each trade k (in order):
      dd_k     = running_peak(cum through k-1) - cum(through k-1)   [cum-pct points, >=0]
      scale_k  = 1.0                              if dd_k <= trigger
                 floor                            if dd_k >= anchor
                 linear(1.0 -> floor) in between  otherwise
      weighted_ret_k = rets[k] * scale_k
    Returns (weighted_returns, scales).  Strictly causal: scale_k uses only trades < k."""
    n = len(rets_ordered)
    out = np.empty(n)
    scales = np.empty(n)
    cum = 0.0
    peak = 0.0
    span = max(anchor - trigger, 1e-9)
    for k in range(n):
        dd = peak - cum  # drawdown BEFORE trade k (path-only)
        if dd <= trigger:
            s = 1.0
        elif dd >= anchor:
            s = floor
        else:
            s = 1.0 - (1.0 - floor) * (dd - trigger) / span
        scales[k] = s
        out[k] = rets_ordered[k] * s
        cum += out[k]  # equity moves by the ACTUALLY-SIZED return (live-faithful: brake compounds)
        peak = max(peak, cum)
    return out, scales


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_is_frame(PARQUET)
    n_is = len(df)
    print(f"IS rows: {n_is}  (max open_time {int(df['open_time'].max())} < cutoff {OOS_CUTOFF_MS})")

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    atr = close * df[ATR_COLUMN].to_numpy(float) / 100.0
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats) == 19
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)
    subp = sub_period_label(ot_days)

    d, oof, _pv = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb, _r = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
    full = oof & np.isfinite(mb)
    fi = np.where(full)[0]
    fi = fi[np.argsort(ot_days[fi])]
    rets = mb[fi]
    sp = subp[fi]

    base_s = pooled_ann_sharpe(rets, n_is)
    base_dd = proxy_maxdd(rets)
    n_trades = len(rets)
    months = (ot_days[fi].max() - ot_days[fi].min()) / 30.44
    print(f"\nbaseline (R2 OFF): pooled Sharpe {base_s:+.3f}  maxDD {base_dd:.1f}  "
          f"n_trades {n_trades}  ({n_trades/months:.1f}/mo)")
    print(f"  cum-pnl range of book: total {rets.sum():+.1f} cum-pct points over {months:.0f} months")

    # ===================== (1) TRIGGER x ANCHOR x FLOOR GRID =====================
    print("\n" + "=" * 100)
    print("(1) R2 GRID (IS-only) — additive cum-pct-point drawdown brake; pooled Sharpe + maxDD")
    print("=" * 100)
    rows = []
    # trigger/anchor in cum-pct points; book maxDD baseline ~306, so triggers 30-120, anchors 80-250.
    for trigger in (20, 40, 60, 80):
        for anchor in (80, 120, 160, 200):
            if anchor <= trigger:
                continue
            for floor in (0.5, 0.33, 0.2):
                rw, scales = apply_drawdown_brake(rets, trigger, anchor, floor)
                rows.append(dict(
                    trigger=trigger, anchor=anchor, floor=floor,
                    pooled_sharpe=round(pooled_ann_sharpe(rw, n_is), 3),
                    maxDD=round(proxy_maxdd(rw), 1),
                    dd_red_pct=round(100 * (proxy_maxdd(rw) - base_dd) / base_dd, 1),
                    fire_rate=round(float((scales < 1.0).mean()), 3),
                    avg_scale=round(float(scales.mean()), 3),
                    total_ret=round(float(rw.sum()), 1),
                ))
    grid = pd.DataFrame(rows)
    grid.to_csv(OUTDIR / "drawdown_brake_grid.csv", index=False)
    # show the best-Sharpe and the best-DD-with-Sharpe>=base configs
    print("  top 8 by pooled Sharpe:")
    print(grid.sort_values("pooled_sharpe", ascending=False).head(8).to_string(index=False))
    print("\n  top 8 by DD reduction among Sharpe >= baseline:")
    ok = grid[grid.pooled_sharpe >= round(base_s, 3)]
    print(ok.sort_values("maxDD").head(8).to_string(index=False))

    # ===================== (2) CHOSEN CONFIG — where does the brake fire? =====================
    # Choose: max DD reduction subject to pooled Sharpe >= baseline (a pure risk-control, no Sharpe cost).
    chosen = ok.sort_values("maxDD").iloc[0]
    TRG, ANC, FLR = int(chosen.trigger), int(chosen.anchor), float(chosen.floor)
    print("\n" + "=" * 100)
    print(f"(2) CHOSEN R2 CONFIG: trigger={TRG} anchor={ANC} floor={FLR} "
          f"(max DD-cut s.t. Sharpe >= baseline)")
    print("=" * 100)
    rw, scales = apply_drawdown_brake(rets, TRG, ANC, FLR)
    print(f"  pooled Sharpe {base_s:+.3f} -> {pooled_ann_sharpe(rw, n_is):+.3f}")
    print(f"  maxDD         {base_dd:.1f} -> {proxy_maxdd(rw):.1f}  "
          f"({100*(proxy_maxdd(rw)-base_dd)/base_dd:+.1f}%)")
    print(f"  total return  {rets.sum():+.1f} -> {rw.sum():+.1f} cum-pct points")
    print(f"  fire rate {float((scales<1.0).mean()):.3f}  avg scale {float(scales.mean()):.3f}")

    # fire concentration by sub-period
    rows2 = []
    for s in sorted(pd.unique(sp)):
        m = sp == s
        rows2.append(dict(
            sub_period=s, n=int(m.sum()),
            full_net=round(float(rets[m].sum()), 2),
            avg_brake_scale=round(float(scales[m].mean()), 3),
            brake_fire_rate=round(float((scales[m] < 1.0).mean()), 3),
        ))
    sp_df = pd.DataFrame(rows2)
    sp_df.to_csv(OUTDIR / "drawdown_brake_subperiod.csv", index=False)
    print("\n  WHERE the brake fires (lower avg_brake_scale = more de-levering in that sub-period):")
    print(sp_df.to_string(index=False))
    neg = sp_df[sp_df.full_net < 0]
    pos = sp_df[sp_df.full_net > 0]
    print(f"\n  avg brake scale in NEGATIVE sub-periods: {neg.avg_brake_scale.mean():.3f}")
    print(f"  avg brake scale in POSITIVE sub-periods: {pos.avg_brake_scale.mean():.3f}")
    print("  (lower-in-negative => brake is regime-agnostically targeting the recurring-loss episodes)")

    # ===================== (3) SEED ROBUSTNESS =====================
    print("\n" + "=" * 100)
    print(f"(3) SEED ROBUSTNESS — chosen R2 (trg={TRG} anc={ANC} flr={FLR}) across 5 seeds")
    print("=" * 100)
    rows3 = []
    for seed in SEEDS:
        ds, oofs, _ = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, seed)
        mbs, _ = letrun(high, low, close, atr, ds, ATR_SL, N_LABEL)
        fm = oofs & np.isfinite(mbs)
        fis = np.where(fm)[0]
        fis = fis[np.argsort(ot_days[fis])]
        rs = mbs[fis]
        s_off = pooled_ann_sharpe(rs, n_is)
        dd_off = proxy_maxdd(rs)
        rws, _ = apply_drawdown_brake(rs, TRG, ANC, FLR)
        s_on = pooled_ann_sharpe(rws, n_is)
        dd_on = proxy_maxdd(rws)
        rows3.append(dict(
            seed=seed,
            sharpe_OFF=round(s_off, 3), sharpe_ON=round(s_on, 3),
            sharpe_delta=round(s_on - s_off, 3),
            maxDD_OFF=round(dd_off, 1), maxDD_ON=round(dd_on, 1),
            dd_red_pct=round(100 * (dd_on - dd_off) / dd_off, 1),
        ))
    sr = pd.DataFrame(rows3)
    sr.to_csv(OUTDIR / "drawdown_brake_seed_robust.csv", index=False)
    print(sr.to_string(index=False))
    print(f"\n  Sharpe Δ: mean {sr.sharpe_delta.mean():+.3f}  min {sr.sharpe_delta.min():+.3f}  "
          f"(all >= 0: {bool((sr.sharpe_delta >= 0).all())})")
    print(f"  maxDD reduction: mean {sr.dd_red_pct.mean():+.1f}%  "
          f"(all reduce: {bool((sr.dd_red_pct < 0).all())})")
    print(f"\nWrote drawdown_brake_*.csv to {OUTDIR}")


if __name__ == "__main__":
    main()
