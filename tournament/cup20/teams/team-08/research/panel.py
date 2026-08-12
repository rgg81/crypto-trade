"""Team 08 offline research panel.

Builds a dense (boundary x symbol) panel from the team's own data root, plus the
funding-event observation series the strategy is actually allowed to see at each
decision (funding rows strictly before the boundary).

Nothing here is a scorer. Every number the certificate cites as a *score* comes from
the organiser commands; this module exists so the design space can be mapped before a
trial is spent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"
IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
INTERVAL = pd.Timedelta(hours=8)


def build_panel(cache: str | None = None) -> dict:
    if cache is not None:
        try:
            data = np.load(cache, allow_pickle=True)
            return {k: data[k] for k in data.files}
        except FileNotFoundError:
            pass

    bars = pd.read_parquet(f"{IS_ROOT}/bars.parquet")
    funding = pd.read_parquet(f"{IS_ROOT}/funding.parquet")
    membership = pd.read_parquet(f"{IS_ROOT}/membership.parquet")

    bars = bars[(bars["open_time"] >= IS_START - pd.Timedelta(days=400))].copy()
    times = pd.DatetimeIndex(sorted(bars["open_time"].unique()))
    times = times[(times >= IS_START) & (times < IS_END)]
    symbols = sorted(membership["symbol"].unique())
    s_index = {s: i for i, s in enumerate(symbols)}

    def pivot(col: str) -> np.ndarray:
        p = bars.pivot(index="open_time", columns="symbol", values=col)
        p = p.reindex(index=times, columns=symbols)
        return p.to_numpy(dtype=float)

    opens = pivot("open")
    closes = pivot("close")
    qvol = pivot("quote_volume")

    # membership at each boundary: forward-fill the weekly reconstitution rows
    recon = sorted(membership["reconstitution_time"].unique())
    recon = pd.DatetimeIndex(recon)
    member = np.zeros((len(times), len(symbols)), dtype=bool)
    by_recon = {t: g["symbol"].tolist() for t, g in membership.groupby("reconstitution_time")}
    slot = recon.searchsorted(times, side="right") - 1
    for i, k in enumerate(slot):
        if k < 0:
            continue
        for sym in by_recon[recon[k]]:
            member[i, s_index[sym]] = True
    elig = member & np.isfinite(opens)

    # forward open-to-open return earned by exposure held from t to t+1
    fwd = np.full_like(opens, np.nan)
    fwd[:-1] = opens[1:] / opens[:-1] - 1.0

    # funding summed into the holding interval (t, t+1]
    fund_hold = np.zeros_like(opens)
    fsym = funding["symbol"].map(s_index)
    fmask = fsym.notna()
    f = funding[fmask].copy()
    f["si"] = fsym[fmask].astype(int)
    settle = pd.DatetimeIndex(f["settlement_time"])
    # bucket index k such that settle in (times[k], times[k+1]]
    k = times.searchsorted(settle, side="left") - 1
    ok = (k >= 0) & (k < len(times))
    np.add.at(fund_hold, (k[ok], f["si"].to_numpy()[ok]), f["funding_rate"].to_numpy()[ok])

    # ---- observation series: what the strategy may see strictly before boundary t ----
    # For every symbol, the sequence of funding events with funding_time < t.
    # We build, per boundary, the last L funding rates and the last L basis observations.
    fund_time = pd.DatetimeIndex(f["funding_time"])
    order = np.lexsort((fund_time.to_numpy(), f["si"].to_numpy()))
    f_si = f["si"].to_numpy()[order]
    f_rate = f["funding_rate"].to_numpy()[order]
    f_time = fund_time.asi8[order]
    f_mark = f["mark_price"].to_numpy()[order]
    f_mark_time = pd.DatetimeIndex(f["mark_time"]).asi8[order]

    # basis proxy: perp close at (or immediately before) mark_time versus the mark price.
    # Bars close at open_time + 8h - 1ms, so a mark stamped on the 8h grid lands 1ms after the
    # close of the bar that ends there.
    close_times = (times + INTERVAL - pd.Timedelta(milliseconds=1)).asi8
    # need the full close series, including pre-IS bars, for early observations
    all_times = pd.DatetimeIndex(sorted(bars["open_time"].unique()))
    all_close_times = (all_times + INTERVAL - pd.Timedelta(milliseconds=1)).asi8
    all_closes = (
        bars.pivot(index="open_time", columns="symbol", values="close")
        .reindex(index=all_times, columns=symbols)
        .to_numpy(dtype=float)
    )
    bi = np.searchsorted(all_close_times, f_mark_time, side="right") - 1
    gap = np.full(len(bi), np.inf)
    valid = bi >= 0
    gap[valid] = (f_mark_time[valid] - all_close_times[bi[valid]]) / 1e9
    perp = np.full(len(bi), np.nan)
    perp[valid] = all_closes[bi[valid], f_si[valid]]
    basis = np.where((gap <= 60.0) & np.isfinite(perp), perp / f_mark - 1.0, np.nan)

    return {
        "times": times.asi8,
        "close_times": close_times,
        "symbols": np.array(symbols),
        "opens": opens,
        "closes": closes,
        "qvol": qvol,
        "elig": elig,
        "fwd": fwd,
        "fund_hold": fund_hold,
        "f_si": f_si,
        "f_rate": f_rate,
        "f_time": f_time,
        "f_basis": basis,
    }


def observation_lags(panel: dict, depth: int) -> tuple[np.ndarray, np.ndarray]:
    """Per (boundary, symbol), the last ``depth`` funding rates and basis observations.

    Index 0 is the most recent observation strictly before the boundary. NaN where a
    symbol has fewer than ``depth`` prior events. Strictly causal by construction: the
    cut uses ``side='left'`` on funding_time against the decision timestamp, which is
    exactly what ``generate_targets`` does.
    """
    times = panel["times"]
    n_t, n_s = panel["opens"].shape
    rate = np.full((depth, n_t, n_s), np.nan)
    bas = np.full((depth, n_t, n_s), np.nan)
    f_si, f_time, f_rate, f_basis = (
        panel["f_si"],
        panel["f_time"],
        panel["f_rate"],
        panel["f_basis"],
    )
    for si in range(n_s):
        m = f_si == si
        if not m.any():
            continue
        ts, rs, bs = f_time[m], f_rate[m], f_basis[m]
        cut = np.searchsorted(ts, times, side="left")  # strictly before
        for d in range(depth):
            idx = cut - 1 - d
            ok = idx >= 0
            rate[d, ok, si] = rs[idx[ok]]
            bas[d, ok, si] = bs[idx[ok]]
    return rate, bas
