# portfolio-tradfi Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `portfolio-tradfi` foundation — a self-updating Binance-TradFi single-company-stock universe, a leak-safe daily-bar backtest core, beta/sector neutralizers, a Dukascopy daily ingest, and a dollar-neutral cross-sectional-momentum iter-001 anchor — plus the user-invocable skill, all green under synthetic-data tests.

**Architecture:** Fork the proven metals foundation (`analysis/portfolio/metals/universe_metals.py`) into a daily-calibrated tradfi core; add an `exchangeInfo`-derived universe classifier and equity-native neutralizers. Every backtest path runs through one leak-safe function (`net_from_raw`) that gross-normalizes, lags one bar (`.shift(1)`), applies taker cost on turnover, and portfolio-vol-targets. OOS is mechanically hidden behind a `--confirm` flag.

**Tech Stack:** Python 3.13, pandas + numpy (`uv sync --group adaptive`), pytest, ruff. Data via `dukascopy-node` (npx, no key). All new code under `analysis/portfolio/tradfi/`.

## Global Constraints

- `OOS_CUTOFF = pd.Timestamp("2025-03-24")` — immutable. IS `< cutoff`; OOS `>= cutoff`.
- **Daily** bars. `CANDLES_PER_YEAR = 252`. Signals past-only; decide on close, fill at open[t+1].
- OOS is HIDDEN: performance printers default `reveal_oos=False`; OOS prints only under an explicit `--confirm` flag.
- `COST_SIDE = 0.0006` (6 bps/side taker + slippage) on `|Δweight|` turnover. Funding NOT modelled.
- `ANNUAL_TARGET_VOL = 0.15`, `MAX_LEV = 5.0`.
- Universe = Binance `contractType == "TRADIFI_PERPETUAL"` single-company stocks, point-in-time. Exclude ETFs/indices, commodities, metals (XAU/XAG/XPT/XPD), pre-IPO synthetics (ANTHROPIC/OPENAI).
- Lazy `import pandas as pd` / `import numpy as np` inside functions is NOT required for `analysis/` scripts (they always run under the adaptive group), but keep module top-level imports limited to pandas/numpy/stdlib.
- Ruff line-length = 100. Run `uv run ruff check . --fix && uv run ruff format .` before every commit.
- Tests live in `tests/test_portfolio_tradfi_foundation.py`. Synthetic-data tests always run; on-disk data tests `pytest.skip` when CSVs are absent.
- Commit messages end with the two trailers used across this repo:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` and the `Claude-Session:` line.

---

### Task 1: Universe module — `exchangeInfo` classifier + hard-coded sector map

**Files:**
- Create: `analysis/portfolio/tradfi/__init__.py` (empty package marker)
- Create: `analysis/portfolio/tradfi/universe_tradfi.py`
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Produces:
  - `EXCLUDE_ETF: frozenset[str]`, `EXCLUDE_COMMODITY: frozenset[str]`, `EXCLUDE_METAL: frozenset[str]`, `EXCLUDE_PRIVATE: frozenset[str]` (bare stems, no `USDT`).
  - `SECTOR_MAP: dict[str, str]` — `{ "AAPLUSDT": "Tech", ... }` over the stock universe.
  - `classify_tradfi_stocks(exchange_info: dict) -> list[str]` — sorted list of `*USDT` symbols that are single-company stocks.
  - `stem(symbol: str) -> str` — strip trailing `USDT`.

- [ ] **Step 1: Write the failing test**

```python
# in tests/test_portfolio_tradfi_foundation.py
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TRADFI = _ROOT / "analysis" / "portfolio" / "tradfi"
sys.path.insert(0, str(_TRADFI))

import universe_tradfi as ut  # noqa: E402


def _exinfo(symbols_types):
    """Minimal exchangeInfo dict: symbols_types = [(symbol, contractType), ...]."""
    return {"symbols": [{"symbol": s, "contractType": ct} for s, ct in symbols_types]}


def test_classify_keeps_single_company_stocks():
    info = _exinfo([
        ("AAPLUSDT", "TRADIFI_PERPETUAL"),
        ("JPMUSDT", "TRADIFI_PERPETUAL"),
        ("BTCUSDT", "PERPETUAL"),          # crypto -> drop (not TRADIFI)
        ("SPYUSDT", "TRADIFI_PERPETUAL"),  # ETF -> drop
        ("XAUUSDT", "TRADIFI_PERPETUAL"),  # metal -> drop
        ("NATGASUSDT", "TRADIFI_PERPETUAL"),  # commodity -> drop
        ("OPENAIUSDT", "TRADIFI_PERPETUAL"),  # private synthetic -> drop
    ])
    out = ut.classify_tradfi_stocks(info)
    assert out == ["AAPLUSDT", "JPMUSDT"]


def test_every_known_stock_has_a_sector():
    # Spot-check core names are mapped; SECTOR_MAP must cover its own keys.
    for sym in ("AAPLUSDT", "JPMUSDT", "TSLAUSDT", "AMZNUSDT", "NVDAUSDT"):
        assert sym in ut.SECTOR_MAP, f"{sym} missing from SECTOR_MAP"
    assert all(isinstance(v, str) and v for v in ut.SECTOR_MAP.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k classify -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'universe_tradfi'`.

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/portfolio/tradfi/universe_tradfi.py
"""TradFi-portfolio universe — Binance exchangeInfo-derived single-company stock perps.

The universe is NOT hard-coded: it is re-derived from Binance USDⓈ-M exchangeInfo by
keeping every contractType == "TRADIFI_PERPETUAL" symbol that is a single-company common
stock (or single-company US-listed ADR), dropping ETFs/indices, commodities, the four
metals (owned by the portfolio-metals track) and pre-IPO synthetics. Point-in-time
membership + ragged starts are handled downstream (a name carries weight only once it has
Dukascopy history).
"""

from __future__ import annotations

# Bare stems (symbol without the trailing USDT). Maintained by hand as Binance lists more.
EXCLUDE_ETF: frozenset[str] = frozenset({
    "SPY", "QQQ", "IWM", "TQQQ", "SQQQ", "SOXL", "UVXY", "XLE",
    "EWJ", "EWY", "EWZ", "EWT", "URNM", "KORU", "STXX",
})
EXCLUDE_COMMODITY: frozenset[str] = frozenset({"NATGAS", "CL", "BZ", "COPPER"})
EXCLUDE_METAL: frozenset[str] = frozenset({"XAU", "XAG", "XPT", "XPD"})
EXCLUDE_PRIVATE: frozenset[str] = frozenset({"ANTHROPIC", "OPENAI"})
_EXCLUDE_ALL = EXCLUDE_ETF | EXCLUDE_COMMODITY | EXCLUDE_METAL | EXCLUDE_PRIVATE

# Hard-coded stock -> sector map (user directive 2026-06-30: hard-code for now).
# Sectors: Tech, Semi, Comm, ConsDisc, ConsStap, Fin, Health, Indust, Energy, Crypto.
SECTOR_MAP: dict[str, str] = {
    "AAPLUSDT": "Tech", "MSFTUSDT": "Tech", "GOOGLUSDT": "Comm", "METAUSDT": "Comm",
    "AMZNUSDT": "ConsDisc", "TSLAUSDT": "ConsDisc", "NVDAUSDT": "Semi", "AMDUSDT": "Semi",
    "AVGOUSDT": "Semi", "MRVLUSDT": "Semi", "QCOMUSDT": "Semi", "TSMUSDT": "Semi",
    "ASMLUSDT": "Semi", "ARMUSDT": "Semi", "LRCXUSDT": "Semi", "KLACUSDT": "Semi",
    "AMATUSDT": "Semi", "MUUSDT": "Semi", "INTCUSDT": "Semi", "ORCLUSDT": "Tech",
    "CRMUSDT": "Tech", "ADBEUSDT": "Tech", "NOWUSDT": "Tech", "IBMUSDT": "Tech",
    "CSCOUSDT": "Tech", "PLTRUSDT": "Tech", "CRWDUSDT": "Tech", "DELLUSDT": "Tech",
    "NFLXUSDT": "Comm", "DISUSDT": "Comm", "ZMUSDT": "Tech",
    "JPMUSDT": "Fin", "VUSDT": "Fin", "BRKBUSDT": "Fin", "COINUSDT": "Crypto",
    "HOODUSDT": "Fin", "MSTRUSDT": "Crypto", "PAYPUSDT": "Fin",
    "WMTUSDT": "ConsStap", "COSTUSDT": "ConsStap", "HDUSDT": "ConsDisc", "EBAYUSDT": "ConsDisc",
    "BABAUSDT": "ConsDisc", "UBERUSDT": "Tech", "DKNGUSDT": "ConsDisc", "GMEUSDT": "ConsDisc",
    "RIVNUSDT": "ConsDisc", "NVOUSDT": "Health", "LLYUSDT": "Health", "HIMSUSDT": "Health",
    "SONYUSDT": "ConsDisc", "NOKUSDT": "Tech", "CRCLUSDT": "Crypto", "CRWVUSDT": "Tech",
    "NBISUSDT": "Tech", "IRENUSDT": "Crypto", "RKLBUSDT": "Indust", "ASTSUSDT": "Comm",
    "SMCIUSDT": "Tech", "WDCUSDT": "Semi", "SNDKUSDT": "Semi", "COHRUSDT": "Semi",
    "GLWUSDT": "Tech", "CIENUSDT": "Tech", "CRDOUSDT": "Semi", "ALABUSDT": "Semi",
    "HPEUSDT": "Tech", "LITEUSDT": "Semi", "FLNCUSDT": "Indust", "NVOUSDT": "Health",
}


def stem(symbol: str) -> str:
    """Strip the trailing USDT quote from a perp symbol (AAPLUSDT -> AAPL)."""
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def classify_tradfi_stocks(exchange_info: dict) -> list[str]:
    """Return the sorted single-company-stock universe from a Binance exchangeInfo dict.

    Keeps `contractType == "TRADIFI_PERPETUAL"` USDT symbols, drops the maintained
    ETF / commodity / metal / private exclude sets. Unknown new stems are KEPT (fail-open:
    a newly-listed stock joins the universe; review the exclude sets when Binance adds ETFs).
    """
    out = []
    for s in exchange_info.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "TRADIFI_PERPETUAL":
            continue
        if not sym.endswith("USDT"):
            continue
        if stem(sym) in _EXCLUDE_ALL:
            continue
        out.append(sym)
    return sorted(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "classify or sector" -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff check analysis/portfolio/tradfi/ tests/test_portfolio_tradfi_foundation.py --fix
uv run ruff format analysis/portfolio/tradfi/ tests/test_portfolio_tradfi_foundation.py
git add analysis/portfolio/tradfi/__init__.py analysis/portfolio/tradfi/universe_tradfi.py tests/test_portfolio_tradfi_foundation.py
git commit -m "feat(tradfi): exchangeInfo-derived single-company-stock universe + sector map"
```

---

### Task 2: Leak-safe daily backtest core (`core_tradfi.py`)

Fork `analysis/portfolio/metals/universe_metals.py`, swapping 8h constants for daily and the metals loader for a generic daily-CSV loader. The leak-safe math (`net_from_raw`, `vol_target`, `panels`) is preserved bit-for-bit in structure.

**Files:**
- Create: `analysis/portfolio/tradfi/core_tradfi.py`
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Consumes: nothing (leaf module).
- Produces:
  - Constants: `OOS_CUTOFF`, `COST_SIDE`, `ANNUAL_TARGET_VOL`, `MAX_LEV`, `CANDLES_PER_YEAR=252`, `TARGET_VOL`, `HORIZONS=(21,63,126,252)`, `VOL_WIN=63`, `PORT_VOL_WIN=63`, `LO0`, `HI1`.
  - `load_tradfi(symbols, data_dir=None) -> dict[str, pd.DataFrame]` (reads `data/<SYM>/1d.csv`).
  - `panels(coins) -> dict[str, pd.DataFrame]` (keys: open/high/low/close/ret_fwd).
  - `vol_target_scale(net) -> pd.Series`, `vol_target(net) -> pd.Series`.
  - `net_from_raw(raw, ret_fwd) -> tuple[pd.Series, pd.DataFrame]`.
  - `msharpe(net, lo=LO0, hi=HI1) -> float`, `turnover`, `maxdd`.
  - `perf_line(label, net, *, reveal_oos=False) -> str`, `is_only(net) -> pd.Series`.
  - `regime_of(idx) -> pd.Series` mapping each daily timestamp to `"bull"|"bear"|"chop"` (fixed date ranges, IS-only).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_portfolio_tradfi_foundation.py
import core_tradfi as ct  # noqa: E402


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
    return {"open": opn, "high": high, "low": low, "close": close,
            "ret_fwd": opn.shift(-1) / opn - 1.0}


def _xsmom_raw(pn):
    """Leak-safe cross-sectional momentum (12-1m), inverse-vol scaled — iter-001 shape."""
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0          # 12m-1m, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    demeaned = mom.sub(mom.mean(axis=1), axis=0)            # cross-sectional demean
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "daily_constants or dollar_accounting" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'core_tradfi'`.

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/portfolio/tradfi/core_tradfi.py
"""TradFi-portfolio foundation — daily-bar leak-safe backtest core.

Forked from analysis/portfolio/metals/universe_metals.py, recalibrated for DAILY bars and a
self-updating stock universe. The leak-safe accounting is identical: decide on close[t],
fill at open[t+1], weights `.shift(1)`-lagged, taker cost on turnover, portfolio vol-target.
OOS stays hidden unless reveal_oos=True (CONFIRMATION).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]

OOS_CUTOFF = pd.Timestamp("2025-03-24")  # immutable; IS < cutoff, OOS >= cutoff
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")

COST_SIDE = 0.0006  # 6 bps/side taker + slippage on |Δweight| turnover
ANNUAL_TARGET_VOL = 0.15
MAX_LEV = 5.0
CANDLES_PER_YEAR = 252  # US equity trading days/year
TARGET_VOL = ANNUAL_TARGET_VOL / np.sqrt(CANDLES_PER_YEAR)  # per-day target ≈ 0.00945

HORIZONS = (21, 63, 126, 252)  # ~1m / 3m / 6m / 12m in trading days
VOL_WIN = 63                   # 3m realized-vol window for inverse-vol sizing
PORT_VOL_WIN = 63              # portfolio vol-target lookback

# Fixed IS regime tags (US equity regimes; IS-only, used for all-weather scoring).
_REGIMES = [
    ("bull", "2012-01-01", "2020-02-19"),
    ("bear", "2020-02-19", "2020-04-01"),   # COVID crash
    ("bull", "2020-04-01", "2022-01-03"),
    ("bear", "2022-01-03", "2022-10-13"),   # 2022 bear
    ("chop", "2022-10-13", "2023-06-01"),
    ("bull", "2023-06-01", "2025-03-24"),
]


def load_tradfi(symbols, data_dir=None) -> dict[str, pd.DataFrame]:
    """Load each symbol's daily CSV into {ticker: OHLCV DataFrame indexed by open_time ms}.

    Missing files are skipped with a note (point-in-time: a name not yet ingested is absent).
    """
    base = Path(data_dir) if data_dir is not None else _ROOT / "data"
    coins: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        p = base / sym / "1d.csv"
        if not p.exists():
            print(f"  ! {sym}: missing {p} — skipped")
            continue
        k = pd.read_csv(p, usecols=["open_time", "open", "high", "low", "close", "volume"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def panels(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Aligned float panels (DatetimeIndex) + leak-safe forward open-to-open return.

    ret_fwd[t] = open[t+1]/open[t] - 1 : the return earned by a position decided at close[t].
    NaN where an asset has no bar (ragged start / holiday) — never forward-filled.
    """
    cols = list(coins)
    opens = pd.DataFrame({s: coins[s]["open"] for s in cols}).astype(float).sort_index()
    out = {"open": opens}
    for field in ("high", "low", "close"):
        out[field] = (
            pd.DataFrame({s: coins[s][field] for s in cols}).astype(float).reindex(opens.index)
        )
    idx = pd.to_datetime(opens.index, unit="ms")
    for df in out.values():
        df.index = idx
    out["ret_fwd"] = out["open"].shift(-1) / out["open"] - 1.0
    return out


def vol_target_scale(net: pd.Series) -> pd.Series:
    """Per-candle vol-target SCALAR (past-only): TARGET_VOL / trailing-vol, capped at MAX_LEV."""
    rv = net.rolling(PORT_VOL_WIN).std().shift(1)
    return (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)


def vol_target(net: pd.Series) -> pd.Series:
    """Scale a per-candle net-return series to ~ANNUAL_TARGET_VOL, capped at MAX_LEV."""
    return net * vol_target_scale(net)


def net_from_raw(raw: pd.DataFrame, ret_fwd: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Leak-safe core: signed raw weights → (vol-targeted net return, lagged weight book).

    gross-normalise to 1 → LAG one bar (.shift(1)) → PnL = Σ w·ret_fwd → taker cost on
    |Δw| turnover → portfolio vol-target.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return vol_target(net), w


def msharpe(net: pd.Series, lo=LO0, hi=HI1) -> float:
    """Annualised Sharpe from MONTHLY summed returns over [lo, hi) (√12 annualisation)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def turnover(w, lo=LO0, hi=HI1) -> float:
    """Mean per-candle gross turnover Σ|Δw| over [lo, hi)."""
    t = (w - w.shift(1)).abs().sum(axis=1) if isinstance(w, pd.DataFrame) else (w - w.shift(1)).abs()
    t = t[(t.index >= lo) & (t.index < hi)]
    return float(t.mean())


def maxdd(net: pd.Series) -> float:
    """Max drawdown of the compounded equity curve (negative fraction)."""
    eq = (1 + net).cumprod()
    return float((eq / eq.cummax() - 1).min())


def regime_of(idx: pd.DatetimeIndex) -> pd.Series:
    """Map each timestamp to a fixed IS regime label ('bull'|'bear'|'chop'|'oos')."""
    out = pd.Series("oos", index=idx, dtype=object)
    for label, lo, hi in _REGIMES:
        m = (idx >= pd.Timestamp(lo)) & (idx < pd.Timestamp(hi))
        out[m] = label
    return out


def regime_sharpe(net: pd.Series) -> dict[str, float]:
    """Per-regime annualised Sharpe over the IS window (all-weather scorecard)."""
    reg = regime_of(net.index)
    out = {}
    for label in ("bull", "bear", "chop"):
        sub = net[reg == label]
        g = sub.groupby(sub.index.to_period("M")).sum()
        out[label] = float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
    return out


def perf_line(label: str, net: pd.Series, *, reveal_oos: bool = False) -> str:
    """One-line IS performance summary. OOS hidden unless reveal_oos=True (CONFIRMATION)."""
    eq = (1 + net).cumprod()
    parts = [
        f"  {label:18} IS_Sharpe={msharpe(net, LO0, OOS_CUTOFF):+.2f}",
        f"maxDD={maxdd(net) * 100:5.1f}%",
        f"netTot={(eq.iloc[-1] - 1) * 100:+.0f}%",
    ]
    if reveal_oos:
        parts.insert(2, f"OOS_Sharpe={msharpe(net, OOS_CUTOFF, HI1):+.2f}")
    return "  ".join(parts)


def is_only(net: pd.Series) -> pd.Series:
    """Slice a net series to the IN-SAMPLE window only (guards accidental OOS peeking)."""
    return net[net.index < OOS_CUTOFF]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "daily_constants or dollar_accounting" -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check analysis/portfolio/tradfi/core_tradfi.py tests/ --fix && uv run ruff format analysis/portfolio/tradfi/ tests/
git add analysis/portfolio/tradfi/core_tradfi.py tests/test_portfolio_tradfi_foundation.py
git commit -m "feat(tradfi): leak-safe daily backtest core (forked from metals, 252-day calibrated)"
```

---

### Task 3: Leak tests — future-bar AND same-bar (the key improvement)

**Files:**
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Consumes: `core_tradfi.net_from_raw`, `panels`, `_xsmom_raw` (test helper from Task 2).

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_portfolio_tradfi_foundation.py
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
    pn2["close"].loc[t] *= 1.5            # only close[t] perturbed; open/ret_fwd untouched
    raw2 = _xsmom_raw(pn2)
    net2, _ = ct.net_from_raw(raw2, pn2["ret_fwd"])
    # net on bar t (return open[t]->open[t+1], position from close[t-1]) is independent of close[t].
    common = net0.index.intersection(net2.index)
    upto_t = common[common <= t]
    pd.testing.assert_series_equal(net0.loc[upto_t], net2.loc[upto_t])
```

- [ ] **Step 2: Run to verify they pass immediately (the core is already leak-safe)**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "corruption or same_bar" -q`
Expected: PASS (2). If `test_same_bar_...` FAILS, the signal uses close[t] for bar-t exposure — that is a real leak; STOP and fix the signal/lag, do not weaken the test.

- [ ] **Step 3: Commit**

```bash
git add tests/test_portfolio_tradfi_foundation.py
git commit -m "test(tradfi): future-bar AND same-bar leak guards on the core"
```

---

### Task 4: Neutralizers — dollar / beta / sector (`neutralize.py`)

**Files:**
- Create: `analysis/portfolio/tradfi/neutralize.py`
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Consumes: `core_tradfi` (for VOL_WIN default only).
- Produces:
  - `dollar_neutralize(raw: pd.DataFrame) -> pd.DataFrame` — per-row cross-sectional demean.
  - `rolling_beta(ret: pd.DataFrame, mkt: pd.Series, win: int = 63) -> pd.DataFrame` — past-only.
  - `beta_neutralize(raw: pd.DataFrame, betas: pd.DataFrame) -> pd.DataFrame` — remove net-beta row exposure.
  - `sector_neutralize(raw: pd.DataFrame, sector_map: dict[str, str]) -> pd.DataFrame` — demean within sector.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_portfolio_tradfi_foundation.py
import neutralize as nz  # noqa: E402


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "neutral or rolling_beta" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'neutralize'`.

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/portfolio/tradfi/neutralize.py
"""Equity-native neutralizers for the tradfi book: dollar / beta / sector.

All are leak-safe row-wise transforms on a raw-weight panel (index = daily DatetimeIndex,
columns = tickers). rolling_beta uses only past returns (no .shift into the future).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def dollar_neutralize(raw: pd.DataFrame) -> pd.DataFrame:
    """Subtract each row's cross-sectional mean so longs$ == shorts$ (net dollar = 0)."""
    return raw.sub(raw.mean(axis=1), axis=0)


def rolling_beta(ret: pd.DataFrame, mkt: pd.Series, win: int = 63) -> pd.DataFrame:
    """Past-only rolling beta of each column's returns to the market proxy `mkt`.

    beta = Cov(asset, mkt) / Var(mkt) over a trailing `win` window. The final window ends at
    the current bar (no forward leak); callers .shift(1) before USING betas to size bar t+1.
    """
    var = mkt.rolling(win).var()
    out = {}
    for c in ret.columns:
        out[c] = ret[c].rolling(win).cov(mkt) / var
    return pd.DataFrame(out, index=ret.index)


def beta_neutralize(raw: pd.DataFrame, betas: pd.DataFrame) -> pd.DataFrame:
    """Remove each row's net market-beta exposure: raw - (Σ w·β / Σ β²)·β.

    Projects the weight vector off the beta vector per row (least-squares hedge of the market
    factor). betas must be past-only and aligned to raw; rows with no beta are left unchanged.
    """
    b = betas.reindex_like(raw)
    num = (raw * b).sum(axis=1)
    den = (b * b).sum(axis=1).replace(0, np.nan)
    k = (num / den).fillna(0.0)
    return raw.sub(b.mul(k, axis=0), axis=0)


def sector_neutralize(raw: pd.DataFrame, sector_map: dict[str, str]) -> pd.DataFrame:
    """Demean weights WITHIN each sector bucket so every sector is net-zero dollar.

    Columns absent from sector_map are treated as their own singleton sector (-> forced to 0,
    which is the safe default: an unmapped name takes no position).
    """
    out = raw.copy()
    sectors: dict[str, list[str]] = {}
    for c in raw.columns:
        sectors.setdefault(sector_map.get(c, f"__{c}"), []).append(c)
    for cols in sectors.values():
        block = raw[cols]
        out[cols] = block.sub(block.mean(axis=1), axis=0)
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "neutral or rolling_beta" -q`
Expected: PASS (3).

- [ ] **Step 5: Commit**

```bash
uv run ruff check analysis/portfolio/tradfi/neutralize.py tests/ --fix && uv run ruff format analysis/portfolio/tradfi/ tests/
git add analysis/portfolio/tradfi/neutralize.py tests/test_portfolio_tradfi_foundation.py
git commit -m "feat(tradfi): dollar/beta/sector neutralizers (leak-safe, past-only betas)"
```

---

### Task 5: Dukascopy daily stock ingest (`ingest_dukascopy_stocks.py`)

Fork the metals `ingest_dukascopy.py` resampler; change 8h→daily and the instrument map to stocks. The network download is a run-step (npx, slow); the resample/format is unit-tested with synthetic intraday data.

**Files:**
- Create: `analysis/portfolio/tradfi/ingest_dukascopy_stocks.py`
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Produces:
  - `INSTRUMENTS: dict[str, tuple[str, str]]` — `{BinanceTicker: (dukascopy_id, earliest_start)}`.
  - `resample_daily(h1: pd.DataFrame) -> pd.DataFrame` — intraday OHLC (UTC index) → daily OHLC with `open_time` ms column + OHLCV.
  - `write_daily_csv(sym: str, daily: pd.DataFrame, data_dir) -> Path` — writes `data/<SYM>/1d.csv` in the Kline CSV schema.
  - `main()` (CLI: `--symbols`, `--start`, `--data-dir`).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_portfolio_tradfi_foundation.py
import ingest_dukascopy_stocks as ids  # noqa: E402


def test_resample_daily_aggregates_intraday_ohlc():
    # two UTC days of hourly bars; daily OHLC = first open / max high / min low / last close.
    idx = pd.date_range("2021-03-01 14:00", periods=13, freq="h", tz="UTC")  # spans 2 sessions
    h1 = pd.DataFrame({
        "open": np.arange(1, 14, dtype=float),
        "high": np.arange(1, 14, dtype=float) + 0.5,
        "low": np.arange(1, 14, dtype=float) - 0.5,
        "close": np.arange(1, 14, dtype=float) + 0.1,
        "volume": 1.0,
    }, index=idx)
    daily = ids.resample_daily(h1)
    assert list(daily.columns) == ["open_time", "open", "high", "low", "close", "volume"]
    # day 1 (2021-03-01): bars 14:00..23:00 -> open=row0.open, high=max, low=min, close=last
    d0 = daily.iloc[0]
    assert d0["open"] == 1.0
    assert d0["high"] == h1.loc["2021-03-01"]["high"].max()
    assert d0["low"] == h1.loc["2021-03-01"]["low"].min()
    # open_time is midnight-UTC epoch ms of that calendar day
    assert d0["open_time"] == int(pd.Timestamp("2021-03-01", tz="UTC").value // 1_000_000)


def test_instruments_map_has_core_names():
    for sym in ("AAPLUSDT", "MSFTUSDT", "TSLAUSDT", "JPMUSDT"):
        assert sym in ids.INSTRUMENTS
        duka_id, start = ids.INSTRUMENTS[sym]
        assert isinstance(duka_id, str) and isinstance(start, str)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "resample_daily or instruments_map" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'ingest_dukascopy_stocks'`.

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/portfolio/tradfi/ingest_dukascopy_stocks.py
"""Ingest Dukascopy daily underlying-stock history → data/<TICKER>/1d.csv.

Binance TradFi single-stock perps all onboarded in 2026 (≈no native history), so the 2010+
backtest history comes from the Dukascopy underlying-stock feed (dukascopy-node, free, no key).
Download hourly OHLC, resample to DAILY (UTC calendar day), write under the BINANCE ticker so
backtest↔live keys match. Prices are Dukascopy bid OHLC (spread modelled via COST_SIDE).
Volume is tick-volume (relative proxy). Fields the source lacks are written "0".

Run from repo root:
    uv run python analysis/portfolio/tradfi/ingest_dukascopy_stocks.py --symbols AAPLUSDT,MSFTUSDT
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_DUKA_CACHE = str(_ROOT / ".dukascopy-cache")
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

# Binance live ticker -> (dukascopy instrument id, earliest sensible start).
# Dukascopy US single-stock ids are lowercase "<ticker>ususd" (e.g. aaplususd). ADRs use the
# US-listed line. Verify per-name depth on first ingest; recent IPOs start at listing.
INSTRUMENTS: dict[str, tuple[str, str]] = {
    "AAPLUSDT": ("aaplususd", "2010-01-01"),
    "MSFTUSDT": ("msftususd", "2010-01-01"),
    "AMZNUSDT": ("amznususd", "2010-01-01"),
    "NVDAUSDT": ("nvdaususd", "2010-01-01"),
    "GOOGLUSDT": ("googlususd", "2010-01-01"),
    "METAUSDT": ("metususd", "2012-05-18"),
    "TSLAUSDT": ("tslususd", "2010-06-29"),
    "JPMUSDT": ("jpmususd", "2010-01-01"),
    "VUSDT": ("vususd", "2010-01-01"),
    "WMTUSDT": ("wmtususd", "2010-01-01"),
    "COSTUSDT": ("costususd", "2010-01-01"),
    "NFLXUSDT": ("nflxususd", "2010-01-01"),
    "AMDUSDT": ("amdususd", "2010-01-01"),
    "INTCUSDT": ("intcususd", "2010-01-01"),
    "JNJ_PLACEHOLDER": ("", ""),  # remove; template marker
    # NOTE: extend to the full SECTOR_MAP roster on first full ingest; recent IPOs:
    # COINUSDT coinususd 2021-04-14, HOODUSDT hoodususd 2021-07-29, PLTRUSDT pltrususd 2020-09-30, etc.
}
INSTRUMENTS.pop("JNJ_PLACEHOLDER", None)


def _price(x: float) -> str:
    return f"{x:.6f}".rstrip("0").rstrip(".") or "0"


def resample_daily(h1: pd.DataFrame) -> pd.DataFrame:
    """Intraday OHLC (tz-aware UTC index) → daily OHLC with open_time(ms)+OHLCV columns.

    open = first open of the UTC calendar day, high = max, low = min, close = last close,
    volume = sum. Empty days are dropped (no fabrication of non-trading days).
    """
    idx = h1.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
        h1 = h1.copy()
        h1.index = idx
    g = h1.resample("1D")
    daily = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
    }).dropna(subset=["open", "close"])
    daily.insert(0, "open_time", (daily.index.tz_convert("UTC").view("int64") // 1_000_000).astype("int64"))
    return daily.reset_index(drop=True)


def write_daily_csv(sym: str, daily: pd.DataFrame, data_dir: str | Path) -> Path:
    """Write daily OHLC to data/<sym>/1d.csv in the project Kline CSV schema (extra cols '0')."""
    out = Path(data_dir) / sym / "1d.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = ["open_time,open,high,low,close,volume,close_time,quote_volume,trades,"
            "taker_buy_base,taker_buy_quote,ignore"]
    for r in daily.itertuples(index=False):
        ct = int(r.open_time) + 86_400_000 - 1
        rows.append(
            f"{int(r.open_time)},{_price(r.open)},{_price(r.high)},{_price(r.low)},"
            f"{_price(r.close)},{_price(r.volume)},{ct},0,0,0,0,0"
        )
    out.write_text("\n".join(rows) + "\n")
    return out


def _run_duka(instrument: str, start: str, end: str, outdir: str, timeout: int = 600):
    """Download hourly OHLC for [start, end) via dukascopy-node; return its h1 DataFrame or None."""
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(_DUKA_CACHE, exist_ok=True)
    cmd = [
        "npx", "--yes", "dukascopy-node", "-i", instrument, "-from", start, "-to", end,
        "-t", "h1", "-f", "csv", "-dir", outdir, "-ch", _DUKA_CACHE, "-r", "3", "-bs", "10",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        print(f"    dukascopy fetch failed for {instrument} {start}..{end}: {e}")
        return None
    files = glob.glob(os.path.join(outdir, f"{instrument}*.csv"))
    if not files:
        return None
    df = pd.read_csv(max(files, key=os.path.getmtime))
    tcol = "timestamp" if "timestamp" in df.columns else df.columns[0]
    df[tcol] = pd.to_datetime(df[tcol], utc=True, errors="coerce")
    df = df.dropna(subset=[tcol]).set_index(tcol)
    df.columns = [c.lower() for c in df.columns]
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    return df[keep]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(INSTRUMENTS))
    ap.add_argument("--end", default=str(pd.Timestamp.utcnow().date()))
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    args = ap.parse_args()
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        if sym not in INSTRUMENTS:
            print(f"  ! {sym}: not in INSTRUMENTS map — skipped")
            continue
        duka_id, start = INSTRUMENTS[sym]
        print(f"  {sym} <- {duka_id} ({start}..{args.end})")
        with tempfile.TemporaryDirectory() as td:
            h1 = _run_duka(duka_id, start, args.end, td)
        if h1 is None or h1.empty:
            print(f"    no data for {sym}")
            continue
        daily = resample_daily(h1)
        p = write_daily_csv(sym, daily, args.data_dir)
        print(f"    wrote {len(daily)} daily bars -> {p}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k "resample_daily or instruments_map" -q`
Expected: PASS (2). (Network download is NOT exercised by tests.)

- [ ] **Step 5: Commit**

```bash
uv run ruff check analysis/portfolio/tradfi/ingest_dukascopy_stocks.py tests/ --fix && uv run ruff format analysis/portfolio/tradfi/ tests/
git add analysis/portfolio/tradfi/ingest_dukascopy_stocks.py tests/test_portfolio_tradfi_foundation.py
git commit -m "feat(tradfi): Dukascopy daily stock ingest (hourly->daily UTC resample)"
```

---

### Task 6: iter-001 anchor — dollar-neutral cross-sectional momentum

**Files:**
- Create: `analysis/portfolio/tradfi/iter_001_xsmom.py`
- Test: `tests/test_portfolio_tradfi_foundation.py`

**Interfaces:**
- Consumes: `core_tradfi` (panels, net_from_raw, perf_line, regime_sharpe), `neutralize.dollar_neutralize`, `universe_tradfi`.
- Produces: `xsmom_raw(pn: dict) -> pd.DataFrame`, `build(coins: dict) -> tuple[pd.Series, pd.DataFrame]`, `main()`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_portfolio_tradfi_foundation.py
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
            {"open": opn, "high": np.maximum(opn, close), "low": np.minimum(opn, close),
             "close": close, "volume": 1.0},
            index=pd.Index(ot, name="open_time"),
        )
    net, w = i1.build(coins)
    assert isinstance(net, pd.Series) and len(net) > 200
    # pre-vol-target lagged weights are dollar-neutral on active rows
    active = w[w.abs().sum(axis=1) > 0]
    assert np.allclose(active.sum(axis=1).to_numpy(), 0.0, atol=1e-9)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k iter001 -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'iter_001_xsmom'`.

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/portfolio/tradfi/iter_001_xsmom.py
"""iter-001 anchor — dollar-neutral cross-sectional momentum (12-1m), daily, vol-targeted.

The market-neutral starting point for the tradfi track. Rank the universe by trailing 12m-1m
return, inverse-vol scale, dollar-neutralize (longs$ == shorts$), gross-normalize → lag → cost
→ portfolio vol-target via the leak-safe core. OOS stays hidden (perf_line reveal_oos=False).
iter-002 will add beta-neutral, iter-003 sector-neutral.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402


def xsmom_raw(pn):
    """Leak-safe cross-sectional 12m-1m momentum, inverse-vol scaled, dollar-neutralized."""
    close = pn["close"]
    mom = close.shift(21) / close.shift(252) - 1.0          # 12m-1m, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    raw = (mom / rvol)
    return nz.dollar_neutralize(raw)


def build(coins):
    """coins -> (vol-targeted net series, lagged weight book) via the leak-safe core."""
    pn = ct.panels(coins)
    raw = xsmom_raw(pn)
    return ct.net_from_raw(raw, pn["ret_fwd"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    # Universe from on-disk ingested names (point-in-time: only what we have data for).
    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_dukascopy_stocks.py first.")
        return
    net, w = build(coins)
    print(ct.perf_line("iter-001 XS-mom", net, reveal_oos=args.confirm))
    print(f"  regimes (IS): {ct.regime_sharpe(ct.is_only(net))}")
    print(f"  turnover/day: {ct.turnover(w, ct.LO0, ct.OOS_CUTOFF):.3f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -k iter001 -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check analysis/portfolio/tradfi/iter_001_xsmom.py tests/ --fix && uv run ruff format analysis/portfolio/tradfi/ tests/
git add analysis/portfolio/tradfi/iter_001_xsmom.py tests/test_portfolio_tradfi_foundation.py
git commit -m "feat(tradfi): iter-001 dollar-neutral cross-sectional momentum anchor"
```

---

### Task 7: Skill file + diary + baseline scaffolding

**Files:**
- Create: `.claude/commands/portfolio-tradfi.md`
- Create: `diary-portfolio-tradfi/EXPLORATION-001.md` (template)
- Create: `BASELINE_TRADFI.md`

**Interfaces:** none (documentation). This task has no test; its deliverable is the committed skill that future iterations invoke.

- [ ] **Step 1: Write the skill file**

Create `.claude/commands/portfolio-tradfi.md` adapting `.claude/commands/portfolio-iteration.md` with: the tradfi mission (market-neutral L/S Binance TradFi single-company stock perps, daily bars, Sharpe metric, all-weather); the 8 pillars and sacred constants from the design spec (`docs/superpowers/specs/2026-06-30-portfolio-tradfi-design.md`); the agent-driven roles (QR → QE/risk → critic with MANDATORY future-bar AND same-bar leak check); the cadence (EXPLORATION ≤2h IS-only, CONFIRMATION reveals OOS via `--confirm`); the NO-CHEATING rules; the foundation file map (`analysis/portfolio/tradfi/`); and the roadmap (iter-001 anchor → iter-002 beta-neutral → iter-003 sector-neutral → factor layering). Keep it ~100 lines, same shape as `portfolio-iteration.md`.

- [ ] **Step 2: Write the diary template and baseline stub**

`diary-portfolio-tradfi/EXPLORATION-001.md`: headers for Hypothesis / Change / IS numbers (Sharpe, maxDD, per-regime) / Leak-check result / Critic verdict / Next. `BASELINE_TRADFI.md`: "No baseline yet — iter-001 is the candidate anchor; promoted only at the first CONFIRMATION (critic PASS, OOS revealed)."

- [ ] **Step 3: Verify the skill is discoverable**

Run: `ls .claude/commands/portfolio-tradfi.md && head -1 .claude/commands/portfolio-tradfi.md`
Expected: file exists; first line is the H1 title.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/portfolio-tradfi.md diary-portfolio-tradfi/ BASELINE_TRADFI.md
git commit -m "feat(tradfi): portfolio-tradfi skill + diary/baseline scaffolding"
```

---

### Task 8: Foundation green + real-data smoke (gate before iterating)

**Files:** none new — runs the full foundation.

- [ ] **Step 1: Full foundation test sweep**

Run: `uv run pytest tests/test_portfolio_tradfi_foundation.py -q`
Expected: all PASS (synthetic-data tests; ~12 tests).

- [ ] **Step 2: Smoke-ingest a few names (network; may be slow)**

Run: `uv run python analysis/portfolio/tradfi/ingest_dukascopy_stocks.py --symbols AAPLUSDT,MSFTUSDT,JPMUSDT,XOM_SKIP 2>&1 | tail`
Expected: `data/AAPLUSDT/1d.csv` etc. written with multi-year daily bars. If `npx`/network is unavailable in this environment, record that and defer the real ingest to a run with network — the synthetic tests already prove the logic.

- [ ] **Step 3: iter-001 IS smoke (only if data ingested)**

Run: `uv run python analysis/portfolio/tradfi/iter_001_xsmom.py`
Expected: one `iter-001 XS-mom IS_Sharpe=...` line (NO OOS), a per-regime line, turnover. OOS must NOT print without `--confirm`.

- [ ] **Step 4: Commit any data-dir/gitignore housekeeping**

```bash
git add -A && git commit -m "chore(tradfi): foundation green; iter-001 IS smoke" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage:** universe (T1) ✓ · daily core + OOS-hidden (T2) ✓ · future+same-bar leak (T3) ✓ · beta/sector neutral (T4) ✓ · Dukascopy daily data (T5) ✓ · iter-001 dollar-neutral anchor (T6) ✓ · skill + diary + baseline (T7) ✓ · all-weather regime scorecard (T2 `regime_sharpe`, T6 prints it) ✓ · `--confirm` OOS gate (T2 `perf_line`, T6) ✓. iter-002 beta-neutral / iter-003 sector-neutral are deliberately OUT of this foundation plan — they are the first EXPLORATIONs run via the skill, using the T4 neutralizers.

**Placeholder scan:** the `JNJ_PLACEHOLDER` marker in T5 is popped immediately and is intentional scaffolding for the maintainer to extend the INSTRUMENTS map; all other code blocks are complete and runnable.

**Type consistency:** `net_from_raw -> (pd.Series, pd.DataFrame)` consumed identically in T3/T6; `xsmom_raw`/`build` signatures match across T6 test and impl; neutralizer signatures in T4 match their T6 usage (`dollar_neutralize(raw)`); `regime_sharpe`/`perf_line` names consistent T2↔T6.
