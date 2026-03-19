"""Forward TP/SL/timeout trade outcome labeling."""

from __future__ import annotations

import numpy as np
import pandas as pd


def label_trades(
    master: pd.DataFrame,
    candidate_indices: np.ndarray,
    tp_pct: float,
    sl_pct: float,
    timeout_minutes: int,
) -> np.ndarray:
    """Label each candidate candle as 1 (long), -1 (short), or 0 (skip).

    For each candidate, simulates both long and short trades forward from
    close[i] and checks which direction hits TP first without hitting SL.

    Args:
        master: DataFrame with columns: symbol, open_time, close_time, open, high, low, close.
        candidate_indices: Integer indices into master for candles to label.
        tp_pct: Take-profit percentage (e.g. 3.0 means 3%).
        sl_pct: Stop-loss percentage (e.g. 2.0 means 2%).
        timeout_minutes: Maximum forward scan duration in minutes.

    Returns:
        Array of labels: 1 (long), -1 (short), 0 (skip/ambiguous).
    """
    if len(candidate_indices) == 0:
        return np.array([], dtype=np.intp)

    sym_arr = master["symbol"].to_numpy(dtype=str)
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

        for j_pos in range(pos + 1, len(sym_idx)):
            j = sym_idx[j_pos]
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
        elif short_tp_hit and not long_tp_hit:
            labels[ci] = -1
        elif long_tp_hit and short_tp_hit:
            # Both TP hit — pick whichever was first
            if long_step < short_step:
                labels[ci] = 1
            elif short_step < long_step:
                labels[ci] = -1
            else:
                labels[ci] = 0  # ambiguous, same candle
        else:
            labels[ci] = 0  # both failed

    return labels
