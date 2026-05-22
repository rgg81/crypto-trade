"""iter-v3/104 — fetch on-chain network-activity data for the v3 universe.

NEW EDGE SOURCE for iter-v3/104: on-chain network activity (a genuinely
non-price-derived information layer; funding/OI/basis are CLOSED for v3).

Data source — CoinMetrics Community API (free, no auth, no key):
    https://community-api.coinmetrics.io/v4/timeseries/asset-metrics

Feasibility (probed 2026-05-19): the free tier delivers exactly two metrics
universe-wide at daily frequency — AdrActCnt (active addresses) and TxCnt
(transaction count) — for btc, trx, bch (AND ldo), gap-free across the full
IS window 2023-03-24..2025-03-24 (732 daily rows). Exchange-flow / supply-
cohort metrics (FlowInExUSD, TxTfrValAdjUSD, SplyAdrBalUSD1M, ...) are GATED
behind paid credentials and return `forbidden` — NOT usable. Liquidation
snapshots (`data.binance.vision .../liquidationSnapshot/`) were probed and
are EMPTY — Binance removed the archive; `/fapi/v1/allForceOrders` returns
HTTP 400 (deprecated). On-chain network-activity is the feasible new source.

LDO is an ERC-20 governance token (Lido) — `ldo` DOES return AdrActCnt/TxCnt
on the free tier, but those count Lido-token-contract interactions, a far
thinner and more idiosyncratic series than a base-layer chain. The v3
hypothesis therefore uses BTC's on-chain network-activity as a CROSS-ASSET
REGIME BROADCAST (the entire altcoin book — BCH+LDO+TRX — is BTC-regime
driven; see `references/crypto-edge-deep.md` "BTC dominance" / on-chain
regime), and additionally each symbol's own base chain where it has one
(bch = Bitcoin Cash L1, trx = Tron L1). LDO has no own L1 — it inherits the
BTC cross-asset broadcast only.

LOOK-AHEAD DISCIPLINE (the load-bearing design choice):
    A daily on-chain metric for UTC day D aggregates all blocks in day D.
    It is only KNOWABLE after day D closes (24:00 UTC). The 8h candle whose
    open_time is the FIRST candle of day D+1 (08:00 UTC D+1 in the 00/08/16
    grid — the candle that opens strictly after D's 24:00 close) is the
    earliest 8h bar at which day D's metric is in the information set.
    This script writes the RAW daily series only; the EDA script
    (`onchain_is_eda.py`) performs the as-of merge with an explicit +1-day
    publication lag, so NO future on-chain information can enter a feature.

Output: data/onchain/<asset>_daily.csv  (schema: date, AdrActCnt, TxCnt)
    where <asset> in {btc, bch, trx}. Idempotent — re-running overwrites.

This is QR analysis tooling (Phases 1-5). It writes ONLY to data/onchain/;
it does NOT touch src/. The production feature module is the QE's Phase-6
job if the brief is GO.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx
import pandas as pd

CM_BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
# IS-only window. OOS_CUTOFF_DATE = 2025-03-24. We fetch a generous lead-in
# (2018-01-01) so rolling-window features have full warm-up inside the IS
# panel; the EDA hard-masks open_time < OOS_CUTOFF_MS regardless.
START = "2018-01-01"
END = "2025-03-24"  # == OOS_CUTOFF_DATE; daily series are inclusive of this day
ASSETS = ["btc", "bch", "trx"]
METRICS = "AdrActCnt,TxCnt"
OUT_DIR = Path("data/onchain")


def fetch_asset(client: httpx.Client, asset: str) -> pd.DataFrame:
    """Fetch the full daily AdrActCnt+TxCnt series for one asset, paginating."""
    rows: list[dict] = []
    params = {
        "assets": asset,
        "metrics": METRICS,
        "start_time": START,
        "end_time": END,
        "frequency": "1d",
        "page_size": "10000",
    }
    url = CM_BASE
    page = 0
    while True:
        resp = client.get(url, params=params if page == 0 else None, timeout=60.0)
        resp.raise_for_status()
        payload = resp.json()
        if "error" in payload:
            raise RuntimeError(f"{asset}: API error {payload['error']}")
        rows.extend(payload.get("data", []))
        nxt = payload.get("next_page_url")
        if not nxt:
            break
        url = nxt
        page += 1
        time.sleep(0.2)
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"{asset}: zero rows returned")
    df["date"] = pd.to_datetime(df["time"]).dt.tz_localize(None).dt.normalize()
    keep = ["date"]
    for m in ("AdrActCnt", "TxCnt"):
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce")
            keep.append(m)
    df = df[keep].sort_values("date").reset_index(drop=True)
    return df


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client() as client:
        for asset in ASSETS:
            df = fetch_asset(client, asset)
            out = OUT_DIR / f"{asset}_daily.csv"
            df.to_csv(out, index=False)
            na = df["AdrActCnt"].isna().sum() if "AdrActCnt" in df else "n/a"
            nt = df["TxCnt"].isna().sum() if "TxCnt" in df else "n/a"
            print(
                f"[{asset}] {len(df)} daily rows "
                f"{df['date'].min().date()}..{df['date'].max().date()} "
                f"-> {out}  (NaN: AdrActCnt={na} TxCnt={nt})"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
