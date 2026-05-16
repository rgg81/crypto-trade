"""TRX OOS diagnostic EDA — iter-v3/060 first cycle 1 EXPLORATION.

Critic FINAL `0fc18c2` Recommendation #2: "TRX OOS deserves a cycle 1 diagnostic
axis." TRX OOS weighted_pnl collapsed +23.03 (/058 seed 42) → +4.16 (/059 unified
10-seed) between architectures. Brief's pre-registered failure-mode "averaging
convergence suppresses high-variance bet placement" fired. But is TRX still
contributing genuine signal under unified architecture, or is its IS contribution
(3.47% of IS PnL, 0.050% avg/trade) near-noise?

This script DOES NOT change V3_FEATURE_COLUMNS, V3_LABEL_PARAMS, RiskV2Config,
V3_MODELS, or any other code state. It is a passive diagnostic to support axis
selection at brief Section 3.

Outputs (committed CSVs):
  - q1_feature_importance_per_symbol.csv  — TRX vs BCH vs LDO importance rank/share
  - q2_label_distribution_trx.csv          — TRX label balance per quarter
  - q3_trade_distribution_trx.csv          — TRX OOS PnL concentration (top-K cumulative)
  - q4_feature_scale_distribution.csv      — TRX vs BCH vs LDO feature ranges
  - q5_trx_oos_vs_is_predictability.csv    — TRX IS WR/PnL by ATR regime
  - q6_trx_058_vs_059_comparison.csv       — TRX trade roster comparison /058 vs /059
  - q7_weighted_vs_unweighted_pnl.csv      — RiskV2 weight_factor effect per symbol

Path decision criterion (documented in brief Section 10):
  Path A — passive diagnostic only, no code change
  Path B — TRX-specific feature engineering (active)
  Path C — TRX-specific label parameter customization (active)
  Path D — drop TRX entirely (universe contraction)

Run:
  uv run python analysis/iteration_v3-060/trx_diagnostic.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants (from BASELINE_V3.md)
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC
TRAINING_MS = 24 * 30 * 24 * 3600 * 1000  # 24 months in ms (informational only)

REPO = Path(__file__).resolve().parents[2]
REPORTS_059 = REPO / "reports-v3" / "iteration_v3-059"
REPORTS_058 = REPO / "reports-v3" / "iteration_v3-058"
FEATURES_V3 = REPO / "data" / "features_v3"
OUTPUT = Path(__file__).parent

V3_FEATURE_COLUMNS_TOP_N = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ---------------------------------------------------------------------------
# Q1 — TRX feature importance: rank/share comparison vs BCH/LDO
# ---------------------------------------------------------------------------


def q1_feature_importance() -> pd.DataFrame:
    """For each of BCH/LDO/TRX + portfolio, return last-month feature importance
    with rank, raw value, and share-of-total. The question: does the unified
    model "see" TRX differently than BCH/LDO?

    Hypothesis: if TRX top-3 importance share is materially lower than BCH/LDO,
    the model is using TRX as a 'noise' contributor — Path D candidate evidence.
    If TRX top-3 share is similar to BCH/LDO, the model is treating TRX as a
    legitimate signal source — Path A/B candidates more appropriate.
    """
    rows = []
    for sym in list(V3_MODELS) + ["portfolio"]:
        path = REPORTS_059 / "in_sample" / f"model_importance_last_month_{sym}.csv"
        df = pd.read_csv(path)
        total = df["importance"].sum()
        df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1
        df["share_pct"] = df["importance"] / total * 100
        df["scope"] = sym
        rows.append(df[["scope", "feature", "rank", "importance", "share_pct"]])
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(OUTPUT / "q1_feature_importance_per_symbol.csv", index=False)
    return out


def q1_top3_summary(q1: pd.DataFrame) -> pd.DataFrame:
    """Compact summary: top-3 importance share + top feature per scope."""
    rows = []
    for scope, g in q1.groupby("scope"):
        top3_share = g.nsmallest(3, "rank")["share_pct"].sum()
        top1 = g[g["rank"] == 1].iloc[0]
        rows.append(
            {
                "scope": scope,
                "top1_feature": top1["feature"],
                "top1_share_pct": top1["share_pct"],
                "top3_share_pct": top3_share,
                "total_features": int(g["rank"].max()),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q1_top3_summary.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q2 — TRX label distribution per quarter (from trades.csv direction balance)
# ---------------------------------------------------------------------------


def q2_label_distribution_trx() -> pd.DataFrame:
    """TRX trade direction balance + outcome (TP/SL/timeout) per quarter.

    Reads /059 IS+OOS trades.csv and aggregates TRX-only rows by quarter.
    Hypothesis: if TRX trades are skewed (e.g., always SHORT in Q3-23 → always
    LONG in Q2-24) the model has captured a regime-conditional signal. If they
    are 50/50 with no temporal structure, Path D candidate evidence (TRX is
    noise-driven).
    """
    is_trades = pd.read_csv(REPORTS_059 / "in_sample" / "trades.csv")
    oos_trades = pd.read_csv(REPORTS_059 / "out_of_sample" / "trades.csv")
    is_trades["split"] = "IS"
    oos_trades["split"] = "OOS"
    trades = pd.concat([is_trades, oos_trades], ignore_index=True)
    trx = trades[trades["symbol"] == "TRXUSDT"].copy()

    # Convert open_time ms → quarter label
    trx["quarter"] = pd.to_datetime(trx["open_time"], unit="ms").dt.to_period("Q")

    rows = []
    for (q, split), g in trx.groupby(["quarter", "split"]):
        n = len(g)
        n_long = (g["direction"] == 1).sum()
        n_short = (g["direction"] == -1).sum()
        n_tp = (g["exit_reason"] == "take_profit").sum()
        n_sl = (g["exit_reason"] == "stop_loss").sum()
        n_to = (g["exit_reason"] == "timeout").sum()
        n_eod = (g["exit_reason"] == "end_of_data").sum()
        pnl = g["weighted_pnl"].sum()
        wins = (g["weighted_pnl"] > 0).sum()
        rows.append(
            {
                "quarter": str(q),
                "split": split,
                "n_trades": n,
                "n_long": n_long,
                "n_short": n_short,
                "long_share": n_long / n if n > 0 else 0.0,
                "n_tp": n_tp,
                "n_sl": n_sl,
                "n_timeout": n_to,
                "n_eod": n_eod,
                "tp_share": n_tp / n if n > 0 else 0.0,
                "sl_share": n_sl / n if n > 0 else 0.0,
                "win_rate": wins / n if n > 0 else 0.0,
                "weighted_pnl": pnl,
            }
        )
    out = pd.DataFrame(rows).sort_values(["split", "quarter"]).reset_index(drop=True)
    out.to_csv(OUTPUT / "q2_label_distribution_trx.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q3 — TRX OOS PnL concentration: top-K trade cumulative contribution
# ---------------------------------------------------------------------------


def q3_trade_distribution_trx() -> pd.DataFrame:
    """TRX OOS trade-level PnL concentration analysis.

    For each split (IS, OOS), sort TRX trades by weighted_pnl descending,
    compute cumulative contribution. If top-3 OOS trades contribute >70%
    of TRX OOS weighted_pnl, the +4.16 is a 'lucky tail' result — Path D
    evidence (signal is noisy / variance-driven). If top-3 contribute <40%,
    distribution is flat and signal is genuine.

    Also reports: per-trade weighted_pnl percentiles, mean/std, % trades
    with weight_factor==0 (RiskV2 vol scaling kills).
    """
    rows = []
    for split in ["IS", "OOS"]:
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        trx = trades[trades["symbol"] == "TRXUSDT"].copy()
        wp = trx["weighted_pnl"].sort_values(ascending=False).values
        total = wp.sum()
        n = len(wp)
        if n == 0:
            continue
        cum = np.cumsum(wp)
        topk = {
            "split": split,
            "n_trades": n,
            "total_weighted_pnl": total,
            "mean_per_trade": wp.mean(),
            "std_per_trade": wp.std(ddof=1) if n > 1 else 0.0,
            "median_per_trade": np.median(wp),
            "p25_per_trade": np.percentile(wp, 25),
            "p75_per_trade": np.percentile(wp, 75),
            "max_per_trade": wp.max(),
            "min_per_trade": wp.min(),
            "n_killed_weight0": (trx["weight_factor"] == 0).sum(),
            "killed_pct": (trx["weight_factor"] == 0).mean() * 100,
        }
        for k in [1, 3, 5, 10]:
            if k <= n:
                topk[f"top{k}_share_pct"] = (cum[k - 1] / total * 100) if total != 0 else float("nan")
            else:
                topk[f"top{k}_share_pct"] = float("nan")
        rows.append(topk)
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q3_trade_distribution_trx.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q4 — TRX vs BCH vs LDO feature scale/range distribution
# ---------------------------------------------------------------------------


def q4_feature_scale_distribution() -> pd.DataFrame:
    """For each of the 14 V3_FEATURE_COLUMNS_TOP_N features, compute the
    IS-window distribution (mean, std, min, p25, p50, p75, max) per symbol.
    Hypothesis: if TRX features have very different scale/range from BCH/LDO,
    the pooled-by-symbol model may be effectively under-using TRX features
    (TRX rows contribute different magnitudes than BCH/LDO at same percentile
    in the joint distribution). Path B candidate evidence (TRX-specific
    normalization or features needed).
    """
    rows = []
    for sym in V3_MODELS:
        df = pd.read_parquet(FEATURES_V3 / f"{sym}_8h_features.parquet")
        # IS window: pre-OOS_CUTOFF
        is_mask = df["open_time"] < OOS_CUTOFF_MS
        is_df = df[is_mask]
        for feat in V3_FEATURE_COLUMNS_TOP_N:
            if feat not in is_df.columns:
                continue
            s = is_df[feat].dropna()
            if len(s) == 0:
                continue
            rows.append(
                {
                    "symbol": sym,
                    "feature": feat,
                    "n_obs": len(s),
                    "mean": s.mean(),
                    "std": s.std(),
                    "min": s.min(),
                    "p25": s.quantile(0.25),
                    "p50": s.quantile(0.50),
                    "p75": s.quantile(0.75),
                    "max": s.max(),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q4_feature_scale_distribution.csv", index=False)
    return out


def q4_scale_divergence_summary(q4: pd.DataFrame) -> pd.DataFrame:
    """For each feature, compute max scale divergence across symbols.

    Two divergence metrics:
      - mean_z: |TRX_mean - BCH_mean| / pooled_std (effect-size analog)
      - std_ratio: max(std) / min(std) across 3 syms
    """
    rows = []
    for feat in V3_FEATURE_COLUMNS_TOP_N:
        g = q4[q4["feature"] == feat]
        if len(g) < 3:
            continue
        trx = g[g["symbol"] == "TRXUSDT"].iloc[0]
        bch = g[g["symbol"] == "BCHUSDT"].iloc[0]
        ldo = g[g["symbol"] == "LDOUSDT"].iloc[0]
        pooled_std = (trx["std"] + bch["std"] + ldo["std"]) / 3
        trx_vs_bch_z = abs(trx["mean"] - bch["mean"]) / pooled_std if pooled_std > 0 else float("nan")
        trx_vs_ldo_z = abs(trx["mean"] - ldo["mean"]) / pooled_std if pooled_std > 0 else float("nan")
        stds = [trx["std"], bch["std"], ldo["std"]]
        std_ratio = max(stds) / min(stds) if min(stds) > 0 else float("nan")
        rows.append(
            {
                "feature": feat,
                "trx_mean": trx["mean"],
                "bch_mean": bch["mean"],
                "ldo_mean": ldo["mean"],
                "trx_std": trx["std"],
                "bch_std": bch["std"],
                "ldo_std": ldo["std"],
                "trx_vs_bch_meanZ": trx_vs_bch_z,
                "trx_vs_ldo_meanZ": trx_vs_ldo_z,
                "std_ratio_max_min": std_ratio,
            }
        )
    out = pd.DataFrame(rows).sort_values("trx_vs_bch_meanZ", ascending=False).reset_index(drop=True)
    out.to_csv(OUTPUT / "q4_scale_divergence_summary.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q5 — TRX IS WR/PnL by ATR regime (low-vol vs high-vol)
# ---------------------------------------------------------------------------


def q5_trx_oos_vs_is_predictability() -> pd.DataFrame:
    """TRX trade outcome by 14-day ATR regime (bottom/middle/top tercile of
    TRX trade entry ATR). Hypothesis: if TRX trades concentrate in a single
    ATR regime AND that regime has materially different WR than the others,
    the model has learned a regime-conditional signal — Path B/C candidate.
    """
    is_trades = pd.read_csv(REPORTS_059 / "in_sample" / "trades.csv")
    oos_trades = pd.read_csv(REPORTS_059 / "out_of_sample" / "trades.csv")
    is_trades["split"] = "IS"
    oos_trades["split"] = "OOS"
    trades = pd.concat([is_trades, oos_trades], ignore_index=True)
    trx = trades[trades["symbol"] == "TRXUSDT"].copy()

    # Load TRX features to get ATR percentile rank at trade entry.
    # Note: trades.csv `open_time` field stores the CLOSE_TIME of the entry
    # candle (the moment the trade was decided / opened). Features parquet is
    # keyed by open_time. The lookup uses close_time on the features side.
    feats_full = pd.read_parquet(FEATURES_V3 / "TRXUSDT_8h_features.parquet")
    # IS-window distribution for tercile thresholds (use open_time for IS filter)
    is_atr = feats_full[feats_full["open_time"] < OOS_CUTOFF_MS]["atr_pct_rank_200"].dropna()

    feats = feats_full[["close_time", "atr_pct_rank_200"]].copy()
    trx = trx.merge(feats, left_on="open_time", right_on="close_time", how="left")
    t33 = is_atr.quantile(1 / 3)
    t67 = is_atr.quantile(2 / 3)

    def regime(x: float) -> str:
        if pd.isna(x):
            return "missing"
        if x < t33:
            return "low"
        if x < t67:
            return "mid"
        return "high"

    trx["atr_regime"] = trx["atr_pct_rank_200"].apply(regime)

    rows = []
    for (split, reg), g in trx.groupby(["split", "atr_regime"]):
        n = len(g)
        wins = (g["weighted_pnl"] > 0).sum()
        rows.append(
            {
                "split": split,
                "atr_regime": reg,
                "n_trades": n,
                "win_rate": wins / n if n > 0 else 0.0,
                "weighted_pnl": g["weighted_pnl"].sum(),
                "avg_per_trade": g["weighted_pnl"].mean() if n > 0 else float("nan"),
            }
        )
    out = pd.DataFrame(rows).sort_values(["split", "atr_regime"]).reset_index(drop=True)
    out.to_csv(OUTPUT / "q5_trx_oos_vs_is_predictability.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q6 — TRX trade roster /058 seed 42 vs /059 unified comparison
# ---------------------------------------------------------------------------


def q6_trx_058_vs_059_comparison() -> pd.DataFrame:
    """Architecture-effect quantification on TRX.

    /058 seed 42 produced TRX OOS +23.03 across 54 trades / 48.1% WR.
    /059 unified produced TRX OOS +4.16 across 48 trades / 39.6% WR.

    Question: are the 48 trades a SUBSET of the 54 (consensus is just stricter)
    OR are they a different roster entirely (consensus shifted entry candidates)?

    Cross-reference open_time × direction overlap.
    """
    t058 = pd.read_csv(REPORTS_058 / "out_of_sample" / "trades.csv")
    t058 = t058[t058["symbol"] == "TRXUSDT"].copy()
    t058["roster"] = "058_seed42"

    t059 = pd.read_csv(REPORTS_059 / "out_of_sample" / "trades.csv")
    t059 = t059[t059["symbol"] == "TRXUSDT"].copy()
    t059["roster"] = "059_unified"

    # Key on (open_time, direction)
    k058 = set(zip(t058["open_time"], t058["direction"]))
    k059 = set(zip(t059["open_time"], t059["direction"]))

    intersect = k058 & k059
    only_058 = k058 - k059
    only_059 = k059 - k058

    rows = [
        {
            "metric": "058_seed42 total trades",
            "value": len(t058),
            "weighted_pnl": float(t058["weighted_pnl"].sum()),
        },
        {
            "metric": "059_unified total trades",
            "value": len(t059),
            "weighted_pnl": float(t059["weighted_pnl"].sum()),
        },
        {
            "metric": "intersection (same open_time AND direction)",
            "value": len(intersect),
            "weighted_pnl": float("nan"),
        },
        {
            "metric": "only in /058 (consensus-dropped from /059)",
            "value": len(only_058),
            "weighted_pnl": float(
                t058[
                    t058[["open_time", "direction"]].apply(
                        lambda r: (r["open_time"], r["direction"]) in only_058, axis=1
                    )
                ]["weighted_pnl"].sum()
            )
            if only_058
            else 0.0,
        },
        {
            "metric": "only in /059 (consensus-added vs /058)",
            "value": len(only_059),
            "weighted_pnl": float(
                t059[
                    t059[["open_time", "direction"]].apply(
                        lambda r: (r["open_time"], r["direction"]) in only_059, axis=1
                    )
                ]["weighted_pnl"].sum()
            )
            if only_059
            else 0.0,
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q6_trx_058_vs_059_comparison.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q7 — Weighted vs unweighted PnL: RiskV2 vol-scaling impact per symbol
# ---------------------------------------------------------------------------


def q7_weighted_vs_unweighted_pnl() -> pd.DataFrame:
    """RiskV2 vol-scaling effect per symbol per split.

    Comparison: net_pnl_pct (unweighted, what the model "saw" as raw signal
    quality) vs weighted_pnl (RiskV2-scaled, what actually contributes to
    portfolio Sharpe). A symbol where weighted < unweighted means RiskV2 is
    systematically shrinking the gains relative to losses → vol-scaling
    weight_factor is anti-correlated with prediction quality (RiskV2 kills
    high-conviction trades that turn out to be the wins).

    Critical for TRX: per_symbol.csv reports +3.95 net_pnl_pct (positive),
    but weighted_pnl sums to -7.35 (NEGATIVE). The comparison.csv
    pct_of_total_pnl column tracks unweighted; portfolio weighted_pnl_total
    tracks weighted. This is the source of the apparent "TRX contributes
    3.47% of IS PnL" reading in BASELINE_V3.md while TRX is actually a NET
    DRAG on portfolio weighted PnL.
    """
    rows = []
    for split in ["IS", "OOS"]:
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        for sym in V3_MODELS:
            g = trades[trades["symbol"] == sym].copy()
            n = len(g)
            if n == 0:
                continue
            unweighted = g["net_pnl_pct"].sum()
            weighted = g["weighted_pnl"].sum()
            wins_unw = (g["net_pnl_pct"] > 0).sum()
            wins_w = (g["weighted_pnl"] > 0).sum()
            avg_wf_on_wins = g[g["net_pnl_pct"] > 0]["weight_factor"].mean() if wins_unw > 0 else float("nan")
            avg_wf_on_losses = g[g["net_pnl_pct"] < 0]["weight_factor"].mean() if (n - wins_unw) > 0 else float("nan")
            rows.append(
                {
                    "split": split,
                    "symbol": sym,
                    "n_trades": n,
                    "unweighted_net_pnl_pct": unweighted,
                    "weighted_pnl": weighted,
                    "weight_attrition_pct": (weighted - unweighted) / abs(unweighted) * 100
                    if unweighted != 0
                    else float("nan"),
                    "avg_weight_on_wins": avg_wf_on_wins,
                    "avg_weight_on_losses": avg_wf_on_losses,
                    "win_weight_minus_loss_weight": avg_wf_on_wins - avg_wf_on_losses
                    if not (pd.isna(avg_wf_on_wins) or pd.isna(avg_wf_on_losses))
                    else float("nan"),
                    "n_killed_weight0": (g["weight_factor"] == 0).sum(),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q7_weighted_vs_unweighted_pnl.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Composite summary
# ---------------------------------------------------------------------------


def write_summary_md(q1_top3: pd.DataFrame, q2: pd.DataFrame, q3: pd.DataFrame,
                     q4_div: pd.DataFrame, q5: pd.DataFrame, q6: pd.DataFrame,
                     q7: pd.DataFrame) -> None:
    """Generate diagnostic_summary.md collating the Path A/B/C/D evidence."""
    lines = []
    lines.append("# TRX Diagnostic EDA Summary — iter-v3/060")
    lines.append("")
    lines.append("Anchor: BASELINE_V3.md iter-v3/059 unified 10-seed ensemble")
    lines.append("")
    lines.append("## Q1 — Feature importance per symbol (last-month IS model)")
    lines.append("")
    lines.append(q1_top3.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q2 — TRX label distribution per quarter")
    lines.append("")
    lines.append(q2.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q3 — TRX OOS PnL concentration (top-K cumulative contribution)")
    lines.append("")
    lines.append(q3.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q4 — TRX vs BCH vs LDO feature scale divergence (top-divergent features)")
    lines.append("")
    lines.append(q4_div.head(10).to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q5 — TRX trade outcome by ATR regime")
    lines.append("")
    lines.append(q5.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q6 — TRX trade roster /058 vs /059 architecture comparison")
    lines.append("")
    lines.append(q6.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Q7 — RiskV2 vol-scaling effect: unweighted vs weighted PnL per symbol")
    lines.append("")
    lines.append(q7.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    (OUTPUT / "diagnostic_summary.md").write_text("\n".join(lines))


def main() -> None:
    print("[iter-v3/060 TRX diagnostic] Q1 — feature importance per symbol")
    q1 = q1_feature_importance()
    q1_top3 = q1_top3_summary(q1)
    print(q1_top3.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q2 — TRX label distribution per quarter")
    q2 = q2_label_distribution_trx()
    print(q2.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q3 — TRX trade PnL concentration")
    q3 = q3_trade_distribution_trx()
    print(q3.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q4 — feature scale distribution")
    q4 = q4_feature_scale_distribution()
    q4_div = q4_scale_divergence_summary(q4)
    print(q4_div.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q5 — TRX trade outcome by ATR regime")
    q5 = q5_trx_oos_vs_is_predictability()
    print(q5.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q6 — TRX /058 vs /059 roster overlap")
    q6 = q6_trx_058_vs_059_comparison()
    print(q6.to_string(index=False))

    print("\n[iter-v3/060 TRX diagnostic] Q7 — weighted vs unweighted PnL per symbol")
    q7 = q7_weighted_vs_unweighted_pnl()
    print(q7.to_string(index=False))

    write_summary_md(q1_top3, q2, q3, q4_div, q5, q6, q7)
    print(f"\n[iter-v3/060] EDA outputs written to {OUTPUT}")


if __name__ == "__main__":
    main()
