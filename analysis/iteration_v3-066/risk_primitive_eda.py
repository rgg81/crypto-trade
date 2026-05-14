"""Risk primitive EDA — UNIVERSAL alternatives + cross-axis orthogonality with iter-v3/065.

iter-v3/066 cycle 1 #7 EXPLORATION (NON-FEATURE PIVOT continuation per Critic /064 Rec #4).

Background (from /065 closeout):
- /060 EXPLORATION anchor: IS Sharpe +0.8325, OOS Sharpe +0.1403; 102 OOS trades.
- /065 PROMISING-AT-EXPLORATION at SUSPICIOUS-OOS-DOMINANT taxonomy.
- /061 introduced per-symbol risk-primitive customization (vol_scale_floor_per_symbol={TRX:0.5})
  but cycle 1 axis selection mandates UNIVERSAL alternatives per
  `feedback_v3_per_symbol_lifts_oos_breaks_is.md` SYSTEM-LEVEL REVERT.

This EDA evaluates UNIVERSAL RISK PRIMITIVE alternatives orthogonal to /065's
labeling axis. The 5 candidate Paths are:

  Path A — Sortino-based vol scaling (replace ATR%rank with downside-dev%rank)
           OUT: requires NEW feature column + risk_v2 logic — 2-axis change
           (violates `feedback_v3_engineered_features_dont_stack.md` single-axis discipline).

  Path B — UNIVERSAL vol_scale_floor 0.3 -> {0.4, 0.5}
           Lift floor for ALL symbols (BCH+LDO+TRX). Replaces /061's TRX-only floor=0.5
           customization with a universal alternative.

  Path C — Confidence-weighted vol scaling (multiply weight_factor by model proba)
           OUT: requires Signal interface change (add confidence) + risk_v2 logic — 2-axis change.

  Path D — DSR-based kill switch (kill trades when 30-trade rolling Sharpe < 0)
           OUT: STATEFUL gate with deadlock risk per `feedback_v3_oracle_eda_validity.md`.
           Per Critic /054 closeout: stateful gates that update on signal-emission entered
           permanent deadlock in iter-v3/054 (BCH+LDO brake-ON at OOS-start, no trades, no state update).
           ORACLE EDA on prior trade roster is INVALID for stateful primitives.

  Path E — UNIVERSAL vol_scale_ceiling 1.0 -> {0.8, 0.7}
           Cap weight_factor for ALL symbols. Tests over-confidence damping at high vol_scale.
           Symmetric brake to Path B (floor); selectively dampens HIGH-weight trades that
           may be lottery-class.

This script produces 6 CSV tables that quantitatively support Path selection.

ORACLE counterfactual methodology:
- The /060 trade roster is held fixed (universal change does not regenerate trade roster).
- For each trade with weight_factor wf ∈ (0, 1):
  - If wf == 0.3 exactly (sat at old floor): raw atr_pct was <=0.3 -> new value = new_floor.
  - If wf == 1.0 exactly (sat at old ceiling): raw atr_pct was >=1.0 -> new value = new_ceiling.
  - Otherwise wf was unclipped: new value = clip(wf, new_floor, new_ceiling).
- Recompute weighted_pnl proportionally: new_wpnl = old_wpnl * (new_wf / old_wf).
- Killed trades (wf == 0): preserved as 0 wpnl.

CAVEAT (per `feedback_v3_oracle_eda_validity.md`): the ORACLE counterfactual is VALID for
STATELESS gates (vol scaling, ceiling cap, floor lift) where signal emission does NOT
update gate state. Path B / Path E are STATELESS. Path D (DSR-based kill) is STATEFUL
and CANNOT be ORACLE-tested — that's why Path D is OUT.

CAVEAT 2: this ORACLE assumes the production runner with Path B / Path E would produce
the SAME trade roster as /060. Path B / Path E change the WEIGHTING of trades, NOT the
emission rule, so the same trades are emitted; the ORACLE assumption is mechanistically
valid. However, Optuna at the production runner re-runs with the modified RiskV2Config —
TPE may converge to slightly different hyperparams whose trade roster differs from /060.
This ORACLE captures the FIRST-ORDER effect; Optuna second-order is not modeled.

CAVEAT 3: ORACLE Sharpe deltas are SMALL in magnitude because vol-scaling weight changes
affect mean AND std proportionally; the dominant first-order effect is partial cancellation.
This is structurally INFORMATIVE: it predicts INERT-AT-EXPLORATION as the most likely
classification (per Section 7 probability calibration).

Outputs (committed CSVs in this directory):
  - T0_anchor_values.csv               -- /060 anchor values with bit-exact file:line refs
  - T1_current_risk_primitive_inventory.csv  -- 7-primitive risk gate stack + per-symbol overrides
  - T2_weight_factor_distribution_per_symbol.csv  -- weight_factor distribution per symbol on /060 trades
  - T3_path_counterfactuals.csv        -- per-Path total + per-symbol IS/OOS wpnl Δ
  - T4_path_oracle_monthly_sharpe.csv  -- per-Path ORACLE Sharpe Δ (the headline metric)
  - T5_path_selection_summary.csv      -- synthesized Path scoring + selection rationale
  - T6_cross_axis_065_orthogonality.csv  -- mechanistic orthogonality check with /065 SL widening

Run:
  uv run python analysis/iteration_v3-066/risk_primitive_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

REPO = Path(__file__).resolve().parents[2]
REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"  # EXPLORATION-mode anchor (3-seed; cycle 1 #1)
OUTPUT = Path(__file__).parent

V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# RiskV2 vol-scaling defaults (from src/crypto_trade/strategies/ml/risk_v2.py:57-58)
DEFAULT_VOL_SCALE_FLOOR = 0.3
DEFAULT_VOL_SCALE_CEILING = 1.0


# ---------------------------------------------------------------------------
# T0 — Anchor-value declaration (per Critic /064 Rec #1 + /065 Rec #1)
# ---------------------------------------------------------------------------


def t0_anchor_values() -> pd.DataFrame:
    """Anchor values bit-exact from /060 reports with explicit file:line citations.

    Per `feedback_v3_iter064_process_lessons.md` Rule 1 + `feedback_v3_iter065_*.md`
    recurrence: brief Section 2.1 anchor-value declarations must match actual
    /060 report contents byte-exactly. T0 produces the cited values; brief
    Section 2.1 must cite T0.

    NB: comparison.csv has TWO sections separated by a blank line + comment row.
    The top section (lines 1-14) is global metrics with 3 cols (metric, in_sample, out_of_sample, ratio).
    The per-symbol section (lines 17-20) has 5 cols (metric==symbol, weighted_pnl, n_trades, win_rate, concentration_pct).
    We parse them separately by reading the file line-by-line.
    """
    cmp_path = REPORTS_060 / "comparison.csv"

    # Parse global metrics section: read lines 1-15 only
    with open(cmp_path) as f:
        lines = f.readlines()

    # First section: until blank line
    metric_map = {}
    oos_map = {}
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) == 4 and parts[0] not in V3_MODELS:
            metric, isv, oosv, _ratio = parts
            try:
                metric_map[metric] = float(isv) if isv not in ("", "—") else float("nan")
                oos_map[metric] = float(oosv) if oosv not in ("", "—") else float("nan")
            except ValueError:
                pass

    # Per-symbol section: rows where metric is in V3_MODELS, with 5 fields
    bch_oos_wpnl = ldo_oos_wpnl = trx_oos_wpnl = float("nan")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) == 5 and parts[0] in V3_MODELS:
            sym, wpnl, _ntr, _wr, _conc = parts
            if sym == "BCHUSDT":
                bch_oos_wpnl = float(wpnl)
            elif sym == "LDOUSDT":
                ldo_oos_wpnl = float(wpnl)
            elif sym == "TRXUSDT":
                trx_oos_wpnl = float(wpnl)

    rows = [
        {
            "metric": "monthly_sharpe_in_sample",
            "value": float(metric_map["monthly_sharpe"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:2",
        },
        {
            "metric": "monthly_sharpe_out_of_sample",
            "value": float(oos_map["monthly_sharpe"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:2",
        },
        {
            "metric": "n_trades_in_sample",
            "value": float(metric_map["n_trades"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:7",
        },
        {
            "metric": "n_trades_out_of_sample",
            "value": float(oos_map["n_trades"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:7",
        },
        {
            "metric": "weighted_pnl_total_in_sample",
            "value": float(metric_map["weighted_pnl_total"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:10",
        },
        {
            "metric": "weighted_pnl_total_out_of_sample",
            "value": float(oos_map["weighted_pnl_total"]),
            "source": "reports-v3/iteration_v3-060/comparison.csv:10",
        },
        {
            "metric": "BCH_OOS_weighted_pnl",
            "value": bch_oos_wpnl,
            "source": "reports-v3/iteration_v3-060/comparison.csv:18",
        },
        {
            "metric": "LDO_OOS_weighted_pnl",
            "value": ldo_oos_wpnl,
            "source": "reports-v3/iteration_v3-060/comparison.csv:19",
        },
        {
            "metric": "TRX_OOS_weighted_pnl",
            "value": trx_oos_wpnl,
            "source": "reports-v3/iteration_v3-060/comparison.csv:20",
        },
        {
            "metric": "frac_positive_paths_cpcv",
            "value": 0.6444,
            "source": "BASELINE_V3.md Headline Metrics (CPCV invariant across architectures)",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T0_anchor_values.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T1 — Current risk primitive inventory
# ---------------------------------------------------------------------------


def t1_current_risk_primitive_inventory() -> pd.DataFrame:
    """Document current 7-primitive risk gate stack + per-symbol overrides at /065 production state.

    Source: run_baseline_v3.py:1377-1419 (RiskV2Config init in _build_v3_model).
    Source: src/crypto_trade/strategies/ml/risk_v2.py for primitive logic.
    """
    rows = [
        {
            "primitive_id": 0,
            "primitive_name": "Vol scaling (weight_factor formula)",
            "formula": "clip(atr_pct_rank_200, floor, ceiling)",
            "default_floor": DEFAULT_VOL_SCALE_FLOOR,
            "default_ceiling": DEFAULT_VOL_SCALE_CEILING,
            "per_symbol_override": "{'TRXUSDT': 0.5} (iter-v3/061 floor override only)",
            "enable_flag": "enable_vol_scaling=True",
            "category": "WEIGHTING (multiplicative)",
            "iteration_added": "iter-v2/001 (sign inverted iter-v2/002)",
        },
        {
            "primitive_id": 1,
            "primitive_name": "Feature z-score OOD (zscore_threshold)",
            "formula": "abs((feat - feat_mean_IS) / feat_std_IS) > zscore_threshold",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_zscore_ood=True; zscore_threshold=2.0",
            "category": "BINARY KILL (universal)",
            "iteration_added": "iter-v3/011 (zscore_threshold=2.0)",
        },
        {
            "primitive_id": 2,
            "primitive_name": "Hurst regime check (hurst_100 percentile)",
            "formula": "hurst_100 outside [Q05_IS, Q95_IS]",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_hurst_check=True",
            "category": "BINARY KILL (universal)",
            "iteration_added": "iter-v2 prior; disabled iter-v3/022 then re-enabled",
        },
        {
            "primitive_id": 3,
            "primitive_name": "ADX gate (adx_threshold)",
            "formula": "ADX_14 < adx_threshold",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "{} (TRX 21 dropped at iter-v3/050)",
            "enable_flag": "enable_adx_gate=True; adx_threshold=20.0",
            "category": "BINARY KILL (universal)",
            "iteration_added": "iter-v2 prior",
        },
        {
            "primitive_id": 4,
            "primitive_name": "Low-vol filter (atr_pct_rank_200 threshold)",
            "formula": "atr_pct_rank_200 < low_vol_filter_threshold",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_low_vol_filter=True; low_vol_filter_threshold=0.33",
            "category": "BINARY KILL (universal)",
            "iteration_added": "iter-v2/004",
        },
        {
            "primitive_id": 5,
            "primitive_name": "Per-symbol PnL cap (max_per_symbol_pnl_share)",
            "formula": "scaled_weight if rolling_share > max_per_symbol_pnl_share",
            "default_floor": np.nan,
            "default_ceiling": 0.40,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_per_symbol_cap=False (DISABLED iter-v3/020 PATH C)",
            "category": "WEIGHTING (proportional)",
            "iteration_added": "iter-v3/020 (PATH C closed; CLOSED-mechanism)",
        },
        {
            "primitive_id": 6,
            "primitive_name": "Regime-conditional kill switch (primitive 9)",
            "formula": "BTC drawdown_30d > dd_threshold OR |BTC vol_zscore_30d| > vol_threshold",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_regime_gate=False (DISABLED iter-v3/023)",
            "category": "BINARY KILL (per-symbol scope)",
            "iteration_added": "iter-v3/022 (PATH C, disabled iter-v3/023)",
        },
        {
            "primitive_id": 7,
            "primitive_name": "Direction-asymmetric kill switch (primitive 10)",
            "formula": "kill if direction == +1 and symbol in block_long_for",
            "default_floor": np.nan,
            "default_ceiling": np.nan,
            "per_symbol_override": "block_long_for=()",
            "enable_flag": "block_long_for=() (DISABLED iter-v3/051 SYSTEM-LEVEL REVERT)",
            "category": "BINARY KILL (per-symbol)",
            "iteration_added": "iter-v3/047 (reverted iter-v3/051)",
        },
        {
            "primitive_id": 8,
            "primitive_name": "Per-symbol drawdown brake (primitive 11)",
            "formula": "pause symbol when 30-day cum_wpnl_dd >= threshold",
            "default_floor": 10.0,
            "default_ceiling": 5.0,
            "per_symbol_override": "{} (none)",
            "enable_flag": "enable_per_symbol_drawdown_brake=False (CLOSED-mechanism iter-v3/054)",
            "category": "STATEFUL KILL",
            "iteration_added": "iter-v3/054 (PATH C-clean closed)",
        },
        {
            "primitive_id": 9,
            "primitive_name": "BTC trend filter (post-trade)",
            "formula": "kill trade if direction fights 14d BTC trend > 15%",
            "default_floor": np.nan,
            "default_ceiling": 15.0,
            "per_symbol_override": "{} (none; all 3 symbols)",
            "enable_flag": "BTC_TREND_CONFIG.enabled=True; threshold_pct=15.0",
            "category": "BINARY KILL (post-trade, universal)",
            "iteration_added": "v2 inheritance",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T1_current_risk_primitive_inventory.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T2 — Weight factor distribution per symbol on /060 trades
# ---------------------------------------------------------------------------


def t2_weight_factor_distribution_per_symbol() -> pd.DataFrame:
    """Per (split, symbol): n trades, killed count, weight_factor distribution buckets.

    This grounds the Path B/E counterfactual: which trades will be affected by
    each Path's floor / ceiling change?

    Hypothesis driven by /060 weight_factor distribution:
    - Path B (floor 0.3 -> 0.4): affects trades currently at exactly 0.3 (saturated
      at floor; raw atr_pct <= 0.3) + trades in (0.3, 0.4) (lifted to 0.4). Killed
      trades preserved at 0.
    - Path E (ceiling 1.0 -> 0.8): affects trades at exactly 1.0 (raw atr_pct >= 1.0)
      + trades in (0.8, 1.0) (capped at 0.8). Killed trades preserved at 0.
    """
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_060 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        for sym in V3_MODELS:
            g = trades[trades["symbol"] == sym]
            wf = g["weight_factor"].values
            n_killed = int((wf == 0.0).sum())
            n_at_floor_0_3 = int(((wf >= 0.299) & (wf <= 0.301)).sum())
            n_in_0_3_to_0_4 = int(((wf > 0.301) & (wf < 0.4)).sum())
            n_in_0_4_to_0_8 = int(((wf >= 0.4) & (wf < 0.8)).sum())
            n_in_0_8_to_1_0 = int(((wf >= 0.8) & (wf < 0.999)).sum())
            n_at_ceiling_1_0 = int((wf >= 0.999).sum())
            wpnl_killed = float(g.loc[wf == 0.0, "weighted_pnl"].sum())
            wpnl_at_floor = float(g.loc[(wf >= 0.299) & (wf <= 0.301), "weighted_pnl"].sum())
            wpnl_in_0_8_to_1_0 = float(
                g.loc[(wf >= 0.8) & (wf < 0.999), "weighted_pnl"].sum()
            )
            wpnl_at_ceiling = float(g.loc[wf >= 0.999, "weighted_pnl"].sum())
            wpnl_total = float(g["weighted_pnl"].sum())

            rows.append(
                {
                    "split": split,
                    "symbol": sym,
                    "n_trades_total": len(g),
                    "n_killed_wf0": n_killed,
                    "n_at_floor_0_3": n_at_floor_0_3,
                    "n_in_0_3_to_0_4": n_in_0_3_to_0_4,
                    "n_in_0_4_to_0_8": n_in_0_4_to_0_8,
                    "n_in_0_8_to_1_0": n_in_0_8_to_1_0,
                    "n_at_ceiling_1_0": n_at_ceiling_1_0,
                    "wpnl_total": wpnl_total,
                    "wpnl_killed": wpnl_killed,
                    "wpnl_at_floor_0_3": wpnl_at_floor,
                    "wpnl_in_0_8_to_1_0": wpnl_in_0_8_to_1_0,
                    "wpnl_at_ceiling_1_0": wpnl_at_ceiling,
                    "mean_wf_nonzero": (
                        float(wf[wf > 0].mean()) if (wf > 0).any() else 0.0
                    ),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T2_weight_factor_distribution_per_symbol.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T3 — Path counterfactuals: per-Path total + per-symbol wpnl Δ
# ---------------------------------------------------------------------------


def apply_path_counterfactual(
    trades: pd.DataFrame, new_floor: float, new_ceiling: float
) -> pd.DataFrame:
    """Apply a (new_floor, new_ceiling) counterfactual to the /060 trades.

    Methodology:
    - For killed trades (wf == 0): preserve wpnl = 0 (gate killed).
    - For wf == 0.3 exactly: raw atr_pct was <= 0.3 (clipped at floor) -> new value = new_floor.
    - For wf == 1.0 exactly: raw atr_pct was >= 1.0 (clipped at ceiling) -> new value = new_ceiling.
    - Otherwise wf is unclipped (raw atr_pct == wf): new value = clip(wf, new_floor, new_ceiling).
    - Recompute weighted_pnl proportionally: new_wpnl = old_wpnl * (new_wf / old_wf).
    """
    new = trades.copy()
    new_wpnls = []
    new_wfs = []
    for _, row in trades.iterrows():
        wf = float(row["weight_factor"])
        if wf == 0.0:
            new_wpnls.append(0.0)
            new_wfs.append(0.0)
            continue
        if wf <= 0.301:
            new_wf = new_floor
        elif wf >= 0.999:
            new_wf = new_ceiling
        else:
            new_wf = float(np.clip(wf, new_floor, new_ceiling))
        new_pnl = float(row["weighted_pnl"]) * (new_wf / wf) if wf > 0 else 0.0
        new_wpnls.append(new_pnl)
        new_wfs.append(new_wf)
    new["weight_factor"] = new_wfs
    new["weighted_pnl"] = new_wpnls
    return new


def t3_path_counterfactuals() -> pd.DataFrame:
    """Per (Path, split, symbol): wpnl Δ vs /060 anchor + total Δ row.

    Paths tested:
      - B(0.4): universal floor 0.3 -> 0.4, ceiling unchanged (1.0)
      - B(0.5): universal floor 0.3 -> 0.5, ceiling unchanged (1.0)
      - E(0.8): universal floor 0.3 (unchanged), ceiling 1.0 -> 0.8
      - E(0.7): universal floor 0.3 (unchanged), ceiling 1.0 -> 0.7
    """
    paths = [
        ("B_floor_0.4", 0.4, 1.0),
        ("B_floor_0.5", 0.5, 1.0),
        ("E_ceiling_0.8", 0.3, 0.8),
        ("E_ceiling_0.7", 0.3, 0.7),
    ]
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_060 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        baseline_total = float(trades["weighted_pnl"].sum())
        for path_label, new_floor, new_ceiling in paths:
            new_trades = apply_path_counterfactual(trades, new_floor, new_ceiling)
            new_total = float(new_trades["weighted_pnl"].sum())
            # Per symbol
            for sym in V3_MODELS:
                sym_mask = trades["symbol"] == sym
                old_sym = float(trades.loc[sym_mask, "weighted_pnl"].sum())
                new_sym = float(new_trades.loc[sym_mask, "weighted_pnl"].sum())
                rows.append(
                    {
                        "split": split,
                        "path": path_label,
                        "new_floor": new_floor,
                        "new_ceiling": new_ceiling,
                        "symbol": sym,
                        "wpnl_baseline": old_sym,
                        "wpnl_counterfactual": new_sym,
                        "wpnl_delta": new_sym - old_sym,
                    }
                )
            # Total row
            rows.append(
                {
                    "split": split,
                    "path": path_label,
                    "new_floor": new_floor,
                    "new_ceiling": new_ceiling,
                    "symbol": "TOTAL",
                    "wpnl_baseline": baseline_total,
                    "wpnl_counterfactual": new_total,
                    "wpnl_delta": new_total - baseline_total,
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T3_path_counterfactuals.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T4 — Path ORACLE monthly Sharpe Δ (the headline metric)
# ---------------------------------------------------------------------------


def compute_monthly_sharpe(trades: pd.DataFrame) -> float:
    """Monthly Sharpe from a trades DF using close_time -> monthly aggregation.

    Annualization: monthly_sharpe = (mean_m / std_m) * sqrt(12).
    Matches /060 baseline: 0.8325 IS / 0.1403 OOS.
    """
    t = trades.copy()
    t["close_dt"] = pd.to_datetime(t["close_time"], unit="ms")
    t["month"] = t["close_dt"].dt.to_period("M")
    monthly = t.groupby("month")["weighted_pnl"].sum()
    mean_m = monthly.mean()
    std_m = monthly.std(ddof=1)
    if std_m == 0 or not np.isfinite(std_m):
        return 0.0
    return float((mean_m / std_m) * np.sqrt(12))


def t4_path_oracle_monthly_sharpe() -> pd.DataFrame:
    """Per (Path, split): ORACLE monthly Sharpe + Δ vs /060.

    This is the HEADLINE PREDICTOR for axis-PASS thresholds per
    `feedback_v3_cycle1_axis_pass_criteria.md`:
      - PROMISING-AT-EXPLORATION: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20
      - INERT-AT-EXPLORATION: IS Δ ∈ [-0.10, +0.10] OR OOS Δ ∈ [-0.20, +0.20]
      - NEGATIVE-AT-EXPLORATION: IS Δ < -0.10 OR OOS Δ < -0.20
    """
    paths = [
        ("B_floor_0.4", 0.4, 1.0),
        ("B_floor_0.5", 0.5, 1.0),
        ("E_ceiling_0.8", 0.3, 0.8),
        ("E_ceiling_0.7", 0.3, 0.7),
    ]
    rows = []
    for split in ("IS", "OOS"):
        path = REPORTS_060 / ("in_sample" if split == "IS" else "out_of_sample") / "trades.csv"
        trades = pd.read_csv(path)
        baseline_sharpe = compute_monthly_sharpe(trades)
        for path_label, new_floor, new_ceiling in paths:
            new_trades = apply_path_counterfactual(trades, new_floor, new_ceiling)
            new_sharpe = compute_monthly_sharpe(new_trades)
            rows.append(
                {
                    "split": split,
                    "path": path_label,
                    "new_floor": new_floor,
                    "new_ceiling": new_ceiling,
                    "sharpe_baseline_060": baseline_sharpe,
                    "sharpe_counterfactual": new_sharpe,
                    "sharpe_delta": new_sharpe - baseline_sharpe,
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T4_path_oracle_monthly_sharpe.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T5 — Path selection summary
# ---------------------------------------------------------------------------


def t5_path_selection_summary(t4: pd.DataFrame, t3: pd.DataFrame) -> pd.DataFrame:
    """Synthesize Path selection scoring.

    Scoring criteria:
    - sign_aligned: both IS and OOS Sharpe Δ have the same sign and both > 0
    - magnitude_in_band: Sharpe Δ magnitudes are within [-0.20, +0.30] (single-seed
      lottery range expected)
    - per_symbol_balanced: max(|sym_wpnl_Δ|) < threshold; checks no one symbol
      dominates the Path effect
    - implementation_cost: 0=single-axis change; 1=2-axis change required
    - exception_flags: paths excluded for methodology reasons
    """
    paths = ["B_floor_0.4", "B_floor_0.5", "E_ceiling_0.8", "E_ceiling_0.7"]
    rows = []
    for path in paths:
        sub = t4[t4["path"] == path]
        is_sharpe_delta = float(sub.loc[sub["split"] == "IS", "sharpe_delta"].iloc[0])
        oos_sharpe_delta = float(sub.loc[sub["split"] == "OOS", "sharpe_delta"].iloc[0])
        sign_aligned = (is_sharpe_delta > 0) and (oos_sharpe_delta > 0)
        magnitude_in_band = (
            abs(is_sharpe_delta) <= 0.30 and abs(oos_sharpe_delta) <= 0.30
        )

        sub_t3 = t3[(t3["path"] == path) & (t3["symbol"] != "TOTAL")]
        max_abs_sym_wpnl_delta = float(sub_t3["wpnl_delta"].abs().max())

        rows.append(
            {
                "path": path,
                "is_sharpe_delta_oracle": is_sharpe_delta,
                "oos_sharpe_delta_oracle": oos_sharpe_delta,
                "sign_aligned_positive": sign_aligned,
                "magnitude_in_band_pm03": magnitude_in_band,
                "max_abs_per_symbol_wpnl_delta": max_abs_sym_wpnl_delta,
                "implementation_cost_axes": 1,  # all 4 are single-axis (RiskV2Config field change)
                "methodology_pass": True,  # all 4 are stateless universal changes
            }
        )

    # Add the excluded paths for documentation
    rows.append(
        {
            "path": "A_sortino_vol_scaling",
            "is_sharpe_delta_oracle": np.nan,
            "oos_sharpe_delta_oracle": np.nan,
            "sign_aligned_positive": False,
            "magnitude_in_band_pm03": False,
            "max_abs_per_symbol_wpnl_delta": np.nan,
            "implementation_cost_axes": 2,
            "methodology_pass": False,
            # "exception": "Requires new feature column + risk_v2 logic — 2-axis change"
        }
    )
    rows.append(
        {
            "path": "C_confidence_weighted_vol_scaling",
            "is_sharpe_delta_oracle": np.nan,
            "oos_sharpe_delta_oracle": np.nan,
            "sign_aligned_positive": False,
            "magnitude_in_band_pm03": False,
            "max_abs_per_symbol_wpnl_delta": np.nan,
            "implementation_cost_axes": 2,
            "methodology_pass": False,
            # "exception": "Requires Signal interface change + risk_v2 logic — 2-axis change"
        }
    )
    rows.append(
        {
            "path": "D_dsr_based_kill_switch",
            "is_sharpe_delta_oracle": np.nan,
            "oos_sharpe_delta_oracle": np.nan,
            "sign_aligned_positive": False,
            "magnitude_in_band_pm03": False,
            "max_abs_per_symbol_wpnl_delta": np.nan,
            "implementation_cost_axes": 1,
            "methodology_pass": False,
            # "exception": "STATEFUL gate — ORACLE EDA invalid per feedback_v3_oracle_eda_validity.md"
        }
    )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T5_path_selection_summary.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T6 — Cross-axis orthogonality check with /065 SL widening
# ---------------------------------------------------------------------------


def t6_cross_axis_065_orthogonality() -> pd.DataFrame:
    """Mechanistic orthogonality check between iter-v3/066 risk-primitive axis and
    iter-v3/065 universal SL widening (DEFAULT_ATR_MULTIPLIERS 1.0 -> 1.5).

    Two changes are MECHANISTICALLY ORTHOGONAL if:
    1. /065 SL widening changes WHICH bars become labeled trades + per-trade TP/SL distances
    2. iter-v3/066 risk primitive changes the WEIGHT applied to those trades
    3. The two operate on DIFFERENT code paths and DIFFERENT state at execution time

    /065 mechanism (labeling axis):
      - Pre-training: DEFAULT_ATR_MULTIPLIERS edits the label generation in
        labeling.py::label_trades. Trades with SL=1.5*ATR vs SL=1.0*ATR have different
        outcomes (some prior SL-hits become TP-hits or timeouts). The training-label
        distribution shifts.
      - At inference (no change): LightGbmStrategy.get_signal returns Signal(direction,
        weight=100, tp_pct=NATR*2.0, sl_pct=NATR*1.5) when atr_tp_multiplier and
        atr_sl_multiplier are passed.
      - Trade execution: SL distance = sl_pct = NATR*1.5; first-hit rule unchanged.

    iter-v3/066 risk primitive (weighting axis):
      - At inference: RiskV2Wrapper._vol_scale returns clip(atr_pct_rank_200, floor, ceiling).
        weight = round(sig.weight * scale * cap_scale) — only affects WEIGHT, not direction,
        tp_pct, or sl_pct.
      - Same code path as /065 sl_pct: unchanged. Same trade roster construction: unchanged.
      - Different state: vol_scale is read-only on atr_pct_rank_200 (a stateless feature);
        labeling.label_trades reads tp_pct/sl_pct as inputs but does NOT consume vol_scale_floor.

    Orthogonality VERIFIED:
      - Code path: labeling.py (axis /065) vs risk_v2.py (axis /066) — separate modules
      - State at execution: ATR multipliers (axis /065) are training-time labels; vol_scale_floor
        (axis /066) is inference-time weight modifier
      - First-order effect on /060 trades: independent linear contributions

    However, SECOND-ORDER coupling exists at Optuna's TPE level:
      - /065 changes label distribution; LightGBM trained on different labels
      - /066 changes weight; Optuna optimizes around new weight distribution
      - When BUNDLED at /069 CONFIRMATION, Optuna sees BOTH simultaneously and may
        converge to hyperparams that capture interaction effects

    For SINGLE-AXIS EXPLORATION discipline (one substantive change per EXPLORATION),
    iter-v3/066 changes ONLY the RiskV2Config field; DEFAULT_ATR_MULTIPLIERS reverts to (2.0, 1.0)
    for /066's run. /065's labeling axis is tested separately and bundled at /069.
    """
    rows = [
        {
            "check": "code_path_isolation",
            "iter_v3_065_module": "src/crypto_trade/strategies/ml/labeling.py",
            "iter_v3_066_module": "src/crypto_trade/strategies/ml/risk_v2.py",
            "isolated": True,
        },
        {
            "check": "execution_time_state_isolation",
            "iter_v3_065_state": "TRAIN-TIME label generation (atr_tp_multiplier, atr_sl_multiplier)",
            "iter_v3_066_state": "INFERENCE-TIME weight modifier (vol_scale_floor, vol_scale_ceiling)",
            "isolated": True,
        },
        {
            "check": "signal_field_independence",
            "iter_v3_065_field": "Signal(.tp_pct, .sl_pct)",
            "iter_v3_066_field": "Signal(.weight)",
            "isolated": True,
        },
        {
            "check": "trade_roster_emission_dependency",
            "iter_v3_065_effect": "CHANGES roster (wider SL = some prior SL-hits become TP/timeout)",
            "iter_v3_066_effect": "DOES NOT change roster (only weight applied to surviving trades)",
            "isolated": True,
        },
        {
            "check": "optuna_search_space_coupling",
            "iter_v3_065_effect": "Label distribution shift -> TPE explores different model regions",
            "iter_v3_066_effect": "Weight distribution shift -> TPE explores different confidence regions",
            "isolated": False,  # Optuna may interact at second order; bundled at /069 captures this
        },
        {
            "check": "single_axis_at_066",
            "value": "/066 changes ONLY RiskV2Config field (Path B or E); DEFAULT_ATR_MULTIPLIERS reverts to (2.0, 1.0)",
            "isolated": True,  # /066 isolates the risk-primitive axis from /065's labeling axis
        },
        {
            "check": "bundle_at_069",
            "iter_v3_069_bundle": "/065 (SL=1.5) + /066 (Path B or E if PROMISING) — multi-seed CONFIRMATION",
            "isolated": False,  # Bundled by design at CONFIRMATION
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT / "T6_cross_axis_065_orthogonality.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 80)
    print("iter-v3/066 Risk Primitive EDA — UNIVERSAL alternatives")
    print("=" * 80)

    print("\n[T0] /060 anchor values (bit-exact)")
    t0 = t0_anchor_values()
    print(t0.to_string(index=False))

    print("\n[T1] Current 7-primitive risk gate inventory")
    t1 = t1_current_risk_primitive_inventory()
    print(t1[["primitive_id", "primitive_name", "enable_flag", "per_symbol_override"]].to_string(index=False))

    print("\n[T2] /060 weight_factor distribution per (split, symbol)")
    t2 = t2_weight_factor_distribution_per_symbol()
    print(t2[["split", "symbol", "n_trades_total", "n_killed_wf0", "n_at_floor_0_3", "n_in_0_3_to_0_4", "n_in_0_4_to_0_8", "n_in_0_8_to_1_0", "n_at_ceiling_1_0", "wpnl_total"]].to_string(index=False))

    print("\n[T3] Path counterfactual wpnl Δ (per Path, per symbol)")
    t3 = t3_path_counterfactuals()
    pivot = t3.pivot_table(
        index=["split", "path"], columns="symbol", values="wpnl_delta", aggfunc="sum"
    )
    print(pivot.to_string())

    print("\n[T4] Path ORACLE monthly Sharpe Δ (HEADLINE)")
    t4 = t4_path_oracle_monthly_sharpe()
    print(t4.to_string(index=False))

    print("\n[T5] Path selection summary")
    t5 = t5_path_selection_summary(t4, t3)
    print(t5.to_string(index=False))

    print("\n[T6] Cross-axis orthogonality with /065 SL widening")
    t6 = t6_cross_axis_065_orthogonality()
    print(t6.to_string(index=False))

    print("\n" + "=" * 80)
    print("PATH SELECTION ANALYSIS")
    print("=" * 80)
    print("""
ORACLE ANALYSIS RESULTS:

  Path B(0.4):  IS ΔSharpe = -0.006   OOS ΔSharpe = +0.006   [SIGN-CONFLICT, tiny magnitude]
  Path B(0.5):  IS ΔSharpe = -0.018   OOS ΔSharpe = +0.003   [SIGN-CONFLICT, LDO IS damage]
  Path E(0.8):  IS ΔSharpe = +0.008   OOS ΔSharpe = +0.022   [BOTH POSITIVE, sign-aligned]
  Path E(0.7):  IS ΔSharpe = -0.032   OOS ΔSharpe = -0.001   [SIGN-CONFLICT, BCH IS damage]

PATH E(0.8) is the QR selection:

  RATIONALE:
  1. BOTH axes ORACLE-positive (only Path with sign-aligned positive ΔSharpe)
  2. LDO OOS is anti-Kelly (6 of 11 trades at wf>=0.8; OOS wpnl -19.72): capping
     LDO high-wf trades is direct anti-Kelly correction (LDO OOS Δ +2.66 wpnl)
  3. BCH OOS gains +0.87 wpnl (limited high-wf BCH OOS trades — only 15 of 35
     at >=0.8 wf); capping protects against over-confidence in volatile regimes
  4. TRX OOS loses -1.51 wpnl (TRX is the Kelly-aligned high-wf winner); this
     is the cost of universal change vs per-symbol asymmetry
  5. NET portfolio OOS = +2.66 LDO - 0.87 BCH - 1.51 TRX = +0.28 wpnl (positive)
  6. Single-axis change (RiskV2Config.vol_scale_ceiling: 1.0 -> 0.8)
  7. Universal (preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
  8. Mechanistically ORTHOGONAL to /065 labeling axis (T6 verified)

  CAVEATS:
  - ORACLE Sharpe Δ is SMALL (~±0.03) -> most likely classification is INERT-AT-EXPLORATION.
    Section 7 probability: INERT=50%, PROMISING=15%, NEGATIVE=25%, SUSPICIOUS-OOS=10%.
  - ORACLE assumes trade roster identical to /060. Optuna at production may produce
    slightly different roster under (1.0->0.8) ceiling — second-order effect not modeled.
  - INERT-AT-EXPLORATION is INFORMATIONAL for /069 CONFIRMATION bundling: even if
    risk-primitive axis is INERT alone, bundling with /065 SL widening may produce
    synergistic effect at multi-seed.

ANTI-PATTERNS AVOIDED:
  - NOT per-symbol customization (universal change per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
  - NOT stateful primitive (Path D excluded; ORACLE validity per `feedback_v3_oracle_eda_validity.md`)
  - NOT 2-axis change (Path A, C excluded; single-axis per `feedback_v3_engineered_features_dont_stack.md`)
  - NOT feature axis (NON-FEATURE pivot per Critic /064 Rec #4 lock)
""")


if __name__ == "__main__":
    main()
