from __future__ import annotations

import contextlib
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_trade.tournament.amended_orchestrator_compat_v3 as compat


def _tree_hashes(root: Path) -> dict[str, tuple[str, int]]:
    result: dict[str, tuple[str, int]] = {}
    for relative_root in ("tournament/top40-v2", "reports-top40-v2"):
        base = root / relative_root
        for path in sorted(base.rglob("*")):
            if path.is_file() and not path.is_symlink():
                relative = path.relative_to(root).as_posix()
                result[relative] = (
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    path.stat().st_mode,
                )
    return result


def test_hash_pinned_loader_returns_private_fresh_modules() -> None:
    first = compat._load_frozen_adapter()
    second = compat._load_frozen_adapter()

    assert first is not second
    original = second.amendment_aware_legacy_state_edit
    first.amendment_aware_legacy_state_edit = object()
    assert second.amendment_aware_legacy_state_edit is original


def test_status_uses_exact_result_transition_lock_authority() -> None:
    adapter = compat._load_frozen_adapter()
    status_authority = compat._locked_authority(adapter)
    result_globals = adapter.amendment_aware_legacy_state_edit.__wrapped__.__globals__

    assert status_authority["_state_lock"] is result_globals["_state_lock"]
    assert (
        status_authority["_read_amended_state_locked"]
        is result_globals["_read_amended_state_locked"]
    )


def test_non_status_command_delegates_without_rebinding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Any] = []
    binding = object()

    def frozen_run(argv: Any, *, root: Any) -> int:
        observed.append((argv, root, adapter.amendment_aware_legacy_state_edit))
        return 9

    adapter = SimpleNamespace(
        amendment_aware_legacy_state_edit=binding,
        run=frozen_run,
    )
    monkeypatch.setattr(compat, "_load_frozen_adapter", lambda: adapter)
    root = Path.cwd().resolve()

    assert compat.run(["register-trial", "team-01", "input.json"], root=root) == 9
    assert observed == [
        (["register-trial", "team-01", "input.json"], root, binding)
    ]


def test_status_loader_is_strictly_non_recovering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    accounting = SimpleNamespace(
        material_trial_count=2,
        cpu_hours=1.25,
        wall_clock_hours=1.5,
        pending_candidate_ids=("candidate",),
    )
    journal = SimpleNamespace(
        head_sha256="a" * 64,
        records=({}, {}),
        teams={"team-01": accounting},
    )
    observed: list[Any] = []

    @contextlib.contextmanager
    def state_lock(root: Path):
        observed.append(("lock", root))
        yield

    authority = {
        "_state_lock": state_lock,
        "_read_amended_state_locked": lambda *_args, **_kwargs: ({"state": 3}, b"", (), ()),
        "_require_integration_ready": lambda state, operation: observed.append(
            ("ready", state, operation)
        ),
        "assert_operation_permitted": lambda state, operation: observed.append(
            ("permitted", state, operation)
        ),
        "_legacy_projection": lambda state: {"schema_version": 2, **state},
    }

    def load_journal(root: Any, config: Any, state: Any, *, recover_projection: bool):
        observed.append(("journal", root, config, state, recover_projection))
        return journal

    args = SimpleNamespace(
        command="research-status",
        config="tournament/top40-v2/config.toml",
        json_out=None,
        team_id="team-01",
    )
    legacy = SimpleNamespace(
        build_parser=lambda: SimpleNamespace(parse_args=lambda _argv: args),
        _load_research_journal=load_journal,
        TEAM_IDS=("team-01",),
    )
    adapter = SimpleNamespace(
        _load_frozen_orchestrator=lambda _root: legacy,
        _canonical_config=lambda _root, value: ("canonical", value),
        _effective_config=lambda config, state: ("effective", config, state),
    )
    monkeypatch.setattr(compat, "_locked_authority", lambda _adapter: authority)

    assert compat._research_status_command(adapter, ["research-status"], root=tmp_path) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["journal_record_count"] == 2
    assert payload["teams"]["team-01"]["pending_candidate_ids"] == ["candidate"]
    journal_call = next(row for row in observed if row[0] == "journal")
    assert journal_call[-1] is False


def test_real_research_status_preserves_all_tournament_and_report_bytes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = Path.cwd().resolve()
    if not (root / "tournament/top40-v2/config.toml").is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    before = _tree_hashes(root)

    assert compat.run(["research-status", "team-03"], root=root) == 0

    payload = json.loads(capsys.readouterr().out)
    assert list(payload["teams"]) == ["team-03"]
    assert _tree_hashes(root) == before


def test_real_status_waits_for_the_result_transition_lock(
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = Path.cwd().resolve()
    if not (root / "tournament/top40-v2/config.toml").is_file():
        pytest.skip("requires the Top40 V2 production worktree")
    adapter = compat._load_frozen_adapter()
    state_lock = compat._locked_authority(adapter)["_state_lock"]

    with ThreadPoolExecutor(max_workers=1) as pool:
        with state_lock(root):
            future = pool.submit(compat.run, ["research-status", "team-01"], root=root)
            with pytest.raises(TimeoutError):
                future.result(timeout=0.2)
        assert future.result(timeout=20) == 0

    payload = json.loads(capsys.readouterr().out)
    assert list(payload["teams"]) == ["team-01"]
