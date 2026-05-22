"""Forward TP/SL/timeout trade outcome labeling."""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd


def compute_sample_uniqueness(
    candidate_indices: np.ndarray,
    timeout_minutes: int,
    open_time_arr: np.ndarray,
    sym_arr: np.ndarray,
) -> np.ndarray:
    """Compute sample uniqueness weights (AFML Ch. 4) — vectorized.

    Each label's outcome depends on forward candles up to timeout. When two
    adjacent samples' label windows overlap, they share information. Uniqueness
    measures how much of each sample's label window is "its own."

    For each sample i with label window [t_i, t_i + timeout_ms]:
      1. Count c_t = number of active label windows at each candle t
      2. Uniqueness(i) = mean(1/c_t) for candles in [t_i, t_i + timeout_ms]

    Uses a vectorized sweep-line approach: O(n log n) per symbol instead of O(n^2).

    Args:
        candidate_indices: Indices into the master arrays for labeled samples.
        timeout_minutes: Label forward-scan duration in minutes.
        open_time_arr: Array of open_time values for the full master df.
        sym_arr: Array of symbol strings for the full master df.

    Returns:
        Array of uniqueness values in (0, 1] with same length as candidate_indices.
    """
    n = len(candidate_indices)
    if n == 0:
        return np.array([], dtype=np.float64)

    timeout_ms = timeout_minutes * 60 * 1000
    uniqueness = np.ones(n, dtype=np.float64)

    # Group candidates by symbol
    sym_groups: dict[str, list[int]] = {}
    for ci, idx in enumerate(candidate_indices):
        sym = str(sym_arr[idx])
        sym_groups.setdefault(sym, []).append(ci)

    for sym, ci_list in sym_groups.items():
        m = len(ci_list)
        ci_arr = np.array(ci_list)

        # Label window: [start, start + timeout] for each candidate
        starts = open_time_arr[candidate_indices[ci_arr]].astype(np.int64)
        ends = starts + timeout_ms

        # Get all candle timestamps for this symbol (sorted)
        sym_mask = sym_arr == sym
        sym_times = np.sort(open_time_arr[sym_mask].astype(np.int64))
        n_times = len(sym_times)
        if n_times == 0:
            continue

        # For each candle timestamp, count how many label windows contain it.
        # A label i is active at candle t if starts[i] <= t <= ends[i].
        # Use vectorized broadcasting: for each time t, count active labels.
        # To avoid O(n_times * m), use a sweep-line with sorted start/end events.

        # Compute c_t for all sym_times using cumulative event counting
        # Events: +1 at each start, -1 at each end+1
        # Sort events by time, sweep to get c_t at each candle
        events = np.concatenate([starts, ends + 1])  # +1 so end is inclusive
        event_vals = np.concatenate([np.ones(m), -np.ones(m)])
        order = np.argsort(events, kind="mergesort")
        events = events[order]
        event_vals = event_vals[order]

        # For each sym_time, compute c_t via binary search into cumulative events
        cum_vals = np.cumsum(event_vals)
        # c_t at time t = cum_vals at last event <= t
        ct_indices = np.searchsorted(events, sym_times, side="right") - 1
        c_t = np.zeros(n_times, dtype=np.float64)
        valid = ct_indices >= 0
        c_t[valid] = cum_vals[ct_indices[valid]]
        c_t = np.maximum(c_t, 1.0)  # avoid division by zero

        inv_ct = 1.0 / c_t

        # For each sample, compute mean(1/c_t) over candles in its window
        # Use binary search to find window boundaries efficiently
        left_idx = np.searchsorted(sym_times, starts, side="left")
        right_idx = np.searchsorted(sym_times, ends, side="right")

        # Prefix sum of inv_ct for O(1) range queries
        prefix = np.zeros(n_times + 1, dtype=np.float64)
        prefix[1:] = np.cumsum(inv_ct)

        for local_i in range(m):
            li = left_idx[local_i]
            ri = right_idx[local_i]
            window_len = ri - li
            if window_len > 0:
                uniqueness[ci_arr[local_i]] = (prefix[ri] - prefix[li]) / window_len
            else:
                uniqueness[ci_arr[local_i]] = 1.0

    return uniqueness


_RESULT_NAMES = {1: "tp", -1: "sl", -2: "timeout", 0: "pending"}


def _trade_pnl(result: int, tp_pct: float, sl_pct: float, fwd_return: float) -> float:
    """Compute the actual PnL for a single direction's outcome.

    Args:
        result: 1=tp hit, -1=sl hit, -2=timeout, 0=pending/end-of-data.
        tp_pct: Take-profit percentage (e.g. 4.0).
        sl_pct: Stop-loss percentage (e.g. 2.0).
        fwd_return: Forward return in percentage for timeout/pending cases.
    """
    if result == 1:
        return tp_pct
    if result == -1:
        return -sl_pct
    # timeout or pending — use actual forward return
    return fwd_return


def _trend_scan_label(
    close_arr: np.ndarray,
    sym_idx: np.ndarray,
    pos: int,
    grid: tuple[int, ...],
) -> tuple[int, int, float]:
    """Select the best horizon by max |t-statistic| and return the trend label.

    For each horizon h in *grid*, fit an OLS linear trend of
    ``close[t : t+h+1]`` on the time index ``[0, 1, ..., h]`` and compute
    the slope t-statistic via closed-form least-squares.

    Returns:
        (label, best_h, fwd_return_pct) where
        - label: +1 if slope >= 0 else -1 at the horizon with max |t-stat|
        - best_h: the selected horizon in candles
        - fwd_return_pct: realized return at the selected horizon (%)
    """
    # Pre-gather the available close prices forward of pos (up to max(grid)+1 bars)
    max_h = max(grid)
    available: list[float] = []
    for j_pos in range(pos + 1, min(pos + max_h + 1, len(sym_idx)) + 1):
        if j_pos >= len(sym_idx):
            break
        available.append(float(close_arr[sym_idx[j_pos]]))
        if len(available) >= max_h:
            break

    entry_close = float(close_arr[sym_idx[pos]])

    best_abs_t = -1.0
    best_label = 1  # default to +1 if no valid horizon found
    best_h = grid[0]
    best_fwd_pct = 0.0

    for h in grid:
        if len(available) < h:
            # Not enough forward bars for this horizon — skip
            continue
        # prices: close[t+1..t+h] (h prices), index 0..h-1 represents candle offset 1..h
        y = np.empty(h + 1, dtype=np.float64)
        y[0] = entry_close
        for k in range(h):
            y[k + 1] = available[k]

        x = np.arange(h + 1, dtype=np.float64)

        # Closed-form OLS slope and t-statistic (dof = n-2)
        n = h + 1
        if n < 3:
            # Need at least 3 points for dof=1 t-test
            continue

        x_mean = x.mean()
        y_mean = y.mean()
        ss_xx = float(np.sum((x - x_mean) ** 2))
        if ss_xx == 0.0:
            continue
        slope = float(np.sum((x - x_mean) * (y - y_mean))) / ss_xx

        # Residual standard error
        y_hat = y_mean + slope * (x - x_mean)
        ss_res = float(np.sum((y - y_hat) ** 2))
        dof = n - 2
        if dof <= 0:
            continue
        se_slope = (ss_res / dof / ss_xx) ** 0.5 if ss_xx > 0 else 0.0
        if se_slope == 0.0:
            t_stat = 1e10 if slope > 0 else (-1e10 if slope < 0 else 0.0)
        else:
            t_stat = slope / se_slope

        abs_t = abs(t_stat)
        if abs_t > best_abs_t:
            best_abs_t = abs_t
            best_label = 1 if slope >= 0 else -1
            best_h = h
            horizon_close = available[h - 1]
            best_fwd_pct = (
                (horizon_close - entry_close) / entry_close * 100.0 if entry_close != 0 else 0.0
            )

    return best_label, best_h, best_fwd_pct


def label_trades(
    master: pd.DataFrame,
    candidate_indices: np.ndarray,
    tp_pct: float,
    sl_pct: float,
    timeout_minutes: int,
    fee_pct: float = 0.1,
    atr_values: np.ndarray | None = None,
    verbose: int = 0,
    verbose_samples: int = 20,
    neutral_threshold_pct: float | None = None,
    label_mode: str = "triple_barrier",
    trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label each candidate candle as 1 (long), -1 (short), or 0 (neutral).

    Returns actual trade PnLs for both directions so the optimizer can
    compute realistic Sharpe ratios.

    Args:
        master: DataFrame with columns: symbol, open_time, close_time,
                open, high, low, close.
        candidate_indices: Integer indices into master for candles to label.
        tp_pct: Take-profit percentage (e.g. 4.0) OR ATR multiplier when
                atr_values is provided.
        sl_pct: Stop-loss percentage (e.g. 2.0) OR ATR multiplier when
                atr_values is provided.
        timeout_minutes: Maximum forward scan duration in minutes.
        fee_pct: Trading fee percentage (deducted from returns).
        atr_values: If provided, array of ATR values per master row.
                    TP = atr * tp_pct, SL = atr * sl_pct (tp_pct/sl_pct
                    become ATR multipliers instead of percentages).
        verbose: If > 0, print detailed labeling info for a random subset.
        verbose_samples: Number of random samples to print (default 20).
        label_mode: Labeling rule to use. Default ``"triple_barrier"``
                    preserves byte-identical behaviour for v1/v2 and any
                    caller that does not pass the parameter. ``"fixed_horizon"``
                    replaces the TP/SL barrier-first-hit rule with the sign
                    of the realized N-candle-forward return (where N is
                    determined by timeout_minutes / candle_interval). Barriers
                    are NOT scanned; the full scan runs to the timeout candle.
                    ``long_pnl`` and ``short_pnl`` are the realized forward
                    return net of fee_pct; ``weight = abs(labeled_pnl)``.
                    ``"trend_scanning"`` (iter-v3/105): for each bar, fits an
                    OLS linear trend over ``close[t:t+h+1]`` for each horizon
                    h in *trend_scan_grid*; selects the horizon with the
                    largest |t-statistic|; labels +1 if slope >= 0 else -1.
                    PnL convention = realized forward return at the selected
                    horizon net of fee_pct (same as ``"fixed_horizon"``).
                    The grid is capped at max(grid) <= timeout_minutes so the
                    existing CV embargo is unchanged. When label_mode is not
                    ``"trend_scanning"``, *trend_scan_grid* is inert.
        trend_scan_grid: Horizon grid (in candles) for the trend-scanning
                    label. Default ``(5, 8, 13, 21)``. Only used when
                    ``label_mode="trend_scanning"``. The maximum must be <=
                    timeout_minutes // interval_minutes to preserve the
                    existing embargo; for the v3 baseline this is 21.
    Returns:
        Tuple of (labels, weights, long_pnls, short_pnls):
        - labels: array of 1 (long) or -1 (short)
        - weights: array of positive floats (net-of-fee return magnitude)
        - long_pnls: array of net PnL if you go long (fee deducted)
        - short_pnls: array of net PnL if you go short (fee deducted)
    """
    n = len(candidate_indices)
    empty = (
        np.array([], dtype=np.intp),
        np.array([], dtype=np.float64),
        np.array([], dtype=np.float64),
        np.array([], dtype=np.float64),
    )
    if n == 0:
        return empty

    # Pick random sample indices for verbose logging
    verbose_set: set[int] = set()
    if verbose > 0 and n > 0:
        rng = np.random.default_rng(42)
        n_show = min(verbose_samples, n)
        verbose_set = set(rng.choice(n, size=n_show, replace=False).tolist())

    sym_arr = master["symbol"].to_numpy(dtype=str)
    open_time_arr = master["open_time"].values
    close_time_arr = master["close_time"].values
    high_arr = master["high"].values
    low_arr = master["low"].values
    close_arr = master["close"].values

    timeout_ms = timeout_minutes * 60 * 1000

    # Build per-symbol sorted index arrays for efficient forward scanning
    symbol_indices: dict[str, np.ndarray] = {}
    for sym in np.unique(sym_arr):
        symbol_indices[sym] = np.where(sym_arr == sym)[0]

    use_atr = atr_values is not None
    tp_mult = tp_pct / 100.0
    sl_mult = sl_pct / 100.0

    labels = np.zeros(n, dtype=np.intp)
    weights = np.ones(n, dtype=np.float64)
    long_pnls = np.zeros(n, dtype=np.float64)
    short_pnls = np.zeros(n, dtype=np.float64)

    for ci, idx in enumerate(candidate_indices):
        entry = close_arr[idx]
        sym = str(sym_arr[idx])
        deadline = close_time_arr[idx] + timeout_ms

        sym_idx = symbol_indices[sym]
        pos = np.searchsorted(sym_idx, idx)

        if use_atr:
            atr = float(atr_values[idx]) if not np.isnan(atr_values[idx]) else entry * 0.02
            tp_dist = atr * tp_pct  # tp_pct is ATR multiplier
            sl_dist = atr * sl_pct  # sl_pct is ATR multiplier
        else:
            tp_dist = entry * tp_mult
            sl_dist = entry * sl_mult

        long_tp_price = entry + tp_dist
        long_sl_price = entry - sl_dist
        short_tp_price = entry - tp_dist
        short_sl_price = entry + sl_dist

        long_result = 0  # 0=pending, 1=tp, -1=sl, -2=timeout
        short_result = 0
        long_step = -1
        short_step = -1
        n_candles_scanned = 0
        last_close = entry

        use_fixed_horizon = label_mode == "fixed_horizon"
        use_trend_scanning = label_mode == "trend_scanning"

        if use_trend_scanning:
            # iter-v3/105: trend-scanning label — skip the per-bar barrier loop entirely.
            # _trend_scan_label accesses the forward close array directly via sym_idx.
            ts_label, ts_h, fwd_return_pct = _trend_scan_label(
                close_arr, sym_idx, pos, trend_scan_grid
            )
            long_pnl = fwd_return_pct - fee_pct
            short_pnl = -fwd_return_pct - fee_pct
            labels[ci] = ts_label
            reason = f"ts_h={ts_h}_fwd_return={fwd_return_pct:+.4f}"
            # verbose logging handled below (same path)
        else:
            for j_pos in range(pos + 1, len(sym_idx)):
                j = sym_idx[j_pos]
                n_candles_scanned += 1
                if close_time_arr[j] > deadline:
                    if long_result == 0:
                        long_result = -2
                        long_step = j_pos
                    if short_result == 0:
                        short_result = -2
                        short_step = j_pos
                    break

                h_bar = high_arr[j]
                lo = low_arr[j]
                last_close = close_arr[j]

                if not use_fixed_horizon:
                    # triple_barrier: detect TP/SL hits and short-circuit
                    if long_result == 0:
                        if lo <= long_sl_price:
                            long_result = -1
                            long_step = j_pos
                        elif h_bar >= long_tp_price:
                            long_result = 1
                            long_step = j_pos

                    if short_result == 0:
                        if h_bar >= short_sl_price:
                            short_result = -1
                            short_step = j_pos
                        elif lo <= short_tp_price:
                            short_result = 1
                            short_step = j_pos

                    if long_result != 0 and short_result != 0:
                        break
            else:
                if long_result == 0:
                    long_result = -2
                    long_step = len(sym_idx)
                if short_result == 0:
                    short_result = -2
                    short_step = len(sym_idx)

            # Compute actual forward return for timeout cases (and fixed_horizon)
            fwd_return_pct = ((last_close - entry) / entry * 100.0) if entry != 0 else 0.0

            if use_fixed_horizon:
                # fixed_horizon: ignore barriers entirely; PnL = realized N-candle return
                long_pnl = fwd_return_pct - fee_pct
                short_pnl = -fwd_return_pct - fee_pct
                if (
                    neutral_threshold_pct is not None
                    and abs(fwd_return_pct) < neutral_threshold_pct
                ):
                    labels[ci] = 0
                    reason = f"fh_neutral→fwd_return={fwd_return_pct:+.4f}"
                else:
                    labels[ci] = 1 if fwd_return_pct >= 0 else -1
                    reason = f"fh_fwd_return={fwd_return_pct:+.4f}"
            else:
                # Actual PnL per direction (net of fees) — triple_barrier path
                if use_atr:
                    tp_pnl_pct = tp_dist / entry * 100.0 if entry != 0 else 0.0
                    sl_pnl_pct = sl_dist / entry * 100.0 if entry != 0 else 0.0
                else:
                    tp_pnl_pct = tp_pct
                    sl_pnl_pct = sl_pct
                long_pnl = _trade_pnl(long_result, tp_pnl_pct, sl_pnl_pct, fwd_return_pct) - fee_pct
                short_pnl = (
                    _trade_pnl(short_result, tp_pnl_pct, sl_pnl_pct, -fwd_return_pct) - fee_pct
                )

                # Label logic — triple_barrier
                long_tp_hit = long_result == 1
                short_tp_hit = short_result == 1

                if long_tp_hit and not short_tp_hit:
                    labels[ci] = 1
                    reason = "long_tp_only"
                elif short_tp_hit and not long_tp_hit:
                    labels[ci] = -1
                    reason = "short_tp_only"
                elif long_tp_hit and short_tp_hit:
                    if long_step <= short_step:
                        labels[ci] = 1
                        reason = "both_tp→long_first"
                    else:
                        labels[ci] = -1
                        reason = "both_tp→short_first"
                else:
                    # No TP hit in either direction — use forward return sign
                    if (
                        neutral_threshold_pct is not None
                        and abs(fwd_return_pct) < neutral_threshold_pct
                    ):
                        labels[ci] = 0
                        reason = f"neutral→fwd_return={fwd_return_pct:+.4f}"
                    else:
                        labels[ci] = 1 if fwd_return_pct >= 0 else -1
                        reason = f"no_tp→fwd_return={fwd_return_pct:+.4f}"

        long_pnls[ci] = long_pnl
        short_pnls[ci] = short_pnl

        # Weight = |net PnL of the labeled direction| (fee-aware)
        labeled_pnl = long_pnl if labels[ci] == 1 else short_pnl
        weights[ci] = abs(labeled_pnl)

        if ci in verbose_set:
            ts = datetime.datetime.fromtimestamp(
                int(open_time_arr[idx]) / 1000, tz=datetime.UTC
            ).strftime("%Y-%m-%d %H:%M")
            dir_label = {1: "LONG", -1: "SHORT", 0: "NEUTRAL"}.get(labels[ci], "?")
            if use_trend_scanning or use_fixed_horizon:
                print(
                    f"  [label] {ts} {sym} entry={entry:.4f} → {dir_label} | "
                    f"fwd_return={fwd_return_pct:+.2f}% "
                    f"long_pnl={long_pnl:+.2f}% short_pnl={short_pnl:+.2f}% | "
                    f"scanned={n_candles_scanned} | {reason}"
                )
            else:
                long_r = _RESULT_NAMES[long_result]
                short_r = _RESULT_NAMES[short_result]
                print(
                    f"  [label] {ts} {sym} entry={entry:.4f} → {dir_label} | "
                    f"long={long_r}({long_pnl:+.2f}%) "
                    f"short={short_r}({short_pnl:+.2f}%) | "
                    f"scanned={n_candles_scanned} | {reason}"
                )

    # Normalize weights: shift to [1, max_weight] range
    if len(weights) > 0 and weights.max() > 0:
        weights = 1.0 + weights / weights.max() * 9.0  # range [1, 10]

    return labels, weights, long_pnls, short_pnls
