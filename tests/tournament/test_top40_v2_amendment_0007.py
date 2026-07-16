"""Focused tests for the pending Amendment 0007 runtime preload boundary."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import NoReturn

import pandas as pd
import pytest

from crypto_trade.tournament import _strategy_worker_preload_v7 as worker_preload
from crypto_trade.tournament import amendment_0007_v2 as amendment
from crypto_trade.tournament import runner_v2

ROOT = Path(__file__).resolve().parents[2]


def _disable_authority_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(amendment, "verify_parent_authorities", lambda _root: None)
    monkeypatch.setattr(
        amendment,
        "_active_integration_guard",
        lambda _root, *, _authorization: contextlib.nullcontext(),
    )


def _run(argv: list[str], *, root: Path) -> int:
    return amendment.run(
        argv,
        root=root,
        _authorization=amendment._ACTIVE_INTEGRATION_AUTHORIZATION,
    )


def _install_fake_frozen_command(monkeypatch: pytest.MonkeyPatch):
    def frozen_command(
        root: Path,
        repository_parent: Path,
        bundle: Path,
        site_packages: Path,
        runtime_site_packages: Path,
        entrypoint: str,
        empty_dir: Path,
        empty_file: Path,
    ) -> list[str]:
        return [
            "/usr/bin/unshare",
            "--mount",
            "/venv/bin/python",
            "-m",
            amendment._FROZEN_WORKER_MODULE,
            "--root",
            str(root),
            "--repository-parent",
            str(repository_parent),
            "--bundle",
            str(bundle),
            "--site-packages",
            str(site_packages),
            "--runtime-site-packages",
            str(runtime_site_packages),
            "--entrypoint",
            entrypoint,
            "--empty-dir",
            str(empty_dir),
            "--empty-file",
            str(empty_file),
        ]

    monkeypatch.setattr(amendment, "_FROZEN_STRATEGY_WORKER_COMMAND", frozen_command)
    monkeypatch.setattr(runner_v2, "_strategy_worker_command", frozen_command)
    return frozen_command


def _worker_arguments(tmp_path: Path) -> tuple[object, ...]:
    return (
        tmp_path,
        tmp_path / "repository-parent",
        tmp_path / "bundle",
        tmp_path / "site-packages",
        tmp_path / "runtime-site-packages",
        "strategy.py",
        tmp_path / "empty-dir",
        tmp_path / "empty-file",
    )


def _smoke_market() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[pd.Timestamp]]:
    times = pd.date_range("2020-02-03", periods=4, freq="8h", tz="UTC")
    bars = pd.DataFrame(
        [
            {
                "open_time": timestamp,
                "symbol": symbol,
                "open": 100.0 + symbol_index + bar_index,
                "close": 100.5 + symbol_index + bar_index,
                "quote_volume": 1_000_000.0,
            }
            for symbol_index, symbol in enumerate(("AAAUSDT", "BBBUSDT"))
            for bar_index, timestamp in enumerate(times)
        ]
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0]],
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [2_000_000.0, 1_000_000.0],
        }
    )
    return bars, funding, membership, [times[2], times[3]]


def _run_smoke_worker(entrypoint: Path) -> pd.DataFrame:
    bars, funding, membership, decisions = _smoke_market()
    return runner_v2._generate_targets_in_worker(
        ROOT,
        "team-07",
        entrypoint,
        bars,
        funding,
        membership,
        decisions,
        seed=7,
        interval_hours=8,
    )


def test_real_parent_authorities_and_preload_bytes_are_exact() -> None:
    amendment.verify_parent_authorities(ROOT)
    worker_preload._verify_preload(ROOT)


def test_real_namespace_mask_allows_direct_a5_protocol_import(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    entrypoint = tmp_path / "a5-import" / "strategy.py"
    entrypoint.parent.mkdir()
    entrypoint.write_text(
        """
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

class Strategy:
    def target_weights(self, context, *, seed):
        scores = score_boundary({
            symbol: float(index)
            for index, symbol in enumerate(context.eligible_symbols)
        })
        winner = max(scores, key=scores.__getitem__)
        return {winner: 0.05}

def build_strategy():
    return Strategy()
""".lstrip(),
        encoding="utf-8",
    )
    replacement = amendment._PreloadStrategyWorkerCommand()
    monkeypatch.setattr(runner_v2, "_strategy_worker_command", replacement)

    targets = _run_smoke_worker(entrypoint)

    assert replacement.calls == 1
    assert "AAAUSDT" not in targets
    assert targets["BBBUSDT"].eq(0.05).all()


def test_real_namespace_non_a5_weights_match_frozen_worker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    entrypoint = tmp_path / "ordinary" / "strategy.py"
    entrypoint.parent.mkdir()
    entrypoint.write_text(
        """
class Strategy:
    def target_weights(self, context, *, seed):
        return {
            symbol: (0.03 if index == 0 else -0.02)
            for index, symbol in enumerate(context.eligible_symbols)
        }

def build_strategy():
    return Strategy()
""".lstrip(),
        encoding="utf-8",
    )
    frozen = _run_smoke_worker(entrypoint)
    replacement = amendment._PreloadStrategyWorkerCommand()
    monkeypatch.setattr(runner_v2, "_strategy_worker_command", replacement)

    wrapped = _run_smoke_worker(entrypoint)

    pd.testing.assert_frame_equal(wrapped, frozen)
    assert replacement.calls == 1


def test_worker_command_replacement_changes_exactly_one_module_token() -> None:
    original = [
        "unshare",
        "--mount",
        "python",
        "-m",
        amendment._FROZEN_WORKER_MODULE,
        "--root",
        "/repo",
    ]
    replaced = amendment._replace_worker_module(original)

    assert original[4] == amendment._FROZEN_WORKER_MODULE
    assert replaced[4] == amendment._PRELOAD_WORKER_MODULE
    assert [index for index, value in enumerate(original) if replaced[index] != value] == [4]


@pytest.mark.parametrize(
    "command",
    [
        ["python", "-m", "wrong.worker"],
        [
            "python",
            "-m",
            amendment._FROZEN_WORKER_MODULE,
            "-m",
            amendment._FROZEN_WORKER_MODULE,
        ],
        ["python", amendment._FROZEN_WORKER_MODULE],
        [
            "python",
            "-m",
            amendment._FROZEN_WORKER_MODULE,
            amendment._PRELOAD_WORKER_MODULE,
        ],
    ],
)
def test_worker_command_replacement_rejects_ambiguous_boundaries(command: list[str]) -> None:
    with pytest.raises(amendment.Amendment0007Error, match="module boundary"):
        amendment._replace_worker_module(command)


@pytest.mark.parametrize(
    "argv",
    [
        ["amendment-0005-status"],
        ["research-status", "team-07"],
        ["register-trial", "team-07", "registration.json"],
        ["run-window", "private", "team-07", "candidate-07"],
        ["run-window", "development"],
        ["run-window", "development", "team-01", "candidate-01"],
        ["run-window", "development", "team-03", "candidate-03"],
        ["run-window", "development", "team-07", "INVALID CANDIDATE"],
        ["run-window", "development", "team-07", "candidate-07", "--json-out"],
    ],
)
def test_non_development_argv_delegates_to_exact_a5_without_patch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
) -> None:
    _disable_authority_checks(monkeypatch)
    original = runner_v2._strategy_worker_command
    observed: list[tuple[object, Path]] = []

    def delegate(values: object, *, root: Path) -> int:
        assert runner_v2._strategy_worker_command is original
        observed.append((values, root))
        return 7

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", delegate)
    assert _run(argv, root=tmp_path) == 7
    assert observed == [(argv, tmp_path.resolve())]
    assert runner_v2._strategy_worker_command is original


def test_development_run_uses_wrapper_and_restores_exactly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _disable_authority_checks(monkeypatch)
    frozen_command = _install_fake_frozen_command(monkeypatch)
    argv = ["run-window", "development", "team-07", "candidate-07"]
    observed: list[list[str]] = []

    def delegate(values: object, *, root: Path) -> int:
        assert values is not argv
        assert list(values) == argv
        assert root == tmp_path.resolve()
        assert isinstance(
            runner_v2._strategy_worker_command,
            amendment._PreloadStrategyWorkerCommand,
        )
        with amendment._A4_MODULE._A2_PATCH_LOCK:
            command = runner_v2._strategy_worker_command(*_worker_arguments(tmp_path))
        observed.append(command)
        return 11

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", delegate)
    assert _run(argv, root=tmp_path) == 11
    assert runner_v2._strategy_worker_command is frozen_command
    assert observed[0][observed[0].index("-m") + 1] == amendment._PRELOAD_WORKER_MODULE
    assert amendment._FROZEN_WORKER_MODULE not in observed[0]


def test_dispatch_uses_one_immutable_argv_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FlippingArguments:
        def __init__(self) -> None:
            self.iterations = 0

        def __iter__(self):
            self.iterations += 1
            if self.iterations == 1:
                return iter(["research-status", "team-07"])
            return iter(["run-window", "development", "team-07", "candidate-07"])

    _disable_authority_checks(monkeypatch)
    arguments = FlippingArguments()
    observed: list[list[str]] = []
    monkeypatch.setattr(
        amendment,
        "_A5_INTEGRATION_RUN",
        lambda values, *, root: observed.append(list(values)) or 0,
    )

    assert (
        amendment.run(
            arguments,  # type: ignore[arg-type]
            root=tmp_path,
            _authorization=amendment._ACTIVE_INTEGRATION_AUTHORIZATION,
        )
        == 0
    )
    assert arguments.iterations == 1
    assert observed == [["research-status", "team-07"]]


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("delegate failed"), KeyboardInterrupt(), SystemExit(9)],
)
def test_development_run_restores_after_every_base_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: BaseException,
) -> None:
    _disable_authority_checks(monkeypatch)
    frozen_command = _install_fake_frozen_command(monkeypatch)

    def fail(_values: object, *, root: Path) -> NoReturn:
        assert root == tmp_path.resolve()
        raise failure

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", fail)
    with pytest.raises(type(failure)):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert runner_v2._strategy_worker_command is frozen_command


def test_delegate_tampering_is_detected_after_exact_restoration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _disable_authority_checks(monkeypatch)
    frozen_command = _install_fake_frozen_command(monkeypatch)

    def tamper(_values: object, *, root: Path) -> int:
        assert root == tmp_path.resolve()

        def intruder(*_args: object) -> list[str]:
            return []

        runner_v2._strategy_worker_command = intruder
        return 0

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", tamper)
    with pytest.raises(amendment.Amendment0007Error, match="exact restoration"):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert runner_v2._strategy_worker_command is frozen_command


def test_success_without_exactly_one_worker_launch_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _disable_authority_checks(monkeypatch)
    frozen_command = _install_fake_frozen_command(monkeypatch)
    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", lambda *_args, **_kwargs: 0)

    with pytest.raises(amendment.Amendment0007Error, match="exactly one"):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert runner_v2._strategy_worker_command is frozen_command


def test_replacement_rejects_nonroot_entrypoint_and_second_launch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _disable_authority_checks(monkeypatch)
    frozen_command = _install_fake_frozen_command(monkeypatch)

    def delegate(_values: object, *, root: Path) -> int:
        replacement = runner_v2._strategy_worker_command
        wrong = list(_worker_arguments(tmp_path))
        wrong[5] = "nested/strategy.py"
        with pytest.raises(amendment.Amendment0007Error, match="root strategy.py"):
            replacement(*wrong)
        with pytest.raises(amendment.Amendment0007Error, match="more than once"):
            replacement(*_worker_arguments(tmp_path))
        raise RuntimeError("expected delegated failure after rejected launches")

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", delegate)
    with pytest.raises(RuntimeError, match="expected delegated failure"):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert runner_v2._strategy_worker_command is frozen_command


def test_preexisting_patch_is_rejected_without_claiming_or_replacing_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _disable_authority_checks(monkeypatch)

    def intruder(*_args: object) -> list[str]:
        return []

    monkeypatch.setattr(runner_v2, "_strategy_worker_command", intruder)

    with pytest.raises(amendment.Amendment0007Error, match="already replaced"):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert runner_v2._strategy_worker_command is intruder


def test_post_authority_failure_occurs_only_after_exact_restoration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    frozen_command = _install_fake_frozen_command(monkeypatch)
    monkeypatch.setattr(
        amendment,
        "_active_integration_guard",
        lambda _root, *, _authorization: contextlib.nullcontext(),
    )
    calls = 0

    def verify(_root: Path) -> None:
        nonlocal calls
        calls += 1
        assert runner_v2._strategy_worker_command is frozen_command
        if calls == 2:
            raise amendment.Amendment0007Error("postcheck failed")

    monkeypatch.setattr(amendment, "verify_parent_authorities", verify)

    def delegate(_values: object, *, root: Path) -> int:
        runner_v2._strategy_worker_command(*_worker_arguments(tmp_path))
        return 0

    monkeypatch.setattr(amendment, "_A5_INTEGRATION_RUN", delegate)
    with pytest.raises(amendment.Amendment0007Error, match="postcheck failed"):
        _run(
            ["run-window", "development", "team-07", "candidate-07"],
            root=tmp_path,
        )
    assert calls == 2
    assert runner_v2._strategy_worker_command is frozen_command


def test_public_dispatch_requires_private_active_entrypoint_identity(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="active-entrypoint"):
        amendment.run(["research-status"], root=tmp_path)


def test_delegated_a5_integration_requires_exact_commit_and_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        amendment,
        "_A5_LOAD_ACTIVE_INTEGRATION",
        lambda _root: ({"status": "active"}, b"wrong", "0" * 40),
    )
    with pytest.raises(amendment.Amendment0007Error, match="authority differs"):
        amendment._verify_delegated_a5_integration(tmp_path)


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-16T18:00:00+00:00",
        "2026-07-16 18:00:00Z",
        "2026-07-16T18:00:00.000000Z",
    ],
)
def test_governance_timestamps_require_canonical_utc(value: str) -> None:
    with pytest.raises(amendment.Amendment0007Error, match="canonical"):
        amendment._canonical_utc(value, "timestamp")
    assert (
        amendment._canonical_utc("2026-07-16T18:00:00Z", "timestamp").isoformat()
        == "2026-07-16T18:00:00+00:00"
    )


def test_loaded_dispatch_identity_change_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    amendment._verify_loaded_integration_dispatch(ROOT)
    monkeypatch.setattr(amendment, "run", lambda *_args, **_kwargs: 0)
    with pytest.raises(PermissionError, match="identity changed"):
        amendment._verify_loaded_integration_dispatch(ROOT)


@pytest.mark.parametrize(
    "attribute",
    ["_run_development_with_preload", "_verified_delegate"],
)
def test_loaded_dispatch_rejects_replaced_direct_helper(
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
) -> None:
    monkeypatch.setattr(amendment, attribute, lambda *_args, **_kwargs: 0)
    with pytest.raises(PermissionError, match="identity changed"):
        amendment._verify_loaded_integration_dispatch(ROOT)


def test_active_guard_detects_integration_change_after_body(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = 0

    def load(_root: Path):
        nonlocal calls
        calls += 1
        return ({"version": calls}, f"version-{calls}".encode(), f"{calls:040x}")

    monkeypatch.setattr(amendment, "_A7_VERIFY_LOADED_DISPATCH", lambda _root: None)
    monkeypatch.setattr(amendment, "_load_active_integration", load)
    with pytest.raises(amendment.Amendment0007Error, match="changed during dispatch"):
        with amendment._active_integration_guard(
            tmp_path,
            _authorization=amendment._ACTIVE_INTEGRATION_AUTHORIZATION,
        ):
            pass
    assert calls == 2


def _synthetic_active_integration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    same_reviewer: bool = False,
) -> tuple[dict[str, object], list[tuple[str, str, str]]]:
    implementation = {
        path: f"exact synthetic bytes for {path}\n".encode()
        for path in amendment.IMPLEMENTATION_FILE_PATHS
    }
    implementation_hashes = {
        path: amendment._SHA256_BYTES(payload) for path, payload in implementation.items()
    }
    commits = {
        amendment.REVIEW_PATH: "2" * 40,
        amendment.FREEZE_PATH: "3" * 40,
        amendment.INTEGRATION_DRAFT_PATH: "4" * 40,
        amendment.INTEGRATION_REVIEW_PATH: "5" * 40,
        amendment.INTEGRATION_FREEZE_PATH: "6" * 40,
    }
    implementation_commit = "1" * 40
    parent_records = amendment._parent_authority_records()
    validation = {
        "a5_a6_a4_regression": "passed",
        "focused_a7": "passed",
        "frozen_worker_regression": "passed",
        "real_namespace_mask_smoke": "passed",
        "ruff": "passed",
    }
    review: dict[str, object] = {
        "activation_authorized": False,
        "amendment_id": amendment.AMENDMENT_ID,
        "decision": "approved",
        "implementation_commit": implementation_commit,
        "implementation_files": implementation_hashes,
        "parent_authorities": parent_records,
        "review_scope": amendment._IMPLEMENTATION_REVIEW_SCOPE,
        "reviewed_at_utc": "2026-07-16T18:00:00Z",
        "reviewer_id": "implementation-reviewer",
        "schema_version": 1,
        "validation": validation,
    }
    review_bytes = amendment._PRETTY_JSON_BYTES(review)
    review_binding = amendment._authority_binding(
        amendment.REVIEW_PATH, review_bytes, commits[amendment.REVIEW_PATH]
    )
    freeze_files = dict(implementation_hashes)
    freeze_files[amendment.REVIEW_PATH] = amendment._SHA256_BYTES(review_bytes)
    entrypoint_binding = amendment._file_binding(
        amendment.ENTRYPOINT_PATH, implementation[amendment.ENTRYPOINT_PATH]
    )
    freeze: dict[str, object] = {
        "activation_status": "pending-integration",
        "amendment_id": amendment.AMENDMENT_ID,
        "entrypoint_candidate": entrypoint_binding,
        "files": freeze_files,
        "final_implementation_commit": implementation_commit,
        "freeze_timestamp_utc": "2026-07-16T18:01:00Z",
        "parent_authorities": parent_records,
        "review": review_binding,
        "schema_version": 1,
        "status": "frozen",
    }
    freeze_bytes = amendment._PRETTY_JSON_BYTES(freeze)
    freeze_binding = amendment._authority_binding(
        amendment.FREEZE_PATH, freeze_bytes, commits[amendment.FREEZE_PATH]
    )
    module_binding = amendment._file_binding(
        amendment.IMPLEMENTATION_MODULE_PATH,
        implementation[amendment.IMPLEMENTATION_MODULE_PATH],
    )
    wrapper_binding: dict[str, object] = {
        "path": amendment.WORKER_WRAPPER_PATH,
        "sha256": amendment._SHA256_BYTES(implementation[amendment.WORKER_WRAPPER_PATH]),
        "size": len(implementation[amendment.WORKER_WRAPPER_PATH]),
    }
    integration_draft: dict[str, object] = {
        "active_entrypoint": entrypoint_binding,
        "amendment_freeze": freeze_binding,
        "amendment_id": amendment.AMENDMENT_ID,
        "delegated_amendment_0005_integration": amendment._DELEGATED_A5_INTEGRATION,
        "dispatch_scope": amendment._DISPATCH_SCOPE,
        "historical_entrypoint": amendment._HISTORICAL_ENTRYPOINT,
        "implementation_module": module_binding,
        "proposed_at_utc": "2026-07-16T18:02:00Z",
        "schema_version": 1,
        "status": "draft",
        "worker_wrapper": wrapper_binding,
    }
    integration_draft_bytes = amendment._PRETTY_JSON_BYTES(integration_draft)
    integration_draft_binding = amendment._authority_binding(
        amendment.INTEGRATION_DRAFT_PATH,
        integration_draft_bytes,
        commits[amendment.INTEGRATION_DRAFT_PATH],
    )
    integration_reviewer = "implementation-reviewer" if same_reviewer else "integration-reviewer"
    integration_review: dict[str, object] = {
        "activation_authorized": True,
        "active_entrypoint": entrypoint_binding,
        "amendment_freeze": freeze_binding,
        "amendment_id": amendment.AMENDMENT_ID,
        "decision": "approved",
        "delegated_amendment_0005_integration": amendment._DELEGATED_A5_INTEGRATION,
        "dispatch_scope": amendment._DISPATCH_SCOPE,
        "historical_entrypoint": amendment._HISTORICAL_ENTRYPOINT,
        "implementation_module": module_binding,
        "integration_draft": integration_draft_binding,
        "review_scope": amendment._INTEGRATION_REVIEW_SCOPE,
        "reviewed_at_utc": "2026-07-16T18:03:00Z",
        "reviewer_id": integration_reviewer,
        "schema_version": 1,
        "worker_wrapper": wrapper_binding,
    }
    integration_review_bytes = amendment._PRETTY_JSON_BYTES(integration_review)
    integration_review_binding = amendment._authority_binding(
        amendment.INTEGRATION_REVIEW_PATH,
        integration_review_bytes,
        commits[amendment.INTEGRATION_REVIEW_PATH],
    )
    integration: dict[str, object] = {
        "activation_journal": {
            "head_sha256": amendment._A5_ACTIVATION_HEAD_SHA256,
            "path": amendment._JOURNAL_PATH,
            "record_count": amendment._A5_ACTIVATION_RECORD_COUNT,
        },
        "activation_timestamp_utc": "2026-07-16T18:04:00Z",
        "active_entrypoint": entrypoint_binding,
        "amendment_freeze": freeze_binding,
        "amendment_id": amendment.AMENDMENT_ID,
        "delegated_amendment_0005_integration": amendment._DELEGATED_A5_INTEGRATION,
        "dispatch_scope": amendment._DISPATCH_SCOPE,
        "historical_entrypoint": amendment._HISTORICAL_ENTRYPOINT,
        "implementation_module": module_binding,
        "integration_draft": integration_draft_binding,
        "integration_review": integration_review_binding,
        "schema_version": 1,
        "status": "active",
        "worker_wrapper": wrapper_binding,
    }
    documents = {
        amendment.REVIEW_PATH: (review, review_bytes),
        amendment.FREEZE_PATH: (freeze, freeze_bytes),
        amendment.INTEGRATION_DRAFT_PATH: (integration_draft, integration_draft_bytes),
        amendment.INTEGRATION_REVIEW_PATH: (integration_review, integration_review_bytes),
        amendment.INTEGRATION_FREEZE_PATH: (
            integration,
            amendment._PRETTY_JSON_BYTES(integration),
        ),
    }
    ancestry: list[tuple[str, str, str]] = []
    monkeypatch.setattr(amendment, "verify_parent_authorities", lambda _root: None)
    monkeypatch.setattr(amendment, "_implementation_bytes", lambda _root: implementation)
    monkeypatch.setattr(
        amendment,
        "_UNIQUE_FIRST_ADD_COMMIT",
        lambda _root, _relative, _payload: implementation_commit,
    )
    monkeypatch.setattr(
        amendment,
        "_read_pretty_json",
        lambda _root, relative, _label: (*documents[relative], commits[relative]),
    )
    monkeypatch.setattr(
        amendment,
        "_require_strict_ancestor",
        lambda _root, ancestor, descendant, label: ancestry.append((ancestor, descendant, label)),
    )
    monkeypatch.setattr(amendment, "_require_commit_tree", lambda *_args: None)
    monkeypatch.setattr(amendment, "_bound_repo_bytes", lambda *_args: b"parent")
    monkeypatch.setattr(amendment, "_GIT_BYTES", lambda *_args, **_kwargs: b"journal\n")

    def validate_journal(_payload, count, head, _label):
        assert count == amendment._A5_ACTIVATION_RECORD_COUNT
        assert head == amendment._A5_ACTIVATION_HEAD_SHA256
        records = [{"record_sha256": "0" * 64} for _ in range(count)]
        records[-1]["record_sha256"] = amendment._A5_ACTIVATION_HEAD_SHA256
        return tuple(records)

    monkeypatch.setattr(amendment, "_VALIDATE_JOURNAL_PREFIX", validate_journal)
    loaded, _payload, _commit = amendment._load_active_integration(tmp_path)
    return dict(loaded), ancestry


def test_synthetic_active_integration_validates_all_governance_layers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    integration, ancestry = _synthetic_active_integration(monkeypatch, tmp_path)
    assert integration["status"] == "active"
    assert [label for _ancestor, _descendant, label in ancestry] == [
        "A5 integration/A7 implementation",
        "A7 implementation/review",
        "A7 review/freeze",
        "A7 freeze/integration draft",
        "A7 integration draft/review",
        "A7 integration review/freeze",
    ]


def test_integration_reviewer_must_be_independent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    with pytest.raises(amendment.Amendment0007Error, match="integration review differs"):
        _synthetic_active_integration(monkeypatch, tmp_path, same_reviewer=True)


def test_worker_wrapper_requires_exact_preloaded_module_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker_preload.protocol, "score_boundary", lambda scores: scores)
    with pytest.raises(worker_preload.StrategyWorkerPreloadError, match="score-boundary"):
        worker_preload._verify_loaded_identities()


def test_preloaded_protocol_import_needs_no_package_search_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tournament_package = sys.modules["crypto_trade.tournament"]
    monkeypatch.setattr(tournament_package, "__path__", [])
    namespace: dict[str, object] = {}

    exec(
        "from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary",
        namespace,
    )

    assert namespace["score_boundary"] is worker_preload._PROTOCOL_SCORE_BOUNDARY


def test_worker_wrapper_root_argument_is_exact(tmp_path: Path) -> None:
    assert worker_preload._root_argument(["--root", str(tmp_path)]) == tmp_path.resolve()
    for values in ([], ["--root"], ["--root", str(tmp_path), "--root", str(tmp_path)]):
        with pytest.raises(worker_preload.StrategyWorkerPreloadError, match="exactly one"):
            worker_preload._root_argument(values)


def test_worker_preflight_failure_uses_frozen_worker_error_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = io.StringIO()
    monkeypatch.setattr(worker_preload.sys, "stdout", output)
    worker_preload._send_preflight_error(worker_preload.StrategyWorkerPreloadError("bad bytes"))

    assert json.loads(output.getvalue()) == {
        "error_type": "StrategySandboxError",
        "message": "A7 worker preload failed: bad bytes",
        "type": "error",
    }
