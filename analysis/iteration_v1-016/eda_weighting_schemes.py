"""iter-v1/016 EDA — characterize baseline sample-weighting scheme + predict effect of alternatives.

Goal
----
Three primary questions:

1. **Current baseline weighting profile** — what does `weights = 1.0 + abs(labeled_pnl) /
   max * 9.0` actually look like distributionally per (symbol, training-month)? How
   concentrated is the weight on extreme-PnL outliers?

2. **Label exit-reason distribution** — what fraction of labels are TP-hit / SL-hit /
   timeout-fallback per (symbol, training-month)? Where /015 collapsed to ~85%
   timeout, the baseline ATR labeling (8% TP / 4% SL / 21-candle timeout) should
   show a healthier mix. If timeout-fallback share is ALREADY > 0.6 in baseline,
   /016's Option C (inverse-class-frequency by exit-reason) is well-motivated.

3. **Quantitative prediction of three weighting schemes**:
   - **Option A (1/realized_vol)**: weight = 1 / (30d realized vol). Downweights
     high-vol samples (e.g. LINK + DOT).
   - **Option B (AFML uniqueness)**: weight ∝ 1/avg_overlap_count (already exists).
   - **Option C (inverse-class-frequency by exit-reason)**: weight = 1/freq(exit_reason)
     within (symbol, training-month). Directly addresses /015's timeout-fallback
     dominance mechanism if the same pattern recurs in /016's labeling regime.

This script runs IS-ONLY (open_time < OOS_CUTOFF_MS=2025-03-24). No model training.
Just labeling.label_trades + statistical characterization.

Output tables (printed + saved to analysis/iteration_v1-016/):
- `weight_profile_summary.csv`: per (symbol, month) quantile of baseline weights
- `exit_reason_distribution.csv`: per (symbol, month) TP/SL/timeout shares
- `weighting_scheme_comparison.csv`: predicted weight reshaping under three options
- `n_eff_label_diversity_proxy.csv`: per (symbol, month) Shannon entropy of exit-reason
  distribution (proxy for "loss surface diversity" — high entropy = mixed exits = high
  n_eff potential; low entropy = timeout-dominated = n_eff collapse risk)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Repo paths
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402

OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)

# Baseline ATR-labeling params (matches run_baseline_v1 lines 251-253)
LABEL_TP_PCT = 8.0  # ATR multiplier when use_atr_labeling=True
LABEL_SL_PCT = 4.0
LABEL_TIMEOUT_MIN = 10080  # 7 days = 21 candles at 8h
INTERVAL_MINUTES = 480  # 8h
TIMEOUT_CANDLES = LABEL_TIMEOUT_MIN // INTERVAL_MINUTES  # 21
ATR_TP_MULT = 2.9  # historical baseline (Model A; varies by model — using A as the rough estimator)
ATR_SL_MULT = 1.5
FEE_PCT = 0.1


def _compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder-ATR matching baseline; past-only via .shift(1) at caller site."""
    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1)),
        ),
    )
    tr[0] = high[0] - low[0]
    # Wilder smoothing
    atr = np.zeros_like(tr)
    atr[:period] = np.nan
    atr[period - 1] = tr[:period].mean()
    for i in range(period, len(tr)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _label_quick(
    df: pd.DataFrame,
    atr_vals: np.ndarray,
    tp_mult: float,
    sl_mult: float,
    timeout_candles: int,
    fee_pct: float,
) -> pd.DataFrame:
    """Lean triple-barrier labeler — matches labeling.py logic for analysis only.

    Returns a DataFrame with one row per labeled candle:
    columns: idx, label (1/-1), exit_reason ("tp"/"sl"/"timeout"), labeled_pnl,
    fwd_return_pct
    """
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close = df["close"].to_numpy(dtype=np.float64)
    n = len(df)

    rows = []
    for i in range(n - 1):
        if np.isnan(atr_vals[i]) or atr_vals[i] <= 0:
            continue
        entry = close[i]
        tp_dist = atr_vals[i] * tp_mult
        sl_dist = atr_vals[i] * sl_mult
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist

        long_result, short_result = 0, 0
        long_step, short_step = -1, -1
        last_close = entry
        scanned = 0
        end_j = min(i + 1 + timeout_candles, n)
        for j in range(i + 1, end_j):
            scanned += 1
            last_close = close[j]
            if long_result == 0:
                if low[j] <= long_sl:
                    long_result = -1
                    long_step = j
                elif high[j] >= long_tp:
                    long_result = 1
                    long_step = j
            if short_result == 0:
                if high[j] >= short_sl:
                    short_result = -1
                    short_step = j
                elif low[j] <= short_tp:
                    short_result = 1
                    short_step = j
            if long_result != 0 and short_result != 0:
                break
        if long_result == 0:
            long_result = -2
        if short_result == 0:
            short_result = -2

        fwd_return = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0

        # tp_pct / sl_pct for PnL accounting at this entry (ATR path)
        tp_pnl = tp_dist / entry * 100.0
        sl_pnl = sl_dist / entry * 100.0

        # Compute PnL per leg
        def _pnl(result, sign):
            if result == 1:
                return tp_pnl
            if result == -1:
                return -sl_pnl
            return sign * fwd_return

        long_pnl = _pnl(long_result, 1.0) - fee_pct
        short_pnl = _pnl(short_result, -1.0) - fee_pct

        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            label = 1
            reason = "long_tp_only"
            labeled_pnl = long_pnl
        elif short_tp_hit and not long_tp_hit:
            label = -1
            reason = "short_tp_only"
            labeled_pnl = short_pnl
        elif long_tp_hit and short_tp_hit:
            if long_step <= short_step:
                label = 1
                reason = "both_tp→long_first"
                labeled_pnl = long_pnl
            else:
                label = -1
                reason = "both_tp→short_first"
                labeled_pnl = short_pnl
        else:
            # No TP hit; use fwd_return sign — TIMEOUT-FALLBACK class
            label = 1 if fwd_return >= 0 else -1
            reason = "timeout_fallback"
            labeled_pnl = long_pnl if label == 1 else short_pnl

        # Simplify exit_reason buckets for analysis
        if reason in ("long_tp_only", "short_tp_only", "both_tp→long_first", "both_tp→short_first"):
            simple = "tp_hit"
        elif reason == "timeout_fallback":
            # Check: is the OPPOSITE leg an SL hit? Then it's a true mixed-SL outcome
            opp_result = short_result if label == 1 else long_result
            if opp_result == -1:
                simple = "sl_hit_opp"  # one-sided TP miss + opp SL hit
            else:
                simple = "timeout"  # both timed out → fwd_return sign fallback
        else:
            simple = "unknown"

        rows.append({
            "idx": i,
            "open_time": int(df["open_time"].iat[i]),
            "label": label,
            "exit_reason": simple,
            "labeled_pnl": labeled_pnl,
            "fwd_return_pct": fwd_return,
            "long_result": long_result,
            "short_result": short_result,
            "atr_pct": atr_vals[i] / entry * 100.0,
        })
    return pd.DataFrame(rows)


def _shannon_entropy(p: np.ndarray) -> float:
    """Shannon entropy over a discrete distribution (base e)."""
    p = p[p > 0]
    return float(-np.sum(p * np.log(p))) if p.size > 0 else 0.0


def main():
    feat_dir = REPO / "data" / "features"
    klines_dir = REPO / "data"
    print(f"\n=== iter-v1/016 EDA — sample-weighting characterization ===")
    print(f"Repo:        {REPO}")
    print(f"OOS cutoff:  {OOS_CUTOFF_MS} (IS-only filter)")
    print(f"Universe:    {list(V1_BASELINE_UNIVERSE)}")
    print(f"Label config: ATR×{ATR_TP_MULT} TP / ATR×{ATR_SL_MULT} SL / {TIMEOUT_CANDLES}-candle timeout")
    print()

    per_month_rows = []
    weight_profile_rows = []

    for sym in V1_BASELINE_UNIVERSE:
        # Load klines from CSV
        k_csv = klines_dir / sym / "8h.csv"
        if not k_csv.exists():
            print(f"[WARN] missing kline csv for {sym}: {k_csv}")
            continue
        kdf = pd.read_csv(k_csv)
        # Keep IS-only rows
        kdf = kdf[kdf["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        if len(kdf) < 200:
            print(f"[WARN] {sym}: only {len(kdf)} IS rows; skip")
            continue
        # Compute ATR for entry-side
        atr_vals = _compute_atr(
            kdf["high"].to_numpy(dtype=np.float64),
            kdf["low"].to_numpy(dtype=np.float64),
            kdf["close"].to_numpy(dtype=np.float64),
            period=14,
        )

        # Label all IS rows (sample once for analysis; in production we
        # only label entry-signal candles, but here we want the full label-distribution shape)
        labels_df = _label_quick(
            kdf,
            atr_vals,
            tp_mult=ATR_TP_MULT,
            sl_mult=ATR_SL_MULT,
            timeout_candles=TIMEOUT_CANDLES,
            fee_pct=FEE_PCT,
        )
        labels_df["symbol"] = sym
        labels_df["month"] = pd.to_datetime(labels_df["open_time"], unit="ms").dt.strftime("%Y-%m")

        # ---- Baseline weight = 1 + |labeled_pnl| / max * 9 (matches labeling.py:543)
        abs_pnl = labels_df["labeled_pnl"].abs().to_numpy()
        w_baseline = (
            1.0 + abs_pnl / max(abs_pnl.max(), 1e-9) * 9.0 if len(abs_pnl) > 0 else np.array([])
        )
        labels_df["w_baseline"] = w_baseline

        # ---- Option A: 1/realized_vol_30d (30-day rolling stdev of returns)
        ret = kdf["close"].pct_change()
        vol_30d = ret.rolling(window=90, min_periods=20).std()  # 30 days × 3 candles/day = 90
        # Align: vol value at label-time entry is .shift(1) past-only
        vol_at_label = vol_30d.shift(1).reindex(labels_df["idx"]).to_numpy()
        # Avoid division by zero / NaN: replace with median vol
        median_vol = np.nanmedian(vol_at_label)
        vol_at_label = np.where(np.isnan(vol_at_label) | (vol_at_label <= 0), median_vol, vol_at_label)
        w_optA = 1.0 / vol_at_label  # unnormalized
        # Normalize to baseline scale [1, 10]
        w_optA_norm = 1.0 + (w_optA - w_optA.min()) / (w_optA.max() - w_optA.min() + 1e-9) * 9.0

        # ---- Option B: AFML uniqueness (1/avg_overlap_count) — simulate analytically
        # For 21-candle timeout, every consecutive labeled candle's window overlaps
        # 20 of its neighbors. avg_overlap_count ≈ min(timeout, days_with_signal_in_window)
        # Approximation: w_optB = 1/c where c is the count of labels active at each candle
        # — full computation handled by compute_sample_uniqueness in production; here we
        # estimate by counting labels within a 21-candle window.
        idx_arr = labels_df["idx"].to_numpy()
        n_labels = len(idx_arr)
        w_optB = np.ones(n_labels, dtype=np.float64)
        for li in range(n_labels):
            this_idx = idx_arr[li]
            # Window [idx, idx+timeout]; count labels with idx_j in [idx-timeout, idx+timeout]
            # whose window overlaps this one
            lo = np.searchsorted(idx_arr, this_idx - TIMEOUT_CANDLES, side="left")
            hi = np.searchsorted(idx_arr, this_idx + TIMEOUT_CANDLES, side="right")
            n_overlap = max(hi - lo, 1)
            w_optB[li] = 1.0 / n_overlap
        # Normalize to [1, 10]
        w_optB_norm = 1.0 + (w_optB - w_optB.min()) / (w_optB.max() - w_optB.min() + 1e-9) * 9.0

        # ---- Option C: inverse-class-frequency by exit_reason within (symbol, month)
        # Group by (symbol, month), compute exit_reason frequencies, weight = 1/freq
        labels_df["w_optC"] = np.nan
        for month, sub in labels_df.groupby("month"):
            freqs = sub["exit_reason"].value_counts(normalize=True).to_dict()
            w_per_row = sub["exit_reason"].map(lambda r: 1.0 / max(freqs[r], 1e-6))
            labels_df.loc[sub.index, "w_optC"] = w_per_row.values
        # Normalize C globally for cross-month comparability (so we don't downweight rare-exit months disproportionately)
        w_optC_arr = labels_df["w_optC"].to_numpy()
        w_optC_norm = 1.0 + (w_optC_arr - w_optC_arr.min()) / (w_optC_arr.max() - w_optC_arr.min() + 1e-9) * 9.0
        labels_df["w_optC_norm"] = w_optC_norm
        labels_df["w_optA_norm"] = w_optA_norm
        labels_df["w_optB_norm"] = w_optB_norm

        # ---- Per-month summary
        for month, sub in labels_df.groupby("month"):
            reason_counts = sub["exit_reason"].value_counts(normalize=True)
            tp_share = float(reason_counts.get("tp_hit", 0.0))
            timeout_share = float(reason_counts.get("timeout", 0.0))
            sl_opp_share = float(reason_counts.get("sl_hit_opp", 0.0))
            ent = _shannon_entropy(reason_counts.to_numpy())
            label_dist = sub["label"].value_counts(normalize=True)
            long_share = float(label_dist.get(1, 0.0))
            short_share = float(label_dist.get(-1, 0.0))
            per_month_rows.append({
                "symbol": sym,
                "month": month,
                "n_labels": int(len(sub)),
                "tp_hit_share": tp_share,
                "timeout_share": timeout_share,
                "sl_opp_share": sl_opp_share,
                "long_share": long_share,
                "short_share": short_share,
                "exit_entropy": ent,
                # Weight summaries per-month
                "w_baseline_p50": float(np.median(sub["w_baseline"])),
                "w_baseline_p95": float(np.quantile(sub["w_baseline"], 0.95)),
                "w_baseline_max": float(sub["w_baseline"].max()),
                "w_optC_p50": float(np.median(sub["w_optC_norm"])),
                "w_optC_p95": float(np.quantile(sub["w_optC_norm"], 0.95)),
            })

        # ---- Per-symbol aggregate weight profile (quantiles)
        weight_profile_rows.append({
            "symbol": sym,
            "n_labels": int(len(labels_df)),
            "w_baseline_p10": float(np.quantile(w_baseline, 0.10)),
            "w_baseline_p50": float(np.quantile(w_baseline, 0.50)),
            "w_baseline_p90": float(np.quantile(w_baseline, 0.90)),
            "w_baseline_p99": float(np.quantile(w_baseline, 0.99)),
            "w_baseline_max": float(w_baseline.max()),
            "w_optA_p50": float(np.quantile(w_optA_norm, 0.50)),
            "w_optA_p90": float(np.quantile(w_optA_norm, 0.90)),
            "w_optB_p50": float(np.quantile(w_optB_norm, 0.50)),
            "w_optB_p90": float(np.quantile(w_optB_norm, 0.90)),
            "w_optC_p50": float(np.quantile(w_optC_norm, 0.50)),
            "w_optC_p90": float(np.quantile(w_optC_norm, 0.90)),
            "tp_share": float((labels_df["exit_reason"] == "tp_hit").mean()),
            "timeout_share": float((labels_df["exit_reason"] == "timeout").mean()),
            "sl_opp_share": float((labels_df["exit_reason"] == "sl_hit_opp").mean()),
        })

    # ---- Write outputs
    per_month_df = pd.DataFrame(per_month_rows)
    weight_profile_df = pd.DataFrame(weight_profile_rows)

    per_month_df.to_csv(OUTPUT_DIR / "exit_reason_distribution.csv", index=False)
    weight_profile_df.to_csv(OUTPUT_DIR / "weight_profile_summary.csv", index=False)

    # ---- Cross-symbol weighting-scheme comparison
    comp_rows = []
    for sym in V1_BASELINE_UNIVERSE:
        rows = weight_profile_df[weight_profile_df["symbol"] == sym]
        if rows.empty:
            continue
        row = rows.iloc[0]
        comp_rows.append({
            "symbol": sym,
            "baseline_concentration_p90_p50": float(row["w_baseline_p90"] / max(row["w_baseline_p50"], 1e-6)),
            "optA_concentration_p90_p50": float(row["w_optA_p90"] / max(row["w_optA_p50"], 1e-6)),
            "optB_concentration_p90_p50": float(row["w_optB_p90"] / max(row["w_optB_p50"], 1e-6)),
            "optC_concentration_p90_p50": float(row["w_optC_p90"] / max(row["w_optC_p50"], 1e-6)),
            "tp_hit_share": float(row["tp_share"]),
            "timeout_share": float(row["timeout_share"]),
        })
    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(OUTPUT_DIR / "weighting_scheme_comparison.csv", index=False)

    # ---- Shannon-entropy diversity proxy (per symbol-month)
    per_month_df["n_eff_proxy_label_diversity"] = per_month_df["exit_entropy"] / np.log(3)  # normalized
    per_month_df.to_csv(OUTPUT_DIR / "n_eff_label_diversity_proxy.csv", index=False)

    # ---- Print summaries
    print("\n## TABLE 1 — Baseline weight quantiles (per symbol, IS-only)")
    print(weight_profile_df[[
        "symbol", "n_labels",
        "w_baseline_p10", "w_baseline_p50", "w_baseline_p90", "w_baseline_p99",
        "tp_share", "timeout_share", "sl_opp_share",
    ]].to_string(index=False))

    print("\n## TABLE 2 — Weighting scheme concentration ratio (p90/p50; lower = more uniform)")
    print(comp_df.to_string(index=False))

    print("\n## TABLE 3 — Per-symbol-month exit-reason distribution summary")
    sym_summary = per_month_df.groupby("symbol").agg({
        "n_labels": "sum",
        "tp_hit_share": ["mean", "min", "max"],
        "timeout_share": ["mean", "min", "max"],
        "exit_entropy": ["mean", "min", "max"],
    }).round(3)
    print(sym_summary)

    print("\n## TABLE 4 — Months with n_eff-COLLAPSE risk (timeout_share > 0.6)")
    risk_months = per_month_df[per_month_df["timeout_share"] > 0.6]
    if len(risk_months) > 0:
        print(risk_months[["symbol", "month", "timeout_share", "exit_entropy", "n_labels"]].to_string(index=False))
        print(f"\nTOTAL: {len(risk_months)} (symbol, month) cells at n_eff-collapse risk (timeout > 0.6)")
        print(f"Universe-total months: {len(per_month_df)}")
        print(f"Risk-cell fraction: {len(risk_months)/len(per_month_df):.1%}")
    else:
        print("None — all (sym, month) cells have timeout_share ≤ 0.6 (healthy mix)")

    print(f"\n[OK] EDA artifacts written to {OUTPUT_DIR}/")
    print("Files:")
    for f in ["weight_profile_summary.csv", "exit_reason_distribution.csv",
              "weighting_scheme_comparison.csv", "n_eff_label_diversity_proxy.csv"]:
        path = OUTPUT_DIR / f
        if path.exists():
            print(f"  {f}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
