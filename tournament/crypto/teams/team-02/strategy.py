"""team-02 — `t02-breakout-channel-v2` strategy.

Per-name 60-candle channel position with a deadband, EMA-smoothed. This is the frozen
QE SPEC (research_brief.md §II.8); the function body is transcribed VERBATIM from the
normative reference implementation `out/scratch/e12_final.py::build_raw_weights` (only the
scratch-only evaluator imports are dropped).

Signal only: the engine owns the eligibility mask, gross-normalisation, the 0.10/0.25 caps,
the decision lag, taker + slippage costs, funding P&L, and vol-targeting. This function emits
RAW signed weights in [-1, 1] per name (NaN never emitted; 0 = flat).

Constants (all fixed, no free parameters): N = 60, D = 0.25, K = 6.

Properties (by construction, harness-checked):
- PURE / DETERMINISTIC: a function of `pn["close"]` alone; no aux usage, no randomness
  (`aux['seed']` unused), no file reads, no network, no wall clock.
- PAST-ONLY: every rolling window ends at row t (same-bar close convention); the
  `adjust=True` EMA is causal and prefix-stable, so truncated-replay / future-corruption
  checks pass by construction.
- COLUMN-SET AGNOSTIC: symbols are derived from `pn["close"]` columns at runtime — never
  hard-coded — so extra unseen / synthetic columns (WIDENING) are handled transparently.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

N = 60
D = 0.25
K = 6


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    close = pn["close"]
    hi = close.rolling(N, min_periods=N).max()
    lo = close.rolling(N, min_periods=N).min()
    rng = hi - lo
    c = (2.0 * (close - lo) / rng - 1.0).where(rng > 0, 0.0)
    s = np.sign(c) * (c.abs() - D).clip(lower=0.0) / (1.0 - D)
    s = s.fillna(0.0)
    return s.ewm(span=K, adjust=True).mean()
