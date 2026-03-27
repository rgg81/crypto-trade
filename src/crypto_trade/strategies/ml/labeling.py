"""Forward TP/SL/timeout trade outcome labeling."""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd

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
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label each candidate candle as 1 (long) or -1 (short).

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

            h = high_arr[j]
            lo = low_arr[j]
            last_close = close_arr[j]

            if long_result == 0:
                if lo <= long_sl_price:
                    long_result = -1
                    long_step = j_pos
                elif h >= long_tp_price:
                    long_result = 1
                    long_step = j_pos

            if short_result == 0:
                if h >= short_sl_price:
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

        # Compute actual forward return for timeout cases
        fwd_return_pct = (
            ((last_close - entry) / entry * 100.0) if entry != 0 else 0.0
        )

        # Actual PnL per direction (net of fees)
        if use_atr:
            tp_pnl_pct = tp_dist / entry * 100.0 if entry != 0 else 0.0
            sl_pnl_pct = sl_dist / entry * 100.0 if entry != 0 else 0.0
        else:
            tp_pnl_pct = tp_pct
            sl_pnl_pct = sl_pct
        long_pnl = _trade_pnl(long_result, tp_pnl_pct, sl_pnl_pct, fwd_return_pct) - fee_pct
        short_pnl = _trade_pnl(short_result, tp_pnl_pct, sl_pnl_pct, -fwd_return_pct) - fee_pct

        long_pnls[ci] = long_pnl
        short_pnls[ci] = short_pnl

        # Label logic (unchanged)
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
            labels[ci] = 1 if fwd_return_pct >= 0 else -1
            reason = f"no_tp→fwd_return={fwd_return_pct:+.4f}"

        # Weight = |net PnL of the labeled direction| (fee-aware)
        labeled_pnl = long_pnl if labels[ci] == 1 else short_pnl
        weights[ci] = abs(labeled_pnl)

        if ci in verbose_set:
            ts = datetime.datetime.fromtimestamp(
                int(open_time_arr[idx]) / 1000, tz=datetime.UTC
            ).strftime("%Y-%m-%d %H:%M")
            dir_label = "LONG" if labels[ci] == 1 else "SHORT"
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
