from __future__ import annotations

import json

import pytest

from crypto_trade.cup50v2.activation import build_activation_record, verify_activation


def test_activation_binds_relative_artifacts_and_transitive_imports(tmp_path) -> None:
    package = tmp_path / "src" / "crypto_trade" / "cup50v2"
    package.mkdir(parents=True)
    (package / "entry.py").write_text("from crypto_trade.cup50v2 import helper\n")
    (package / "helper.py").write_text("VALUE = 1\n")
    (tmp_path / "config.toml").write_text("name='cup50v2'\n")
    (tmp_path / "tests.out").write_text("passed\n")
    destination = tmp_path / "activation.json"
    build_activation_record(
        destination,
        repository_root=tmp_path,
        artifacts=["config.toml"],
        evaluator_entries=["src/crypto_trade/cup50v2/entry.py"],
        git_commit="a" * 40,
        git_clean=True,
        sandbox_image="cup50v2",
        sandbox_image_digest="b" * 64,
        focused_test_transcript="tests.out",
        isolation_verified=True,
    )
    record = verify_activation(destination, repository_root=tmp_path)
    assert "src/crypto_trade/cup50v2/helper.py" in record["artifacts"]
    with pytest.raises(FileExistsError):
        build_activation_record(
            destination,
            repository_root=tmp_path,
            artifacts=[],
            evaluator_entries=["src/crypto_trade/cup50v2/entry.py"],
            git_commit="a" * 40,
            git_clean=True,
            sandbox_image="cup50v2",
            sandbox_image_digest="b" * 64,
            focused_test_transcript="tests.out",
            isolation_verified=True,
        )
    (package / "helper.py").write_text("VALUE = 2\n")
    with pytest.raises(ValueError, match="drifted"):
        verify_activation(destination, repository_root=tmp_path)


def test_activation_record_itself_is_digest_bound(tmp_path) -> None:
    # A malformed hand-written record cannot be mistaken for an activated tournament.
    path = tmp_path / "activation.json"
    path.write_text(json.dumps({"activation_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="record digest"):
        verify_activation(path, repository_root=tmp_path)
