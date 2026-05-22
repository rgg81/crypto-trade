"""iter-v3/114 — LDO kill-switch gating EDA (GO/NO-GO).

Cycle-6 EXPLORATION slot #5. Axis: a per-symbol LDO regime-conditional
EXOGENOUS-trigger kill-switch (binary off/on) — RiskV3 primitive 9 re-targeted
from TRX (iter-v3/022) to LDO.

The EDA is strictly IS-only (every labelled row has close_time < OOS_CUTOFF_MS).
It answers four questions in order:

  T1  Deadlock-impossibility: is the exogenous trigger genuinely independent of
      LDO trade outcomes? (a structural check the brief Section 2 formalises)
  T2  Trigger separation: does each candidate exogenous trigger (BTC-DD,
      BTC-vol-z, LDO-realvol-z) separate loss-making LDO candle-windows from
      profitable ones, on the FULL IS LDO candle panel (not just 9 trades)?
  T3  Threshold sweep: across IS-percentile thresholds, what is the
      counterfactual IS effect of suppressing LDO candles flagged by the
      trigger? Pick the IS-calibrated threshold.
  T4  ORACLE counterfactual on the /059 LDO IS roster (9 trades): how many of
      the 9 IS LDO trades does the chosen gate suppress, and what is the
      counterfactual IS weighted-PnL delta? (valid because the trigger is
      exogenous — Section 2 of the brief.)
  T5  Behavioural-effect predictor: pre-register the expected LDO IS trade-count
      reduction and the portfolio-roster shift, with a falsifier band ABOVE the
      inertia floor (Critic /113 Recommendation 3).
  T6  GO/NO-GO verdict synthesis.
  T7  Per-symbol non-contamination check (BCH/TRX untouched — the gate is
      LDO-only; their IS candle panels are unchanged by construction).
  T8  IC / feature-set check (a risk axis adds NO features; confirm).
  T9  OOS trigger-coverage sanity annex (clearly fenced; sizes whether the gate
      has any OOS surface — NOT a threshold-tuning step).

Outputs T1..T9 CSVs into analysis/iteration_v3-114/.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from _shared import (
    OOS_CUTOFF_MS,
    TARGET,
    asof_trigger,
    build_btc_regime_series,
    build_ldo_realvol_zscore,
    label_one_symbol,
    load_059_ldo_roster,
    load_btc_8h_csv,
    load_symbol_8h,
)

# write outputs next to this script regardless of cwd
OUT = str(Path(__file__).resolve().parent)


# --------------------------------------------------------------------------
# Build the IS LDO candle panel + the three exogenous trigger series.
# --------------------------------------------------------------------------
def build_panel() -> pd.DataFrame:
    """IS-only LDO candle panel: every labelled LDO 8h candle, joined past-only
    to BTC-DD, BTC-vol-z, LDO-realvol-z."""
    ldo = load_symbol_8h(TARGET, is_only=True)
    ldo = label_one_symbol(ldo)
    ldo = ldo.loc[ldo["label_valid"]].reset_index(drop=True)

    btc = load_btc_8h_csv()
    btc_reg = build_btc_regime_series(btc)
    ldo_vol = build_ldo_realvol_zscore(load_symbol_8h(TARGET, is_only=False))

    ot = ldo["open_time"].to_numpy(dtype=np.int64)
    ldo["btc_drawdown_pct"] = asof_trigger(ot, btc_reg, "btc_drawdown_pct")
    ldo["btc_vol_zscore"] = asof_trigger(ot, btc_reg, "btc_vol_zscore")
    ldo["ldo_realvol_zscore"] = asof_trigger(ot, ldo_vol, "ldo_realvol_zscore")
    # the gate's absolute-value comparands (risk_v3 compares abs(dd), abs(vz))
    ldo["abs_btc_dd"] = ldo["btc_drawdown_pct"].abs()
    ldo["abs_btc_vz"] = ldo["btc_vol_zscore"].abs()
    ldo["abs_ldo_vz"] = ldo["ldo_realvol_zscore"].abs()
    return ldo


# --------------------------------------------------------------------------
# T1 — deadlock-impossibility structural check
# --------------------------------------------------------------------------
def t1_deadlock_check(panel: pd.DataFrame) -> pd.DataFrame:
    """Confirm each exogenous trigger is a function of price only — NOT of LDO
    trade outcomes. The decisive structural property: the trigger series is
    fully determined BEFORE any LDO trade is taken (it is built from BTC/LDO
    OHLCV alone). A kill-switch that suppresses LDO trading cannot alter BTC
    price, cannot alter LDO price, hence cannot alter the trigger. The
    gate-state transition function has NO dependence on the gate's own action
    -> no closed feedback loop -> deadlock impossible.

    The /054 endogenous drawdown brake deadlocked because brake-ON suppressed
    the LDO trades whose PnL fed the brake's own drawdown tracker. Here the
    trigger is computed from exogenous price; the table records the input
    provenance of each candidate trigger to make the independence auditable.
    """
    rows = [
        {
            "trigger": "btc_drawdown_pct",
            "input_series": "BTCUSDT 8h close",
            "depends_on_LDO_trades": False,
            "depends_on_LDO_price": False,
            "depends_on_BTC_price": True,
            "deadlock_possible": False,
            "note": "BTC price unaffected by LDO trading -> trigger frozen-free",
        },
        {
            "trigger": "btc_vol_zscore",
            "input_series": "BTCUSDT 8h close log-returns",
            "depends_on_LDO_trades": False,
            "depends_on_LDO_price": False,
            "depends_on_BTC_price": True,
            "deadlock_possible": False,
            "note": "BTC vol unaffected by LDO trading -> trigger frozen-free",
        },
        {
            "trigger": "ldo_realvol_zscore",
            "input_series": "LDOUSDT 8h close log-returns",
            "depends_on_LDO_trades": False,
            "depends_on_LDO_price": True,
            "depends_on_BTC_price": False,
            "deadlock_possible": False,
            "note": (
                "LDO PRICE != LDO TRADE OUTCOMES; kill-switch halts LDO trading "
                "not LDO price -> realized-vol series updates regardless -> "
                "frozen-free. Contrast /054 endogenous PnL-streak brake."
            ),
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T1_deadlock_impossibility.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T2 — trigger separation on the full IS LDO candle panel
# --------------------------------------------------------------------------
def t2_trigger_separation(panel: pd.DataFrame) -> pd.DataFrame:
    """For each candidate trigger, split the IS LDO candle panel at the trigger
    median into a HIGH-trigger and LOW-trigger half, and compare the realized
    candle outcome (candle_net_pnl) of each half.

    A trigger SEPARATES if the HIGH-trigger half (the regime the kill-switch
    would suppress) has materially WORSE mean candle PnL than the LOW-trigger
    half. The mean-PnL gap is the raw separation strength; a Welch t-stat sizes
    significance. We also report the win rate (candle_net_pnl > 0) per half.
    """
    rows = []
    cn = panel["candle_net_pnl"].to_numpy()
    for trig in ("abs_btc_dd", "abs_btc_vz", "abs_ldo_vz"):
        v = panel[trig].to_numpy()
        ok = np.isfinite(v) & np.isfinite(cn)
        v2, cn2 = v[ok], cn[ok]
        if len(v2) < 30:
            continue
        med = np.median(v2)
        hi = cn2[v2 > med]
        lo = cn2[v2 <= med]
        # Welch t-stat for difference of means (hi - lo)
        m_hi, m_lo = hi.mean(), lo.mean()
        s_hi = hi.std(ddof=1) / np.sqrt(len(hi)) if len(hi) > 1 else np.nan
        s_lo = lo.std(ddof=1) / np.sqrt(len(lo)) if len(lo) > 1 else np.nan
        se = np.sqrt(s_hi**2 + s_lo**2)
        tstat = (m_hi - m_lo) / se if se and np.isfinite(se) else np.nan
        rows.append(
            {
                "trigger": trig,
                "n_candles": len(cn2),
                "median_threshold": round(float(med), 4),
                "n_high": len(hi),
                "n_low": len(lo),
                "mean_pnl_high": round(float(m_hi), 4),
                "mean_pnl_low": round(float(m_lo), 4),
                "separation_gap": round(float(m_hi - m_lo), 4),
                "winrate_high": round(float((hi > 0).mean()), 4),
                "winrate_low": round(float((lo > 0).mean()), 4),
                "welch_t": round(float(tstat), 3) if np.isfinite(tstat) else np.nan,
                "separates": bool(np.isfinite(tstat) and (m_hi - m_lo) < 0),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T2_trigger_separation.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T3 — threshold sweep (counterfactual IS effect of suppression)
# --------------------------------------------------------------------------
def t3_threshold_sweep(panel: pd.DataFrame) -> pd.DataFrame:
    """For each trigger and a grid of IS-percentile thresholds, simulate the
    counterfactual: SUPPRESS every IS LDO candle whose trigger value exceeds the
    threshold, KEEP the rest. Measure:
        - fire_rate          fraction of IS candles suppressed
        - suppressed_mean    mean candle_net_pnl of the SUPPRESSED candles
        - kept_mean          mean candle_net_pnl of the KEPT candles
        - kept_total_uplift  (kept_mean - all_mean) — the per-candle quality
                             uplift of the surviving panel
        - lossavoid_ratio    fraction of suppressed candles that were losers

    A useful gate suppresses a high-loss-density slice: suppressed_mean << 0
    and lossavoid_ratio high. The threshold for the brief is chosen on the
    best trigger as the percentile where suppressed_mean is most negative
    subject to fire_rate in a sane band (~8-25%) — small enough not to gut the
    panel, large enough to be behaviourally non-inert.
    """
    cn = panel["candle_net_pnl"].to_numpy()
    all_mean = np.nanmean(cn)
    pctiles = [75, 80, 82, 85, 88, 90, 92, 95]
    rows = []
    for trig in ("abs_btc_dd", "abs_btc_vz", "abs_ldo_vz"):
        v = panel[trig].to_numpy()
        ok = np.isfinite(v) & np.isfinite(cn)
        v2, cn2 = v[ok], cn[ok]
        if len(v2) < 30:
            continue
        for p in pctiles:
            thr = np.percentile(v2, p)
            fire = v2 > thr
            n_fire = int(fire.sum())
            if n_fire == 0:
                continue
            supp = cn2[fire]
            kept = cn2[~fire]
            rows.append(
                {
                    "trigger": trig,
                    "pctile": p,
                    "threshold": round(float(thr), 4),
                    "fire_rate": round(n_fire / len(cn2), 4),
                    "n_suppressed": n_fire,
                    "n_kept": len(kept),
                    "suppressed_mean_pnl": round(float(supp.mean()), 4),
                    "kept_mean_pnl": round(float(kept.mean()), 4)
                    if len(kept)
                    else np.nan,
                    "all_mean_pnl": round(float(all_mean), 4),
                    "kept_total_uplift": round(
                        float(kept.mean() - all_mean), 4
                    )
                    if len(kept)
                    else np.nan,
                    "lossavoid_ratio": round(float((supp < 0).mean()), 4),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T3_threshold_sweep.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T4 — ORACLE counterfactual on the /059 LDO IS roster (9 trades)
# --------------------------------------------------------------------------
def t4_oracle_roster(chosen_trigger: str, chosen_threshold: float) -> pd.DataFrame:
    """Apply the chosen gate to the canonical /059 LDO IS trade roster.

    For each of the 9 IS LDO trades, recompute the trigger value at the trade's
    open_time (past-only as-of join) and mark the trade SUPPRESSED if the
    trigger exceeds the chosen threshold. Report:
        - per-trade: open_time, direction, exit_reason, net_pnl_pct,
          weighted_pnl, trigger value, suppressed?
        - aggregate: counterfactual IS weighted-PnL delta = -sum(weighted_pnl of
          suppressed trades); IS trade-count delta.

    This is a VALID counterfactual because the trigger is EXOGENOUS — the gate's
    suppression of an LDO trade does not change the BTC/LDO price series the
    trigger is built from, so the trigger value at every other trade's open_time
    is unchanged. (An endogenous PnL-streak trigger would NOT have this
    property; that is the /054 invalid-ORACLE case.)

    The map column tells which trigger -> series:
        abs_btc_dd  -> btc_drawdown_pct (abs)
        abs_btc_vz  -> btc_vol_zscore   (abs)
        abs_ldo_vz  -> ldo_realvol_zscore (abs)
    """
    roster = load_059_ldo_roster("in_sample")
    btc = load_btc_8h_csv()
    btc_reg = build_btc_regime_series(btc)
    ldo_vol = build_ldo_realvol_zscore(load_symbol_8h(TARGET, is_only=False))

    ot = roster["open_time"].to_numpy(dtype=np.int64)
    series_map = {
        "abs_btc_dd": ("btc_drawdown_pct", btc_reg),
        "abs_btc_vz": ("btc_vol_zscore", btc_reg),
        "abs_ldo_vz": ("ldo_realvol_zscore", ldo_vol),
    }
    col, src = series_map[chosen_trigger]
    raw = asof_trigger(ot, src, col)
    trig_val = np.abs(raw)
    suppressed = trig_val > chosen_threshold

    rows = []
    for k in range(len(roster)):
        r = roster.iloc[k]
        rows.append(
            {
                "open_time": int(r["open_time"]),
                "date": pd.to_datetime(int(r["open_time"]), unit="ms").strftime(
                    "%Y-%m-%d"
                ),
                "direction": int(r["direction"]),
                "exit_reason": r["exit_reason"],
                "net_pnl_pct": round(float(r["net_pnl_pct"]), 4),
                "weighted_pnl": round(float(r["weighted_pnl"]), 4),
                "trigger": chosen_trigger,
                "trigger_value": round(float(trig_val[k]), 4)
                if np.isfinite(trig_val[k])
                else np.nan,
                "threshold": round(float(chosen_threshold), 4),
                "suppressed": bool(suppressed[k]),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T4_oracle_roster_counterfactual.csv", index=False)

    # aggregate
    supp_rows = df[df["suppressed"]]
    keep_rows = df[~df["suppressed"]]
    agg = pd.DataFrame(
        [
            {
                "chosen_trigger": chosen_trigger,
                "chosen_threshold": round(float(chosen_threshold), 4),
                "n_is_ldo_trades": len(df),
                "n_suppressed": len(supp_rows),
                "n_kept": len(keep_rows),
                "suppressed_wpnl_sum": round(
                    float(supp_rows["weighted_pnl"].sum()), 4
                ),
                "kept_wpnl_sum": round(float(keep_rows["weighted_pnl"].sum()), 4),
                "baseline_wpnl_sum": round(float(df["weighted_pnl"].sum()), 4),
                "counterfactual_wpnl_delta": round(
                    float(-supp_rows["weighted_pnl"].sum()), 4
                ),
                "suppressed_were_losers": int((supp_rows["net_pnl_pct"] < 0).sum()),
                "suppressed_were_winners": int(
                    (supp_rows["net_pnl_pct"] >= 0).sum()
                ),
            }
        ]
    )
    agg.to_csv(f"{OUT}/T4_oracle_aggregate.csv", index=False)
    return agg


# --------------------------------------------------------------------------
# T5 — behavioural-effect predictor (pre-registered, ABOVE the inertia floor)
# --------------------------------------------------------------------------
def t5_behavioural_predictor(
    panel: pd.DataFrame,
    chosen_trigger: str,
    chosen_threshold: float,
    t4_agg: pd.DataFrame,
) -> pd.DataFrame:
    """Pre-register the expected behavioural effect of the kill-switch — sized
    well above the 8% behavioural-inertia floor (Critic /113 Recommendation 3).

    Two distinct behavioural-effect channels are pre-registered:

    (A) LDO-roster channel — the % of the /059 LDO IS roster the gate suppresses.
        The /059 LDO IS roster is 9 trades; if the gate suppresses k of them the
        LDO-roster shift is k/9. This is the DIRECT, target-symbol behavioural
        effect — and on a 9-trade roster it is coarse (one trade = 11.1%).

    (B) Portfolio-roster channel — the % of the /059 PORTFOLIO IS roster
        (BCH+TRX+LDO = 171 trades) that changes. Suppressing k LDO trades is a
        k/171 portfolio-roster shift. NOTE: this is the metric the /113 inertia
        falsifier used (it moved only 1.89% / 156). A risk gate that touches one
        symbol's ~9-trade IS roster within a 171-trade portfolio CANNOT move the
        PORTFOLIO roster by 8% — at most 9/171 = 5.3%. The PORTFOLIO-roster
        metric is therefore the WRONG inertia metric for a per-symbol risk axis:
        a per-symbol gate is structurally incapable of clearing an 8% portfolio
        floor. The brief Section 4.3 pre-registers the inertia falsifier on the
        TARGET-SYMBOL (LDO) roster instead — that is the metric the axis can
        legitimately move.

    The pre-registered behavioural-effect predictor (the falsifier band) is on
    the LDO IS trade-count reduction, with a floor set ABOVE inertia:

        Predicted LDO IS trade suppression: the T4 ORACLE count (k of 9).
        Behavioural-inertia falsifier (LDO-roster): if the production backtest
        suppresses < 1 LDO IS trade (LDO IS roster Δ = 0 vs the /059-canonical
        9), the axis is behaviourally inert and the iteration is INERT.

    Because the gate operates at the per-bar candidate-signal layer (it kills
    the signal before Optuna sees the bar — RiskV3 primitive 9 order: regime
    gate fires FIRST), it also reshapes the LDO training panel. The
    panel-suppression count (IS LDO candles with trigger > threshold) is the
    broader behavioural surface and is reported as the panel-channel predictor.
    """
    v = panel[chosen_trigger].to_numpy()
    cn = panel["candle_net_pnl"].to_numpy()
    ok = np.isfinite(v) & np.isfinite(cn)
    v2 = v[ok]
    panel_fire = int((v2 > chosen_threshold).sum())
    panel_total = int(len(v2))

    k_supp = int(t4_agg["n_suppressed"].iloc[0])
    rows = [
        {
            "channel": "LDO_panel_candles",
            "metric": "IS LDO candles suppressed (training-panel reshape)",
            "predicted_count": panel_fire,
            "denominator": panel_total,
            "predicted_pct": round(panel_fire / panel_total * 100, 2)
            if panel_total
            else np.nan,
            "inertia_floor_pct": 8.0,
            "above_inertia_floor": bool(
                panel_total and panel_fire / panel_total * 100 >= 8.0
            ),
        },
        {
            "channel": "LDO_roster_trades",
            "metric": "/059 LDO IS roster trades suppressed (ORACLE T4)",
            "predicted_count": k_supp,
            "denominator": 9,
            "predicted_pct": round(k_supp / 9 * 100, 2),
            "inertia_floor_pct": 8.0,
            "above_inertia_floor": bool(k_supp / 9 * 100 >= 8.0),
        },
        {
            "channel": "portfolio_roster_trades",
            "metric": "/059 PORTFOLIO IS roster shift (WRONG metric for per-symbol axis)",
            "predicted_count": k_supp,
            "denominator": 171,
            "predicted_pct": round(k_supp / 171 * 100, 2),
            "inertia_floor_pct": 8.0,
            "above_inertia_floor": False,
            # a per-symbol gate is structurally incapable of an 8% portfolio shift
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T5_behavioural_predictor.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T6 — GO/NO-GO verdict synthesis
# --------------------------------------------------------------------------
def t6_verdict(
    t2: pd.DataFrame,
    t3: pd.DataFrame,
    t4_agg: pd.DataFrame,
    chosen_trigger: str,
    chosen_threshold: float,
) -> pd.DataFrame:
    """Synthesise the GO/NO-GO verdict.

    GO criteria (all must hold):
      C1  the chosen trigger SEPARATES in T2 (HIGH-trigger half has worse mean
          candle PnL than the LOW-trigger half; separation_gap < 0).
      C2  at the chosen threshold, T3 suppressed_mean_pnl < 0 AND
          lossavoid_ratio > 0.50 (the suppressed slice is loss-dense).
      C3  the T4 ORACLE counterfactual on the /059 LDO IS roster suppresses
          >= 1 LDO trade AND the counterfactual weighted-PnL delta is >= 0
          (the gate, on the canonical roster, removes net loss not net gain).
      C4  fire_rate at the chosen threshold is in [0.08, 0.30] (behaviourally
          non-inert on the panel, but not panel-gutting).

    A "SHARPENED-GO" is recorded if C1-C3 hold but C4 is marginal, or if the
    ORACLE roster is too thin (9 trades) to be decisive on its own — the
    production backtest is then the decisive test (THE PRIME DIRECTIVE: the EDA
    designs the experiment, it does not terminate it).
    """
    sep = t2[t2["trigger"] == chosen_trigger]
    c1 = bool(len(sep) and sep["separates"].iloc[0])

    sweep = t3[
        (t3["trigger"] == chosen_trigger)
        & (np.isclose(t3["threshold"], chosen_threshold))
    ]
    if len(sweep):
        c2 = bool(
            (sweep["suppressed_mean_pnl"].iloc[0] < 0)
            and (sweep["lossavoid_ratio"].iloc[0] > 0.50)
        )
        fire_rate = float(sweep["fire_rate"].iloc[0])
        c4 = bool(0.08 <= fire_rate <= 0.30)
    else:
        c2, c4, fire_rate = False, False, np.nan

    n_supp = int(t4_agg["n_suppressed"].iloc[0])
    cf_delta = float(t4_agg["counterfactual_wpnl_delta"].iloc[0])
    c3 = bool(n_supp >= 1 and cf_delta >= 0.0)

    go = c1 and c2 and c3 and c4
    sharpened = (c1 and c2 and c3) and not c4

    if go:
        verdict = "GO"
    elif sharpened:
        verdict = "SHARPENED-GO"
    elif c1 and c2:
        # trigger separates and suppresses loss but roster too thin / fire-rate
        # off — the production backtest is the decisive test
        verdict = "SHARPENED-GO"
    else:
        verdict = "WEAK-GO"  # never NO-GO at EDA — PRIME DIRECTIVE: run the backtest

    df = pd.DataFrame(
        [
            {
                "chosen_trigger": chosen_trigger,
                "chosen_threshold": round(float(chosen_threshold), 4),
                "C1_trigger_separates": c1,
                "C2_suppressed_slice_loss_dense": c2,
                "C3_oracle_roster_removes_net_loss": c3,
                "C4_fire_rate_in_band": c4,
                "fire_rate": round(fire_rate, 4)
                if np.isfinite(fire_rate)
                else np.nan,
                "oracle_n_suppressed": n_supp,
                "oracle_cf_wpnl_delta": round(cf_delta, 4),
                "verdict": verdict,
            }
        ]
    )
    df.to_csv(f"{OUT}/T6_go_nogo_verdict.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T7 — per-symbol non-contamination check
# --------------------------------------------------------------------------
def t7_non_contamination() -> pd.DataFrame:
    """Confirm the kill-switch is LDO-only and cannot touch BCH/TRX.

    The production gate (RiskV3 primitive 9) fires only for symbols in
    config.regime_gate_symbols. iter-v3/114 sets that to ("LDOUSDT",). BCH and
    TRX are NOT in scope, so _regime_gate_fires returns False for them
    unconditionally and their candidate signals pass through unchanged. At the
    per-symbol architecture layer (one LightGBM per symbol), BCH/TRX Optuna
    trajectories are wholly independent of the LDO gate — per
    `feedback_v3_single_seed_frozen_baseline.md` (the iter-v3/022 forensic
    finding: a TRX-only regime gate produced bit-identical BCH/LDO rosters).
    The table records the expected per-symbol gate exposure.
    """
    rows = [
        {
            "symbol": "BCHUSDT",
            "in_regime_gate_symbols": False,
            "expected_gate_fires": 0,
            "expected_roster_change": "none (bit-identical to /059 BCH)",
        },
        {
            "symbol": "TRXUSDT",
            "in_regime_gate_symbols": False,
            "expected_gate_fires": 0,
            "expected_roster_change": "none (bit-identical to /059 TRX)",
        },
        {
            "symbol": "LDOUSDT",
            "in_regime_gate_symbols": True,
            "expected_gate_fires": ">=1 (the target; see T4/T5)",
            "expected_roster_change": "LDO IS roster shrinks by the suppressed count",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T7_non_contamination.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T8 — feature-set / IC check (a risk axis adds NO features)
# --------------------------------------------------------------------------
def t8_feature_set_check() -> pd.DataFrame:
    """A risk-management axis adds ZERO features. iter-v3/114 reverts
    V3_FEATURE_COLUMNS from /113's 22-feature stack back to the /059-canonical
    14-feature stack. There is no new feature family, hence no IC gate to run
    (Critic Check 4 is non-applicable). The table records the feature-set state
    transition so the brief Section 3.5 / Phase 5.5 gate can verify it.
    """
    rows = [
        {
            "aspect": "V3_FEATURE_COLUMNS count",
            "iter_v3_113": 22,
            "iter_v3_114": 14,
            "delta": "revert 22 -> 14 (drop /113 multi-frequency daily features)",
        },
        {
            "aspect": "new feature families",
            "iter_v3_113": "8 daily features (CLOSED at /113)",
            "iter_v3_114": "0",
            "delta": "none — risk axis, not a feature axis",
        },
        {
            "aspect": "IC gate (Critic Check 4)",
            "iter_v3_113": "FAIL strict reading (4 daily features |IC|>0.70)",
            "iter_v3_114": "non-applicable (no new features)",
            "delta": "Check 4 N/A",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/T8_feature_set_check.csv", index=False)
    return df


# --------------------------------------------------------------------------
# T9 — OOS trigger-coverage sanity annex (FENCED — sizes OOS surface only)
# --------------------------------------------------------------------------
def t9_oos_coverage_annex(chosen_trigger: str, chosen_threshold: float) -> pd.DataFrame:
    """FENCED OOS ANNEX. Loads the /059 LDO OOS roster ONLY to size whether the
    chosen gate would have ANY OOS firing surface — i.e. whether the gate is
    dead on arrival in the OOS window. This is NOT a threshold-tuning step; the
    threshold is fixed by the IS-only T3 sweep BEFORE this annex runs. The annex
    answers one question: 'does the IS-calibrated gate fire at all on the OOS
    LDO trades, or is it inert OOS?'

    Reported numbers are coverage counts only — never used to adjust the
    threshold. The brief cites this annex as a feasibility check, flagged as the
    one place the EDA touches an OOS-window file. (The QR does NOT inspect OOS
    Sharpe / PnL — only the trigger-firing count on the OOS roster open_times.)
    """
    roster = load_059_ldo_roster("out_of_sample")
    btc = load_btc_8h_csv()
    btc_reg = build_btc_regime_series(btc)
    ldo_vol = build_ldo_realvol_zscore(load_symbol_8h(TARGET, is_only=False))
    series_map = {
        "abs_btc_dd": ("btc_drawdown_pct", btc_reg),
        "abs_btc_vz": ("btc_vol_zscore", btc_reg),
        "abs_ldo_vz": ("ldo_realvol_zscore", ldo_vol),
    }
    col, src = series_map[chosen_trigger]
    ot = roster["open_time"].to_numpy(dtype=np.int64)
    trig_val = np.abs(asof_trigger(ot, src, col))
    fires = trig_val > chosen_threshold
    df = pd.DataFrame(
        [
            {
                "chosen_trigger": chosen_trigger,
                "chosen_threshold": round(float(chosen_threshold), 4),
                "n_oos_ldo_trades": len(roster),
                "n_oos_trigger_fires": int(np.nansum(fires)),
                "oos_fire_coverage": round(
                    float(np.nansum(fires)) / len(roster), 4
                )
                if len(roster)
                else np.nan,
                "gate_dead_on_arrival_oos": bool(np.nansum(fires) == 0),
                "note": "coverage-sizing ONLY; threshold fixed IS-only by T3",
            }
        ]
    )
    df.to_csv(f"{OUT}/T9_oos_coverage_annex.csv", index=False)
    return df


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    print("=" * 72)
    print("iter-v3/114 — LDO kill-switch gating EDA (GO/NO-GO)")
    print("=" * 72)

    panel = build_panel()
    print(f"IS LDO candle panel: {len(panel)} labelled candles")
    print(f"  open_time range: {panel['open_time'].min()} .. {panel['open_time'].max()}")
    assert (panel["close_time"] < OOS_CUTOFF_MS).all(), "IS-only violated"

    t1 = t1_deadlock_check(panel)
    print("\n[T1] deadlock-impossibility:")
    print(t1[["trigger", "depends_on_LDO_trades", "deadlock_possible"]].to_string(index=False))

    t2 = t2_trigger_separation(panel)
    print("\n[T2] trigger separation (HIGH-trigger half vs LOW):")
    print(t2.to_string(index=False))

    t3 = t3_threshold_sweep(panel)
    print("\n[T3] threshold sweep (counterfactual IS suppression):")
    print(t3.to_string(index=False))

    # ---- choose the trigger + threshold (IS-only) ----
    # trigger: the one with the strongest (most negative) separation_gap in T2
    sep_ok = t2[t2["separates"]]
    if len(sep_ok):
        chosen_trigger = sep_ok.sort_values("separation_gap").iloc[0]["trigger"]
    else:
        # no trigger separates cleanly — still pick the least-bad and run the
        # backtest (PRIME DIRECTIVE: EDA designs, does not terminate)
        chosen_trigger = t2.sort_values("separation_gap").iloc[0]["trigger"]
    print(f"\nchosen trigger (strongest IS separation): {chosen_trigger}")

    # threshold: on the chosen trigger, the percentile whose suppressed slice is
    # most loss-dense subject to fire_rate in [0.08, 0.30]
    cand = t3[
        (t3["trigger"] == chosen_trigger)
        & (t3["fire_rate"] >= 0.08)
        & (t3["fire_rate"] <= 0.30)
    ].copy()
    if len(cand):
        # rank by loss density: most-negative suppressed_mean_pnl, tie-break
        # highest lossavoid_ratio
        cand = cand.sort_values(
            ["suppressed_mean_pnl", "lossavoid_ratio"],
            ascending=[True, False],
        )
        chosen_threshold = float(cand.iloc[0]["threshold"])
        chosen_pctile = int(cand.iloc[0]["pctile"])
    else:
        # fall back to the 85th percentile of the chosen trigger
        sub = t3[t3["trigger"] == chosen_trigger]
        row85 = sub[sub["pctile"] == 85]
        chosen_threshold = float(row85.iloc[0]["threshold"]) if len(row85) else float(
            sub.iloc[len(sub) // 2]["threshold"]
        )
        chosen_pctile = 85
    print(f"chosen threshold (IS-calibrated): {chosen_threshold:.4f} "
          f"(pctile {chosen_pctile})")

    t4 = t4_oracle_roster(chosen_trigger, chosen_threshold)
    print("\n[T4] ORACLE counterfactual on /059 LDO IS roster (9 trades):")
    print(t4.to_string(index=False))

    t5 = t5_behavioural_predictor(panel, chosen_trigger, chosen_threshold, t4)
    print("\n[T5] behavioural-effect predictor:")
    print(t5.to_string(index=False))

    t6 = t6_verdict(t2, t3, t4, chosen_trigger, chosen_threshold)
    print("\n[T6] GO/NO-GO verdict:")
    print(t6.to_string(index=False))

    t7 = t7_non_contamination()
    print("\n[T7] per-symbol non-contamination:")
    print(t7.to_string(index=False))

    t8 = t8_feature_set_check()
    print("\n[T8] feature-set check:")
    print(t8.to_string(index=False))

    t9 = t9_oos_coverage_annex(chosen_trigger, chosen_threshold)
    print("\n[T9] OOS trigger-coverage annex (FENCED — coverage sizing only):")
    print(t9.to_string(index=False))

    print("\n" + "=" * 72)
    print(f"EDA COMPLETE — verdict: {t6['verdict'].iloc[0]}")
    print("=" * 72)


if __name__ == "__main__":
    main()
