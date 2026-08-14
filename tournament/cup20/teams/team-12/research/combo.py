"""Combine cached exact sleeve matrices under the preregistered rule and score offline."""
from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
import fastsim as FS, metricsfast as MF

SLEEVES = ("carry", "trend", "lowrisk", "flow")


def proxy(panel, W):
    t0, n = panel.t0, len(panel.times)
    cl = panel.close
    r = cl[t0 - 1 : t0 + n - 1] / cl[t0 - 2 : t0 + n - 2] - 1.0
    r = np.where(np.isfinite(r), r, 0.0)
    x = np.zeros(n)
    x[1:] = (W[:-1] * r[1:]).sum(axis=1)
    return x


def multipliers(panel, W, bars):
    n = len(panel.times)
    x = proxy(panel, W)
    m = np.ones(n)
    if bars <= 0:
        return m
    c1 = np.cumsum(x); c2 = np.cumsum(x * x)
    for i in range(bars, n):
        s = c1[i - 1] - (c1[i - bars - 1] if i - bars - 1 >= 0 else 0.0)
        q = c2[i - 1] - (c2[i - bars - 1] if i - bars - 1 >= 0 else 0.0)
        var = (q - s * s / bars) / (bars - 1)
        if var > 0:
            m[i] = 1.0 / np.sqrt(var)
    return m


def combine(panel, mats, names=SLEEVES, bars=270, equal_notional=False):
    n = len(panel.times)
    out = np.zeros_like(mats[names[0]])
    mus = {}
    for k in names:
        mu = np.ones(n) if equal_notional else multipliers(panel, mats[k], bars)
        mus[k] = mu
        out += mu[:, None] * mats[k]
    return out, mus


def rebalance(n, cadence, phase, W):
    r = (np.arange(n) % cadence) == (phase % cadence)
    return r & (np.abs(W).sum(axis=1) > 0)


def score(panel, W, cadence, phase, trial_count=2, label=""):
    rb = rebalance(len(panel.times), cadence, phase, W)
    sc = MF.scored_vector(FS.run_book(W, rb, panel), panel, trial_count=trial_count)
    if label:
        print(MF.show(sc, label)); sys.stdout.flush()
    return sc
