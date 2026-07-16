from __future__ import annotations

import dataclasses
import json
import threading
from concurrent.futures import ThreadPoolExecutor
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
    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(
        compat, "_A3_RUN", lambda argv, *, root: observed.append((argv, root)) or 4
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

    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(compat, "_A3_LOAD_ADAPTER", lambda: Adapter())

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

    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(compat, "_A3_LOAD_ADAPTER", lambda: Adapter())
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
    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(
        compat,
        "_A3_LOAD_ADAPTER",
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


def test_production_runner_contract_deletion_fails_and_restores() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    original = compat.runner_v2.tournament_contract

    def delete() -> None:
        del compat.runner_v2.tournament_contract

    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="binding changed"):
        compat.run_with_schema3_runner_compatibility(root=root, runner_call=delete)

    assert compat.runner_v2.tournament_contract is original


def test_live_amendment_authority_tamper_is_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(compat._A3_MODULE, "run", lambda *_args, **_kwargs: 0)
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="0003.*authority"):
        compat._verify_amendment_authorities()


def test_live_amendment_0002_reader_tamper_is_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(compat._A2_MODULE, "_read_exact_schema3_state", object())
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="0002.*authority"):
        compat._verify_amendment_authorities()


def test_noncanonical_config_and_repeated_validation_fail_closed() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    state = json.loads((root / "tournament/top40-v2/run_state.json").read_text())
    config = compat.top40_v2.load_config(root / TOP40_CONFIG)

    def mismatched_config() -> None:
        bad = dataclasses.replace(config, sha256="0" * 64)
        compat.runner_v2.tournament_contract.validate_run_state(state, bad)

    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="noncanonical"):
        compat.run_with_schema3_runner_compatibility(
            root=root,
            runner_call=mismatched_config,
        )

    def repeated() -> None:
        contract = compat.runner_v2.tournament_contract
        contract.validate_run_state(state, config)
        contract.validate_run_state(state, config)

    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="repeated"):
        compat.run_with_schema3_runner_compatibility(root=root, runner_call=repeated)


def test_concurrent_wrappers_share_the_amendment_0002_lock() -> None:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    state = json.loads((root / "tournament/top40-v2/run_state.json").read_text())
    config = compat.top40_v2.load_config(root / TOP40_CONFIG)
    first_entered = threading.Event()
    second_entered = threading.Event()
    release_first = threading.Event()

    def invoke(label: str) -> str:
        def call() -> str:
            compat.runner_v2.tournament_contract.validate_run_state(state, config)
            if label == "first":
                first_entered.set()
                assert release_first.wait(timeout=5)
            else:
                second_entered.set()
            return label

        return compat.run_with_schema3_runner_compatibility(root=root, runner_call=call)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(invoke, "first")
        assert first_entered.wait(timeout=5)
        second = pool.submit(invoke, "second")
        assert not second_entered.wait(timeout=0.2)
        release_first.set()
        assert first.result(timeout=10) == "first"
        assert second.result(timeout=10) == "second"


TOP40_CONFIG = "tournament/top40-v2/config.toml"
