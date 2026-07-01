"""Generate a quantstats HTML tearsheet for the CONFIRMED portfolio-tradfi baseline (iter-015).

Mirrors analysis/portfolio/gen_quantstats.py (crypto) and the metals precedent: extract the deployed
net daily return series, hand it to quantstats reports.html with a benchmark, write the HTML.

The reported book = iter-015 DEPLOYED config (the ONE config of record):
    book   = (1-0.25)*[sector-relative multi-horizon MOM + 0.5*(3y-1y LTR)] + 0.25*TSMOM
    band   = hysteresis delta = 0.010  (iter-015 CHOSEN_DELTA)
    freq   = 1 (daily rebalance)       (iter-015 CHOSEN_FREQ)
    VIX    = iter-008 brake ON (base=20 / floor=0.50)
    cost   = 6 bps/side (1x), vol-targeted to 15% annual, 69 Yahoo names, 2010->2026.

This is a REPORTING deliverable: the OOS was already revealed at iter-015 CONFIRMATION, so the FULL
period (IS + revealed OOS, 2010->2026) is the correct, intended window here — NOT an OOS-hiding
violation. The net series is the SAME past-only, leak-safe deployed net used by iter_015_cost.py /
iter_015_oos_check.py (reused verbatim via iter_015_cost._deployed_net1x on the frozen (0.010, 1)
cell) — merely NOT sliced at OOS_CUTOFF. Nothing about the strategy changes.

Benchmark = the equal-weight-69 universe daily return (iter_013.market_return) — the honest,
PIT market-neutral reference (the book is ~market-neutral with a small controlled TSMOM tilt, so
performance relative to the EW-69 tape is the informative comparison).

Run: uv run python analysis/portfolio/tradfi/gen_quantstats_tradfi.py
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import quantstats as qs  # noqa: E402
import universe_tradfi as ut  # noqa: E402

warnings.filterwarnings("ignore")

OUT_DIR = ct._ROOT / "reports-tradfi"
OUT_HTML = OUT_DIR / "quantstats_iter015_allperiods.html"
TITLE = "portfolio-tradfi iter-015 (2010-2026, all periods)"
PERIODS_PER_YEAR = 252  # daily US-equity trading days


def build_series(data_dir: str | None = None) -> tuple[pd.Series, pd.Series]:
    """Return (deployed iter-015 daily net returns, EW-69 benchmark) over the FULL 2010-2026 period.

    The net series is iter_015_cost._deployed_net1x on the FROZEN, pre-registered deployed cell
    (delta=iter_015.CHOSEN_DELTA=0.010, freq=iter_015.CHOSEN_FREQ=1, lam=0.25, VIX-ON, 1x cost) —
    the identical past-only object iter_015_oos_check confirms, just not date-sliced.
    """
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, data_dir)
    if not coins:
        raise SystemExit("No ingested tradfi data found. Run ingest_yahoo.py first.")
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)  # EW-69 universe forward return = honest market-neutral benchmark
    vix = i8.load_vix_close(ret_fwd.index, data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    # DEPLOYED iter-015 daily net (lam=0.25, VIX-ON, 1x cost) on the FROZEN (0.010, 1) cell.
    returns = i15._deployed_net1x(pn, ret_fwd, s_vix, i15.CHOSEN_DELTA, i15.CHOSEN_FREQ).dropna()
    returns.name = "iter-015"

    bench = mkt.reindex(returns.index).dropna()
    bench.name = "EW-69 universe"
    returns = returns.reindex(bench.index)  # align to the shared benchmark-defined trading calendar
    return returns, bench


def _year_returns(returns: pd.Series) -> pd.Series:
    """Compounded calendar-year return series (for best/worst-year reporting)."""
    return returns.groupby(returns.index.year).apply(lambda x: float((1 + x).prod() - 1))


def print_headline(returns: pd.Series, syms_n: int) -> None:
    """Print the headline full-period quantstats metrics to stdout."""
    sharpe = float(qs.stats.sharpe(returns, periods=PERIODS_PER_YEAR))
    sortino = float(qs.stats.sortino(returns, periods=PERIODS_PER_YEAR))
    cagr = float(qs.stats.cagr(returns, periods=PERIODS_PER_YEAR))
    mdd = float(qs.stats.max_drawdown(returns))
    vol = float(qs.stats.volatility(returns, periods=PERIODS_PER_YEAR))
    calmar = float(qs.stats.calmar(returns))
    yr = _year_returns(returns)
    best_yr, worst_yr = yr.idxmax(), yr.idxmin()
    # analysis-native cross-reference (monthly-summed Sharpe, sqrt-12) over the FULL period
    ms_full = ct.msharpe(returns, ct.LO0, ct.HI1)

    print("=" * 88)
    print("HEADLINE — portfolio-tradfi iter-015 DEPLOYED (2010-2026, ALL PERIODS)")
    print("=" * 88)
    print(
        f"  window        : {returns.index.min().date()} .. {returns.index.max().date()}  "
        f"({len(returns)} trading days, {syms_n} names)"
    )
    print(f"  Sharpe (252d) : {sharpe:+.3f}")
    print(f"  Sortino (252d): {sortino:+.3f}")
    print(f"  CAGR          : {cagr * 100:+.2f}%")
    print(f"  Volatility    : {vol * 100:6.2f}% ann.")
    print(f"  Max drawdown  : {mdd * 100:+.2f}%")
    print(f"  Calmar        : {calmar:+.3f}")
    print(f"  Best year     : {int(best_yr)}  {yr.loc[best_yr] * 100:+.2f}%")
    print(f"  Worst year    : {int(worst_yr)}  {yr.loc[worst_yr] * 100:+.2f}%")
    print(f"  (x-ref) monthly-Sharpe(sqrt-12), analysis convention: {ms_full:+.3f}")
    print("  Per-calendar-year compounded net return:")
    for y in yr.index:
        print(f"      {int(y)}: {yr.loc[y] * 100:+7.2f}%")
    print("=" * 88)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    # Frozen-cell guard: report the pre-registered deployed cell, never a drifted one.
    assert (i15.CHOSEN_DELTA, i15.CHOSEN_FREQ) == (0.010, 1), (
        f"iter-015 deployed cell drifted to {(i15.CHOSEN_DELTA, i15.CHOSEN_FREQ)} — refusing"
    )

    returns, bench = build_series(args.data_dir)
    if returns.dropna().empty:
        raise SystemExit("empty deployed return series — check data ingestion")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qs.reports.html(
        returns,
        benchmark=bench,
        output=str(OUT_HTML),
        title=TITLE,
        periods_per_year=PERIODS_PER_YEAR,
    )
    print(f"\nwrote tearsheet -> {OUT_HTML}")

    # headline metrics to stdout (n names = ingested universe members feeding the book)
    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms_n = len([p for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP])
    print_headline(returns.dropna(), syms_n)


if __name__ == "__main__":
    main()
