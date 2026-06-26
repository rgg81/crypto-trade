"""Tests for iter-012 — the CFTC COT positioning ensemble sleeve (the champion).

  * the COT sleeve is restricted to GOLD/SILVER (iter-004 robust subset; full-4 was OOS-falsified);
  * adding the COT dose IMPROVES the IS Sharpe over no-COT (identical position-level accounting);
  * the COT-ensemble net is leak-free w.r.t. future PRICES (release-timing lag is iter-004's).
The IS/leak claims load real data + COT; they skip if the metals CSVs aren't ingested.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "analysis" / "portfolio" / "metals"))

import iter_010_breadth_accel as i10  # noqa: E402
import iter_012_cot_ensemble as i12  # noqa: E402
import universe_metals as um  # noqa: E402


def test_cot_is_gold_silver_only():
    """The COT sleeve must be gold/silver only — full-4 COT was OOS-falsified (a dead-path)."""
    assert i12.COT_COLS == ("XAUUSDT", "XAGUSDT")
    assert i12.CHAMP12["cot_w"] > 0


def test_cot_dose_improves_is():
    """On real metals, adding the COT dose lifts IS Sharpe vs cot_w=0 (same accounting)."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    cm = um.load_metals()
    is_lo, is_hi = "2000-01-01", str(um.OOS_CUTOFF.date())
    sr0 = i10._seg(i12.desk_net(cm, cot_w=0.0), is_lo, is_hi)["sharpe"]
    sr1 = i10._seg(i12.desk_net(cm, cot_w=i12.CHAMP12["cot_w"]), is_lo, is_hi)["sharpe"]
    assert sr1 > sr0 + 0.03  # the ensemble materially lifts IS


def test_cot_ensemble_net_is_price_leak_free():
    """Corrupting future PRICES leaves the past COT-ensemble net bit-identical (no price leak).

    (The COT report RELEASE-timing leak-safety is the +6d lag in iter_004_cot.align_cot_to_grid,
    triple-verified there; this guards the price path of the ensemble.)
    """
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    coins = um.load_metals()
    idx = max((d for d in coins.values()), key=len).index
    cut = int(idx[len(idx) - 200])
    n0 = i12.desk_net(coins)
    cc = {}
    for s, d in coins.items():
        d = d.copy()
        m = d.index >= cut
        for c in ("open", "high", "low", "close"):
            d.loc[m, c] = d.loc[m, c].to_numpy() * 2.5 + 11.0
        cc[s] = d
    n1 = i12.desk_net(cc)
    bound = pd.Timestamp(int(idx[len(idx) - 201]), unit="ms")
    common = n0.index.intersection(n1.index)
    common = common[common < bound]
    assert len(common) > 100
    assert float((n0.loc[common] - n1.loc[common]).abs().max()) < 1e-9
    _ = np  # keep import used


def test_cot_peek_earlier_does_not_help():
    """PEEK-EARLIER falsifier: applying the COT a week BEFORE its public release (a deliberate
    look-ahead) must NOT materially beat the proper +6d-lagged IS. If a too-small lag were leaking
    future info, peeking would lift the Sharpe — it must not (the iter-004 falsifier, in CI).
    """
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    cm = um.load_metals()
    is_lo, is_hi = "2000-01-01", str(um.OOS_CUTOFF.date())
    proper = i10._seg(i12.desk_net(cm), is_lo, is_hi)["sharpe"]  # +6d release lag (CHAMP12 default)
    peek = i10._seg(i12.desk_net(cm, cot_lag=i12.CHAMP12["cot_lag"] - 7), is_lo, is_hi)["sharpe"]
    assert peek <= proper + 0.10  # peeking a week early gives no exploitable edge -> not a leak
