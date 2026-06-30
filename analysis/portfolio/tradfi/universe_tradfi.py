"""TradFi-portfolio universe — Binance exchangeInfo-derived single-company stock perps.

The universe is NOT hard-coded: it is re-derived from Binance USDⓈ-M exchangeInfo by
keeping every contractType == "TRADIFI_PERPETUAL" symbol that is a single-company common
stock (or single-company US-listed ADR), dropping ETFs/indices, commodities, the four
metals (owned by the portfolio-metals track) and pre-IPO synthetics. Point-in-time
membership + ragged starts are handled downstream (a name carries weight only once it has
Dukascopy history).
"""

from __future__ import annotations

# Bare stems (symbol without the trailing USDT). Maintained by hand as Binance lists more.
EXCLUDE_ETF: frozenset[str] = frozenset(
    {
        "SPY",
        "QQQ",
        "IWM",
        "TQQQ",
        "SQQQ",
        "SOXL",
        "UVXY",
        "XLE",
        "EWJ",
        "EWY",
        "EWZ",
        "EWT",
        "URNM",
        "KORU",
        "STXX",
    }
)
EXCLUDE_COMMODITY: frozenset[str] = frozenset({"NATGAS", "CL", "BZ", "COPPER"})
EXCLUDE_METAL: frozenset[str] = frozenset({"XAU", "XAG", "XPT", "XPD"})
EXCLUDE_PRIVATE: frozenset[str] = frozenset({"ANTHROPIC", "OPENAI"})
_EXCLUDE_ALL = EXCLUDE_ETF | EXCLUDE_COMMODITY | EXCLUDE_METAL | EXCLUDE_PRIVATE

# Hard-coded stock -> sector map (user directive 2026-06-30: hard-code for now).
# Sectors: Tech, Semi, Comm, ConsDisc, ConsStap, Fin, Health, Indust, Energy, Crypto.
SECTOR_MAP: dict[str, str] = {
    "AAPLUSDT": "Tech",
    "MSFTUSDT": "Tech",
    "GOOGLUSDT": "Comm",
    "METAUSDT": "Comm",
    "AMZNUSDT": "ConsDisc",
    "TSLAUSDT": "ConsDisc",
    "NVDAUSDT": "Semi",
    "AMDUSDT": "Semi",
    "AVGOUSDT": "Semi",
    "MRVLUSDT": "Semi",
    "QCOMUSDT": "Semi",
    "TSMUSDT": "Semi",
    "ASMLUSDT": "Semi",
    "ARMUSDT": "Semi",
    "LRCXUSDT": "Semi",
    "KLACUSDT": "Semi",
    "AMATUSDT": "Semi",
    "MUUSDT": "Semi",
    "INTCUSDT": "Semi",
    "ORCLUSDT": "Tech",
    "CRMUSDT": "Tech",
    "ADBEUSDT": "Tech",
    "NOWUSDT": "Tech",
    "IBMUSDT": "Tech",
    "CSCOUSDT": "Tech",
    "PLTRUSDT": "Tech",
    "CRWDUSDT": "Tech",
    "DELLUSDT": "Tech",
    "NFLXUSDT": "Comm",
    "DISUSDT": "Comm",
    "ZMUSDT": "Tech",
    "JPMUSDT": "Fin",
    "VUSDT": "Fin",
    "BRKBUSDT": "Fin",
    "COINUSDT": "Crypto",
    "HOODUSDT": "Fin",
    "MSTRUSDT": "Crypto",
    "PAYPUSDT": "Fin",
    "WMTUSDT": "ConsStap",
    "COSTUSDT": "ConsStap",
    "HDUSDT": "ConsDisc",
    "EBAYUSDT": "ConsDisc",
    "BABAUSDT": "ConsDisc",
    "UBERUSDT": "Tech",
    "DKNGUSDT": "ConsDisc",
    "GMEUSDT": "ConsDisc",
    "RIVNUSDT": "ConsDisc",
    "NVOUSDT": "Health",
    "LLYUSDT": "Health",
    "HIMSUSDT": "Health",
    "SONYUSDT": "ConsDisc",
    "NOKUSDT": "Tech",
    "CRCLUSDT": "Crypto",
    "CRWVUSDT": "Tech",
    "NBISUSDT": "Tech",
    "IRENUSDT": "Crypto",
    "RKLBUSDT": "Indust",
    "ASTSUSDT": "Comm",
    "SMCIUSDT": "Tech",
    "WDCUSDT": "Semi",
    "SNDKUSDT": "Semi",
    "COHRUSDT": "Semi",
    "GLWUSDT": "Tech",
    "CIENUSDT": "Tech",
    "CRDOUSDT": "Semi",
    "ALABUSDT": "Semi",
    "HPEUSDT": "Tech",
    "LITEUSDT": "Semi",
    "FLNCUSDT": "Indust",
}


def stem(symbol: str) -> str:
    """Strip the trailing USDT quote from a perp symbol (AAPLUSDT -> AAPL)."""
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def classify_tradfi_stocks(exchange_info: dict) -> list[str]:
    """Return the sorted single-company-stock universe from a Binance exchangeInfo dict.

    Keeps `contractType == "TRADIFI_PERPETUAL"` USDT symbols, drops the maintained
    ETF / commodity / metal / private exclude sets. Unknown new stems are KEPT (fail-open:
    a newly-listed stock joins the universe; review the exclude sets when Binance adds ETFs).
    """
    out = []
    for s in exchange_info.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "TRADIFI_PERPETUAL":
            continue
        if not sym.endswith("USDT"):
            continue
        if stem(sym) in _EXCLUDE_ALL:
            continue
        out.append(sym)
    return sorted(out)
