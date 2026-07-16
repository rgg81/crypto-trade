"""Draft pure-crypto preflight wrapper for every Top-40 V2 command."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from crypto_trade.tournament import (
    amendment_integrity_v2,
    pure_crypto_universe_v6,
    runner_schema3_compat_v4,
)

AMENDMENT_ID = pure_crypto_universe_v6.AMENDMENT_ID
AMENDMENT_ROOT = "tournament/top40-v2/amendments/0006"
SPEC_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"

PARENT_AUTHORITIES = {
    "amendment_0004_active_runner_sha256": (
        "03006ea1ce391ef3c8da6244acb89aab19f7e63d1e0a617e2743894a575fd6cd"
    ),
    "amendment_0004_freeze_sha256": (
        "bfb9e82c0b9a0950ead9b94ae61fe9f6c091462b106e46bd51113894b6eb9465"
    ),
}

IMPLEMENTATION_FILE_PATHS = (
    "scripts/top40_v2_tournament_pure_crypto_v6.py",
    "src/crypto_trade/tournament/amendment_0006_v2.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "tests/tournament/test_top40_v2_amendment_0006.py",
    SPEC_PATH,
)

_A4_MODULE = runner_schema3_compat_v4
_A4_RUN = _A4_MODULE.run
_A4_VERIFY = _A4_MODULE._verify_amendment_authorities
_PURE_MODULE = pure_crypto_universe_v6
_PURE_AUDIT = _PURE_MODULE.audit_pure_crypto_universe
_PURE_REPORT_BYTES = _PURE_MODULE.audit_report_bytes
_PURE_REPORT_SHA256 = _PURE_MODULE.audit_report_sha256
_PURE_MODULE_SHA256 = "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192"
_PURE_MODULE_SIZE = 34_031
_READ_REPO_FILE = amendment_integrity_v2.read_repo_file
_SHA256_BYTES = amendment_integrity_v2.sha256_bytes


class Amendment0006Error(ValueError):
    """The draft pure-crypto wrapper failed closed."""


def _bound_repo_bytes(
    root: Path, relative: str, expected_sha256: str, expected_size: int, label: str
) -> bytes:
    try:
        observed, _path, payload, info = _READ_REPO_FILE(
            root,
            relative,
            label,
            maximum_bytes=expected_size,
            require_single_link=True,
        )
    except (OSError, ValueError) as exc:
        raise Amendment0006Error(f"cannot read {label}: {exc}") from exc
    if (
        observed != relative
        or info.st_size != expected_size
        or len(payload) != expected_size
        or _SHA256_BYTES(payload) != expected_sha256
    ):
        raise Amendment0006Error(f"{label} differs from frozen authority")
    return payload


def verify_parent_authorities(root: str | Path) -> None:
    """Verify the exact frozen runner delegated to by this additive draft."""

    root_path = Path(root).resolve()
    _bound_repo_bytes(
        root_path,
        "src/crypto_trade/tournament/runner_schema3_compat_v4.py",
        PARENT_AUTHORITIES["amendment_0004_active_runner_sha256"],
        12_114,
        "Amendment 0004 active runner",
    )
    _bound_repo_bytes(
        root_path,
        "tournament/top40-v2/amendments/0004/freeze.json",
        PARENT_AUTHORITIES["amendment_0004_freeze_sha256"],
        1_865,
        "Amendment 0004 freeze",
    )
    _bound_repo_bytes(
        root_path,
        "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
        _PURE_MODULE_SHA256,
        _PURE_MODULE_SIZE,
        "Amendment 0006 pure-crypto audit module",
    )
    if _A4_MODULE.run is not _A4_RUN or _A4_MODULE._verify_amendment_authorities is not _A4_VERIFY:
        raise Amendment0006Error("Amendment 0004 callable identity changed")
    pure_identities = {
        "audit_pure_crypto_universe": _PURE_AUDIT,
        "audit_report_bytes": _PURE_REPORT_BYTES,
        "audit_report_sha256": _PURE_REPORT_SHA256,
    }
    if any(
        getattr(_PURE_MODULE, name, None) is not value for name, value in pure_identities.items()
    ):
        raise Amendment0006Error("Amendment 0006 pure-crypto callable identity changed")
    _A4_VERIFY()


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Audit before and after delegating every command to the exact Amendment 0004 runner.

    This is a reviewed-wrapper candidate only.  No active entrypoint imports it, and its presence
    alone does not activate Amendment 0006.
    """

    values = list(sys.argv[1:] if argv is None else argv)
    root_path = Path.cwd().resolve() if root is None else Path(root).resolve()
    verify_parent_authorities(root_path)
    before = _PURE_REPORT_BYTES(root_path)

    result: int | None = None
    failure: BaseException | None = None
    try:
        result = int(_A4_RUN(values, root=root_path))
    except BaseException as exc:
        failure = exc

    try:
        after = _PURE_REPORT_BYTES(root_path)
        if after != before:
            raise Amendment0006Error("pure-crypto audit report changed during delegation")
        verify_parent_authorities(root_path)
    except BaseException as integrity_failure:
        raise integrity_failure from failure

    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    if result is None:
        raise Amendment0006Error("delegated command returned no result")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Run the reviewed wrapper with the same fail-closed CLI surface as Amendment 0004."""

    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-pure-crypto: error: {exc}", file=sys.stderr)
        return 2
