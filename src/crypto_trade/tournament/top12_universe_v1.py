"""Fail-closed audit for the weekly six-month Top-12 pure-crypto universe."""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import stat
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.tournament import pure_crypto_universe_v6

POLICY_ID = "top12-v1-pure-crypto-six-month-liquidity-v1"
POLICY_SHA256 = "9459e7dd55bdee32fa4b949db9c219473cb82b8889ed185de5cbe57975d67345"
DATA_MANIFEST_PATH = "tournament/top12/data_manifest.json"
DATA_MANIFEST_SHA256 = "0ced737d1ee62f5a45470c7e363510d4e30aa5a9eb98f82cd17df94caac31198"
UNIVERSE_BUILD_PATH = "tournament/top12-v1/universe-build.json"
UNIVERSE_BUILD_SHA256 = "baa28a2ed0a726bb97f44b6793a0bee6b75d5edd183b8909446c0c9e916e8245"
SOURCE_MANIFEST_SHA256 = "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3"

TRAILING_DAYS = 180
UNIVERSE_SIZE = 12
FIRST_RECONSTITUTION = pd.Timestamp("2020-08-03T00:00:00Z")
HARD_END_EXCLUSIVE = pd.Timestamp("2026-07-01T00:00:00Z")

REQUIRED_BINDINGS = {
    "bars": {
        "path": "data/top12/snapshot-v1/bars.parquet",
        "rows": 1_719_896,
        "sha256": "f6f6364c34d23725d96a41c5cec216a83ca8cb05145e70b56aa239508b1cb99b",
        "size": 79_899_406,
    },
    "contract_metadata": {
        "path": "data/top12/snapshot-v1/contract_metadata.parquet",
        "rows": 667,
        "sha256": "0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243",
        "size": 15_984,
    },
    "exchange_info": {
        "path": "data/top12/snapshot-v1/exchange_info.json",
        "rows": 832,
        "sha256": "aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64",
        "size": 1_682_464,
    },
    "membership": {
        "path": "data/top12/snapshot-v1/membership.parquet",
        "rows": 3_708,
        "sha256": "084e4f19b40053fcb2188d35821bedc70ff680ba4af17e7ad032c1253f31fb87",
        "size": 36_094,
    },
}

_METADATA_COLUMNS = (
    "symbol",
    "contract_type",
    "quote_asset",
    "margin_asset",
    "is_crypto",
    "onboard_date",
    "delivery_date",
    "underlying_type",
    "metadata_source",
)
_MEMBERSHIP_COLUMNS = (
    "reconstitution_time",
    "symbol",
    "liquidity_rank",
    "trailing_quote_volume",
)


class Top12UniverseError(ValueError):
    """The Top-12 membership or its native-crypto classification cannot be proven."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _regular_bytes(root: Path, relative: str, *, maximum: int) -> bytes:
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts:
        raise Top12UniverseError(f"unsafe authority path: {relative}")
    path = root / raw
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise Top12UniverseError(f"authority file is missing or unsafe: {relative}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise Top12UniverseError(f"authority file is invalid or too large: {relative}")
        payload = bytearray()
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise Top12UniverseError(f"authority file changed while read: {relative}")
            payload.extend(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise Top12UniverseError(f"authority file grew while read: {relative}")
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise Top12UniverseError(f"authority file changed while read: {relative}")
        return bytes(payload)
    finally:
        os.close(descriptor)


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise Top12UniverseError(f"duplicate key in {label}: {key}")
            result[key] = value
        return result

    def reject(value: str) -> None:
        raise Top12UniverseError(f"nonfinite JSON value in {label}: {value}")

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Top12UniverseError(f"{label} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise Top12UniverseError(f"{label} must be a JSON object")
    return value


def _manifest(root: Path) -> tuple[Mapping[str, Any], dict[str, Mapping[str, Any]]]:
    payload = _regular_bytes(root, DATA_MANIFEST_PATH, maximum=128 * 1024)
    if _sha256(payload) != DATA_MANIFEST_SHA256:
        raise Top12UniverseError("Top-12 data manifest differs from authority")
    manifest = _strict_json(payload, "Top-12 data manifest")
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or len(raw_files) != 12:
        raise Top12UniverseError("Top-12 manifest must bind exactly twelve files")
    files: dict[str, Mapping[str, Any]] = {}
    for raw in raw_files:
        if not isinstance(raw, Mapping) or set(raw) != {"name", "path", "rows", "sha256", "size"}:
            raise Top12UniverseError("Top-12 manifest contains a malformed file entry")
        name = raw.get("name")
        if not isinstance(name, str) or name in files:
            raise Top12UniverseError("Top-12 manifest names are invalid or duplicated")
        files[name] = raw
    for name, expected in REQUIRED_BINDINGS.items():
        raw = files.get(name)
        if raw is None or any(raw.get(key) != value for key, value in expected.items()):
            raise Top12UniverseError(f"Top-12 manifest {name} binding changed")
    sources = manifest.get("sources")
    if (
        not isinstance(sources, Mapping)
        or sources.get("derived_from_manifest_sha256") != SOURCE_MANIFEST_SHA256
        or sources.get("universe_rule")
        != (
            "weekly Monday 00:00 UTC top 12 native-crypto USDT perpetuals by median "
            "daily quote volume over 180 complete prior days"
        )
    ):
        raise Top12UniverseError("Top-12 derivation authority changed")
    return manifest, files


def _bound_payload(
    root: Path,
    files: Mapping[str, Mapping[str, Any]],
    name: str,
) -> bytes:
    raw = files[name]
    size = raw["size"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise Top12UniverseError(f"invalid manifest size for {name}")
    payload = _regular_bytes(root, str(raw["path"]), maximum=size)
    if len(payload) != size or _sha256(payload) != raw["sha256"]:
        raise Top12UniverseError(f"bound Top-12 bytes changed for {name}")
    return payload


def _parquet(payload: bytes, label: str, columns: list[str] | None = None) -> pd.DataFrame:
    try:
        return pd.read_parquet(io.BytesIO(payload), engine="pyarrow", columns=columns)
    except Exception as exc:
        raise Top12UniverseError(f"cannot parse bound {label} parquet") from exc


def _exchange_index(payload: bytes) -> dict[str, Mapping[str, Any]]:
    raw = _strict_json(payload, "exchange info")
    symbols = raw.get("symbols")
    if not isinstance(symbols, list):
        raise Top12UniverseError("exchange info symbols are missing")
    result: dict[str, Mapping[str, Any]] = {}
    for contract in symbols:
        if not isinstance(contract, Mapping):
            raise Top12UniverseError("exchange info contains a non-object contract")
        symbol = contract.get("symbol")
        if not isinstance(symbol, str) or symbol in result:
            raise Top12UniverseError("exchange info symbols are invalid or duplicated")
        result[symbol] = contract
    return result


def _metadata(
    payload: bytes,
    exchange: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    frame = _parquet(payload, "contract metadata")
    if tuple(frame.columns) != _METADATA_COLUMNS or len(frame) != 667:
        raise Top12UniverseError("contract metadata shape differs from authority")
    if frame["symbol"].duplicated().any():
        raise Top12UniverseError("contract metadata symbols are duplicated")
    frame = frame.copy()
    frame["symbol"] = frame["symbol"].astype(str)
    frame["onboard_date"] = pd.to_datetime(frame["onboard_date"], utc=True, errors="raise")
    frame["delivery_date"] = pd.to_datetime(frame["delivery_date"], utc=True, errors="raise")
    if (
        not frame["contract_type"].eq("PERPETUAL").all()
        or not frame["quote_asset"].eq("USDT").all()
        or not frame["margin_asset"].eq("USDT").all()
        or not frame["is_crypto"].eq(True).all()
    ):
        raise Top12UniverseError("contract metadata contains a non-crypto contract")
    for row in frame.itertuples(index=False):
        reasons = pure_crypto_universe_v6.symbol_policy_violations(row.symbol)
        if reasons:
            raise Top12UniverseError(
                f"contract metadata symbol {row.symbol} is forbidden: {', '.join(reasons)}"
            )
        if row.metadata_source == "current_exchangeInfo":
            contract = exchange.get(row.symbol)
            if contract is None:
                raise Top12UniverseError(
                    f"current contract {row.symbol} is absent from exchange info"
                )
            reasons = pure_crypto_universe_v6.current_contract_violations(
                contract,
                expected_symbol=row.symbol,
            )
            if reasons:
                raise Top12UniverseError(
                    f"current contract {row.symbol} is not pure crypto: {', '.join(reasons)}"
                )
        elif row.metadata_source == "archive_inference":
            if (
                row.underlying_type != "ARCHIVE_INFERRED_COIN"
                or row.symbol not in pure_crypto_universe_v6.REVIEWED_ARCHIVE_ONLY_CRYPTO
            ):
                raise Top12UniverseError(f"archive-only contract {row.symbol} lacks authority")
        else:
            raise Top12UniverseError(f"unknown metadata source for {row.symbol}")
    return frame.set_index("symbol")


def _membership(payload: bytes, metadata: pd.DataFrame) -> pd.DataFrame:
    frame = _parquet(payload, "membership")
    if tuple(frame.columns) != _MEMBERSHIP_COLUMNS or len(frame) != 3_708:
        raise Top12UniverseError("membership shape differs from authority")
    result = frame.copy()
    result["symbol"] = result["symbol"].astype(str)
    result["reconstitution_time"] = pd.to_datetime(
        result["reconstitution_time"],
        utc=True,
        errors="raise",
    )
    if (
        result.duplicated(["reconstitution_time", "symbol"]).any()
        or result.duplicated(["reconstitution_time", "liquidity_rank"]).any()
        or not result["symbol"].isin(metadata.index).all()
        or not result["liquidity_rank"].between(1, UNIVERSE_SIZE).all()
        or not result["trailing_quote_volume"].map(
            lambda value: isinstance(value, (int, float))
            and math.isfinite(float(value))
            and float(value) > 0.0
        ).all()
    ):
        raise Top12UniverseError("membership contains invalid values")
    grouped = result.groupby("reconstitution_time", sort=True, observed=True)
    for boundary, group in grouped:
        if (
            len(group) != UNIVERSE_SIZE
            or sorted(group["liquidity_rank"].tolist()) != list(range(1, UNIVERSE_SIZE + 1))
            or boundary.weekday() != 0
            or boundary.hour != 0
            or boundary.minute != 0
            or boundary.second != 0
        ):
            raise Top12UniverseError(f"invalid weekly membership at {boundary}")
    boundaries = pd.DatetimeIndex(sorted(result["reconstitution_time"].unique()))
    expected = pd.date_range(
        FIRST_RECONSTITUTION,
        HARD_END_EXCLUSIVE,
        freq="W-MON",
        inclusive="left",
    )
    if not boundaries.equals(expected):
        raise Top12UniverseError("membership weekly boundary sequence is incomplete")
    return result


def _recompute(bars_payload: bytes, metadata: pd.DataFrame) -> pd.DataFrame:
    bars = _parquet(
        bars_payload,
        "bars",
        columns=["open_time", "symbol", "quote_volume"],
    )
    bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True, errors="raise")
    bars["symbol"] = bars["symbol"].astype(str)
    bars["quote_volume"] = pd.to_numeric(bars["quote_volume"], errors="raise")
    if bars["quote_volume"].isna().any() or (bars["quote_volume"] < 0.0).any():
        raise Top12UniverseError("bars contain invalid quote volume")
    bars = bars.loc[bars["symbol"].isin(metadata.index)].copy()
    bars["date"] = bars["open_time"].dt.floor("D")
    daily = (
        bars.groupby(["symbol", "date"], sort=False, observed=True)["quote_volume"]
        .sum()
        .reset_index()
    )
    rows: list[dict[str, object]] = []
    for boundary in pd.date_range(
        FIRST_RECONSTITUTION,
        HARD_END_EXCLUSIVE,
        freq="W-MON",
        inclusive="left",
    ):
        start = boundary - pd.Timedelta(days=TRAILING_DAYS)
        window = daily.loc[(daily["date"] >= start) & (daily["date"] < boundary)]
        statistics = window.groupby("symbol", observed=True).agg(
            trailing_quote_volume=("quote_volume", "median"),
            history_days=("date", "nunique"),
        )
        active = metadata.loc[
            (metadata["onboard_date"] <= start) & (metadata["delivery_date"] > boundary)
        ].index
        selected = (
            statistics.loc[
                (statistics["history_days"] == TRAILING_DAYS) & statistics.index.isin(active)
            ]
            .reset_index()
            .sort_values(
                ["trailing_quote_volume", "symbol"],
                ascending=[False, True],
                kind="mergesort",
            )
            .head(UNIVERSE_SIZE)
        )
        if len(selected) != UNIVERSE_SIZE:
            raise Top12UniverseError(f"cannot reproduce twelve members at {boundary}")
        for rank, row in enumerate(selected.itertuples(index=False), start=1):
            rows.append(
                {
                    "reconstitution_time": boundary,
                    "symbol": row.symbol,
                    "liquidity_rank": rank,
                    "trailing_quote_volume": float(row.trailing_quote_volume),
                }
            )
    return pd.DataFrame(rows, columns=_MEMBERSHIP_COLUMNS)


def audit_top12_universe(root: str | Path) -> Mapping[str, Any]:
    """Prove exact six-month ranks and fail closed on non-crypto economic exposure."""

    root_path = Path(root).resolve()
    _manifest_value, files = _manifest(root_path)
    build_payload = _regular_bytes(root_path, UNIVERSE_BUILD_PATH, maximum=64 * 1024)
    if _sha256(build_payload) != UNIVERSE_BUILD_SHA256:
        raise Top12UniverseError("Top-12 universe build record differs from authority")
    build = _strict_json(build_payload, "Top-12 universe build record")
    if (
        build.get("data_manifest_sha256") != DATA_MANIFEST_SHA256
        or build.get("membership_sha256") != REQUIRED_BINDINGS["membership"]["sha256"]
        or build.get("source_manifest_sha256") != SOURCE_MANIFEST_SHA256
        or build.get("trailing_complete_days") != TRAILING_DAYS
        or build.get("universe_size") != UNIVERSE_SIZE
    ):
        raise Top12UniverseError("Top-12 universe build record semantics changed")

    exchange = _exchange_index(_bound_payload(root_path, files, "exchange_info"))
    metadata = _metadata(_bound_payload(root_path, files, "contract_metadata"), exchange)
    observed = _membership(_bound_payload(root_path, files, "membership"), metadata)
    expected = _recompute(_bound_payload(root_path, files, "bars"), metadata)
    normalized = observed.reset_index(drop=True)
    if not normalized.equals(expected):
        raise Top12UniverseError("membership is not the exact causal 180-day Top-12 ranking")

    symbols = sorted(observed["symbol"].unique())
    metadata_sources = Counter(str(metadata.loc[symbol, "metadata_source"]) for symbol in symbols)
    latest = observed.loc[
        observed["reconstitution_time"] == observed["reconstitution_time"].max()
    ].sort_values("liquidity_rank")
    return {
        "classification": {
            "allowed_economic_exposure": "native-crypto-only",
            "forbidden_exposure_violations": 0,
            "metadata_source_counts": dict(sorted(metadata_sources.items())),
            "unknown_classification_is_ineligible": True,
        },
        "data_manifest_sha256": DATA_MANIFEST_SHA256,
        "first_reconstitution": observed["reconstitution_time"].min().isoformat(),
        "last_reconstitution": observed["reconstitution_time"].max().isoformat(),
        "latest_members": latest["symbol"].tolist(),
        "membership_rows": len(observed),
        "membership_sha256": REQUIRED_BINDINGS["membership"]["sha256"],
        "membership_symbols": len(symbols),
        "policy_id": POLICY_ID,
        "policy_sha256": POLICY_SHA256,
        "ranking": {
            "liquidity_measure": "median-daily-quote-volume",
            "lookback_complete_days": TRAILING_DAYS,
            "point_in_time": True,
            "reconstitution": "weekly-monday-00:00-utc",
            "tie_breaker": "lexicographically-smaller-symbol",
            "universe_size": UNIVERSE_SIZE,
        },
        "schema_version": 1,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "status": "passed",
        "weekly_reconstitutions": observed["reconstitution_time"].nunique(),
    }


def audit_report_bytes(root: str | Path) -> bytes:
    return _canonical(audit_top12_universe(root))


def audit_report_sha256(root: str | Path) -> str:
    return _sha256(audit_report_bytes(root))


__all__ = [
    "DATA_MANIFEST_PATH",
    "DATA_MANIFEST_SHA256",
    "POLICY_ID",
    "POLICY_SHA256",
    "Top12UniverseError",
    "audit_report_bytes",
    "audit_report_sha256",
    "audit_top12_universe",
]
