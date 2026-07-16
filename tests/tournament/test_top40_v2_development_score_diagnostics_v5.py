"""Focused scientific-contract tests for Amendment 0005."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament import development_score_diagnostics_v5 as diagnostics
from crypto_trade.tournament.amendment_integrity_v2 import (
    pretty_json_bytes,
    sha256_bytes,
)
from crypto_trade.tournament.development_score_diagnostics_v5 import (
    label_score_panel,
    parse_executable_source_manifest,
    parse_score_adapter_manifest,
    parse_semantic_coupling_review,
)

EXECUTABLE_SOURCE_MANIFEST_PATH = (
    "tournament/top40-v2/teams/team-04/score-adapters/candidate-04.executable-source-manifest.json"
)


def test_executable_source_manifest_is_acyclic_and_complete() -> None:
    payload = pretty_json_bytes(
        {
            "schema_version": 1,
            "manifest_kind": "top40-v2-executable-source-manifest-v1",
            "team_id": "team-04",
            "family_id": "family-04",
            "candidate_id": "candidate-04",
            "files": [
                {"path": "risk_policy.json", "sha256": "a" * 64, "size": 10},
                {"path": "strategy.py", "sha256": "b" * 64, "size": 20},
            ],
        }
    )
    parsed = parse_executable_source_manifest(
        payload,
        expected_team_id="team-04",
        expected_family_id="family-04",
        expected_candidate_id="candidate-04",
    )
    assert [entry["path"] for entry in parsed["files"]] == [
        "risk_policy.json",
        "strategy.py",
    ]


@pytest.mark.parametrize(
    ("commit", "label"),
    [
        ("1" * 40, "semantic-review tree"),
        ("2" * 40, "score-manifest tree"),
        ("3" * 40, "registration tree"),
    ],
)
def test_each_candidate_history_boundary_rejects_an_incomplete_executable_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    commit: str,
    label: str,
) -> None:
    source = {
        "helper.py": b"VALUE = 1\n",
        "risk_policy.json": b"{}\n",
        "strategy.py": b"from helper import VALUE\n",
    }
    manifest = {
        "files": [
            {
                "path": relative,
                "sha256": sha256_bytes(source[relative]),
                "size": len(source[relative]),
            }
            for relative in ("risk_policy.json", "strategy.py")
        ]
    }
    boundary_label = label
    materialized: list[tuple[str, str]] = []

    def fake_git_bytes(
        root: Path,
        *arguments: str,
        label: str,
    ) -> bytes:
        assert root == tmp_path
        assert arguments[0] == "show"
        bound_commit, relative = arguments[1].split(":", 1)
        assert bound_commit == commit
        prefix = "tournament/top40-v2/teams/team-04/"
        assert relative.startswith(prefix)
        assert label.startswith(f"{boundary_label} executable dependency ")
        return source[relative.removeprefix(prefix)]

    def fake_materialize_team_tree(
        root: Path,
        bound_commit: str,
        team_id: str,
        destination: Path,
    ) -> None:
        assert root == tmp_path
        assert (bound_commit, team_id) == (commit, "team-04")
        materialized.append((bound_commit, team_id))
        destination.mkdir(mode=0o700, parents=True, exist_ok=False)
        for relative, payload in source.items():
            (destination / relative).write_bytes(payload)

    monkeypatch.setattr(diagnostics, "git_bytes", fake_git_bytes)
    monkeypatch.setattr(diagnostics, "_A1_MATERIALIZE_TREE", fake_materialize_team_tree)

    with pytest.raises(
        ValueError,
        match=f"{label} executable dependency set is incomplete",
    ):
        diagnostics.verify_executable_sources_at_commit(
            tmp_path,
            commit,
            "team-04",
            manifest,
            label=label,
        )
    assert materialized == [(commit, "team-04")]


def _manifest(*, horizon: int = 48) -> bytes:
    return pretty_json_bytes(
        {
            "schema_version": 1,
            "adapter_id": "top40-v2-declared-score-boundary-v1",
            "team_id": "team-04",
            "family_id": "family-04",
            "candidate_id": "candidate-04",
            "stage": "development",
            "hook": "strategy.score_boundary",
            "capture_boundary": "candidate-declared-post-transform-pre-selection-weight-cap-risk",
            "schedule_utc": {
                "anchor_timestamp_utc": "2020-02-03T00:00:00Z",
                "interval_hours": 24,
            },
            "label": {
                "label_id": "manifest-horizon-simple-executable-open-to-open-return-v1",
                "holding_horizon_hours": horizon,
                "return_definition": "simple-executable-open-to-open",
                "executable_price_column": "open",
                "score_direction": "higher-score-higher-return",
                "statistic_id": "globally-pooled-pearson-v1",
                "purge_cross_fold_endpoints": True,
                "minimum_pairs": 2,
            },
            "score_description": "Higher transformed values imply higher expected returns.",
            "semantic_coupling_review_sha256": "a" * 64,
        }
    )


def test_manifest_supports_fixed_48_hour_horizon() -> None:
    manifest = parse_score_adapter_manifest(
        _manifest(),
        expected_team_id="team-04",
        expected_family_id="family-04",
        expected_candidate_id="candidate-04",
    )
    assert manifest.holding_horizon_hours == 48


def test_labels_are_exact_simple_open_returns_and_globally_pooled_pearson() -> None:
    manifest = parse_score_adapter_manifest(_manifest())
    scores = pd.DataFrame(
        {
            "decision_time": [
                "2020-02-03T00:00:00Z",
                "2020-02-03T00:00:00Z",
                "2020-08-31T00:00:00Z",
            ],
            "symbol": ["AUSDT", "BUSDT", "AUSDT"],
            "score": [1.0, 2.0, 9.0],
        }
    )
    bars = pd.DataFrame(
        {
            "open_time": [
                "2020-02-03T00:00:00Z",
                "2020-02-05T00:00:00Z",
                "2020-02-03T00:00:00Z",
                "2020-02-05T00:00:00Z",
            ],
            "symbol": ["AUSDT", "AUSDT", "BUSDT", "BUSDT"],
            "open": [100.0, 110.0, 100.0, 120.0],
        }
    )
    panel, statistics = label_score_panel(scores, bars, manifest)
    assert panel["forward_return"].tolist() == pytest.approx([0.1, 0.2])
    assert statistics["development_pearson"] == pytest.approx(1.0)
    assert statistics["purged_fold_boundary_decision_count"] == 1
    assert statistics["qualification_gate"] is False


def test_manifest_rejects_non_grid_horizon() -> None:
    with pytest.raises(ValueError, match="holding horizon"):
        parse_score_adapter_manifest(_manifest(horizon=10))


def test_static_review_is_hash_bindable_but_explicitly_not_runtime_proof() -> None:
    payload = pretty_json_bytes(
        {
            "schema_version": 1,
            "review_kind": "top40-v2-score-semantic-coupling-static-review-v1",
            "team_id": "team-04",
            "family_id": "family-04",
            "candidate_id": "candidate-04",
            "strategy_sha256": "a" * 64,
            "executable_source_manifest_path": EXECUTABLE_SOURCE_MANIFEST_PATH,
            "executable_source_manifest_sha256": "b" * 64,
            "hook": "strategy.score_boundary",
            "declared_capture_boundary": (
                "candidate-declared-post-transform-pre-selection-weight-cap-risk"
            ),
            "decision": "approve",
            "reviewer_id": "independent-reviewer",
            "reviewed_at_utc": "2026-07-16T00:00:00Z",
            "findings": {
                "direct_hook_call_found": True,
                "score_object_is_declared_model_ranking_signal": True,
                "hook_after_declared_score_transform": True,
                "hook_before_selection_weight_caps_and_risk": True,
                "no_decoy_or_transient_score_path_found": True,
            },
            "runtime_proof_limit": "static-review-attestation-not-runtime-semantic-proof",
        }
    )
    parsed = parse_semantic_coupling_review(
        payload,
        expected_team_id="team-04",
        expected_family_id="family-04",
        expected_candidate_id="candidate-04",
        expected_strategy_sha256="a" * 64,
        expected_executable_source_manifest_path=EXECUTABLE_SOURCE_MANIFEST_PATH,
        expected_executable_source_manifest_sha256="b" * 64,
    )
    assert parsed["runtime_proof_limit"].endswith("not-runtime-semantic-proof")
    with pytest.raises(ValueError, match="binding"):
        parse_semantic_coupling_review(
            payload,
            expected_team_id="team-04",
            expected_family_id="family-04",
            expected_candidate_id="candidate-04",
            expected_strategy_sha256="b" * 64,
            expected_executable_source_manifest_path=EXECUTABLE_SOURCE_MANIFEST_PATH,
            expected_executable_source_manifest_sha256="b" * 64,
        )
