from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
_TRADFI = _ROOT / "analysis" / "portfolio" / "tradfi"
sys.path.insert(0, str(_TRADFI))

import core_tradfi as ct  # noqa: E402
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
