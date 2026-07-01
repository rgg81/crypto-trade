"""Smoke + leak-safety tests for the iter-012 broad-universe factor probe.

These are SELF-CONTAINED: they build a tiny synthetic price panel (no network, no data_broad/) and
verify the load-bearing invariants of the broad factor stack — factor signals are sector-neutral,
past-only (future-bar corruption never moves a pre-cut signal), the cross-sectional z-score is
inf-robust, and the ingest ticker/schema helpers behave. The full ~500-name run is a probe script,
not a unit test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_TRADFI = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
if str(_TRADFI) not in sys.path:
    sys.path.insert(0, str(_TRADFI))

import ingest_yahoo_broad as iyb  # noqa: E402
import iter_012_broad as ib  # noqa: E402

_SECTORS = ("Tech", "Fin", "Health")


def _synth(n_days: int = 900, n_names: int = 12, seed: int = 0):
    """Tiny synthetic coins dict + sector map with real cross-sectional drift/size dispersion."""
    rng = np.random.default_rng(seed)
    idx_ms = (pd.Timestamp("2015-01-01").value // 10**6) + np.arange(n_days) * 86_400_000
    tickers = [f"T{i:02d}" for i in range(n_names)]
    coins = {}
    for i, t in enumerate(tickers):
        rets = rng.normal(0.0004 * (i - n_names / 2), 0.02, n_days)  # drift dispersion
        close = 100.0 * np.exp(np.cumsum(rets))
        openp = close * (1.0 + rng.normal(0.0, 0.001, n_days))
        vol = rng.uniform(1e6, 1e7, n_days) * (i + 1)  # size dispersion
        df = pd.DataFrame(
            {
                "open": openp,
                "high": np.maximum(openp, close) * 1.01,
                "low": np.minimum(openp, close) * 0.99,
                "close": close,
                "volume": vol,
            },
            index=idx_ms,
        )
        df.index.name = "open_time"
        coins[t] = df
    sectors = {t: _SECTORS[i % len(_SECTORS)] for i, t in enumerate(tickers)}
    return coins, tickers, sectors


def test_import_and_factor_set():
    assert ib.FACTORS == ("MOM_12_1", "LTR_3y1y", "BAB_lowbeta", "LOWVOL", "SIZE", "STREV_1m")


def test_binance_to_broad_mapping():
    assert ib.binance_to_broad("AAPLUSDT") == "AAPL"
    assert ib.binance_to_broad("BRKBUSDT") == "BRK-B"
    assert ib.binance_to_broad("PAYPUSDT") == "PYPL"
    # ingest module must agree with the probe module on the mapping.
    assert iyb.binance_to_broad("BRKBUSDT") == "BRK-B"


def test_xs_z_is_inf_robust():
    x = pd.DataFrame(
        {"a": [1.0, np.inf, 3.0], "b": [2.0, 2.0, np.nan], "c": [3.0, 4.0, 5.0]},
        index=pd.date_range("2020-01-01", periods=3),
    )
    z = ib._xs_z(x)
    assert np.isfinite(z.to_numpy()[~np.isnan(z.to_numpy())]).all()  # no inf survives
    assert (z.abs() <= 3.0 + 1e-9).to_numpy()[~np.isnan(z.to_numpy())].all()  # winsorized


def test_build_signals_are_sector_neutral():
    coins, tickers, sectors = _synth()
    pn = ib.make_panel(coins, tickers)
    signals = ib.build_signals(pn, sectors, tickers)
    buckets: dict[str, list[str]] = {}
    for t in tickers:
        buckets.setdefault(sectors[t], []).append(t)
    for name, sig in signals.items():
        active = sig.abs().sum(axis=1) > 1e-9
        for cols in buckets.values():
            resid = sig.loc[active, cols].sum(axis=1).abs().max()
            assert resid < 1e-9, f"{name} not sector-neutral (resid={resid:.1e})"


def test_build_signals_future_bar_no_leak():
    """Corrupt close/volume/ret_fwd AFTER a cut; every pre-cut factor signal is bit-identical."""
    coins, tickers, sectors = _synth(seed=3)
    pn = ib.make_panel(coins, tickers)
    sig0 = ib.build_signals(pn, sectors, tickers)
    cut = pn["close"].index[len(pn["close"]) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    m = pn_c["close"].index >= cut
    pn_c["close"].loc[m] *= -7.0
    pn_c["volume"].loc[m] *= 3.0
    pn_c["ret_fwd"].loc[m] += 5.0
    sig1 = ib.build_signals(pn_c, sectors, tickers)
    for name in ib.FACTORS:
        a = sig0[name].loc[sig0[name].index < cut].fillna(0.0).to_numpy()
        b = sig1[name].loc[sig1[name].index < cut].fillna(0.0).to_numpy()
        assert np.allclose(a, b, atol=1e-12), f"{name} leaks future info"


def test_standalone_net_runs_and_is_finite():
    coins, tickers, sectors = _synth()
    pn = ib.make_panel(coins, tickers)
    signals = ib.build_signals(pn, sectors, tickers)
    net = ib.standalone_net(signals["MOM_12_1"], pn["ret_fwd"])
    assert len(net) > 100
    assert np.isfinite(net.to_numpy()).all()


def test_select_positive_lowcorr_filters_and_decorrelates():
    idx = pd.bdate_range("2016-01-04", periods=500)
    rng = np.random.default_rng(1)
    a = pd.Series(0.0012 + rng.normal(0, 0.005, len(idx)), index=idx)
    b = a * 0.98 + rng.normal(0, 0.0003, len(idx))  # ~0.99 corr to A (redundant)
    c = pd.Series(0.0010 + rng.normal(0, 0.005, len(idx)), index=idx)  # independent, positive
    neg = pd.Series(-0.0015 + rng.normal(0, 0.005, len(idx)), index=idx)  # negative-EV
    sel = ib.select_positive_lowcorr({"A": a, "B": b, "C": c, "NEG": neg})
    assert "NEG" not in sel  # negative-EV dropped
    assert "C" in sel  # independent positive kept
    assert ("A" in sel) ^ ("B" in sel)  # only one of the redundant pair kept


def test_to_daily_frame_schema():
    idx = pd.date_range("2021-01-04", periods=5, freq="D")
    raw = pd.DataFrame(
        {"Open": 10.0, "High": 11.0, "Low": 9.0, "Close": 10.5, "Volume": 1e6}, index=idx
    )
    out = iyb._to_daily_frame(raw)
    assert list(out.columns) == ["open_time", "open", "high", "low", "close", "volume"]
    assert out["open_time"].dtype == np.int64
    # UTC-midnight epoch-ms for 2021-01-04
    assert int(out["open_time"].iloc[0]) == int(pd.Timestamp("2021-01-04", tz="UTC").value // 10**6)
