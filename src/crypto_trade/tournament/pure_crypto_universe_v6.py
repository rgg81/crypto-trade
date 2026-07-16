"""Fail-closed pure-crypto audit for the frozen Top-40 V2 snapshot.

The audit is deliberately read-only.  It binds the existing Phase-0 manifest and the three
classification-bearing snapshot files by exact path, size, row count, and SHA-256, parses the
bound bytes, and proves that every candidate and every weekly member is a native crypto contract.
It does not rebuild or reinterpret the frozen liquidity ranks.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype

from crypto_trade.tournament import amendment_integrity_v2

AMENDMENT_ID = "top40-v2-amendment-0006-pure-crypto-universe"
POLICY_ID = "top40-v2-pure-crypto-usdt-perpetual-v1"

DATA_MANIFEST_PATH = "tournament/top40/data_manifest.json"
DATA_MANIFEST_SHA256 = "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3"
DATA_MANIFEST_SIZE = 6_541
DATA_MANIFEST_FILE_COUNT = 12


@dataclass(frozen=True)
class SnapshotFileBinding:
    """Exact immutable authority for one classification-bearing snapshot file."""

    name: str
    path: str
    sha256: str
    size: int
    rows: int
    require_single_link: bool = False


SNAPSHOT_FILE_BINDINGS = (
    SnapshotFileBinding(
        name="contract_metadata",
        path="data/top40/snapshot-v1/contract_metadata.parquet",
        sha256="0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243",
        size=15_984,
        rows=667,
    ),
    SnapshotFileBinding(
        name="exchange_info",
        path="data/top40/snapshot-v1/exchange_info.json",
        sha256="aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64",
        size=1_682_464,
        rows=832,
    ),
    SnapshotFileBinding(
        name="membership",
        path="data/top40/snapshot-v1/membership.parquet",
        sha256="f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14",
        size=134_866,
        rows=12_866,
    ),
)
_BINDING_BY_NAME = {binding.name: binding for binding in SNAPSHOT_FILE_BINDINGS}

# Exact bases, never suffixes.  Exact matching avoids rejecting legitimate native crypto tokens
# such as S, M, FRAX, ENA, SKY, STBL, USUAL, and RESOLV.
STABLE_BASES = frozenset(
    {
        "ALUSD",
        "BFUSD",
        "BUSD",
        "CEUR",
        "CRVUSD",
        "CUSD",
        "DAI",
        "DOLA",
        "EURC",
        "EURS",
        "FDUSD",
        "FRXUSD",
        "GHO",
        "GUSD",
        "HUSD",
        "LUSD",
        "MIM",
        "MUSD",
        "OUSD",
        "PYUSD",
        "RLUSD",
        "SFRXUSD",
        "SUSD",
        "SUSDE",
        "TUSD",
        "USDC",
        "USDD",
        "USDE",
        "USD0",
        "USD1",
        "USDJ",
        "USDP",
        "USDQ",
        "USDS",
        "USDT",
        "USDTB",
        "USDX",
        "UST",
        "USTC",
        "XUSD",
    }
)

# Direct economic exposures that Binance has classified as COIN at least once.  The subtype and
# underlying-type checks remain primary for newly listed TradFi contracts; this exact base list is
# a defense against tokenized commodities and classification drift.
NON_CRYPTO_BASES = frozenset(
    {
        "BZ",
        "CL",
        "COPPER",
        "NATGAS",
        "PAXG",
        "XAG",
        "XAU",
        "XAUT",
        "XPD",
        "XPT",
    }
)

LEVERAGED_BASES = frozenset(
    {
        "1INCHDOWN",
        "1INCHUP",
        "AAVEDOWN",
        "AAVEUP",
        "ADADOWN",
        "ADAUP",
        "BCHDOWN",
        "BCHUP",
        "BNBDOWN",
        "BNBUP",
        "BTCDOWN",
        "BTCUP",
        "DOTDOWN",
        "DOTUP",
        "EOSDOWN",
        "EOSUP",
        "ETHBEAR",
        "ETHBULL",
        "ETHDOWN",
        "ETHUP",
        "FILDOWN",
        "FILUP",
        "LINKDOWN",
        "LINKUP",
        "LTCDOWN",
        "LTCUP",
        "SUSHIDOWN",
        "SUSHIUP",
        "SXPDOWN",
        "SXPUP",
        "TRXDOWN",
        "TRXUP",
        "UNIDOWN",
        "UNIUP",
        "XLMDOWN",
        "XLMUP",
        "XRPDOWN",
        "XRPUP",
        "YFIDOWN",
        "YFIUP",
    }
)

FORBIDDEN_UNDERLYING_TYPES = frozenset(
    {
        "COMMODITY",
        "EQUITY",
        "ETF",
        "FOREX",
        "INDEX",
        "KR_EQUITY",
        "METAL",
        "PREMARKET",
        "STOCK",
        "TRADFI",
    }
)

# Binance's ``RWA`` subtype is a crypto sector label as well as a possible source of ambiguity.
# It is intentionally not forbidden: native protocol tokens such as CFG and MANTRA remain crypto.
# Direct commodity-backed tokens are rejected by NON_CRYPTO_BASES, and direct TradFi contracts
# fail the exact PERPETUAL/COIN requirements before subtype inspection.
FORBIDDEN_UNDERLYING_SUBTYPES = frozenset(
    {
        "commodity",
        "equity",
        "etf",
        "forex",
        "fx",
        "index",
        "metal",
        "metals",
        "preipo",
        "preciousmetal",
        "stock",
        "tradfi",
    }
)

REVIEWED_ARCHIVE_ONLY_CRYPTO = frozenset(
    {
        "1000BTTCUSDT",
        "AKROUSDT",
        "ANCUSDT",
        "ANTUSDT",
        "AUDIOUSDT",
        "BDXNUSDT",
        "BTSUSDT",
        "BTTUSDT",
        "BZRXUSDT",
        "COCOSUSDT",
        "DODOUSDT",
        "EOSUSDT",
        "FRONTUSDT",
        "GALUSDT",
        "HNTUSDT",
        "KEEPUSDT",
        "LENDUSDT",
        "LUNAUSDT",
        "MATICUSDT",
        "MBLUSDT",
        "NUUSDT",
        "RNDRUSDT",
        "SRMUSDT",
        "SXPUSDT",
        "TOMOUSDT",
        "YFIIUSDT",
    }
)

_SYMBOL = re.compile(r"^[A-Z0-9]+USDT$")
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

_INTEGRITY_MODULE_SHA256 = "e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab"
_INTEGRITY_MODULE = amendment_integrity_v2
_READ_REPO_FILE = _INTEGRITY_MODULE.read_repo_file
_STRICT_JSON_OBJECT = _INTEGRITY_MODULE.strict_json_object
_SHA256_BYTES = _INTEGRITY_MODULE.sha256_bytes
_PRETTY_JSON_BYTES = _INTEGRITY_MODULE.pretty_json_bytes


class PureCryptoUniverseError(ValueError):
    """The frozen universe cannot be proven to contain only native crypto contracts."""


def _regular_module_bytes(path: Path, label: str) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise PureCryptoUniverseError(f"{label} is missing or unsafe: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > 8 * 1024 * 1024
        ):
            raise PureCryptoUniverseError(f"{label} must be a bounded single-link file")
        payload = bytearray()
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise PureCryptoUniverseError(f"{label} changed while read")
            payload.extend(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise PureCryptoUniverseError(f"{label} grew while read")
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
            raise PureCryptoUniverseError(f"{label} changed while read")
        return bytes(payload)
    finally:
        os.close(descriptor)


def _verify_integrity_authority() -> None:
    payload = _regular_module_bytes(
        Path(_INTEGRITY_MODULE.__file__).resolve(), "Amendment integrity authority"
    )
    if hashlib.sha256(payload).hexdigest() != _INTEGRITY_MODULE_SHA256:
        raise PureCryptoUniverseError("Amendment integrity authority bytes changed")
    identities = {
        "read_repo_file": _READ_REPO_FILE,
        "strict_json_object": _STRICT_JSON_OBJECT,
        "sha256_bytes": _SHA256_BYTES,
        "pretty_json_bytes": _PRETTY_JSON_BYTES,
    }
    if any(
        getattr(_INTEGRITY_MODULE, name, None) is not value for name, value in identities.items()
    ):
        raise PureCryptoUniverseError("Amendment integrity helper identity changed")


def _read_bound_file(root: Path, binding: SnapshotFileBinding) -> bytes:
    try:
        relative, _path, payload, info = _READ_REPO_FILE(
            root,
            binding.path,
            f"pure-crypto {binding.name}",
            maximum_bytes=binding.size,
            # The frozen binary snapshot is deliberately shared by hard link across the
            # tournament worktrees.  Descriptor-relative O_NOFOLLOW reads, stable fstat
            # identity, exact size, and exact SHA-256 remain mandatory.  Repository-owned
            # amendment/manifest authorities are single-link files.
            require_single_link=binding.require_single_link,
        )
    except (OSError, ValueError) as exc:
        raise PureCryptoUniverseError(f"cannot read bound {binding.name}: {exc}") from exc
    if relative != binding.path or info.st_size != binding.size or len(payload) != binding.size:
        raise PureCryptoUniverseError(f"{binding.name} path or size differs from authority")
    if _SHA256_BYTES(payload) != binding.sha256:
        raise PureCryptoUniverseError(f"{binding.name} SHA-256 differs from authority")
    return payload


def _read_manifest(root: Path) -> tuple[Mapping[str, Any], bytes]:
    binding = SnapshotFileBinding(
        name="data_manifest",
        path=DATA_MANIFEST_PATH,
        sha256=DATA_MANIFEST_SHA256,
        size=DATA_MANIFEST_SIZE,
        rows=DATA_MANIFEST_FILE_COUNT,
        require_single_link=True,
    )
    payload = _read_bound_file(root, binding)
    try:
        manifest = _STRICT_JSON_OBJECT(payload, "pure-crypto data manifest")
    except ValueError as exc:
        raise PureCryptoUniverseError(str(exc)) from exc
    if _PRETTY_JSON_BYTES(manifest) != payload:
        raise PureCryptoUniverseError("data manifest is not canonical pretty JSON")
    return manifest, payload


def _validate_manifest_bindings(manifest: Mapping[str, Any]) -> None:
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != DATA_MANIFEST_FILE_COUNT:
        raise PureCryptoUniverseError("data manifest file count differs from authority")
    by_name: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(files):
        if not isinstance(raw, Mapping):
            raise PureCryptoUniverseError(f"data manifest file {index} is not an object")
        if set(raw) != {"name", "path", "rows", "sha256", "size"}:
            raise PureCryptoUniverseError(f"data manifest file {index} has invalid keys")
        name = raw.get("name")
        if not isinstance(name, str) or name in by_name:
            raise PureCryptoUniverseError("data manifest file names are invalid or duplicated")
        by_name[name] = raw
    for binding in SNAPSHOT_FILE_BINDINGS:
        expected = {
            "name": binding.name,
            "path": binding.path,
            "rows": binding.rows,
            "sha256": binding.sha256,
            "size": binding.size,
        }
        if by_name.get(binding.name) != expected:
            raise PureCryptoUniverseError(
                f"data manifest {binding.name} entry differs from exact authority"
            )


def _normalize_classification(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def symbol_policy_violations(symbol: object) -> tuple[str, ...]:
    """Return deterministic name-level reasons that a symbol is not a pure crypto USDT pair."""

    if not isinstance(symbol, str) or not symbol.isascii() or _SYMBOL.fullmatch(symbol) is None:
        return ("symbol-format",)
    base = symbol[:-4]
    reasons: list[str] = []
    if base in STABLE_BASES:
        reasons.append("stablecoin-base")
    if base in LEVERAGED_BASES:
        reasons.append("leveraged-token-base")
    if base in NON_CRYPTO_BASES:
        reasons.append("direct-non-crypto-base")
    return tuple(reasons)


def _subtype_violations(raw: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(raw, list):
        return (), ("underlying-subtypes-not-list",)
    normalized: list[str] = []
    reasons: list[str] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str) or not value or value != value.strip() or not value.isascii():
            reasons.append("underlying-subtype-invalid")
            continue
        token = _normalize_classification(value)
        if not token or token in seen:
            reasons.append("underlying-subtype-invalid")
            continue
        seen.add(token)
        normalized.append(token)
        if token in FORBIDDEN_UNDERLYING_SUBTYPES:
            reasons.append(f"forbidden-underlying-subtype:{token}")
    return tuple(normalized), tuple(reasons)


def current_contract_violations(
    contract: Mapping[str, Any], *, expected_symbol: str | None = None
) -> tuple[str, ...]:
    """Return exact reasons a current exchangeInfo contract is not native crypto."""

    symbol = contract.get("symbol")
    reasons = list(symbol_policy_violations(symbol))
    if expected_symbol is not None and symbol != expected_symbol:
        reasons.append("symbol-mismatch")
    base = symbol[:-4] if isinstance(symbol, str) and _SYMBOL.fullmatch(symbol) else None
    if contract.get("contractType") != "PERPETUAL":
        reasons.append("contract-type-not-perpetual")
    underlying_type = contract.get("underlyingType")
    if underlying_type != "COIN":
        normalized = str(underlying_type).upper()
        reason = (
            "forbidden-underlying-type"
            if normalized in FORBIDDEN_UNDERLYING_TYPES
            else "underlying-type-not-coin"
        )
        reasons.append(reason)
    if contract.get("quoteAsset") != "USDT":
        reasons.append("quote-asset-not-usdt")
    if contract.get("marginAsset") != "USDT":
        reasons.append("margin-asset-not-usdt")
    if base is not None and contract.get("baseAsset") != base:
        reasons.append("base-asset-mismatch")
    _normalized, subtype_reasons = _subtype_violations(contract.get("underlyingSubType"))
    reasons.extend(subtype_reasons)
    return tuple(dict.fromkeys(reasons))


def _load_parquet(payload: bytes, label: str) -> pd.DataFrame:
    try:
        frame = pd.read_parquet(io.BytesIO(payload), engine="pyarrow")
    except Exception as exc:
        raise PureCryptoUniverseError(f"cannot parse bound {label} parquet: {exc}") from exc
    if not isinstance(frame, pd.DataFrame):
        raise PureCryptoUniverseError(f"bound {label} did not decode to a dataframe")
    return frame


def _load_exchange_info(payload: bytes) -> Mapping[str, Any]:
    try:
        return _STRICT_JSON_OBJECT(payload, "pure-crypto exchange_info")
    except ValueError as exc:
        raise PureCryptoUniverseError(str(exc)) from exc


def _exchange_index(
    exchange_info: Mapping[str, Any],
) -> tuple[
    dict[str, Mapping[str, Any]],
    Counter[str],
    Counter[str],
    Counter[str],
    Counter[str],
    dict[str, list[str]],
    set[str],
]:
    symbols = exchange_info.get("symbols")
    expected_rows = _BINDING_BY_NAME["exchange_info"].rows
    if not isinstance(symbols, list) or len(symbols) != expected_rows:
        raise PureCryptoUniverseError("exchange_info symbol count differs from authority")
    index: dict[str, Mapping[str, Any]] = {}
    type_counts: Counter[str] = Counter()
    raw_subtype_counts: Counter[str] = Counter()
    normalized_subtype_counts: Counter[str] = Counter()
    forbidden_subtype_counts: Counter[str] = Counter()
    exclusion_reason_symbols: dict[str, list[str]] = {}
    eligible_symbols: set[str] = set()
    for position, raw in enumerate(symbols):
        if not isinstance(raw, Mapping):
            raise PureCryptoUniverseError(f"exchange_info symbol {position} is not an object")
        symbol = raw.get("symbol")
        if not isinstance(symbol, str) or not symbol or symbol in index:
            raise PureCryptoUniverseError("exchange_info symbols are invalid or duplicated")
        normalized_subtypes, subtype_reasons = _subtype_violations(raw.get("underlyingSubType"))
        if any(
            reason in {"underlying-subtypes-not-list", "underlying-subtype-invalid"}
            for reason in subtype_reasons
        ):
            raise PureCryptoUniverseError(f"exchange_info has malformed subtypes for {symbol}")
        index[symbol] = raw
        underlying_type = raw.get("underlyingType")
        type_counts[str(underlying_type) if underlying_type is not None else "<missing>"] += 1
        for raw_subtype, normalized in zip(
            raw.get("underlyingSubType", []), normalized_subtypes, strict=True
        ):
            raw_subtype_counts[raw_subtype] += 1
            normalized_subtype_counts[normalized] += 1
            if normalized in FORBIDDEN_UNDERLYING_SUBTYPES:
                forbidden_subtype_counts[normalized] += 1
        reasons = current_contract_violations(raw)
        if reasons:
            for reason in reasons:
                exclusion_reason_symbols.setdefault(reason, []).append(symbol)
        else:
            eligible_symbols.add(symbol)
    if tuple(index) != tuple(sorted(index)):
        raise PureCryptoUniverseError("exchange_info symbols are not canonically sorted")
    return (
        index,
        type_counts,
        raw_subtype_counts,
        normalized_subtype_counts,
        forbidden_subtype_counts,
        exclusion_reason_symbols,
        eligible_symbols,
    )


def _validate_metadata(
    metadata: pd.DataFrame, exchange_index: Mapping[str, Mapping[str, Any]]
) -> tuple[dict[str, str], set[str], set[str], list[str]]:
    expected = _BINDING_BY_NAME["contract_metadata"]
    if tuple(metadata.columns) != _METADATA_COLUMNS or len(metadata) != expected.rows:
        raise PureCryptoUniverseError("contract_metadata shape differs from authority")
    if not is_bool_dtype(metadata["is_crypto"]):
        raise PureCryptoUniverseError("contract_metadata.is_crypto is not boolean")
    symbols = metadata["symbol"].tolist()
    if (
        any(not isinstance(symbol, str) for symbol in symbols)
        or len(set(symbols)) != len(symbols)
        or symbols != sorted(symbols)
    ):
        raise PureCryptoUniverseError("contract_metadata symbols are invalid or unsorted")

    underlying_by_symbol: dict[str, str] = {}
    current_symbols: set[str] = set()
    archive_symbols: set[str] = set()
    accepted_rwa_symbols: list[str] = []
    for row in metadata.itertuples(index=False):
        symbol = row.symbol
        name_reasons = symbol_policy_violations(symbol)
        if name_reasons:
            raise PureCryptoUniverseError(
                f"contract_metadata rejects {symbol}: {', '.join(name_reasons)}"
            )
        if not bool(row.is_crypto):
            raise PureCryptoUniverseError(f"contract_metadata marks {symbol} non-crypto")
        current = exchange_index.get(symbol)
        if current is None:
            archive_symbols.add(symbol)
            expected_fields = (
                row.contract_type == "PERPETUAL"
                and row.quote_asset == "USDT"
                and row.margin_asset == "USDT"
                and row.underlying_type == "ARCHIVE_INFERRED_COIN"
                and row.metadata_source == "archive_inference"
            )
            if symbol not in REVIEWED_ARCHIVE_ONLY_CRYPTO or not expected_fields:
                raise PureCryptoUniverseError(
                    f"archive-only contract {symbol} lacks exact reviewed crypto authority"
                )
        else:
            current_symbols.add(symbol)
            reasons = current_contract_violations(current, expected_symbol=symbol)
            if reasons:
                raise PureCryptoUniverseError(
                    f"current contract {symbol} is not pure crypto: {', '.join(reasons)}"
                )
            expected_fields = (
                row.contract_type == current.get("contractType")
                and row.quote_asset == current.get("quoteAsset")
                and row.margin_asset == current.get("marginAsset")
                and row.underlying_type == current.get("underlyingType")
                and row.metadata_source == "current_exchangeInfo"
            )
            if not expected_fields:
                raise PureCryptoUniverseError(
                    f"contract_metadata disagrees with current exchangeInfo for {symbol}"
                )
            normalized_subtypes, _reasons = _subtype_violations(current.get("underlyingSubType"))
            if "rwa" in normalized_subtypes:
                accepted_rwa_symbols.append(symbol)
        underlying_by_symbol[symbol] = str(row.underlying_type)

    if archive_symbols != set(REVIEWED_ARCHIVE_ONLY_CRYPTO):
        missing = sorted(set(REVIEWED_ARCHIVE_ONLY_CRYPTO) - archive_symbols)
        extra = sorted(archive_symbols - set(REVIEWED_ARCHIVE_ONLY_CRYPTO))
        raise PureCryptoUniverseError(
            f"archive-only reviewed set differs: missing={missing}, extra={extra}"
        )
    if current_symbols & archive_symbols or len(current_symbols | archive_symbols) != len(metadata):
        raise PureCryptoUniverseError("contract_metadata source partition is invalid")
    return underlying_by_symbol, current_symbols, archive_symbols, accepted_rwa_symbols


def _validate_membership(
    membership: pd.DataFrame,
    underlying_by_symbol: Mapping[str, str],
    exchange_index: Mapping[str, Mapping[str, Any]],
    archive_symbols: set[str],
) -> tuple[set[str], list[str]]:
    expected = _BINDING_BY_NAME["membership"]
    if tuple(membership.columns) != _MEMBERSHIP_COLUMNS or len(membership) != expected.rows:
        raise PureCryptoUniverseError("membership shape differs from authority")
    symbols = membership["symbol"].tolist()
    if any(not isinstance(symbol, str) for symbol in symbols):
        raise PureCryptoUniverseError("membership contains a non-string symbol")
    member_symbols = set(symbols)
    if not member_symbols or not member_symbols.issubset(underlying_by_symbol):
        raise PureCryptoUniverseError("membership contains an unknown contract_metadata symbol")
    if any(symbol_policy_violations(symbol) for symbol in member_symbols):
        raise PureCryptoUniverseError("membership contains a rejected symbol name")

    times = pd.to_datetime(membership["reconstitution_time"], utc=True, errors="coerce")
    if times.isna().any() or not is_integer_dtype(membership["liquidity_rank"]):
        raise PureCryptoUniverseError("membership time or rank columns are invalid")
    if (membership["liquidity_rank"] < 1).any():
        raise PureCryptoUniverseError("membership contains a nonpositive liquidity rank")
    normalized = membership.assign(reconstitution_time=times)
    if (
        normalized.duplicated(["reconstitution_time", "symbol"]).any()
        or normalized.duplicated(["reconstitution_time", "liquidity_rank"]).any()
    ):
        raise PureCryptoUniverseError("membership contains a duplicate symbol or rank")
    _validate_membership_ranks(normalized)

    accepted_rwa_symbols: list[str] = []
    for symbol in sorted(member_symbols - archive_symbols):
        current = exchange_index.get(symbol)
        if current is None:
            raise PureCryptoUniverseError(f"current membership contract {symbol} is missing")
        reasons = current_contract_violations(current, expected_symbol=symbol)
        if reasons:
            raise PureCryptoUniverseError(
                f"membership contract {symbol} is not pure crypto: {', '.join(reasons)}"
            )
        normalized_subtypes, _reasons = _subtype_violations(current.get("underlyingSubType"))
        if "rwa" in normalized_subtypes:
            accepted_rwa_symbols.append(symbol)
    return member_symbols, accepted_rwa_symbols


def _validate_membership_ranks(membership: pd.DataFrame) -> None:
    """Require each legitimate early or mature reconstitution to rank 1..N, with N <= 40."""

    for reconstitution_time, frame in membership.groupby(
        "reconstitution_time", observed=True, sort=True
    ):
        ranks = sorted(int(value) for value in frame["liquidity_rank"])
        if not ranks or len(ranks) > 40 or ranks != list(range(1, len(ranks) + 1)):
            raise PureCryptoUniverseError(
                f"membership ranks are not contiguous 1..N (N <= 40) at {reconstitution_time}"
            )


def _sorted_counts(values: Counter[str]) -> dict[str, int]:
    return {key: int(values[key]) for key in sorted(values)}


def _symbol_set_record(symbols: set[str] | frozenset[str]) -> dict[str, Any]:
    ordered = sorted(symbols)
    payload = json.dumps(ordered, allow_nan=False, ensure_ascii=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return {
        "count": len(ordered),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "symbols": ordered,
    }


def _classification_cohort(
    *, denominator: str, denominator_count: int, symbols: list[str] | set[str]
) -> dict[str, Any]:
    record = _symbol_set_record(set(symbols))
    return {
        "denominator": denominator,
        "denominator_count": denominator_count,
        **record,
    }


def _policy_sha256() -> str:
    policy = {
        "current_contract_type": "PERPETUAL",
        "current_underlying_type": "COIN",
        "forbidden_underlying_subtypes": sorted(FORBIDDEN_UNDERLYING_SUBTYPES),
        "forbidden_underlying_types": sorted(FORBIDDEN_UNDERLYING_TYPES),
        "leveraged_bases": sorted(LEVERAGED_BASES),
        "non_crypto_bases": sorted(NON_CRYPTO_BASES),
        "reviewed_archive_only_crypto": sorted(REVIEWED_ARCHIVE_ONLY_CRYPTO),
        "stable_bases": sorted(STABLE_BASES),
        "symbol_pattern": _SYMBOL.pattern,
    }
    payload = json.dumps(
        policy, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_pure_crypto_universe(root: str | Path) -> dict[str, Any]:
    """Audit the exact frozen snapshot and return a byte-deterministic success report."""

    root_path = Path(root).resolve()
    _verify_integrity_authority()
    manifest, manifest_bytes = _read_manifest(root_path)
    _validate_manifest_bindings(manifest)

    payloads = {
        binding.name: _read_bound_file(root_path, binding) for binding in SNAPSHOT_FILE_BINDINGS
    }
    metadata = _load_parquet(payloads["contract_metadata"], "contract_metadata")
    membership = _load_parquet(payloads["membership"], "membership")
    exchange_info = _load_exchange_info(payloads["exchange_info"])
    (
        exchange_index,
        type_counts,
        raw_subtype_counts,
        normalized_subtype_counts,
        forbidden_subtype_counts,
        exclusion_reason_symbols,
        eligible_exchange_symbols,
    ) = _exchange_index(exchange_info)
    (
        underlying_by_symbol,
        current_symbols,
        archive_symbols,
        metadata_rwa_symbols,
    ) = _validate_metadata(metadata, exchange_index)
    member_symbols, membership_rwa_symbols = _validate_membership(
        membership,
        underlying_by_symbol,
        exchange_index,
        archive_symbols,
    )

    metadata_type_counts = Counter(underlying_by_symbol.values())
    membership_type_counts = Counter(underlying_by_symbol[symbol] for symbol in member_symbols)
    non_coin_counts = Counter({key: value for key, value in type_counts.items() if key != "COIN"})
    all_metadata_symbols = set(underlying_by_symbol)
    current_member_symbols = member_symbols - archive_symbols
    archive_member_symbols = member_symbols & archive_symbols
    exchange_denominator = "all frozen current exchangeInfo symbols"
    metadata_denominator = "all frozen contract_metadata symbols"
    membership_denominator = "all distinct frozen membership symbols"
    report: dict[str, Any] = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "policy_id": POLICY_ID,
        "policy_sha256": _policy_sha256(),
        "status": "passed",
        "authorities": {
            "data_manifest": {
                "path": DATA_MANIFEST_PATH,
                "sha256": DATA_MANIFEST_SHA256,
                "size": DATA_MANIFEST_SIZE,
            },
            **{
                binding.name: {
                    "path": binding.path,
                    "rows": binding.rows,
                    "sha256": binding.sha256,
                    "size": binding.size,
                }
                for binding in SNAPSHOT_FILE_BINDINGS
            },
        },
        "counts": {
            "archive_only_metadata_symbols": len(archive_symbols),
            "contract_metadata_rows": len(metadata),
            "contract_metadata_symbols": len(underlying_by_symbol),
            "current_exchange_eligible_pure_crypto_contracts": len(eligible_exchange_symbols),
            "current_exchange_non_coin_contracts": sum(non_coin_counts.values()),
            "current_exchange_symbols": len(exchange_index),
            "current_metadata_symbols": len(current_symbols),
            "data_manifest_files": len(manifest["files"]),
            "membership_archive_only_symbols": len(member_symbols & archive_symbols),
            "membership_current_symbols": len(member_symbols - archive_symbols),
            "membership_rows": len(membership),
            "membership_symbols": len(member_symbols),
            "violations": 0,
        },
        "accepted_symbol_sets": {
            "all_contract_metadata": _symbol_set_record(all_metadata_symbols),
            "archive_only_contract_metadata": _symbol_set_record(archive_symbols),
            "current_contract_metadata": _symbol_set_record(current_symbols),
            "all_membership": _symbol_set_record(member_symbols),
            "archive_only_membership": _symbol_set_record(archive_member_symbols),
            "current_membership": _symbol_set_record(current_member_symbols),
            "eligible_current_exchange": _symbol_set_record(eligible_exchange_symbols),
        },
        "classifications": {
            "accepted_rwa_sector_metadata_symbols": sorted(metadata_rwa_symbols),
            "accepted_rwa_sector_membership_symbols": sorted(membership_rwa_symbols),
            "current_exchange_exclusion_cohorts": {
                reason: _classification_cohort(
                    denominator=exchange_denominator,
                    denominator_count=len(exchange_index),
                    symbols=symbols,
                )
                for reason, symbols in sorted(exclusion_reason_symbols.items())
            },
            "current_exchange_forbidden_subtype_counts": {
                "denominator": exchange_denominator,
                "denominator_count": len(exchange_index),
                "counts": _sorted_counts(forbidden_subtype_counts),
            },
            "current_exchange_non_coin_by_underlying_type": {
                "denominator": exchange_denominator,
                "denominator_count": len(exchange_index),
                "counts": _sorted_counts(non_coin_counts),
            },
            "current_exchange_normalized_subtype_vocabulary": {
                "denominator": exchange_denominator,
                "denominator_count": len(exchange_index),
                "counts": _sorted_counts(normalized_subtype_counts),
            },
            "current_exchange_raw_subtype_vocabulary": {
                "denominator": exchange_denominator,
                "denominator_count": len(exchange_index),
                "counts": _sorted_counts(raw_subtype_counts),
            },
            "current_exchange_underlying_type_counts": {
                "denominator": exchange_denominator,
                "denominator_count": len(exchange_index),
                "counts": _sorted_counts(type_counts),
            },
            "metadata_underlying_type_counts": {
                "denominator": metadata_denominator,
                "denominator_count": len(all_metadata_symbols),
                "counts": _sorted_counts(metadata_type_counts),
            },
            "membership_underlying_type_counts": {
                "denominator": membership_denominator,
                "denominator_count": len(member_symbols),
                "counts": _sorted_counts(membership_type_counts),
            },
        },
        "archive_only_symbols": sorted(archive_symbols),
        "violations": [],
    }

    # Recheck the authority after all parsing and require the manifest to remain byte-identical.
    final_manifest, final_manifest_bytes = _read_manifest(root_path)
    if final_manifest_bytes != manifest_bytes or final_manifest != manifest:
        raise PureCryptoUniverseError("data manifest changed during pure-crypto audit")
    _verify_integrity_authority()
    return report


def audit_report_bytes(root: str | Path) -> bytes:
    """Return the canonical deterministic audit report bytes without writing a file."""

    return _PRETTY_JSON_BYTES(audit_pure_crypto_universe(root))


def audit_report_sha256(root: str | Path) -> str:
    """Return the SHA-256 of the canonical deterministic audit report."""

    return _SHA256_BYTES(audit_report_bytes(root))
