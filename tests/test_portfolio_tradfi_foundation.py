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


import ingest_dukascopy_stocks as ids  # noqa: E402


def test_resample_daily_aggregates_intraday_ohlc():
    # two UTC days of hourly bars; daily OHLC = first open / max high / min low / last close.
    idx = pd.date_range("2021-03-01 14:00", periods=13, freq="h", tz="UTC")  # spans 2 sessions
    h1 = pd.DataFrame(
        {
            "open": np.arange(1, 14, dtype=float),
            "high": np.arange(1, 14, dtype=float) + 0.5,
            "low": np.arange(1, 14, dtype=float) - 0.5,
            "close": np.arange(1, 14, dtype=float) + 0.1,
            "volume": 1.0,
        },
        index=idx,
    )
    daily = ids.resample_daily(h1)
    assert list(daily.columns) == ["open_time", "open", "high", "low", "close", "volume"]
    # day 1 (2021-03-01): bars 14:00..23:00 -> open=row0.open, high=max, low=min, close=last
    d0 = daily.iloc[0]
    assert d0["open"] == 1.0
    assert d0["high"] == h1.loc["2021-03-01"]["high"].max()
    assert d0["low"] == h1.loc["2021-03-01"]["low"].min()
    # open_time is midnight-UTC epoch ms of that calendar day
    assert d0["open_time"] == int(pd.Timestamp("2021-03-01", tz="UTC").value // 1_000_000)


def test_resample_daily_drops_weekend_and_flat_holiday_bars():
    """TRADING-DAY filter: weekends AND flat (high==low) holiday carries are DROPPED.

    Equities trade ~252 days/yr; the Dukascopy stock-CFD feed pads closed days with a flat
    carried quote. resample_daily must drop them so shift(252)==12 trading months stays valid.
    Each clause is exercised independently: Sat/Sun carry a NON-flat range (only the weekday
    clause can drop them) and a weekday holiday is FLAT (only the high==low clause can drop it).
    """
    spec = [
        ("2021-03-05", "trading"),  # Fri -> kept
        ("2021-03-06", "weekend"),  # Sat, NON-flat -> dropped by weekday clause
        ("2021-03-07", "weekend"),  # Sun, NON-flat -> dropped by weekday clause
        ("2021-03-08", "trading"),  # Mon -> kept
        ("2021-03-09", "holiday"),  # Tue, FLAT carry -> dropped by high==low clause
        ("2021-03-10", "trading"),  # Wed -> kept
    ]
    frames = []
    for date, kind in spec:
        hrs = pd.date_range(f"{date} 14:00", periods=4, freq="h", tz="UTC")
        if kind == "holiday":  # flat carried quote: open==high==low==close
            op = hi = lo = cl = np.full(4, 50.0)
        else:  # trading + weekend both get a real intraday range (high != low)
            base = 10.0 if kind == "trading" else 20.0
            op = base + np.arange(4, dtype=float)
            hi, lo, cl = op + 0.5, op - 0.5, op + 0.1
        frames.append(
            pd.DataFrame({"open": op, "high": hi, "low": lo, "close": cl, "volume": 1.0}, index=hrs)
        )
    daily = ids.resample_daily(pd.concat(frames))
    kept = [str(d.date()) for d in pd.to_datetime(daily["open_time"], unit="ms")]
    assert kept == [
        "2021-03-05",
        "2021-03-08",
        "2021-03-10",
    ]  # 3 trading days; 2 weekend + 1 holiday dropped
    assert len(daily) == 3


def test_instruments_map_has_core_names():
    for sym in ("AAPLUSDT", "MSFTUSDT", "TSLAUSDT", "JPMUSDT"):
        assert sym in ids.INSTRUMENTS
        duka_id, start = ids.INSTRUMENTS[sym]
        assert isinstance(duka_id, str) and isinstance(start, str)


import iter_001_xsmom as i1  # noqa: E402


def test_iter001_build_is_dollar_neutral_and_leak_safe():
    coins = {}
    rng = np.random.default_rng(11)
    start = int(pd.Timestamp("2018-01-01").value // 1_000_000)
    ot = start + np.arange(500) * 86_400_000
    for i in range(8):
        close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500)))
        opn = np.concatenate([[close[0]], close[:-1]])
        coins[f"S{i}USDT"] = pd.DataFrame(
            {
                "open": opn,
                "high": np.maximum(opn, close),
                "low": np.minimum(opn, close),
                "close": close,
                "volume": 1.0,
            },
            index=pd.Index(ot, name="open_time"),
        )
    net, w = i1.build(coins)
    assert isinstance(net, pd.Series) and len(net) > 200
    # pre-vol-target lagged weights are dollar-neutral on active rows
    active = w[w.abs().sum(axis=1) > 0]
    assert np.allclose(active.sum(axis=1).to_numpy(), 0.0, atol=1e-9)


def test_production_xsmom_future_bar_no_leak():
    """The REAL production signal (dollar_neutralize(mom/rvol)) must be future-bar leak-safe.

    Corrupting the raw signal + forward returns AFTER a cutoff must not change net/weights
    before it. Mirrors test_future_bar_corruption_does_not_change_past_net but against the
    production i1.xsmom_raw operation order, not the local _xsmom_raw proxy.
    """
    pn = _make_panel(seed=22)
    raw = i1.xsmom_raw(pn)
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


def test_production_xsmom_same_bar_close_no_leak():
    """The REAL production signal (dollar_neutralize(mom/rvol)) must be same-bar leak-safe too."""
    pn = _make_panel(seed=21)
    raw = i1.xsmom_raw(pn)
    net0, _ = ct.net_from_raw(raw, pn["ret_fwd"])
    t = pn["close"].index[300]
    pn2 = {k: v.copy() for k, v in pn.items()}
    pn2["close"].loc[t] *= 1.5
    raw2 = i1.xsmom_raw(pn2)
    net2, _ = ct.net_from_raw(raw2, pn2["ret_fwd"])
    common = net0.index.intersection(net2.index)
    upto_t = common[common <= t]
    pd.testing.assert_series_equal(net0.loc[upto_t], net2.loc[upto_t])


import iter_002_sector_rel as i2  # noqa: E402


def test_iter002_build_is_dollar_and_sector_neutral_and_leak_safe():
    """iter-002 build() must produce a lagged weight book that is BOTH dollar-neutral AND
    per-sector-neutral (each sector's active weights sum ~0) — sector-neutrality is the whole
    point of the one change, and it implies dollar-neutrality by construction (no extra
    dollar_neutralize call). Uses real SECTOR_MAP tickers spanning a multi-name sector (Semi),
    a second multi-name sector (Tech) and a SINGLETON sector (Health=LLY -> forced to 0)."""
    syms = [
        "NVDAUSDT",
        "AMDUSDT",
        "MUUSDT",  # Semi (multi-name)
        "AAPLUSDT",
        "MSFTUSDT",
        "ORCLUSDT",  # Tech (multi-name)  (ORCL absent on disk but valid in SECTOR_MAP)
        "LLYUSDT",  # Health (singleton -> 0 weight)
    ]
    rng = np.random.default_rng(13)
    start = int(pd.Timestamp("2018-01-01").value // 1_000_000)
    ot = start + np.arange(500) * 86_400_000
    coins = {}
    for s in syms:
        close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500)))
        opn = np.concatenate([[close[0]], close[:-1]])
        coins[s] = pd.DataFrame(
            {
                "open": opn,
                "high": np.maximum(opn, close),
                "low": np.minimum(opn, close),
                "close": close,
                "volume": 1.0,
            },
            index=pd.Index(ot, name="open_time"),
        )
    net, w = i2.build(coins)
    assert isinstance(net, pd.Series) and len(net) > 200
    active = w[w.abs().sum(axis=1) > 0]
    assert len(active) > 100
    # (1) whole book is dollar-neutral on every active row
    assert np.allclose(active.sum(axis=1).to_numpy(), 0.0, atol=1e-9)
    # (2) EACH multi-name sector's weights sum ~0 on active rows (the load-bearing property)
    sectors: dict[str, list[str]] = {}
    for c in w.columns:
        sectors.setdefault(ut.SECTOR_MAP[c], []).append(c)
    for sec, cols in sectors.items():
        block_sum = active[cols].sum(axis=1)
        assert np.allclose(block_sum.to_numpy(), 0.0, atol=1e-9), f"{sec} not sector-neutral"
    # (3) singleton sector (Health=LLY) takes ZERO weight on every active bar (forced to 0
    # by demeaning against itself; the lone leading NaN is the net_from_raw .shift(1) warm-up)
    assert np.allclose(active["LLYUSDT"].to_numpy(), 0.0, atol=1e-12)


def test_iter002_sector_rel_raw_future_bar_no_leak():
    """The production iter-002 signal (sector_neutralize(mom/rvol)) must be future-bar leak-safe:
    corrupting raw + forward returns AFTER a cutoff must not change net/weights before it."""
    pn = _make_panel(seed=24)
    # Give the synthetic columns a real multi-name sector map (S0..S5 -> A/A/A/B/B/B).
    smap = {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw = i2.sector_rel_raw(pn)
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
    finally:
        ut.SECTOR_MAP = orig


def test_perf_line_hides_oos_by_default():
    """perf_line without reveal_oos must leak NO OOS info: no OOS_Sharpe, and maxDD/netTot
    computed over IS-only (not the full series that extends past OOS_CUTOFF)."""
    idx = pd.date_range("2024-06-01", periods=500, freq="B")  # crosses 2025-03-24
    net = pd.Series(0.001, index=idx)  # steady positive so IS total < full total
    line = ct.perf_line("x", net)
    assert "OOS_Sharpe" not in line
    is_net = net[net.index < ct.OOS_CUTOFF]
    is_tot = ((1 + is_net).cumprod().iloc[-1] - 1) * 100
    full_tot = ((1 + net).cumprod().iloc[-1] - 1) * 100
    assert is_tot < full_tot  # proves OOS rows are excluded from the IS total
    assert f"netTot={is_tot:+.0f}%" in line
    assert "OOS_Sharpe" in ct.perf_line("x", net, reveal_oos=True)
