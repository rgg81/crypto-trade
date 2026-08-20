from __future__ import annotations

import json

import pandas as pd
import pytest

from crypto_trade.cup50v2.isolation import (
    evaluator_container_command,
    export_evaluator_bundle,
    export_protocol_bundle,
    require_image_digest,
    scan_research_root,
)
from crypto_trade.cup50v2.paper import (
    digest_markdown,
    first_boundary_after,
    freeze_desk_authority,
    healthcheck,
    require_append_only,
    verify_desk_authority,
    verify_parity,
)
from crypto_trade.cup50v2.snapshot import (
    Snapshot,
    load_snapshot,
    stitch_snapshots,
    verify_semantic_coverage,
    write_split_snapshots,
    write_team_visible_snapshot,
)


def test_physical_split_endpoint_semantics_and_roster_censorship(tmp_path) -> None:
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    split = pd.Timestamp("2024-02-01T00:00:00Z")
    end = pd.Timestamp("2024-03-01T00:00:00Z")
    bars = pd.DataFrame(
        [
            [start, start + pd.Timedelta(hours=8), "A", 1, 1, 10],
            [split - pd.Timedelta(hours=8), split, "A", 1, 1, 10],
            [split, split + pd.Timedelta(hours=8), "B", 1, 1, 10],
        ],
        columns=["open_time", "close_time", "symbol", "open", "close", "quote_volume"],
    )
    funding = pd.DataFrame(
        [
            [start, "A", 0.0, 1.0],
            [split, "A", 0.0, 1.0],
            [split, "B", 0.0, 1.0],
            [end, "B", 0.0, 1.0],
        ],
        columns=["funding_time", "symbol", "funding_rate", "mark_price"],
    )
    marks = funding.rename(columns={"funding_time": "mark_time"})[
        ["mark_time", "symbol", "mark_price"]
    ]
    membership = pd.DataFrame(
        [[start, "A", 1, 10.0], [split, "B", 1, 10.0]],
        columns=[
            "reconstitution_time",
            "symbol",
            "liquidity_rank",
            "median_daily_quote_volume",
        ],
    )
    metadata = pd.DataFrame(
        [
            ["A", start - pd.Timedelta(days=1), end, "current"],
            ["B", split - pd.Timedelta(days=1), end, "current"],
        ],
        columns=["symbol", "onboard_date", "delivery_date", "metadata_source"],
    )
    research_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_start=start,
        oos_start=split,
        oos_end=end,
    )
    assert research_paths.manifest.stat().st_mode & 0o444 == 0o444
    assert sealed_paths.manifest.stat().st_mode & 0o444 == 0o444
    research, sealed = load_snapshot(research_paths.root), load_snapshot(sealed_paths.root)
    verify_semantic_coverage(research)
    verify_semantic_coverage(sealed)
    assert set(research.bars["symbol"]) == {"A"}
    assert set(research.contract_metadata["symbol"]) == {"A"}
    assert split in set(research.funding["funding_time"])
    assert (sealed.funding["funding_time"] > split).all()
    stitched = stitch_snapshots(research, sealed)
    assert set(stitched.membership["symbol"]) == {"A", "B"}
    visible = write_team_visible_snapshot(research, root=tmp_path / "team-is")
    assert "open" not in pd.read_parquet(visible.files["bars"])
    assert "mark_price" not in pd.read_parquet(visible.files["funding"])
    assert not (visible.root / "mark_prices.parquet").exists()

    manifest = json.loads(research_paths.manifest.read_text())
    manifest["files"]["bars"]["rows"] += 1
    research_paths.manifest.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest body digest"):
        load_snapshot(research_paths.root)


def test_launch_boundary_is_strictly_after_release() -> None:
    assert first_boundary_after(pd.Timestamp("2026-08-17T08:00:00Z")) == pd.Timestamp(
        "2026-08-17T16:00:00Z"
    )


def test_paper_authority_detects_strategy_lineage_change(tmp_path) -> None:
    release = tmp_path / "release.json"
    winner = tmp_path / "strategy.py"
    authority = tmp_path / "authority.json"
    release.write_text("released\n")
    winner.write_text("VALUE = 1\n")
    freeze_desk_authority(
        authority,
        release_path=release,
        winner_bundle=winner,
        nomination_sha256="a" * 64,
        release_time=pd.Timestamp("2026-08-17T08:00:00Z"),
    )
    verify_desk_authority(authority, release_path=release, winner_bundle=winner)
    winner.write_text("VALUE = 2\n")
    with pytest.raises(ValueError, match="new lineage"):
        verify_desk_authority(authority, release_path=release, winner_bundle=winner)


def test_append_only_cache_generation() -> None:
    before = pd.DataFrame({"time": [1, 2], "value": [10.0, 20.0]})
    after = pd.DataFrame({"time": [1, 2, 3], "value": [10.0, 20.0, 30.0]})
    require_append_only(before, after, key_columns=["time"])
    after.loc[0, "value"] = 11.0
    with pytest.raises(AssertionError):
        require_append_only(before, after, key_columns=["time"])


def test_paper_backtest_parity_is_bit_exact() -> None:
    targets = pd.DataFrame(
        {"AUSDT": [0.1, 0.0]},
        index=pd.date_range("2026-08-17", periods=2, freq="8h", tz="UTC"),
    )
    digest = verify_parity(targets, targets.copy(deep=True))
    assert len(digest) == 64
    drifted = targets.copy(deep=True)
    drifted.iloc[-1, 0] = 1e-12
    with pytest.raises(AssertionError):
        verify_parity(targets, drifted)


def test_paper_healthcheck_and_digest_fail_closed() -> None:
    now = pd.Timestamp("2026-08-18T00:00:00Z")
    state = {
        "lineage_sha256": "a" * 64,
        "latest_boundary": "2026-08-17T16:00:00Z",
        "membership_count": 50,
        "parity": True,
        "append_invariant": True,
        "public_data_only": True,
    }
    health = healthcheck(state, now=now)
    assert health.status == "healthy"
    assert "Forward days: 1 / 365" in digest_markdown(health, forward_days=1, observations=3)
    state["membership_count"] = 49
    assert healthcheck(state, now=now).status == "failed"


def test_clean_room_scan_and_container_contract(tmp_path) -> None:
    team = tmp_path / "team"
    protocol = tmp_path / "protocol"
    snapshot = tmp_path / "is"
    output = tmp_path / "output"
    policy = tmp_path / "config.toml"
    policy.write_text("name='cup50v2'\n")
    for path in (team, protocol, snapshot):
        path.mkdir()
    write_team_visible_snapshot(
        Snapshot(
            pd.DataFrame(columns=["open", "close"]),
            pd.DataFrame(columns=["mark_price", "funding_rate"]),
            pd.DataFrame(columns=["mark_price"]),
            pd.DataFrame(),
            pd.DataFrame(),
            "a" * 64,
            pd.Timestamp("2024-01-01T00:00:00Z"),
            pd.Timestamp("2024-02-01T00:00:00Z"),
            False,
        ),
        root=snapshot,
    )
    assert scan_research_root(team) == ()
    command = evaluator_container_command(
        image="cup50v2@sha256:" + "a" * 64,
        research_root=team,
        protocol_root=protocol,
        is_snapshot=snapshot,
        output_root=output,
        command=["python", "evaluate.py"],
        read_only_files={policy: "/workspace/config.toml"},
    )
    assert "--network=none" in command and "--read-only" in command
    assert any(part.startswith("--user=") for part in command)
    assert any("dst=/workspace/config.toml,readonly" in part for part in command)
    (team / ".git").mkdir()
    assert scan_research_root(team) == (".git",)
    (team / "raw-cache.parquet").write_bytes(b"not really parquet")
    assert "raw-cache.parquet" in scan_research_root(team)
    (team / "escape.py").write_text("import pathlib\npathlib.Path('/tmp').read_text()\n")
    assert "forbidden-import:escape.py:pathlib" in scan_research_root(team)


def test_protocol_export_contains_only_the_strategy_interface(tmp_path) -> None:
    source = tmp_path / "protocol.py"
    source.write_text("VALUE = 1\n")
    destination = tmp_path / "export"

    manifest = export_protocol_bundle(source, destination)

    assert manifest["namespace"] == "cup50v2-protocol-export"
    assert destination.stat().st_mode & 0o777 == 0o755
    files = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*"))
    assert files == [
        "crypto_trade",
        "crypto_trade/__init__.py",
        "crypto_trade/cup50v2",
        "crypto_trade/cup50v2/__init__.py",
        "crypto_trade/cup50v2/protocol.py",
        "manifest.json",
    ]
    with pytest.raises(FileExistsError):
        export_protocol_bundle(source, destination)


def test_evaluator_export_rejects_imports_from_earlier_namespaces(tmp_path) -> None:
    source = tmp_path / "cup50v2"
    source.mkdir()
    (source / "__init__.py").write_text("")
    (source / "entry.py").write_text("from crypto_trade.cup50v2 import helper\n")
    (source / "helper.py").write_text("VALUE = 1\n")
    destination = tmp_path / "evaluator"

    manifest = export_evaluator_bundle(source, destination)

    assert manifest["namespace"] == "cup50v2-evaluator-export"
    assert set(manifest["files"]) == {
        "crypto_trade/cup50v2/__init__.py",
        "crypto_trade/cup50v2/entry.py",
        "crypto_trade/cup50v2/helper.py",
    }
    contaminated = tmp_path / "cup50v2-contaminated"
    contaminated.mkdir()
    (contaminated / "bad.py").write_text("from crypto_trade.cup20 import replay\n")
    with pytest.raises(ValueError, match="source must be the CUP-50 v2"):
        export_evaluator_bundle(contaminated, tmp_path / "bad-export")

    (source / "bad.py").write_text("from crypto_trade.cup20 import replay\n")
    with pytest.raises(ValueError, match="outside CUP-50 v2"):
        export_evaluator_bundle(source, tmp_path / "bad-export")


def test_sandbox_image_tag_must_resolve_to_bound_digest(monkeypatch) -> None:
    class Result:
        returncode = 0
        stdout = "sha256:" + "a" * 64 + "\n"

    monkeypatch.setattr(
        "crypto_trade.cup50v2.isolation.subprocess.run", lambda *args, **kwargs: Result()
    )
    assert require_image_digest("cup50v2", "a" * 64) == "sha256:" + "a" * 64
    with pytest.raises(RuntimeError, match="does not resolve"):
        require_image_digest("cup50v2", "b" * 64)
