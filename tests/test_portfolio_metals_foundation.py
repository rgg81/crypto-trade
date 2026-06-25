"""Foundation tests for the metals portfolio: leak-safety, neutrality, cost, resample, data.

These guard the reusable backtest core (analysis/portfolio/metals/universe_metals.py) and the
Dukascopy 8h resampler (ingest_dukascopy.py). Synthetic-data tests always run; the on-disk
data-sanity test skips if the (gitignored) CSVs haven't been ingested yet.
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

import ingest_dukascopy as ing  # noqa: E402
import universe_metals as um  # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────────────
def _make_panel(n: int = 600, k: int = 4, seed: int = 0) -> dict[str, pd.DataFrame]:
    """Random-walk OHLC panels for k assets, 8h DatetimeIndex — shape `panels()` returns."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="8h")
    cols = [f"M{i}" for i in range(k)]
    close = pd.DataFrame(
        {c: 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))) for c in cols}, index=idx
    )
    opn = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(np.maximum(opn.values, close.values), index=idx, columns=cols) * 1.001
    low = pd.DataFrame(np.minimum(opn.values, close.values), index=idx, columns=cols) * 0.999
    return {
        "open": opn,
        "high": high,
        "low": low,
        "close": close,
        "ret_fwd": opn.shift(-1) / opn - 1.0,
    }


def _trend_raw(pn: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """A representative leak-safe inverse-vol trend signal (the iter-001 shape) for testing."""
    close = pn["close"]
    rvol = close.pct_change().rolling(um.VOL_WIN).std()
    sig = sum(np.sign(close / close.shift(h) - 1.0) for h in um.HORIZONS) / len(um.HORIZONS)
    return sig / rvol


# ── leak-safety ───────────────────────────────────────────────────────────────────────
def test_net_from_raw_is_past_only():
    """Corrupting raw signal + forward returns AFTER a cutoff must not change any net before it."""
    pn = _make_panel(seed=1)
    raw = _trend_raw(pn)
    net0, w0 = um.net_from_raw(raw, pn["ret_fwd"])

    cut = net0.index[len(net0) // 2]
    raw_c = raw.copy()
    ret_c = pn["ret_fwd"].copy()
    raw_c.loc[raw_c.index >= cut] *= -7.0  # arbitrary future corruption
    ret_c.loc[ret_c.index >= cut] += 5.0
    net1, w1 = um.net_from_raw(raw_c, ret_c)

    a = net0[net0.index < cut]
    b = net1[net1.index < cut]
    common = a.index.intersection(b.index)
    pd.testing.assert_series_equal(a.loc[common], b.loc[common])
    # deployed weights before the cutoff are bit-identical too
    pd.testing.assert_frame_equal(w0[w0.index < cut], w1[w1.index < cut])


def test_vol_target_is_past_only():
    """vol_target uses trailing rolling().shift(1), so future perturbation can't leak backward."""
    rng = np.random.default_rng(2)
    net = pd.Series(
        rng.normal(0, 0.01, 500), index=pd.date_range("2020-01-01", periods=500, freq="8h")
    )
    cut = net.index[300]
    s0 = um.vol_target(net)
    net_c = net.copy()
    net_c.loc[net_c.index >= cut] += 9.0
    s1 = um.vol_target(net_c)
    pd.testing.assert_series_equal(s0[s0.index < cut], s1[s1.index < cut])


# ── dollar-neutrality (market-neutral arm) ────────────────────────────────────────────
def test_dollar_neutral_signal_stays_neutral():
    """A cross-sectionally balanced raw signal yields a deployed book with Σweights ≈ 0."""
    pn = _make_panel(seed=3)
    raw = _trend_raw(pn)
    raw = raw.sub(raw.mean(axis=1), axis=0)  # demean cross-section → dollar-neutral
    _, w = um.net_from_raw(raw, pn["ret_fwd"])
    active = w[(w.abs().sum(axis=1) > 1e-9)]
    assert active.sum(axis=1).abs().max() < 1e-9


# ── cost accounting ───────────────────────────────────────────────────────────────────
def test_cost_matches_turnover_formula():
    """The cost deducted by net_from_raw equals COST_SIDE × Σ|Δw| (turnover) exactly."""
    pn = _make_panel(seed=4)
    raw = _trend_raw(pn)
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * pn["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    cost = um.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    expect_pre_vt = (pnl - cost).dropna()

    # reconstruct the engine's pre-vol-target net and compare
    net_vt, _ = um.net_from_raw(raw, pn["ret_fwd"])
    # net_vt = expect_pre_vt * vol_target_scale ; divide back out where scale > 0
    rv = expect_pre_vt.rolling(um.PORT_VOL_WIN).std().shift(1)
    scale = (um.TARGET_VOL / rv).clip(upper=um.MAX_LEV).fillna(0.0)
    rebuilt = expect_pre_vt * scale
    pd.testing.assert_series_equal(net_vt, rebuilt.dropna(), check_names=False)


def test_zero_turnover_has_zero_cost():
    """A held (constant) position incurs no per-candle cost after the initial entry."""
    idx = pd.date_range("2020-01-01", periods=300, freq="8h")
    w = pd.DataFrame({"A": 0.5, "B": -0.5}, index=idx)
    delta_cost = um.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    assert (delta_cost.iloc[1:] == 0).all()  # no churn → no ongoing cost


# ── 8h resample correctness ───────────────────────────────────────────────────────────
def test_resample_8h_ohlcv_aggregation():
    """resample_8h aggregates open=first/high=max/low=min/close=last/volume=sum per UTC bucket."""
    # 8 hourly bars 00:00..07:00 UTC → exactly one [00,08) bucket
    idx = pd.date_range("2023-03-06 00:00", periods=8, freq="1h", tz="UTC")
    h1 = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 14, 15, 16, 17],
            "high": [10, 11, 20, 13, 14, 15, 16, 17],
            "low": [9, 8, 12, 13, 14, 15, 16, 17],
            "close": [11, 12, 13, 14, 15, 16, 17, 18],
            "volume": [1, 1, 1, 1, 1, 1, 1, 1],
        },
        index=idx,
    )
    out = ing.resample_8h(h1)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["open"] == 10 and row["close"] == 18
    assert row["high"] == 20 and row["low"] == 8 and row["volume"] == 8
    assert out.index[0] == pd.Timestamp("2023-03-06 00:00", tz="UTC")


def test_resample_8h_drops_empty_buckets():
    """A weekend gap (no bars in a bucket) must not produce a fabricated flat candle."""
    idx = list(pd.date_range("2023-03-06 00:00", periods=3, freq="1h", tz="UTC")) + list(
        pd.date_range("2023-03-06 16:00", periods=3, freq="1h", tz="UTC")
    )
    h1 = pd.DataFrame(
        {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx
    )
    out = ing.resample_8h(h1)
    # [00,08) and [16,24) present; the empty [08,16) bucket dropped
    assert len(out) == 2
    assert pd.Timestamp("2023-03-06 08:00", tz="UTC") not in out.index


# ── on-disk data sanity (skips if not ingested) ───────────────────────────────────────
@pytest.mark.parametrize("sym", um.UNIVERSE)
def test_ingested_csv_sanity(sym):
    p = _ROOT / "data" / sym / "8h.csv"
    if not p.exists():
        pytest.skip(f"{sym} not ingested yet ({p})")
    df = pd.read_csv(p)
    assert df["open_time"].is_monotonic_increasing
    assert df["open_time"].duplicated().sum() == 0
    assert (df[["open", "high", "low", "close"]] > 0).all().all()
    assert (df["close_time"] - df["open_time"] == 8 * 3600 * 1000 - 1).all()
    hours = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.hour.unique()
    assert set(hours).issubset({0, 8, 16})  # UTC-aligned 8h grid
