"""Team-01 EDA step 4 -- joint surface over conviction shape, vol window, ladder and overlap.

Same scope declaration as ``eda_03_shape.py``: gross, cost-free signal diagnostics only. No cost
model, no funding, no caps, no common risk unit, no risk policy, no charter floor is computed here.
``dW`` is the annualised sum of absolute target-weight changes at unit gross -- a property of the
strategy's own weight sequence, reported so a specification that structurally cannot be traded is
not carried into a trial.

Questions posed before the numbers:
 1. Does a continuous bounded conviction beat a hard sign, and does it beat it *per unit of weight
    churn*? Mechanism: near a zero crossing a sign flip trades the full position for an arbitrarily
    small change in the underlying trend, which is a pure cost with no information in it.
 2. Is fold F3 -- the post-FTX chop -- survivable by any own-history specification, or is it the
    structural limit of this lane?
 3. Does a slower own-volatility estimate reduce churn without costing edge?
"""

from __future__ import annotations

import numpy as np

from eda_03_shape import BARS_PER_YEAR, HEAD, book, report
from panel import build_panel, log_returns, rolling_std, rolling_sum


def prepare(vol_bars: int):
    panel = build_panel()
    ret = log_returns(panel.signal_price)
    vol = rolling_std(ret, vol_bars)
    finite = vol[np.isfinite(vol) & (vol > 0)]
    vol = np.maximum(vol, np.quantile(finite, 0.01))
    fwd = np.full_like(panel.exec_open, np.nan)
    fwd[:-1] = panel.exec_open[1:] / panel.exec_open[:-1] - 1.0
    return panel, ret, vol, fwd


def shaped(ret, vol, anchor, ladder, kind, scale):
    parts, ok = [], None
    for multiple in ladder:
        length = max(3, int(round(anchor * multiple)))
        with np.errstate(invalid="ignore"):
            z = rolling_sum(ret, length) / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        if kind == "sign":
            part = np.sign(z)
        elif kind == "clip":
            part = np.clip(z / scale, -1.0, 1.0)
        elif kind == "tanh":
            part = np.tanh(z / scale)
        else:
            raise ValueError(kind)
        parts.append(np.where(good, part, 0.0))
    return np.where(ok, np.mean(np.stack(parts), axis=0), np.nan)


def main() -> None:
    for vol_bars in (90, 180):
        panel, ret, vol, fwd = prepare(vol_bars)
        folds = panel.fold_of_boundary()
        elig = panel.eligible
        print(f"\n================ own-vol window = {vol_bars} bars ({vol_bars // 3} days)")
        print("conviction shape x ladder x overlap; dW = annualised sum |dw| at unit gross")
        print(HEAD.replace("turn", "  dW"))
        for kind, scale in (("sign", 0.0), ("clip", 1.0), ("tanh", 1.0), ("tanh", 0.5)):
            for anchor in (45, 90, 135):
                for ladder in ((1 / 3, 1.0, 2.0), (1.0, 2.0, 4.0)):
                    conv = shaped(ret, vol, anchor, ladder, kind, scale)
                    for hold in (1, 9, 21):
                        tag = (
                            f"{kind}{scale if kind != 'sign' else ''} L={anchor} "
                            f"x{'lo' if ladder[0] < 1 else 'hi'} h={hold}"
                        )
                        report(tag, book(conv, vol, elig, hold=hold), fwd, folds, panel.grid)
                print()


if __name__ == "__main__":
    main()
