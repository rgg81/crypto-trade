"""Tests for the SEC-EDGAR point-in-time (PIT) fundamentals pipeline (VALUE + QUALITY factors).

The load-bearing test is `test_pit_no_look_ahead*`: it PROVES that a fundamental fact never appears
in the daily series before its `filed` date — the discipline that makes these factors leak-safe.
Everything else (annual-duration filter, restatement handling, real_ticker mapping, factor
sector-neutrality + NaN->0 handling, the factor-sign economics) guards the surrounding machinery.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TRADFI = _ROOT / "analysis" / "portfolio" / "tradfi"
sys.path.insert(0, str(_TRADFI))

import features_fundamental as ff  # noqa: E402
import ingest_edgar as ie  # noqa: E402
import universe_tradfi as ut  # noqa: E402


def _facts(rows: list[tuple[str, str, float]], starts: list[str] | None = None) -> pd.DataFrame:
    """Build a facts frame from (filed, end, val) tuples (+ optional matching start dates)."""
    df = pd.DataFrame(rows, columns=["filed", "end", "val"])
    df["filed"] = pd.to_datetime(df["filed"])
    df["end"] = pd.to_datetime(df["end"])
    df["start"] = pd.to_datetime(starts) if starts is not None else pd.NaT
    return df[["filed", "end", "start", "val"]]


# ============================================================ THE PIT no-look-ahead test =========
def test_pit_no_look_ahead_synthetic():
    """A fact is absent on every trading day BEFORE its `filed` date and present on/after it."""
    # FY2022 book equity (period end 2022-12-31) becomes public only when the 10-K files 2023-02-15.
    facts = _facts([("2023-02-15", "2022-12-31", 500.0)])
    days = pd.date_range("2023-01-01", "2023-03-31", freq="D")
    series = ie.pit_daily(facts, days)

    filed = pd.Timestamp("2023-02-15")
    before = series[series.index < filed]
    on_after = series[series.index >= filed]

    # THE assertion: nothing knowable before the filing date.
    assert before.isna().all(), "look-ahead: fact present before its filed date"
    # And the value is carried forward from the filing date onward.
    assert (on_after == 500.0).all()
    # The exact boundary day (== filed) is knowable (filing is public that day).
    assert series.loc[filed] == 500.0


def test_pit_uses_filed_not_period_end():
    """The series must switch on `filed`, NOT on the (much earlier) period `end`."""
    # Period ended 2022-12-31 but not filed until 2023-02-20: the ~7-week gap is the leak window.
    facts = _facts([("2023-02-20", "2022-12-31", 42.0)])
    days = pd.date_range("2022-12-31", "2023-03-01", freq="D")
    series = ie.pit_daily(facts, days)
    # On the period-end date itself (2022-12-31) the value is UNKNOWN (not yet filed).
    assert np.isnan(series.loc[pd.Timestamp("2022-12-31")])
    # It only appears from the filed date.
    assert series.loc[pd.Timestamp("2023-02-20")] == 42.0
    assert np.isnan(series.loc[pd.Timestamp("2023-02-19")])


def test_pit_no_look_ahead_real_cached_fact():
    """Real cached AAPL fact: FY2006 book equity was filed 2009-10-27 (XBRL adoption lag)."""
    cache = _ROOT / "data" / "edgar" / "CIK0000320193.json"
    if not cache.exists():
        pytest.skip("AAPL companyfacts not cached (run ingest_edgar.py)")
    import json

    fj = json.loads(cache.read_text())
    facts = ie.extract_concept_facts(fj, *ie.BOOK_EQUITY)
    assert not facts.empty
    # The earliest AAPL StockholdersEquity fact has a 2006 period end but a 2009 filed date.
    earliest_filed = facts["filed"].min()
    assert earliest_filed >= pd.Timestamp("2009-01-01")
    # Build the daily series and assert nothing is known before the FIRST filing date.
    days = pd.date_range("2008-01-01", "2010-12-31", freq="D")
    series = ie.pit_daily(facts, days)
    assert series[series.index < earliest_filed].isna().all()
    assert series[series.index >= earliest_filed].notna().any()


# ============================================================ PIT selection mechanics ============
def test_pit_carries_latest_filed_period():
    """As new fiscal years are filed, the series advances to the latest-period value."""
    facts = _facts(
        [
            ("2022-02-15", "2021-12-31", 100.0),
            ("2023-02-15", "2022-12-31", 130.0),
            ("2024-02-15", "2023-12-31", 160.0),
        ]
    )
    days = pd.to_datetime(["2022-06-01", "2023-06-01", "2024-06-01"])
    s = ie.pit_daily(facts, days)
    assert list(s.values) == [100.0, 130.0, 160.0]


def test_pit_restatement_overrides_from_filed_date():
    """A restatement of the SAME period (same end, later filed) applies only from its filed date."""
    facts = _facts(
        [
            ("2023-02-15", "2022-12-31", 100.0),  # original
            ("2023-08-01", "2022-12-31", 90.0),  # 10-K/A restatement, filed later
        ]
    )
    days = pd.to_datetime(["2023-03-01", "2023-09-01"])
    s = ie.pit_daily(facts, days)
    assert s.iloc[0] == 100.0  # before the restatement, the original stands
    assert s.iloc[1] == 90.0  # after, the restated value


def test_pit_comparative_does_not_override_latest():
    """A prior-year comparative re-reported in a new filing must NOT overwrite the latest period."""
    facts = _facts(
        [
            ("2023-02-15", "2022-12-31", 130.0),  # FY2022 (latest at this point)
            ("2024-02-15", "2023-12-31", 160.0),  # FY2023 latest
            ("2024-02-15", "2022-12-31", 131.0),  # FY2022 comparative in the FY2023 10-K
        ]
    )
    days = pd.to_datetime(["2024-06-01"])
    s = ie.pit_daily(facts, days)
    assert s.iloc[0] == 160.0  # latest period wins, not the 131.0 comparative


def test_annual_filter_excludes_quarters():
    """annual=True keeps ~365d fiscal-year facts and drops ~90d quarterly facts."""
    facts = _facts(
        [
            ("2023-04-30", "2023-03-31", 25.0),  # Q1 (90d) — should be dropped
            ("2023-02-15", "2022-12-31", 100.0),  # FY (365d) — should be kept
        ],
        starts=["2023-01-01", "2022-01-01"],
    )
    days = pd.to_datetime(["2023-06-01"])
    annual = ie.pit_daily(facts, days, annual=True)
    assert annual.iloc[0] == 100.0  # the quarter never becomes the selected value


# ============================================================ ticker/CIK mapping =================
def test_real_ticker_overrides():
    assert ie.real_ticker("BRKBUSDT") == "BRK-B"
    assert ie.real_ticker("PAYPUSDT") == "PYPL"
    assert ie.real_ticker("AAPLUSDT") == "AAPL"
    assert ie.real_ticker("BABAUSDT") == "BABA"  # ADR uses its US listing == stem


def test_extract_missing_concept_is_empty():
    """A companyfacts JSON lacking the requested us-gaap concept -> empty frame (foreign IFRS)."""
    fj = {"facts": {"us-gaap": {}}}
    out = ie.extract_concept_facts(fj, *ie.BOOK_EQUITY)
    assert out.empty
    # And PIT-daily of an empty frame is all-NaN (-> 0 weight downstream).
    days = pd.date_range("2020-01-01", periods=5, freq="D")
    assert ie.pit_daily(out, days).isna().all()


# ============================================================ factor construction ================
def _toy_panels_and_close():
    """Two sectors x two names each, with hand-set PIT fundamentals + a flat price panel."""
    days = pd.date_range("2020-01-01", periods=4, freq="D")
    cols = ["AUSDT", "BUSDT", "CUSDT", "DUSDT"]
    close = pd.DataFrame(10.0, index=days, columns=cols)
    shares = pd.DataFrame(1.0, index=days, columns=cols)  # mcap = 10 each
    # A cheaper (higher book) vs expensive within sector X; likewise sector Y.
    book = pd.DataFrame({"AUSDT": 8.0, "BUSDT": 2.0, "CUSDT": 7.0, "DUSDT": 3.0}, index=days)
    assets = pd.DataFrame(100.0, index=days, columns=cols)
    gp = pd.DataFrame({"AUSDT": 40.0, "BUSDT": 10.0, "CUSDT": 35.0, "DUSDT": 5.0}, index=days)
    ni = pd.DataFrame(5.0, index=days, columns=cols)
    rev = pd.DataFrame(50.0, index=days, columns=cols)
    panels = {
        "book_equity": book,
        "assets": assets,
        "net_income": ni,
        "revenues": rev,
        "gross_profit": gp,
        "shares": shares,
    }
    sector = {"AUSDT": "X", "BUSDT": "X", "CUSDT": "Y", "DUSDT": "Y"}
    return panels, close, sector


def test_value_factor_longs_cheap_within_sector():
    """Sector-neutral VALUE raw goes LONG the higher book-to-price (cheaper) name in each sector."""
    panels, close, sector = _toy_panels_and_close()
    raw = ff.sector_neutral_raw(ff.book_to_price(panels, close), sector)
    row = raw.iloc[-1]
    assert row["AUSDT"] > 0 > row["BUSDT"]  # sector X: A (book 8) long, B (book 2) short
    assert row["CUSDT"] > 0 > row["DUSDT"]  # sector Y: C (book 7) long, D (book 3) short


def test_quality_factor_longs_profitable_within_sector():
    panels, close, sector = _toy_panels_and_close()
    raw = ff.sector_neutral_raw(ff.gross_profitability(panels, close), sector)
    row = raw.iloc[-1]
    assert row["AUSDT"] > 0 > row["BUSDT"]  # gp/assets: A(0.40) long, B(0.10) short
    assert row["CUSDT"] > 0 > row["DUSDT"]


def test_sector_neutral_raw_is_net_zero_per_sector():
    """Each sector's weights sum to ~0 (dollar- and sector-neutral book)."""
    panels, close, sector = _toy_panels_and_close()
    raw = ff.sector_neutral_raw(ff.book_to_price(panels, close), sector)
    last = raw.iloc[-1]
    assert abs(last["AUSDT"] + last["BUSDT"]) < 1e-9
    assert abs(last["CUSDT"] + last["DUSDT"]) < 1e-9


def test_unknown_fundamental_takes_zero_weight():
    """A NaN fundamental (foreign ADR / pre-filing) becomes a 0 weight, never a NaN position."""
    panels, close, sector = _toy_panels_and_close()
    panels["book_equity"] = panels["book_equity"].copy()
    panels["book_equity"]["BUSDT"] = np.nan  # B's book unknown
    raw = ff.sector_neutral_raw(ff.book_to_price(panels, close), sector)
    assert not raw.isna().any().any()
    assert (raw["BUSDT"] == 0.0).all()


def test_negative_book_equity_dropped_from_value():
    """A negative book equity (distressed) yields no VALUE signal (NaN -> 0 weight)."""
    panels, close, sector = _toy_panels_and_close()
    panels["book_equity"] = panels["book_equity"].copy()
    panels["book_equity"]["BUSDT"] = -5.0
    bp = ff.book_to_price(panels, close)
    assert bp["BUSDT"].isna().all()


def test_universe_maps_to_ciks_offline():
    """Every SECTOR_MAP name resolves to a real SEC ticker; the cached CIK map covers all names."""
    cache = _ROOT / "data" / "edgar"
    if not (cache / "_company_tickers.json").exists():
        pytest.skip("company_tickers cache absent (run ingest_edgar.py)")
    ciks = ie.resolve_ciks(sorted(ut.SECTOR_MAP), cache)
    # All 69 names resolve to a CIK (foreign ADRs resolve too; they just lack us-gaap facts).
    assert len(ciks) == len(ut.SECTOR_MAP)
