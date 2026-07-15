from __future__ import annotations

from pathlib import Path

from crypto_trade.tournament import _strategy_worker_v2, runner_v2


def test_v2_worker_masks_both_tournaments_and_private_records(tmp_path: Path):
    sensitive = {
        path.relative_to(tmp_path).as_posix()
        for path in _strategy_worker_v2._sensitive_paths(tmp_path)
        if path.is_relative_to(tmp_path)
    }

    assert "tournament/top40" in sensitive
    assert "reports-top40" in sensitive
    assert "tournament/top40-v2/private" in sensitive
    assert "tournament/top40-v2/teams" in sensitive
    assert "reports-top40-v2" in sensitive


def test_v2_runner_launches_only_the_v2_worker(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runner_v2.shutil, "which", lambda _name: "/usr/bin/unshare")
    command = runner_v2._strategy_worker_command(
        tmp_path,
        tmp_path.parent,
        tmp_path / "bundle",
        tmp_path / "site-packages",
        tmp_path / "runtime-site-packages",
        "strategy.py",
        tmp_path / "empty-dir",
        tmp_path / "empty-file",
    )

    module_index = command.index("-m") + 1
    assert command[module_index] == "crypto_trade.tournament._strategy_worker_v2"


def test_worker_environment_does_not_inherit_organizer_credentials(monkeypatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("HTTPS_PROXY", "http://secret.invalid")

    environment = runner_v2._strategy_worker_environment(7)

    assert "AWS_SECRET_ACCESS_KEY" not in environment
    assert "HTTPS_PROXY" not in environment
    assert environment["PYTHONHASHSEED"] == "7"
