"""
iter-v1/028 EDA — LTC OOS catastrophe re-analysis (TRADE-LEVEL ORACLE).

Re-analyzes the baseline LTC OOS catastrophe (-47.25% net PnL, OOS Sharpe per-trade -0.27)
to identify the DOMINANT loss channel and select a mechanism that is BASIN-RELOCATION-ROBUST
(vs /022's gate which dissolved when the basin relocated under single-cohort retraining).

INPUTS (read-only):
- reports-v1/iteration_v1-baseline/{in_sample,out_of_sample}/trades.csv
- reports-v1/iteration_v1-baseline/{in_sample,out_of_sample}/monthly_pnl.csv
- reports-v1/iteration_v1-022/{in_sample,out_of_sample}/trades.csv (for basin-relocation diagnostic)
- data/LTCUSDT/8h.csv (price data, for context regime classification)

OUTPUTS:
- ltc_baseline_trade_attribution.csv     — per-trade attribution at IS+OOS
- ltc_oos_loss_channels.csv              — dominant loss channels ranked
- ltc_022_basin_relocation_diagnostic.csv — basin shift in /022 retrained roster
- ltc_mechanism_robustness_predictions.csv — predicted effect of 6 candidate mechanisms
- ltc_oos_confidence_distribution.csv    — confidence x outcome distribution
- ltc_monthly_loss_clustering.csv        — month-clustering signature

Key questions answered:
1. Which loss channel dominates LTC OOS? (direction, regime, vol, confidence, weight_factor)
2. Are baseline LTC losses BASIN-INVARIANT (would survive retraining) or BASIN-CONTINGENT?
3. Which mechanism CANDIDATE is most basin-relocation-robust? (key /022 lesson)
4. Predicted IS+OOS effect on baseline 34-trade roster for each candidate.

USAGE:
    cd /home/roberto/crypto-trade/.worktrees/quant-research
    uv run python analysis/iteration_v1-028/ltc_oos_catastrophe_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASELINE_REPORT = ROOT / "reports-v1" / "iteration_v1-baseline"
ITER022_REPORT = ROOT / "reports-v1" / "iteration_v1-022"
OUT_DIR = ROOT / "analysis" / "iteration_v1-028"
OUT_DIR.mkdir(exist_ok=True)


def _read_trades(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p)
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time_dt"] = pd.to_datetime(df["close_time"], unit="ms")
    df["month"] = df["open_time_dt"].dt.strftime("%Y-%m")
    df["holding_h"] = (df["close_time_dt"] - df["open_time_dt"]).dt.total_seconds() / 3600.0
    return df


# ============================================================
# 1. Read baseline LTC trades
# ============================================================
print("[1/7] Reading baseline LTC trades...")
is_all = _read_trades(BASELINE_REPORT / "in_sample" / "trades.csv")
oos_all = _read_trades(BASELINE_REPORT / "out_of_sample" / "trades.csv")

ltc_is = is_all[is_all["symbol"] == "LTCUSDT"].copy().reset_index(drop=True)
ltc_oos = oos_all[oos_all["symbol"] == "LTCUSDT"].copy().reset_index(drop=True)

print(f"   LTC IS  trades = {len(ltc_is):3d}  net PnL% = {ltc_is['net_pnl_pct'].sum():+8.2f}")
print(f"   LTC OOS trades = {len(ltc_oos):3d}  net PnL% = {ltc_oos['net_pnl_pct'].sum():+8.2f}")
print()


# ============================================================
# 2. Direction-split attribution (longs vs shorts) at IS+OOS
# ============================================================
print("[2/7] Direction-split attribution (IS+OOS)...")
attribution_rows = []
for label, df in [("IS", ltc_is), ("OOS", ltc_oos)]:
    for d_label, d_val in [("long", 1), ("short", -1)]:
        sub = df[df["direction"] == d_val]
        if len(sub) == 0:
            continue
        sharpe = sub["net_pnl_pct"].mean() / sub["net_pnl_pct"].std() if sub["net_pnl_pct"].std() > 0 else 0.0
        attribution_rows.append({
            "sample": label,
            "direction": d_label,
            "n_trades": len(sub),
            "n_wins": int((sub["net_pnl_pct"] > 0).sum()),
            "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
            "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
            "weighted_pnl_pct": round(sub["weighted_pnl"].sum(), 4),
            "avg_pnl_pct": round(sub["net_pnl_pct"].mean(), 4),
            "median_pnl_pct": round(sub["net_pnl_pct"].median(), 4),
            "std_pnl_pct": round(sub["net_pnl_pct"].std(), 4),
            "per_trade_sharpe": round(sharpe, 4),
            "share_of_pnl_pct": round(100 * sub["net_pnl_pct"].sum() / df["net_pnl_pct"].sum(), 2)
                if df["net_pnl_pct"].sum() != 0 else 0.0,
        })

attribution_df = pd.DataFrame(attribution_rows)
attribution_df.to_csv(OUT_DIR / "ltc_baseline_trade_attribution.csv", index=False)
print(attribution_df.to_string(index=False))
print()


# ============================================================
# 3. OOS loss channel ranking (which factor concentrates losses?)
# ============================================================
print("[3/7] OOS loss channel ranking...")
loss_channels = []

# Channel A: direction
for d_label, d_val in [("long", 1), ("short", -1)]:
    sub = ltc_oos[ltc_oos["direction"] == d_val]
    if len(sub) > 0:
        losses = sub[sub["net_pnl_pct"] < 0]
        loss_channels.append({
            "channel": f"direction={d_label}",
            "trade_share_pct": round(100 * len(sub) / len(ltc_oos), 2),
            "loss_count": len(losses),
            "loss_share_pct": round(100 * len(losses) / max(1, len(ltc_oos[ltc_oos["net_pnl_pct"] < 0])), 2),
            "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
            "share_of_total_loss_pct": round(100 * sub["net_pnl_pct"].sum() / ltc_oos["net_pnl_pct"].sum(), 2)
                if ltc_oos["net_pnl_pct"].sum() != 0 else 0.0,
            "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
        })

# Channel B: exit_reason
for reason in ltc_oos["exit_reason"].unique():
    sub = ltc_oos[ltc_oos["exit_reason"] == reason]
    losses = sub[sub["net_pnl_pct"] < 0]
    loss_channels.append({
        "channel": f"exit_reason={reason}",
        "trade_share_pct": round(100 * len(sub) / len(ltc_oos), 2),
        "loss_count": len(losses),
        "loss_share_pct": round(100 * len(losses) / max(1, len(ltc_oos[ltc_oos["net_pnl_pct"] < 0])), 2),
        "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
        "share_of_total_loss_pct": round(100 * sub["net_pnl_pct"].sum() / ltc_oos["net_pnl_pct"].sum(), 2)
            if ltc_oos["net_pnl_pct"].sum() != 0 else 0.0,
        "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
    })

# Channel C: confidence buckets
for lo, hi in [(0.60, 0.75), (0.75, 0.85), (0.85, 1.00)]:
    sub = ltc_oos[(ltc_oos["confidence"] >= lo) & (ltc_oos["confidence"] < hi)]
    if len(sub) > 0:
        loss_channels.append({
            "channel": f"conf=[{lo:.2f},{hi:.2f})",
            "trade_share_pct": round(100 * len(sub) / len(ltc_oos), 2),
            "loss_count": int((sub["net_pnl_pct"] < 0).sum()),
            "loss_share_pct": round(100 * (sub["net_pnl_pct"] < 0).sum() / max(1, (ltc_oos["net_pnl_pct"] < 0).sum()), 2),
            "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
            "share_of_total_loss_pct": round(100 * sub["net_pnl_pct"].sum() / ltc_oos["net_pnl_pct"].sum(), 2)
                if ltc_oos["net_pnl_pct"].sum() != 0 else 0.0,
            "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
        })

# Channel D: weight_factor buckets (does the existing R-layer ever fire on LTC?)
wf_bins = [(0.99, 1.01), (0.30, 0.40), (0.10, 0.30)]
for lo, hi in wf_bins:
    sub = ltc_oos[(ltc_oos["weight_factor"] >= lo) & (ltc_oos["weight_factor"] < hi)]
    if len(sub) > 0:
        loss_channels.append({
            "channel": f"weight_factor=[{lo:.2f},{hi:.2f})",
            "trade_share_pct": round(100 * len(sub) / len(ltc_oos), 2),
            "loss_count": int((sub["net_pnl_pct"] < 0).sum()),
            "loss_share_pct": round(100 * (sub["net_pnl_pct"] < 0).sum() / max(1, (ltc_oos["net_pnl_pct"] < 0).sum()), 2),
            "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
            "share_of_total_loss_pct": round(100 * sub["net_pnl_pct"].sum() / ltc_oos["net_pnl_pct"].sum(), 2)
                if ltc_oos["net_pnl_pct"].sum() != 0 else 0.0,
            "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
        })

# Channel E: pnl_magnitude buckets (loss-tail concentration)
ltc_oos["pnl_bucket"] = pd.cut(
    ltc_oos["net_pnl_pct"],
    bins=[-100, -7, -4, 0, 4, 100],
    labels=["catastrophic(<-7)", "moderate_loss[-7,-4)", "small_loss[-4,0)", "small_win[0,4)", "big_win(>=4)"],
)
for bucket_label, group in ltc_oos.groupby("pnl_bucket"):
    if len(group) > 0:
        loss_channels.append({
            "channel": f"pnl_bucket={bucket_label}",
            "trade_share_pct": round(100 * len(group) / len(ltc_oos), 2),
            "loss_count": int((group["net_pnl_pct"] < 0).sum()),
            "loss_share_pct": round(100 * (group["net_pnl_pct"] < 0).sum() / max(1, (ltc_oos["net_pnl_pct"] < 0).sum()), 2),
            "net_pnl_pct": round(group["net_pnl_pct"].sum(), 4),
            "share_of_total_loss_pct": round(100 * group["net_pnl_pct"].sum() / ltc_oos["net_pnl_pct"].sum(), 2)
                if ltc_oos["net_pnl_pct"].sum() != 0 else 0.0,
            "win_rate_pct": round(100 * (group["net_pnl_pct"] > 0).mean(), 2),
        })

loss_channels_df = pd.DataFrame(loss_channels).sort_values("net_pnl_pct", ascending=True)
loss_channels_df.to_csv(OUT_DIR / "ltc_oos_loss_channels.csv", index=False)
print(loss_channels_df.to_string(index=False))
print()


# ============================================================
# 4. Monthly loss clustering (when did losses concentrate?)
# ============================================================
print("[4/7] Monthly loss clustering...")
monthly_rows = []
for month, group in ltc_oos.groupby("month"):
    total_pnl = group["net_pnl_pct"].sum()
    monthly_rows.append({
        "month": month,
        "n_trades": len(group),
        "net_pnl_pct": round(total_pnl, 4),
        "n_longs": int((group["direction"] == 1).sum()),
        "n_shorts": int((group["direction"] == -1).sum()),
        "long_pnl_pct": round(group[group["direction"] == 1]["net_pnl_pct"].sum(), 4),
        "short_pnl_pct": round(group[group["direction"] == -1]["net_pnl_pct"].sum(), 4),
        "win_rate_pct": round(100 * (group["net_pnl_pct"] > 0).mean(), 2),
        "max_drawdown_in_month": round(group["net_pnl_pct"].min(), 4),
    })
monthly_df = pd.DataFrame(monthly_rows).sort_values("net_pnl_pct", ascending=True)
monthly_df.to_csv(OUT_DIR / "ltc_monthly_loss_clustering.csv", index=False)
print(monthly_df.to_string(index=False))
print()


# ============================================================
# 5. Confidence x outcome distribution (calibration check)
# ============================================================
print("[5/7] Confidence x outcome distribution...")
conf_rows = []
for label, df in [("IS", ltc_is), ("OOS", ltc_oos)]:
    for lo, hi in [(0.55, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 1.01)]:
        sub = df[(df["confidence"] >= lo) & (df["confidence"] < hi)]
        if len(sub) > 0:
            conf_rows.append({
                "sample": label,
                "conf_bucket": f"[{lo:.2f},{hi:.2f})",
                "n_trades": len(sub),
                "win_rate_pct": round(100 * (sub["net_pnl_pct"] > 0).mean(), 2),
                "net_pnl_pct": round(sub["net_pnl_pct"].sum(), 4),
                "avg_pnl_pct": round(sub["net_pnl_pct"].mean(), 4),
            })
conf_df = pd.DataFrame(conf_rows)
conf_df.to_csv(OUT_DIR / "ltc_oos_confidence_distribution.csv", index=False)
print(conf_df.to_string(index=False))
print()


# ============================================================
# 6. /022 basin-relocation diagnostic
# ============================================================
print("[6/7] /022 basin-relocation diagnostic (Jaccard against baseline LTC roster)...")
iter022_is = _read_trades(ITER022_REPORT / "in_sample" / "trades.csv")
iter022_oos = _read_trades(ITER022_REPORT / "out_of_sample" / "trades.csv")

# Both /022 datasets are already LTC-only by dispatch
basin_rows = []
for sample_label, base, iter022 in [
    ("IS", ltc_is, iter022_is),
    ("OOS", ltc_oos, iter022_oos),
]:
    base_keys = set(base["open_time"].tolist())
    iter022_keys = set(iter022["open_time"].tolist())
    overlap = base_keys & iter022_keys
    union = base_keys | iter022_keys
    base_only = base_keys - iter022_keys
    iter022_only = iter022_keys - base_keys
    base_only_df = base[base["open_time"].isin(base_only)]
    iter022_only_df = iter022[iter022["open_time"].isin(iter022_only)]
    overlap_df_base = base[base["open_time"].isin(overlap)]
    basin_rows.append({
        "sample": sample_label,
        "baseline_trades": len(base),
        "iter022_trades": len(iter022),
        "overlap_trades": len(overlap),
        "jaccard": round(len(overlap) / max(1, len(union)), 4),
        "baseline_only_trades": len(base_only_df),
        "baseline_only_net_pnl_pct": round(base_only_df["net_pnl_pct"].sum(), 4),
        "iter022_only_trades": len(iter022_only_df),
        "iter022_only_net_pnl_pct": round(iter022_only_df["net_pnl_pct"].sum(), 4),
        "overlap_baseline_net_pnl_pct": round(overlap_df_base["net_pnl_pct"].sum(), 4),
    })
basin_df = pd.DataFrame(basin_rows)
basin_df.to_csv(OUT_DIR / "ltc_022_basin_relocation_diagnostic.csv", index=False)
print(basin_df.to_string(index=False))
print()


# ============================================================
# 7. Mechanism robustness predictions
# ============================================================
print("[7/7] Mechanism robustness predictions on baseline 34-trade OOS roster...")

# Mechanism candidates and their effect on the BASELINE roster
mechanism_rows = []

# A: R5 vol-target ceiling (proportional scaling at high vol)
# /010 attempted; reconsider with LTC-only training
# Approx: scale weight by 0.5 if natr_p50 > LTC threshold. Need LTC price stdev as proxy.
# Without feature parquet access, simulate: take trades whose pnl magnitude > 5% (high-vol proxy)
# These are larger losses; reducing weight reduces them BUT also reduces wins.
proxy_high_vol = ltc_oos[ltc_oos["net_pnl_pct"].abs() > 5.0]
if len(proxy_high_vol) > 0:
    counterfactual_pnl_A = (ltc_oos["net_pnl_pct"] * np.where(ltc_oos["net_pnl_pct"].abs() > 5.0, 0.5, 1.0)).sum()
    n_affected_A = len(proxy_high_vol)
else:
    counterfactual_pnl_A = ltc_oos["net_pnl_pct"].sum()
    n_affected_A = 0

# B: Feature subset (drop volume features, train only on price action)
# Untestable without rerun; flag as "requires backtest"
counterfactual_pnl_B = None

# C: Meta-labeling (M2 binary acts on M1 direction; only confident trades fire)
# Approx: keep only confidence > 0.85
mask_C = ltc_oos["confidence"] > 0.85
counterfactual_pnl_C = ltc_oos[mask_C]["net_pnl_pct"].sum()
n_kept_C = mask_C.sum()
n_dropped_C = (~mask_C).sum()

# D: Sample weighting (inverse-concurrency; AFML Ch.4)
# Untestable without rerun; flag as "requires backtest"
counterfactual_pnl_D = None

# E: ATR threshold tuning per-cohort (tighter SL or wider TP for LTC)
# Approx: assume tighter SL caps losses at -3% (vs current -5/-7%)
clipped_pnl = ltc_oos["net_pnl_pct"].clip(lower=-3.0)
counterfactual_pnl_E_tighter_sl = clipped_pnl.sum()
# Wider TP: assume timeout wins extend by 30%
mask_tw = (ltc_oos["exit_reason"] == "timeout") & (ltc_oos["net_pnl_pct"] > 0)
adjusted_pnl_E_wider_tp = ltc_oos["net_pnl_pct"].copy()
adjusted_pnl_E_wider_tp.loc[mask_tw] = adjusted_pnl_E_wider_tp.loc[mask_tw] * 1.3
counterfactual_pnl_E_wider_tp = adjusted_pnl_E_wider_tp.sum()

# F: Tighter BTC regime gate (|BTC ret_42| > 4%, long-only-mode for strict bear cut)
# /022's gate was |BTC| > 4% (already tight); F requires a DIFFERENT regime feature
# Use proxy: filter trades where MONTH had cumulative LTC drawdown > -8% in prior 30 days
# Approximation: drop trades opened in months where prior month was net negative
ltc_oos_sorted = ltc_oos.sort_values("open_time").reset_index(drop=True)
ltc_oos_sorted["month_pnl"] = ltc_oos_sorted.groupby("month")["net_pnl_pct"].transform("sum")
# trades opened after a month with > -10% loss are dropped
month_pnl_lookup = ltc_oos_sorted.groupby("month")["net_pnl_pct"].sum().to_dict()
def prior_month_pnl(month_str):
    try:
        y, m = month_str.split("-")
        y, m = int(y), int(m)
        if m == 1:
            prev = f"{y-1}-12"
        else:
            prev = f"{y}-{m-1:02d}"
        return month_pnl_lookup.get(prev, 0.0)
    except Exception:
        return 0.0
ltc_oos_sorted["prior_month_pnl"] = ltc_oos_sorted["month"].apply(prior_month_pnl)
mask_F = ltc_oos_sorted["prior_month_pnl"] > -10.0
counterfactual_pnl_F = ltc_oos_sorted[mask_F]["net_pnl_pct"].sum()
n_kept_F = mask_F.sum()
n_dropped_F = (~mask_F).sum()

# Build summary
mechanism_rows = [
    {
        "candidate": "A_R5_vol_ceiling",
        "description": "scale weight=0.5 for high-vol trades (|pnl|>5%)",
        "basin_relocation_robust": "PARTIAL (proxy via |pnl|; real impl uses NATR ex-ante)",
        "n_baseline_trades_kept": int(len(ltc_oos)),
        "n_baseline_trades_scaled": int(n_affected_A),
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": round(counterfactual_pnl_A, 4),
        "delta_pnl_pct": round(counterfactual_pnl_A - ltc_oos["net_pnl_pct"].sum(), 4),
        "basin_invariance_score": "MEDIUM — scaling acts on every roster; mechanism doesn't dissolve under retraining",
        "requires_full_backtest": "YES — proxy only descriptive",
    },
    {
        "candidate": "B_feature_subset",
        "description": "drop volume features OR keep only price-action features for LTC training",
        "basin_relocation_robust": "HIGH — fundamentally changes the substrate; new basin is the goal",
        "n_baseline_trades_kept": None,
        "n_baseline_trades_scaled": None,
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": None,
        "delta_pnl_pct": None,
        "basin_invariance_score": "N/A — substrate change",
        "requires_full_backtest": "YES — no proxy",
    },
    {
        "candidate": "C_meta_labeling",
        "description": "M2 secondary classifier: keep only conf > 0.85",
        "basin_relocation_robust": "LOW — depends on M1 confidence calibration; basin-contingent if M1 retrains",
        "n_baseline_trades_kept": int(n_kept_C),
        "n_baseline_trades_scaled": int(n_dropped_C),
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": round(counterfactual_pnl_C, 4),
        "delta_pnl_pct": round(counterfactual_pnl_C - ltc_oos["net_pnl_pct"].sum(), 4),
        "basin_invariance_score": "LOW — gate on confidence which is basin-output",
        "requires_full_backtest": "YES",
    },
    {
        "candidate": "D_sample_weighting",
        "description": "AFML Ch.4 inverse-concurrency weighting OR hard-negative oversampling",
        "basin_relocation_robust": "HIGH — changes the training objective; basin IS the change",
        "n_baseline_trades_kept": None,
        "n_baseline_trades_scaled": None,
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": None,
        "delta_pnl_pct": None,
        "basin_invariance_score": "N/A — substrate change",
        "requires_full_backtest": "YES",
    },
    {
        "candidate": "E_atr_thresholds_tighter_sl",
        "description": "tighter SL (cap loss at -3% via lower atr_sl multiplier)",
        "basin_relocation_robust": "MEDIUM-HIGH — SL is post-decision exit; mechanism acts on every trade equally regardless of basin",
        "n_baseline_trades_kept": int(len(ltc_oos)),
        "n_baseline_trades_scaled": int((ltc_oos["net_pnl_pct"] < -3.0).sum()),
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": round(counterfactual_pnl_E_tighter_sl, 4),
        "delta_pnl_pct": round(counterfactual_pnl_E_tighter_sl - ltc_oos["net_pnl_pct"].sum(), 4),
        "basin_invariance_score": "MEDIUM-HIGH — operates post-prediction, basin-relocation-orthogonal",
        "requires_full_backtest": "YES — would also affect TP fires",
    },
    {
        "candidate": "F_prior_month_drawdown_gate",
        "description": "skip trades in months after prior month -10% drawdown",
        "basin_relocation_robust": "MEDIUM — stateful but not gate-of-targeted-prop; basin-orthogonal",
        "n_baseline_trades_kept": int(n_kept_F),
        "n_baseline_trades_scaled": int(n_dropped_F),
        "baseline_oos_pnl_pct_obs": round(ltc_oos["net_pnl_pct"].sum(), 4),
        "baseline_oos_pnl_pct_counterfactual": round(counterfactual_pnl_F, 4),
        "delta_pnl_pct": round(counterfactual_pnl_F - ltc_oos["net_pnl_pct"].sum(), 4),
        "basin_invariance_score": "MEDIUM — stateful gate; trade-roster level",
        "requires_full_backtest": "YES — STATEFUL needs deadlock proof",
    },
]
mech_df = pd.DataFrame(mechanism_rows)
mech_df.to_csv(OUT_DIR / "ltc_mechanism_robustness_predictions.csv", index=False)
print(mech_df.to_string(index=False))
print()


# ============================================================
# Summary statistics for brief Section 2
# ============================================================
print("=" * 70)
print("SUMMARY for brief Section 2")
print("=" * 70)
print(f"Baseline LTC OOS: {len(ltc_oos)} trades, net PnL {ltc_oos['net_pnl_pct'].sum():+.2f}%, win rate {(ltc_oos['net_pnl_pct'] > 0).mean()*100:.1f}%")
print(f"Per-trade Sharpe: {ltc_oos['net_pnl_pct'].mean() / ltc_oos['net_pnl_pct'].std():+.4f}")
print()

print("Direction breakdown (OOS):")
for d_val, d_label in [(1, "long"), (-1, "short")]:
    sub = ltc_oos[ltc_oos["direction"] == d_val]
    print(f"  {d_label:5s}: {len(sub):2d} trades ({len(sub)/len(ltc_oos)*100:5.1f}%) "
          f"net PnL {sub['net_pnl_pct'].sum():+8.2f}%  "
          f"win rate {(sub['net_pnl_pct'] > 0).mean()*100:5.1f}%")
print()

print(f"Loss-side concentration (catastrophic <-7% bucket):")
cat = ltc_oos[ltc_oos["net_pnl_pct"] <= -7.0]
print(f"  n_trades = {len(cat)}, net_pnl_share = {cat['net_pnl_pct'].sum() / ltc_oos['net_pnl_pct'].sum() * 100:5.1f}% of total OOS")
print()

print("Stop-loss concentration:")
sl = ltc_oos[ltc_oos["exit_reason"] == "stop_loss"]
print(f"  n_SL_trades = {len(sl)}, SL share of trades = {len(sl)/len(ltc_oos)*100:.1f}%, SL net PnL = {sl['net_pnl_pct'].sum():+.2f}%")
print()

print(f"Top 3 worst OOS months:")
print(monthly_df.head(3).to_string(index=False))
print()

print(f"BASIN RELOCATION (vs /022 retrained):")
for r in basin_rows:
    print(f"  {r['sample']}: Jaccard={r['jaccard']:.3f}, baseline_only={r['baseline_only_trades']}, iter022_only={r['iter022_only_trades']}")
print()

print("ALL CSVs written to:", OUT_DIR)
print("=" * 70)
