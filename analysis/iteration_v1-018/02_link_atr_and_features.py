"""LINK feature distribution + ATR profile vs other v1 symbols — iter-v1/018 EDA.

Reads the v1 feature parquets (data/features/<SYM>_8h_features.parquet) for
LINK + BTC + ETH + LTC + DOT (v1 BASELINE_UNIVERSE) and computes IS-only
distribution stats on V1_FEATURE_COLUMNS_PRUNED to characterize where LINK
differs from the pool — informing the per-cohort specialization dimension
selection.

IS-only: training_start = 2023-04-04 (first walk-forward window) through
OOS_CUTOFF_DATE = 2025-03-24. (Reading the parquet directly; no labels/no
training; no leak.)

Outputs (committed):
- link_natr_profile.csv : LINK NATR_14 quantiles vs other syms (IS-only)
- link_feature_stats.csv : LINK std vs portfolio-median for each PRUNED feature
- link_atr_calibration.csv : if LINK had its own ATR multipliers,
  what TP/SL distances would put it at the SAME bp-of-NATR floor that v1
  Model A has? (ATR=2.9/1.45 for A; ATR=3.5/1.75 for C)

NO TRAINING. NO MODEL FIT. Pure IS-only distribution stats.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FEAT_DIR = ROOT / "data" / "features"
OUT = ROOT / "analysis" / "iteration_v1-018"
OUT.mkdir(parents=True, exist_ok=True)

# IS window
IS_START_MS = 1680566400000  # 2023-04-04 00:00:00 UTC
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC

V1_PRUNED = [
    "cal_dow_norm",
    "cal_hour_norm",
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "mom_macd_hist_12_26_9",
    "mom_macd_line_12_26_9",
    "mom_roc_10",
    "mom_rsi_14",
    "mom_stoch_d_14",
    "mom_stoch_k_14",
    "mom_willr_14",
    "mr_pct_from_high_20",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "stat_autocorr_lag5",
    "stat_kurtosis_20",
    "stat_log_return_1",
    "stat_return_5",
    "stat_skew_20",
    "trend_adx_14",
    "trend_aroon_osc_14",
    "trend_aroon_osc_50",
    "trend_ema_cross_5_12",
    "trend_minus_di_14",
    "trend_plus_di_14",
    "trend_supertrend_14_3",
    "vol_atr_14",
    "vol_bb_bandwidth_20",
    "vol_cmf_14",
    "vol_mfi_14",
    "vol_natr_14",
    "vol_range_spike_24",
    "vol_range_spike_72",
    "vol_taker_buy_ratio",
    "vol_volume_pctchg_5",
    "vol_volume_rel_20",
]

UNIVERSE = ["LINKUSDT", "BTCUSDT", "ETHUSDT", "LTCUSDT", "DOTUSDT"]


def load_is_features(sym: str) -> pd.DataFrame:
    p = FEAT_DIR / f"{sym}_8h_features.parquet"
    if not p.exists():
        raise FileNotFoundError(p)
    df = pd.read_parquet(p)
    # The parquet columns include open_time (close_time of bar - 1?), keep it.
    # Filter to IS window: open_time in [IS_START_MS, OOS_CUTOFF_MS).
    if "open_time" not in df.columns:
        raise KeyError(f"open_time missing in {p}")
    is_df = df[(df["open_time"] >= IS_START_MS) & (df["open_time"] < OOS_CUTOFF_MS)].copy()
    return is_df


def quantile_table(sym_dfs: dict[str, pd.DataFrame], col: str) -> pd.DataFrame:
    rows = []
    for sym, df in sym_dfs.items():
        if col not in df.columns:
            rows.append(dict(symbol=sym, feature=col, missing=True))
            continue
        s = df[col].dropna()
        rows.append(
            dict(
                symbol=sym,
                feature=col,
                n=len(s),
                mean=round(s.mean(), 6),
                std=round(s.std(), 6),
                p05=round(s.quantile(0.05), 6),
                p25=round(s.quantile(0.25), 6),
                p50=round(s.quantile(0.50), 6),
                p75=round(s.quantile(0.75), 6),
                p95=round(s.quantile(0.95), 6),
                missing=False,
            )
        )
    return pd.DataFrame(rows)


def main() -> None:
    print(f"Loading IS features (2023-04-04 → 2025-03-24) for {UNIVERSE}")
    sym_dfs = {sym: load_is_features(sym) for sym in UNIVERSE}
    for sym, df in sym_dfs.items():
        print(f"  {sym}: {len(df)} IS rows; cols present from pruned: "
              f"{sum(c in df.columns for c in V1_PRUNED)}/{len(V1_PRUNED)}")

    # 1. NATR_14 quantile profile — key for ATR calibration choice
    natr_table = quantile_table(sym_dfs, "vol_natr_14")
    natr_path = OUT / "link_natr_profile.csv"
    natr_table.to_csv(natr_path, index=False)
    print(f"\n[1] NATR_14 distribution (IS-only) → {natr_path}")
    print(natr_table.to_string(index=False))

    # 2. ATR_14 raw values — same comparison
    atr_table = quantile_table(sym_dfs, "vol_atr_14")
    atr_path = OUT / "link_atr_profile.csv"
    atr_table.to_csv(atr_path, index=False)
    print(f"\n[2] ATR_14 distribution (IS-only) → {atr_path}")
    print(atr_table.to_string(index=False))

    # 3. For each PRUNED feature, std and % distance LINK vs portfolio-median.
    # Identifies features where LINK is structurally different — candidates for
    # LINK-specific feature relevance.
    rows = []
    for col in V1_PRUNED:
        if col not in sym_dfs["LINKUSDT"].columns:
            continue
        link_s = sym_dfs["LINKUSDT"][col].dropna()
        if len(link_s) == 0:
            continue
        link_mean = link_s.mean()
        link_std = link_s.std()
        # portfolio median std (across other 4 syms)
        others = [s for s in UNIVERSE if s != "LINKUSDT"]
        other_stds = [sym_dfs[s][col].std() for s in others if col in sym_dfs[s].columns]
        port_med_std = np.median(other_stds) if other_stds else float("nan")
        other_means = [sym_dfs[s][col].mean() for s in others if col in sym_dfs[s].columns]
        port_med_mean = np.median(other_means) if other_means else float("nan")
        std_ratio = link_std / port_med_std if port_med_std > 0 else float("nan")
        rows.append(
            dict(
                feature=col,
                link_mean=round(link_mean, 6),
                link_std=round(link_std, 6),
                portfolio_med_mean=round(port_med_mean, 6),
                portfolio_med_std=round(port_med_std, 6),
                link_std_ratio=round(std_ratio, 4),
            )
        )
    feat_df = pd.DataFrame(rows)
    feat_df = feat_df.sort_values("link_std_ratio", ascending=False, na_position="last")
    feat_path = OUT / "link_feature_stats.csv"
    feat_df.to_csv(feat_path, index=False)
    print(f"\n[3] LINK feature std vs portfolio-median (IS-only) → {feat_path}")
    print("\nTop 10 features where LINK has HIGHER std than portfolio median:")
    print(feat_df.head(10).to_string(index=False))
    print("\nBottom 10 (LINK has LOWER std):")
    print(feat_df.tail(10).to_string(index=False))

    # 4. ATR multiplier calibration — what TP/SL distance would symmetric LINK
    # ATR multiplier achieve vs the C-default (3.5/1.75) and A-default (2.9/1.45)?
    # NATR_14 median sets the "typical" 8h volatility floor.
    link_natr_p50 = float(sym_dfs["LINKUSDT"]["vol_natr_14"].dropna().quantile(0.50))
    link_natr_p25 = float(sym_dfs["LINKUSDT"]["vol_natr_14"].dropna().quantile(0.25))
    link_natr_p75 = float(sym_dfs["LINKUSDT"]["vol_natr_14"].dropna().quantile(0.75))

    cal_rows = []
    for label, mult_tp, mult_sl in [
        ("baseline C (3.5/1.75)", 3.5, 1.75),
        ("Model A profile (2.9/1.45)", 2.9, 1.45),
        ("Specialization A: tighter (3.0/1.5)", 3.0, 1.5),
        ("Specialization B: wider (4.0/2.0)", 4.0, 2.0),
        ("Specialization C: 1:1 (2.0/2.0)", 2.0, 2.0),
        ("Specialization D: 3:1 (4.5/1.5)", 4.5, 1.5),
    ]:
        # TP / SL distance at p50 NATR (LINK's typical bar volatility)
        tp_dist_p50 = mult_tp * link_natr_p50
        sl_dist_p50 = mult_sl * link_natr_p50
        cal_rows.append(
            dict(
                spec=label,
                atr_tp_mult=mult_tp,
                atr_sl_mult=mult_sl,
                rr=round(mult_tp / mult_sl, 4),
                tp_dist_p25_pct=round(mult_tp * link_natr_p25, 4),
                tp_dist_p50_pct=round(tp_dist_p50, 4),
                tp_dist_p75_pct=round(mult_tp * link_natr_p75, 4),
                sl_dist_p25_pct=round(mult_sl * link_natr_p25, 4),
                sl_dist_p50_pct=round(sl_dist_p50, 4),
                sl_dist_p75_pct=round(mult_sl * link_natr_p75, 4),
            )
        )
    cal_df = pd.DataFrame(cal_rows)
    cal_path = OUT / "link_atr_calibration.csv"
    cal_df.to_csv(cal_path, index=False)
    print(f"\n[4] ATR multiplier calibration at LINK NATR quantiles → {cal_path}")
    print(cal_df.to_string(index=False))

    print(f"\nLINK NATR_14 quantiles (IS): p25={link_natr_p25:.4f}%  "
          f"p50={link_natr_p50:.4f}%  p75={link_natr_p75:.4f}%")


if __name__ == "__main__":
    main()
