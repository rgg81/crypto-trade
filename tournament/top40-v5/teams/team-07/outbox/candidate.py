"""team-07 -- cointegration convergence. Discovery baseline.

The most direct expression of the lane mandate: rolling pairwise Engle-Granger cointegration on
log closes, a *preregistered* half-life rather than a fitted one, and a divergence stop.

Every constant below is either Tier-0 (fixed by the sealed thesis and never searchable), the
declared Tier-1 *centre*, or a declared Tier-2 *default*.  Nothing here has been moved in response
to a result, because there are no results yet.  See RATIONALE.md for the mapping.

Design notes that matter for reading the code:

* Statelessness (thesis C4).  No state may persist across decisions, so every stop is a function
  of the rolling window alone.  "Bars since entry" is unavailable; "bars since the residual last
  crossed its in-window mean" is, and is used instead.  The whole position rule is a function of
  three window statistics per pair -- current z, the peak |z| of the *current* excursion, and the
  age of that excursion.
* Because the Engle-Granger regression carries an intercept, the fitted residual has mean exactly
  zero in-window.  So "the in-window mean" is 0, z = e_last / sd(e), and "crossed the mean" is a
  sign change of e.  This also gives magnitude-scale equivariance for free (thesis C5): a symbol
  rescaling P -> cP shifts log P by log c, which alpha absorbs.
* No symbol identity, no absolute dates, no time-of-day conditioning anywhere.  Leg roles inside a
  pair are assigned by trailing liquidity, not by name.
* No volatility targeting of any kind: the ex-ante risk unit is the organizer's (thesis C7).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------------
# Tier 0 -- fixed by preregistration, never searched.
# --------------------------------------------------------------------------------------------
# Half-life and window are declared in *days* because that is what an OU half-life means; they are
# converted to bars from the observed bar spacing.  W >= 6H is the mandate's window/half-life
# coupling (thesis C2).
HALF_LIFE_DAYS = 5.0          # Tier-1 knob 3 centre: H = 15 bars on an 8h grid
WINDOW_DAYS = 60.0            # Tier-2 knob 6 default: W = 180 bars on an 8h grid
WINDOW_HALF_LIFE_RATIO = 6.0  # C2: W >= 6H

# --------------------------------------------------------------------------------------------
# Tier 1 -- declared search grid, held at the declared centre for this trial.
# --------------------------------------------------------------------------------------------
Z_STOP = 3.5        # knob 1 centre -- divergence stop, in formation-window sigma
AGE_STOP_HL = 2.0   # knob 2 centre -- excursion-age stop, k half-lives (the *primary* stop)
Z_IN = 2.0          # knob 4 centre -- entry threshold
N_PAIRS = 20        # knob 5 centre -- pairs held

# --------------------------------------------------------------------------------------------
# Tier 2 -- declared, held at default; opened only on the stated trigger.
# --------------------------------------------------------------------------------------------
ADF_TAU = -3.0          # knob 7  -- ADF t-stat screen on the EG residual
Z_OUT = 0.25            # knob 8  -- take-profit
M_PARTNERS = 5          # knob 9  -- correlation-ranked partners tested per symbol (C6)
M_MAX = 2               # knob 10 -- max pairs a single symbol may appear in
EVENT_VETO = 8.0        # knob 11 -- idiosyncratic-event veto, in trailing leg dispersion
BETA_DRIFT_BAND = 0.50  # knob 12 -- S2 relationship-invalidation band on beta
LIQ_FLOOR = 0.25        # knob 13 -- universe filter, cross-sectional quote-volume percentile
FUNDING_VETO = True     # knob 14 -- veto a pair whose carry eats the convergence it is chasing
FUNDING_SHARE = 0.5     # fraction of expected convergence gain that carry may consume

# --------------------------------------------------------------------------------------------
# Structural guards.  Not knobs: numerical floors and compute bounds, stated so they are visible.
# --------------------------------------------------------------------------------------------
MIN_WINDOW_BARS = 40
MAX_WINDOW_BARS = 400
MAX_SYMBOLS = 400        # bounds the O(N*m) pair count; well above a Binance USD-M cross-section
MIN_SYMBOLS = 4
FALLBACK_BARS_PER_DAY = 3.0   # 8h venue funding clock, used only if bar spacing is unreadable
MAX_SYMBOL_WEIGHT = 0.0999    # engine cap is 0.10; stay strictly inside it
MAX_GROSS = 0.99              # engine cap is 1.00
MAX_NET = 0.24                # engine cap is 0.25
EPS = 1e-12


# --------------------------------------------------------------------------------------------
# Pure helpers.
# --------------------------------------------------------------------------------------------
def _stamps(index: pd.Index, window: int) -> np.ndarray | None:
    """Trailing `window` index entries as int64 nanoseconds, or None if the index is not a clock.

    Never returns an absolute date to the caller's logic -- the values are only ever compared
    between symbols for alignment, or differenced to recover the bar spacing.

    Broadly guarded on purpose: an exception raised here would produce a flat book for the whole
    run, which the kit warns is indistinguishable from a strategy with no edge.  Returning None
    instead degrades alignment to positional, which is merely less safe rather than silent.
    """
    try:
        stamps = pd.DatetimeIndex(index[-window:])
    except Exception:
        return None
    try:
        stamps = stamps.tz_localize(None)
    except TypeError:
        pass  # already tz-naive
    except Exception:
        return None
    try:
        return stamps.to_numpy(dtype="datetime64[ns]").astype("int64")
    except Exception:
        return None


def _median_bar_seconds(index: pd.Index) -> float:
    """Median spacing of a bar index, in seconds.  A duration, never an absolute date."""
    if len(index) < 3:
        return 0.0
    stamps = _stamps(index, 64)
    if stamps is None or stamps.size < 3:
        return 0.0
    gaps = np.diff(stamps)
    gaps = gaps[gaps > 0]
    if gaps.size == 0:
        return 0.0
    return float(np.median(gaps)) / 1e9


def _horizons(bars_per_day: float) -> tuple[int, int]:
    """Preregistered half-life and formation window, in bars, subject to W >= 6H."""
    half_life = int(round(HALF_LIFE_DAYS * bars_per_day))
    half_life = max(half_life, 2)
    window = int(round(WINDOW_DAYS * bars_per_day))
    window = max(window, int(round(WINDOW_HALF_LIFE_RATIO * half_life)), MIN_WINDOW_BARS)
    window = min(window, MAX_WINDOW_BARS)
    # If the clamp above broke the coupling, the half-life yields rather than the window.
    half_life = min(half_life, max(2, int(window // WINDOW_HALF_LIFE_RATIO)))
    return half_life, window


def _panel(
    bars: Mapping[str, pd.DataFrame], symbols: Sequence[str], window: int
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Aligned (S, W) log-close panel plus per-symbol trailing median quote volume.

    Symbols whose last `window` timestamps do not match the reference grid are dropped rather
    than silently misaligned -- a misaligned pair regression is a spurious cointegration factory.
    `symbols` is expected longest-history first, so the reference grid is taken from the most
    established member.  If the index is not a clock at all, alignment degrades to positional.
    """
    reference: np.ndarray | None = None
    rows: list[np.ndarray] = []
    volumes: list[float] = []
    kept: list[str] = []
    for symbol in symbols:
        frame = bars.get(symbol)
        if frame is None or len(frame) < window:
            continue
        if "close" not in frame.columns:
            continue
        stamps = _stamps(frame.index, window)
        if stamps is not None:
            if reference is None:
                reference = stamps
            elif not np.array_equal(stamps, reference):
                continue
        closes = np.asarray(frame["close"].to_numpy()[-window:], dtype="float64")
        if not np.all(np.isfinite(closes)) or np.any(closes <= 0.0):
            continue
        if "quote_volume" in frame.columns:
            raw = np.asarray(frame["quote_volume"].to_numpy()[-window:], dtype="float64")
            raw = raw[np.isfinite(raw)]
            volume = float(np.median(raw)) if raw.size else 0.0
        else:
            volume = 0.0
        rows.append(np.log(closes))
        volumes.append(volume)
        kept.append(symbol)
    if not kept:
        return [], np.empty((0, window)), np.empty(0)
    return kept, np.vstack(rows), np.asarray(volumes, dtype="float64")


def _candidate_pairs(logs: np.ndarray, volumes: np.ndarray, partners: int) -> np.ndarray:
    """Each symbol's top-`partners` return-correlated peers, as unique unordered pairs.

    Thesis C6: testing all N(N-1)/2 pairs manufactures thousands of spurious relationships by
    construction.  Restricting to O(N*m) keeps the multiple-testing burden countable.

    Leg roles are set by trailing liquidity -- the deeper name is the regressor -- which is a
    statistical rule, so pair construction carries no symbol identity.
    """
    count = logs.shape[0]
    returns = np.diff(logs, axis=1)
    centred = returns - returns.mean(axis=1, keepdims=True)
    scale = np.sqrt((centred * centred).sum(axis=1))
    scale = np.where(scale > EPS, scale, 1.0)
    unit = centred / scale[:, None]
    corr = unit @ unit.T
    np.fill_diagonal(corr, -np.inf)

    width = int(min(partners, count - 1))
    if width < 1:
        return np.empty((0, 2), dtype="int64")
    top = np.argpartition(-corr, kth=width - 1, axis=1)[:, :width]

    seen: set[tuple[int, int]] = set()
    for a in range(count):
        for b in top[a]:
            b = int(b)
            if b == a or not np.isfinite(corr[a, b]):
                continue
            # regressor x = deeper leg; index order breaks exact ties deterministically
            if (volumes[a], a) >= (volumes[b], b):
                pair = (b, a)
            else:
                pair = (a, b)
            seen.add(pair)
    if not seen:
        return np.empty((0, 2), dtype="int64")
    return np.asarray(sorted(seen), dtype="int64")


def _ols_residual(dependent: np.ndarray, regressor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Batched Engle-Granger step one: y ~ 1 + x.  Returns beta and the mean-zero residual."""
    y_centred = dependent - dependent.mean(axis=1, keepdims=True)
    x_centred = regressor - regressor.mean(axis=1, keepdims=True)
    sxx = (x_centred * x_centred).sum(axis=1)
    sxy = (x_centred * y_centred).sum(axis=1)
    usable = sxx > EPS
    beta = np.where(usable, sxy / np.where(usable, sxx, 1.0), 0.0)
    residual = y_centred - beta[:, None] * x_centred
    return beta, residual


def _adf_t(residual: np.ndarray) -> np.ndarray:
    """Batched Engle-Granger step two: ADF t-stat on the residual, one lag, no constant.

    The residual is mean-zero by construction, so no intercept belongs in the test regression.
    Singular or degenerate systems return +inf, which fails the screen.
    """
    if residual.shape[1] < 8:
        return np.full(residual.shape[0], np.inf)
    diffs = np.diff(residual, axis=1)
    target = diffs[:, 1:]
    level = residual[:, 1:-1]
    lagged = diffs[:, :-1]
    design = np.stack([level, lagged], axis=2)

    gram = np.einsum("ptk,ptl->pkl", design, design)
    moment = np.einsum("ptk,pt->pk", design, target)
    det = gram[:, 0, 0] * gram[:, 1, 1] - gram[:, 0, 1] * gram[:, 1, 0]
    usable = np.abs(det) > EPS
    safe = np.where(usable, det, 1.0)

    inverse = np.empty_like(gram)
    inverse[:, 0, 0] = gram[:, 1, 1] / safe
    inverse[:, 1, 1] = gram[:, 0, 0] / safe
    inverse[:, 0, 1] = -gram[:, 0, 1] / safe
    inverse[:, 1, 0] = -gram[:, 1, 0] / safe

    coef = np.einsum("pkl,pl->pk", inverse, moment)
    fitted = np.einsum("ptk,pk->pt", design, coef)
    error = target - fitted
    dof = max(target.shape[1] - 2, 1)
    sigma2 = (error * error).sum(axis=1) / dof
    variance = sigma2 * inverse[:, 0, 0]
    usable = usable & (variance > EPS) & np.isfinite(variance)
    stat = np.where(usable, coef[:, 0] / np.sqrt(np.where(usable, variance, 1.0)), np.inf)
    return np.where(np.isfinite(stat), stat, np.inf)


def _excursion(residual: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stateless replacement for trade bookkeeping (thesis C4).

    Returns (current z, peak |z| of the current excursion, age of that excursion in bars), where
    an excursion runs from the residual's last sign change to now.  This reconstructs entry,
    take-profit and both stops from the window alone: a position is held while the excursion has
    *already* reached the entry threshold and has not yet decayed past take-profit, timed out, or
    breached the divergence stop.
    """
    width = residual.shape[1]
    sigma = residual.std(axis=1, ddof=1)
    sigma = np.where(sigma > EPS, sigma, np.nan)
    z_path = residual / sigma[:, None]
    z_now = z_path[:, -1]

    opposite = residual * residual[:, -1][:, None] < 0.0
    columns = np.arange(width)
    last_cross = np.where(opposite, columns, -1).max(axis=1)
    age = (width - 1) - last_cross          # width when no crossing exists in the window

    inside = columns > last_cross[:, None]
    peak = np.where(inside, np.abs(np.nan_to_num(z_path)), 0.0).max(axis=1)
    return z_now, peak, age.astype("float64")


def _event_flags(logs: np.ndarray, lookback: int, threshold: float) -> np.ndarray:
    """Single-name news veto: a bar whose |log return| dwarfs the leg's own trailing dispersion.

    This is the observable shadow of the unlocks, listings and liquidation cascades the dataset
    does not carry.  News is a *permanent* relationship break, not a temporary excursion.
    """
    returns = np.abs(np.diff(logs, axis=1))
    dispersion = np.median(returns, axis=1)
    live = dispersion > EPS
    recent = returns[:, -min(lookback, returns.shape[1]):]
    return live & (recent > threshold * dispersion[:, None]).any(axis=1)


def _funding_medians(funding: pd.DataFrame, symbol_count: int) -> Mapping[str, float]:
    """Trailing median 8h funding rate per symbol, read defensively.

    The kit is explicit that the column is `funding_rate`, not `last_funding_rate`.  Reading a
    column that does not exist produces a flat book rather than an error, so every access is
    guarded.  Rows are taken from the tail rather than filtered on a timestamp so that no
    timezone assumption can silently empty the frame.
    """
    if not isinstance(funding, pd.DataFrame) or funding.empty:
        return {}
    if "symbol" not in funding.columns or "funding_rate" not in funding.columns:
        return {}
    keep = max(2000, 120 * max(symbol_count, 1))
    tail = funding.tail(keep)
    try:
        grouped = tail.groupby("symbol")["funding_rate"].median()
    except (TypeError, ValueError):
        return {}
    return {
        str(key): float(value)
        for key, value in grouped.items()
        if np.isfinite(value)
    }


# --------------------------------------------------------------------------------------------
# Strategy.
# --------------------------------------------------------------------------------------------
class CointegrationConvergence:
    """Rolling pairwise Engle-Granger convergence with a preregistered half-life.

    The instance holds no mutable attributes.  Every decision is computed from the window it is
    handed, which satisfies exact-replay determinism by construction rather than by discipline.
    """

    def target_weights(
        self, context, *, seed: int
    ) -> Mapping[str, float] | None:
        # DecisionContext fields are accessed directly: they are guaranteed by the protocol
        # dataclass, and RULES.md forbids `getattr`.
        eligible = [str(s) for s in context.eligible_symbols]
        bars = context.bars
        if not eligible or not isinstance(bars, Mapping):
            return {}

        # --- horizons, in bars, from the observed spacing -------------------------------------
        lengths = [(len(bars[s]), s) for s in eligible if s in bars and len(bars[s]) > 0]
        if not lengths:
            return {}
        lengths.sort(key=lambda item: (-item[0], item[1]))
        longest, anchor = lengths[0]
        spacing = _median_bar_seconds(bars[anchor].index)
        bars_per_day = 86400.0 / spacing if spacing > 0.0 else FALLBACK_BARS_PER_DAY
        half_life, window = _horizons(bars_per_day)
        if longest < window:
            return {}

        # --- aligned panel, liquidity floor ---------------------------------------------------
        # Longest-history first, so the reference grid comes from the most established member.
        symbols, logs, volumes = _panel(bars, [s for _, s in lengths], window)
        if len(symbols) < MIN_SYMBOLS:
            return {}
        if LIQ_FLOOR > 0.0:
            floor = float(np.quantile(volumes, LIQ_FLOOR))
            keep = np.flatnonzero(volumes >= floor)
            if keep.size >= MIN_SYMBOLS:
                symbols = [symbols[i] for i in keep]
                logs, volumes = logs[keep], volumes[keep]
        if len(symbols) > MAX_SYMBOLS:
            keep = np.argsort(-volumes)[:MAX_SYMBOLS]
            keep.sort()
            symbols = [symbols[i] for i in keep]
            logs, volumes = logs[keep], volumes[keep]
        if len(symbols) < MIN_SYMBOLS:
            return {}

        # --- candidate pairs, cointegration screen -------------------------------------------
        pairs = _candidate_pairs(logs, volumes, M_PARTNERS)
        if pairs.shape[0] == 0:
            return {}
        left, right = pairs[:, 0], pairs[:, 1]
        dependent, regressor = logs[left], logs[right]

        beta, residual = _ols_residual(dependent, regressor)
        adf = _adf_t(residual)

        # S2, relationship invalidation: the hedge ratio re-estimated on the recent half of the
        # window must still describe the same relationship.  This is falsifier F2 run live.
        recent = max(window // 2, 8)
        beta_recent, _ = _ols_residual(dependent[:, -recent:], regressor[:, -recent:])
        drift = np.abs(beta_recent - beta) / np.maximum(np.abs(beta), EPS)

        z_now, peak, age = _excursion(residual)
        sigma = residual.std(axis=1, ddof=1)
        flagged = _event_flags(logs, half_life, EVENT_VETO)

        # A cointegrating vector with beta <= 0 is a long/long common-trend bet, not a
        # relative-value spread.  It is outside the family, so it is screened out on sign --
        # a structural condition, not a fitted threshold.
        screen = (
            np.isfinite(adf)
            & (adf <= ADF_TAU)
            & (beta > 0.0)
            & (drift <= BETA_DRIFT_BAND)
            & (sigma > EPS)
            & np.isfinite(z_now)
            & ~flagged[left]
            & ~flagged[right]
        )
        # The three stops and the entry band, all as window statistics:
        #   S3 divergence stop -- the excursion never breached z_stop
        #   S1 excursion-age stop (primary) -- it is no older than k half-lives
        #   entry / take-profit -- it reached z_in, and has not yet decayed inside z_out
        signal = (
            screen
            & (peak >= Z_IN)
            & (peak < Z_STOP)
            & (np.abs(z_now) >= Z_OUT)
            & (age <= AGE_STOP_HL * half_life)
        )
        live = np.flatnonzero(signal)
        if live.size == 0:
            return {}

        # --- funding veto ---------------------------------------------------------------------
        # Direction: e > 0 means the dependent leg is rich, so we short it.
        direction = -np.sign(z_now)
        if FUNDING_VETO:
            rates = _funding_medians(context.funding, len(symbols))
            if rates:
                per_symbol = np.asarray([rates.get(s, 0.0) for s in symbols], dtype="float64")
                # Carry paid over one half-life, per unit of pair gross, against the convergence
                # gain expected over the same span (half the gap closes in one half-life).
                carry = direction[live] * (
                    per_symbol[left[live]] - beta[live] * per_symbol[right[live]]
                )
                cost = carry * half_life / (1.0 + beta[live])
                gain = 0.5 * np.abs(residual[live, -1]) / (1.0 + beta[live])
                live = live[cost <= FUNDING_SHARE * gain]
                if live.size == 0:
                    return {}

        # --- book construction ----------------------------------------------------------------
        # Ranked by the mandate's own statistic -- strength of cointegration evidence, not by
        # expected return.  Equal gross per pair; legs beta-weighted; each symbol capped at M_MAX
        # appearances so the book is a portfolio rather than a levered view on two names.
        order = live[np.argsort(adf[live], kind="stable")]
        pair_gross = MAX_GROSS / N_PAIRS
        weights: dict[str, float] = {}
        appearances: dict[str, int] = {}
        held = 0
        for index in order:
            if held >= N_PAIRS:
                break
            y_symbol = symbols[left[index]]
            x_symbol = symbols[right[index]]
            if appearances.get(y_symbol, 0) >= M_MAX or appearances.get(x_symbol, 0) >= M_MAX:
                continue
            side = float(direction[index])
            hedge = float(beta[index])
            if side == 0.0 or not np.isfinite(hedge) or hedge <= 0.0:
                continue
            scale = pair_gross / (1.0 + hedge)
            weights[y_symbol] = weights.get(y_symbol, 0.0) + side * scale
            weights[x_symbol] = weights.get(x_symbol, 0.0) - side * hedge * scale
            appearances[y_symbol] = appearances.get(y_symbol, 0) + 1
            appearances[x_symbol] = appearances.get(x_symbol, 0) + 1
            held += 1

        book = {
            symbol: float(np.clip(value, -MAX_SYMBOL_WEIGHT, MAX_SYMBOL_WEIGHT))
            for symbol, value in weights.items()
            if np.isfinite(value) and abs(value) > 1e-6
        }
        if not book:
            return {}

        gross = sum(abs(v) for v in book.values())
        if gross > MAX_GROSS:
            book = {s: v * MAX_GROSS / gross for s, v in book.items()}
        net = sum(book.values())
        if abs(net) > MAX_NET:
            book = {s: v * MAX_NET / abs(net) for s, v in book.items()}
        return book


def build_strategy() -> CointegrationConvergence:
    return CointegrationConvergence()
