"""Append-only custody for the roots the organizer must write into.

Freezing `private` made a receipt that had to fail as soon as the tournament ran: the directory
collects transcript audits, adjudications, falsifier evidence, dispositions, and during observation
one evidence file per point. A check that must fail when the process works is worse than no check,
because it teaches the operator to wave the failure through. These tests pin the invariant that
replaced it -- gaining records is fine, losing or rewriting one is not.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.cup50v2.quarantine import create_receipt, verify_receipt


def _root(tmp_path: Path, name: str, files: dict[str, str]) -> Path:
    root = tmp_path / name
    root.mkdir(parents=True, exist_ok=True)
    for filename, body in files.items():
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    return root


REQUIRED = ("acquisition", "caches", "private", "reports", "sealed")


def _receipt(tmp_path: Path, roots: dict[str, Path]) -> Path:
    """A receipt must cover all five roots, so unnamed ones get an empty directory."""
    complete = dict(roots)
    for name in REQUIRED:
        complete.setdefault(name, _root(tmp_path, name, {}))
    path = tmp_path / "receipt.json"
    create_receipt(path, roots={name: str(value) for name, value in complete.items()})
    return path


def test_a_new_record_in_an_append_only_root_is_allowed(tmp_path: Path) -> None:
    private = _root(tmp_path, "private", {"audits/team-01.json": "{}"})
    sealed = _root(tmp_path, "sealed", {"bars.parquet": "frozen"})
    receipt = _receipt(tmp_path, {"private": private, "sealed": sealed})

    (private / "audits" / "team-02.json").write_text("{}")
    (private / "observation.jsonl").write_text('{"event": "point-start"}\n')
    verify_receipt(receipt)  # the shape the real field produced: 39 added, none touched


def test_rewriting_an_existing_record_is_still_caught(tmp_path: Path) -> None:
    private = _root(tmp_path, "private", {"audits/team-01.json": json.dumps({"status": "finding"})})
    receipt = _receipt(tmp_path, {"private": private})

    (private / "audits" / "team-01.json").write_text(json.dumps({"status": "clean"}))
    with pytest.raises(ValueError, match="rewrote records"):
        verify_receipt(receipt)


def test_deleting_an_existing_record_is_still_caught(tmp_path: Path) -> None:
    private = _root(tmp_path, "private", {"audits/team-01.json": "{}", "keep.json": "{}"})
    receipt = _receipt(tmp_path, {"private": private})

    (private / "audits" / "team-01.json").unlink()
    with pytest.raises(ValueError, match="lost records"):
        verify_receipt(receipt)


def test_a_frozen_root_still_admits_nothing_at_all(tmp_path: Path) -> None:
    """The relaxation must not have leaked into the roots it was never meant to touch."""
    sealed = _root(tmp_path, "sealed", {"bars.parquet": "frozen"})
    receipt = _receipt(tmp_path, {"sealed": sealed})

    (sealed / "extra.parquet").write_text("new")
    with pytest.raises(ValueError, match="drifted"):
        verify_receipt(receipt)
