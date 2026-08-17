"""Frozen-winner forward paper-desk invariants."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from crypto_trade.cup50.trials import source_bundle_digest


def first_boundary_after(release_time: pd.Timestamp, *, interval_hours: int = 8) -> pd.Timestamp:
    released = pd.Timestamp(release_time)
    if released.tzinfo is None:
        raise ValueError("release_time must be timezone-aware UTC")
    released = released.tz_convert("UTC")
    if interval_hours <= 0 or 24 % interval_hours:
        raise ValueError("paper interval must divide one UTC day")
    epoch = pd.Timestamp("1970-01-01T00:00:00Z")
    step = pd.Timedelta(hours=interval_hours)
    elapsed = released - epoch
    ticks = math.floor(elapsed / step) + 1
    return epoch + ticks * step


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def freeze_desk_authority(
    destination: str | Path,
    *,
    release_path: str | Path,
    winner_bundle: str | Path,
    nomination_sha256: str,
    release_time: pd.Timestamp,
) -> Mapping[str, object]:
    """Bind the released winner centre to one immutable 365-day paper lineage."""
    path = Path(destination)
    if path.exists():
        raise FileExistsError("paper desk authority already exists")
    if len(nomination_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in nomination_sha256
    ):
        raise ValueError("paper authority requires a frozen nomination SHA-256")
    launch = first_boundary_after(release_time)
    release_sha256 = hashlib.sha256(Path(release_path).read_bytes()).hexdigest()
    bundle_sha256 = source_bundle_digest(winner_bundle)
    lineage_body = {
        "release_sha256": release_sha256,
        "winner_bundle_sha256": bundle_sha256,
        "nomination_sha256": nomination_sha256,
    }
    body: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50-paper",
        **lineage_body,
        "lineage_sha256": hashlib.sha256(_canonical(lineage_body)).hexdigest(),
        "launch_time": launch.isoformat().replace("+00:00", "Z"),
        "minimum_end_time": (launch + pd.Timedelta(days=365)).isoformat().replace("+00:00", "Z"),
        "public_data_only": True,
    }
    record = {**body, "authority_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return record


def verify_desk_authority(
    path: str | Path, *, release_path: str | Path, winner_bundle: str | Path
) -> Mapping[str, object]:
    record = json.loads(Path(path).read_text())
    digest = record.pop("authority_sha256", None)
    if digest != hashlib.sha256(_canonical(record)).hexdigest():
        raise ValueError("paper desk authority digest mismatch")
    if record["release_sha256"] != hashlib.sha256(Path(release_path).read_bytes()).hexdigest():
        raise ValueError("paper desk release lineage drifted")
    if record["winner_bundle_sha256"] != source_bundle_digest(winner_bundle):
        raise ValueError("paper desk strategy changed; start a new lineage")
    return {**record, "authority_sha256": digest}


@dataclasses.dataclass(frozen=True, slots=True)
class CacheGeneration:
    generation: int
    parent_sha256: str | None
    cutoff: pd.Timestamp
    row_digest: str
    generation_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class PaperHealth:
    status: str
    lineage_sha256: str
    latest_boundary: pd.Timestamp
    age_hours: float
    membership_count: int
    parity: bool
    append_invariant: bool
    public_data_only: bool


def healthcheck(state: Mapping[str, object], *, now: pd.Timestamp) -> PaperHealth:
    """Fail closed on stale data, parity drift, cache revision, lineage, or membership size."""
    current = pd.Timestamp(now)
    if current.tzinfo is None:
        raise ValueError("healthcheck time must be timezone-aware UTC")
    latest = pd.Timestamp(state["latest_boundary"])
    if latest.tzinfo is None:
        raise ValueError("latest paper boundary must be timezone-aware UTC")
    current, latest = current.tz_convert("UTC"), latest.tz_convert("UTC")
    age_hours = float((current - latest) / pd.Timedelta(hours=1))
    lineage = str(state.get("lineage_sha256", ""))
    membership_count = int(state.get("membership_count", 0))
    parity = bool(state.get("parity"))
    append_invariant = bool(state.get("append_invariant"))
    public_only = bool(state.get("public_data_only"))
    healthy = (
        len(lineage) == 64
        and 0.0 <= age_hours <= 12.0
        and membership_count == 50
        and parity
        and append_invariant
        and public_only
    )
    return PaperHealth(
        "healthy" if healthy else "failed",
        lineage,
        latest,
        age_hours,
        membership_count,
        parity,
        append_invariant,
        public_only,
    )


def digest_markdown(health: PaperHealth, *, forward_days: int, observations: int) -> str:
    if forward_days < 0 or observations < 0:
        raise ValueError("paper digest counts cannot be negative")
    return (
        "# CUP-50 forward paper desk\n\n"
        f"- Status: {health.status}\n"
        f"- Lineage: `{health.lineage_sha256}`\n"
        f"- Latest canonical boundary: {health.latest_boundary.isoformat()}\n"
        f"- Boundary age: {health.age_hours:.2f} hours\n"
        f"- Dynamic universe members: {health.membership_count}\n"
        f"- Exact-replay parity: {'pass' if health.parity else 'fail'}\n"
        f"- Append invariance: {'pass' if health.append_invariant else 'fail'}\n"
        f"- Public-data-only: {'pass' if health.public_data_only else 'fail'}\n"
        f"- Forward days: {forward_days} / 365 minimum\n"
        f"- Official observations: {observations}\n"
    )


def cache_generation(
    *,
    generation: int,
    parent_sha256: str | None,
    cutoff: pd.Timestamp,
    rows: pd.DataFrame,
) -> CacheGeneration:
    if generation < 1 or (generation == 1) != (parent_sha256 is None):
        raise ValueError("cache generations need one genesis and a parent thereafter")
    edge = pd.Timestamp(cutoff)
    if edge.tzinfo is None:
        raise ValueError("cache cutoff must be timezone-aware UTC")
    payload = (
        rows.sort_index(axis=1)
        .to_json(orient="table", date_format="iso", double_precision=15, index=False)
        .encode()
    )
    row_digest = hashlib.sha256(payload).hexdigest()
    body: Mapping[str, object] = {
        "generation": generation,
        "parent_sha256": parent_sha256,
        "cutoff": edge.tz_convert("UTC").isoformat(),
        "row_digest": row_digest,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return CacheGeneration(generation, parent_sha256, edge.tz_convert("UTC"), row_digest, digest)


def require_append_only(
    previous_rows: pd.DataFrame,
    next_rows: pd.DataFrame,
    *,
    key_columns: list[str],
) -> None:
    """A later public-data generation may append, never revise a prior keyed row."""
    if previous_rows.duplicated(key_columns).any() or next_rows.duplicated(key_columns).any():
        raise ValueError("cache generation contains duplicate keys")
    old = previous_rows.sort_values(key_columns, ignore_index=True)
    indexed = next_rows.set_index(key_columns)
    keys = (
        pd.MultiIndex.from_frame(old[key_columns]) if len(key_columns) > 1 else old[key_columns[0]]
    )
    try:
        recovered = indexed.loc[keys].reset_index()
    except KeyError as error:
        raise ValueError("new cache generation deleted prior keys") from error
    recovered = recovered.loc[:, old.columns]
    pd.testing.assert_frame_equal(old, recovered, check_exact=True)


def verify_parity(backtest_targets: pd.DataFrame, paper_targets: pd.DataFrame) -> str:
    pd.testing.assert_frame_equal(backtest_targets, paper_targets, check_exact=True)
    payload = backtest_targets.sort_index(axis=1).to_json(
        orient="table", date_format="iso", double_precision=15
    )
    return hashlib.sha256(payload.encode()).hexdigest()
