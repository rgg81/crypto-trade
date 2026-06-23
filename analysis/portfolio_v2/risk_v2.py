"""risk_v2 — IS-calibrated risk layer for the portfolio-iteration-v2 BASELINE CANDIDATE.

The candidate (standalone dollar-neutral XS-mom, rank 21-40, 8h, via run_book_from_signal) is
MERGE-WITH-RISK-LAYER: the ONLY blocking condition is the drawdown (-37% IS / -25% OOS). This
module converts it into a deployable book by bounding the tail, WITHOUT touching the signal or the
engine's computation (parity-safe — the engine is unchanged except for an additive `raw_net` key).

Two orthogonal, past-only primitives, both applied as a per-candle EXPOSURE MULTIPLIER on the net:

  R2-style DRAWDOWN BRAKE (loss-stop, state-discontinuous, NOT proportional scaling)
  ----------------------------------------------------------------------------------
  A rolling-peak equity brake with a two-threshold HYSTERESIS state machine:
    * Track equity E[t] = cumprod(1 + net_book) and its running peak, using net up to t-1 ONLY.
    * trailing_dd[t] = E[t-1] / peak[t-1] - 1            (computed from the past, applied at t)
    * State ON  (brake engaged, exposure = brake_factor) once trailing_dd <= -dd_trigger.
    * State OFF (exposure = 1.0) again once trailing_dd recovers above -dd_release
      (release < trigger => hysteresis band; prevents chattering on/off at the threshold).
  This is loss-stop semantics: a binary cut to `brake_factor`, held until equity recovers, NOT a
  continuous proportional dial. State-discontinuous + explainable (preferred per the risk mandate).

  The brake is computed on the book's OWN equity curve up to t-1 and applied to candle t, so it is
  strictly path-dependent / past-only (no look-ahead). Because it scales the book's GROSS exposure,
  it scales the candle's RETURN and its TURNOVER-COST together. We apply it as a uniform per-candle
  multiplier on the engine `net` (return and cost both live inside `raw_net`, which `net` scales) —
  the approximation the brief endorses, stated explicitly here.

  STATIC TIGHTENING (lower TARGET_VOL / MAX_LEV — a shallower UNCONDITIONAL tail)
  ------------------------------------------------------------------------------
  Recompute the engine's vol-target scale from `raw_net` with a lower `target_vol` and/or `max_lev`
  (exact, not an approximation — it re-runs the engine's own clip(TARGET_VOL/rv, MAX_LEV) formula on
  the same past-only realized-vol estimate). target_vol=engine default + max_lev=engine default is a
  no-op (bit-for-bit the engine net). Lowering either yields a uniformly shallower book.

Composition: net_risk[t] = retarget(raw_net)[t] * brake_mult[t]. The brake state machine runs on the
RETARGETED net's equity curve (the curve the brake actually rides), so the two primitives compose
correctly. All thresholds are IS-CALIBRATED (pre-2025-03-24) and frozen before any OOS evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import engine_v2 as e2


# ---------------------------------------------------------------------------------------------
# Static tightening — exact vol-target retarget from raw_net
# ---------------------------------------------------------------------------------------------
def retarget(raw_net: pd.Series, target_vol: float, max_lev: float) -> pd.Series:
    """Recompute the engine's past-only vol-target net from raw_net with new (target_vol, max_lev).

    Identical formula to engine_v2.run_book_from_signal:
        rv    = raw_net.rolling(PORT_VOL_WIN).std().shift(1)
        scale = (target_vol / rv).clip(upper=max_lev).fillna(0.0)
        net   = raw_net * scale

    (target_vol=TARGET_VOL, max_lev=MAX_LEV reproduces the engine net bit-for-bit.)
    """
    rv = raw_net.rolling(e2.PORT_VOL_WIN).std().shift(1)
    scale = (target_vol / rv).clip(upper=max_lev).fillna(0.0)
    return (raw_net * scale.reindex(raw_net.index)).dropna()


# ---------------------------------------------------------------------------------------------
# R2-style drawdown brake — two-threshold hysteresis state machine, past-only
# ---------------------------------------------------------------------------------------------
def dd_brake_multiplier(
    net: pd.Series,
    dd_trigger: float,
    dd_release: float,
    brake_factor: float,
) -> pd.Series:
    """Per-candle exposure multiplier in {brake_factor, 1.0} from a rolling-peak DD hysteresis stop.

    Strictly past-only: the multiplier at candle t is decided from the equity curve through t-1.

      equity[t]    = prod_{s<=t} (1 + net[s] * mult[s])      (the ACTUAL braked equity it rides)
      peak[t]      = max_{s<=t} equity[s]
      trailing_dd  = equity[t-1] / peak[t-1] - 1             (known at t)
      state ON  iff trailing_dd <= -dd_trigger               (engage brake -> exposure brake_factor)
      state OFF iff trailing_dd >  -dd_release                (release -> exposure 1.0)
      (dd_release < dd_trigger => hysteresis band; in between, hold current state.)

    The brake feeds back on its OWN braked equity (a real loss-stop sizes off the realized, braked
    book), so the recursion is computed candle-by-candle. Returns a Series aligned to `net.index`.
    """
    vals = net.to_numpy()
    n = len(vals)
    mult = np.ones(n)
    equity = 1.0
    peak = 1.0
    state_on = False
    prev_equity = 1.0
    prev_peak = 1.0
    for t in range(n):
        # decide mult[t] from the past (equity/peak through t-1)
        if t > 0:
            tdd = prev_equity / prev_peak - 1.0
            if state_on:
                if tdd > -dd_release:
                    state_on = False
            else:
                if tdd <= -dd_trigger:
                    state_on = True
        mult[t] = brake_factor if state_on else 1.0
        # advance the braked equity with this candle's realized (braked) return
        equity *= 1.0 + vals[t] * mult[t]
        peak = max(peak, equity)
        prev_equity, prev_peak = equity, peak
    return pd.Series(mult, index=net.index)


# ---------------------------------------------------------------------------------------------
# Composed risk layer
# ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class RiskConfig:
    """Frozen, IS-calibrated risk-layer parameters."""

    target_vol: float = e2.TARGET_VOL  # default 0.01 -> no-op tightening
    max_lev: float = e2.MAX_LEV  # default 3.0 -> no-op tightening
    dd_trigger: float | None = None  # e.g. 0.10 -> engage brake at -10% trailing DD; None=off
    dd_release: float = 0.05  # release at -5% trailing DD (must be < dd_trigger)
    brake_factor: float = 0.5  # cut exposure to 50% while engaged


def apply_risk(raw_net: pd.Series, cfg: RiskConfig) -> dict:
    """Apply (static tightening -> DD brake) to a book's raw_net. Returns the risk-layered net + the
    intermediate series for stress forensics.

    net_retargeted = retarget(raw_net, cfg.target_vol, cfg.max_lev)
    brake_mult     = dd_brake_multiplier(net_retargeted, ...)   (None trigger -> all-ones)
    net_risk       = net_retargeted * brake_mult
    """
    net_rt = retarget(raw_net, cfg.target_vol, cfg.max_lev)
    if cfg.dd_trigger is None:
        brake = pd.Series(1.0, index=net_rt.index)
    else:
        brake = dd_brake_multiplier(net_rt, cfg.dd_trigger, cfg.dd_release, cfg.brake_factor)
    net_risk = (net_rt * brake).dropna()
    return {"net": net_risk, "net_retargeted": net_rt, "brake_mult": brake}


# ---------------------------------------------------------------------------------------------
# Metrics (shared with the run script / report)
# ---------------------------------------------------------------------------------------------
def max_dd(net: pd.Series) -> float:
    """Max drawdown (negative fraction) of the compounded equity curve over the whole series."""
    eq = (1.0 + net).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def window_dd(net: pd.Series, lo, hi=None) -> float:
    """Max drawdown over [lo, hi) of an equity curve RESET to 1.0 at lo (window-local DD)."""
    s = net[net.index >= lo]
    if hi is not None:
        s = s[s.index < hi]
    if len(s) == 0:
        return 0.0
    eq = (1.0 + s).cumprod()
    return float((eq / eq.cummax() - 1.0).min())
