from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament import runner_v3
from crypto_trade.tournament import top40_amendment_0001 as amendment
from crypto_trade.tournament import top40_amendment_0001_integration as integration
from crypto_trade.tournament.coaching_v3 import build_training_metric_packet
from crypto_trade.tournament.qualification_v3 import CandidateIdentity

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize(
    ("stage", "score_start", "score_end"),
    (
        ("train", "2020-02-03T00:00:00Z", "2022-06-30"),
        ("validation", "2022-07-01T00:00:00Z", "2023-06-30"),
        ("public", "2020-02-03T00:00:00Z", "2023-06-30"),
        ("private", "2023-07-01T00:00:00Z", "2024-06-30"),
        ("final_oos", "2024-07-01T00:00:00Z", "2026-06-30"),
    ),
)
def test_all_frozen_score_bounds_match_the_complete_parent_metric_packet(
    stage: str,
    score_start: str,
    score_end: str,
) -> None:
    index = pd.date_range("2019-11-01", "2026-06-30", freq="1D", tz="UTC")
    phase = np.arange(len(index), dtype=float)
    base = pd.Series(0.001 + np.sin(phase) * 0.0005, index=index, name="net_return")
    stressed = pd.Series(base.to_numpy() - 0.0001, index=index, name="net_return")
    btc = pd.Series(np.full(len(index), 0.003), index=index, name="btc_return")
    authorized = runner_v3.AuthorizedWindow(
        stage=stage,
        replay_start="2020-02-03T00:00:00Z",
        end_exclusive=(pd.Timestamp(score_end, tz="UTC") + pd.Timedelta(days=1)).isoformat(),
        score_start=score_start,
        score_end_inclusive=score_end,
    )
    config = {
        "statistics": {
            "bootstrap_samples": 100,
            "bootstrap_block_days": 5,
            "bootstrap_seed": 20260718,
        }
    }

    packet = amendment.compute_metrics_with_utc_bounds(
        base, stressed, btc, config, authorized
    )
    normalized = dataclasses.replace(
        authorized,
        score_start=amendment._explicit_utc(score_start),
        score_end_inclusive=amendment._explicit_utc(score_end),
    )
    expected = dict(
        amendment._PARENT_COMPUTE_METRICS(
            base,
            stressed,
            btc,
            config,
            normalized,
        )
    )
    parent_window = expected["scored_window"]
    expected["scored_window"] = runner_v3.EvaluationWindow(
        pd.Timestamp(score_start).strftime("%Y-%m-%d"),
        score_end,
        parent_window.metrics,
    )

    scored_window = packet["scored_window"]
    assert isinstance(scored_window, runner_v3.EvaluationWindow)
    assert packet == expected


def test_parent_mixed_bounds_reproduce_the_original_pandas_failure() -> None:
    index = pd.date_range("2020-01-01", "2020-03-31", freq="1D", tz="UTC")
    values = pd.Series(0.001, index=index, name="net_return")
    authorized = runner_v3.AuthorizedWindow(
        stage="train",
        replay_start="2020-01-01T00:00:00Z",
        end_exclusive="2020-04-01T00:00:00Z",
        score_start="2020-03-01T00:00:00Z",
        score_end_inclusive="2020-03-31",
    )
    config = {
        "statistics": {
            "bootstrap_samples": 100,
            "bootstrap_block_days": 5,
            "bootstrap_seed": 20260718,
        }
    }

    with pytest.raises(ValueError, match="same UTC offset"):
        amendment._PARENT_COMPUTE_METRICS(
            values,
            values,
            values.rename("btc_return"),
            config,
            authorized,
        )


def test_amended_train_metrics_are_accepted_by_the_frozen_coaching_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = pd.date_range("2020-01-01", "2022-06-30", freq="1D", tz="UTC")
    phase = np.arange(len(index), dtype=float)
    base = pd.Series(0.001 + np.sin(phase) * 0.0005, index=index, name="net_return")
    stressed = pd.Series(base.to_numpy() - 0.0001, index=index, name="net_return")
    btc = pd.Series(np.full(len(index), 0.003), index=index, name="btc_return")
    authorized = runner_v3.AuthorizedWindow(
        stage="train",
        replay_start="2020-02-03T00:00:00Z",
        end_exclusive="2022-07-01T00:00:00Z",
        score_start="2020-02-03T00:00:00Z",
        score_end_inclusive="2022-06-30",
    )
    metrics = amendment.compute_metrics_with_utc_bounds(
        base,
        stressed,
        btc,
        {
            "statistics": {
                "bootstrap_samples": 100,
                "bootstrap_block_days": 5,
                "bootstrap_seed": 20260718,
            }
        },
        authorized,
    )
    output = "reports-top40-v3/labs/team-01/amendment-canary"
    artifact_names = (
        "targets",
        "events",
        "positions",
        "evaluator_returns",
        "double_cost_evaluator_returns",
        "daily_returns",
        "double_cost_daily_returns",
        "trades",
    )
    authority = integration.IntegrationAuthority(
        freeze_file_sha256="0" * 64,
        freeze_commit="4" * 40,
        record_sha256="1" * 64,
        implementation_commit="2" * 40,
        config_sha256="3" * 64,
        parent_phase0_record_sha256=integration.PARENT_PHASE0_RECORD_SHA256,
        activation_journal_head_sha256=integration.ACTIVATION_JOURNAL_HEAD_SHA256,
    )
    monkeypatch.setattr(integration, "_VERIFY_INTEGRATION", lambda _root: authority)
    evaluator_sha256 = integration.evaluator_authority_sha256(ROOT)
    identity = CandidateIdentity(
        team_id="team-01",
        candidate_id="amendment-canary",
        source_bundle_sha256="a" * 64,
        strategy_sha256="b" * 64,
        dependency_lock_sha256="c" * 64,
        config_sha256="d" * 64,
        risk_policy_sha256="e" * 64,
        data_authority_sha256="f" * 64,
        evaluator_sha256=evaluator_sha256,
    )
    runner_packet = {
        "stage": "train",
        "team_id": "team-01",
        "entrypoint": "tournament/top40-v3/teams/team-01/strategy.py",
        "seeds": [20260718],
        "data_manifest_sha256": identity.data_authority_sha256,
        "config_sha256": identity.config_sha256,
        "strategy_sha256": identity.strategy_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "source_bundle_sha256": identity.source_bundle_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
        "pure_crypto_policy_sha256": "2" * 64,
        "pure_crypto_report_sha256": "3" * 64,
        "output_dir": output,
        "scored_window": dataclasses.asdict(metrics["scored_window"]),
        "double_cost_sharpe": metrics["double_cost_sharpe"],
        "regime_sharpe": metrics["regime_sharpe"],
        "confidence_intervals": {
            "net_sharpe_95": list(metrics["net_sharpe_confidence_interval"]),
            "double_cost_sharpe_95": list(
                metrics["double_cost_sharpe_confidence_interval"]
            ),
        },
        "artifacts": {name: f"{output}/{name}.artifact" for name in artifact_names},
        "artifact_sha256": {
            name: format(index + 4, "x")[-1] * 64
            for index, name in enumerate(artifact_names)
        },
        "artifact_sizes": {
            name: 1_000 + index for index, name in enumerate(artifact_names)
        },
        "decision_count": 2_600,
        "event_count": 4_000,
        "trade_count": 1_500,
    }

    coaching_packet = build_training_metric_packet(runner_packet, identity)

    assert coaching_packet["scored_window"]["start"] == "2020-02-03"
    assert coaching_packet["scored_window"]["end"] == "2022-06-30"


def test_installer_is_idempotent_and_rejects_an_unverified_metric_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(amendment, "_sha256_file", lambda _path: amendment.PARENT_RUNNER_SHA256)
    monkeypatch.setattr(runner_v3, "_compute_metrics", amendment._PARENT_COMPUTE_METRICS)
    monkeypatch.setattr(
        runner_v3,
        "_evaluator_authority_sha256",
        amendment._PARENT_EVALUATOR_AUTHORITY_SHA256,
    )

    amendment.install()
    amendment.install()
    assert runner_v3._compute_metrics is amendment.compute_metrics_with_utc_bounds
    assert runner_v3._evaluator_authority_sha256 is amendment.evaluator_authority_sha256

    monkeypatch.setattr(runner_v3, "_compute_metrics", lambda *_args: {})
    with pytest.raises(amendment.Amendment0001Error, match="replaced unexpectedly"):
        amendment.install()
