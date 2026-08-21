"""A frozen bundle's digest must be a property of its source, not of what has run there.

source_bundle_digest hashes every file under the bundle via rglob("*"), so a stray
__pycache__/*.pyc changes it. The paper desk re-verifies that digest on EVERY tick, which means a
single in-place import would stop a desk with "strategy changed; start a new lineage" -- days
later, intermittently, and looking exactly like tampering.

This nearly happened: an early version of the ensemble test exec'd the bundle in place and left a
.pyc inside it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.cup50v2.trials import source_bundle_digest

TEAMS = Path("tournament/cup50v2/teams")
NOMINATIONS = Path("tournament/cup50v2/nominations")


def _bundles() -> list[Path]:
    return sorted(path for path in TEAMS.glob("*") if path.is_dir())


@pytest.mark.parametrize("bundle", _bundles(), ids=lambda p: p.name)
def test_no_frozen_bundle_carries_bytecode_or_build_artifacts(bundle: Path) -> None:
    strays = [
        item.relative_to(bundle).as_posix()
        for item in bundle.rglob("*")
        if item.is_file() and (item.suffix == ".pyc" or "__pycache__" in item.parts)
    ]
    assert not strays, f"{bundle.name} carries build artifacts that change its digest: {strays}"


@pytest.mark.parametrize("bundle", _bundles(), ids=lambda p: p.name)
def test_a_nominated_bundle_still_hashes_to_what_it_nominated(bundle: Path) -> None:
    """The repository copy is what the desk binds to, so it must still be the frozen bytes."""
    nomination = NOMINATIONS / f"{bundle.name}.json"
    if not nomination.is_file():
        pytest.skip(f"{bundle.name} is organizer-written, not a nominated lane")
    expected = json.loads(nomination.read_text())["source_bundle_sha256"]
    assert source_bundle_digest(bundle) == expected


def test_the_digest_really_does_move_when_a_stray_file_appears(tmp_path: Path) -> None:
    """The reason the two tests above are worth having, demonstrated rather than asserted."""
    bundle = tmp_path / "bundle"
    (bundle / "__pycache__").mkdir(parents=True)
    (bundle / "strategy.py").write_text("def build_strategy():\n    return None\n")
    before = source_bundle_digest(bundle)
    (bundle / "__pycache__" / "strategy.cpython-313.pyc").write_bytes(b"\x00bytecode")
    assert source_bundle_digest(bundle) != before
