"""iter-v3/106 EDA script 4 — final regime-separator check + drawdown-brake counterfactual.

EDA 2 + EDA 3 falsified the user's literal "unseen-regime" hypothesis on the
14-feature Mahalanobis OOD axis (month AUC 0.559, trade AUC 0.504) and showed
that a trailing-drawdown brake would STOP trades that are net-PROFITABLE
(drawdowns mean-revert on this roster).

This script is the LAST-CHANCE check before a NULL-AT-EDA verdict. It asks two
questions, both strictly IS-only and strictly causal:

  Q4 — Is there ANY single causal regime variable, measured as a SUSTAINED
       state (a trailing window, not a point), that separates loss months from
       profit months at AUC >= 0.70? We sweep a wider battery than EDA 2:
         - BTC trailing return over 30/60/90 days (bull vs bear directional state)
         - BTC trailing realized vol over 30/60 days (absolute level + percentile)
         - symbol trailing realized vol percentile
         - symbol trailing return (own directional state)
         - the 14-feature Mahalanobis OOD at 3 reference-window lengths
           (12 / 18 / 24 months) — to rule out that 24m was simply the wrong
           reference length
       A clean separator here would resurrect the axis with a different
       construction. No separator >= 0.70 => the axis is genuinely NULL.

  Q5 — Full IS counterfactual for a trailing-equity drawdown brake (the user's
       "stop when losing" mechanism, the cleanest stop construction). For a grid
       of trigger thresholds, simulate: kill every trade entered while the
       portfolio trailing-equity drawdown (known from prior closed trades, i.e.
       past-only) exceeds the trigger. Report the resulting IS weighted_pnl and
       IS monthly Sharpe. This QUANTIFIES whether a stop helps at all.

NO CHEATING — IS-only, causal. The OOS roster is never read. BTC/symbol regime
variables use close.shift(1) before any rolling op. The drawdown state for a
trade is computed only from trades that CLOSED before it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS

OUT_DIR = "analysis/iteration_v3-106"
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
TRADES_CSV = "reports-v3/iteration_v3-059/in_sample/trades.csv"
BAR_MS = 8 * 60 * 60 * 1000


def auc_loss_high(values: np.ndarray, is_loss: np.ndarray) -> float:
    ok = np.isfinite(values)
    vl, vp = values[ok & is_loss], values[ok & ~is_loss]
    if len(vl) == 0 or len(vp) == 0:
        return np.nan
    wins = sum((a > b) + 0.5 * (a == b) for a in vl for b in vp)
    return wins / (len(vl) * len(vp))


def maha_month(feats: dict, month_start_ms: int, month_end_ms: int, ref_months: int) -> float:
    fcols = list(V3_FEATURE_COLUMNS)
    month_start = pd.Timestamp(month_start_ms, unit="ms")
    train_start = int((month_start - pd.DateOffset(months=ref_months)).value // 1_000_000)
    per_sym = []
    for s in SYMBOLS:
        df = feats[s]
        ref = df[(df["close_time"] >= train_start) & (df["close_time"] < month_start_ms)]
        test = df[(df["close_time"] >= month_start_ms) & (df["close_time"] <= month_end_ms)]
        X = ref[fcols].to_numpy()
        X = X[~np.isnan(X).any(axis=1)]
        T = test[fcols].to_numpy()
        T = T[~np.isnan(T).any(axis=1)]
        if len(X) < 100 or len(T) == 0:
            continue
        mu = X.mean(axis=0)
        cov = np.cov(X, rowvar=False)
        cov = cov + 1e-6 * np.mean(np.diag(cov)) * np.eye(cov.shape[0])
        try:
            inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            continue
        d = T - mu
        d2 = np.einsum("ij,jk,ik->i", d, inv, d)
        d2 = d2[d2 >= 0]
        if len(d2):
            per_sym.append(float(np.sqrt(d2).mean()))
    return float(np.mean(per_sym)) if per_sym else np.nan


def main() -> None:
    months = pd.read_csv(f"{OUT_DIR}/T1_per_month_is_pnl.csv")
    months["is_loss"] = months["weighted_pnl"] < 0
    is_loss = months["is_loss"].to_numpy()

    # ---- load feature parquets (close_time-indexed, see EDA 3 note) ----
    fcols_needed = list(dict.fromkeys(["open_time", "close_time", "close",
                                       "atr_pct_rank_200", "range_realized_vol_50",
                                       *V3_FEATURE_COLUMNS]))
    feats = {}
    for s in SYMBOLS:
        df = pq.read_table(f"data/features_v3/{s}_8h_features.parquet",
                            columns=fcols_needed).to_pandas()
        feats[s] = df.sort_values("close_time").reset_index(drop=True)

    btc = pq.read_table("data/features_v3/BTCUSDT_8h_features.parquet",
                        columns=["close_time", "close"]).to_pandas()
    btc = btc.sort_values("close_time").reset_index(drop=True)
    bc = btc["close"].astype(float)
    logret = np.log(bc / bc.shift(1))

    print("=" * 84)
    print("iter-v3/106 EDA 4 — FINAL REGIME-SEPARATOR SWEEP + DRAWDOWN-BRAKE COUNTERFACTUAL")
    print("=" * 84)

    # ------------------------------------------------------------------
    # Q4 — wide causal regime-separator sweep at month level
    # ------------------------------------------------------------------
    rows = []
    for _, m in months.iterrows():
        ms_start = int(pd.Period(m["month"], freq="M").start_time.value // 1_000_000)
        ms_end = int(pd.Period(m["month"], freq="M").end_time.value // 1_000_000)
        rec: dict[str, float] = {"month": m["month"]}

        # BTC trailing return / vol at month start (causal)
        bidx = int(np.searchsorted(btc["close_time"].to_numpy(), ms_start, side="left")) - 1
        for days, bars in [(30, 90), (60, 180), (90, 270)]:
            if bidx - bars >= 0:
                rec[f"btc_ret_{days}d"] = float(bc.iloc[bidx] / bc.iloc[bidx - bars] - 1.0)
            else:
                rec[f"btc_ret_{days}d"] = np.nan
        for days, bars in [(30, 90), (60, 180)]:
            if bidx - bars >= 0:
                rec[f"btc_vol_{days}d"] = float(logret.iloc[bidx - bars + 1 : bidx + 1].std())
            else:
                rec[f"btc_vol_{days}d"] = np.nan
        # absolute BTC return magnitude (regime intensity, direction-agnostic)
        rec["btc_abs_ret_60d"] = abs(rec["btc_ret_60d"]) if np.isfinite(rec["btc_ret_60d"]) else np.nan

        # symbol trailing return + vol percentile at month start (causal, averaged)
        sret, svolp = [], []
        for s in SYMBOLS:
            df = feats[s]
            sidx = int(np.searchsorted(df["close_time"].to_numpy(), ms_start, side="left")) - 1
            if sidx - 90 >= 0:
                sret.append(float(df["close"].iloc[sidx] / df["close"].iloc[sidx - 90] - 1.0))
            if sidx >= 0 and np.isfinite(df["atr_pct_rank_200"].iloc[sidx]):
                svolp.append(float(df["atr_pct_rank_200"].iloc[sidx]))
        rec["sym_ret_30d"] = float(np.mean(sret)) if sret else np.nan
        rec["sym_atr_pct"] = float(np.mean(svolp)) if svolp else np.nan

        # Mahalanobis OOD at 3 reference lengths
        for ref_m in (12, 18, 24):
            rec[f"maha_ood_{ref_m}m"] = maha_month(feats, ms_start, ms_end, ref_m)

        rows.append(rec)

    q4 = pd.DataFrame(rows)
    q4 = q4.merge(months[["month", "is_loss", "weighted_pnl"]], on="month")
    q4.to_csv(f"{OUT_DIR}/T7_wide_regime_separators.csv", index=False)

    cands = [c for c in q4.columns if c not in ("month", "is_loss", "weighted_pnl")]
    print()
    print("Q4 — wide regime-separator sweep (month level, 15 loss vs 21 profit)")
    print(f"{'candidate':<22} {'mean(loss)':>12} {'mean(profit)':>13} {'AUC':>8} {'|AUC-.5|':>9}")
    print("-" * 68)
    res = []
    for c in cands:
        v = q4[c].to_numpy(dtype=float)
        a = auc_loss_high(v, q4["is_loss"].to_numpy())
        ok = np.isfinite(v)
        ml = v[ok & q4["is_loss"].to_numpy()].mean() if (ok & q4["is_loss"].to_numpy()).any() else np.nan
        mp = v[ok & ~q4["is_loss"].to_numpy()].mean() if (ok & ~q4["is_loss"].to_numpy()).any() else np.nan
        strength = abs(a - 0.5) if np.isfinite(a) else np.nan
        print(f"{c:<22} {ml:>12.4f} {mp:>13.4f} {a:>8.3f} {strength:>9.3f}")
        res.append({"candidate": c, "mean_loss": ml, "mean_profit": mp,
                    "auc": a, "abs_auc_minus_half": strength})
    pd.DataFrame(res).sort_values("abs_auc_minus_half", ascending=False).to_csv(
        f"{OUT_DIR}/T8_separator_ranking.csv", index=False)
    best = max((r for r in res if np.isfinite(r["abs_auc_minus_half"])),
               key=lambda r: r["abs_auc_minus_half"])
    print()
    print(f"STRONGEST separator: {best['candidate']}  AUC={best['auc']:.3f}  "
          f"(|AUC-0.5|={best['abs_auc_minus_half']:.3f})")
    print("PASS bar for a usable causal detector: |AUC-0.5| >= 0.20  (AUC<=0.30 or >=0.70)")
    print(f"  => {'PASS' if best['abs_auc_minus_half'] >= 0.20 else 'FAIL — no clean separator'}")

    # ------------------------------------------------------------------
    # Q5 — full IS counterfactual: trailing-equity drawdown brake
    # ------------------------------------------------------------------
    df = pd.read_csv(TRADES_CSV)
    assert (df["open_time"] < OOS_CUTOFF_MS).all(), "IS-only invariant violated"
    df = df.sort_values("open_time").reset_index(drop=True)

    def monthly_sharpe(frame: pd.DataFrame) -> float:
        if len(frame) == 0:
            return np.nan
        f = frame.copy()
        f["month"] = pd.to_datetime(f["open_time"], unit="ms").dt.to_period("M").astype(str)
        mo = f.groupby("month")["weighted_pnl"].sum()
        return float(mo.mean() / mo.std(ddof=1) * np.sqrt(12)) if len(mo) > 1 and mo.std(ddof=1) > 0 else np.nan

    base_wpnl = df["weighted_pnl"].sum()
    base_sharpe = monthly_sharpe(df)
    print()
    print("Q5 — trailing-equity DRAWDOWN-BRAKE counterfactual (the 'stop when losing' mechanism)")
    print(f"  /059 IS baseline: weighted_pnl {base_wpnl:+.2f}, monthly Sharpe {base_sharpe:+.4f}")
    print(f"  {'trigger(wpnl)':>14} {'trades_killed':>14} {'kept_wpnl':>11} {'kept_sharpe':>12} {'Δsharpe':>9}")
    print("  " + "-" * 64)
    q5 = []
    for trig in (3.0, 5.0, 8.0, 10.0, 12.0, 15.0):
        # Past-only trailing drawdown: recompute equity from prior trades only.
        cum, peak = 0.0, 0.0
        kept_rows = []
        killed = 0
        for _, tr in df.iterrows():
            dd = peak - cum  # drawdown known BEFORE this trade (past-only)
            if dd >= trig:
                killed += 1
                # killed trade: contributes 0, equity unchanged for this trade
                # (the brake removes the trade entirely)
                continue
            kept_rows.append(tr)
            cum += tr["weighted_pnl"]
            peak = max(peak, cum)
        kept = pd.DataFrame(kept_rows)
        kw = kept["weighted_pnl"].sum() if len(kept) else 0.0
        ks = monthly_sharpe(kept)
        dsh = ks - base_sharpe if np.isfinite(ks) and np.isfinite(base_sharpe) else np.nan
        print(f"  {trig:>14.1f} {killed:>14} {kw:>11.2f} {ks:>12.4f} {dsh:>+9.4f}")
        q5.append({"trigger_wpnl": trig, "trades_killed": killed,
                   "kept_wpnl": kw, "kept_monthly_sharpe": ks, "delta_sharpe": dsh})
    pd.DataFrame(q5).to_csv(f"{OUT_DIR}/T9_drawdown_brake_counterfactual.csv", index=False)
    print()
    print("  Reading: a POSITIVE Δsharpe at some trigger => a drawdown brake helps.")
    print("  A NEGATIVE Δsharpe at every trigger => stopping in drawdowns HURTS")
    print("  (drawdowns mean-revert; the brake kills the recovery — the /054 failure mode).")
    print()
    print(f"Wrote {OUT_DIR}/T7_wide_regime_separators.csv  ({len(q4)} rows)")
    print(f"Wrote {OUT_DIR}/T8_separator_ranking.csv")
    print(f"Wrote {OUT_DIR}/T9_drawdown_brake_counterfactual.csv")


if __name__ == "__main__":
    main()
