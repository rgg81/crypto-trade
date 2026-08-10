"""Offline book simulator for team-04 EDA.

NOT a scorer. The organiser's harness is the only scorer; this exists so a trial is spent on a
question rather than on a guess. It mirrors the parts of the pipeline that change a design
decision -- next-bar-open fills, quantity-holding between rebalances, per-side cost, native
funding, and the common risk unit -- and ignores the parts that do not (participation cap,
delisting force-exit, solvency).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 1095.0  # 8h bars per year
COST_BPS_PER_SIDE = 7.5


def build_funding_matrix(grid: pd.DatetimeIndex, symbols: list[str]) -> np.ndarray:
    """Funding paid by a long over the interval (grid[i], grid[i+1]], as a rate, row i."""
    f = pd.read_parquet("data/cup20/is/funding.parquet")
    tcol = "funding_time" if "funding_time" in f.columns else f.columns[0]
    rcol = "funding_rate" if "funding_rate" in f.columns else f.columns[-1]
    f = f[[tcol, "symbol", rcol]].rename(columns={tcol: "t", rcol: "rate"})
    f["t"] = pd.to_datetime(f["t"], utc=True)
    idx = grid.searchsorted(pd.DatetimeIndex(f["t"]), side="left") - 1
    f = f.assign(row=idx)
    f = f[(f.row >= 0) & (f.row < len(grid))]
    sym_index = {s: j for j, s in enumerate(symbols)}
    f = f[f.symbol.isin(sym_index)]
    out = np.zeros((len(grid), len(symbols)))
    np.add.at(out, (f.row.to_numpy(), f.symbol.map(sym_index).to_numpy()), f.rate.to_numpy())
    return out


def simulate(
    weights: np.ndarray,
    rebalance: np.ndarray,
    opens: np.ndarray,
    funding: np.ndarray | None,
    start: int,
    *,
    risk_unit: bool = True,
    cost_mult: float = 1.0,
):
    """Hold quantities between rebalances; fill at the open of the bar starting at the decision.

    `weights[i]` are the intended targets at decision i (rows where `rebalance[i]` is False are
    ignored -- quantities are simply carried). Returns a dict of diagnostics.
    """
    n, k = weights.shape
    px = opens
    # --- pass 1: reference book (no scaling), to derive the common risk unit ------------------
    def run(scale: np.ndarray | None, cm: float):
        w_held = np.zeros(k)          # current weights (drift with price)
        gross_ret = np.zeros(n)
        net_ret = np.zeros(n)
        turn = np.zeros(n)
        fund_ret = np.zeros(n)
        side_long = np.zeros(n)
        side_short = np.zeros(n)
        trades = 0
        for i in range(start, n - 1):
            if rebalance[i]:
                tgt = weights[i].copy()
                if scale is not None:
                    tgt = tgt * scale[i]
                g = np.abs(tgt).sum()
                if g > 1.0:                      # gross cap, by reduction
                    tgt = tgt / g
                mx = np.abs(tgt).max() if k else 0.0
                if mx > 0.20:
                    tgt = tgt * (0.20 / mx)
                d = tgt - w_held
                t = np.abs(d).sum()
                turn[i] = t
                trades += int((np.abs(d) > 1e-12).sum())
                net_ret[i] -= t * cm * COST_BPS_PER_SIDE * 1e-4
                w_held = tgt
            # hold over (grid[i], grid[i+1]]
            with np.errstate(invalid="ignore", divide="ignore"):
                step = px[i + 1] / px[i] - 1.0
            step = np.where(np.isfinite(step), step, 0.0)
            contrib = w_held * step
            fcontrib = -(w_held * funding[i]) if funding is not None else np.zeros(k)
            long_mask = w_held > 0
            side_long[i] = float(contrib[long_mask].sum() + fcontrib[long_mask].sum())
            side_short[i] = float(contrib[~long_mask].sum() + fcontrib[~long_mask].sum())
            pnl = float(contrib.sum())
            fpnl = float(fcontrib.sum())
            gross_ret[i] = pnl + fpnl
            fund_ret[i] = fpnl
            net_ret[i] += pnl + fpnl
            w_held = w_held * (1.0 + step)       # quantities carried -> weights drift
        return gross_ret, net_ret, turn, trades, fund_ret, side_long, side_short

    g1 = run(None, 1.0)[0]
    if not risk_unit:
        scale = None
    else:
        s = pd.Series(g1)
        vol = s.shift(1).rolling(270, min_periods=270).std() * np.sqrt(ANN)
        scale = np.clip(0.10 / vol.to_numpy(), 0.20, 3.0)
        scale = np.where(np.isfinite(scale), scale, 1.0)
    g, nr, turn, trades, fr, sl, ss = run(scale, cost_mult)
    return {
        "gross": g[start:],
        "net": nr[start:],
        "turnover": turn[start:],
        "trades": trades,
        "funding": fr[start:],
        "scale": scale,
        "long_gross": sl[start:],
        "short_gross": ss[start:],
    }


def stats(res: dict, grid: pd.DatetimeIndex, start: int) -> dict:
    net = pd.Series(res["net"], index=grid[start:])
    gross = pd.Series(res["gross"], index=grid[start:])
    eq = (1 + net).cumprod()
    dd = 1 - eq / eq.cummax()
    years = len(net) / ANN
    tot_turn = float(res["turnover"].sum())
    daily = net.resample("1D").sum()
    dgross = gross.resample("1D").sum()
    return {
        "sharpe": float(daily.mean() / daily.std() * np.sqrt(365.0)),
        "gross_sharpe": float(dgross.mean() / dgross.std() * np.sqrt(365.0)),
        "ann_ret": float(eq.iloc[-1] ** (1 / years) - 1),
        "ann_vol": float(daily.std() * np.sqrt(365.0)),
        "maxdd": float(dd.max()),
        "turnover_yr": tot_turn / years,
        "gross_edge_bps": float(gross.sum() / tot_turn * 1e4) if tot_turn > 0 else np.nan,
        "trades": res["trades"],
        "funding_share": float(res["funding"].sum() / abs(gross.sum())) if gross.sum() else np.nan,
        "top5_day_share": float(daily.abs().nlargest(5).sum() / daily.abs().sum()),
        "long_pnl": float(res["long_gross"].sum()),
        "short_pnl": float(res["short_gross"].sum()),
        "cost_share": float(
            (tot_turn * COST_BPS_PER_SIDE * 1e-4) / gross.clip(lower=0).sum()
        ) if gross.clip(lower=0).sum() > 0 else float("nan"),
    }


def fold_sharpes(res: dict, grid: pd.DatetimeIndex, start: int) -> list[float]:
    """Fold Sharpes on DAILY returns x sqrt(365), which is what the organiser's metric uses."""
    net = pd.Series(res["net"], index=grid[start:]).resample("1D").sum()
    edges = [pd.Timestamp(x, tz="UTC") for x in
             ("2020-08-17", "2021-08-01", "2022-08-01", "2023-08-01", "2024-08-01")]
    out = []
    for a, b in zip(edges[:-1], edges[1:], strict=True):
        seg = net[(net.index >= a) & (net.index < b)]
        out.append(float(seg.mean() / seg.std() * np.sqrt(365.0)) if len(seg) > 10 else float("nan"))
    return out


def quarter_fraction(res: dict, grid: pd.DatetimeIndex, start: int) -> float:
    net = pd.Series(res["net"], index=grid[start:])
    q = net.resample("QE").sum()
    return float((q > 0).mean())
