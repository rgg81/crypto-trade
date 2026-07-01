"""Ingest a BROAD liquid US large/mid-cap universe -> data_broad/<TICKER>/1d.csv (iter-012).

WHY a separate broad universe. The tradeable-69 Binance-perp names are homogeneous mega-cap GROWTH,
so the cross-sectional VALUE / SIZE / LOW-BETA / LOW-VOL factors are signal-negative there (no cheap
tail, no small tail, no genuine low-beta tail). The multi-factor pivot's PIVOTAL question is whether
those same factors RESURRECT on a broad universe with real cross-sectional diversity. This script
builds that universe. It writes to `data_broad/` (SEPARATE dir, gitignored) so it never touches the
tradeable-69 `data/` of record.

  * UNIVERSE = current S&P 500 constituents (pulled live from Wikipedia's constituent table), UNION
    the tradeable-69's broad tickers (so the hybrid deployable-69 probe has a complete sub-panel).
  * SECTORS = GICS sector straight from the same Wikipedia table (11 GICS sectors) — the sector-map
    needed for sector-neutral factors. For the ~14 tradeable-69 ADRs/recent-IPOs NOT in the S&P 500
    we fall back to an INTERNAL->GICS map derived from universe_tradfi.SECTOR_MAP. Cached to
    `data_broad/_sectors.json` so the factor script never needs the network.
  * PRICES = Yahoo daily TOTAL-RETURN (auto_adjust=True: dividend+split adjusted) 2010-2025, project
    Kline 6-col CSV schema (identical to core_tradfi.load_tradfi's reader).

>>> SURVIVORSHIP BIAS <<<  Current S&P 500 membership is NOT point-in-time: a name is in today's
index BECAUSE it survived and grew. Backtesting factors on current membership INFLATES results
(the failures were delisted and are absent). This is a deliberate FIRST-PASS diversity test — is
there enough cross-sectional spread for BAB/low-vol/size/value to fire at all? — NOT a deployable
backtest. If the factors work here, the follow-up is a PIT-membership (delisted-inclusive) rebuild.
Every downstream report flags this.

Run from repo root:
    uv run python analysis/portfolio/tradfi/ingest_yahoo_broad.py
    uv run python analysis/portfolio/tradfi/ingest_yahoo_broad.py --limit 10   # smoke test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx
import pandas as pd
import yfinance as yf

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import universe_tradfi as ut  # noqa: E402
from ingest_dukascopy_stocks import write_daily_csv  # noqa: E402  (reuse the exact schema writer)

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SECTORS_JSON = "_sectors.json"  # data_broad/_sectors.json : {broad_ticker: GICS sector}

# Tradeable-69 internal sector tags -> GICS sector labels (for the ~14 non-S&P-500 names).
_INTERNAL_TO_GICS: dict[str, str] = {
    "Tech": "Information Technology",
    "Semi": "Information Technology",
    "Comm": "Communication Services",
    "ConsDisc": "Consumer Discretionary",
    "ConsStap": "Consumer Staples",
    "Fin": "Financials",
    "Health": "Health Care",
    "Indust": "Industrials",
    "Energy": "Energy",
    "Crypto": "Financials",  # crypto-proxy equities bucketed with Financials for neutralization
}
# Binance perp ticker -> Yahoo ticker overrides for the tradeable-69 (else stem: AAPLUSDT -> AAPL).
_YAHOO_OVERRIDES: dict[str, str] = {"BRKBUSDT": "BRK-B", "PAYPUSDT": "PYPL"}


def binance_to_broad(sym: str) -> str:
    """Tradeable-69 Binance perp ticker (AAPLUSDT) -> Yahoo/broad ticker (AAPL / BRK-B / PYPL)."""
    if sym in _YAHOO_OVERRIDES:
        return _YAHOO_OVERRIDES[sym]
    return ut.stem(sym)


def _clean(cell: str) -> str:
    """Strip HTML tags + unescape the few entities the constituent table uses."""
    txt = re.sub(r"<[^>]+>", "", cell)
    return txt.replace("&amp;", "&").replace("&nbsp;", " ").strip()


def sp500_from_wikipedia(url: str = WIKI_URL, timeout: float = 30.0) -> dict[str, str]:
    """Parse the S&P 500 constituent table -> {yahoo_ticker: GICS sector}.

    Isolates ONLY the first wikitable (id="constituents"), so the second 'recent changes' table can
    never leak company-name strings into the sector column. Symbols use Yahoo's dash convention
    (BRK.B -> BRK-B). Raises on an empty/failed parse so the caller can fall back or abort loudly.
    """
    r = httpx.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (research)"})
    r.raise_for_status()
    html = r.text
    start = html.find('id="constituents"')
    if start < 0:
        raise RuntimeError("S&P 500 constituent table not found on Wikipedia page")
    end = html.find("</table>", start)
    table = html[start:end]
    out: dict[str, str] = {}
    for row in re.findall(r"<tr>(.*?)</tr>", table, re.S)[1:]:  # skip header row
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        if len(cells) < 4:
            continue
        sym = _clean(cells[0]).replace(".", "-")  # BRK.B -> BRK-B (Yahoo convention)
        sector = _clean(cells[2])
        if sym and sector:
            out[sym] = sector
    if len(out) < 400:
        raise RuntimeError(f"parsed only {len(out)} S&P 500 names (<400) — table format changed?")
    return out


def build_universe() -> dict[str, str]:
    """{broad_ticker: GICS sector} = S&P 500 (Wikipedia) UNION the tradeable-69 broad tickers.

    The 69 are added so the hybrid deployable-69 probe has a complete sub-panel even for the ADRs /
    recent IPOs that are not S&P 500 members; their sector comes from the INTERNAL->GICS map.
    """
    universe = sp500_from_wikipedia()
    n_sp = len(universe)
    added = 0
    for binance_sym, internal_sector in ut.SECTOR_MAP.items():
        bt = binance_to_broad(binance_sym)
        if bt not in universe:
            universe[bt] = _INTERNAL_TO_GICS.get(internal_sector, "Industrials")
            added += 1
    print(f"  universe: {n_sp} S&P 500 + {added} tradeable-69 extras = {len(universe)} names")
    return universe


def _to_daily_frame(df: pd.DataFrame) -> pd.DataFrame | None:
    """One ticker's yfinance OHLCV frame -> project [open_time(ms), O, H, L, C, V]; None if empty.

    auto_adjust=True means OHLC are already total-return adjusted. The Date index is tz-naive
    calendar midnights; localize to UTC and emit epoch-ms (as_unit('ms').asi8 under pandas 3.0).
    """
    if df is None or df.empty:
        return None
    df = df.rename(columns={c: str(c).lower() for c in df.columns})
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    if "open" not in keep or "close" not in keep:
        return None
    df = df[keep].dropna(subset=["open", "close"]).sort_index()
    if df.empty:
        return None
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    out = df.reset_index(drop=True)
    out.insert(0, "open_time", idx.normalize().as_unit("ms").asi8.astype("int64"))
    if "volume" not in out.columns:
        out["volume"] = 0.0
    return out[["open_time", "open", "high", "low", "close", "volume"]]


def _download_chunk(
    tickers: list[str], start: str, end: str, retries: int = 3
) -> dict[str, pd.DataFrame]:
    """Batched yf.download (group_by='ticker') -> {ticker: raw OHLCV}; skips missing tickers."""
    for attempt in range(retries):
        try:
            data = yf.download(
                tickers,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                actions=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )
        except Exception as e:  # noqa: BLE001
            print(f"    chunk error (attempt {attempt + 1}): {e}")
            data = None
        if data is not None and not data.empty:
            break
        time.sleep(1.0 + attempt)
    else:
        return {}
    out: dict[str, pd.DataFrame] = {}
    if isinstance(data.columns, pd.MultiIndex):
        for t in tickers:
            if t in data.columns.get_level_values(0):
                out[t] = data[t].dropna(how="all")
    else:  # single-ticker call collapses to a flat frame
        out[tickers[0]] = data
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--end", default=str((pd.Timestamp.now("UTC") + pd.Timedelta(days=1)).date()))
    ap.add_argument("--data-dir", default=str(_ROOT / "data_broad"))
    ap.add_argument("--chunk", type=int, default=60, help="tickers per batched download")
    ap.add_argument("--limit", type=int, default=0, help="cap universe size (smoke test); 0 = all")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between chunks (politeness)")
    args = ap.parse_args()

    print(f"Broad-universe ingest -> {args.data_dir}  ({args.start}..{args.end}, auto_adjust=True)")
    print("  *** SURVIVORSHIP CAVEAT: current S&P 500 membership is NOT point-in-time. ***\n")

    universe = build_universe()  # {broad_ticker: GICS sector}
    tickers = sorted(universe)
    if args.limit:
        tickers = tickers[: args.limit]

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    # Cache the sector map FIRST (network-free input for the factor script).
    (data_dir / SECTORS_JSON).write_text(
        json.dumps({t: universe[t] for t in tickers}, indent=0, sort_keys=True)
    )

    ok: list[str] = []
    failed: list[str] = []
    for i in range(0, len(tickers), args.chunk):
        chunk = tickers[i : i + args.chunk]
        frames = _download_chunk(chunk, args.start, args.end)
        for t in chunk:
            daily = _to_daily_frame(frames.get(t))
            if daily is None or daily.empty:
                failed.append(t)
                continue
            write_daily_csv(t, daily, args.data_dir)
            ok.append(t)
        print(
            f"  chunk {i // args.chunk + 1}: {len(chunk)} req -> {len(ok)} ok / {len(failed)} fail"
        )
        time.sleep(args.pause)

    print(f"\nDone. {len(ok)}/{len(tickers)} ingested; {len(failed)} failed.")
    if failed:
        print("  failed: " + ", ".join(failed))
    print(f"  sectors cached -> {data_dir / SECTORS_JSON}")


if __name__ == "__main__":
    main()
