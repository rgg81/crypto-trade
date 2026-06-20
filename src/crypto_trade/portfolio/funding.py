"""Incremental funding-rate refresh — the live tick must refresh funding (carry leg depends on it).

Mirrors the `fetch-funding` CLI exactly: incremental append to data/funding_rates/<SYM>.csv
(schema funding_time, funding_rate) from /fapi/v1/fundingRate. The backtest's iter_004.load_funding
reads these files, so refreshing them every tick keeps the live carry signal in parity.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx
import pandas as pd

FAPI_BASE = "https://fapi.binance.com"
ENDPOINT = "/fapi/v1/fundingRate"
DEFAULT_START_MS = 1_546_300_800_000  # 2019-01-01 UTC


def refresh_funding(symbols: list[str], data_dir: str, base_url: str = FAPI_BASE,
                    pause: float = 0.1) -> dict[str, int]:
    """Incrementally fetch funding for each symbol; append to data/funding_rates/<SYM>.csv.

    Returns {symbol: n_new_rows}. Funding is on production fapi (klines stay production too).
    """
    out_dir = Path(data_dir) / "funding_rates"
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, int] = {}
    with httpx.Client(base_url=base_url, timeout=30.0) as http:
        for symbol in symbols:
            cache_path = out_dir / f"{symbol}.csv"
            cached = pd.DataFrame(columns=["funding_time", "funding_rate"])
            start_ms = DEFAULT_START_MS
            if cache_path.exists():
                cached = pd.read_csv(cache_path)
                if len(cached) > 0:
                    start_ms = int(cached["funding_time"].max()) + 1
            rows: list[dict] = []
            current = start_ms
            while True:
                params = {"symbol": symbol, "limit": 1000, "startTime": current}
                try:
                    r = http.get(ENDPOINT, params=params)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPStatusError:
                    break  # symbol may have no funding history; skip cleanly
                if not data:
                    break
                for d in data:
                    rows.append({"funding_time": int(d["fundingTime"]),
                                 "funding_rate": float(d["fundingRate"])})
                last = int(data[-1]["fundingTime"])
                if len(data) < 1000:
                    break
                current = last + 1
                time.sleep(pause)
            new_df = pd.DataFrame(rows)
            if len(new_df) == 0:
                result[symbol] = 0
                continue
            full = pd.concat([cached, new_df], ignore_index=True)
            full = (full.drop_duplicates(subset=["funding_time"], keep="last")
                    .sort_values("funding_time").reset_index(drop=True))
            full.to_csv(cache_path, index=False)
            result[symbol] = len(new_df)
    return result
