"""iter-v1/043 EDA — LINK-only trend-scanning specialist isolation.

Anchor: /036 LINK+DOT trend-scan specialist (OOS Sharpe +1.7465, 105 trades, 54.3% WR).
LINK-only subset of /036 OOS: 52 trades, +108.9066 net PnL%, 55.8% WR.

Question: does isolating LINK from DOT preserve the per-cohort lift, or is the
LINK+DOT pairing load-bearing for the +1.7465 headline?

Method: read /036 trades.csv, extract LINK subset, compute monthly Sharpe at
LINK-only weight (no diversification across DOT), then predict /043 OOS Sharpe
under three regression scenarios (full preservation / partial / refutation).

Cross-reference: /018 LINK-only with triple-barrier σ_t (40-feature pruned set,
NOT trend-scanning, NOT 44-feature pruned set) achieved OOS Sharpe +0.9789 at
48 trades / 50.0% WR / +53.80 PnL%.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def load_036_link_oos() -> pd.DataFrame:
    t = pd.read_csv("reports-v1/iteration_v1-036/out_of_sample/trades.csv")
    link = t[t.symbol == "LINKUSDT"].copy()
    link["close_dt"] = pd.to_datetime(link["close_time"], unit="ms")
    link["ym"] = link["close_dt"].dt.to_period("M")
    return link


def link_only_monthly_sharpe(link: pd.DataFrame) -> dict:
    """Compute LINK-only OOS monthly Sharpe from /036 trade roster.

    NOTE: /036 portfolio Sharpe (+1.7465) is computed at PORTFOLIO daily PnL
    level (LINK + DOT combined), so we cannot simply 'extract LINK Sharpe' from
    /036's portfolio reports. We reconstruct LINK-only monthly Sharpe by
    aggregating LINK trades at monthly cadence and applying sqrt(12)
    annualization — the same convention reports/comparison.csv uses for the
    'sharpe' metric in monthly OOS regime (see run_baseline_v1.py).
    """
    monthly = link.groupby("ym").net_pnl_pct.agg(["sum", "count"]).reset_index()
    monthly.columns = ["ym", "pnl_pct", "n_trades"]
    mean_m = monthly.pnl_pct.mean()
    std_m = monthly.pnl_pct.std(ddof=1)
    sharpe_monthly = (mean_m / std_m) * np.sqrt(12) if std_m > 0 else float("nan")
    return {
        "n_months": len(monthly),
        "mean_monthly_pnl_pct": mean_m,
        "std_monthly_pnl_pct": std_m,
        "link_only_monthly_sharpe": sharpe_monthly,
        "total_pnl_pct": link.net_pnl_pct.sum(),
        "n_trades": len(link),
        "win_rate": (link.net_pnl_pct > 0).mean(),
        "monthly_table": monthly,
    }


def reference_036_portfolio() -> dict:
    cmp = pd.read_csv("reports-v1/iteration_v1-036/comparison.csv")
    cmp_map = dict(zip(cmp.metric, cmp.out_of_sample))
    return {
        "036_oos_sharpe": float(cmp_map["sharpe"]),
        "036_oos_trades": int(float(cmp_map["total_trades"])),
        "036_oos_win_rate": cmp_map["win_rate"],
        "036_oos_max_dd": cmp_map["max_drawdown"],
    }


def reference_018_link_only() -> dict:
    """/018 LINK-only with triple-barrier σ_t (NOT trend-scanning).

    Substrate differs from /043 in TWO ways:
      1. Label mode: σ_t triple-barrier vs trend-scanning
      2. Feature set: 40 cols pruned (no regime_momentum_signed_5d) vs 44 cols
    So /018 is a directional precedent only, not a numerical anchor.
    """
    cmp = pd.read_csv("reports-v1/iteration_v1-018/comparison.csv")
    cmp_map = dict(zip(cmp.metric, cmp.out_of_sample))
    return {
        "018_oos_sharpe": float(cmp_map["sharpe"]),
        "018_oos_trades": int(float(cmp_map["total_trades"])),
        "018_oos_win_rate": cmp_map["win_rate"],
        "018_oos_net_pnl_pct": float(cmp_map["total_net_pnl"]),
    }


def predict_043(link_subset: dict, ref_036: dict, ref_018: dict) -> dict:
    """Predict /043 OOS Sharpe band under three modal scenarios.

    The LINK-only subset extracted from /036's portfolio has 52 trades but only
    one symbol's variance — so daily/monthly volatility is HIGHER than the
    LINK+DOT portfolio (no DOT-diversification damping). Naive expectation:
    LINK-only Sharpe < LINK+DOT pooled Sharpe at same per-symbol PnL because
    DIVERSIFICATION term is removed from denominator.

    Three scenarios:
      (A) LOAD-BEARING-LINK: Optuna at LINK-only finds CLEANER trajectory than
          when forced to co-optimize with DOT signal. /018 precedent (LINK-only
          σ_t Sharpe +0.98 vs LINK-in-pool +0.34, Δ +0.64) supports this.
          LINK-only trend-scan Sharpe regresses HIGHER than LINK subset implied
          by diversification analysis, possibly within [/036 portfolio − 0.30,
          /036 portfolio + 0.30] = [+1.45, +2.05].
      (B) PAIRING-MATTERS: DOT trades co-occur with LINK trades at similar
          regimes (small-cap-trend-persistent); their joint variance is
          ANTI-correlated periods so portfolio σ < single-σ. Removing DOT raises
          σ, LINK-only Sharpe drops vs /036. Band: [+0.80, +1.40].
      (C) LINK-DEPENDS-ON-DOT: LINK trend-scan signal needs DOT's regime
          correlation for robustness; isolating LINK exposes noise. NEG band:
          [-0.50, +0.80].
    """
    # LINK-only intrinsic Sharpe from /036 trade roster (52 trades over OOS)
    link_intrinsic_sharpe = link_subset["link_only_monthly_sharpe"]

    # Modal band for /043 prediction. The intrinsic Sharpe is the LOAD-BEARING
    # anchor — but Optuna trajectory at single-seed will drift +/− 0.30 around
    # this from /036's value (different optima when objective is LINK-only).
    pred_central = link_intrinsic_sharpe
    pred_low = link_intrinsic_sharpe - 0.40  # ENSEMBLE_SIZE 5→3 + DOT-correlation removal
    pred_high = link_intrinsic_sharpe + 0.30  # cleaner Optuna at single-cohort

    # Probability weighting (subjective Bayesian prior on three modal regimes)
    # Anchors: /018 precedent (PROMISING-CLEAN at LINK-only Δ +0.16 vs LINK-in-pool;
    # /035→/036 transition where pool→2-cohort PRESERVED bimodal signal);
    # ensemble shrinkage 5→3 + DOT removal cost.
    return {
        "link_intrinsic_oos_sharpe_from_036_subset": link_intrinsic_sharpe,
        "036_anchor_portfolio_sharpe": ref_036["036_oos_sharpe"],
        "delta_intrinsic_vs_036": link_intrinsic_sharpe - ref_036["036_oos_sharpe"],
        "043_prediction_central": pred_central,
        "043_prediction_band_low": pred_low,
        "043_prediction_band_high": pred_high,
        "043_delta_vs_036_central": pred_central - ref_036["036_oos_sharpe"],
        "scenario_A_load_bearing_link_prob": 0.20,
        "scenario_A_band": "[+1.45, +2.05]",
        "scenario_B_pairing_matters_prob": 0.55,
        "scenario_B_band": "[+0.80, +1.40]",
        "scenario_C_link_depends_on_dot_prob": 0.25,
        "scenario_C_band": "[-0.50, +0.80]",
    }


def main():
    link = load_036_link_oos()
    link_subset = link_only_monthly_sharpe(link)
    ref_036 = reference_036_portfolio()
    ref_018 = reference_018_link_only()
    pred = predict_043(link_subset, ref_036, ref_018)

    print("=" * 72)
    print("iter-v1/043 EDA — LINK-only trend-scanning specialist isolation")
    print("=" * 72)
    print()

    print("--- /036 LINK-only subset (from portfolio trades.csv, OOS) ---")
    print(f"  n_trades:                  {link_subset['n_trades']}")
    print(f"  win_rate:                  {link_subset['win_rate']*100:.1f}%")
    print(f"  total_net_pnl_pct:         {link_subset['total_pnl_pct']:+.4f}")
    print(f"  n_months:                  {link_subset['n_months']}")
    print(f"  mean_monthly_pnl_pct:      {link_subset['mean_monthly_pnl_pct']:+.4f}")
    print(f"  std_monthly_pnl_pct:       {link_subset['std_monthly_pnl_pct']:.4f}")
    print(f"  LINK-only monthly Sharpe:  {link_subset['link_only_monthly_sharpe']:+.4f}")
    print()
    print(link_subset["monthly_table"].to_string(index=False))
    print()

    print("--- /036 portfolio reference (LINK+DOT trend-scan, OOS) ---")
    for k, v in ref_036.items():
        print(f"  {k}: {v}")
    print()

    print("--- /018 LINK-only σ_t triple-barrier reference (40-col, OOS) ---")
    for k, v in ref_018.items():
        print(f"  {k}: {v}")
    print()

    print("--- /043 PREDICTION ---")
    for k, v in pred.items():
        if isinstance(v, float):
            print(f"  {k}: {v:+.4f}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
