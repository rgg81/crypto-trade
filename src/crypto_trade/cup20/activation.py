"""Activation freeze: one record binding every authority before the first result.

The record is the tournament's root of trust. Everything a result could later be argued about --
the policy, the charter the teams read, the evaluation code, the two data windows, the audit that
cleared the universe, the interpreter's dependency set and the test run that declared the machinery
sound -- is reduced to one digest each here, before any team has seen a number. After activation,
any of those changing is a fact about the tournament, not a detail: ``verify_activation`` recomputes
every one of them from the same paths and refuses to agree.

The record itself is deliberately NOT self-authenticating -- a digest of the record inside the
record proves nothing. Its integrity comes from being committed to version control at freeze time;
the digests inside it are what make everything *else* immutable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from crypto_trade.cup20.archive import bundle_digest
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.snapshot import load_snapshot

# Every bound authority, in record order, paired with the label used to attribute drift. Adding a
# row here is the only way to bind a new authority, and tests/cup20/test_activation.py asserts its
# own mutation table covers this tuple exactly -- so a new authority cannot ship unverified.
#
# The list is the charter's own sentence, item for item: "an activation record hash-binds this
# charter, the config, the implementation, the dependency lock, the data authority, the pure-crypto
# audit and the focused test output". "The data authority" is the two snapshot manifests -- the
# bytes the tournament actually evaluates against, on both sides of the cutoff.
_AUTHORITIES: tuple[tuple[str, str], ...] = (
    ("config_sha256", "config"),
    ("charter_sha256", "charter"),
    ("implementation_sha256", "implementation"),
    ("is_manifest_sha256", "IS snapshot"),
    ("sealed_manifest_sha256", "sealed snapshot"),
    ("pure_crypto_audit_sha256", "pure-crypto audit"),
    ("dependency_lock_sha256", "dependency lock"),
    ("test_output_sha256", "test output"),
)

# The paths ``verify_activation`` re-reads. Stored as given -- relative paths stay relative, so a
# record frozen from the repository root must also be verified from the repository root.
_PATH_FIELDS: tuple[str, ...] = (
    "config_path",
    "charter_path",
    "implementation_root",
    "is_root",
    "sealed_root",
    "pure_crypto_audit_path",
    "dependency_lock_path",
    "test_output_path",
)

_REQUIRED_FIELDS: tuple[str, ...] = tuple(key for key, _ in _AUTHORITIES) + _PATH_FIELDS
_HEX_DIGITS = frozenset("0123456789abcdef")

# ``bundle_digest`` over a tree with no files. Not an error inside ``archive.py`` -- an empty team
# submission is a legitimate thing for it to describe -- but as an ACTIVATION authority it is a
# fail-open: a mistyped or unmounted implementation root would hash to this constant and freeze
# cleanly while binding nothing at all.
_EMPTY_BUNDLE_DIGEST = hashlib.sha256().hexdigest()


def _digest(path: Path) -> str:
    """SHA-256 of a file's exact bytes. Propagates ``FileNotFoundError``, which names the path."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _implementation_digest(root: Path) -> str:
    """Bundle digest of the evaluation code, with the empty-tree fail-open closed."""
    if not root.is_dir():
        raise FileNotFoundError(f"implementation root is not a directory: {root}")
    digest = bundle_digest(root)
    if digest == _EMPTY_BUNDLE_DIGEST:
        raise ValueError(f"implementation root contains no files: {root}")
    return digest


def _snapshot_digest(root: Path, label: str) -> str:
    """The snapshot's manifest digest, RECOMPUTED from the files on disk.

    Reading ``manifest.json``'s ``manifest_sha256`` field and hashing that would bind the
    snapshot's own *claim* about its contents rather than the contents: swapping ``bars.parquet``
    while leaving ``manifest.json`` alone would leave the claim, and any digest of it, byte-for-byte
    unchanged. ``load_snapshot`` recomputes every file's digest and rejects the snapshot if the
    manifest's claim disagrees, so the value returned here is only ever a digest of data that was
    verified to be present and intact at this moment.

    That rejection is re-raised carrying ``label`` because it IS the drift signal for a swapped
    file, and it arrives before the comparison loop below ever runs -- without the label an
    operator would be told a snapshot is inconsistent but not which of the two.
    """
    try:
        return load_snapshot(root).manifest_sha256
    except ValueError as error:
        raise ValueError(f"{label} at {root} does not match its own manifest: {error}") from error


def build_activation_record(
    config_path: str | Path,
    charter_path: str | Path,
    is_root: str | Path,
    sealed_root: str | Path,
    test_output: str | Path,
    dependency_lock: str | Path = "uv.lock",
    implementation_root: str | Path = "src/crypto_trade/cup20",
    # Organiser-only. The audit necessarily names every universe member, including the sixteen that
    # enter only during the holdout, and reports which members had already delisted at build time
    # -- the exact fact snapshot.py censors out of the IS contract metadata. It stays a bound
    # authority, from a path teams are prohibited from reading, rather than being restricted to IS
    # members: an attestation over 63 of 79 members would no longer be the attestation the charter
    # claims, and would not close the leak anyway, since the post-cutoff delisters are IS members.
    pure_crypto_audit: str | Path = "tournament/cup20/private/pure-crypto-audit.json",
    *,
    sealed_root_override: str | Path | None = None,
) -> dict[str, str]:
    """Hash-bind charter, config, implementation, data authorities, audit, lock and test output.

    ``config_path`` is loaded through ``load_config``, not merely hashed: an authority that fails
    its own validation is drift already, and freezing its digest would notarise the drift instead
    of catching it.

    ``sealed_root_override`` changes only WHERE the sealed snapshot is read from; the record still
    carries ``sealed_root`` as the path the contract names. It exists for the same window as
    :func:`verify_activation`'s override -- once ``crypto_trade.cup20.quarantine`` has moved the
    sealed tree out of the working tree, an amendment that has to be re-frozen cannot read it at
    the contract path, and the alternative (recording the quarantine path) would write a location
    into the record that stops existing the moment the holdout comes back. It cannot weaken the
    freeze: the digest is still whatever the tree it points at actually hashes to, and
    ``quarantine.verify_quarantine_in_effect`` is what establishes that nothing is sitting at the
    contract path in its place.
    """
    is_manifest = _snapshot_digest(Path(is_root), "IS snapshot")
    sealed_digest_root = Path(sealed_root if sealed_root_override is None else sealed_root_override)
    sealed_manifest = _snapshot_digest(sealed_digest_root, "sealed snapshot")
    if is_manifest == sealed_manifest:
        # Two roots resolving to one snapshot means either the teams were handed the sealed window
        # or the holdout was handed the in-sample one. Refuse to notarise it.
        raise ValueError("IS and sealed snapshots must have distinct manifest digests")
    return {
        "config_sha256": load_config(config_path).sha256,
        "charter_sha256": _digest(Path(charter_path)),
        "implementation_sha256": _implementation_digest(Path(implementation_root)),
        "is_manifest_sha256": is_manifest,
        "sealed_manifest_sha256": sealed_manifest,
        "pure_crypto_audit_sha256": _digest(Path(pure_crypto_audit)),
        "dependency_lock_sha256": _digest(Path(dependency_lock)),
        "test_output_sha256": _digest(Path(test_output)),
        "config_path": str(config_path),
        "charter_path": str(charter_path),
        "implementation_root": str(implementation_root),
        "is_root": str(is_root),
        "sealed_root": str(sealed_root),
        "pure_crypto_audit_path": str(pure_crypto_audit),
        "dependency_lock_path": str(dependency_lock),
        "test_output_path": str(test_output),
    }


def _load_record(path: Path) -> dict[str, str]:
    """Parse a frozen record and reject any shape that would make the comparison below unsound."""
    payload: Any = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"activation record {path} must be a JSON object")
    for field in _REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError(f"activation record {path} is missing {field}")
        value = payload[field]
        if not isinstance(value, str):
            raise ValueError(f"activation record {path} field {field} must be a string")
    for key, _ in _AUTHORITIES:
        value = payload[key]
        if len(value) != 64 or not set(value) <= _HEX_DIGITS:
            raise ValueError(f"activation record {path} field {key} is not a SHA-256 digest")
    return payload


def verify_activation(
    path: str | Path, *, sealed_root_override: str | Path | None = None
) -> dict[str, str]:
    """Recompute every bound authority and fail on any drift.

    Returns the frozen record unchanged when every authority still matches, so a caller can use the
    return value as the authoritative record without re-reading the file.

    ``sealed_root_override`` changes only WHERE the sealed snapshot is read from -- never what it
    must hash to. It exists for the window in which ``crypto_trade.cup20.quarantine`` has moved the
    sealed tree out of the working tree entirely: without it, the single most important check in
    this module would be unavailable for the whole research phase, which is exactly when the
    organiser most needs to be able to run it. It cannot weaken the verification, because the
    comparison below is still against the digest frozen before any team started: a tampered tree
    pointed at by an override fails just as loudly as one in place. What it CAN do is verify a
    pristine copy while a tampered copy sits at the record's own ``sealed_root`` -- so it is only
    sound in combination with ``quarantine.verify_quarantine_in_effect``, which asserts that no
    tree exists at that path at all, and ``quarantine.restore_holdout`` calls this a second time
    with no override once the tree is back.
    """
    record_path = Path(path)
    record = _load_record(record_path)
    current = build_activation_record(
        record["config_path"],
        record["charter_path"],
        record["is_root"],
        record["sealed_root"],
        record["test_output_path"],
        record["dependency_lock_path"],
        record["implementation_root"],
        record["pure_crypto_audit_path"],
        sealed_root_override=sealed_root_override,
    )
    for key, label in _AUTHORITIES:
        if current[key] != record[key]:
            raise ValueError(f"activation authority changed: {label}")
    return record
