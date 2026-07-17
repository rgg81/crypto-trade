"""team-05 — t05-volume-liquidity-anomalies-v1 / Amihud illiquidity rank book.

Family (registry-approved): volume/liquidity anomalies, menu #6. Sub-mechanism taken forward:
the Amihud illiquidity premium — illiquid names must pay a return premium, so hold the
illiquid end long against the liquid end short. Rank-linear symmetric, quasi-static book.

`build_raw_weights(pn, aux)` is a PURE, DETERMINISTIC, PAST-ONLY function of its inputs.
Every value on row t is computable from bars at or before t (trailing rolling windows +
same-row cross-sectional rank). `aux['seed']` is accepted but unused — there is no randomness
anywhere. Only `pn['close']` and `pn['volume']` are read (per the FINAL SPEC); no VIX, no
sector_map, no open/high/low, no ret_fwd (not in the interface anyway).

The engine (`tournament.engine`) owns everything downstream of the raw signed weights:
gross-normalisation to 1, the |w_i| <= 0.10 per-name cap, the |Σw| <= 0.25 net cap, the
`.shift(1)` decision lag, taker costs on |Δweight| turnover, and the 15%/yr vol-target. This
module NEVER pre-applies any of them.

Parameters are FIXED by research_brief.md FINAL SPEC (exp-016 selected as the plateau center
of the all-positive K ∈ {126, 252, 504} illiquidity plateau):

  ILLIQ_WINDOW      = 252   trailing rows for the Amihud mean
  ILLIQ_MIN_PERIODS = 126   a name needs >= 126 valid (ret, dollar) days in the window
                            (ragged starts enter after ~6 months of history)
"""

from __future__ import annotations

ILLIQ_WINDOW = 252
ILLIQ_MIN_PERIODS = 126


def build_raw_weights(pn, aux):
    """Raw signed weight panel (dates x tickers); NaN = flat. Long illiquid / short liquid.

    Steps (research_brief.md FINAL SPEC, verbatim):
      1. close, volume from the panel; ticker set derived from the panel columns at runtime.
      2. ret    = close.pct_change(fill_method=None)                 (NaN preserved, no padding)
      3. dollar = (close * volume) masked to NaN where <= 0          (zero/absent bars excluded)
      4. illiq  = (|ret| / dollar).rolling(252, min_periods=126).mean()  (rolling skips NaN)
      5. eligibility at row t: illiq non-NaN AND close non-NaN       (else NaN raw weight = flat)
      6. rank   = illiq.rank(axis=1, method='average') over eligible names (ascending: 1 = most
                  liquid); raw_i = rank_i - (N_t + 1)/2 -> most illiquid gets the largest
                  positive weight, book dollar-neutral pre-caps by symmetry. Row scale is
                  irrelevant (the engine gross-normalises).
    """
    close = pn["close"]
    volume = pn["volume"]

    ret = close.pct_change(fill_method=None)
    dollar = (close * volume).where(lambda x: x > 0)
    illiq = (ret.abs() / dollar).rolling(
        ILLIQ_WINDOW, min_periods=ILLIQ_MIN_PERIODS
    ).mean()

    # eligibility: valid illiquidity AND a live close on the decision bar
    key = illiq.where(close.notna())
    rank = key.rank(axis=1, method="average")
    n_eligible = key.notna().sum(axis=1)
    raw = rank.sub((n_eligible + 1) / 2.0, axis=0)
    return raw
