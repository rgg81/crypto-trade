"""CUP-50 generalization-first tournament."""

from crypto_trade.cup50.config import (
    FOLDS,
    IS_START,
    LANES,
    MANDATES,
    OOS_END,
    OOS_START,
    TEAM_IDS,
    load_config,
    validate_config,
)
from crypto_trade.cup50.neighbourhood import Dimension, Neighbourhood, generate_neighbourhood
from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2
from crypto_trade.cup50.replay import (
    CandidateReplay,
    EvaluationResultV2,
    ExecutionConfig,
    ReplayState,
    run_candidate,
)
from crypto_trade.cup50.scoring import (
    CellScore,
    NeighbourhoodScore,
    PointScore,
    RankedEntry,
    rank_entries,
    score_cell,
    score_neighbourhood,
    score_point,
)
from crypto_trade.cup50.snapshot import Snapshot, load_snapshot, stitch_snapshots
from crypto_trade.cup50.universe import (
    ListingEpisode,
    build_membership,
    canonical_daily_quote_volume,
    derive_listing_episodes,
    pure_crypto_symbols,
)

__all__ = [
    "CandidateReplay",
    "CellScore",
    "DecisionContextV2",
    "Dimension",
    "EvaluationResultV2",
    "ExecutionConfig",
    "FOLDS",
    "IS_START",
    "LANES",
    "ListingEpisode",
    "MANDATES",
    "Neighbourhood",
    "NeighbourhoodScore",
    "OOS_END",
    "OOS_START",
    "PointScore",
    "RankedEntry",
    "ReplayState",
    "Snapshot",
    "TEAM_IDS",
    "TargetStrategyV2",
    "build_membership",
    "canonical_daily_quote_volume",
    "derive_listing_episodes",
    "generate_neighbourhood",
    "load_config",
    "load_snapshot",
    "pure_crypto_symbols",
    "rank_entries",
    "run_candidate",
    "score_cell",
    "score_neighbourhood",
    "score_point",
    "stitch_snapshots",
    "validate_config",
]
