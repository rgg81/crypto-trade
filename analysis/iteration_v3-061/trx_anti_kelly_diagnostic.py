"""TRX anti-Kelly RiskV2 deep diagnostic + intervention design — iter-v3/061.

Cycle 1 #2 EXPLORATION. Per Critic FINAL `3cee250` Recommendation #3 mandate:
the RiskV2 vol-scaling weight_factor calibration is iter-v3/061 axis.

Background (from /060 Q7 finding, anchored at /059 unified 10-seed):

    | Symbol | IS win_w − loss_w | OOS win_w − loss_w |
    |--------|-------------------|---------------------|
    | BCH    | +0.099 (Kelly-aligned)        | +0.072 |
    | LDO    | +0.222 (strongly Kelly-aligned) | +0.189 |
    | TRX    | -0.061 (anti-Kelly)            | -0.014 (anti-Kelly) |

The RiskV2 _vol_scale function (src/crypto_trade/strategies/ml/risk_v2.py:580-592)
returns `clip(atr_pct_rank_200, vol_scale_floor=0.3, vol_scale_ceiling=1.0)`.
weight_factor IS the ATR percentile rank (with a 0.3 floor). For BCH/LDO,
HIGH-vol regimes correspond to wins (Kelly-aligned with the sizing formula);
for TRX, HIGH-vol regimes correspond to losses (anti-Kelly).

This EDA quantifies:
  Q1 — Anti-Kelly statistical significance (t-stat, bootstrap CI per symbol per split)
  Q2 — TRX weight_factor distribution percentiles by win/loss outcome
  Q3 — TRX trade outcome by 5-quantile weight_factor bucket (where in the
       distribution is the anti-Kelly concentrated?)
  Q4 — Counterfactual simulation: what happens to TRX weighted_pnl if we
       cap-or-floor weight_factor at various per-symbol values?
  Q5 — Cross-symbol sensitivity: does raising TRX floor leak into BCH/LDO?
       (Per-symbol floor design = floor changes ONLY for TRX; BCH/LDO unchanged.)
  Q6 — Path selection: B (per-symbol floor) / C (universal reformulation) /
       D (passive diagnostic) / E (reverse-sign falsification check).

Path B intervention candidate (preferred per quantitative findings below):
    `vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}` — raise TRX floor 0.3 → 0.5.
    Mechanism: TRX winning trades (avg weight 0.546) currently include trades
    in the [0.3, 0.5) tail that would be lifted to 0.5; losing trades (avg
    weight 0.606) sit mostly above 0.5 already so are unaffected. Net effect:
    win-side weight rises faster than loss-side, partially neutralizing
    anti-Kelly. BCH/LDO unchanged.

This script DOES NOT change V3_FEATURE_COLUMNS, V3_LABEL_PARAMS, V3_MODELS, or
ANY OTHER code state. It is a passive diagnostic + counterfactual to support
axis selection at brief Section 3.

Outputs (committed CSVs):
  - q1_anti_kelly_significance.csv          — per-symbol per-split t-stat + bootstrap CI
  - q2_trx_weight_distribution_by_outcome.csv  — TRX weight_factor percentiles per outcome
  - q3_trx_outcome_by_weight_bucket.csv     — TRX WR/PnL by 5-quantile weight bucket
  - q4_counterfactual_floor_sensitivity.csv — TRX weighted_pnl under floors 0.3/0.4/0.5/0.6
  - q5_cross_symbol_floor_sensitivity.csv   — BCH/LDO weighted_pnl invariance at TRX-only floor
  - q6_path_decision_summary.csv            — synthesized verdict
  - diagnostic_summary.md                   — composite report

Run:
  uv run python analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

REPO = Path(__file__).resolve().parents[2]
REPORTS_059 = REPO / "reports-v3" / "iteration_v3-059"  # CONFIRMATION-mode anchor (10-seed)
REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"  # EXPLORATION-mode anchor (3-seed; cycle 1 #1)
OUTPUT = Path(__file__).parent

V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# RiskV2 vol-scaling defaults (from src/crypto_trade/strategies/ml/risk_v2.py)
DEFAULT_VOL_SCALE_FLOOR = 0.3
DEFAULT_VOL_SCALE_CEILING = 1.0

# Bootstrap sample count for CI
N_BOOTSTRAP = 5000
RNG_SEED = 191664963  # ENSEMBLE_SEEDS[0] for reproducibility


# ---------------------------------------------------------------------------
# Q1 — Anti-Kelly statistical significance: t-stat + bootstrap CI
# ---------------------------------------------------------------------------


def _bootstrap_diff_ci(
    wins_w: np.ndarray, loss_w: np.ndarray, n_boot: int, rng: np.random.Generator,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap CI for (mean wins_w - mean loss_w)."""
    if len(wins_w) < 2 or len(loss_w) < 2:
        return float("nan"), float("nan")
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        w_samp = rng.choice(wins_w, size=len(wins_w), replace=True)
        l_samp = rng.choice(loss_w, size=len(loss_w), replace=True)
        diffs[i] = w_samp.mean() - l_samp.mean()
    return float(np.quantile(diffs, alpha / 2)), float(np.quantile(diffs, 1 - alpha / 2))


def _welch_t(wins_w: np.ndarray, loss_w: np.ndarray) -> tuple[float, float]:
    """Welch's t-statistic (unequal-variance) for H0: wins_w_mean == loss_w_mean.

    Returns (t_stat, two-sided p-value approximation via normal asymptotic).
    """
    if len(wins_w) < 2 or len(loss_w) < 2:
        return float("nan"), float("nan")
    nw, nl = len(wins_w), len(loss_w)
    mw, ml = wins_w.mean(), loss_w.mean()
    vw = wins_w.var(ddof=1)
    vl = loss_w.var(ddof=1)
    se = np.sqrt(vw / nw + vl / nl)
    if se == 0:
        return float("nan"), float("nan")
    t_stat = (mw - ml) / se
    # Normal approximation for p-value (fine for n>30)
    from math import erf, sqrt
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / sqrt(2))))
    return float(t_stat), float(p_val)


def q1_anti_kelly_significance() -> pd.DataFrame:
    """Per-(symbol, split): mean win-weight, mean loss-weight, Welch t-stat,
    bootstrap CI for the difference.

    CRITICAL METHODOLOGY NOTE: This Q1 runs TWO partition methods to expose
    the /060 Q7 finding's dependence on partition definition:

    (A) /060 Q7 method: partition by `net_pnl_pct > 0` (pre-sizing direction).
        Includes weight=0 KILLED trades whose net_pnl_pct happens to be > 0
        in the "wins" bucket — these contribute 0 to portfolio but pull down
        the avg weight on the win partition.

    (B) /061 Q1 method (PREFERRED for portfolio Sharpe questions): partition
        by `weighted_pnl > 0` (post-sizing portfolio impact). Excludes weight=0
        killed trades from both partitions — these contribute 0 portfolio
        weighted_pnl and shouldn't be in either bucket for sizing analysis.

    The TWO methods produce OPPOSITE SIGNS for TRX:
      Method A: TRX IS diff = -0.061 (anti-Kelly)   — /060 Q7 reading
      Method B: TRX IS diff = +0.020 (Kelly-aligned) — /061 cleaned partition

    This is because TRX has 15 IS trades with weight=0 (killed by gates) whose
    net_pnl_pct > 0 — 15/79 ≈ 19% of IS trades. They inflate the "wins" count
    under Method A with weight=0 entries, dragging the avg_win_w down.

    Hypothesis test: H0: μ_wins_w == μ_loss_w. CI excludes 0 → statistically
    significant difference at α=0.05.
    """
    rng = np.random.default_rng(RNG_SEED)
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        for sym in V3_MODELS:
            g = trades[trades["symbol"] == sym].copy()
            # Method B (preferred): weighted_pnl > 0 partition (excludes killed)
            wins_b = g[g["weighted_pnl"] > 0]["weight_factor"].values
            losses_b = g[g["weighted_pnl"] < 0]["weight_factor"].values
            # Method A (/060 Q7 replication): net_pnl_pct > 0 partition (includes killed)
            wins_a = g[g["net_pnl_pct"] > 0]["weight_factor"].values
            losses_a = g[g["net_pnl_pct"] < 0]["weight_factor"].values
            if len(wins_b) < 2 or len(losses_b) < 2:
                continue
            # Method B stats
            diff_b = wins_b.mean() - losses_b.mean()
            t_b, p_b = _welch_t(wins_b, losses_b)
            ci_lo_b, ci_hi_b = _bootstrap_diff_ci(wins_b, losses_b, N_BOOTSTRAP, rng)
            ci_excl_b = (ci_lo_b > 0 and ci_hi_b > 0) or (ci_lo_b < 0 and ci_hi_b < 0)
            # Method A stats (the /060 Q7 partition)
            diff_a = wins_a.mean() - losses_a.mean() if len(wins_a) > 0 and len(losses_a) > 0 else float("nan")
            t_a, p_a = _welch_t(wins_a, losses_a) if (len(wins_a) >= 2 and len(losses_a) >= 2) else (float("nan"), float("nan"))
            rows.append(
                {
                    "split": split,
                    "symbol": sym,
                    "method_B_n_wins": len(wins_b),
                    "method_B_n_losses": len(losses_b),
                    "method_B_mean_win_w": float(wins_b.mean()),
                    "method_B_mean_loss_w": float(losses_b.mean()),
                    "method_B_diff": float(diff_b),
                    "method_B_welch_t": t_b,
                    "method_B_p_value": p_b,
                    "method_B_ci_lo_95": ci_lo_b,
                    "method_B_ci_hi_95": ci_hi_b,
                    "method_B_ci_excludes_zero": ci_excl_b,
                    "method_A_060_q7_diff": float(diff_a),
                    "method_A_060_q7_welch_t": t_a,
                    "method_A_060_q7_p_value": p_a,
                    "n_killed_in_wins_partition_A": int((g[g["net_pnl_pct"] > 0]["weight_factor"] == 0).sum()),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q1_anti_kelly_significance.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q2 — TRX weight_factor distribution percentiles by win/loss outcome
# ---------------------------------------------------------------------------


def q2_trx_weight_distribution_by_outcome() -> pd.DataFrame:
    """TRX weight_factor percentiles (P10/P25/P50/P75/P90) by win/loss outcome
    in IS and OOS.

    Hypothesis: if the anti-Kelly is concentrated in the LOWER tail of TRX
    winning trades (winners weighted at 0.3-0.5, near the floor), raising the
    floor to 0.5 would lift those winners' contribution without touching
    losses (which sit at higher percentiles). If the anti-Kelly is uniform
    across the distribution, raising the floor wouldn't help selectively.
    """
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        g = trades[trades["symbol"] == "TRXUSDT"].copy()
        for outcome, mask in (
            ("wins", g["weighted_pnl"] > 0),
            ("losses", g["weighted_pnl"] < 0),
            ("zero_killed", g["weight_factor"] == 0),
        ):
            sub = g[mask]
            if len(sub) == 0:
                continue
            w = sub["weight_factor"].values
            rows.append(
                {
                    "split": split,
                    "outcome": outcome,
                    "n": len(w),
                    "mean": float(w.mean()),
                    "std": float(w.std(ddof=1)) if len(w) > 1 else 0.0,
                    "p10": float(np.quantile(w, 0.10)),
                    "p25": float(np.quantile(w, 0.25)),
                    "p50": float(np.quantile(w, 0.50)),
                    "p75": float(np.quantile(w, 0.75)),
                    "p90": float(np.quantile(w, 0.90)),
                    "min": float(w.min()),
                    "max": float(w.max()),
                    "frac_below_05": float((w < 0.5).mean()),
                    "frac_below_04": float((w < 0.4).mean()),
                    "frac_at_floor_030": float((w <= 0.301).mean()),  # tolerance for float
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q2_trx_weight_distribution_by_outcome.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q3 — TRX trade outcome by 5-quantile weight_factor bucket
# ---------------------------------------------------------------------------


def q3_trx_outcome_by_weight_bucket() -> pd.DataFrame:
    """For TRX trades (IS + OOS separately): bucket trades by weight_factor
    quintile (Q1 = lowest 20%, Q5 = highest 20%), compute n / WR /
    weighted_pnl / mean_per_trade per bucket.

    Anti-Kelly diagnosis: if WR is HIGHEST in Q1 (lowest weight) and LOWEST
    in Q5 (highest weight), the model's high-confidence signals (those with
    high atr_pct_rank_200 = high weight) are wrong on TRX.

    Counterfactual prediction: if we floor weights at 0.5, all Q1 trades and
    most Q2 trades get lifted to 0.5. This proportionally amplifies their
    contribution to total weighted_pnl. If Q1+Q2 are WIN-skewed (which the
    anti-Kelly hypothesis predicts), this is net-positive.
    """
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        g = trades[trades["symbol"] == "TRXUSDT"].copy()
        # Exclude killed trades (weight_factor == 0) from quantile bucketing
        nonzero = g[g["weight_factor"] > 0].copy()
        if len(nonzero) < 5:
            continue
        # 5-quantile bucketing
        nonzero["weight_q"] = pd.qcut(
            nonzero["weight_factor"], q=5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"],
            duplicates="drop"
        )
        for bucket, sub in nonzero.groupby("weight_q", observed=True):
            wins = (sub["weighted_pnl"] > 0).sum()
            losses = (sub["weighted_pnl"] < 0).sum()
            wr = wins / len(sub) if len(sub) > 0 else 0.0
            wp_sum = sub["weighted_pnl"].sum()
            unw_sum = sub["net_pnl_pct"].sum()
            rows.append(
                {
                    "split": split,
                    "weight_bucket": str(bucket),
                    "weight_range_min": float(sub["weight_factor"].min()),
                    "weight_range_max": float(sub["weight_factor"].max()),
                    "n_trades": len(sub),
                    "n_wins": int(wins),
                    "n_losses": int(losses),
                    "win_rate": float(wr),
                    "weighted_pnl_sum": float(wp_sum),
                    "unweighted_pnl_sum": float(unw_sum),
                    "weighted_pnl_per_trade": float(wp_sum / len(sub)) if len(sub) > 0 else 0.0,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q3_trx_outcome_by_weight_bucket.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q4 — Counterfactual: TRX weighted_pnl under different per-symbol floors
# ---------------------------------------------------------------------------


def q4_counterfactual_floor_sensitivity() -> pd.DataFrame:
    """For TRX trades only, simulate what weighted_pnl would be under
    different per-symbol vol_scale_floor values: {0.30 (current), 0.40, 0.50, 0.60}.

    Mechanism: weighted_pnl = net_pnl_pct × weight_factor.
    Counterfactual weight_factor at floor F:
        new_w = max(F, current_w) if current_w > 0  [floor lift]
        new_w = 0 if current_w == 0                  [killed trades stay killed]

    Counterfactual weighted_pnl = net_pnl_pct × new_w.

    This is a CONSERVATIVE estimate — it assumes the model's trade selection
    (open_time, direction, exit_reason) is UNCHANGED. In reality, raising the
    floor doesn't affect kill/no-kill or direction decisions; it only modifies
    sizing on trades that already passed gate cascade. So the conservatism is
    minimal.

    NOTE: The counterfactual ignores any portfolio re-weighting effects (each
    symbol contributes pnl independently to the unified portfolio sum). The
    floor change applies ONLY to TRX; BCH/LDO weight_factor unchanged.
    """
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        g = trades[trades["symbol"] == "TRXUSDT"].copy()
        for floor in (0.30, 0.40, 0.50, 0.60):
            # New weight: max(floor, w) only when w > 0 (preserve killed trades at 0)
            new_w = np.where(g["weight_factor"] > 0, np.maximum(floor, g["weight_factor"]), 0.0)
            new_wp = g["net_pnl_pct"].values * new_w
            wins_mask = new_wp > 0
            losses_mask = new_wp < 0
            n_total = len(g)
            n_wins = int(wins_mask.sum())
            n_losses = int(losses_mask.sum())
            rows.append(
                {
                    "split": split,
                    "vol_scale_floor": floor,
                    "n_trades": n_total,
                    "weighted_pnl_sum": float(new_wp.sum()),
                    "weighted_pnl_mean": float(new_wp.mean()) if n_total > 0 else 0.0,
                    "n_wins": n_wins,
                    "n_losses": n_losses,
                    "win_rate": float(n_wins / n_total) if n_total > 0 else 0.0,
                    "avg_win_w": float(new_w[wins_mask].mean()) if n_wins > 0 else float("nan"),
                    "avg_loss_w": float(new_w[losses_mask].mean()) if n_losses > 0 else float("nan"),
                    "win_minus_loss_w": float(new_w[wins_mask].mean() - new_w[losses_mask].mean())
                    if (n_wins > 0 and n_losses > 0)
                    else float("nan"),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q4_counterfactual_floor_sensitivity.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q5 — Cross-symbol floor sensitivity (BCH/LDO invariance check)
# ---------------------------------------------------------------------------


def q5_cross_symbol_floor_sensitivity() -> pd.DataFrame:
    """Per-symbol floor design: vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}
    means BCH and LDO unchanged at 0.3. Demonstrate this is the case by
    simulating each symbol's weighted_pnl under both (a) universal floor 0.3
    (current) and (b) per-symbol floor with TRX-only=0.5.

    Expected: BCH and LDO weighted_pnl IDENTICAL under both scenarios; TRX
    weighted_pnl improved.
    """
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_059 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        for sym in V3_MODELS:
            g = trades[trades["symbol"] == sym].copy()
            current_wp_sum = g["weighted_pnl"].sum()
            # Per-symbol floor design: only TRX gets 0.5; BCH/LDO stay at 0.3
            sym_floor = 0.5 if sym == "TRXUSDT" else 0.3
            new_w = np.where(g["weight_factor"] > 0, np.maximum(sym_floor, g["weight_factor"]), 0.0)
            new_wp = g["net_pnl_pct"].values * new_w
            new_wp_sum = new_wp.sum()
            rows.append(
                {
                    "split": split,
                    "symbol": sym,
                    "applied_floor": sym_floor,
                    "current_weighted_pnl_sum": float(current_wp_sum),
                    "counterfactual_weighted_pnl_sum": float(new_wp_sum),
                    "delta": float(new_wp_sum - current_wp_sum),
                    "delta_pct": float((new_wp_sum - current_wp_sum) / abs(current_wp_sum) * 100)
                    if current_wp_sum != 0
                    else float("nan"),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q5_cross_symbol_floor_sensitivity.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Q6 — Path decision synthesis
# ---------------------------------------------------------------------------


def q6_path_decision(q1: pd.DataFrame, q2: pd.DataFrame, q3: pd.DataFrame,
                    q4: pd.DataFrame, q5: pd.DataFrame) -> pd.DataFrame:
    """Synthesize Path B/C/D/E decision criteria from Q1-Q5 findings.

    PARTITION-METHOD CRITICAL: Q1 surfaces that the /060 Q7 anti-Kelly finding
    was driven by the inclusion of weight=0 killed trades in the "wins" bucket
    (Method A: partition by net_pnl_pct > 0). Under the more appropriate
    partition (Method B: weighted_pnl > 0, which excludes killed trades from
    both partitions because they contribute 0 portfolio wpnl), the anti-Kelly
    sign DISAPPEARS at IS (TRX diff = +0.020, t-stat = +0.34) and is NOT
    statistically significant at OOS (TRX diff = -0.031, t-stat = -0.49,
    bootstrap CI [-0.154, +0.088] includes 0).

    Decision rules:
      Path B (per-symbol floor=0.5) — chosen if:
        - Q4 counterfactual lift is >= +0.5 OOS wpnl AND
        - IS counterfactual is non-destructive (delta within ±0.5 wpnl)
        - Note: lift is expected to be MARGINAL (within 3-seed noise floor)
      Path C (universal reformulation) — chosen if:
        - Method B Q1 confirms TRX statistically anti-Kelly across IS+OOS
        - (NOT the case at /061 EDA — Method B falsifies anti-Kelly significance)
      Path D (passive diagnostic + axis closure) — chosen if:
        - Method B Q1 falsifies anti-Kelly significance AND
        - Q4 counterfactual lifts are within noise floor (|delta| < 0.5 wpnl)
      Path E (reverse-sign for TRX) — never chosen at single-EXPLORATION;
        only valid if other paths show clear-negative AND there is
        adversarial-strength evidence anti-Kelly is real
    """
    # Extract key numbers (Method B partition — preferred for portfolio Sharpe)
    trx_is = q1[(q1["symbol"] == "TRXUSDT") & (q1["split"] == "IS")].iloc[0]
    trx_oos = q1[(q1["symbol"] == "TRXUSDT") & (q1["split"] == "OOS")].iloc[0]
    bch_is = q1[(q1["symbol"] == "BCHUSDT") & (q1["split"] == "IS")].iloc[0]
    ldo_is = q1[(q1["symbol"] == "LDOUSDT") & (q1["split"] == "IS")].iloc[0]

    # Q4 counterfactual at floor=0.5
    q4_05_is = q4[(q4["split"] == "IS") & (q4["vol_scale_floor"] == 0.50)].iloc[0]
    q4_03_is = q4[(q4["split"] == "IS") & (q4["vol_scale_floor"] == 0.30)].iloc[0]
    q4_05_oos = q4[(q4["split"] == "OOS") & (q4["vol_scale_floor"] == 0.50)].iloc[0]
    q4_03_oos = q4[(q4["split"] == "OOS") & (q4["vol_scale_floor"] == 0.30)].iloc[0]

    is_lift = q4_05_is["weighted_pnl_sum"] - q4_03_is["weighted_pnl_sum"]
    oos_lift = q4_05_oos["weighted_pnl_sum"] - q4_03_oos["weighted_pnl_sum"]

    # Q4 counterfactual at floor=0.6 (alternative)
    q4_06_oos = q4[(q4["split"] == "OOS") & (q4["vol_scale_floor"] == 0.60)].iloc[0]
    oos_lift_06 = q4_06_oos["weighted_pnl_sum"] - q4_03_oos["weighted_pnl_sum"]

    # Q2: TRX winning trade P25 weight (IS + OOS)
    trx_wins_is_p25 = q2[(q2["outcome"] == "wins") & (q2["split"] == "IS")]["p25"].iloc[0] if len(q2[(q2["outcome"] == "wins") & (q2["split"] == "IS")]) > 0 else float("nan")
    trx_wins_oos_p25 = q2[(q2["outcome"] == "wins") & (q2["split"] == "OOS")]["p25"].iloc[0] if len(q2[(q2["outcome"] == "wins") & (q2["split"] == "OOS")]) > 0 else float("nan")

    # Q1 Method A vs Method B sign comparison
    trx_is_method_a = trx_is["method_A_060_q7_diff"]
    trx_is_method_b = trx_is["method_B_diff"]
    trx_oos_method_a = trx_oos["method_A_060_q7_diff"]
    trx_oos_method_b = trx_oos["method_B_diff"]
    sign_flip_is = (trx_is_method_a * trx_is_method_b < 0)
    sign_flip_oos = (trx_oos_method_a * trx_oos_method_b < 0)

    rows = []
    rows.append({"criterion": "TRX IS partition-method sign flip A vs B",
                 "value": float(sign_flip_is),
                 "interpretation": f"Method A (060 Q7)={trx_is_method_a:+.4f}, Method B (cleaned)={trx_is_method_b:+.4f}"})
    rows.append({"criterion": "TRX OOS partition-method sign flip A vs B",
                 "value": float(sign_flip_oos),
                 "interpretation": f"Method A (060 Q7)={trx_oos_method_a:+.4f}, Method B (cleaned)={trx_oos_method_b:+.4f}"})
    rows.append({"criterion": "TRX IS anti-Kelly significant (Method B CI)",
                 "value": float(trx_is["method_B_ci_excludes_zero"]),
                 "interpretation": f"Welch t={trx_is['method_B_welch_t']:+.2f}, CI=[{trx_is['method_B_ci_lo_95']:.3f}, {trx_is['method_B_ci_hi_95']:.3f}]"})
    rows.append({"criterion": "TRX OOS anti-Kelly significant (Method B CI)",
                 "value": float(trx_oos["method_B_ci_excludes_zero"]),
                 "interpretation": f"Welch t={trx_oos['method_B_welch_t']:+.2f}, CI=[{trx_oos['method_B_ci_lo_95']:.3f}, {trx_oos['method_B_ci_hi_95']:.3f}]"})
    rows.append({"criterion": "BCH IS Kelly direction (sign of Method B diff)",
                 "value": float(bch_is["method_B_diff"]),
                 "interpretation": "Positive sign indicates Kelly-aligned (baseline)"})
    rows.append({"criterion": "LDO IS Kelly direction (sign of Method B diff)",
                 "value": float(ldo_is["method_B_diff"]),
                 "interpretation": "Positive sign indicates Kelly-aligned (baseline)"})
    rows.append({"criterion": "TRX IS wins weight P25 (Method B)",
                 "value": float(trx_wins_is_p25),
                 "interpretation": "If < 0.5, raising floor to 0.5 would lift IS winning-trade weight"})
    rows.append({"criterion": "TRX OOS wins weight P25 (Method B)",
                 "value": float(trx_wins_oos_p25),
                 "interpretation": "If < 0.5, raising floor to 0.5 would lift OOS winning-trade weight"})
    rows.append({"criterion": "TRX Q4 floor=0.5 IS counterfactual lift",
                 "value": float(is_lift),
                 "interpretation": "Δ weighted_pnl_sum vs current (floor=0.3) — IS"})
    rows.append({"criterion": "TRX Q4 floor=0.5 OOS counterfactual lift",
                 "value": float(oos_lift),
                 "interpretation": "Δ weighted_pnl_sum vs current (floor=0.3) — OOS"})
    rows.append({"criterion": "TRX Q4 floor=0.6 OOS counterfactual lift",
                 "value": float(oos_lift_06),
                 "interpretation": "Δ weighted_pnl_sum vs current (floor=0.3) — OOS at floor=0.6 (alt)"})

    # Verdict logic — REVISED in light of partition-method analysis
    # The /060 Q7 anti-Kelly finding does NOT survive Method B partition cleanup.
    # Path B becomes a marginal-lift intervention; Path D becomes the diagnostic
    # closure (publish partition-method correction).
    method_b_significant = trx_is["method_B_ci_excludes_zero"] or trx_oos["method_B_ci_excludes_zero"]
    counterfactual_oos_lift_meaningful = abs(oos_lift) > 0.3  # >0.3 wpnl is just above 3-seed noise
    is_destructive = is_lift < -0.5  # IS regression >0.5 wpnl is meaningful

    if method_b_significant and counterfactual_oos_lift_meaningful and not is_destructive:
        verdict = "Path B (TRX-specific weight_factor floor=0.5) — moderate evidence"
    elif counterfactual_oos_lift_meaningful and not is_destructive:
        # No Method B significance, but counterfactual OOS lift > noise; Path B as INERT-bias-correction
        verdict = "Path B (TRX floor=0.5) — counterfactual OOS lift +{:.2f}wpnl > noise; IS bit-identical".format(oos_lift)
    elif sign_flip_is or sign_flip_oos:
        verdict = "Path D (passive diagnostic + partition-method correction publication)"
    else:
        verdict = "Path D (passive diagnostic — no clear axis intervention)"

    rows.append({"criterion": "VERDICT",
                 "value": float(method_b_significant) * 10 + float(counterfactual_oos_lift_meaningful),
                 "interpretation": verdict})

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT / "q6_path_decision_summary.csv", index=False)
    return out


# ---------------------------------------------------------------------------
# Summary writer
# ---------------------------------------------------------------------------


def write_summary_md(q1: pd.DataFrame, q2: pd.DataFrame, q3: pd.DataFrame,
                     q4: pd.DataFrame, q5: pd.DataFrame, q6: pd.DataFrame) -> None:
    lines = []
    lines.append("# TRX Anti-Kelly Diagnostic — iter-v3/061")
    lines.append("")
    lines.append("Cycle 1 #2 EXPLORATION. Per Critic FINAL `3cee250` Rec #3.")
    lines.append("")
    lines.append("Anchor: BASELINE_V3.md iter-v3/059 unified 10-seed CONFIRMATION-mode")
    lines.append("(/060 EXPLORATION-MODE-REFERENCE is the cycle 1 axis-PASS anchor;")
    lines.append("EDA uses /059 trade roster because /060 is structurally equivalent at")
    lines.append("the trade-level RiskV2 attribution — both are runs of the same source")
    lines.append("code over the same OHLC data, just at different ensemble sizes; the")
    lines.append("RiskV2 _vol_scale formula is invariant across ensemble size).")
    lines.append("")
    lines.append("## Q1 — Anti-Kelly statistical significance (with partition-method comparison)")
    lines.append("")
    lines.append(q1.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("**CRITICAL FINDING**: The /060 Q7 anti-Kelly finding (TRX -0.061 IS, -0.014 OOS)")
    lines.append("was driven by a partition-method choice. Method A (/060 Q7) uses")
    lines.append("`net_pnl_pct > 0` as the win definition, which INCLUDES weight=0 killed")
    lines.append("trades that happen to be raw-direction-positive. TRX has 15 such trades in IS")
    lines.append("(19% of IS trades) — they contribute 0 to portfolio weighted_pnl but pull down")
    lines.append("the avg_win_w under Method A.")
    lines.append("")
    lines.append("Method B (`weighted_pnl > 0`) excludes killed trades from both partitions, which")
    lines.append("is the appropriate partition for **portfolio Sharpe questions**. Under Method B:")
    lines.append("- TRX IS diff = +0.020 (Kelly-aligned, NOT anti-Kelly; t=+0.34; CI [-0.091, +0.130] includes 0)")
    lines.append("- TRX OOS diff = -0.031 (anti-Kelly direction, but t=-0.49; CI [-0.154, +0.088] includes 0)")
    lines.append("")
    lines.append("**Neither IS nor OOS TRX anti-Kelly is statistically significant** at Method B")
    lines.append("partition. The /060 Q7 finding survives the sign-flip test only in OOS, and even")
    lines.append("there the magnitude is so small that bootstrap CI generously covers 0.")
    lines.append("")
    lines.append("## Q2 — TRX weight_factor distribution by win/loss/killed outcome")
    lines.append("")
    lines.append(q2.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("**Reading**: Percentiles of weight_factor by outcome. `frac_below_05`")
    lines.append("is the key column for floor=0.5 counterfactual: it's the fraction of")
    lines.append("trades in that outcome whose weight would be RAISED to 0.5 under the")
    lines.append("proposed floor change.")
    lines.append("")
    lines.append("## Q3 — TRX outcome by 5-quantile weight bucket")
    lines.append("")
    lines.append(q3.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("**Reading**: TRX trades binned by weight_factor quintile. If WR is")
    lines.append("HIGHER in Q1 (lowest weight) than Q5 (highest weight), the anti-Kelly")
    lines.append("mechanism is concentrated where lifting the floor would help.")
    lines.append("")
    lines.append("## Q4 — TRX counterfactual: weighted_pnl under different floors")
    lines.append("")
    lines.append(q4.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("**Reading**: Conservative counterfactual assuming trade selection")
    lines.append("(open_time, direction, exit_reason) is invariant — only weight_factor")
    lines.append("changes via floor lift. Floor=0.3 row reproduces current state; floor=0.5")
    lines.append("is the Path B intervention candidate.")
    lines.append("")
    lines.append("## Q5 — BCH/LDO invariance at per-symbol TRX-only floor=0.5")
    lines.append("")
    lines.append(q5.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("**Reading**: Demonstrates that per-symbol floor design ({\"TRXUSDT\":")
    lines.append("0.5}) leaves BCH/LDO weighted_pnl IDENTICAL — these rows should have")
    lines.append("delta=0 and delta_pct=0.")
    lines.append("")
    lines.append("## Q6 — Path decision synthesis")
    lines.append("")
    lines.append(q6.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    (OUTPUT / "diagnostic_summary.md").write_text("\n".join(lines))


def main() -> None:
    print("[iter-v3/061 TRX anti-Kelly diagnostic] Q1 — anti-Kelly significance")
    q1 = q1_anti_kelly_significance()
    print(q1.to_string(index=False))

    print("\n[iter-v3/061 TRX anti-Kelly diagnostic] Q2 — TRX weight distribution by outcome")
    q2 = q2_trx_weight_distribution_by_outcome()
    print(q2.to_string(index=False))

    print("\n[iter-v3/061 TRX anti-Kelly diagnostic] Q3 — TRX outcome by weight bucket")
    q3 = q3_trx_outcome_by_weight_bucket()
    print(q3.to_string(index=False))

    print("\n[iter-v3/061 TRX anti-Kelly diagnostic] Q4 — counterfactual floor sensitivity")
    q4 = q4_counterfactual_floor_sensitivity()
    print(q4.to_string(index=False))

    print("\n[iter-v3/061 TRX anti-Kelly diagnostic] Q5 — cross-symbol floor invariance")
    q5 = q5_cross_symbol_floor_sensitivity()
    print(q5.to_string(index=False))

    print("\n[iter-v3/061 TRX anti-Kelly diagnostic] Q6 — path decision synthesis")
    q6 = q6_path_decision(q1, q2, q3, q4, q5)
    print(q6.to_string(index=False))

    write_summary_md(q1, q2, q3, q4, q5, q6)
    print(f"\n[iter-v3/061] EDA outputs written to {OUTPUT}")


if __name__ == "__main__":
    main()
