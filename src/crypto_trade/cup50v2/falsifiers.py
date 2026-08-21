"""Organizer-run checks a candidate must survive before it is observed.

CUP-50 ran none of these, and its field was twelve unchanged organizer seeds, so nothing was ever
asked to prove it was a mechanism rather than an artifact. Each check below answers one specific way
a candidate can look real and not be.

They run on the research window, at nomination, and cost a team nothing: a preregistered control
that can never be promoted is not a trial, and charging for it is how prior editions made honest
self-examination unaffordable.
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
from collections.abc import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.replay import REBALANCE_COLUMN


@dataclasses.dataclass(frozen=True, slots=True)
class FalsifierOutcome:
    name: str
    passed: bool
    detail: str
    evidence: Mapping[str, object] = dataclasses.field(default_factory=dict)


def target_stream_digest(targets: pd.DataFrame) -> str:
    """A stable fingerprint of the decisions a candidate made."""
    payload = targets.to_json(orient="split", date_format="iso", double_precision=15)
    return hashlib.sha256(payload.encode()).hexdigest()


def sign_inversion(
    candidate_score: float, inverted_score: float, *, name: str = "sign-inversion"
) -> FalsifierOutcome:
    """An edge whose exact opposite scores as well is a construction artifact.

    If flipping every weight leaves the score intact, the number is coming from the shape of the
    book -- its turnover, its exposure profile, its cost footprint -- and not from the direction the
    mechanism claims to predict.
    """
    passed = inverted_score < candidate_score
    return FalsifierOutcome(
        name=name,
        passed=passed,
        detail=(
            f"inverted score {inverted_score:.6f} "
            f"{'is below' if passed else 'matches or beats'} candidate {candidate_score:.6f}"
        ),
        evidence={"candidate": candidate_score, "inverted": inverted_score},
    )


def invert_targets(targets: pd.DataFrame) -> pd.DataFrame:
    """Flip every weight and leave the rebalance schedule alone."""
    inverted = targets.copy()
    columns = [column for column in inverted.columns if column != REBALANCE_COLUMN]
    inverted[columns] = -inverted[columns]
    return inverted


def corruption_cut_points(
    decisions: Sequence[pd.Timestamp], *, key: bytes, count: int = 6
) -> tuple[pd.Timestamp, ...]:
    """Pick cut points from a key rather than a schedule, so they cannot be anticipated."""
    if len(decisions) < 3:
        return tuple(decisions[:1])
    usable = list(decisions[1:-1])
    digest = hmac.new(key, b"future-corruption", hashlib.sha256).digest()
    generator = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    picks = sorted(
        set(generator.choice(len(usable), size=min(count, len(usable)), replace=False).tolist())
    )
    return tuple(usable[index] for index in picks)


# Everything a strategy can read from a bar. Corrupting only `close` leaves a lane that trades
# volume share, taker flow or funding free to reach forward through a column the test never touches.
CORRUPTIBLE_COLUMNS = (
    "close",
    "high",
    "low",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)


def future_corruption(
    generate: Callable[[pd.DataFrame], pd.DataFrame],
    bars: pd.DataFrame,
    *,
    cut_points: Sequence[pd.Timestamp],
    corrupt_columns: Sequence[str] = CORRUPTIBLE_COLUMNS,
) -> FalsifierOutcome:
    """Corrupt everything after a cut point; the decisions up to it must not move.

    The evaluator already slices the context causally, so this is not a test of the evaluator. It
    tests the candidate's own state: a strategy that accumulates a panel, fits a model, or caches a
    clustering can reach forward through its own memory in a way the interface cannot prevent.
    """
    reference = generate(bars)
    columns = [column for column in corrupt_columns if column in bars.columns]
    responded = 0
    for cut in cut_points:
        corrupted = bars.copy()
        closes = pd.DatetimeIndex(pd.to_datetime(corrupted["close_time"], utc=True))
        future = closes >= pd.Timestamp(cut)
        for column in columns:
            # Widen first: an integer column such as trade_count cannot take a float multiplier in
            # place, and a corruption that raises is a corruption that never happened.
            corrupted[column] = corrupted[column].astype(float)
            corrupted.loc[future, column] = corrupted.loc[future, column] * 7.5 + 1.0
        observed = generate(corrupted)
        index = pd.DatetimeIndex(observed.index)
        before, after = index < pd.Timestamp(cut), index >= pd.Timestamp(cut)
        expected = target_stream_digest(reference.loc[before])
        if expected != target_stream_digest(observed.loc[before]):
            return FalsifierOutcome(
                name="future-corruption",
                passed=False,
                detail=f"decisions before {pd.Timestamp(cut).isoformat()} changed when the "
                "future was corrupted",
                evidence={"cut_point": pd.Timestamp(cut).isoformat(), "columns": columns},
            )
        # Positive control: the suffix must move. A constant book, or one that ignores every
        # corrupted column, passes the prefix test trivially and the evidence cannot tell the
        # difference between a causal candidate and an inert one.
        if target_stream_digest(reference.loc[after]) != target_stream_digest(observed.loc[after]):
            responded += 1
    return FalsifierOutcome(
        name="future-corruption",
        passed=True,
        detail=(
            f"{len(cut_points)} cut points left every earlier decision unchanged; "
            f"{responded} of them changed the decisions after the cut"
        ),
        evidence={
            "cut_points": [pd.Timestamp(cut).isoformat() for cut in cut_points],
            "corrupted_columns": columns,
            "cut_points_with_a_responsive_suffix": responded,
            "positive_control": "passed" if responded else "VACUOUS: no suffix responded",
        },
    )


def determinism(
    *streams: pd.DataFrame, hash_seeds: Sequence[int] | None = None
) -> FalsifierOutcome:
    """Independent runs of the same source and seed must agree bit for bit.

    Two runs inside one process share a hash seed, so the defect this exists to catch -- a float sum
    accumulated over set iteration, whose order depends on PYTHONHASHSEED -- survives it untouched.
    A lane found exactly that bug in an organizer seed. Pass streams generated under different hash
    seeds and name them.
    """
    digests = [target_stream_digest(stream) for stream in streams]
    agree = len(set(digests)) == 1
    return FalsifierOutcome(
        name="determinism",
        passed=agree and len(digests) >= 2,
        detail=(
            f"{len(digests)} independent runs agree"
            if agree
            else f"independent runs diverged across {len(set(digests))} distinct streams"
        ),
        evidence={
            "digests": digests,
            "hash_seeds": list(hash_seeds) if hash_seeds else "not varied",
        },
    )


def regime_spell_placebo(targets: pd.DataFrame, *, key: bytes, rounds: int = 32) -> pd.DataFrame:
    """Shuffle whole runs of the target stream, preserving each spell's length.

    A symbol permutation is a no-op on a book that is uniform across names, which is most
    directional lanes; CUP-20 found that its placebo had no teeth for exactly that reason. Shuffling
    *spells* keeps the book's holding periods, turnover and exposure profile intact and destroys
    only the alignment between the book and the market, which is the thing under test.
    """
    if targets.empty:
        return targets.copy()
    digest = hmac.new(key, b"regime-spell-placebo", hashlib.sha256).digest()
    generator = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    columns = [column for column in targets.columns if column != REBALANCE_COLUMN]
    values = targets[columns].to_numpy(dtype=float)

    spells: list[tuple[int, int]] = []
    start = 0
    for position in range(1, len(values) + 1):
        if position == len(values) or not np.array_equal(values[position], values[start]):
            spells.append((start, position))
            start = position
    order = generator.permutation(len(spells))

    rebuilt = np.empty_like(values)
    cursor = 0
    for index in order:
        begin, end = spells[index]
        block = values[begin:end]
        rebuilt[cursor : cursor + len(block)] = block
        cursor += len(block)
    placebo = targets.copy()
    placebo[columns] = rebuilt
    return placebo
