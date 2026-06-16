"""IS-ONLY cross-sub-period IC STABILITY screen of a wide technical-indicator net — iter-v1/014 (BTCUSDT).

CAMPAIGN LESSON (iter-005..012): high IS-IC does NOT imply OOS generalization. The 19-col HYBRID set
gives +0.39 IS Sharpe at N=9 but the directional edge INVERTS IS-bull (+31%) -> OOS-bull (-22%) — the
signal is overfit to 2023-24 IS-bull microstructure (diary-v1/012). The let-run LONG edge is positive
in 6/9 IS sub-periods and negative in the SAME 3 bear/correction sub-periods for ALL seeds (brief 011).

So the iter-014 SELECTION CRITERION is NOT peak IS-IC. It is **cross-IS-sub-period SIGN+MAGNITUDE
STABILITY of the indicator's univariate IC vs the forward return**. An indicator whose IC is the same
sign and similar magnitude in EVERY IS sub-period (2021 bull, 2022 bear, 2023 recovery, 2024 bull,
2025-Q1 correction) is the IS-visible signature of a relationship that holds ACROSS regimes — the kind
that may survive into OOS. An indicator with strong IC only in the 2023-24 bull and flat/negative in
2022 is the OVERFIT TRAP to avoid.

WHAT THIS SCRIPT DOES (IS-ONLY):
  1. Inventory a WIDE net of technical indicators we have NOT leaned on (beyond the 19-col hybrid):
     oscillators (Stoch, Williams %R, CCI-proxy, ROC, MOM, RSI windows), trend (Aroon, DI spread,
     supertrend, EMA/SMA cross, PSAR, ADX windows), volatility (BB bandwidth/%B, Keltner-proxy via
     ATR, Donchian-proxy via pct-from-high/low, Garman-Klass/Parkinson/hist windows, range_spike,
     NATR), volume/flow (OBV-slope, CMF, MFI, taker-buy ratio, ease-of-movement-proxy, VWAP-dev,
     volume rel/pctchg), statistical (autocorr, skew, kurtosis, returns), regime/microstructure
     (hurst, entropy, cusum, basis, funding, OI). Concrete parquet column names only.
  2. For EACH candidate compute the univariate Spearman IC vs the N=9 (3d) fixed-horizon forward LOG
     return IN EACH ~6-month IS sub-period; report full-IS IC, per-sub-period IC, frac-of-sub-periods
     SAME SIGN (vs the full-IS-IC sign), IC dispersion (std across sub-periods), worst-sub-period IC,
     and a STABILITY SCORE = mean(|IC|) * frac_same_sign  (rewards consistent-sign + non-trivial size;
     a flip-flopping or near-zero indicator scores low even with one strong sub-period).
  3. Tag each candidate IN_19COL / NEW. Print the 19-col members on the same stability metric as the
     baseline-to-beat, and rank the NEW candidates by stability score.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any forward
quantity; forward return computed AFTER the filter (tail rows NaN-mask — no OOS candle in the frame);
features used as-is from the parquet (already past-only by features_v1). Nothing fit/selected against
OOS; OOS rows never read. `src/`, the runner, and OOS are UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-014/subperiod_ic_stability.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
N_LABEL = 9  # fixed_horizon 3d (the iter-010/011 direction; matches the campaign milestone)
SUBPERIOD_DAYS = 182.5  # ~6 months
MIN_SUBPERIOD_N = 60  # require enough rows in a sub-period for a meaningful IC
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-014"

# The current 19-col HYBRID set (iter-009/010) — measured on the SAME stability metric as the baseline.
ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7",
    "vol_garman_klass_10",
    "vol_atr_5",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5",
    "vol_mfi_7",
    "mom_rsi_9",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
    "vol_cmf_10",
    "ent_shannon_10",
    "trend_adx_14",
    "trend_supertrend_14_3",
    "btc_funding_spread_30_90",
    "funding_rate_zscore_30",
    "stat_autocorr_lag5",
    "vol_range_spike_72",
    "mr_rsi_extreme_14",
    "stat_kurtosis_20",
)

# A WIDE net of technical-indicator candidate columns (only ones that exist in the parquet are kept).
# Grouped by family for the inventory print; flattened for the IC loop.
CANDIDATE_FAMILIES: dict[str, tuple[str, ...]] = {
    "oscillator_stoch": (
        "mom_stoch_k_5", "mom_stoch_d_5", "mom_stoch_k_9", "mom_stoch_d_9",
        "mom_stoch_k_14", "mom_stoch_d_14", "mom_stoch_k_21", "mom_stoch_d_21",
    ),
    "oscillator_willr": ("mom_willr_7", "mom_willr_14", "mom_willr_21"),
    "oscillator_roc_mom": (
        "mom_roc_3", "mom_roc_5", "mom_roc_10", "mom_roc_15", "mom_roc_20", "mom_roc_30",
        "mom_mom_5", "mom_mom_10", "mom_mom_15", "mom_mom_20",
    ),
    "oscillator_rsi": ("mom_rsi_5", "mom_rsi_7", "mom_rsi_9", "mom_rsi_14", "mom_rsi_21", "mom_rsi_30"),
    "trend_adx_di": (
        "trend_adx_7", "trend_plus_di_7", "trend_minus_di_7",
        "trend_adx_14", "trend_plus_di_14", "trend_minus_di_14",
        "trend_adx_21", "trend_plus_di_21", "trend_minus_di_21",
    ),
    "trend_aroon": (
        "trend_aroon_osc_14", "trend_aroon_up_14", "trend_aroon_down_14",
        "trend_aroon_osc_25", "trend_aroon_osc_50",
    ),
    "trend_macd": (
        "mom_macd_line_8_21_5", "mom_macd_hist_8_21_5", "mom_macd_signal_8_21_5",
        "mom_macd_line_12_26_9", "mom_macd_hist_12_26_9",
        "mom_macd_line_5_13_3", "mom_macd_hist_5_13_3",
    ),
    "trend_structure": (
        "trend_ema_cross_5_12", "trend_ema_cross_9_21", "trend_ema_cross_12_50",
        "trend_sma_cross_10_50", "trend_sma_cross_20_50", "trend_sma_cross_20_100",
        "trend_supertrend_7_3", "trend_supertrend_10_2", "trend_supertrend_14_3",
        "trend_psar_dir", "trend_psar_af",
    ),
    "vol_bb": (
        "vol_bb_bandwidth_10", "vol_bb_pctb_10", "vol_bb_bandwidth_15", "vol_bb_pctb_15",
        "vol_bb_bandwidth_20", "vol_bb_pctb_20", "vol_bb_bandwidth_30", "vol_bb_pctb_30",
        "mr_bb_pctb_10", "mr_bb_pctb_15", "mr_bb_pctb_20", "mr_bb_pctb_30",
    ),
    "vol_realized": (
        "vol_atr_5", "vol_atr_7", "vol_atr_10", "vol_atr_14", "vol_atr_21",
        "vol_natr_7", "vol_natr_14", "vol_natr_21",
        "vol_garman_klass_10", "vol_garman_klass_20", "vol_garman_klass_30",
        "vol_parkinson_10", "vol_parkinson_20",
        "vol_hist_5", "vol_hist_10", "vol_hist_20", "vol_hist_30",
    ),
    "vol_range_spike": (
        "vol_range_spike_12", "vol_range_spike_24", "vol_range_spike_36",
        "vol_range_spike_48", "vol_range_spike_72", "vol_range_spike_96",
    ),
    "volume_flow": (
        "vol_obv", "vol_ad", "vol_cmf_10", "vol_cmf_14", "vol_cmf_20",
        "vol_mfi_7", "vol_mfi_10", "vol_mfi_14", "vol_mfi_21",
        "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_taker_buy_ratio_sma_10",
        "vol_taker_buy_ratio_sma_20", "vol_taker_buy_ratio_sma_50",
        "vol_volume_rel_5", "vol_volume_rel_10", "vol_volume_rel_20", "vol_volume_rel_50",
        "vol_volume_pctchg_5", "vol_volume_pctchg_10", "vol_volume_pctchg_20",
        "vol_vwap", "mr_dist_vwap",
    ),
    "mean_reversion": (
        "mr_zscore_10", "mr_zscore_20", "mr_zscore_30", "mr_zscore_50", "mr_zscore_100",
        "mr_rsi_extreme_7", "mr_rsi_extreme_14", "mr_rsi_extreme_21",
        "mr_pct_from_high_5", "mr_pct_from_high_10", "mr_pct_from_high_20",
        "mr_pct_from_high_50", "mr_pct_from_high_100",
        "mr_pct_from_low_5", "mr_pct_from_low_10", "mr_pct_from_low_20",
        "mr_pct_from_low_50", "mr_pct_from_low_100",
        "mr_dist_sma_10", "mr_dist_sma_20", "mr_dist_sma_50",
    ),
    "statistical": (
        "stat_return_1", "stat_return_3", "stat_return_5", "stat_return_10", "stat_return_20",
        "stat_autocorr_lag1", "stat_autocorr_lag5", "stat_autocorr_lag10",
        "stat_skew_10", "stat_skew_20", "stat_skew_30", "stat_skew_50",
        "stat_kurtosis_10", "stat_kurtosis_20", "stat_kurtosis_30", "stat_kurtosis_50",
    ),
    "regime_micro": (
        "hurst_100", "regime_momentum_signed_5d", "rev_extension_z_3", "vol_state_z_natr_30",
        "rev_halflife_50", "rev_vol_gate_signed",
        "ent_shannon_10", "ent_shannon_20", "ent_shannon_50", "ent_volume_20",
        "cusum_norm_1s", "cusum_norm_2s", "cusum_break_5",
        "basis_zscore_30", "long_short_zscore_30",
    ),
    "funding_oi_cross": (
        "funding_rate_zscore_30", "funding_rate_zscore_90", "btc_funding_rate_8h_impulse",
        "btc_funding_spread_30_90",
        "oi_delta_30_z90", "btc_oi_delta_5_z30", "oi_price_divergence_30",
        "eth_vs_btc_ret_ratio_30", "ltc_vs_btc_ret_ratio_30", "dot_vs_btc_ret_ratio_30",
    ),
    "interaction": (
        "interact_rsi_x_adx", "interact_stoch_x_adx", "interact_natr_x_adx",
        "interact_rsi_x_natr", "interact_ret1_x_natr", "interact_ret1_x_ret3",
    ),
}


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
        hi = edge + SUBPERIOD_DAYS
        edges.append((edge, hi))
        edge = hi
    return edges


def safe_ic(x: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < MIN_SUBPERIOD_N:
        return np.nan, int(m.sum())
    xv = x[m]
    if np.nanstd(xv) == 0:
        return np.nan, int(m.sum())
    ic, _ = spearmanr(xv, y[m])
    return float(ic), int(m.sum())


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)  # computed AFTER the IS filter; tail NaN-masks

    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]
    print(f"IS rows: {n_is}  span days: {round(ot_days.max() - ot_days.min())}  "
          f"sub-periods ({len(bounds)}): {sub_labels}")
    print(f"forward label: fixed_horizon log-return N={N_LABEL} (3d)")
    print("=" * 120)

    # ----- inventory: which candidate columns exist -----
    present_by_family, missing = {}, []
    all_candidates: list[str] = []
    for fam, cols in CANDIDATE_FAMILIES.items():
        present = [c for c in cols if c in df.columns]
        miss = [c for c in cols if c not in df.columns]
        present_by_family[fam] = present
        missing += miss
        for c in present:
            if c not in all_candidates:
                all_candidates.append(c)
    print("INVENTORY — candidate columns present per family:")
    for fam, present in present_by_family.items():
        print(f"  {fam:18s} ({len(present):2d}): {present}")
    if missing:
        print(f"  MISSING (not in parquet, skipped): {sorted(set(missing))}")
    in19 = set(ITER009_FEATURES)
    print(f"\nTotal distinct candidate columns: {len(all_candidates)}  "
          f"(of which {len(in19 & set(all_candidates))} are in the current 19-col set)")
    print("=" * 120)

    # ----- per-candidate sub-period IC stability -----
    rows = []
    for col in all_candidates:
        x_full = df[col].to_numpy(float)
        ic_full, n_full = safe_ic(x_full, y)
        sub_ics = []
        for lo, hi in bounds:
            m = (ot_days >= lo) & (ot_days < hi)
            ic_sp, n_sp = safe_ic(x_full[m], y[m])
            sub_ics.append(ic_sp if (n_sp >= MIN_SUBPERIOD_N) else np.nan)
        sub_arr = np.array(sub_ics, float)
        valid_sub = sub_arr[np.isfinite(sub_arr)]
        n_valid = len(valid_sub)
        if n_valid == 0 or not np.isfinite(ic_full):
            continue
        sign_ref = np.sign(ic_full) if ic_full != 0 else 1.0
        frac_same_sign = float(np.mean(np.sign(valid_sub) == sign_ref))
        mean_abs = float(np.mean(np.abs(valid_sub)))
        ic_disp = float(np.std(valid_sub, ddof=1)) if n_valid > 1 else 0.0
        worst_signed = float(np.min(valid_sub * sign_ref))  # most-adverse sub-period in ref direction
        recent_ic = next((v for v in reversed(sub_arr) if np.isfinite(v)), np.nan)
        recent_same_sign = bool(np.isfinite(recent_ic) and np.sign(recent_ic) == sign_ref)
        # STABILITY SCORE: consistent-sign AND non-trivial-magnitude. Penalize sign flips hard.
        stability_score = mean_abs * frac_same_sign
        rows.append(dict(
            feature=col,
            in_19col=col in in19,
            ic_full=round(ic_full, 4),
            n_full=n_full,
            n_subperiods=n_valid,
            frac_same_sign=round(frac_same_sign, 3),
            mean_abs_ic=round(mean_abs, 4),
            ic_dispersion=round(ic_disp, 4),
            worst_signed_ic=round(worst_signed, 4),
            recent_ic=round(recent_ic, 4) if np.isfinite(recent_ic) else np.nan,
            recent_same_sign=recent_same_sign,
            stability_score=round(stability_score, 5),
            **{f"ic_{sub_labels[i]}": (round(sub_ics[i], 4) if np.isfinite(sub_ics[i]) else np.nan)
               for i in range(len(bounds))},
        ))

    res = pd.DataFrame(rows).sort_values("stability_score", ascending=False).reset_index(drop=True)
    res.to_csv(OUTDIR / "subperiod_ic_stability.csv", index=False)

    # ----- report: 19-col baseline-to-beat on the stability metric -----
    print("CURRENT 19-COL SET — sub-period IC stability (the baseline-to-beat):")
    print(f"  {'feature':28s} {'ic_full':>8s} {'frac_sign':>9s} {'mean|IC|':>9s} "
          f"{'disp':>7s} {'worst±':>8s} {'recent':>8s} {'rec_ok':>6s} {'stab':>8s}")
    sub19 = res[res["in_19col"]].sort_values("stability_score", ascending=False)
    for _, r in sub19.iterrows():
        print(f"  {r['feature']:28s} {r['ic_full']:+8.4f} {r['frac_same_sign']:9.3f} "
              f"{r['mean_abs_ic']:9.4f} {r['ic_dispersion']:7.4f} {r['worst_signed_ic']:+8.4f} "
              f"{r['recent_ic']:+8.4f} {str(r['recent_same_sign']):>6s} {r['stability_score']:8.5f}")
    if len(sub19):
        print(f"\n  19-col SUMMARY: mean stability_score={sub19['stability_score'].mean():.5f}  "
              f"mean frac_same_sign={sub19['frac_same_sign'].mean():.3f}  "
              f"median frac_same_sign={sub19['frac_same_sign'].median():.3f}  "
              f"frac with all-6-same-sign={float((sub19['frac_same_sign'] >= 0.999).mean()):.3f}")

    print("\n" + "=" * 120)
    print("TOP 35 NEW candidates (NOT in 19-col) by STABILITY SCORE = mean|IC| * frac_same_sign:")
    print(f"  {'feature':28s} {'ic_full':>8s} {'frac_sign':>9s} {'mean|IC|':>9s} "
          f"{'disp':>7s} {'worst±':>8s} {'recent':>8s} {'rec_ok':>6s} {'stab':>8s}")
    new = res[~res["in_19col"]].head(35)
    for _, r in new.iterrows():
        print(f"  {r['feature']:28s} {r['ic_full']:+8.4f} {r['frac_same_sign']:9.3f} "
              f"{r['mean_abs_ic']:9.4f} {r['ic_dispersion']:7.4f} {r['worst_signed_ic']:+8.4f} "
              f"{r['recent_ic']:+8.4f} {str(r['recent_same_sign']):>6s} {r['stability_score']:8.5f}")

    # ----- the "fully sign-consistent" club: same sign in ALL valid sub-periods AND recent-OK -----
    full_n = max(r["n_subperiods"] for r in rows)
    club = res[(res["frac_same_sign"] >= 0.999) & (res["recent_same_sign"]) &
               (res["n_subperiods"] >= full_n - 0)]
    club = club.sort_values("stability_score", ascending=False)
    print("\n" + "=" * 120)
    print(f"ALL-SUB-PERIOD-SIGN-CONSISTENT CLUB (same IC sign in ALL {full_n} sub-periods AND "
          f"recent sub-period same sign):")
    print(f"  {'feature':28s} {'in19':>5s} {'ic_full':>8s} {'mean|IC|':>9s} {'disp':>7s} {'stab':>8s}")
    for _, r in club.iterrows():
        print(f"  {r['feature']:28s} {str(r['in_19col']):>5s} {r['ic_full']:+8.4f} "
              f"{r['mean_abs_ic']:9.4f} {r['ic_dispersion']:7.4f} {r['stability_score']:8.5f}")
    print(f"\n  CLUB size: {len(club)}  (in_19col: {int(club['in_19col'].sum())}, "
          f"NEW: {int((~club['in_19col']).sum())})")

    print(f"\nWrote: {OUTDIR / 'subperiod_ic_stability.csv'}  ({len(res)} candidates)")


if __name__ == "__main__":
    main()
