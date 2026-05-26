"""iter-v1/016 EDA — per-symbol weight concentration in baseline `abs(labeled_pnl)` scheme.

Hypothesis (sharpened post Table-1 finding):
--------------------------------------------
The /015 timeout-fallback problem DOES NOT exist at v1 baseline ATR labels:
- TP-hit share: ~51% (healthy mix)
- Timeout share: ~10-13% (well below /015's >85%)
- ZERO (symbol, month) cells with timeout > 0.6

This refutes Option C (inverse-class-frequency on exit_reason) as the right
intervention. The actual mechanism at the v1 baseline is **per-symbol weight
imbalance via `abs(labeled_pnl)`**:

- LTC p90 = 4.47, p99 = 6.26 → biggest outliers
- DOT p90 = 4.28, p99 = 6.12 → second
- LINK p90 = 2.97, p99 = 4.04 → smallest

LTC is the WORST OOS contributor (−47.25%) and DOT a weak one. If the baseline's
loss surface is dominated by LTC/DOT high-PnL outliers, Optuna selects
hyperparameters that overfit to those noise sources.

This script quantifies:
1. **Per-symbol total-weight share** under each scheme (baseline vs uniformity vs uniqueness)
2. **High-weight tail effect** — fraction of total weight concentrated in top 5% of samples
3. **Per-symbol training-row count vs total-weight share** — ideally equal; baseline pumps LTC/DOT
4. **Predict Optuna loss-surface diversification** — measure n_eff proxy as effective sample size
   `n_eff_kish = (Σw)² / Σw²` per (symbol, training-month). Higher n_eff_kish = more uniform =
   better Optuna search.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402

OUTPUT_DIR = Path(__file__).parent
ATR_TP_MULT = 2.9
ATR_SL_MULT = 1.5
TIMEOUT_CANDLES = 21
FEE_PCT = 0.1


def _compute_atr(high, low, close, period=14):
    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1)),
        ),
    )
    tr[0] = high[0] - low[0]
    atr = np.zeros_like(tr)
    atr[:period] = np.nan
    atr[period - 1] = tr[:period].mean()
    for i in range(period, len(tr)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _label_pnl_distribution(df: pd.DataFrame, atr_vals: np.ndarray) -> pd.DataFrame:
    """Quick labeler — returns DataFrame with labeled_pnl, fwd_return, atr_pct per row."""
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close = df["close"].to_numpy(dtype=np.float64)
    n = len(df)
    out = []
    for i in range(n - 1):
        if np.isnan(atr_vals[i]) or atr_vals[i] <= 0:
            continue
        entry = close[i]
        tp_dist = atr_vals[i] * ATR_TP_MULT
        sl_dist = atr_vals[i] * ATR_SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist

        long_result, short_result = 0, 0
        long_step, short_step = -1, -1
        last_close = entry
        end_j = min(i + 1 + TIMEOUT_CANDLES, n)
        for j in range(i + 1, end_j):
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
        tp_pnl = tp_dist / entry * 100.0
        sl_pnl = sl_dist / entry * 100.0

        def _pnl(result, sign):
            if result == 1:
                return tp_pnl
            if result == -1:
                return -sl_pnl
            return sign * fwd_return

        long_pnl = _pnl(long_result, 1.0) - FEE_PCT
        short_pnl = _pnl(short_result, -1.0) - FEE_PCT

        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            label, labeled_pnl = 1, long_pnl
        elif short_tp_hit and not long_tp_hit:
            label, labeled_pnl = -1, short_pnl
        elif long_tp_hit and short_tp_hit:
            if long_step <= short_step:
                label, labeled_pnl = 1, long_pnl
            else:
                label, labeled_pnl = -1, short_pnl
        else:
            label = 1 if fwd_return >= 0 else -1
            labeled_pnl = long_pnl if label == 1 else short_pnl

        out.append({
            "idx": i,
            "open_time": int(df["open_time"].iat[i]),
            "label": label,
            "labeled_pnl": labeled_pnl,
            "abs_pnl": abs(labeled_pnl),
            "fwd_return_pct": fwd_return,
            "atr_pct": atr_vals[i] / entry * 100.0,
        })
    return pd.DataFrame(out)


def _kish_n_eff(weights: np.ndarray) -> float:
    """Kish's effective sample size = (Σw)² / Σw². For uniform weights, n_eff = n."""
    s = weights.sum()
    s2 = (weights ** 2).sum()
    if s2 == 0:
        return 0.0
    return float((s ** 2) / s2)


def main():
    print("\n=== iter-v1/016 EDA — per-symbol weight concentration ===")

    all_labels = []
    for sym in V1_BASELINE_UNIVERSE:
        k_csv = REPO / "data" / sym / "8h.csv"
        if not k_csv.exists():
            print(f"[WARN] missing {k_csv}")
            continue
        kdf = pd.read_csv(k_csv)
        kdf = kdf[kdf["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        atr_vals = _compute_atr(
            kdf["high"].to_numpy(dtype=np.float64),
            kdf["low"].to_numpy(dtype=np.float64),
            kdf["close"].to_numpy(dtype=np.float64),
        )
        df = _label_pnl_distribution(kdf, atr_vals)
        df["symbol"] = sym
        df["month"] = pd.to_datetime(df["open_time"], unit="ms").dt.strftime("%Y-%m")
        all_labels.append(df)
    labels = pd.concat(all_labels, ignore_index=True)
    print(f"Labels collected: {len(labels)} rows across {labels['symbol'].nunique()} symbols")

    # Pool-A (BTC+ETH) is one model. Compute training cohort per model:
    # Model A = BTC + ETH; Model C = LINK; Model D = LTC; Model E = DOT
    model_map = {
        "BTCUSDT": "A", "ETHUSDT": "A",
        "LINKUSDT": "C", "LTCUSDT": "D", "DOTUSDT": "E",
    }
    labels["model"] = labels["symbol"].map(model_map)

    # ---- Compute baseline weights = 1 + abs_pnl/max * 9 (matches labeling.py:543)
    # Run PER (model, month) to mirror training-month behavior
    rows_kish = []
    for (model, month), sub in labels.groupby(["model", "month"]):
        abs_pnl = sub["abs_pnl"].to_numpy()
        if len(abs_pnl) == 0 or abs_pnl.max() == 0:
            continue
        w_baseline = 1.0 + abs_pnl / abs_pnl.max() * 9.0
        # Uniform (all 1s) — what AFML uniqueness reduces to at constant overlap
        w_uniform = np.ones_like(abs_pnl)
        # Option B sketch — uniqueness-weighted (= constant 1/21 for dense labels, NORMALIZED to 1/avg)
        # Per AFML, uniqueness ≈ 1/overlap_count; with dense daily-labels in 21-candle horizon,
        # uniqueness ≈ 1/21 for all. After normalization, effectively uniform.
        # So in practice Option B uniformizes weights.
        w_optB_norm = np.ones_like(abs_pnl)  # post-normalization equiv

        # Per-symbol weight shares within this (model, month)
        for sym in sub["symbol"].unique():
            mask = sub["symbol"] == sym
            sub_sym = sub[mask]
            sub_abs = sub_sym["abs_pnl"].to_numpy()
            sub_w_baseline = 1.0 + sub_abs / max(abs_pnl.max(), 1e-9) * 9.0  # normalized to model-month max
            total_baseline_w = w_baseline.sum()
            total_uniform_w = w_uniform.sum()
            share_baseline = float(sub_w_baseline.sum() / total_baseline_w) if total_baseline_w > 0 else 0.0
            share_uniform = float(len(sub_sym) / max(len(sub), 1))
            rows_kish.append({
                "model": model,
                "month": month,
                "symbol": sym,
                "n": int(len(sub_sym)),
                "share_baseline_weight": share_baseline,
                "share_uniform_weight": share_uniform,
                "delta_baseline_vs_uniform": share_baseline - share_uniform,
            })

    kish_df = pd.DataFrame(rows_kish)
    kish_df.to_csv(OUTPUT_DIR / "per_symbol_weight_share.csv", index=False)

    print("\n## TABLE 1 — Per-symbol weight-share difference (baseline vs uniform), per model")
    print("Δ > 0 = baseline UPWEIGHTS this symbol; Δ < 0 = baseline DOWNWEIGHTS")
    by_model_sym = kish_df.groupby(["model", "symbol"]).agg({
        "share_baseline_weight": "mean",
        "share_uniform_weight": "mean",
        "delta_baseline_vs_uniform": ["mean", "std", "min", "max"],
        "n": "sum",
    }).round(4)
    print(by_model_sym)

    # Specifically for Model A (BTC+ETH pooled), how does baseline split between BTC vs ETH?
    print("\n## TABLE 2 — Model A (BTC+ETH pooled) weight-share split")
    model_a = kish_df[kish_df["model"] == "A"]
    model_a_summary = model_a.groupby("symbol")[["share_baseline_weight", "share_uniform_weight"]].agg(["mean", "std"]).round(4)
    print(model_a_summary)

    # ---- Kish n_eff per (model, month) under baseline vs uniform
    rows_neff = []
    for (model, month), sub in labels.groupby(["model", "month"]):
        abs_pnl = sub["abs_pnl"].to_numpy()
        if len(abs_pnl) == 0 or abs_pnl.max() == 0:
            continue
        w_baseline = 1.0 + abs_pnl / abs_pnl.max() * 9.0
        n_actual = len(sub)
        n_eff_baseline = _kish_n_eff(w_baseline)
        n_eff_uniform = n_actual  # = (n*1)² / (n*1²) = n
        rows_neff.append({
            "model": model,
            "month": month,
            "n_actual": n_actual,
            "n_eff_kish_baseline": n_eff_baseline,
            "n_eff_kish_uniform": n_eff_uniform,
            "n_eff_ratio_baseline_to_uniform": n_eff_baseline / max(n_eff_uniform, 1),
        })
    neff_df = pd.DataFrame(rows_neff)
    neff_df.to_csv(OUTPUT_DIR / "kish_n_eff_per_cell.csv", index=False)

    print("\n## TABLE 3 — Kish n_eff per (model, month) — baseline vs uniform")
    print("n_eff_ratio = baseline / uniform; closer to 1.0 = more uniform = better")
    print(neff_df.groupby("model").agg({
        "n_actual": ["mean", "min", "max"],
        "n_eff_kish_baseline": ["mean", "min", "max"],
        "n_eff_ratio_baseline_to_uniform": ["mean", "min", "max", "std"],
    }).round(3))

    # Identify the WORST cells (lowest Kish ratio = most concentrated)
    worst = neff_df.sort_values("n_eff_ratio_baseline_to_uniform").head(20)
    print("\n## TABLE 4 — 20 WORST (model, month) cells by Kish n_eff ratio")
    print("(Lowest ratio = most weight concentrated on outliers)")
    print(worst[["model", "month", "n_actual", "n_eff_kish_baseline", "n_eff_ratio_baseline_to_uniform"]].to_string(index=False))

    # ---- Per-symbol abs_pnl percentiles — to show LTC/DOT outliers
    print("\n## TABLE 5 — Per-symbol abs(labeled_pnl) distribution (IS-only, %)")
    pnl_dist = labels.groupby("symbol")["abs_pnl"].describe(percentiles=[0.5, 0.9, 0.95, 0.99]).round(2)
    print(pnl_dist)

    # ---- Summary metric: what's the "fairness" of Model A's BTC vs ETH split under each scheme?
    print("\n## TABLE 6 — Predicted IS PnL contribution per scheme")
    print("Lower-vol symbols (BTC/ETH) get larger shares under UNIFORM; higher-vol (LTC/DOT) lose.")
    a_share_baseline = model_a.groupby("symbol")["share_baseline_weight"].mean()
    a_share_uniform = model_a.groupby("symbol")["share_uniform_weight"].mean()
    print(f"  Model A BTC baseline share: {a_share_baseline.get('BTCUSDT', 0):.3f} | uniform: {a_share_uniform.get('BTCUSDT', 0):.3f}")
    print(f"  Model A ETH baseline share: {a_share_baseline.get('ETHUSDT', 0):.3f} | uniform: {a_share_uniform.get('ETHUSDT', 0):.3f}")
    print(f"  Model A BTC under-weighting (baseline < uniform): {(a_share_uniform.get('BTCUSDT', 0) - a_share_baseline.get('BTCUSDT', 0)):+.4f}")

    print(f"\n[OK] Artifacts written to {OUTPUT_DIR}/")
    for f in ["per_symbol_weight_share.csv", "kish_n_eff_per_cell.csv"]:
        print(f"  {f}")


if __name__ == "__main__":
    main()
