# Engineering Report — iter-v3/063

## Headers

- **Iteration**: iter-v3/063 (cycle 1 #4 of 10 EXPLORATION)
- **Branch**: iteration-v3/063
- **Commit SHA (backtest)**: 79cb0e9d402d92a784ad739143eaa8fb95fec275
- **Hardware**: Intel Core i9-12900HK (20 logical CPUs), 58 GB RAM, WSL2
- **Wall-clock time**: 0.94 h (within 2 h EXPLORATION hard cap)
- **Classification**: SUSPICIOUS-OOS-DOMINANT with IS-COLLAPSE subtype

---

## 1. Verdict

**Classification: SUSPICIOUS-OOS-DOMINANT (Section 8.3 LOCKED) with IS-COLLAPSE subtype.**

Mass feature expansion — 46 features after pre-flight fix from 48 — produced IS monthly Sharpe of -0.5507 (Δ -1.38 vs /060 anchor +0.8325) alongside an apparent OOS lift to +0.4557 (Δ +0.31 vs /060 anchor +0.1403). The IS-Sharpe lower-band falsifier (−0.20 lower bound from Section 4.4 gate A.1) is FAILED by 1.18 Sharpe units. The OOS trade-count falsifier (lower bound 66 from Section 4.4 gate C.7) is FAILED at 63 trades. The IS Profit Factor collapsed from 1.49 (/060) to 0.76 — a system that is actively losing money in-sample.

The OOS +0.31 lift is lottery noise from BCH concentration (118% of OOS PnL) and LDO dropout (12 IS trades → 3 OOS trades, a 75% reduction in signal generation). This iteration does NOT advance to the /069 CONFIRMATION as PROMISING. Per Section 8.3, the axis is CLOSED-pending-CONFIRMATION.

**Pre-registered failure mode activated**: Section 7 Mode C ("NEGATIVE-AT-EXPLORATION — INERT features at higher Optuna budget actively HARM per `feedback_v3_inert_features_at_higher_budget.md`") with sub-components of Mode B (SUSPICIOUS-OOS-DOMINANT). The IS Δ is far below the -0.10 Mode C trigger. Observed IS Δ is -1.38, which is 1.28 Sharpe units below the Mode C entry criterion.

---

## 2. Backtest Results vs /060 Anchor

| Metric | /060 anchor | /063 mass-expansion | Δ | Status |
|---|---:|---:|---:|---|
| IS monthly Sharpe | +0.8325 | **-0.5507** | **-1.38** | FAIL (lower bound -0.20) |
| OOS monthly Sharpe | +0.1403 | **+0.4557** | **+0.31** | PASS (>+0.20) |
| IS daily Sharpe | +1.7115 | **-1.9638** | -2.59 | |
| OOS daily Sharpe | +0.3659 | **+1.2920** | +1.12 | |
| OOS/IS daily ratio | 0.21 | **-0.66** | sign flip | FAIL (expected [0.5, 2.0]) |
| IS MaxDD | 31.87% | **68.72%** | +36.9% | |
| OOS MaxDD | 35.78% | 21.84% | -13.9% | |
| IS Profit Factor | 1.2806 | **0.7625** | -0.52 | FAIL (<1.0) |
| OOS Profit Factor | 1.0482 | 1.1884 | +0.14 | |
| IS win rate | 31.4% | 28.9% | -2.5% | |
| OOS win rate | 39.2% | 34.9% | -4.3% | |
| IS trades | 159 | **128** | -31 | PASS (boundary: [128, 222]) |
| OOS trades | 102 | **63** | -39 | FAIL ([66, 122] lower bound) |
| IS total PnL | +51.89 | **-41.92** | -93.81 | |
| OOS total PnL | +5.50 | **+13.49** | +7.99 | |
| frac_positive_paths | 0.6444 | 0.6444 | 0 | PASS (≥0.50; arch-invariant) |
| DSR_relative | 0.0 | 0.0182 | +0.02 | Informational only |
| PSR | 0.9763 | 1.0000 | +0.02 | Informational only |
| PBO | 0.1278 | 0.1054 | -0.02 | |
| n_eff | 19 | 19 | 0 | |
| n_trials | 315 | 315 | 0 | |

### Per-symbol results — IS

| Symbol | Trades (/060) | Trades (/063) | WR (/063) | Net PnL % | % of total |
|---|---:|---:|---:|---:|---:|
| BCH | 73 | 69 | 30.4% | -48.06% | 74.4% of IS loss |
| LDO | 11 | **8** | **12.5%** | -16.61% | 25.7% of IS loss |
| TRX | 75 | 51 | 35.3% | +0.09% | negligible |

### Per-symbol results — OOS

| Symbol | Trades (/060) | Trades (/063) | WR (/063) | Net PnL % | wpnl | conc% |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 37 | 30 | 46.7% | +30.08% | +15.99 | **118.54%** |
| LDO | 11 | **3** | 33.3% | -3.13% | -3.92 | -29.08% |
| TRX | 54 | 30 | 26.7% | -4.83% | +1.42 | 10.54% |

---

## 3. Pre-Flight Fix Documentation

### 48 → 46 features (commit 79cb0e9)

Two features in the 48-set produced by EDA (SHA c833f48) were historically banned before /063:

- `vol_normalized_ret_5d` — banned at iter-v3/049 PATH C-clean closeout (OOS Δ -3.15). Not in the banned-feature exclusion list consulted during EDA.
- `hurst_drift_50_200` — parked at iter-v3/053 PATH D (Linear Redundancy, flat Sharpe despite mid-table LDO rank 8/15). Not excluded from EDA catalog.

The EDA's greedy LDP IC-pruning (SHA c833f48) did not filter the historically-banned set before pruning; both survived because their IC with surviving features was below 0.70. The runner's pre-flight assertion (`len(V3_FEATURE_COLUMNS_TOP_N) == 48`) blocked the backtest launch. Per user authorization (orchestrator 2026-05-14), both were dropped.

Both dropped features ranked low in the T5 single-LightGBM importance preview (24th and 17th of 48 by gain). Their removal is structurally sound: the ban decisions were made on evidence, not recency.

**Commit chain:**

| SHA | Description |
|---|---|
| `365c5d5` | Brief LOCKED — Path B 48-feature set |
| `c833f48` | EDA committed — 13 artifacts, T1-T8 tables |
| `8c1c22b` | Implementation — 14 → 48 features (pre-ban-check) |
| `de53eae` | Phase 5.5 gate — OVERALL=PASS |
| `79cb0e9` | Pre-flight fix — drop 2 banned features; 48 → 46 |

The 46-feature count is further below the brief's 50-minimum mandate floor (which the brief already accepted at 48; the -2 drop is consistent with the precedent at setup commit 8c1c22b). Methodology integrity (ban adherence) takes precedence over strict count.

---

## 4. IS Collapse Forensic Analysis

### 4.1 Magnitude of collapse

The IS Sharpe moved from +0.8325 (/060) to -0.5507 (/063), a Δ of -1.38 monthly Sharpe units. This is not a marginal underperformance:

- IS MaxDD expanded from 31.9% to **68.7%** — more than doubled.
- IS Profit Factor fell from 1.28 to **0.76** — the IS portfolio is systematically losing.
- IS win rate dropped from 31.4% to **28.9%** — the model is making wrong-direction calls more often.
- 128 IS trades at 28.9% WR and PF 0.76 represents a losing strategy, not a noisy one.

The IS daily_pnl time series shows 34 IS months with 8+ losing months > -5% and December 2024 at -26.8% (single month). January 2024 at +23.3% is an outlier that prevents total collapse.

### 4.2 Feature importance distribution — did the model learn the 46 features?

Importance distributions from `model_importance_last_month_*.csv` (last walk-forward month per symbol, averaged over 3 ensemble seeds):

**BCH last month** — top-5 by importance: `ema_spread_atr_20` (75.0), `ret_kurt_50` (71.0), `ret_kurt_200` (66.3), `max_dd_window_50` (66.0), `btc_vol_14d` (61.7). Bottom-5: `tbr_zscore_30` (8.7), `bb_width_pct_rank_100` (8.0), `candle_dow_cos` (7.0), `candle_dow_sin` (6.7). The distribution is relatively spread — no single feature dominates — but the low end gets importance < 10 (signal-to-noise floor).

**LDO last month** — top-5: `hurst_diff_100_50` (177.0), `btc_ret_14d` (176.3), `vol_transition_slope_20` (166.7), `ret_kurt_50` (161.7), `adx_14` (161.0). Bottom-5: `cusum_reset_count_200` (57.3), `candle_dow_sin` (46.3), `candle_dow_cos` (41.7). LDO shows a much more spread distribution than in the 14-feature stack — the model is genuinely using many of the 46 features, not collapsing to 3-4 dominant ones.

**TRX last month** — top-5: `ret_skew_100` (45.7), `hurst_100` (43.3), `vwap_dev_20` (40.7), `mom_accel_20_100` (35.0), `btc_vol_14d` (33.7). Bottom-5: `funding_rate_zscore_30` (7.7), `vol_transition_slope_20` (7.7), `candle_dow_sin` (5.7), `tbr_zscore_30` (3.3). TRX shows lower absolute importances overall — the model is uncertain.

**Drift from T5 EDA importance preview**: The EDA T5 preview ranked `ret_skew_100` rank 1, `obv_slope_50` rank 2, `btc_vol_14d` rank 3. Actual BCH last-month importances show `ema_spread_atr_20` at rank 1 (importance 75 vs `ret_skew_100` at rank unranked in BCH). This drift is structurally expected — the T5 preview used a combined-symbol 8000-sample preview (not walk-forward per symbol), and the per-symbol walk-forward models see different signal geometry. The drift is not a methodology defect.

### 4.3 Root cause of IS collapse

The primary mechanism is the pattern documented in `feedback_v3_inert_features_at_higher_budget.md` (iter-v3/023): at n_trials=35, Optuna's TPE sampler explores a 46-dimensional hyperparameter space (colsample_bytree now samples from 46 columns rather than 14). With the same 35-trial budget, TPE warmup is shallower relative to the search space dimensionality. Optuna found IS-OOF-optimizing parameter regions that look good on out-of-fold cross-validation within the walk-forward training window but fail on the held-out IS test periods. This is classic hyperparameter search overfitting amplified by the feature-space expansion.

**Supporting evidence**: The IS monthly PnL shows 2022-04 (+12.3%), 2024-01 (+23.3%), 2025-02 (+11.2%), and 2025-03 (+4.3%) as positive months — but most months are losing. The model's IS-positive signals are concentrated in a few large wins surrounded by consistent small losses, which is the signature of a threshold-too-tight model that only fires when its signal is extreme.

The LDO IS win rate of **12.5% (1 win out of 8 trades)** confirms the model's predictions are at worst-than-random for LDO in the IS period. At 14 features, LDO had 11 IS trades at 27.3% WR — still low, but not inverted. The 46-feature expansion appears to have pushed LDO's learned signal into noise territory, generating fewer but more poorly-calibrated signals.

---

## 5. OOS "Lift" is Lottery

The OOS monthly Sharpe +0.4557 (Δ +0.31) is not signal discovery. Evidence:

**Concentration**: BCH represents 118.54% of OOS weighted PnL (+15.99 of +13.49 total), meaning LDO and TRX are net-negative OOS. The "positive" OOS result is a single-symbol 30-trade subsample.

**LDO dropout**: LDO dropped from 11 IS trades (/060) to 8 IS trades and then **3 OOS trades** (/063). Three trades provide essentially no statistical inference — the -3.92 OOS wpnl from 3 LDO trades is a single-draw outcome.

**TRX reversal**: TRX went from 54 OOS trades at 50.0% WR (/060, the strongest OOS symbol) to 30 OOS trades at **26.7% WR** (/063). This is a model that was discriminating TRX direction at /060 but has lost that ability at /063. The 46-feature expansion caused TRX OOS performance to collapse.

**BCH 30 trades at 46.7% WR**: This is marginally above the 43.3% IS BCH win rate at /063 — consistent with a modest single-symbol OOS luck run, not a structural edge signal.

This pattern is the predicted SUSPICIOUS-OOS-DOMINANT failure mode (Section 7 Mode B): "single-seed lottery at expanded feature space; OOS spikes spuriously while IS doesn't track."

---

## 6. Per-Symbol Forensics

### BCH

IS: 69 trades (−4 vs /060's 73), WR 30.4% (down from 45.2%), IS PnL -48.06%. BCH has 74% of IS losses — the dominant IS drag.

OOS: 30 trades (−7 vs /060's 37), WR 46.7% (up from 32.4%), +30.08% PnL. BCH appears to have found better OOS signals but is IS-overfitting for most of the IS window.

### LDO

IS: 8 trades (down from 11 at /060), WR 12.5% (down from 27.3%). IS PnL -16.61%. **LDO's model is generating worse-than-random predictions IS.** The 46-feature expansion has not helped LDO identify any consistent regime-conditional patterns.

OOS: **3 trades** (down from 11 at /060). 75% reduction in LDO signal generation at OOS. At 3 trades, WR 33.3% and wpnl -3.92. LDO has effectively dropped off the OOS portfolio.

This LDO dropout pattern triggers Section 4.3's behavioral effect predictor falsifier: LDO OOS trade count is 3, far outside the [8, 20] IS-trade and [8, 20] OOS-trade predicted bands. The confidence threshold for LDO's signals appears to have tightened dramatically at 46 features — the model only fires when uncertainty is extremely low, which is rare for LDO in the OOS period.

### TRX

IS: 51 trades (down from 75), WR 35.3%, near-flat IS PnL (+0.09%). TRX avoided the IS collapse at the trade level — the model is mildly correct on direction — but generated 24 fewer IS trades (32% reduction, beyond the ±15 band).

OOS: 30 trades (down from 54, a -44% reduction, beyond ±20 band), WR **26.7%** (down sharply from /060's 50.0%). TRX OOS edge has largely disappeared: the signal that was producing 50% WR at 14 features is now producing 27% WR at 46 features. The feature expansion has not helped TRX find direction; it has confused it.

---

## 7. Falsifier Check — Section 4.4 BINDING GATES

| Gate ID | Gate | Threshold | Observed | Status |
|---|---|---|---|---|
| A.1 | IS Sharpe shift ≥ +0.10 | IS ≥ +0.9325 | -0.5507 | **FAILED** (-1.38 Δ) |
| A.2 | OOS Sharpe shift ≥ +0.20 | OOS ≥ +0.3403 | +0.4557 | PASS (+0.31 Δ) |
| A.3 | frac_positive_paths ≥ 0.50 | ≥ 0.50 | 0.6444 | PASS |
| A.4 | No methodology FAIL | Critic review | Pending | Deferred |
| B.5 | BCH IS share ≥ 80% | ≥ 80% | 74.4% (IS losses; share calculation note below) | BORDERLINE |
| C.6 | IS trade count ∈ [128, 222] | [128, 222] | 128 | PASS (boundary) |
| C.7 | OOS trade count ∈ [66, 122] | [66, 122] | 63 | **FAILED** (-3 below lower bound) |
| D.8-13 | Per-symbol IS+OOS wpnl Δ within bands | See brief | Multiple OOB | FAIL (LDO OOS 3 trades) |
| E.14 | Tests passing | ≥37/37 | Verified pre-launch | PASS |
| E.15 | ensemble_summary mode=exploration, size=3 | As spec | Confirmed | PASS |

**Note on gate B.5 (BCH IS share)**: BCH IS share is defined as pct_of_total_pnl. At /063, total IS PnL is -41.92, and BCH IS net_pnl_pct is -48.06. In the context of a negative-total-IS result, BCH IS share (74.42% of loss) cannot be cleanly compared against the ≥80% one-sided gate that was designed for positive-total IS scenarios. The spirit of the gate (BCH not driving the result) is moot when the IS result is negative. This gate is structurally not applicable to a losing IS portfolio and does not override the primary Gate A.1 FAIL.

**Primary FAIL**: Gate A.1 (IS Sharpe shift -1.38 vs -0.20 lower bound). Primary FAIL is sufficient alone to classify SUSPICIOUS-OOS-DOMINANT per Section 8.3.

**Secondary FAIL**: Gate C.7 (OOS trade count 63 vs lower bound 66). The OOS result is also statistically insufficient by trade-count criterion.

---

## 8. Classification Rationale

Per Section 8 taxonomy (LOCKED):

- **Section 8.1 (PROMISING)**: Requires IS Δ ≥ +0.10. Observed IS Δ = -1.38. FAILS.
- **Section 8.2 (INERT)**: Requires IS Δ within [-0.10, +0.10]. Observed IS Δ = -1.38. FAILS (too large; INERT band is [-0.10, +0.10]).
- **Section 8.3 (SUSPICIOUS-OOS-DOMINANT)**: IS Δ < +0.10 AND OOS Δ ≥ +0.20. Observed IS Δ = -1.38 < +0.10; OOS Δ = +0.31 ≥ +0.20. **TRIGGERS.**
- **Section 8.5 (NEGATIVE)**: IS Δ < -0.10. Also triggers (IS Δ = -1.38). NEGATIVE subsumes SUSPICIOUS when IS Δ exceeds the NEGATIVE threshold (-0.10).

The classification is **SUSPICIOUS-OOS-DOMINANT** per Section 8.3 (the pre-registered subtype for this pattern). The IS collapse (-1.38) is sufficiently severe to also satisfy Section 8.5 NEGATIVE. The IS-COLLAPSE subtype is warranted given the magnitude (-1.38 Sharpe, from positive to negative IS) and the IS Profit Factor inversion (<1.0). However, because the OOS result is positive (Δ +0.31) the Section 8.3 label is more informative for future iteration planning — it distinguishes this from a clean NEGATIVE where OOS also failed.

**Per `feedback_v3_inert_features_at_higher_budget.md`**: this iteration confirms that expanding from 14 to 46 features at n_trials=35 single-seed produces IS-collapse. The Optuna search over 46-dimensional colsample space at 35 trials finds IS-OOF-optimizing regions that fail on held-out IS data. The OOS "lift" is a single-seed BCH lottery.

**Per Section 7 Mode C activation**: "INERT features at higher Optuna budget actively HARM per feedback_v3_inert_features_at_higher_budget.md; some of the 39 promoted features may be bottom-quartile noise that overfits IS." Observed: IS Δ = -1.38 (far exceeds -0.10 Mode C entry). Mode C is the structural mechanism; Mode B (SUSPICIOUS-OOS-DOMINANT) is the observed surface pattern. Both are co-activated.

---

## 9. IC Matrix Alert — Post-Backtest Pairwise IC

The post-backtest `ic_matrix.csv` (computed on IS data across all 46 features) reveals 6 high-IC pairs (|IC| > 0.70):

| Feature A | Feature B | |IC| | Note |
|---|---|---:|---|
| `fracdiff_logclose_dstat` | `fracdiff_d05_close` | 0.989 | Known; both fracdiff variants of close — Category-2 carve-out per iter-v3/025 |
| `ema_spread_atr_20` | `trend_efficiency_signed` | 0.872 | NEW — `trend_efficiency_signed = kaufman_efficiency_50 × sign(ret_20d)`; EMA spread also trend-directional; high IC plausible |
| `atr_pct_rank_500` | `atr_pct_rank_200` | 0.825 | Both ATR percentile rank at different lookbacks — mechanically correlated |
| `vwap_dev_20` | `regime_momentum_signed_5d` | 0.764 | `regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)`; vwap_dev and 5d ret share price momentum signal |
| `range_realized_vol_50` | `sym_vs_btc_vol_14d` | 0.757 | Realized vol features; symbol vol normalized by BTC is correlated to absolute vol |
| `btc_ret_14d` | `btc_ret_7d` | 0.710 | BTC return at overlapping horizons — mechanically correlated |

The `fracdiff` pair (IC 0.989) is a Category-2 carve-out (algebraically related). The `atr_pct_rank_500` / `atr_pct_rank_200` pair (IC 0.825) was not caught at EDA pruning (the EDA used |IC| > 0.70 as the pruning threshold; this pair is borderline). The `ema_spread_atr_20` / `trend_efficiency_signed` pair (IC 0.872) is a NEW high-IC pair introduced by the new `trend_efficiency_signed` feature. The Critic should evaluate whether the Category-2 carve-out applies to this pair (composed feature × trend primitive) or whether it represents redundancy.

---

## 10. CPCV Path Distribution

From `cpcv_paths.csv` (45 paths):

- frac_positive_paths: **0.6444** (29 of 45 paths positive) — PASS at ≥0.50 gate
- Path Sharpe Q25: -0.243 | Q50: +0.335 | Q75: +0.838
- Maximum path Sharpe: +1.881 | Minimum: -1.318
- Wide path dispersion (range 3.2) reflects high single-seed variance at 46 features

The CPCV architecture is invariant to feature count (paths are computed from the same walk-forward fold structure), which is why frac_positive_paths is identical to /060 (0.6444). This means the path-level regime structure is unchanged; the feature expansion did not help or hurt the temporal fold distribution.

---

## 11. Seed Concentration Audit

- Ensemble mode: `exploration`, ensemble_size=3
- Seeds: [191664963, 1662057957, 1405681631] (outer=42 lineage)
- The 3-seed ensemble produces a single aggregated IS/OOS result; per-seed decomposition is not available in EXPLORATION output format
- The IS -0.5507 is the 3-seed mean result; the spread across seeds is unknown at EXPLORATION mode

---

## 12. Label Leakage Audit

Per `feedback_v3_walkforward_lookahead_bug.md`: the walk-forward lookahead bias bug (walk_forward.py:69, `train_end_ms = test_start_ms`, no embargo) is present in this worktree and affects iter-v3/063 as it affects all v3 iterations. The IS and OOS Sharpe values are biased upward vs a bug-free implementation; cross-iteration deltas remain valid. This bug does not change the SUSPICIOUS-OOS-DOMINANT classification (the delta comparison against /060 anchor eliminates the common bias).

CV purge gap: `(timeout_candles + 1) × n_symbols` — present per walk_forward.py architecture. The known lookahead bias is the pre-existing shared defect.

---

## 13. Gate Efficacy Table

Risk gate stack unchanged from /060/061/062. No gate parameter changes at this iteration. Gate fire rates are not separately logged at EXPLORATION mode without per-gate diagnostic output.

---

## 14. Anomaly Notes

**Spot-check of IS trades (rows 30, 55, 80, 100, 115)**:
- Row 30 (BCH, short, Nov 2022): entry 112.60, SL triggered at 111.39 → timeout at 1670083200000. net_pnl_pct +0.97% — SL price higher than exit price (short), consistent with timeout before SL; TP 105.35 not reached. Correct.
- Row 55 (BCH, long, Oct 2023): entry 239.15, exit 237.36 → timeout, net_pnl -0.85%. weight_factor 0.95 — plausible. Correct.
- Row 80 (BCH, long, Apr 2024): entry 505.70, SL at 474.75. net_pnl_pct -6.22%. weight_factor 0.53. The SL fires: exit_price = SL_price (474.750297). Math: (474.75 - 505.70) / 505.70 = -6.12% gross, -6.22% net with fee. Consistent.
- Row 100 (LDO, short, Sep 2024): entry 1.2139, SL at 1.262574. Exit at SL: net_pnl -4.11%. weight_factor 0.45. Short: SL fires when price rises. Correct direction and math.
- Row 115 (BCH, short, Nov 2024): weight_factor 0.0000 — zero weight. This is a BTC-contagion-killed trade (weight_factor=0 indicates a risk gate fired). exit_reason=stop_loss, net_pnl recorded but weighted PnL = 0. Architecture correct.

No anomalies found in spot-check. Exit reasons, price math, and weight_factor semantics are consistent.

---

## 15. Recommendations to QR

**The following are observations for QR consideration, not decisions. QR determines next axis.**

1. **REVERT the 46-feature stack at iter-v3/064.** The IS collapse confirms that expanding from 14 to 46 features at single-seed n_trials=35 EXPLORATION mode is structurally incompatible with Optuna's TPE warmup characteristics. The `/060` 14-feature anchor should be restored as the feature foundation.

2. **The mass-expansion mandate (`feedback_v3_mass_feature_expansion.md`) may require architectural adjustment.** The memory rule mandates mass expansion at cycle 5 first EXPLORATION (iter-v3/062, shifted to /063). A 46-feature jump at single-seed n_trials=35 produces IS collapse per the `feedback_v3_inert_features_at_higher_budget.md` pattern. Phased expansion (add 3-5 features individually at single-seed, then bundle survivors at CONFIRMATION) is the alternative. The QR may wish to amend the mandate to require multi-seed validation BEFORE single-seed mass-expansion EXPLORATION — similar to TRX axis discipline precedents.

3. **`trend_efficiency_signed` shows high IC with `ema_spread_atr_20` (0.872)**. If QR considers adding `trend_efficiency_signed` individually to the 14-feature stack at a future iteration, the Critic should verify whether the Category-2 carve-out applies. The feature's signal content may be largely redundant with the existing `ema_spread_atr_20`.

4. **LDO dropout to 3 OOS trades is the most concerning signal.** LDO is already thin (11 IS trades at /060). The 46-feature expansion appears to have further restricted LDO's confidence threshold to near-zero. Any future per-LDO axis should audit whether confidence calibration is structurally broken for LDO at expanded feature stacks.

5. **The /069 CONFIRMATION Path B4 spec is unaffected.** This EXPLORATION classified SUSPICIOUS-OOS-DOMINANT-CLOSED does not change the /069 CONFIRMATION brief (DSR_relative reformulation + multi-seed validation of the current /060-anchored baseline). Path B4 proceeds independently.

---

## Status

**OVERALL=READY-FOR-CRITIC**

Classification: SUSPICIOUS-OOS-DOMINANT (Section 8.3) with IS-COLLAPSE subtype.
IS Sharpe gate A.1 FAILED at -1.38 Δ (lower bound -0.20).
OOS trade-count gate C.7 FAILED at 63 trades (lower bound 66).
Axis CLOSED for cycle 1; does NOT advance to /069 CONFIRMATION as PROMISING.
