"""Symbol discovery from Binance exchange info and data.binance.vision S3 bucket."""

from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

S3_BUCKET_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
S3_PREFIX = "data/futures/um/monthly/klines/"
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


@dataclass(frozen=True)
class SymbolInfo:
    """A discovered symbol with its status."""

    symbol: str
    status: str  # "TRADING", "DELISTED", "UNKNOWN"


def discover_from_exchange_info(base_url: str, http: httpx.Client) -> list[SymbolInfo]:
    """Discover active perpetual symbols from Binance exchange info API."""
    resp = http.get(f"{base_url}/fapi/v1/exchangeInfo")
    resp.raise_for_status()
    data = resp.json()
    symbols = []
    for s in data.get("symbols", []):
        if s.get("contractType") == "PERPETUAL":
            symbols.append(SymbolInfo(symbol=s["symbol"], status=s.get("status", "UNKNOWN")))
    return symbols


def discover_from_data_vision(http: httpx.Client) -> list[str]:
    """Discover all symbols available on data.binance.vision (including delisted).

    Paginates the S3 bucket listing using the marker parameter.
    """
    symbols: list[str] = []
    marker = ""

    while True:
        params: dict[str, str] = {
            "prefix": S3_PREFIX,
            "delimiter": "/",
        }
        if marker:
            params["marker"] = marker

        resp = http.get(S3_BUCKET_URL, params=params)
        resp.raise_for_status()

        root = ElementTree.fromstring(resp.text)

        for prefix_elem in root.findall(".//s3:CommonPrefixes/s3:Prefix", S3_NS):
            prefix_text = prefix_elem.text or ""
            # prefix looks like "data/futures/um/monthly/klines/BTCUSDT/"
            parts = prefix_text.rstrip("/").split("/")
            if parts:
                symbols.append(parts[-1])

        # Check if there are more results
        is_truncated = root.findtext("s3:IsTruncated", namespaces=S3_NS)
        if is_truncated != "true":
            break

        # Get the last prefix as the next marker
        next_marker = root.findtext("s3:NextMarker", namespaces=S3_NS)
        if next_marker:
            marker = next_marker
        elif symbols:
            marker = S3_PREFIX + symbols[-1] + "/"
        else:
            break

    return symbols


def merge_symbols(api_symbols: list[SymbolInfo], vision_symbols: list[str]) -> list[SymbolInfo]:
    """Merge symbols from API and data.binance.vision, tagging status."""
    api_map = {s.symbol: s.status for s in api_symbols}
    result: dict[str, SymbolInfo] = {}

    for s in api_symbols:
        result[s.symbol] = s

    for sym in vision_symbols:
        if sym not in result:
            status = api_map.get(sym, "DELISTED")
            result[sym] = SymbolInfo(symbol=sym, status=status)

    return sorted(result.values(), key=lambda s: s.symbol)
