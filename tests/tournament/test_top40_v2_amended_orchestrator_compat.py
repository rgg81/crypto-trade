from __future__ import annotations

import contextlib
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_trade.tournament.amended_orchestrator_compat_v3 as compat
from crypto_trade.tournament.top40_v2 import LoadedV2Config


def _config(tmp_path: Path) -> LoadedV2Config:
    return LoadedV2Config(
        path=tmp_path / "config.toml",
        sha256="a" * 64,
        raw={"research_budget": {"deadline_utc": "2026-08-01T18:00:00Z"}},
    )


def _projection() -> dict[str, Any]:
    return {"schema_version": 2, "phase": "research"}


def _adapter() -> SimpleNamespace:
    @contextlib.contextmanager
    def frozen_edit(*_args: Any, **_kwargs: Any):
        yield _projection()

    adapter = SimpleNamespace(
        _READ_ONLY_LEGACY_COMMANDS=compat._READ_ONLY_OPERATIONS,
        amendment_aware_legacy_state_edit=frozen_edit,
        read_amendment_aware_legacy_state=lambda *_args, **_kwargs: _projection(),
        validate_run_state=lambda *_args, **_kwargs: None,
    )
    adapter.run = lambda _argv, *, root: 0
    return adapter


def test_read_only_command_receives_unchanged_projection(tmp_path: Path) -> None:
    adapter = _adapter()
    compatible_edit = compat._make_compatible_edit(adapter)

    with compatible_edit(
        tmp_path,
        _config(tmp_path),
        operation="research-status",
        staged_changes=[],
    ) as observed:
        assert observed == _projection()


def test_mutation_followed_by_exception_is_still_rejected(tmp_path: Path) -> None:
    compatible_edit = compat._make_compatible_edit(_adapter())

    with pytest.raises(ValueError, match="state mutation"):
        with compatible_edit(
            tmp_path,
            _config(tmp_path),
            operation="research-status",
            staged_changes=[],
        ) as observed:
            observed["phase"] = "qualification_closed"
            raise RuntimeError("body failed after mutation")


def test_staged_output_followed_by_exception_is_still_rejected(tmp_path: Path) -> None:
    changes: list[Any] = []
    compatible_edit = compat._make_compatible_edit(_adapter())

    with pytest.raises(ValueError, match="staged file mutation"):
        with compatible_edit(
            tmp_path,
            _config(tmp_path),
            operation="research-status",
            staged_changes=changes,
        ):
            changes.append(object())
            raise RuntimeError("body failed after staging")


def test_direct_protected_file_write_is_rejected_and_rolled_back(tmp_path: Path) -> None:
    target = tmp_path / "reports-top40-v2" / "sentinel.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"before\n")
    compatible_edit = compat._make_compatible_edit(_adapter())

    with pytest.raises(ValueError, match="protected file mutation"):
        with compatible_edit(
            tmp_path,
            _config(tmp_path),
            operation="research-status",
            staged_changes=[],
        ):
            target.write_bytes(b"after\n")

    assert target.read_bytes() == b"before\n"


def test_result_bearing_command_forwards_exact_frozen_arguments(tmp_path: Path) -> None:
    adapter = _adapter()
    observed: list[tuple[Any, ...]] = []
    changes: list[Any] = []

    def clock() -> Any:
        return object()

    @contextlib.contextmanager
    def frozen_edit(
        root: Any,
        config: Any,
        *,
        operation: str,
        staged_changes: Any,
        clock: Any,
    ):
        observed.append((root, config, operation, staged_changes, clock))
        yield _projection()

    adapter.amendment_aware_legacy_state_edit = frozen_edit
    compatible_edit = compat._make_compatible_edit(adapter)
    config = _config(tmp_path)
    with compatible_edit(
        tmp_path,
        config,
        operation="register-trial",
        staged_changes=changes,
        clock=clock,
    ):
        pass

    assert observed == [(tmp_path, config, "register-trial", changes, clock)]


def test_hash_pinned_loader_returns_private_fresh_modules() -> None:
    first = compat._load_frozen_adapter()
    second = compat._load_frozen_adapter()

    assert first is not second
    assert first._READ_ONLY_LEGACY_COMMANDS == compat._READ_ONLY_OPERATIONS
    original = second.amendment_aware_legacy_state_edit
    first.amendment_aware_legacy_state_edit = object()
    assert second.amendment_aware_legacy_state_edit is original


def test_run_uses_private_binding_and_restores_it(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = _adapter()
    original = adapter.amendment_aware_legacy_state_edit

    def frozen_run(_argv: Any, *, root: Any) -> int:
        assert adapter.amendment_aware_legacy_state_edit is not original
        return 7

    adapter.run = frozen_run
    monkeypatch.setattr(compat, "_load_frozen_adapter", lambda: adapter)

    assert compat.run(["research-status"], root=None) == 7
    assert adapter.amendment_aware_legacy_state_edit is original


def test_run_detects_tamper_during_exception_and_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _adapter()
    original = adapter.amendment_aware_legacy_state_edit

    def frozen_run(_argv: Any, *, root: Any) -> int:
        adapter.amendment_aware_legacy_state_edit = original
        raise ValueError("boom")

    adapter.run = frozen_run
    monkeypatch.setattr(compat, "_load_frozen_adapter", lambda: adapter)

    with pytest.raises(RuntimeError, match="authority changed") as caught:
        compat.run(["research-status"], root=None)
    assert isinstance(caught.value.__cause__, ValueError)
    assert adapter.amendment_aware_legacy_state_edit is original


def test_concurrent_runs_use_distinct_adapter_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters: queue.SimpleQueue[SimpleNamespace] = queue.SimpleQueue()
    barrier = threading.Barrier(2)
    originals: list[Any] = []
    for result in (3, 5):
        adapter = _adapter()
        original = adapter.amendment_aware_legacy_state_edit
        originals.append(original)

        def frozen_run(
            _argv: Any,
            *,
            root: Any,
            current: SimpleNamespace = adapter,
            expected: Any = original,
            value: int = result,
        ) -> int:
            barrier.wait(timeout=5)
            assert current.amendment_aware_legacy_state_edit is not expected
            return value

        adapter.run = frozen_run
        adapters.put(adapter)

    monkeypatch.setattr(compat, "_load_frozen_adapter", adapters.get)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: compat.run(["research-status"]), range(2)))

    assert sorted(results) == [3, 5]


def test_real_research_status_preserves_all_protected_bytes() -> None:
    root = Path.cwd().resolve()
    config = root / "tournament/top40-v2/config.toml"
    if not config.is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    before = compat._read_only_snapshot(root)

    assert compat.run(["research-status"], root=root) == 0

    assert compat._read_only_snapshot(root) == before
