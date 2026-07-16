"""Public identity hook for prospective Top-40 V2 declared-score diagnostics.

Candidate code may import :func:`score_boundary` directly into ``strategy.py`` and call it at
the candidate-declared score boundary. In ordinary development execution the hook is an identity
function. Amendment 0005's sandboxed replay temporarily replaces only that direct module binding
with an organizer-owned identity capture. Runtime capture does not prove that the supplied values
are the model's ranking signal or that the call is semantically before portfolio construction;
that claim requires a separately hash-bound candidate-specific static source review.
"""

from __future__ import annotations

from typing import TypeVar

ADAPTER_ID = "top40-v2-declared-score-boundary-v1"
HOOK_QUALNAME = "strategy.score_boundary"
CAPTURE_BOUNDARY = "candidate-declared-post-transform-pre-selection-weight-cap-risk"

_ScoreDictionary = TypeVar("_ScoreDictionary", bound=dict[str, float])


def score_boundary(scores: _ScoreDictionary) -> _ScoreDictionary:
    """Return the exact object supplied by candidate code without inspecting or copying it."""

    return scores
