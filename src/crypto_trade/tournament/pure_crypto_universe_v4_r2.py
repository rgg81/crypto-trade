"""Data-bound pure-native-crypto audit for the July-inclusive V4-R2 snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype

from crypto_trade.tournament import pure_crypto_universe_v6 as policy

POLICY_ID = "top40-v4-r2-pure-crypto-usdt-perpetual-v1"
POLICY_SHA256 = policy._policy_sha256()


class PureCryptoR2Error(ValueError):
    """The edition-2 snapshot cannot be proven to contain only native crypto."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_bytes(path: Path, label: str, *, maximum: int = 2 * 1024 * 1024) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise PureCryptoR2Error(f"{label} is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except OSError as exc:
        raise PureCryptoR2Error(f"cannot read {label}") from exc
    identities = (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns),
        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns),
    )
    if len(payload) > maximum or len(set(identities)) != 1 or stat.S_ISLNK(current.st_mode):
        raise PureCryptoR2Error(f"{label} changed while being read")
    return payload


def _safe_relative_path(root: Path, relative: str, label: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise PureCryptoR2Error(f"{label} path is unsafe")
    lexical = root
    for part in pure.parts:
        lexical /= part
        if os.path.lexists(lexical) and lexical.is_symlink():
            raise PureCryptoR2Error(f"{label} path traverses a symlink")
    path = lexical.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise PureCryptoR2Error(f"{label} is missing or unsafe")
    return path


def _entry(manifest: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise PureCryptoR2Error("snapshot manifest files are malformed")
    matches = [row for row in rows if isinstance(row, Mapping) and row.get("name") == name]
    if len(matches) != 1:
        raise PureCryptoR2Error(f"snapshot manifest must bind exactly one {name}")
    return matches[0]


def _bound_path(root: Path, entry: Mapping[str, Any]) -> Path:
    relative = entry.get("path")
    if not isinstance(relative, str):
        raise PureCryptoR2Error("snapshot entry path is invalid")
    path = _safe_relative_path(root, relative, "snapshot entry")
    if path.stat().st_size != entry.get("size") or _sha256(path) != entry.get("sha256"):
        raise PureCryptoR2Error("snapshot entry bytes differ from the manifest")
    return path


def _exchange_index(path: Path) -> dict[str, Mapping[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PureCryptoR2Error("exchange_info is invalid JSON") from exc
    rows = value.get("symbols") if isinstance(value, Mapping) else None
    if not isinstance(rows, list):
        raise PureCryptoR2Error("exchange_info symbols are malformed")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("symbol"), str):
            raise PureCryptoR2Error("exchange_info contains an invalid contract")
        symbol = str(row["symbol"])
        if symbol in result:
            raise PureCryptoR2Error("exchange_info contains a duplicate contract")
        result[symbol] = row
    return result


def _metadata(
    path: Path,
    exchange: Mapping[str, Mapping[str, Any]],
    eligible_symbols: set[str],
) -> tuple[pd.DataFrame, set[str]]:
    frame = pd.read_parquet(path, engine="pyarrow")
    required = {
        "symbol",
        "contract_type",
        "quote_asset",
        "margin_asset",
        "is_crypto",
        "underlying_type",
        "metadata_source",
    }
    if not required.issubset(frame.columns) or not is_bool_dtype(frame["is_crypto"]):
        raise PureCryptoR2Error("contract_metadata schema is invalid")
    symbols = frame["symbol"].tolist()
    if (
        any(not isinstance(symbol, str) for symbol in symbols)
        or len(symbols) != len(set(symbols))
        or symbols != sorted(symbols)
    ):
        raise PureCryptoR2Error("contract_metadata symbols are invalid or unsorted")
    excluded_unreviewed: set[str] = set()
    for row in frame.itertuples(index=False):
        symbol = str(row.symbol)
        reasons = policy.symbol_policy_violations(symbol)
        if reasons or not bool(row.is_crypto):
            raise PureCryptoR2Error(f"contract_metadata rejects {symbol}: {reasons}")
        current = exchange.get(symbol)
        if current is None:
            valid_archive = (
                row.contract_type == "PERPETUAL"
                and row.quote_asset == "USDT"
                and row.margin_asset == "USDT"
                and row.underlying_type == "ARCHIVE_INFERRED_COIN"
                and row.metadata_source == "archive_inference"
            )
            if not valid_archive:
                raise PureCryptoR2Error(f"archive-only contract metadata is invalid: {symbol}")
            if symbol not in policy.REVIEWED_ARCHIVE_ONLY_CRYPTO:
                if symbol in eligible_symbols:
                    raise PureCryptoR2Error(
                        f"unreviewed archive-only contract entered membership: {symbol}"
                    )
                excluded_unreviewed.add(symbol)
        else:
            reasons = policy.current_contract_violations(current, expected_symbol=symbol)
            if reasons:
                raise PureCryptoR2Error(f"current contract is not native crypto: {symbol}")
    return frame, excluded_unreviewed


def _membership(path: Path, metadata: pd.DataFrame) -> pd.DataFrame:
    frame = pd.read_parquet(path, engine="pyarrow")
    required = {"reconstitution_time", "symbol", "liquidity_rank", "trailing_quote_volume"}
    if set(frame.columns) != required or not is_integer_dtype(frame["liquidity_rank"]):
        raise PureCryptoR2Error("membership schema is invalid")
    symbols = set(frame["symbol"])
    if not symbols or not symbols.issubset(set(metadata["symbol"])):
        raise PureCryptoR2Error("membership contains an unknown contract")
    if any(policy.symbol_policy_violations(symbol) for symbol in symbols):
        raise PureCryptoR2Error("membership contains a prohibited contract")
    times = pd.to_datetime(frame["reconstitution_time"], utc=True, errors="coerce")
    normalized = frame.assign(reconstitution_time=times)
    if times.isna().any() or normalized.duplicated(["reconstitution_time", "symbol"]).any():
        raise PureCryptoR2Error("membership timestamps or identities are invalid")
    policy._validate_membership_ranks(normalized)
    return normalized


def audit_pure_crypto_universe(
    root: str | Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    manifest_path = _safe_relative_path(
        root_path, str(config["data"]["manifest_path"]), "snapshot manifest"
    )
    manifest_payload = _regular_bytes(manifest_path, "snapshot manifest")
    manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
    try:
        manifest = json.loads(manifest_payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PureCryptoR2Error("snapshot manifest is invalid JSON") from exc
    if not isinstance(manifest, Mapping):
        raise PureCryptoR2Error("snapshot manifest root is malformed")
    authority = config["universe"]["a6_authority"]
    if manifest_sha256 != config["data"]["manifest_sha256"]:
        raise PureCryptoR2Error("snapshot manifest differs from the config")
    if manifest_sha256 != authority["data_manifest_sha256"]:
        raise PureCryptoR2Error("snapshot manifest differs from the pure-crypto authority")
    window_end = str(manifest["window"]["hard_end_exclusive"]).replace("+00:00", "Z")
    if window_end != config["data"]["hard_end_exclusive"]:
        raise PureCryptoR2Error("snapshot omits part of the configured holdout")

    binding_names = ("contract_metadata", "exchange_info", "membership")
    bindings = {name: _entry(manifest, name) for name in binding_names}
    paths = {name: _bound_path(root_path, entry) for name, entry in bindings.items()}
    exchange = _exchange_index(paths["exchange_info"])
    raw_membership = pd.read_parquet(paths["membership"], columns=["symbol"], engine="pyarrow")
    membership_symbols = set(raw_membership["symbol"])
    metadata, excluded_unreviewed = _metadata(
        paths["contract_metadata"], exchange, membership_symbols
    )
    membership = _membership(paths["membership"], metadata)
    if excluded_unreviewed.intersection(membership["symbol"]):
        raise PureCryptoR2Error("unreviewed archive-only contract is eligible")
    expected = {
        "contract_metadata_sha256": bindings["contract_metadata"]["sha256"],
        "exchange_info_sha256": bindings["exchange_info"]["sha256"],
        "membership_sha256": bindings["membership"]["sha256"],
        "expected_contract_metadata_symbols": len(metadata),
        "expected_distinct_membership_symbols": int(membership["symbol"].nunique()),
        "expected_membership_rows": len(membership),
    }
    if any(authority.get(key) != value for key, value in expected.items()):
        raise PureCryptoR2Error("pure-crypto config bindings differ from the snapshot")
    return {
        "schema_version": 1,
        "policy_id": POLICY_ID,
        "policy_sha256": POLICY_SHA256,
        "status": "passed",
        "authorities": {
            "data_manifest": {"path": config["data"]["manifest_path"], "sha256": manifest_sha256},
            **{name: dict(entry) for name, entry in bindings.items()},
        },
        "counts": {
            "contract_metadata_symbols": len(metadata),
            "current_exchange_symbols": len(exchange),
            "membership_rows": len(membership),
            "membership_symbols": int(membership["symbol"].nunique()),
            "excluded_unreviewed_archive_symbols": len(excluded_unreviewed),
            "violations": 0,
        },
        "excluded_unreviewed_archive_symbol_ids": sorted(excluded_unreviewed),
        "violations": [],
    }


def audit_report_bytes(root: str | Path, config: Mapping[str, Any]) -> bytes:
    value = audit_pure_crypto_universe(root, config)
    return json.dumps(value, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


__all__ = [
    "POLICY_ID",
    "POLICY_SHA256",
    "PureCryptoR2Error",
    "audit_pure_crypto_universe",
    "audit_report_bytes",
]
