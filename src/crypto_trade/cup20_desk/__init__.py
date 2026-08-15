"""Forward paper desk for the CUP-20 winner, team-02 ``channel-position-ls``.

This package *consumes* the frozen tournament stack in ``crypto_trade.cup20`` and never modifies
it: ``src/crypto_trade/cup20`` is hash-bound by ``tournament/cup20/activation-freeze.json``. The
desk is paper-only -- there is no signed client and no order path anywhere in it.
"""

from crypto_trade.cup20_desk.authority import (
    AUTHORITY_FIELDS,
    SCHEMA_VERSION,
    TOURNAMENT,
    WINNER_CANDIDATE_ID,
    WINNER_TEAM_ID,
    DeploymentChangedError,
    DeskAuthority,
    candidate_root,
    current_desk_authority,
    evaluator_root,
    verify_desk_authority,
)

__all__ = [
    "AUTHORITY_FIELDS",
    "SCHEMA_VERSION",
    "TOURNAMENT",
    "WINNER_CANDIDATE_ID",
    "WINNER_TEAM_ID",
    "DeploymentChangedError",
    "DeskAuthority",
    "candidate_root",
    "current_desk_authority",
    "evaluator_root",
    "verify_desk_authority",
]
