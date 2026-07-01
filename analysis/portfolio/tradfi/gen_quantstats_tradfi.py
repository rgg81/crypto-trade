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

Benchmark (`--benchmark`, default `ew69`):
  * `ew69` — the equal-weight-69 universe daily return (iter_013.market_return): the honest, PIT
    market-neutral reference (the book is ~market-neutral with a small controlled TSMOM tilt, so
    performance relative to the EW-69 tape is the informative comparison). DEFAULT — the existing
    reports-tradfi/quantstats_iter015_allperiods.html is reproduced byte-for-byte.
  * `spy` — the S&P 500 via SPY total-return (yfinance auto_adjust=True == dividend+split adjusted,
    matching the strategy's total-return basis; ^GSPC price-index fallback if SPY is flaky). SPY
    daily open-to-open forward returns are aligned to the strategy trading-day index (same NYSE
    calendar, same open[t]->open[t+1] convention the strategy + EW-69 benchmark use), so realized
    beta/alpha are like-for-like. Writes a SEPARATE HTML and prints beta/corr/alpha/IR/Sharpe vs SPY
    — the point of a market benchmark: show the book is ~market-neutral / independent of the S&P.

Run (default EW-69):  uv run python analysis/portfolio/tradfi/gen_quantstats_tradfi.py
Run (vs S&P 500):     ... gen_quantstats_tradfi.py --benchmark spy
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
PERIODS_PER_YEAR = 252  # daily US-equity trading days

# Per-benchmark output HTML + tearsheet title. Default (ew69) reproduces the pre-existing report.
BENCH_CONFIG = {
    "ew69": (
        OUT_DIR / "quantstats_iter015_allperiods.html",
        "portfolio-tradfi iter-015 (2010-2026, all periods)",
    ),
    "spy": (
        OUT_DIR / "quantstats_iter015_allperiods_SPY.html",
        "portfolio-tradfi iter-015 (2010-2026) vs S&P 500",
    ),
}

# SPY total-return benchmark (yfinance, dividend+split adjusted); ^GSPC price-index fallback.
SPY_DIRNAME = "SPY"
SPY_TICKER = "SPY"
SPY_FALLBACK_TICKER = "^GSPC"
SPY_START = "2010-01-01"
SPY_END = "2026-06-30"


def _fetch_spy_csv(base: Path) -> str:
    """Download SPY (fallback ^GSPC) total-return daily bars -> base/SPY/1d.csv; return ticker used.

    Reuses the exact yfinance path + project CSV schema from ingest_yahoo (auto_adjust=True ==
    dividend+split adjusted == a total-return index). Imported lazily so the default EW-69 run needs
    neither yfinance nor the network.
    """
    from ingest_dukascopy_stocks import write_daily_csv  # noqa: PLC0415
    from ingest_yahoo import _to_daily_frame, download_daily  # noqa: PLC0415

    end_excl = str((pd.Timestamp(SPY_END) + pd.Timedelta(days=1)).date())  # yfinance end exclusive
    used = SPY_TICKER
    df = download_daily(SPY_TICKER, SPY_START, end_excl)
    if df is None or df.empty:
        print(f"  ! {SPY_TICKER} unavailable — falling back to {SPY_FALLBACK_TICKER} (PRICE-only)")
        used = SPY_FALLBACK_TICKER
        df = download_daily(SPY_FALLBACK_TICKER, SPY_START, end_excl)
    if df is None or df.empty:
        raise SystemExit(f"Could not download SPY/{SPY_FALLBACK_TICKER} from yfinance.")
    daily = _to_daily_frame(df)
    p = write_daily_csv(SPY_DIRNAME, daily, str(base))
    print(f"  cached {used} total-return -> {p} ({len(daily)} bars)")
    return used


def load_spy_bench(data_dir: str | None = None) -> pd.Series:
    """SPY daily open-to-open forward return, total-return basis, cached at data/SPY/1d.csv.

    Uses the SAME open[t]->open[t+1] forward convention as the strategy PnL + the EW-69 benchmark,
    so realized beta/alpha are like-for-like. Downloads + caches on first call, reads cache after.
    """
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    csv_path = base / SPY_DIRNAME / "1d.csv"
    if not csv_path.exists():
        _fetch_spy_csv(base)
    df = pd.read_csv(csv_path, usecols=["open_time", "open"])
    df = df.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    opens = df["open"].astype(float)
    opens.index = pd.to_datetime(opens.index, unit="ms")
    ret_fwd = (opens.shift(-1) / opens - 1.0).dropna()  # open[t+1]/open[t]-1, matches the strategy
    ret_fwd.name = "S&P 500 (SPY TR)"
    return ret_fwd


def build_series(
    benchmark: str = "ew69", data_dir: str | None = None
) -> tuple[pd.Series, pd.Series]:
    """Return (deployed iter-015 daily net returns, benchmark) over the FULL 2010-2026 period.

    The net series is iter_015_cost._deployed_net1x on the FROZEN, pre-registered deployed cell
    (delta=iter_015.CHOSEN_DELTA=0.010, freq=iter_015.CHOSEN_FREQ=1, lam=0.25, VIX-ON, 1x cost) —
    the identical past-only object iter_015_oos_check confirms, just not date-sliced. Only the
    benchmark leg varies: `ew69` = equal-weight-69 universe, `spy` = S&P 500 (SPY total-return).
    """
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, data_dir)
    if not coins:
        raise SystemExit("No ingested tradfi data found. Run ingest_yahoo.py first.")
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    vix = i8.load_vix_close(ret_fwd.index, data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    # DEPLOYED iter-015 daily net (lam=0.25, VIX-ON, 1x cost) on the FROZEN (0.010, 1) cell.
    returns = i15._deployed_net1x(pn, ret_fwd, s_vix, i15.CHOSEN_DELTA, i15.CHOSEN_FREQ).dropna()
    returns.name = "iter-015"

    if benchmark == "spy":
        bench = load_spy_bench(data_dir).reindex(returns.index).dropna()
        bench.name = "S&P 500 (SPY TR)"
    else:
        mkt = i13.market_return(pn)  # EW-69 universe forward return = market-neutral reference
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


def print_benchmark_stats(returns: pd.Series, bench: pd.Series) -> None:
    """Print realized strategy-vs-benchmark stats: beta, correlation, annualized alpha, IR, Sharpes.

    Beta/alpha are the CAPM regression of the strategy net on the benchmark (alpha annualized
    arithmetically x252, matching quantstats' greeks convention). Information ratio = annualized
    mean/std of the active return (strategy - benchmark). All over the FULL aligned period.
    """
    df = pd.concat([returns.rename("s"), bench.rename("b")], axis=1).dropna()
    s, b = df["s"], df["b"]
    var_b = float(b.var())
    beta = float(s.cov(b) / var_b) if var_b > 0 else float("nan")
    corr = float(s.corr(b))
    alpha_ann = float(s.mean() - beta * b.mean()) * PERIODS_PER_YEAR
    active = s - b
    ir = (
        float(active.mean() / active.std() * (PERIODS_PER_YEAR**0.5))
        if active.std() > 0
        else float("nan")
    )
    sharpe_s = float(qs.stats.sharpe(s, periods=PERIODS_PER_YEAR))
    sharpe_b = float(qs.stats.sharpe(b, periods=PERIODS_PER_YEAR))

    print("=" * 88)
    print(f"STRATEGY vs {bench.name} — realized market benchmark (2010-2026, ALL PERIODS)")
    print("=" * 88)
    print(
        f"  aligned window  : {s.index.min().date()} .. {s.index.max().date()}  "
        f"({len(s)} trading days)"
    )
    print(f"  beta            : {beta:+.4f}")
    print(f"  correlation     : {corr:+.4f}")
    print(f"  alpha (ann.)    : {alpha_ann * 100:+.2f}%")
    print(f"  information ratio: {ir:+.3f}")
    print(f"  Sharpe strategy : {sharpe_s:+.3f}")
    print(f"  Sharpe {bench.name[:9]:9}: {sharpe_b:+.3f}")
    print("=" * 88)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--benchmark", choices=("ew69", "spy"), default="ew69")
    args = ap.parse_args()

    # Frozen-cell guard: report the pre-registered deployed cell, never a drifted one.
    assert (i15.CHOSEN_DELTA, i15.CHOSEN_FREQ) == (0.010, 1), (
        f"iter-015 deployed cell drifted to {(i15.CHOSEN_DELTA, i15.CHOSEN_FREQ)} — refusing"
    )

    out_html, title = BENCH_CONFIG[args.benchmark]
    returns, bench = build_series(args.benchmark, args.data_dir)
    if returns.dropna().empty:
        raise SystemExit("empty deployed return series — check data ingestion")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qs.reports.html(
        returns,
        benchmark=bench,
        output=str(out_html),
        title=title,
        periods_per_year=PERIODS_PER_YEAR,
    )
    print(f"\nwrote tearsheet -> {out_html}")

    # headline metrics to stdout (n names = ingested universe members feeding the book)
    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms_n = len([p for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP])
    print_headline(returns.dropna(), syms_n)

    # Market-benchmark comparison (the point of benchmarking against the S&P): show independence.
    if args.benchmark == "spy":
        print_benchmark_stats(returns, bench)


if __name__ == "__main__":
    main()
