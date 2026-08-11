"""Shared EDA panel builder for team-05.

Builds a point-in-time panel of 8h bars for the top-20 universe, with the shock-signature
features the lane is about. Everything here is past-only by construction: every feature at
decision boundary ``t`` uses only the bar that CLOSED at ``t`` and bars before it.

This module is RESEARCH ONLY. It computes no floors, no Sharpe-vs-floor verdict and no ranking
score. Every scored number team-05 acts on comes out of the organiser's harness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"
BARS_PER_YEAR = 1095.0


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bars = pd.read_parquet(f"{IS_ROOT}/bars.parquet")
    funding = pd.read_parquet(f"{IS_ROOT}/funding.parquet")
    membership = pd.read_parquet(f"{IS_ROOT}/membership.parquet")
    return bars, funding, membership


def membership_mask(bars: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    """Boolean (open_time x symbol) frame: was this symbol a point-in-time member?

    A bar with ``open_time == T`` closes at ``T + 8h``, which is the decision boundary it informs.
    Membership at that boundary is the latest reconstitution at or before it.
    """
    boundaries = pd.DatetimeIndex(sorted(bars["open_time"].unique())) + pd.Timedelta(hours=8)
    recon = membership.copy()
    recon["reconstitution_time"] = pd.to_datetime(recon["reconstitution_time"], utc=True)
    wide = (
        recon.assign(member=True)
        .pivot_table(index="reconstitution_time", columns="symbol", values="member", aggfunc="max")
        .fillna(False)
        .astype(bool)
    )
    aligned = wide.reindex(wide.index.union(boundaries)).ffill().reindex(boundaries).fillna(False)
    aligned.index = boundaries - pd.Timedelta(hours=8)  # index by open_time again
    return aligned.astype(bool)


def build_panel(lookback: int = 60) -> dict[str, pd.DataFrame]:
    """Wide frames indexed by ``open_time``, columns = symbol."""
    bars, funding, membership = load_raw()
    bars = bars.sort_values(["symbol", "open_time"])

    def wide(col: str) -> pd.DataFrame:
        return bars.pivot(index="open_time", columns="symbol", values=col).sort_index()

    op, hi, lo, cl = wide("open"), wide("high"), wide("low"), wide("close")
    qv, tc = wide("quote_volume"), wide("trade_count")
    tbq = wide("taker_buy_quote_volume")

    ret = cl.pct_change()
    # trailing scale, strictly past: shift(1) so the shock bar never sets its own scale
    sigma = ret.rolling(lookback, min_periods=lookback // 2).std().shift(1)
    rng = (hi - lo) / cl
    rng_scale = rng.rolling(lookback, min_periods=lookback // 2).median().shift(1)
    qv_scale = qv.rolling(lookback, min_periods=lookback // 2).median().shift(1)
    tc_scale = tc.rolling(lookback, min_periods=lookback // 2).median().shift(1)

    # signed move normalised by its own recent scale
    z = ret / sigma
    # range relative to its own recent scale
    rr = rng / rng_scale
    # activity spikes
    vspike = qv / qv_scale
    tspike = tc / tc_scale
    # price impact per unit of dollar flow, relative to normal:
    # how much range this bar produced per unit of (relative) volume
    impact = rr / vspike
    # taker imbalance (used only as a disclosed diagnostic, never as the driver)
    taker_imb = (2.0 * tbq - qv) / qv

    # funding: the most recent settled rate strictly before the bar close
    fund = funding.copy()
    fund["funding_time"] = pd.to_datetime(fund["funding_time"], utc=True)
    fwide = fund.pivot_table(
        index="funding_time", columns="symbol", values="funding_rate", aggfunc="last"
    ).sort_index()
    # 8h-interval normalisation: some symbols settle 4-hourly, so sum into the 8h bucket
    f8 = fwide.resample("8h", label="left", closed="left").sum(min_count=1)
    f8 = f8.reindex(cl.index).ffill(limit=3)

    mask = membership_mask(bars, membership).reindex(index=cl.index, columns=cl.columns)
    mask = mask.fillna(False).astype(bool)
    tradable = mask & cl.notna() & sigma.notna() & (sigma > 0)

    return {
        "close": cl,
        "open": op,
        "ret": ret,
        "sigma": sigma,
        "z": z,
        "rr": rr,
        "vspike": vspike,
        "tspike": tspike,
        "impact": impact,
        "taker_imb": taker_imb,
        "funding": f8,
        "qv": qv,
        "tradable": tradable,
    }


def forward_returns(close: pd.DataFrame, horizons=(1, 2, 3, 6)) -> dict[int, pd.DataFrame]:
    """Return realised over the h bars AFTER the decision boundary.

    A decision taken at the close of bar ``i`` fills at ``open[i+1]``, so the honest forward
    return is ``open[i+1+h] / open[i+1] - 1``. Using opens rather than closes matches the
    organiser's execution contract.
    """
    return {}


def forward_from_open(op: pd.DataFrame, horizons=(1, 2, 3, 6)) -> dict[int, pd.DataFrame]:
    out = {}
    for h in horizons:
        out[h] = op.shift(-(1 + h)) / op.shift(-1) - 1.0
    return out


def demean(frame: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectionally demean across point-in-time members (removes the market factor)."""
    masked = frame.where(mask)
    return masked.sub(masked.mean(axis=1), axis=0)


def summarise(name: str, values: np.ndarray) -> str:
    values = values[np.isfinite(values)]
    if values.size == 0:
        return f"{name:<38} n=0"
    mean = values.mean()
    se = values.std(ddof=1) / np.sqrt(values.size)
    return (
        f"{name:<38} n={values.size:>7d}  mean={mean * 1e4:>8.2f}bp  "
        f"t={mean / se if se > 0 else float('nan'):>6.2f}  hit={float((values > 0).mean()):>5.3f}"
    )
