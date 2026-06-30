from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
_TRADFI = _ROOT / "analysis" / "portfolio" / "tradfi"
sys.path.insert(0, str(_TRADFI))

import core_tradfi as ct  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402


def _exinfo(symbols_types):
    """Minimal exchangeInfo dict: symbols_types = [(symbol, contractType), ...]."""
    return {"symbols": [{"symbol": s, "contractType": ctype} for s, ctype in symbols_types]}


def test_classify_keeps_single_company_stocks():
    info = _exinfo(
        [
            ("AAPLUSDT", "TRADIFI_PERPETUAL"),
            ("JPMUSDT", "TRADIFI_PERPETUAL"),
            ("BTCUSDT", "PERPETUAL"),  # crypto -> drop (not TRADIFI)
            ("SPYUSDT", "TRADIFI_PERPETUAL"),  # ETF -> drop
            ("XAUUSDT", "TRADIFI_PERPETUAL"),  # metal -> drop
            ("NATGASUSDT", "TRADIFI_PERPETUAL"),  # commodity -> drop
            ("OPENAIUSDT", "TRADIFI_PERPETUAL"),  # private synthetic -> drop
        ]
    )
    out = ut.classify_tradfi_stocks(info)
    assert out == ["AAPLUSDT", "JPMUSDT"]


def test_every_known_stock_has_a_sector():
    # Spot-check core names are mapped; SECTOR_MAP must cover its own keys.
    for sym in ("AAPLUSDT", "JPMUSDT", "TSLAUSDT", "AMZNUSDT", "NVDAUSDT"):
        assert sym in ut.SECTOR_MAP, f"{sym} missing from SECTOR_MAP"
    assert all(isinstance(v, str) and v for v in ut.SECTOR_MAP.values())


def _make_panel(n=400, k=6, seed=0):
    """Random-walk daily OHLC panels for k assets — the shape panels() returns."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")  # business days
    cols = [f"S{i}" for i in range(k)]
    close = pd.DataFrame(
        {c: 100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))) for c in cols}, index=idx
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


def _xsmom_raw(pn):
    """Leak-safe cross-sectional momentum (12-1m), inverse-vol scaled — iter-001 shape."""
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0  # 12m-1m, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    demeaned = mom.sub(mom.mean(axis=1), axis=0)  # cross-sectional demean
    return demeaned / rvol


def test_daily_constants():
    assert ct.CANDLES_PER_YEAR == 252
    assert ct.OOS_CUTOFF == pd.Timestamp("2025-03-24")


def test_net_from_raw_dollar_accounting_and_shape():
    pn = _make_panel(seed=2)
    raw = _xsmom_raw(pn)
    net, w = ct.net_from_raw(raw, pn["ret_fwd"])
    assert isinstance(net, pd.Series) and len(net) > 200
    # lagged weights gross-normalize to ~1 on rows that have any signal
    gsum = w.abs().sum(axis=1)
    active = gsum[gsum > 0]
    assert np.allclose(active.to_numpy(), 1.0, atol=1e-9)


def test_future_bar_corruption_does_not_change_past_net():
    """Corrupting raw signal + forward returns AFTER a cutoff must not change net before it."""
    pn = _make_panel(seed=3)
    raw = _xsmom_raw(pn)
    net0, w0 = ct.net_from_raw(raw, pn["ret_fwd"])
    cut = net0.index[len(net0) // 2]
    raw_c, ret_c = raw.copy(), pn["ret_fwd"].copy()
    raw_c.loc[raw_c.index >= cut] *= -7.0
    ret_c.loc[ret_c.index >= cut] += 5.0
    net1, w1 = ct.net_from_raw(raw_c, ret_c)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    pd.testing.assert_series_equal(net0.loc[common], net1.loc[common])
    pd.testing.assert_frame_equal(w0[w0.index < cut], w1[w1.index < cut])


def test_same_bar_close_cannot_affect_its_own_return():
    """SAME-BAR leak guard: corrupting close[t] (and only t) must not change net[t] or net[<t].

    This is the leak class the standard future-only test misses (it cost the metals track a
    withdrawn iteration). A leak-safe signal decided at close[t] is applied via .shift(1) to
    ret_fwd[t]=open[t+1]/open[t]; the realized return on bar t must not depend on close[t].
    """
    pn = _make_panel(seed=4)
    raw = _xsmom_raw(pn)
    net0, _ = ct.net_from_raw(raw, pn["ret_fwd"])
    # Corrupt a single bar's CLOSE deep in the middle, rebuild the signal from it.
    t = pn["close"].index[300]
    pn2 = {k: v.copy() for k, v in pn.items()}
    pn2["close"].loc[t] *= 1.5  # only close[t] perturbed; open/ret_fwd untouched
    raw2 = _xsmom_raw(pn2)
    net2, _ = ct.net_from_raw(raw2, pn2["ret_fwd"])
    # net on bar t (return open[t]->open[t+1], position from close[t-1]) is independent of close[t].
    common = net0.index.intersection(net2.index)
    upto_t = common[common <= t]
    pd.testing.assert_series_equal(net0.loc[upto_t], net2.loc[upto_t])


def test_dollar_neutral_rows_sum_to_zero():
    pn = _make_panel(seed=5)
    raw = _xsmom_raw(pn).dropna(how="all")
    dn = nz.dollar_neutralize(raw)
    rs = dn.sum(axis=1).dropna()
    assert np.allclose(rs.to_numpy(), 0.0, atol=1e-9)


def test_sector_neutral_each_bucket_sums_to_zero():
    pn = _make_panel(seed=6, k=6)
    raw = _xsmom_raw(pn).dropna(how="all")
    smap = {"S0": "A", "S1": "A", "S2": "A", "S3": "B", "S4": "B", "S5": "B"}
    sn = nz.sector_neutralize(raw, smap)
    for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
        rs = sn[bucket].sum(axis=1).dropna()
        assert np.allclose(rs.to_numpy(), 0.0, atol=1e-9)


def test_rolling_beta_is_past_only():
    pn = _make_panel(seed=7)
    ret = pn["close"].pct_change()
    mkt = ret.mean(axis=1)
    betas = nz.rolling_beta(ret, mkt, win=63)
    # corrupting the tail of returns must not change early betas
    ret_c = ret.copy()
    cut = ret.index[250]
    ret_c.loc[ret_c.index >= cut] *= 9.0
    betas_c = nz.rolling_beta(ret_c, mkt, win=63)
    early = betas.index[betas.index < cut]
    pd.testing.assert_frame_equal(betas.loc[early], betas_c.loc[early])
