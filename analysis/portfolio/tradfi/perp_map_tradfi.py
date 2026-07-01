"""Task A — SECTOR_MAP stem -> live Binance TradFi-perp symbol resolver.

The iter-016 book is priced/validated on Yahoo underlying total-return bars stored under
``data/<KEY>/1d.csv`` where ``<KEY>`` is the ``universe_tradfi.SECTOR_MAP`` key (e.g. ``AAPLUSDT``).
The desk FILLS on Binance single-stock ``TRADIFI_PERPETUAL`` perps. This module resolves each
SECTOR_MAP key to its LIVE perp ``symbol`` EMPIRICALLY (do NOT assume ``<STEM>USDT``) by querying
``/fapi/v1/exchangeInfo`` and matching on the contract's ``baseAsset`` (= ``stem(KEY)``).

Empirically (2026-07-01, live exchangeInfo): all 69 SECTOR_MAP keys resolve, and the live perp
``symbol`` equals the key in every case (``stem(KEY) == baseAsset``). The identity holds because the
Yahoo store was already named with Binance's perp convention (incl. Binance-specific tickers such as
``PAYP`` for PayPal, ``BRKB`` for Berkshire-B, ``V`` for Visa). Recent-IPO names with no live perp
would appear in the UNMAPPED list — currently none.

``perp_symbol_map()`` LIVE-resolves (authoritative). ``PERP_SYMBOL_MAP`` is a committed static
snapshot fallback so downstream code (ingest, reconcile, the paper engine) is deterministic even
without network. On a live-resolve network error ``perp_symbol_map`` warns and returns the snapshot.

Run:  uv run python analysis/portfolio/tradfi/perp_map_tradfi.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import universe_tradfi as ut  # noqa: E402

FAPI_BASE = "https://fapi.binance.com"
EXCHANGE_INFO = "/fapi/v1/exchangeInfo"
TRADIFI = "TRADIFI_PERPETUAL"

# --- committed static snapshot (resolved 2026-07-01 against live exchangeInfo) ------------------
# Downstream fallback so ingest/reconcile stay deterministic offline. Live-resolve is authoritative.
PERP_SYMBOL_MAP: dict[str, str] = {
    "AAPLUSDT": "AAPLUSDT",
    "ADBEUSDT": "ADBEUSDT",
    "ALABUSDT": "ALABUSDT",
    "AMATUSDT": "AMATUSDT",
    "AMDUSDT": "AMDUSDT",
    "AMZNUSDT": "AMZNUSDT",
    "ARMUSDT": "ARMUSDT",
    "ASMLUSDT": "ASMLUSDT",
    "ASTSUSDT": "ASTSUSDT",
    "AVGOUSDT": "AVGOUSDT",
    "BABAUSDT": "BABAUSDT",
    "BRKBUSDT": "BRKBUSDT",
    "CIENUSDT": "CIENUSDT",
    "COHRUSDT": "COHRUSDT",
    "COINUSDT": "COINUSDT",
    "COSTUSDT": "COSTUSDT",
    "CRCLUSDT": "CRCLUSDT",
    "CRDOUSDT": "CRDOUSDT",
    "CRMUSDT": "CRMUSDT",
    "CRWDUSDT": "CRWDUSDT",
    "CRWVUSDT": "CRWVUSDT",
    "CSCOUSDT": "CSCOUSDT",
    "DELLUSDT": "DELLUSDT",
    "DISUSDT": "DISUSDT",
    "DKNGUSDT": "DKNGUSDT",
    "EBAYUSDT": "EBAYUSDT",
    "FLNCUSDT": "FLNCUSDT",
    "GLWUSDT": "GLWUSDT",
    "GMEUSDT": "GMEUSDT",
    "GOOGLUSDT": "GOOGLUSDT",
    "HDUSDT": "HDUSDT",
    "HIMSUSDT": "HIMSUSDT",
    "HOODUSDT": "HOODUSDT",
    "HPEUSDT": "HPEUSDT",
    "IBMUSDT": "IBMUSDT",
    "INTCUSDT": "INTCUSDT",
    "IRENUSDT": "IRENUSDT",
    "JPMUSDT": "JPMUSDT",
    "KLACUSDT": "KLACUSDT",
    "LITEUSDT": "LITEUSDT",
    "LLYUSDT": "LLYUSDT",
    "LRCXUSDT": "LRCXUSDT",
    "METAUSDT": "METAUSDT",
    "MRVLUSDT": "MRVLUSDT",
    "MSFTUSDT": "MSFTUSDT",
    "MSTRUSDT": "MSTRUSDT",
    "MUUSDT": "MUUSDT",
    "NBISUSDT": "NBISUSDT",
    "NFLXUSDT": "NFLXUSDT",
    "NOKUSDT": "NOKUSDT",
    "NOWUSDT": "NOWUSDT",
    "NVDAUSDT": "NVDAUSDT",
    "NVOUSDT": "NVOUSDT",
    "ORCLUSDT": "ORCLUSDT",
    "PAYPUSDT": "PAYPUSDT",
    "PLTRUSDT": "PLTRUSDT",
    "QCOMUSDT": "QCOMUSDT",
    "RIVNUSDT": "RIVNUSDT",
    "RKLBUSDT": "RKLBUSDT",
    "SMCIUSDT": "SMCIUSDT",
    "SNDKUSDT": "SNDKUSDT",
    "SONYUSDT": "SONYUSDT",
    "TSLAUSDT": "TSLAUSDT",
    "TSMUSDT": "TSMUSDT",
    "UBERUSDT": "UBERUSDT",
    "VUSDT": "VUSDT",
    "WDCUSDT": "WDCUSDT",
    "WMTUSDT": "WMTUSDT",
    "ZMUSDT": "ZMUSDT",
}


def _fetch_tradfi_contracts(base_url: str = FAPI_BASE) -> dict[str, dict]:
    """Return ``{symbol: contract}`` for every live ``TRADIFI_PERPETUAL`` on exchangeInfo."""
    with httpx.Client(base_url=base_url, timeout=30.0) as http:
        r = http.get(EXCHANGE_INFO)
        r.raise_for_status()
        info = r.json()
    return {s["symbol"]: s for s in info.get("symbols", []) if s.get("contractType") == TRADIFI}


def resolve_perp_map(contracts: dict[str, dict]) -> tuple[dict[str, str], list[str]]:
    """Match each SECTOR_MAP key to a live perp symbol; return ``(mapping, unmapped_keys)``.

    Match order (empirical, NOT ``<STEM>USDT`` assumption): (1) exact ``symbol`` hit, then
    (2) ``stem(KEY) == baseAsset``. A key with neither is UNMAPPED (recent IPO not yet listed).
    """
    by_symbol = contracts
    by_base = {c["baseAsset"]: c for c in contracts.values()}
    mapping: dict[str, str] = {}
    unmapped: list[str] = []
    for key in sorted(ut.SECTOR_MAP):
        st = ut.stem(key)
        if key in by_symbol:
            mapping[key] = by_symbol[key]["symbol"]
        elif st in by_base:
            mapping[key] = by_base[st]["symbol"]
        else:
            unmapped.append(key)
    return mapping, unmapped


def perp_symbol_map(
    data_dir: str | None = None, *, live: bool = True, base_url: str = FAPI_BASE
) -> dict[str, str]:
    """Return ``{SECTOR_MAP key: live perp symbol}`` (authoritative live-resolve).

    ``data_dir`` is accepted for call-site symmetry with the other tradfi helpers; resolution is
    exchangeInfo-driven and does not read local data. With ``live=False`` (or on a network error)
    the committed ``PERP_SYMBOL_MAP`` snapshot is returned so the call is deterministic offline.
    """
    _ = data_dir  # resolution is exchangeInfo-driven; kept for signature symmetry
    if not live:
        return dict(PERP_SYMBOL_MAP)
    try:
        contracts = _fetch_tradfi_contracts(base_url)
    except (httpx.HTTPError, OSError) as exc:  # pragma: no cover — network-dependent
        print(f"  ! perp_symbol_map live-resolve failed ({exc!r}) — using static snapshot")
        return dict(PERP_SYMBOL_MAP)
    mapping, _unmapped = resolve_perp_map(contracts)
    return mapping


def main() -> None:
    try:
        contracts = _fetch_tradfi_contracts()
    except (httpx.HTTPError, OSError) as exc:  # pragma: no cover
        print(
            f"live exchangeInfo unavailable ({exc!r}); using static snapshot "
            f"({len(PERP_SYMBOL_MAP)} names)"
        )
        for key, sym in sorted(PERP_SYMBOL_MAP.items()):
            print(f"  {key:12} -> {sym}")
        return
    mapping, unmapped = resolve_perp_map(contracts)
    print("=" * 88)
    print(
        f"TradFi perp map — {len(mapping)}/{len(ut.SECTOR_MAP)} SECTOR_MAP keys resolved to a "
        "live TRADIFI_PERPETUAL"
    )
    print("=" * 88)
    for key, sym in sorted(mapping.items()):
        c = contracts[sym]
        ob = datetime.fromtimestamp(c["onboardDate"] / 1000, tz=UTC).date()
        flag = "" if key == sym else "   <-- symbol != key"
        print(
            f"  {key:12} -> {sym:12} base={c['baseAsset']:9} onboard={ob} "
            f"status={c['status']}{flag}"
        )
    print(f"\n  UNMAPPED (no live perp — recent IPO?): {unmapped or 'NONE'}")
    # snapshot drift guard
    drift = {k: v for k, v in mapping.items() if PERP_SYMBOL_MAP.get(k) != v}
    new_keys = sorted(set(mapping) - set(PERP_SYMBOL_MAP))
    if drift or new_keys:
        print(f"  ! SNAPSHOT DRIFT vs PERP_SYMBOL_MAP: changed={drift} new={new_keys}")
    else:
        print("  static PERP_SYMBOL_MAP snapshot matches live resolve (no drift)")


if __name__ == "__main__":
    main()
