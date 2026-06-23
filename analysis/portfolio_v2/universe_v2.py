"""universe_v2 — survivorship-safe pool loaders + point-in-time eligibility.

Two pools:
  - load_pool_v1compat() : EXACTLY v1's iter_002.load_universe (lifetime >= MIN_HISTORY filter,
    2026 on-disk snapshot). Used ONLY for the parity gate + reproducing the v1 numbers.
  - load_pool_pit()      : the survivorship-safe pool — every ex-stable USDT perp incl. delisted,
    NO lifetime filter. A young coin simply never seasons until it has `season` trailing candles.

eligibility(coins, rank_lo, rank_hi, season) returns a past-only bool DataFrame:
  - season None/0 -> v1-compat: rank = liq.rank(desc); elig = (rank > lo) & (rank <= hi).
    With lo=0, hi=20 this is iter_002's `rank <= TOP_N` bit-for-bit.
  - season set    -> PIT: a coin must have >= season trailing non-NaN closes strictly before t to
    enter the rank denominator at all; un-seasoned coins get NaN rank and are excluded from BOTH
    the traded set and the denominator (a young coin cannot steal a slot pre-signal).

All liquidity / seasoning state is .shift(1) lagged -> strictly past-only.
"""

from __future__ import annotations

import glob
import re

import pandas as pd

# ---- v1 constants (must match for parity) --------------------------------------------------
HORIZONS = [21, 42, 84, 168]
VOL_WIN = 84
LIQ_WIN = 90
MIN_HISTORY = 2190  # ~2y of 8h candles — v1's established-coin lifetime filter
TOP_N = 20
STABLE = re.compile(r"(USDC|BUSD|FDUSD|TUSD|USD1|DAI|USDP|EUR|USTC|FRAX|PAXG|XUSD|USDE)")

# Non-COIN perps to EXCLUDE from the crypto universe (Binance `underlyingType != COIN`:
# tokenized stocks/EQUITY, COMMODITY, INDEX baskets, PREMARKET/pre-IPO). A crypto cross-sectional
# momentum strategy must not trade these — different dynamics, TradFi agreements, and they polluted
# the rank-21-40 pool (INTC/CRCL were top OOS positions; BTCDOM/DEFI indices throughout). Applied to
# load_pool_pit ONLY (load_pool_v1compat keeps the iter_002 universe for the v1 parity gate).
# Regenerate from exchangeInfo (underlyingType) when the listing set changes — see scripts note.
NON_COIN_PERPS = frozenset({
    "0GUSDT", "ALLUSDT", "AMZNUSDT", "AZTECUSDT", "BLUEBIRDUSDT", "BMNRUSDT", "BREVUSDT",
    "BTCDOMUSDT", "CCUSDT", "COINUSDT", "COPPERUSDT", "CRCLUSDT", "DEFIUSDT", "EDGEUSDT",
    "EPICUSDT", "ESPUSDT", "EWJUSDT", "FAKEKR000660USDT", "FOGOUSDT", "GOOGLUSDT", "HOODUSDT",
    "INTCUSDT", "KATUSDT", "KITEUSDT", "MEGAUSDT", "METAUSDT", "METUSDT", "MONUSDT",
    "MSTRUSDT", "NVDAUSDT", "OPENAIUSDT", "PAYPUSDT", "PLTRUSDT", "QNTXUSDT", "QQQUSDT",
    "SENTUSDT", "SPACEFUSDT", "SPCXUSDT", "SPYUSDT", "STABLEUSDT", "TSLAUSDT", "XAGUSDT",
    "XAUUSDT", "XPDUSDT", "XPTUSDT", "YBUSDT", "ZAMAUSDT",
})

# Data root for this worktree: pf_data/ (data/ is sparse here).
DATA_GLOB = "pf_data/*USDT/8h.csv"


def _sym_from_path(p: str) -> str:
    # pf_data/<SYM>/8h.csv -> <SYM>
    return p.replace("\\", "/").split("/")[-2]


def load_pool_v1compat() -> dict:
    """EXACTLY v1's iter_002.load_universe, reading from pf_data/ instead of data/.

    glob ex-stable ascii USDT perps, drop coins with total length < MIN_HISTORY, dedup open_time,
    set ms open_time index sorted. This is the survivorship-INFLATED v1 snapshot — used only to
    reproduce the v1 numbers and to anchor the parity gate.
    """
    coins: dict = {}
    for p in sorted(glob.glob(DATA_GLOB)):
        sym = _sym_from_path(p)
        if not sym.endswith("USDT") or STABLE.search(sym) or not sym.isascii():
            continue
        try:
            k = pd.read_csv(p, usecols=["open_time", "open", "close", "quote_volume"])
        except Exception:
            continue
        if len(k) < MIN_HISTORY:
            continue
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def load_pool_pit() -> dict:
    """Survivorship-safe pool: every ex-stable ascii USDT perp incl. delisted, NO lifetime filter.

    A coin with < season history just never becomes eligible (handled in eligibility()); a delisted
    coin keeps its full on-disk history through its terminal candle (post-delist cells become NaN
    after the panel reindex -> ineligible -> the position closes at the last available price).
    """
    coins: dict = {}
    for p in sorted(glob.glob(DATA_GLOB)):
        sym = _sym_from_path(p)
        if (
            not sym.endswith("USDT")
            or STABLE.search(sym)
            or not sym.isascii()
            or sym in NON_COIN_PERPS  # exclude tokenized stocks / commodities / indices / pre-market
        ):
            continue
        try:
            k = pd.read_csv(p, usecols=["open_time", "open", "close", "quote_volume"])
        except Exception:
            continue
        # NO MIN_HISTORY filter — the whole point of the survivorship fix.
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def _panel(coins: dict, col: str) -> pd.DataFrame:
    """Build a datetime-indexed wide panel of `col` across coins, aligned to the union open grid.

    The grid + alignment mirror iter_002/iter_020 exactly: union of all open_time stamps, sorted,
    reindexed per coin, ms -> datetime. Missing cells (young/delisted) stay NaN (no fill).
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    out = pd.DataFrame({s: d[col] for s, d in coins.items()}).astype(float)
    out = out.reindex(opens.index)
    out.index = pd.to_datetime(opens.index, unit="ms")
    # preserve a stable column order (insertion order of the coins dict, as v1 does)
    return out[list(coins.keys())]


def eligibility(
    coins: dict,
    rank_lo: float,
    rank_hi: float,
    season: int | None,
    liq_win: int = LIQ_WIN,
) -> pd.DataFrame:
    """Past-only eligibility bool DataFrame for the rank band (rank_lo, rank_hi].

    liq = qv.rolling(liq_win).mean().shift(1)  — trailing $-volume known as of the prior candle.
    `liq_win` defaults to the v1 parity constant LIQ_WIN=90; it is overridable ONLY so the fast unit
    tests can exercise short synthetic panels. All production / parity calls use the default.

    season None/0  -> v1-compat:
        rank = liq.rank(axis=1, ascending=False)
        elig = (rank > rank_lo) & (rank <= rank_hi)
      (rank_lo=0, rank_hi=TOP_N reproduces iter_002's `rank <= TOP_N` bit-for-bit.)

    season set     -> PIT:
        seasoned = close.notna().shift(1).rolling(season).sum() == season   (>= season trailing
                   non-NaN closes strictly before t)
        rank = liq.where(seasoned).rank(axis=1, ascending=False)
        elig = seasoned & (rank > rank_lo) & (rank <= rank_hi)
      Un-seasoned coins get NaN rank -> excluded from the denominator AND the traded set.
    """
    qv = _panel(coins, "quote_volume")
    liq = qv.rolling(liq_win).mean().shift(1)

    if not season:  # None or 0 -> v1-compat
        rank = liq.rank(axis=1, ascending=False)
        elig = (rank > rank_lo) & (rank <= rank_hi)
        return elig.fillna(False)

    close = _panel(coins, "close")
    # >= season trailing non-NaN closes STRICTLY before t (shift(1) -> past-only).
    seasoned = (close.notna().shift(1).rolling(season).sum() == season).fillna(False)
    rank = liq.where(seasoned).rank(axis=1, ascending=False)
    elig = seasoned & (rank > rank_lo) & (rank <= rank_hi)
    return elig.fillna(False)


def candidate_count_per_year(coins: dict, season: int | None, liq_win: int = LIQ_WIN) -> pd.Series:
    """Diagnostic: mean count of eligible-ranked candidates per calendar year (the rank denominator
    size before the band is applied). Under PIT this must GROW toward 2026 — a flat count would
    prove residual snapshot bias. Implemented as the count of coins with a finite seasoned rank.
    """
    qv = _panel(coins, "quote_volume")
    liq = qv.rolling(liq_win).mean().shift(1)
    if not season:
        rank = liq.rank(axis=1, ascending=False)
    else:
        close = _panel(coins, "close")
        seasoned = (close.notna().shift(1).rolling(season).sum() == season).fillna(False)
        rank = liq.where(seasoned).rank(axis=1, ascending=False)
    per_candle = rank.notna().sum(axis=1)
    return per_candle.groupby(per_candle.index.year).mean()
