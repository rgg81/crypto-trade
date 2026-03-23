"""Forward TP/SL/timeout trade outcome labeling."""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd

_RESULT_NAMES = {1: "tp", -1: "sl", -2: "timeout", 0: "pending"}


def label_trades(
    master: pd.DataFrame,
    candidate_indices: np.ndarray,
    tp_pct: float,
    sl_pct: float,
    timeout_minutes: int,
    verbose: int = 0,
    verbose_samples: int = 20,
) -> tuple[np.ndarray, np.ndarray]:
    """Label each candidate candle as 1 (long) or -1 (short) with sample weights.

    For each candidate, simulates both long and short trades forward from
    close[i].  If one direction hits TP (and the other doesn't), that direction
    wins.  If both hit or neither hits, the direction with the better forward
    return is chosen.

    Sample weights are proportional to the absolute forward return so that
    high-conviction labels carry more influence during training.

    Args:
        master: DataFrame with columns: symbol, open_time, close_time, open, high, low, close.
        candidate_indices: Integer indices into master for candles to label.
        tp_pct: Take-profit percentage (e.g. 3.0 means 3%).
        sl_pct: Stop-loss percentage (e.g. 2.0 means 2%).
        timeout_minutes: Maximum forward scan duration in minutes.
        verbose: If > 0, print detailed labeling info for a random subset.
        verbose_samples: Number of random samples to print (default 20).

    Returns:
        Tuple of (labels, weights):
        - labels: array of 1 (long) or -1 (short)
        - weights: array of positive floats (higher = stronger signal)
    """
    if len(candidate_indices) == 0:
        return np.array([], dtype=np.intp), np.array([], dtype=np.float64)

    # Pick random sample indices for verbose logging
    verbose_set: set[int] = set()
    if verbose > 0 and len(candidate_indices) > 0:
        rng = np.random.default_rng(42)
        n_show = min(verbose_samples, len(candidate_indices))
        verbose_set = set(rng.choice(len(candidate_indices), size=n_show, replace=False).tolist())

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

    tp_mult = tp_pct / 100.0
    sl_mult = sl_pct / 100.0

    labels = np.zeros(len(candidate_indices), dtype=np.intp)
    weights = np.ones(len(candidate_indices), dtype=np.float64)

    for ci, idx in enumerate(candidate_indices):
        entry = close_arr[idx]
        sym = str(sym_arr[idx])
        deadline = close_time_arr[idx] + timeout_ms

        sym_idx = symbol_indices[sym]
        # Find position of idx in the symbol's array, then scan forward
        pos = np.searchsorted(sym_idx, idx)

        long_tp_price = entry * (1 + tp_mult)
        long_sl_price = entry * (1 - sl_mult)
        short_tp_price = entry * (1 - tp_mult)
        short_sl_price = entry * (1 + sl_mult)

        long_result = 0  # 0=pending, 1=tp, -1=sl, -2=timeout
        short_result = 0
        long_step = -1
        short_step = -1
        n_candles_scanned = 0

        # Track the last close price within the window for return calculation
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

            # Check long
            if long_result == 0:
                if lo <= long_sl_price:
                    long_result = -1
                    long_step = j_pos
                elif h >= long_tp_price:
                    long_result = 1
                    long_step = j_pos

            # Check short
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
            # Ran out of data
            if long_result == 0:
                long_result = -2
                long_step = len(sym_idx)
            if short_result == 0:
                short_result = -2
                short_step = len(sym_idx)

        # Label logic
        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1

        if long_tp_hit and not short_tp_hit:
            labels[ci] = 1
            reason = "long_tp_only"
        elif short_tp_hit and not long_tp_hit:
            labels[ci] = -1
            reason = "short_tp_only"
        elif long_tp_hit and short_tp_hit:
            # Both TP hit — pick whichever was first
            if long_step <= short_step:
                labels[ci] = 1
                reason = "both_tp→long_first"
            else:
                labels[ci] = -1
                reason = "both_tp→short_first"
        else:
            # Neither TP hit — use forward return to decide direction
            fwd_return = (last_close - entry) / entry if entry != 0 else 0.0
            labels[ci] = 1 if fwd_return >= 0 else -1
            reason = f"no_tp→fwd_return={fwd_return:+.4f}"

        # Weight = absolute forward return (higher return = stronger signal)
        fwd_return_abs = abs(last_close - entry) / entry if entry != 0 else 0.0
        weights[ci] = fwd_return_abs

        if ci in verbose_set:
            ts = datetime.datetime.fromtimestamp(
                int(open_time_arr[idx]) / 1000, tz=datetime.UTC
            ).strftime("%Y-%m-%d %H:%M")
            dir_label = "LONG" if labels[ci] == 1 else "SHORT"
            long_r = _RESULT_NAMES[long_result]
            short_r = _RESULT_NAMES[short_result]
            print(
                f"  [label] {ts} {sym} entry={entry:.4f} → {dir_label} | "
                f"long={long_r}(step {long_step - pos}) "
                f"short={short_r}(step {short_step - pos}) | "
                f"fwd={fwd_return_abs:+.4f} scanned={n_candles_scanned} | "
                f"{reason}"
            )

    # Normalize weights: shift to [1, max_weight] range so all samples contribute
    if len(weights) > 0 and weights.max() > 0:
        weights = 1.0 + weights / weights.max() * 9.0  # range [1, 10]

    return labels, weights
