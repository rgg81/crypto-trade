"""Turn a regime state into a book, and run it through the fast simulator.

Two dials, deliberately separated so the mandate's own question -- is the regime that matters for
DIRECTION the same one that matters for SIZING? -- can be asked as an experiment rather than
assumed:

* ``state``   (T,) in [-1, +1]: the market-level regime's directional call. It sets the NET
  exposure of a book whose gross the organiser always renormalises to one, so it is expressed as
  how many of the eligible names are held long against short -- the only way a weights-only
  protocol can express "less exposure" at all.
* ``rank``    (T,S): the per-symbol regime score. It decides WHICH names take the long slots. A
  book with no rank is uniform, and a uniform book makes the organiser's permutation placebo a
  no-op, so this is also what gives the falsifier something to null.
"""

from __future__ import annotations

import numpy as np

from panel import Panel


def cadence_mask(T: int, cadence: int, phase: int) -> np.ndarray:
    m = np.zeros(T, dtype=bool)
    m[phase % cadence :: cadence] = True
    return m


def build_weights(
    p: Panel,
    state: np.ndarray,
    *,
    rank: np.ndarray | None = None,
    cadence: int = 1,
    phase: int = 0,
    rebalance_on_change: bool = False,
    warmup: int | None = None,
    mode: str = "onoff",
) -> tuple[np.ndarray, np.ndarray]:
    """(T,S) raw weights and (T,) rebalance flags.

    ``mode="onoff"`` -- what the frozen candidate does. state > 0 is all-long, state < 0 is
    all-short, and state == 0 (or NaN) is FLAT: the row is an explicit rebalance carrying no
    weight, which is how a weights-only protocol says "go to cash".

    ``mode="ladder"`` -- state in [-1, 1] discretised onto the achievable net/gross ladder: with n
    names at equal magnitude, k long and n-k short gives a net of (2k-n)/n, so state == 0 is
    dollar-neutral rather than flat.

    The two are NOT the same book at state 0 and the difference is not cosmetic: under "ladder" a
    zero state buys half the universe and sells the other half in eligibility order, which is an
    arbitrary cross-sectional bet wearing the label "no exposure". "onoff" is the default because
    that mislabelling cost this team a whole sweep, and a default that quietly trades when the
    signal says do nothing is the wrong default.
    """
    if mode not in {"onoff", "ladder"}:
        raise ValueError(f"mode must be 'onoff' or 'ladder', got {mode!r}")
    T, S = p.open.shape
    w = np.zeros((T, S))
    reb = cadence_mask(T, cadence, phase)
    if warmup:
        reb[:warmup] = False
    if rebalance_on_change:
        changed = np.zeros(T, dtype=bool)
        prev = np.nan
        for t in range(T):
            v = state[t]
            if not (np.isnan(v) and np.isnan(prev)) and v != prev:
                changed[t] = True
            prev = v
        if warmup:
            changed[:warmup] = False
        reb = reb | changed

    elig = p.eligible
    for t in np.flatnonzero(reb):
        e = np.flatnonzero(elig[t])
        n = len(e)
        if n == 0:
            continue
        s = state[t]
        if not np.isfinite(s) or s == 0.0:
            continue  # flat: an explicit rebalance row carrying no weight
        if mode == "onoff":
            k = n if s > 0.0 else 0
        else:
            k = max(0, min(n, int(round((s + 1.0) / 2.0 * n))))
        if rank is None:
            order = e
        else:
            r = rank[t, e]
            r = np.where(np.isfinite(r), r, -np.inf)
            order = e[np.argsort(-r, kind="stable")]
        sign = np.full(n, -1.0)
        sign[:k] = 1.0
        w[t, order] = sign
    return w, reb
