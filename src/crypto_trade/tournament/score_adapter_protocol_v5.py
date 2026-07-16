"""Public identity hook for prospective Top-40 V2 score diagnostics.

Candidate code may import :func:`score_boundary` directly into ``strategy.py`` and call it at
the manifest-declared pre-construction boundary.  In ordinary development execution the hook is
an identity function.  Amendment 0005's sandboxed replay temporarily replaces only that direct
module binding with an organizer-owned identity capture.
"""

from __future__ import annotations

from typing import TypeVar

ADAPTER_ID = "top40-v2-preconstruction-score-boundary-v1"
HOOK_QUALNAME = "strategy.score_boundary"
CAPTURE_BOUNDARY = "post-transform-pre-selection-weight-cap-risk"

_ScoreDictionary = TypeVar("_ScoreDictionary", bound=dict[str, float])


def score_boundary(scores: _ScoreDictionary) -> _ScoreDictionary:
    """Return the exact object supplied by candidate code without inspecting or copying it."""

    return scores
