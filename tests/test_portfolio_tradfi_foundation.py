from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

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


import iter_003_hysteresis as i3  # noqa: E402


def test_iter003_delta0_reproduces_iter002_bit_identical():
    """delta=0 must reproduce iter-002 net_from_raw EXACTLY (band identity, renorm no-op).

    The pre-registered identity check: with no band, held==target, the per-bar gross renorm is a
    multiply-by-1.0 no-op, and the .shift(1) lag is the same — so net AND the lagged weight book are
    bit-for-bit identical to ct.net_from_raw. This anchors every non-zero-delta number as a pure
    one-change delta off the iter-002 baseline.
    """
    pn = _make_panel(seed=31)
    smap = {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw = i2.sector_rel_raw(pn)
        net_b, w_b = i3.banded_net(raw, pn["ret_fwd"], 0.0)
        net_i2, w_i2 = ct.net_from_raw(raw, pn["ret_fwd"])
        pd.testing.assert_series_equal(net_b, net_i2)
        pd.testing.assert_frame_equal(w_b, w_i2)
    finally:
        ut.SECTOR_MAP = orig


def test_iter003_banded_future_bar_no_leak():
    """The BANDED build must be future-bar leak-safe despite the path-dependent recursion.

    The hysteresis recursion held[t]=f(w_tgt[t], held[t-1]) is strictly causal: corrupting the raw
    signal + forward returns AFTER a cutoff must not change the banded net OR the lagged held book
    before it. This is the load-bearing guarantee — a path-dependent band that peeked forward would
    silently inflate IS. Tested at the CHOSEN delta (band active, not the identity).
    """
    pn = _make_panel(seed=32)
    smap = {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw = i2.sector_rel_raw(pn)
        net0, w0 = i3.banded_net(raw, pn["ret_fwd"], i3.CHOSEN_DELTA)
        cut = net0.index[len(net0) // 2]
        raw_c, ret_c = raw.copy(), pn["ret_fwd"].copy()
        raw_c.loc[raw_c.index >= cut] *= -7.0
        ret_c.loc[ret_c.index >= cut] += 5.0
        net1, w1 = i3.banded_net(raw_c, ret_c, i3.CHOSEN_DELTA)
        common = net0.index.intersection(net1.index)
        common = common[common < cut]
        pd.testing.assert_series_equal(net0.loc[common], net1.loc[common])
        pd.testing.assert_frame_equal(w0[w0.index < cut], w1[w1.index < cut])
    finally:
        ut.SECTOR_MAP = orig


def test_iter003_band_reduces_turnover_monotone():
    """A larger no-trade band must NOT increase turnover (SNAP band trades strictly less often).

    Mechanical sanity that the band does what it claims — turnover is non-increasing in delta and
    strictly lower than the delta=0 baseline once the band is active.
    """
    pn = _make_panel(seed=33)
    smap = {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw = i2.sector_rel_raw(pn)
        turns = []
        for delta in (0.0, 0.01, 0.03):
            _, w = i3.banded_net(raw, pn["ret_fwd"], delta)
            turns.append(ct.turnover(w, ct.LO0, ct.HI1))
        assert turns[1] < turns[0] and turns[2] <= turns[1]  # monotone non-increasing, band active
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


import iter_004_mom_rev as i4  # noqa: E402


def _i4_smap(pn):
    """Real multi-name sector map for the synthetic columns (S0..S5 -> A/A/A/B/B/B)."""
    return {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}


def test_iter004_rev_sleeve_is_sector_neutral_and_negated():
    """The reversal sleeve must be (1) per-sector net-zero (sector_neutralize) and (2) the SIGN
    NEGATION of the raw 1-month return / rvol — long recent losers, short recent winners."""
    pn = _make_panel(seed=40)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        rraw = i4.rev_raw(pn).dropna(how="all")
        # (1) each sector bucket sums to ~0 on every row
        for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
            rs = rraw[bucket].sum(axis=1).dropna()
            assert np.allclose(rs.to_numpy(), 0.0, atol=1e-9)
        # (2) sign: before sector-demean, rev = -(close/close.shift(21)-1)/rvol — a name that ROSE
        # over the last 21d (positive raw return) must get a NEGATIVE pre-demean reversal weight.
        close = pn["close"]
        raw_ret = close / close.shift(21) - 1.0
        rvol = close.pct_change().rolling(ct.VOL_WIN).std()
        pre_demean = (-raw_ret / rvol).dropna(how="all")
        # opposite sign to the raw 1-month return wherever finite & non-zero
        m = raw_ret.reindex_like(pre_demean).abs() > 1e-9
        assert (np.sign(pre_demean[m]) == -np.sign(raw_ret.reindex_like(pre_demean)[m])).all().all()
    finally:
        ut.SECTOR_MAP = orig


def test_iter004_mom_only_banded_reproduces_iter003():
    """mom-only sleeve through the iter-004 path must equal iter-003 banded net bit-for-bit
    (the momentum sleeve is reused byte-for-byte from iter-002 -> iter-003)."""
    pn = _make_panel(seed=41)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        net4, w4 = i3.banded_net(i4.mom_raw(pn), pn["ret_fwd"], i3.CHOSEN_DELTA)
        net3, w3 = i3.banded_net(i2.sector_rel_raw(pn), pn["ret_fwd"], i3.CHOSEN_DELTA)
        pd.testing.assert_series_equal(net4, net3)
        pd.testing.assert_frame_equal(w4, w3)
    finally:
        ut.SECTOR_MAP = orig


def _i4_leak_check(combine_fn):
    """Shared future-bar leak harness: corrupting raw + forward returns AFTER a cutoff must not
    change the combined BANDED net OR the lagged held book before it."""
    pn = _make_panel(seed=42)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw0 = combine_fn(pn)
        net0, w0 = i3.banded_net(raw0, pn["ret_fwd"], i3.CHOSEN_DELTA)
        cut = net0.index[len(net0) // 2]
        # corrupt the underlying panel AFTER cut, then rebuild the combined raw from scratch
        pn_c = {k: v.copy() for k, v in pn.items()}
        pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
        pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
        raw1 = combine_fn(pn_c)
        net1, w1 = i3.banded_net(raw1, pn_c["ret_fwd"], i3.CHOSEN_DELTA)
        common = net0.index.intersection(net1.index)
        common = common[common < cut]
        pd.testing.assert_series_equal(net0.loc[common], net1.loc[common])
        pd.testing.assert_frame_equal(w0[w0.index < cut], w1[w1.index < cut])
    finally:
        ut.SECTOR_MAP = orig


def test_iter004_equal_weight_combined_banded_future_bar_no_leak():
    """Combiner (a) equal-weight: combined banded build must be future-bar leak-safe."""
    _i4_leak_check(lambda pn: i4.combine_equal(i4.mom_raw(pn), i4.rev_raw(pn)))


def test_iter004_invvol_combined_banded_future_bar_no_leak():
    """Combiner (b) inverse-vol parity: the past-only sleeve-vol weighting (.shift(1)) plus the
    combined banded build must be future-bar leak-safe — the inverse-vol weights add a new path
    (sleeve net -> rolling std -> shift(1)) that must not peek forward."""
    _i4_leak_check(lambda pn: i4.combine_invvol(i4.mom_raw(pn), i4.rev_raw(pn), pn["ret_fwd"]))


def test_iter004_invvol_weights_are_past_only():
    """The inverse-vol sleeve weights themselves must be past-only: corrupting the tail of the
    panel must not change the early weights (the .shift(1) on the rolling sleeve vol is load-bearing)."""  # noqa: E501
    pn = _make_panel(seed=43)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        mraw, rraw = i4.mom_raw(pn), i4.rev_raw(pn)
        w_mom0, _ = i4.invvol_weights(mraw, rraw, pn["ret_fwd"])
        cut = w_mom0.dropna().index[len(w_mom0.dropna()) // 2]
        pn_c = {k: v.copy() for k, v in pn.items()}
        pn_c["close"].loc[pn_c["close"].index >= cut] *= 3.0
        pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 4.0
        w_mom1, _ = i4.invvol_weights(i4.mom_raw(pn_c), i4.rev_raw(pn_c), pn_c["ret_fwd"])
        early = w_mom0.index[w_mom0.index < cut]
        pd.testing.assert_series_equal(w_mom0.loc[early], w_mom1.loc[early])
    finally:
        ut.SECTOR_MAP = orig


def test_iter004_combined_books_stay_sector_neutral():
    """Both combiners must preserve per-sector net-zero dollar (a linear combo of per-sector-zero
    panels is per-sector-zero) BEFORE the band — the band may then induce the same tiny drift as
    iter-003, but the pre-band combined book must be exactly sector-neutral."""
    pn = _make_panel(seed=44)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        for raw in (
            i4.combine_equal(i4.mom_raw(pn), i4.rev_raw(pn)),
            i4.combine_invvol(i4.mom_raw(pn), i4.rev_raw(pn), pn["ret_fwd"]),
        ):
            raw = raw.dropna(how="all")
            for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
                rs = raw[bucket].sum(axis=1)
                assert np.allclose(rs.to_numpy(), 0.0, atol=1e-9)
    finally:
        ut.SECTOR_MAP = orig


import iter_005_multihorizon as i5  # noqa: E402


def test_iter005_single_sleeve_banded_reproduces_iter003():
    """Pre-registered IDENTITY: a one-sleeve blend `sleeve(252)` through the iter-003 band must
    reproduce iter-003's banded net. The blend's per-sleeve gross-norm + the band's own gross-norm
    is idempotent up to MACHINE EPSILON (the extra division re-rounds), so the match is allclose
    ~1e-16, not bit-exact — the IS Sharpe is identical. This anchors the multi-horizon blend as a
    pure one-change delta off the iter-002 -> iter-003 12-1m baseline."""
    pn = _make_panel(seed=50)
    smap = {c: ("A" if i < 3 else "B") for i, c in enumerate(pn["close"].columns)}
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        net5, w5 = i3.banded_net(i5.sleeve(pn, 252), pn["ret_fwd"], i3.CHOSEN_DELTA)
        net3, w3 = i3.banded_net(i2.sector_rel_raw(pn), pn["ret_fwd"], i3.CHOSEN_DELTA)
        pd.testing.assert_series_equal(net5, net3, atol=1e-12, rtol=0.0)
        pd.testing.assert_frame_equal(w5.fillna(0.0), w3.fillna(0.0), atol=1e-12, rtol=0.0)
        # the IS Sharpe (the reported headline number) matches to machine epsilon — the only
        # divergence is the extra gross-norm division re-rounding, not a signal-level difference
        sh5 = ct.msharpe(net5, ct.LO0, ct.OOS_CUTOFF)
        sh3 = ct.msharpe(net3, ct.LO0, ct.OOS_CUTOFF)
        assert abs(sh5 - sh3) < 1e-9
    finally:
        ut.SECTOR_MAP = orig


def test_iter005_multihorizon_banded_future_bar_no_leak():
    """The multi-horizon BANDED build must be future-bar leak-safe: the blend is a row-wise linear
    combination of past-only gross-normed sleeves, fed into the strictly-causal iter-003 band.
    Corrupting the panel + forward returns AFTER a cutoff must not change the banded net OR the
    lagged held book before it. Reuses the iter-004 combined-build leak harness on mh_raw."""
    _i4_leak_check(lambda pn: i5.mh_raw(pn))


def test_iter005_each_sleeve_is_unit_gross_and_sector_neutral():
    """Each gross-normed sleeve must (1) be per-sector net-zero (linear combo of sector_neutralize)
    and (2) have unit gross (sum|w|=1) on every active row — so the equal-weight blend gives each
    horizon equal scale. The blend itself stays per-sector net-zero (linear combo of zero-sum)."""
    pn = _make_panel(seed=51)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        for lookback in i5.HORIZONS_MH:
            s = i5.sleeve(pn, lookback).dropna(how="all")
            for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
                assert np.allclose(s[bucket].sum(axis=1).to_numpy(), 0.0, atol=1e-9)
            gross = s.abs().sum(axis=1)
            active = gross > 1e-9
            assert np.allclose(gross[active].to_numpy(), 1.0, atol=1e-9)
        blend = i5.mh_raw(pn).dropna(how="all")
        for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
            assert np.allclose(blend[bucket].sum(axis=1).to_numpy(), 0.0, atol=1e-9)
    finally:
        ut.SECTOR_MAP = orig


def test_iter005_sleeve_is_past_only():
    """Each momentum sleeve is past-only: corrupting the tail of the close panel must not change any
    sleeve weight before the cutoff (close.shift(>=21) + trailing-63 rvol never read forward)."""
    pn = _make_panel(seed=52)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        s0 = i5.mh_raw(pn)
        cut = s0.dropna(how="all").index[len(s0.dropna(how="all")) // 2]
        pn_c = {k: v.copy() for k, v in pn.items()}
        pn_c["close"].loc[pn_c["close"].index >= cut] *= 3.0
        s1 = i5.mh_raw(pn_c)
        early = s0.index[s0.index < cut]
        pd.testing.assert_frame_equal(s0.loc[early], s1.loc[early])
    finally:
        ut.SECTOR_MAP = orig


import iter_006_crashbrake as i6  # noqa: E402


def test_iter006_gate_off_reproduces_iter005():
    """Pre-registered IDENTITY: a forced all-zero crash gate must reproduce iter-005's banded net
    bit-for-bit. With g=0 the convex blend (1-g)*mh + g*sleeve(252) collapses to mh exactly, so the
    banded build is byte-identical to iter-005 — anchoring iter-006 as a pure one-change delta."""
    pn = _make_panel(seed=60)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        zeros = pd.Series(0.0, index=pn["close"].index)
        net6, w6 = i3.banded_net(
            i6.crash_braked_raw(pn, gate=zeros), pn["ret_fwd"], i3.CHOSEN_DELTA
        )
        net5, w5 = i3.banded_net(i5.mh_raw(pn), pn["ret_fwd"], i3.CHOSEN_DELTA)
        pd.testing.assert_series_equal(net6, net5)
        pd.testing.assert_frame_equal(w6, w5)
    finally:
        ut.SECTOR_MAP = orig


def test_iter006_gate_on_collapses_to_12_1m_sleeve():
    """With a forced all-ONE gate, the book collapses to the 12-1m sleeve (the crash book) — the
    banded build must equal iter-005's one-sleeve sleeve(252) build (the bear-robust fallback)."""
    pn = _make_panel(seed=61)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        ones = pd.Series(1.0, index=pn["close"].index)
        net_on, w_on = i3.banded_net(
            i6.crash_braked_raw(pn, gate=ones), pn["ret_fwd"], i3.CHOSEN_DELTA
        )
        net_s, w_s = i3.banded_net(i5.sleeve(pn, 252), pn["ret_fwd"], i3.CHOSEN_DELTA)
        pd.testing.assert_series_equal(net_on, net_s)
        pd.testing.assert_frame_equal(w_on, w_s)
    finally:
        ut.SECTOR_MAP = orig


def test_iter006_crashbraked_future_bar_no_leak():
    """The gated build must be future-bar leak-safe: the bear-state gate is a past-only function of
    the EW-universe trailing return, and the convex blend feeds the strictly-causal iter-003 band.
    Corrupting the panel + forward returns AFTER a cutoff must not change the braked net OR the
    lagged held book before it. Reuses the iter-004 combined-build leak harness on the gated raw."""
    _i4_leak_check(lambda pn: i6.crash_braked_raw(pn))


def test_iter006_bear_state_is_past_only():
    """The crash gate g[t] must be past-only: corrupting the tail of the close panel must not change
    any gate value before the cutoff (market_index uses close[t]/close[t-1]; the trailing-252 return
    never reads forward)."""
    pn = _make_panel(seed=62)
    g0 = i6.bear_state(pn["close"])
    cut = g0.index[len(g0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= 3.0
    g1 = i6.bear_state(pn_c["close"])
    early = g0.index[g0.index < cut]
    pd.testing.assert_series_equal(g0.loc[early], g1.loc[early])


def test_iter006_gated_book_stays_sector_neutral():
    """The gated convex blend must stay per-sector net-zero pre-band (a row-wise convex combination
    of two per-sector-zero books is per-sector-zero) for any gate path — tested with the real
    data-driven gate."""
    pn = _make_panel(seed=63)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        raw = i6.crash_braked_raw(pn).dropna(how="all")
        for bucket in (["S0", "S1", "S2"], ["S3", "S4", "S5"]):
            assert np.allclose(raw[bucket].sum(axis=1).to_numpy(), 0.0, atol=1e-9)
    finally:
        ut.SECTOR_MAP = orig


import iter_008_vix_stop as i8  # noqa: E402


def _synth_vix(index: pd.DatetimeIndex, seed: int = 70) -> pd.Series:
    """A VIX-like positive series on `index`: ~15 baseline with fat upside spikes (some > 20/40)."""
    rng = np.random.default_rng(seed)
    return pd.Series(12.0 + 8.0 * np.abs(rng.normal(0, 1.0, len(index))), index=index)


def _i8_net6(pn):
    """iter-006 vol-targeted net on a synthetic panel (the series the iter-008 overlays scale)."""
    return i3.banded_net(i6.crash_braked_raw(pn), pn["ret_fwd"], i6.CHOSEN_DELTA)[0]


def test_iter008_vix_brake_inert_below_base_is_identity():
    """Pre-registered IDENTITY: when VIX never exceeds the baseline (base huge), the VIX scalar is
    1.0 everywhere and net*scale reproduces the iter-006 net bit-for-bit — the brake is a no-op in
    calm tape, so every non-trivial number is a pure de-lever delta off iter-006."""
    pn = _make_panel(seed=64)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        net6 = _i8_net6(pn)
        vix = _synth_vix(net6.index)
        s = i8.vix_scale(vix, base=1e9).reindex(net6.index).fillna(1.0)
        assert np.allclose(s.to_numpy(), 1.0, atol=1e-12)  # fully inert
        pd.testing.assert_series_equal(net6 * s, net6)
    finally:
        ut.SECTOR_MAP = orig


def test_iter008_dd_stop_never_trips_is_identity():
    """Pre-registered IDENTITY: with D_trip = +inf the drawdown stop never trips, scale==1, and the
    stopped net equals the iter-006 net bit-for-bit."""
    pn = _make_panel(seed=65)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        net6 = _i8_net6(pn)
        pd.testing.assert_series_equal(i8.dd_brake(net6, d_trip=1e9), net6)
    finally:
        ut.SECTOR_MAP = orig


def test_iter008_vix_scale_is_past_only():
    """The VIX brake scalar must be past-only: corrupting the VIX tail after a cutoff must not
    change any scale value before it (reindex+ffill+`.shift(1)` never reads forward)."""
    idx = pd.date_range("2020-01-01", periods=300, freq="B")
    vix = _synth_vix(idx, seed=71)
    s0 = i8.vix_scale(vix)
    cut = idx[150]
    vix_c = vix.copy()
    vix_c.loc[vix_c.index >= cut] = 999.0
    s1 = i8.vix_scale(vix_c)
    early = idx[idx < cut]
    pd.testing.assert_series_equal(s0.loc[early], s1.loc[early])


def test_iter008_dd_brake_is_past_only():
    """The drawdown stop scalar must be strictly causal: scale[t] depends only on returns before t,
    so corrupting the net tail after a cutoff must not change any scale value before it."""
    rng = np.random.default_rng(72)
    idx = pd.date_range("2020-01-01", periods=300, freq="B")
    net = pd.Series(rng.normal(0.0003, 0.01, len(idx)), index=idx)
    s0 = i8.dd_brake_scale(net, d_trip=0.05, floor=0.5, rearm=0.025)
    cut = idx[150]
    net_c = net.copy()
    net_c.loc[net_c.index >= cut] -= 0.5  # huge corruption after the cutoff
    s1 = i8.dd_brake_scale(net_c, d_trip=0.05, floor=0.5, rearm=0.025)
    early = idx[idx < cut]
    pd.testing.assert_series_equal(s0.loc[early], s1.loc[early])


def test_iter008_dd_floor_no_self_lock_and_rearms():
    """floor>0 keeps the de-levered book moving so it can RECOVER and re-arm (no self-lock):
    on a path that crashes then rallies, the scalar must (1) never drop below the floor and
    (2) trip to the floor in the crash AND return to 1.0 after the rally re-arms it."""
    idx = pd.date_range("2020-01-01", periods=120, freq="B")
    # 40 days of -2%/day crash (>> D_trip) then 80 days of +2%/day recovery
    path = np.concatenate([np.full(40, -0.02), np.full(80, 0.02)])
    net = pd.Series(path, index=idx)
    s = i8.dd_brake_scale(net, d_trip=0.15, floor=0.5, rearm=0.075)
    assert float(s.min()) >= 0.5 - 1e-12  # never below the floor (no self-lock)
    assert np.isclose(float(s.min()), 0.5)  # actually tripped to the floor in the crash
    assert np.isclose(float(s.iloc[-1]), 1.0)  # re-armed to full after the recovery


def test_iter008_combined_future_bar_no_leak():
    """LOAD-BEARING: the COMBINED VIX+stop build must be future-bar leak-safe. Corrupting the panel,
    the forward returns AND the VIX series after a cutoff must not change the combined net before it
    — the VIX brake reads only VIX[<t], the stop reads only returns[<t], and both multiply the
    future-bar-leak-safe iter-006 net."""
    pn = _make_panel(seed=66)
    smap = _i4_smap(pn)
    orig = ut.SECTOR_MAP
    try:
        ut.SECTOR_MAP = smap
        net6 = _i8_net6(pn)
        vix = _synth_vix(net6.index)
        d_trip = i8.dd_trip_level(net6)
        comb0 = i8.dd_brake(net6 * i8.vix_scale(vix).reindex(net6.index).fillna(1.0), d_trip)
        cut = comb0.index[len(comb0) // 2]
        pn_c = {k: v.copy() for k, v in pn.items()}
        pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
        pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
        vix_c = vix.copy()
        vix_c.loc[vix_c.index >= cut] = 999.0
        net6_c = _i8_net6(pn_c)
        comb1 = i8.dd_brake(net6_c * i8.vix_scale(vix_c).reindex(net6_c.index).fillna(1.0), d_trip)
        common = comb0.index.intersection(comb1.index)
        common = common[common < cut]
        pd.testing.assert_series_equal(comb0.loc[common], comb1.loc[common])
    finally:
        ut.SECTOR_MAP = orig


# =====================================================================================
# C1 — SPLIT-UNADJUSTMENT REGRESSION GUARD (the data-hardening test that would have caught
# the Dukascopy bug that BLOCK-PENDING-FIX'd iter-006). Runs against the ON-DISK Yahoo data;
# skips if the data dir is absent (CI). Split-adjusted total-return data must be CONTINUOUS
# across split ex-dates: an unadjusted N:1 split prints a single-day open-to-open DOWN gap of
# -(1 - 1/N) (4:1 -> -0.75, 10:1 -> -0.90, 20:1 -> -0.95). A symmetric |ret|<0.40 floor is
# NOT usable here because the meme-heavy universe has REAL >40% single-day moves (GME +3.01 /
# -0.555 on 2021-01-26 / 2021-02-01; COIN +0.54; ASTS +0.55) — those are genuine, not split
# artifacts. So the guard is two-pronged: (a) a DOWNSIDE split-artifact floor that the worst
# real single-day collapse (GME -0.555) clears but every named split (>=4:1) trips, and
# (b) exact continuity at the known split ex-dates.
# =====================================================================================

# Known split ex-dates the Dukascopy split-unadjustment corrupted (Yahoo total-return fixes them).
_KNOWN_SPLITS = {
    "AAPLUSDT": "2020-08-31",  # 4-for-1
    "AMZNUSDT": "2022-06-06",  # 20-for-1
    "NVDAUSDT": "2021-07-20",  # 4-for-1
}
# Split-down signature floor: catches every named split (>=4:1 -> <=-0.75) while clearing the
# worst REAL single-day move in 8y of 69 meme-heavy names (GME -0.555). A >~3:1 single-bar
# collapse on adjusted data is a split-unadjustment artifact, not a tradable price move.
_SPLIT_FLOOR = -0.65


def _disk_ret_fwd():
    """On-disk Yahoo open-to-open ret_fwd panel (SECTOR_MAP names), or None if data absent (CI)."""
    base = ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    if not syms:
        return None
    return ct.panels(ct.load_tradfi(syms, None))["ret_fwd"]


def test_no_split_unadjustment_down_gaps_on_disk():
    """No on-disk name may have a single-day open-to-open DOWN gap below the split-artifact floor.

    This is the guard that would have caught the Dukascopy split-unadjustment bug: on unadjusted
    data AAPL/NVDA print -0.75 and AMZN -0.95 on their split ex-dates — all below -0.65. The
    worst REAL collapse on clean Yahoo data is GME -0.555 (a genuine meme unwind), which clears
    the floor. UP-spikes (GME +3.01) are never split artifacts (splits divide price), so the
    guard is downside-only.
    """
    rf = _disk_ret_fwd()
    if rf is None:
        pytest.skip("no on-disk tradfi data (CI)")
    worst = rf.min()  # most-negative open-to-open return per name
    offenders = {s: round(float(v), 3) for s, v in worst.items() if v < _SPLIT_FLOOR}
    assert not offenders, (
        f"split-unadjustment DOWN-gap(s) below floor {_SPLIT_FLOOR}: {offenders} — "
        "split-adjusted total-return data should never single-bar collapse this hard"
    )


def test_known_split_dates_are_continuous_on_disk():
    """At each known split ex-date the adjusted series must be CONTINUOUS (|open-to-open ret|<0.40).

    Exact, name-and-date-targeted version of the guard: the Dukascopy bug manifested as a
    -0.75/-0.95 jump precisely here; on Yahoo total-return data the ±4-calendar-day window around
    each split clears 0.40 with a wide margin (~0.08), confirming the split is fully adjusted out.
    """
    rf = _disk_ret_fwd()
    if rf is None:
        pytest.skip("no on-disk tradfi data (CI)")
    for sym, sd in _KNOWN_SPLITS.items():
        assert sym in rf.columns, f"{sym} missing from on-disk panel"
        col = rf[sym].dropna()
        d = pd.Timestamp(sd)
        win = col[(col.index >= d - pd.Timedelta(days=4)) & (col.index <= d + pd.Timedelta(days=4))]
        assert not win.empty, f"{sym}: no bars near split {sd}"
        mx = float(win.abs().max())
        assert mx < 0.40, (
            f"{sym} split {sd}: adjusted series must be continuous (|ret|<0.40) but "
            f"max|open-to-open ret|={mx:.3f} — split-unadjustment artifact (the Dukascopy bug)"
        )
