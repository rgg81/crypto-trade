"""Deterministic tournament validation and scoring utilities."""

from crypto_trade.tournament.engine import (
    EvaluationResult,
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.metrics import (
    aggregate_daily_returns,
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.top40 import (
    HARD_COMPLIANCE_CHECKS,
    Submission,
    TeamScore,
    load_submission,
    score_tournament,
    validate_submission,
    verify_canonical_artifacts,
)

__all__ = [
    "HARD_COMPLIANCE_CHECKS",
    "REBALANCE_INSTRUCTION_COLUMN",
    "EvaluationResult",
    "EvaluatorConfig",
    "Submission",
    "TeamScore",
    "aggregate_daily_returns",
    "classify_btc_regimes",
    "compute_regime_sharpes",
    "compute_window_metrics",
    "evaluate_base_and_double_cost",
    "evaluate_targets",
    "generate_targets",
    "load_submission",
    "score_tournament",
    "sharpe_confidence_interval",
    "validate_submission",
    "verify_canonical_artifacts",
]
