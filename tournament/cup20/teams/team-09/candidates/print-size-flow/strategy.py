"""Team 09 -- taker-flow / price-volume pressure.

WHAT THIS TRADES
----------------
A dollar-neutral cross-sectional book over the point-in-time top-20 universe, driven by the
structure of aggressive (taker) order flow rather than by its level.

Each bar in this snapshot reports ``taker_buy_quote_volume`` beside ``quote_volume`` and
``trade_count``, so three things are directly observable per symbol per 8h bar:

  * the signed taker imbalance   ``imb = (2 * taker_buy_quote - quote) / quote``  -- who paid the
    spread, in USDT, net;
  * the average print size       ``ats = quote_volume / trade_count``             -- whether that
    USDT arrived in many small trades or a few large ones;
  * the price move it accompanied.

The naive reading of this lane -- buy the names with the highest taker-buy ratio -- is measured
here as the transparent baseline and it is close to worthless on this window: same universe, same
book shape, same controls, it delivers a 2x-cost Sharpe near 0.5 with a worst fold near -1.3.

What carries this book is the CONDITIONING, and it is two-sided:

  1. ``IMBSML`` -- the taker imbalance measured ONLY over the bars whose average print was below
     that symbol's own recent norm. Buy pressure that arrives as many small prints is distributed
     across many participants; buy pressure that arrives as a few large prints is one participant,
     and one participant is usually an execution algo working a block or a liquidation being
     unwound. The first is information, the second is a transient. Restricting the imbalance to
     the granular bars more than doubles its stand-alone score.

  2. ``COVATS`` -- the USDT-weighted covariance, over the same window, between a bar's imbalance
     and that bar's print-size shock. It is positive when the unusually-large-print bars leaned
     the same way as the flow overall, i.e. when the block prints CONFIRM the granular pressure
     rather than fading it.

Neither is sufficient. Together they say: aggressive buying is informative when it is broad-based
AND size-confirmed. Substituting the all-bar imbalance for ``IMBSML`` halves the score;
substituting the large-print imbalance halves it too; removing ``COVATS`` halves it again; and
replacing the print-size conditioning with a plain equal-bar weighting -- which removes the
big-bar dominance without using print size at all -- recovers less than half the gap. The
mechanism is print size, not de-weighting.

WHAT IS DELIBERATELY REMOVED
----------------------------
The score is residualised cross-sectionally, every boundary, against three controls:

  * the contemporaneous price move over the same window -- so this is not price momentum;
  * the symbol's own average print size over the norm window, and
  * the symbol's own quote volume over the norm window -- jointly the size / activity class.

The two level controls matter: without them a large part of the raw flow signal is a
big-coin-beats-small-coin tilt that this window happens to pay, and that is not taker flow. The
residualisation is a same-boundary cross-sectional regression, so it introduces no window and no
look-ahead.

BOOK SHAPE
----------
``HOLD_BARS`` overlapping sleeves, one opened at every boundary and each held ``HOLD_BARS``
boundaries: long the top ``SLEEVE_NAMES`` residual scores, short the bottom ``SLEEVE_NAMES``,
equal weight inside each sleeve, dollar neutral. This is the average over every phase offset of a
cadence-``HOLD_BARS`` book rather than one arbitrary choice of phase, which matters because a
single-phase cadence-42 version of this same signal spanned 2x Sharpe -0.00 to +1.36 across its 42
offsets. The tranche book is the mean of that distribution and cannot be lucky in phase.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

# ---------------------------------------------------------------- declared parameters
# Every one of these is a neighbourhood coordinate: module level, one plain numeric literal on one
# line, named identically to the coordinate, and equal to the nominee's declared value.
FORMATION_BARS = 81
"""Bars of taker flow accumulated into the score (81 x 8h = 27 days)."""

NORM_BARS = 126
"""Bars forming each symbol's own print-size norm and its size/liquidity controls (42 days).

Deliberately longer than FORMATION_BARS: a print-size SHOCK is only a shock against a slower
baseline, and when the two windows coincide the measure degenerates toward a within-window
covariance whose sign is dominated by the window edge."""

HOLD_BARS = 72
"""Boundaries each sleeve is held; also the number of overlapping sleeves (72 x 8h = 24 days)."""

SLEEVE_NAMES = 4
"""Names per side in each sleeve -- one fifth of a 20-name universe per side. Charter 14.9
records that a diversified short sleeve on this window is gross-negative and that reaching
gross-positive requires narrowing to roughly a fifth of the names; this is that width."""

# ---------------------------------------------------------------- fixed constants
_SHOCK_CLIP = 3.0
"""Print-size shocks are clipped to +/- 3 log units before weighting, so one degenerate bar (a
near-empty bar with two prints) cannot dominate a 90-bar covariance."""

# There is deliberately NO minimum-count guard on the below-norm-print subset. An earlier draft
# required FORMATION_BARS / 6 qualifying bars, which left IMBSML undefined on about 9% of eligible
# symbol-boundaries -- concentrated in exactly the print-size regime shifts this measure is about --
# and handed those cases to whatever the missing-component policy happened to be. That policy then
# accounted for roughly thirty points of the offline ranking score, which is a rule doing the work
# of a mechanism. Removing the guard makes the measure defined almost everywhere, makes the score
# nearly indifferent to the missing-component policy, and improves the book. See the certificate.


def _ranks(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank mapped to [-1, 1]; ties broken by position, as offline."""
    n = values.size
    if n < 2:
        return np.zeros(n)
    order = np.argsort(np.argsort(values, kind="stable"), kind="stable")
    return 2.0 * order / (n - 1) - 1.0


def _residualise(y: np.ndarray, controls: list[np.ndarray]) -> np.ndarray:
    """Same-boundary cross-sectional OLS residual of ``y`` on ``controls`` (intercept included)."""
    design = np.column_stack([np.ones(y.size), *controls])
    if y.size <= design.shape[1] + 2:
        return y - y.mean()
    try:
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    except np.linalg.LinAlgError:
        return y - y.mean()
    return y - design @ beta


class PrintSizeFlow:
    """Cross-sectional taker-flow book conditioned on print size."""

    def __init__(self) -> None:
        self._sleeves: deque[dict[str, float]] = deque(maxlen=HOLD_BARS)
        self._last: dict[str, float] = {}

    # -------------------------------------------------------- per-symbol measures
    def _measures(self, frame) -> tuple[float, float, float, float, float] | None:
        """``(COVATS, IMBSML, window return, print-size level, quote-volume level)``.

        Every value is formed from the rows the context supplied, which end at the bar closing at
        the decision time. Nothing later is reachable.
        """
        need = FORMATION_BARS + NORM_BARS
        if len(frame) < need + 1:
            return None
        tail = frame.iloc[-(need + 1) :]
        quote = tail["quote_volume"].to_numpy(dtype=float)
        taker = tail["taker_buy_quote_volume"].to_numpy(dtype=float)
        trades = tail["trade_count"].to_numpy(dtype=float)
        close = tail["close"].to_numpy(dtype=float)

        with np.errstate(invalid="ignore", divide="ignore"):
            imbalance = np.where(quote > 0.0, (2.0 * taker - quote) / quote, np.nan)
            print_size = np.where(
                (trades > 0.0) & (quote > 0.0), np.log(quote / np.maximum(trades, 1.0)), np.nan
            )
            log_quote = np.where(quote > 0.0, np.log(quote), np.nan)

        # Rolling NORM_BARS mean of log print size, evaluated on the rows STRICTLY BEFORE each
        # bar, for the last FORMATION_BARS bars. Bars carrying no print size are excluded from
        # both the sum and the count rather than treated as zero.
        finite = np.isfinite(print_size)
        filled = np.where(finite, print_size, 0.0)
        csum = np.concatenate([[0.0], np.cumsum(filled)])
        ccnt = np.concatenate([[0.0], np.cumsum(finite.astype(float))])
        n = print_size.size
        idx = np.arange(n - FORMATION_BARS, n)  # the bars the window accumulates over
        lo = idx - NORM_BARS
        if lo[0] < 0:
            return None
        window_sum = csum[idx] - csum[lo]
        window_cnt = ccnt[idx] - ccnt[lo]
        with np.errstate(invalid="ignore", divide="ignore"):
            norm = np.where(window_cnt > 0.0, window_sum / window_cnt, np.nan)
        shock = np.clip(print_size[idx] - norm, -_SHOCK_CLIP, _SHOCK_CLIP)

        bar_imb = imbalance[idx]
        bar_quote = quote[idx]
        usable = np.isfinite(shock) & np.isfinite(bar_imb) & np.isfinite(bar_quote)
        if not usable.any():
            return None

        # COVATS -- USDT-weighted covariance of imbalance with the print-size shock.
        denom = bar_quote[usable].sum()
        if denom <= 0.0:
            return None
        covats = float((bar_imb[usable] * shock[usable] * bar_quote[usable]).sum() / denom)

        # IMBSML -- imbalance over the below-norm-print bars only, USDT weighted within them.
        small = usable & (shock <= 0.0)
        if not small.any():
            return None
        small_quote = bar_quote[small].sum()
        if small_quote <= 0.0:
            return None
        imbsml = float((bar_imb[small] * bar_quote[small]).sum() / small_quote)

        # Controls.
        first, last = close[-FORMATION_BARS - 1], close[-1]
        if not (np.isfinite(first) and np.isfinite(last) and first > 0.0 and last > 0.0):
            return None
        window_return = float(np.log(last / first))
        size_level = float(np.nanmean(print_size[-NORM_BARS:]))
        liquidity_level = float(np.nanmean(log_quote[-NORM_BARS:]))
        if not (np.isfinite(size_level) and np.isfinite(liquidity_level)):
            return None
        return covats, imbsml, window_return, size_level, liquidity_level

    # -------------------------------------------------------- protocol
    def target_weights(self, context: DecisionContext, *, seed: int):
        eligible = sorted(context.eligible_symbols)
        rows: list[tuple[str, tuple[float, float, float, float, float]]] = []
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            measured = self._measures(frame)
            if measured is not None and all(np.isfinite(measured)):
                rows.append((symbol, measured))

        if len(rows) >= 2 * SLEEVE_NAMES + 2:
            names = [name for name, _ in rows]
            block = np.array([values for _, values in rows], dtype=float)
            raw = _ranks(block[:, 0]) + _ranks(block[:, 1])
            residual = _residualise(
                raw, [_ranks(block[:, 2]), _ranks(block[:, 3]), _ranks(block[:, 4])]
            )
            order = np.argsort(np.argsort(residual, kind="stable"), kind="stable")
            sleeve: dict[str, float] = {}
            size = 0.5 / SLEEVE_NAMES
            for position, name in zip(order, names, strict=True):
                if position >= len(names) - SLEEVE_NAMES:
                    sleeve[name] = size
                elif position < SLEEVE_NAMES:
                    sleeve[name] = -size
            self._last = sleeve
        # Too few scored names to form both sleeves: repeat the previous sleeve rather than
        # opening an arbitrary one. The book still ages out through the tranche average.
        self._sleeves.append(dict(self._last))

        pooled: dict[str, float] = {}
        for sleeve in self._sleeves:
            for name, weight in sleeve.items():
                pooled[name] = pooled.get(name, 0.0) + weight
        count = len(self._sleeves)
        allowed = set(eligible)
        return {
            name: weight / count
            for name, weight in pooled.items()
            if name in allowed and abs(weight) > 0.0
        }


def build_strategy() -> TargetStrategy:
    return PrintSizeFlow()
