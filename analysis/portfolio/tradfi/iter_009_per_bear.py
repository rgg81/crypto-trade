"""iter-009 — PER-BEAR VALIDATION of the iter-006 momentum book + the iter-008 VIX brake.

This is a DATA-EXPANSION + VALIDATION harness, NOT a new strategy: it re-runs the UNCHANGED
iter-006 stack and the UNCHANGED iter-008 VIX-alone overlay on the extended 2010-2025 IS window
and decomposes the result across the FIVE documented US-equity bears now in sample:

    2011    (debt-ceiling / EU)   2011-07-22 -> 2011-10-03
    2015-16 (China / oil)         2015-08-17 -> 2016-02-11
    2018-Q4 (Fed / QT)            2018-10-01 -> 2018-12-24
    COVID   (V-crash)             2020-02-19 -> 2020-04-01   (one of the original 2)
    2022    (momentum grind)      2022-01-03 -> 2022-10-13   (one of the original 2)

The question: does the momentum edge HOLD across 2010-2025, and does the VIX bear-control
GENERALIZE across 5 bears, or was the 2-bear (COVID + 2022) result a coincidence?

Bear windows are the SAME macro-anchored dates pre-registered in core_tradfi._REGIMES (peak->trough
+ named catalyst), NOT tuned to P&L. Per bear we report the iter-006 book's return + Sharpe, the
VIX-alone book's return + Sharpe, whether the VIX brake FIRED (exposure scalar < 1 in the window),
and whether it HELPED (Δ return, Δ in-window maxDD). OOS stays HIDDEN — every metric is IS-only
(`< OOS_CUTOFF 2025-03-24`); no OOS number is computed or printed.

Run: uv run python analysis/portfolio/tradfi/iter_009_per_bear.py
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
import iter_006_crashbrake as i6  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# The 5 IS bears (macro-anchored peak->trough windows == core_tradfi._REGIMES bear tags).
BEARS = [
    ("2011 debt-ceil ", "2011-07-22", "2011-10-03"),
    ("2015-16 China  ", "2015-08-17", "2016-02-11"),
    ("2018-Q4 Fed     ", "2018-10-01", "2018-12-24"),
    ("COVID  V-crash  ", "2020-02-19", "2020-04-01"),
    ("2022   grind    ", "2022-01-03", "2022-10-13"),
]


def _win(net: pd.Series, lo: str, hi: str) -> pd.Series:
    return net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]


def _sharpe(s: pd.Series) -> float:
    g = s.groupby(s.index.to_period("M")).sum()
    return float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")


def _ret(s: pd.Series) -> float:
    return float((np.prod(1.0 + s) - 1.0) * 100)


def _mdd(s: pd.Series) -> float:
    eq = (1.0 + s).cumprod()
    return float((eq / eq.cummax() - 1.0).min() * 100)


def main() -> None:
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

    # iter-006 working best (UNCHANGED) + VIX-alone overlay (UNCHANGED, pinned base=20/floor=0.50).
    net6 = ct.is_only(i3.banded_net(i6.crash_braked_raw(pn), pn["ret_fwd"], i6.CHOSEN_DELTA)[0])
    vix = i8.load_vix_close(net6.index, args.data_dir)
    s_vix = i8.vix_scale(vix).reindex(net6.index).fillna(1.0)
    net_vix = net6 * s_vix

    n_names = sum(
        1
        for s in syms
        if coins[s].index.min() <= int(pd.Timestamp("2010-12-31").value // 1_000_000)
    )
    print("=" * 100)
    print(
        "iter-009 — PER-BEAR VALIDATION (iter-006 book + iter-008 VIX-alone, 2010-2025 IS, OOS HIDDEN)"  # noqa: E501
    )
    print("=" * 100)
    print(
        f"  universe: {len(syms)} on-disk names ({n_names} with 2010 history); "
        f"IS bars (union grid) = {len(net6)};  "
        f"IS span {net6.index.min().date()}..{net6.index.max().date()}"
    )

    # --- full-IS headline (single reproducible source for the diary) ---
    r6, rv = ct.regime_sharpe(net6), ct.regime_sharpe(net_vix)
    print("\n  --- FULL-IS (2010-01-04 .. 2025-03-24) ---")
    print(
        f"  iter-006        net={ct.msharpe(net6, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
        f"bull={r6['bull']:+.2f} bear={r6['bear']:+.2f} chop={r6['chop']:+.2f}  "
        f"maxDD={_mdd(net6):5.1f}%"
    )
    print(
        f"  VIX brake ALONE net={ct.msharpe(net_vix, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
        f"bull={rv['bull']:+.2f} bear={rv['bear']:+.2f} chop={rv['chop']:+.2f}  "
        f"maxDD={_mdd(net_vix):5.1f}%"
    )

    # --- PER-BEAR TABLE (the key deliverable) ---
    print("\n  --- PER-BEAR (iter-006 base  ->  VIX-alone), + did VIX fire / help ---")
    print(
        "    bear              | iter006 Sh/ret%  | VIX Sh/ret%      | VIX fire (mean/min/frac<1) "
        "| help: Δret / mdd6->mddVIX"
    )
    n_fired = n_helped = 0
    for lab, lo, hi in BEARS:
        b6, bv = _win(net6, lo, hi), _win(net_vix, lo, hi)
        sv = _win(s_vix, lo, hi)
        sh6, rt6, md6 = _sharpe(b6), _ret(b6), _mdd(b6)
        shv, rtv, mdv = _sharpe(bv), _ret(bv), _mdd(bv)
        fired = float((sv < 0.999).mean()) * 100
        helped = (rtv > rt6 + 1e-9) or (mdv > md6 + 1e-9)  # better return OR shallower drawdown
        n_fired += fired > 0
        n_helped += helped
        verdict = "HELP" if helped else "hurt" if rtv < rt6 - 1e-9 else "flat"
        print(
            f"    {lab} | {sh6:+5.2f} / {rt6:+6.1f}  | {shv:+5.2f} / {rtv:+6.1f}  "
            f"| {sv.mean():.2f} / {sv.min():.2f} / {fired:3.0f}%        "
            f"| {rtv - rt6:+5.1f}pp / {md6:+5.1f}->{mdv:+5.1f}%  {verdict}"
        )
    print(
        f"\n  GENERALIZATION: VIX brake FIRED in {n_fired}/5 bears, "
        f"HELPED (better ret or shallower DD) in {n_helped}/5."
    )
    print(
        "  note: COVID (~1.5 months, ~2 monthly points) Sharpe is unreliable — "
        "read its return / maxDD."
    )


if __name__ == "__main__":
    main()
