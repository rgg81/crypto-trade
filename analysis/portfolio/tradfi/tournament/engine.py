"""tradfi-cup-01 evaluator — organizer-owned scoring on the proven ``core_tradfi`` primitives.

Teams emit RAW signed weight panels only (``build_raw_weights(pn, aux)``); this module owns
everything after: gross-normalisation, per-name / net caps, the ``.shift(1)`` decision lag,
taker cost on turnover, portfolio vol-targeting, and all metrics. ``ret_fwd`` is scoring-only
and is NEVER handed to a strategy (``team_view`` strips it).

Data enters ONLY through ``load_is_coins`` / ``load_is_panels``: the manifest is re-hashed on
every load and any bar past the IS boundary raises ``ISBoundaryError``.
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

import core_tradfi as ct  # noqa: E402
from tournament import constants as tc  # noqa: E402  (package-style; see __init__.py)
from universe_tradfi import SECTOR_MAP  # noqa: E402

TEAM_PANELS = ("open", "high", "low", "close", "volume")


class ISBoundaryError(RuntimeError):
    """A bar past the IS boundary reached the team-facing loader."""


# ---------------------------------------------------------------- loading -----------------------
def load_is_coins(
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    verify: bool = True,
) -> dict[str, pd.DataFrame]:
    """Manifest-driven coins dict from the frozen IS snapshot (incl. VIX), boundary-enforced."""
    from tournament import snapshot as tsnap

    if verify:
        tsnap.verify_manifest(snapshot_dir, manifest_path)
    manifest = tsnap.read_manifest(manifest_path)
    symbols = sorted({Path(rel).parts[0] for rel in manifest["files"]})
    coins = ct.load_tradfi(symbols, snapshot_dir)
    for sym, df in coins.items():
        if len(df) and int(df.index.max()) > tc.IS_END_MS:
            raise ISBoundaryError(
                f"{sym}: bar open_time {int(df.index.max())} past IS end {tc.IS_END_MS}"
            )
    return coins


def panels_with_volume(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """``ct.panels`` plus an aligned float volume panel (core's panels() lacks volume)."""
    tradable = {s: df for s, df in coins.items() if s != tc.VIX_SYM}
    pn = ct.panels(tradable)
    cols = list(tradable)
    ms_index = pd.DataFrame({s: tradable[s]["open"] for s in cols}).astype(float).sort_index().index
    vol = pd.DataFrame({s: tradable[s]["volume"] for s in cols}).astype(float).reindex(ms_index)
    vol.index = pd.to_datetime(ms_index, unit="ms")
    pn["volume"] = vol
    return pn


def vix_series(coins: dict[str, pd.DataFrame]) -> pd.Series | None:
    """VIX close as a DatetimeIndex Series (or None when absent)."""
    df = coins.get(tc.VIX_SYM)
    if df is None:
        return None
    s = df["close"].astype(float)
    s.index = pd.to_datetime(df.index, unit="ms")
    return s


def team_view(pn: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """The ONLY market view handed to strategies: OHLCV copies, ``ret_fwd`` stripped."""
    return {k: pn[k].copy() for k in TEAM_PANELS}


def make_aux(coins: dict[str, pd.DataFrame], *, seed: int = tc.SEED) -> dict:
    vix = vix_series(coins)
    tickers = [s for s in coins if s != tc.VIX_SYM]
    return {
        "vix": vix.copy() if vix is not None else None,
        "sector_map": {t: SECTOR_MAP.get(t, "Unknown") for t in tickers},
        "seed": seed,
    }


def load_is_panels(
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    verify: bool = True,
) -> tuple[dict[str, pd.DataFrame], dict]:
    """(full panels incl. ret_fwd + volume, aux) from the frozen snapshot. Team code must only
    ever see ``team_view(pn)`` — callers own that discipline; the harness enforces it."""
    coins = load_is_coins(snapshot_dir, manifest_path, verify=verify)
    return panels_with_volume(coins), make_aux(coins)


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


# ---------------------------------------------------------------- evaluation --------------------
def net_series(
    raw: pd.DataFrame,
    ret_fwd: pd.DataFrame,
    *,
    cost_mult: float = 1.0,
    funding: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    """Capped book -> (vol-targeted net return, lagged weight book). Mirrors ``ct.net_from_raw``
    with the cap stage inserted pre-shift; funding P&L = −w·f on the held (lagged) book."""
    w = normalize_and_cap(raw).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * tc.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    fund = 0.0
    if funding is not None:
        fund = (w * funding.reindex(index=w.index, columns=w.columns).fillna(0.0)).sum(axis=1)
    net = (pnl - fund - cost).dropna()
    return ct.vol_target(net), w


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

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate(net: pd.Series, w: pd.DataFrame, *, lo: pd.Timestamp, hi: pd.Timestamp) -> Metrics:
    """Score one (net, weight-book) pair over [lo, hi) with the core metric helpers."""
    s = net[(net.index >= lo) & (net.index < hi)]
    ws = w[(w.index >= lo) & (w.index < hi)]
    active = ws.abs().sum(axis=1) > 0
    n_long = (ws > 1e-12).sum(axis=1)[active]
    n_short = (ws < -1e-12).sum(axis=1)[active]
    eq = (1 + s).cumprod()
    return Metrics(
        sharpe=float(ct.msharpe(net, lo, hi)),
        maxdd=float(ct.maxdd(s)) if len(s) else float("nan"),
        ann_turnover=float(ct.turnover(ws) * ct.CANDLES_PER_YEAR),
        total_return=float(eq.iloc[-1] - 1.0) if len(s) else float("nan"),
        n_months=int(s.groupby(s.index.to_period("M")).count().shape[0]) if len(s) else 0,
        regime_sharpe={k: float(v) for k, v in ct.regime_sharpe(s).items()},
        median_names_long=float(n_long.median()) if len(n_long) else float("nan"),
        median_names_short=float(n_short.median()) if len(n_short) else float("nan"),
        mean_gross=float(ws.abs().sum(axis=1)[active].mean()) if active.any() else 0.0,
        mean_net=float(ws.sum(axis=1)[active].mean()) if active.any() else 0.0,
    )


def run_is(
    raw: pd.DataFrame, pn: dict[str, pd.DataFrame], *, cost_mult: float = 1.0
) -> tuple[pd.Series, pd.DataFrame, Metrics]:
    """One-call IS scoring: conform -> caps -> net -> metrics over the IS window."""
    raw = conform_raw(raw, pn)
    net, w = net_series(raw, pn["ret_fwd"], cost_mult=cost_mult)
    return net, w, evaluate(net, w, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
