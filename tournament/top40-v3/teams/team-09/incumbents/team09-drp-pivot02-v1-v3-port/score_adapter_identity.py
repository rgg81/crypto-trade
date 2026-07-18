"""Candidate-local identity hook at the declared score boundary.

The V3 worker stages this file with the candidate.  It deliberately has no
organizer-side behavior: the strategy receives the same score object it passes
in, while an audit can still identify the declared boundary from source.
"""

from __future__ import annotations

ADAPTER_ID = "top40-v3-candidate-local-declared-score-boundary-v1"
HOOK_QUALNAME = "strategy.score_boundary"
CAPTURE_BOUNDARY = "candidate-declared-post-transform-pre-selection-weight-cap-risk"


def score_boundary[T: dict[str, float]](scores: T) -> T:
    """Return the exact supplied object without inspecting or copying it."""

    return scores
