"""Sample weighting module for iter-v1/031.

Provides ``composite_inv_concurrency`` sample weights: each training bar is
weighted by the inverse of the number of label windows active at that bar
(evaluated AT ENTRY, not window-averaged), then mean-renormalized per
(symbol, training_window) so each symbol contributes equal total weight.

This is structurally distinct from iter-v1/016's ``uniqueness_only`` mode:
- /016 used window-AVERAGED ``mean(1/c_t)`` over the full 21-bar label window
  → per-symbol weight std ≈ 0.0033 (degenerate; Kish ~ 1.0)
- /031 uses SCALAR ``1/c_at_entry(t)`` evaluated AT entry bar only
  → per-symbol weight std ≈ 0.33 (100× wider; Kish 0.899 pooled; mechanism alive)

The weight formula from the brief Section 3.3:

    For each (symbol, training_window):
        c_at_entry(t) = count of label windows ACTIVE at bar t (same-symbol only)
                      = number of bars t' <= t such that bar t' has a label window
                        [t', t' + label_timeout_bars) that contains t
        raw_weight_t  = 1 / c_at_entry(t)
        weight_t      = raw_weight_t / mean(raw_weight_t over training_window)

Property: per-symbol weight sum = N (training window size).  Per-symbol mean = 1.0.
"""

from __future__ import annotations

import numpy as np


def compute_concurrency_at_entry(
    open_times: np.ndarray,
    symbol_arr: np.ndarray,
    train_mask: np.ndarray,
    label_timeout_bars: int,
    interval_ms: int,
) -> np.ndarray:
    """Return ``c_at_entry`` for every bar in the master frame.

    ``c_at_entry(t)`` is the number of label windows that are ACTIVE at bar t,
    i.e., the count of bars t' such that:
        - t' is in the SAME symbol as t
        - t' <= t   (past-only; no future-bar contamination)
        - t' + label_timeout_bars * interval_ms > t  (window hasn't expired yet)

    The result array is aligned with the FULL master frame (all bars), not just
    training bars.  Callers should index with train_mask to extract training rows.

    Parameters
    ----------
    open_times:
        Open-time timestamps in milliseconds, aligned with the master frame rows.
    symbol_arr:
        Symbol string per row, same length as ``open_times``.
    train_mask:
        Boolean mask over the master frame identifying training rows.  Used to
        restrict label-window candidates to the training window for a given cell.
    label_timeout_bars:
        Number of bars in the label timeout (e.g., 21 for a 21-candle timeout).
    interval_ms:
        Bar interval in milliseconds (e.g., 8 * 3600 * 1000 for 8h).

    Returns
    -------
    np.ndarray
        Float array of shape ``(len(open_times),)`` with ``c_at_entry`` per bar.
        Bars outside the training mask (test rows) are set to 1.0 (neutral weight).
        Values are always >= 1.
    """
    n = len(open_times)
    c_at_entry = np.ones(n, dtype=np.float64)

    label_window_ms = label_timeout_bars * interval_ms

    # For each symbol, process only training bars.
    unique_syms = np.unique(symbol_arr)
    for sym in unique_syms:
        sym_mask = symbol_arr == sym
        # Training bars for this symbol.
        training_sym_mask = sym_mask & train_mask
        idxs = np.where(training_sym_mask)[0]
        if len(idxs) == 0:
            continue
        t_arr = open_times[idxs]
        # For each bar i at open_time t_i, count bars j where:
        #   t_j <= t_i  AND  t_j + label_window_ms > t_i
        # i.e., t_i - label_window_ms < t_j <= t_i
        # Vectorised: for each i, count j in t_arr where
        #   t_arr[j] <= t_arr[i] and t_arr[j] > t_arr[i] - label_window_ms
        # Using broadcasting (n_train x n_train):
        #   both arrays are over the same per-symbol training index set so this
        #   scales as O(n_sym^2) per symbol; with ~5700 bars/sym × 24-month
        #   window = ~2700 training bars, this is ~2700^2 / sym ~ 7.3M ops/sym,
        #   <1s per symbol.
        # t_arr_col shape (n_train_sym, 1); t_arr_row shape (1, n_train_sym)
        t_col = t_arr.reshape(-1, 1)  # each bar in rows
        t_row = t_arr.reshape(1, -1)  # candidate windows in cols
        # active[i, j] = True iff window starting at t_row[j] is active at t_col[i]
        active = (t_row <= t_col) & (t_row + label_window_ms > t_col)
        c = active.sum(axis=1).astype(np.float64)  # shape (n_sym,)
        # Guard: c >= 1 always (each bar's own window is active at its own time)
        c = np.maximum(c, 1.0)
        c_at_entry[idxs] = c

    return c_at_entry


def compute_composite_inv_concurrency_weights(
    open_times: np.ndarray,
    symbol_arr: np.ndarray,
    train_mask: np.ndarray,
    label_timeout_bars: int,
    interval_ms: int,
) -> np.ndarray:
    """Compute mean-renormalized ``inv_concurrency_only`` weights for training rows.

    Weight formula (brief Section 3.3):
        raw_weight_t  = 1 / c_at_entry(t)
        weight_t      = raw_weight_t / mean(raw_weight_t over (symbol, training_window))

    Mean-renormalization is PER SYMBOL so that each symbol contributes equal total
    weight to pooled Model A training dispatch.

    Parameters
    ----------
    open_times, symbol_arr, train_mask, label_timeout_bars, interval_ms:
        Same semantics as ``compute_concurrency_at_entry``.

    Returns
    -------
    np.ndarray
        Float array of shape ``(train_mask.sum(),)`` — weights for training rows only.
        Per-symbol: mean = 1.0, sum = N_sym (training count for that symbol).
        Deterministic given identical inputs and seed (no randomness).
    """
    c_at_entry = compute_concurrency_at_entry(
        open_times, symbol_arr, train_mask, label_timeout_bars, interval_ms
    )
    # Extract training rows only
    train_idxs = np.where(train_mask)[0]
    c_train = c_at_entry[train_idxs]
    syms_train = symbol_arr[train_idxs]

    raw_weights = 1.0 / c_train  # shape (n_train,)

    # Mean-renormalize per symbol
    weights = raw_weights.copy()
    unique_syms = np.unique(syms_train)
    for sym in unique_syms:
        mask = syms_train == sym
        mu = raw_weights[mask].mean()
        if mu > 0:
            weights[mask] = raw_weights[mask] / mu
        else:
            weights[mask] = 1.0  # fallback: uniform if degenerate

    return weights
