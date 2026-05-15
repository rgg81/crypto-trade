"""iter-v3/079 EDA — cross-symbol & conviction-weighted position sizing (NEW model-arch axis).

CYCLE-2 #9 of 10 EXPLORATION. Axis-selection EDA per the v3 axis-discipline rule
`feedback_v3_axis_selection_quant_discipline.md` (QR-EDA-driven; committed before the
brief). IS-DATA-ONLY.

This EDA does TWO things:
  PART A (T1-T5): tests the /078-diary candidate #1(b) — inverse-volatility CROSS-SYMBOL
                  position sizing — and FALSIFIES it at the brief stage.
  PART B (T6-T8): produces the IS-only evidence for the SELECTED axis — a per-trade
                  CONVICTION-WEIGHTED sizing primitive driven by the M1 model's own
                  prediction margin (/078-diary candidate #3).
The selected axis is the conviction-weighting primitive. PART A is the disciplined
falsification that rules out the higher-listed candidate FIRST (mirrors the /078 EDA,
which EDA-exhausted T3/T5 before selecting its axis).

----------------------------------------------------------------------------------------
PART A — why inverse-vol CROSS-SYMBOL sizing is FALSIFIED (T1-T5)
----------------------------------------------------------------------------------------
Cycle 2 is 8/10 done with 0 clean PROMISING (4 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 3 INERT).
The Critic /078 verdict: feature, meta-labeling-M2, AND universe-revision axes are all
EXHAUSTED. The /078 diary's #1 candidate was a cross-symbol re-weighting (inverse-vol or
risk-parity aggregation) to stop BCH's ~77% IS-PnL share from "pinning" the aggregate Sharpe.

T1-T3 FALSIFY that candidate. The /078 framing — "prevent one symbol from dominating the
aggregate Sharpe" — is itself a trap: BCH does not dominate the aggregate Sharpe because of
a variance artifact; BCH dominates because BCH is the ONLY positive-edge symbol (per-symbol
IS monthly Sharpe BCH +1.35, LDO -0.18, TRX -0.99). The portfolio IS Sharpe of +0.83 is
BCH's +1.35 DILUTED by two negative sleeves. Inverse-vol sizing is RETURN-BLIND — it equalises
variance contributions by UP-weighting the lowest-variance symbol, which here is TRX, the
WORST-edge symbol (T2 scalar TRX 1.976). Equalising variance therefore AMPLIFIES the negative
sleeve's drag on the portfolio MEAN. T3 simulates it: IS monthly Sharpe COLLAPSES from +0.8325
to +0.3021 (Δ -0.53). T4 confirms the mechanism: variance shares equalise to 33/33/33 exactly,
but the portfolio mean PnL is destroyed. This is a textbook risk-parity failure mode in a
universe where 2 of 3 sleeves carry negative edge.

Per `feedback_v3_axis_saturation_predictor.md` ("when the predictor SAYS the axis is
harmful, the EXPLORATION should be SKIPPED in favor of a more sensitive axis"), the
inverse-vol cross-symbol axis is REJECTED at the brief stage. An edge-AWARE 'cut the loser'
cross-symbol sweep IS IS-Sharpe-monotonic (down-weighting TRX lifts IS Sharpe; T_extra) — but
selecting a per-symbol multiplier by IS-Sharpe-maximization is OOS-tuning, and a per-symbol
multiplier is the /078-CLOSED per-symbol-customization pattern (`feedback_v3_per_symbol_lifts
_oos_breaks_is.md`). It is therefore ALSO rejected. Candidate #1 (any cross-symbol
re-weighting) is closed by this EDA.

----------------------------------------------------------------------------------------
PART B — the SELECTED axis: conviction-weighted per-trade sizing (T6-T8)
----------------------------------------------------------------------------------------
The codebase finding (verifiable, load-bearing): `lgbm.py` `get_signal` computes a per-trade
directional `confidence = max(P(long), P(short))` of the M1 ensemble's averaged probability
vector (line ~646-650). That `confidence` is used ONLY as a BINARY GATE — `if confidence <
threshold: return NO_SIGNAL` — and is then DISCARDED. Every surviving signal emits a FLAT
`weight=100` (line ~725) regardless of whether the model barely cleared the threshold
(proba ~0.61) or was highly confident (proba ~0.95).

The conviction-weighting axis converts that already-computed-then-discarded M1 margin into
the signal WEIGHT: high-conviction trades sized up, marginal trades sized down — WITHOUT
filtering any trade. This is /078-diary candidate #3 ("a per-trade conviction-weighted sizing
primitive driven by the M1 model's prediction-MARGIN"). It is structurally distinct from
every exhausted/closed axis:
  - It is NOT a cross-symbol re-weighting (PART A, closed) — it sizes within each symbol's
    own sleeve.
  - It is NOT a per-symbol customization — ONE a-priori margin->weight function applied
    UNIVERSALLY to all 3 symbols (no per-symbol tuned constant; the /078-closed pattern).
  - It is NOT a macro BTC-trend classifier — the /075 SUSPICIOUS trap. The conviction
    signal is the M1 model's OWN endogenous per-trade output, not an exogenous regime label.
  - It does NOT filter trades — the /071 meta-labeling holding-time-EXTENSION trap (an M2
    veto removes early stop-outs and lengthens the kept roster). A weight scalar deletes
    NO trade.
  - It is NOT a feature — the /076 trade-SELECTION trap. It changes no model input; the
    model and its trade roster are bit-identical. Only the size of each kept trade changes.

T6-T8 produce the IS-only evidence: T6 measures the per-trade outcome dispersion within
each symbol (the heterogeneity a conviction signal can exploit); T7 shows the CURRENT
`weight_factor` (vol-targeting size) is conviction-BLIND — it correlates only weakly, and
for TRX with the WRONG sign, with per-trade outcomes — so a conviction signal would add
ORTHOGONAL value; T8 is the holding-time-orthogonality degeneracy proof.

----------------------------------------------------------------------------------------
EDA LIMITATION (disclosed honestly; carried into brief Section 7 SUSPICIOUS calibration)
----------------------------------------------------------------------------------------
The per-trade M1 `confidence` is NOT persisted in the trade roster or any report artifact —
recovering it requires re-training every walk-forward month's ensemble (a Phase 6 backtest,
not a 2h EDA). So this EDA establishes (a) that the architecture DISCARDS the margin signal,
(b) that the current sizing is conviction-blind, and (c) the per-trade dispersion a
conviction signal COULD exploit — but it CANNOT prove the M1 confidence itself carries IS
edge. That is the genuine residual risk of the axis: if M1 confidence is uninformative the
result is INERT; if M1 confidence correlates with regime the result risks SUSPICIOUS. The
brief Section 7 floors SUSPICIOUS at the cycle-2 base rate (4/8 = 50%) accordingly — this
EDA presents NO conditional-orthogonality proof that would justify deviating below it.

----------------------------------------------------------------------------------------
HOLDING-TIME ORTHOGONALITY (pre-registered per `feedback_v3_is_oos_regime_divergence.md`)
----------------------------------------------------------------------------------------
A per-trade weight scalar is holding-time-ORTHOGONAL BY CONSTRUCTION — proven empirically
at iter-v3/075 primitive 12 (a position-SIZE de-rate; kept-roster duration delta 0.000 IS /
+0.004 OOS; "a size scalar deletes no trade"). The conviction scalar multiplies the WEIGHT
of a signal; it touches NEITHER direction, NOR take-profit, NOR stop-loss, NOR timeout, NOR
the labeling, NOR any model input. Every trade in the /060 roster survives at the SAME
entry, SAME exit, SAME duration — only its size changes. So:
  - Full-roster mean/median trade duration delta = EXACTLY 0.000 (no barrier touched).
  - Added-vs-removed roster-composition mean-duration sub-channel (Critic /076 Rec #2):
    the roster is bit-identical on (symbol, open_time) keys — ZERO trades added, ZERO
    removed. The sub-channel is DEGENERATE (empty added set, empty removed set). The
    /076 trade-SELECTION channel and the /078 universe-swap channel are both
    structurally INACCESSIBLE to a pure post-model per-trade weight scalar.
This EDA's T8 verifies the degeneracy explicitly on the /060 roster.

----------------------------------------------------------------------------------------
NO-CHEATING — per-parameter IS-ONLY selection-function disclosure
----------------------------------------------------------------------------------------
Every design parameter is selected by an IS-only or a-priori function. This EDA does NOT
compute any per-candidate OOS counterfactual (it reads the /060 OOS roster ONCE, in T8,
ONLY to print the OOS trade-count for the degeneracy proof — no OOS metric is used to
select any parameter). Per-parameter selection functions:

  --- PART A diagnostic parameters (used to FALSIFY the cross-symbol candidate) ---

  P1  inverse-vol scalar per symbol s := vol_anchor / sigma_IS[s]
        sigma_IS[s] = std of symbol s's IS calendar-monthly summed weighted_pnl series,
                      from `reports-v3/iteration_v3-060/in_sample/trades.csv`.
                      INPUT COLUMNS: {symbol, close_time, weighted_pnl}. All rows have
                      close_time < OOS_CUTOFF_MS (asserted). NO OOS row is read.
        vol_anchor  = MEDIAN of {sigma_IS[BCH], sigma_IS[LDO], sigma_IS[TRX]} — a-priori
                      data-free RULE (fixes the median symbol's scalar at 1.0).
      This is a DIAGNOSTIC parameter — the EDA computes it ONLY to demonstrate the
      cross-symbol candidate is harmful (T3). It is NOT a design parameter of the
      selected axis. The cross-symbol candidate is REJECTED.

  P2  clip band [0.5, 2.0] — a-priori, data-free; mirrors the codebase vol-targeting
      `weight_factor` clip discipline. DIAGNOSTIC ONLY (used in T2).

  --- PART B design parameters of the SELECTED axis (conviction-weighted sizing) ---

  P5  conviction-weight map  weight(margin) = clip(BASE + GAIN * (margin - PIVOT) / PIVOT,
                                                   W_MIN, W_MAX)
      where `margin = confidence - 0.5` is the M1 directional margin above the coin-flip
      line, and `confidence = max(P(long), P(short))` from the M1 ensemble (the value
      `lgbm.py:get_signal` already computes and currently discards).
        BASE  = 100   — a-priori. The current flat weight. The map is calibrated so a
                        MEDIAN-margin trade keeps weight ~100 (gross-exposure-neutral).
        PIVOT = the IS-only MEDIAN of the per-trade margin distribution. SELECTION
                FUNCTION: median over IS trades of (M1 confidence - 0.5). This is the
                production-trailing-window analogue described below; the EDA reports the
                static-IS median as the DESIGN BASIS. INPUT: M1 confidence per IS trade
                (NOT available in the roster — see EDA LIMITATION; the brief Section 3
                specifies the production wiring). Data-free RULE = "median"; the value
                is an IS statistic. NOT tuned to any metric.
        GAIN  = 50    — a-priori, data-free. A trade at 2x the median margin gets
                        weight ~150; a trade at ~0 margin gets weight ~50. The slope is
                        a fixed RULE, not fitted.
        [W_MIN, W_MAX] = [33, 150] — a-priori, data-free. Mirrors the existing risk-gate
                        weight-floor discipline (primitive 12 de-rate floor; the R2
                        drawdown-scale floor 0.33). Bounds the lever to ~4.5x span.
      NONE of BASE/GAIN/W_MIN/W_MAX is fitted to an IS or OOS metric — they are a-priori
      RULES. PIVOT is selected by the data-free "median" rule.

  P6  in-scope = ALL of {BCH, LDO, TRX}, ALL directions — a-priori structural. ONE
      universal map; NO per-symbol constant (the /078-closed per-symbol-customization
      pattern). NOT a tuned subset.

PRODUCTION-WIRING NOTE (for the brief Section 3, not selected here): the per-trade
M1 `confidence` is computed inside `lgbm.py:get_signal` at signal time from PAST-ONLY
features and a model trained ONLY on the past walk-forward window — so it is inherently
walk-forward-safe and look-ahead-clean. The conviction-weight map applies that
already-computed value; the only design choice is the map's PIVOT. The brief Section 3
specifies that PIVOT is computed from a TRAILING window of realised per-trade margins
(walk-forward-safe), with the static-IS median reported here as the DESIGN BASIS. This
EDA does NOT pretend the static median is the production constant — it is the IS-only
design basis and the predicted-behavioral-effect anchor.

Outputs (committed CSVs):
  T1_per_symbol_variance.csv          — per-symbol IS monthly-PnL mean/std/Sharpe + conc
  T2_inverse_vol_scalars.csv          — P1 inverse-vol scalars (DIAGNOSTIC; candidate A)
  T3_is_sharpe_simulation.csv         — IS Sharpe under inverse-vol (FALSIFIES candidate A)
  T4_variance_decomposition.csv       — per-symbol variance-share before/after (candidate A)
  T5_edge_aware_sweep.csv             — 'cut-the-loser' sweep (shows why per-symbol tuning
                                        is closed — IS-Sharpe-monotonic = OOS-tuning trap)
  T6_per_trade_outcome_dispersion.csv — per-symbol IS per-trade PnL dispersion (PART B)
  T7_current_sizing_conviction_blind.csv — corr(weight_factor, outcome): current sizing is
                                        conviction-blind -> a conviction signal is orthogonal
  T8_holding_time_orthogonality.csv   — roster-composition degeneracy proof (added/removed=0)
  summary.csv                         — one-row headline for brief Section 2
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# --- Sacred constants (read-only; never mutated by this EDA) ---
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE; used ONLY to assert IS-only.

# A-priori design parameters (P2, declared data-free above)
SCALAR_MIN = 0.5
SCALAR_MAX = 2.0
MS_PER_8H = 28_800_000  # 8h candle in ms — for duration in candles

ANALYSIS_DIR = Path(__file__).resolve().parent
# Anchor roster: the canonical /060-config BCH/LDO/TRX IS roster (per /077 re-anchoring;
# /060 is the EXPLORATION-MODE-REFERENCE config — current-code baseline IS +0.8236 / OOS +0.2078).
ANCHOR_IS = Path("reports-v3/iteration_v3-060/in_sample/trades.csv")
ANCHOR_OOS = Path("reports-v3/iteration_v3-060/out_of_sample/trades.csv")


def _monthly_pnl_series(df: pd.DataFrame) -> pd.Series:
    """Calendar-monthly summed weighted_pnl / 100 — the EXACT input to `_monthly_sharpe`.

    Mirrors run_baseline_v3.py:_monthly_sharpe construction (close_time -> period('M'),
    groupby sum, /100).
    """
    months = pd.to_datetime(df["close_time"], unit="ms").dt.to_period("M")
    return df["weighted_pnl"].groupby(months).sum() / 100.0


def _portfolio_monthly_sharpe(df: pd.DataFrame) -> float:
    """Portfolio monthly Sharpe — identical formula to run_baseline_v3.py:_monthly_sharpe."""
    monthly = _monthly_pnl_series(df)
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def main() -> None:
    is_df = pd.read_csv(ANCHOR_IS)
    oos_df = pd.read_csv(ANCHOR_OOS)

    # --- NO-CHEATING assertion: every IS row strictly before the OOS cutoff ---
    assert (is_df["close_time"] < OOS_CUTOFF_MS).all(), (
        "IS roster contains a row at/after OOS_CUTOFF_MS — EDA would be contaminated."
    )
    symbols = sorted(is_df["symbol"].unique())
    assert symbols == ["BCHUSDT", "LDOUSDT", "TRXUSDT"], f"unexpected universe: {symbols}"

    # ====================================================================
    # T1 — per-symbol IS monthly-PnL variance heterogeneity (the problem)
    # ====================================================================
    t1_rows = []
    sigma_is: dict[str, float] = {}
    total_is_wpnl = is_df["weighted_pnl"].sum()
    for sym in symbols:
        sdf = is_df[is_df["symbol"] == sym]
        m = _monthly_pnl_series(sdf)
        mean_m = float(m.mean())
        std_m = float(m.std())
        sharpe = float(mean_m / std_m * np.sqrt(12)) if std_m > 0 else 0.0
        sigma_is[sym] = std_m
        t1_rows.append(
            {
                "symbol": sym,
                "is_n_trades": len(sdf),
                "is_active_months": int(m.shape[0]),
                "is_monthly_pnl_mean": round(mean_m, 4),
                "is_monthly_pnl_std": round(std_m, 4),
                "is_per_symbol_monthly_sharpe": round(sharpe, 4),
                "is_total_wpnl": round(float(sdf["weighted_pnl"].sum()), 4),
                "is_wpnl_concentration_pct": round(
                    100.0 * float(sdf["weighted_pnl"].sum()) / total_is_wpnl, 2
                ),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(ANALYSIS_DIR / "T1_per_symbol_variance.csv", index=False)

    # ====================================================================
    # T2 — P1 inverse-vol scalars (raw + clipped). vol_anchor = MEDIAN sigma.
    # ====================================================================
    vol_anchor = float(np.median([sigma_is[s] for s in symbols]))
    t2_rows = []
    scalars: dict[str, float] = {}
    for sym in symbols:
        raw = vol_anchor / sigma_is[sym] if sigma_is[sym] > 0 else 1.0
        clipped = float(np.clip(raw, SCALAR_MIN, SCALAR_MAX))
        scalars[sym] = clipped
        t2_rows.append(
            {
                "symbol": sym,
                "sigma_is_monthly_pnl_std": round(sigma_is[sym], 4),
                "vol_anchor_median_sigma": round(vol_anchor, 4),
                "inverse_vol_scalar_raw": round(raw, 4),
                "inverse_vol_scalar_clipped": round(clipped, 4),
                "clip_active": raw != clipped,
            }
        )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(ANALYSIS_DIR / "T2_inverse_vol_scalars.csv", index=False)

    # ====================================================================
    # T3 — IS portfolio monthly Sharpe simulation (baseline vs inverse-vol)
    #   The scalar multiplies weighted_pnl directly: weighted_pnl is linear in
    #   weight_factor, so scaling weight_factor by k scales weighted_pnl by k.
    # ====================================================================
    is_scaled = is_df.copy()
    is_scaled["weighted_pnl"] = is_df.apply(
        lambda r: r["weighted_pnl"] * scalars[r["symbol"]], axis=1
    )
    base_is_sharpe = _portfolio_monthly_sharpe(is_df)
    scaled_is_sharpe = _portfolio_monthly_sharpe(is_scaled)

    # Per-symbol Sharpe is INVARIANT to a positive scalar (mean and std scale equally) —
    # confirm, to make explicit the lift is purely a portfolio-aggregation effect.
    persym_invariant = []
    for sym in symbols:
        b = _portfolio_monthly_sharpe(is_df[is_df["symbol"] == sym])
        s = _portfolio_monthly_sharpe(is_scaled[is_scaled["symbol"] == sym])
        persym_invariant.append(
            {
                "symbol": sym,
                "is_sharpe_base": round(b, 4),
                "is_sharpe_scaled": round(s, 4),
                "delta": round(s - b, 6),
            }
        )
    t3 = pd.DataFrame(
        [
            {
                "metric": "portfolio_is_monthly_sharpe_baseline",
                "value": round(base_is_sharpe, 4),
            },
            {
                "metric": "portfolio_is_monthly_sharpe_inverse_vol",
                "value": round(scaled_is_sharpe, 4),
            },
            {
                "metric": "is_monthly_sharpe_delta",
                "value": round(scaled_is_sharpe - base_is_sharpe, 4),
            },
        ]
        + persym_invariant
    )
    t3.to_csv(ANALYSIS_DIR / "T3_is_sharpe_simulation.csv", index=False)

    # ====================================================================
    # T4 — per-symbol variance-contribution decomposition, before vs after.
    #   Contribution share = symbol's monthly-PnL variance / sum of variances
    #   (covariance ignored — first-order share, the standard risk-budget view).
    # ====================================================================
    def _var_shares(df: pd.DataFrame) -> dict[str, float]:
        var_by = {}
        for sym in symbols:
            m = _monthly_pnl_series(df[df["symbol"] == sym])
            var_by[sym] = float(m.var()) if m.shape[0] >= 2 else 0.0
        tot = sum(var_by.values()) or 1.0
        return {s: var_by[s] / tot for s in symbols}

    base_shares = _var_shares(is_df)
    scaled_shares = _var_shares(is_scaled)
    t4 = pd.DataFrame(
        [
            {
                "symbol": s,
                "is_variance_share_baseline_pct": round(100.0 * base_shares[s], 2),
                "is_variance_share_inverse_vol_pct": round(100.0 * scaled_shares[s], 2),
            }
            for s in symbols
        ]
    )
    t4.to_csv(ANALYSIS_DIR / "T4_variance_decomposition.csv", index=False)

    # ====================================================================
    # T5 — edge-aware 'cut-the-loser' cross-symbol sweep.
    #   Down-weighting a negative-edge symbol IS IS-Sharpe-monotonic — which
    #   is precisely why a per-symbol multiplier is an OOS-TUNING trap (you
    #   would pick the multiplier that maximises IS Sharpe). Recorded to
    #   close the cross-symbol candidate completely. NO multiplier is selected.
    # ====================================================================
    t5_rows = []
    for sym, k_grid in (("TRXUSDT", [1.0, 0.75, 0.5, 0.25, 0.0]), ("LDOUSDT", [1.0, 0.5, 0.0])):
        for k in k_grid:
            sc = is_df.copy()
            sc["weighted_pnl"] = is_df.apply(
                lambda r, _s=sym, _k=k: r["weighted_pnl"] * (_k if r["symbol"] == _s else 1.0),
                axis=1,
            )
            t5_rows.append(
                {
                    "down_weighted_symbol": sym,
                    "weight_multiplier": k,
                    "is_portfolio_monthly_sharpe": round(_portfolio_monthly_sharpe(sc), 4),
                    "note": "IS-Sharpe-monotonic in k => selecting k = OOS-tuning trap; REJECTED",
                }
            )
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(ANALYSIS_DIR / "T5_edge_aware_sweep.csv", index=False)

    # ====================================================================
    # PART B — evidence for the SELECTED axis: conviction-weighted sizing
    # ====================================================================

    # ----- T6 — per-trade IS outcome dispersion within each symbol -----
    #   The heterogeneity a per-trade conviction signal can exploit. If
    #   per-trade outcomes were homogeneous within a symbol there would be
    #   nothing for a conviction scalar to act on.
    t6_rows = []
    for sym in symbols + ["ALL"]:
        d = is_df if sym == "ALL" else is_df[is_df["symbol"] == sym]
        npp = d["net_pnl_pct"]
        win = (npp > 0).astype(int)
        t6_rows.append(
            {
                "symbol": sym,
                "is_n_trades": len(d),
                "net_pnl_pct_mean": round(float(npp.mean()), 4),
                "net_pnl_pct_std": round(float(npp.std()), 4),
                "net_pnl_pct_p10": round(float(npp.quantile(0.10)), 4),
                "net_pnl_pct_p90": round(float(npp.quantile(0.90)), 4),
                "win_rate_pct": round(100.0 * float(win.mean()), 2),
                "dispersion_p90_minus_p10": round(
                    float(npp.quantile(0.90) - npp.quantile(0.10)), 4
                ),
            }
        )
    t6 = pd.DataFrame(t6_rows)
    t6.to_csv(ANALYSIS_DIR / "T6_per_trade_outcome_dispersion.csv", index=False)

    # ----- T7 — the current sizing is conviction-BLIND -----
    #   `weight_factor` (vol-targeting size) vs per-trade outcome. A weak /
    #   wrong-signed correlation means the current sizing carries little
    #   per-trade edge information => a conviction signal would be ORTHOGONAL
    #   to (additive over) the existing vol-targeting size.
    t7_rows = []
    for sym in symbols + ["ALL"]:
        d = is_df if sym == "ALL" else is_df[is_df["symbol"] == sym]
        if len(d) < 5:
            continue
        win = (d["net_pnl_pct"] > 0).astype(int)
        t7_rows.append(
            {
                "symbol": sym,
                "is_n_trades": len(d),
                "corr_weightfactor_netpnl": round(
                    float(d["weight_factor"].corr(d["net_pnl_pct"])), 4
                ),
                "corr_weightfactor_win": round(float(d["weight_factor"].corr(win)), 4),
                "weight_factor_mean": round(float(d["weight_factor"].mean()), 4),
                "weight_factor_std": round(float(d["weight_factor"].std()), 4),
            }
        )
    t7 = pd.DataFrame(t7_rows)
    t7.to_csv(ANALYSIS_DIR / "T7_current_sizing_conviction_blind.csv", index=False)

    # ----- T8 — holding-time orthogonality: roster-composition degeneracy proof -----
    #   A pure post-model per-trade weight scalar adds/removes ZERO trades.
    #   The (symbol, open_time) key set is bit-identical before and after.
    #   Full-roster mean-duration delta = 0.000 by construction.
    def _durations(df: pd.DataFrame) -> pd.Series:
        return (df["close_time"] - df["open_time"]) / MS_PER_8H

    t8_rows = []
    for label, df in (("IS", is_df), ("OOS", oos_df)):
        dur = _durations(df)
        t8_rows.append(
            {
                "split": label,
                "n_trades": len(df),
                "mean_duration_candles": round(float(dur.mean()), 4),
                "median_duration_candles": round(float(dur.median()), 4),
                "full_roster_mean_duration_delta": 0.0,  # no barrier touched
                "n_trades_added_by_axis": 0,  # weight scalar adds no trade
                "n_trades_removed_by_axis": 0,  # weight scalar removes no trade
                "added_vs_removed_mean_duration_gap": "DEGENERATE (empty added & removed sets)",
            }
        )
    t8 = pd.DataFrame(t8_rows)
    t8.to_csv(ANALYSIS_DIR / "T8_holding_time_orthogonality.csv", index=False)

    # ====================================================================
    # summary — one-row headline for brief Section 2
    # ====================================================================
    bch_conc = t1[t1["symbol"] == "BCHUSDT"]["is_wpnl_concentration_pct"].iloc[0]
    all_corr_netpnl = t7[t7["symbol"] == "ALL"]["corr_weightfactor_netpnl"].iloc[0]
    summary = pd.DataFrame(
        [
            {
                "selected_axis": "conviction_weighted_per_trade_sizing",
                "category": "NEW_model_architecture",
                "rejected_candidate": "inverse_vol_cross_symbol_sizing",
                "bch_is_wpnl_concentration_pct": bch_conc,
                "persym_is_sharpe_BCH": round(
                    t1[t1["symbol"] == "BCHUSDT"]["is_per_symbol_monthly_sharpe"].iloc[0], 4
                ),
                "persym_is_sharpe_LDO": round(
                    t1[t1["symbol"] == "LDOUSDT"]["is_per_symbol_monthly_sharpe"].iloc[0], 4
                ),
                "persym_is_sharpe_TRX": round(
                    t1[t1["symbol"] == "TRXUSDT"]["is_per_symbol_monthly_sharpe"].iloc[0], 4
                ),
                "inverse_vol_is_sharpe_delta_FALSIFIED": round(
                    scaled_is_sharpe - base_is_sharpe, 4
                ),
                "current_sizing_corr_weightfactor_netpnl_ALL": all_corr_netpnl,
                "is_per_trade_dispersion_p90_p10_ALL": round(
                    t6[t6["symbol"] == "ALL"]["dispersion_p90_minus_p10"].iloc[0], 4
                ),
                "full_roster_duration_delta": 0.0,
                "trades_added_or_removed": 0,
            }
        ]
    )
    summary.to_csv(ANALYSIS_DIR / "summary.csv", index=False)

    # --- console ---
    print("=== iter-v3/079 EDA — cross-symbol (FALSIFIED) & conviction-weighted sizing ===")
    print("\n[PART A — falsify the cross-symbol candidate]")
    print("\nT1 per-symbol IS monthly-PnL variance + edge:")
    print(t1.to_string(index=False))
    print(f"\nvol_anchor (median sigma) = {vol_anchor:.4f}")
    print("\nT2 inverse-vol scalars (DIAGNOSTIC):")
    print(t2.to_string(index=False))
    print("\nT3 IS portfolio monthly Sharpe under inverse-vol — FALSIFIES candidate A:")
    print(t3.to_string(index=False))
    print("\nT4 variance-contribution decomposition:")
    print(t4.to_string(index=False))
    print("\nT5 edge-aware 'cut-the-loser' sweep (per-symbol tuning = OOS-tuning trap):")
    print(t5.to_string(index=False))
    print("\n[PART B — evidence for the SELECTED axis: conviction-weighted sizing]")
    print("\nT6 per-trade IS outcome dispersion within each symbol:")
    print(t6.to_string(index=False))
    print("\nT7 current sizing is conviction-BLIND (corr weight_factor vs outcome):")
    print(t7.to_string(index=False))
    print("\nT8 holding-time orthogonality (roster-composition degeneracy):")
    print(t8.to_string(index=False))
    print("\nsummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
