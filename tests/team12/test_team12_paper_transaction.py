from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

REPOSITORY = Path(__file__).parents[2]


def _load_runner():
    path = REPOSITORY / "run_team12_paper.py"
    spec = importlib.util.spec_from_file_location(
        "run_team12_paper_for_test",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()


def _bind_cache(paper: Path, generation: Path) -> None:
    manifest = generation / "cache-manifest.json"
    payload = {
        "status": "PASS",
        "artifacts": {
            "cache_manifest": {
                "path": manifest.relative_to(paper).as_posix(),
                "rows": 1,
                "sha256": runner.sha256_file(manifest),
                "size": manifest.stat().st_size,
            }
        },
    }
    (paper / "integrity.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_refresh_prepares_generation_without_publishing_or_pruning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_root = tmp_path / "market-cache"
    current = cache_root / "generations" / "old"
    current.mkdir(parents=True)
    (current / "seed").write_text("old", encoding="utf-8")
    (cache_root / "CURRENT").write_text(
        "generations/old\n",
        encoding="utf-8",
    )

    def fake_build(*args: object, **kwargs: object) -> SimpleNamespace:
        staging = Path(kwargs["cache_dir"])
        (staging / "cache-manifest.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        return SimpleNamespace(market_data="market", diagnostics="diagnostics")

    monkeypatch.setattr(
        runner,
        "_current_cache_generation",
        lambda *args, **kwargs: current,
    )
    monkeypatch.setattr(runner, "build_live_market_data", fake_build)
    monkeypatch.setattr(
        runner,
        "verify_live_cache_manifest",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        runner,
        "_prune_directories",
        lambda *args, **kwargs: pytest.fail("prepare pruned cache generations"),
    )

    prepared = runner._refresh_cache_generation(
        object(),
        boundary=pd.Timestamp("2026-07-27T00:00:00Z"),
        cache_root=cache_root,
        client=object(),
        prior_accounting_admissions=None,
    )

    assert prepared.cache_dir.is_dir()
    assert prepared.cache_dir != current
    assert (cache_root / "CURRENT").read_text(encoding="utf-8") == (
        "generations/old\n"
    )


def test_persist_failure_never_publishes_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "market-cache" / "generations" / "candidate"
    candidate.mkdir(parents=True)
    live_data = SimpleNamespace(cache_dir=candidate)
    monkeypatch.setattr(runner, "load_frozen_snapshot", object)
    monkeypatch.setattr(
        runner,
        "_refresh_cache_generation",
        lambda *args, **kwargs: live_data,
    )
    monkeypatch.setattr(runner, "run_live_replay", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        runner,
        "persist_paper_tick",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("persist failed")),
    )
    monkeypatch.setattr(
        runner,
        "_publish_committed_cache",
        lambda *args, **kwargs: pytest.fail("failed tick published cache"),
    )

    with pytest.raises(RuntimeError, match="persist failed"):
        runner.paper_tick(
            boundary=pd.Timestamp("2026-07-27T00:00:00Z"),
            paper_dir=tmp_path,
            refresh=False,
        )


def test_success_publishes_only_after_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "market-cache" / "generations" / "candidate"
    candidate.mkdir(parents=True)
    live_data = SimpleNamespace(cache_dir=candidate)
    order: list[str] = []
    monkeypatch.setattr(runner, "load_frozen_snapshot", object)
    monkeypatch.setattr(
        runner,
        "_refresh_cache_generation",
        lambda *args, **kwargs: live_data,
    )
    monkeypatch.setattr(runner, "run_live_replay", lambda *args, **kwargs: object())

    def persist(*args: object, **kwargs: object) -> dict[str, Path]:
        order.append("persist")
        return {"integrity": tmp_path / "integrity.json"}

    def publish(paper: Path, generation: Path) -> None:
        assert paper == tmp_path
        assert generation == candidate
        order.append("publish")

    monkeypatch.setattr(runner, "persist_paper_tick", persist)
    monkeypatch.setattr(runner, "_publish_committed_cache", publish)

    runner.paper_tick(
        boundary=pd.Timestamp("2026-07-27T00:00:00Z"),
        paper_dir=tmp_path,
        refresh=False,
    )
    assert order == ["persist", "publish"]


def test_publish_requires_exact_integrity_binding_before_prune(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper = tmp_path
    generation = paper / "market-cache" / "generations" / "candidate"
    generation.mkdir(parents=True)
    (generation / "cache-manifest.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    _bind_cache(paper, generation)
    monkeypatch.setattr(
        runner,
        "verify_live_cache_manifest",
        lambda *args, **kwargs: {},
    )
    observed: dict[str, object] = {}

    def prune(
        root: Path,
        *,
        keep: int,
        preserve: set[Path] | None = None,
    ) -> None:
        observed["root"] = root
        observed["keep"] = keep
        observed["preserve"] = preserve
        assert (paper / "market-cache" / "CURRENT").read_text(
            encoding="utf-8"
        ) == "generations/candidate\n"

    monkeypatch.setattr(runner, "_prune_directories", prune)
    runner._publish_committed_cache(paper, generation)

    assert observed["keep"] == 9
    assert observed["preserve"] == {generation.resolve()}


def test_publish_refuses_unbound_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper = tmp_path
    bound = paper / "market-cache" / "generations" / "bound"
    candidate = paper / "market-cache" / "generations" / "candidate"
    for generation in (bound, candidate):
        generation.mkdir(parents=True)
        (generation / "cache-manifest.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
    _bind_cache(paper, bound)
    monkeypatch.setattr(
        runner,
        "verify_live_cache_manifest",
        lambda *args, **kwargs: {},
    )
    with pytest.raises(RuntimeError, match="does not bind"):
        runner._publish_committed_cache(paper, candidate)
    assert not (paper / "market-cache" / "CURRENT").exists()


def test_reconcile_derives_current_from_integrity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper = tmp_path
    bound = paper / "market-cache" / "generations" / "bound"
    stale = paper / "market-cache" / "generations" / "stale"
    for generation in (bound, stale):
        generation.mkdir(parents=True)
        (generation / "cache-manifest.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
    _bind_cache(paper, bound)
    (paper / "market-cache" / "CURRENT").write_text(
        "generations/stale\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "verify_live_cache_manifest",
        lambda *args, **kwargs: {},
    )

    runner._reconcile_current_from_integrity(paper)

    assert (paper / "market-cache" / "CURRENT").read_text(
        encoding="utf-8"
    ) == "generations/bound\n"


def test_prune_always_preserves_bound_generation(tmp_path: Path) -> None:
    bound = tmp_path / "old-bound"
    unbound_a = tmp_path / "unbound-a"
    unbound_b = tmp_path / "unbound-b"
    for path in (bound, unbound_a, unbound_b):
        path.mkdir()

    runner._prune_directories(
        tmp_path,
        keep=0,
        preserve={bound},
    )

    assert bound.is_dir()
    assert not unbound_a.exists()
    assert not unbound_b.exists()
