"""Causal weekly Top-50 universe construction."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

import numpy as np
import pandas as pd

MEMBERSHIP_COLUMNS = (
    "reconstitution_time",
    "symbol",
    "liquidity_rank",
    "median_daily_quote_volume",
)

_ALLOWED_OPEN_HOURS = frozenset({0, 8, 16})
_EXCLUDED_CLASSIFICATIONS = frozenset(
    {
        "stablecoin",
        "leveraged-token",
        "metal",
        "commodity",
        "tradfi",
        "equity",
        "fund",
        "index",
        "fx",
        "unknown",
    }
)
_STABLE_BASES = frozenset(
    {
        "BUSD",
        "DAI",
        "FDUSD",
        "FRAX",
        "PYUSD",
        "TUSD",
        "USDC",
        "USDD",
        "USDE",
        "USDP",
        "UST",
        "USTC",
    }
)
_NON_CRYPTO_BASES = frozenset(
    {
        "AUD",
        "BTCDOM",
        "DEFI",
        "EUR",
        "GBP",
        "JPY",
        "PAXG",
        "XAG",
        "XAU",
        "XAUT",
    }
)
_LEVERAGED_SUFFIXES = ("BULL", "BEAR", "DOWN", "UP", "2L", "2S", "3L", "3S", "4L", "4S")


@dataclasses.dataclass(frozen=True, slots=True)
class ListingEpisode:
    symbol: str
    start: pd.Timestamp
    end: pd.Timestamp


def _utc(value: object, label: str) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware UTC")
    result = result.tz_convert("UTC")
    if result.utcoffset() != pd.Timedelta(0):  # pragma: no cover - tz_convert guarantees this
        raise ValueError(f"{label} must be UTC")
    return result


def weekly_reconstitution_times(
    start: pd.Timestamp, end: pd.Timestamp, *, weekday: int = 0
) -> tuple[pd.Timestamp, ...]:
    """Monday 00:00 UTC boundaries in the half-open interval ``[start, end)``."""
    start_utc, end_utc = _utc(start, "start"), _utc(end, "end")
    if not 0 <= weekday <= 6:
        raise ValueError("weekday must be in 0..6")
    if start_utc >= end_utc:
        return ()
    days = pd.date_range(start_utc.normalize(), end_utc, freq="D", inclusive="left", tz="UTC")
    return tuple(day for day in days if day >= start_utc and day.weekday() == weekday)


def pure_crypto_symbols(metadata: pd.DataFrame) -> frozenset[str]:
    """Return only positively classified native-crypto USDT-margined perpetuals.

    Missing or unknown classifications fail closed.  ``onboard_date`` is intentionally not read:
    current exchange metadata may classify a contract, but historical archive episodes decide
    when it traded.
    """
    required = {
        "symbol",
        "contract_type",
        "quote_asset",
        "margin_asset",
        "classification",
    }
    missing = required - set(metadata)
    if missing:
        raise ValueError(f"contract metadata missing columns: {sorted(missing)}")
    if metadata["symbol"].astype(str).duplicated().any():
        raise ValueError("contract metadata contains duplicate symbols")
    allowed: set[str] = set()
    for row in metadata.itertuples(index=False):
        symbol = str(row.symbol).upper()
        if not symbol.endswith("USDT"):
            continue
        base = symbol.removesuffix("USDT")
        if base in _STABLE_BASES or base in _NON_CRYPTO_BASES or base.endswith(_LEVERAGED_SUFFIXES):
            continue
        classification = str(getattr(row, "classification", "unknown")).strip().lower()
        native = classification in {"crypto", "native-crypto"}
        if classification in _EXCLUDED_CLASSIFICATIONS or not native:
            continue
        if (
            str(row.contract_type) == "PERPETUAL"
            and str(row.quote_asset) == "USDT"
            and str(row.margin_asset) == "USDT"
        ):
            allowed.add(symbol)
    return frozenset(allowed)


def classify_current_exchange_contracts(
    metadata: pd.DataFrame,
    *,
    historical_classifications: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Create a fresh fail-closed classification from contract facts.

    ``COIN`` is Binance's positive native-crypto underlying type. Historical
    archive-only rows have no authoritative asset classification and therefore
    remain ``unknown`` even when an earlier data build labelled them by
    inference. Listing dates are not consulted, so current metadata cannot
    erase an older archive-derived trading episode.
    """
    required = {"symbol", "contract_type", "quote_asset", "margin_asset", "underlying_type"}
    missing = required - set(metadata)
    if missing:
        raise ValueError(f"contract metadata missing classification facts: {sorted(missing)}")
    result = metadata.copy()
    source = (
        result["metadata_source"].astype(str)
        if "metadata_source" in result
        else pd.Series("unknown", index=result.index)
    )
    positive = (
        source.eq("current_exchangeInfo")
        & result["underlying_type"].astype(str).eq("COIN")
        & result["contract_type"].astype(str).eq("PERPETUAL")
        & result["quote_asset"].astype(str).eq("USDT")
        & result["margin_asset"].astype(str).eq("USDT")
    )
    reviewed = historical_classifications or {}
    invalid = set(reviewed.values()) - ({"crypto"} | _EXCLUDED_CLASSIFICATIONS)
    if invalid:
        raise ValueError(
            f"historical classification audit contains invalid labels: {sorted(invalid)}"
        )
    historical_positive = result["symbol"].astype(str).map(reviewed).eq("crypto")
    positive |= historical_positive
    result["classification"] = np.where(positive, "crypto", "unknown")
    audited_labels = result["symbol"].astype(str).map(reviewed)
    result.loc[audited_labels.notna() & ~historical_positive, "classification"] = audited_labels
    return result


def canonical_daily_quote_volume(
    bars: pd.DataFrame, *, end: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Median-ranking input with a value only for exact, canonical three-bar UTC days."""
    required = {"open_time", "close_time", "symbol", "quote_volume"}
    missing = required - set(bars)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    frame = bars.loc[:, sorted(required)].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    if end is not None:
        cutoff = _utc(end, "end")
        frame = frame.loc[frame["open_time"] < cutoff].copy()
    frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
    frame["quote_volume"] = pd.to_numeric(frame["quote_volume"], errors="raise")
    if frame[["open_time", "close_time"]].isna().any().any():
        raise ValueError("bars contain invalid timestamps")
    if not np.isfinite(frame["quote_volume"].to_numpy(dtype=float)).all():
        raise ValueError("bars contain non-finite quote volume")
    if (frame["quote_volume"] < 0).any():
        raise ValueError("quote volume cannot be negative")
    if frame.duplicated(["open_time", "symbol"]).any():
        raise ValueError("bars contain duplicate (open_time, symbol) rows")

    frame["day"] = frame["open_time"].dt.normalize()
    frame["hour"] = frame["open_time"].dt.hour
    duration = frame["close_time"] - frame["open_time"]
    # Binance encodes an 8h close as open + 8h - 1ms.  Accept exact half-open encodings too, but
    # never an arbitrary duration that happens to give a day three rows.
    canonical_duration = duration.isin(
        [pd.Timedelta(hours=8), pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1)]
    )
    grouped = frame.groupby(["day", "symbol"], sort=True)
    rows: list[dict[str, object]] = []
    for (day, symbol), group in grouped:
        hours = tuple(sorted(int(value) for value in group["hour"]))
        complete = (
            len(group) == 3
            and hours == (0, 8, 16)
            and bool(canonical_duration.loc[group.index].all())
        )
        if complete:
            rows.append(
                {
                    "day": day,
                    "symbol": str(symbol),
                    "quote_volume": float(group["quote_volume"].sum()),
                }
            )
    if not rows:
        return pd.DataFrame(index=pd.DatetimeIndex([], tz="UTC"))
    complete = pd.DataFrame(rows)
    pivot = complete.pivot(index="day", columns="symbol", values="quote_volume").sort_index()
    full_days = pd.date_range(pivot.index.min(), pivot.index.max(), freq="D", tz="UTC")
    return pivot.reindex(full_days)


def derive_listing_episodes(
    bars: pd.DataFrame, *, interval_hours: int = 8
) -> tuple[ListingEpisode, ...]:
    """Derive listing and relisting episodes solely from archived canonical bars."""
    if interval_hours <= 0:
        raise ValueError("interval_hours must be positive")
    required = {"open_time", "close_time", "symbol"}
    missing = required - set(bars)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    frame = bars.loc[:, ["open_time", "close_time", "symbol"]].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
    if frame.duplicated(["open_time", "symbol"]).any():
        raise ValueError("bars contain duplicate episode keys")
    gap = pd.Timedelta(hours=interval_hours)
    episodes: list[ListingEpisode] = []
    for symbol, group in frame.sort_values(["symbol", "open_time"]).groupby("symbol", sort=True):
        start: pd.Timestamp | None = None
        previous_open: pd.Timestamp | None = None
        previous_close: pd.Timestamp | None = None
        for row in group.itertuples(index=False):
            opened, closed = pd.Timestamp(row.open_time), pd.Timestamp(row.close_time)
            if start is None or previous_open is None or opened - previous_open != gap:
                if start is not None and previous_close is not None:
                    episodes.append(ListingEpisode(str(symbol), start, previous_close))
                start = opened
            previous_open, previous_close = opened, closed
        if start is not None and previous_close is not None:
            episodes.append(ListingEpisode(str(symbol), start, previous_close))
    return tuple(episodes)


def episode_eligibility(
    episodes: Sequence[ListingEpisode], boundaries: Sequence[pd.Timestamp]
) -> pd.DataFrame:
    """Past-only listing eligibility to combine with complete-window volume eligibility.

    Episode *ends* are deliberately not consulted.  An end is only knowable after trading stops,
    and extending a still-live episode with future archive bars must not rewrite an old boundary.
    The exact 180-day completeness predicate in :func:`build_membership` removes a delisted or
    recently relisted contract as soon as its archive develops a gap.
    """
    ordered = tuple(_utc(boundary, "boundary") for boundary in boundaries)
    symbols = sorted({episode.symbol for episode in episodes})
    result = pd.DataFrame(False, index=pd.DatetimeIndex(ordered), columns=symbols, dtype=bool)
    for episode in episodes:
        active = [boundary for boundary in ordered if episode.start < boundary]
        if active:
            result.loc[active, episode.symbol] = True
    return result


def _eligibility_at(eligible: pd.DataFrame, boundary: pd.Timestamp, columns: pd.Index) -> pd.Series:
    index = pd.DatetimeIndex(pd.to_datetime(eligible.index, utc=True))
    if not index.is_unique:
        raise ValueError("eligibility has duplicate timestamps")
    normalized = eligible.copy()
    normalized.index = index
    if boundary not in normalized.index:
        return pd.Series(False, index=columns)
    row = normalized.loc[boundary].reindex(columns, fill_value=False)
    if row.isna().any():
        return row.fillna(False).astype(bool)
    return row.astype(bool)


def build_membership(
    daily_quote_volume: pd.DataFrame,
    *,
    eligible: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    lookback_days: int = 180,
    target_size: int = 50,
) -> pd.DataFrame:
    """Rank each Monday independently; no hysteresis and no future execution availability."""
    if lookback_days < 1 or target_size < 1:
        raise ValueError("lookback_days and target_size must be positive")
    volume = daily_quote_volume.copy()
    volume.index = pd.DatetimeIndex(pd.to_datetime(volume.index, utc=True))
    if not volume.index.is_unique or not volume.index.is_monotonic_increasing:
        raise ValueError("daily_quote_volume index must be unique and ascending")
    boundaries = tuple(_utc(value, "reconstitution_time") for value in reconstitution_times)
    if list(boundaries) != sorted(set(boundaries)):
        raise ValueError("reconstitution times must be strictly ascending")
    rows: list[dict[str, object]] = []
    for boundary in boundaries:
        days = pd.date_range(
            boundary - pd.Timedelta(days=lookback_days),
            boundary,
            freq="D",
            inclusive="left",
            tz="UTC",
        )
        history = volume.reindex(days)
        complete = history.notna().sum(axis=0).eq(lookback_days)
        allowed = _eligibility_at(eligible, boundary, volume.columns)
        medians = history.median(axis=0, skipna=True)
        candidates = [
            (str(symbol), float(medians[symbol]))
            for symbol in volume.columns
            if bool(complete[symbol]) and bool(allowed[symbol]) and pd.notna(medians[symbol])
        ]
        # Python's stable total key makes the stated lexical tie-break explicit.
        ordered = sorted(candidates, key=lambda item: (-item[1], item[0]))[:target_size]
        for rank, (symbol, median) in enumerate(ordered, start=1):
            rows.append(
                {
                    "reconstitution_time": boundary,
                    "symbol": symbol,
                    "liquidity_rank": rank,
                    "median_daily_quote_volume": median,
                }
            )
    if not rows:
        return pd.DataFrame(columns=MEMBERSHIP_COLUMNS)
    return pd.DataFrame(rows, columns=MEMBERSHIP_COLUMNS).sort_values(
        ["reconstitution_time", "liquidity_rank", "symbol"], ignore_index=True
    )


def first_full_boundary(membership: pd.DataFrame, *, target_size: int = 50) -> pd.Timestamp:
    counts = membership.groupby("reconstitution_time", sort=True).size()
    exact = counts[counts.eq(target_size)]
    if exact.empty:
        raise ValueError(f"membership never reaches exactly {target_size} names")
    return pd.Timestamp(exact.index[0]).tz_convert("UTC")


def require_exact_membership(
    membership: pd.DataFrame,
    boundaries: Sequence[pd.Timestamp],
    *,
    target_size: int = 50,
) -> None:
    counts = membership.groupby("reconstitution_time").size()
    failures = {
        boundary.isoformat(): int(counts.get(boundary, 0))
        for boundary in map(pd.Timestamp, boundaries)
        if int(counts.get(boundary, 0)) != target_size
    }
    if failures:
        raise ValueError(f"weekly membership is not exact Top-{target_size}: {failures}")


def members_at(membership: pd.DataFrame, decision_time: pd.Timestamp) -> tuple[str, ...]:
    """Membership from the latest boundary at or before ``decision_time``."""
    decision = _utc(decision_time, "decision_time")
    times = pd.DatetimeIndex(pd.to_datetime(membership["reconstitution_time"], utc=True))
    known = times[times <= decision]
    if known.empty:
        return ()
    boundary = known.max()
    rows = membership.loc[times == boundary].sort_values(["liquidity_rank", "symbol"])
    return tuple(rows["symbol"].astype(str))


def assert_append_invariant(
    before: pd.DataFrame, after: pd.DataFrame, *, cutoff: pd.Timestamp
) -> None:
    """Require that appending future raw data did not rewrite old weekly membership."""
    edge = _utc(cutoff, "cutoff")
    for label, frame in (("before", before), ("after", after)):
        if set(MEMBERSHIP_COLUMNS) - set(frame):
            raise ValueError(f"{label} membership has the wrong schema")
    left = before.loc[pd.to_datetime(before["reconstitution_time"], utc=True) < edge]
    right = after.loc[pd.to_datetime(after["reconstitution_time"], utc=True) < edge]
    columns = list(MEMBERSHIP_COLUMNS)
    left = left.loc[:, columns].sort_values(columns[:3], ignore_index=True)
    right = right.loc[:, columns].sort_values(columns[:3], ignore_index=True)
    pd.testing.assert_frame_equal(left, right, check_exact=True)
