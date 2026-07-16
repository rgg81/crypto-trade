"""Focused scientific-contract tests for Amendment 0005."""

from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.amendment_integrity_v2 import pretty_json_bytes
from crypto_trade.tournament.development_score_diagnostics_v5 import (
    label_score_panel,
    parse_score_adapter_manifest,
    parse_semantic_coupling_review,
)


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
    )
    assert parsed["runtime_proof_limit"].endswith("not-runtime-semantic-proof")
    with pytest.raises(ValueError, match="binding"):
        parse_semantic_coupling_review(
            payload,
            expected_team_id="team-04",
            expected_family_id="family-04",
            expected_candidate_id="candidate-04",
            expected_strategy_sha256="b" * 64,
        )
