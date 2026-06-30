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
