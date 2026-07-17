"""team-10 — t10-ts-trend-v1 strategy (FROZEN SPEC, research_brief.md Section 9.1).

Plain per-name time-series trend: each name goes long / short on the sign of its own
trailing 12-month (252d) vol-normalized return with a 1-week (5d) skip, sized inversely to
its own EWM volatility, then EMA-21 smoothed. No cross-sectional operation of any kind, no
gating: every quantity used for name i comes from name i's own ``close`` series alone.

Interface contract (CHARTER Sec. 7): ``build_raw_weights(pn, aux) -> pd.DataFrame`` of RAW
signed weights (NaN/0 = flat). PURE, DETERMINISTIC, PAST-ONLY function of ``pn['close']``:
- every operation (pct_change, log, ewm, shift, sign) is causal — row t depends only on
  data at or before t; the future-corruption / truncated-replay harness is satisfied
  structurally.
- ``aux`` (vix, sector_map, seed) is intentionally UNUSED — no randomness anywhere.
- tickers are the panel columns at runtime (never hard-coded).

The engine owns everything downstream: gross-normalise to 1, |w_i| <= 0.10, |net| <= 0.25,
the .shift(1) decision lag, 6 bps/side cost on |dw|, and 15%/yr vol-targeting. We emit raw
signed weights only; same-bar decisions.

Constants (ALL fixed by the frozen spec, nothing left to the QE): momentum lookback K=252,
skip s=5, sqrt-normalizer sqrt(247) = sqrt(252-5), vol = EWM std(span=63, min_periods=42)
of ``close.pct_change(fill_method=None)`` floored at 0.004/day, transform = sign, sizing =
1/sigma, weight smoothing = EMA span 21 (min_periods=1) applied AFTER ``fillna(0.0)``.
"""

from __future__ import annotations

import numpy as np


def build_raw_weights(pn, aux):
    close = pn["close"]                                   # dates x tickers, ragged starts
    ret = close.pct_change(fill_method=None)              # simple daily returns, no padding
    logp = np.log(close)
    sigma = ret.ewm(span=63, min_periods=42).std().clip(lower=0.004)
    mom = logp.shift(5) - logp.shift(252)                 # 12m momentum, 1w skip
    z = mom / (sigma * np.sqrt(247.0))                    # 247 = 252 - 5
    w = np.sign(z) / sigma                                # sign transform, inverse-vol size
    w = w.fillna(0.0).ewm(span=21, min_periods=1).mean()  # EMA-21 weight smoothing
    return w
