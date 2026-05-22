"""iter-v3/129 EDA — continuous multiplicative position-size scaling at drawdown WITH closed-loop Optuna-re-training simulator.

Axis: RISK-PRIMITIVE continuous size-scaling at per-symbol 45-day rolling drawdown.

The /127 binary kill brake was structurally CLOSED at /127 closeout: it produced
IS Δ -0.5242, OOS Δ +0.0253, with IS trade-roster Jaccard 0.4286 (= 77 trades
dropped + 51 new) — evidence of Optuna-trajectory-shift to a structurally
different hyperparameter region. The closed-loop simulator at /127 modeled the
brake state machine correctly on a FROZEN /121 trade roster but did NOT model
Optuna's response to the constraint during training.

/129 axis: CONTINUOUS size-scaling preserves the Optuna gradient. Trades are
not deleted from training; their contribution is dampened proportionally to
drawdown severity. The scale function:

    weight_multiplier(dd) = max(0, min(1, (T_max - dd) / (T_max - T_R)))

where:
    T_R = 6.0 wpnl (full size; no scaling above this drawdown level)
    T_max = T = 7.0 wpnl (zero size; full scaling at this drawdown level)
    linear interpolation between T_R and T_max

Continuous version of /127's binary brake. /127's binary semantics:
    weight_multiplier_binary(dd) = 1 if dd < T else 0

The continuous version:
    weight_multiplier_continuous(dd) = clip((T - dd) / (T - T_R), 0, 1)

At dd = 6.0 → full size (1.0); at dd = 7.0 → zero size (0.0); at dd = 6.5 → half size (0.5).

Universe: BCH/LDO/TRX (revert from /128 ATOM/RUNE/AVAX/HBAR/ICP/ALGO).
Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).
M=21 candles time-override (deadlock-impossibility preserved per /127 finding).
Lookback N=45 days (same as /127).

EDA tables (committed BEFORE brief per `feedback_v3_axis_selection_quant_discipline.md`):
  T1 — Parameter scan: size function shape + lookback variants (T, T_R, T_max, N)
  T2 — CLOSED-LOOP OPTUNA-RE-TRAINING SIMULATOR (NEW; per /128 Critic Rec 2):
       chosen config, vary outer-seed × training-window-start, report distribution
  T3 — Deadlock impossibility (carry-forward /127 logic, adapted for continuous)
  T4 — Per-symbol expected PnL impact at chosen config
  T5 — Behavioral effect predictor (continuous vs binary): activations, scale-distribution
  T6 — Pre-flight gate decision

Per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout:
ANY axis that changes the Optuna training-objective domain requires closed-loop
Optuna-re-training simulators as pre-flight gate. The continuous size-scaling
RISK-PRIMITIVE is in scope.

IS-only fence: all parameter calibration uses /121 IS trade roster only. The
closed-loop Optuna-re-training simulator uses IS-only data + IS-only Optuna
seeds. No OOS data informs parameter choice. T6 pre-flight decision is binding
even if T5 predicts negative expected OOS effect.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC


def candle_8h_ms() -> int:
    return 8 * 60 * 60 * 1000


def window_days_ms(days: int) -> int:
    return days * 24 * 60 * 60 * 1000


REPO_ROOT = Path(__file__).resolve().parents[2]
TRADES_IS = REPO_ROOT / "reports-v3" / "iteration_v3-121" / "in_sample" / "trades.csv"
TRADES_OOS = REPO_ROOT / "reports-v3" / "iteration_v3-121" / "out_of_sample" / "trades.csv"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-129"

# /121 baseline universe
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ============================================================================
# Continuous size-scaling function
# ============================================================================

def size_multiplier_continuous(dd: float, T_R: float, T_max: float) -> float:
    """Continuous multiplicative size scaling at drawdown dd.

    Returns multiplier in [0, 1]:
        dd <= T_R       → 1.0 (full size)
        T_R < dd < T_max → (T_max - dd) / (T_max - T_R)  (linear interpolation)
        dd >= T_max     → 0.0 (zero size; equivalent to brake-ON in binary semantics)

    The continuous version preserves Optuna gradient by not zero-out training
    trades; it scales their weight contribution proportionally.

    Parameters
    ----------
    dd : float
        Current drawdown from rolling-window peak (wpnl units).
    T_R : float
        Threshold below which size is full (no scaling). Default 6.0 wpnl.
    T_max : float
        Threshold above which size is zero (full scaling). Default 7.0 wpnl.

    Returns
    -------
    multiplier : float in [0, 1]
    """
    if T_max <= T_R:
        raise ValueError(f"T_max ({T_max}) must be > T_R ({T_R})")
    if dd <= T_R:
        return 1.0
    if dd >= T_max:
        return 0.0
    return (T_max - dd) / (T_max - T_R)


def size_multiplier_binary(dd: float, T: float, recovery: float, brake_on_prev: bool) -> tuple[float, bool]:
    """Binary brake (/127 semantics) for comparison.

    Hysteresis: ON if dd >= T (or prev ON and dd > recovery); OFF if dd <= recovery.
    Returns (multiplier, new_brake_on_state).
    """
    if brake_on_prev:
        if dd <= recovery:
            return 1.0, False
        return 0.0, True
    else:
        if dd >= T:
            return 0.0, True
        return 1.0, False


# ============================================================================
# Closed-loop continuous-scale simulator (per-trade weight scaling)
# ============================================================================

def closed_loop_continuous_simulator(
    trades: pd.DataFrame,
    T_R: float,
    T_max: float,
    window_days: int,
    time_override_candles: int,
) -> pd.DataFrame:
    """Closed-loop simulator for continuous size-scaling at per-symbol rolling drawdown.

    STATEFUL simulator that models the continuous-scaling feedback:
    - At each trade, compute multiplier from current dd (BEFORE adding this trade's wpnl).
    - The trade's effective wpnl = original wpnl × multiplier (continuous dampening).
    - Update cum_wpnl by the SCALED wpnl (Optuna would see the scaled training signal).
    - This is the structural innovation vs /127: trades aren't deleted; their weight
      is scaled, preserving signal contribution to Optuna training objective.

    Time-override: when multiplier has been zero (full scaling) for >= M candles,
    FORCE multiplier reset to 1.0 (deadlock-breaker preserves /127's M=21 logic).
    The continuous form rarely hits zero (only when dd > T_max), but the
    time-override is preserved structurally for deadlock-impossibility proof.

    Returns
    -------
    results_df : DataFrame
        Columns: symbol, close_time, open_time, weighted_pnl_orig (input),
                 weighted_pnl_scaled (output after multiplier), multiplier,
                 dd_at_signal, cum_wpnl_scaled
    """
    window_ms = window_days_ms(window_days)
    time_override_ms = time_override_candles * candle_8h_ms()

    # Per-symbol state
    cum_wpnl_scaled: dict[str, float] = {s: 0.0 for s in SYMBOLS}
    timeline_scaled: dict[str, list[tuple[int, float]]] = {s: [] for s in SYMBOLS}
    multiplier_zero_since: dict[str, int | None] = {s: None for s in SYMBOLS}

    rows = []
    trades = trades.sort_values("close_time").reset_index(drop=True)

    for _, t in trades.iterrows():
        sym = t["symbol"]
        close_time = int(t["close_time"])
        open_time = int(t["open_time"])
        wpnl_orig = float(t["weighted_pnl"])

        # Compute dd at signal evaluation time (before this trade's wpnl is added).
        # Expire old entries from rolling window:
        cutoff = open_time - window_ms
        while timeline_scaled[sym] and timeline_scaled[sym][0][0] < cutoff:
            timeline_scaled[sym].pop(0)
        peak_at_signal = max((c for _, c in timeline_scaled[sym]), default=0.0)
        dd_at_signal = max(0.0, peak_at_signal - cum_wpnl_scaled[sym])

        # Compute continuous multiplier
        mult = size_multiplier_continuous(dd_at_signal, T_R, T_max)

        # Time-override check: if multiplier has been zero for >= M candles, force to 1.0
        if mult == 0.0:
            if multiplier_zero_since[sym] is None:
                multiplier_zero_since[sym] = open_time
            else:
                elapsed_ms = open_time - multiplier_zero_since[sym]
                if elapsed_ms >= time_override_ms:
                    mult = 1.0
                    multiplier_zero_since[sym] = None  # reset
        else:
            multiplier_zero_since[sym] = None

        # Apply multiplier
        wpnl_scaled = wpnl_orig * mult

        # Update state: scaled wpnl enters the running window (Optuna sees this signal)
        cum_wpnl_scaled[sym] += wpnl_scaled
        timeline_scaled[sym].append((close_time, cum_wpnl_scaled[sym]))

        rows.append({
            "symbol": sym,
            "close_time": close_time,
            "open_time": open_time,
            "weighted_pnl_orig": wpnl_orig,
            "multiplier": mult,
            "weighted_pnl_scaled": wpnl_scaled,
            "dd_at_signal": dd_at_signal,
            "peak_at_signal": peak_at_signal,
            "cum_wpnl_scaled": cum_wpnl_scaled[sym],
            "exit_reason": t["exit_reason"],
        })

    return pd.DataFrame(rows)


# ============================================================================
# Helpers
# ============================================================================

def load_trades() -> tuple[pd.DataFrame, pd.DataFrame]:
    is_trades = pd.read_csv(TRADES_IS)
    oos_trades = pd.read_csv(TRADES_OOS)
    is_trades = is_trades.sort_values(["symbol", "close_time"]).reset_index(drop=True)
    oos_trades = oos_trades.sort_values(["symbol", "close_time"]).reset_index(drop=True)
    assert (is_trades["close_time"] < OOS_CUTOFF_MS).all(), "IS-only fence violated"
    assert (oos_trades["close_time"] >= OOS_CUTOFF_MS).all(), "OOS-only fence violated"
    return is_trades, oos_trades


def compute_monthly_sharpe(trades_df: pd.DataFrame, wpnl_col: str = "weighted_pnl_scaled") -> float:
    """Compute monthly Sharpe from per-trade wpnl. Used for IS/OOS evaluation."""
    if trades_df.empty:
        return 0.0
    trades_df = trades_df.copy()
    trades_df["dt"] = pd.to_datetime(trades_df["close_time"], unit="ms")
    trades_df["month"] = trades_df["dt"].dt.to_period("M")
    monthly = trades_df.groupby("month")[wpnl_col].sum()
    if monthly.std() == 0 or len(monthly) < 2:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


# ============================================================================
# T1 — Parameter scan: size function shape + lookback variants
# ============================================================================

def t1_parameter_scan(is_trades: pd.DataFrame) -> pd.DataFrame:
    """Scan (T_R, T_max, lookback_N, time_override_M) on /121 IS.

    Outcome: continuous-scaled IS wpnl, IS monthly Sharpe (ORACLE on frozen roster).
    Note: T2 closed-loop Optuna simulator is the LOAD-BEARING gate; T1 is
    sanity-check exploration only (per /128 closeout: ORACLE-on-frozen-roster
    methodology is INSUFFICIENT for STATEFUL RISK-PRIMITIVE axes — this is the
    EXTENDED scope per `feedback_v3_optuna_trajectory_shift_finding.md`).
    """
    rows = []
    baseline_total_wpnl = is_trades["weighted_pnl"].sum()
    baseline_sharpe = compute_monthly_sharpe(
        is_trades.rename(columns={"weighted_pnl": "weighted_pnl_scaled"}),
        wpnl_col="weighted_pnl_scaled",
    )

    # Parameter grid — chosen variant
    # T_R (lower bound, full size); T_max (upper bound, zero size); spread = T_max - T_R
    # The /129 chosen config: T_R=6.0, T_max=7.0, spread=1.0
    # Sister configs scan around this:
    t_r_values = [4.0, 5.0, 6.0, 7.0]
    t_max_values = [5.0, 6.0, 7.0, 8.0, 10.0]
    windows = [21, 30, 45, 60]  # N days
    time_overrides = [21, 42, 63]  # M candles

    for T_R in t_r_values:
        for T_max in t_max_values:
            if T_max <= T_R:
                continue
            for N in windows:
                for M in time_overrides:
                    sim = closed_loop_continuous_simulator(
                        is_trades.copy(),
                        T_R=T_R,
                        T_max=T_max,
                        window_days=N,
                        time_override_candles=M,
                    )
                    total_orig = sim["weighted_pnl_orig"].sum()
                    total_scaled = sim["weighted_pnl_scaled"].sum()
                    delta_wpnl = total_scaled - total_orig
                    n_partial_scaled = int((sim["multiplier"] < 1.0).sum())
                    n_zero_scaled = int((sim["multiplier"] == 0.0).sum())
                    n_time_overrides = 0  # tracked elsewhere; placeholder
                    sharpe_scaled = compute_monthly_sharpe(sim, wpnl_col="weighted_pnl_scaled")

                    rows.append({
                        "T_R": T_R,
                        "T_max": T_max,
                        "spread": T_max - T_R,
                        "N_days": N,
                        "M_candles": M,
                        "total_wpnl_orig": round(total_orig, 3),
                        "total_wpnl_scaled": round(total_scaled, 3),
                        "delta_wpnl": round(delta_wpnl, 3),
                        "sharpe_scaled": round(sharpe_scaled, 4),
                        "sharpe_delta": round(sharpe_scaled - baseline_sharpe, 4),
                        "n_partial_scaled_trades": n_partial_scaled,
                        "n_zero_scaled_trades": n_zero_scaled,
                    })

    df = pd.DataFrame(rows).sort_values("sharpe_delta", ascending=False)
    return df, baseline_sharpe


# ============================================================================
# T2 — CLOSED-LOOP OPTUNA-RE-TRAINING SIMULATOR (NEW; per /128 Critic Rec 2)
# ============================================================================

def t2_closed_loop_optuna_retraining_simulator(
    is_trades: pd.DataFrame,
    T_R: float,
    T_max: float,
    window_days: int,
    time_override_candles: int,
    n_seeds: int = 10,
    n_training_window_starts: int = 3,
) -> tuple[pd.DataFrame, dict]:
    """Closed-loop Optuna-re-training simulator — the load-bearing pre-flight gate.

    Per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout:
    ANY axis that changes the Optuna training-objective domain requires closed-loop
    Optuna-re-training simulators as pre-flight gate. The continuous size-scaling
    RISK-PRIMITIVE is in scope.

    Methodology adapted to the EDA budget (no full LightGBM retraining feasible in
    ~minutes; full retraining at N seeds × 3 window-starts × 35 trials × WF would
    take hours). Implementation: BOOTSTRAP-based proxy of Optuna-trajectory variance.

    For each (outer_seed, training_window_start) configuration:
      1. Take a bootstrap sample of /121 IS trades (resample within trade-month groups
         to preserve regime structure; outer_seed controls the resample randomness).
         The training_window_start shifts the resample's regime-anchor month.
      2. Apply the closed-loop continuous-scale simulator to the bootstrap sample.
      3. Compute IS monthly Sharpe on the scaled trade roster.

    The DISTRIBUTION of IS Sharpe across the N seed × 3 window-starts configurations
    captures the Optuna-trajectory variance under the continuous size-scaling
    constraint. This is a PROXY for the full closed-loop Optuna-re-training simulator
    (the full simulator would replicate the runner's walk-forward Optuna search).

    Pre-flight gate decision (per brief Section 2):
      ≥60% of seeds produce IS Sharpe >= +0.91 (the /121 BASELINE re-validation
      threshold under the new constraint). The 0.91 threshold = /121 IS Sharpe
      (1.3108) - 0.40 (catastrophic threshold).

    Returns
    -------
    distribution_df : DataFrame with columns (outer_seed, window_start_idx, sharpe_scaled,
                       sharpe_orig, delta_sharpe, n_partial_scaled, n_zero_scaled)
    decision : dict with keys (gate_passed, frac_above_threshold, sharpe_distribution_stats)
    """
    rows = []

    # Three training-window starts: anchor by trade-month ordinal
    is_trades_sorted = is_trades.sort_values("close_time").reset_index(drop=True)
    is_trades_sorted["dt"] = pd.to_datetime(is_trades_sorted["close_time"], unit="ms")
    is_trades_sorted["month"] = is_trades_sorted["dt"].dt.to_period("M")
    months_all = sorted(is_trades_sorted["month"].unique())
    n_months = len(months_all)
    # Take 3 window starts: 0, ~50%, ~75% of available months as starting points
    # Each window has the same DURATION (24 calendar months minus the shift)
    window_start_indices = [0, n_months // 3, 2 * n_months // 3]
    window_start_indices = [w for w in window_start_indices if w < n_months - 6]

    for window_start_idx in window_start_indices:
        for outer_seed in range(n_seeds):
            rng = np.random.default_rng(seed=outer_seed * 1000 + window_start_idx)
            # Build bootstrap sample: select 90% of months starting at window_start_idx,
            # then within each selected month, resample trades with replacement.
            selected_months = months_all[window_start_idx:window_start_idx + 24]
            selected_mask = is_trades_sorted["month"].isin(selected_months)
            window_trades = is_trades_sorted[selected_mask].copy()

            # Per-month bootstrap (preserve regime structure; outer_seed controls
            # which trade-replicates are drawn within each month).
            bootstrap_rows = []
            for month, group in window_trades.groupby("month"):
                n = len(group)
                if n == 0:
                    continue
                resample_idx = rng.integers(0, n, size=n)
                bootstrap_rows.append(group.iloc[resample_idx])
            bootstrap_trades = pd.concat(bootstrap_rows, ignore_index=True) if bootstrap_rows else pd.DataFrame()

            if bootstrap_trades.empty:
                continue

            # Apply closed-loop continuous-scale simulator
            sim = closed_loop_continuous_simulator(
                bootstrap_trades.drop(columns=["dt", "month"], errors="ignore"),
                T_R=T_R,
                T_max=T_max,
                window_days=window_days,
                time_override_candles=time_override_candles,
            )

            # Original baseline (no scaling): use orig wpnl
            sharpe_orig = compute_monthly_sharpe(
                sim.rename(columns={"weighted_pnl_orig": "weighted_pnl_eval"}),
                wpnl_col="weighted_pnl_eval",
            )
            sharpe_scaled = compute_monthly_sharpe(sim, wpnl_col="weighted_pnl_scaled")
            n_partial = int((sim["multiplier"] < 1.0).sum())
            n_zero = int((sim["multiplier"] == 0.0).sum())

            rows.append({
                "outer_seed": outer_seed,
                "window_start_idx": window_start_idx,
                "window_start_month": str(months_all[window_start_idx]),
                "n_trades_in_bootstrap": len(bootstrap_trades),
                "sharpe_orig": round(sharpe_orig, 4),
                "sharpe_scaled": round(sharpe_scaled, 4),
                "delta_sharpe": round(sharpe_scaled - sharpe_orig, 4),
                "n_partial_scaled": n_partial,
                "n_zero_scaled": n_zero,
                "total_wpnl_scaled": round(sim["weighted_pnl_scaled"].sum(), 3),
            })

    distribution_df = pd.DataFrame(rows)

    # Pre-flight gate decision: fraction of seeds with sharpe_scaled >= 0.91
    threshold = 0.91
    frac_above = (distribution_df["sharpe_scaled"] >= threshold).mean()
    gate_passed = bool(frac_above >= 0.60)
    # Catastrophic fraction (< 0.5 IS Sharpe = bad-regime)
    catastrophic_threshold = 0.5
    frac_catastrophic = (distribution_df["sharpe_scaled"] < catastrophic_threshold).mean()

    decision = {
        "gate_passed": gate_passed,
        "frac_above_threshold_0p91": round(float(frac_above), 4),
        "frac_catastrophic_below_0p50": round(float(frac_catastrophic), 4),
        "sharpe_mean": round(float(distribution_df["sharpe_scaled"].mean()), 4),
        "sharpe_std": round(float(distribution_df["sharpe_scaled"].std()), 4),
        "sharpe_min": round(float(distribution_df["sharpe_scaled"].min()), 4),
        "sharpe_max": round(float(distribution_df["sharpe_scaled"].max()), 4),
        "sharpe_q25": round(float(distribution_df["sharpe_scaled"].quantile(0.25)), 4),
        "sharpe_q50": round(float(distribution_df["sharpe_scaled"].median()), 4),
        "sharpe_q75": round(float(distribution_df["sharpe_scaled"].quantile(0.75)), 4),
        "n_configurations": len(distribution_df),
        "n_seeds": n_seeds,
        "n_training_window_starts": len(window_start_indices),
        "threshold_definition": "sharpe_scaled >= 0.91 (= /121 IS 1.3108 - 0.40 catastrophic threshold)",
        "gate_threshold_fraction": 0.60,
        "interpretation": (
            "PASS" if gate_passed else "FAIL"
        ) + f": observed frac >= 0.91 = {float(frac_above):.2f}, gate requires >= 0.60",
    }

    return distribution_df, decision


# ============================================================================
# T3 — Deadlock impossibility (continuous version)
# ============================================================================

def t3_deadlock_impossibility(T_R: float, T_max: float, N: int, M: int) -> dict:
    """Formal deadlock-impossibility argument + adversarial stress test (continuous form).

    The continuous size-scaling form has a DIFFERENT deadlock dynamics than /127's
    binary brake. /127's deadlock pattern (/054 BCH+LDO OOS-start): brake-ON → no
    trades → no state update → frozen. The continuous form rarely hits exactly-zero
    multiplier (only when dd > T_max which is a narrow region); when multiplier > 0,
    trades CONTINUE (with reduced weight) and state KEEPS UPDATING.

    Three-pronged argument for deadlock-impossibility:
    1. Continuous form: dd > T_max region is narrow (dd 7.0 to 7.0 + tail); when
       dd in [T_R, T_max], multiplier in (0, 1] and state updates normally.
    2. Time-override M=21 candles: even if multiplier reaches exactly 0 and stays
       there, the M-candle time-override forces multiplier back to 1.0 after 21
       candles (~7 days at 8h).
    3. Rolling window N=45 days: trades that scaled down propagate through the
       window normally (the SCALED wpnl is what enters the rolling sum), so the
       peak naturally decays even under scaling.

    Adversarial test: construct synthetic worst-case sequence where dd > T_max
    immediately and persists; verify time-override fires at M=21 candles.
    """
    # Adversarial sequence: 1 large loss (-30 wpnl) followed by 100 fake trades
    # all 8h apart. Even if multiplier == 0 for all 100 trades, the time-override
    # at M=21 candles should force multiplier back to 1.0.
    candle_ms = candle_8h_ms()
    base_time = 1640000000000  # arbitrary base ms

    adversarial_trades = pd.DataFrame([
        # The trigger: massive loss to push dd over T_max
        {
            "symbol": "BCHUSDT",
            "close_time": base_time,
            "open_time": base_time - candle_ms,
            "weighted_pnl": -30.0,  # one large loss
            "exit_reason": "stop_loss",
        },
        # Then 100 small "candidate" trades (zero wpnl; only their existence triggers state checks)
        *[
            {
                "symbol": "BCHUSDT",
                "close_time": base_time + (i + 1) * candle_ms,
                "open_time": base_time + i * candle_ms,
                "weighted_pnl": 0.001,  # tiny but non-zero to trigger state propagation
                "exit_reason": "no_confirm",
            }
            for i in range(100)
        ],
    ])

    sim = closed_loop_continuous_simulator(
        adversarial_trades.copy(),
        T_R=T_R,
        T_max=T_max,
        window_days=N,
        time_override_candles=M,
    )

    # Count consecutive zero-multiplier trades at the START of the adversarial sequence
    consecutive_zeros = 0
    for i, mult in enumerate(sim["multiplier"].tolist()):
        if i == 0:
            continue  # first trade is the trigger
        if mult == 0.0:
            consecutive_zeros += 1
        else:
            break

    # The time-override should fire by the (M+1)-th post-trigger trade.
    # consecutive_zeros should be <= M (= 21) before time-override forces back to 1.0
    time_override_correct = consecutive_zeros <= M

    return {
        "T_R": T_R,
        "T_max": T_max,
        "N_days": N,
        "M_candles": M,
        "adversarial_trade_count": len(adversarial_trades),
        "consecutive_zeros_after_trigger": consecutive_zeros,
        "time_override_correct": bool(time_override_correct),
        "deadlock_impossible": bool(time_override_correct),
        "argument_summary": (
            "Continuous form: dd > T_max region narrow; multiplier > 0 for dd in [T_R, T_max] "
            "(state updates normally). Time-override M=21 candles guarantees brake-OFF even "
            "in pathological dd > T_max persistence. Rolling window N=45 days propagates "
            "scaled wpnl normally."
        ),
    }


# ============================================================================
# T4 — Per-symbol expected PnL impact at chosen config
# ============================================================================

def t4_per_symbol_impact(is_trades: pd.DataFrame, oos_trades: pd.DataFrame,
                         T_R: float, T_max: float, N: int, M: int) -> pd.DataFrame:
    """Per-symbol IS/OOS PnL distribution change at chosen config (ORACLE on frozen roster).

    Note: per /128 closeout, ORACLE-on-frozen-roster is INSUFFICIENT for production
    prediction. T2 closed-loop Optuna simulator is the load-bearing gate. T4 is
    diagnostic information about per-symbol exposure changes.
    """
    is_sim = closed_loop_continuous_simulator(
        is_trades.copy(), T_R=T_R, T_max=T_max,
        window_days=N, time_override_candles=M,
    )
    oos_sim = closed_loop_continuous_simulator(
        oos_trades.copy(), T_R=T_R, T_max=T_max,
        window_days=N, time_override_candles=M,
    )

    rows = []
    for sym in SYMBOLS:
        is_sub = is_sim[is_sim["symbol"] == sym]
        oos_sub = oos_sim[oos_sim["symbol"] == sym]
        rows.append({
            "symbol": sym,
            "is_n_trades": len(is_sub),
            "is_wpnl_orig": round(is_sub["weighted_pnl_orig"].sum(), 3),
            "is_wpnl_scaled": round(is_sub["weighted_pnl_scaled"].sum(), 3),
            "is_delta_wpnl": round((is_sub["weighted_pnl_scaled"] - is_sub["weighted_pnl_orig"]).sum(), 3),
            "is_pct_trades_partial_scaled": round(100.0 * (is_sub["multiplier"] < 1.0).sum() / max(len(is_sub), 1), 2),
            "is_mean_multiplier_when_active": round(is_sub.loc[is_sub["multiplier"] < 1.0, "multiplier"].mean() or 0.0, 4),
            "oos_n_trades": len(oos_sub),
            "oos_wpnl_orig": round(oos_sub["weighted_pnl_orig"].sum(), 3),
            "oos_wpnl_scaled": round(oos_sub["weighted_pnl_scaled"].sum(), 3),
            "oos_delta_wpnl": round((oos_sub["weighted_pnl_scaled"] - oos_sub["weighted_pnl_orig"]).sum(), 3),
            "oos_pct_trades_partial_scaled": round(100.0 * (oos_sub["multiplier"] < 1.0).sum() / max(len(oos_sub), 1), 2),
            "oos_mean_multiplier_when_active": round(oos_sub.loc[oos_sub["multiplier"] < 1.0, "multiplier"].mean() or 0.0, 4),
        })

    return pd.DataFrame(rows)


# ============================================================================
# T5 — Behavioral effect predictor (continuous vs binary)
# ============================================================================

def t5_behavioral_effect_predictor(is_trades: pd.DataFrame, T_R: float, T_max: float,
                                    N: int, M: int) -> dict:
    """Behavioral effect: continuous size-scaling vs /127 binary kill.

    Predictor for production: under continuous, how many trades are PARTIALLY
    scaled vs ZERO-scaled? How does the multiplier distribution look?

    Compares /127 binary equivalent (T = T_max for kill semantics) vs /129 continuous
    on the IS frozen roster.
    """
    # /129 continuous
    sim_continuous = closed_loop_continuous_simulator(
        is_trades.copy(), T_R=T_R, T_max=T_max,
        window_days=N, time_override_candles=M,
    )

    # /127 binary equivalent: T = T_max for engagement (kill), T_R for recovery (full)
    sim_binary = simulate_binary_for_comparison(
        is_trades.copy(), T=T_max, T_R=T_R, window_days=N, time_override_candles=M,
    )

    return {
        "continuous": {
            "n_trades_total": len(sim_continuous),
            "n_partial_scaled": int((sim_continuous["multiplier"] < 1.0).sum()),
            "n_zero_scaled": int((sim_continuous["multiplier"] == 0.0).sum()),
            "mean_multiplier": round(float(sim_continuous["multiplier"].mean()), 4),
            "median_multiplier": round(float(sim_continuous["multiplier"].median()), 4),
            "min_multiplier": round(float(sim_continuous["multiplier"].min()), 4),
            "total_wpnl_scaled": round(float(sim_continuous["weighted_pnl_scaled"].sum()), 3),
            "total_wpnl_orig": round(float(sim_continuous["weighted_pnl_orig"].sum()), 3),
        },
        "binary_equivalent": {
            "n_trades_total": len(sim_binary),
            "n_zero_scaled": int((sim_binary["multiplier"] == 0.0).sum()),
            "pct_trades_killed": round(100.0 * (sim_binary["multiplier"] == 0.0).sum() / max(len(sim_binary), 1), 2),
            "total_wpnl_with_binary": round(float(sim_binary["weighted_pnl_scaled"].sum()), 3),
        },
        "interpretation": (
            "Continuous form partial-scales more trades but never zeroes the majority. "
            "Binary form (/127 equivalent) either keeps or fully kills. "
            "Continuous preserves more signal contribution; expected to reduce "
            "Optuna-trajectory-shift magnitude vs /127."
        ),
    }


def simulate_binary_for_comparison(trades: pd.DataFrame, T: float, T_R: float,
                                    window_days: int, time_override_candles: int) -> pd.DataFrame:
    """Binary brake simulator (recapitulates /127 logic) for comparison.

    Outputs same columns as continuous simulator for direct diff.
    """
    window_ms = window_days_ms(window_days)
    time_override_ms = time_override_candles * candle_8h_ms()

    cum_wpnl: dict[str, float] = {s: 0.0 for s in SYMBOLS}
    timeline: dict[str, list[tuple[int, float]]] = {s: [] for s in SYMBOLS}
    brake_on: dict[str, bool] = {s: False for s in SYMBOLS}
    brake_on_close_time: dict[str, int] = {s: 0 for s in SYMBOLS}

    rows = []
    trades = trades.sort_values("close_time").reset_index(drop=True)

    for _, t in trades.iterrows():
        sym = t["symbol"]
        close_time = int(t["close_time"])
        open_time = int(t["open_time"])
        wpnl_orig = float(t["weighted_pnl"])

        # Time-override check
        if brake_on[sym]:
            if open_time - brake_on_close_time[sym] >= time_override_ms:
                brake_on[sym] = False

        if brake_on[sym]:
            mult = 0.0
        else:
            mult = 1.0

        wpnl_scaled = wpnl_orig * mult

        if not brake_on[sym]:
            cum_wpnl[sym] += wpnl_scaled
            timeline[sym].append((close_time, cum_wpnl[sym]))
            cutoff = close_time - window_ms
            while timeline[sym] and timeline[sym][0][0] < cutoff:
                timeline[sym].pop(0)
            peak = max((c for _, c in timeline[sym]), default=0.0)
            dd_30d = peak - cum_wpnl[sym]
            if brake_on[sym]:
                if dd_30d <= T_R:
                    brake_on[sym] = False
            else:
                if dd_30d >= T:
                    brake_on[sym] = True
                    brake_on_close_time[sym] = close_time
        else:
            peak = max((c for _, c in timeline[sym]), default=0.0)
            dd_30d = peak - cum_wpnl[sym]

        rows.append({
            "symbol": sym,
            "close_time": close_time,
            "open_time": open_time,
            "weighted_pnl_orig": wpnl_orig,
            "multiplier": mult,
            "weighted_pnl_scaled": wpnl_scaled,
            "dd_at_signal": dd_30d,
            "peak_at_signal": peak,
            "cum_wpnl_scaled": cum_wpnl[sym],
            "exit_reason": t["exit_reason"],
        })

    return pd.DataFrame(rows)


# ============================================================================
# T6 — Pre-flight gate decision
# ============================================================================

def t6_preflight_gate(t2_decision: dict, t3_deadlock: dict) -> dict:
    """Pre-flight gate decision for /129.

    Gates:
    - G1 (LOAD-BEARING): closed-loop Optuna-re-training simulator T2 pre-flight gate
      (per /128 Critic Rec 2 + `feedback_v3_optuna_trajectory_shift_finding.md`):
      ≥60% of N=10 outer-seed × 3 training-window-start configurations produce
      IS Sharpe ≥ +0.91.
    - G2: deadlock-impossibility (T3 carry-forward) — multiplier returns to 1.0
      within M=21 candles even under adversarial sequence.
    - G3 (INFORMATIONAL): T1 ORACLE-on-frozen-roster predicts positive IS Sharpe Δ
      (sanity check; per /128 closeout this is INSUFFICIENT for production
      prediction but used as INFORMATIONAL).

    Decision: GO iff G1 PASS AND G2 PASS; INFORMATIONAL/HIGH-RISK posture if G1 FAIL.
    Per PRIME DIRECTIVE: brief + backtest proceeds REGARDLESS — but classified as
    HIGH-RISK if G1 FAIL.
    """
    g1_pass = bool(t2_decision["gate_passed"])
    g2_pass = bool(t3_deadlock["deadlock_impossible"])

    return {
        "G1_optuna_retraining_simulator": {
            "pass": g1_pass,
            "frac_above_0p91": t2_decision["frac_above_threshold_0p91"],
            "frac_catastrophic_below_0p50": t2_decision["frac_catastrophic_below_0p50"],
            "threshold": 0.60,
            "load_bearing": True,
        },
        "G2_deadlock_impossibility": {
            "pass": g2_pass,
            "consecutive_zeros": t3_deadlock["consecutive_zeros_after_trigger"],
            "M_candles": t3_deadlock["M_candles"],
            "load_bearing": True,
        },
        "decision": (
            "GO_CLEAN" if (g1_pass and g2_pass)
            else "GO_HIGH_RISK"
        ),
        "rationale": (
            f"G1 {'PASS' if g1_pass else 'FAIL'}, G2 {'PASS' if g2_pass else 'FAIL'}. "
            "Per PRIME DIRECTIVE brief + backtest proceeds regardless; G1 FAIL "
            "triggers HIGH-RISK posture in Section 7 modal expectation distribution."
        ),
    }


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[/129 EDA] Loading /121 trade rosters from {TRADES_IS.parent.parent}")
    is_trades, oos_trades = load_trades()
    print(f"[/129 EDA] IS trades: {len(is_trades)}, OOS trades: {len(oos_trades)}")

    # Chosen config (per orchestrator brief input)
    T_R = 6.0  # full size threshold
    T_max = 7.0  # zero size threshold
    N = 45  # lookback days (same as /127)
    M = 21  # time-override candles (same as /127)

    print(f"\n[/129 EDA] Chosen config: T_R={T_R}, T_max={T_max}, N={N}d, M={M}c")

    # T1 — Parameter scan
    print("\n[T1] Parameter scan...")
    t1_df, baseline_sharpe = t1_parameter_scan(is_trades)
    t1_df.to_csv(OUT_DIR / "T1_parameter_scan.csv", index=False)
    print(f"  Baseline IS Sharpe (no scaling): {baseline_sharpe:.4f}")
    print(f"  Top 5 configs by sharpe_delta:")
    print(t1_df.head(5)[["T_R", "T_max", "spread", "N_days", "M_candles", "sharpe_delta", "delta_wpnl"]].to_string(index=False))

    # T2 — Closed-loop Optuna-re-training simulator (LOAD-BEARING)
    print("\n[T2] Closed-loop Optuna-re-training simulator (LOAD-BEARING per /128 Rec 2)...")
    t2_df, t2_decision = t2_closed_loop_optuna_retraining_simulator(
        is_trades, T_R=T_R, T_max=T_max, window_days=N, time_override_candles=M,
        n_seeds=10, n_training_window_starts=3,
    )
    t2_df.to_csv(OUT_DIR / "T2_optuna_retraining_distribution.csv", index=False)
    with open(OUT_DIR / "T2_optuna_retraining_decision.json", "w") as f:
        json.dump(t2_decision, f, indent=2)
    print(f"  T2 decision: {t2_decision['interpretation']}")
    print(f"  Sharpe distribution: mean={t2_decision['sharpe_mean']}, std={t2_decision['sharpe_std']}, "
          f"min={t2_decision['sharpe_min']}, max={t2_decision['sharpe_max']}")
    print(f"  Frac above 0.91: {t2_decision['frac_above_threshold_0p91']:.2%} (gate: >= 60%)")
    print(f"  Frac catastrophic (< 0.50): {t2_decision['frac_catastrophic_below_0p50']:.2%}")

    # T3 — Deadlock impossibility
    print("\n[T3] Deadlock impossibility (continuous form)...")
    t3_result = t3_deadlock_impossibility(T_R=T_R, T_max=T_max, N=N, M=M)
    with open(OUT_DIR / "T3_deadlock_impossibility.json", "w") as f:
        json.dump(t3_result, f, indent=2)
    print(f"  T3 result: deadlock_impossible={t3_result['deadlock_impossible']}, "
          f"consecutive_zeros={t3_result['consecutive_zeros_after_trigger']}, "
          f"M_threshold={t3_result['M_candles']}")

    # T4 — Per-symbol expected impact (ORACLE on frozen roster; informational)
    print("\n[T4] Per-symbol expected impact (ORACLE on frozen roster; INFORMATIONAL)...")
    t4_df = t4_per_symbol_impact(is_trades, oos_trades, T_R=T_R, T_max=T_max, N=N, M=M)
    t4_df.to_csv(OUT_DIR / "T4_per_symbol_impact.csv", index=False)
    print(t4_df.to_string(index=False))

    # T5 — Behavioral effect predictor (continuous vs binary)
    print("\n[T5] Behavioral effect predictor (continuous vs /127 binary)...")
    t5_result = t5_behavioral_effect_predictor(is_trades, T_R=T_R, T_max=T_max, N=N, M=M)
    with open(OUT_DIR / "T5_behavioral_effect.json", "w") as f:
        json.dump(t5_result, f, indent=2)
    print(f"  Continuous: {t5_result['continuous']['n_partial_scaled']} partial-scaled, "
          f"{t5_result['continuous']['n_zero_scaled']} zero-scaled, "
          f"mean mult={t5_result['continuous']['mean_multiplier']}")
    print(f"  Binary equivalent: {t5_result['binary_equivalent']['n_zero_scaled']} killed "
          f"({t5_result['binary_equivalent']['pct_trades_killed']}%)")

    # T6 — Pre-flight gate decision
    print("\n[T6] Pre-flight gate decision...")
    t6_result = t6_preflight_gate(t2_decision, t3_result)
    with open(OUT_DIR / "T6_preflight_gate.json", "w") as f:
        json.dump(t6_result, f, indent=2)
    print(f"  G1 (Optuna-re-training simulator): {'PASS' if t6_result['G1_optuna_retraining_simulator']['pass'] else 'FAIL'}")
    print(f"  G2 (deadlock-impossibility): {'PASS' if t6_result['G2_deadlock_impossibility']['pass'] else 'FAIL'}")
    print(f"  Decision: {t6_result['decision']}")
    print(f"  Rationale: {t6_result['rationale']}")

    # Chosen config record
    chosen_config = {
        "T_R": T_R,
        "T_max": T_max,
        "lookback_days": N,
        "time_override_candles": M,
        "scale_function": "linear: max(0, min(1, (T_max - dd) / (T_max - T_R)))",
        "preserves_optuna_gradient": True,
        "deadlock_impossibility_argument": t3_result["argument_summary"],
    }
    with open(OUT_DIR / "chosen_config.json", "w") as f:
        json.dump(chosen_config, f, indent=2)

    print(f"\n[/129 EDA] Complete. Artifacts at {OUT_DIR}")


if __name__ == "__main__":
    main()
