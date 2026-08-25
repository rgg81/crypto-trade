from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import snapshot_preflight as preflight

START = pd.Timestamp("2021-01-04", tz="UTC")
END = pd.Timestamp("2021-02-01", tz="UTC")
SYMBOLS = ("BTCUSDT", "AAAUSDT", "BBBUSDT")


def _grid() -> pd.DatetimeIndex:
    return pd.date_range(START, END - pd.Timedelta(hours=8), freq="8h", tz="UTC")


def _bars(
    symbols: Sequence[str] = SYMBOLS, drop: Iterable[tuple[str, pd.Timestamp]] = ()
) -> pd.DataFrame:
    dropped = set(drop)
    rows = [
        {"open_time": stamp, "symbol": symbol, "open": 100.0}
        for stamp in _grid()
        for symbol in symbols
        if (symbol, stamp) not in dropped
    ]
    return pd.DataFrame(rows)


def _marks(
    symbols: Sequence[str] = SYMBOLS, drop: Iterable[tuple[str, pd.Timestamp]] = ()
) -> pd.DataFrame:
    dropped = set(drop)
    rows = [
        {"mark_time": stamp, "symbol": symbol, "mark_price": 100.0}
        for stamp in _grid()
        for symbol in symbols
        if (symbol, stamp) not in dropped
    ]
    return pd.DataFrame(rows)


def _funding(symbols: Sequence[str] = SYMBOLS, skip: Iterable[str] = ()) -> pd.DataFrame:
    skipped = set(skip)
    rows = [
        {"settlement_time": stamp, "symbol": symbol, "funding_rate": 0.0001}
        for stamp in _grid()
        for symbol in symbols
        if symbol not in skipped
    ]
    return pd.DataFrame(rows)


def _membership(symbols: Sequence[str] = SYMBOLS) -> pd.DataFrame:
    rows = [
        {
            "reconstitution_time": week,
            "symbol": symbol,
            "liquidity_rank": rank,
            "trailing_quote_volume": 1_000.0,
        }
        for week in pd.date_range(START, END, freq="7D", tz="UTC")
        for rank, symbol in enumerate(symbols, start=1)
    ]
    return pd.DataFrame(rows)


def _check(**overrides):  # type: ignore[no-untyped-def]
    payload = {
        "bars": _bars(),
        "marks": _marks(),
        "funding": _funding(),
        "membership": _membership(),
        **overrides,
    }
    return preflight.check_decision_grid(
        payload["bars"],
        payload["marks"],
        payload["funding"],
        payload["membership"],
        start=START,
        end_exclusive=END,
    )


def test_a_complete_snapshot_passes() -> None:
    report = _check()
    assert report.ok
    assert report.findings == ()
    assert report.boundaries == len(_grid())
    assert report.membership_symbols == len(SYMBOLS)


def test_a_missing_mark_for_an_eligible_symbol_is_reported() -> None:
    """The exact CUP-20 condition: engine_v2 raises here, so the preflight must catch it first."""

    boundary = _grid()[10]
    report = _check(marks=_marks(drop=[("AAAUSDT", boundary)]))
    assert not report.ok
    assert report.counts_by_kind()["missing_mark_for_eligible_symbol"] == 1
    finding = report.findings[0]
    assert finding.boundary == boundary.isoformat()
    assert finding.symbols == ("AAAUSDT",)


def test_every_offending_boundary_is_reported_not_only_the_first() -> None:
    """A preflight that stops at the earliest failure turns one repair pass into twenty."""

    boundaries = list(_grid()[5:25])
    report = _check(marks=_marks(drop=[("AAAUSDT", stamp) for stamp in boundaries]))
    reported = [
        finding.boundary
        for finding in report.findings
        if finding.kind == "missing_mark_for_eligible_symbol"
    ]
    assert reported == [stamp.isoformat() for stamp in boundaries]


def test_a_member_without_an_open_is_not_a_finding() -> None:
    """The engine takes eligible AND fillable, so a member with no bar simply cannot trade.

    Reporting it would flood the preflight with delisted contracts and hide real defects.
    """

    boundary = _grid()[12]
    report = _check(
        bars=_bars(drop=[("AAAUSDT", boundary)]),
        marks=_marks(drop=[("AAAUSDT", boundary)]),
    )
    assert report.ok


def test_boundaries_before_the_first_reconstitution_have_no_members() -> None:
    late = _membership()
    late["reconstitution_time"] = late["reconstitution_time"] + pd.Timedelta(days=14)
    report = _check(membership=late, marks=_marks(drop=[("AAAUSDT", _grid()[0])]))
    assert report.ok


def test_missing_funding_for_an_active_symbol_month_is_reported() -> None:
    report = _check(funding=_funding(skip=["BBBUSDT"]))
    assert not report.ok
    kinds = report.counts_by_kind()
    assert kinds["missing_funding_for_active_symbol_month"] >= 1
    finding = next(
        item for item in report.findings if item.kind == "missing_funding_for_active_symbol_month"
    )
    assert "BBBUSDT" in finding.symbols


def test_an_empty_funding_table_is_reported() -> None:
    empty = pd.DataFrame(columns=["settlement_time", "symbol", "funding_rate"])
    report = _check(funding=empty)
    assert "funding_table_empty" in report.counts_by_kind()


def test_a_gap_in_the_regime_source_is_reported() -> None:
    """Regime labels come from one symbol; a gap there silently relabels history."""

    gaps = [("BTCUSDT", stamp) for stamp in _grid()[3:6]]
    report = _check(bars=_bars(drop=gaps), marks=_marks(drop=gaps))
    finding = next(item for item in report.findings if item.kind == "regime_source_gap")
    assert "3_missing_boundaries" in finding.symbols[0]


def test_an_absent_regime_source_is_reported() -> None:
    symbols = ("AAAUSDT", "BBBUSDT")
    report = _check(
        bars=_bars(symbols),
        marks=_marks(symbols),
        funding=_funding(symbols),
        membership=_membership(symbols),
    )
    assert "regime_source_absent" in report.counts_by_kind()


def test_assert_names_the_first_offending_boundary_and_raises() -> None:
    boundary = _grid()[7]
    with pytest.raises(preflight.SnapshotPreflightError, match="missing_mark_for_eligible_symbol"):
        preflight.assert_decision_grid_is_executable(
            _bars(),
            _marks(drop=[("AAAUSDT", boundary)]),
            _funding(),
            _membership(),
            start=START,
            end_exclusive=END,
        )


def test_assert_returns_the_report_when_the_grid_is_clean() -> None:
    report = preflight.assert_decision_grid_is_executable(
        _bars(), _marks(), _funding(), _membership(), start=START, end_exclusive=END
    )
    assert report.ok


def test_findings_are_truncated_with_a_visible_flag() -> None:
    """Silent truncation reads as 'covered everything' when it did not."""

    boundaries = list(_grid()[:30])
    report = preflight.check_decision_grid(
        _bars(),
        _marks(drop=[("AAAUSDT", stamp) for stamp in boundaries]),
        _funding(),
        _membership(),
        start=START,
        end_exclusive=END,
        limit=5,
    )
    assert report.truncated
    assert len([f for f in report.findings if f.kind == "missing_mark_for_eligible_symbol"]) == 5


def test_an_empty_window_is_rejected_rather_than_passing_vacuously() -> None:
    """'Clean' and 'parsed nothing' must not be the same result."""

    with pytest.raises(preflight.SnapshotPreflightError, match="no bars inside"):
        preflight.check_decision_grid(
            _bars(),
            _marks(),
            _funding(),
            _membership(),
            start=pd.Timestamp("2019-01-01", tz="UTC"),
            end_exclusive=pd.Timestamp("2019-02-01", tz="UTC"),
        )


def test_report_json_is_serialisable_and_carries_no_prices() -> None:
    report = _check(marks=_marks(drop=[("AAAUSDT", _grid()[2])]))
    payload = preflight.report_to_json(report)
    assert payload["schema_version"] == "top40-v5-snapshot-preflight-v1"
    assert payload["ok"] is False
    text = repr(payload)
    assert "100.0" not in text, "preflight output must not leak price levels"
