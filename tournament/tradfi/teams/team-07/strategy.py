"""team-07 — t07-overnight-tugofwar-v1 strategy.

Family: Overnight-vs-intraday gap decomposition ("tug of war"). The frozen QE
specification (research_brief.md §7) is the trailing overnight-return persistence
book: cross-sectionally sort names by their trailing 252-day mean overnight
component, weight linear in centered pct-rank, and smooth the weight panel with an
EMA (halflife=5) to control turnover at 6 bps/side.

Mechanism (research_brief.md §1-2): decompose each name's daily return into an
overnight component ``on[t] = open[t]/close[t-1] - 1`` and an intraday component
``id[t] = close[t]/open[t] - 1``. The IS experiment ledger (e-002..e-018) located
the tradeable edge in the OVERNIGHT component alone (ON-only, e-002/007/012); the
intraday-fade leg was net-negative and the canonical spread merely diluted ON, so
the final spec is ON-only.

Contract (CHARTER §7): PURE, DETERMINISTIC, PAST-ONLY function of its inputs.
  * Inputs touched: ``pn['open']`` and ``pn['close']`` ONLY. No high/low/volume,
    no vix, no sector_map, no seed (aux is unused — the book carries no randomness).
  * Tickers are derived from the panel columns at runtime (never hard-coded).
  * Emits RAW signed weights only. The engine owns gross-normalisation, the
    0.10/0.25 caps, the ``.shift(1)`` decision lag, costs and the 15% vol-target —
    none of that is pre-applied here.
  * NaN weight = flat name (engine treats it as zero exposure).

Every constant below is fixed by the frozen spec — do not tune:
  W = 252 bars, min_periods = 252 (strict: any NaN inside the trailing window
  blanks the name that day), cross-sectional transform = pct-rank centered by row
  mean, weighting linear in centered rank, EMA halflife = 5 bars (min_periods = 1,
  pandas defaults adjust=True / ignore_na=False).
"""

from __future__ import annotations

import pandas as pd

# Frozen parameters (research_brief.md §7 — "nothing left to decide").
_FORMATION_W = 252  # trailing formation window, bars
_MIN_PERIODS = 252  # strict: full window required before a name gets a signal
_EMA_HALFLIFE = 5  # weight-panel smoothing halflife, bars


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    """Raw signed weight panel (dates × tickers); NaN = flat.

    Past-only by construction:
      * ``on[t] = open[t]/close[t-1] - 1`` uses only bars at or before t.
      * ``rolling(252).mean()`` is a trailing (backward) window.
      * ``rank``/centering are row-wise (cross-sectional, no time leak).
      * ``ewm(...).mean()`` is a causal exponential weighted mean along time.
    ``aux`` (vix / sector_map / seed) is intentionally unused: the spec adds no
    regime gating and no randomness.
    """
    o, c = pn["open"], pn["close"]  # dates × tickers; tickers from panel columns
    on = o / c.shift(1) - 1.0  # overnight component: open[t] / close[t-1] - 1
    sig = on.rolling(_FORMATION_W, min_periods=_MIN_PERIODS).mean()
    r = sig.rank(axis=1, pct=True)  # cross-sectional pct-rank (method='average', na keep)
    w = r.sub(r.mean(axis=1), axis=0)  # center -> row-wise dollar-neutral; NaN stays NaN
    return w.ewm(halflife=_EMA_HALFLIFE, min_periods=1).mean()  # turnover-control smoothing
