"""Re-derive the certificate's two central empirical claims AT THE NOMINEE'S OWN PARAMETERS.

Written while completing the certificate, to make sure every number asserted in prose is one
that has actually been reproduced from the frozen configuration (FORMATION_BARS=81,
NORM_BARS=126) rather than carried over from an earlier draft configuration.

Claim A (section 2.2) -- the print-size asymmetry: taker imbalance restricted to the bars whose
average print was BELOW the symbol's own norm (``imbsml``) is more informative than the same
imbalance restricted to the ABOVE-norm bars (``imbbig``). This is the reverse of the stated prior.
Also reports ``lvl`` (plain imbalance, the obvious reading) and ``imbeq`` (equal-bar-weight
imbalance, the control that removes big-bar dominance WITHOUT using print size).

Claim B (section 2.4) -- what the three cross-sectional controls remove, and the residual's
disclosed leftover tilt to realised volatility.

Run:  uv run python tournament/cup20/teams/team-09/research/verify_claims.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import sweep as SW
from flow import prev_mean, rank_rows
from ic import forward_returns, rank_ic, summarise

SW.init()
E = SW._S["E"]
p = SW._S["p"]
fe = SW._S["fe"]
f = SW._S["f"]
cut = SW._S["cut"]
tt = pd.DatetimeIndex(p.times)
PG = ("ret", "size", "liq")

# The nominee's own parameters.
W_NOMINEE = 81
NB_NOMINEE = 126


def xcorr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    """Mean per-boundary cross-sectional rank correlation."""
    ra, rb = rank_rows(a, mask), rank_rows(b, mask)
    out = []
    for i in range(ra.shape[0]):
        ok = np.isfinite(ra[i]) & np.isfinite(rb[i])
        if ok.sum() < 6:
            continue
        x, y = ra[i][ok], rb[i][ok]
        if x.std() <= 0 or y.std() <= 0:
            continue
        out.append(((x - x.mean()) * (y - y.mean())).mean() / (x.std() * y.std()))
    return float(np.mean(out))


def main() -> None:
    print("=== Claim A: print-size asymmetry, purged rank IC (controls ret+size+liq) ===")
    for h in (9, 21, 42):
        print(f"-- forecast horizon h={h} bars --")
        fwd = forward_returns(p, h)
        for kind in ("imbsml", "imbbig", "lvl", "imbeq"):
            score = SW.score((kind,), (1.0,), 21, PG)
            r = summarise(rank_ic(score, fwd, E), tt, fe)
            folds = [round(r.get(k, float("nan")), 3) for k in ("F1", "F2", "F3", "F4")]
            print(f"   {kind:8s} w=21  ic={r['ic']:+.4f}  t={r['t']:6.2f}  folds={folds}")

    print()
    print("=== Claim B: control correlations of the nominee score (w=81, nb=126) ===")
    raw = SW.score(("bigp", "imbsml"), (1.0, 1.0), W_NOMINEE, (), nb=NB_NOMINEE, strict=True)
    res = SW.score(("bigp", "imbsml"), (1.0, 1.0), W_NOMINEE, PG, nb=NB_NOMINEE, strict=True)
    controls = {
        "window price move": rank_rows(SW.raw_measure("ret", W_NOMINEE, NB_NOMINEE), E),
        "print-size class": rank_rows(cut(prev_mean(f.log_ats, NB_NOMINEE)), E),
        "turnover class": rank_rows(cut(prev_mean(f.log_qv, NB_NOMINEE)), E),
        "realised vol 90 (NOT controlled)": rank_rows(cut(f.realised_vol(90)), E),
    }
    for name, control in controls.items():
        print(
            f"   raw vs {name:34s}: {xcorr(raw, control, E):+.4f}"
            f"   residual vs same: {xcorr(res, control, E):+.4f}"
        )
    print(f"   corr(raw score, residual score) = {xcorr(raw, res, E):+.4f}")


if __name__ == "__main__":
    main()
