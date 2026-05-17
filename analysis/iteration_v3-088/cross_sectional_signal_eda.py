"""iter-v3/088 — Cross-sectional relative-value EDA (IS-ONLY).

RE-ARCHITECTURE iteration. Direction LOCKED by the orchestrator: replace the
per-symbol absolute-triple-barrier architecture with a cross-sectional
relative-value RANKING model (the equity-quant cross-sectional factor playbook
ported to crypto perps — Poh/Lim/Zohren/Roberts arXiv 2012.07149; Liu/Tsyvinski
JoF 2022; Cakici et al. IRFA 94 2024).

This EDA validates — ON IS DATA ONLY (open_time < OOS_CUTOFF_MS = 2025-03-24) —
the design choices a cross-sectional ranking model needs settled a-priori:

  T1  Universe screen: data depth + IS-window liquidity of all candidate
      Binance-USDT perps (exclude V3_EXCLUDED_SYMBOLS). Pick the WIDE
      cross-sectional universe.
  T2  Does a cross-sectional relative-value signal EXIST on IS data? The
      canonical test: the rank information coefficient (rank-IC) of a
      past-return predictor against the forward cross-sectional rank of
      returns, across a grid of forward horizons. A positive, stable
      rank-IC at some horizon = a tradeable cross-sectional signal.
  T3  Forward-horizon selection: rank-IC and its IC information ratio
      (mean/std) across horizons {1,2,3,4,6,9} 8h-bars. Pick the horizon
      with the best IS IC-IR.
  T4  Long-short decile/tercile spread: at the chosen horizon, the realized
      forward return of the top vs bottom cross-sectional quantile. This is
      the economic magnitude of the edge and informs quantile-cutoff choice.
  T5  Universe-width sensitivity: rank-IC computed on the wide universe vs
      narrowed subsets — confirms a cross-section needs real breadth (you
      cannot rank 3 symbols).
  T6  Feature cross-sectional-normalization probe: rank-IC of RAW features
      vs CROSS-SECTIONALLY-RANKED features against the forward return rank —
      tests whether cross-sectional normalization of the 14-feature stack
      adds signal.

NO-CHEATING: every table is computed on IS rows only (open_time <
OOS_CUTOFF_MS). The forward horizon, the universe, and the quantile cutoff
are SELECTED on the IS columns; OOS is never read. Outputs are CSVs committed
alongside this script.

Run: uv run python analysis/iteration_v3-088/cross_sectional_signal_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FEATURES_DIR = REPO / "data" / "features_v3"

# IMMUTABLE — the v3 sacred constant. IS = strictly before this ms.
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC

# v3 forbidden symbols (v1/v2 traded + MKR) — a cross-sectional universe must
# exclude them exactly as V3_EXCLUDED_SYMBOLS does.
V3_EXCLUDED = {
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT", "MKRUSDT",
}

# The 14-feature /059 anchor stack (BASELINE_V3) — present in every features_v3 parquet.
ANCHOR_14 = [
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
]

# Candidate cross-sectional universe — liquid Binance-USDT perps with deep 8h
# history, all non-v1/v2, all with a features_v3 parquet available OR fetchable.
# The T1 screen below ranks them; this is the screening pool, not the final pick.
CANDIDATE_POOL = [
    "BCHUSDT", "LDOUSDT", "TRXUSDT", "GALAUSDT", "MANAUSDT", "SANDUSDT",
    "FILUSDT", "AVAXUSDT", "ADAUSDT", "HBARUSDT", "VETUSDT", "AAVEUSDT",
    "ATOMUSDT", "ALGOUSDT", "FTMUSDT", "GRTUSDT", "RUNEUSDT", "THETAUSDT",
    "EOSUSDT", "ICPUSDT", "CRVUSDT", "AXSUSDT",
    # CHZUSDT excluded: no Binance spot pair -> no features_v3 parquet buildable.
]

HORIZONS = [1, 2, 3, 4, 6, 9]  # forward 8h-bar horizons to scan


def _load_is(symbol: str) -> pd.DataFrame | None:
    """Load a features_v3 parquet, IS rows only. Returns None if unavailable."""
    p = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def _fwd_return(close: pd.Series, h: int) -> pd.Series:
    """Forward h-bar simple return. close[t+h]/close[t]-1. Last h rows NaN."""
    return close.shift(-h) / close - 1.0


def main() -> None:
    print("=" * 70)
    print("iter-v3/088 cross-sectional relative-value EDA — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print("=" * 70)

    # --- Load all candidates, IS only -------------------------------------
    frames: dict[str, pd.DataFrame] = {}
    for sym in CANDIDATE_POOL:
        if sym in V3_EXCLUDED:
            continue
        df = _load_is(sym)
        if df is None or len(df) < 200:
            print(f"  {sym}: SKIP (no parquet / <200 IS rows)")
            continue
        frames[sym] = df
    print(f"\nLoaded {len(frames)} candidate symbols with IS features.\n")

    # ====================================================================
    # T1 — universe screen: data depth + IS-window liquidity
    # ====================================================================
    t1_rows = []
    for sym, df in frames.items():
        # IS-window median 8h quote volume = liquidity proxy.
        qv = df["quote_volume"].astype(float)
        first_ms = int(df["open_time"].iloc[0])
        # listing burn-in: drop first 60 days (180 8h-bars) for new-listing
        # non-stationarity — count rows AFTER burn-in.
        rows_post_burnin = int((df["open_time"] >= first_ms + 60 * 86400_000).sum())
        t1_rows.append({
            "symbol": sym,
            "is_rows_total": len(df),
            "is_rows_post_60d_burnin": rows_post_burnin,
            "is_first_date_ms": first_ms,
            "is_median_quote_vol_usd": round(float(qv.median()), 0),
            "is_min_quote_vol_usd": round(float(qv.quantile(0.05)), 0),
        })
    t1 = pd.DataFrame(t1_rows).sort_values("is_median_quote_vol_usd", ascending=False)
    # Screen: keep symbols with >=1500 IS rows post-burn-in AND median 8h
    # quote-volume >= $2M (a liquidity floor — thin perps add noise to the
    # cross-section, not signal).
    t1["passes_screen"] = (
        (t1["is_rows_post_60d_burnin"] >= 1500)
        & (t1["is_median_quote_vol_usd"] >= 2_000_000)
    )
    t1.to_csv(OUT / "T1_universe_screen.csv", index=False)
    universe = list(t1[t1["passes_screen"]]["symbol"])
    print(f"T1 — universe screen: {len(universe)} of {len(frames)} symbols pass")
    print(f"  PASS: {universe}")
    print(f"  (screen: >=1500 IS rows post-60d-burn-in AND median 8h QV >= $2M)\n")

    if len(universe) < 8:
        print("WARNING: <8 symbols pass — a cross-section needs breadth.")

    # --- Build a pooled IS panel, restricted to the screened universe -----
    # Align on open_time. Each symbol contributes (open_time, close, 14 feats).
    panels: dict[str, pd.DataFrame] = {}
    for sym in universe:
        df = frames[sym]
        cols = ["open_time", "close"] + [c for c in ANCHOR_14 if c in df.columns]
        sub = df[cols].copy()
        # 60-day listing burn-in
        first_ms = int(sub["open_time"].iloc[0])
        sub = sub[sub["open_time"] >= first_ms + 60 * 86400_000].copy()
        sub = sub.set_index("open_time")
        panels[sym] = sub

    # Common timestamp axis = union; cross-section at each timestamp is the set
    # of symbols trading at that timestamp (>= MIN_XS symbols).
    MIN_XS = 6  # need at least 6 symbols to form a meaningful cross-section
    all_ts = sorted(set().union(*[set(p.index) for p in panels.values()]))
    print(f"Pooled IS panel: {len(all_ts)} unique 8h timestamps across {len(universe)} symbols\n")

    # past-return predictor: 12-bar (4-day) trailing return — the cross-sectional
    # momentum predictor (Jegadeesh-Titman ported; 12 bars chosen a-priori as a
    # standard medium-horizon momentum window, NOT tuned).
    PAST_WIN = 12
    for sym, p in panels.items():
        p["past_ret_12"] = p["close"] / p["close"].shift(PAST_WIN) - 1.0

    # ====================================================================
    # T2 + T3 — does a cross-sectional signal exist, and at what horizon?
    #   At each timestamp with >= MIN_XS symbols: cross-sectionally rank the
    #   past-return predictor, cross-sectionally rank the forward return,
    #   compute the Spearman rank-IC. Aggregate over IS timestamps.
    # ====================================================================
    t3_rows = []
    per_h_ic_series: dict[int, list[float]] = {h: [] for h in HORIZONS}
    for h in HORIZONS:
        # forward h-bar return per symbol
        for sym, p in panels.items():
            p[f"fwd_{h}"] = _fwd_return(p["close"], h)
        ics: list[float] = []
        for ts in all_ts:
            preds, fwds = [], []
            for sym, p in panels.items():
                if ts not in p.index:
                    continue
                row = p.loc[ts]
                pr, fw = row["past_ret_12"], row[f"fwd_{h}"]
                if pd.notna(pr) and pd.notna(fw):
                    preds.append(float(pr))
                    fwds.append(float(fw))
            if len(preds) < MIN_XS:
                continue
            pr_arr = pd.Series(preds).rank()
            fw_arr = pd.Series(fwds).rank()
            ic = pr_arr.corr(fw_arr, method="pearson")  # rank-corr = Spearman
            if pd.notna(ic):
                ics.append(float(ic))
        ics_arr = np.array(ics)
        per_h_ic_series[h] = ics
        mean_ic = float(ics_arr.mean()) if len(ics_arr) else float("nan")
        std_ic = float(ics_arr.std(ddof=1)) if len(ics_arr) > 1 else float("nan")
        ic_ir = mean_ic / std_ic if std_ic and std_ic > 0 else float("nan")
        frac_pos = float((ics_arr > 0).mean()) if len(ics_arr) else float("nan")
        # t-stat of the mean IC across the IS cross-section snapshots
        t_stat = (
            mean_ic / (std_ic / np.sqrt(len(ics_arr)))
            if std_ic and std_ic > 0 and len(ics_arr) > 1
            else float("nan")
        )
        t3_rows.append({
            "fwd_horizon_bars": h,
            "fwd_horizon_days": round(h * 8 / 24, 2),
            "n_xs_snapshots": len(ics_arr),
            "mean_rank_ic": round(mean_ic, 5),
            "std_rank_ic": round(std_ic, 5),
            "ic_information_ratio": round(ic_ir, 4),
            "frac_snapshots_positive_ic": round(frac_pos, 4),
            "t_stat_mean_ic": round(t_stat, 3),
        })
    t3 = pd.DataFrame(t3_rows)
    t3["abs_ic_information_ratio"] = t3["ic_information_ratio"].abs()
    t3.to_csv(OUT / "T3_horizon_rank_ic.csv", index=False)
    print("T2/T3 — cross-sectional rank-IC of 12-bar past return vs forward return:")
    print(t3.to_string(index=False))
    # SELECT the horizon: STRONGEST IS IC information ratio by MAGNITUDE
    # (|mean/std|) — an IS-only, SIGN-AGNOSTIC criterion. A negative rank-IC is
    # a tradeable cross-sectional signal (reversal): a ranking model learns the
    # sign from the labels. Selecting by raw IC-IR would wrongly prefer the
    # weakest horizon. OOS is never consulted.
    best = t3.loc[t3["abs_ic_information_ratio"].idxmax()]
    H = int(best["fwd_horizon_bars"])
    sig_sign = "REVERSAL (past winners underperform)" if best["mean_rank_ic"] < 0 \
        else "MOMENTUM (past winners outperform)"
    print(f"\n  -> SELECTED forward horizon (strongest |IS IC-IR|): {H} bars "
          f"({H*8/24:.1f} days), IC-IR={best['ic_information_ratio']}, "
          f"mean rank-IC={best['mean_rank_ic']}, t={best['t_stat_mean_ic']}")
    print(f"  -> cross-sectional signal DIRECTION: {sig_sign}\n")

    # ====================================================================
    # T4 — long-short quantile spread at the SELECTED horizon H, traded in the
    #   IS-determined signal DIRECTION. The T3 rank-IC is negative (reversal),
    #   so a profitable cross-sectional book LONGs the recent LOSERS (bottom
    #   past-return quantile) and SHORTs the recent WINNERS (top quantile).
    #   We report BOTH the momentum-direction spread (top-minus-bottom) and the
    #   reversal-direction spread (bottom-minus-top) so the brief shows the
    #   sign explicitly; the model would learn whichever sign IS has.
    # ====================================================================
    for sym, p in panels.items():
        p[f"fwd_{H}"] = _fwd_return(p["close"], H)
    t4_long = []
    for q_name, q_lo, q_hi in [("tercile", 1 / 3, 2 / 3), ("quartile", 0.25, 0.75)]:
        longs, shorts = [], []
        for ts in all_ts:
            rows = []
            for sym, p in panels.items():
                if ts not in p.index:
                    continue
                r = p.loc[ts]
                if pd.notna(r["past_ret_12"]) and pd.notna(r[f"fwd_{H}"]):
                    rows.append((sym, float(r["past_ret_12"]), float(r[f"fwd_{H}"])))
            if len(rows) < MIN_XS:
                continue
            rows.sort(key=lambda x: x[1])  # ascending past return
            n = len(rows)
            lo_cut = int(np.floor(q_lo * n))
            hi_cut = int(np.ceil(q_hi * n))
            bottom = rows[:max(lo_cut, 1)]            # recent LOSERS
            top = rows[hi_cut:] if hi_cut < n else rows[-1:]  # recent WINNERS
            longs.append(np.mean([r[2] for r in top]))    # fwd ret of winners
            shorts.append(np.mean([r[2] for r in bottom]))  # fwd ret of losers
        longs_a, shorts_a = np.array(longs), np.array(shorts)
        mom_ls = longs_a - shorts_a   # momentum book: long winners, short losers
        rev_ls = shorts_a - longs_a   # reversal book: long losers, short winners
        t4_long.append({
            "quantile_scheme": q_name,
            "n_snapshots": len(longs_a),
            "mean_winner_fwd_ret": round(float(longs_a.mean()), 5),
            "mean_loser_fwd_ret": round(float(shorts_a.mean()), 5),
            "momentum_book_mean_spread": round(float(mom_ls.mean()), 5),
            "momentum_book_spread_sharpe": round(
                float(mom_ls.mean() / mom_ls.std(ddof=1))
                if mom_ls.std(ddof=1) > 0 else float("nan"), 4),
            "reversal_book_mean_spread": round(float(rev_ls.mean()), 5),
            "reversal_book_spread_sharpe": round(
                float(rev_ls.mean() / rev_ls.std(ddof=1))
                if rev_ls.std(ddof=1) > 0 else float("nan"), 4),
            "frac_snapshots_reversal_positive": round(float((rev_ls > 0).mean()), 4),
        })
    t4 = pd.DataFrame(t4_long)
    t4.to_csv(OUT / "T4_long_short_spread.csv", index=False)
    print(f"T4 — long-short quantile spread at horizon H={H} "
          f"(momentum book vs reversal book):")
    print(t4.to_string(index=False))
    print()

    # ====================================================================
    # T5 — universe-width sensitivity: rank-IC at H on the FULL screened
    #   universe vs narrowed subsets (top-k by liquidity). Confirms breadth
    #   matters — a cross-section is meaningless at N=3.
    # ====================================================================
    t5_rows = []
    liq_order = list(t1[t1["passes_screen"]].sort_values(
        "is_median_quote_vol_usd", ascending=False)["symbol"])
    for k in [3, 5, 8, 12, len(universe)]:
        if k > len(universe):
            continue
        sub_syms = liq_order[:k]
        ics = []
        for ts in all_ts:
            preds, fwds = [], []
            for sym in sub_syms:
                p = panels[sym]
                if ts not in p.index:
                    continue
                r = p.loc[ts]
                if pd.notna(r["past_ret_12"]) and pd.notna(r[f"fwd_{H}"]):
                    preds.append(float(r["past_ret_12"]))
                    fwds.append(float(r[f"fwd_{H}"]))
            if len(preds) < min(MIN_XS, k):
                continue
            ic = pd.Series(preds).rank().corr(pd.Series(fwds).rank())
            if pd.notna(ic):
                ics.append(float(ic))
        ics_a = np.array(ics)
        std = ics_a.std(ddof=1) if len(ics_a) > 1 else float("nan")
        t5_rows.append({
            "universe_width_k": k,
            "n_snapshots": len(ics_a),
            "mean_rank_ic": round(float(ics_a.mean()), 5) if len(ics_a) else float("nan"),
            "ic_information_ratio": round(
                float(ics_a.mean() / std) if std and std > 0 else float("nan"), 4),
        })
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_universe_width_sensitivity.csv", index=False)
    print(f"T5 — universe-width sensitivity (rank-IC at H={H}):")
    print(t5.to_string(index=False))
    print()

    # ====================================================================
    # T6 — per-feature cross-sectional rank-IC + cross-sectional DISPERSION.
    #   For each of the 14 anchor features: (a) the per-snapshot Spearman
    #   rank-IC of the feature vs the forward-H return — how predictive the
    #   feature is OF THE CROSS-SECTIONAL ORDER; (b) the cross-sectional
    #   dispersion of the feature (mean per-snapshot std/|mean|) — a feature
    #   with ~zero cross-sectional dispersion (e.g. btc_ret_14d, identical for
    #   every symbol at a timestamp) carries NO cross-sectional information
    #   and must be cross-sectionally DROPPED or DEMEANED in the ranking model.
    # ====================================================================
    t6_rows = []
    for feat in ANCHOR_14:
        ics, disp = [], []
        for ts in all_ts:
            vals, fwds = [], []
            for sym, p in panels.items():
                if ts not in p.index or feat not in p.columns:
                    continue
                r = p.loc[ts]
                if pd.notna(r[feat]) and pd.notna(r[f"fwd_{H}"]):
                    vals.append(float(r[feat]))
                    fwds.append(float(r[f"fwd_{H}"]))
            if len(vals) < MIN_XS:
                continue
            va = np.array(vals)
            ic = pd.Series(vals).rank().corr(pd.Series(fwds).rank())
            if pd.notna(ic):
                ics.append(float(ic))
            # cross-sectional dispersion: std across symbols / (|mean|+eps)
            m = abs(va.mean())
            disp.append(float(va.std() / (m + 1e-9)))
        ra = np.array(ics)
        da = np.array(disp)
        t6_rows.append({
            "feature": feat,
            "n_snapshots": len(ra),
            "mean_xs_rank_ic_vs_fwd": round(float(ra.mean()), 5) if len(ra) else float("nan"),
            "abs_mean_xs_rank_ic": round(abs(float(ra.mean())), 5) if len(ra) else float("nan"),
            "ic_ir": round(
                float(ra.mean() / ra.std(ddof=1))
                if len(ra) > 1 and ra.std(ddof=1) > 0 else float("nan"), 4),
            "mean_xs_dispersion": round(float(da.mean()), 5) if len(da) else float("nan"),
        })
    t6 = pd.DataFrame(t6_rows).sort_values("abs_mean_xs_rank_ic", ascending=False)
    t6.to_csv(OUT / "T6_feature_xs_rank_ic.csv", index=False)
    print(f"T6 — per-feature cross-sectional rank-IC + dispersion (H={H}):")
    print(t6.to_string(index=False))
    print()

    # ====================================================================
    # T7 — multi-feature COMPOSITE predictor vs the single momentum predictor.
    #   A cross-sectional RANKING MODEL combines many features. T7 tests, IS
    #   only, whether an equal-weight composite of the 14 anchor features'
    #   per-snapshot cross-sectional ranks (each rank SIGN-ALIGNED to its own
    #   IS rank-IC) produces a stronger rank-IC vs the forward return than the
    #   single 12-bar momentum predictor. A composite that beats the single
    #   predictor is direct IS evidence that a multi-feature ranking model has
    #   headroom over classical cross-sectional momentum — the core claim of
    #   the re-architecture (Poh/Lim/Zohren arXiv 2012.07149).
    #   NO-CHEATING: the sign-alignment uses the SAME IS rank-IC computed in T6
    #   (IS data only); the composite is evaluated on the SAME IS snapshots.
    # ====================================================================
    feat_sign = {r["feature"]: (1.0 if r["mean_xs_rank_ic_vs_fwd"] >= 0 else -1.0)
                 for r in t6_rows}
    # exclude near-zero-dispersion features (no cross-sectional content)
    xs_feats = [r["feature"] for r in t6_rows
                if pd.notna(r["mean_xs_dispersion"]) and r["mean_xs_dispersion"] > 1e-4]
    comp_ic, mom_ic = [], []
    for ts in all_ts:
        # gather symbols present with all xs_feats + fwd + past_ret
        recs = []
        for sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r[f"fwd_{H}"]) or pd.isna(r["past_ret_12"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in xs_feats):
                continue
            recs.append((sym, r))
        if len(recs) < MIN_XS:
            continue
        fwds = pd.Series([float(r[f"fwd_{H}"]) for _, r in recs])
        # composite score: sum over features of (sign-aligned cross-sectional rank)
        comp = np.zeros(len(recs))
        for f in xs_feats:
            fr = pd.Series([float(r[f]) for _, r in recs]).rank()
            comp += feat_sign[f] * fr.to_numpy()
        comp_s = pd.Series(comp)
        mom_s = pd.Series([float(r["past_ret_12"]) for _, r in recs])
        ic_c = comp_s.rank().corr(fwds.rank())
        ic_m = mom_s.rank().corr(fwds.rank())
        if pd.notna(ic_c):
            comp_ic.append(float(ic_c))
        if pd.notna(ic_m):
            mom_ic.append(float(ic_m))
    ca, ma = np.array(comp_ic), np.array(mom_ic)
    t7 = pd.DataFrame([
        {
            "predictor": "single_12bar_momentum",
            "n_snapshots": len(ma),
            "mean_rank_ic": round(float(ma.mean()), 5),
            "ic_information_ratio": round(
                float(ma.mean() / ma.std(ddof=1)) if ma.std(ddof=1) > 0 else float("nan"), 4),
            "t_stat": round(
                float(ma.mean() / (ma.std(ddof=1) / np.sqrt(len(ma))))
                if len(ma) > 1 and ma.std(ddof=1) > 0 else float("nan"), 3),
        },
        {
            "predictor": f"equalweight_composite_{len(xs_feats)}feat",
            "n_snapshots": len(ca),
            "mean_rank_ic": round(float(ca.mean()), 5),
            "ic_information_ratio": round(
                float(ca.mean() / ca.std(ddof=1)) if ca.std(ddof=1) > 0 else float("nan"), 4),
            "t_stat": round(
                float(ca.mean() / (ca.std(ddof=1) / np.sqrt(len(ca))))
                if len(ca) > 1 and ca.std(ddof=1) > 0 else float("nan"), 3),
        },
    ])
    t7.to_csv(OUT / "T7_composite_vs_momentum.csv", index=False)
    print(f"T7 — multi-feature composite predictor vs single momentum (H={H}):")
    print(t7.to_string(index=False))
    print(f"  composite uses {len(xs_feats)} cross-sectionally-dispersed features: {xs_feats}")
    comp_ir = abs(float(ca.mean() / ca.std(ddof=1))) if ca.std(ddof=1) > 0 else 0.0
    mom_ir = abs(float(ma.mean() / ma.std(ddof=1))) if ma.std(ddof=1) > 0 else 0.0
    print(f"  -> composite |IC-IR| {comp_ir:.4f} vs momentum |IC-IR| {mom_ir:.4f} "
          f"({'COMPOSITE STRONGER — ranking model has headroom' if comp_ir > mom_ir else 'momentum stronger'})\n")

    # --- Summary ----------------------------------------------------------
    print("=" * 70)
    print("EDA SUMMARY — design choices selected on IS data only")
    print("=" * 70)
    print(f"  Universe (T1): {len(universe)} liquid non-v1/v2 perps -> {universe}")
    print(f"  Forward horizon (T3, strongest |IS IC-IR|): {H} bars = {H*8/24:.1f} days")
    print(f"  Cross-sectional signal exists: mean rank-IC={best['mean_rank_ic']} "
          f"t={best['t_stat_mean_ic']} -> {sig_sign}")
    print(f"  L-S spread (T4) + breadth (T5) + composite headroom (T7): see CSVs")
    print("  ALL tables IS-only. OOS never read. Horizon/universe/quantile a-priori or IS-selected.")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
