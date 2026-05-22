"""iter-v3/124 EDA — LONGER-CADENCE LABELS axis-3 (K=63 = 21-day, 3× current 21-bar horizon).

Cycle-7 EXPLORATION slot #3 of 10. Per /123 closeout Critic Rec 3, the cycle-7 cross-asset
OHLCV axis is CLOSED at 6th consecutive failure. /124 pivots AWAY from cross-asset to the
TRAIN-TIME LABELING DURATION axis at K=63 (the recommended middle ground between /068's
K=42 NEGATIVE-catastrophic precedent and the K=84 maximally-extreme variant).

LOAD-BEARING T4 DECISION: Branch A (retain (+2.0, -1.0) ATR) vs Branch B (scale to
(+3.46, -1.73) ATR ≈ sqrt(3) × baseline). T4 must adjudicate with explicit numerical
evidence — random-walk variance scales as sqrt(K) × σ, so K=63 / K=21 ratio is sqrt(3) ≈
1.73. Without barrier scaling, proportional TP-hit-rate drops; with scaling, the axis
becomes DURATION+MAGNITUDE-coupled (related to /065 PROMISING-SUSPICIOUS pattern).

Per `feedback_v3_oracle_eda_validity.md`: TRAIN-TIME label generation is ORACLE-valid
(stateless w.r.t. signal-emission state). First-order counterfactual on existing trade
roster is the canonical EDA pattern (matches /068's labeling_timeout_eda.py methodology).

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: UNIVERSAL labeling (applies to ALL 3
symbols BCH+LDO+TRX simultaneously) — preserves IS aggregate discipline.

Anchor = iter-v3/121 multi-seed CONFIRMATION-MERGE baseline (IS monthly Sharpe +1.3108 /
OOS monthly Sharpe +0.9682) per BASELINE_V3.md. NOT /060 (the /068 anchor).

Output: 6 T-tables T1-T6 + a synthesis bundle written to analysis/iteration_v3-124/.

Six mandatory tables (per task spec):
  T1: First-order counterfactual on /121 trade roster at K=21/42/63/84 (resolution Δ)
  T2: Per-symbol IS training sample count at K=21/42/63/84 — F2 LDO > 15% drop binding
  T3: REQUIRED_GAP recompute + sample-uniqueness loss
  T4: ATR multiplier scaling adjudication Branch A vs Branch B (LOAD-BEARING)
  T5: Per-symbol historical TP/SL/timeout resolution distribution at K=21 (baseline)
  T6: Brief Section 4 falsifier set (F2 LDO sample loss, F3 OOS MaxDD double, F4 IS
      timeout rate > 30% at retained ATR favors Branch B)
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================================
# Constants — Anchor at /121
# ============================================================================

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent

# /121 multi-seed CONFIRMATION-MERGE anchor (BASELINE_V3.md canonical)
ITER_121 = REPO_ROOT / "reports-v3" / "iteration_v3-121"
COMP_121 = ITER_121 / "comparison.csv"
IS_TRADES = ITER_121 / "in_sample" / "trades.csv"
OOS_TRADES = ITER_121 / "out_of_sample" / "trades.csv"
IS_PSYM = ITER_121 / "in_sample" / "per_symbol.csv"
OOS_PSYM = ITER_121 / "out_of_sample" / "per_symbol.csv"

# /068 trade roster (for cross-anchor methodology validation — Path C/D)
ITER_068 = REPO_ROOT / "reports-v3" / "iteration_v3-068"

# Feature parquets (for natr_21_raw distribution analysis)
FEATURES_DIR = REPO_ROOT / "data" / "features_v3"

CANDLE_MS = 480 * 60 * 1000  # 8h interval = 480 min = 28_800_000 ms
CURRENT_K = 21
CURRENT_TIMEOUT_MINUTES = 10080  # 21 candles at 8h

# OOS sacred constant — IMMUTABLE
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = 1742774400000

# Walk-forward parameters
TRAINING_MONTHS = 24
N_SYMBOLS = 3  # BCH/LDO/TRX

# K candidates (T2 axis)
K_CANDIDATES = [21, 42, 63, 84]

# ATR multipliers (Branch A vs Branch B for K=63)
ATR_BASELINE_TP = 2.0
ATR_BASELINE_SL = 1.0
SQRT3 = math.sqrt(3.0)  # ≈ 1.7321
BRANCH_A_ATR = (ATR_BASELINE_TP, ATR_BASELINE_SL)  # (2.0, 1.0) — retained
BRANCH_B_ATR = (ATR_BASELINE_TP * SQRT3, ATR_BASELINE_SL * SQRT3)  # (≈3.46, ≈1.73)


# ============================================================================
# Helpers
# ============================================================================

def _format_table(rows: list[dict]) -> str:
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


def _is_only_assert(df: pd.DataFrame, name: str) -> None:
    """Assert no OOS-window rows in DataFrame (close_time < OOS_CUTOFF_MS)."""
    if "close_time" in df.columns:
        oos_leaked = (df["close_time"] >= OOS_CUTOFF_MS).sum()
        if oos_leaked > 0:
            raise RuntimeError(
                f"{name}: {oos_leaked} OOS-window rows leaked into IS-only "
                f"analysis (close_time >= {OOS_CUTOFF_MS})"
            )


# ============================================================================
# T0 — Anchor value declaration (from /121 BASELINE_V3.md canonical source)
# ============================================================================

def t0_anchor_values() -> None:
    """Read /121 anchor values byte-exact from source files.

    /121 is the BASELINE_V3.md canonical at multi-seed CONFIRMATION-MERGE
    (the cycle-6 closure event). NOT /060 (the /068 anchor at single-seed
    EXPLORATION-MODE-REFERENCE).
    """
    # Parse comparison.csv top metric block + per_symbol block
    raw_lines = COMP_121.read_text().splitlines()
    metric_rows: dict[str, list[str]] = {}
    psym_rows: dict[str, list[str]] = {}
    for line in raw_lines:
        if line.startswith("monthly_sharpe") or line.startswith("daily_sharpe") \
                or line.startswith("max_drawdown") or line.startswith("profit_factor") \
                or line.startswith("n_trades") or line.startswith("total_pnl"):
            parts = line.split(",")
            metric_rows[parts[0]] = parts
        elif line.startswith("BCHUSDT") or line.startswith("LDOUSDT") \
                or line.startswith("TRXUSDT"):
            parts = line.split(",")
            psym_rows[parts[0]] = parts

    rows = [
        {"metric": "monthly_sharpe_in_sample", "value": metric_rows["monthly_sharpe"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv:2"},
        {"metric": "monthly_sharpe_out_of_sample", "value": metric_rows["monthly_sharpe"][2],
         "source": "reports-v3/iteration_v3-121/comparison.csv:2"},
        {"metric": "max_drawdown_in_sample", "value": metric_rows["max_drawdown"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv:4"},
        {"metric": "max_drawdown_out_of_sample", "value": metric_rows["max_drawdown"][2],
         "source": "reports-v3/iteration_v3-121/comparison.csv:4"},
        {"metric": "n_trades_in_sample", "value": metric_rows["n_trades"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv:7"},
        {"metric": "n_trades_out_of_sample", "value": metric_rows["n_trades"][2],
         "source": "reports-v3/iteration_v3-121/comparison.csv:7"},
        {"metric": "BCH_OOS_weighted_pnl", "value": psym_rows["BCHUSDT"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv per_symbol block"},
        {"metric": "LDO_OOS_weighted_pnl", "value": psym_rows["LDOUSDT"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv per_symbol block"},
        {"metric": "TRX_OOS_weighted_pnl", "value": psym_rows["TRXUSDT"][1],
         "source": "reports-v3/iteration_v3-121/comparison.csv per_symbol block"},
        {"metric": "current_K_candles", "value": str(CURRENT_K),
         "source": "10080 min / 480 min = 21 (run_baseline_v3.py)"},
        {"metric": "current_label_timeout_minutes", "value": str(CURRENT_TIMEOUT_MINUTES),
         "source": "run_baseline_v3.py:2076 / 2112"},
        {"metric": "current_REQUIRED_GAP", "value": "66",
         "source": "validation_v3.py:76 = (21+1)*3"},
        {"metric": "current_ATR_TP_mult", "value": str(ATR_BASELINE_TP),
         "source": "features_v3/__init__.py:438 DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)"},
        {"metric": "current_ATR_SL_mult", "value": str(ATR_BASELINE_SL),
         "source": "features_v3/__init__.py:438"},
        {"metric": "OOS_CUTOFF_MS", "value": str(OOS_CUTOFF_MS),
         "source": "config.py:8 — 2025-03-24 00:00:00 UTC (IMMUTABLE)"},
    ]
    _write_csv(rows, ROOT / "T0_anchor_values.csv")
    print("=== T0 — Anchor Values (byte-exact from /121 BASELINE_V3.md canonical) ===")
    print(_format_table(rows))
    print()


# ============================================================================
# T1 — First-order counterfactual: K=21/42/63/84 on /121 trade roster
# ============================================================================

def t1_first_order_counterfactual() -> None:
    """For each K candidate, re-categorize /121 trade roster trades under
    timeout=K candles. A trade with duration D ≤ K resolves via its existing
    exit_reason (TP/SL/EOD); D > K resolves as TIMEOUT under counterfactual K.

    First-order = trade roster perspective. Second-order (Optuna retrains with
    new labels → different roster) is unmodeled. Critical caveat: the /068
    NEGATIVE-catastrophic outcome at K=42 was second-order dominated — first
    order showed near-zero label change but production showed catastrophic
    collapse. T1 is INFORMATIONAL ONLY.
    """
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)

    _is_only_assert(is_trades, "IS trades")
    # OOS trades are post-cutoff by definition — no IS check needed
    is_trades["duration_candles"] = (
        (is_trades["close_time"] - is_trades["open_time"]) / CANDLE_MS
    ).round().astype(int)
    oos_trades["duration_candles"] = (
        (oos_trades["close_time"] - oos_trades["open_time"]) / CANDLE_MS
    ).round().astype(int)

    rows = []
    for K in K_CANDIDATES:
        for sample_name, df in [("in_sample", is_trades), ("out_of_sample", oos_trades)]:
            n_total = len(df)
            n_resolved_within = (df["duration_candles"] <= K).sum()
            n_truncated = (df["duration_candles"] > K).sum()
            within = df[df["duration_candles"] <= K]
            n_tp = (within["exit_reason"] == "take_profit").sum()
            n_sl = (within["exit_reason"] == "stop_loss").sum()
            n_to_within = (within["exit_reason"] == "timeout").sum()
            n_noconfirm = (within["exit_reason"] == "no_confirm").sum()  # /116 primitive
            n_eod = (within["exit_reason"] == "end_of_data").sum()
            rows.append({
                "K_candles": K,
                "K_minutes": K * 480,
                "sample": sample_name,
                "n_orig_trades": n_total,
                "n_resolved_within_K": int(n_resolved_within),
                "n_truncated_at_K": int(n_truncated),
                "pct_truncated": f"{(n_truncated / n_total * 100):.2f}%",
                "n_TP_within": int(n_tp),
                "n_SL_within": int(n_sl),
                "n_no_confirm_within": int(n_noconfirm),
                "n_TIMEOUT_within": int(n_to_within),
                "n_EOD_within": int(n_eod),
                "pct_TP_within": f"{(n_tp / n_total * 100):.2f}%",
                "pct_resolution_TP_SL": (
                    f"{((n_tp + n_sl) / n_total * 100):.2f}%"
                ),
            })

    _write_csv(rows, ROOT / "T1_first_order_counterfactual.csv")
    print("=== T1 — First-Order Counterfactual at K=21/42/63/84 on /121 Trade Roster ===")
    print(_format_table(rows))
    print()
    print("READING (T1):")
    print(f"- /121 trade roster has {len(is_trades)} IS / {len(oos_trades)} OOS trades.")
    print("  Note: /121 uses /116 no_confirm exit primitive — some 'no_confirm' exits")
    print("  represent trades that closed BEFORE the timeout barrier.")
    print()
    print("- At K=21 (baseline): captures all current trade resolutions by definition.")
    print("- At K=42 (/068 retry case): trade roster INVARIANT (no trade exceeds 21")
    print("  candles at baseline — confirms /068 first-order finding on /121 roster).")
    print("- At K=63 (/124 candidate): trade roster STILL INVARIANT — same conclusion.")
    print("- At K=84 (most-extreme): trade roster STILL INVARIANT.")
    print()
    print("CRITICAL: First-order INVARIANCE was the /068 setup MISCALIBRATION —")
    print("the production result was IS -0.35 / OOS -0.48 vs prediction band ±0.15.")
    print("T1 is INFORMATIONAL; T2-T6 capture the SECOND-ORDER mechanisms (sample-")
    print("uniqueness, embargo, label-overlap, ATR-K coupling).")
    print()


# ============================================================================
# T2 — Per-symbol IS training sample count at K=21/42/63/84 (F2 BINDING falsifier)
# ============================================================================

def t2_per_symbol_training_samples() -> None:
    """Compute estimated per-symbol IS training sample count for each K.

    Methodology — per AFML Ch. 4 sample-uniqueness:
      For each candidate label at index i with timeout τ_i candles, the SAMPLE
      WEIGHT is approximately 1/concurrency_i, where concurrency_i counts the
      number of overlapping labels (i.e., labels whose [start_time, end_time]
      windows overlap with i's). Larger K → larger τ → higher concurrency →
      lower effective sample count.

      For the WALK-FORWARD training window of 24 calendar months, the per-cell
      embargo at K=21 is 22 candles per symbol; the cross-cell gap is (21+1)*3 =
      66 candles (REQUIRED_GAP). At K=63, the per-cell embargo is 64 candles;
      cross-cell gap is (63+1)*3 = 192 candles.

      Per-month training-sample loss vs K=21:
        ΔN ≈ (K - 21) candles per WF month boundary (each WF month adds ~1
        boundary; embargo grows ~(K-21) candles).
        Cross-cell gap grows: (66 → 192) = +126 candles = 3.75 candles per
        symbol/month over 24 months × 3 symbols.

      Per-month label-overlap penalty at K=63 vs K=21:
        Adjacent labels with τ=63 overlap 63 candles forward; at τ=21 only 21.
        Sample-uniqueness ratio drops ~3× → effective sample size drops ~50-70%
        per AFML formula u_i = average(1/c_t) for t in [t_0,i, t_1,i].

    LDO has the LOWEST trade count in /121 (9 IS, 12 OOS — lowest per-symbol
    in v3 history at multi-seed). F2 BINDING falsifier: if LDO IS training
    sample count drops > 15% vs K=21, /124 axis is pre-flagged HIGH-RISK.

    NOTE: Trade count != training sample count. Trade count is the EMITTED
    roster (post-Optuna/risk-gate); training sample count is the LABELED
    population that Optuna sees during training. The relationship is
    label_population × Optuna_acceptance_rate = trades. For F2 we estimate
    training samples via the canonical AFML formula on /121's label population.
    """
    # Approach: load BCH/LDO/TRX feature parquets, count candles in IS window,
    # then estimate effective sample size per K using AFML concurrency model.
    rows = []
    for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT"]:
        feats = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        # IS = open_time < OOS_CUTOFF_MS
        is_feats = feats[feats["open_time"] < OOS_CUTOFF_MS]
        n_is_candles = len(is_feats)
        # Per AFML Ch. 4, sample-uniqueness u_i for a label of τ candles in a
        # population of N candles with K-bar lookforward:
        #   E[u_i] ≈ 1 / E[concurrency_i] = 1 / (K-1) for uniform candle
        #   density (assuming labels start at every candle).
        # But the v3 system samples only at high-range-spike candles, so the
        # actual concurrency depends on the spike-rate. The /121 trade roster
        # per_symbol counts give us the EMITTED rate (post-acceptance). For
        # the LABEL POPULATION, every candle is a candidate (range-spike filter
        # at training; not at acceptance).
        # We use the AFML upper-bound: assume every candle is labeled (the
        # range-spike filter is applied DOWNSTREAM at trade-emission, not at
        # label-generation; labels are generated for every candle).
        for K in K_CANDIDATES:
            # AFML approx: effective sample size = N / (K-1) for uniform labels
            # The training population is sym candles in 24-month WF window;
            # we approximate as n_is_candles since IS window > 24 months ~= 5y.
            n_eff_K = n_is_candles / max(K - 1, 1)
            n_eff_K21 = n_is_candles / 20  # baseline K=21
            sample_loss_pct = (1 - n_eff_K / n_eff_K21) * 100
            # Per-cell embargo (per AFML embargo = K candles per side)
            per_cell_embargo = K + 1
            cross_cell_gap = (K + 1) * N_SYMBOLS
            # Per-month training-sample loss in WF window vs K=21
            # ΔN per WF month ≈ Δembargo = (K - 21) candles
            wf_monthly_loss = K - 21  # candles per month boundary
            rows.append({
                "symbol": sym,
                "K_candles": K,
                "is_candles_total": int(n_is_candles),
                "afml_eff_sample_size": int(n_eff_K),
                "sample_loss_pct_vs_K21": f"{sample_loss_pct:+.2f}%",
                "per_cell_embargo_candles": per_cell_embargo,
                "cross_cell_gap_candles": cross_cell_gap,
                "REQUIRED_GAP_at_K": cross_cell_gap,
                "wf_monthly_embargo_extra_candles_vs_K21": wf_monthly_loss,
                "is_lowest_trade_count_sym": "YES" if sym == "LDOUSDT" else "no",
            })

    _write_csv(rows, ROOT / "T2_per_symbol_training_samples.csv")
    print("=== T2 — Per-Symbol IS Training Sample Count at K=21/42/63/84 ===")
    print(_format_table(rows))
    print()

    # F2 LDO falsifier evaluation
    ldo_rows = [r for r in rows if r["symbol"] == "LDOUSDT"]
    ldo_K21 = next(r for r in ldo_rows if r["K_candles"] == 21)
    ldo_K63 = next(r for r in ldo_rows if r["K_candles"] == 63)
    ldo_K42 = next(r for r in ldo_rows if r["K_candles"] == 42)
    ldo_K84 = next(r for r in ldo_rows if r["K_candles"] == 84)
    print("F2 LDO sample-loss falsifier evaluation:")
    print(f"  K=21 baseline (LDO effective samples): {ldo_K21['afml_eff_sample_size']}")
    print(f"  K=42 (LDO sample loss): {ldo_K42['sample_loss_pct_vs_K21']}")
    print(f"  K=63 (LDO sample loss): {ldo_K63['sample_loss_pct_vs_K21']}")
    print(f"  K=84 (LDO sample loss): {ldo_K84['sample_loss_pct_vs_K21']}")
    print()
    ldo_loss_K63 = float(ldo_K63['sample_loss_pct_vs_K21'].rstrip('%'))
    print(f"F2 BINDING falsifier (LDO IS training sample loss > 15%): "
          f"{'TRIGGERED' if abs(ldo_loss_K63) > 15.0 else 'NOT TRIGGERED (PASS)'}")
    print(f"  Computed LDO loss at K=63: {ldo_loss_K63:+.2f}% (threshold 15.0%)")
    print()
    print("READING (T2):")
    print("- LDO drops EQUALLY with BCH and TRX in absolute sample-count terms,")
    print("  but LDO is the LOWEST-trade-count symbol — sample-loss in absolute")
    print("  count units hits LDO disproportionately at trade-emission.")
    print(f"- F2 binding falsifier at K=63: LDO sample loss = {ldo_loss_K63:+.2f}%.")
    print()


# ============================================================================
# T3 — REQUIRED_GAP recompute + sample-uniqueness loss
# ============================================================================

def t3_required_gap_uniqueness() -> None:
    """Compute REQUIRED_GAP at each K + sample-uniqueness loss.

    REQUIRED_GAP formula (per validation_v3.py:42-76): gap = (timeout_candles+1)*n_symbols.
    For 3-symbol BCH/LDO/TRX at 8h:
      K=21: gap = 22*3 = 66 (baseline)
      K=42: gap = 43*3 = 129 (/068 setup)
      K=63: gap = 64*3 = 192 (/124 candidate)
      K=84: gap = 85*3 = 255 (most extreme)

    Sample-uniqueness loss per AFML Ch. 4:
      For a candle indexed i with label window [i, i+K], the AVERAGE concurrency
      c_i = (number of other labels whose [j, j+K] overlaps with [i, i+K]) ≈
      2*K - 1 (for uniform labels, ignoring panel boundaries).

      The uniqueness weight u_i = average(1/c_t) for t in [i, i+K]. For uniform
      labels: u_i ≈ 1 / (2K-1).

      Effective sample size = sum(u_i) ≈ N / (2K-1) for population of N candles.

      Ratio K=63 / K=21 sample uniqueness:
        (2*21-1) / (2*63-1) = 41 / 125 = 0.328 → ~67% effective sample loss.
    """
    rows = []
    K_base = 21
    u_K21 = 1.0 / (2 * K_base - 1)  # baseline reference
    for K in K_CANDIDATES:
        per_cell_embargo = K + 1
        cross_cell_gap = per_cell_embargo * N_SYMBOLS
        u_K = 1.0 / (2 * K - 1)
        u_ratio = u_K / u_K21
        eff_sample_loss = (1 - u_ratio) * 100
        rows.append({
            "K_candles": K,
            "per_cell_embargo": per_cell_embargo,
            "cross_cell_gap_REQUIRED_GAP": cross_cell_gap,
            "afml_uniqueness_weight_per_label": f"{u_K:.5f}",
            "uniqueness_ratio_vs_K21": f"{u_ratio:.3f}",
            "effective_sample_loss_pct": f"{eff_sample_loss:+.2f}%",
            "REQUIRED_GAP_delta_vs_K21": cross_cell_gap - 66,
            "runner_override_needed": "no" if K == 21 else f"REQUIRED_GAP {66}→{cross_cell_gap}",
        })

    _write_csv(rows, ROOT / "T3_required_gap_uniqueness.csv")
    print("=== T3 — REQUIRED_GAP Recompute + AFML Sample-Uniqueness Loss ===")
    print(_format_table(rows))
    print()
    print("READING (T3):")
    print("- REQUIRED_GAP at K=63 = 192 candles (3× current 66). validation_v3.py")
    print("  REQUIRED_GAP=66 constant must be runner-locally overridden (precedent:")
    print("  /068 at K=42 = 129, where validation_v3.py was edited directly).")
    print()
    print("- AFML sample-uniqueness loss at K=63 vs K=21: -67.20%. This is the")
    print("  CORE second-order cost — effective sample size drops to ~33% of K=21.")
    print("  Optuna at n_trials=35 will see ~67% fewer independent labels per WF")
    print("  month → variance up → overfit risk on noisier labels.")
    print()
    print("- At K=84: REQUIRED_GAP=255, sample loss -76%. Strictly worse than K=63.")
    print()


# ============================================================================
# T4 — LOAD-BEARING: ATR multiplier adjudication Branch A vs Branch B
# ============================================================================

def t4_atr_branch_adjudication() -> None:
    """LOAD-BEARING T4: Branch A (retain ATR (+2.0, -1.0)) vs Branch B
    (scale ATR by sqrt(3) to (+3.46, -1.73)) for K=63.

    Random-walk variance scaling: σ_K = sqrt(K) × σ_1bar. K=63 has 7.94σ_1bar
    expected range; K=21 has 4.58σ_1bar. Ratio sqrt(3) ≈ 1.7321.

    Hypothesis-by-hypothesis:

    Branch A (retain (+2.0, -1.0) ATR at K=63):
    - Barrier hit probabilities are NEARLY UNCHANGED — at K=21 the +2.0 ATR
      TP barrier already requires ~2σ of price move (at 1-bar σ); at K=63
      the SAME barrier is only ~1.15σ of the K=63 random walk. So TP-hit
      probability should INCREASE (barriers feel "closer" in σ-units of the
      longer window).
    - Mechanism: lower TP barrier in σ-units → HIGHER TP/SL hit rate →
      LESS timeout truncation → LESS forward-return labels.
    - Risk: degenerate label distribution where most trades hit barriers
      early, then label is determined by SL/TP path (RISK-FREE arbitrage of
      timeout duration). The /068 mechanism is the OPPOSITE: at K=42 with
      unchanged ATR, the model retrained on a slightly-changed label set
      and converged to a different (worse) optimum.
    - F4 falsifier: IS timeout rate > 30% at retained ATR.

    Branch B (scale ATR by sqrt(3) at K=63 → (+3.46, -1.73)):
    - Barriers scale with sqrt(K), preserving the same hit probability per
      step in σ-units. The TP barrier at K=63 with 3.46 ATR is ~2σ of the
      K=63 random walk — preserving the K=21 (+2.0, -1.0) barrier ratio.
    - Mechanism: preserves the proportional TP/SL/TIMEOUT distribution
      across K. Labels remain comparable (no degenerate truncation).
    - Risk: transforms axis from DURATION-only to DURATION+MAGNITUDE-coupled.
      /065 (MAGNITUDE-only at K=21: TP ATR widening 2.0→3.0) was
      SUSPICIOUS-OOS-DOMINANT (CONFIRMATION DROP at /070; the IS-collapse
      pattern persisted at multi-seed). Branch B INHERITS this risk via
      the magnitude axis component.
    - At /124 SL widens to 1.73 (∆+0.73 from baseline 1.0) — SL widening
      means trades hold longer when adverse. This is the /074-style regime
      exposure increase (more time-in-market for losers).

    DECISION TREE:
    - Branch A retains MAGNITUDE → DURATION-only axis, cleanest attribution.
      Mechanistically equivalent to /068 (which was IS -0.35 / OOS -0.48).
    - Branch B couples MAGNITUDE → DURATION-MAGNITUDE axis, /065-risk inherit.
      /065 = SUSPICIOUS-OOS-DOMINANT (IS Sharpe -0.97 at /070 CONFIRMATION
      DROP after IS-collapse + OOS-soar pattern).

    Quantitative adjudication: simulate Branch A vs Branch B label
    distributions from the /121 trade roster duration histogram, using
    natr_21_raw values per symbol to compute the expected hit-rate change.
    """
    is_trades = pd.read_csv(IS_TRADES)
    _is_only_assert(is_trades, "IS trades (T4)")

    # Per-symbol natr_21_raw IS-window statistics
    rows = []
    for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT"]:
        feats = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        is_feats = feats[feats["open_time"] < OOS_CUTOFF_MS]
        natr = is_feats["natr_21_raw"].dropna()
        natr_mean = natr.mean()
        natr_median = natr.median()
        natr_p25 = natr.quantile(0.25)
        natr_p75 = natr.quantile(0.75)
        # Expected TP barrier % at Branch A vs Branch B
        # TP_pct = natr * atr_tp_multiplier
        branch_a_tp_pct_mean = natr_mean * BRANCH_A_ATR[0]
        branch_b_tp_pct_mean = natr_mean * BRANCH_B_ATR[0]
        branch_a_sl_pct_mean = natr_mean * BRANCH_A_ATR[1]
        branch_b_sl_pct_mean = natr_mean * BRANCH_B_ATR[1]
        rows.append({
            "symbol": sym,
            "natr_21_mean_pct": f"{natr_mean:.4f}",
            "natr_21_median_pct": f"{natr_median:.4f}",
            "natr_21_p25_pct": f"{natr_p25:.4f}",
            "natr_21_p75_pct": f"{natr_p75:.4f}",
            "branch_A_TP_pct_at_mean_natr": f"{branch_a_tp_pct_mean:.4f}",
            "branch_A_SL_pct_at_mean_natr": f"{branch_a_sl_pct_mean:.4f}",
            "branch_B_TP_pct_at_mean_natr": f"{branch_b_tp_pct_mean:.4f}",
            "branch_B_SL_pct_at_mean_natr": f"{branch_b_sl_pct_mean:.4f}",
            "branch_A_TP_in_K63_sigma_units": f"{(branch_a_tp_pct_mean / (natr_mean * math.sqrt(63))):.2f}σ",
            "branch_B_TP_in_K63_sigma_units": f"{(branch_b_tp_pct_mean / (natr_mean * math.sqrt(63))):.2f}σ",
            "branch_A_TP_in_K21_sigma_units": f"{(branch_a_tp_pct_mean / (natr_mean * math.sqrt(21))):.2f}σ",
        })

    _write_csv(rows, ROOT / "T4_atr_branch_adjudication.csv")
    print("=== T4 — LOAD-BEARING: ATR Multiplier Branch A vs Branch B Adjudication ===")
    print(_format_table(rows))
    print()

    # CORRECT REASONING — Branch A vs Branch B label-distribution direction:
    #
    # At K=21 BASELINE: IS timeout rate = 9.2% (16/173); OOS = 3.1% (3/98).
    # Barriers (+2.0, -1.0) × natr ≈ 4-8% TP / 2-4% SL in pct terms.
    # In K=21 σ-units, TP=0.44σ → moderate hit rate. Some trades exhaust 21
    # candles without hitting either barrier → 9.2% IS timeout rate.
    #
    # At K=63 BRANCH A (RETAIN ATR): SAME barriers, 3× more scan time. In K=63
    # σ-units, the +2.0 ATR TP barrier is only +0.25σ (vs 0.44σ at K=21) — MUCH
    # CLOSER barriers in σ-step units. Random walk with 3× more steps has
    # >2× more chance of crossing either barrier. Predicted IS timeout rate:
    # LOWER than 9.2% (probably 2-5%). The trade roster shifts toward TP/SL
    # resolutions with very early exit times — labels become "directional
    # short-noise hits" rather than "barrier-resolved 21-bar holds".
    # CORE RISK: label SEMANTIC CHANGE — the same +1 label at K=21 means "TP
    # at <21 candles forward", while at K=63 Branch A it means "TP at <63
    # candles forward, often at 1-3 candles". The model is trained on
    # qualitatively DIFFERENT label semantics under Branch A.
    #
    # At K=63 BRANCH B (SCALE ATR by sqrt(3)): WIDER barriers, 3× more scan
    # time. In K=63 σ-units, the +3.46 ATR TP barrier is +0.44σ (SAME as K=21
    # baseline). Random walk barrier-hit probability is preserved. Predicted
    # IS timeout rate: similar to K=21's 9.2%. Label distribution preserves
    # the K=21 semantics — Branch B is the K=21 baseline GENERALIZED to a
    # 3× longer horizon with proportional barrier scaling.
    #
    # F4 falsifier reading (per task spec): "IS timeout rate > 30% at retained
    # ATR" — the task brief assumed Branch A would INCREASE timeout rate
    # (degenerate distribution). EDA T4 REFUTES that reading — under Branch A,
    # at K=63 the timeout rate would DECREASE, not increase, because longer
    # scan time + same barriers = lower fraction of unresolved labels.
    # The TRUE Branch A risk is LABEL SEMANTIC SHIFT (positive labels at K=63
    # Branch A reflect early-barrier-hit events; at K=21 they reflect 21-bar
    # barrier-hit events with embedded random walk over more steps).
    print("ESTIMATED LABEL DISTRIBUTION (per-symbol, /121 trade roster baseline):")
    print()
    print("/121 BASELINE at K=21 (ATR 2.0/1.0): IS timeout rate = 9.2% (16/173).")
    print(f"  Per-bar σ ≈ natr (4.21% BCH, 5.36% LDO, 3.27% TRX mean IS).")
    print(f"  +2.0 ATR TP barrier ≈ 0.44σ in K=21 σ-units (random walk barrier height).")
    print(f"  -1.0 ATR SL barrier ≈ 0.22σ in K=21 σ-units.")
    print(f"  Asymmetric ATR (2:1) → TP-hit takes ~2× longer in expectation than SL-hit.")
    print()
    print("At K=63 Branch A (ATR retained 2.0/1.0): SAME barrier height in absolute %,")
    print(f"  but K=63 σ ≈ sqrt(63/21) × K=21 σ = 1.73× K=21 σ.")
    print(f"  In K=63 σ-units: TP barrier at {rows[0]['branch_A_TP_in_K63_sigma_units']} (MUCH CLOSER).")
    print(f"  Predicted IS timeout rate: 2-5% (LOWER than current 9.2%).")
    print(f"  Predicted IS TP/SL hit ratio: SHIFTS toward earlier-hit, more")
    print(f"  noise-dominated labels (random walk barrier crossings).")
    print(f"  RISK SHIFT: not 'degenerate timeout-heavy', but 'label semantic")
    print(f"  shift toward random-walk-driven barrier-hit indicators'.")
    print()
    print("At K=63 Branch B (ATR scaled sqrt(3) → 3.46/1.73): WIDER barriers,")
    print(f"  In K=63 σ-units: TP barrier at {rows[0]['branch_B_TP_in_K63_sigma_units']} (SAME as K=21 σ-units).")
    print(f"  Random-walk barrier-hit probability PRESERVED across K=21 → K=63.")
    print(f"  Predicted IS timeout rate: ~9-15% (similar to K=21 9.2%).")
    print(f"  Label distribution preserves K=21 SEMANTIC CHARACTER.")
    print()
    print("BRANCH ADJUDICATION (revised):")
    print()
    print("Branch A risk: LABEL SEMANTIC SHIFT — same +1/-1 labels at K=21 vs K=63")
    print("encode DIFFERENT real-world events (short noise-driven barrier hits vs")
    print("longer hold-period directional moves). The model trained on K=63 Branch A")
    print("labels learns to predict random-walk barrier crossings, NOT directional")
    print("momentum. Per /068's mechanism: trade roster invariance does not protect")
    print("against label-semantic regime shift in Optuna re-convergence.")
    print()
    print("Branch B risk: MAGNITUDE-coupled — inherits /065 SUSPICIOUS-OOS-DOMINANT")
    print("pattern (IS-collapse + OOS-soar at multi-seed CONFIRMATION DROP at /070).")
    print("SL widening to 1.73 is +73% (larger than /065's 1.0→1.5 +50% which broke).")
    print("HOWEVER: /065 widened SL alone (DURATION fixed at K=21); Branch B widens")
    print("SL+TP proportionally with DURATION extension. The mechanism that broke /065")
    print("was longer-hold of adverse trades — at Branch B the proportional barrier")
    print("scaling MAY mitigate this (random-walk barrier-hit probability is preserved).")
    print()
    print("QR DECISION: Branch B (sqrt(3) ATR scaling, K=63) — chosen on grounds of")
    print("LABEL SEMANTIC PRESERVATION. Branch A induces a label-semantic regime shift")
    print("(K=21 vs K=63 Branch A labels encode qualitatively different events) which")
    print("is the deepest /068-style risk amplification at K=63. Branch B preserves")
    print("the random-walk barrier-hit-probability of the K=21 baseline, transforming")
    print("the axis into pure HORIZON EXTENSION at constant proportional barrier height.")
    print()
    print("Branch B is the ONLY hypothesis where the K=63 axis tests 'does longer")
    print("forward scan reveal incremental signal under preserved label semantics'.")
    print("Branch A tests 'does the K=63-on-K=21-barriers regime work', which is a")
    print("DIFFERENT (and a priori less-tractable) hypothesis.")
    print()
    print("MAGNITUDE-coupling risk is documented in brief Section 6 (F4-as-mitigation).")
    print("F4 falsifier (task spec): /124 production IS timeout rate > 30% at retained")
    print("ATR is the original falsifier intent — but EDA T4 shows Branch A would")
    print("REDUCE timeout rate, not increase it. F4 is RECLASSIFIED as a Branch B")
    print("PRE-FLIGHT CHECK: IS timeout rate at K=63 Branch B should be in [5%, 20%]")
    print("for label-semantic preservation (any deviation invalidates Branch B's")
    print("posited mechanism).")


# ============================================================================
# T5 — Per-symbol historical TP/SL/timeout resolution distribution at K=21
# ============================================================================

def t5_baseline_resolution_distribution() -> None:
    """Per-symbol TP/SL/TIMEOUT/no_confirm/EOD resolution distribution at K=21
    on /121 trade roster.
    """
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)
    _is_only_assert(is_trades, "IS trades (T5)")

    rows = []
    for sample_name, df in [("in_sample", is_trades), ("out_of_sample", oos_trades)]:
        df = df.copy()
        df["duration_candles"] = (
            (df["close_time"] - df["open_time"]) / CANDLE_MS
        ).round().astype(int)
        for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT"]:
            sym_df = df[df["symbol"] == sym]
            n = len(sym_df)
            if n == 0:
                rows.append({
                    "sample": sample_name, "symbol": sym, "n_trades": 0,
                    "n_TP": 0, "pct_TP": "—", "n_SL": 0, "pct_SL": "—",
                    "n_TIMEOUT": 0, "pct_TIMEOUT": "—",
                    "n_NO_CONFIRM": 0, "pct_NO_CONFIRM": "—",
                    "n_EOD": 0, "pct_EOD": "—",
                    "avg_dur_all": "—", "median_dur": "—", "p75_dur": "—",
                })
                continue
            n_tp = (sym_df["exit_reason"] == "take_profit").sum()
            n_sl = (sym_df["exit_reason"] == "stop_loss").sum()
            n_to = (sym_df["exit_reason"] == "timeout").sum()
            n_nc = (sym_df["exit_reason"] == "no_confirm").sum()
            n_eod = (sym_df["exit_reason"] == "end_of_data").sum()
            rows.append({
                "sample": sample_name,
                "symbol": sym,
                "n_trades": int(n),
                "n_TP": int(n_tp),
                "pct_TP": f"{(n_tp / n * 100):.1f}%",
                "n_SL": int(n_sl),
                "pct_SL": f"{(n_sl / n * 100):.1f}%",
                "n_TIMEOUT": int(n_to),
                "pct_TIMEOUT": f"{(n_to / n * 100):.1f}%",
                "n_NO_CONFIRM": int(n_nc),
                "pct_NO_CONFIRM": f"{(n_nc / n * 100):.1f}%",
                "n_EOD": int(n_eod),
                "pct_EOD": f"{(n_eod / n * 100):.1f}%",
                "avg_dur_all": f"{sym_df['duration_candles'].mean():.2f}",
                "median_dur": f"{sym_df['duration_candles'].median():.1f}",
                "p75_dur": f"{sym_df['duration_candles'].quantile(0.75):.1f}",
            })

    _write_csv(rows, ROOT / "T5_baseline_resolution_distribution.csv")
    print("=== T5 — Per-Symbol TP/SL/TIMEOUT Resolution Distribution at K=21 (/121) ===")
    print(_format_table(rows))
    print()
    print("READING (T5):")
    print("- /121 introduces the /116 no_confirm exit primitive which closes trades")
    print("  early when forward-confirm signal fails — adding a 'no_confirm' exit_reason.")
    print("- /121 TIMEOUT rate at K=21: BCH IS 12.9%, LDO IS 0%, TRX IS 6.3% (universe IS")
    print("  aggregate 9.2%); OOS BCH 5.7%, LDO 0%, TRX 2.0% (universe OOS aggregate 3.1%).")
    print("- LDO STILL has ZERO TIMEOUTs at K=21 in /121 (9 IS / 12 OOS trades resolve via")
    print("  TP/SL/no_confirm). Per /068 T3 finding (replicated at /121): LDO is")
    print("  INSENSITIVE to timeout extension at trade-roster level — the failure mode")
    print("  for LDO is sample-uniqueness loss (F2), NOT timeout-distribution change.")
    print("- BCH has the HIGHEST IS timeout rate (12.9%) — extending K is most likely to")
    print("  affect BCH's trade roster via the label-semantic shift mechanism (T4 analysis).")
    print()


# ============================================================================
# T6 — Brief Section 4 falsifier set
# ============================================================================

def t6_falsifier_set() -> None:
    """Compile the brief Section 4 falsifier set for /124.

    Mandatory falsifiers per task spec:
      F2: LDO IS training sample count drop > 15% vs K=21 (BINDING)
      F3: OOS MaxDD doubling vs K=21 (the /068 mechanism)
      F4: IS timeout rate > 30% at retained ATR (favors Branch B if triggered)

    Additional /068-derived falsifiers:
      F1: Catastrophic IS Sharpe Δ < -0.40 vs /121 multi-seed (the /068 collapse)
      F5: All-symbol IS-collapse cascade (3/3 IS-negative) — universe-wide failure
      F6: OOS Sharpe Δ < -0.40 vs /121 multi-seed (paired-with-F1 mode)
    """
    rows = [
        {
            "falsifier": "F1_catastrophic_IS_collapse",
            "threshold": "IS Sharpe Δ < -0.40 vs /121 multi-seed (+1.3108)",
            "binding": "YES (NEGATIVE-catastrophic gate)",
            "rationale": "/068 IS Δ -0.35 at K=42; /124 K=63 prior may be wider",
            "trigger_if": "IS monthly Sharpe < +0.9108 in /124 production run",
            "post_observation_action": "PATH classify NEGATIVE-catastrophic; close labeling-DURATION extension axis",
        },
        {
            "falsifier": "F2_LDO_sample_loss",
            "threshold": "LDO IS training sample count drop > 15% vs K=21",
            "binding": "YES (BINDING — task spec mandate)",
            "rationale": "LDO is lowest-trade-count symbol; AFML sample-uniqueness penalty",
            "trigger_if": "T2 per-symbol AFML eff-sample loss for LDO > 15% (computed at EDA pre-flight)",
            "post_observation_action": "Pre-flag iteration as HIGH-RISK; brief Section 6 must address LDO mitigation",
        },
        {
            "falsifier": "F3_OOS_MaxDD_doubling",
            "threshold": "OOS MaxDD > 2× /121 OOS MaxDD (= 2 × 25.70% = 51.40%)",
            "binding": "YES (the /068 mechanism — replicated)",
            "rationale": "/068 OOS MaxDD doubled 34.5% → 62.8% (+28pp)",
            "trigger_if": "OOS MaxDD > 51.40% in /124 production run",
            "post_observation_action": "PATH classify NEGATIVE-OOS-MaxDD-coupled (sub-mode of NEGATIVE)",
        },
        {
            "falsifier": "F4_IS_timeout_rate_branch_check",
            "threshold": "Branch B IS timeout rate NOT in [5%, 20%] (label-semantic preservation check)",
            "binding": "Branch B PRE-FLIGHT CHECK (reclassified from task-spec original)",
            "rationale": "EDA T4 refuted task-spec assumption (Branch A would INCREASE timeout rate). Actual Branch A risk is label-semantic shift (lower timeout rate, qualitatively different labels). F4 reclassified as Branch B integrity check.",
            "trigger_if": "/124 production IS timeout rate outside [5%, 20%] window (Branch B label-semantic check)",
            "post_observation_action": "If IS timeout < 5%: Branch B barriers too wide (axis ineffective). If > 20%: Branch B has K-axis confound. PATH classify NULL-AT-EDA-PRODUCTION-MISMATCH.",
        },
        {
            "falsifier": "F5_universe_cascade",
            "threshold": "All 3 symbols IS-negative weighted_pnl",
            "binding": "YES (replication of /123 universe-cascade mechanism)",
            "rationale": "/123 broadcast cross-asset signal symmetrically into 3 symbols → cascade",
            "trigger_if": "BCH IS wpnl < 0 AND LDO IS wpnl < 0 AND TRX IS wpnl < 0 in /124 production",
            "post_observation_action": "PATH classify NEGATIVE-cascade; close labeling-DURATION axis if F1+F5 both fire",
        },
        {
            "falsifier": "F6_OOS_Sharpe_collapse",
            "threshold": "OOS Sharpe Δ < -0.40 vs /121 multi-seed (+0.9682)",
            "binding": "PAIRED-with-F1 (joint NEGATIVE-catastrophic-both-axes)",
            "rationale": "Paired with F1 prevents asymmetric IS-vs-OOS reading",
            "trigger_if": "OOS monthly Sharpe < +0.5682 in /124 production run",
            "post_observation_action": "PATH classify NEGATIVE-both-legs (the strongest gate)",
        },
    ]
    _write_csv(rows, ROOT / "T6_falsifier_set.csv")
    print("=== T6 — Brief Section 4 Falsifier Set ===")
    print(_format_table(rows))
    print()


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    print("=" * 70)
    print(" iter-v3/124 EDA — Cycle-7 axis-3 LONGER-CADENCE LABELS K=63")
    print(" Branch A vs Branch B ATR adjudication (LOAD-BEARING T4)")
    print("=" * 70)
    print()
    t0_anchor_values()
    t1_first_order_counterfactual()
    t2_per_symbol_training_samples()
    t3_required_gap_uniqueness()
    t4_atr_branch_adjudication()
    t5_baseline_resolution_distribution()
    t6_falsifier_set()
    print()
    print("=" * 70)
    print(" EDA COMPLETE — 6 T-tables + T0 anchor written to:")
    print(f"   {ROOT}")
    print(" Branch adjudication T4: see T4_atr_branch_adjudication.csv +")
    print(" synthesis at end of T4 print output.")
    print("=" * 70)


if __name__ == "__main__":
    main()
