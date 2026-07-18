"""crypto-cup-01 evaluator — organizer-owned scoring on the 8h Binance-perp grid.

Teams emit RAW signed weight panels only (``build_raw_weights(pn, aux)``); this module owns
everything after: the weekly top-40 eligibility mask, gross-normalisation, per-name / net
caps, the ``.shift(1)`` decision lag, taker + liquidity-scaled slippage cost on turnover,
FUNDING P&L, portfolio vol-targeting, and all metrics. ``ret_fwd`` is scoring-only and is
NEVER handed to a strategy (``team_view`` strips it).

Exact order of operations (net_series):
  raw → eligibility mask (weekly floor: outside-top-40 weights zeroed at decision time)
      → normalize_and_cap (gross=1, |w_i|≤0.10, |Σw|≤0.25)
      → w = capped.shift(1)                       # decide close[t-1], fill open[t]
      → pnl  = Σ w·ret_fwd                        # ret_fwd = open[t+1]/open[t] − 1
      → cost = Σ |Δw|·(COST_SIDE·cost_mult + slip_side·slip_mult)
      → fpnl = −Σ w·fund_win                      # held book pays the candle's funding events
      → net  = vol_target(pnl + fpnl − cost)      # past-only, 1%/candle target, ≤3× lev

Funding model (replaces iter_004's nearest-within-4h, which silently DROPPED events for
symbols on 4h/1h funding intervals): every event with timestamp in ``(open[t], open[t+1]]``
is SUMMED into ``fund_win[t]`` and charged to the book held during candle t. Timestamps
within 60s of an 8h boundary are snapped first (Binance stamps events with ms jitter).
``aux["funding"]`` exposes the SAME panel to teams — events of candle t are knowable at
candle t's close, exactly like ``close[t]`` (same-bar convention, harness-enforced).

Data enters ONLY through ``load_is_bundle`` / ``build_panels``: the manifest is re-hashed on
every load and any row past the IS boundary raises ``ISBoundaryError``.
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from portfolio_tournament import constants as tc  # noqa: E402

TEAM_PANELS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)

# aux key -> column in data_is/<SYM>/oi.csv. Row open_time=T aggregates the 5-min metrics of
# [T, T+8h): SAME-BAR info for candle T (knowable at T's close), like close[T]. NaN where a
# symbol has no OI history (pre-2020-09 or dead delisted names) — teams must NaN-tolerate.
AUX_OI_COLS = {
    "oi": "sum_open_interest",
    "oi_value": "sum_open_interest_value",
    "tt_ls_accounts": "count_toptrader_long_short_ratio",
    "tt_ls_positions": "sum_toptrader_long_short_ratio",
    "ls_accounts": "count_long_short_ratio",
    "taker_ls_vol": "sum_taker_long_short_vol_ratio",
}
AUX_KEYS = (*AUX_OI_COLS, "funding", "eligibility")

_FUNDING_SNAP_MS = 60_000  # snap funding timestamps within 60s of an 8h boundary


class ISBoundaryError(RuntimeError):
    """A row past the IS boundary reached the team-facing loader."""


# ---------------------------------------------------------------- loading -----------------------
def load_is_bundle(
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    verify: bool = True,
) -> dict:
    """Manifest-driven raw-data bundle from the frozen IS snapshot, boundary-enforced.

    Returns {"klines": {sym: df}, "funding": {sym: Series}, "oi": {sym: df}, "elig": df} —
    every frame indexed by ms ``open_time`` (funding by ms ``funding_time``).
    """
    from portfolio_tournament import snapshot as tsnap

    if verify:
        tsnap.verify_manifest(snapshot_dir, manifest_path)
    manifest = tsnap.read_manifest(manifest_path)
    symbols = tsnap.manifest_symbols(manifest)

    klines: dict[str, pd.DataFrame] = {}
    funding: dict[str, pd.Series] = {}
    oi: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        k = pd.read_csv(snapshot_dir / sym / "8h.csv")
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        klines[sym] = k
        fp = snapshot_dir / sym / "funding.csv"
        if fp.exists():
            f = pd.read_csv(fp).drop_duplicates(subset="funding_time", keep="last")
            funding[sym] = f.set_index("funding_time")["funding_rate"].astype(float).sort_index()
        op = snapshot_dir / sym / "oi.csv"
        if op.exists():
            o = pd.read_csv(op)
            o = o.drop_duplicates(subset="open_time", keep="last").set_index("open_time")
            oi[sym] = o.sort_index()
    elig = pd.read_csv(snapshot_dir / "_universe" / "eligibility.csv", index_col="open_time")
    bundle = {"klines": klines, "funding": funding, "oi": oi, "elig": elig}
    check_bundle_boundary(bundle, tc.IS_END_MS)
    return bundle


def check_bundle_boundary(bundle: dict, end_ms: int) -> None:
    """Raise ``ISBoundaryError`` if ANY row/event in the bundle is stamped past ``end_ms``."""
    for sym, df in bundle["klines"].items():
        if len(df) and int(df.index.max()) > end_ms:
            raise ISBoundaryError(f"{sym}: kline open_time {int(df.index.max())} past {end_ms}")
    for sym, s in bundle["funding"].items():
        if len(s) and int(s.index.max()) > end_ms:
            raise ISBoundaryError(f"{sym}: funding_time {int(s.index.max())} past {end_ms}")
    for sym, df in bundle["oi"].items():
        if len(df) and int(df.index.max()) > end_ms:
            raise ISBoundaryError(f"{sym}: oi open_time {int(df.index.max())} past {end_ms}")
    if len(bundle["elig"]) and int(bundle["elig"].index.max()) > end_ms:
        raise ISBoundaryError(f"eligibility row {int(bundle['elig'].index.max())} past {end_ms}")


# ---------------------------------------------------------------- panels ------------------------
def funding_candle_panel(
    funding: dict[str, pd.Series], grid_ms: pd.Index, cols: list[str]
) -> pd.DataFrame:
    """Per-candle summed funding events: fund_win[t] = Σ rate over ts ∈ (open[t], open[t+1]].

    Boundary events stamped with ms jitter are snapped to the boundary first. An event at
    exactly ``open[t+1]`` belongs to candle t (the book held THROUGH the boundary pays it —
    the live engine rebalances just after the candle open, i.e. after the funding snapshot).
    Missing symbols / candles → 0.0 (no event, no charge).
    """
    step = tc.STEP_MS
    out: dict[str, pd.Series] = {}
    for sym in cols:
        s = funding.get(sym)
        if s is None or not len(s):
            continue
        ts = s.index.to_numpy(dtype=np.int64)
        near = (np.round(ts / step) * step).astype(np.int64)
        snapped = np.where(np.abs(ts - near) <= _FUNDING_SNAP_MS, near, ts)
        cand = ((snapped - 1) // step) * step
        out[sym] = pd.Series(s.to_numpy(dtype=float)).groupby(cand).sum()
    panel = pd.DataFrame(out).reindex(index=grid_ms, columns=cols).fillna(0.0)
    return panel


def slip_side_panel(qv: pd.DataFrame) -> pd.DataFrame:
    """Per-coin per-candle slippage fraction (past-only, liquidity-scaled).

    slip_bps = clip(SLIP_A + SLIP_B / dvol_$M, SLIP_FLOOR, SLIP_CAP);  dvol from the trailing
    LIQ_WIN-candle mean quote-volume, ``.shift(1)``, ×3 to a daily figure. NaN liquidity
    (un-warmed / un-listed) → 0 slip — the eligibility mask keeps those untradable anyway.
    """
    liq = qv.rolling(tc.LIQ_WIN).mean().shift(1)
    dvol_m = liq * 3.0 / 1e6
    bps = (tc.SLIP_A + tc.SLIP_B / dvol_m.clip(lower=1e-6)).clip(
        lower=tc.SLIP_FLOOR, upper=tc.SLIP_CAP
    )
    bps = bps.where(dvol_m.notna(), 0.0)
    return (bps / 1e4).fillna(0.0)


def build_panels(bundle: dict) -> tuple[dict, dict, dict]:
    """(pn, aux, scoring) from a raw bundle — the single panel-construction code path.

    pn      : the 9 TEAM_PANELS + ``ret_fwd`` (scoring-only), DatetimeIndex × sorted symbols.
    aux     : funding + 6 OI/ratio panels + eligibility (bool) + seed — team-visible copies
              are made by ``make_team_aux``; these are the evaluator's originals.
    scoring : fund_win / slip_side / elig references used by ``net_series``.
    """
    klines = bundle["klines"]
    cols = sorted(klines)
    lo = min(int(df.index.min()) for df in klines.values())
    hi = max(int(df.index.max()) for df in klines.values())
    grid_ms = pd.Index(pd.RangeIndex(lo, hi + tc.STEP_MS, tc.STEP_MS), name="open_time")
    dt = pd.to_datetime(grid_ms, unit="ms")

    pn: dict[str, pd.DataFrame] = {}
    for fieldname in TEAM_PANELS:
        f = pd.DataFrame({s: klines[s][fieldname] for s in cols}).astype(float).reindex(grid_ms)
        f.index = dt
        pn[fieldname] = f
    pn["ret_fwd"] = pn["open"].shift(-1) / pn["open"] - 1.0

    fund_win = funding_candle_panel(bundle["funding"], grid_ms, cols)
    fund_win.index = dt

    aux: dict = {}
    oi_bundle = bundle["oi"]
    for key, col in AUX_OI_COLS.items():
        avail = {
            s: oi_bundle[s][col].astype(float)
            for s in cols
            if s in oi_bundle and col in oi_bundle[s].columns
        }
        if avail:
            f = pd.DataFrame(avail).reindex(index=grid_ms, columns=cols)
        else:
            f = pd.DataFrame(np.nan, index=grid_ms, columns=cols)
        f.index = dt
        aux[key] = f
    aux["funding"] = fund_win

    elig = bundle["elig"].reindex(index=grid_ms, columns=cols).fillna(0).astype(bool)
    elig.index = dt
    aux["eligibility"] = elig
    aux["seed"] = tc.SEED

    scoring = {
        "fund_win": fund_win,
        "slip_side": slip_side_panel(pn["quote_volume"]),
        "elig": elig,
    }
    return pn, aux, scoring


def team_view(pn: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """The ONLY market view handed to strategies: the 9 panels, ``ret_fwd`` stripped."""
    return {k: pn[k].copy() for k in TEAM_PANELS}


def make_team_aux(aux: dict) -> dict:
    """Deep-copied aux for the strategy — teams can never mutate the evaluator's originals."""
    return {k: (v.copy() if isinstance(v, pd.DataFrame | pd.Series) else v) for k, v in aux.items()}


def load_is_panels(
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    verify: bool = True,
) -> tuple[dict, dict, dict]:
    """(pn incl. ret_fwd, aux, scoring) from the frozen snapshot. Team code must only ever
    see ``team_view(pn)`` + ``make_team_aux(aux)`` — the harness enforces that discipline."""
    return build_panels(load_is_bundle(snapshot_dir, manifest_path, verify=verify))


# ---------------------------------------------------------------- caps --------------------------
def _trim_net(w: pd.DataFrame) -> pd.DataFrame:
    """Scale down the heavier side row-wise so |Σw| <= NET_CAP (magnitudes only shrink)."""
    pos = w.clip(lower=0.0)
    neg = w.clip(upper=0.0)
    pos_sum = pos.sum(axis=1)
    neg_sum = (-neg).sum(axis=1)
    net = pos_sum - neg_sum
    with np.errstate(divide="ignore", invalid="ignore"):
        k_pos = pd.Series(
            np.where(net > tc.NET_CAP, (tc.NET_CAP + neg_sum) / pos_sum, 1.0), index=w.index
        )
        k_neg = pd.Series(
            np.where(net < -tc.NET_CAP, (pos_sum + tc.NET_CAP) / neg_sum, 1.0), index=w.index
        )
    k_pos = k_pos.clip(upper=1.0).fillna(1.0)
    k_neg = k_neg.clip(upper=1.0).fillna(1.0)
    return pos.mul(k_pos, axis=0) + neg.mul(k_neg, axis=0)


def _gross(w: pd.DataFrame) -> pd.Series:
    """Row gross with values within 1 ulp-band of 1.0 snapped to exactly 1.0 — keeps
    re-normalisation a bit-exact no-op on already-normalised books (idempotence)."""
    g = w.abs().sum(axis=1)
    return g.mask((g - 1.0).abs() <= 1e-12, 1.0).replace(0.0, np.nan)


def normalize_and_cap(raw: pd.DataFrame) -> pd.DataFrame:
    """Organizer-owned book construction: gross-normalise to 1, then iterate per-name clip
    (|w_i| <= PER_NAME_CAP) + net trim (|Σw| <= NET_CAP) + re-normalise; final clip+trim WITHOUT
    re-normalise so every constraint holds exactly (gross may end < 1 — e.g. a pure directional
    book collapses to the net cap; the portfolio vol-target re-levers the return stream).
    All-zero rows stay zero. Identity on books already satisfying gross=1 + both caps."""
    w = raw
    if any(dt.kind != "f" for dt in w.dtypes):
        w = w.astype(float)
    if not np.isfinite(w.to_numpy()).all():  # sanitize ONLY when needed — a no-op pass would
        w = w.replace([np.inf, -np.inf], np.nan).fillna(0.0)  # alter layout and ulp-drift sums
    w = w.div(_gross(w), axis=0).fillna(0.0)
    for _ in range(tc.CAP_ITERS):
        capped = _trim_net(w.clip(-tc.PER_NAME_CAP, tc.PER_NAME_CAP))
        if capped.equals(w):  # no violation anywhere — clip+trim were bit-exact no-ops
            return w
        w = capped.div(_gross(capped), axis=0).fillna(0.0)
    return _trim_net(w.clip(-tc.PER_NAME_CAP, tc.PER_NAME_CAP))


def conform_raw(raw: pd.DataFrame, pn: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Align a strategy's raw output onto the panel grid: panel index × tradable columns.
    Unknown columns are dropped; missing columns/rows become flat (0 after fillna)."""
    if not isinstance(raw, pd.DataFrame):
        raise TypeError(f"build_raw_weights must return a DataFrame, got {type(raw).__name__}")
    grid = pn["open"]
    return raw.reindex(index=grid.index, columns=grid.columns)


# ---------------------------------------------------------------- metrics helpers ---------------
def msharpe(net: pd.Series, lo, hi) -> float:
    """Annualised Sharpe from MONTHLY summed returns over [lo, hi) (√12 annualisation)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")


def maxdd(net: pd.Series) -> float:
    eq = (1 + net).cumprod()
    return float((eq / eq.cummax() - 1).min())


def vol_target(net: pd.Series) -> pd.Series:
    """Past-only per-candle vol-target (1%/candle, PORT_VOL_WIN trailing, ≤MAX_LEV)."""
    rv = net.rolling(tc.PORT_VOL_WIN).std().shift(1)
    scale = (tc.TARGET_VOL / rv).clip(upper=tc.MAX_LEV).fillna(0.0)
    return net * scale


def regime_of(idx: pd.DatetimeIndex) -> pd.Series:
    out = pd.Series("other", index=idx, dtype=object)
    for label, lo, hi in tc._REGIMES:
        m = (idx >= pd.Timestamp(lo)) & (idx < pd.Timestamp(hi))
        out[m] = label
    return out


def regime_sharpe(net: pd.Series) -> dict[str, float]:
    """Per-regime annualised Sharpe (all-weather scorecard over the fixed crypto regimes)."""
    reg = regime_of(net.index)
    out: dict[str, float] = {}
    for label in ("bull", "bear", "chop"):
        sub = net[reg == label]
        g = sub.groupby(sub.index.to_period("M")).sum()
        out[label] = (
            float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
        )
    return out


# ---------------------------------------------------------------- evaluation --------------------
def net_series(
    raw: pd.DataFrame,
    pn: dict[str, pd.DataFrame],
    scoring: dict,
    *,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
    apply_funding: bool = True,
) -> tuple[pd.Series, pd.DataFrame, dict]:
    """Raw book -> (vol-targeted net return, lagged weight book, component parts).

    The weekly floor is enforced HERE: weights outside the current top-40 list are zeroed at
    decision time, so a coin dropping out at a Monday refresh is force-closed at the next
    candle open (≤8h later) and the close-out turnover IS costed.
    """
    masked = raw.where(scoring["elig"], 0.0)
    w = normalize_and_cap(masked).shift(1)
    ret_fwd = pn["ret_fwd"].reindex(columns=w.columns)
    pnl = (w * ret_fwd).sum(axis=1)
    dw = (w - w.shift(1)).abs()
    slip = scoring["slip_side"].reindex(index=w.index, columns=w.columns).fillna(0.0)
    cost = (dw * (tc.COST_SIDE * cost_mult + slip * slip_mult)).sum(axis=1)
    if apply_funding:
        fund_win = scoring["fund_win"].reindex(index=w.index, columns=w.columns).fillna(0.0)
        fpnl = -(w * fund_win).sum(axis=1)
    else:
        fpnl = pd.Series(0.0, index=w.index)
    raw_net = (pnl + fpnl - cost).dropna()
    rv = raw_net.rolling(tc.PORT_VOL_WIN).std().shift(1)
    scale = (tc.TARGET_VOL / rv).clip(upper=tc.MAX_LEV).fillna(0.0)
    net = raw_net * scale
    parts = {"pnl": pnl, "fpnl": fpnl, "cost": cost, "raw_net": raw_net, "scale": scale}
    return net, w, parts


@dataclass(frozen=True)
class Metrics:
    sharpe: float
    maxdd: float
    ann_turnover: float
    total_return: float
    n_months: int
    regime_sharpe: dict[str, float] = field(default_factory=dict)
    median_names_long: float = float("nan")
    median_names_short: float = float("nan")
    mean_gross: float = float("nan")
    mean_net: float = float("nan")
    total_funding_pnl: float = float("nan")
    total_cost: float = float("nan")

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate(
    net: pd.Series,
    w: pd.DataFrame,
    parts: dict | None = None,
    *,
    lo: pd.Timestamp,
    hi: pd.Timestamp,
) -> Metrics:
    """Score one (net, weight-book) pair over [lo, hi)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    ws = w[(w.index >= lo) & (w.index < hi)]
    active = ws.abs().sum(axis=1) > 0
    n_long = (ws > 1e-12).sum(axis=1)[active]
    n_short = (ws < -1e-12).sum(axis=1)[active]
    eq = (1 + s).cumprod()
    to = (ws - ws.shift(1)).abs().sum(axis=1)
    tf = tcost = float("nan")
    if parts is not None:
        fp = parts["fpnl"]
        cp = parts["cost"]
        tf = float(fp[(fp.index >= lo) & (fp.index < hi)].sum())
        tcost = float(cp[(cp.index >= lo) & (cp.index < hi)].sum())
    return Metrics(
        sharpe=msharpe(net, lo, hi),
        maxdd=maxdd(s) if len(s) else float("nan"),
        ann_turnover=float(to.mean() * tc.CANDLES_PER_YEAR) if len(to) else float("nan"),
        total_return=float(eq.iloc[-1] - 1.0) if len(s) else float("nan"),
        n_months=int(s.groupby(s.index.to_period("M")).count().shape[0]) if len(s) else 0,
        regime_sharpe=regime_sharpe(s),
        median_names_long=float(n_long.median()) if len(n_long) else float("nan"),
        median_names_short=float(n_short.median()) if len(n_short) else float("nan"),
        mean_gross=float(ws.abs().sum(axis=1)[active].mean()) if active.any() else 0.0,
        mean_net=float(ws.sum(axis=1)[active].mean()) if active.any() else 0.0,
        total_funding_pnl=tf,
        total_cost=tcost,
    )


def run_is(
    raw: pd.DataFrame,
    pn: dict[str, pd.DataFrame],
    scoring: dict,
    *,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
) -> tuple[pd.Series, pd.DataFrame, Metrics]:
    """One-call IS scoring: conform -> mask+caps -> net -> metrics over the IS window."""
    raw = conform_raw(raw, pn)
    net, w, parts = net_series(raw, pn, scoring, cost_mult=cost_mult, slip_mult=slip_mult)
    return net, w, evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
