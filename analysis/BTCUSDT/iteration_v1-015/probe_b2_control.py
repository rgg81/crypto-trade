"""PROBE B2 (iter-v1/015, BTCUSDT, IS-ONLY) — R2 brake vs FLAT-multiplier CONTROL.

THE METRIC-TRAP GUARD (the iter-012 lesson, applied to R2). Probe B showed the chosen R2 brake
(trigger=20, anchor=80, floor=0.2) lifts pooled Sharpe +1.87 -> +2.58 and cuts maxDD -61%. But it
fires at ~89% rate with avg scale ~0.435 — so it is mostly a GLOBAL size cut, not a surgical
de-lever of the loss episodes. A global constant size cut does NOT change pooled Sharpe (Sharpe is
scale-invariant) but it DOES change the *additive* maxDD (in cum-pct points) because DD is in
absolute units. So the pooled-Sharpe LIFT must come from the PATH-DEPENDENT part of R2 (de-levering
more during drawdowns than during run-ups) — OR it is an artifact of how I annualize pooled Sharpe.

THIS PROBE ISOLATES THE PATH-DEPENDENT CONTRIBUTION. I compare, on the IDENTICAL trade stream:
  (A) R2 brake (path-dependent, chosen config).
  (B) FLAT multiplier = R2's realized average scale (same average size, NO path-dependence).
  (C) baseline (size 1.0).
If (A) pooled Sharpe >> (B) pooled Sharpe, the lift is GENUINELY path-dependent (R2 cuts size during
drawdowns and restores it during recoveries — a real risk mechanism). If (A) ~= (B), the "lift" is
just the variance-reduction of a smaller book and R2 adds nothing a flat size cut wouldn't (and the
pooled-Sharpe number is then NOT a deployment edge — exactly the iter-012 trap).

I ALSO report the ADDITIVE-DD reduction for the flat control, since DD is scale-sensitive: a flat
0.435x cut mechanically cuts additive DD by ~56.5%. R2 must beat that to claim a DD edge.

OOS-VIGILANCE: IS-only; path-only brake state; no forward info.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-015/probe_b2_control.py
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
)
from probe_b_drawdown_brake import apply_drawdown_brake  # noqa: E402

PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-015"
ATR_SL = 1.45
TRG, ANC, FLR = 20, 80, 0.2  # chosen in probe B


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
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)

    print("\n" + "=" * 100)
    print(f"R2 (path-dependent) vs FLAT (same avg size) vs BASELINE — chosen R2 trg={TRG} anc={ANC} "
          f"flr={FLR}")
    print("  CLAIM TEST: R2 pooled-Sharpe must EXCEED the flat control to be a genuine path mechanism")
    print("=" * 100)
    rows = []
    for seed in SEEDS:
        d, oof, _ = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, seed)
        mb, _r = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
        fm = oof & np.isfinite(mb)
        fi = np.where(fm)[0]
        fi = fi[np.argsort(ot_days[fi])]
        rets = mb[fi]

        # baseline
        s_base = pooled_ann_sharpe(rets, n_is)
        dd_base = proxy_maxdd(rets)
        # R2 path-dependent
        rw, scales = apply_drawdown_brake(rets, TRG, ANC, FLR)
        s_r2 = pooled_ann_sharpe(rw, n_is)
        dd_r2 = proxy_maxdd(rw)
        avg_scale = float(scales.mean())
        # FLAT control = same average size, no path-dependence
        rflat = rets * avg_scale
        s_flat = pooled_ann_sharpe(rflat, n_is)
        dd_flat = proxy_maxdd(rflat)
        rows.append(dict(
            seed=seed,
            base_sharpe=round(s_base, 3), R2_sharpe=round(s_r2, 3), flat_sharpe=round(s_flat, 3),
            R2_minus_flat_sharpe=round(s_r2 - s_flat, 3),
            base_DD=round(dd_base, 1), R2_DD=round(dd_r2, 1), flat_DD=round(dd_flat, 1),
            R2_DD_vs_flat_pct=round(100 * (dd_r2 - dd_flat) / dd_flat, 1),
            avg_scale=round(avg_scale, 3),
        ))
    res = pd.DataFrame(rows)
    res.to_csv(OUTDIR / "drawdown_brake_vs_flat.csv", index=False)
    print(res.to_string(index=False))
    print("\n  KEY READS:")
    print(f"   R2 pooled-Sharpe minus FLAT pooled-Sharpe: mean {res.R2_minus_flat_sharpe.mean():+.3f} "
          f"(>0 => path-dependence adds genuine edge; ~0 => R2 == a flat size cut)")
    print(f"   R2 maxDD vs FLAT maxDD: mean {res.R2_DD_vs_flat_pct.mean():+.1f}% "
          f"(<0 => R2 cuts DD MORE than a same-size flat cut => genuine DD mechanism)")
    print(f"   FLAT pooled-Sharpe minus BASELINE: mean "
          f"{(res.flat_sharpe - res.base_sharpe).mean():+.3f} "
          f"(should be ~0 — Sharpe is scale-invariant; confirms the harness)")


if __name__ == "__main__":
    main()
