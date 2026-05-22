# Iteration iter-v3/053 — Diary

## Decision: EXPLORATION-NULL-RESULT (PATH D) — hurst_drift_50_200 UNIVERSAL SWAP fires pre-registered Section 8 LOCKED PATH D mechanically; feature LEARNED at LDO rank 8/15 mid-table despite R²=1.0 linear redundancy with 3 source primitives; LR-PF MECHANISM falsified but OUTCOME confirmed (flat Sharpe); 15th-slot SWAP family STRUCTURALLY EXHAUSTED at single-seed EXPLORATION; cycle 4 #3 of 10

iter-v3/053 = **cycle 4 #3 of 10** EXPLORATIONs post-iter-v3/050 NO-MERGE CONFIRMATION closeout. **Axis** (orchestrator pick per /052 closeout HIGH-priority #1, QR-EDA-supported at SHA `1fc6d55` with three pre-falsifiers disclosed upfront): SWAP `V3_FEATURE_COLUMNS_TOP_N` 15th element — DROP `regime_momentum_signed_3d` (PARKED per /052 PATH C-suspicious closeout) and ADD `hurst_drift_50_200` = `hurst_50 − hurst_200` (Category 1 NEW engineered feature; algebraic identity `hurst_drift_50_200 = hurst_100 − hurst_diff_100_50 − hurst_200` with R²=1.0 verified at EDA). SINGLE-AXIS SWAP: net feature count UNCHANGED at 15; V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX); REQUIRED_GAP UNCHANGED (66). Run spec: `--seeds 1 --n-trials 35 --clean-oof` (EXPLORATION-spec; 525 total Optuna trials = 3 syms × 5 inner × 35).

Result: **IS single-seed Sharpe +0.4726 / OOS single-seed Sharpe +0.4745 (seed 42); IS-OOS daily Sharpe ratio 1.2105.** Per the brief Section 8 pre-registered 5-path criteria (LOCKED at brief commit SHA `f76cb69`), **PATH D NULL-RESULT fires unambiguously** — all three AND-conditions trigger simultaneously. Per Critic FINAL `c056354`:

- PATH A (PROMISING-clean): IS Δ -0.0375 (FAIL ≥+0.05); rank-≤-10 LDO=8 PASS; ratio 1.21 PASS → NO (IS Δ misses)
- PATH B (PROMISING-INERT): rank ≥14/15 ALL 3 syms required; **BCH=14, LDO=8, TRX=15** → LDO BREAKS ALL-syms condition → NO
- PATH C-clean: IS Δ -0.0375 (not < -0.10); OOS Δ -0.0308 (not < -0.30) → NO
- PATH C-suspicious: IS-OOS daily ratio 1.2105 IN-BAND [0.5, 2.0] → NO
- **PATH D (NULL-RESULT): IS Δ -0.0375 ∈ (-0.10, +0.05) ✓ AND OOS Δ -0.0308 ∈ (-0.20, +0.20) ✓ AND axis LEARNED (LDO rank 8/15) ✓ → FIRES UNAMBIGUOUSLY**

**Mechanism (Critic Adversarial Findings #1-3 SHA `c056354`):** The QR pre-registered PATH B INERT-via-rank as 55% probability outcome based on LR-PF mechanism (R²=1.0 linear redundancy implies model should treat the feature as INERT and Optuna should assign negligible split budget). **The MECHANISM was falsified.** hurst_drift_50_200 was LEARNED at LDO rank 8/15 (mid-table, 130.2 importance) despite the algebraic identity with 3 source primitives. The portfolio rank initially mis-framed by Engineering report as "rank #1" (261.4 aggregated importance) was corrected by Critic to TRUE rank 14/15 portfolio — only LDO's outlier mid-table allocation prevents PATH B from firing; BCH (14/15) and TRX (15/15) place hurst_drift in bottom tier consistent with the LR-PF prediction at those symbols. **The OUTCOME was confirmed:** IS Δ -0.04 and OOS Δ -0.03 vs /028 baseline — no Sharpe lift despite the LDO mid-table learning. Tree models CAN allocate split BUDGET to a linearly-redundant precomputed column for representation EFFICIENCY (single-split access vs depth-3 reconstruction from `hurst_100`, `hurst_diff_100_50`, `hurst_200`) without that allocation reflecting NEW information content. The Sharpe-Δ test is the correct primary diagnostic for R²=1.0 features.

**CPCV 3-iteration stability finding (Critic Adversarial Finding #3):** CPCV path distribution at /053 is IDENTICAL to /051 and /052 to 4 decimal places on both median path Sharpe (+0.3351) and Q25 path Sharpe (-0.243), with positive-path count CONSTANT at 29/45 (64.4%) across THREE consecutive 15th-slot SWAP EXPLORATIONs. This is the cleanest signal yet that **the 14-feature base stack dominates cross-path generalization at 3-sym universe + n_trials=35 + ENSEMBLE_SIZE=5.** The 15th slot is mechanically incapable of moving CPCV distribution at single-seed EXPLORATION. The 15th-slot SWAP family is STRUCTURALLY EXHAUSTED at single-seed EXPLORATION scope. Continuing 15th-slot SWAP experiments (4th, 5th, 6th candidate feature) is a guaranteed sequence of NULL-RESULT or PROMISING-INERT outcomes at CPCV level. **The QR must escape the 15th-slot SWAP family at /054.**

**hurst_drift_50_200 PARKED** (not CLOSED) — compute function + 5 adversarial tests retained as dead-code coverage at zero revert cost per established discipline. The R²=1.0 algebraic identity precludes re-testing at higher Optuna budget per `feedback_v3_inert_features_at_higher_budget.md`.

Wall-clock: 1.25h (well within 2h EXPLORATION cap; consistent with /051=1.28h, /052=1.25h). 12/12 standard methodology checks PASS per Critic FINAL `c056354` (look-ahead, embargo, IC with source-primitive carve-out, ADF, hypothesis-implementation alignment, library pinning, etc.). No tag issued (EXPLORATION).

**Memory rule update applied at orchestrator level (new file):** `feedback_v3_lr_pf_methodology.md` created at Critic FINAL `c056354` codifying: (a) R²=1.0 exact identity features use Sharpe-Δ as primary falsifier, importance rank INFORMATIONAL only; (b) |IC|∈(0.5,1.0) features retain `feedback_v3_engineered_feature_pivot.md` importance ≥30 carve-out gate; (c) |IC|<0.5 features retain standard rank ≥ 14/15 ALL-syms PATH B mechanics. This is the primary methodological contribution of iter-v3/053.

## What Was Tested

**Hypothesis (locked in brief Section 1, SHA `f76cb69`, REFRAMED HYPOTHESIS B):** "ADDING `hurst_drift_50_200` to V3_FEATURE_COLUMNS_TOP_N at universal scope (SWAP with regime_momentum_signed_3d which DROPS per /052 closeout; net count stays 15) — alongside the system-level REVERT carry-forward (V3_MODELS = 3-sym BCH+LDO+TRX, V3_ATR_MULTIPLIERS_PER_SYMBOL = {}, block_long_for = (), REQUIRED_GAP = 66) — investigates whether the NEW Category 1 engineered feature `hurst_drift_50_200 = hurst_50 − hurst_200` (regime-drift between short-horizon and long-horizon Hurst windows) provides incremental discriminative value to LightGBM's tree-split decisions, DESPITE the EDA-discovered LINEAR REDUNDANCY R² = 1.0 with 3 source primitives. The composed feature presents a SINGLE pre-aggregated number to LightGBM, which MAY improve `colsample_bytree` efficiency if regime-drift signal exists. The primary value of the EXPLORATION is to DOCUMENT the **Linear Redundancy Pre-Falsifier (LR-PF)** methodology — an EDA-time guard against INERT-OVERFIT outcomes for future Category 2 composed-feature axis selections."

**Predicted bands (brief Section 1 + Section 4):**
- IS Sharpe: [+0.40, +0.60] (mean +0.50); Δ vs /028 anchor: [-0.10, +0.05]
- OOS Sharpe: [+0.20, +0.85] (mean +0.50); Δ vs /028 anchor: [-0.30, +0.30]
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.0] with 60% prob
- IS trade count: [130, 200]; OOS trade count: [70, 110]
- hurst_drift importance rank: 13-15/15 in ALL 3 syms (PATH B saturation-INERT, 55% prob)

**Predicted path classification (locked in brief Section 0.5):**
- PATH A: 5% / PATH B: **55%** / PATH C-clean: 10% / PATH C-suspicious: 15% / **PATH D: 15%**

**Spec (locked in brief Section 0.5; setup commit SHA `abc52dc`):**
- ITERATION_LABEL = "v3-053"
- V3_FEATURE_COLUMNS_TOP_N = 15 features (SWAP 15th element: DROP regime_momentum_signed_3d; ADD hurst_drift_50_200)
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED from /052
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} UNCHANGED
- block_long_for = () UNCHANGED
- REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED (universe unchanged)
- regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
- compute_hurst_drift_50_200 ACTIVATED in dispatch (NEW; engineered_v3.py:490-554)
- compute_regime_momentum_signed_3d RETAINED in dispatch as dead-code dispatch (zero revert cost per /052 mandate)
- compute_fracdiff_d05_close + 5 adversarial tests RETAINED as dead-code (PARKED at /051)
- 5 NEW adversarial tests in `tests/features_v3/test_hurst_drift_50_200_universal.py` PASS
- Runner: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto inner ensemble); outer_seeds = 1 (EXPLORATION-spec)
- Wall-clock: 1.25h (within 2h cap)
- Total Optuna trials: 525 = 3 syms × 5 inner × 35

## Headline Numbers

### Single-seed primary (comparison.csv + seed_summary.json; seed 42 only)

| Metric | iter-v3/028 BASELINE (multi-seed mean) | iter-v3/051 (1-seed) | iter-v3/052 (1-seed) | **iter-v3/053 (1-seed)** | Δ vs iter-v3/028 | Δ vs iter-v3/052 |
|---|---:|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.4506 | +0.5161 | **+0.4726** | **-0.0375** | **-0.0435** |
| **OOS monthly Sharpe** | +0.5053 | +0.5891 | +1.4295 | **+0.4745** | **-0.0308** | **-0.9550** |
| **IS daily Sharpe** | — | +0.9685 | +1.1692 | **+1.1849** | — | +0.0157 |
| **OOS daily Sharpe** | — | +1.1116 | +2.7204 | **+1.4344** | — | -1.2860 |
| **IS-OOS daily Sharpe ratio** | 0.99 | 1.148 (in-band) | 2.327 (OUT-OF-BAND) | **1.2105 (in-band)** | in-band | -1.116 (re-enters band) |
| IS Trades | 156 (mean) | 178 | 188 | 180 | +24 (+15.4%) | -8 (-4.3%) |
| OOS Trades | 95 (mean) | 96 | 93 | 96 | +1 (+1.1%) | +3 (+3.2%) |
| IS MaxDD | 41.43% | 37.37% | 32.58% | **45.37%** | +3.9pp worse | **+12.8pp worse** |
| OOS MaxDD | 23.53% | 32.75% | 30.42% | **44.22%** | **+20.7pp worse** | **+13.8pp worse** |
| OOS Calmar | 0.92 | 0.53 | 1.47 | 0.5558 | -0.36 | -0.92 |
| OOS Top concentration (BCH wpnl) | 76.47% (TRX) | 67.65% (BCH) | 74.58% (BCH) | **100.04%** (BCH) | +23.6pp | +25.5pp |
| DSR | 0.0 (structural at /028 multi-seed) | 0.0 (structural) | 0.0 (structural) | **0.0** (structural at n_trials=525) | structural artifact | identical |
| PBO | 0.1243 | 0.1168 | 0.1090 | **0.1377** | +0.013 | +0.029 |
| frac_positive_paths | 0.644 | 0.644 | 0.644 | **0.644** | identical | identical |
| Median path Sharpe | +0.335 | +0.3350 | +0.3351 | **+0.3351** | identical | identical (4 decimal places) |
| Q25 path Sharpe | — | -0.243 | -0.243 | **-0.243** | identical | identical (4 decimals) |
| PSR | 1.0 | 1.0 | 1.0 | **1.0** | saturation | saturation |
| n_trials | 1050 | 525 | 525 | 525 | EXPLORATION spec | EXPLORATION spec |
| n_eff | 19 | 19 | 19 | **19** | within range | identical (CYCLE-4 CONSTANT) |

**Critical observation #1:** CPCV path distribution is BIT-IDENTICAL to /051 and /052 (29/45 positive paths, median Sharpe +0.3351 to 4 decimal places, Q25 -0.243 to 4 decimal places). This is the THIRD consecutive cycle-4 EXPLORATION with IDENTICAL CPCV statistics. The 15th slot is mechanically incapable of moving CPCV distribution at this regime.

**Critical observation #2:** OOS max_dd of 44.22% is the **highest in cycle 4** (vs /052's 30.42%, /051's 32.75%). Driver: 2025-08 OOS at -33.51% on 12 trades (substantially worse than /052's -13.52% and /051's -10.73% worst month). Optuna hyperparameter draw at /053 localized larger negative trades in the Aug 2025 volatility window. At multi-seed CONFIRMATION this would be seed-averaged; no structural action warranted at EXPLORATION stage.

**Critical observation #3:** BCH OOS concentration at 100.04% (BCH wpnl 24.59 ≈ total OOS wpnl 24.58 after rounding). TRX +63.48% and LDO -63.52% approximately cancel in aggregate. The 3-symbol OOS is structurally fragile: LDO cancels 63.5% of BCH's contribution every period.

### Per-symbol decomposition (seed 42)

**IS per-symbol:**

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 86 | 44.2% | +56.46% | +0.657% | **+255.38%** |
| LDOUSDT | 9 | 22.2% | -16.09% | -1.787% | **-72.76%** |
| TRXUSDT | 85 | 30.6% | -18.27% | -0.215% | **-82.62%** |

IS is extremely BCH-concentrated at /053 (BCH 255% of total IS PnL; LDO and TRX both negative IS contributors). The IS max_dd of 45.37% (elevated vs /052's 32.58%) reflects the TRX IS drag (-82.62% IS PnL share). Single-seed IS per-symbol results are Optuna-draw sensitive at n_trials=35 single-seed; no structural interpretation should be placed on the BCH-dominant IS split. This is the highest BCH IS PnL share in cycle 4 (vs /052: BCH +62.46%, LDO +61.26%, TRX -23.72%; vs /051: BCH +104.05%, TRX +10.91%, LDO -14.96%) — the /053 Optuna draw found a configuration strongly BCH-optimized at IS at the cost of higher IS variance.

**OOS per-symbol:**

| Symbol | trades | win_rate | weighted_pnl | net_pnl_pct | concentration_pct |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 36 | 47.2% | **+24.59** | +33.71% | **+100.04%** |
| TRXUSDT | 44 | 47.7% | **+15.60** | +19.69% | +63.48% |
| LDOUSDT | 16 | 25.0% | **-15.61** | -21.82% | -63.52% |

BCH and TRX OOS WR ~47% — healthy. LDO OOS WR 25.0% — firmly in the below-50% drag territory. LDO OOS weighted_pnl at -15.61 confirms the cycle-4 structural LDO drag (see Section LDO Drag below).

### §8 Pre-registered Path Verdict (mechanical, non-renegotiable)

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND ratio ∈ [0.5, 2.0] AND rank ≤ 10 in ≥1 sym | IS Δ -0.0375 (FAIL ≥+0.05); LDO rank 8 PASS; ratio 1.21 PASS | NO |
| PATH B (PROMISING-INERT) | rank ≥ 14/15 ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | BCH 14, LDO **8**, TRX 15 (FAIL ALL-syms) | NO |
| PATH C-clean | IS Δ < -0.10 OR OOS Δ < -0.30 | -0.0375 not < -0.10; -0.0308 not < -0.30 | NO |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | 1.2105 IN-BAND | NO |
| **PATH D (NULL-RESULT)** | **IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED** | **IS Δ -0.0375 ✓ AND OOS Δ -0.0308 ✓ AND LDO rank 8 (LEARNED) ✓** | **YES — UNAMBIGUOUS** |

**PATH D is the sole path whose conditions are met. No discretion.**

## Why PATH D NULL-RESULT (Critic adjudication, FINAL SHA `c056354`)

The pre-registered Section 8 LOCKED PATH D trigger fires unambiguously:

1. **IS Δ -0.0375 ∈ (-0.10, +0.05)** — the IS Sharpe band is the saturation-flat band; -0.0375 sits comfortably inside the band.

2. **OOS Δ -0.0308 ∈ (-0.20, +0.20)** — the OOS Sharpe band is the null-OOS band; -0.0308 sits comfortably inside the band.

3. **Axis LEARNED at LDO rank 8/15** — hurst_drift_50_200 was assigned mid-table importance (130.2 LDO; 96.8 TRX; 34.4 BCH; 261.4 portfolio aggregated). The brief's pre-registered PATH D trigger required rank ≤ 13 in ≥1 sym; LDO rank=8 satisfies this. **The QR's PATH D framing was correct**: PATH D was 15% pre-registered probability for "axis LEARNED but flat Sharpe" — the LR-PF methodology documentation outcome.

4. **PATH B (PROMISING-INERT) does NOT fire** because LDO rank=8 breaks the ALL-syms condition. The QR's pre-registered 55% probability for PATH B INERT-via-rank was mechanistically WRONG (the LR-PF MECHANISM did not produce uniform bottom-tier ranking) while OUTCOME-CORRECT (no Sharpe lift).

5. **PATH C-suspicious does NOT fire** because IS-OOS daily ratio 1.2105 sits comfortably in-band [0.5, 2.0]. No OOS-window-localized artifact.

The classification is mechanically determined by the pre-registration. No QR clarification could change the verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline.

## SURPRISING Importance Finding + Critic Correction

### Engineering report initially mis-framed portfolio rank — corrected to TRUE rank 14/15

The Engineering report (SHA `161a43d`) Section "SURPRISING FINDING" framed hurst_drift_50_200 as "rank #1 portfolio importance" (261.4 aggregated importance). **Critic FINAL `c056354` Adversarial Finding #1 corrected this:**

Portfolio importance ranking (last_month_portfolio.csv):

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | range_realized_vol_50 | 456.6 |
| 2 | ret_kurt_50 | 425.8 |
| 3 | vwap_dev_20 | 402.0 |
| ... | ... | ... |
| 13 | btc_ret_14d | 272.0 |
| **14** | **hurst_drift_50_200** | **261.4** |
| 15 | regime_momentum_signed_5d | 257.0 |

hurst_drift_50_200 is **rank 14/15 portfolio** — only LDO's outlier mid-table allocation (8/15, 130.2 importance) prevents PATH B from firing. BCH (14/15, 34.4) and TRX (15/15, 96.8) place hurst_drift in bottom tier consistent with the LR-PF prediction at those symbols. The portfolio aggregated "rank #1" framing rested entirely on LDO's anomalous mid-table allocation arithmetically summing with BCH+TRX bottom-tier allocations to surpass regime_momentum_signed_5d (257.0) by 4.4 units — an importance-aggregation artifact, not a signal-quality signal.

### Per-symbol importance vs source-primitive `hurst_diff_100_50`

| Symbol | hurst_drift rank | hurst_drift imp | hurst_diff_100_50 rank | hurst_diff imp | IC(drift, diff) |
|---|---:|---:|---:|---:|---:|
| BCH | 14 / 15 | 34.4 | 12 / 15 | 53.4 | -0.866 |
| LDO | **8 / 15** | **130.2** | 13 / 15 | 102.6 | -0.866 |
| TRX | 15 / 15 | 96.8 | 13 / 15 | 116.0 | -0.866 |
| Portfolio | 14 / 15 | 261.4 | 12 / 15 | 272.0 | -0.866 |

The runtime pooled IS IC(hurst_drift_50_200, hurst_diff_100_50) = **-0.866** confirms the algebraic identity at the linear-projection level. At LDO specifically, hurst_drift substantially outranks hurst_diff (rank 8 vs 13) — LDO's model prioritizes the derived feature over the source primitive, consistent with the **tree-efficiency mechanism**. At BCH, hurst_diff outranks hurst_drift (rank 12 vs 14). At TRX, both are bottom-tier (rank 13 and 15). The pattern is symbol-specific and Optuna-draw-dependent.

## LR-PF Methodology Refinement (NEW Memory Rule)

**New memory rule created at /053 closeout: `feedback_v3_lr_pf_methodology.md`** (orchestrator-applied at Critic FINAL `c056354` Adversarial Finding #2).

### Falsified MECHANISM (QR brief Section 2 pre-falsifier #1)

The QR brief at SHA `f76cb69` Section 2 stated: "R²=1.0 → monitor importance rank." The implicit prediction was low importance = PATH B INERT. The /053 evidence FALSIFIES this:

- hurst_drift_50_200 LEARNED at LDO rank 8/15 (mid-table, 130.2 importance) despite R²=1.0 algebraic identity with 3 source primitives
- Tree models CAN allocate split BUDGET to a linearly-redundant precomputed column for representation EFFICIENCY (single-split access vs depth-3 reconstruction)
- Importance rank reflects EFFICIENCY allocation, NOT NEW signal content

### Confirmed OUTCOME (the EXPLORATION's primary contribution)

The Sharpe-Δ test is the CORRECT primary diagnostic for R²=1.0 features:
- IS Δ -0.0375 ∈ (-0.10, +0.05) ✓ (flat)
- OOS Δ -0.0308 ∈ (-0.20, +0.20) ✓ (flat)
- No new signal extracted; OUTCOME-INERT confirmed

### New memory rule codification

`feedback_v3_lr_pf_methodology.md` codifies three tiers of falsifier discipline based on linear-redundancy magnitude:

1. **R²=1.0 exact algebraic identity**: PRIMARY falsifier = IS Sharpe Δ ∈ (-0.10, +0.05); importance rank INFORMATIONAL only. Drop the feature after PATH D verdict; do NOT retest at higher Optuna budget per `feedback_v3_inert_features_at_higher_budget.md`.
2. **|IC| ∈ (0.5, 1.0) partial redundancy**: current `feedback_v3_engineered_feature_pivot.md` carve-out APPLIES (importance ≥ 30 threshold). Sharpe-Δ + importance rank BOTH apply as falsifiers.
3. **|IC| < 0.5 orthogonal**: standard `rank ≥ 14/15 ALL-syms = PATH B` mechanics APPLY. Sharpe-Δ + importance rank BOTH apply as falsifiers.

This codification supersedes the brief's "monitor importance rank" language for R²=1.0 features and compounds across all subsequent Category 2 composed-feature axis selections.

Memory rule expansion at /052 closeout (`feedback_v3_engineered_features_dont_stack.md`) covering SAME-FAMILY sister stacking at ANY IC remains in force and orthogonal to the new LR-PF rule.

## CPCV 3-Iteration Stability: 15th-Slot SWAP Family STRUCTURALLY EXHAUSTED

The /053 CPCV statistics are, for the THIRD consecutive cycle-4 EXPLORATION, essentially identical:

| Statistic | iter-v3/051 | iter-v3/052 | **iter-v3/053** |
|---|---:|---:|---:|
| Paths positive | 29 of 45 (64.4%) | 29 of 45 (64.4%) | **29 of 45 (64.4%)** |
| Median path Sharpe | +0.335 | +0.3351 | **+0.3351** |
| Q25 path Sharpe | -0.243 | -0.243 | **-0.243** |
| Q75 path Sharpe | +0.884 | +0.838 | +0.838 |
| PBO (per-cell mean) | 0.1168 | 0.1090 | 0.1377 |

**Median and Q25 are IDENTICAL to 4 decimal places across three 15th-slot SWAP EXPLORATIONs.** Positive-path count is CONSTANT at 29/45. The 14-feature base stack dominates cross-path generalization; the 15th-slot content has been INVISIBLE at the CPCV level across all three cycle-4 EXPLORATION tests:

| Iteration | 15th-slot feature | CPCV median Sharpe | CPCV Q25 Sharpe | Outcome |
|---|---|---:|---:|---|
| iter-v3/051 | fracdiff_d05_close | +0.335 | -0.243 | EXPLORATION-NULL-RESULT; PARKED |
| iter-v3/052 | regime_momentum_signed_3d | +0.3351 | -0.243 | EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED |
| **iter-v3/053** | **hurst_drift_50_200** | **+0.3351** | **-0.243** | **EXPLORATION-NULL-RESULT PATH D; PARKED** |

**Three-iteration CPCV stability is the cleanest structural diagnostic in cycle 4.** Continuing 15th-slot SWAP experiments (4th, 5th, 6th candidate feature) is a guaranteed sequence of NULL-RESULT or PROMISING-INERT outcomes at CPCV level. **The QR MUST escape the 15th-slot SWAP family at /054.** Per Critic FINAL `c056354` Adversarial Finding #3: "This is the structural limit on cycle 4 #4-10 axis design." Per the same finding's Recommendation #3: "Pre-register CPCV distribution sensitivity as a 6th pre-falsifier band — `PATH E (CPCV-INVARIANT NULL)`: CPCV positive-path count, median path Sharpe, and Q25 path Sharpe all match /051/052/053 to 2 decimals. If PATH E fires alongside any other path, the axis is classified as 'failed to escape 15th-slot saturation' and the axis family is CLOSED at /054."

To move the CPCV distribution, a structural change to the base stack (different feature family replacing a mid-table feature) or a non-feature axis (labeling, risk architecture, universe) would be required.

## LDO Drag Structural Across 3 Cycle-4 Iterations

LDO OOS performance:

| Iteration | LDO OOS wpnl | LDO OOS trades | LDO OOS WR | 15th-slot feature |
|---|---:|---:|---:|---|
| iter-v3/051 | -17.44 | 13 | 23.1% | fracdiff_d05_close |
| iter-v3/052 | -13.96 | 14 | 28.6% | regime_momentum_signed_3d |
| **iter-v3/053** | **-15.61** | **16** | **25.0%** | **hurst_drift_50_200** |

LDO OOS weighted_pnl has ranged -13.96 to -17.44 across three consecutive cycle-4 EXPLORATION 15th-slot SWAPs (range = 3.48 units). The variation is within single-seed Optuna noise. **The structural LDO OOS negative signal is stable and independent of the 15th-slot content:** LDO's WR oscillates 23-29% (all below 50%) and weighted_pnl oscillates -14 to -17. **No 15th-slot feature has addressed the LDO signal generator problem.**

LDO IS at /053: 9 trades, 22.2% WR, -16.09% net_pnl_pct, -72.76% IS PnL share — the worst LDO IS result in cycle 4 (vs /052: 15 trades, 40.0% WR, +61.26% IS PnL share recovering; vs /051: 11 trades, 27.3% WR, -14.96% IS PnL share but +36.78% weighted_pnl share). The /053 LDO IS result is Optuna-draw-sensitive at n_trials=35 single-seed; no structural trend should be read into the IS oscillations. **The LDO OOS drag, however, has been structurally negative across 3 EXPLORATIONs** with default ATR and no per-symbol customizations.

LDO REMOVAL was investigated at /052 EDA (SHA `0a10581`) and PRE-FALSIFIED — LDO weighted_pnl was +11.155 at /051 IS = +36.78% IS contributor when corrected for weight_factor. The 2-sym counterfactual triggered PATH C-suspicious by construction (IS Δ -0.16, IS-OOS daily ratio 3.58 OUT-OF-BAND). **Returning to LDO removal at /054 requires fresh /053-trade-roster EDA superseding /052's.**

## n_eff = 19: Cycle-4 STRUCTURAL CONSTANT — DSR = 0 Mechanically Inevitable at Single-Seed

n_effective_trials = 19 across /051, /052, /053 (CONSISTENT to integer precision). The 15-feature stack's effective independent trial count saturates at ~19 well below the naive n_trials count of 525. This is now a **CYCLE-4 STRUCTURAL CONSTANT.**

DSR = 0 at single-seed EXPLORATION is **mechanically inevitable**:

```
E[max_SR] ≈ Z_alpha × sqrt(2 × ln(n_eff))
         ≈ 1.645 × sqrt(2 × ln(19))
         ≈ 1.645 × 2.43
         ≈ 4.00
```

Realized OOS daily Sharpe of ~1.4 at /053 does not clear E[max_SR] ≈ 4.00 threshold. DSR mechanically lands at exactly 0.0 (lower-bound clamp).

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY; CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR] = 3.37) which still doesn't clear annualized 4.0. **Cycle 4 CONFIRMATION at iter-v3/061 will need to either (a) increase n_trials to ≥ 100 per cell, OR (b) propose alternative multiple-testing gate** per Critic FINAL `c056354` Adversarial Finding #5. DSR gate reformulation is one of the HIGH-priority axes for /054.

## Memory Rule Updates

### NEW (orchestrator-applied at Critic FINAL SHA `c056354`)

- **`feedback_v3_lr_pf_methodology.md` CREATED 2026-05-11** — three-tier falsifier discipline based on linear-redundancy magnitude:
  - R²=1.0 exact: Sharpe-Δ primary falsifier; importance rank INFORMATIONAL only
  - |IC|∈(0.5,1.0): importance ≥30 carve-out gate (per `feedback_v3_engineered_feature_pivot.md`)
  - |IC|<0.5: standard rank ≥ 14/15 ALL-syms PATH B mechanics

### Carried forward / referenced

- **`feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11** (orchestrator-applied at /052 Critic `34cc46f`) covers SAME-FAMILY sister stacking at ANY IC. UNCHANGED at /053 closeout.
- **`feedback_v3_axis_selection_quant_discipline.md` fired at /053** — QR EDA at SHA `1fc6d55` produced numerical pre-falsifiers BEFORE locking brief; orchestrator pick PRELIMINARILY SUPPORTED. Section 10 audit trail documents the EDA-supported re-framing.
- **`feedback_v3_engineered_features_proven.md` UNCHANGED** — regime_momentum family established by 5d at /025+/028 CONFIRMATION-MERGE; hurst_drift PARKED at /053 does NOT invalidate the proven status of regime_momentum_signed_5d.
- **`feedback_v3_strict_10_to_1_cadence.md` advances 3/10** for cycle 4. iter-v3/053 is cycle 4 #3; 7 more EXPLORATIONs needed before iter-v3/061 CONFIRMATION.
- **`feedback_v3_dsr_mode_artifact.md` UNCHANGED** — DSR=0.0 at /053 EXPLORATION-spec n_trials=525 is INFORMATIONAL ONLY per established interpretation. n_eff=19 is now a CYCLE-4 STRUCTURAL CONSTANT.
- **`feedback_v3_single_seed_frozen_baseline.md` REVISED interpretation applied** — when V3_FEATURE_COLUMNS_TOP_N changes universally, per-symbol Optuna trajectories perturb; what looks like "axis lift" is search-trajectory artifact on the base 14 features.
- **`feedback_v3_engineered_feature_pivot.md` REFINED at /053** — Category 2 IC carve-out APPLIES to |IC|∈(0.5,1.0); does NOT cover R²=1.0 exact identities (new tier per LR-PF rule).
- **`feedback_v3_inert_features_at_higher_budget.md` APPLIED at /053** — hurst_drift_50_200 PARKED post-PATH D; do NOT retest at higher Optuna budget.
- **`feedback_v3_structural_over_knob_exploration.md` mandate for /054**: NEW feature families > NEW model arch > NEW labeling > NEW risk primitive > universe > knob axes. Three consecutive 15th-slot SWAP experiments confirm CPCV-insensitivity; /054 MUST escape the 15th-slot SWAP family.
- **`feedback_v3_concentration_is_signal.md` referenced** — per-symbol PnL share caps CLOSED at /020; orthogonal mechanisms (per-symbol drawdown brake; universe expansion) remain valid axes for /054.

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture PRESERVED** as cycle 4 baseline (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66).
- **hurst_drift_50_200 PARKED at /053 closeout** (not CLOSED). Compute function (engineered_v3.py:490-554) + 5 adversarial tests (tests/features_v3/test_hurst_drift_50_200_universal.py) retained as zero-revert-cost dead-code coverage per established discipline analogous to fracdiff_d05_close PARKED status and regime_momentum_signed_3d dispatch-retained status.
- **regime_momentum_signed_3d UNIVERSAL axis CLOSED at /052** (PATH C-suspicious). Compute function retained as inert dispatch at /053 head per /052 closeout mandate.
- **regime_momentum_signed_5d PRESERVED** in V3_FEATURE_COLUMNS_TOP_N (iter-v3/028 edge ingredient; portfolio rank 15/15 at /053 — Optuna draw at /053 prioritized hurst_drift in the 15th slot's split budget; family proven status preserved per `feedback_v3_engineered_features_proven.md`).
- **fracdiff_d05_close remains PARKED** at /051 closeout. compute function + 5 tests retained as zero-revert-cost dead-code coverage.
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure** — validated at multi-seed (/050); no architectural defects.
- **Primitive 10 (`block_long_for`) wired value `()`** UNCHANGED from /051; mechanism + tests + GateStats counter PRESERVED as code.
- **LDO removal axis DEFERRED** to multi-seed CONFIRMATION (iter-v3/061+) where single-seed lottery artifacts dissolve. Returning to LDO removal at /054 requires fresh /053-trade-roster EDA superseding /052's pre-falsification at SHA `0a10581`.
- **`--clean-oof` guardrail RETAINED** (SHA `6a216b5`). Behavior correct at /053.
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## Cycle 4 Cadence: 3/10 EXPLORATIONs Advanced

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- **Cycle 4 #3 of 10 = iter-v3/053** (hurst_drift_50_200 SWAP UNIVERSAL; **EXPLORATION-NULL-RESULT PATH D**; PARKED — LR-PF methodology refined)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md`)
- **7 more EXPLORATIONs remain** before cycle 4 CONFIRMATION: iter-v3/054 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/053 actual: 1.25h within cap.

**Cycle 4 hypothesis status** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/053 result: IS +0.4726 BELOW +0.5101 floor by -0.0375; OOS +0.4745 BELOW +0.5053 floor by -0.0308. **PATH D NULL-RESULT classification means no axis advance.** The cycle 4 hypothesis is NOT YET satisfied via clean PROMISING; 7 EXPLORATIONs remaining.

## iter-v3/054 Axis Priorities

Per Critic FINAL `c056354` Recommendation #1 + Adversarial Finding #3 (15th-slot SWAP family STRUCTURALLY EXHAUSTED at single-seed EXPLORATION):

### MANDATORY PRIORITY: EXIT the 15th-slot SWAP family

Three consecutive 15th-slot Category-2-composed-feature SWAP attempts (fracdiff PARKED at /051; regime_momentum_signed_3d CLOSED PATH C-suspicious at /052; hurst_drift_50_200 PARKED via PATH D at /053) confirm CPCV-insensitivity at this scope. **iter-v3/054 axis MUST be structurally distinguishable from 15th-slot SWAP.**

### HIGH-priority axes for /054

1. **CatBoost head-to-head — NEW model architecture** (per /050 Critic recommendation + /052 closeout HIGH-priority #2)
   - Mechanism: replace LightGBM with CatBoost; per-symbol fit; same V3_FEATURE_COLUMNS_TOP_N
   - The iter-v3/016 LightGBM→XGBoost test was NEGATIVE clean at n_trials=10 (saturated); CatBoost has distinct optimization defaults (Ordered Boosting; symmetric trees; native categorical handling) and may behave differently
   - Implementation cost: 4-8h impl likely exceeds 2h cap; alternative methodology-only proof-of-concept (1-2h spike on single symbol-month) followed by full backtest in CONFIRMATION
   - Aligns with `feedback_v3_structural_over_knob_exploration.md`: Category 2 structural axis (NEW model arch)

2. **DSR gate reformulation — methodology axis** (deferred from /028 + /039 + /050 + /052)
   - Mechanism: replace DSR > 0.95 absolute threshold with relative DSR (rank-percentile of CPCV path Sharpes); fixes the structural DSR=0 artifact at EXPLORATION-spec n_trials=525 and n_eff=19 cycle-4 CONSTANT
   - Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY; CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR]=3.37) which still doesn't clear annualized 4.0
   - Implementation cost: ~1.5h (DSR computation modification + Critic gate update); analysis-only — no wall-clock budget consumption on backtest
   - Aligns with cycle 4 hypothesis: DSR reformulation could enable IS Sharpe +0.50 to clear MERGE gate at iter-v3/061 CONFIRMATION

3. **Per-symbol drawdown brake — NEW risk primitive** (NEW axis; orthogonal to CLOSED per-symbol cap precedents)
   - Mechanism: per-symbol drawdown trigger that pauses trades on a single symbol when its rolling weighted_pnl drawdown hits threshold; loss-stop semantics differs from proportional scaling (CLOSED at /020 per `feedback_v3_concentration_is_signal.md`)
   - Targets the LDO drag structural problem confirmed across /051-/053 (LDO OOS wpnl -13.96 to -17.44 range)
   - Implementation cost: ~1.5h impl
   - Aligns with `feedback_v3_structural_over_knob_exploration.md`: Category 4 structural axis (NEW risk primitive); orthogonal to per-symbol PnL share caps per `feedback_v3_concentration_is_signal.md`

4. **Base-stack feature reordering — replacing a mid-table feature in base 14, not slot 15**
   - Mechanism: identify a mid-table feature in base 14 (e.g. rank 8-12 at /053 last_month_portfolio.csv) and replace with a genuinely orthogonal Category 1 feature (|IC| < 0.50 against ALL existing 14 base features)
   - Directly tests CPCV path distribution response to non-slot-15 changes
   - Requires fresh EDA on which base feature is marginal contributor at /053 + orthogonal candidate selection
   - Implementation cost: 2h+ (EDA + adversarial tests + backtest)

### MEDIUM-priority axes

5. **Labeling architecture change** (CLOSED at /017 for meta-labeling specifically; not closed for fixed-horizon return labels; deferred from cycle 3+)
6. **Universe expansion** (CLOSED for per-symbol PnL share caps at /020; expansion-as-orthogonal-mechanism per `feedback_v3_concentration_is_signal.md` remains valid axis)

### LOW-priority axes (CLOSED or saturated)

7. ~~LDO removal investigation~~ — DEFERRED to multi-seed CONFIRMATION; pre-falsified at /052 EDA SHA `0a10581`. Returning to LDO removal at /054 requires fresh /053-trade-roster EDA superseding /052's.
8. ~~regime_momentum_signed_3d UNIVERSAL retest~~ — CLOSED for cycle 4 (PATH C-suspicious; family exhausted at universal single-seed scope)
9. ~~hurst_drift_50_200 retest at higher Optuna budget~~ — CLOSED per `feedback_v3_inert_features_at_higher_budget.md` (R²=1.0 algebraic identity precludes retest)
10. ~~ADX gate tuning~~ — CLOSED at /015 (`feedback_v3_adx_axis_asymmetric_v3.md`)
11. ~~Per-symbol PnL caps~~ — CLOSED at /020 (`feedback_v3_concentration_is_signal.md`)
12. ~~Per-symbol ATR multipliers~~ — CLOSED at /045-/050 (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
13. ~~Further 15th-slot SWAP experiments~~ — STRUCTURALLY EXHAUSTED at single-seed EXPLORATION; CPCV-INVARIANT

### Recommended /054 axis (ranked)

**Tier 1 (within 2h EXPLORATION cap):**
- DSR gate reformulation (~1.5h; methodology-only)
- Per-symbol drawdown brake (~1.5h impl; NEW risk primitive)

**Tier 2 (1-2h spike then defer full backtest to CONFIRMATION):**
- CatBoost head-to-head (1-2h methodology-only spike)

**Tier 3 (2h+ if EDA can complete in <1h):**
- Base-stack feature reordering (requires fresh EDA + orthogonal candidate selection)

### Pre-register CPCV-INVARIANT NULL as PATH E

Per Critic FINAL `c056354` Recommendation #3 + Adversarial Finding #3: For iter-v3/054 brief Section 8, ADD: **"PATH E (CPCV-INVARIANT NULL): CPCV positive-path count, median path Sharpe, and Q25 path Sharpe all match /051/052/053 to 2 decimals. If PATH E fires alongside any other path, the axis is classified as 'failed to escape 15th-slot saturation' and the axis family is CLOSED at /054."** This protects future EXPLORATIONs from continuing 15th-slot SWAP saturation when CPCV distribution remains bit-identical to the structural exhaustion pattern.

## EDA Priorities for iter-v3/054 (per `feedback_v3_axis_selection_quant_discipline.md`)

Per the rule, the QR must produce numerical tables in `analysis/iteration_v3-054/*.py` with EDA-derived numerical evidence BEFORE locking the brief. EDA priorities depend on selected axis:

### If axis = DSR gate reformulation

- Reformulate DSR with rank-percentile of CPCV path Sharpes against expected null distribution
- Test whether reformulated DSR clears 0.95 threshold for iter-v3/028 baseline (+0.5101 IS, +0.5053 OOS, n_trials=1050)
- Test reformulation against /051/052/053 (n_trials=525 each)
- Analysis-only — no backtest budget consumption; can land brief + setup in <1h
- Code change in `src/crypto_trade/validation_v3.py` or equivalent CPCV/DSR module

### If axis = Per-symbol drawdown brake

- Compute /053 trade roster rolling weighted_pnl drawdown per symbol
- Identify drawdown threshold candidates (e.g. -10%, -15%, -20%) that would have paused LDO at /053 without affecting BCH or TRX
- Simulate threshold effect on /053 trade roster (counterfactual PnL with paused LDO trades during drawdown)
- Estimate expected behavioral effect: how many LDO trades would be killed?

### If axis = CatBoost head-to-head

- Spike on single symbol-month (e.g. BCH 2024-12) to verify CatBoost reproduces LightGBM result within ±5% on isolated test
- Translate LightGBM Optuna parameter space to CatBoost equivalents
- Document `colsample_bytree` analog (`feature_border_type` + `border_count`)
- Document expected wall-clock for full backtest (estimate based on spike runtime × 3 syms × n_trials)

### If axis = Base-stack feature reordering

- Aggregate /053 last_month_portfolio.csv importance ranks
- Identify rank 8-12 feature in base 14 that is marginal contributor across 3 syms
- Select orthogonal Category 1 candidate with |IC| < 0.50 against ALL existing 14 base features + against the candidate's source primitives
- Document expected behavioral effect: how many trades change?

## See Also

- `briefs-v3/iteration_v3-053/research_brief.md` — Phase 5 brief (SHA `f76cb69`; REFRAMED HYPOTHESIS B; three pre-falsifiers disclosed)
- `briefs-v3/iteration_v3-053/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `853bc7e`)
- `briefs-v3/iteration_v3-053/engineering_report.md` — Phase 6/7 engineering report (SHA `161a43d`; PATH D classification; portfolio rank mis-framing later corrected by Critic)
- `briefs-v3/iteration_v3-053/review.md` — Phase 7.5 Critic FINAL (SHA `c056354`; EXPLORATION-NULL-RESULT PATH D; portfolio rank correction; LR-PF methodology refinement; 15th-slot SWAP family structurally exhausted)
- `reports-v3/iteration_v3-053/comparison.csv` — primary numerical results (single-seed)
- `reports-v3/iteration_v3-053/seed_summary.json` — per-seed data (1 outer seed)
- `reports-v3/iteration_v3-053/dsr.json` — DSR/PBO/PSR/n_eff (n_trials=525 EXPLORATION-spec)
- `reports-v3/iteration_v3-053/per_cell_pbo.csv` — per-cell PBO
- `reports-v3/iteration_v3-053/cpcv_paths.csv` — CPCV path data (45 paths; bit-identical to /051/052 on median + Q25)
- `reports-v3/iteration_v3-053/ic_matrix.csv` — hurst_drift_50_200 vs existing 14 features (IC vs hurst_diff_100_50 = -0.866 pooled)
- `reports-v3/iteration_v3-053/adf_test.csv` — hurst_drift_50_200 ADF stationarity per symbol (BCH p=1.55e-21; LDO p=1.13e-15; TRX p=2.59e-21)
- `reports-v3/iteration_v3-053/in_sample/per_symbol.csv` — IS per-symbol PnL attribution
- `reports-v3/iteration_v3-053/out_of_sample/per_symbol.csv` — OOS per-symbol PnL attribution
- `reports-v3/iteration_v3-053/in_sample/model_importance_last_month_*.csv` — feature importance per symbol + portfolio (hurst_drift rank BCH 14/15 + LDO 8/15 + TRX 15/15 + portfolio 14/15)
- `reports-v3/iteration_v3-053/in_sample/trades.csv` + `out_of_sample/trades.csv` — trade rosters
- `analysis/iteration_v3-053/hurst_drift_50_200_eda.py` + 6 CSVs + `synthesis.md` (SHA `1fc6d55`) — QR EDA with three pre-falsifiers disclosed (R²=1.0 linear redundancy; insignificant univariate ρ; max |IC| 0.85-0.88)
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 490-554) — `compute_hurst_drift_50_200` NEW (ACTIVATED at /053 setup)
- `src/crypto_trade/features_v3/engineered_v3.py` (regime_momentum_signed_3d retained as dead-code dispatch) — preserved per /052 closeout
- `src/crypto_trade/features_v3/__init__.py` — V3_FEATURE_COLUMNS_TOP_N (15 elements at /053; SWAP regime_momentum_signed_3d → hurst_drift_50_200)
- `run_baseline_v3.py` — ITERATION_LABEL "v3-053"; V3_MODELS 3-sym; block_long_for=(); `_verify_feature_columns` enforces hurst_drift_50_200 PRESENT + regime_momentum_signed_3d ABSENT
- `validation_v3.py` — REQUIRED_GAP=66 (UNCHANGED from /051/052)
- `tests/features_v3/test_hurst_drift_50_200_universal.py` — 5 adversarial tests (PASS at /053; retained as dead-code coverage at /054 setup)
- `tests/features_v3/test_regime_momentum_signed_3d_universal.py` — 5 adversarial tests (PASS; dead-code coverage at /053)
- `tests/features_v3/test_fracdiff_d05_universal.py` — 5 adversarial tests (PASS; dead-code coverage at /053)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS; SHA `b0576df`)
- Setup commit SHA `abc52dc` — V3_FEATURE_COLUMNS_TOP_N SWAP + compute_hurst_drift_50_200 dispatch activation
- Fix commit SHA `d16d7bb` — engineering fix
- Gate commit SHA `853bc7e` — Phase 5.5 gate
- Backfill commit SHA `c516826` — head SHA at engineering report time
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_lr_pf_methodology.md` — **NEW (2026-05-11; orchestrator-applied at /053 Critic FINAL `c056354`)** — R²=1.0 features use Sharpe-Δ as primary falsifier, importance rank INFORMATIONAL
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_features_dont_stack.md` — EXPANDED 2026-05-11 at /052 (orchestrator-applied at /052 Critic `34cc46f`) — UNCHANGED at /053
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_axis_selection_quant_discipline.md` — fired at /053 EDA pre-falsifier disclosure
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_features_proven.md` — regime_momentum family proven status preserved (5d at /025+/028)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_structural_over_knob_exploration.md` — Category 1-5 structural priority for /054; NEW feature families top
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 3/10 advanced
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_dsr_mode_artifact.md` — DSR EXPLORATION-INFORMATIONAL interpretation; n_eff=19 cycle-4 CONSTANT
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — REVISED interpretation applied
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_feature_pivot.md` — REFINED at /053 — Category 2 IC carve-out applies to |IC|∈(0.5,1.0) NOT R²=1.0 exact
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_inert_features_at_higher_budget.md` — APPLIED at /053; hurst_drift PARKED post-PATH D; no retest at higher budget
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_concentration_is_signal.md` — orthogonal mechanisms for /054 axis 3 (per-symbol drawdown brake)
- `diary-v3/iteration_v3-052.md` — immediate predecessor (EXPLORATION-NEGATIVE PATH C-suspicious; cycle 4 #2 of 10; same memory rule expansion lineage)
- `diary-v3/iteration_v3-051.md` — cycle 4 #1 of 10 (EXPLORATION-NULL-RESULT PATH D; fracdiff PARKED)
- `diary-v3/iteration_v3-050.md` — cycle 3 CONFIRMATION-NO-MERGE-revert closeout
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor; regime_momentum_signed_5d edge ingredient)
- `diary-v3/iteration_v3-025.md` — regime_momentum_signed_5d first PROMISING (single-seed)
- `briefs-v3/exploration_catalog.md` — iter-v3/053 catalog row at diary closure (EXPLORATION-NULL-RESULT PATH D verdict; LR-PF methodology refined; 15th-slot SWAP family structurally exhausted)
