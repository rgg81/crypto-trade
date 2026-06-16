"""IS-ONLY design-decision test: trend-state direction vs LightGBM direction, +/- magnitude meta-label — iter-v1/016 (BTCUSDT).

PURPOSE
-------
Scripts 1+2 established two facts (IS-only, sub-period stability lens):
  (i)  Gating the LightGBM-LEARNED direction on PREDICTED magnitude makes the most-recent IS
       sub-period WORSE (-2.10 -> -8.25): the big moves are where the overfit sign is most wrong.
  (ii) A STATELESS trend-state direction (close vs SMA200, .shift(1)) is the only rule in the
       campaign whose MOST-RECENT IS sub-period (the OOS fingerprint) is POSITIVE (+1.5..+2.5
       across SMA windows 100-300), with the LOWEST cross-sub-period dispersion.

This script makes the FINAL design decision for iter-016 by comparing, on a faithful walk-forward
let-winners-run proxy:
  BOOK 1 = LGBM-direction  : the campaign's overfit model direction (sign of WF-OOF prediction).
  BOOK 2 = TREND-STATE     : close_prev > SMA(w).shift(1) -> long else short. NO fit -> no overfit.
  BOOK 3 = TREND-STATE + MAGNITUDE META-LABEL : among BOOK 2 trades, take only those a walk-forward
           magnitude REGRESSOR (FE stable vol-core) predicts to be in the TOP (1-q) of |move|.
           This is the López de Prado meta-labeling pattern (AFML Ch.3): the trend-state rule is M1
           (direction), the magnitude model is M2 (act/size). The engine already ships
           MetaLabelingStrategy — this is the IS go/no-go on whether the M2 filter helps the
           trend-state M1 (the dissociation in script 1 was specifically with a LEARNED M1).

We report per-sub-period Sharpe, frac_pos, dispersion, worst, RECENT, win-rate, and trade retention.
The winner is the book with the best stability fingerprint at a usable trade rate.

Also reports a fee+slippage-adjusted per-trade hurdle so the let-run book's edge survives costs:
honest round-trip cost = 0.1% fee + 0.04% slippage = 0.14% per trade (the baseline's costs).

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; forward N-return AFTER the filter; SMA + magnitude model trained/threshold-ed on
PAST rows only (strict train<test-start - embargo); `.shift(1)` direction; OOS never read. `src/`
+ runner + OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-016/design_decision_trendstate_metalabel.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-016"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
EMBARGO = N_LABEL
SMA_WIN = 200          # trend-state window (robust 100-300 per probe; 200 = mid, crypto-canonical)
META_Q = 0.40          # meta-label: keep trades with predicted |move| >= past-only p40 (top 60%)
RT_COST = 0.14         # honest round-trip cost, % (0.1% fee + 0.04% slippage) — let-run = 1 trade

MAG_CORE: tuple[str, ...] = (
    "vol_natr_7", "vol_natr_14", "vol_garman_klass_10", "vol_garman_klass_20",
    "vol_parkinson_10", "vol_parkinson_20", "vol_bb_bandwidth_20", "vol_bb_bandwidth_30",
    "vol_atr_14", "vol_hist_20", "vol_range_spike_72", "interact_natr_x_adx",
)

# The campaign's 19-col HYBRID directional set (for BOOK 1 LGBM-direction proxy).
DIR19: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days: np.ndarray) -> list[tuple[float, float]]:
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r: np.ndarray, tpy: float) -> float:
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def wf_predict(df, bounds, ot_days, cols, target, classify):
    """Purged/embargoed walk-forward predictions (regressor for magnitude, classifier for direction)."""
    import lightgbm as lgb
    X = df[list(cols)].to_numpy(float)
    n = len(df)
    pred = np.full(n, np.nan)
    tr_thr = {q: np.full(n, np.nan) for q in (META_Q,)}
    row_idx = np.arange(n)
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        first_i = int(row_idx[tm].min())
        cut = first_i - EMBARGO
        if cut < 200:
            continue
        trm = (row_idx < cut) & np.isfinite(target) & np.isfinite(X).all(axis=1)
        if trm.sum() < 200:
            continue
        if classify:
            m = lgb.LGBMClassifier(n_estimators=200, num_leaves=31, max_depth=5,
                                   learning_rate=0.05, min_child_samples=30, subsample=0.8,
                                   colsample_bytree=0.8, reg_lambda=1.0, random_state=42, verbose=-1)
            m.fit(X[trm], (target[trm] > 0).astype(int))
            te = row_idx[tm]
            ok = np.isfinite(X[te]).all(axis=1)
            p = np.full(len(te), np.nan)
            if ok.sum():
                p[ok] = m.predict_proba(X[te][ok])[:, 1]  # P(up)
            pred[te] = p
        else:
            m = lgb.LGBMRegressor(n_estimators=200, num_leaves=31, max_depth=5,
                                  learning_rate=0.05, min_child_samples=30, subsample=0.8,
                                  colsample_bytree=0.8, reg_lambda=1.0, random_state=42, verbose=-1)
            m.fit(X[trm], target[trm])
            trp = m.predict(X[trm])
            te = row_idx[tm]
            ok = np.isfinite(X[te]).all(axis=1)
            p = np.full(len(te), np.nan)
            if ok.sum():
                p[ok] = m.predict(X[te][ok])
            pred[te] = p
            for q in (META_Q,):
                tr_thr[q][te] = float(np.quantile(trp, q))
    return pred, tr_thr


def stability(per_trade, fire, ot_days, bounds, sub_labels):
    tpy = BARS_PER_YEAR / max(N_LABEL, 1)
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(per_trade)
        arr = per_trade[m]
        sh.append(ann_sharpe(arr, tpy) if len(arr) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent = next((v for v in reversed(s) if np.isfinite(v)), np.nan)
    nt = int((fire & np.isfinite(per_trade)).sum())
    pt = per_trade[fire & np.isfinite(per_trade)]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        full=round(ann_sharpe(pt, tpy), 4) if nt else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        n_scored=int(len(valid)), n_trades=nt,
        win_rate=round(float(np.mean(pt > 0)), 4) if nt else np.nan,
        mean_ret_pct=round(float(np.mean(pt) * 100.0), 4) if nt else np.nan,
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)            # signed forward N-return, AFTER IS filter
    # cost is applied per-trade inside net_per_trade() below (one round-trip per let-run trade).
    abs_y = np.abs(y)

    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]
    tpy = BARS_PER_YEAR / N_LABEL
    print(f"IS rows {len(df)}  sub-periods {len(bounds)}  N={N_LABEL}(14d)  SMA{SMA_WIN}  "
          f"meta_q=p{int(META_Q*100)}  RT_cost={RT_COST}%  trades/yr~{tpy:.1f}")
    print("=" * 118)

    # ---- BOOK 1: LGBM direction (walk-forward classifier on the 19-col directional set) ----
    p_up, _ = wf_predict(df, bounds, ot_days, DIR19, y, classify=True)
    lgbm_dir = np.where(np.isfinite(p_up), np.where(p_up >= 0.5, 1.0, -1.0), np.nan)

    # ---- BOOK 2: trend-state direction (stateless, past-only) ----
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    ts_dir = np.where(np.isfinite(sma) & np.isfinite(cp), np.where(cp > sma, 1.0, -1.0), np.nan)

    # ---- magnitude meta-label model (walk-forward regressor on FE stable vol-core) ----
    mag_pred, mag_thr = wf_predict(df, bounds, ot_days, MAG_CORE, abs_y, classify=False)

    # common universe: rows with a finite forward move AND a finite walk-forward prediction set
    base = np.isfinite(y) & np.isfinite(mag_pred) & np.isfinite(lgbm_dir) & np.isfinite(ts_dir)

    # per-trade signed NET return: gross signed move minus round-trip cost on the |move|.
    # let-winners-run = ONE trade per signal held N candles, so ONE round-trip cost.
    def net_per_trade(direction: np.ndarray) -> np.ndarray:
        gross = direction * y
        return gross - (RT_COST / 100.0)  # cost reduces every trade's signed return

    book1 = stability(net_per_trade(lgbm_dir), base, ot_days, bounds, sub_labels)
    book2 = stability(net_per_trade(ts_dir), base, ot_days, bounds, sub_labels)
    meta_fire = base & (mag_pred >= mag_thr[META_Q])
    book3 = stability(net_per_trade(ts_dir), meta_fire, ot_days, bounds, sub_labels)

    rows = [("BOOK1_lgbm_dir", book1), ("BOOK2_trend_state", book2),
            ("BOOK3_trend_state+mag_meta", book3)]
    print(f"{'book':30s} {'full':>7s} {'fpos':>5s} {'disp':>7s} {'worst':>8s} "
          f"{'RECENT':>8s} {'trades':>7s} {'WR':>6s} {'mret%':>7s}")
    for name, b in rows:
        print(f"{name:30s} {b['full']!s:>7} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['worst']!s:>8} {b['recent']!s:>8} {b['n_trades']!s:>7} "
              f"{b['win_rate']!s:>6} {b['mean_ret_pct']!s:>7}")

    print("\n" + "=" * 118)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE (last col = most-recent IS sub-period = OOS fingerprint):")
    print("  " + f"{'book':30s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in rows:
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub"]]
        print(f"  {name:30s} " + " ".join(cells))

    out = []
    for name, b in rows:
        rec = dict(book=name, **{k: v for k, v in b.items() if k != "per_sub"})
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = b["per_sub"][i]
        out.append(rec)
    pd.DataFrame(out).to_csv(OUTDIR / "design_decision_trendstate_metalabel.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'design_decision_trendstate_metalabel.csv'}")

    # ---- decision summary ----
    print("\n" + "=" * 118)
    print("DECISION CRITERIA (IS-only fingerprint of OOS generalization):")
    print("  * RECENT > 0  (the LightGBM-direction book never achieved this)")
    print("  * frac_pos >= 0.7 and dispersion as low as possible")
    print("  * meta-label (BOOK3) ADOPTED only if it RAISES win-rate AND keeps RECENT >= BOOK2 RECENT")
    print("    at retention >= ~0.5; otherwise BOOK2 (bare trend-state) is the design.")
    b2r, b3r = book2["recent"], book3["recent"]
    b2w, b3w = book2["win_rate"], book3["win_rate"]
    ret = book3["n_trades"] / max(book2["n_trades"], 1)
    print(f"\n  BOOK2 recent={b2r} WR={b2w} | BOOK3 recent={b3r} WR={b3w} retention={ret:.2f}")
    meta_helps = (np.isfinite(b3r) and np.isfinite(b2r) and b3r >= b2r
                  and np.isfinite(b3w) and np.isfinite(b2w) and b3w > b2w and ret >= 0.45)
    print(f"  => META-LABEL {'HELPS (adopt BOOK3)' if meta_helps else 'does NOT help (adopt BOOK2 bare)'}")


if __name__ == "__main__":
    main()
