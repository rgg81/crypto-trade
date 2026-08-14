"""The exact arithmetic the frozen strategy performs, in one place.

`strategy.py` streams `DecisionContext` and cannot import this module, so the code is transcribed
rather than shared -- but it is transcribed from here, and `validate_exact.py` asserts that the
transcription and this function agree elementwise on the real panel. Anything that drifts between
them is a bug in one of the two, and the assertion is what finds it.

Definitions, all on the decision grid:

    m[t]        the equal-weight market log return the strategy observes AT decision t: the mean,
                over the symbols eligible at t, of log(close of the last closed bar / close of the
                bar before it). The last bar closed by decision t is the bar that OPENED at t-1,
                so m[t] is the bar-(t-1) return -- causal by construction, and one bar is all the
                lag the harness's own truncation rule allows.
    rv[j]       sqrt(mean(m[j-INNER+1 .. j]^2))   -- short-horizon realised volatility.
    vov[t]      std(rv[t-OUTER+1 .. t]) / mean(same)  -- the COEFFICIENT OF VARIATION of that
                volatility over the outer window. Scale-free: it is a statement about how STEADY
                the variance process is, not about how large it is.
    z[t]        (vov[t] - mean(vov[t-BASE+1 .. t])) / std(vov[t-BASE+1 .. t])

Every window is required to be FULLY populated; the layer stands flat until it is. Population
standard deviations (ddof=0) throughout.
"""

from __future__ import annotations

import numpy as np


def vov_z(m: np.ndarray, inner: int, outer: int, base: int) -> np.ndarray:
    """Causal z-scored vol-of-vol. Row t uses only m[0..t]. NaN until every window is full.

    ``m`` must be finite everywhere. A single NaN poisons every cumulative sum after it, and the
    first version of this function then fell through a ``sd > 0`` guard to a constant 0.0 -- which
    produced a book that was always long or always flat and looked like a real (bad) result rather
    than like a bug. It is asserted rather than tolerated.
    """
    m = np.asarray(m, dtype=float)
    if not np.isfinite(m).all():
        raise ValueError(
            f"vov_z requires a finite market-return series; {int((~np.isfinite(m)).sum())} "
            "non-finite values found"
        )
    n = len(m)
    out = np.full(n, np.nan)
    sq = m**2
    c2 = np.concatenate(([0.0], np.cumsum(sq)))
    rv = np.full(n, np.nan)
    if inner <= n:
        idx = np.arange(inner - 1, n)
        rv[idx] = np.sqrt((c2[idx + 1] - c2[idx + 1 - inner]) / inner)
    cr = np.concatenate(([0.0], np.cumsum(np.nan_to_num(rv))))
    cr2 = np.concatenate(([0.0], np.cumsum(np.nan_to_num(rv) ** 2)))
    vov = np.full(n, np.nan)
    first_v = inner - 1 + outer - 1
    if first_v < n:
        idx = np.arange(first_v, n)
        s1 = cr[idx + 1] - cr[idx + 1 - outer]
        s2 = cr2[idx + 1] - cr2[idx + 1 - outer]
        mean = s1 / outer
        var = np.clip(s2 / outer - mean * mean, 0.0, None)
        vov[idx] = np.where(mean > 0, np.sqrt(var) / mean, np.nan)
    cv = np.concatenate(([0.0], np.cumsum(np.nan_to_num(vov))))
    cv2 = np.concatenate(([0.0], np.cumsum(np.nan_to_num(vov) ** 2)))
    first_z = first_v + base - 1
    if first_z < n:
        idx = np.arange(first_z, n)
        s1 = cv[idx + 1] - cv[idx + 1 - base]
        s2 = cv2[idx + 1] - cv2[idx + 1 - base]
        mean = s1 / base
        var = np.clip(s2 / base - mean * mean, 0.0, None)
        sd = np.sqrt(var)
        if not (sd > 0).all():
            raise ValueError("zero-variance vol-of-vol window; the signal has collapsed")
        out[idx] = (vov[idx] - mean) / sd
    return out


def decision_market_returns(panel, root="data/cup20/is") -> np.ndarray:
    """m[t]: the series the frozen strategy accumulates, one value per decision boundary.

    Aggregated over the symbols ELIGIBLE AT t -- exactly the set the strategy is handed -- using
    each one's own last CLOSED bar's log return, which is the bar that opened at t-1.

    Read from the bar file rather than from the panel's own matrices, because the panel starts at
    IS_START and the bar that closed at the FIRST decision opened before it. The strategy sees that
    bar (every symbol's frame carries its whole history), so the replica must too; taking it from
    the panel would leave m[0] undefined and shift the whole series by one boundary.
    """
    import pandas as pd
    from pathlib import Path

    bars = pd.read_parquet(Path(root) / "bars.parquet", columns=["open_time", "symbol", "close"])
    bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True)
    wide = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    wide = wide.reindex(columns=list(panel.symbols))
    with np.errstate(invalid="ignore", divide="ignore"):
        step = np.log(wide.to_numpy(dtype=float) / wide.shift(1).to_numpy(dtype=float))
    step[~np.isfinite(step)] = np.nan
    pos = {t: i for i, t in enumerate(wide.index)}
    interval = panel.times[1] - panel.times[0]
    n = len(panel.times)
    out = np.full(n, np.nan)
    for t in range(n):
        row = pos.get(panel.times[t] - interval)
        if row is None:
            continue
        sel = panel.eligible[t] & np.isfinite(step[row])
        if sel.any():
            out[t] = float(step[row][sel].mean())
    return out
