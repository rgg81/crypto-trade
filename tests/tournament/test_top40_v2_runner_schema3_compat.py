from __future__ import annotations

import dataclasses
import json
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_trade.tournament.runner_schema3_compat_v4 as compat

TOP40_CONFIG = "tournament/top40-v2/config.toml"
DEVELOPMENT_ARGV = ["run-window", "development", "team-01", "candidate"]


def _production_root() -> Path:
    root = Path.cwd().resolve()
    if not (root / TOP40_CONFIG).is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    return root


def _install_fake_adapter(
    monkeypatch: pytest.MonkeyPatch,
    callback: Any,
) -> None:
    class Adapter:
        def run(self, argv: Any, *, root: Any) -> int:
            return callback(argv, root)

    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(compat, "_A3_LOAD_ADAPTER", lambda: Adapter())


def _run_development(root: Path) -> int:
    return compat.run_development_window_with_schema3_compatibility(
        root=root,
        argv=DEVELOPMENT_ARGV,
        _authorization=compat._DEVELOPMENT_RUN_AUTHORIZATION,
    )


def test_active_status_delegates_with_post_authority_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []
    checks: list[str] = []
    monkeypatch.setattr(
        compat, "_verify_amendment_authorities", lambda: checks.append("checked")
    )
    monkeypatch.setattr(
        compat, "_A3_RUN", lambda argv, *, root: observed.append((argv, root)) or 4
    )

    assert compat.run(["research-status", "team-01"], root=root) == 4
    assert observed == [(["research-status", "team-01"], root)]
    assert checks == ["checked", "checked", "checked"]


def test_non_runner_command_delegates_without_contract_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []
    checks: list[str] = []

    class Adapter:
        def run(self, argv: Any, *, root: Any) -> int:
            observed.append((argv, root, compat.runner_v2.tournament_contract))
            return 6

    monkeypatch.setattr(
        compat, "_verify_amendment_authorities", lambda: checks.append("checked")
    )
    monkeypatch.setattr(compat, "_A3_LOAD_ADAPTER", lambda: Adapter())

    assert compat.run(["register-family", "team-03", "input.json"], root=root) == 6
    assert observed[0][0:2] == (["register-family", "team-03", "input.json"], root)
    assert observed[0][2] is compat.top40_v2
    assert checks == ["checked", "checked", "checked"]


def test_development_command_uses_stage_bound_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    observed: list[Any] = []
    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)

    def wrapper(*, root: Any, argv: Any, _authorization: Any) -> int:
        observed.append((root, argv, _authorization))
        return 8

    monkeypatch.setattr(
        compat,
        "run_development_window_with_schema3_compatibility",
        wrapper,
    )

    assert compat.run(DEVELOPMENT_ARGV, root=root) == 8
    assert observed == [(root, DEVELOPMENT_ARGV, compat._DEVELOPMENT_RUN_AUTHORIZATION)]


def test_direct_helper_rejects_missing_authority_private_and_finalist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    monkeypatch.setattr(
        compat,
        "_A3_LOAD_ADAPTER",
        lambda: pytest.fail("invalid scope reached the frozen adapter"),
    )
    with pytest.raises(PermissionError, match="active-entrypoint"):
        compat.run_development_window_with_schema3_compatibility(
            root=root,
            argv=DEVELOPMENT_ARGV,
        )
    for argv in (
        ["run-window", "private", "team-01", "candidate"],
        ["run-finalist", "team-01"],
    ):
        with pytest.raises(ValueError, match="exact run-window development"):
            compat.run_development_window_with_schema3_compatibility(
                root=root,
                argv=argv,
                _authorization=compat._DEVELOPMENT_RUN_AUTHORIZATION,
            )


def test_active_private_and_finalist_paths_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path.cwd().resolve()
    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    with pytest.raises(ValueError, match="only for development"):
        compat.run(["run-window", "private", "team-01", "candidate"], root=root)
    with pytest.raises(ValueError, match="not frozen"):
        compat.run(["run-finalist", "team-01"], root=root)


def test_production_phase0_snapshot_path_accepts_schema3_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _production_root()
    manifest_path = root / "tournament/top40/data_manifest.json"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    def callback(_argv: Any, _root: Any) -> int:
        accepted = compat.runner_v2._v2_phase0_allows_fast_snapshot_verification(
            root,
            manifest_path,
            manifest,
            manifest_text,
        )
        return int(accepted)

    _install_fake_adapter(monkeypatch, callback)
    assert _run_development(root) == 1


def test_production_runner_exception_restores_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _production_root()
    original = compat.runner_v2.tournament_contract

    def fail(_argv: Any, _root: Any) -> int:
        raise RuntimeError("expected test failure")

    _install_fake_adapter(monkeypatch, fail)
    with pytest.raises(RuntimeError, match="expected test failure"):
        _run_development(root)
    assert compat.runner_v2.tournament_contract is original


@pytest.mark.parametrize("delete", [False, True])
def test_production_runner_contract_tamper_fails_and_restores(
    monkeypatch: pytest.MonkeyPatch,
    delete: bool,
) -> None:
    root = _production_root()
    original = compat.runner_v2.tournament_contract

    def tamper(_argv: Any, _root: Any) -> int:
        if delete:
            del compat.runner_v2.tournament_contract
        else:
            compat.runner_v2.tournament_contract = object()
        return 0

    _install_fake_adapter(monkeypatch, tamper)
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="binding changed"):
        _run_development(root)
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


@pytest.mark.parametrize("ordinary", [False, True])
def test_delegation_tamper_after_success_is_detected(
    monkeypatch: pytest.MonkeyPatch,
    ordinary: bool,
) -> None:
    root = Path.cwd().resolve()
    checks = 0

    def verify() -> None:
        nonlocal checks
        checks += 1
        if checks == 3:
            raise compat.RunnerSchema3CompatibilityError("post-delegation tamper")

    monkeypatch.setattr(compat, "_verify_amendment_authorities", verify)
    if ordinary:
        monkeypatch.setattr(
            compat,
            "_A3_LOAD_ADAPTER",
            lambda: SimpleNamespace(run=lambda *_args, **_kwargs: 0),
        )
        argv = ["validate-config"]
    else:
        monkeypatch.setattr(compat, "_A3_RUN", lambda *_args, **_kwargs: 0)
        argv = ["research-status"]
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="post-delegation"):
        compat.run(argv, root=root)


def test_noncanonical_config_and_repeated_validation_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _production_root()
    state = json.loads((root / "tournament/top40-v2/run_state.json").read_text())
    config = compat.top40_v2.load_config(root / TOP40_CONFIG)

    def mismatched(_argv: Any, _root: Any) -> int:
        bad = dataclasses.replace(config, sha256="0" * 64)
        compat.runner_v2.tournament_contract.validate_run_state(state, bad)
        return 0

    _install_fake_adapter(monkeypatch, mismatched)
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="noncanonical"):
        _run_development(root)

    def repeated(_argv: Any, _root: Any) -> int:
        contract = compat.runner_v2.tournament_contract
        contract.validate_run_state(state, config)
        contract.validate_run_state(state, config)
        return 0

    _install_fake_adapter(monkeypatch, repeated)
    with pytest.raises(compat.RunnerSchema3CompatibilityError, match="repeated"):
        _run_development(root)


def test_concurrent_wrappers_share_the_amendment_0002_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _production_root()
    state = json.loads((root / "tournament/top40-v2/run_state.json").read_text())
    config = compat.top40_v2.load_config(root / TOP40_CONFIG)
    first_entered = threading.Event()
    second_entered = threading.Event()
    release_first = threading.Event()
    adapters: queue.SimpleQueue[Any] = queue.SimpleQueue()

    for label in ("first", "second"):
        class Adapter:
            def run(self, _argv: Any, *, root: Any, value: str = label) -> int:
                compat.runner_v2.tournament_contract.validate_run_state(state, config)
                if value == "first":
                    first_entered.set()
                    assert release_first.wait(timeout=5)
                    return 1
                second_entered.set()
                return 2

        adapters.put(Adapter())

    monkeypatch.setattr(compat, "_verify_amendment_authorities", lambda: None)
    monkeypatch.setattr(compat, "_A3_LOAD_ADAPTER", adapters.get)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_run_development, root)
        assert first_entered.wait(timeout=5)
        second = pool.submit(_run_development, root)
        assert not second_entered.wait(timeout=0.2)
        release_first.set()
        assert first.result(timeout=10) == 1
        assert second.result(timeout=10) == 2
