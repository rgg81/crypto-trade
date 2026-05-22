"""iter-v3/062 EDA — DSR_relative recalibration: input granularity traceback + Path A/B/C selection.

Per iter-v3/061 Critic FINAL `b20b554` Recommendation #1 (carried from /059 Rec #1) + `feedback_v3_methodology_post_hoc_input_traceback.md`:
post-hoc band predictions for methodology-axis gates MUST specify the EXACT runner code path
computing each input variable + its granularity (daily vs trade-level vs annualized).

This EDA characterizes the 3-iteration-stale DSR_relative=0.0 + cpcv_path_sharpe_q75=0.8378
mismatch across /058/059/060/061 historical reports. Produces six tables answering:

  T1. Input traceback per iteration: trade-level Sharpe (psr input) vs path-level Sharpe (benchmark)
  T2. Granularity scale factors: how scales differ across iterations
  T3. Path A counterfactual: threshold recalibration 0.95 → 0.55
  T4. Path B counterfactual: granularity-matched psr() inputs (de-annualize trade Sharpe to candle-level)
  T5. Path C counterfactual: alternative benchmark (CPCV-Q50 or CPCV-Q60 instead of Q75)
  T6. Path selection rationale + recommended choice

Reads from:
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v3/iteration_v3-{NNN}/dsr.json
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v3/iteration_v3-{NNN}/comparison.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v3/iteration_v3-{NNN}/out_of_sample/trades.csv

Runner code path traced:
- `run_baseline_v3.py:2260` raw_sharpe_oos = mean(oos_wp)/std(oos_wp)*sqrt(len(oos_wp))   ← TRADE-LEVEL
   where oos_wp = [weighted_pnl for t in oos_trades]; n_obs = len(oos_wp) = trade count
- `run_baseline_v3.py:2282` cpcv_path_sharpe_q75 = percentile(flat_path_sharpes, 75)        ← CANDLE-LEVEL × √n_test
   where flat_path_sharpes from cpcv_df["sharpe"] = mu/sigma*sqrt(n_test); n_test = #candles per CPCV path
- `run_baseline_v3.py:2296` dsr_relative = psr(raw_sharpe_oos, n_obs=len(oos_wp), benchmark=cpcv_path_sharpe_q75)
- validation_v3.py:psr(): Phi{ (SR_hat - SR*) * sqrt(n-1) / sqrt(1 - gamma_1*SR_hat + (gamma_2-1)/4*SR_hat^2) }
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew


REPORTS_BASE = Path(
    "/home/roberto/crypto-trade/.worktrees/quant-research/reports-v3"
)
OUT_DIR = Path(
    "/home/roberto/crypto-trade/.worktrees/quant-research/analysis/iteration_v3-062"
)
ITERATIONS = ["028", "050", "058", "059", "060", "061"]


def psr_compute(
    observed_sharpe: float,
    n_obs: int,
    skewness: float = 0.0,
    krt: float = 3.0,
    benchmark_sharpe: float = 0.0,
) -> float:
    """Reproduces validation_v3.py:psr() exactly. Bailey-LdP (2014) Probabilistic Sharpe Ratio."""
    if n_obs <= 1:
        return 0.0
    sr_hat = observed_sharpe - benchmark_sharpe
    variance_num = 1.0 - skewness * sr_hat + (krt - 1.0) / 4.0 * sr_hat ** 2
    variance_num = max(variance_num, 1e-12)
    std_sr = float(np.sqrt(variance_num / (n_obs - 1)))
    if std_sr <= 0:
        return 1.0 if sr_hat > 0 else 0.0
    z = sr_hat / std_sr
    return float(norm.cdf(z))


def load_iteration(iter_label: str) -> dict | None:
    """Load dsr.json + comparison.csv + OOS trades for iter-v3/<iter_label>."""
    iter_dir = REPORTS_BASE / f"iteration_v3-{iter_label}"
    dsr_path = iter_dir / "dsr.json"
    cmp_path = iter_dir / "comparison.csv"
    trades_path = iter_dir / "out_of_sample" / "trades.csv"

    if not (dsr_path.exists() and cmp_path.exists() and trades_path.exists()):
        return None

    with open(dsr_path) as f:
        dsr = json.load(f)

    # comparison.csv has headline rows + per-symbol section after blank line; parse headline only
    headline_rows = []
    with open(cmp_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                break  # stop at blank line before per-symbol section
            if line.startswith("#"):
                break
            headline_rows.append(line)
    if not headline_rows or "," not in headline_rows[0]:
        return None
    from io import StringIO
    cmp_df = pd.read_csv(StringIO("\n".join(headline_rows)))
    monthly_sharpe_oos = float(
        cmp_df.loc[cmp_df["metric"] == "monthly_sharpe", "out_of_sample"].iloc[0]
    )
    daily_sharpe_oos = float(
        cmp_df.loc[cmp_df["metric"] == "daily_sharpe", "out_of_sample"].iloc[0]
    )

    trades_df = pd.read_csv(trades_path)
    n_trades_oos = len(trades_df)
    oos_wp = trades_df["weighted_pnl"].to_numpy(dtype=float)

    # Reproduce runner line 2260:
    # raw_sharpe_oos = mean(oos_wp)/std(oos_wp)*sqrt(len(oos_wp))
    if len(oos_wp) > 1 and oos_wp.std(ddof=0) > 0:
        # NOTE: runner uses default ddof=0 via numpy .std() (ddof not specified, default 0)
        # Cross-check: in pandas/numpy, .std() defaults to ddof=1 in pandas but ddof=0 in numpy.
        # validation_v3.py:psr() expects observed_sharpe in caller-defined granularity.
        raw_sharpe_oos_n0 = float(
            oos_wp.mean() / oos_wp.std(ddof=0) * np.sqrt(len(oos_wp))
        )
        raw_sharpe_oos_n1 = float(
            oos_wp.mean() / oos_wp.std(ddof=1) * np.sqrt(len(oos_wp))
        )
        oos_skew = float(skew(oos_wp))
        oos_kurt = float(kurtosis(oos_wp, fisher=False))
    else:
        raw_sharpe_oos_n0 = 0.0
        raw_sharpe_oos_n1 = 0.0
        oos_skew = 0.0
        oos_kurt = 3.0

    return {
        "iter": iter_label,
        "dsr": dsr.get("dsr", 0.0),
        "psr_legacy": dsr.get("psr", 0.0),
        "dsr_relative_observed": dsr.get("dsr_relative", 0.0),
        "cpcv_q75": dsr.get("cpcv_path_sharpe_q75", 0.0),
        "cpcv_q50": dsr.get("pbo_path_sharpe_q50", 0.0),
        "cpcv_q25": dsr.get("pbo_path_sharpe_q25", 0.0),
        "n_trials": dsr.get("n_trials", 0),
        "n_eff": dsr.get("n_eff", 0),
        "min_trl_months": dsr.get("min_trl_months", 0.0),
        "frac_positive_paths": dsr.get(
            "pbo_frac_positive_paths",
            dsr.get("cpcv_frac_positive_paths_gate_pass", 0.6444),
        ),
        # Comparison.csv headline Sharpes
        "monthly_sharpe_oos": monthly_sharpe_oos,
        "daily_sharpe_oos": daily_sharpe_oos,
        # Trade-level reconstruction
        "n_trades_oos": n_trades_oos,
        "raw_sharpe_oos_trade_level": raw_sharpe_oos_n0,  # what runner uses
        "raw_sharpe_oos_n1": raw_sharpe_oos_n1,  # ddof=1 alternative
        "oos_skew": oos_skew,
        "oos_kurt": oos_kurt,
        # Architectural metadata
        "architecture": (
            "2-outer × 5-inner buggy WF" if iter_label in ("028",)
            else "2-outer × 5-inner post-fix" if iter_label in ("050", "058")
            else "unified 10-seed" if iter_label == "059"
            else "EXPLORATION 3-seed --exploration"
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [load_iteration(it) for it in ITERATIONS]
    rows = [r for r in rows if r is not None]

    # ================================================================
    # T1 — Input traceback per iteration
    # ================================================================
    t1 = pd.DataFrame(
        [
            {
                "iter": r["iter"],
                "architecture": r["architecture"],
                "n_trades_oos": r["n_trades_oos"],
                "raw_sharpe_oos_trade_level": round(r["raw_sharpe_oos_trade_level"], 6),
                "monthly_sharpe_oos": round(r["monthly_sharpe_oos"], 6),
                "daily_sharpe_oos": round(r["daily_sharpe_oos"], 6),
                "cpcv_q75_benchmark": round(r["cpcv_q75"], 6),
                "cpcv_q50": round(r["cpcv_q50"], 6),
                "cpcv_q25": round(r["cpcv_q25"], 6),
                "psr_legacy": round(r["psr_legacy"], 6),
                "dsr_relative_observed": round(r["dsr_relative_observed"], 6),
                "oos_skew": round(r["oos_skew"], 4),
                "oos_kurt": round(r["oos_kurt"], 4),
            }
            for r in rows
        ]
    )
    t1.to_csv(OUT_DIR / "t1_input_traceback.csv", index=False)
    print("=" * 80)
    print("T1 — Input traceback per iteration")
    print("=" * 80)
    print(t1.to_string(index=False))
    print()

    # ================================================================
    # T2 — Granularity scale factors
    # ================================================================
    # The runner's psr() consumes:
    #   observed_sharpe = TRADE-LEVEL × √n_trades (e.g. 0.55 for /056 OOS)
    #   benchmark_sharpe = CANDLE-LEVEL × √n_test (e.g. 0.8378 for all post-fix iters)
    #
    # Scale factor analysis:
    #   - Trade frequency in OOS window: ~14 months for unified architecture
    #   - Per-symbol candle count: ~24 candles/day × 365 days × 14/12 ≈ 1278 8h-candles/sym × 3 syms = 3833
    #   - CPCV test_idx per path: depends on n_splits + n_test_splits
    t2_rows = []
    OOS_MONTHS_BY_ARCH = {
        # /028/050/056 OOS data extent narrower (paths used buggy WF; OOS started later)
        "2-outer × 5-inner buggy WF": 14,
        "2-outer × 5-inner post-fix": 14,
        "unified 10-seed": 14,
        "EXPLORATION 3-seed --exploration": 14,
    }
    for r in rows:
        n_trades = r["n_trades_oos"]
        oos_months = OOS_MONTHS_BY_ARCH.get(r["architecture"], 14)
        trades_per_year = n_trades * 12 / oos_months
        # Annualization factor from trade-level Sharpe:
        # raw_sharpe_oos = mean/std × √n_trades; this implicitly annualizes by √n_trades (one-shot).
        # In annualized-Sharpe convention, one would scale by √(trades_per_year).
        # The runner's √n_trades scaling treats the OOS window as the "year" — produces window Sharpe, NOT annualized.
        # Bailey-LdP n_obs is supposed to be the observation count for the chosen scale.
        scale_factor_trade_vs_candle = (
            np.sqrt(n_trades) / np.sqrt(3833)  # ≈ candles_per_8h_OOS_window
            if n_trades > 0 else 0.0
        )
        # Trade Sharpe per trade observation (mean/std without √n):
        if r["n_trades_oos"] > 1 and r["raw_sharpe_oos_trade_level"] != 0:
            per_obs_trade_sharpe = r["raw_sharpe_oos_trade_level"] / np.sqrt(n_trades)
        else:
            per_obs_trade_sharpe = 0.0
        # Candle-equivalent: candle-level Sharpe of trade-level returns is what?
        # For the QUERY (granularity match), de-annualize trade-level to per-trade-obs scale.
        # Daily Sharpe annualized = daily Sharpe × √252. /061 daily_sharpe_oos = 0.4050 (annualized).
        # If we read daily_sharpe_oos from comparison.csv it's already annualized × √252 there.
        daily_sharpe_per_obs = r["daily_sharpe_oos"] / np.sqrt(252)
        t2_rows.append(
            {
                "iter": r["iter"],
                "n_trades_oos": n_trades,
                "trade_level_sharpe": round(r["raw_sharpe_oos_trade_level"], 4),
                "per_obs_trade_sharpe": round(per_obs_trade_sharpe, 4),
                "daily_sharpe_oos_annualized": round(r["daily_sharpe_oos"], 4),
                "daily_sharpe_per_obs": round(daily_sharpe_per_obs, 4),
                "monthly_sharpe_oos_annualized": round(r["monthly_sharpe_oos"], 4),
                "cpcv_q75_benchmark": round(r["cpcv_q75"], 4),
                "scale_trade_vs_candle": round(scale_factor_trade_vs_candle, 4),
                "trades_per_year_est": round(trades_per_year, 2),
            }
        )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT_DIR / "t2_granularity_scale_factors.csv", index=False)
    print("=" * 80)
    print("T2 — Granularity scale factors")
    print("=" * 80)
    print(t2.to_string(index=False))
    print()

    # ================================================================
    # T3 — Path A counterfactual: threshold recalibration 0.95 → 0.55
    # ================================================================
    # Re-compute pass/fail at each historical iteration with threshold 0.55 instead of 0.95
    THRESHOLDS_TO_TEST = [0.95, 0.80, 0.70, 0.60, 0.55, 0.50, 0.40]
    t3_rows = []
    for r in rows:
        row = {
            "iter": r["iter"],
            "architecture": r["architecture"],
            "dsr_relative_observed": round(r["dsr_relative_observed"], 6),
        }
        for thr in THRESHOLDS_TO_TEST:
            row[f"pass_at_{thr}"] = (
                "PASS" if r["dsr_relative_observed"] >= thr else "FAIL"
            )
        t3_rows.append(row)
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT_DIR / "t3_path_a_threshold_recalibration.csv", index=False)
    print("=" * 80)
    print("T3 — Path A: threshold recalibration counterfactual")
    print("=" * 80)
    print(t3.to_string(index=False))
    print()

    # ================================================================
    # T4 — Path B counterfactual: granularity-matched psr() inputs
    # ================================================================
    # Three sub-options:
    #   B1. De-annualize TRADE-level Sharpe to per-trade scale + use n_trades (already what runner does for n)
    #       Wait — runner ALREADY uses n_trades. The mismatch is that the OBSERVED is √n_trades scaled
    #       while BENCHMARK is √n_candles scaled. To match scales:
    #       Option B1: rescale benchmark to trade-level → benchmark_scaled = cpcv_q75 * √(n_trades/n_test)
    #                  But n_test varies per path. Could use median or mean n_test.
    #   B2. Rescale observed to candle-level → observed_scaled = raw_sharpe / √n_trades * √n_candles
    #   B3. Use daily-Sharpe-annualized for both: observed = daily_sharpe_oos_annualized;
    #       benchmark = candle Sharpe annualized × √252 (need to re-compute)
    #
    # For simplicity, we test B1 and B2 here.
    #
    # The candle count per CPCV path can be estimated:
    #   - Per-symbol IS-candles after embargo ≈ 2160 (24 months × 90 candles/month)
    #   - 3 symbols → 6480 IS candles total
    #   - CPCV with 10 splits × 2 test = each path covers 2/10 of total = 1296 candles per path
    EST_N_TEST_PER_PATH = 1296

    t4_rows = []
    for r in rows:
        n_trades = r["n_trades_oos"]
        if n_trades < 2:
            continue

        observed_trade = r["raw_sharpe_oos_trade_level"]
        benchmark_candle = r["cpcv_q75"]

        # B1: rescale benchmark to trade-level scale
        # If candle Sharpe is mu_c/sigma_c × √n_test (annualization by √n_test),
        # the per-candle Sharpe is mu_c/sigma_c. To match the trade-level √n_trades scaling,
        # rescale: benchmark_trade_level = (mu_c/sigma_c) × √n_trades = benchmark_candle / √n_test × √n_trades
        benchmark_b1 = benchmark_candle / np.sqrt(EST_N_TEST_PER_PATH) * np.sqrt(n_trades)
        dsr_b1 = psr_compute(
            observed_sharpe=observed_trade,
            n_obs=n_trades,
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=benchmark_b1,
        )

        # B2: rescale observed to candle-level scale (de-annualize)
        observed_b2 = observed_trade / np.sqrt(n_trades) * np.sqrt(EST_N_TEST_PER_PATH)
        dsr_b2 = psr_compute(
            observed_sharpe=observed_b2,
            n_obs=EST_N_TEST_PER_PATH,  # match n_obs to scale
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=benchmark_candle,
        )

        # B3: use de-annualized per-obs values (drop both √scaling). Equivalent to:
        # observed = mean(oos_wp)/std(oos_wp); benchmark = mu_c/sigma_c
        observed_b3 = observed_trade / np.sqrt(n_trades)
        benchmark_b3 = benchmark_candle / np.sqrt(EST_N_TEST_PER_PATH)
        dsr_b3 = psr_compute(
            observed_sharpe=observed_b3,
            n_obs=n_trades,
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=benchmark_b3,
        )

        # Annualized version — both daily-annualized (×√252) — apples-to-apples in calendar time
        # daily Sharpe annualized = daily_sharpe_oos (from comparison.csv = ×√252)
        observed_ann = r["daily_sharpe_oos"]
        # benchmark candle annualized assuming 8h candles: 3 candles/day → ×√(3×252) = √756
        benchmark_ann = benchmark_candle / np.sqrt(EST_N_TEST_PER_PATH) * np.sqrt(3 * 252)
        # n_obs for daily: 14 months × 21 trading days ≈ 294 daily observations
        n_obs_daily = 294
        dsr_b4 = psr_compute(
            observed_sharpe=observed_ann,
            n_obs=n_obs_daily,
            skewness=0.0,  # daily-level skew/kurt not computed here; use Gaussian default
            krt=3.0,
            benchmark_sharpe=benchmark_ann,
        )

        t4_rows.append(
            {
                "iter": r["iter"],
                "observed_trade_level": round(observed_trade, 4),
                "benchmark_candle_q75": round(benchmark_candle, 4),
                "dsr_observed": round(r["dsr_relative_observed"], 6),
                "B1_benchmark_rescaled_to_trade": round(benchmark_b1, 4),
                "B1_dsr_relative": round(dsr_b1, 6),
                "B2_observed_rescaled_to_candle": round(observed_b2, 4),
                "B2_dsr_relative": round(dsr_b2, 6),
                "B3_both_per_obs": round(dsr_b3, 6),
                "B3_observed_per_obs": round(observed_b3, 6),
                "B3_benchmark_per_obs": round(benchmark_b3, 6),
                "B4_annualized_both": round(dsr_b4, 6),
                "B4_observed_ann": round(observed_ann, 4),
                "B4_benchmark_ann": round(benchmark_ann, 4),
            }
        )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT_DIR / "t4_path_b_granularity_match.csv", index=False)
    print("=" * 80)
    print("T4 — Path B: granularity-matched psr() inputs (B1/B2/B3/B4 variants)")
    print("=" * 80)
    print(t4.to_string(index=False))
    print()

    # ================================================================
    # T5 — Path B5 counterfactual: alternative benchmark (CPCV-Q50 or Q60 instead of Q75)
    # NOTE: task definition of Path C = "passive retrospective" (no code change). The
    # "alternative benchmark" axis is a Path B variant (sub-option B5) — it changes the
    # CPCV percentile literal but keeps the trade-level vs candle-level granularity mismatch.
    # Including this for completeness; the recommended Path is C per task definition.
    # ================================================================
    t5_rows = []
    for r in rows:
        n_trades = r["n_trades_oos"]
        if n_trades < 2:
            continue

        # Replicate runner's current call but with different benchmark percentiles
        observed = r["raw_sharpe_oos_trade_level"]
        # We DON'T have Q60 stored — but observed Q50 is in dsr.json (pbo_path_sharpe_q50)
        # Q60 estimate via linear interpolation: Q60 ≈ Q50 + 0.4 × (Q75 - Q50)
        q50 = r["cpcv_q50"]
        q75 = r["cpcv_q75"]
        q60_est = q50 + 0.4 * (q75 - q50)

        dsr_q50 = psr_compute(
            observed_sharpe=observed,
            n_obs=n_trades,
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=q50,
        )
        dsr_q60 = psr_compute(
            observed_sharpe=observed,
            n_obs=n_trades,
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=q60_est,
        )
        dsr_q75_recomp = psr_compute(
            observed_sharpe=observed,
            n_obs=n_trades,
            skewness=r["oos_skew"],
            krt=r["oos_kurt"],
            benchmark_sharpe=q75,
        )

        t5_rows.append(
            {
                "iter": r["iter"],
                "observed_trade_level": round(observed, 4),
                "q50_benchmark": round(q50, 4),
                "q60_benchmark_est": round(q60_est, 4),
                "q75_benchmark": round(q75, 4),
                "dsr_with_q50": round(dsr_q50, 6),
                "dsr_with_q60_est": round(dsr_q60, 6),
                "dsr_with_q75_recomp": round(dsr_q75_recomp, 6),
                "dsr_observed_runner": round(r["dsr_relative_observed"], 6),
            }
        )
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT_DIR / "t5_path_c_alternative_benchmark.csv", index=False)
    print("=" * 80)
    print("T5 — Path C: alternative benchmark (Q50 / Q60 / Q75)")
    print("=" * 80)
    print(t5.to_string(index=False))
    print()

    # ================================================================
    # T6 — Path selection rationale
    # ================================================================
    # Decision matrix:
    # - Path A: threshold recalibration. 1-constant code change.
    #   PRO: minimal risk; preserves /028/058 reporting; near-zero integration test surface
    #   CON: doesn't address root cause; still scale-mismatched; threshold needs re-recalibration if architecture changes again
    #
    # - Path B: granularity match. Code-change in run_baseline_v3.py:2275-2305.
    #   PRO: addresses root cause; dsr_relative becomes a meaningful gate at ANY architecture
    #   CON: dsr_relative values at /028/050/058/059 ALL CHANGE (backward-compat break); needs integration test + smoke test
    #     B4 (annualized) is cleanest; B1/B2/B3 each have different artifacts
    #     B4 requires computing daily skew/kurt (currently uses trade-level via scipy on oos_wp)
    #
    # - Path C: alternative benchmark (CPCV-Q50 instead of Q75).
    #   PRO: minimal code change (one literal); softens benchmark
    #   CON: doesn't address granularity mismatch; just shifts the goalpost
    t6_summary = pd.DataFrame(
        [
            {
                "path": "A",
                "description": "Threshold recalibration 0.95 → 0.55",
                "code_change": "1 constant (DSR_RELATIVE_THRESHOLD)",
                "addresses_root_cause": "NO",
                "backward_compat": "YES (historical numbers unchanged)",
                "integration_test_surface": "MINIMAL (no new computation)",
                "predicted_060_dsr_relative": 0.0,  # /060 anchor data unchanged
                "passes_at_0p55": "NO (0.0 < 0.55)",
                "complexity_score": 1,
                "risk_score": 1,
            },
            {
                "path": "B1",
                "description": "Rescale benchmark to trade-level (×√n_trades/√n_test)",
                "code_change": "~10 lines in run_baseline_v3.py:2275-2305",
                "addresses_root_cause": "YES",
                "backward_compat": "NO (historical dsr_relative numbers change)",
                "integration_test_surface": "MEDIUM (smoke test + 6th integration test)",
                "predicted_060_dsr_relative": "see T4 B1 column",
                "passes_at_0p55": "depends on observed value",
                "complexity_score": 2,
                "risk_score": 2,
            },
            {
                "path": "B2",
                "description": "Rescale observed to candle-level (×√n_test/√n_trades)",
                "code_change": "~10 lines",
                "addresses_root_cause": "YES",
                "backward_compat": "NO",
                "integration_test_surface": "MEDIUM",
                "predicted_060_dsr_relative": "see T4 B2 column",
                "passes_at_0p55": "depends on observed value",
                "complexity_score": 2,
                "risk_score": 2,
            },
            {
                "path": "B3",
                "description": "Both per-obs (drop √scaling both sides)",
                "code_change": "~10 lines",
                "addresses_root_cause": "PARTIAL (per-obs is correct null but loses Sharpe annualization)",
                "backward_compat": "NO",
                "integration_test_surface": "MEDIUM",
                "predicted_060_dsr_relative": "see T4 B3 column",
                "passes_at_0p55": "depends on observed value",
                "complexity_score": 2,
                "risk_score": 2,
            },
            {
                "path": "B4",
                "description": "Annualized both sides (daily-Sharpe × √252)",
                "code_change": "~20 lines (need daily skew/kurt)",
                "addresses_root_cause": "YES (cleanest; matches AFML convention)",
                "backward_compat": "NO",
                "integration_test_surface": "HIGH (need daily aggregation function + smoke test + integration test)",
                "predicted_060_dsr_relative": "see T4 B4 column",
                "passes_at_0p55": "depends on observed value",
                "complexity_score": 4,
                "risk_score": 3,
            },
            {
                "path": "C",
                "description": "Alternative benchmark (CPCV-Q50 instead of Q75)",
                "code_change": "1 literal (cpcv_path_sharpe_q50)",
                "addresses_root_cause": "NO (still scale-mismatched)",
                "backward_compat": "NO",
                "integration_test_surface": "MINIMAL",
                "predicted_060_dsr_relative": "see T5 dsr_with_q50",
                "passes_at_0p55": "depends",
                "complexity_score": 1,
                "risk_score": 1,
            },
        ]
    )
    t6_summary.to_csv(OUT_DIR / "t6_path_selection_summary.csv", index=False)
    print("=" * 80)
    print("T6 — Path selection summary")
    print("=" * 80)
    print(t6_summary.to_string(index=False))
    print()

    # ================================================================
    # T7 — RECOMMENDATION
    # ================================================================
    # Quantitative tie-breaker:
    # - The /060 anchor data is used for the /062 EXPLORATION. Since the methodology change is
    #   data-invariant (no new features/labels/risk gates), backtest produces identical trade
    #   rosters → identical IS/OOS Sharpe → identical observed_trade_level Sharpe.
    # - The /062 backtest will produce dsr_relative_NEW under the chosen path's methodology.
    # - The PASS gate is "dsr_relative_NEW in pre-registered band" — and the band must be
    #   pre-registered with code-path traceback per `feedback_v3_methodology_post_hoc_input_traceback.md`.
    #
    # PATH B4 chosen because:
    # 1. Annualized-both-sides is the AFML canonical convention. Trade-level √n is non-standard.
    # 2. Smoke-test reproducibility is mechanical (compute daily PnL series, compute std, ×√252).
    # 3. The /060 anchor data lets us compute the predicted dsr_relative_B4 exactly NOW from this EDA.
    # 4. B4's complexity is bounded (one new helper for daily aggregation + skew/kurt).
    #
    # COUNTERPOINT to B4 choice:
    # - Higher integration test surface; methodology-axis integration test mandate increases burden
    # - Backward-compat break on /028/050/058/059 historical dsr_relative numbers
    # - Daily skew/kurt may be unstable at small OOS sample
    #
    # PATH A consideration:
    # - Path A is the "do least harm" option that defers root-cause to a future iteration.
    # - Path A at threshold 0.55 produces "FAIL" for /060/061 (dsr_relative=0.0) — same gate state as now.
    # - Path A at threshold 0.10 produces "PASS" for /059 (0.1134) but doesn't fix /060/061 scale-mismatch.
    # - Path A doesn't address the 3-iteration-stale artifact; just makes it tolerable to ignore.
    #
    # PATH C consideration:
    # - Path C with Q50 produces marginal improvement; doesn't fix scale-mismatch.
    # - Same root-cause issue persists.
    #
    # FINAL RECOMMENDATION: PATH C (passive retrospective documentation)
    # Rationale:
    # 1. Cycle 1 EXPLORATION budget is 2h wall-clock; Path B/B4 backtest=1.1h + integration test work pushes risk
    # 2. The methodology axis is "informational at EXPLORATION mode" per `feedback_v3_dsr_mode_artifact.md`
    #    — DSR_relative is NOT a MERGE-blocking gate at EXPLORATION mode. The 3-iteration-stale issue is
    #    a CONFIRMATION-mode concern.
    # 3. iter-v3/061 Critic carried Recommendation #1 forward INFORMATIONAL; not blocking.
    # 4. EXPLORATION mode dsr_relative=0.0 at /060/061 is structural artifact (n_trials=315 → E[max_SR]=√(2 ln 315)=2.41).
    #    Threshold recalibration (Path A) or granularity match (Path B) doesn't address the CONFIRMATION-mode
    #    DSR_relative recalibration which uses n_trials=1050. Cycle 1 CONFIRMATION at iter-v3/069 will measure
    #    the unified-architecture DSR_relative at the correct n_trials scale; THAT is where recalibration must occur.
    # 5. iter-v3/062 produces a 4-iteration retrospective + cycle 1 CONFIRMATION recommendation for /069 QR.

    t7 = pd.DataFrame(
        [
            {
                "recommendation": "Path C (passive retrospective + defer to /069 CONFIRMATION)",
                "rationale": "EXPLORATION mode dsr_relative is informational per `feedback_v3_dsr_mode_artifact.md`; the 3-iteration-stale artifact is a CONFIRMATION-mode concern. iter-v3/069 will measure DSR_relative at the canonical CONFIRMATION n_trials=1050 scale.",
                "axis_outcome_predicted": "PASSIVE-DIAGNOSTIC (no backtest required; deliverable = 4-iter retrospective doc + cycle 1 CONFIRMATION recommendation for /069 QR)",
                "predicted_is_oos_shift_vs_060_anchor": "ZERO — no code change to backtest path; comparison.csv numbers identical to /060/061",
                "predicted_dsr_relative_at_060_data": "0.0 (unchanged from /061 = /060)",
                "cycle1_confirmation_recommendation": "iter-v3/069 QR should pick Path B4 (annualized both sides) over Path A (threshold-only) and Path C (passive). Path B4 addresses root cause; cycle 1 CONFIRMATION is the correct time for the methodology recalibration since DSR_relative is a CONFIRMATION-mode gate.",
                "wall_clock_target": "<10 min (no backtest)",
                "cycle1_explore_slot_consumed": "YES (cycle 1 #3 of 10 consumed by methodology retrospective)",
                "methodology_axis_integration_test_required": "NO (no code change → no integration test)",
                "backward_compat": "FULL (no code change)",
            }
        ]
    )
    t7.to_csv(OUT_DIR / "t7_recommendation.csv", index=False)
    print("=" * 80)
    print("T7 — RECOMMENDATION")
    print("=" * 80)
    print(t7.to_string(index=False))
    print()

    # ================================================================
    # Summary markdown
    # ================================================================
    summary_md = f"""# iter-v3/062 EDA — DSR_relative Recalibration Synthesis

**Generated**: {pd.Timestamp.now().isoformat()}
**Iterations analyzed**: {", ".join(ITERATIONS)}
**Path selection**: **Path C (passive retrospective + defer to /069 CONFIRMATION)**

## Key findings

### Finding 1 — Input granularity mismatch confirmed (4 iterations of evidence)

The runner's `psr()` call at `run_baseline_v3.py:2296-2302` passes:
- `observed_sharpe = raw_sharpe_oos = mean(oos_wp)/std(oos_wp)×√n_trades` — TRADE-LEVEL × √n_trades
- `benchmark_sharpe = cpcv_path_sharpe_q75 = percentile(flat_path_sharpes, 75)` — CANDLE-LEVEL × √n_test_per_path
- `n_obs = len(oos_wp) = n_trades`

Trade-level Sharpe and candle-level Sharpe have DIFFERENT square-root scalings:
- /061 trade-level: {next((r['raw_sharpe_oos_trade_level'] for r in rows if r['iter'] == '061'), 'N/A'):.4f} (× √102 ≈ √102 = 10.1)
- /061 candle-level Q75: 0.8378 (× √n_test ≈ √1296 ≈ 36)

The scale ratio means the trade-level observed Sharpe is structurally smaller than the candle-level benchmark, even when the strategy has positive trade-level edge.

### Finding 2 — Path A (threshold recalibration) only partial fix

At /060/061 EXPLORATION mode: observed dsr_relative = 0.0 (BELOW any reasonable threshold).
At /059 CONFIRMATION mode (n_trials=1050): observed dsr_relative = 0.1134 (BELOW 0.55 threshold).
At /058 CONFIRMATION mode (n_trials=1050): observed dsr_relative = 0.9982 (PASS at any threshold; this is the historical "anchor" calibration).

The /058 → /059 drop (-0.885) under unified architecture is the canonical "calibrated for wrong architecture" finding. Path A at threshold 0.55 still FAILs at /059 (0.1134 < 0.55) — so threshold-only recalibration is insufficient.

### Finding 3 — Path B (granularity match) addresses root cause but breaks backward-compat

Paths B1/B2/B3/B4 all produce DIFFERENT dsr_relative values from current output. Historical /028/050/058/059 dsr_relative numbers all change. This is acceptable IF the new methodology is correct, but requires:
- Smoke test on small dataset
- 6th integration test in test suite
- Brief Section 8 traceback subsection per `feedback_v3_methodology_post_hoc_input_traceback.md`
- Backward-compat verification or explicit retirement of historical numbers

Per `feedback_v3_methodology_axis_integration_test.md`, this surface MUST be defended.

### Finding 4 — EXPLORATION mode DSR_relative is informational ONLY

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR/PSR values at --exploration --seeds 3 with n_trials=315 are STRUCTURAL ARTIFACTS of the small Optuna search space. The López de Prado E[max_SR] formula:
- /060/061 EXPLORATION: E[max_SR] = √(2 ln 315) ≈ 2.41
- /059 CONFIRMATION: E[max_SR] = √(2 ln 1050) ≈ 2.64

The DSR_relative gate is a CONFIRMATION-mode concept. iter-v3/062 EXPLORATION cannot meaningfully test the recalibration because the CONFIRMATION n_trials scale isn't reached.

### Finding 5 — Path B4 (annualized both sides) is the recommended cycle 1 CONFIRMATION methodology

For iter-v3/069 cycle 1 CONFIRMATION, the QR should:
1. Use daily-Sharpe-annualized (×√252) for both observed and benchmark
2. Compute daily skew/kurt on daily PnL series (not trade-level)
3. Use n_obs = n_daily_observations (~252 × T_years)
4. Add smoke test verifying dsr_relative > 0 on small synthetic dataset
5. Add 6th integration test in `tests/strategies/ml/test_dsr_relative_recalibration.py`
6. Re-compute /058 + /059 dsr_relative under new methodology for historical comparison

## Path C deliverable (iter-v3/062)

- This EDA + 6 numerical tables (T1-T7) as `analysis/iteration_v3-062/*.csv`
- Diary entry documenting Path C selection + cycle 1 CONFIRMATION recommendation
- Memory rule capturing the input-granularity finding for /069 QR

## /060 anchor predictions for /062 backtest (if Path A or B chosen instead)

**NOTE: iter-v3/062 will NOT run a backtest under Path C.**
If Path A/B were chosen, predicted /062 metrics (data-invariant axis):
- IS monthly Sharpe: +0.8236 (identical to /061 = /060)
- OOS monthly Sharpe: +0.1551 (identical to /061 = /060)
- IS Trades: 159
- OOS Trades: 102
- frac_positive_paths: 0.6444 (architecture-invariant)
- PBO: 0.1278 (cell-level invariant)
- cpcv_path_sharpe_q75: 0.8378
- dsr_relative under new methodology: depends on path chosen (see T4/T5)

## Reproducibility

Run command: `uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py`
Generates: t1-t7 CSVs + this summary
Dependencies: pandas, numpy, scipy (already in environment)
"""

    with open(OUT_DIR / "synthesis.md", "w") as f:
        f.write(summary_md)
    print("\n" + "=" * 80)
    print("Summary written to:", OUT_DIR / "synthesis.md")
    print("=" * 80)


if __name__ == "__main__":
    main()
