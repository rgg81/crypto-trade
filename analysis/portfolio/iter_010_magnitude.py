"""portfolio-iteration EXPLORATION-010 — MAGNITUDE-weighted signals vs binary SIGN.

The canonical iter_005 walk-forward-λ net (IS +1.30 / OOS +1.37 / DD -23%) builds each coin's
directional signal from BINARY SIGN of both components:
  - trend = mean over h∈{21,42,84,168} of  sign(close/close.shift(h) - 1)   ∈ {-1,-0.5,0,0.5,1}
  - carry = -sign( trailing-9 mean funding )                                 ∈ {-1,0,1}

HYPOTHESIS: sign discards magnitude. A continuous strength signal — "how strong the trend" /
"how extreme the funding vs peers" — may carry more alpha than its sign alone.

PRINCIPLED CONTINUOUS FORMS (leak-safe):
  - trend MAGNITUDE: mean over h of clip( (close/close.shift(h)-1) / vol_h , ±C ), a vol-scaled
    momentum z (risk-adjusted momentum). vol_h = rolling std of the h-step return, past-only,
    shift(1). This is the SAME information sign uses, but graded by t-stat-like strength.
  - carry MAGNITUDE: -cross_sectional_z( trailing-9 mean funding ), clipped ±C. The z uses ONLY
    the same-candle cross-section (no leak); the trailing-9 window is past-only. Short the most
    extreme-positive-funding coins HARDER than the marginal ones.

We test, ONE COMPONENT AT A TIME, on the EXACT canonical framework (per-λ vol-target THEN
walk-forward stitch — iter_005.walkforward; NOT iter_007's raw-stitch ordering):
  (A) magnitude-trend + sign-carry
  (B) sign-trend + magnitude-carry
  (C) magnitude-trend + magnitude-carry
each vs the SIGN baseline (iter_005). ROBUSTNESS: the clip knob C is swept {1.5,2,3,4,inf} and a
rank-based trend variant is shown, to prove any lift is not knife-edge / OOS-picked.

HARD RULES honored: taker 0.05%/side, all signals past-only/leak-safe, λ walk-forward unchanged
(iter_005.LAM_GRID / walkforward), never tuned on OOS, OOS_CUTOFF=2025-03-24. Reuses iter_002 /
iter_004 / iter_005 helpers (load_universe, load_funding, vol_target, msharpe, line, walkforward).
"""

from __future__ import annotations

import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

# default magnitude clip (z-units). Set from a principled prior (≈2σ ≈ "extreme"), NOT OOS-picked.
# Robustness sweep below proves the result is flat in C.
CLIP_DEFAULT = 3.0


def _shared_panels(coins: dict):
    """All past-only inputs shared across every variant — identical to iter_005.lam_nets prep."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    fund_next = fund.shift(-1)
    return opens, close, qv, fund, ret_fwd, elig, rvol, fund_next


def trend_sign(close: pd.DataFrame) -> pd.DataFrame:
    """Canonical SIGN trend: mean over horizons of sign(h-step return)."""
    return sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)


def trend_magnitude(close: pd.DataFrame, clip: float) -> pd.DataFrame:
    """Vol-scaled momentum z (risk-adjusted momentum), clipped ±clip, meaned over horizons.

    For each horizon h: r_h = close/close.shift(h) - 1; vol_h = rolling-std of the h-step return
    over a 3h window (past-only via the shift below). z_h = clip(r_h / vol_h, ±clip). This grades
    each horizon's vote by its strength-per-unit-risk instead of collapsing to ±1.
    """
    parts = []
    for h in base.HORIZONS:
        r_h = close / close.shift(h) - 1.0
        # vol of the h-step return itself, trailing — same family as sign's "is it up over h".
        vol_h = r_h.rolling(base.VOL_WIN).std()
        z = (r_h / vol_h.replace(0, np.nan)).clip(-clip, clip)
        parts.append(z)
    return sum(parts) / len(parts)


def trend_rank(close: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional rank trend variant (robustness): mean over h of centered xsec rank of r_h.

    A rank is winsorization-free and scale-free — if magnitude beats sign for a structural reason
    (graded conviction) and not for a clip-specific reason, the rank form should also beat sign.
    """
    parts = []
    for h in base.HORIZONS:
        r_h = (close / close.shift(h) - 1.0).where(elig)
        rk = r_h.rank(axis=1)
        n = elig.sum(axis=1)
        centered = rk.sub(n.add(1) / 2, axis=0).div(n, axis=0) * 2.0  # → roughly [-1, +1]
        parts.append(centered)
    return sum(parts) / len(parts)


def carry_sign(fund: pd.DataFrame) -> pd.DataFrame:
    """Canonical SIGN carry: -sign(trailing-9 mean funding)."""
    return -np.sign(fund.rolling(f4.M_FUND).mean())


def carry_magnitude(fund: pd.DataFrame, elig: pd.DataFrame, clip: float) -> pd.DataFrame:
    """-cross_sectional_z(trailing-9 mean funding), clipped ±clip.

    The trailing-9 mean is past-only. The z is computed ACROSS the eligible cross-section AT each
    candle (mean/std over columns of the SAME row) — no time leak. Short the most extreme-positive
    funding coins harder; long the most extreme-negative.
    """
    tf = fund.rolling(f4.M_FUND).mean().where(elig)
    mu = tf.mean(axis=1)
    sd = tf.std(axis=1)
    z = tf.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0).clip(-clip, clip)
    return -z.fillna(0.0)


def lam_nets(trend: pd.DataFrame, carry: pd.DataFrame, panels) -> dict:
    """Per-λ net for a given (trend, carry) signal pair — IDENTICAL pipeline to iter_005.lam_nets:
    blend → inverse-vol size → gross-normalize to 1 → lag → cost → real funding P&L → PER-λ
    vol-target. The ONLY thing that changes across variants is the trend/carry signal definition.
    """
    _opens, _close, _qv, _fund, ret_fwd, elig, rvol, fund_next = panels
    nets = {}
    for lam in wf.LAM_GRID:
        raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


def turnover(trend: pd.DataFrame, carry: pd.DataFrame, panels, lam: float = 0.25) -> float:
    """Mean per-candle one-way turnover of the lagged weights at a representative λ (diagnostic)."""
    _opens, _close, _qv, _fund, _ret_fwd, elig, rvol, _fund_next = panels
    raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    return float((w - w.shift(1)).abs().sum(axis=1).mean())


def report(label: str, trend: pd.DataFrame, carry: pd.DataFrame, panels) -> pd.Series:
    """Walk-forward-stitch a signal pair (iter_005.walkforward) and print the standard line."""
    nets = lam_nets(trend, carry, panels)
    net_wf, picks = wf.walkforward(nets)
    base.line(label, net_wf)
    oos = Counter(b for y, b in picks if y >= 2025)
    tn = turnover(trend, carry, panels)
    print(f"     OOS λ-picks={dict(sorted(oos.items()))}  turnover≈{tn:.3f}")
    return net_wf


def main() -> None:
    coins = base.load_universe()
    panels = _shared_panels(coins)
    _opens, close, _qv, fund, _ret_fwd, elig, _rvol, _fund_next = panels
    print(
        f"EXPLORATION-010: MAGNITUDE vs SIGN signals — {len(coins)} candidates, "
        f"λ-grid {wf.LAM_GRID}, clip C={CLIP_DEFAULT}"
    )

    t_sign = trend_sign(close)
    t_mag = trend_magnitude(close, CLIP_DEFAULT)
    c_sign = carry_sign(fund)
    c_mag = carry_magnitude(fund, elig, CLIP_DEFAULT)

    print("\n-- canonical SIGN baseline + the three magnitude variants --")
    report("BASE sign/sign", t_sign, c_sign, panels)
    report("A  MAGt/sign  ", t_mag, c_sign, panels)
    report("B  sign/MAGc  ", t_sign, c_mag, panels)
    report("C  MAGt/MAGc  ", t_mag, c_mag, panels)

    print("\n-- ROBUSTNESS: trend-clip sweep C∈{1.5,2,3,4,inf} (variant A, sign-carry fixed) --")
    for c in [1.5, 2.0, 3.0, 4.0, np.inf]:
        tag = "inf" if not np.isfinite(c) else f"{c:g}"
        report(f"A  C={tag:>4}   ", trend_magnitude(close, c), c_sign, panels)

    print("\n-- ROBUSTNESS: carry-clip sweep C∈{1.5,2,3,4,inf} (variant B, sign-trend fixed) --")
    for c in [1.5, 2.0, 3.0, 4.0, np.inf]:
        tag = "inf" if not np.isfinite(c) else f"{c:g}"
        report(f"B  C={tag:>4}   ", t_sign, carry_magnitude(fund, elig, c), panels)

    print("\n-- ROBUSTNESS: rank-trend variant (winsor-free; vs sign-carry) --")
    report("A' rank-trend ", trend_rank(close, elig), c_sign, panels)


if __name__ == "__main__":
    main()
