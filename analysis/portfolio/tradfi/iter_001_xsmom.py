"""iter-001 anchor — dollar-neutral cross-sectional momentum (12-1m), daily, vol-targeted.

The market-neutral starting point for the tradfi track. Rank the universe by trailing 12m-1m
return, inverse-vol scale, dollar-neutralize (longs$ == shorts$), gross-normalize → lag → cost
→ portfolio vol-target via the leak-safe core. OOS stays hidden (perf_line reveal_oos=False).
iter-002 will add beta-neutral, iter-003 sector-neutral.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np  # noqa: F401

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402


def xsmom_raw(pn):
    """Leak-safe cross-sectional 12m-1m momentum, inverse-vol scaled, dollar-neutralized."""
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0  # 12m-1m, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    raw = mom / rvol
    return nz.dollar_neutralize(raw)


def build(coins):
    """coins -> (vol-targeted net series, lagged weight book) via the leak-safe core."""
    pn = ct.panels(coins)
    raw = xsmom_raw(pn)
    return ct.net_from_raw(raw, pn["ret_fwd"])


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
    net, w = build(coins)
    print(ct.perf_line("iter-001 XS-mom", net, reveal_oos=args.confirm))
    print(f"  regimes (IS): {ct.regime_sharpe(ct.is_only(net))}")
    print(f"  turnover/day: {ct.turnover(w, ct.LO0, ct.OOS_CUTOFF):.3f}")


if __name__ == "__main__":
    main()
