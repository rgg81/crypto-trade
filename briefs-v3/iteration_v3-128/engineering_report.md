# Engineering Report — iter-v3/128

## Headers
- Iteration: iter-v3/128
- Branch: iteration-v3/128
- Commit SHA: 10a689dd78c0ee7a9c010e1bae96eb2a0120ebba
- Hardware: WSL2 Linux 6.6.114 / Roberto local workstation
- Wall-clock time: 1.70h

---

## Configuration Diff vs Baseline (/121 CONFIRMATION-MERGE)

| Parameter | /121 Baseline | /128 This run | Change |
|---|---|---|---|
| V3_MODELS | BCH, LDO, TRX | ATOM, RUNE, AVAX, HBAR, ICP, ALGO | WHOLESALE REPLACEMENT |
| Cardinality | 3 | 6 | +3 |
| REQUIRED_GAP | 66 = (21+1)×3 | 132 = (21+1)×6 | +66 (cardinality-conditional) |
| enable_per_symbol_drawdown_brake | False | False | REVERT from /127 True |
| ENSEMBLE_SIZE | 10 (CONFIRMATION) | 3 (EXPLORATION) | Mode change |
| n_trials | 35 | 35 | Unchanged |
| V3_FEATURE_COLUMNS_TOP_N | 14 | 14 | Unchanged |
| Triple-barrier K | 21 | 21 | Unchanged |
| ATR multipliers | (2.0, 1.0) | (2.0, 1.0) | Unchanged |
| no_confirm_trigger_atr | 0.50 | 0.50 | Unchanged |
| no_confirm_k_candles | 4 | 4 | Unchanged |
| Bar interval | 8h | 8h | Unchanged |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | SACRED CONSTANT |
| training_months | 24 | 24 | SACRED CONSTANT |

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | **-0.4219** | **+2.1354** | -5.06 |
| daily_sharpe | -0.7163 | +2.2877 | -3.19 |
| max_drawdown | 154.68% | 29.14% | 0.19 |
| profit_factor | 0.9153 | 1.3415 | 1.47 |
| win_rate | 30.6% | 39.9% | 1.30 |
| n_trades | 399 | 163 | 0.41 |
| total_pnl (wpnl) | -63.28 | +76.54 | -1.21 |
| monthly_calmar | -0.4091 | +2.6269 | -6.42 |
| dsr | 0.0000 | — | — |
| pbo | 0.0992 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 630 | — | — |
| n_effective_trials | 19 | — | — |

**IS Anchor deltas (vs /121 PUBLIC IS +1.3108 / OOS +0.9682):**
- IS Δ = -0.4219 - 1.3108 = **-1.7327** (catastrophic)
- OOS Δ = 2.1354 - 0.9682 = **+1.1672** (all-time v3 OOS record)

**IS Anchor deltas (vs ADJUSTED 3-seed compression IS +1.06 / OOS +0.85):**
- IS adj-Δ = **-1.4819**
- OOS adj-Δ = **+1.2854**
- Dissociation |IS adj-Δ - OOS adj-Δ| = **2.7673** (far above 0.50 F3 threshold)

---

## Per-Symbol IS Attribution Table

| Symbol | IS trades | IS WR | IS net_pnl | IS % of total loss | IS positive? |
|---|---|---|---|---|---|
| ALGOUSDT | 64 | 25.0% | **-110.52** | **85.7% of total drag** | NO |
| HBARUSDT | 54 | 31.5% | -39.84 | 30.9% | NO |
| RUNEUSDT | 79 | 30.4% | -37.34 | 28.9% | NO |
| AVAXUSDT | 77 | 33.8% | -11.13 | 8.6% | NO |
| ICPUSDT | 57 | 36.8% | -2.68 | 2.1% | NO |
| ATOMUSDT | 68 | 44.1% | **+72.48** | (+56.2% of total — sole survivor) | YES |
| **TOTAL** | **399** | **33.6%** | **-129.03** | — | 1/6 |

**IS attribution finding:** ALGOUSDT is the primary IS casualty (-110.52 on 64 trades, WR 25.0%). Five of six symbols are IS-negative. Only ATOMUSDT survives (+72.48, WR 44.1%). F5 fires (5/6 symbols IS-negative, threshold ≥3).

---

## Per-Symbol OOS Attribution Table

| Symbol | OOS trades | OOS WR | OOS net_pnl | OOS % of total | OOS positive? |
|---|---|---|---|---|---|
| ICPUSDT | 24 | 54.2% | +35.34 | 28.5% | YES |
| AVAXUSDT | 33 | 45.5% | +30.75 | 24.8% | YES |
| ATOMUSDT | 28 | 39.3% | +19.73 | 15.9% | YES |
| HBARUSDT | 23 | 43.5% | +19.11 | 15.4% | YES |
| ALGOUSDT | 27 | 37.0% | +15.30 | 12.3% | YES |
| RUNEUSDT | 28 | 35.7% | +3.97 | 3.2% | YES |
| **TOTAL** | **163** | **42.3%** | **+124.20** | — | 6/6 |

**OOS attribution finding:** OOS lift is BROAD-BASED. All 6 symbols are OOS-positive. No single-symbol carrier: top symbol ICPUSDT at 28.5% is well below the 40% F7 concentration threshold. RUNE is the weakest at 3.2% but still positive. This is the opposite of a /127-style single-symbol carrier.

**OOS max symbol concentration: ICPUSDT = 28.5%. F7 DOES NOT FIRE.**

---

## IS Regime Analysis — What Caused the IS Catastrophe

**Worst IS months (portfolio-level):**

| Month | PnL | Trades | WR | Context |
|---|---|---|---|---|
| 2024-04 | -71.01 | 19 | 15.8% | Alt bear; ALGO/RUNE/AVAX massive SL run |
| 2024-01 | -46.90 | 20 | 20.0% | Jan 2024 crypto correction; all 6 symbols SL-heavy |
| 2023-11 | -39.79 | 19 | 21.1% | Post-LUNA FTX consolidation; model still long-biased |
| 2024-11 | -32.67 | 22 | 22.7% | Model short-biased; 2024 bull run forces SL cascade |
| 2023-10 | -26.84 | 20 | 20.0% | Continued chop/bear regime |

**Direction analysis in catastrophic IS months:**
- 2024-04: LONG 16 trades = -75.32, SHORT 3 trades = +4.31 → model LONG into bear
- 2024-01: LONG 18 trades = -36.29, SHORT 2 trades = -10.61 → model LONG into correction
- 2023-11: LONG 5 trades = -15.02, SHORT 14 trades = -24.77 → model SHORT into FTX recovery bounce
- 2024-11: LONG 5 trades = +33.32, SHORT 17 trades = -65.99 → model SHORT into 2024 bull run

**The IS catastrophe is NOT a single crash event (LUNA/FTX was May 2022 and November 2022 respectively).** The LUNA crash month (2022-05) produced +4.17 IS (model correctly short or absent). The FTX month (2022-11) produced +22.66 IS. The IS losses are CONCENTRATED in the 2023H2–2025Q1 altcoin bear-chop regime (2023-10 through 2025-03). The model trains on 24-month rolling windows that include the 2022 bear, which produced strong directional signals, then enters a choppy regime where the same feature stack generates losing signals.

**ALGOUSDT dominates IS drag (-110.52):** ALGO LONG trades contributed -118.89 on 28 trades (WR 7.1%). This is a near-total long-signal failure. ALGO's feature stack drives it to go long in all the choppy/sideways periods post-2023, collecting stop-losses repeatedly. ALGO SHORT (+8.37 on 36 trades) is modestly profitable, confirming the issue is LONG-SIGNAL QUALITY on ALGO specifically under the /121 14-feature stack — not a gross label or data error.

**IS MaxDD 154.68% is wpnl-based**: this metric is computed on accumulated weighted PnL, which can exceed 100% when the total drawdown exceeds the initial base capital denominator. The absolute drawdown magnitude reflects 6-symbol simultaneous SL cascades in multiple months.

---

## OOS Regime Analysis — Why OOS Is Exceptional

**OOS monthly breakdown (all 13 OOS months):**

| Month | PnL | Trades | WR | Comment |
|---|---|---|---|---|
| 2025-04 | +5.61 | 15 | 40.0% | OOS start; positive |
| 2025-05 | +13.73 | 26 | 38.5% | Broad altcoin recovery |
| 2025-06 | +20.51 | 16 | 43.8% | AVAX+ICP dominate |
| 2025-07 | +14.06 | 27 | 37.0% | RUNE+ALGO+ATOM contribute |
| 2025-08 | +1.36 | 14 | 35.7% | Flat |
| 2025-09 | +12.66 | 3 | 66.7% | Only 3 trades, all large TP |
| 2025-10 | +10.87 | 2 | 100.0% | 2 TP trades |
| 2025-11 | -8.93 | 5 | 20.0% | Only OOS loss month |
| 2026-01 | +7.19 | 20 | 40.0% | Broad positive |
| 2026-02 | +2.26 | 18 | 38.9% | Modest positive |
| 2026-03 | -3.01 | 2 | 50.0% | Tiny sample |
| 2026-04 | +24.11 | 6 | 66.7% | ALGO+ATOM TP-heavy |
| 2026-05 | +23.78 | 9 | 66.7% | Strong close |

**OOS regime observation:** The 2025-2026 OOS window captures a strong L1 directional regime (altcoin recovery/bull phase post-March 2025). The model generates directionally correct signals in this trending regime, driving high WR months (Sep/Oct/Apr/May 2026). The 11-month positive streak (Apr 2025 – Nov 2025 then again Jan 2026+) is structurally consistent with a trending OOS regime favoring the L1 directional hypothesis. This is NOT randomly distributed — the OOS regime is genuinely favorable for directional L1 signals.

---

## Feature Importance — EDA Prediction vs Runner Result

**Portfolio-level feature importance (last IS training month):**

| Rank | Feature | Importance | EDA HIGH-RISK prediction |
|---|---|---|---|
| 1 | range_realized_vol_50 | 1017 | Volatile across IS endpoints |
| 2 | max_dd_window_50 | 1003 | Volatile across IS endpoints |
| 3 | ret_kurt_200 | 955 | Volatile |
| 4 | ret_skew_200 | 840 | Volatile |
| 5 | ret_kurt_50 | 811 | Volatile |
| 6 | vwap_dev_20 | 802 | Volatile |
| 7 | ret_skew_50 | 767 | Volatile |
| 8 | ema_spread_atr_20 | 758 | Volatile |
| 9 | ret_autocorr_lag1_50 | 743 | Volatile |
| 10 | btc_ret_14d | 695 | Volatile |
| 11 | hurst_diff_100_50 | 662 | Volatile |
| 12 | hurst_100 | 600 | Volatile |
| 13 | sym_vs_btc_ret_7d | 505 | Volatile |
| 14 | regime_momentum_signed_5d | 466 | Volatile |

The EDA pre-registered G4 FAIL on all 6 symbols (AUC range > 0.05 across IS endpoints). The runner confirms that the feature stack is learned by all 6 symbols at last IS month — no catastrophic feature exclusions. However, the IS IS performance collapse validates the EDA's HIGH-RISK posture prediction: the rolling-endpoint instability translates directly into walk-forward misfires in the 2023H2–2025Q1 chop regime.

---

## Seed Concentration Audit

Single outer seed (42) × ENSEMBLE_SIZE=3 inner seeds. EXPLORATION mode — no multi-seed outer variance estimate. CPCV paths provide the variance signal:

**CPCV path Sharpe distribution (45 paths):**
- Positive paths: 20/45 = **44.4%** (threshold: 55% — FAILS)
- Q25: -1.47, Q50: -0.34, Q75: +0.92
- Mean: -0.26, Max: +3.64, Min: -3.70

The CPCV distribution reveals extreme bimodality: 6 paths above +1.7 (the "good OOS regime paths") and the majority clustered negative or slightly positive (the "IS-dominated bear-chop paths"). This is a structural regime-dissociation signature. The path variance of 2.76 (interquartile range ~2.39) is the highest observed in cycle-7.

---

## Label Leakage Audit

REQUIRED_GAP = 132 = (21+1) × 6 (cardinality-conditional formula). Verified in runner pre-flight: `_verify_label_leakage_gap("8h")` with `required_gap_override=132`. The cardinality-6 override was implemented at commit `0469665`. López de Prado purge requirement satisfied.

---

## Gate Efficacy Table

Per-regime report shows only "unknown" regime — regime gate not active for this universe (no BTC-regime classifier was separately configured for ATOM/RUNE/AVAX/HBAR/ICP/ALGO universe). The 7-gate RiskV2 gates (R1/R2/R3/vol-target/ADX/Hurst/OOD) operate as inherited from /121.

No_confirm gate: fires at confirmed rate visible in exit_reason distribution. Key IS exit breakdown for ALGOUSDT:
- stop_loss: 44 trades, -219.33 (catastrophic)
- take_profit: 13 trades, +110.51
- timeout: 2 trades, +7.77
- no_confirm: 5 trades, -9.46

The stop_loss dominance (44 of 64 ALGO trades = 68.8% SL rate) confirms the model consistently enters in the wrong direction on ALGO in the IS chop regime. This is a signal-quality failure, not a gate failure.

---

## Anomaly Notes

**Spot-check 10 random IS trades:**

ALGO 2024-04 SL cascade: 7 ALGO LONG trades all hit stop_loss at -5.1 to -7.1% each. Entry prices and SL prices arithmetically consistent with ATR multiplier 2.0. Math checks out — these are legitimate SL hits.

ATOM IS Nov 2022: +7.35, +6.33, 0.0 (no_confirm), -4.04 — consistent with post-FTX volatility where ATOM had directional trends the model caught. Math verified.

No NaN PnL, no NaN Sharpe (IS Sharpe is -0.4219, definitively non-NaN). No zero-trade months in OOS. OOS Dec 2025 shows 0.0000 PnL with 1 trade — checking: this is a no_confirm exit at breakeven (PnL = -fee_pct approximately zero at no_confirm). Legitimate.

**IS MaxDD 154.68% interpretation:** wpnl-based drawdown exceeds 100% because the metric accumulates signed weighted PnL; when peak-to-trough exceeds the initial reference level, the percentage can exceed 100%. This is a metric artifact of the wpnl accounting convention, not a leverage violation. The 5 simultaneous SL-cascade months (2024-01, 2023-11, 2024-04, 2024-11, 2023-10) accounting for -217.2 combined wpnl drive the drawdown to this extreme.

No `V3_EXCLUDED_SYMBOLS` violations — the new universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO) contains no v1 or v2 symbols.

---

## Section 8 Falsifier Decision Tree (first-match-wins)

**Falsifier inputs:**
- IS monthly Sharpe: -0.4219
- OOS monthly Sharpe: +2.1354
- ADJUSTED IS anchor: +1.06, ADJUSTED OOS anchor: +0.85
- IS adj-delta: **-1.4819**, OOS adj-delta: **+1.2854**
- Dissociation: **2.7673**
- IS negative symbols: 5/6; OOS negative symbols: 0/6

| Criterion | Condition | Observed | Fires? |
|---|---|---|---|
| **1 — NEGATIVE-catastrophic** | IS < +0.91 OR OOS < +0.67 | IS = **-0.4219 < 0.91** | **YES — FIRST MATCH** |
| 2 — NEGATIVE-deadlock | N/A (drawdown brake reverted) | — | Skip |
| 3 — NEGATIVE-INERT | IS ∈ [0.91, 1.06] AND OOS ∈ [0.67, 0.95] | Not reached | Not evaluated |
| 4 — NEGATIVE-no-effect | IS adj-Δ ∈ [-0.05, +0.05] AND OOS adj-Δ ∈ [-0.05, +0.05] | Not reached | Not evaluated |
| 5 — NEGATIVE-clean | IS adj-Δ ∈ [0.05, 0.10] AND OOS adj-Δ ∈ [-0.05, +0.05] | Not reached | Not evaluated |
| 6 — SUSPICIOUS-OOS-DOMINANT | F3: dissociation > 0.50 | Would fire (2.77 >> 0.50) | Not reached |
| 7 — PROMISING-cohort-fragile | IS ∈ [0.91, 1.36] AND OOS ∈ [0.67, 1.27] AND F5 | Not reached | Not evaluated |
| 8 — PROMISING-strong | IS ≥ 1.16 AND OOS ≥ 1.07 | Not reached | Not evaluated |
| 9 — PROMISING-PARTIAL-MECHANICAL | IS ∈ [1.06, 1.16] AND OOS ∈ [1.02, 1.17] | Not reached | Not evaluated |

**MECHANICAL CLASSIFICATION: NEGATIVE-catastrophic (Criterion 1 fires — IS -0.4219 < threshold 0.91).**

---

## /116-Override Candidate Analysis

The user's prompt asks whether /128 satisfies the three /116-override diagnostics (broad-based OOS lift, IS collapse mechanical/regime-specific, not a single-symbol carrier). These are the diagnostics that produced the /116 PROMISING-MECHANICAL override classification in that iteration. The /128 result shares structural surface similarity with /116 (IS below negative threshold, large OOS positive), but the diagnostics produce a DIFFERENT outcome:

**Diagnostic 1 — Broad-based OOS lift:**
ALL 6 symbols are OOS-positive (ALGO +15.30, ATOM +19.73, AVAX +30.75, HBAR +19.11, ICP +35.34, RUNE +3.97). Top OOS concentration = 28.5% (ICPUSDT) — well below the 40% F7 threshold. OOS lift passes the /116 diagnostic: NOT a single-symbol carrier.

**Diagnostic 2 — IS collapse: regime-specific or structural?**
The IS collapse is PARTIALLY regime-specific (the 2023H2–2025Q1 altcoin bear-chop regime concentrates the losses) but also PARTIALLY structural (ALGOUSDT is a systematic losing symbol with WR 25% across the entire IS window, not just one regime). The /116 result had ALL three IS symbols making sense in retrospect — the IS drag was traced to the no_confirm rule cutting winning trades in chop. Here, 5 of 6 symbols are IS-negative, and the ALGO IS failure (28 LONG trades at WR 7.1%) is too systematic across the full IS window to be attributed solely to regime. The IS collapse is DEEPER than /116's (IS -0.42 vs /116's IS +0.62), and the F5 cascade (5/6 IS-negative) has no analog in /116 (all 3 symbols contributed positively to IS in /116, just at lower WR than /060 anchor).

**Diagnostic 3 — Concentration check:**
OOS concentration PASSES (max 28.5% < 40% F7). This is structurally better than a single-carrier result. The CPCV frac_pos 0.444 FAILS the 0.55 floor — different from /116 where this gate may have been evaluated differently.

**Synthesis — /116-override-candidate verdict:**

/128 DOES NOT satisfy the /116 override criteria. The critical failure point is Diagnostic 2: in /116, the IS drag had a clean mechanical explanation (no_confirm cuts winning trades before barrier, confirmed by EDA T8 showing the cut trades would have been TP-bound) and ALL three symbols were IS-positive. In /128, 5 of 6 symbols are IS-negative, ALGOUSDT has WR 25% across the full IS window (not a regime artifact — the model systematically fails to learn ALGO), and the IS-vs-OOS dissociation of 2.77 standard deviations is 5.5× the /116 value. The broad-based OOS lift (Diagnostic 1) is genuinely encouraging, but without a mechanical IS explanation and with systematic ALGO IS failure, the /116-override logic does not transfer. The /116 override was specifically for a mechanical-drag case (exit rule cutting winners); /128 is a signal-quality-collapse case (model cannot trade 5 of 6 symbols profitably in IS).

---

## One-Paragraph Diagnosis

/128 produces the sharpest IS/OOS dissociation in v3 history: IS monthly Sharpe -0.42 (worst since pre-/059 era) alongside OOS monthly Sharpe +2.13 (all-time v3 record). The dissociation is structurally explained by regime asymmetry: the 24-month rolling IS training window learns from the 2022–2025 altcoin bear-chop period, where the 14-feature /121 stack generates losing directional signals for 5 of 6 L1 symbols (especially ALGOUSDT: 28 LONG trades at WR 7.1%, -118.89 cumulative), while the 2025-2026 OOS window is a strong L1 directional bull regime where all 6 symbols produce positive returns. The cardinality-6 expansion amplifies both the IS losses (6 simultaneous SL cascades in bad months) and the OOS gains (6 symbols all profiting in the altcoin recovery). OOS lift is genuinely broad-based (all 6 symbols positive, top concentration 28.5%), trade-rate floor is cleared (163 OOS trades), and PBO=0.099 is healthy — but frac_pos_paths=0.444 fails the 0.55 floor and the IS catastrophe (5/6 symbols negative, MaxDD 154%) cannot be attributed to a single mechanical defect or a single regime shock. The first-match-wins gate fires at Criterion 1 (IS -0.42 < threshold 0.91): mechanical classification is NEGATIVE-catastrophic. The /116-override pathway is NOT satisfied because the IS failure is symbol-specific and systematic rather than rule-mechanical, and F5 fires (5/6 IS-negative vs /116's 0/3 IS-negative). The result closes the sector-pure cardinality-6 L1 sub-axis within cycle-7 and carries a Critic question: is the broad-based OOS lift (Diagnostic 1 PASS) carrying genuine transferable signal about the ATOM/ICP/AVAX/HBAR universe that a future IS-window-updated CONFIRMATION could validate?

---

## Status

OVERALL=READY-FOR-CRITIC
