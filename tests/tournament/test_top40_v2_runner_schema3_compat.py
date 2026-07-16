from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_trade.tournament.runner_schema3_compat_v4 as compat


def test_active_status_delegates_to_frozen_amendment_0003(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []
    monkeypatch.setattr(
        compat.amended_orchestrator_compat_v3,
        "run",
        lambda argv, *, root: observed.append((argv, root)) or 4,
    )

    assert compat.run(["research-status", "team-01"], root=root) == 4
    assert observed == [(["research-status", "team-01"], root)]


def test_non_runner_command_delegates_without_contract_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []

    class Adapter:
        def run(self, argv: Any, *, root: Any) -> int:
            observed.append((argv, root, compat.runner_v2.tournament_contract))
            return 6

    monkeypatch.setattr(
        compat.amended_orchestrator_compat_v3,
        "_load_frozen_adapter",
        lambda: Adapter(),
    )

    assert compat.run(["register-family", "team-03", "input.json"], root=root) == 6
    assert observed[0][0:2] == (["register-family", "team-03", "input.json"], root)
    assert observed[0][2] is compat.top40_v2


def test_development_command_uses_runner_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []

    class Adapter:
        def run(self, argv: Any, *, root: Any) -> int:
            observed.append(("adapter", argv, root))
            return 8

    def wrapper(*, root: Any, runner_call: Any, expected_state_validations: int = 1) -> int:
        observed.append(("wrapper", root, expected_state_validations))
        return runner_call()

    monkeypatch.setattr(
        compat.amended_orchestrator_compat_v3,
        "_load_frozen_adapter",
        lambda: Adapter(),
    )
    monkeypatch.setattr(compat, "run_with_schema3_runner_compatibility", wrapper)

    values = ["run-window", "development", "team-01", "candidate"]
    assert compat.run(values, root=root) == 8
    assert observed == [
        ("wrapper", root, 1),
        ("adapter", values, root),
    ]


def test_private_and_finalist_runner_paths_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    monkeypatch.setattr(
        compat.amended_orchestrator_compat_v3,
        "_load_frozen_adapter",
        lambda: SimpleNamespace(run=lambda *_args, **_kwargs: 0),
    )

    with pytest.raises(ValueError, match="only for development"):
        compat.run(["run-window", "private", "team-01", "candidate"], root=root)
    with pytest.raises(ValueError, match="not frozen"):
        compat.run(["run-finalist", "team-01"], root=root)


def test_production_phase0_snapshot_path_accepts_schema3_facade() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    manifest_path = root / "tournament/top40/data_manifest.json"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    import json

    manifest = json.loads(manifest_text)

    result = compat.run_with_schema3_runner_compatibility(
        root=root,
        runner_call=lambda: compat.runner_v2._v2_phase0_allows_fast_snapshot_verification(
            root,
            manifest_path,
            manifest,
            manifest_text,
        ),
    )

    assert result is True


def test_production_runner_exception_restores_contract() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    original = compat.runner_v2.tournament_contract

    def fail() -> None:
        raise RuntimeError("expected test failure")

    with pytest.raises(RuntimeError, match="expected test failure"):
        compat.run_with_schema3_runner_compatibility(root=root, runner_call=fail)

    assert compat.runner_v2.tournament_contract is original


def test_production_runner_contract_tamper_fails_and_restores() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    original = compat.runner_v2.tournament_contract

    def tamper() -> None:
        compat.runner_v2.tournament_contract = object()

    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="binding changed"):
        compat.run_with_schema3_runner_compatibility(root=root, runner_call=tamper)

    assert compat.runner_v2.tournament_contract is original


TOP40_CONFIG = "tournament/top40-v2/config.toml"
