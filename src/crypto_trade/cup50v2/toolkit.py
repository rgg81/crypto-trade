"""Shared, organizer-owned primitives for lane sources.

Every lane needs the same handful of things: a causal view of the eligible cross-section, a
volatility estimate, a way to turn a signal into weights that are not dominated by whichever name
happens to be wildest, and a way to stop rebalancing a book into the ground.  Writing those twelve
times over produces twelve subtly different definitions, and then a lane's result partly measures
its plumbing.

Nothing here is a strategy.  It computes only from what ``DecisionContextV2`` exposes -- bars that
closed before the decision, funding settled before it, and the eligible symbol list -- so a lane
built on it inherits the interface's causality rather than having to re-establish it.  Teams may
copy any of it into their own source and change it; it is a floor, not a fence.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

BARS_PER_DAY = 3
BARS_PER_YEAR = 365 * BARS_PER_DAY


def bars_for_days(days: float) -> int:
    """Canonical 8h bars in a number of days."""
    return int(round(days * BARS_PER_DAY))


def is_daily_decision(context) -> bool:
    """True at the 00:00 UTC boundary.

    Deciding once a day rather than three times cuts turnover by construction, and the cost wall,
    not signal absence, is what kills most books here.
    """
    return pd.Timestamp(context.decision_time).hour == 0


def close_panel(context, *, symbols: Sequence[str] | None = None) -> pd.DataFrame:
    """Wide close prices for the eligible cross-section, oldest first."""
    names = list(symbols if symbols is not None else context.eligible_symbols)
    columns = {}
    for symbol in names:
        history = context.bars.get(symbol)
        if history is None or history.empty:
            continue
        frame = history.set_index("close_time")["close"]
        columns[symbol] = frame[~frame.index.duplicated(keep="last")]
    if not columns:
        return pd.DataFrame()
    return pd.DataFrame(columns).sort_index()


def column_panel(context, column: str, *, symbols: Sequence[str] | None = None) -> pd.DataFrame:
    """Wide view of any bar column the interface exposes."""
    names = list(symbols if symbols is not None else context.eligible_symbols)
    columns = {}
    for symbol in names:
        history = context.bars.get(symbol)
        if history is None or history.empty or column not in history:
            continue
        frame = history.set_index("close_time")[column]
        columns[symbol] = frame[~frame.index.duplicated(keep="last")]
    if not columns:
        return pd.DataFrame()
    return pd.DataFrame(columns).sort_index()


def trailing_return(panel: pd.DataFrame, bars: int, *, skip: int = 0) -> pd.Series:
    """Return over ``bars`` closing ``skip`` bars ago, per symbol."""
    if panel.empty or len(panel) <= bars + skip:
        return pd.Series(dtype=float)
    end = panel.iloc[-1 - skip]
    start = panel.iloc[-1 - skip - bars]
    return (end / start - 1.0).replace([np.inf, -np.inf], np.nan).dropna()


def bar_returns(panel: pd.DataFrame) -> pd.DataFrame:
    return panel.pct_change().replace([np.inf, -np.inf], np.nan)


def realised_sigma(panel: pd.DataFrame, bars: int = 90) -> pd.Series:
    """Annualised volatility of 8h log returns, per symbol."""
    if panel.empty or len(panel) < 3:
        return pd.Series(dtype=float)
    logs = np.log(panel).diff().replace([np.inf, -np.inf], np.nan)
    window = logs.tail(bars)
    counts = window.notna().sum()
    sigma = window.std(ddof=1) * math.sqrt(BARS_PER_YEAR)
    return sigma.where(counts >= max(3, bars // 4)).dropna()


def downside_sigma(panel: pd.DataFrame, bars: int = 90) -> pd.Series:
    """Annualised semi-deviation: only losses count."""
    if panel.empty:
        return pd.Series(dtype=float)
    logs = np.log(panel).diff().replace([np.inf, -np.inf], np.nan).tail(bars)
    losses = logs.where(logs < 0.0)
    counts = losses.notna().sum()
    sigma = losses.std(ddof=1) * math.sqrt(BARS_PER_YEAR)
    return sigma.where(counts >= 3).dropna()


def cross_sectional_z(values: pd.Series) -> pd.Series:
    """Z-score across the cross-section; a degenerate section scores zero, not infinity."""
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return pd.Series(dtype=float)
    spread = float(clean.std(ddof=1))
    if not math.isfinite(spread) or spread <= 0.0:
        return pd.Series(0.0, index=clean.index)
    return (clean - float(clean.mean())) / spread


def cross_sectional_rank(values: pd.Series) -> pd.Series:
    """Rank across the cross-section, mapped to [-0.5, 0.5]. Scale-free and outlier-proof."""
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return pd.Series(dtype=float)
    if len(clean) == 1:
        return pd.Series(0.0, index=clean.index)
    return clean.rank(method="average").sub(0.5).div(len(clean)).sub(0.5)


def vol_parity(
    signals: Mapping[str, float],
    sigma: pd.Series,
    *,
    gross: float = 1.0,
    symbol_cap: float = 0.15,
    neutral: bool = True,
) -> dict[str, float]:
    """Turn signed signals into weights that risk the same amount per name.

    Sizing proportional to the raw signal hands the book to whichever name is most volatile, which
    is a bet on volatility rather than on the mechanism.  With ``neutral`` set and both sides
    present, each side is normalised separately, so the book is balanced by risk rather than by
    however many names happened to fire.
    """
    if not signals or sigma.empty:
        return {}
    raw: dict[str, float] = {}
    for symbol, signal in signals.items():
        value = float(signal)
        scale = float(sigma.get(symbol, float("nan")))
        if not math.isfinite(value) or value == 0.0 or not math.isfinite(scale) or scale <= 0.0:
            continue
        raw[symbol] = value / scale
    if not raw:
        return {}
    longs = {symbol: value for symbol, value in raw.items() if value > 0.0}
    shorts = {symbol: value for symbol, value in raw.items() if value < 0.0}
    weights: dict[str, float] = {}
    if neutral and longs and shorts:
        for side, budget in ((longs, gross / 2.0), (shorts, gross / 2.0)):
            total = sum(abs(value) for value in side.values())
            weights.update({symbol: value / total * budget for symbol, value in side.items()})
    else:
        total = sum(abs(value) for value in raw.values())
        weights = {symbol: value / total * gross for symbol, value in raw.items()}
    return _apply_symbol_cap(weights, symbol_cap=symbol_cap, gross=gross)


def _fill_side(
    values: Mapping[str, float], *, budget: float, symbol_cap: float
) -> dict[str, float]:
    """Distribute a budget in proportion to risk, capping names and refilling the remainder.

    Clipping alone silently shrinks the book: a single name over the cap would take its ceiling and
    the freed budget would go unused, so the strategy would run smaller than it asked to for a
    reason it never expressed. The freed budget is redistributed among the names still below the
    cap until either the budget is spent or every name is at its ceiling.
    """
    remaining = dict(values)
    fixed: dict[str, float] = {}
    available = budget
    sign = 1.0 if budget >= 0 else -1.0
    while remaining and available * sign > 1e-15:
        total = sum(abs(value) for value in remaining.values())
        if total <= 0.0:
            break
        scaled = {
            symbol: abs(value) / total * abs(available) for symbol, value in remaining.items()
        }
        capped = {symbol: value for symbol, value in scaled.items() if value > symbol_cap + 1e-15}
        if not capped:
            fixed.update({symbol: sign * value for symbol, value in scaled.items()})
            available = 0.0
            break
        for symbol in capped:
            fixed[symbol] = sign * symbol_cap
            del remaining[symbol]
        available = abs(available) - symbol_cap * len(capped)
        available *= sign
    return fixed


def _apply_symbol_cap(
    weights: Mapping[str, float], *, symbol_cap: float, gross: float
) -> dict[str, float]:
    """Cap each name, refilling within each side so the book keeps the budget it asked for."""
    longs = {symbol: value for symbol, value in weights.items() if float(value) > 0.0}
    shorts = {symbol: value for symbol, value in weights.items() if float(value) < 0.0}
    result: dict[str, float] = {}
    for side in (longs, shorts):
        if not side:
            continue
        budget = sum(float(value) for value in side.values())
        result.update(_fill_side(side, budget=budget, symbol_cap=symbol_cap))
    total = sum(abs(value) for value in result.values())
    if total > gross > 0.0:
        result = {symbol: value / total * gross for symbol, value in result.items()}
    return {
        symbol: value for symbol, value in result.items() if math.isfinite(value) and value != 0.0
    }


def top_by_absolute(values: pd.Series, count: int) -> pd.Series:
    """The ``count`` strongest signals by magnitude, ties broken by symbol for determinism."""
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return clean
    ordered = clean.reindex(
        sorted(clean.index, key=lambda symbol: (-abs(float(clean[symbol])), str(symbol)))
    )
    return ordered.head(max(0, int(count)))


def long_short_extremes(values: pd.Series, count: int) -> dict[str, float]:
    """Long the ``count`` highest and short the ``count`` lowest, as +1/-1 signals."""
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 2 * count or count < 1:
        return {}
    ordered = sorted(clean.index, key=lambda symbol: (float(clean[symbol]), str(symbol)))
    signals = {str(symbol): -1.0 for symbol in ordered[:count]}
    signals.update({str(symbol): 1.0 for symbol in ordered[-count:]})
    return signals


def equal_weight_index(panel: pd.DataFrame) -> pd.Series:
    """8h returns of an equal-weight book over the panel's columns."""
    if panel.empty:
        return pd.Series(dtype=float)
    return bar_returns(panel).mean(axis=1, skipna=True).dropna()


def beta_to(panel: pd.DataFrame, benchmark: pd.Series, bars: int) -> pd.Series:
    """Per-symbol beta against a benchmark return series over the trailing window."""
    if panel.empty or benchmark.empty:
        return pd.Series(dtype=float)
    returns = bar_returns(panel).tail(bars)
    reference = benchmark.reindex(returns.index)
    variance = float(reference.var(ddof=1))
    if not math.isfinite(variance) or variance <= 0.0:
        return pd.Series(dtype=float)
    return returns.apply(lambda column: column.cov(reference) / variance).dropna()


def drawdown_from_high(panel: pd.DataFrame, bars: int) -> pd.Series:
    """Distance below the trailing high, as a negative fraction."""
    if panel.empty:
        return pd.Series(dtype=float)
    window = panel.tail(bars)
    high = window.max()
    last = window.iloc[-1]
    return (last / high - 1.0).replace([np.inf, -np.inf], np.nan).dropna()


def funding_by_symbol(context) -> dict[str, pd.Series]:
    """Funding rate history per symbol, oldest first."""
    frame = context.funding
    if frame is None or frame.empty or "funding_rate" not in frame:
        return {}
    result: dict[str, pd.Series] = {}
    for symbol, group in frame.groupby("symbol", sort=False):
        ordered = group.sort_values("funding_time")
        result[str(symbol)] = ordered["funding_rate"].astype(float).reset_index(drop=True)
    return result


def kmeans_labels(matrix: np.ndarray, clusters: int, *, seed: int, rounds: int = 25) -> np.ndarray:
    """Deterministic k-means with a spread initialisation and empty-cluster repair.

    Picking initial centres uniformly can seat every one of them inside the same group, after which
    the empty centres never move and the whole cross-section lands in one cluster: the caller sees a
    clustering that silently did nothing. The seed the evaluator supplies is the only randomness.
    """
    data = np.asarray(matrix, dtype=float)
    if data.ndim != 2 or len(data) == 0:
        return np.zeros(len(data), dtype=int)
    clusters = max(1, min(int(clusters), len(data)))
    generator = np.random.default_rng(seed)

    # k-means++ seeding: each new centre is drawn far from the ones already chosen.
    centres = [data[generator.integers(len(data))]]
    while len(centres) < clusters:
        distances = np.min(
            np.stack([((data - centre) ** 2).sum(axis=1) for centre in centres]), axis=0
        )
        total = float(distances.sum())
        if not math.isfinite(total) or total <= 0.0:
            centres.append(data[generator.integers(len(data))])
            continue
        centres.append(data[generator.choice(len(data), p=distances / total)])
    centres = np.asarray(centres, dtype=float)

    labels = np.full(len(data), -1, dtype=int)
    for _ in range(rounds):
        distances = ((data[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
        updated = distances.argmin(axis=1)
        if np.array_equal(updated, labels):
            break
        labels = updated
        for index in range(clusters):
            members = data[labels == index]
            if len(members):
                centres[index] = members.mean(axis=0)
            else:
                # Re-seat an abandoned centre on the worst-fitted point rather than leaving it
                # stranded where it can never win a member again.
                worst = int(distances[np.arange(len(data)), labels].argmax())
                centres[index] = data[worst]
    return labels


@dataclasses.dataclass
class TargetSmoother:
    """Exponential blending plus a no-trade band, held as strategy state.

    Two costs are being managed. Rebalancing all the way to a fresh signal every day pays the full
    spread on noise, and a book whose weights jitter around a stable view pays repeatedly for
    nothing. Blending damps the first; the band suppresses the second by holding when the requested
    move is too small to be worth its own cost.
    """

    decay: float = 0.25
    band: float = 0.05
    prune: float = 5e-4
    gross: float = 1.0

    current: dict[str, float] = dataclasses.field(default_factory=dict)
    emitted: dict[str, float] = dataclasses.field(default_factory=dict)

    def update(self, raw: Mapping[str, float], eligible: Sequence[str]) -> dict[str, float] | None:
        """Blend, prune, and either emit the new book or hold the old one."""
        allowed = set(map(str, eligible))
        blended: dict[str, float] = {}
        for symbol in set(self.current) | set(raw):
            if symbol not in allowed:
                continue
            previous = float(self.current.get(symbol, 0.0))
            target = float(raw.get(symbol, 0.0))
            value = (1.0 - self.decay) * previous + self.decay * target
            if abs(value) >= self.prune:
                blended[symbol] = value
        total = sum(abs(value) for value in blended.values())
        if total > self.gross > 0.0:
            blended = {symbol: value / total * self.gross for symbol, value in blended.items()}
        self.current = blended
        move = sum(
            abs(blended.get(symbol, 0.0) - self.emitted.get(symbol, 0.0))
            for symbol in set(blended) | set(self.emitted)
        )
        if self.emitted and move < self.band:
            return None
        self.emitted = dict(blended)
        return dict(blended)
