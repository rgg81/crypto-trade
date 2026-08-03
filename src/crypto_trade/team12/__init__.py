"""Post-tournament research and paper-trading support for the frozen Team 12 winner."""

from crypto_trade.team12.authority import (
    CANDIDATE_ID,
    TEAM_ID,
    verify_deployment_authority,
    verify_frozen_authority,
)

__all__ = [
    "CANDIDATE_ID",
    "TEAM_ID",
    "verify_deployment_authority",
    "verify_frozen_authority",
]
