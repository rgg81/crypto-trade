"""Deprecated noncanonical BER audit serializer; A5 never executes this module.

The canonical score source is the organizer-owned ``score_boundary`` call in
``strategy.py``.  This pre-A5 artifact remains only for byte-level audit tests
and must not be promoted, registered as an adapter, or used for official IC.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_MODULE_NAME = "_team04_pivot01_ber_strategy"
_PIVOT_DIR = Path(__file__).resolve().parent


def _load_strategy_module() -> ModuleType:
    existing = sys.modules.get(_MODULE_NAME)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PIVOT_DIR / "strategy.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Team 04 BER strategy")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ber = _load_strategy_module()


class OrganizerScoreAdapter:
    """Serialize scores for noncanonical audit comparisons only."""

    canonical = False
    official_score_source = False
    role = "deprecated-noncanonical-audit-only"
    schema_version = 1
    team_id = "team-04"
    family_id = "team-04-broad-exhaustion-reversal-v1"
    candidate_id = "team-04-ber-reference-001"
    score_name = "ber_ranked_exhaustion_reversal"
    higher_score_role = "long"

    def extract_scores(self, context: Any, *, seed: int) -> dict[str, float] | None:
        scores = ber.build_strategy().preconstruction_scores(context, seed=seed)
        if scores is None:
            return None
        return {symbol: scores[symbol] for symbol in sorted(scores)}

    def score_record(self, context: Any, *, seed: int) -> dict[str, Any] | None:
        scores = self.extract_scores(context, seed=seed)
        if scores is None:
            return None
        timestamp = ber._utc_timestamp(getattr(context, "decision_time", None))
        decision_time = None
        if timestamp is not None:
            decision_time = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "schema_version": self.schema_version,
            "team_id": self.team_id,
            "family_id": self.family_id,
            "candidate_id": self.candidate_id,
            "decision_time": decision_time,
            "score_name": self.score_name,
            "higher_score_role": self.higher_score_role,
            "construction_stage": "after-feature-eligibility-and-ranking-before-sleeves",
            "uses_labels": False,
            "scores": scores,
        }

    def serialize_score_record(self, context: Any, *, seed: int) -> bytes | None:
        record = self.score_record(context, seed=seed)
        if record is None:
            return None
        return json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")


def build_score_adapter() -> OrganizerScoreAdapter:
    """Return a fresh audit-only serializer, never an official A5 adapter."""

    return OrganizerScoreAdapter()
