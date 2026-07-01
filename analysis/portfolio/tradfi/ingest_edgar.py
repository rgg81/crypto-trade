"""SEC-EDGAR point-in-time (PIT) fundamentals ingest for the tradfi VALUE + QUALITY factors.

PIT discipline is the whole point. A reported fundamental value is knowable ONLY on/after the
`filed` date of the filing that first disclosed it — NEVER on its period `end` date. A 10-K for
fiscal-year ending 2023-12-31 is typically filed in late January/February 2024; using the FY2023
book value on any day before that filing is look-ahead. Every daily series built here carries, for
trading day t, the LATEST fact whose `filed` <= t (`reindex(method="ffill")` over filed dates), and
the regression test in tests/test_tradfi_fundamentals.py proves a fact never appears before `filed`.

Pipeline:
  1. Map each of the 69 `universe_tradfi.SECTOR_MAP` Binance perp tickers -> its real SEC ticker
     (BRKB->BRK-B, PAYP->PYPL, ADRs use their US listing) -> its CIK via SEC's company_tickers.json.
  2. Fetch `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` per CIK, cache raw JSON
     to data/edgar/<CIK>.json (gitignored). SEC needs a descriptive User-Agent + ~10 req/s limit.
  3. Extract the core US-GAAP (+ dei) XBRL concepts, each fact carrying `filed` / `end` / `val`.
  4. PIT-align each concept into a per-name daily series (carry latest fact with filed <= t).

Foreign ADRs (BABA/TSM/ASML/NVO/SONY/ARM/NOK) file 20-F/6-K under IFRS, so their companyfacts carry
no us-gaap StockholdersEquity/Assets/etc. — they resolve to a CIK but yield EMPTY concept series ->
NaN in the factors -> 0 weight (point-in-time, leak-safe: a name with no known fundamental simply
takes no fundamental position).

Run from repo root (one-time ingest; re-runs skip cached CIKs):
    uv run python analysis/portfolio/tradfi/ingest_edgar.py
    uv run python analysis/portfolio/tradfi/ingest_edgar.py --symbols AAPLUSDT,MSFTUSDT --force
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import universe_tradfi as ut  # noqa: E402

# SEC politeness: a descriptive UA is MANDATORY (SEC blocks blank/robotic UAs) + <=10 req/s.
USER_AGENT = "portfolio-tradfi research contact@example.com"
_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
_REQ_PAUSE = 0.12  # ~8 req/s, comfortably under the 10 req/s limit

# Binance perp stem -> real SEC ticker overrides (everything else maps to its stem).
#   BRKB -> BRK-B (SEC dashes the Berkshire class-B line), PAYP -> PYPL (PayPal's listed symbol).
#   ADRs (BABA/TSM/ASML/ARM/NVO/SONY/NOK) trade under their US listing == stem, so no override.
SEC_TICKER_OVERRIDES: dict[str, str] = {"BRKB": "BRK-B", "PAYP": "PYPL"}

# Foreign 20-F/6-K filers: resolve to a CIK but publish IFRS (no us-gaap facts) -> expected NaN.
FOREIGN_ADRS: frozenset[str] = frozenset({"BABA", "TSM", "ASML", "NVO", "SONY", "ARM", "NOK"})

# ---- core XBRL concept groups (taxonomy, concept-name candidates, unit) ------------------------
# Instant (balance-sheet / cover-page) concepts carry only `end`; duration (flow) concepts carry
# `start`+`end` and are annual-filtered downstream. Candidate lists are tried in order (first hit).
BOOK_EQUITY = ("us-gaap", ["StockholdersEquity"], "USD")
ASSETS = ("us-gaap", ["Assets"], "USD")
NET_INCOME = ("us-gaap", ["NetIncomeLoss"], "USD")
REVENUES = (
    "us-gaap",
    [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "USD",
)
GROSS_PROFIT = ("us-gaap", ["GrossProfit"], "USD")
COST_OF_REVENUE = (
    "us-gaap",
    ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "USD",
)
SHARES = (
    "dei",
    ["EntityCommonStockSharesOutstanding"],
    "shares",
)
SHARES_FALLBACK = ("us-gaap", ["CommonStockSharesOutstanding"], "shares")

ANNUAL_MIN_DAYS = 340  # a 10-K fiscal year duration lands ~365d; comparatives/quarters are excluded
ANNUAL_MAX_DAYS = 400


def real_ticker(binance_sym: str) -> str:
    """Binance perp ticker (AAPLUSDT) -> its real SEC ticker (AAPL / BRK-B / PYPL)."""
    st = ut.stem(binance_sym)
    return SEC_TICKER_OVERRIDES.get(st, st)


def _http_get_json(url: str, timeout: float = 30.0) -> dict | None:
    """GET a JSON document with the required SEC User-Agent; None on 404/HTTP error."""
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted SEC host)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"    HTTP {e.code} for {url}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"    error fetching {url}: {e}")
        return None


def load_ticker_cik_map(cache_dir: Path, force: bool = False) -> dict[str, int]:
    """SEC ticker (upper) -> CIK int, from company_tickers.json (cached under data/edgar/)."""
    cache = cache_dir / "_company_tickers.json"
    raw: dict | None = None
    if cache.exists() and not force:
        raw = json.loads(cache.read_text())
    else:
        raw = _http_get_json(_TICKER_MAP_URL)
        if raw is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(raw))
    if not raw:
        return {}
    return {row["ticker"].upper(): int(row["cik_str"]) for row in raw.values()}


def resolve_ciks(symbols: list[str], cache_dir: Path, force: bool = False) -> dict[str, int]:
    """Binance perp ticker -> CIK for every name resolvable in SEC's ticker map."""
    t2c = load_ticker_cik_map(cache_dir, force=force)
    out: dict[str, int] = {}
    for sym in symbols:
        cik = t2c.get(real_ticker(sym).upper())
        if cik is not None:
            out[sym] = cik
    return out


def fetch_companyfacts(cik: int, cache_dir: Path, force: bool = False) -> dict | None:
    """Fetch + cache one CIK's companyfacts JSON. Returns the parsed dict (None if unavailable)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"CIK{cik:010d}.json"
    if cache.exists() and not force:
        try:
            return json.loads(cache.read_text())
        except json.JSONDecodeError:
            pass  # corrupt cache -> re-fetch
    data = _http_get_json(_FACTS_URL.format(cik=cik))
    if data is not None:
        cache.write_text(json.dumps(data))
    return data


def extract_concept_facts(
    facts_json: dict, taxonomy: str, concepts: list[str], unit: str
) -> pd.DataFrame:
    """Return a [filed, end, start, val] frame for the first present concept, else empty.

    Each XBRL fact under facts[taxonomy][concept]["units"][unit] carries `end`, `val`, `filed`, and
    (for duration concepts) `start`. We keep those three/four fields; downstream PIT selection uses
    `filed` (knowability) and `end` (recency), never fabricating a value before it was filed.
    """
    node = facts_json.get("facts", {}).get(taxonomy, {})
    for concept in concepts:
        c = node.get(concept)
        if not c:
            continue
        arr = c.get("units", {}).get(unit)
        if not arr:
            continue
        rows = []
        for f in arr:
            if f.get("val") is None or "end" not in f or "filed" not in f:
                continue
            rows.append(
                {
                    "filed": pd.Timestamp(f["filed"]),
                    "end": pd.Timestamp(f["end"]),
                    "start": pd.Timestamp(f["start"]) if f.get("start") else pd.NaT,
                    "val": float(f["val"]),
                }
            )
        if rows:
            return pd.DataFrame(rows)
    return pd.DataFrame(columns=["filed", "end", "start", "val"])


def pit_step(facts: pd.DataFrame, annual: bool = False) -> pd.Series:
    """Reduce raw facts -> a PIT step series indexed by `filed` date (val = latest-period known).

    THE PIT RULE: as of a given `filed` date d, the knowable value of a concept is the fact with the
    MAXIMUM period `end` among all facts with `filed` <= d (ties on `end` broken by the latest
    `filed`, i.e. the most recent restatement). Because the pool of filed facts grows monotonically
    with d and we only ever advance to `end >= best_end`, a single forward scan in (filed, end)
    order yields, per `filed` date, the correct point-in-time val. For flow concepts, `annual=True`
    keeps only ~annual-duration facts (the 10-K fiscal-year figure), dropping quarters/comparatives.

    Returns an empty Series if there are no usable facts (foreign IFRS filers / missing concept).
    """
    if facts.empty:
        return pd.Series(dtype=float)
    df = facts.dropna(subset=["filed", "end", "val"]).copy()
    if annual:
        dur = (df["end"] - df["start"]).dt.days
        df = df[dur.between(ANNUAL_MIN_DAYS, ANNUAL_MAX_DAYS)]
    if df.empty:
        return pd.Series(dtype=float)
    df = df.sort_values(["filed", "end"])
    best_end: pd.Timestamp | None = None
    best_val = np.nan
    snap: dict[pd.Timestamp, float] = {}
    for filed, end, val in df[["filed", "end", "val"]].itertuples(index=False):
        if best_end is None or end >= best_end:
            best_end, best_val = end, val
        snap[filed] = best_val  # last write per filed date == max-end value after that filing
    s = pd.Series(snap).sort_index()
    return s[~s.index.duplicated(keep="last")]


def pit_daily(
    facts: pd.DataFrame, trading_days: pd.DatetimeIndex, annual: bool = False
) -> pd.Series:
    """PIT step reindexed onto `trading_days` (carry latest fact filed <= t; NaN pre-first)."""
    step = pit_step(facts, annual=annual)
    if step.empty:
        return pd.Series(np.nan, index=trading_days)
    return step.reindex(trading_days, method="ffill")


def _daily_for(
    facts_json: dict, spec: tuple[str, list[str], str], trading_days: pd.DatetimeIndex, annual: bool
) -> pd.Series:
    tax, concepts, unit = spec
    return pit_daily(extract_concept_facts(facts_json, tax, concepts, unit), trading_days, annual)


def build_fundamental_panels(
    symbols: list[str], trading_days: pd.DatetimeIndex, cache_dir: Path | None = None
) -> dict[str, pd.DataFrame]:
    """Build PIT daily fundamental panels (trading_days x symbols) from cached companyfacts.

    Returns {concept: DataFrame}. `gross_profit` is GrossProfit where present, else Revenues -
    CostOfRevenue (Novy-Marx fallback). Names with no us-gaap facts (foreign ADRs / uncached) are
    all-NaN columns -> 0 weight downstream. This reads ONLY the on-disk cache; run the ingest first.
    """
    cache = cache_dir if cache_dir is not None else _ROOT / "data" / "edgar"
    ciks = resolve_ciks(symbols, cache)
    cols = {
        k: {} for k in ("book_equity", "assets", "net_income", "revenues", "gross_profit", "shares")
    }
    for sym in symbols:
        cik = ciks.get(sym)
        fj = None
        if cik is not None:
            p = cache / f"CIK{cik:010d}.json"
            if p.exists():
                try:
                    fj = json.loads(p.read_text())
                except json.JSONDecodeError:
                    fj = None
        if fj is None:
            nan = pd.Series(np.nan, index=trading_days)
            for k in cols:
                cols[k][sym] = nan
            continue
        book = _daily_for(fj, BOOK_EQUITY, trading_days, annual=False)
        assets = _daily_for(fj, ASSETS, trading_days, annual=False)
        ni = _daily_for(fj, NET_INCOME, trading_days, annual=True)
        rev = _daily_for(fj, REVENUES, trading_days, annual=True)
        gp = _daily_for(fj, GROSS_PROFIT, trading_days, annual=True)
        cost = _daily_for(fj, COST_OF_REVENUE, trading_days, annual=True)
        shares = _daily_for(fj, SHARES, trading_days, annual=False)
        if shares.isna().all():
            shares = _daily_for(fj, SHARES_FALLBACK, trading_days, annual=False)
        # Gross-profit fallback: Revenues - CostOfRevenue where GrossProfit isn't tagged.
        gp = gp.where(gp.notna(), rev - cost)
        cols["book_equity"][sym] = book
        cols["assets"][sym] = assets
        cols["net_income"][sym] = ni
        cols["revenues"][sym] = rev
        cols["gross_profit"][sym] = gp
        cols["shares"][sym] = shares
    return {k: pd.DataFrame(v).reindex(columns=symbols) for k, v in cols.items()}


def _concept_coverage(fj: dict) -> dict[str, bool]:
    """Which core concepts a companyfacts JSON actually carries (for the ingest coverage report)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")])
    out = {}
    for name, spec, ann in (
        ("book", BOOK_EQUITY, False),
        ("assets", ASSETS, False),
        ("ni", NET_INCOME, True),
        ("rev", REVENUES, True),
        ("gp", GROSS_PROFIT, True),
        ("shares", SHARES, False),
    ):
        s = _daily_for(fj, spec, idx, ann)
        if name == "shares" and s.isna().all():
            s = _daily_for(fj, SHARES_FALLBACK, idx, False)
        out[name] = bool(s.notna().any())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(sorted(ut.SECTOR_MAP)))
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--force", action="store_true", help="re-fetch even if cached")
    ap.add_argument("--pause", type=float, default=_REQ_PAUSE, help="seconds between SEC requests")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    cache_dir = Path(args.data_dir) / "edgar"
    cache_dir.mkdir(parents=True, exist_ok=True)

    ciks = resolve_ciks(symbols, cache_dir, force=args.force)
    print(f"SEC-EDGAR ingest: {len(symbols)} names, {len(ciks)} resolved to a CIK\n")

    usable: list[str] = []
    empty: list[str] = []
    unresolved = [s for s in symbols if s not in ciks]
    for sym in symbols:
        cik = ciks.get(sym)
        if cik is None:
            print(f"  ! {sym:10} <- {real_ticker(sym):7} : NO CIK — skipped")
            continue
        fj = fetch_companyfacts(cik, cache_dir, force=args.force)
        time.sleep(args.pause)
        if fj is None:
            print(f"  ! {sym:10} <- CIK{cik:010d} : NO companyfacts (404/error)")
            empty.append(sym)
            continue
        cov = _concept_coverage(fj)
        has_core = cov["book"] and cov["shares"]  # minimum for the VALUE factor
        tag = "OK " if has_core else "IFRS/empty"
        adr = " [ADR]" if ut.stem(sym) in FOREIGN_ADRS else ""
        flags = "".join(k[0].upper() if v else "." for k, v in cov.items())
        print(f"  {tag:10} {sym:10} CIK{cik:010d}  concepts[{flags}]{adr}")
        (usable if has_core else empty).append(sym)

    print(f"\nDone. usable(core VALUE)={len(usable)}/{len(symbols)}  empty/IFRS={len(empty)}")
    if empty:
        print("  no usable us-gaap fundamentals: " + ", ".join(empty))
    if unresolved:
        print("  unresolved CIK: " + ", ".join(unresolved))
    print("  concept flags = [book,assets,ni,rev,gp,shares]  (letter=present, .=missing)")


if __name__ == "__main__":
    main()
