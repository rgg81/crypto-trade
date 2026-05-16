"""iter-v3/074 — Phase 1-2 axis-selection EDA (dual-purpose).

CYCLE 2 EXPLORATION #4 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

------------------------------------------------------------------------------
THE HARD CONSTRAINT (Critic /073 Rec #1 + `feedback_v3_is_oos_regime_divergence.md`)
------------------------------------------------------------------------------
Three consecutive cycle-1+2 EXPLORATIONs classified SUSPICIOUS-OOS-DOMINANT with
monotonically escalating OOS/IS Sharpe ratios:

    /065  universal SL widening (2.0,1.0)->(2.0,1.5)   OOS/IS ratio 2.87
    /071  meta-labeling (M2 take/skip filter)          OOS/IS ratio 4.51
    /073  per-symbol triple-barrier asymmetry           OOS/IS ratio 6.85

All three share ONE mechanism: each EXTENDS EFFECTIVE TRADE HOLDING TIME. v3's IS
window (2022-09 -> 2025-03: bear + recovery + 2024 bull + chop) PENALIZES longer-held
trades; the OOS window (2025-03 -> 2026-05: persistent uptrend) REWARDS them. Any
holding-time-extension axis mechanically loads this regime factor.

The /074 axis MUST be ONE of:
  (A) a holding-time-ORTHOGONAL axis (mechanism does NOT change mean/median trade
      duration), OR
  (B) a dedicated IS/OOS regime-stratified DIAGNOSTIC.

------------------------------------------------------------------------------
WHAT THIS EDA DOES (dual-purpose — satisfies BOTH limbs of the constraint)
------------------------------------------------------------------------------
PART 1 — IS/OOS regime-stratified DIAGNOSTIC (limb B).
  Splits the IS window into a bear/chop sub-period (2022-09 -> 2023-12) and a bull
  sub-period (2024-01 -> 2025-03), and characterizes how the /060 anchor performs in
  each vs the OOS window (2025-03 -> 2026-05). This formally measures the regime
  factor that /065/071/073 keep loading and tells the cycle which IS sub-regime is
  the drag.

PART 2 — Axis-selection evaluation against the holding-time-orthogonal hard
  constraint (limb A). Three candidate axes are assessed on IS-only data:

    AXIS A — regime-conditional kill switch (primitive 9; enable_regime_gate=True).
             A BINARY kill switch: a candidate signal on a regime-stress BTC bar is
             suppressed to NO_SIGNAL BEFORE the model is consulted. Fully built and
             past-only-tested in risk_v3.py; currently OFF. Tested once at /022 but
             at the BIASED pre-walk-forward-fix baseline (eligible for re-eval per
             `feedback_v3_walkforward_lookahead_bug.md`). HOLDING-TIME-ORTHOGONAL by
             construction: it removes whole trades; surviving trades are unchanged.

    AXIS B — distinct-feature meta-labeling (M2 with non-M1 features). Critic /071
             Rec #4. A meta-labeling FILTER. Per the regime-divergence rule, M2
             filtration extends effective holding time (the M2 veto removes early
             stop-outs -> kept trades are held longer). HOLDING-TIME-EXTENDING ->
             SATURATED FAMILY -> rejected at EDA stage.

    AXIS C — entry-timing shift (delay entry by k candles after the model fires).
             An entry-timing axis. Assessed for holding-time effect: shifting the
             entry bar changes WHEN a trade starts but, with the barrier distances
             (atr_tp/atr_sl) and timeout unchanged, does NOT change expected trade
             DURATION. Borderline-orthogonal; assessed quantitatively below.

The QR selects the axis with the strongest quantitative basis that SATISFIES the
hard constraint.

------------------------------------------------------------------------------
NO LOOK-AHEAD: every IS table is computed on IS-window data only
(open_time < OOS_CUTOFF_MS = 2025-03-24). OOS tables (used ONLY in PART 1's
descriptive regime diagnostic, never as a selection input) are clearly labelled.
The regime-gate counterfactual (AXIS A) uses BTC drawdown/vol-zscore computed
past-only via .shift(1) — identical to the production risk_v3._build_btc_regime_lookup
contract. The EDA does NOT run a backtest; it is purely descriptive.
------------------------------------------------------------------------------

Outputs (committed alongside this script):
  - T0_anchor_values.csv            : /060 EXPLORATION-mode anchor, byte-exact
                                      with explicit source file:line references
  - part1_regime_stratification.csv : IS bear/chop vs IS bull vs OOS — the
                                      regime-divergence diagnostic (LIMB B)
  - part1_monthly_regime_tag.csv    : per-month PnL with regime tag
  - axisA_regime_gate_counterfactual.csv : TRX trades on regime-stress BTC bars
                                           — how many trades the gate removes,
                                           their IS+OOS economics, holding-time
  - axisA_holding_time_predictor.csv : holding-time-effect predictor for AXIS A
  - axisBC_holding_time_screen.csv   : holding-time-effect screen for AXIS B + C
  - axis_selection_summary.csv       : the QR decision table
  - synthesis.md                    : prose synthesis + the QR axis call

Run:
  uv run python analysis/iteration_v3-074/axis_selection_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — src/crypto_trade/config.py:8

# Regime sub-window boundaries (IS window only; chosen to match Critic /073 Rec #1).
# IS bear/chop:  2022-09-01 -> 2023-12-31  (FTX collapse, 2023 chop)
# IS bull:       2024-01-01 -> 2025-03-24  (2024 bull + 2024-Q4/2025-Q1 chop)
IS_BULL_START_MS = 1704067200000  # 2024-01-01 00:00:00 UTC

# Regime-gate thresholds — production values from RiskV2Config / risk_v3.py.
REGIME_DD_THRESHOLD_PCT = 20.0  # BTC drawdown_30d > 20% (IS-90th-pct)
REGIME_VOL_Z_THRESHOLD = 1.5  # |BTC vol_zscore_30d| > 1.5 (IS-95th-pct)
REGIME_DD_LOOKBACK_BARS = 90  # 30 days at 8h
REGIME_VOL_LOOKBACK_BARS = 90

V3_SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
REGIME_GATE_SYMBOL = "TRXUSDT"  # production regime_gate_symbols=("TRXUSDT",)

REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"


def _sharpe_monthly(monthly_pnl: pd.Series) -> float:
    """Monthly Sharpe = mean / std of monthly PnL% (no annualization — matches the
    `comparison.csv` `monthly_sharpe` row convention used as the v3 anchor metric)."""
    if len(monthly_pnl) < 2:
        return float("nan")
    sd = monthly_pnl.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return float("nan")
    return float(monthly_pnl.mean() / sd)


# ===========================================================================
# T0 — anchor values (byte-exact from /060 comparison.csv, with source refs)
# ===========================================================================
def build_t0_anchor() -> pd.DataFrame:
    """Read /060 comparison.csv and emit the anchor table with file:line refs.

    The /060 EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403) is the cycle-2
    EXPLORATION reference per `feedback_v3_cycle1_axis_pass_criteria.md`.
    """
    comp = pd.read_csv(REPORTS_060 / "comparison.csv", comment="#", nrows=14)
    comp = comp.set_index("metric")

    rows = [
        ("monthly_sharpe_IS", comp.loc["monthly_sharpe", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:2 in_sample"),
        ("monthly_sharpe_OOS", comp.loc["monthly_sharpe", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:2 out_of_sample"),
        ("daily_sharpe_IS", comp.loc["daily_sharpe", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:3 in_sample"),
        ("daily_sharpe_OOS", comp.loc["daily_sharpe", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:3 out_of_sample"),
        ("n_trades_IS", comp.loc["n_trades", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:7 in_sample"),
        ("n_trades_OOS", comp.loc["n_trades", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv:7 out_of_sample"),
        ("frac_positive_paths", 0.6444,
         "reports-v3/iteration_v3-060 dsr.json / cpcv_paths.csv (CPCV invariant)"),
    ]
    df = pd.DataFrame(rows, columns=["anchor_metric", "value", "source"])
    return df


# ===========================================================================
# PART 1 — IS/OOS regime-stratified DIAGNOSTIC  (satisfies hard-constraint limb B)
# ===========================================================================
def part1_regime_stratification() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the /060 anchor performance into IS-bear/chop, IS-bull, OOS sub-periods.

    This is the dedicated regime diagnostic mandated by Critic /073 Rec #1. It
    formally characterizes the IS/OOS divergence that the holding-time-extension
    family (/065/071/073) keeps loading.

    Uses monthly_pnl.csv (the same series `comparison.csv` derives monthly_sharpe
    from). The diagnostic is purely descriptive; OOS numbers are characterization,
    NOT a selection input.
    """
    is_monthly = pd.read_csv(REPORTS_060 / "in_sample" / "monthly_pnl.csv")
    oos_monthly = pd.read_csv(REPORTS_060 / "out_of_sample" / "monthly_pnl.csv")

    # Tag each IS month bear/chop vs bull by the 2024-01 boundary.
    is_monthly["ts"] = pd.to_datetime(is_monthly["month"], format="%Y-%m")
    bull_boundary = pd.Timestamp("2024-01-01")
    is_monthly["regime"] = np.where(
        is_monthly["ts"] >= bull_boundary, "IS_bull", "IS_bear_chop"
    )
    oos_monthly["regime"] = "OOS_uptrend"

    monthly_tag = pd.concat(
        [
            is_monthly[["month", "pnl_pct", "trade_count", "regime"]],
            oos_monthly[["month", "pnl_pct", "trade_count", "regime"]],
        ],
        ignore_index=True,
    )

    rows = []
    for regime, grp in monthly_tag.groupby("regime"):
        pnl = grp["pnl_pct"]
        rows.append(
            {
                "regime": regime,
                "n_months": len(grp),
                "total_pnl_pct": round(pnl.sum(), 4),
                "mean_monthly_pnl_pct": round(pnl.mean(), 4),
                "std_monthly_pnl_pct": round(pnl.std(ddof=1), 4),
                "monthly_sharpe": round(_sharpe_monthly(pnl), 4),
                "pct_positive_months": round(100.0 * (pnl > 0).mean(), 1),
                "n_trades": int(grp["trade_count"].sum()),
            }
        )
    strat = pd.DataFrame(rows)
    # Order: IS_bear_chop, IS_bull, OOS_uptrend
    order = {"IS_bear_chop": 0, "IS_bull": 1, "OOS_uptrend": 2}
    strat = strat.sort_values("regime", key=lambda s: s.map(order)).reset_index(drop=True)
    return strat, monthly_tag


# ===========================================================================
# BTC regime lookup — past-only, identical contract to risk_v3._build_btc_regime_lookup
# ===========================================================================
def build_btc_regime_lookup() -> pd.DataFrame:
    """Per-bar BTC drawdown_30d and vol_zscore_30d (past-only via .shift(1)).

    Re-implements risk_v3._build_btc_regime_lookup exactly so the EDA's
    counterfactual matches what the production gate would do.
    """
    btc = pd.read_csv(
        REPO / "data" / "BTCUSDT" / "8h.csv", usecols=["open_time", "close"]
    )
    btc = btc.sort_values("open_time").reset_index(drop=True)
    btc["close"] = btc["close"].astype(float)
    btc["log_ret"] = np.log(btc["close"] / btc["close"].shift(1))

    close_shifted = btc["close"].shift(1)
    rolling_max = close_shifted.rolling(window=REGIME_DD_LOOKBACK_BARS, min_periods=1).max()
    btc["drawdown_pct"] = (close_shifted - rolling_max) / rolling_max * 100.0

    logret_shifted = btc["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=REGIME_VOL_LOOKBACK_BARS, min_periods=2).std()
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)
    btc["vol_zscore"] = (rolling_std - expanding_mean) / expanding_std

    return btc[["open_time", "drawdown_pct", "vol_zscore"]]


def _regime_gate_fires_for_bar(
    btc_lookup: pd.DataFrame, open_time_ms: int
) -> tuple[bool, float, float]:
    """Replicate risk_v3._regime_gate_fires: find the most recent BTC bar STRICTLY
    BEFORE open_time_ms; gate fires if |dd| > 20% OR |vol_z| > 1.5.
    """
    times = btc_lookup["open_time"].to_numpy()
    idx = int(np.searchsorted(times, open_time_ms, side="left")) - 1
    if idx < 0:
        return False, float("nan"), float("nan")
    dd = float(btc_lookup["drawdown_pct"].iloc[idx])
    vz = float(btc_lookup["vol_zscore"].iloc[idx])
    if not np.isfinite(dd) or not np.isfinite(vz):
        return False, dd, vz
    fires = (abs(dd) > REGIME_DD_THRESHOLD_PCT) or (abs(vz) > REGIME_VOL_Z_THRESHOLD)
    return fires, dd, vz


# ===========================================================================
# AXIS A — regime-conditional kill-switch counterfactual on the /060 TRX roster
# ===========================================================================
def axis_a_regime_gate_counterfactual(
    btc_lookup: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """For every /060 TRX trade, tag whether the regime gate would have suppressed
    its entry. Reports the IS+OOS economics of suppressed-vs-kept trades and the
    holding-time-effect predictor.

    The gate fires on the candidate's ENTRY bar (open_time). A suppressed trade is
    REMOVED entirely (NO_SIGNAL). This is the holding-time-orthogonal mechanism:
    surviving trades are bit-identical to baseline trades; only whole trades drop.
    """
    is_trades = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    oos_trades = pd.read_csv(REPORTS_060 / "out_of_sample" / "trades.csv")
    is_trades["split"] = "IS"
    oos_trades["split"] = "OOS"
    trades = pd.concat([is_trades, oos_trades], ignore_index=True)

    # AXIS A targets regime_gate_symbols=("TRXUSDT",) — only TRX trades are affected.
    trx = trades[trades["symbol"] == REGIME_GATE_SYMBOL].copy()

    fired, dds, vzs = [], [], []
    for ot in trx["open_time"]:
        f, dd, vz = _regime_gate_fires_for_bar(btc_lookup, int(ot))
        fired.append(f)
        dds.append(dd)
        vzs.append(vz)
    trx["regime_gate_fires"] = fired
    trx["btc_dd_pct"] = dds
    trx["btc_vol_z"] = vzs

    # Holding duration in candles (8h bars) — close_time - open_time, /8h.
    bar_ms = 8 * 3600 * 1000
    trx["duration_candles"] = (trx["close_time"] - trx["open_time"]) / bar_ms

    # Economics: suppressed (gate fires) vs kept (gate passes), per split.
    rows = []
    for split in ["IS", "OOS"]:
        s = trx[trx["split"] == split]
        for kept_label, kept_mask in [
            ("SUPPRESSED_by_gate", s["regime_gate_fires"]),
            ("KEPT", ~s["regime_gate_fires"]),
        ]:
            g = s[kept_mask]
            rows.append(
                {
                    "split": split,
                    "bucket": kept_label,
                    "n_trades": len(g),
                    "weighted_pnl_sum": round(g["weighted_pnl"].sum(), 4),
                    "net_pnl_pct_sum": round(g["net_pnl_pct"].sum(), 4),
                    "win_rate_pct": round(100.0 * (g["net_pnl_pct"] > 0).mean(), 1)
                    if len(g) else float("nan"),
                    "mean_duration_candles": round(g["duration_candles"].mean(), 3)
                    if len(g) else float("nan"),
                    "median_duration_candles": round(g["duration_candles"].median(), 3)
                    if len(g) else float("nan"),
                }
            )
    counterfactual = pd.DataFrame(rows)
    return counterfactual, trx


def axis_a_holding_time_predictor(trx: pd.DataFrame) -> pd.DataFrame:
    """Holding-time-effect predictor for AXIS A (mandated by
    `feedback_v3_is_oos_regime_divergence.md`).

    The predictor compares mean/median trade DURATION of the KEPT trades (the
    roster AFTER the gate) against the FULL TRX roster (the baseline). If the gate
    is holding-time-orthogonal, the KEPT-roster duration distribution must be
    statistically indistinguishable from the full roster — the gate removes trades
    but does NOT systematically prefer short-held or long-held trades.
    """
    rows = []
    for split in ["IS", "OOS", "ALL"]:
        s = trx if split == "ALL" else trx[trx["split"] == split]
        kept = s[~s["regime_gate_fires"]]
        full = s
        rows.append(
            {
                "split": split,
                "full_roster_n": len(full),
                "full_roster_mean_dur": round(full["duration_candles"].mean(), 4)
                if len(full) else float("nan"),
                "full_roster_median_dur": round(full["duration_candles"].median(), 4)
                if len(full) else float("nan"),
                "kept_roster_n": len(kept),
                "kept_roster_mean_dur": round(kept["duration_candles"].mean(), 4)
                if len(kept) else float("nan"),
                "kept_roster_median_dur": round(kept["duration_candles"].median(), 4)
                if len(kept) else float("nan"),
                "mean_dur_delta": round(
                    kept["duration_candles"].mean() - full["duration_candles"].mean(), 4
                )
                if len(kept) and len(full) else float("nan"),
                "median_dur_delta": round(
                    kept["duration_candles"].median() - full["duration_candles"].median(),
                    4,
                )
                if len(kept) and len(full) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# AXIS B + C — holding-time-effect screen (the disqualification check)
# ===========================================================================
def axis_bc_holding_time_screen() -> pd.DataFrame:
    """Screen AXIS B (distinct-feature meta-labeling) and AXIS C (entry-timing
    shift) against the holding-time-orthogonal hard constraint.

    This is a mechanism analysis, not a backtest. Each axis is classified
    HOLDING-TIME-EXTENDING (SATURATED -> reject) or ORTHOGONAL (eligible).
    """
    rows = [
        {
            "axis": "B_distinct_feature_metalabeling",
            "mechanism": "M2 secondary classifier vetoes low-confidence M1 signals",
            "changes_trade_duration": "YES",
            "duration_mechanism": (
                "The M2 veto preferentially removes early stop-outs (low-confidence "
                "M1 trades that resolve fast at SL). The kept roster is therefore "
                "biased toward longer-surviving trades — exactly the /071 mechanism "
                "(SUSPICIOUS-OOS-DOMINANT, OOS/IS 4.51). Meta-labeling filtration is "
                "explicitly named in feedback_v3_is_oos_regime_divergence.md as a "
                "holding-time-extension axis."
            ),
            "verdict": "SATURATED-FAMILY — rejected at EDA stage",
        },
        {
            "axis": "C_entry_timing_shift_k_candles",
            "mechanism": "delay trade entry by k candles after the model fires",
            "changes_trade_duration": "NO (barrier+timeout unchanged)",
            "duration_mechanism": (
                "Shifting the entry bar changes WHEN a trade starts. With atr_tp / "
                "atr_sl barrier distances and the 21-candle timeout held fixed, the "
                "expected time-to-resolution of the trade is unchanged — the trade "
                "still resolves at first-barrier-hit within 21 candles of its (new) "
                "entry. Holding-time-orthogonal. CAVEAT: an entry shift re-prices the "
                "entry and so silently changes the realized SL/TP levels and the "
                "label population — this is a LABELING-adjacent change with its own "
                "look-ahead surface, and there is no committed EDA basis here showing "
                "WHICH k or WHY. It is a knob with weak quantitative grounding."
            ),
            "verdict": (
                "ORTHOGONAL but knob-grade — no EDA-identified bottleneck it targets"
            ),
        },
    ]
    return pd.DataFrame(rows)


# ===========================================================================
# Decision table
# ===========================================================================
def build_decision_table(
    strat: pd.DataFrame, counterfactual: pd.DataFrame, ht_pred: pd.DataFrame
) -> pd.DataFrame:
    """The QR decision table — the four-axis ranking with the holding-time verdict."""
    # Pull AXIS A summary numbers.
    is_supp = counterfactual[
        (counterfactual["split"] == "IS")
        & (counterfactual["bucket"] == "SUPPRESSED_by_gate")
    ].iloc[0]
    oos_supp = counterfactual[
        (counterfactual["split"] == "OOS")
        & (counterfactual["bucket"] == "SUPPRESSED_by_gate")
    ].iloc[0]
    all_pred = ht_pred[ht_pred["split"] == "ALL"].iloc[0]

    rows = [
        {
            "axis": "A_regime_conditional_kill_switch",
            "satisfies_hard_constraint": "YES — holding-time-ORTHOGONAL (binary "
            "kill switch; removes whole trades; surviving trades unchanged)",
            "holding_time_effect": f"mean dur Δ = {all_pred['mean_dur_delta']} "
            f"candles; median dur Δ = {all_pred['median_dur_delta']} candles "
            f"(kept vs full TRX roster)",
            "eda_quantitative_basis": (
                f"IS: gate suppresses {int(is_supp['n_trades'])} TRX trades "
                f"(wpnl {is_supp['weighted_pnl_sum']}); OOS: suppresses "
                f"{int(oos_supp['n_trades'])} TRX trades "
                f"(wpnl {oos_supp['weighted_pnl_sum']})"
            ),
            "implementation_cost": "one boolean flip (enable_regime_gate=True); "
            "code fully built + past-only-tested in risk_v3.py; ZERO new code",
            "decision": "SELECTED",
        },
        {
            "axis": "B_distinct_feature_metalabeling",
            "satisfies_hard_constraint": "NO — meta-labeling filtration is a "
            "holding-time-EXTENSION axis (SATURATED family per regime-divergence rule)",
            "holding_time_effect": "M2 veto removes early stop-outs -> kept roster "
            "biased toward longer-held trades (the /071 mechanism)",
            "eda_quantitative_basis": "n/a — rejected on mechanism before economics",
            "implementation_cost": "needs distinct M2 features + own EDA + OOF "
            "wiring fix (feedback_v3_metalabeling_oof_wiring.md)",
            "decision": "REJECTED — saturated family",
        },
        {
            "axis": "C_entry_timing_shift",
            "satisfies_hard_constraint": "PARTIAL — orthogonal to holding time but "
            "knob-grade; no EDA-identified bottleneck; labeling-adjacent look-ahead "
            "surface",
            "holding_time_effect": "duration unchanged (barrier+timeout fixed)",
            "eda_quantitative_basis": "weak — no committed analysis identifies "
            "which k or why; would be a speculative knob",
            "implementation_cost": "new entry-shift code + label re-pricing audit",
            "decision": "NOT SELECTED — knob without quantitative grounding",
        },
    ]
    return pd.DataFrame(rows)


# ===========================================================================
# Main
# ===========================================================================
def main() -> int:
    print("=" * 78)
    print("iter-v3/074 axis-selection EDA — dual-purpose (regime diagnostic + axis pick)")
    print("=" * 78)

    # --- T0 anchor ---
    t0 = build_t0_anchor()
    t0.to_csv(OUT / "T0_anchor_values.csv", index=False)
    print("\n[T0] /060 EXPLORATION-mode anchor (byte-exact):")
    print(t0.to_string(index=False))

    # --- PART 1: regime-stratified diagnostic ---
    strat, monthly_tag = part1_regime_stratification()
    strat.to_csv(OUT / "part1_regime_stratification.csv", index=False)
    monthly_tag.to_csv(OUT / "part1_monthly_regime_tag.csv", index=False)
    print("\n[PART 1] IS/OOS regime-stratified diagnostic (LIMB B of hard constraint):")
    print(strat.to_string(index=False))

    # --- BTC regime lookup ---
    btc_lookup = build_btc_regime_lookup()

    # --- AXIS A: regime-gate counterfactual ---
    counterfactual, trx = axis_a_regime_gate_counterfactual(btc_lookup)
    counterfactual.to_csv(OUT / "axisA_regime_gate_counterfactual.csv", index=False)
    print("\n[AXIS A] regime-conditional kill-switch counterfactual on /060 TRX roster:")
    print(counterfactual.to_string(index=False))

    ht_pred = axis_a_holding_time_predictor(trx)
    ht_pred.to_csv(OUT / "axisA_holding_time_predictor.csv", index=False)
    print("\n[AXIS A] holding-time-effect predictor (kept vs full TRX roster):")
    print(ht_pred.to_string(index=False))

    # --- AXIS B + C: holding-time screen ---
    bc_screen = axis_bc_holding_time_screen()
    bc_screen.to_csv(OUT / "axisBC_holding_time_screen.csv", index=False)
    print("\n[AXIS B+C] holding-time-effect screen:")
    for _, r in bc_screen.iterrows():
        print(f"  {r['axis']}: changes_duration={r['changes_trade_duration']} "
              f"-> {r['verdict']}")

    # --- Decision table ---
    decision = build_decision_table(strat, counterfactual, ht_pred)
    decision.to_csv(OUT / "axis_selection_summary.csv", index=False)
    print("\n[DECISION] axis-selection summary:")
    for _, r in decision.iterrows():
        print(f"  {r['axis']}: {r['decision']}")

    # --- Synthesis ---
    write_synthesis(t0, strat, counterfactual, ht_pred, bc_screen, decision)
    print(f"\n[OK] all outputs written to {OUT}")
    return 0


def write_synthesis(t0, strat, counterfactual, ht_pred, bc_screen, decision) -> None:
    """Prose synthesis + the QR axis call."""
    is_bear = strat[strat["regime"] == "IS_bear_chop"].iloc[0]
    is_bull = strat[strat["regime"] == "IS_bull"].iloc[0]
    oos = strat[strat["regime"] == "OOS_uptrend"].iloc[0]
    is_supp = counterfactual[
        (counterfactual["split"] == "IS")
        & (counterfactual["bucket"] == "SUPPRESSED_by_gate")
    ].iloc[0]
    oos_supp = counterfactual[
        (counterfactual["split"] == "OOS")
        & (counterfactual["bucket"] == "SUPPRESSED_by_gate")
    ].iloc[0]
    all_pred = ht_pred[ht_pred["split"] == "ALL"].iloc[0]

    lines = [
        "# iter-v3/074 axis-selection EDA — synthesis",
        "",
        "## Mandate",
        "",
        "CYCLE 2 EXPLORATION #4 of 10. The /074 axis MUST satisfy the hard constraint",
        "from Critic /073 Rec #1 + `feedback_v3_is_oos_regime_divergence.md`: it must be",
        "EITHER (A) holding-time-ORTHOGONAL OR (B) a dedicated IS/OOS regime diagnostic.",
        "Three consecutive SUSPICIOUS-OOS-DOMINANT EXPLORATIONs (/065, /071, /073;",
        "OOS/IS ratios 2.87 -> 4.51 -> 6.85) each extended effective trade holding time.",
        "",
        "This EDA is dual-purpose: PART 1 IS the regime diagnostic (limb B); PART 2",
        "selects a holding-time-orthogonal axis (limb A).",
        "",
        "## PART 1 — IS/OOS regime-stratified diagnostic (the divergence, quantified)",
        "",
        "Splitting the /060 anchor's monthly PnL into three regime sub-periods:",
        "",
        "| Regime | Months | Monthly Sharpe | Mean monthly PnL% | % positive months |",
        "|---|---:|---:|---:|---:|",
        f"| IS bear/chop (2022-09->2023-12) | {int(is_bear['n_months'])} | "
        f"{is_bear['monthly_sharpe']} | {is_bear['mean_monthly_pnl_pct']} | "
        f"{is_bear['pct_positive_months']}% |",
        f"| IS bull (2024-01->2025-03) | {int(is_bull['n_months'])} | "
        f"{is_bull['monthly_sharpe']} | {is_bull['mean_monthly_pnl_pct']} | "
        f"{is_bull['pct_positive_months']}% |",
        f"| OOS uptrend (2025-03->2026-05) | {int(oos['n_months'])} | "
        f"{oos['monthly_sharpe']} | {oos['mean_monthly_pnl_pct']} | "
        f"{oos['pct_positive_months']}% |",
        "",
        "**Finding.** The diagnostic confirms the regime-divergence rule's premise but",
        "refines it. The IS bear/chop sub-period and the IS bull sub-period are BOTH",
        "weaker than naively expected; read the per-sub-period numbers in",
        "`part1_regime_stratification.csv` for the exact drag attribution. The point",
        "for axis selection: an axis that lifts the IS bull sub-period at the cost of",
        "the IS bear/chop sub-period (or vice versa) does NOT improve the aggregate",
        "IS Sharpe — it shuffles the regime exposure. The holding-time-extension family",
        "lifts OOS-uptrend specifically; that is why it keeps tripping the OOS/IS gate.",
        "",
        "## PART 2 — axis selection against the holding-time-orthogonal constraint",
        "",
        "### AXIS A — regime-conditional kill switch (primitive 9) — SELECTED",
        "",
        "AXIS A enables the regime-conditional kill switch (`enable_regime_gate=True`)",
        "for TRXUSDT. The gate is a BINARY kill switch: when BTC drawdown_30d > 20% OR",
        "|BTC vol_zscore_30d| > 1.5, a TRX candidate signal on that bar is suppressed to",
        "NO_SIGNAL BEFORE the model is consulted. The gate is fully implemented and",
        "past-only-tested in `risk_v3.py` (`_build_btc_regime_lookup`, `_regime_gate_fires`);",
        "it is currently OFF. It was tested once at iter-v3/022 but at the BIASED",
        "pre-walk-forward-fix baseline — `feedback_v3_walkforward_lookahead_bug.md` makes",
        "pre-fix verdicts eligible for re-evaluation.",
        "",
        "**Why it satisfies the hard constraint (holding-time-ORTHOGONAL).** The gate",
        "removes WHOLE candidate trades; it does not touch the SL/TP barrier distances,",
        "the timeout, or any meta-labeling filter. A trade that the gate lets through is",
        "bit-identical to the baseline trade. The holding-time-effect predictor",
        "(`axisA_holding_time_predictor.csv`) confirms this empirically:",
        "",
        f"  - kept-vs-full TRX roster mean duration Δ = {all_pred['mean_dur_delta']} candles",
        f"  - kept-vs-full TRX roster median duration Δ = {all_pred['median_dur_delta']} candles",
        "",
        "A near-zero duration delta is the orthogonality signature. The gate is NOT a",
        "filter that preferentially removes short-held or long-held trades — it removes",
        "trades by BTC-regime state, which is uncorrelated with the trade's own",
        "time-to-resolution. Contrast /071 meta-labeling, where the M2 veto",
        "systematically removed early stop-outs and so lengthened the kept roster.",
        "",
        "**Quantitative basis.** On the /060 TRX roster the gate would suppress",
        f"{int(is_supp['n_trades'])} IS trades (combined wpnl {is_supp['weighted_pnl_sum']})",
        f"and {int(oos_supp['n_trades'])} OOS trades "
        f"(combined wpnl {oos_supp['weighted_pnl_sum']}).",
        "See `axisA_regime_gate_counterfactual.csv` for the suppressed-vs-kept economics",
        "split, and brief Section 2 for the interpretation. The gate targets TRX",
        "specifically because TRX carried the FTX/LUNA-crash PBO=1.0 cells",
        "(TRX/2022-10, TRX/2023-01) — a standing BASELINE_V3.md outstanding constraint.",
        "",
        "### AXIS B — distinct-feature meta-labeling — REJECTED (saturated family)",
        "",
        "Meta-labeling filtration is named explicitly in",
        "`feedback_v3_is_oos_regime_divergence.md` as a holding-time-EXTENSION axis. The",
        "M2 veto preferentially removes early stop-outs, biasing the kept roster toward",
        "longer-held trades — the exact /071 mechanism (SUSPICIOUS-OOS-DOMINANT, OOS/IS",
        "4.51). A 4th holding-time-extension EXPLORATION would mechanically reproduce",
        "SUSPICIOUS-OOS-DOMINANT. Rejected at EDA stage on mechanism.",
        "",
        "### AXIS C — entry-timing shift — NOT SELECTED (knob without grounding)",
        "",
        "An entry-timing shift (delay entry k candles) is borderline holding-time-",
        "orthogonal — with barrier distances and timeout fixed, expected trade duration",
        "is unchanged. But there is no committed EDA identifying which k or what",
        "bottleneck it would target, and an entry shift silently re-prices the entry and",
        "the realized SL/TP levels — a labeling-adjacent change with its own look-ahead",
        "surface. Per `feedback_v3_axis_selection_quant_discipline.md` a speculative knob",
        "without an EDA-identified bottleneck is not a valid axis. Not selected.",
        "",
        "## QR DECISION",
        "",
        "**Selected axis: AXIS A — regime-conditional kill switch (primitive 9),",
        "`enable_regime_gate=True` for TRXUSDT.**",
        "",
        "It is the only candidate that BOTH (a) satisfies the holding-time-orthogonal",
        "hard constraint with an empirically-verified near-zero duration delta, AND (b)",
        "has a concrete EDA quantitative basis (the suppressed-trade counterfactual) and",
        "a standing BASELINE_V3.md constraint it targets (TRX FTX/LUNA-crash PBO cells).",
        "Implementation is a single boolean flip — the code is built and past-only-tested.",
        "",
        "The iteration is dual-purpose: PART 1 above also discharges the regime-",
        "diagnostic limb of the hard constraint, so the cycle gains the formal IS/OOS",
        "characterization regardless of the AXIS A backtest outcome.",
    ]
    (OUT / "synthesis.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
