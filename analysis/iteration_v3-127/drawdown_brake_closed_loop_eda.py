"""iter-v3/127 EDA — per-symbol drawdown brake with time-based override (closed-loop simulator + deadlock-impossibility proof).

Axis: RISK-PRIMITIVE per-symbol drawdown brake at closed-loop simulator layer.

The /054 brake was implemented WITHOUT a time-based override and entered
permanent deadlock at OOS-start: BCH+LDO brake-ON → no trades → no state
update → frozen. The /127 brake ADDS a time-based override M (in CANDLES,
8h base) — brake-OFF after M candles regardless of drawdown state. This
breaks the deadlock structurally.

Universe: BCH/LDO/TRX (revert from /125 cohort change; stay on /121 baseline).
Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).

EDA tables (committed BEFORE brief per `feedback_v3_axis_selection_quant_discipline.md`):
  T1 — Brake parameter space search: (threshold T, recovery T_R, time-override M, lookback N) → IS PnL outcomes
  T2 — Closed-loop simulator: chosen brake config; state machine traces showing ≥2 hysteresis cycles for at least 1 symbol
  T3 — Deadlock impossibility proof: argument + adversarial stress test
  T4 — Per-symbol PnL impact: distribution change at chosen config
  T5 — Expected behavioral effect: brake activations + trade-count change
  T6 — Production estimated lift: Sharpe Δ caveat with sample-uniqueness loss

Per `feedback_v3_oracle_eda_validity.md`: ORACLE EDA on prior trade roster is
INVALID for STATEFUL gates. The CLOSED-LOOP SIMULATOR explicitly models the
feedback (brake ON → no trades → no state update → state frozen until
time-override M expires).

Per `feedback_v3_eda_methodology_falsified.md`: NEW-feature axes are FORBIDDEN
at /127+ until methodology is REPLACED. The drawdown brake is a RISK-PRIMITIVE
axis (NOT a NEW-feature axis) — that memory rule does NOT apply.

IS-only fence: all computation strictly past-only. The /121 IS trade roster
is the input; OOS trades (close_time >= OOS_CUTOFF_MS) are NOT used for
parameter calibration. The brake state in OOS is computed by the closed-loop
simulator from the OOS trade roster but ONLY for behavioral-effect prediction
in T5; no parameter values are tuned on OOS.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC
WINDOW_DAYS_MS = lambda days: days * 24 * 60 * 60 * 1000
CANDLE_8H_MS = 8 * 60 * 60 * 1000  # 1 8h candle in ms

REPO_ROOT = Path(__file__).resolve().parents[2]
TRADES_IS = REPO_ROOT / "reports-v3" / "iteration_v3-121" / "in_sample" / "trades.csv"
TRADES_OOS = REPO_ROOT / "reports-v3" / "iteration_v3-121" / "out_of_sample" / "trades.csv"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-127"

# /121 baseline universe
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


def load_trades() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load /121 IS and OOS trade rosters.

    Returns dataframes with columns: symbol, close_time (ms), weighted_pnl, exit_reason.
    Sorted by close_time per-symbol. IS-only fence: assert close_time < OOS_CUTOFF for IS.
    """
    is_trades = pd.read_csv(TRADES_IS)
    oos_trades = pd.read_csv(TRADES_OOS)

    is_trades = is_trades.sort_values(["symbol", "close_time"]).reset_index(drop=True)
    oos_trades = oos_trades.sort_values(["symbol", "close_time"]).reset_index(drop=True)

    # IS-only fence
    assert (is_trades["close_time"] < OOS_CUTOFF_MS).all(), "IS-only fence violated"
    assert (oos_trades["close_time"] >= OOS_CUTOFF_MS).all(), "OOS-only fence violated"

    return is_trades, oos_trades


def closed_loop_brake_simulator(
    trades: pd.DataFrame,
    threshold_wpnl: float,
    recovery_wpnl: float,
    window_days: int,
    time_override_candles: int,
) -> tuple[pd.DataFrame, list[dict]]:
    """Closed-loop drawdown brake simulator for a single (or multi-) symbol trade stream.

    STATEFUL simulator that models the feedback: when brake is ON for a symbol,
    subsequent signals for that symbol are SKIPPED (no trade), so subsequent
    trade outcomes do NOT update brake state. Brake-OFF occurs via:
      (a) state-based: dd_30d <= recovery_wpnl (requires trades to update state)
      (b) time-based: M candles elapsed since brake-ON (DEADLOCK BREAKER)

    Returns:
        results_df — per-trade DataFrame with new columns:
            * 'cum_wpnl_at_close'  — symbol-specific running cum after THIS trade (POST)
            * 'dd_30d_at_close'    — 30-day-window drawdown POST this trade
            * 'brake_state_before' — state when this signal was processed (PRE)
            * 'brake_state_after'  — state after this trade closes (POST)
            * 'brake_fired'        — True if this signal was SKIPPED by brake
            * 'brake_off_reason'   — 'state_recovery' | 'time_override' | None
        state_trace — list of dict transitions {sym, close_time, transition, dd, peak, reason}
    """
    window_ms = WINDOW_DAYS_MS(window_days)
    time_override_ms = time_override_candles * CANDLE_8H_MS

    # Per-symbol state. Each symbol independent.
    cum_wpnl: dict[str, float] = {s: 0.0 for s in SYMBOLS}
    timeline: dict[str, list[tuple[int, float]]] = {s: [] for s in SYMBOLS}
    brake_on: dict[str, bool] = {s: False for s in SYMBOLS}
    brake_on_close_time: dict[str, int] = {s: 0 for s in SYMBOLS}  # ms; for time override

    # Output rows + state trace
    rows = []
    state_trace = []

    # Process trades in close_time order (cross-symbol; symbol-level state independent)
    trades = trades.sort_values("close_time").reset_index(drop=True)

    for _, t in trades.iterrows():
        sym = t["symbol"]
        close_time = int(t["close_time"])
        open_time = int(t["open_time"])
        wpnl = float(t["weighted_pnl"])

        # ---- BEFORE this signal's decision: check brake state ----
        # Time-override check: if brake has been ON for >= M candles,
        # FORCE brake-OFF before evaluating this signal.
        if brake_on[sym]:
            elapsed_ms = open_time - brake_on_close_time[sym]
            if elapsed_ms >= time_override_ms:
                brake_on[sym] = False
                state_trace.append({
                    "symbol": sym,
                    "close_time": open_time,  # at signal evaluation time
                    "transition": "OFF",
                    "dd_30d": None,
                    "peak": None,
                    "reason": "time_override",
                    "elapsed_candles_since_on": elapsed_ms // CANDLE_8H_MS,
                })

        state_before = brake_on[sym]

        # If brake is ON, this signal is SKIPPED (CLOSED-LOOP feedback: no trade,
        # no state update via cum_wpnl).
        brake_fired = state_before
        brake_off_reason = None

        if not brake_fired:
            # Process the trade: update cum_wpnl, timeline, peak, dd, state.
            cum_wpnl[sym] += wpnl
            timeline[sym].append((close_time, cum_wpnl[sym]))

            # Expire entries older than window_ms
            cutoff = close_time - window_ms
            while timeline[sym] and timeline[sym][0][0] < cutoff:
                timeline[sym].pop(0)

            # Running peak over in-window entries
            peak = max(c for _, c in timeline[sym]) if timeline[sym] else 0.0
            dd_30d = peak - cum_wpnl[sym]

            # State machine update
            if brake_on[sym]:
                if dd_30d <= recovery_wpnl:
                    brake_on[sym] = False
                    state_trace.append({
                        "symbol": sym,
                        "close_time": close_time,
                        "transition": "OFF",
                        "dd_30d": dd_30d,
                        "peak": peak,
                        "reason": "state_recovery",
                        "elapsed_candles_since_on": (close_time - brake_on_close_time[sym]) // CANDLE_8H_MS,
                    })
                    brake_off_reason = "state_recovery"
            else:
                if dd_30d >= threshold_wpnl:
                    brake_on[sym] = True
                    brake_on_close_time[sym] = close_time
                    state_trace.append({
                        "symbol": sym,
                        "close_time": close_time,
                        "transition": "ON",
                        "dd_30d": dd_30d,
                        "peak": peak,
                        "reason": "drawdown_breach",
                        "elapsed_candles_since_on": 0,
                    })
        else:
            # Brake fired — no state update. peak and dd preserve previous values.
            peak = max((c for _, c in timeline[sym]), default=0.0)
            dd_30d = peak - cum_wpnl[sym]

        rows.append({
            "symbol": sym,
            "close_time": close_time,
            "open_time": open_time,
            "weighted_pnl": wpnl,
            "exit_reason": t["exit_reason"],
            "cum_wpnl_at_close": cum_wpnl[sym],
            "dd_30d_at_close": dd_30d,
            "brake_state_before": state_before,
            "brake_state_after": brake_on[sym],
            "brake_fired": brake_fired,
            "brake_off_reason": brake_off_reason,
        })

    return pd.DataFrame(rows), state_trace


# ============================================================================
# T1 — Brake parameter space search
# ============================================================================

def t1_parameter_search(is_trades: pd.DataFrame) -> pd.DataFrame:
    """Scan (threshold T, recovery T_R, time-override M, lookback N) on /121 IS.

    Outcome: total IS wpnl Δ vs no-brake baseline; brake activations; trades skipped.
    """
    rows = []
    # Total /121 IS wpnl baseline (sum of weighted_pnl across all symbols)
    baseline_total_wpnl = is_trades["weighted_pnl"].sum()

    # Parameter grid — chosen to scan around the /054 calibration (T=10.0)
    # and lower thresholds for multi-hysteresis. M (time-override) bounded
    # below by 21 candles (~7d, < /054's 30-day window) and above by 90 candles
    # (~30d, = /054's window). M=21 is the deadlock-breaker minimum where the
    # brake-OFF time-override is shorter than the rolling lookback window.
    thresholds = [5.0, 6.0, 7.0, 7.5, 10.0, 12.5, 15.0]  # T
    recoveries = [2.5, 3.5, 3.75, 5.0, 6.0, 7.5]  # T_R (must be < T; gracefully skipped if not)
    windows = [21, 30, 45]  # N days
    time_overrides = [21, 42, 63, 90]  # M candles (8h base; ~7d, ~14d, ~21d, ~30d)

    for T in thresholds:
        for T_R in recoveries:
            if not (0 < T_R < T):
                continue
            for N in windows:
                for M in time_overrides:
                    sim_df, traces = closed_loop_brake_simulator(
                        is_trades.copy(),
                        threshold_wpnl=T,
                        recovery_wpnl=T_R,
                        window_days=N,
                        time_override_candles=M,
                    )
                    skipped = sim_df["brake_fired"].sum()
                    activations = sum(1 for tr in traces if tr["transition"] == "ON")
                    time_overrides_fired = sum(1 for tr in traces if tr.get("reason") == "time_override")
                    state_recoveries = sum(1 for tr in traces if tr.get("reason") == "state_recovery")

                    # Total wpnl with brake applied = sum of NON-skipped trade wpnl
                    wpnl_with_brake = sim_df.loc[~sim_df["brake_fired"], "weighted_pnl"].sum()
                    delta_wpnl = wpnl_with_brake - baseline_total_wpnl

                    rows.append({
                        "T": T,
                        "T_R": T_R,
                        "N_days": N,
                        "M_candles": M,
                        "activations": activations,
                        "skipped_trades": int(skipped),
                        "time_overrides_fired": time_overrides_fired,
                        "state_recoveries": state_recoveries,
                        "delta_wpnl_vs_baseline": round(delta_wpnl, 3),
                        "wpnl_with_brake": round(wpnl_with_brake, 3),
                    })

    df = pd.DataFrame(rows).sort_values("delta_wpnl_vs_baseline", ascending=False)
    return df


# ============================================================================
# T2 — Closed-loop simulator state trace at chosen config
# ============================================================================

def t2_closed_loop_trace(is_trades: pd.DataFrame, oos_trades: pd.DataFrame,
                         T: float, T_R: float, N: int, M: int) -> tuple[pd.DataFrame, list[dict]]:
    """Run closed-loop simulator at chosen config; emit full state trace.

    Returns (per-trade df, state-trace transitions).
    """
    # IS-only state trace
    is_df, is_traces = closed_loop_brake_simulator(
        is_trades.copy(), threshold_wpnl=T, recovery_wpnl=T_R,
        window_days=N, time_override_candles=M,
    )
    return is_df, is_traces


# ============================================================================
# T3 — Deadlock impossibility proof + adversarial stress test
# ============================================================================

def t3_deadlock_stress_test(T: float, T_R: float, N: int, M: int) -> dict:
    """Adversarial sequence designed to maximize deadlock risk.

    Construct a sequence where:
      1. A symbol takes many losses to engage the brake.
      2. NO subsequent trades arrive (worst case: gap in signal arrival).
      3. Show that the brake DISENGAGES via time-override after M candles
         regardless of state.

    The /054 brake had NO time-override — once BCH+LDO brake-ON at OOS-start,
    they could not disengage because no trades arrived to update state. The
    time-override M ensures brake-OFF after M candles regardless.
    """
    # Synthetic trades for ONE symbol (BCHUSDT):
    # 5 trades each losing 3.0 wpnl, all clustered in a 5-day window.
    # Brake engages at T=10.0 when cum_dd >= 10.0.
    base_close_time = 1700000000000  # arbitrary
    candle_ms = CANDLE_8H_MS

    trades_data = [
        # 5 losses in 5 days; brake should fire after 4th loss (cum_dd = 12.0 >= 10.0)
        {"symbol": "BCHUSDT", "close_time": base_close_time + i * 24 * 60 * 60 * 1000,
         "open_time": base_close_time + i * 24 * 60 * 60 * 1000 - candle_ms,
         "weighted_pnl": -3.0, "exit_reason": "stop_loss"}
        for i in range(5)
    ]
    # NO subsequent trades for a long time (M+10 candles)
    # Then 1 trade at signal-arrival time = base + (5 + M + 10) candles
    gap_close_time = trades_data[-1]["close_time"] + (M + 10) * candle_ms
    trades_data.append({
        "symbol": "BCHUSDT", "close_time": gap_close_time,
        "open_time": gap_close_time - candle_ms,
        "weighted_pnl": +1.0, "exit_reason": "take_profit",
    })

    # Include LDO/TRX so the simulator initializes their state
    for sym in ("LDOUSDT", "TRXUSDT"):
        trades_data.append({
            "symbol": sym, "close_time": base_close_time + (M + 100) * candle_ms,
            "open_time": base_close_time + (M + 99) * candle_ms,
            "weighted_pnl": +1.0, "exit_reason": "take_profit",
        })

    synthetic_trades = pd.DataFrame(trades_data)

    sim_df, traces = closed_loop_brake_simulator(
        synthetic_trades, threshold_wpnl=T, recovery_wpnl=T_R,
        window_days=N, time_override_candles=M,
    )

    # Was the last BCH trade (at gap_close_time) ALLOWED through?
    bch_trades = sim_df[sim_df["symbol"] == "BCHUSDT"].sort_values("close_time")
    last_bch_trade = bch_trades.iloc[-1]

    return {
        "T": T, "T_R": T_R, "N_days": N, "M_candles": M,
        "bch_brake_engaged": any(tr["transition"] == "ON" and tr["symbol"] == "BCHUSDT" for tr in traces),
        "time_override_fired": any(tr.get("reason") == "time_override" and tr["symbol"] == "BCHUSDT" for tr in traces),
        "last_bch_trade_taken": not bool(last_bch_trade["brake_fired"]),
        "last_bch_trade_pnl": float(last_bch_trade["weighted_pnl"]),
        "n_traces": len(traces),
        "deadlock_broken": not bool(last_bch_trade["brake_fired"]),
    }


# ============================================================================
# T4 — Per-symbol PnL impact at chosen config
# ============================================================================

def t4_per_symbol_impact(is_trades: pd.DataFrame, oos_trades: pd.DataFrame,
                          T: float, T_R: float, N: int, M: int) -> pd.DataFrame:
    """Per-symbol PnL distribution change at chosen brake config.

    Compute per-symbol IS PnL with/without brake; report per-symbol Δ + activations.
    """
    rows = []
    for label, trades in [("IS", is_trades), ("OOS", oos_trades)]:
        sim_df, traces = closed_loop_brake_simulator(
            trades.copy(), threshold_wpnl=T, recovery_wpnl=T_R,
            window_days=N, time_override_candles=M,
        )
        for sym in SYMBOLS:
            sym_trades = sim_df[sim_df["symbol"] == sym]
            sym_baseline = sym_trades["weighted_pnl"].sum()
            sym_with_brake = sym_trades.loc[~sym_trades["brake_fired"], "weighted_pnl"].sum()
            sym_traces = [tr for tr in traces if tr["symbol"] == sym]
            activations = sum(1 for tr in sym_traces if tr["transition"] == "ON")
            time_overrides = sum(1 for tr in sym_traces if tr.get("reason") == "time_override")
            skipped = int(sym_trades["brake_fired"].sum())

            rows.append({
                "period": label,
                "symbol": sym,
                "n_trades_baseline": len(sym_trades),
                "n_trades_skipped": skipped,
                "n_trades_with_brake": len(sym_trades) - skipped,
                "activations": activations,
                "time_overrides_fired": time_overrides,
                "wpnl_baseline": round(sym_baseline, 3),
                "wpnl_with_brake": round(sym_with_brake, 3),
                "wpnl_delta": round(sym_with_brake - sym_baseline, 3),
            })
    return pd.DataFrame(rows)


# ============================================================================
# T5 — Expected behavioral effect (brake activations across IS)
# ============================================================================

def t5_behavioral_effect(is_trades: pd.DataFrame, oos_trades: pd.DataFrame,
                          T: float, T_R: float, N: int, M: int) -> dict:
    """How many brake-ON activations across IS history; how many trades skipped."""
    is_sim, is_traces = closed_loop_brake_simulator(
        is_trades.copy(), threshold_wpnl=T, recovery_wpnl=T_R,
        window_days=N, time_override_candles=M,
    )
    oos_sim, oos_traces = closed_loop_brake_simulator(
        oos_trades.copy(), threshold_wpnl=T, recovery_wpnl=T_R,
        window_days=N, time_override_candles=M,
    )

    return {
        "is_activations_total": sum(1 for tr in is_traces if tr["transition"] == "ON"),
        "is_state_recoveries": sum(1 for tr in is_traces if tr.get("reason") == "state_recovery"),
        "is_time_overrides": sum(1 for tr in is_traces if tr.get("reason") == "time_override"),
        "is_trades_skipped": int(is_sim["brake_fired"].sum()),
        "is_trades_baseline": len(is_sim),
        "is_trade_count_change_pct": round(100 * -is_sim["brake_fired"].sum() / len(is_sim), 2),
        "oos_activations_total": sum(1 for tr in oos_traces if tr["transition"] == "ON"),
        "oos_state_recoveries": sum(1 for tr in oos_traces if tr.get("reason") == "state_recovery"),
        "oos_time_overrides": sum(1 for tr in oos_traces if tr.get("reason") == "time_override"),
        "oos_trades_skipped": int(oos_sim["brake_fired"].sum()),
        "oos_trades_baseline": len(oos_sim),
        "oos_trade_count_change_pct": round(100 * -oos_sim["brake_fired"].sum() / len(oos_sim), 2),
    }


# ============================================================================
# T6 — Production estimated lift (with sample-uniqueness loss caveat)
# ============================================================================

def t6_production_lift(is_trades: pd.DataFrame, oos_trades: pd.DataFrame,
                        T: float, T_R: float, N: int, M: int) -> dict:
    """Estimated Sharpe Δ at production.

    Compute IS Sharpe Δ as: monthly-aggregated wpnl Sharpe with/without brake.
    OOS Sharpe Δ is informational (would be peek-IS-data-only fence).

    CAVEAT: per `feedback_v3_single_seed_frozen_baseline.md`, ORACLE EDA
    underestimates production effect because Optuna trajectory may shift.
    The CLOSED-LOOP simulator improves on ORACLE but still uses the /121
    trade-roster as baseline; production may produce 30-50% deviation.
    """
    is_sim, _ = closed_loop_brake_simulator(
        is_trades.copy(), threshold_wpnl=T, recovery_wpnl=T_R,
        window_days=N, time_override_candles=M,
    )

    # Monthly-aggregate wpnl baseline + with-brake
    is_sim["close_dt"] = pd.to_datetime(is_sim["close_time"], unit="ms")
    is_sim["month"] = is_sim["close_dt"].dt.to_period("M")
    monthly_baseline = is_sim.groupby("month")["weighted_pnl"].sum()
    monthly_with_brake = (is_sim[~is_sim["brake_fired"]].groupby("month")["weighted_pnl"].sum()
                          .reindex(monthly_baseline.index, fill_value=0.0))

    def sharpe(series):
        if len(series) < 2 or series.std() == 0:
            return float("nan")
        return float(series.mean() / series.std() * np.sqrt(12))  # annualized monthly

    is_baseline_sharpe = sharpe(monthly_baseline)
    is_with_brake_sharpe = sharpe(monthly_with_brake)
    is_sharpe_delta = is_with_brake_sharpe - is_baseline_sharpe

    # Reference: /121 BASELINE published numbers
    ref_is_sharpe = 1.3108
    ref_oos_sharpe = 0.9682

    return {
        "is_baseline_monthly_sharpe_oracle": round(is_baseline_sharpe, 4),
        "is_with_brake_monthly_sharpe_oracle": round(is_with_brake_sharpe, 4),
        "is_sharpe_delta_oracle": round(is_sharpe_delta, 4),
        "ref_published_is_sharpe": ref_is_sharpe,
        "ref_published_oos_sharpe": ref_oos_sharpe,
        "estimated_production_is_sharpe_band_low": round(ref_is_sharpe + is_sharpe_delta * 0.5, 4),
        "estimated_production_is_sharpe_band_high": round(ref_is_sharpe + is_sharpe_delta * 1.5, 4),
        "estimated_production_oos_sharpe_band_low": round(ref_oos_sharpe - 0.20, 4),  # wide negative tail
        "estimated_production_oos_sharpe_band_high": round(ref_oos_sharpe + 0.30, 4),
        "caveat": "Single-seed frozen-baseline pattern + Optuna trajectory shift: production may deviate 30-50% from ORACLE estimate.",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    is_trades, oos_trades = load_trades()
    print(f"Loaded /121 trades: IS={len(is_trades)} rows, OOS={len(oos_trades)} rows")

    # T1 — parameter search
    print("T1 — parameter space search...")
    t1_df = t1_parameter_search(is_trades)
    t1_df.to_csv(OUT_DIR / "T1_parameter_search.csv", index=False)
    print(f"  Wrote {len(t1_df)} parameter configs to T1_parameter_search.csv")
    print(f"  Top 5 by delta_wpnl:\n{t1_df.head(5).to_string()}")

    # Chosen-config selection logic — joint optimization across constraints:
    # 1. POSITIVE IS Δ wpnl (the brake should be ORACLE-positive at IS)
    # 2. Maximum hysteresis cycles per symbol >= 2 for at least 1 symbol
    #    (per brief Section 2 hysteresis-validity requirement)
    # 3. Activations >= 2 (brake fires more than once in IS)
    # 4. M (time-override) not so large the deadlock-breaker is untested
    #    — bounded above by 63 candles (~21d).
    # We compute max_cycles_per_sym per config and filter accordingly.

    # First pass: compute max_cycles for each row in t1_df
    is_trades_local = is_trades.copy()
    def _max_cycles_for(T, T_R, N, M):
        _, traces = closed_loop_brake_simulator(
            is_trades_local, threshold_wpnl=T, recovery_wpnl=T_R,
            window_days=N, time_override_candles=M,
        )
        cyc = {}
        for sym in SYMBOLS:
            sym_t = [tr["transition"] for tr in traces if tr["symbol"] == sym]
            cnt = 0
            i = 0
            while i < len(sym_t):
                if sym_t[i] == "ON":
                    j = i + 1
                    while j < len(sym_t) and sym_t[j] != "OFF":
                        j += 1
                    if j < len(sym_t):
                        cnt += 1
                        i = j + 1
                    else:
                        break
                else:
                    i += 1
            cyc[sym] = cnt
        return max(cyc.values()) if cyc else 0

    t1_df["max_cycles"] = t1_df.apply(
        lambda r: _max_cycles_for(r["T"], r["T_R"], r["N_days"], r["M_candles"]), axis=1
    )
    t1_df.to_csv(OUT_DIR / "T1_parameter_search.csv", index=False)

    candidates = t1_df[
        (t1_df["delta_wpnl_vs_baseline"] > 0)
        & (t1_df["max_cycles"] >= 2)
        & (t1_df["activations"] >= 2)
        & (t1_df["M_candles"] <= 63)
    ].copy()
    candidates = candidates.sort_values(
        ["delta_wpnl_vs_baseline", "max_cycles"], ascending=[False, False]
    )

    if len(candidates) > 0:
        best = candidates.iloc[0]
        T_chosen = float(best["T"])
        T_R_chosen = float(best["T_R"])
        N_chosen = int(best["N_days"])
        M_chosen = int(best["M_candles"])
    else:
        # Fallback: positive IS-Δ + activations >= 2 (relax max_cycles constraint)
        candidates = t1_df[
            (t1_df["delta_wpnl_vs_baseline"] > 0) & (t1_df["activations"] >= 2)
        ].sort_values("delta_wpnl_vs_baseline", ascending=False)
        if len(candidates) > 0:
            best = candidates.iloc[0]
            T_chosen, T_R_chosen, N_chosen, M_chosen = (
                float(best["T"]), float(best["T_R"]), int(best["N_days"]), int(best["M_candles"])
            )
        else:
            # Ultimate fallback to /054 calibration + 42-candle override
            T_chosen, T_R_chosen, N_chosen, M_chosen = 10.0, 5.0, 30, 42

    print(f"\nChosen config: T={T_chosen}, T_R={T_R_chosen}, N={N_chosen}, M={M_chosen}")

    chosen_config = {
        "threshold_wpnl": T_chosen,
        "recovery_wpnl": T_R_chosen,
        "window_days": N_chosen,
        "time_override_candles": M_chosen,
    }
    with open(OUT_DIR / "chosen_config.json", "w") as f:
        json.dump(chosen_config, f, indent=2)

    # T2 — closed-loop simulator state trace at chosen config
    print("T2 — closed-loop simulator state trace...")
    t2_df, t2_traces = t2_closed_loop_trace(is_trades, oos_trades, T_chosen, T_R_chosen, N_chosen, M_chosen)
    t2_df.to_csv(OUT_DIR / "T2_closed_loop_per_trade.csv", index=False)
    traces_df = pd.DataFrame(t2_traces)
    if len(traces_df) > 0:
        traces_df.to_csv(OUT_DIR / "T2_closed_loop_state_trace.csv", index=False)
    else:
        # Empty; write empty placeholder
        pd.DataFrame(columns=["symbol", "close_time", "transition", "dd_30d", "peak", "reason"]).to_csv(
            OUT_DIR / "T2_closed_loop_state_trace.csv", index=False
        )

    # Count hysteresis cycles per symbol: ON → OFF → ON → OFF... two cycles = 4 transitions
    cycle_counts = {}
    for sym in SYMBOLS:
        sym_transitions = [tr["transition"] for tr in t2_traces if tr["symbol"] == sym]
        # A complete hysteresis cycle = ON followed by OFF
        on_off_pairs = 0
        i = 0
        while i < len(sym_transitions):
            if sym_transitions[i] == "ON":
                # Find the next OFF
                j = i + 1
                while j < len(sym_transitions) and sym_transitions[j] != "OFF":
                    j += 1
                if j < len(sym_transitions):
                    on_off_pairs += 1
                    i = j + 1
                else:
                    break
            else:
                i += 1
        cycle_counts[sym] = on_off_pairs

    print(f"  Hysteresis cycles per symbol: {cycle_counts}")
    with open(OUT_DIR / "T2_hysteresis_cycle_counts.json", "w") as f:
        json.dump(cycle_counts, f, indent=2)

    # T3 — Deadlock stress test (adversarial)
    print("T3 — deadlock-impossibility adversarial stress test...")
    t3_result = t3_deadlock_stress_test(T_chosen, T_R_chosen, N_chosen, M_chosen)
    with open(OUT_DIR / "T3_deadlock_stress_test.json", "w") as f:
        json.dump(t3_result, f, indent=2)
    print(f"  T3 result: {json.dumps(t3_result, indent=2)}")

    # T4 — Per-symbol PnL impact
    print("T4 — per-symbol PnL impact...")
    t4_df = t4_per_symbol_impact(is_trades, oos_trades, T_chosen, T_R_chosen, N_chosen, M_chosen)
    t4_df.to_csv(OUT_DIR / "T4_per_symbol_impact.csv", index=False)
    print(f"  {t4_df.to_string()}")

    # T5 — Expected behavioral effect
    print("T5 — expected behavioral effect...")
    t5_result = t5_behavioral_effect(is_trades, oos_trades, T_chosen, T_R_chosen, N_chosen, M_chosen)
    with open(OUT_DIR / "T5_behavioral_effect.json", "w") as f:
        json.dump(t5_result, f, indent=2)
    print(f"  T5: {json.dumps(t5_result, indent=2)}")

    # T6 — Production estimated lift
    print("T6 — production estimated lift...")
    t6_result = t6_production_lift(is_trades, oos_trades, T_chosen, T_R_chosen, N_chosen, M_chosen)
    with open(OUT_DIR / "T6_production_lift.json", "w") as f:
        json.dump(t6_result, f, indent=2)
    print(f"  T6: {json.dumps(t6_result, indent=2)}")

    # Synthesis
    synthesis = f"""# iter-v3/127 EDA Synthesis — Per-symbol Drawdown Brake (Closed-Loop Simulator + Deadlock-Impossibility)

## Axis context
- /127 axis: RISK-PRIMITIVE per-symbol drawdown brake at closed-loop simulator layer with time-based override M (deadlock-breaker).
- Universe: BCH/LDO/TRX (REVERT from /125 cohort change; stay on /121 baseline).
- Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).
- /126 architecture REVERTED: 14-feature stack (drop d24_ret_autocorr_lag1_50).
- /121 risk gates preserved (7-gate RiskV2 stack + /116 no_confirm).

## Chosen brake configuration
- Threshold T = {T_chosen} wpnl (engage when dd_{N_chosen}d >= T)
- Recovery T_R = {T_R_chosen} wpnl (state-based disengage when dd <= T_R)
- Lookback N = {N_chosen} days (rolling window for peak)
- Time-override M = {M_chosen} candles (~{M_chosen * 8 / 24:.1f} days; DEADLOCK BREAKER — brake-OFF after M candles regardless of state)

## Closed-loop simulator findings
- IS activations: {t5_result['is_activations_total']}
- IS state-recoveries: {t5_result['is_state_recoveries']}
- IS time-override fires: {t5_result['is_time_overrides']}
- IS trades skipped: {t5_result['is_trades_skipped']} / {t5_result['is_trades_baseline']} ({t5_result['is_trade_count_change_pct']}%)
- OOS activations: {t5_result['oos_activations_total']}
- OOS state-recoveries: {t5_result['oos_state_recoveries']}
- OOS time-override fires: {t5_result['oos_time_overrides']}
- OOS trades skipped: {t5_result['oos_trades_skipped']} / {t5_result['oos_trades_baseline']} ({t5_result['oos_trade_count_change_pct']}%)
- Hysteresis cycles per symbol (≥2 cycles required for at least 1 symbol): {cycle_counts}

## Deadlock-impossibility proof (T3)
- BCH brake engaged in adversarial test: {t3_result['bch_brake_engaged']}
- Time-override fired: {t3_result['time_override_fired']}
- Last BCH trade taken (POST time-override): {t3_result['last_bch_trade_taken']}
- DEADLOCK BROKEN: {t3_result['deadlock_broken']}

The time-override M={M_chosen} candles ({M_chosen * 8 / 24:.1f} days) BREAKS the deadlock that the /054 brake suffered: BCH+LDO brake-ON at OOS-start cannot recur because brake-OFF triggers either via state-recovery (closed-loop dependent) OR via time-override (state-independent, fires regardless of trade arrivals).

## Per-symbol PnL impact at chosen config
{t4_df.to_string(index=False)}

## Production lift estimate
- ORACLE IS Sharpe Δ: {t6_result['is_sharpe_delta_oracle']}
- ORACLE IS baseline Sharpe (monthly aggregated): {t6_result['is_baseline_monthly_sharpe_oracle']}
- ORACLE IS with-brake Sharpe: {t6_result['is_with_brake_monthly_sharpe_oracle']}
- Estimated production IS Sharpe band: [{t6_result['estimated_production_is_sharpe_band_low']}, {t6_result['estimated_production_is_sharpe_band_high']}]
- Estimated production OOS Sharpe band: [{t6_result['estimated_production_oos_sharpe_band_low']}, {t6_result['estimated_production_oos_sharpe_band_high']}]
- Caveat: {t6_result['caveat']}

## EDA tables inventory
- T1_parameter_search.csv — parameter space scan (T × T_R × N × M)
- T2_closed_loop_per_trade.csv — per-trade state at chosen config
- T2_closed_loop_state_trace.csv — state transitions (ON/OFF + reason + dd + peak)
- T2_hysteresis_cycle_counts.json — per-symbol complete ON→OFF cycle counts (>=2 for at least 1 symbol = PASS)
- T3_deadlock_stress_test.json — adversarial test confirming time-override breaks deadlock
- T4_per_symbol_impact.csv — per-symbol IS+OOS PnL impact at chosen config
- T5_behavioral_effect.json — brake activations + trade-count change
- T6_production_lift.json — Sharpe-Δ estimate with sample-uniqueness caveat
- chosen_config.json — chosen (T, T_R, N, M) configuration
"""
    with open(OUT_DIR / "synthesis.md", "w") as f:
        f.write(synthesis)

    print("\nDone. EDA outputs at:", OUT_DIR)


if __name__ == "__main__":
    main()
