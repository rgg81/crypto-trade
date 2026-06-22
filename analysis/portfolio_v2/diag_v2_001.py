"""portfolio-iteration-v2 iter-v2-001 DIAGNOSTICS — characterize the anchor's IS +1.53 / OOS +0.01.

Per the critic's PASS-WITH-CONCERNS review. Answers: is IS +1.53 a discovered edge or a 2021-2023
thin-denominator cohort artifact? And how fragile is OOS +0.01 to a pessimistic thin-tail slip?

Prints, for the v2-anchor (rank 21-40, PIT, slip) and v1-honest (top-20, PIT, slip):
  - per-CALENDAR-YEAR Sharpe (not net%) — IS strength localization
  - the rank-band denominator per year (names IN the band) + avgPos per year — thinness check
  - OOS split into sub-windows (2025-03-24..2025-12-31 vs 2026) — don't over-read one sign
  - walk-forward λ-picks per year — regime-specific λ check
  - anchor under a thin-tail-PESSIMISTIC slip model (cap=25bp, B=40) — cost fragility
  - PIT-pool delisting + internal-gap census — residual-survivorship measurement

Run from worktree root:  uv run python analysis/portfolio_v2/diag_v2_001.py
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402


def slip_pessimistic(dvol_m):
    """Thin-tail-pessimistic per-side slip (bps): clip(2 + 40/dvol_M, 2, 25).
    ~2.2bp @ $200M, ~3bp @ $40M, ~10bp @ $5M, capped 25bp (vs default cap 10)."""
    if isinstance(dvol_m, pd.DataFrame | pd.Series):
        d = dvol_m.clip(lower=1e-6)
        return (2.0 + 40.0 / d).clip(lower=2.0, upper=25.0)
    arr = np.asarray(dvol_m, dtype=float)
    arr = np.where(arr < 1e-6, 1e-6, arr)
    return np.clip(2.0 + 40.0 / arr, 2.0, 25.0)


def per_year_sharpe(net: pd.Series) -> dict:
    out = {}
    for y, s in net.groupby(net.index.year):
        lo = pd.Timestamp(f"{int(y)}-01-01")
        hi = pd.Timestamp(f"{int(y) + 1}-01-01")
        out[int(y)] = round(float(e2.msharpe(net, lo, hi)), 2)
    return out


def per_year_mean(df_count: pd.Series) -> dict:
    return {
        int(y): round(float(v), 1) for y, v in df_count.groupby(df_count.index.year).mean().items()
    }


def characterize(label: str, res: dict) -> None:
    net = res["net"]
    band = res["elig"].sum(axis=1)  # names IN the band per candle
    pos = (res["held_w"].abs() > 1e-9).sum(axis=1)  # non-zero held positions per candle
    print(f"\n=== {label} ===")
    is_s = e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF)
    oos_s = e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1)
    print(f"  IS={is_s:+.2f}  OOS={oos_s:+.2f}")
    print(f"  per-year Sharpe : {per_year_sharpe(net)}")
    print(f"  band names/yr   : {per_year_mean(band)}")
    print(f"  avgPos/yr       : {per_year_mean(pos)}")
    # OOS sub-windows
    w1 = e2.msharpe(net, e2.OOS_CUTOFF, pd.Timestamp("2026-01-01"))
    w2 = e2.msharpe(net, pd.Timestamp("2026-01-01"), e2.HI1)
    n1 = int(((net.index >= e2.OOS_CUTOFF) & (net.index < pd.Timestamp("2026-01-01"))).sum())
    n2 = int((net.index >= pd.Timestamp("2026-01-01")).sum())
    print(
        f"  OOS sub-windows : 2025-03..12 Sharpe={w1:+.2f} (n={n1})  2026 Sharpe={w2:+.2f} (n={n2})"
    )
    picks = Counter(lam for _, lam in res["picks"])
    by_year = {}
    for yr, lam in res["picks"]:
        by_year.setdefault(yr, Counter())[lam] += 1
    print(f"  λ-pick totals   : {dict(sorted(picks.items()))}")
    print(f"  λ-picks by year : { {y: dict(c) for y, c in sorted(by_year.items())} }")


def pool_census(coins: dict) -> None:
    """Delisting + internal-gap census of the PIT pool (residual-survivorship measurement)."""
    step = e2.STEP_MS
    # global last open_time across the pool = data extent
    global_last = max(int(d.index.max()) for d in coins.values())
    delisted = []
    gappy = 0
    total_internal_gaps = 0
    for s, d in coins.items():
        idx = d.index.to_numpy()
        if int(idx.max()) < global_last - step:  # last candle before data extent => delisted/dead
            delisted.append(s)
        # internal gaps: consecutive open_time diffs > step within the coin's own active range
        diffs = np.diff(idx)
        ngap = int((diffs > step).sum())
        if ngap:
            gappy += 1
            total_internal_gaps += ngap
    print("\n=== PIT-pool census (residual survivorship) ===")
    print(f"  pool size                : {len(coins)} coins")
    print(
        f"  delisted (last < extent) : {len(delisted)} coins  "
        f"(e.g. {', '.join(sorted(delisted)[:12])}{'...' if len(delisted) > 12 else ''})"
    )
    known = [
        c
        for c in (
            "TOMOUSDT",
            "BLZUSDT",
            "ANCUSDT",
            "CVCUSDT",
            "FTMUSDT",
            "MATICUSDT",
            "LINAUSDT",
            "WAVESUSDT",
            "SRMUSDT",
            "RAYUSDT",
        )
        if c in coins
    ]
    known_delisted = [c for c in known if c in set(delisted)]
    print(f"  known dead names present : {known} (of which delisted-tagged: {known_delisted})")
    print(
        f"  coins with internal gaps : {gappy} coins, {total_internal_gaps} total gap-candles "
        f"(affects the ==season seasoning rule)"
    )


def main() -> None:
    print("=" * 100)
    print("iter-v2-001 DIAGNOSTICS — is IS +1.53 an edge or a thin-cohort artifact?")
    print("=" * 100)
    pool_pit = uv.load_pool_pit()
    pool_census(pool_pit)

    r_anc = e2.run_book(
        pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps
    )
    r_hon = e2.run_book(
        pool_pit, rank_lo=0, rank_hi=20, season=168, slip_bps_fn=e2.default_slip_bps
    )
    characterize("v2 ANCHOR (21-40, PIT, default slip)", r_anc)
    characterize("v1 HONEST (top20, PIT, default slip)", r_hon)

    print("\n=== v2-anchor under THIN-TAIL-PESSIMISTIC slip (cap=25bp, B=40) ===")
    r_pess = e2.run_book(pool_pit, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=slip_pessimistic)
    print(
        f"  IS={e2.msharpe(r_pess['net'], e2.LO0, e2.OOS_CUTOFF):+.2f}  "
        f"OOS={e2.msharpe(r_pess['net'], e2.OOS_CUTOFF, e2.HI1):+.2f}  "
        f"(default was IS+1.53/OOS+0.01)"
    )
    print(f"  per-year Sharpe : {per_year_sharpe(r_pess['net'])}")


if __name__ == "__main__":
    main()
