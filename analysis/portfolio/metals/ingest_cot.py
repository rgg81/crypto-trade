"""metals-portfolio COT ingestion — CFTC disaggregated futures-only positioning cache.

The COT (Commitments of Traders) report is the data source for the iter-004 managed-money
contrarian SLEEVE, exactly as `ingest_dukascopy.py` is the data source for the price candles.
It fetches the CFTC weekly disaggregated futures-only report (`cot_reports.cot_year`,
`cot_report_type='disaggregated_fut'`) for 2014..2026, filters to the 5 metal contracts, keeps
the managed-money + producer/merchant positioning columns, and caches a tidy long-format frame to
`data/cot/cot_metals.parquet` (gitignored — regenerable, exactly like the price CSVs).

Leak-safety lives DOWNSTREAM (iter_004_cot.align_cot_to_grid applies a conservative release lag).
This module only fetches + tidies the raw weekly snapshots, keyed by the Tuesday `Report_Date`.

Contracts (CFTC `Market_and_Exchange_Names` → Binance perp ticker):
  GOLD - COMMODITY EXCHANGE INC.            → XAUUSDT   (tradeable)
  SILVER - COMMODITY EXCHANGE INC.          → XAGUSDT   (tradeable)
  PLATINUM - NEW YORK MERCANTILE EXCHANGE   → XPTUSDT   (tradeable)
  PALLADIUM - NEW YORK MERCANTILE EXCHANGE  → XPDUSDT   (tradeable)
  COPPER- #1 - COMMODITY EXCHANGE INC.      → COPPER    (feature-only — no metal perp)
MICRO GOLD is explicitly EXCLUDED (a separate, smaller contract that would double-count gold).

Idempotent: re-running overwrites the cache deterministically. `cot_year` may drop an
`f_year.txt` scratch file in the CWD — this module removes it on exit.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import cot_reports as cot
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = _ROOT / "data" / "cot" / "cot_metals.parquet"

# CFTC contract long-name → Binance perp ticker. MICRO GOLD intentionally absent.
CONTRACTS: dict[str, str] = {
    "GOLD - COMMODITY EXCHANGE INC.": "XAUUSDT",
    "SILVER - COMMODITY EXCHANGE INC.": "XAGUSDT",
    "PLATINUM - NEW YORK MERCANTILE EXCHANGE": "XPTUSDT",
    "PALLADIUM - NEW YORK MERCANTILE EXCHANGE": "XPDUSDT",
    "COPPER- #1 - COMMODITY EXCHANGE INC.": "COPPER",  # feature-only (no metal perp)
}

# Columns kept from the disaggregated futures-only report. Managed-money (the speculative crowd
# this sleeve fades) + producer/merchant (commercials, kept for completeness / future use).
KEEP_COLS: list[str] = [
    "Market_and_Exchange_Names",
    "Report_Date_as_YYYY-MM-DD",
    "Open_Interest_All",
    "M_Money_Positions_Long_All",
    "M_Money_Positions_Short_All",
    "Prod_Merc_Positions_Long_All",
    "Prod_Merc_Positions_Short_All",
]
_NUMERIC_COLS: list[str] = [c for c in KEEP_COLS if c not in ("Market_and_Exchange_Names",)][1:]

YEARS = range(2014, 2027)  # 2014 buffers the z-score warmup before the gold/silver 2015 era


def fetch_cot(years: range = YEARS) -> pd.DataFrame:
    """Fetch + concat the disaggregated futures-only COT for `years`, filter to the 5 metals.

    Returns a tidy long-format frame: one row per (ticker, Tuesday Report_Date), with the kept
    positioning columns coerced to numeric, a `ticker` column (mapped from the CFTC long name),
    and a parsed `date` column. Sorted by (ticker, date). Years that fail to download are skipped
    with a note so a partial cache still builds.
    """
    frames: list[pd.DataFrame] = []
    for yr in years:
        try:
            raw = cot.cot_year(year=yr, cot_report_type="disaggregated_fut")
        except Exception as exc:  # network / availability — skip, keep going
            print(f"  ! {yr}: fetch failed ({exc}) — skipped")
            continue
        sub = raw[raw["Market_and_Exchange_Names"].isin(CONTRACTS)][KEEP_COLS].copy()
        frames.append(sub)
        print(f"  {yr}: {len(sub)} metal-rows")
    if not frames:
        raise RuntimeError("no COT data fetched for any year")

    allc = pd.concat(frames, ignore_index=True)
    allc["ticker"] = allc["Market_and_Exchange_Names"].map(CONTRACTS)
    allc["date"] = pd.to_datetime(allc["Report_Date_as_YYYY-MM-DD"])
    for c in _NUMERIC_COLS:
        allc[c] = pd.to_numeric(allc[c], errors="coerce")
    allc = allc.sort_values(["ticker", "date"]).reset_index(drop=True)
    return allc


def ingest(path: Path = CACHE_PATH, years: range = YEARS) -> pd.DataFrame:
    """Fetch, tidy, and cache the metals COT panel to `path` (idempotent). Returns the frame.

    Cleans up the `f_year.txt` scratch file `cot_year` may leave in the CWD.
    """
    df = fetch_cot(years)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    # cot_year may write a scratch f_year.txt into the CWD — remove it.
    with contextlib.suppress(FileNotFoundError):
        Path("f_year.txt").unlink()
    return df


def refresh_recent(path: Path = CACHE_PATH, n_years: int = 2) -> pd.DataFrame:
    """Incremental live refresh: re-fetch the last `n_years` calendar years (one CFTC call each) and
    MERGE into the cached panel (dedup on (ticker, date), keep latest) so the deep history is kept
    and only recent weekly releases are appended. Used by the live engine."""
    import datetime as _dt

    yr = _dt.datetime.now(_dt.UTC).year
    new = fetch_cot(range(yr - n_years + 1, yr + 1))
    if path.exists():
        new = (
            pd.concat([pd.read_parquet(path), new])
            .drop_duplicates(["ticker", "date"], keep="last")
            .sort_values(["ticker", "date"])
            .reset_index(drop=True)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_parquet(path)
    with contextlib.suppress(FileNotFoundError):
        Path("f_year.txt").unlink()
    return new


def main() -> None:
    df = ingest()
    print(f"\nCACHED {df.shape[0]} rows × {df.shape[1]} cols → {CACHE_PATH}")
    span = df.groupby("ticker")["date"].agg(["min", "max", "count"])
    print(span.to_string())
    wd = df["date"].dt.weekday.value_counts().sort_index().to_dict()
    print(f"report weekdays (1=Tue, 0=Mon holiday-shift): {wd}")


if __name__ == "__main__":
    main()
