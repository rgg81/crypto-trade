"""Generic, organizer-owned capture for the Amendment 0005 score boundary."""

from __future__ import annotations

import dataclasses
import math
import struct
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from crypto_trade.tournament import score_adapter_protocol_v5 as protocol


class ScoreBoundaryError(ValueError):
    """The candidate did not honor its preregistered score-boundary contract."""


@dataclasses.dataclass(frozen=True, slots=True)
class BoundaryResult:
    weights: Mapping[str, float] | None
    scores: Mapping[str, float] | None


def _target_globals(strategy: Any) -> dict[str, Any]:
    target = getattr(strategy, "target_weights", None)
    function = getattr(target, "__func__", target)
    namespace = getattr(function, "__globals__", None)
    if not callable(target) or type(namespace) is not dict:
        raise ScoreBoundaryError(
            "strategy.target_weights must have one inspectable direct module namespace"
        )
    if namespace.get("score_boundary") is not protocol.score_boundary:
        raise ScoreBoundaryError(
            "strategy.py must directly import the organizer score_boundary identity"
        )
    return namespace


def _number_token(value: object) -> tuple[type[object], bytes]:
    if type(value) not in {int, float}:
        raise ScoreBoundaryError(
            "score_boundary requires built-in finite non-Boolean int/float values"
        )
    converted = float(value)
    if not math.isfinite(converted):
        raise ScoreBoundaryError("score_boundary values must be finite")
    return type(value), struct.pack("!d", converted)


def _snapshot_scores(value: object) -> tuple[dict[str, float], tuple[tuple[str, type[object], bytes], ...]]:
    if type(value) is not dict:
        raise ScoreBoundaryError("score_boundary requires an exact built-in dict")
    normalized: dict[str, float] = {}
    tokens: list[tuple[str, type[object], bytes]] = []
    for symbol, raw_score in value.items():
        if type(symbol) is not str or not symbol:
            raise ScoreBoundaryError("score_boundary keys must be nonempty built-in strings")
        value_type, token = _number_token(raw_score)
        normalized[symbol] = float(raw_score)
        tokens.append((symbol, value_type, token))
    return normalized, tuple(tokens)


def _assert_unmodified(
    captured_object: dict[str, float],
    expected: tuple[tuple[str, type[object], bytes], ...],
) -> None:
    _normalized, observed = _snapshot_scores(captured_object)
    if observed != expected:
        raise ScoreBoundaryError("candidate mutated the score dictionary after score_boundary")


class GenericScoreBoundaryAdapter:
    """Patch one direct binding for one decision, capture once, and restore it exactly."""

    def __init__(self, strategy: Any) -> None:
        self._namespace = _target_globals(strategy)
        self._active = False

    def evaluate(
        self,
        delegate: Callable[[], Mapping[str, float] | None],
        *,
        scheduled: bool,
        eligible_symbols: Sequence[str],
    ) -> BoundaryResult:
        if not callable(delegate):
            raise TypeError("score-boundary delegate must be callable")
        if self._active:
            raise ScoreBoundaryError("score-boundary capture cannot be re-entered")
        if len(eligible_symbols) != len(set(eligible_symbols)) or any(
            type(symbol) is not str for symbol in eligible_symbols
        ):
            raise ScoreBoundaryError("eligible symbols must be unique built-in strings")
        if self._namespace.get("score_boundary") is not protocol.score_boundary:
            raise ScoreBoundaryError("strategy score_boundary binding changed before decision")

        calls = 0
        captured: dict[str, float] | None = None
        captured_object: dict[str, float] | None = None
        captured_tokens: tuple[tuple[str, type[object], bytes], ...] | None = None

        def capture(value: dict[str, float]) -> dict[str, float]:
            nonlocal calls, captured, captured_object, captured_tokens
            calls += 1
            if calls > 1:
                raise ScoreBoundaryError("score_boundary may be called at most once per decision")
            normalized, tokens = _snapshot_scores(value)
            unknown = set(normalized) - set(eligible_symbols)
            if unknown:
                raise ScoreBoundaryError(
                    "score_boundary contains symbols outside current eligibility"
                )
            captured = normalized
            captured_object = value
            captured_tokens = tokens
            return value

        self._active = True
        weights: Mapping[str, float] | None = None
        failure: BaseException | None = None
        try:
            self._namespace["score_boundary"] = capture
            try:
                weights = delegate()
            except BaseException as exc:
                failure = exc
        finally:
            observed = self._namespace.get("score_boundary")
            self._namespace["score_boundary"] = protocol.score_boundary
            self._active = False
            if observed is not capture:
                raise ScoreBoundaryError(
                    "strategy changed the organizer score_boundary binding during decision"
                ) from failure
            if self._namespace.get("score_boundary") is not protocol.score_boundary:
                raise ScoreBoundaryError("strategy score_boundary binding could not be restored")
        if failure is not None:
            raise failure.with_traceback(failure.__traceback__)
        if scheduled and calls != 1:
            raise ScoreBoundaryError(
                "scheduled decision did not call score_boundary exactly once"
            )
        if not scheduled and calls != 0:
            raise ScoreBoundaryError("score_boundary was called outside the manifest schedule")
        if captured_object is not None and captured_tokens is not None:
            _assert_unmodified(captured_object, captured_tokens)
        if scheduled and weights and not captured:
            raise ScoreBoundaryError(
                "nonempty scheduled targets require a nonempty score capture"
            )
        return BoundaryResult(weights=weights, scores=captured if scheduled else None)


def build_adapter(adapter_id: str, strategy: Any) -> GenericScoreBoundaryAdapter:
    if adapter_id != protocol.ADAPTER_ID:
        raise ScoreBoundaryError(f"unsupported score adapter: {adapter_id!r}")
    return GenericScoreBoundaryAdapter(strategy)
