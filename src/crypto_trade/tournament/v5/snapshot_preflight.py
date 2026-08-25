"""Whole-grid executability preflight for a built snapshot.

No unit test can find a data defect. CUP-20 ran 862 passing tests over a snapshot that held 21
decision boundaries at which the evaluator raises ``missing current mark for eligible symbols`` —
it would have crashed all twelve teams on their first backtest. The only thing that finds that
class of defect is walking the real decision grid before anyone is dispatched.

V5 arms the same hazard from a second direction: ``snapshot.build_snapshot`` fetches funding and
mark prices only for symbols that appear in the *membership* it just built, so a seasoned universe
ranked over a wider liquid pool can admit a contract whose marks were never downloaded. That is
exactly the CUP-20 failure, pre-armed, and it is why this runs at activation rather than in CI.

The checks mirror ``engine_v2.evaluate_targets`` conditions rather than approximating them:

* a boundary's eligible set is the point-in-time membership intersected with symbols that have a
  non-null open at that boundary — the same ``eligible & fillable`` intersection the engine takes;
* every symbol in that set must have a boundary mark, or the engine raises;
* funding must exist for every symbol-month in which a member actually traded;
* BTCUSDT must be complete across the grid, because the regime labels every gate depends on are
  derived from it and a gap there silently relabels history.

Every offending boundary is reported, never just the first: a preflight that stops at the earliest
failure turns one repair pass into twenty.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

REGIME_SOURCE_SYMBOL = "BTCUSDT"
MAX_REPORTED_BOUNDARIES = 200


class SnapshotPreflightError(AssertionError):
    """Raised when the built snapshot cannot support its own decision grid."""


@dataclasses.dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    boundary: str
    symbols: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "boundary": self.boundary, "symbols": list(self.symbols)}


@dataclasses.dataclass(frozen=True, slots=True)
class PreflightReport:
    """Disclosure-safe summary of grid executability. Carries no prices and no returns."""

    start: str
    end_exclusive: str
    boundaries: int
    membership_symbols: int
    findings: tuple[Finding, ...]
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return not self.findings

    def counts_by_kind(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.kind] = counts.get(finding.kind, 0) + 1
        return dict(sorted(counts.items()))

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "top40-v5-snapshot-preflight-v1",
            "start": self.start,
            "end_exclusive": self.end_exclusive,
            "boundaries": self.boundaries,
            "membership_symbols": self.membership_symbols,
            "ok": self.ok,
            "counts_by_kind": self.counts_by_kind(),
            "findings": [finding.as_dict() for finding in self.findings],
            "findings_truncated": self.truncated,
        }


def _pivot_notna(frame: pd.DataFrame, index: str, column: str, value: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    return frame.pivot(index=index, columns=column, values=value).notna()


def _membership_mask(
    membership: pd.DataFrame, boundaries: pd.DatetimeIndex, symbols: Sequence[str]
) -> pd.DataFrame:
    """Point-in-time membership expanded onto the decision grid.

    Mirrors ``eligible_at``: a boundary takes the most recent reconstitution at or before it, and
    boundaries earlier than the first reconstitution have no members at all.
    """

    reconstitutions = pd.to_datetime(membership["reconstitution_time"], utc=True)
    weekly = (
        pd.crosstab(reconstitutions, membership["symbol"])
        .gt(0)
        .reindex(columns=list(symbols), fill_value=False)
        .sort_index()
    )
    positions = np.searchsorted(weekly.index.to_numpy(), boundaries.to_numpy(), side="right") - 1
    mask = pd.DataFrame(False, index=boundaries, columns=list(symbols))
    known = positions >= 0
    if known.any():
        mask.loc[boundaries[known], :] = weekly.to_numpy()[positions[known]]
    return mask


def _offending(mask: pd.DataFrame, kind: str, limit: int) -> tuple[list[Finding], bool]:
    findings: list[Finding] = []
    rows = mask.to_numpy()
    offending_rows = np.flatnonzero(rows.any(axis=1))
    truncated = len(offending_rows) > limit
    columns = np.asarray(mask.columns)
    for position in offending_rows[:limit]:
        symbols = tuple(sorted(columns[rows[position]]))
        findings.append(
            Finding(kind=kind, boundary=mask.index[position].isoformat(), symbols=symbols)
        )
    return findings, truncated


def check_decision_grid(
    bars: pd.DataFrame,
    marks: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    start: pd.Timestamp | str,
    end_exclusive: pd.Timestamp | str,
    limit: int = MAX_REPORTED_BOUNDARIES,
) -> PreflightReport:
    """Walk every decision boundary and report every way the snapshot cannot support it."""

    window_start = pd.Timestamp(start, tz="UTC") if not isinstance(start, pd.Timestamp) else start
    window_end = (
        pd.Timestamp(end_exclusive, tz="UTC")
        if not isinstance(end_exclusive, pd.Timestamp)
        else end_exclusive
    )

    frame = bars.loc[:, ["open_time", "symbol", "open"]].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame = frame[(frame["open_time"] >= window_start) & (frame["open_time"] < window_end)]
    if frame.empty:
        raise SnapshotPreflightError("no bars inside the requested evaluation window")

    open_notna = _pivot_notna(frame, "open_time", "symbol", "open").sort_index()
    boundaries = pd.DatetimeIndex(open_notna.index)
    symbols = list(open_notna.columns)

    mark_frame = marks.loc[:, ["mark_time", "symbol", "mark_price"]].copy()
    mark_frame["mark_time"] = pd.to_datetime(mark_frame["mark_time"], utc=True)
    mark_notna = (
        _pivot_notna(mark_frame, "mark_time", "symbol", "mark_price")
        .reindex(index=boundaries, columns=symbols)
        .fillna(False)
        .astype(bool)
    )

    member = _membership_mask(membership, boundaries, symbols)
    eligible = member & open_notna.fillna(False).astype(bool)

    findings: list[Finding] = []
    truncated = False

    missing_mark = eligible & ~mark_notna
    rows, was_truncated = _offending(missing_mark, "missing_mark_for_eligible_symbol", limit)
    findings.extend(rows)
    truncated |= was_truncated

    findings.extend(_funding_findings(funding, eligible, limit))
    findings.extend(_regime_source_findings(open_notna, boundaries))

    return PreflightReport(
        start=window_start.isoformat(),
        end_exclusive=window_end.isoformat(),
        boundaries=len(boundaries),
        membership_symbols=int(member.any(axis=0).sum()),
        findings=tuple(findings),
        truncated=truncated,
    )


def _funding_findings(funding: pd.DataFrame, eligible: pd.DataFrame, limit: int) -> list[Finding]:
    """Every symbol-month in which a member could trade must carry funding rows.

    Funding is a cashflow on a carried position, so a missing month is not a gap in a diagnostic —
    it silently pays the book nothing and changes its P&L.
    """

    if funding.empty:
        return [Finding(kind="funding_table_empty", boundary="", symbols=())]
    settled = pd.to_datetime(funding["settlement_time"], utc=True).dt.tz_convert(None)
    have = {
        (symbol, str(period))
        for symbol, period in zip(funding["symbol"], settled.dt.to_period("M"), strict=False)
    }

    months = eligible.index.tz_convert(None).to_period("M")
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for month in months.unique():
        rows = eligible.loc[months == month]
        active = [symbol for symbol in rows.columns if bool(rows[symbol].any())]
        missing = tuple(sorted(symbol for symbol in active if (symbol, str(month)) not in have))
        if missing and (key := (str(month), "funding")) not in seen:
            seen.add(key)
            findings.append(
                Finding(
                    kind="missing_funding_for_active_symbol_month",
                    boundary=str(month),
                    symbols=missing,
                )
            )
        if len(findings) >= limit:
            break
    return findings


def _regime_source_findings(
    open_notna: pd.DataFrame, boundaries: pd.DatetimeIndex
) -> list[Finding]:
    """The regime labels every gate depends on come from one symbol; a gap relabels history."""

    if REGIME_SOURCE_SYMBOL not in open_notna.columns:
        return [Finding(kind="regime_source_absent", boundary="", symbols=(REGIME_SOURCE_SYMBOL,))]
    present = open_notna[REGIME_SOURCE_SYMBOL].fillna(False).astype(bool)
    gaps = boundaries[~present.to_numpy()]
    if len(gaps) == 0:
        return []
    return [
        Finding(
            kind="regime_source_gap",
            boundary=gaps[0].isoformat(),
            symbols=(f"{REGIME_SOURCE_SYMBOL}:{len(gaps)}_missing_boundaries",),
        )
    ]


def assert_decision_grid_is_executable(
    bars: pd.DataFrame,
    marks: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    start: pd.Timestamp | str,
    end_exclusive: pd.Timestamp | str,
    limit: int = MAX_REPORTED_BOUNDARIES,
) -> PreflightReport:
    """Return the report, or raise with every offending boundary named."""

    report = check_decision_grid(
        bars, marks, funding, membership, start=start, end_exclusive=end_exclusive, limit=limit
    )
    if report.ok:
        return report
    summary = ", ".join(f"{kind}={count}" for kind, count in report.counts_by_kind().items())
    first = report.findings[0]
    raise SnapshotPreflightError(
        f"snapshot cannot support its decision grid ({summary}); "
        f"first at {first.boundary or 'n/a'}: {first.kind} {list(first.symbols[:8])}"
    )


def report_to_json(report: PreflightReport) -> Mapping[str, object]:
    return report.as_dict()


__all__ = [
    "Finding",
    "PreflightReport",
    "SnapshotPreflightError",
    "assert_decision_grid_is_executable",
    "check_decision_grid",
    "report_to_json",
]
