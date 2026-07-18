"""Funding-rate archive fallback — data.binance.vision monthly ZIPs (organizer-only).

The REST endpoint (/fapi/v1/fundingRate) can return nothing or a truncated head for
DELISTED perps. This fetcher fills the gap from the public monthly archives:

    https://data.binance.vision/data/futures/um/monthly/fundingRate/<SYM>/<SYM>-fundingRate-YYYY-MM.zip

Months are derived from the symbol's on-disk kline span; 404 months are skipped (a perp's
archive only exists for its live months). Output merges into the SAME
``funding_rates/<SYM>.csv`` schema (``funding_time,funding_rate``) the REST fetcher writes —
dedup on funding_time, sorted. Resumable and idempotent.

Archive CSV schemas vary by vintage; the reader sniffs the header and accepts both
``calc_time,funding_interval_hours,last_funding_rate`` (current) and any header carrying a
``*time*`` column + a ``*funding_rate*`` column.
"""

from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

import httpx
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from portfolio_tournament import constants as tc  # noqa: E402

ARCHIVE_URL = (
    "https://data.binance.vision/data/futures/um/monthly/fundingRate/"
    "{sym}/{sym}-fundingRate-{ym}.zip"
)


def _parse_archive_csv(data: bytes) -> pd.DataFrame:
    """-> DataFrame(funding_time, funding_rate) from one monthly archive CSV (header-sniffed)."""
    df = pd.read_csv(io.BytesIO(data))
    cols = {c.lower().strip(): c for c in df.columns}
    tcol = next((cols[c] for c in cols if "time" in c), None)
    rcol = next((cols[c] for c in cols if "funding_rate" in c or c == "rate"), None)
    if tcol is None or rcol is None:
        raise ValueError(f"unrecognized archive schema: {list(df.columns)}")
    out = pd.DataFrame(
        {
            "funding_time": pd.to_numeric(df[tcol], errors="coerce").astype("Int64"),
            "funding_rate": pd.to_numeric(df[rcol], errors="coerce"),
        }
    ).dropna()
    out["funding_time"] = out["funding_time"].astype("int64")
    return out


def month_range(lo_ms: int, hi_ms: int) -> list[str]:
    lo = pd.Timestamp(lo_ms, unit="ms").to_period("M")
    hi = pd.Timestamp(hi_ms, unit="ms").to_period("M")
    return [str(p) for p in pd.period_range(lo, hi, freq="M")]


def fetch_symbol(
    sym: str,
    src_data_dir: Path,
    out_dir: Path,
    *,
    client: httpx.Client | None = None,
    pause: float = 0.1,
) -> tuple[int, int]:
    """Fetch every archive month spanning the symbol's klines; merge into out_dir/<SYM>.csv.

    Returns (months_fetched, new_rows)."""
    kp = Path(src_data_dir) / sym / "8h.csv"
    if not kp.exists():
        print(f"  ! {sym}: no klines on disk — skipped")
        return 0, 0
    k = pd.read_csv(kp, usecols=["open_time"])
    months = month_range(int(k["open_time"].min()), int(k["open_time"].max()))
    out_csv = Path(out_dir) / f"{sym}.csv"
    cached = (
        pd.read_csv(out_csv)
        if out_csv.exists()
        else pd.DataFrame(columns=["funding_time", "funding_rate"])
    )
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=30.0, follow_redirects=True)
    frames, hit = [], 0
    try:
        for ym in months:
            r = client.get(ARCHIVE_URL.format(sym=sym, ym=ym))
            if r.status_code == 404:
                continue
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for name in z.namelist():
                    frames.append(_parse_archive_csv(z.read(name)))
            hit += 1
            time.sleep(pause)
    finally:
        if own_client:
            client.close()
    if not frames:
        return 0, 0
    new = pd.concat(frames, ignore_index=True)
    full = pd.concat([cached, new], ignore_index=True)
    full = (
        full.drop_duplicates(subset=["funding_time"], keep="first")
        .sort_values("funding_time")
        .reset_index(drop=True)
    )
    n_new = len(full) - len(cached)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(out_csv, index=False)
    print(f"  {sym}: {hit} archive months, +{n_new} rows -> {len(full)} total")
    return hit, n_new


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="fetch-funding-archive")
    ap.add_argument("--symbols", default="", help="comma list; or use --from-file")
    ap.add_argument("--from-file", default="", help="newline/JSON list of symbols")
    ap.add_argument("--src", default=str(tc.MAIN_DATA_DIR), help="kline store (for month spans)")
    ap.add_argument("--out", default="", help="funding dir (default <src>/funding_rates)")
    args = ap.parse_args(argv)

    syms: list[str] = [s for s in args.symbols.split(",") if s.strip()]
    if args.from_file:
        text = Path(args.from_file).read_text().strip()
        syms += json.loads(text) if text.startswith("[") else text.split()
    if not syms:
        print("no symbols given")
        return 1
    out_dir = Path(args.out) if args.out else Path(args.src) / "funding_rates"
    total_new = 0
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for i, sym in enumerate(dict.fromkeys(syms), start=1):
            print(f"[{i}/{len(syms)}] {sym}")
            try:
                _, n_new = fetch_symbol(sym, Path(args.src), out_dir, client=client)
                total_new += n_new
            except Exception as e:  # noqa: BLE001 — keep going; report at the end
                print(f"  ! {sym}: {e!r}")
    print(f"done: +{total_new} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
