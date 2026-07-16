"""Organizer-owned score capture for Team01's registered RDF family.

The adapter deliberately does not reproduce the signal formula.  It observes the exact
``scored`` sequence passed by the historical strategy to ``_select_signed_tails`` and delegates
to that original function without changing its arguments or result.
"""

from __future__ import annotations

import dataclasses
import math
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

ADAPTER_ID = "team01-rdf-select-signed-tails-v1"
FAMILY_ID = "t01-residual-drift-funding-v1"

_T = TypeVar("_T")


@dataclasses.dataclass(frozen=True)
class CapturedScore:
    """One exact pre-construction score observed inside the historical strategy."""

    symbol: str
    score: float


@dataclasses.dataclass(frozen=True)
class AdaptedDecision:
    """Historical target result plus an optional scheduled score cross-section."""

    weights: Mapping[str, float] | None
    scores: tuple[CapturedScore, ...] | None


class Team01RdfScoreAdapter:
    """Capture the RDF score at its last boundary before portfolio construction."""

    adapter_id = ADAPTER_ID
    family_id = FAMILY_ID

    def __init__(self, strategy: Any) -> None:
        strategy_type = type(strategy)
        module = sys.modules.get(strategy_type.__module__)
        if module is None:
            raise TypeError("historical strategy module is not loaded")
        if strategy_type.__name__ != "ResidualDriftFundingStrategy":
            raise TypeError("Team01 RDF adapter received an unexpected strategy class")
        selector = getattr(module, "_select_signed_tails", None)
        if not callable(selector):
            raise TypeError("historical Team01 RDF module lacks _select_signed_tails")
        if not callable(getattr(module, "_combine_scores", None)):
            raise TypeError("historical Team01 RDF module lacks _combine_scores")
        if not hasattr(strategy, "_parameters"):
            raise TypeError("historical Team01 RDF strategy lacks frozen parameters")
        reference = getattr(module, "REFERENCE_PARAMETERS", None)
        if reference is None or strategy._parameters != reference:
            raise ValueError("historical Team01 RDF strategy is not its frozen reference cell")
        self._module = module
        self._selector: Callable[..., Any] = selector

    @staticmethod
    def _normalise_capture(
        raw: Any,
        *,
        eligible_symbols: frozenset[str],
    ) -> tuple[CapturedScore, ...]:
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise TypeError("RDF selector scored input must be a sequence")
        result: list[CapturedScore] = []
        observed: set[str] = set()
        for item in raw:
            if (
                not isinstance(item, Sequence)
                or isinstance(item, (str, bytes))
                or len(item) != 3
            ):
                raise TypeError("RDF selector scored rows must be (symbol, score, volatility)")
            symbol, raw_score, raw_volatility = item
            if (
                not isinstance(symbol, str)
                or not symbol
                or symbol not in eligible_symbols
                or symbol == "BTCUSDT"
                or symbol in observed
            ):
                raise ValueError("RDF selector score symbols are invalid or duplicated")
            if isinstance(raw_score, bool) or isinstance(raw_volatility, bool):
                raise TypeError("RDF selector score and volatility must be numeric")
            try:
                score = float(raw_score)
                volatility = float(raw_volatility)
            except (TypeError, ValueError) as exc:
                raise TypeError("RDF selector score and volatility must be numeric") from exc
            if not math.isfinite(score) or not math.isfinite(volatility) or volatility <= 0.0:
                raise ValueError("RDF selector score rows must be finite with positive volatility")
            observed.add(symbol)
            result.append(CapturedScore(symbol=symbol, score=score))
        if not result:
            raise ValueError("RDF selector cannot receive an empty score cross-section")
        return tuple(result)

    def evaluate(
        self,
        target_call: Callable[[], _T],
        *,
        eligible_symbols: Sequence[str],
    ) -> AdaptedDecision:
        """Call the original target method once and capture its exact selector input."""

        eligible = tuple(eligible_symbols)
        if any(not isinstance(symbol, str) or not symbol for symbol in eligible):
            raise TypeError("eligible symbols must be nonempty strings")
        if len(eligible) != len(set(eligible)):
            raise ValueError("eligible symbols cannot contain duplicates")
        captures: list[tuple[CapturedScore, ...]] = []
        original = self._selector

        def capture_and_delegate(scored: Any, *args: Any, **kwargs: Any) -> Any:
            captures.append(
                self._normalise_capture(scored, eligible_symbols=frozenset(eligible))
            )
            if len(captures) > 1:
                raise ValueError("RDF strategy invoked its construction selector more than once")
            return original(scored, *args, **kwargs)

        if getattr(self._module, "_select_signed_tails", None) is not original:
            raise ValueError("historical RDF selector changed before score capture")
        setattr(self._module, "_select_signed_tails", capture_and_delegate)
        try:
            raw_weights = target_call()
            if getattr(self._module, "_select_signed_tails", None) is not capture_and_delegate:
                raise ValueError("historical strategy replaced the organizer score capture")
        finally:
            setattr(self._module, "_select_signed_tails", original)

        if raw_weights is not None and not isinstance(raw_weights, Mapping):
            raise TypeError("historical strategy returned a non-mapping target")
        if raw_weights and len(captures) != 1:
            raise ValueError("nonempty RDF targets were constructed without an observed score")
        return AdaptedDecision(
            weights=raw_weights,
            scores=captures[0] if captures else None,
        )


def build_adapter(adapter_id: str, strategy: Any) -> Team01RdfScoreAdapter:
    """Construct the only reviewed score adapter supported by amendment 0001."""

    if adapter_id != ADAPTER_ID:
        raise ValueError("unsupported organizer score adapter")
    return Team01RdfScoreAdapter(strategy)
