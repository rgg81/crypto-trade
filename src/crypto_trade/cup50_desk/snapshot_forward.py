"""Continue the frozen CUP-50 universe and assemble an exact-replay snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from crypto_trade.cup50.config import IS_START, OOS_END
from crypto_trade.cup50.snapshot import Snapshot, load_snapshot, stitch_snapshots
from crypto_trade.cup50.universe import (
    build_membership,
    canonical_daily_quote_volume,
    classify_current_exchange_contracts,
    derive_listing_episodes,
    episode_eligibility,
    pure_crypto_symbols,
    require_exact_membership,
    weekly_reconstitution_times,
)
from crypto_trade.cup50_desk.authority import repository_root, sha256_file
from crypto_trade.cup50_desk.live_data import (
    BARS,
    CONTRACT_METADATA,
    FUNDING,
    MARK_PRICES,
    execution_symbols_from_membership,
    load_cached_frame,
)

TARGET_SIZE = 50
LOOKBACK_DAYS = 180


class ForwardUniverseError(RuntimeError):
    """A forward Monday could not produce the exact frozen Top-50."""


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("snapshot boundary must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def _historical_classifications(root: Path) -> dict[str, str]:
    payload = json.loads(
        (root / "tournament" / "cup50" / "historical-asset-classification.json").read_text()
    )
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("historical classification audit has no entries")
    return {
        str(symbol): str(record["classification"])
        for symbol, record in entries.items()
        if isinstance(record, dict) and "classification" in record
    }


def _verified_acquisition_frame(root: Path, name: str) -> pd.DataFrame:
    acquisition = root / "data" / "cup50" / "acquisition-remediated-20260817"
    manifest = json.loads((acquisition / "manifest.json").read_text())
    matches = [entry for entry in manifest["files"] if entry.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"acquisition manifest has {len(matches)} {name!r} entries")
    entry = matches[0]
    path = acquisition / entry["path"]
    if sha256_file(path) != entry["sha256"]:
        raise ValueError(f"verified acquisition {name} checksum drifted")
    frame = pd.read_parquet(path)
    if len(frame) != int(entry["rows"]):
        raise ValueError(f"verified acquisition {name} row count drifted")
    return frame


def _classified_metadata(root: Path, generation: Path) -> pd.DataFrame:
    historical = _verified_acquisition_frame(root, CONTRACT_METADATA)
    live = load_cached_frame(generation, CONTRACT_METADATA)
    combined = pd.concat([historical, live], ignore_index=True)
    combined = combined.drop_duplicates("symbol", keep="last").sort_values("symbol")
    return classify_current_exchange_contracts(
        combined.reset_index(drop=True),
        historical_classifications=_historical_classifications(root),
    )


def _causal_reconstitution_times(boundary: object) -> tuple[pd.Timestamp, ...]:
    """Return only Monday rosters already effective at the decision boundary.

    The half-open weekly helper needs an upper edge just after ``decision`` so a Monday 00:00
    decision includes its own reconstitution.  Extending that edge by a full day is noncausal:
    from Sunday 08:00 onward it asks for Monday's roster before Sunday is a complete UTC day.
    """
    decision = _utc(boundary)
    result = weekly_reconstitution_times(
        OOS_END + pd.Timedelta(seconds=1),
        decision + pd.Timedelta(nanoseconds=1),
    )
    if any(reconstitution > decision for reconstitution in result):  # pragma: no cover
        raise AssertionError("forward membership includes a future reconstitution")
    return result


def derive_forward_membership(
    generation: Path,
    boundary: object,
    *,
    root: str | Path | None = None,
) -> tuple[pd.DataFrame, tuple[str, ...], tuple[str, ...]]:
    """Resolver passed to the acquisition layer after the wide bar panel is refreshed."""
    base = Path(root).resolve() if root is not None else repository_root()
    decision = _utc(boundary)
    research = load_snapshot(base / "data" / "cup50" / "is")
    sealed = load_snapshot(base / "data" / "cup50" / "sealed")
    recorded = pd.concat([research.membership, sealed.membership], ignore_index=True)
    recorded["reconstitution_time"] = pd.to_datetime(
        recorded["reconstitution_time"], utc=True
    )
    recorded = recorded.sort_values(
        ["reconstitution_time", "liquidity_rank", "symbol"], ignore_index=True
    )
    recorded_last = pd.Timestamp(recorded["reconstitution_time"].max())

    boundaries = _causal_reconstitution_times(decision)
    wide_historical = _verified_acquisition_frame(base, BARS)
    earliest = (boundaries[0] if boundaries else decision) - pd.Timedelta(days=LOOKBACK_DAYS)
    wide_historical["open_time"] = pd.to_datetime(wide_historical["open_time"], utc=True)
    wide_historical = wide_historical.loc[
        (wide_historical["open_time"] >= earliest)
        & (wide_historical["open_time"] < OOS_END)
    ]
    live_bars = load_cached_frame(generation, BARS)
    wide = pd.concat([wide_historical, live_bars], ignore_index=True)
    wide = wide.drop_duplicates(["open_time", "symbol"], keep="last").sort_values(
        ["open_time", "symbol"], ignore_index=True
    )
    metadata = _classified_metadata(base, generation)
    allowed = pure_crypto_symbols(metadata)
    volume = canonical_daily_quote_volume(wide, end=decision)
    episodes = derive_listing_episodes(wide)
    eligible = episode_eligibility(
        episodes, boundaries, lookback_days=LOOKBACK_DAYS, interval_hours=8
    )
    eligible = eligible.reindex(index=pd.DatetimeIndex(boundaries), columns=volume.columns)
    eligible = eligible.fillna(False).astype(bool)
    disallowed = eligible.columns.difference(pd.Index(sorted(allowed)))
    if len(disallowed):
        eligible.loc[:, disallowed] = False
    forward = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=boundaries,
        lookback_days=LOOKBACK_DAYS,
        target_size=TARGET_SIZE,
    )
    try:
        require_exact_membership(forward, boundaries, target_size=TARGET_SIZE)
    except ValueError as exc:
        raise ForwardUniverseError(str(exc)) from exc
    combined = pd.concat([recorded, forward], ignore_index=True)
    combined = combined.drop_duplicates(
        ["reconstitution_time", "symbol"], keep="last"
    ).sort_values(["reconstitution_time", "liquidity_rank", "symbol"], ignore_index=True)
    active_rows = combined.loc[combined["reconstitution_time"] <= decision]
    latest = pd.Timestamp(active_rows["reconstitution_time"].max())
    current = tuple(
        active_rows.loc[active_rows["reconstitution_time"] == latest]
        .sort_values(["liquidity_rank", "symbol"])["symbol"]
        .astype(str)
    )
    if len(current) != TARGET_SIZE or not set(current) <= allowed:
        raise ForwardUniverseError(
            f"membership at {decision} is not an exact pure-crypto Top-{TARGET_SIZE}"
        )
    # The seam roster is needed for the unscored bridge; every later roster is retained for
    # participation-limited exits even after it ceases to be eligible.
    accounting = combined.loc[combined["reconstitution_time"] >= recorded_last]
    execution = execution_symbols_from_membership(accounting)
    return combined, current, execution


def _combine(
    historical: pd.DataFrame,
    live: pd.DataFrame,
    *,
    key: list[str],
    live_mask: pd.Series | None = None,
) -> pd.DataFrame:
    incoming = live.loc[live_mask].copy() if live_mask is not None else live.copy()
    result = pd.concat([historical, incoming], ignore_index=True)
    if result.duplicated(key).any():
        duplicates = result.loc[result.duplicated(key, keep=False)].sort_values(key)
        value_columns = [column for column in result if column not in key]
        for _, group in duplicates.groupby(key, dropna=False, sort=False):
            first = group.iloc[0]
            for column in value_columns:
                values = group[column]
                equal = values.eq(first[column]) | (values.isna() & pd.isna(first[column]))
                if not equal.all():
                    raise ValueError(f"snapshot source conflict on {key}: {column}")
        result = result.drop_duplicates(key, keep="first")
    return result.sort_values(key, ignore_index=True)


def build_forward_snapshot(
    generation: Path,
    membership: pd.DataFrame,
    boundary: object,
    *,
    root: str | Path | None = None,
) -> Snapshot:
    """Append the current immutable generation to the two frozen snapshot partitions."""
    base = Path(root).resolve() if root is not None else repository_root()
    decision = _utc(boundary)
    right = decision + pd.Timedelta(hours=8)
    historical = stitch_snapshots(
        load_snapshot(base / "data" / "cup50" / "is"),
        load_snapshot(base / "data" / "cup50" / "sealed"),
    )
    live_bars = load_cached_frame(generation, BARS)
    live_funding = load_cached_frame(generation, FUNDING)
    live_marks = load_cached_frame(generation, MARK_PRICES)
    member_symbols = set(membership["symbol"].astype(str))
    live_bars = live_bars.loc[live_bars["symbol"].astype(str).isin(member_symbols)]
    live_funding = live_funding.loc[live_funding["symbol"].astype(str).isin(member_symbols)]
    live_marks = live_marks.loc[live_marks["symbol"].astype(str).isin(member_symbols)]
    funding_time = pd.to_datetime(live_funding["settlement_time"], utc=True)
    mark_time = pd.to_datetime(live_marks["mark_time"], utc=True)
    frames = {
        "bars": _combine(
            historical.bars,
            live_bars,
            key=["open_time", "symbol"],
        ),
        "funding": _combine(
            historical.funding,
            live_funding,
            key=["funding_time", "symbol"],
            live_mask=funding_time > OOS_END,
        ),
        "mark_prices": _combine(
            historical.mark_prices,
            live_marks,
            key=["mark_time", "symbol"],
            live_mask=mark_time > OOS_END,
        ),
        "membership": membership.copy(),
        "contract_metadata": _classified_metadata(base, generation),
    }
    frames["bars"] = frames["bars"].loc[
        pd.to_datetime(frames["bars"]["open_time"], utc=True) < right
    ].copy()
    frames["funding"] = frames["funding"].loc[
        pd.to_datetime(frames["funding"]["settlement_time"], utc=True) <= right
    ].copy()
    frames["mark_prices"] = frames["mark_prices"].loc[
        pd.to_datetime(frames["mark_prices"]["mark_time"], utc=True) <= decision
    ].copy()
    generation_manifest = (generation / "cache-manifest.json").read_bytes()
    membership_digest = hashlib.sha256(
        membership.to_json(
            orient="table", date_format="iso", double_precision=15, index=False
        ).encode()
    ).hexdigest()
    digest = hashlib.sha256(
        b":".join(
            [
                historical.manifest_sha256.encode(),
                hashlib.sha256(generation_manifest).hexdigest().encode(),
                membership_digest.encode(),
                right.isoformat().encode(),
            ]
        )
    ).hexdigest()
    snapshot = Snapshot(
        **frames,
        manifest_sha256=digest,
        window_start=IS_START,
        window_end=right,
        sealed=True,
    )
    _require_execution_coverage(snapshot, decision)
    return snapshot


def _members_at(membership: pd.DataFrame, decision: pd.Timestamp) -> tuple[str, ...]:
    rows = membership.loc[
        pd.to_datetime(membership["reconstitution_time"], utc=True) <= decision
    ]
    edge = pd.Timestamp(rows["reconstitution_time"].max())
    return tuple(rows.loc[rows["reconstitution_time"] == edge, "symbol"].astype(str))


def _require_execution_coverage(snapshot: Snapshot, through: pd.Timestamp) -> None:
    bars = snapshot.bars.copy()
    marks = snapshot.mark_prices.copy()
    bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True)
    marks["mark_time"] = pd.to_datetime(marks["mark_time"], utc=True)
    bar_keys = set(zip(bars["open_time"], bars["symbol"].astype(str), strict=True))
    mark_keys = set(zip(marks["mark_time"], marks["symbol"].astype(str), strict=True))
    decisions = pd.date_range(OOS_END, through, freq="8h", tz="UTC")
    for decision in decisions:
        members = _members_at(snapshot.membership, decision)
        if len(members) != TARGET_SIZE:
            raise ForwardUniverseError(f"{decision} does not carry exactly 50 members")
        missing_bars = [name for name in members if (decision, name) not in bar_keys]
        missing_marks = [name for name in members if (decision, name) not in mark_keys]
        if missing_bars or missing_marks:
            raise ValueError(
                f"forward readiness failed at {decision}: "
                f"missing bars={missing_bars}, missing marks={missing_marks}"
            )
