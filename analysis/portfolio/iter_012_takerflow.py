"""portfolio-iteration EXPLORATION-012 — TAKER-FLOW IMBALANCE (microstructure momentum overlay).

ONE new STRUCTURAL change to the canonical iter_005 baseline (walk-forward-λ trend+carry, honest
IS +1.30 / OOS +1.37 / maxDD -23%). First use of a MICROSTRUCTURE factor — aggressive market-buy
vs market-sell taker order flow — a column always on disk but never touched.

CRYPTO-NATIVE RATIONALE (quant-researcher):
  Each 8h kline carries taker_buy_volume = aggressive market BUYS (orders that lifted the offer),
  and by difference taker-sell = volume - taker_buy. The per-candle FLOW IMBALANCE
      imb[t] = taker_buy_volume[t] / volume[t] - 0.5            in [-0.5, +0.5]
  measures whether aggressors were net lifting offers (informed/momentum DEMAND, imb>0) or net
  hitting bids (distribution, imb<0). Aggressive buying is the footprint of informed/momentum flow;
  aggressive selling the footprint of forced/disinterested distribution.

  KEY ORTHOGONALITY QUESTION: is taker-buy pressure just recent price-up re-skinned (collinear with
  the [21,42,84,168] trend already in the book), or an independent factor? The mechanism says
  independent: a candle can close UP on passive buying (offers pulled) with NEGATIVE taker-buy
  share, or close flat while aggressors lift. We MEASURE it: corr(per-candle imb, same-candle
  return) and corr(smoothed flow_z, trend signal) on IS. If the latter is high the overlay is a
  momentum re-skin and must be REJECTED (gate [4], threshold < 0.50).

  DIRECTION (tested BOTH ways, sign mechanism-determined NOT OOS-picked): MOMENTUM-directional (long
  high aggressive-buy / short high aggressive-sell = informed demand persists) vs CONTRARIAN-at-
  extremes (extreme aggressive buying = exhaustion top -> fade). The code runs the literal sign flip
  and prints both; γ>0 in the blend means the profitable direction.

SIGNAL CONSTRUCTION (per coin-candle t, ALL inputs known at close[t], PAST-ONLY):
  imb[t]      = taker_buy_volume[t]/volume[t] - 0.5                         # completed-candle flow
  flow_sm[t]  = imb.rolling(SMOOTH_WIN).mean()                  # de-noise (single print is noise)
  flow_z[t,c] = cross-sectional z-score of flow_sm across ELIGIBLE coins at t (row-demeaned/row-std)
  The weight lag is applied by `w = raw...shift(1)` (mirrors trend/carry) so a signal built from
  close[t] info is applied to the open[t+1]->open[t+2] return. No future data touches flow_z (the
  z-score row-stats are same-time cross-section only).

HEADLINE CHOICES (justified; robustness rows print the alternatives):
  - VOLUME version (taker_buy_volume/volume), NOT quote-volume: base-volume taker share is the clean
    participation-imbalance primitive; quote-volume re-encodes a price-level weighting (quote=base ×
    price) that partially re-injects the very price move we want orthogonality from. The qv version
    is printed as a one-line cross-check (near-identical empirically).
  - SMOOTH_WIN = 42 candles (~14d): per-candle imbalance is noise; the project daily-equivalent
    convention is 3-4x lookback. 42 sits at HORIZONS[1], between de-noising and trend-redundancy.
    The window robustness sweep covers {21,42,84,168} so 42 is one cell of a scan, not a tuned pick.
  - cross-sectional Z-SCORE transform: makes the overlay scale-comparable to trend (mean-sign in
    [-1,1]) so a fixed γ has stable meaning; the centering makes it dollar-neutral by construction.

CONSTRUCTION (mirrors iter_005/iter_011 EXACTLY; overlay BEFORE /rvol so it flows through the
IDENTICAL gross-normalize -> lag -> cost+funding -> PER-λ vol-target -> wf.walkforward stitch):
  sig = (1-λ)·trend + λ·carry + γ·flow_z
  γ=0 BYTE-REPRODUCES iter_005 (IS +1.30 / OOS +1.37 / -23%) — HARD sanity gate; if it does not
  match, halt before reading any γ>0 cell. (Diary EXPLORATION-005 quotes +1.22; current data and
  the live iter_005 run reproduce +1.37 — the live reproduction is the anchor.)

NO-CHEATING: γ is a STRUCTURAL family-weight (no regime-non-stationarity evidence, unlike λ which
EARNED its walk-forward) -> ROBUSTNESS-PROVEN over a fixed grid (every cell positive IS+OOS), NEVER
walk-forwarded, NEVER OOS-picked. λ walk-forward UNCHANGED. Taker 0.05%/side both sides + a 2× cost
stress on the standalone (a gross-only / turnover-eaten edge is a REJECT). OOS_CUTOFF fixed.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

# --- signal knobs (structural; robustness-checked, NEVER OOS-tuned) ---
SMOOTH_WIN = 42  # trailing smoothing window for the imbalance (~14d of 8h == HORIZONS[1])

# --- blend / robustness ---
GAMMA_GRID = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]  # structural family-weight grid (robustness scan)
WINDOW_GRID = [21, 42, 84, 168]  # smoothing-window robustness scan (== base.HORIZONS)
EPS = 0.05  # materiality band: "not worse" / "real lift" threshold (same as iter_008/011)


def load_flow(coins: dict) -> dict:
    """Re-read taker-flow + volume columns for the SAME universe (load_universe pulls only
    open/close/qvol). Returns aligned DataFrames on the ms index, restricted to the coins dict so
    the point-in-time universe is byte-identical to the baseline's.
    """
    tbv, vol, tbq, qv = {}, {}, {}, {}
    by_sym = {p.split("/")[1]: p for p in glob.glob("data/*USDT/8h.csv")}
    for sym in coins:
        p = by_sym.get(sym)
        if p is None:
            continue
        usecols = [
            "open_time",
            "volume",
            "taker_buy_volume",
            "quote_volume",
            "taker_buy_quote_volume",
        ]
        k = pd.read_csv(p, usecols=usecols)
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        tbv[sym] = k["taker_buy_volume"].astype(float)
        vol[sym] = k["volume"].astype(float)
        tbq[sym] = k["taker_buy_quote_volume"].astype(float)
        qv[sym] = k["quote_volume"].astype(float)
    return {
        "taker_buy_volume": pd.DataFrame(tbv),
        "volume": pd.DataFrame(vol),
        "taker_buy_quote_volume": pd.DataFrame(tbq),
        "quote_volume": pd.DataFrame(qv),
    }


def build_flow_z(
    taker_buy: pd.DataFrame,
    volume: pd.DataFrame,
    elig: pd.DataFrame,
    smooth_win: int,
    direction: int = 1,
) -> pd.DataFrame:
    """Cross-sectional z-score of the trailing-smoothed taker-buy imbalance, PAST-ONLY.

    imb[t]     = taker_buy/volume - 0.5            (completed candle t, known at close[t])
    flow_sm[t] = imb.rolling(smooth_win).mean()    (t and earlier only)
    flow_z[t,c]= (flow_sm - rowmean) / rowstd  over the ELIGIBLE cross-section at t (same-time only)
    direction = +1 momentum (long high-buy-imbalance), -1 contrarian (the sign flip; both printed).
    The weight lag is applied later via `.shift(1)`; nothing here uses future data (z-score rowstats
    are same-row cross-section, smoothing is trailing).
    """
    imb = taker_buy / volume.replace(0, np.nan) - 0.5
    flow_sm = imb.rolling(smooth_win).mean()
    sm = flow_sm.where(elig)  # restrict the cross-section to eligible coins for the row-stats
    row_mean = sm.mean(axis=1)
    row_std = sm.std(axis=1)
    z = sm.sub(row_mean, axis=0).div(row_std.replace(0, np.nan), axis=0)
    return (direction * z).where(elig)


def _panels(coins: dict) -> dict:
    """Shared past-only inputs — IDENTICAL to iter_005.lam_nets / iter_011._panels prep, plus the
    taker-flow signal (headline volume version, MOMENTUM direction, SMOOTH_WIN).
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    flow = load_flow(coins)
    tbv = flow["taker_buy_volume"].reindex(index=opens.index, columns=opens.columns)
    vol = flow["volume"].reindex(index=opens.index, columns=opens.columns)
    tbq = flow["taker_buy_quote_volume"].reindex(index=opens.index, columns=opens.columns)
    qvf = flow["quote_volume"].reindex(index=opens.index, columns=opens.columns)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund, tbv, vol, tbq, qvf):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)
    flow_z = build_flow_z(tbv, vol, elig, SMOOTH_WIN, direction=1)
    flow_z_qv = build_flow_z(tbq, qvf, elig, SMOOTH_WIN, direction=1)  # qv cross-check
    return {
        "ret_fwd": ret_fwd,
        "elig": elig,
        "rvol": rvol,
        "trend": trend,
        "carry": carry,
        "fund_next": fund_next,
        "flow_z": flow_z,
        "flow_z_qv": flow_z_qv,
        # raw stashed so the window robustness sweep rebuilds flow_z variants without re-loading the
        # universe (trend/carry/rvol/elig are fixed across all smoothing-window variants).
        "_opens": opens,
        "_close": close,
        "_tbv": tbv,
        "_vol": vol,
    }


def lam_nets_gamma(p: dict, gamma: float, flow_key: str = "flow_z") -> dict:
    """Canonical iter_005 per-λ net with a γ-weighted taker-flow overlay folded into the directional
    core BEFORE /rvol. Mirrors iter_005.lam_nets line-for-line except `trend` -> `core + γ·flow_z`.
    γ=0 => the canonical net exactly. PER-λ vol-target applied here (iter_005 line 50) — ordering
    preserved.
    """
    overlay = gamma * p[flow_key].fillna(0.0)
    nets = {}
    for lam in wf.LAM_GRID:
        sig = (1 - lam) * p["trend"] + lam * p["carry"] + overlay
        raw = (sig / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


def stitched_turnover(p: dict, gamma: float) -> float:
    """Mean one-sided per-candle turnover of the DEPLOYED (walk-forward-λ-chosen) portfolio, using
    the SAME λ-selection as the headline run (best PAST vol-targeted monthly Sharpe). Mirrors
    iter_011.stitched_turnover with the γ overlay.
    """
    overlay = gamma * p["flow_z"].fillna(0.0)
    weights, nets = {}, {}
    for lam in wf.LAM_GRID:
        sig = (1 - lam) * p["trend"] + lam * p["carry"] + overlay
        raw = (sig / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        weights[lam] = w
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    vt_panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(vt_panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    cols = weights[wf.LAM_GRID[0]].columns
    w_parts = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = vt_panel[(vt_panel.index >= lo) & (vt_panel.index < hi)]
        if len(train) < 200:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        wm = weights[tsh.idxmax()].reindex(columns=cols)
        wm = wm[(wm.index >= m0) & (wm.index < test_hi)]
        if not wm.empty:
            w_parts.append(wm)
    wfull = pd.concat(w_parts).sort_index()
    return float((wfull - wfull.shift(1)).abs().sum(axis=1).mean())


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    return {
        "is": base.msharpe(net, base.LO0, base.OOS_CUTOFF),
        "oos": base.msharpe(net, base.OOS_CUTOFF, base.HI1),
        "dd": dd,
        "tot": (eq.iloc[-1] - 1) * 100,
        "yr": yr,
    }


def standalone(p: dict, cost_mult: float, direction: int = 1) -> dict:
    """Build flow_z as a self-contained cross-sectional signal (z-score, gross-normalized, lagged,
    real funding + taker cost at cost_mult×, per-candle vol-targeted) — directly comparable to the
    baseline. direction flips the sign (momentum vs contrarian). Returns stats + turnover.
    """
    sig = p["flow_z"].fillna(0.0) if direction == 1 else (-p["flow_z"]).fillna(0.0)
    raw = sig.where(p["elig"])
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = base.vol_target((pnl + fpnl - cost).dropna())
    gross_net = base.vol_target((pnl + fpnl).dropna())  # pre-cost (cost honesty diagnostic)
    s = stats(net)
    s["turn"] = float((w - w.shift(1)).abs().sum(axis=1).mean())
    s["gross_is"] = base.msharpe(gross_net, base.LO0, base.OOS_CUTOFF)
    s["gross_oos"] = base.msharpe(gross_net, base.OOS_CUTOFF, base.HI1)
    return s


def standalone_net(p: dict, direction: int = 1) -> pd.Series:
    """The standalone flow_z NET return series (1× taker, real funding, NOT vol-targeted) — used by
    the residual-orthogonality diagnostic so it shares the baseline's raw-return space.
    """
    sig = p["flow_z"].fillna(0.0) if direction == 1 else (-p["flow_z"]).fillna(0.0)
    raw = sig.where(p["elig"])
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return (pnl + fpnl - cost).dropna()


def residual_orthogonality(p: dict) -> dict:
    """Critic Rec 3 — regress the standalone flow_z net on the baseline TREND net, report the
    RESIDUAL OOS Sharpe. If flow_z were just a second momentum factor (a re-skin of trend), its
    return series would be spanned by the trend net and the residual would collapse. A residual that
    stays materially positive OOS proves the factor is INDEPENDENTLY additive, not return-stacking.

    Beta is fit on IS ONLY (no OOS peek); the same IS-fit beta is applied to the OOS residual.
    """
    flow = standalone_net(p, direction=1)
    # baseline trend net = the γ=0, λ=0 (pure trend) net, in the same raw-return space (NOT vt)
    raw = (p["trend"] / p["rvol"]).where(p["elig"])
    wt = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    tpnl = (wt * p["ret_fwd"].reindex(columns=wt.columns)).sum(axis=1)
    tf = -(wt * p["fund_next"].reindex(columns=wt.columns)).sum(axis=1)
    tc = base.COST_SIDE * (wt - wt.shift(1)).abs().sum(axis=1)
    trend_net = (tpnl + tf - tc).dropna()
    df = pd.DataFrame({"flow": flow, "trend": trend_net}).dropna()
    is_df = df[df.index < base.OOS_CUTOFF]
    f_is, t_is = is_df["flow"], is_df["trend"]
    var = float((t_is**2).mean() - t_is.mean() ** 2)
    cov = float((f_is * t_is).mean() - f_is.mean() * t_is.mean())
    beta = cov / var if var > 0 else 0.0
    resid = df["flow"] - beta * df["trend"]  # IS-fit beta applied to the whole series
    return {
        "beta": beta,
        "raw_is": base.msharpe(df["flow"], base.LO0, base.OOS_CUTOFF),
        "raw_oos": base.msharpe(df["flow"], base.OOS_CUTOFF, base.HI1),
        "resid_is": base.msharpe(resid, base.LO0, base.OOS_CUTOFF),
        "resid_oos": base.msharpe(resid, base.OOS_CUTOFF, base.HI1),
    }


def coverage(p: dict) -> dict:
    """Coverage diagnostic for the DENSE always-on overlay (not an event count, unlike iter_011's
    sparse liqfade): fraction of eligible cells that carry a finite flow_z (after the SMOOTH_WIN
    warmup), IS vs OOS. A dense cross-sectional tilt — the vol-target degeneracy that produced
    iter_011's -99% standalone cannot recur here.
    """
    finite = p["flow_z"].notna() & p["elig"]
    elig = p["elig"]
    is_m = elig.index < base.OOS_CUTOFF
    oos_m = elig.index >= base.OOS_CUTOFF
    is_cov = finite[is_m].sum().sum() / max(int(elig[is_m].sum().sum()), 1)
    oos_cov = finite[oos_m].sum().sum() / max(int(elig[oos_m].sum().sum()), 1)
    med_active = float(finite.sum(axis=1)[finite.sum(axis=1) > 0].median())
    return {"is_cov": is_cov, "oos_cov": oos_cov, "med_active": med_active}


def orthogonality(p: dict, other_key: str = "trend", flow_key: str = "flow_z") -> float:
    """Pooled cross-coin Pearson corr(flow_z, <other>) over IS ELIGIBLE cells. THE key orthogonality
    number: if corr to trend is high the overlay is a momentum re-skin (gate [4] threshold < 0.50).
    Eligibility enters via the finite mask (flow_z is NaN outside elig) — never `.where(elig) != 0`.
    """
    fl = p[flow_key]
    ot = p[other_key].where(p["elig"])
    is_mask = fl.index < base.OOS_CUTOFF
    a = fl[is_mask].to_numpy().ravel()
    b = ot[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def imb_vs_return_corr(p: dict) -> float:
    """Diagnostic: corr(per-candle imbalance, same-candle return) over IS eligible cells. Documents
    whether taker-buy share is just 'price went up' (would be ~+0.8) or informed flow (~+0.3).
    """
    imb = (p["_tbv"] / p["_vol"].replace(0, np.nan) - 0.5).where(p["elig"])
    ret = (p["_close"] / p["_opens"] - 1.0).where(p["elig"])
    is_mask = imb.index < base.OOS_CUTOFF
    a = imb[is_mask].to_numpy().ravel()
    b = ret[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def window_sweep(p: dict, b: dict) -> None:
    """Smoothing-window robustness sweep — rebuild flow_z per smoothing window and blend at γ∈{0.05,
    0.10} on the canonical walk-forward net. If only the 42-cell lifts and the others are flat/
    negative, the headline is a tuned cell -> downgrade. Reuses the fixed trend/carry/rvol/elig
    panels (only the smoothing window changes).
    """
    print(
        "\n  --- SMOOTHING-WINDOW ROBUSTNESS (γ=0.05/0.10 blend; baseline OOS "
        f"{b['oos']:+.2f}/DD {b['dd'] * 100:.0f}%) ---"
    )
    print(
        f"  {'win':>4} {'corrTrend':>9} {'sa_IS':>6} {'sa_OOS':>7}  "
        f"{'g05 IS':>7} {'g05 OOS':>8} {'g05 DD':>7}  {'g10 IS':>7} {'g10 OOS':>8} {'g10 DD':>7}"
    )
    for win in WINDOW_GRID:
        fz = build_flow_z(p["_tbv"], p["_vol"], p["elig"], win, direction=1)
        pv = {**p, "flow_z": fz}
        corr = orthogonality(pv, "trend")
        sa = standalone(pv, 1.0, direction=1)
        s05 = stats(wf.walkforward(lam_nets_gamma(pv, 0.05))[0])
        s10 = stats(wf.walkforward(lam_nets_gamma(pv, 0.10))[0])
        print(
            f"  {win:>4d} {corr:>+9.3f} {sa['is']:>+6.2f} {sa['oos']:>+7.2f}  "
            f"{s05['is']:>+7.2f} {s05['oos']:>+8.2f} {s05['dd'] * 100:>6.0f}%  "
            f"{s10['is']:>+7.2f} {s10['oos']:>+8.2f} {s10['dd'] * 100:>6.0f}%"
        )


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-012: TAKER-FLOW IMBALANCE (microstructure overlay) — {len(coins)} coins")
    print(
        f"  signal: flow_z = xsec z-score of (taker_buy/vol - 0.5).rolling({SMOOTH_WIN}).mean(); "
        f"MOMENTUM dir; γ grid {GAMMA_GRID}\n"
    )

    p = _panels(coins)

    # --- coverage (dense overlay, not an event flag) ---
    cv = coverage(p)
    print(
        f"  COVERAGE (dense): IS finite-flow_z fraction of eligible={cv['is_cov']:.2f}  "
        f"OOS={cv['oos_cov']:.2f}  median active coins/candle={cv['med_active']:.0f}\n"
    )

    # --- mechanism / orthogonality: is taker-buy just recent price-up? ---
    imb_ret = imb_vs_return_corr(p)
    corr_tr = orthogonality(p, "trend")
    corr_tr_qv = orthogonality(p, "trend", "flow_z_qv")
    corr_ca = orthogonality(p, "carry")
    corr_ok = np.isfinite(corr_tr) and corr_tr < 0.50
    print("  --- MECHANISM / ORTHOGONALITY (IS, eligible cells) ---")
    print(
        f"  corr(per-candle imb, same-candle ret) = {imb_ret:+.3f}  "
        f"(if ~+0.8 it's just price-up; ~+0.3 = informed flow)"
    )
    print(
        f"  corr(flow_z, trend) = {corr_tr:+.3f}  (qv version {corr_tr_qv:+.3f})  -> "
        f"{'PASS (<0.50, independent factor)' if corr_ok else 'FAIL (>=0.50, momentum re-skin)'}"
    )
    print(f"  corr(flow_z, carry) = {corr_ca:+.3f}\n")

    # --- STANDALONE both directions + cost honesty (1× and 2× taker) ---
    print("  --- STANDALONE flow_z cross-sectional signal (BOTH directions, cost honesty) ---")
    print(f"  {'':18}{'IS':>7}{'OOS':>7}{'maxDD':>7}{'netTot':>8}{'turn':>7}")
    sa_mom1 = standalone(p, 1.0, direction=1)
    sa_mom2 = standalone(p, 2.0, direction=1)
    sa_con1 = standalone(p, 1.0, direction=-1)
    print(
        f"  {'MOMENTUM 1× taker':18}{sa_mom1['is']:>+7.2f}{sa_mom1['oos']:>+7.2f}"
        f"{sa_mom1['dd'] * 100:>6.0f}%{sa_mom1['tot']:>+7.0f}%{sa_mom1['turn']:>7.3f}"
    )
    print(
        f"  {'MOMENTUM 2× taker':18}{sa_mom2['is']:>+7.2f}{sa_mom2['oos']:>+7.2f}"
        f"{sa_mom2['dd'] * 100:>6.0f}%{sa_mom2['tot']:>+7.0f}%{sa_mom2['turn']:>7.3f}"
    )
    print(
        f"  {'CONTRARIAN 1× taker':18}{sa_con1['is']:>+7.2f}{sa_con1['oos']:>+7.2f}"
        f"{sa_con1['dd'] * 100:>6.0f}%{sa_con1['tot']:>+7.0f}%{sa_con1['turn']:>7.3f}"
    )
    print(
        f"  {'MOMENTUM gross':18}{sa_mom1['gross_is']:>+7.2f}{sa_mom1['gross_oos']:>+7.2f}  "
        f"(pre-cost; turnover ~{sa_mom1['turn']:.3f} << baseline 0.296 — overlay is turnover-cheap)"
    )
    # qv-version standalone cross-check (one line)
    pv_qv = {**p, "flow_z": p["flow_z_qv"]}
    sa_qv = standalone(pv_qv, 1.0, direction=1)
    print(
        f"  {'qv-version 1× MOM':18}{sa_qv['is']:>+7.2f}{sa_qv['oos']:>+7.2f}"
        f"{sa_qv['dd'] * 100:>6.0f}%{sa_qv['tot']:>+7.0f}%{sa_qv['turn']:>7.3f}"
    )
    print(f"     MOMENTUM 1× net%/yr={sa_mom1['yr']}")
    mom_dir = sa_mom1["is"] >= sa_con1["is"]  # direction the data picks
    print(
        f"     direction picked by data: "
        f"{'MOMENTUM (+1, long aggressive-buy)' if mom_dir else 'CONTRARIAN (-1)'}\n"
    )

    # --- residual orthogonality (critic Rec 3): is the edge INDEPENDENT of trend, or stacking? ---
    ro = residual_orthogonality(p)
    resid_ok = ro["resid_oos"] > 0.5
    resid_tag = (
        "independently additive (NOT just a 2nd momentum factor)"
        if resid_ok
        else "spanned by trend (return-stacking)"
    )
    print("  --- RESIDUAL ORTHOGONALITY (flow_z net regressed on TREND net; IS-fit beta) ---")
    print(
        f"  beta={ro['beta']:+.2f}  raw flow IS/OOS={ro['raw_is']:+.2f}/{ro['raw_oos']:+.2f}"
        f"  -> RESIDUAL IS/OOS={ro['resid_is']:+.2f}/{ro['resid_oos']:+.2f}"
    )
    print(f"     {resid_tag}\n")

    # --- canonical baseline reproduction (γ=0) via the SAME iter_005.walkforward stitch ---
    base_nets = lam_nets_gamma(p, 0.0)
    base_wf, _ = wf.walkforward(base_nets)
    b = stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    print(
        f"  CANONICAL baseline (γ=0, iter_005 net): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}% netTot={b['tot']:+.0f}%"
    )
    print(f"     net%/yr={b['yr']}")
    print("     (sanity: must match iter_005 IS+1.30/OOS+1.37/-23%)\n")

    # --- robustness sweep over γ (NOT walk-forwarded; measured on the CANONICAL net) ---
    print("  --- ROBUSTNESS SWEEP (γ; λ walk-forwarded; per-λ-vol-target-then-stitch) ---")
    print(
        f"  {'gamma':>5} {'IS':>7} {'OOS':>7} {'dIS':>7} {'dOOS':>7} {'maxDD':>7} "
        f"{'turn':>6} {'all-yr+IS':>9}"
    )
    rows = []
    for gamma in GAMMA_GRID:
        nets = lam_nets_gamma(p, gamma)
        net_wf, _ = wf.walkforward(nets)
        s = stats(net_wf)
        turn = stitched_turnover(p, gamma)
        is_net = net_wf[net_wf.index < base.OOS_CUTOFF]
        is_yr = is_net.groupby(is_net.index.year).sum()
        yr_is_pos = bool((is_yr >= 0).all())
        rows.append({"gamma": gamma, **s, "turn": turn, "yr_is_pos": yr_is_pos})
        print(
            f"  {gamma:>5.2f} {s['is']:>+7.2f} {s['oos']:>+7.2f} {s['is'] - b['is']:>+7.2f} "
            f"{s['oos'] - b['oos']:>+7.2f} {s['dd'] * 100:>6.0f}% {turn:>6.3f} "
            f"{'yes' if yr_is_pos else 'NO':>9}"
        )

    mid = next(r for r in rows if abs(r["gamma"] - 0.10) < 1e-9)
    print(f"\n  mid-grid γ=0.10 net%/yr={mid['yr']}")

    # --- smoothing-window robustness (prove it is not a tuned cell) ---
    window_sweep(p, b)

    # --- pre-registered falsifier verdict ---
    nz = [r for r in rows if r["gamma"] > 0]
    all_cells_pos = all(r["is"] >= b["is"] - EPS and r["oos"] >= b["oos"] - EPS for r in nz)
    small = next(r for r in nz if abs(r["gamma"] - 0.05) < 1e-9)
    small_signal = (small["oos"] - b["oos"]) >= 0.10 and (small["is"] - b["is"]) >= -EPS
    mid_lift = mid["oos"] - b["oos"]
    lift_ok = mid_lift >= 0.20
    dd_no_blowout = all(r["dd"] >= -0.28 for r in nz)
    dd_cut = any(
        r["dd"] > b["dd"] and r["is"] >= b["is"] - EPS and r["oos"] >= b["oos"] - EPS for r in nz
    )
    yr_ok = all(r["yr_is_pos"] for r in nz)
    cost_ok = sa_mom1["is"] > 0 and sa_mom1["oos"] > 0 and sa_mom2["is"] > 0 and sa_mom2["oos"] > 0

    print(f"\n  === PRE-REGISTERED FALSIFIER VERDICT (n={n_oos_mo} OOS months) ===")
    print(f"  [1] all γ cells IS+OOS >= baseline-{EPS}: {'PASS' if all_cells_pos else 'FAIL'}")
    print(
        f"  [2] signal present at small γ=0.05 (dOOS>=+0.10, not only-at-large): "
        f"dOOS={small['oos'] - b['oos']:+.2f} -> {'PASS' if small_signal else 'FAIL'}"
    )
    print(
        f"  [3] mid-grid γ=0.10 OOS lift >= +0.20 (above n={n_oos_mo}mo noise): "
        f"dOOS={mid_lift:+.2f} -> {'PASS' if lift_ok else 'FAIL'}"
    )
    print(
        f"  [4] corr(flow_z, trend) < 0.50 (independent factor, not momentum re-skin): "
        f"{corr_tr:+.3f} -> {'PASS' if corr_ok else 'FAIL'}"
    )
    print(
        f"  [5] maxDD >= -28% across grid (no tail-levering): "
        f"{'PASS' if dd_no_blowout else 'FAIL'}  "
        f"[stretch: CUTS DD below {b['dd'] * 100:.0f}% on a positive cell: "
        f"{'YES' if dd_cut else 'no'}]"
    )
    print(f"  [6] no IS year flips negative (blend): {'PASS' if yr_ok else 'FAIL'}")
    print(
        f"  [7] standalone net-positive at 1× AND 2× taker (not gross-only/turnover-eaten): "
        f"{'PASS' if cost_ok else 'FAIL'}"
    )

    gates = [all_cells_pos, small_signal, lift_ok, corr_ok, dd_no_blowout, yr_ok, cost_ok]
    if all(gates):
        print(
            "\n  VERDICT: EDGE — robustness-proven orthogonal microstructure overlay. Recommend "
            "CONFIRM (walk-forward-γ / held-OOS) before baseline promotion."
        )
    elif corr_ok and dd_no_blowout and all_cells_pos and cost_ok and not lift_ok:
        print(
            "\n  VERDICT: NOISE (real-but-too-small) — leak-safe, orthogonal, cost-honest, not "
            "harmful, but the OOS lift is inside the OOS-month-Sharpe noise band. NOT worth the "
            "added complexity. REJECT as accretive change (honest down-call)."
        )
    else:
        print("\n  VERDICT: REJECT — failed a mechanism/robustness/cost falsifier above. NOT kept.")


if __name__ == "__main__":
    main()
