"""team-02 / channel-position-ls -- cross-sectional position inside a coin's own quarter range.

Mechanism. A perpetual's trailing extreme is a level, and levels are where resting liquidity, stop
orders and liquidation triggers cluster. Where a coin currently sits between its own trailing low
and its own trailing high is therefore a statement about how completely it has already consumed
the resting supply (or bid) inside that range: a coin pinned at the top of its quarter range has
repeatedly cleared every seller willing to sell there, and a coin pinned at the bottom has
repeatedly failed to hold its bids and has printed a fresh liquidation trigger each time. That is
a statement about LOCATION IN A RANGE and deliberately not about rate of change -- the range
normalisation discards how violent the move was and keeps only how far through its own band the
coin has travelled, so two coins that both sit at a new quarter high score identically however
differently they got there. Measured cross-sectionally on the in-sample window, the rank
correlation between this score and the same-window return is 0.67, and the book below beats the
same-window-return book built the identical way by roughly half a Sharpe point.

The book. At every rebalance boundary the eligible point-in-time universe is ranked by

    u = (close - min(low, FORMATION_BARS)) / (max(high, FORMATION_BARS) - min(low, FORMATION_BARS))

and the SLEEVE_SIZE highest are held long, the SLEEVE_SIZE lowest short, equally weighted, with
the two sleeves at equal gross so the book carries no deliberate market exposure. Between
rebalance boundaries the strategy returns ``None``, which holds quantities and generates no
turnover: on an 8h grid a book that retargets at every boundary spends its whole turnover budget
rebalancing against price drift alone.

Two range-structure CONTROLS were hypothesised as separators of a break that carries from one that
snaps back, implemented here behind constants, and both are FROZEN OFF because both made the book
worse (see RESEARCH-CERTIFICATE.md):

  * CONTROL_FRESH_BARS -- promote coins that printed a new FORMATION_BARS extreme within the last
    N bars, so the sleeve prefers a level breach that is actually fresh over one that is merely
    near an extreme;
  * CONTROL_COMPRESSION -- promote coins whose channel is wide relative to current true range,
    i.e. coins that have gone quiet inside a large band and are therefore coiled.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

# --- declared neighbourhood coordinates -------------------------------------------------------
# Module-level, single-valued, plain numeric literals, named exactly as in neighbourhood.json.

FORMATION_BARS = 252
"""Length of the trailing Donchian channel in 8h bars. 252 bars = 84 days = one calendar quarter:
long enough for a level to have accumulated resting orders, recent enough that the participants
who placed them are still positioned."""

REBALANCE_BARS = 21
"""8h bars between explicit rebalances. 21 bars = exactly 7 days, matching the weekly Monday 00:00
UTC universe reconstitution, and slow enough that annualised one-way turnover stays well inside
the 25x cap."""

PHASE_OFFSET = 12
"""Residue of the absolute 8h bar index at which the weekly rebalance fires. 12 is the residue of
Monday 00:00 UTC modulo 21, so the book retargets on the reconstitution boundary itself and always
trades the universe it has just been given. Chosen for that alignment, not for its backtest."""

# --- fixed structural choices ------------------------------------------------------------------

SLEEVE_SIZE = 3
"""Names per side. Six equally weighted names is 1/6 = 0.1667 of gross each, under the 0.20
per-symbol cap, so the book is never reduced by the exposure caps and its executed weights are the
weights it asked for."""

CONTROL_FRESH_BARS = 0
"""Breach-freshness control. 0 disables it. When positive, a coin that printed a new
FORMATION_BARS high (low) within this many bars is promoted ahead of every non-breacher in the
long (short) ordering. FROZEN OFF: it cost about 0.07-0.20 of Sharpe at every setting tested."""

CONTROL_COMPRESSION = 0
"""Range-compression control. 0 disables it. When 1, coins in the compressed half of
(channel width) / (average true range) are promoted in both orderings. FROZEN OFF: it cut the
phase-averaged Sharpe from 1.52 to 0.64 and deepened the worst drawdown."""

_BAR_NANOSECONDS = 8 * 3600 * 10**9
_ATR_BARS = 42
_COMPRESSION_PROMOTION = 0.5
_FRESH_PROMOTION = 1.0


def _bar_index(timestamp: pd.Timestamp) -> int:
    """Absolute 8h bar ordinal, so PHASE_OFFSET means one fixed weekday-and-hour."""
    return int(pd.Timestamp(timestamp).value // _BAR_NANOSECONDS)


def _channel_features(frame: pd.DataFrame, formation_bars: int, fresh_bars: int,
                      want_compression: bool) -> tuple[float, bool, bool, float] | None:
    """(u, fresh_high, fresh_low, compression) from past-only rows, or None if not computable."""
    if len(frame) < formation_bars:
        return None
    high = frame["high"].to_numpy(dtype=float)
    low = frame["low"].to_numpy(dtype=float)
    close = frame["close"].to_numpy(dtype=float)
    window_high = high[-formation_bars:]
    window_low = low[-formation_bars:]
    channel_high = float(np.nanmax(window_high))
    channel_low = float(np.nanmin(window_low))
    last_close = float(close[-1])
    if not (np.isfinite(channel_high) and np.isfinite(channel_low) and np.isfinite(last_close)):
        return None
    width = channel_high - channel_low
    if width <= 0.0:
        return None
    position = min(1.0, max(0.0, (last_close - channel_low) / width))

    fresh_high = fresh_low = False
    if fresh_bars > 0 and len(frame) >= formation_bars + 1:
        span = min(fresh_bars, len(frame) - formation_bars)
        for offset in range(span):
            end = len(frame) - offset
            prior_high = float(np.nanmax(high[end - 1 - formation_bars : end - 1]))
            prior_low = float(np.nanmin(low[end - 1 - formation_bars : end - 1]))
            bar_close = float(close[end - 1])
            if np.isfinite(prior_high) and bar_close > prior_high:
                fresh_high = True
            if np.isfinite(prior_low) and bar_close < prior_low:
                fresh_low = True

    compression = 0.0
    if want_compression and len(frame) >= _ATR_BARS + 1:
        recent_high = high[-_ATR_BARS:]
        recent_low = low[-_ATR_BARS:]
        previous_close = close[-_ATR_BARS - 1 : -1]
        true_range = np.maximum(
            recent_high - recent_low,
            np.maximum(
                np.abs(recent_high - previous_close), np.abs(recent_low - previous_close)
            ),
        )
        average_true_range = float(np.nanmean(true_range))
        if np.isfinite(average_true_range) and average_true_range > 0.0:
            compression = width / (average_true_range * float(np.sqrt(formation_bars)))
    return position, fresh_high, fresh_low, compression


class ChannelPositionLongShort:
    """Long the SLEEVE_SIZE names highest in their own channel, short the SLEEVE_SIZE lowest."""

    def __init__(
        self,
        formation_bars: int = FORMATION_BARS,
        rebalance_bars: int = REBALANCE_BARS,
        phase_offset: int = PHASE_OFFSET,
        sleeve_size: int = SLEEVE_SIZE,
        control_fresh_bars: int = CONTROL_FRESH_BARS,
        control_compression: int = CONTROL_COMPRESSION,
    ) -> None:
        self.formation_bars = int(formation_bars)
        self.rebalance_bars = max(1, int(rebalance_bars))
        self.phase_offset = int(phase_offset)
        self.sleeve_size = max(1, int(sleeve_size))
        self.control_fresh_bars = max(0, int(control_fresh_bars))
        self.control_compression = int(control_compression) != 0

    def _is_rebalance(self, decision_time: pd.Timestamp) -> bool:
        return _bar_index(decision_time) % self.rebalance_bars == (
            self.phase_offset % self.rebalance_bars
        )

    def _orderings(
        self, context: DecisionContext
    ) -> tuple[list[tuple[float, str]], list[tuple[float, str]]] | None:
        rows: list[tuple[str, float, bool, bool, float]] = []
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or frame.empty:
                continue
            features = _channel_features(
                frame, self.formation_bars, self.control_fresh_bars, self.control_compression
            )
            if features is None:
                continue
            position, fresh_high, fresh_low, compression = features
            if not np.isfinite(position):
                continue
            rows.append((str(symbol), position, fresh_high, fresh_low, compression))
        if len(rows) < 2 * self.sleeve_size:
            return None

        compressed: set[str] = set()
        if self.control_compression:
            values = sorted(row[4] for row in rows)
            median = values[len(values) // 2]
            compressed = {row[0] for row in rows if row[4] >= median}

        long_scores: list[tuple[float, str]] = []
        short_scores: list[tuple[float, str]] = []
        for symbol, position, fresh_high, fresh_low, _ in rows:
            long_value = position
            short_value = 1.0 - position
            if self.control_fresh_bars > 0:
                long_value += _FRESH_PROMOTION * float(fresh_high)
                short_value += _FRESH_PROMOTION * float(fresh_low)
            if symbol in compressed:
                long_value += _COMPRESSION_PROMOTION
                short_value += _COMPRESSION_PROMOTION
            long_scores.append((long_value, symbol))
            short_scores.append((short_value, symbol))
        return long_scores, short_scores

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        if not self._is_rebalance(context.decision_time):
            return None
        orderings = self._orderings(context)
        if orderings is None:
            # Not enough coins with a fully formed channel to build both sleeves at equal gross.
            # Holding quantities is the honest answer; going flat would churn the book on a data
            # gap rather than on a signal.
            return None
        long_scores, short_scores = orderings
        # Descending by score, ties broken by symbol name, so the book is fully deterministic.
        longs: Sequence[tuple[float, str]] = sorted(
            long_scores, key=lambda item: (-item[0], item[1])
        )[: self.sleeve_size]
        chosen_long = {symbol for _, symbol in longs}
        shorts = [item for item in sorted(short_scores, key=lambda item: (-item[0], item[1]))
                  if item[1] not in chosen_long][: self.sleeve_size]
        if len(shorts) < self.sleeve_size:
            return None
        weight = 1.0 / (2.0 * self.sleeve_size)
        targets: dict[str, float] = {}
        for _, symbol in longs:
            targets[symbol] = weight
        for _, symbol in shorts:
            targets[symbol] = -weight
        return targets


def build_strategy() -> TargetStrategy:
    return ChannelPositionLongShort(
        formation_bars=FORMATION_BARS,
        rebalance_bars=REBALANCE_BARS,
        phase_offset=PHASE_OFFSET,
        sleeve_size=SLEEVE_SIZE,
        control_fresh_bars=CONTROL_FRESH_BARS,
        control_compression=CONTROL_COMPRESSION,
    )
