# iter-v3/125 — Cycle-7 slot 4 — EXPLORATION-NEGATIVE-catastrophic / WILD V3_MODELS replacement under lifted constraints; cohort-shaped-architecture finding

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 4 of 10; first under LIFTED constraints per `feedback_v3_cycle7_constraints_lifted.md`; single axis: V3_MODELS tuple WHOLESALE REPLACEMENT BCH/LDO/TRX → ATOM/RUNE/UNI at 8h)
**Axis**: WILD universe replacement (Critic Priority 4 of /124 menu deferred; user-mandated WILD axis class)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `53cfc06`
**Classification**: NEGATIVE-catastrophic — IS Sharpe Δ −1.248 vs /121 multi-seed baseline (>3× the −0.40 threshold) AND OOS Sharpe Δ −0.858 (>2× the −0.30 threshold); both legs trigger first-match NEGATIVE-catastrophic
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

Single-axis V3_MODELS tuple replacement. The runner's `V3_MODELS` tuple was changed from `("v3-123-BCH","BCHUSDT"), ("v3-123-LDO","LDOUSDT"), ("v3-123-TRX","TRXUSDT")` to `("v3-125-ATOM","ATOMUSDT"), ("v3-125-RUNE","RUNEUSDT"), ("v3-125-UNI","UNIUSDT")`. /124's K=63 + Branch B (3.4641, 1.7321) ATR scaling were REVERTED to /121-canonical K=21 + (2.0, 1.0). All other architecture bit-identical to /121: 14-feature V3_FEATURE_COLUMNS_TOP_N, +2/−1 ATR triple-barrier K=21, 7-gate RiskV2, /116 no_confirm primitive (trigger_atr=0.50, k_candles=4), REQUIRED_GAP=66, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35.

Selection rationale: ATOM/RUNE/UNI were never in any prior V3_MODELS bundle; all 3 cleared G1 data-depth (≥30 IS months evaluable); G2 within-candidate ret_corr ≤ 0.631 (PASS < 0.85); G3 ADF p < 1e-6 on all 9 feature-symbol pairs. Sector diversity by construction: L0 hub (Cosmos) + cross-chain DeFi (THORChain) + DEX governance (Uniswap), structurally orthogonal to the all-DeFi /110-111 attempt and the all-gaming /087 attempt.

Commit chain: EDA `a2bd2d6` → brief `6bb4519` → setup `85f413b` (V3_MODELS replacement + /124 REVERT in one atomic commit) → engineering report `b8e91a6` → Critic FINAL `53cfc06`. Wall-clock ≈ 1.1h (estimated; run.log not present in artefacts — same anomaly as /124; engineering proceeded from comparison.csv + dsr.json + ensemble_summary.json + IS/OOS trade artefacts which were complete).

Files changed: `run_baseline_v3.py` (V3_MODELS tuple + ITERATION_LABEL "v3-125" + `_verify_feature_columns` symbol-loop reflecting new universe + `DEFAULT_ATR_MULTIPLIERS` assertion expected (2.0, 1.0)); `src/crypto_trade/features_v3/__init__.py` (`DEFAULT_ATR_MULTIPLIERS` (3.4641, 1.7321) → (2.0, 1.0) REVERTING /124 Branch B). ZERO `src/` changes to feature pipeline (`process_symbol_v3` is symbol-agnostic).

Pre-flight feature parquet generation for ATOM/RUNE/UNI completed at Phase 6 step 2 (≤5min one-time generation).

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /125 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **+0.0632** | **−1.2476** |
| OOS monthly Sharpe | +0.9682 | **+0.1104** | **−0.8578** |
| IS daily Sharpe | 3.1180 | +0.1677 | −2.95 |
| OOS daily Sharpe | 2.3979 | +0.2135 | −2.18 |
| IS MaxDD | 26.38% | **82.97%** | **+56.59pp** (3.14×) |
| OOS MaxDD | 25.70% | 36.76% | +11.06pp |
| Profit Factor IS | 1.6019 | 1.0229 | −0.58 |
| Profit Factor OOS | 1.3869 | 1.0247 | −0.36 |
| Win Rate OOS | 39.8% | 34.2% | −5.6pp |
| IS trades | 173 | 208 | +35 |
| OOS trades | 98 | 79 | −19 |
| OOS/IS Sharpe ratio | 0.7386 | 1.747 | (ratio inflated by IS near-zero denominator; not signal) |
| PSR | 1.0 | **0.7965** | −0.20 |
| PBO mean | 0.1278 | 0.1064 | −0.02 (PASS by gate; informational) |
| frac_positive_paths | 0.6444 | **0.4667** | −0.178 (BELOW 0.55 floor — FAIL) |

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- ATOMUSDT: 68 IS trades, 44.1% WR, net_pnl_pct **+72.48%** (sole carrier; pct_of_total_pnl +974%)
- UNIUSDT: 61 IS trades, 39.3% WR, net_pnl_pct **−27.70%** (drag; pct_of_total_pnl −372%)
- RUNEUSDT: 79 IS trades, 30.4% WR, net_pnl_pct **−37.34%** (largest drag; pct_of_total_pnl −502%; WR substantially below 33.3% 2:1 ATR breakeven)

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- ATOMUSDT: 28 OOS trades, 42.9% WR, net_pnl_pct **+22.29%** (carrier)
- RUNEUSDT: 28 OOS trades, 35.7% WR, net_pnl_pct **+3.97%** (marginal positive)
- UNIUSDT: 23 OOS trades, 26.1% WR, net_pnl_pct **−27.29%** (sole OOS drag; WR collapsed to 26%)

F2 (1-symbol carrier) and F3 (cross-cohort transfer failure) both TRIGGERED simultaneously. IS structure: ATOM single carrier with 2-of-3 IS drag (RUNE + UNI both >25% IS loss). OOS structure: inversion — UNI becomes the sole drag (WR 26% well below 2:1 ATR breakeven); ATOM remains positive; RUNE flips marginally positive. Cross-cohort transfer mechanism: the 14-feature stack + (2.0, 1.0)-ATR K=21 + /121 Optuna search trajectory cannot extract edge from the new universe — IS MaxDD 82.97% (vs /121 26.38%) indicates systematic IS misfitting on RUNE/UNI specifically.

## 3. Mechanism: cohort-shaped architecture — 14-feature stack + ATR + K=21 calibration is BCH/LDO/TRX-cohort-tuned

The /125 axis falsifies the implicit assumption that the /121 architecture's edge generalizes to any 3-symbol-cohort universe selection. The root cause is a quantitative-structural mismatch in 3 axes (per T2 EDA + production attribution):

**Vol-magnitude axis**: ATOM/RUNE/UNI per-bar return magnitudes 150–195 bps (median |ret_1bar|) — substantially HIGHER than BCH/LDO/TRX 85–168 bps. The +2/−1 ATR triple-barrier with `natr_21_raw` ATR column adapts proportionally PER-SYMBOL, but the K=21 timeout horizon at 8h cadence ≈ 7 days; on higher-vol candidates more of the per-bar variance is consumed by intra-candle path-noise rather than directional resolution. RUNE's IS WR 30.4% (substantially below the 33.3% 2:1 ATR breakeven) is the clean signature: the asymmetric barrier ratio is mis-calibrated for the candidate's vol-magnitude regime.

**Kurtosis-tail axis**: candidate universe median ret_kurt_50 = 0.99–1.36 (RUNE lowest at 0.99); BCH/LDO/TRX = 1.09–1.83 (BCH highest at 1.83). The 14-feature stack's tail-event features (ret_kurt_50, ret_kurt_200, ret_skew_50, ret_skew_200, max_dd_window_50, range_realized_vol_50) are tuned on BCH's heavier-tail distribution; on flatter-tail candidates the importance allocation Optuna learns at IS becomes less discriminative. The 6 of 14 tail-risk features (43% of the stack) carry less signal load on flat-tail candidates — the model has reduced effective representational capacity for the new universe.

**Timeout-rate axis**: candidate triple-barrier timeout rates 2.8–4.6% vs incumbent 3.8–6.9% (T6 EDA). LOWER timeout rates on candidates indicate FASTER label resolution — which interacts adversely with the /116 no_confirm primitive (K=4 candle exit acceleration). If labels resolve faster intrinsically, the no_confirm RULE-layer's marginal benefit shrinks. The /121 baseline's IS lift over /059 (+0.22) was partially the no_confirm RULE-layer's contribution; that contribution is structurally smaller on a faster-resolving label population.

**The 3 axes converge into one finding**: the 14-feature stack + (2.0, 1.0)-ATR K=21 + 7-gate RiskV2 + /116 no_confirm + ENSEMBLE_SIZE=3 EXPLORATION budget is BCH/LDO/TRX-cohort-shaped — calibrated implicitly to the 85–168 bps per-bar magnitude regime + 1.09–1.83 kurtosis regime + 3.8–6.9% timeout-rate regime of the incumbent cohort. Pre-flight gates G1/G2/G3 (data-depth + ret_corr + ADF) are necessary but NOT sufficient for cross-cohort transfer — they say nothing about whether the trained model's implicit calibration on tail-event structure transfers. The IS MaxDD 82.97% is the diagnostic that this implicit calibration FAILED to transfer.

## 4. The universe-substitution axis closure — 8th attempt in v3 history

The /125 axis is the 8th universe-substitution attempt across v3 cycles 1–7, all NEGATIVE-or-NEUTRAL:

| # | Iter | Universe change | Verdict |
|---|------|-----------------|---------|
| 1 | /021 | +HBAR +AVAX (add 2) | NEGATIVE-clean |
| 2 | /069 | +ADA (add 1) | NEGATIVE-INERT |
| 3 | /078 | Replace LDO → ADA | SUSPICIOUS-OOS-DOMINANT (universe-swap factor-loading) |
| 4 | /083 | +FIL (add 1) | NEGATIVE-catastrophic |
| 5 | /087 | +GALA +MANA +SAND (wholesale 3→6) | NEGATIVE |
| 6 | /110-111 | CRV/AAVE/GRT/ADA (DeFi-cluster expansion) | NEGATIVE |
| 7 | /069 again | ADA-replace-LDO (re-attempt) | NEGATIVE-INERT |
| 8 | **/125** | **WHOLESALE ATOM/RUNE/UNI under LIFTED constraints with /121 baseline** | **NEGATIVE-catastrophic** |

/125 is the FIRST under LIFTED constraints with /121 baseline (no_confirm enabled) — the prior 7 were all under /059-anchored constraints. The differential is now isolated: the LIFTED-constraint + no_confirm-enabled regime ALSO does NOT generalize across cohorts. The universe-substitution axis is broadly CLOSED across all v3 history including the lifted-constraint regime.

The PRIOR-NOT-YET-TESTED conjunction the /125 brief Section 10.3 pre-registered — "wild universe ∧ never-V3_MODELS-bundled ∧ sector-diverse ∧ /121-anchored with no_confirm" — was the most permissive priors set v3 had tested. The conjunction FAILED. No combination of selection criteria under the 14-feature stack + (2.0, 1.0)-ATR K=21 + /121-Optuna-trajectory architecture has produced a new-universe PROMISING result.

## 5. Critic verdict summary

OVERALL = **EXPLORATION-NEGATIVE-catastrophic**. Zero clarifications raised (catastrophic verdict unambiguous via first-match-wins). 7 of 8 checks PASS + 1 N/A:

- **Check 1 (look-ahead)**: PASS. Feature pipeline `process_symbol_v3` symbol-agnostic; single axis is V3_MODELS tuple substitution; no new look-ahead surface. /058 walk-forward fix at `walk_forward.py:113` intact.
- **Check 2 (embargo)**: PASS. REQUIRED_GAP=66 unchanged from /121.
- **Check 3 (multiple-testing)**: SPLIT (FAIL informational for EXPLORATION). DSR=0.0 + PSR=0.7965 (below 0.95 gate) + PBO=0.1064 PASS + frac_positive_paths=0.4667 BELOW 0.55 floor (CPCV gate informational). The frac_positive_paths failure is the corroborating EXPLORATION-mode signal that the CPCV path distribution centered slightly negative.
- **Check 4 (IC)**: PASS by carry-forward. No new features.
- **Check 5 (ADF)**: PASS. T4 EDA showed 9/9 candidate-symbol × incumbent-feature pairs p < 1e-6.
- **Check 6 (Pareto)**: N/A (single-seed EXPLORATION).
- **Check 7 (reproducibility)**: PASS. Commit SHA `85f413b` stamped; ITERATION_LABEL v3-125; V3_MODELS verified at runner; PnL math spot-check clean.
- **Check 8 (alignment)**: PASS. V3_MODELS replacement implemented exactly per brief Section 3; 0% trade-roster overlap with /121 OOS roster (zero BCH/LDO/TRX in OOS trades — behavioral-effect predictor at Section 4.4 satisfied). Modal expectation NEGATIVE 50% prior + NEGATIVE-catastrophic 25% prior bucket; observed NEGATIVE-catastrophic — within prior distribution at the worse tail.

## 6. PATH classification

**NEGATIVE-catastrophic** per Section 8 first-match. IS Sharpe Δ −1.248 (>3× the −0.40 catastrophic-IS-collapse threshold) AND OOS Sharpe Δ −0.858 (>2× the −0.30 catastrophic-OOS-collapse threshold) — both legs trigger NEGATIVE-catastrophic with large margin. The CPCV frac_positive_paths failure at 0.4667 (below 0.55 floor) is the corroborating signal that the CPCV path distribution centered slightly negative (q50 = −0.137; q25 = −1.054); the PSR drop /121 1.0 → /125 0.7965 corroborates the catastrophic verdict but stays above the 0.5 floor on observed Sharpe distribution.

F1 (IS catastrophe) + F2 (1-symbol carrier) + F3 (cross-cohort transfer failure) + F6 (IS MaxDD breach 50%) all TRIGGERED. F4 (OOS-spike SUSPICIOUS) NOT triggered (OOS Sharpe +0.11 well below the +0.30 OOS-positive threshold for SUSPICIOUS classification). F5 (single-candidate breakthrough PROMISING-PARTIAL) NOT triggered (ATOM IS +72% qualifies on PnL Δ, but the broader Section 6 PROMISING gate requires OOS Δ > +3pp at the carrier; ATOM OOS Δ vs zero +22% qualifies in isolation but the universe-aggregate OOS Δ is −0.86 vs /121, dominating).

## 7. Hypothesis check and process notes

### 7.1 Hypothesis falsified

Brief Section 1 hypothesis: "Wholesale replacing V3_MODELS BCH/LDO/TRX with the structurally-distinct ATOM/RUNE/UNI universe at 8h cadence (anchored against /121 with /116 no_confirm enabled) carries differentiable directional signal beyond the saturated incumbent distribution." **FALSIFIED.** The wild universe under the LIFTED-constraint regime with no_confirm enabled does NOT generalize the /121 baseline edge — IS Sharpe collapses to +0.06 with MaxDD 82.97% (architecture-distribution mismatch, not signal absence on the candidates).

The wide prediction band (IS Δ [−0.30, +0.30] / OOS Δ [−0.30, +0.40]) was BREACHED on the IS lower bound by −0.95 and the OOS lower bound by −0.56. Future universe-substitution axes (if any are revisited under genuinely different architecture conditions) should pre-register an envelope of IS Δ [−1.50, +0.40] / OOS Δ [−1.00, +0.50] reflecting the 8-attempt evidence base.

### 7.2 Process note — run.log missing (recurrence)

Same anomaly as /124: engineering report Section Headers notes `Wall-clock time: not logged (run.log absent; report written from output artefacts)`. /124 and /125 are the second and third consecutive iterations with missing run.log. Engineering proceeded from `comparison.csv` + `dsr.json` + `ensemble_summary.json` + IS/OOS trade-level artefacts which were complete. No methodology impact. Memory note for future iterations: confirm `run.log` is written at backtest start before clean-up; investigate why the writer is not firing.

## 8. BASELINE_V3.md status

UNCHANGED — /121 stays canonical at `v0.v3-121` (IS +1.3108 / OOS +0.9682). Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean). /125 is EXPLORATION-class (not CONFIRMATION) AND was NEGATIVE-catastrophic on both legs — no baseline update is even logically eligible.

## 9. Next-iteration ideas — /126 multi-frequency feature stack (per Critic PRIMARY recommendation)

Per /125 Critic FINAL `53cfc06` PRIMARY recommendation: pivot /126 to **multi-frequency feature stack — 8h base candles + 24h-aggregated features at the feature-stack layer**. This is a NEW dimension in v3 catalog (FEATURE-CADENCE-STACK at fixed label horizon), structurally distinct from the /117 24h-base candle frequency axis (CANDLE-FREQUENCY at fixed feature stack — different axis class) and from the /124 K=63 longer-cadence labels axis (LABEL-DURATION at fixed base cadence — also different axis class).

**Universe**: REVERT to /121 baseline BCH/LDO/TRX. This isolates the multi-frequency axis from the /125 wild-universe confound — the per-symbol feature pipeline is identical to /121 with a 24h-aggregated overlay; the comparison is anchored against the same 14-feature stack on the same universe.

**Architecture state at /126 entry**: KEEP /121 architecture (14-feature 8h stack + ATR (2.0, 1.0) + K=21 + /116 no_confirm + REQUIRED_GAP=66 + ENSEMBLE_SIZE=3 EXPLORATION). ADD specific 24h-aggregated features (per /126 EDA per `feedback_v3_axis_selection_quant_discipline.md`).

**Why this axis**: per `feedback_v3_structural_over_knob_exploration.md` — NEW feature families rank above universe substitution and gate-threshold knobs. No prior /124-equivalent precedent in cycle-7 axis menu. The /113 cycle-6 daily-feature EXPLORATION found that some daily-feature primitives carry standalone permutation-validated signal (T5 walk-forward AUC 0.5275 p=0.00) but the FULL 8-feature stack washed in the 22-feature combined stack — suggesting a single carefully-selected 24h feature on top of the 14-feature 8h baseline at /121 anchor (not /113's /059 anchor) is the genuinely-new variant. EDA at /126 must enforce the tightened IC < 0.40 pairwise gate (per /122 RECURRENCE refinement) against the 14-feature 8h incumbents — at least 3 of the 8 /113 daily features had IC > 0.70 with incumbents and are banned candidates.

**Cycle-7 cadence**: slot 4/10 EXPLORATION done (this iteration). 6 EXPLORATIONs remain + /132 CONFIRMATION.

---

**Catalog entry appended** to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/125 | 2026-05-21 | WILD V3_MODELS ATOM/RUNE/UNI (constraints lifted) | -1.2476 | -0.8578 | EXPLORATION-NEGATIVE-catastrophic — 8th universe substitution failure | NO |
```

**Tag**: `v0.v3-125`. Does NOT supersede `v0.v3-121` as canonical.

**Memory updates**: APPEND cycle-7 slot 4 NEGATIVE-catastrophic + lifted-constraints status to `project_v3_cycle7_setup.md`; NEW feedback file `feedback_v3_architecture_cohort_shaped.md` documenting that the 14-feature stack + (2.0, 1.0)-ATR K=21 calibration is BCH/LDO/TRX-cohort-shaped and does not transfer cleanly to symbols with different vol-magnitude + kurtosis profiles.
