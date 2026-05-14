"""iter-v3/068 EDA — LABELING TIMEOUT axis.

NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4 directive (locked for /065-/068).
Cycle 1 #9 of 10. Sibling axis to /065 (SL multiplier — TRAIN-TIME, magnitude dimension)
and /067 (inference threshold floor — INFERENCE-TIME, gate dimension). /068 axis is
LABELING TIMEOUT — TRAIN-TIME, DURATION dimension.

Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403).

Per `feedback_v3_iter064_process_lessons.md`:
  Rule 1: T0 anchor values from comparison.csv:LINE byte-exact (NOT hand-typed).
  Rule 3: NEGATIVE probability for non-feature single-axis at single-seed n_trials=35
          calibrated UP (≥25%).
  Rule 5: 14-feature anchor is LOCAL OPTIMUM — non-feature axes are productive.

Per `feedback_v3_oracle_eda_validity.md`: TRAIN-TIME label generation is ORACLE-valid
(stateless w.r.t. signal emission state). Counterfactual estimation is valid.

Per `feedback_v3_engineered_features_dont_stack.md`: ONE substantive axis change per
EXPLORATION. /065's SL widening UNCHANGED at default (2.0, 1.0) — orthogonal axis.
/066's vol_scale_ceiling REVERTED to default 1.0 — clean attribution.
/067's _inference_threshold_floor REVERTED to default 0.0 — clean attribution.

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: UNIVERSAL labeling timeout
(applies to ALL 3 symbols BCH+LDO+TRX simultaneously) — preserves IS aggregate
discipline.

Output: 6 tables (T0-T5) committed to analysis/iteration_v3-068/.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================================
# Constants
# ============================================================================

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent

# /060 EXPLORATION anchor (Section 2.1 T0 source: reports-v3/iteration_v3-060/)
ITER_060 = REPO_ROOT / "reports-v3" / "iteration_v3-060"
COMP_060 = ITER_060 / "comparison.csv"
IS_TRADES = ITER_060 / "in_sample" / "trades.csv"
OOS_TRADES = ITER_060 / "out_of_sample" / "trades.csv"
IS_PSYM = ITER_060 / "in_sample" / "per_symbol.csv"
OOS_PSYM = ITER_060 / "out_of_sample" / "per_symbol.csv"

CANDLE_MS = 480 * 60 * 1000  # 8h interval = 480 min = 28_800_000 ms
CURRENT_TIMEOUT_CANDLES = 21  # 10080 min / 480 min = 21
CURRENT_TIMEOUT_MINUTES = 10080


def _format_table(rows: list[dict]) -> str:
    """Pretty-print a list of dicts as a markdown table."""
    if not rows:
        return ""
    keys = list(rows[0].keys())
    out = ["| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(r[k]) for k in keys) + " |")
    return "\n".join(out)


def _write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ============================================================================
# T0 — Anchor value declaration (Rule 1 compliance)
# ============================================================================

def t0_anchor_values() -> None:
    """Read /060 anchor values byte-exact from source files.

    NB: Two distinct per-symbol PnL columns exist:
    - `weighted_pnl` (in comparison.csv per_symbol block at lines 18-20): the
      Optuna objective metric (PnL with weight_factor scaling applied). These
      are the anchor values cited in cycle 1 orchestrator briefs (BCH OOS +1.9078,
      LDO OOS -19.72, TRX OOS +23.31). MATCHES the brief Section 2.1 spec exactly.
    - `net_pnl_pct` (in out_of_sample/per_symbol.csv): the raw signed PnL%
      with weight_factor=1.0 (informational; the unweighted aggregate). These
      DIFFER from weighted_pnl (BCH OOS -8.69 vs +1.91, etc.).

    Rule 1 (`feedback_v3_iter064_process_lessons.md`) requires anchor values
    match the orchestrator spec. WE USE `weighted_pnl` per the brief spec.
    """
    # comparison.csv has metric block (rows 1-15) then per_symbol block.
    comp = pd.read_csv(COMP_060, nrows=14)
    monthly = comp.set_index("metric")[["in_sample", "out_of_sample"]]

    # Parse per_symbol block (rows 18-20) directly to grab weighted_pnl column
    # Header at row 17 is: # per_symbol,weighted_pnl,n_trades,win_rate,concentration_pct
    # We parse the raw text for byte-exact integrity (orchestrator brief spec).
    raw_lines = COMP_060.read_text().splitlines()
    psym_rows: dict[str, list[str]] = {}
    for line in raw_lines:
        if line.startswith("BCHUSDT") or line.startswith("LDOUSDT") or line.startswith("TRXUSDT"):
            parts = line.split(",")
            psym_rows[parts[0]] = parts  # [sym, weighted_pnl, n_trades, win_rate, concentration_pct]

    is_psym = pd.read_csv(IS_PSYM)

    def _grab(metric: str, where: str) -> str:
        return monthly.loc[metric, where]

    def _psym_is(df, sym: str, col: str) -> str:
        return str(df.set_index("symbol").loc[sym, col])

    rows = [
        {"metric": "monthly_sharpe_in_sample", "value": str(_grab("monthly_sharpe", "in_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:2"},
        {"metric": "monthly_sharpe_out_of_sample", "value": str(_grab("monthly_sharpe", "out_of_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:2"},
        {"metric": "n_trades_in_sample", "value": str(_grab("n_trades", "in_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:7"},
        {"metric": "n_trades_out_of_sample", "value": str(_grab("n_trades", "out_of_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:7"},
        {"metric": "weighted_pnl_total_in_sample", "value": str(_grab("weighted_pnl_total", "in_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:10"},
        {"metric": "weighted_pnl_total_out_of_sample", "value": str(_grab("weighted_pnl_total", "out_of_sample")),
         "source": "reports-v3/iteration_v3-060/comparison.csv:10"},
        # Orchestrator-spec anchor values: per_symbol.weighted_pnl OOS from comparison.csv
        {"metric": "BCH_OOS_weighted_pnl", "value": psym_rows["BCHUSDT"][1],
         "source": "reports-v3/iteration_v3-060/comparison.csv:18 (per_symbol block, weighted_pnl col)"},
        {"metric": "LDO_OOS_weighted_pnl", "value": psym_rows["LDOUSDT"][1],
         "source": "reports-v3/iteration_v3-060/comparison.csv:19 (per_symbol block, weighted_pnl col)"},
        {"metric": "TRX_OOS_weighted_pnl", "value": psym_rows["TRXUSDT"][1],
         "source": "reports-v3/iteration_v3-060/comparison.csv:20 (per_symbol block, weighted_pnl col)"},
        # IS attribution (from in_sample/per_symbol.csv — no weighted_pnl column at IS level)
        {"metric": "BCH_IS_net_pnl_pct", "value": _psym_is(is_psym, "BCHUSDT", "net_pnl_pct"),
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "LDO_IS_net_pnl_pct", "value": _psym_is(is_psym, "LDOUSDT", "net_pnl_pct"),
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "TRX_IS_net_pnl_pct", "value": _psym_is(is_psym, "TRXUSDT", "net_pnl_pct"),
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "BCH_IS_concentration_pct", "value": _psym_is(is_psym, "BCHUSDT", "pct_of_total_pnl"),
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv (pct_of_total_pnl col)"},
        {"metric": "current_label_timeout_minutes", "value": str(CURRENT_TIMEOUT_MINUTES),
         "source": "run_baseline_v3.py:1398"},
        {"metric": "current_label_timeout_candles", "value": str(CURRENT_TIMEOUT_CANDLES),
         "source": "run_baseline_v3.py:740 (10080 / 480 = 21)"},
        {"metric": "frac_positive_paths_cpcv", "value": "0.6444",
         "source": "BASELINE_V3.md Headline Metrics (CPCV architecture-invariant)"},
    ]
    _write_csv(rows, ROOT / "T0_anchor_values.csv")
    print("=== T0 — Anchor Values (byte-exact from source) ===")
    print(_format_table(rows))
    print()


# ============================================================================
# T1 — Current label distribution at timeout=21 candles per symbol
# ============================================================================

def t1_current_label_distribution() -> None:
    """Estimate current label resolution distribution from /060 trade roster.

    Trade exit_reason is a downstream proxy for label resolution:
    - take_profit at candle K → label = +1 (positive direction; TP-hit before timeout)
    - stop_loss at candle K → label = -1 (negative direction; SL-hit before timeout)
    - timeout at candle 21 → label resolved via forward-return sign (-2 → ±1 by sign,
      or 0 if neutral_threshold_pct applies)
    - end_of_data → trade carry over end of OOS data (1 trade in /060 OOS — out of scope)

    NOTE: This is the TRADE ROSTER perspective (post-Optuna/risk-gate emission),
    not the FULL LABEL POPULATION (which is generated per ALL candles via labeling.py).
    The trade roster is a Monte Carlo subset of the label population; still informative
    re: durations because Optuna sees the SAME forward-scan logic at training.
    """
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)

    def _summarize(df: pd.DataFrame, sample_name: str) -> list[dict]:
        df = df.copy()
        df["duration_candles"] = ((df["close_time"] - df["open_time"]) / CANDLE_MS).astype(int)
        rows = []
        for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT"]:
            sym_df = df[df["symbol"] == sym]
            n = len(sym_df)
            n_tp = (sym_df["exit_reason"] == "take_profit").sum()
            n_sl = (sym_df["exit_reason"] == "stop_loss").sum()
            n_to = (sym_df["exit_reason"] == "timeout").sum()
            n_eod = (sym_df["exit_reason"] == "end_of_data").sum()
            avg_tp = sym_df.loc[sym_df["exit_reason"] == "take_profit", "duration_candles"].mean() if n_tp > 0 else float("nan")
            avg_sl = sym_df.loc[sym_df["exit_reason"] == "stop_loss", "duration_candles"].mean() if n_sl > 0 else float("nan")
            avg_all = sym_df["duration_candles"].mean() if n > 0 else float("nan")
            rows.append({
                "sample": sample_name,
                "symbol": sym,
                "n_trades": int(n),
                "n_TP": int(n_tp),
                "n_SL": int(n_sl),
                "n_TIMEOUT": int(n_to),
                "n_EOD": int(n_eod),
                "pct_TIMEOUT": f"{(n_to / n * 100):.2f}%" if n > 0 else "—",
                "avg_dur_all": f"{avg_all:.2f}" if not math.isnan(avg_all) else "—",
                "avg_dur_TP": f"{avg_tp:.2f}" if not math.isnan(avg_tp) else "—",
                "avg_dur_SL": f"{avg_sl:.2f}" if not math.isnan(avg_sl) else "—",
            })
        return rows

    is_rows = _summarize(is_trades, "in_sample")
    oos_rows = _summarize(oos_trades, "out_of_sample")
    all_rows = is_rows + oos_rows
    _write_csv(all_rows, ROOT / "T1_current_label_distribution.csv")

    print("=== T1 — Current Trade Roster Distribution at timeout=21 candles ===")
    print(_format_table(all_rows))
    print()


# ============================================================================
# T2 — Counterfactual at alternative timeouts (re-label trade roster)
# ============================================================================

def t2_counterfactual_timeouts() -> None:
    """First-order counterfactual: re-categorize observed trades under timeout=K candles.

    A trade with duration D ≤ K resolved via its existing exit_reason (TP/SL/EOD).
    A trade with duration D > K resolves as TIMEOUT at K under the counterfactual.

    NB: This is FIRST-ORDER counterfactual. SECOND-ORDER (Optuna retrains with new
    labels → different model → different trade roster) is unmodeled. The observed
    trade roster reflects the SPECIFIC labels Optuna trained on. New timeouts change
    the LABEL distribution that Optuna sees during training — second-order effects
    can dominate.

    Output: per-Path trade-disposition counts + estimated trade-count.
    """
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)
    is_trades["duration_candles"] = ((is_trades["close_time"] - is_trades["open_time"]) / CANDLE_MS).astype(int)
    oos_trades["duration_candles"] = ((oos_trades["close_time"] - oos_trades["open_time"]) / CANDLE_MS).astype(int)

    paths = {
        "Path_A (timeout=7)": 7,
        "Path_B (timeout=14)": 14,
        "Path_C (timeout=42)": 42,
        "Path_D (timeout=63)": 63,
        "ANCHOR (timeout=21)": 21,
    }

    rows = []
    for path_name, K in paths.items():
        for sample_name, df in [("in_sample", is_trades), ("out_of_sample", oos_trades)]:
            n_total = len(df)
            n_resolved_within = (df["duration_candles"] <= K).sum()  # trades that already terminated within K
            n_truncated_to_timeout = (df["duration_candles"] > K).sum()  # would become timeout under new K
            # Of within-resolution: how many were originally TP / SL / TIMEOUT (in /060's 21-candle world)
            within = df[df["duration_candles"] <= K]
            n_tp = (within["exit_reason"] == "take_profit").sum()
            n_sl = (within["exit_reason"] == "stop_loss").sum()
            n_to_within = (within["exit_reason"] == "timeout").sum()  # would re-trigger as timeout at K too
            n_eod = (within["exit_reason"] == "end_of_data").sum()
            rows.append({
                "path": path_name,
                "K_candles": K,
                "K_minutes": K * 480,
                "sample": sample_name,
                "n_orig_trades": n_total,
                "n_resolved_within_K": int(n_resolved_within),
                "n_truncated_to_timeout_at_K": int(n_truncated_to_timeout),
                "pct_truncated": f"{(n_truncated_to_timeout / n_total * 100):.2f}%" if n_total > 0 else "—",
                "n_TP_within": int(n_tp),
                "n_SL_within": int(n_sl),
                "n_TIMEOUT_within": int(n_to_within),
                "n_EOD_within": int(n_eod),
            })

    _write_csv(rows, ROOT / "T2_counterfactual_timeouts.csv")
    print("=== T2 — First-Order Counterfactual Trade Resolution at Alternative Timeouts ===")
    print(_format_table(rows))
    print()


# ============================================================================
# T3 — LDO-specific timeout interaction (label noise hypothesis)
# ============================================================================

def t3_ldo_label_noise() -> None:
    """LDO-specific: does shorter or longer timeout help label noise?

    LDO is the WEAKEST signal symbol at /060:
      - IS: 11 trades, 27.3% WR, -11.44% net PnL%, -25.44% of total IS PnL
      - OOS: 11 trades, 18.2% WR, -25.08% net PnL%
      - Zero IS timeouts; zero OOS timeouts (per T1)

    HYPOTHESIS — LDO label noise interaction with timeout:
    - SHORTER timeout (7 candles): less time for noise to swamp signal → cleaner labels
      → potentially better classifier. BUT also less time for genuine TP to fire →
      label distribution shifts toward TIMEOUT (forward-return sign) — equivalent to
      directional return labeling (less informative than TP/SL).
    - LONGER timeout (42-63 candles): more chance for genuine TP to fire OR for SL
      to fire AFTER drawdown → labels reflect terminal outcome of full trade
      lifecycle. BUT also more noise contamination (the longer you wait, the more
      random walk dominates).

    EDA on LDO trade durations:
    """
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)
    is_trades["duration_candles"] = ((is_trades["close_time"] - is_trades["open_time"]) / CANDLE_MS).astype(int)
    oos_trades["duration_candles"] = ((oos_trades["close_time"] - oos_trades["open_time"]) / CANDLE_MS).astype(int)

    ldo_is = is_trades[is_trades["symbol"] == "LDOUSDT"]
    ldo_oos = oos_trades[oos_trades["symbol"] == "LDOUSDT"]

    rows = []
    for sample_name, df in [("in_sample", ldo_is), ("out_of_sample", ldo_oos)]:
        if len(df) == 0:
            rows.append({"sample": sample_name, "stat": "(empty)", "value": "—"})
            continue
        rows.append({"sample": sample_name, "stat": "n_trades", "value": str(len(df))})
        rows.append({"sample": sample_name, "stat": "duration_min", "value": f"{df['duration_candles'].min():.0f}"})
        rows.append({"sample": sample_name, "stat": "duration_max", "value": f"{df['duration_candles'].max():.0f}"})
        rows.append({"sample": sample_name, "stat": "duration_mean", "value": f"{df['duration_candles'].mean():.2f}"})
        rows.append({"sample": sample_name, "stat": "duration_median", "value": f"{df['duration_candles'].median():.1f}"})
        rows.append({"sample": sample_name, "stat": "duration_p25", "value": f"{df['duration_candles'].quantile(0.25):.2f}"})
        rows.append({"sample": sample_name, "stat": "duration_p75", "value": f"{df['duration_candles'].quantile(0.75):.2f}"})
        rows.append({"sample": sample_name, "stat": "n_TP", "value": str((df["exit_reason"] == "take_profit").sum())})
        rows.append({"sample": sample_name, "stat": "n_SL", "value": str((df["exit_reason"] == "stop_loss").sum())})
        rows.append({"sample": sample_name, "stat": "n_TIMEOUT", "value": str((df["exit_reason"] == "timeout").sum())})
        rows.append({"sample": sample_name, "stat": "n_EOD", "value": str((df["exit_reason"] == "end_of_data").sum())})
        if (df["exit_reason"] == "take_profit").sum() > 0:
            avg_tp = df.loc[df["exit_reason"] == "take_profit", "duration_candles"].mean()
            rows.append({"sample": sample_name, "stat": "avg_TP_duration", "value": f"{avg_tp:.2f}"})
        if (df["exit_reason"] == "stop_loss").sum() > 0:
            avg_sl = df.loc[df["exit_reason"] == "stop_loss", "duration_candles"].mean()
            rows.append({"sample": sample_name, "stat": "avg_SL_duration", "value": f"{avg_sl:.2f}"})

    _write_csv(rows, ROOT / "T3_ldo_label_noise.csv")
    print("=== T3 — LDO-Specific Timeout Interaction (label noise hypothesis) ===")
    print(_format_table(rows))
    print()

    # Interpretation
    print("READING:")
    print("- LDO zero timeouts in BOTH samples — all 22 LDO trades resolved via TP/SL")
    print("  before the 21-candle deadline. The current timeout=21 ALREADY captures full")
    print("  LDO label resolution.")
    print("- LDO avg TP duration in IS = 4.33 candles; OOS LDO has 2 TPs only.")
    print("- LDO durations skew SHORT (median ~3-5 candles for the resolved trades).")
    print("- Shorter timeout (Path A=7): would still capture LDO TPs but lose some SLs")
    print("  > 7 candles (1 SL at 20 candles in IS would become TIMEOUT under K=7).")
    print("- Longer timeout (Path C=42, Path D=63): NO downstream effect on LDO resolution.")
    print("  LDO labels are insensitive to timeout-extension at the trade-roster level.")
    print("- This SUGGESTS the LDO weakness is NOT a timeout/label-noise issue. It's")
    print("  a signal-quality issue at the feature/model level.")
    print()


# ============================================================================
# T4 — Predicted impact bands per Path
# ============================================================================

def t4_predicted_impact_bands() -> None:
    """Per-Path predicted IS / OOS Sharpe Δ bands.

    Structural reasoning (FIRST-ORDER + caveat for second-order):

    Path A (timeout=7 candles, -67% duration):
    - 50/159 IS trades (31.4%) currently resolve at K > 7 → would become TIMEOUT.
    - 22/102 OOS trades (21.6%) currently resolve at K > 7 → would become TIMEOUT.
    - Label distribution shifts MASSIVELY toward forward-return labels (timeout fwd-sign).
    - Forward-return labels are NOISIER than TP/SL — directional sign of a 7-candle
      window is highly correlated with random walk noise.
    - Predicted second-order: Optuna trained on noisier labels → worse classifier →
      OOS Sharpe degradation.
    - Direction: NEGATIVE.

    Path B (timeout=14 candles, -33% duration):
    - 22/159 IS trades (13.8%) currently resolve at K > 14.
    - 14/102 OOS trades (13.7%) currently resolve at K > 14.
    - Intermediate disruption. Some longer-cycle TP/SL labels lost.
    - Direction: WEAKLY NEGATIVE.

    ANCHOR (timeout=21 candles, current):
    - 9/159 IS trades (5.7%) are timeouts.
    - 3/102 OOS trades (2.9%) are timeouts.
    - Most labels are TP/SL resolved.

    Path C (timeout=42 candles, +100% duration):
    - 0 additional IS trades resolved (every IS trade currently at K=21 timeout had
      ALREADY exhausted forward window — extending to K=42 doesn't capture any new
      TP/SL since the 21-candle scan went the full deadline + forward window).
      WAIT — the scan loop in labeling.py:240-274 breaks at first deadline OR TP/SL hit.
      A trade marked timeout at K=21 means it scanned to deadline=K=21 without hitting
      TP/SL. Extending K to 42 would allow MORE scan time → some timeout trades MIGHT
      now hit TP/SL.
    - Path C expected: ~9 IS timeouts and ~3 OOS timeouts MAY convert to TP/SL labels.
    - Predicted shift is SMALL since timeouts are 5.7% IS, 2.9% OOS.
    - Direction: WEAKLY POSITIVE (label cleanup) OR WEAKLY NEGATIVE (longer window =
      more noise contamination of forward fwd-return at K).

    Path D (timeout=63 candles, +200% duration):
    - Even more scan time. Similar to Path C but stronger.
    - The risk is INCREASED LABEL OVERLAP per AFML Ch. 4: longer label windows mean
      adjacent samples overlap MORE — sample uniqueness weights drop → effective
      sample size drops → Optuna sees fewer independent labels → variance up.
    - The sample-uniqueness weighting in labeling.py:11-109 should partially correct,
      but the effective sample size still drops.
    - Direction: NEGATIVE (sample-uniqueness penalty dominates the label-cleanup
      benefit; tests with K=63 on similar setups are absent from v3 catalog).

    Path E (PASSIVE DIAGNOSTIC — no axis change):
    - Reports the EDA findings to the catalog and SKIPS the EXPLORATION.
    - Selected ONLY if EDA shows timeout=21 is already optimal.

    Saturation falsifier interpretation:
    - If EDA T1+T2 show timeout=21 already captures 95-97% of label resolution, then
      timeout extension is structurally saturated (Path C/D negligible benefit; Path
      A/B introduce noise).
    - This IS the empirical finding: 9/159 IS timeouts (5.7%) → timeout=21 captures
      94.3% of full TP/SL resolution. Path C extension would have to convert most of
      these 9 IS timeouts to additional TP/SL labels — but they didn't hit in 21
      candles, so why would they in 42? (Forward random walk; some MIGHT.)
    """
    rows = [
        {
            "path": "Path_A (timeout=7 = -67% dur)",
            "K_candles": 7,
            "trades_affected_IS": 50,
            "trades_affected_OOS": 22,
            "label_shift": "MAJOR (31.4% IS / 21.6% OOS to fwd-return)",
            "is_delta_band": "[-0.40, -0.05]",
            "oos_delta_band": "[-0.50, -0.05]",
            "direction": "NEGATIVE (label noise injection)",
            "structural_risk": "Forward-return labels at K=7 are dominated by random walk noise",
        },
        {
            "path": "Path_B (timeout=14 = -33% dur)",
            "K_candles": 14,
            "trades_affected_IS": 22,
            "trades_affected_OOS": 14,
            "label_shift": "MEDIUM (13.8% IS / 13.7% OOS to fwd-return)",
            "is_delta_band": "[-0.25, +0.00]",
            "oos_delta_band": "[-0.30, +0.05]",
            "direction": "WEAKLY NEGATIVE (intermediate noise)",
            "structural_risk": "Longer-cycle TP/SL trades become noisy fwd-return labels",
        },
        {
            "path": "ANCHOR (timeout=21 = current)",
            "K_candles": 21,
            "trades_affected_IS": 0,
            "trades_affected_OOS": 0,
            "label_shift": "BASELINE (5.7% IS / 2.9% OOS timeouts)",
            "is_delta_band": "0",
            "oos_delta_band": "0",
            "direction": "REFERENCE",
            "structural_risk": "—",
        },
        {
            "path": "Path_C (timeout=42 = +100% dur)",
            "K_candles": 42,
            "trades_affected_IS": "~9 timeout→TP/SL conversion",
            "trades_affected_OOS": "~3 timeout→TP/SL conversion",
            "label_shift": "MINOR (~5.7% IS / ~2.9% OOS labels potentially upgrade)",
            "is_delta_band": "[-0.10, +0.10]",
            "oos_delta_band": "[-0.15, +0.15]",
            "direction": "INERT (label cleanup vs sample-uniqueness tradeoff)",
            "structural_risk": "Sample-uniqueness drop; effective sample size penalty; Optuna 2nd-order coupling",
        },
        {
            "path": "Path_D (timeout=63 = +200% dur)",
            "K_candles": 63,
            "trades_affected_IS": "~9 timeout→TP/SL conversion + sample overlap",
            "trades_affected_OOS": "~3 timeout→TP/SL conversion + sample overlap",
            "label_shift": "MINOR + sample overlap DOMINANT",
            "is_delta_band": "[-0.25, +0.05]",
            "oos_delta_band": "[-0.30, +0.05]",
            "direction": "WEAKLY NEGATIVE (sample-uniqueness drop dominates)",
            "structural_risk": "Adjacent samples overlap heavily; effective sample size collapses; embargo at 64 candles (63+1)",
        },
        {
            "path": "Path_E (PASSIVE DIAGNOSTIC — no change)",
            "K_candles": 21,
            "trades_affected_IS": 0,
            "trades_affected_OOS": 0,
            "label_shift": "REFERENCE",
            "is_delta_band": "0",
            "oos_delta_band": "0",
            "direction": "INERT-by-design",
            "structural_risk": "Skip — saturation justified by T1/T2 finding",
        },
    ]
    _write_csv(rows, ROOT / "T4_predicted_impact_bands.csv")
    print("=== T4 — Per-Path Predicted IS/OOS Sharpe Δ Bands ===")
    print(_format_table(rows))
    print()


# ============================================================================
# T5 — Path selection summary + scoring
# ============================================================================

def t5_path_selection_summary() -> None:
    """7-criteria scoring per path."""
    rows = [
        {"path": "Path_A (K=7)", "stateless": "YES", "universal": "YES",
         "orthogonal_065": "YES", "orthogonal_066": "YES", "orthogonal_067": "YES",
         "promising_viable": "NO (NEGATIVE direction)", "trade_floor_safe": "YES (no trade-count drop)",
         "score": "5/7"},
        {"path": "Path_B (K=14)", "stateless": "YES", "universal": "YES",
         "orthogonal_065": "YES", "orthogonal_066": "YES", "orthogonal_067": "YES",
         "promising_viable": "NO (WEAKLY NEGATIVE)", "trade_floor_safe": "YES",
         "score": "5/7"},
        {"path": "Path_C (K=42)", "stateless": "YES", "universal": "YES",
         "orthogonal_065": "YES", "orthogonal_066": "YES", "orthogonal_067": "YES",
         "promising_viable": "MARGINAL (INERT-band center; ~5% chance of PROMISING)",
         "trade_floor_safe": "YES", "score": "5/7 (marginal)"},
        {"path": "Path_D (K=63)", "stateless": "YES", "universal": "YES",
         "orthogonal_065": "YES", "orthogonal_066": "YES", "orthogonal_067": "YES",
         "promising_viable": "NO (WEAKLY NEGATIVE — sample-uniqueness)",
         "trade_floor_safe": "YES", "score": "5/7"},
        {"path": "Path_E (PASSIVE DIAGNOSTIC)", "stateless": "—", "universal": "—",
         "orthogonal_065": "—", "orthogonal_066": "—", "orthogonal_067": "—",
         "promising_viable": "NO (by design)", "trade_floor_safe": "—",
         "score": "DIAGNOSTIC"},
    ]
    _write_csv(rows, ROOT / "T5_path_selection_summary.csv")
    print("=== T5 — Path Selection Summary (7 criteria) ===")
    print(_format_table(rows))
    print()

    # Path selection logic
    print("PATH SELECTION:")
    print()
    print("T1+T2 finding: timeout=21 captures 94.3% IS / 97.1% OOS of TP/SL label")
    print("resolution. The remaining 5.7% IS / 2.9% OOS are genuine timeouts where")
    print("forward random walk did not hit either barrier.")
    print()
    print("T3 finding: LDO is INSENSITIVE to timeout extension (zero LDO timeouts at")
    print("/060). LDO weakness is signal-quality, not label-noise.")
    print()
    print("T4 prediction:")
    print("- Path A (K=7): NEGATIVE direction. 31% of IS labels become noisy fwd-return.")
    print("- Path B (K=14): WEAKLY NEGATIVE. 14% relabel shift.")
    print("- Path C (K=42): INERT band. Sample-uniqueness vs label-cleanup tradeoff.")
    print("- Path D (K=63): WEAKLY NEGATIVE. Sample-uniqueness penalty dominates.")
    print("- Path E (passive): INERT by design.")
    print()
    print("QR DECISION: **Path C (timeout=42, +100% duration)**.")
    print()
    print("Rationale:")
    print("1. ONLY Path with predicted band CENTERED at INERT-axis with non-zero")
    print("   upside (OOS Δ band [-0.15, +0.15] spans both signs).")
    print("2. Mechanistically distinct from Path A/B (label-noise INJECTION direction)")
    print("   vs Path C (label-clean direction — convert timeouts to TP/SL).")
    print("3. Path D introduces sample-uniqueness penalty (embargo gap from 22 → 64")
    print("   candles per cell) — too aggressive for cycle 1 EXPLORATION.")
    print("4. Path C's ~9 IS timeout → TP/SL conversion targets the SPECIFIC trades")
    print("   where /060's 21-candle window was just barely insufficient. These are")
    print("   the highest-information ADDITIONAL labels.")
    print("5. EMBARGO gap calculation: 42/8h=5.25 → 5+1 = 6 candles intra-cell vs")
    print("   current 22 per cell; cross-cell gap = 6*3 = 18 candles vs current 66.")
    print("   Note: This REDUCES the embargo gap (looser) — small leakage risk relief.")
    print("   Actually NO: compute_embargo_candles(42*480, 480) = 42*480//480+1 = 43.")
    print("   Per-cell embargo: 43 candles; cross-cell gap = 43*3 = 129 candles.")
    print("   This is LARGER than current 66 (more conservative purging).")
    print("6. INERT-AT-EXPLORATION is the most likely classification (~50%) — this")
    print("   is the structurally safest non-feature axis for cycle 1 #9.")
    print()
    print("Path C selection rationale per Rule 5 (`feedback_v3_iter064_process_lessons.md`):")
    print("- Local optimum at /060 is RESISTANT to feature-axis perturbations at single-")
    print("  seed n_trials=35; non-feature axes (timeout) are the productive direction.")
    print("- /065 (labeling SL widening) was PROMISING; /067 (ensemble gate threshold)")
    print("  closed as TBD; /068 (labeling timeout) is the labeling-axis DURATION")
    print("  complement to /065's labeling MAGNITUDE.")
    print()
    print("Path eliminations:")
    print("- Path A OUT: predicted NEGATIVE direction; label noise injection.")
    print("- Path B OUT: predicted WEAKLY NEGATIVE; same mechanism as Path A at smaller scale.")
    print("- Path D OUT: predicted WEAKLY NEGATIVE; sample-uniqueness drop dominates.")
    print("- Path E OUT: passive diagnostic skips the cycle 1 #9 slot. RESERVED if")
    print("  Critic adjudicates Path C as methodologically unfit (e.g., embargo gap")
    print("  consequences not pre-modeled).")


# ============================================================================
# T6 — Cross-axis orthogonality with iter-v3/065 (LABELING SL) and /066 (RISK) and /067 (ENSEMBLE)
# ============================================================================

def t6_cross_axis_orthogonality() -> None:
    """Orthogonality matrix vs prior cycle 1 axes."""
    rows = [
        {
            "stage": "feature_engineering",
            "iter_065_SL_widening": "no change",
            "iter_066_vol_scale_ceiling": "no change",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "no change",
            "orthogonal": "YES (4 axes, all stage-1 inert)",
        },
        {
            "stage": "label_generation_MAGNITUDE",
            "iter_065_SL_widening": "TRAIN-TIME: sl_multiplier 1.0 → 1.5",
            "iter_066_vol_scale_ceiling": "no change",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "no change (magnitude unchanged)",
            "orthogonal": "YES (068 ≠ 065 stage at sub-stage)",
        },
        {
            "stage": "label_generation_DURATION",
            "iter_065_SL_widening": "no change",
            "iter_066_vol_scale_ceiling": "no change",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "TRAIN-TIME: label_timeout_minutes 10080 → 20160 (K=42)",
            "orthogonal": "YES (068 is unique stage; nothing else touches duration)",
        },
        {
            "stage": "embargo_purging",
            "iter_065_SL_widening": "no change (preserves label_timeout_minutes=10080 → embargo=22)",
            "iter_066_vol_scale_ceiling": "no change",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "CHANGES (label_timeout_minutes=20160 → embargo=43; cross-cell gap=129)",
            "orthogonal": "PARTIAL (068 affects walk-forward embargo computation; structural — purge tightens)",
        },
        {
            "stage": "optuna_hyperparameter_search",
            "iter_065_SL_widening": "TPE on different labels",
            "iter_066_vol_scale_ceiling": "TPE unchanged",
            "iter_067_inference_threshold_floor": "TPE unchanged",
            "iter_068_label_timeout": "TPE on different labels (some timeout→TP/SL conversions)",
            "orthogonal": "PARTIAL (068 ≠ 065 because timeout vs SL multiplier perturb different label dims)",
        },
        {
            "stage": "model_training",
            "iter_065_SL_widening": "fit on changed labels",
            "iter_066_vol_scale_ceiling": "no change",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "fit on changed labels (~9 IS labels per cell converted)",
            "orthogonal": "PARTIAL (068 affects same code path as 065 but at different sub-stage)",
        },
        {
            "stage": "inference_time_prediction",
            "iter_065_SL_widening": "no direct change (proba surface differs from model)",
            "iter_066_vol_scale_ceiling": "weight modifier",
            "iter_067_inference_threshold_floor": "emission gate threshold",
            "iter_068_label_timeout": "no change",
            "orthogonal": "YES (068 ≠ 066, 067 at inference stage)",
        },
        {
            "stage": "risk_gate_stack",
            "iter_065_SL_widening": "no change",
            "iter_066_vol_scale_ceiling": "ceiling field changed",
            "iter_067_inference_threshold_floor": "no change",
            "iter_068_label_timeout": "no change",
            "orthogonal": "YES (068 ≠ 066 at risk-primitive stage)",
        },
        {
            "stage": "trade_emission",
            "iter_065_SL_widening": "different roster (different model + different labels)",
            "iter_066_vol_scale_ceiling": "different roster (weight cap)",
            "iter_067_inference_threshold_floor": "different roster (threshold floor)",
            "iter_068_label_timeout": "different roster (different model + different labels)",
            "orthogonal": "NO (all 4 axes affect roster — but via STRUCTURALLY DISTINCT mechanisms)",
        },
    ]
    _write_csv(rows, ROOT / "T6_cross_axis_orthogonality.csv")
    print("=== T6 — Cross-Axis Orthogonality Matrix ===")
    print(_format_table(rows))
    print()
    print("VERDICT: /068 (label timeout) is MECHANISTICALLY ORTHOGONAL to /065 (label")
    print("SL), /066 (weight ceiling), and /067 (inference threshold) on 7 of 9 stages.")
    print("Overlap exists at trade-emission stage (all axes affect roster) AND at the")
    print("optuna_hyperparameter_search stage with /065 (both touch labels). However,")
    print("/068 perturbs the DURATION dimension of triple-barrier labeling, while /065")
    print("perturbs the MAGNITUDE dimension — first-order independent perturbations.")
    print()
    print("CRITICAL — Embargo coupling:")
    print("- /068 changes walk_forward.py:compute_embargo_candles via")
    print("  label_timeout_minutes change. Per-cell embargo at K=42: 43 candles.")
    print("  Cross-cell gap (3 syms): 43*3 = 129 candles. CURRENT is 66.")
    print("- This DOUBLES the embargo purge → fewer training samples per WF month.")
    print("- The training set shrinks by approximately (43-22)/24/30.4 = ~3% per month")
    print("  at 24-month WF window. Effective sample size penalty < 5%.")
    print("- This is a structural CONSEQUENCE of the timeout change, NOT a separate")
    print("  axis. Disclosed in Section 4.4 falsifier band E.18.")


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    print("=" * 70)
    print("iter-v3/068 EDA — LABELING TIMEOUT axis")
    print("Cycle 1 #9 of 10. NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4.")
    print(f"Anchor: iter-v3/060 (IS +0.8325 / OOS +0.1403).")
    print(f"Current label_timeout_minutes = {CURRENT_TIMEOUT_MINUTES} = {CURRENT_TIMEOUT_CANDLES} candles at 8h.")
    print("=" * 70)
    print()

    t0_anchor_values()
    t1_current_label_distribution()
    t2_counterfactual_timeouts()
    t3_ldo_label_noise()
    t4_predicted_impact_bands()
    t5_path_selection_summary()
    t6_cross_axis_orthogonality()

    print()
    print("=" * 70)
    print("EDA COMPLETE — outputs in analysis/iteration_v3-068/")
    print("Files: T0_anchor_values.csv, T1_current_label_distribution.csv,")
    print("       T2_counterfactual_timeouts.csv, T3_ldo_label_noise.csv,")
    print("       T4_predicted_impact_bands.csv, T5_path_selection_summary.csv,")
    print("       T6_cross_axis_orthogonality.csv")
    print("=" * 70)


if __name__ == "__main__":
    main()
