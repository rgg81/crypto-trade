"""iter-v3/095 Phase-1 GO/NO-GO — STRESS TEST (decisive adjudication).

The first-pass EDA (cointegration_go_nogo_eda.py) returned a fragile GO. This
stress test interrogates the three weaknesses an honest fail-fast adjudication
must resolve BEFORE committing a build:

  WEAKNESS 1 — thin tradeability. 231 round-trips over 38 months (~6/month);
    453 of 672 persistent pair-windows fired ZERO trades. Is there a book here
    at all, or is the +0.66 aggregate net an artifact of summing 672 mostly-zero
    pair-windows?
  WEAKNESS 2 — persistence is mechanical. Adjacent 24-month formation windows
    share 23/24 months (96% identical data) — high Engle-Granger persistence is
    EXPECTED and is NOT evidence the spread is tradeable next month. The real
    question: does a spread that is cointegrated in-formation actually
    MEAN-REVERT out-of-formation?
  WEAKNESS 3 — slow half-life. Median 60 bars = 20 days; in a 1-month (~90-bar)
    trading window a 20-day-HL spread gets ~1.5 cycles. That is why 2/3 of
    pair-windows never round-trip.

THE DECISIVE TEST — a faithful walk-forward pairs BOOK.
  Replicates the actual strategy a v3 cointegration runner would deploy:
    - 24-month formation window; pick the TOP-K pairs by Engle-Granger p-value
      among those with a tradeable formation half-life (2-60 bars);
    - trade the spread z-score on the SUBSEQUENT 1-month window, market-neutral,
      cost charged per round-trip leg-set;
    - aggregate the per-pair PnL into ONE monthly book PnL series;
    - report the BOOK's IS monthly Sharpe net of cost, and the same gross, and
      the trade count.
  This is the number that decides GO vs NO-GO — not pair-window-level summing.

  Additional decisive diagnostic — OUT-OF-FORMATION SPREAD ADF:
    for each selected pair, ADF-test the spread on the TRADING window using the
    FORMATION hedge ratio. If the formation cointegration does NOT survive into
    the trading window (out-of-formation spread ADF p >= 0.10 routinely), the
    cointegration "persistence" is an in-sample-overlap artifact and the axis
    is dead — that is the cycle-4 prep memo Candidate-B caveat, quantified.

NO CHEATING — IS-only (open_time < OOS_CUTOFF_MS); walk-forward-faithful.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

OOS_CUTOFF_MS = 1742774400000
TRAINING_MONTHS = 24
INTERVAL_MS = 8 * 60 * 60 * 1000
BARS_PER_MONTH = 30 * 3
DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v3-095")

XS_UNIVERSE = (
    "ADAUSDT", "AVAXUSDT", "FILUSDT", "FTMUSDT", "BCHUSDT", "GALAUSDT",
    "EOSUSDT", "CRVUSDT", "AAVEUSDT", "SANDUSDT", "ATOMUSDT", "LDOUSDT",
    "AXSUSDT", "TRXUSDT", "RUNEUSDT", "MANAUSDT", "ICPUSDT", "ALGOUSDT",
    "GRTUSDT", "THETAUSDT", "VETUSDT", "HBARUSDT",
)

COINT_PVALUE = 0.05
COST_PER_ROUNDTRIP = 0.0020  # 4 leg-fills x 0.05% taker — market-neutral pair
MIN_FORMATION_BARS = int(TRAINING_MONTHS * BARS_PER_MONTH * 0.80)

# Pairs book parameters — pre-registered, chosen GENEROUSLY (give the axis its
# best shot before declaring NO-GO):
TOP_K = 10              # trade up to 10 pairs per month — a real book breadth
HL_LO, HL_HI = 2, 60    # formation-window half-life band for selection
Z_LOOKBACK = 45         # spread z-score rolling window (bars)
Z_ENTRY = 2.0
Z_EXIT = 0.5
# A more permissive variant tested in parallel — Z_ENTRY=1.5 trades more often,
# directly attacking weakness 1 (thin trade count).
Z_ENTRY_LOOSE = 1.5


def load_log_prices():
    series, qvs = {}, {}
    for sym in XS_UNIVERSE:
        path = DATA_DIR / sym / "8h.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, usecols=["open_time", "close", "quote_volume"])
        df = df[df["open_time"] < OOS_CUTOFF_MS]
        if df.empty:
            continue
        df = df.set_index("open_time").sort_index()
        series[sym] = np.log(df["close"].astype(float))
        qvs[sym] = df["quote_volume"].astype(float)
    return pd.DataFrame(series).sort_index(), pd.DataFrame(qvs).sort_index()


def windows(panel):
    times = panel.index.to_numpy()
    t0, t1 = int(times.min()), int(times.max())
    month_ms = BARS_PER_MONTH * INTERVAL_MS
    formation_ms = TRAINING_MONTHS * month_ms
    out, cursor = [], t0 + formation_ms
    while cursor + month_ms <= t1:
        out.append(
            dict(
                idx=len(out),
                form_lo=cursor - formation_ms, form_hi=cursor,
                trade_lo=cursor, trade_hi=cursor + month_ms,
            )
        )
        cursor += month_ms
    return out


def eligible(panel, qv, lo, hi):
    seg = panel[(panel.index >= lo) & (panel.index < hi)]
    qseg = qv[(qv.index >= lo) & (qv.index < hi)]
    out = []
    for sym in panel.columns:
        if len(seg[sym].dropna()) < MIN_FORMATION_BARS:
            continue
        qmed = qseg[sym].dropna().median() if sym in qseg else 0.0
        if not np.isfinite(qmed) or qmed < 2_000_000:
            continue
        out.append(sym)
    return out


def eg_fit(y, x):
    """Engle-Granger fit. Returns (pval, intercept, beta, half_life)."""
    a = pd.concat([y, x], axis=1).dropna()
    if len(a) < 60:
        return np.nan, np.nan, np.nan, np.nan
    yv, xv = a.iloc[:, 0].to_numpy(), a.iloc[:, 1].to_numpy()
    try:
        _, pval, _ = coint(yv, xv)
    except Exception:
        return np.nan, np.nan, np.nan, np.nan
    X = np.column_stack([np.ones_like(xv), xv])
    bfull, *_ = np.linalg.lstsq(X, yv, rcond=None)
    spread = yv - (bfull[0] + bfull[1] * xv)
    sl, sn = spread[:-1], spread[1:]
    Xs = np.column_stack([np.ones_like(sl), sl])
    ar, *_ = np.linalg.lstsq(Xs, sn, rcond=None)
    rho = ar[1]
    hl = -np.log(2.0) / np.log(rho) if 0.0 < rho < 1.0 else np.nan
    return pval, bfull[0], bfull[1], hl


def trade_pair(panel, sy, sx, intercept, beta, w, z_entry):
    """Trade the z-score signal on the OUT-OF-FORMATION trading window.

    Spread mu/sd from the FORMATION window. Returns (n_trades, gross, net,
    trade_window_monthly_return, oof_adf_pvalue).
    """
    form = panel[(panel.index >= w["form_lo"]) & (panel.index < w["form_hi"])]
    trade = panel[(panel.index >= w["trade_lo"]) & (panel.index < w["trade_hi"])]
    f = pd.concat([form[sy], form[sx]], axis=1).dropna()
    t = pd.concat([trade[sy], trade[sx]], axis=1).dropna()
    if len(f) < 60 or len(t) < 10:
        return 0, 0.0, 0.0, 0.0, np.nan
    fy, fx = f.iloc[:, 0].to_numpy(), f.iloc[:, 1].to_numpy()
    fspread = fy - (intercept + beta * fx)
    mu, sd = float(fspread.mean()), float(fspread.std())
    if sd <= 0:
        return 0, 0.0, 0.0, 0.0, np.nan
    ty, tx = t.iloc[:, 0].to_numpy(), t.iloc[:, 1].to_numpy()
    tspread = ty - (intercept + beta * tx)
    z = (tspread - mu) / sd
    # out-of-formation spread ADF — does the cointegration survive the window?
    try:
        oof_adf = adfuller(tspread, maxlag=4, autolag=None)[1] if len(tspread) >= 20 else np.nan
    except Exception:
        oof_adf = np.nan

    pos, entry, n, gross = 0, 0.0, 0, 0.0
    for i in range(len(z)):
        if pos == 0:
            if z[i] >= z_entry:
                pos, entry = -1, tspread[i]
            elif z[i] <= -z_entry:
                pos, entry = +1, tspread[i]
        elif abs(z[i]) <= Z_EXIT:
            gross += pos * (tspread[i] - entry)
            n += 1
            pos = 0
    if pos != 0:
        gross += pos * (tspread[-1] - entry)
        n += 1
    net = gross - n * COST_PER_ROUNDTRIP
    return n, gross, net, net, oof_adf


def run_book(panel, qv, wins, z_entry, label):
    """Faithful walk-forward pairs book. Returns the monthly book-PnL series."""
    monthly_net, monthly_gross, monthly_trades = [], [], []
    oof_adf_all = []
    selected_count = []
    for w in wins:
        elig = eligible(panel, qv, w["form_lo"], w["form_hi"])
        seg = panel[(panel.index >= w["form_lo"]) & (panel.index < w["form_hi"])]
        # rank candidate pairs by formation Engle-Granger p-value, keep only
        # cointegrated (p<0.05) with a tradeable formation half-life.
        cands = []
        for a, b in itertools.combinations(elig, 2):
            pval, ic, beta, hl = eg_fit(seg[a], seg[b])
            if np.isnan(pval) or pval >= COINT_PVALUE:
                continue
            if not (np.isfinite(hl) and HL_LO <= hl <= HL_HI):
                continue
            cands.append((pval, a, b, ic, beta, hl))
        cands.sort(key=lambda r: r[0])  # lowest p-value first
        chosen = cands[:TOP_K]
        selected_count.append(len(chosen))
        # trade each chosen pair on the trading window; book = equal-weight mean
        net_list, gross_list, n_list = [], [], []
        for pval, a, b, ic, beta, hl in chosen:
            n, g, nt, _, oof = trade_pair(panel, a, b, ic, beta, w, z_entry)
            net_list.append(nt)
            gross_list.append(g)
            n_list.append(n)
            if np.isfinite(oof):
                oof_adf_all.append(oof)
        if net_list:
            # equal-weight book: average pair PnL (each pair = 1 unit notional)
            monthly_net.append(float(np.mean(net_list)))
            monthly_gross.append(float(np.mean(gross_list)))
            monthly_trades.append(int(np.sum(n_list)))
        else:
            monthly_net.append(0.0)
            monthly_gross.append(0.0)
            monthly_trades.append(0)

    net = np.array(monthly_net)
    gross = np.array(monthly_gross)
    # monthly Sharpe — the v3 headline metric convention
    net_sharpe = net.mean() / net.std() if net.std() > 0 else 0.0
    gross_sharpe = gross.mean() / gross.std() if gross.std() > 0 else 0.0
    total_trades = int(np.sum(monthly_trades))
    n_months = len(wins)
    print(f"\n  [{label}]  z_entry={z_entry}")
    print(f"    months traded:                {n_months}")
    print(f"    mean pairs selected/month:    {np.mean(selected_count):.1f}")
    print(f"    total round-trip trades:      {total_trades}"
          f"  ({total_trades / n_months:.1f}/month)")
    print(f"    book mean monthly NET PnL:    {net.mean():+.5f}")
    print(f"    book mean monthly GROSS PnL:  {gross.mean():+.5f}")
    print(f"    book NET monthly Sharpe:      {net_sharpe:+.4f}")
    print(f"    book GROSS monthly Sharpe:    {gross_sharpe:+.4f}")
    print(f"    frac months NET-positive:     {float((net > 0).mean()):.4f}")
    if oof_adf_all:
        oof_adf_all = np.array(oof_adf_all)
        print(f"    OUT-OF-FORMATION spread ADF:  median p={np.median(oof_adf_all):.4f}"
              f"  | frac p<0.10 (still cointegrated): {float((oof_adf_all < 0.10).mean()):.4f}")
    return dict(
        net_sharpe=net_sharpe, gross_sharpe=gross_sharpe,
        total_trades=total_trades, n_months=n_months,
        mean_net=float(net.mean()), frac_pos=float((net > 0).mean()),
        oof_adf_median=float(np.median(oof_adf_all)) if len(oof_adf_all) else np.nan,
        oof_adf_frac_coint=float((np.array(oof_adf_all) < 0.10).mean()) if len(oof_adf_all) else np.nan,
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/095 Phase-1 GO/NO-GO — STRESS TEST: faithful walk-forward book")
    print("=" * 78)
    panel, qv = load_log_prices()
    wins = windows(panel)
    print(f"IS log-price panel: {panel.shape[0]} bars x {panel.shape[1]} symbols")
    print(f"Walk-forward windows: {len(wins)}  | TOP_K={TOP_K} pairs/month"
          f"  | HL band [{HL_LO},{HL_HI}] bars")
    print(f"Cost per round-trip: {COST_PER_ROUNDTRIP} (4 legs x 0.05% taker)")

    print("\n" + "-" * 78)
    print("THE DECISIVE BOOK — does a faithful walk-forward pairs book clear cost?")
    print("-" * 78)
    r_strict = run_book(panel, qv, wins, Z_ENTRY, "STRICT z-entry 2.0")
    r_loose = run_book(panel, qv, wins, Z_ENTRY_LOOSE, "LOOSE z-entry 1.5")

    print("\n" + "=" * 78)
    print("GO / NO-GO VERDICT — stress-tested")
    print("=" * 78)
    # Pre-registered GO criterion for the stress test: the BEST faithful book
    # variant must produce a NET monthly Sharpe materially above zero. v3's
    # /059 baseline is OOS monthly Sharpe +0.58; the merge floor is +1.0. A new
    # STRATEGY CLASS that cannot clear an IS NET monthly Sharpe of +0.30 — even
    # GENEROUSLY parameterized — has no realistic path to the merge bar and a
    # NEGATIVE OOS is foreseeable. The trade-rate floor (>=10/month) is also a
    # hard project gate.
    best = max([r_strict, r_loose], key=lambda r: r["net_sharpe"])
    crit_sharpe = best["net_sharpe"] >= 0.30
    crit_traderate = (best["total_trades"] / best["n_months"]) >= 10.0
    # out-of-formation cointegration survival — the prep-memo caveat, quantified
    crit_oof = (
        np.isfinite(best["oof_adf_frac_coint"])
        and best["oof_adf_frac_coint"] >= 0.50
    )
    print(f"  best faithful book: NET monthly Sharpe {best['net_sharpe']:+.4f}"
          f"  (>= +0.30 ? {'PASS' if crit_sharpe else 'FAIL'})")
    print(f"  trade rate: {best['total_trades'] / best['n_months']:.1f}/month"
          f"  (>= 10 ? {'PASS' if crit_traderate else 'FAIL'})")
    print(f"  out-of-formation spread still cointegrated: "
          f"{best['oof_adf_frac_coint']:.4f}"
          f"  (>= 0.50 ? {'PASS' if crit_oof else 'FAIL'})")
    print()
    verdict = "GO" if (crit_sharpe and crit_traderate and crit_oof) else "NO-GO"
    print(f"  >>> STRESS-TESTED VERDICT: {verdict} <<<")
    print("=" * 78)


if __name__ == "__main__":
    main()
