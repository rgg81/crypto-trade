"""Regression tests for the iter-007 drawdown-brake kill-switch (the load-bearing R-layer).

The brake guards real capital, so it ships with its own tests (the foundation suite does not cover
it): past-only causality, down-only scaling, the floor=0 self-lock guard, the apply identity, the
arm→deep-drawdown→V-recovery re-arm (the de-lever-at-the-bottom defense), and the bear-blindness of
the IS-only calibration. All synthetic — no data load required.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_METALS = _ROOT / "analysis" / "portfolio" / "metals"
sys.path.insert(0, str(_METALS))

import iter_007_allweather as aw  # noqa: E402
import iter_007_calibrate as cal  # noqa: E402

_IDX = pd.date_range("2020-01-01", periods=40, freq="8h")


def _series(vals) -> pd.Series:
    return pd.Series(list(vals), index=pd.date_range("2020-01-01", periods=len(vals), freq="8h"))


def test_brake_down_only_and_two_state():
    """k ∈ {floor, 1.0} only — the overlay can only REDUCE exposure, never lever up."""
    rng = np.random.default_rng(0)
    idx = pd.date_range("2020-01-01", periods=400, freq="8h")
    net0 = pd.Series(rng.normal(0, 0.03, 400), index=idx)
    k = aw.dd_brake_scalar(net0, 0.15, 0.075, 0.25)
    assert set(np.unique(k.to_numpy())).issubset({0.25, 1.0})
    assert (k <= 1.0).all() and (k >= 0.25).all()


def test_apply_brake_is_elementwise_product():
    """apply_brake(net0, k) == k·net0 exactly (parity: one scalar on the whole book)."""
    net0 = _series([0.01, -0.02, 0.03, -0.01])
    k = _series([1.0, 0.25, 0.25, 1.0])
    pd.testing.assert_series_equal(aw.apply_brake(net0, k), net0 * k)


def test_brake_floor_zero_raises():
    """floor=0 is a self-locking full halt (frozen equity never re-arms) — must raise, not run."""
    with pytest.raises(ValueError, match="floor"):
        aw.dd_brake_scalar(_series([0.0, -0.5, 0.0]), 0.15, 0.075, 0.0)


def test_brake_is_past_only():
    """Causality: corrupting net0 AFTER a cutoff cannot change any k before it (past-only)."""
    rng = np.random.default_rng(1)
    idx = pd.date_range("2020-01-01", periods=300, freq="8h")
    net0 = pd.Series(rng.normal(0, 0.04, 300), index=idx)
    k0 = aw.dd_brake_scalar(net0, 0.15, 0.075, 0.25)
    cut = 200
    net0c = net0.copy()
    net0c.iloc[cut:] = net0c.iloc[cut:].to_numpy() * -9.0 + 3.0  # arbitrary future corruption
    k1 = aw.dd_brake_scalar(net0c, 0.15, 0.075, 0.25)
    pd.testing.assert_series_equal(k0.iloc[:cut], k1.iloc[:cut])


def test_brake_arms_then_rearms_on_v_recovery():
    """De-lever-at-the-bottom defense: a deep drawdown ARMS the brake (k→floor), and a V-recovery
    RE-ARMS it (k→1.0) once the drawdown climbs above −D_rearm — it does NOT lock in the loss."""
    net0 = _series([-0.06] * 6 + [0.10] * 20)  # plunge past −15%, then a strong recovery
    k = aw.dd_brake_scalar(net0, 0.15, 0.075, 0.25)
    assert (k == 1.0).iloc[:3].all()  # starts un-armed (full exposure)
    assert (k == 0.25).any()  # the deep drawdown ARMED the brake
    armed_idx = np.where(k.to_numpy() == 0.25)[0]
    assert (k.iloc[armed_idx[-1] + 1 :] == 1.0).any()  # RE-ARMED after the recovery
    assert k.iloc[-1] == 1.0  # fully re-armed by the end of the V (no lock-in)


def test_calibration_is_bear_blind():
    """The IS-only calibration must refuse to load bear data (the discipline guard)."""
    with pytest.raises(AssertionError, match="bear"):
        cal._l2_is_net(Path("/tmp/data_bear/whatever"))


def test_calibration_thresholds_in_sane_range():
    """If IS data is present, the DERIVED thresholds are a sane IS-tail depth (worst quintile)."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        pytest.skip("metals data not ingested")
    c = cal.calibrate()
    assert 0.05 < c["d_trip"] < 0.30  # a real drawdown-tail depth, not noise / not absurd
    assert abs(c["d_rearm"] - c["d_trip"] / 2) < 1e-9  # hysteresis = half the trip depth
    assert abs(c["pct_bars_armed"] - cal.ARM_QUANTILE) < 0.03  # armed on ~the worst quintile
