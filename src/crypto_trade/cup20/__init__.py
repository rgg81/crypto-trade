"""CUP-20 tournament policy, evaluation and scoring."""

from crypto_trade.cup20.activation import build_activation_record, verify_activation
from crypto_trade.cup20.archive import (
    archive_directory,
    bundle_digest,
    scan_for_blindness_violations,
    verify_neighbourhood_coordinates,
)
from crypto_trade.cup20.bootstrap import (
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)
from crypto_trade.cup20.config import (
    IS_END,
    SEALED_END,
    SEALED_START,
    TEAM_IDS,
    LoadedConfig,
    load_config,
    validate_config,
)
from crypto_trade.cup20.journal import (
    accepted_trial_count,
    append_record,
    read_records,
    verify_chain,
)
from crypto_trade.cup20.metrics import (
    WindowMetrics,
    daily_returns,
    fold_positive_pnl_shares,
    fold_sharpes,
    holdout_folds,
    is_folds,
    max_drawdown,
    sharpe,
    window_metrics,
)
from crypto_trade.cup20.neighbourhood import (
    NeighbourhoodDeclaration,
    load_declaration,
    median_metrics,
    positive_point_fraction,
)
from crypto_trade.cup20.qualification import GateVector, evaluate_floors
from crypto_trade.cup20.report import atomic_release, build_packet, write_manifest
from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars
from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    evaluator_config,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.cup20.scoring import (
    RankedEntry,
    rank_entries,
    robustness_score,
    select_advancing,
)
from crypto_trade.cup20.snapshot import (
    Snapshot,
    SnapshotPaths,
    load_snapshot,
    resolve_is_start,
    write_split_snapshots,
)
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times

__all__ = [
    "IS_END",
    "SEALED_END",
    "SEALED_START",
    "TEAM_IDS",
    "CandidateRun",
    "GateVector",
    "LoadedConfig",
    "NeighbourhoodDeclaration",
    "RankedEntry",
    "Snapshot",
    "SnapshotPaths",
    "WindowMetrics",
    "accepted_trial_count",
    "append_record",
    "apply_risk_scalars",
    "archive_directory",
    "atomic_release",
    "build_activation_record",
    "build_membership",
    "build_packet",
    "bundle_digest",
    "circular_block_bootstrap_positive_fraction",
    "common_risk_scalars",
    "daily_returns",
    "decision_grid",
    "evaluate_floors",
    "evaluator_config",
    "fold_positive_pnl_shares",
    "fold_sharpes",
    "holdout_folds",
    "is_folds",
    "load_config",
    "load_declaration",
    "load_snapshot",
    "max_drawdown",
    "median_metrics",
    "normalise_unit_gross",
    "positive_point_fraction",
    "rank_entries",
    "read_records",
    "resolve_is_start",
    "robustness_score",
    "run_candidate",
    "scan_for_blindness_violations",
    "select_advancing",
    "sharpe",
    "trial_adjusted_confidence",
    "validate_config",
    "verify_activation",
    "verify_chain",
    "verify_neighbourhood_coordinates",
    "weekly_reconstitution_times",
    "window_metrics",
    "write_manifest",
    "write_split_snapshots",
]
