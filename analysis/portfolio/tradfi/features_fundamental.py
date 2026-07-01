"""Cross-sectional, sector-neutral VALUE + QUALITY factors from PIT SEC-EDGAR fundamentals.

Built strictly from point-in-time fundamentals (ingest_edgar.build_fundamental_panels, which carries
for each trading day t only facts with `filed` <= t) plus the current close (price is PIT-trivial —
close[t] is known at close[t]). Every factor is turned into a raw weight book the same leak-safe way
the momentum sleeves are: cross-sectional z-score (past/known-only), then per-sector demean so the
book is dollar- and sector-neutral. Downstream the probe runs each raw book through the SAME
`core_tradfi.net_from_raw` / hysteresis-band machinery as the momentum book, so the resulting net
Sharpe is directly comparable.

Factors (all leak-safe; NaN where the fundamental is unknown -> 0 weight):
  VALUE
    book_to_price     = PIT book equity / market cap, mcap = PIT shares * close[t]   (long cheap)
    earnings_to_price = PIT annual net income / market cap                           (long cheap)
  QUALITY
    gross_profitability = PIT gross profit / PIT assets  (Novy-Marx 2013)            (long high)
    roe                 = PIT net income / PIT book equity                           (long high)

Sign convention: a HIGHER factor value == a MORE attractive name == a LONGER position. book-to-price
and earnings-to-price are high for cheap names; gross-profitability and ROE are high for quality
names. Sector-neutralization removes the sector bet (a cross-sectional value/quality book, not a
sector-tilt book) — matching the momentum sleeves so the sleeves compose cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import universe_tradfi as ut  # noqa: E402
from ingest_edgar import build_fundamental_panels  # noqa: E402

Z_CLIP = 3.0  # winsorize the cross-sectional z-score to +/- 3 sigma (tame single-name blow-ups)


def xs_zscore(factor: pd.DataFrame, clip: float = Z_CLIP) -> pd.DataFrame:
    """Row-wise (cross-sectional) z-score, clipped to +/- `clip`. NaNs stay NaN (unknown -> no bet).

    Standardising ACROSS names each day (not through time) is past-only: it uses only values known
    at t. A name with an unknown fundamental (NaN) is excluded from the day's mean/std, stays NaN.
    """
    mu = factor.mean(axis=1)
    sd = factor.std(axis=1).replace(0, np.nan)
    z = factor.sub(mu, axis=0).div(sd, axis=0)
    return z.clip(-clip, clip)


def sector_neutral_raw(
    factor: pd.DataFrame, sector_map: dict[str, str] | None = None
) -> pd.DataFrame:
    """factor -> cross-sectional z-score -> per-sector demean (dollar- + sector-neutral raw book).

    A name with an UNKNOWN fundamental (NaN — foreign ADR, or pre-first-filing) takes EXACTLY 0
    weight (the required point-in-time behavior): it is excluded from its sector's mean and never
    given a balancing position. Each sector is demeaned over its KNOWN members only, so the sector
    still nets to ~0 dollars. Singleton-known sectors demean to 0 (safe default — no lone-name bet).
    """
    sm = sector_map if sector_map is not None else ut.SECTOR_MAP
    z = xs_zscore(factor)  # NaN where the fundamental is unknown
    out = pd.DataFrame(0.0, index=z.index, columns=z.columns)
    sectors: dict[str, list[str]] = {}
    for c in z.columns:
        sectors.setdefault(sm.get(c, f"__{c}"), []).append(c)
    for cols in sectors.values():
        block = z[cols]
        demeaned = block.sub(block.mean(axis=1), axis=0)  # skipna mean over known members only
        out[cols] = demeaned.fillna(0.0)  # unknown members -> 0 weight
    return out


# ---------------------------------------------------------------- raw factor levels --------------
def market_cap(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """PIT market cap = PIT shares-outstanding * close[t] (both known at close[t])."""
    shares = panels["shares"].reindex(index=close.index, columns=close.columns)
    return shares * close


def book_to_price(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """VALUE level: PIT book equity / PIT market cap. High == cheap. Non-positive book -> NaN."""
    book = panels["book_equity"].reindex(index=close.index, columns=close.columns)
    mcap = market_cap(panels, close).replace(0, np.nan)
    bp = book / mcap
    return bp.where(book > 0)  # negative-book (distressed) names carry no value signal


def earnings_to_price(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """VALUE level: PIT annual net income / PIT market cap. High == cheap earnings yield."""
    ni = panels["net_income"].reindex(index=close.index, columns=close.columns)
    mcap = market_cap(panels, close).replace(0, np.nan)
    return ni / mcap


def gross_profitability(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """QUALITY level: PIT gross profit / PIT assets (Novy-Marx 2013). High == profitable."""
    gp = panels["gross_profit"].reindex(index=close.index, columns=close.columns)
    assets = panels["assets"].reindex(index=close.index, columns=close.columns).replace(0, np.nan)
    return (gp / assets).where(assets > 0)


def roe(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """QUALITY level: PIT net income / PIT book equity. High == high return on equity."""
    ni = panels["net_income"].reindex(index=close.index, columns=close.columns)
    book = panels["book_equity"].reindex(index=close.index, columns=close.columns)
    return (ni / book).where(book > 0)


# ---------------------------------------------------------------- factor raw books ---------------
def value_raw(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """Sector-neutral z-scored VALUE raw book (book-to-price; long cheap)."""
    return sector_neutral_raw(book_to_price(panels, close))


def quality_raw(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """Sector-neutral z-scored QUALITY raw book (gross-profitability; long high)."""
    return sector_neutral_raw(gross_profitability(panels, close))


def earnings_yield_raw(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """Sector-neutral z-scored earnings-to-price raw book (secondary VALUE)."""
    return sector_neutral_raw(earnings_to_price(panels, close))


def roe_raw(panels: dict[str, pd.DataFrame], close: pd.DataFrame) -> pd.DataFrame:
    """Sector-neutral z-scored ROE raw book (secondary QUALITY)."""
    return sector_neutral_raw(roe(panels, close))


def load_panels(close: pd.DataFrame, cache_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Convenience: build PIT fundamental panels aligned to a price panel's (index, columns)."""
    return build_fundamental_panels(list(close.columns), close.index, cache_dir=cache_dir)


def coverage(panels: dict[str, pd.DataFrame], oos_cutoff: pd.Timestamp) -> dict[str, int]:
    """IS-window count of names with >=1 known observation per concept (leak-safe diagnostic)."""
    out: dict[str, int] = {}
    for k, df in panels.items():
        is_df = df[df.index < oos_cutoff]
        out[k] = int((is_df.notna().any(axis=0)).sum())
    return out
