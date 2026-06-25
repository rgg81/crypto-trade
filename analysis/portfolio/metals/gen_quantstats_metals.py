"""Full quantstats tearsheet for the metals baseline (iter-008 sleeve-aware regime book).

Builds the MAXIMAL continuous series: gold/silver re-ingested gap-free from 2005 (Dukascopy depth) +
platinum/palladium from 2022 (their data start), runs the FROZEN regime-book baseline, compounds the
8h net to daily, and emits a full quantstats HTML report.

HONEST SCOPE: this is the strategy's full HISTORICAL SIMULATION across every available month — it
mixes in-sample (2015→2025-03), the selection-period bear (2011-2015), the pristine validation bear
(2008), and the bull OOS (2025-03→2026-06). It is NOT a pure live/forward track record. Metals are
24/5 so the daily series is a ~252-day/yr trading calendar (periods_per_year=252).

Run:  uv run python analysis/portfolio/metals/gen_quantstats_metals.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import quantstats as qs

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import ingest_dukascopy as ing  # noqa: E402
import iter_008_allweather as r8  # noqa: E402
import universe_metals as um  # noqa: E402

FULL_DIR = _HERE.parents[2] / "data_full"  # continuous gold/silver 2005+ ∪ pt/pd 2022+
MAIN_DIR = _HERE.parents[2] / "data"
GS = {"XAUUSDT": "xauusd", "XAGUSDT": "xagusd"}
PTPD = ("XPTUSDT", "XPDUSDT")
START = "2005-06-01"  # warmup before the first reportable month (~2006); through to now
REPORT_FROM = pd.Timestamp("2006-06-01")  # trim signal warmup
OUT = _HERE.parents[2] / "reports" / "portfolio-metals" / "quantstats_regime_book_all_months.html"


def _build_full_dataset() -> None:
    """Gap-free gold/silver 2005→now (one clean pull) + pt/pd copied from data/. Idempotent."""
    end = (pd.Timestamp.utcnow().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    for ticker, inst in GS.items():
        out = ing.csv_path(FULL_DIR, ticker, "8h")
        if out.exists():
            print(f"  {ticker}: cached")
            continue
        print(f"  {ticker} ← dukascopy {inst} {START}..{end} (continuous) ...", flush=True)
        with tempfile.TemporaryDirectory(prefix="full_") as tmp:
            ing.write_klines(
                out, ing.to_klines(ing.resample_8h(ing.fetch_h1(inst, START, end, tmp)))
            )
    for ticker in PTPD:  # pt/pd: copy the 2022+ data we already have
        src, dst = ing.csv_path(MAIN_DIR, ticker, "8h"), ing.csv_path(FULL_DIR, ticker, "8h")
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"  {ticker}: copied pt/pd from data/")


def to_daily(net: pd.Series) -> pd.Series:
    """Compound the per-8h net into daily returns (weekends drop out → ~252-day/yr calendar)."""
    s = net.copy()
    s.index = pd.to_datetime(s.index)
    return ((1 + s).resample("1D").prod() - 1).dropna()


def main() -> None:
    print("Building maximal continuous dataset (gold/silver 2005+, pt/pd 2022+)...")
    _build_full_dataset()
    coins = um.load_metals(FULL_DIR)
    spans = {
        s: (
            pd.to_datetime(d.index[0], unit="ms").date(),
            pd.to_datetime(d.index[-1], unit="ms").date(),
        )
        for s, d in coins.items()
    }
    print(f"  universe {tuple(coins)}  spans {spans}")

    net, _ = r8.regime_book(
        coins
    )  # FROZEN baseline (win450/thr0.6/a0.5/dW0.25→1.5 + sleeve-aware brake)
    net = net[net.index >= REPORT_FROM]
    daily = to_daily(net)
    print(
        f"  net 8h candles {len(net)}  → daily returns {len(daily)}  "
        f"({daily.index[0].date()} → {daily.index[-1].date()})"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    qs.reports.html(
        daily,
        benchmark=None,
        output=str(OUT),
        title="Metals Sleeve-Aware Regime Book — full historical simulation (all months)",
        periods_per_year=252,
    )
    print(f"\n  ✅ tearsheet → {OUT}")


if __name__ == "__main__":
    main()
