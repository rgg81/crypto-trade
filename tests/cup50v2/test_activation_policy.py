"""What activation binds, and what it deliberately does not."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REQUIRED = {
    "focused_suite",
    "full_pytest",
    "ruff",
    "deterministic_worker_counts",
    "deterministic_hash_seeds",
    "full_is_readiness_field",
    "clean_room_workspace_scan",
    "sandbox_isolation_smoke",
}


def _activate(tmp_path: Path, preflight: dict, monkeypatch) -> None:
    import argparse

    from crypto_trade.cup50v2 import cli

    path = tmp_path / "preflight.json"
    path.write_text(json.dumps(preflight))
    monkeypatch.setattr(cli, "require_isolation_available", lambda **_: "25.0.1")
    monkeypatch.setattr(cli, "require_image_digest", lambda *a, **k: "sha256:" + "a" * 64)
    monkeypatch.setattr(cli, "verify_receipt", lambda *a, **k: {})
    cli._activate(
        argparse.Namespace(
            sandbox_image="cup50v2-evaluator:test",
            sandbox_image_digest="sha256:" + "a" * 64,
            quarantine_receipt=str(tmp_path / "receipt.json"),
            preflight=str(path),
            repository_root=str(tmp_path),
        )
    )


def test_an_incomplete_preflight_is_refused(tmp_path: Path, monkeypatch) -> None:
    partial = {name: "passed" for name in REQUIRED - {"sandbox_isolation_smoke"}}
    with pytest.raises(ValueError, match="preflight is incomplete"):
        _activate(tmp_path, partial, monkeypatch)


def test_a_failed_check_is_refused(tmp_path: Path, monkeypatch) -> None:
    failing = {name: "passed" for name in REQUIRED}
    failing["full_is_readiness_field"] = "failed"
    with pytest.raises(ValueError, match="preflight is incomplete"):
        _activate(tmp_path, failing, monkeypatch)


def test_the_paper_parity_smoke_is_not_an_activation_check() -> None:
    """It gates launching a desk, not running the field.

    The desk is downstream of the release and is not bound by the activation record, so requiring
    it here would force the desk to exist before any research happened and buy no integrity.
    """
    source = Path("src/crypto_trade/cup50v2/cli.py").read_text()
    start = source.index("required_checks = {")
    block = source[start : source.index("}", start)]
    assert "paper_backtest_parity_smoke" not in block
    assert "sandbox_isolation_smoke" in block


def test_the_recorded_sandbox_probe_shows_real_isolation() -> None:
    """The preflight evidence has to say the container was actually confined."""
    probe = json.loads(
        Path("tournament/cup50v2/preflight/docker-isolation-smoke.txt").read_text().strip()
    )
    assert probe["network_reachable"] is False
    assert probe["organizer_execution_visible"] is False
    assert probe["protocol_read_only"] is True
    assert probe["team_read_only"] is True
    assert probe["output_writable"] is True
    assert probe["toolkit_importable"] is True
    # The team snapshot carries no execution marks; the open is stripped at export.
    assert "mark_prices.parquet" not in probe["snapshot_files"]
