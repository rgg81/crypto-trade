"""Offline mirror of the preregistered combination rule. Validated against the real strategy."""
from __future__ import annotations
import numpy as np
import sleeves as SL

SLEEVE_ORDER = ("carry", "trend", "lowrisk", "flow")


def build_sleeves(panel, elig, *, carry_lb=126, trend_base=90, lowrisk_base=189, flow_base=63):
    return {
        "carry": SL.s_carry(panel, elig, lookback=carry_lb),
        "trend": SL.s_trend(panel, elig, base=trend_base),
        "lowrisk": SL.s_lowrisk(panel, elig, base=lowrisk_base),
        "flow": SL.s_flow(panel, elig, base=flow_base),
    }


def proxy_returns(panel, W):
    """x_k(g) = sum_i w_k,i(g-1) * (close_i[g-1]/close_i[g-2] - 1), the rule's proxy series."""
    t0 = panel.t0; n = len(panel.times)
    cl = panel.close
    r = cl[t0 - 1 : t0 + n - 1] / cl[t0 - 2 : t0 + n - 2] - 1.0   # index i -> close[gi-1]/close[gi-2]-1
    r = np.where(np.isfinite(r), r, 0.0)
    x = np.zeros(n)
    x[1:] = (W[:-1] * r[1:]).sum(axis=1)
    return x


def combine(panel, sleeves, *, names=SLEEVE_ORDER, risk_parity_bars=270, equal_notional=False):
    n = len(panel.times)
    xs = {k: proxy_returns(panel, sleeves[k]) for k in names}
    mult = {k: np.ones(n) for k in names}
    if not equal_notional:
        for k in names:
            x = xs[k]
            for i in range(n):
                # history holds observations attributed to boundaries strictly before i
                if i < risk_parity_bars:
                    continue
                w = x[i - risk_parity_bars : i]
                sd = float(np.std(w, ddof=1))
                mult[k][i] = 1.0 / sd if np.isfinite(sd) and sd > 0 else 1.0
    out = np.zeros_like(sleeves[names[0]])
    for k in names:
        out += mult[k][:, None] * sleeves[k]
    return out, mult, xs
