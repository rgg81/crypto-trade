import httpx

from crypto_trade.discovery import (
    SymbolInfo,
    discover_from_data_vision,
    discover_from_exchange_info,
    merge_symbols,
)

EXCHANGE_INFO_RESPONSE = {
    "symbols": [
        {"symbol": "BTCUSDT", "contractType": "PERPETUAL", "status": "TRADING"},
        {"symbol": "ETHUSDT", "contractType": "PERPETUAL", "status": "TRADING"},
        {"symbol": "BTCUSDT_240329", "contractType": "CURRENT_QUARTER", "status": "TRADING"},
    ]
}

S3_XML_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/BTCUSDT/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/ETHUSDT/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/LUNAUSDT/</Prefix>
  </CommonPrefixes>
</ListBucketResult>
"""

S3_XML_PAGE1 = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>true</IsTruncated>
  <NextMarker>data/futures/um/monthly/klines/ETHUSDT/</NextMarker>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/BTCUSDT/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/ETHUSDT/</Prefix>
  </CommonPrefixes>
</ListBucketResult>
"""

S3_XML_PAGE2 = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <CommonPrefixes>
    <Prefix>data/futures/um/monthly/klines/SOLUSDT/</Prefix>
  </CommonPrefixes>
</ListBucketResult>
"""


def test_discover_from_exchange_info():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=EXCHANGE_INFO_RESPONSE)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        symbols = discover_from_exchange_info("https://fapi.binance.com", http)

    assert len(symbols) == 2
    assert symbols[0].symbol == "BTCUSDT"
    assert symbols[0].status == "TRADING"
    assert symbols[1].symbol == "ETHUSDT"


def test_discover_from_data_vision():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=S3_XML_RESPONSE)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        symbols = discover_from_data_vision(http)

    assert symbols == ["BTCUSDT", "ETHUSDT", "LUNAUSDT"]


def test_discover_from_data_vision_pagination():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, text=S3_XML_PAGE1)
        return httpx.Response(200, text=S3_XML_PAGE2)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        symbols = discover_from_data_vision(http)

    assert call_count == 2
    assert symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def test_merge_symbols():
    api_symbols = [
        SymbolInfo(symbol="BTCUSDT", status="TRADING"),
        SymbolInfo(symbol="ETHUSDT", status="TRADING"),
    ]
    vision_symbols = ["BTCUSDT", "ETHUSDT", "LUNAUSDT"]

    merged = merge_symbols(api_symbols, vision_symbols)

    assert len(merged) == 3
    symbols_dict = {s.symbol: s.status for s in merged}
    assert symbols_dict["BTCUSDT"] == "TRADING"
    assert symbols_dict["ETHUSDT"] == "TRADING"
    assert symbols_dict["LUNAUSDT"] == "DELISTED"


def test_merge_symbols_empty_api():
    merged = merge_symbols([], ["BTCUSDT", "SOLUSDT"])
    assert len(merged) == 2
    assert all(s.status == "DELISTED" for s in merged)


def test_merge_symbols_empty_vision():
    api_symbols = [SymbolInfo(symbol="BTCUSDT", status="TRADING")]
    merged = merge_symbols(api_symbols, [])
    assert len(merged) == 1
    assert merged[0].symbol == "BTCUSDT"
