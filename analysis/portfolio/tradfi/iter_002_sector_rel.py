"""iter-002 — SECTOR-RELATIVE cross-sectional momentum (12-1m), daily, vol-targeted.

ONE change vs iter-001: demean the momentum SIGNAL *within each sector bucket* instead of
across the whole universe. iter-001 ran `dollar_neutralize(mom/rvol)` — a single cross-sectional
demean — which on this ~62%-Semi+Tech universe is dominated by sector-vs-sector drift (noise for
momentum, IS_Sharpe -0.18, NEGATIVE-CONFIRMED). Here we apply `sector_neutralize(mom/rvol,
SECTOR_MAP)`: each sector nets to zero dollar by construction, so the book is long-best-in-sector
/ short-worst-in-sector and dollar-neutral *automatically* (no extra dollar_neutralize). This
isolates idiosyncratic within-sector momentum from the sector drift.

Single-name sectors (e.g. Health = LLY alone) get demeaned against themselves → forced to 0
weight. That is the correct, safe default: a name with no within-sector peer takes no position.

OOS stays hidden (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). Everything
flows through the leak-safe core (net_from_raw `.shift(1)`-lags weights). Do NOT tune here — this
is the pre-registered one-change sector-relative variant; report whatever IS number it gives.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402


def sector_rel_raw(pn):
    """Leak-safe sector-RELATIVE 12m-1m momentum, inverse-vol scaled, sector-neutralized.

    raw = sector_neutralize( (close.shift(21)/close.shift(252) - 1) / rolling_63_rvol, SECTOR_MAP )
    No dollar_neutralize: per-sector demeaning already makes every sector — and therefore the
    whole row — net zero dollar (confirm via the row-sum check in main / the unit test).
    """
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0  # 12m-1m, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    raw = mom / rvol
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def build(coins):
    """coins -> (vol-targeted net series, lagged weight book) via the leak-safe core."""
    pn = ct.panels(coins)
    raw = sector_rel_raw(pn)
    return ct.net_from_raw(raw, pn["ret_fwd"])


def _net_nocost(raw, ret_fwd):
    """Gross (cost-off) vol-targeted net — net_from_raw minus the turnover-cost term."""
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    return ct.vol_target(pnl.dropna())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    # Universe from on-disk ingested names (point-in-time: only what we have data for).
    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_dukascopy_stocks.py first.")
        return

    pn = ct.panels(coins)
    raw = sector_rel_raw(pn)
    net, w = ct.net_from_raw(raw, pn["ret_fwd"])

    print(ct.perf_line("iter-002 sector-rel", net, reveal_oos=args.confirm))
    print(f"  regimes (IS): {ct.regime_sharpe(ct.is_only(net))}")
    print(f"  turnover/day: {ct.turnover(w, ct.LO0, ct.OOS_CUTOFF):.3f}")

    # --- book sanity (IS-only): N active, gross, dollar-neutral-by-construction confirmation ---
    raw_is = raw[raw.index < ct.OOS_CUTOFF]
    gross_is = raw_is.abs().sum(axis=1).replace(0, np.nan)
    rowsum_max = float(raw_is.sum(axis=1).abs().div(gross_is).max())  # |Σw| / Σ|w| per row
    w_is = w[w.index < ct.OOS_CUTOFF]
    gross_w = w_is.abs().sum(axis=1)
    live = gross_w > 1e-9
    n_active = float((w_is[live] != 0).sum(axis=1).mean())
    gross_mean = float(gross_w[live].mean())
    print(f"  N active (IS, mean names/bar): {n_active:.1f} of {len(coins)} ingested")
    print(f"  gross Σ|w| (IS, active rows): {gross_mean:.3f}  (dollar-neutral by construction)")
    print(f"  max |row-sum| / gross (IS): {rowsum_max:.1e}  (~0 confirms each sector nets zero)")

    # --- iter-001-style characterization (diagnostic, NOT tuning) ---
    gross_net = _net_nocost(raw, pn["ret_fwd"])
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gross_net, ct.LO0, ct.OOS_CUTOFF)
    neg_net, _ = ct.net_from_raw(-raw, pn["ret_fwd"])
    sh_neg = ct.msharpe(neg_net, ct.LO0, ct.OOS_CUTOFF)
    print(
        f"  diag: gross(cost-off) IS_Sharpe={sh_gross:+.2f}  net={sh_net:+.2f}  "
        f"(cost drag {sh_gross - sh_net:+.2f})"
    )
    print(f"  diag: NEGATED signal IS_Sharpe={sh_neg:+.2f}")


if __name__ == "__main__":
    main()
