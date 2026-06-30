from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TRADFI = _ROOT / "analysis" / "portfolio" / "tradfi"
sys.path.insert(0, str(_TRADFI))

import universe_tradfi as ut  # noqa: E402


def _exinfo(symbols_types):
    """Minimal exchangeInfo dict: symbols_types = [(symbol, contractType), ...]."""
    return {"symbols": [{"symbol": s, "contractType": ct} for s, ct in symbols_types]}


def test_classify_keeps_single_company_stocks():
    info = _exinfo(
        [
            ("AAPLUSDT", "TRADIFI_PERPETUAL"),
            ("JPMUSDT", "TRADIFI_PERPETUAL"),
            ("BTCUSDT", "PERPETUAL"),  # crypto -> drop (not TRADIFI)
            ("SPYUSDT", "TRADIFI_PERPETUAL"),  # ETF -> drop
            ("XAUUSDT", "TRADIFI_PERPETUAL"),  # metal -> drop
            ("NATGASUSDT", "TRADIFI_PERPETUAL"),  # commodity -> drop
            ("OPENAIUSDT", "TRADIFI_PERPETUAL"),  # private synthetic -> drop
        ]
    )
    out = ut.classify_tradfi_stocks(info)
    assert out == ["AAPLUSDT", "JPMUSDT"]


def test_every_known_stock_has_a_sector():
    # Spot-check core names are mapped; SECTOR_MAP must cover its own keys.
    for sym in ("AAPLUSDT", "JPMUSDT", "TSLAUSDT", "AMZNUSDT", "NVDAUSDT"):
        assert sym in ut.SECTOR_MAP, f"{sym} missing from SECTOR_MAP"
    assert all(isinstance(v, str) and v for v in ut.SECTOR_MAP.values())
