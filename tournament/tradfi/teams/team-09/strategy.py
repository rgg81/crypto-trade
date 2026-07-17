"""team-09 — tradfi-cup-01 submission — t09-jump-momentum-v1.

Short-horizon jump / attention CONTINUATION, cross-sectional. LONG the recent-jump end of the
cross-section, short the boring end: in this retail-selected single-stock perp universe, names
that just printed extreme single-day returns attract attention-driven leveraged flow that
CONTINUES over the following weeks rather than mean-reverting.

Frozen QE spec (research_brief.md §II.8): JUMP(k=3, L=42), linear centered cross-sectional
rank, EMA halflife 10 on the weight panel. Reference lab: out/scratch/scratch_jump_lab.py with
config {"k": 3, "L": 42, "d": 0, "smooth_hl": 10} (exp-026 ≡ exp-021).

Contract (CHARTER §7): pure, deterministic, PAST-ONLY function of its inputs.
- Uses pn['close'] ONLY. `aux` is NOT read — no VIX (out of family bounds), no sector_map,
  no seed (the strategy carries no randomness).
- Tickers/dates are derived from the panel at runtime; nothing is hard-coded.
- The engine owns everything downstream (gross-normalise, |w_i|<=0.10, |net|<=0.25, the
  .shift(1) decision lag, costs, and the vol-target). This function emits RAW signed weights
  only; NaN handling collapses to 0.0 flat rows here so the EMA warmup is well-defined.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

# ---- Frozen spec constants (research_brief.md §II.8; nothing left to QE judgement) ----------
_K = 3  # top-k daily returns averaged
_L = 42  # trailing window in trading days (short-horizon family bound: L <= 42)
_SMOOTH_HL = 10.0  # EMA halflife (days) on the weight panel
# min_obs = max(min(15, L-2), ceil(0.6*L)) = max(min(15,40), ceil(25.2)) = max(15, 26) = 26
_MIN_OBS = max(min(15, _L - 2), math.ceil(0.6 * _L))
_MIN_NAMES = 10  # rows with fewer valid signals than this are flat (0)


def _topk_mean_trailing(ret: pd.DataFrame, k: int, L: int, min_obs: int) -> pd.DataFrame:
    """Mean of the k largest values in each trailing L-window (per column); NaN if < min_obs.

    Row t uses the window t-(L-1) .. t inclusive. Rows t < L-1 (incomplete window) are NaN.
    NaNs inside a window are excluded from the top-k selection (mapped to -inf, which cannot
    survive into the top-k when the valid count is >= min_obs >= k).
    """
    v = ret.to_numpy(dtype=float)  # T x N
    T, N = v.shape
    out = np.full((T, N), np.nan)
    if T < L:
        return pd.DataFrame(out, index=ret.index, columns=ret.columns)
    win = sliding_window_view(v, L, axis=0)  # (T-L+1) x N x L
    valid = (~np.isnan(win)).sum(axis=2)
    filled = np.where(np.isnan(win), -np.inf, win)
    part = np.partition(filled, L - k, axis=2)[:, :, L - k :]
    tk = part.mean(axis=2)
    ok = (valid >= min_obs) & np.isfinite(tk)
    out[L - 1 :, :] = np.where(ok, tk, np.nan)
    return pd.DataFrame(out, index=ret.index, columns=ret.columns)


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    """Raw signed weights for t09-jump-momentum-v1. See module docstring / §II.8.

    Steps (past-only, deterministic):
    1. r = close / close.shift(1) - 1  (strict NaN propagation, no padding, no fill).
    2. JUMP[i,t] = mean of the 3 largest r[i] over the trailing 42 rows; NaN if < 26 valid.
    3. per-day centered rank c = (rank - (n+1)/2) / n over the valid names.
    4. w_pre = +c (LONG high-jump, short boring); rows with n < 10 -> 0; residual NaN -> 0.
    5. w = w_pre.ewm(halflife=10, min_periods=1).mean() down the rows (days).
    """
    close = pn["close"]
    ret = close / close.shift(1) - 1.0

    sig = _topk_mean_trailing(ret, _K, _L, _MIN_OBS)

    rank = sig.rank(axis=1, method="average")  # ascending, NaN excluded
    n = sig.notna().sum(axis=1)
    c = rank.sub((n + 1) / 2.0, axis=0).div(n, axis=0)  # centered rank in (-0.5, +0.5)
    w = c  # LONG high-jump, short boring — the family direction, hard-coded

    w = w.where(n >= _MIN_NAMES, other=0.0).fillna(0.0)
    w = w.ewm(halflife=_SMOOTH_HL, min_periods=1).mean()
    return w
