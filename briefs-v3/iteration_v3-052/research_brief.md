# Iteration v3-052 — Research Brief (regime_momentum_signed_3d UNIVERSAL SWAP)

**Type**: EXPLORATION (Cycle 4 #2 of 10)
**Track**: v3 (rigor arm) — fifty-second iteration
**Branch**: `iteration-v3/052` (off iter-v3/051 head at SHA `87f3c93`)
**Date**: 2026-05-11
**Author**: QR (autopilot)

**PIVOT NOTICE**: This brief is a PIVOT from the previous orchestrator-mandated axis (LDO removal + fracdiff drop). Per `feedback_v3_axis_selection_quant_discipline.md`, the orchestrator may not commit axis setup without QR EDA backing. The /052 EDA at SHA `0a10581` REVEALED that the orchestrator premise ("LDO IS PnL share -14.96%") misread `net_pnl_pct` instead of `weighted_pnl`. On the Sharpe-relevant metric, **LDO is an IS CONTRIBUTOR at /051 (+11.155 weighted_pnl, +36.78% bundle share)**. 2-sym counterfactual triggers PATH C-suspicious (IS-OOS daily ratio 3.58 out-of-band) — structurally identical to the per-symbol customization anti-pattern. **QR EDA supersedes orchestrator pick.** Section 10 audit trail documents the supersession. PIVOTED axis = `regime_momentum_signed_3d` at universal scope, EDA-validated per `analysis/iteration_v3-051/` SHA `290f37b` RANKED #2 queued for /052.

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default (per `feedback_v3_exploration_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/052 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #2 of 10 (second EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)

Carry-forward state (UNCHANGED from iter-v3/051 head):
  - V3_FEATURE_COLUMNS_TOP_N at /051 HEAD = 15 features (incl. fracdiff_d05_close)
  - V3_MODELS at /051 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED at /052)
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty per /051 system-level REVERT; UNCHANGED at /052)
  - block_long_for = () (empty per /051 system-level REVERT; UNCHANGED at /052)
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient; UNCHANGED at /052)
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
  - adx_threshold_per_symbol = {} (empty)
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /051 HEAD = 66 = (21+1)×3 (UNCHANGED at /052 — universe unchanged)

SINGLE-AXIS SWAP for /052 (QR-EDA-backed pivot per `feedback_v3_axis_selection_quant_discipline.md`):
  AXIS: SWAP fracdiff_d05_close → regime_momentum_signed_3d in V3_FEATURE_COLUMNS_TOP_N
    (DROP fracdiff_d05_close as 15th element; ADD regime_momentum_signed_3d as 15th element)
    Mechanism: ret_3d × sign(hurst_100 − 0.5) — orthogonal time-scale variant of the
                iter-v3/028 edge ingredient regime_momentum_signed_5d (sister composed feature).
    Net effect: V3_FEATURE_COLUMNS_TOP_N stays at 15 features; fracdiff PARKED, 3d ACTIVATED.

Setup commit changes (locked in §3):
  - src/crypto_trade/features_v3/engineered_v3.py: ACTIVATE regime_momentum_signed_3d dispatch
    in add_engineered_v3_features (add 1 line after compute_regime_momentum_signed_5d call)
  - src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N = 15 (SWAP 15th element:
    fracdiff_d05_close → regime_momentum_signed_3d)
  - REGENERATE feature parquets for 4 symbols (BCH, LDO, TRX, ALGO; ALGO available but not in
    V3_MODELS at /052) via `uv run crypto-trade features --track v3 --interval 8h --symbols
    BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT --format parquet --workers 4`
  - run_baseline_v3.py:_verify_feature_columns updated (assert 15 with regime_momentum_signed_3d
    present; assert fracdiff_d05_close NOT present)
  - run_baseline_v3.py:ITERATION_LABEL = "v3-052"
  - V3_MODELS, REQUIRED_GAP, V3_ATR_MULTIPLIERS_PER_SYMBOL, block_long_for: UNCHANGED from /051
  - compute_fracdiff_d05_close + 5 adversarial tests RETAINED as dead-code (zero revert cost;
    feature column dropped but compute function preserved per /051 PARKED status)
  - compute_regime_momentum_signed_3d: ACTIVATED (was dead code at engineered_v3.py:330);
    dispatch line added in add_engineered_v3_features

Predicted classification (locked in §7):
  - PATH A (PROMISING-clean): 25% probability
  - PATH B (PROMISING-INERT): 30%
  - PATH C-clean (NEGATIVE-clean): 20%
  - PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS): 10%
  - PATH D (EXPLORATION-NULL-RESULT, per Critic FINAL `32cc46f` rec #3): 15%
```

**Context**: iter-v3/051 EXPLORATION-NULL-RESULT closeout per Critic FINAL `32cc46f`. fracdiff_d05_close at universal scope was LEARNED (ranks 11-12/15) but produced NO IS lift; OOS lift +0.08 within single-seed=42 lottery noise. The /051 closeout originally identified LDO removal investigation as the cycle 4 #2 HIGH-priority axis. The QR EDA at SHA `0a10581` (committed prior to this brief) revealed the orchestrator premise (LDO IS PnL share -14.96%) misread `net_pnl_pct` (sums per-trade raw % returns; ignores weight_factor) vs `weighted_pnl` (the Sharpe-relevant metric). LDO is an IS CONTRIBUTOR at /051 (+11.155 weighted_pnl, +36.78% bundle share), and 2-sym counterfactual triggers PATH C-suspicious (IS-OOS daily ratio 3.58 OUT-OF-BAND) — structurally identical to per-symbol customization anti-pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`).

**Per `feedback_v3_axis_selection_quant_discipline.md` rule 4 ("QR Audit Trail section added when orchestrator's original axis pick is superseded"), the QR EDA supersedes the orchestrator pick.** The PIVOTED axis = `regime_momentum_signed_3d` at universal scope (SWAP with fracdiff_d05_close in V3_FEATURE_COLUMNS_TOP_N; net count stays 15). This axis is EDA-validated per /051 RANKED #2 queued for /052 (`analysis/iteration_v3-051/synthesis.md` SHA `290f37b`):

- ADF stationary p=0 across all 4 symbols (axis_c_regime_3d_adf.csv)
- Max |IC| = 0.6192 (BCH vs vwap_dev_20) < 0.70 strict gate — NO carve-out needed (CLEANER than fracdiff which needed Category-2 source-primitive carve-out at LDO 0.7381)
- Univariate Spearman significant at ALL 4 symbols (BCH ρ=-0.058 p=1e-5; LDO ρ=-0.044 p=0.024; TRX ρ=-0.068 p=4e-12; ALGO ρ=-0.058 p=3e-5); mean ρ -0.057 = STRONGER mean-reversion signal than fracdiff (mean ρ -0.044)
- IC with sister feature regime_momentum_signed_5d: 0.4683 at BCH (moderate; below 0.50 stacking-risk threshold per `feedback_v3_engineered_features_dont_stack.md` precedent at iter-v3/026)
- /044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+/052 (3-sym BCH+LDO+TRX). The /044 EDA target (ALGO LONG WR 18.2% IS / 11.1% OOS) does NOT apply to the cycle 4 starting baseline.
- compute_regime_momentum_signed_3d already exists as dead code (engineered_v3.py:330-376; reactivation cost: 1 dispatch line + parquet regen)
- Per `feedback_v3_engineered_features_proven.md`: composed engineered features CAN work at universal scope (iter-v3/025 PROMISING + iter-v3/028 CONFIRMATION-MERGE precedent — SAME COMPOSED FEATURE FAMILY as regime_momentum_signed_5d, which IS the iter-v3/028 baseline edge ingredient)

iter-v3/052 = cycle 4 #2 of 10 EXPLORATIONs (per `feedback_v3_strict_10_to_1_cadence.md`). iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first; do NOT collapse 10th EXPLORATION).

---

## Section 1 — Hypothesis

ADDING `regime_momentum_signed_3d` to V3_FEATURE_COLUMNS_TOP_N at universal scope (SWAP with fracdiff_d05_close; net count stays 15) — alongside the system-level REVERT carry-forward (V3_MODELS = 3-sym BCH+LDO+TRX, V3_ATR_MULTIPLIERS_PER_SYMBOL = {}, block_long_for = (), REQUIRED_GAP = 66) — investigates whether the orthogonal time-scale variant of the iter-v3/028 edge ingredient regime_momentum_signed_5d captures shorter-horizon (3-bar = 1-day at 8h cadence) regime persistence that the 5-bar variant misses, lifting bundle IS Sharpe vs iter-v3/028 baseline reference +0.5101 while preserving OOS Sharpe ≥ +0.5053.

**Predicted single-seed result (per QR EDA at SHA `290f37b`, axis_c_regime_3d_* CSVs):**
- Bundle IS Sharpe: predicted band [+0.40, +0.75] (mean +0.58); Δ vs /028 anchor +0.5101: **[-0.10, +0.25]** (lift small to moderate). Rationale: stationary feature with stronger univariate signal than fracdiff (mean ρ -0.057 vs -0.044), all 4 symbols significant; tree models can use it for split decisions in regions where regime_momentum_signed_5d's 5-bar lookback misses faster regime transitions (BCH+LDO+TRX are mid-cap symbols where 3-bar = 1-day regime cycles are more frequent than 5-day cycles).
- Bundle OOS Sharpe: predicted band [+0.25, +0.85] (mean +0.55); Δ vs /028 anchor +0.5053: **[-0.25, +0.35]** (uncertain; Optuna response uncertainty at single-seed n_trials=35).
- IS-OOS daily Sharpe ratio: predicted ∈ [0.5, 2.0] band (clean lift, not suspicious — falsifier band per `feedback_v3_engineered_features_dont_stack.md`).
- IS trade count: predicted band [130, 200] (Δ -25% to +12% vs /051's 178). Mechanism: stationary mean-reversion feature with negative univariate ρ may TIGHTEN the model's signal threshold (fewer marginal trades) OR LOOSEN it (the feature provides additional differentiation enabling new trades). Direction uncertain at single-seed.
- OOS trade count: predicted band [75, 115] (Δ -22% to +19% vs /051's 96).
- regime_momentum_signed_3d importance rank: predicted top-10 in at least 1 of 3 symbols (per iter-v3/028 precedent where regime_momentum_signed_5d is rank 11-14/14 across multi-seed but still ESSENTIAL — the proven mandate per `feedback_v3_engineered_features_proven.md`).

This axis directly addresses the cycle 4 starting hypothesis: "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)" (per iter-v3/050 diary §Cadence). The 3d variant is a NEW universal engineered feature in the SAME proven family as the iter-v3/028 baseline edge ingredient (regime_momentum_signed_5d — multi-seed validated).

---

## Section 2 — IS-Only Numerical Evidence

**Primary EDA evidence sourced from committed `analysis/iteration_v3-051/axis_c_regime_3d_*.csv` (SHA `290f37b`), produced by `axis_c_regime_3d_compute.py` on-the-fly from `close` + `hurst_100` primitives in feature parquets.**

**Secondary evidence sourced from `analysis/iteration_v3-052/ldo_removal_eda.py` (SHA `0a10581`), documenting why the orchestrator's LDO-removal mandate was superseded.**

### 2.1 — regime_momentum_signed_3d ADF stationarity (axis_c_regime_3d_adf.csv)

| Symbol | n_is_obs | ADF p-value | Stationary at p<0.05 |
|---|---:|---:|---|
| BCHUSDT | 5628 | 0.0 | **TRUE** |
| LDOUSDT | 2642 | 0.0 | **TRUE** |
| TRXUSDT | 5570 | 0.0 | **TRUE** |
| ALGOUSDT | 5126 | 0.0 | **TRUE** |

**ALL 4 SYMBOLS STATIONARY at p<0.05.** The sign-flip composition (`ret_3d × sign(hurst_100 − 0.5)`) is structurally stationary because both factors are stationary: `ret_3d` is a 3-bar log-return (stationary by construction), and `sign(hurst_100 − 0.5)` is a bounded {-1, 0, +1} indicator. ADF p-values are all rounded to 0 by statsmodels (extremely strong rejection of the unit-root null).

### 2.2 — regime_momentum_signed_3d Information Coefficient (axis_c_regime_3d_ic.csv) — STRICT GATE PASS

Max |IC| (Pearson) of `regime_momentum_signed_3d` vs each existing 14-feature column, per symbol:

| Symbol | max \|IC\| | with feature | source_primitive? |
|---|---:|---|---|
| BCHUSDT | **0.6192** | vwap_dev_20 | NO |
| LDOUSDT | **0.6139** | vwap_dev_20 | NO |
| TRXUSDT | **0.5181** | vwap_dev_20 | NO |
| ALGOUSDT | **0.5970** | vwap_dev_20 | NO |

**ALL POST-STRICT-GATE PASS**: max |IC| = 0.6192 < 0.70 strict gate (NO carve-out needed). Comparison vs fracdiff_d05_close which required Category-2 carve-out at LDO 0.7381 (with vwap_dev_20 source primitive).

**IC with sister feature `regime_momentum_signed_5d`** (stacking-risk diagnostic per `feedback_v3_engineered_features_dont_stack.md`):
- BCH: 0.4683 (moderate; below 0.50 stacking-risk threshold from iter-v3/026 anti-pattern)
- LDO: 0.4271 (lower than BCH; less redundant)
- TRX: 0.4497 (moderate)
- ALGO: 0.4657 (moderate)

The 3d ↔ 5d correlation is moderate-not-redundant. Adding 3d alongside 5d at single-seed n_trials=35 carries documented stacking risk (iter-v3/026 IS collapse 0.05 + OOS spike +1.45 = 27× ratio anti-pattern), BUT:
- The iter-v3/026 stacking was 2 DIFFERENT engineered features (regime_momentum + vol_adj_autocorr), not orthogonal time-scale variants of the same composition.
- IC at 0.43-0.47 is well BELOW the 0.65+ range where high redundancy distorts colsample picks.
- 3d and 5d differ in time-scale (1-day vs 5-day at 8h cadence) — they target different regime persistence horizons, not the same signal at the same scale.

### 2.3 — regime_momentum_signed_3d Univariate Spearman (axis_c_regime_3d_univariate.csv) — STRONGER THAN FRACDIFF

Univariate Spearman ρ of `regime_momentum_signed_3d` vs forward 1-bar return per symbol:

| Symbol | n_obs | spearman_ρ | p-value | Significant at p<0.05 |
|---|---:|---:|---:|---|
| BCHUSDT | 5627 | **−0.058** | 1e-05 | **TRUE** |
| LDOUSDT | 2641 | **−0.044** | 0.024 | **TRUE** |
| TRXUSDT | 5569 | **−0.068** | 4e-12 | **TRUE** (strongest) |
| ALGOUSDT | 5125 | **−0.058** | 3e-05 | **TRUE** |

**ALL 4 SYMBOLS SIGNIFICANT** at p<0.05 with negative ρ (mean-reversion signal). Effect sizes consistent across symbols (ρ range -0.044 to -0.068).

Comparison to fracdiff_d05_close (iter-v3/051 baseline feature, PARKED at /052 SWAP):

| Symbol | fracdiff_d05_close ρ | regime_momentum_signed_3d ρ | Stronger? |
|---|---:|---:|---|
| BCHUSDT | -0.038 | **-0.058** | 3d |
| LDOUSDT | -0.051 | -0.044 | fracdiff (marginal) |
| TRXUSDT | -0.050 | **-0.068** | 3d |
| ALGOUSDT | -0.038 | **-0.058** | 3d |
| **Mean** | **-0.044** | **-0.057** | **3d STRONGER** |

The 3d variant has a stronger univariate signal than fracdiff on 3 of 4 symbols. Per `feedback_v3_axis_selection_quant_discipline.md`, univariate Spearman is the WEAKEST evidence type (warning from iter-v3/070 failure mode); used here as a comparative sanity check, NOT as primary justification. The primary justification is (1) stationarity, (2) IC strict-gate PASS (no carve-out), (3) cycle 4 axis priority alignment, (4) proven family precedent (regime_momentum_signed_5d at iter-v3/028 multi-seed CONFIRMATION-MERGE).

### 2.4 — Why fracdiff was DROPPED and 3d ADDED (the SWAP rationale)

iter-v3/051 fracdiff_d05_close ranked 11-13/15 across BCH/LDO/TRX (feature LEARNED, low importance):

| Symbol | fracdiff rank | Total features |
|---|---:|---:|
| BCHUSDT | 11/15 | 15 |
| LDOUSDT | 12/15 | 15 |
| TRXUSDT | 13/15 | 15 |

The /051 EXPLORATION-NULL-RESULT verdict was PARKED, not CLOSED — feature LEARNED but no decisive IS lift; OOS lift within single-seed lottery noise. Per Critic FINAL `32cc46f` rec #2: DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N at /052 setup (15 → 14). Retain compute function + tests at zero revert cost.

The PIVOT axis ADDS regime_momentum_signed_3d in fracdiff's place (15 → 14 from fracdiff DROP, then 14 → 15 from 3d ADD). Net V3_FEATURE_COLUMNS_TOP_N count: **15 features (UNCHANGED)**. The SWAP isolates the 3d-vs-fracdiff comparison cleanly: same feature count, same Optuna budget, same 14 base features, only the 15th slot changes.

### 2.5 — /044 ALGO LONG falsification is CONDITIONAL on ALGO universe

The iter-v3/044 QR EDA at SHA `eff841e` (cycle3_is_diagnosis.py) falsified regime_momentum_signed_3d on the grounds that "regime_momentum_signed_3d does NOT discriminate ALGO LONG WR (22.2% > 0, 13.3% <=0)" and that ALGO LONG was the single largest IS attribution loss (-53.26 PnL, 33 trades, 18.2% IS WR / 11.1% OOS WR).

**This falsification is CONDITIONAL on ALGO being in V3_MODELS.** At iter-v3/051+ (post-system-level REVERT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`), V3_MODELS = 3-sym BCH+LDO+TRX (ALGO REVERTED). The /044 target symbol is absent. The /044 falsification does NOT apply to the cycle 4 starting baseline.

| Iteration | V3_MODELS | /044 falsification applies? |
|---|---|---|
| iter-v3/044 | 4-sym (BCH/LDO/TRX/ALGO) | YES — ALGO LONG bottleneck in universe |
| iter-v3/051 | 3-sym (BCH/LDO/TRX) | NO — ALGO REVERTED out |
| iter-v3/052 | 3-sym (BCH/LDO/TRX) | NO — ALGO REVERTED out |

The /051 EDA at SHA `290f37b` (synthesis.md §c3) explicitly registered this conditional: *"iter-v3/044 QR EDA FALSIFIED 3d at the IS-axis bottleneck symbol... However ALGO is REVERTED at iter-v3/051 (3-sym universe), so this falsification may not apply at the cycle 4 starting baseline."*

The /052 PIVOT activates the 3d variant at the universe where the falsification does NOT apply.

### 2.6 — Why LDO removal was REJECTED (orchestrator pick PRE-FALSIFIED by /052 QR EDA)

The orchestrator-proposed axis for /052 was LDO removal + fracdiff drop. The QR EDA at SHA `0a10581` (`analysis/iteration_v3-052/ldo_removal_eda.py` + 7 CSVs) revealed:

- Orchestrator's "LDO IS PnL share -14.96%" reading sourced `net_pnl_pct` (sums per-trade raw % returns; IGNORES weight_factor). The Sharpe-relevant metric is `weighted_pnl` (weight_factor × pnl_pct).
- LDO actual weighted_pnl at /051 IS: **+11.155** = +36.78% bundle share (CONTRIBUTOR, not drag).
- LDO actual weighted_pnl at /051 OOS: -17.44 = -100.08% bundle share (CONFIRMED drag).
- 2-sym BCH+TRX counterfactual (drop all LDO trades, recompute Sharpe):

| Scenario | IS Sharpe | OOS Sharpe | IS-OOS daily ratio |
|---|---:|---:|---:|
| 3-sym /051 actual | +0.4571 | +0.5890 | 1.06 (in-band) |
| 2-sym counterfactual | +0.2960 | +1.6030 | **3.58 (OUT-OF-BAND)** |
| **Δ** | **−0.1611** | **+1.0139** | — |

LDO removal: IS Δ -0.16 (BREAKS BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md`); IS-OOS daily ratio 3.58 OUT-OF-BAND (PATH C-suspicious anti-pattern per `feedback_v3_engineered_features_dont_stack.md`). Structurally identical to per-symbol customization anti-pattern at universe-composition level.

**LDO removal axis PRE-FALSIFIED at EDA stage** — would consume a cycle 4 EXPLORATION slot to mechanically re-confirm an anti-pattern. The QR EDA supersedes the orchestrator pick per `feedback_v3_axis_selection_quant_discipline.md` rule 4. Section 10 documents the full audit trail.

### 2.7 — Conclusion of §2 (PIVOT BASIS)

regime_momentum_signed_3d at universal scope is EDA-validated for /052 cycle 4 #2 axis:

- **ADF stationary at p<0.05 across all 4 symbols** (axis_c_regime_3d_adf.csv)
- **IC strict-gate PASS** (max |IC| = 0.6192 < 0.70; NO carve-out needed — cleaner than fracdiff)
- **Univariate ρ significant at all 4 symbols** (mean ρ -0.057; stronger than fracdiff -0.044)
- **IC with sister 5d feature 0.43-0.47** (below stacking-risk threshold)
- **/044 ALGO LONG falsification CONDITIONAL on ALGO universe**; does NOT apply to 3-sym /051+/052 universe
- **compute function dead code at engineered_v3.py:330-376** (1-line dispatch reactivation + parquet regen)
- **Same proven family as iter-v3/028 baseline edge ingredient** regime_momentum_signed_5d (composed engineered feature; multi-seed CONFIRMATION-MERGE)
- **Cycle 4 HIGH-priority axis** per `feedback_v3_structural_over_knob_exploration.md` (NEW universal engineered feature)

Pre-registration in §7-§8 sets PATH B (PROMISING-INERT) as most likely (30%) and PATH A (PROMISING-clean) as second-most-likely (25%). PATH C-suspicious is now unlikely (10%) — the EDA evidence does NOT predict the OOS-only artifact that the LDO removal axis predicted. Section 10 audit trail documents the orchestrator-supersession.

<!-- DEPRECATED ORCHESTRATOR-PICK SECTIONS BELOW (LDO removal pre-falsified) — retained for audit trail visibility. The /052 axis SWAPPED to regime_momentum_signed_3d per QR EDA. -->

### 2.8 — Appendix: LDO removal axis pre-falsification (orchestrator-pick supersession audit)

Per `feedback_v3_axis_selection_quant_discipline.md` rule 4 (QR Audit Trail when orchestrator pick superseded), the original orchestrator-mandated axis (LDO removal + fracdiff drop) was pre-falsified at EDA stage. Full evidence in `analysis/iteration_v3-052/ldo_removal_eda.py` SHA `0a10581` + 7 CSV outputs + synthesis.md. Summary:

**A. Metric error correction.** Orchestrator premise "LDO IS PnL share -14.96%" sourced `per_symbol.csv:net_pnl_pct` (sums per-trade raw % returns; IGNORES `weight_factor`). Bundle Sharpe is driven by `weighted_pnl` (= weight_factor × pnl_pct).

| Window | LDO trades (wf>0) | LDO weighted_pnl | wpnl share | LDO WR |
|---|---:|---:|---:|---:|
| IS | 9 of 11 raw | **+11.155** | **+36.78%** | 33.3% |
| OOS | 13 of 13 raw | **−17.44** | **−100.08%** | 23.1% |

LDO is an IS CONTRIBUTOR (+36.78% bundle share, dominated by 3 large take-profit exits) and an OOS drag (-100.08% share, 10 SLs vs 3 TPs).

**B. 2-sym counterfactual.** Drop LDO trades from /051 roster, recompute Sharpe (multi_axis_eda methodology):

| Scenario | IS Sharpe | OOS Sharpe | IS-OOS daily ratio |
|---|---:|---:|---:|
| 3-sym /051 actual | +0.4571 | +0.5890 | 1.06 (in-band) |
| 2-sym (no LDO) | +0.2960 | +1.6030 | **3.58 (OUT-OF-BAND)** |
| **Δ** | **−0.1611** | **+1.0139** | — |

LDO removal: IS Δ **−0.16** (BREAKS BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md`); IS-OOS daily ratio **3.58 OUT-OF-BAND** (PATH C-suspicious per `feedback_v3_engineered_features_dont_stack.md`). Structurally identical to per-symbol customization anti-pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) applied at universe-composition level.

**C. Cross-iteration LDO pattern.** LDO IS wpnl is POSITIVE at every config since /028 baseline (+5.02 /028 multi-seed; +43.90 /045 single-seed lottery; +0.85 /047-/050; +11.155 /051). LDO OOS wpnl is consistently negative at single-seed=42 (-19.13 /047-/050 frozen baseline; -17.44 /051; -22.05 /028 multi-seed). The OOS drag is direction-asymmetric (11 of 13 OOS trades are SHORTs; 9 of those 11 SLed). 2025-Q3 declining-LDO regime concentrates losses.

**D. LDO data extent.** LDO has 42.9% less IS data than BCH/TRX (30.1 months vs 62.8 months). Structural reason for OOS regression; insufficient cause to justify removing IS contribution. 

**Pre-falsification consequences (per `feedback_v3_axis_selection_quant_discipline.md`):**
- LDO removal would consume a cycle 4 EXPLORATION slot to mechanically re-confirm the IS-OOS PATH C-suspicious anti-pattern at the universe-composition level.
- The expected outcome (IS Δ -0.16, OOS Δ +1.01, ratio 3.58) provides ZERO learning signal beyond confirming the anti-pattern; the result is determined by the EDA roster counterfactual.
- The QR EDA at SHA `0a10581` supersedes the orchestrator pick. PIVOT to `regime_momentum_signed_3d` UNIVERSAL (§§2.1-2.7) per /051 EDA RANKED #2 queued for /052.

(LDO removal axis QUEUED for re-evaluation at multi-seed CONFIRMATION as a structural distinct test where single-seed lottery artifacts dissolve. NOT a /052-/060 cycle 4 EXPLORATION slot.)

---

## Section 3 — Proposed Changes

### 3.1 — Setup commit (single-axis SWAP: regime_momentum_signed_3d ↔ fracdiff_d05_close)

1. **`src/crypto_trade/features_v3/engineered_v3.py:add_engineered_v3_features`** — ACTIVATE `regime_momentum_signed_3d` dispatch
   ```python
   def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
       df = compute_regime_momentum_signed_5d(df)
       # iter-v3/052: ACTIVATE regime_momentum_signed_3d dispatch (was dead code at L330).
       # SWAP with fracdiff_d05_close in V3_FEATURE_COLUMNS_TOP_N (15th element).
       # QR EDA at SHA `290f37b` /051 EDA RANKED #2 queued for /052:
       #   - ADF stationary all 4 syms (p=0); IC strict-gate PASS (max |IC| 0.6192 < 0.70)
       #   - Univariate ρ significant all 4 syms (mean -0.057; stronger than fracdiff -0.044)
       #   - IC with 5d sister 0.43-0.47 (below stacking-risk 0.50 threshold)
       #   - /044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+
       # Per `feedback_v3_engineered_features_proven.md`: composed engineered features CAN
       # work at universal scope (iter-v3/025 + /028 precedent — SAME COMPOSED FEATURE FAMILY).
       df["regime_momentum_signed_3d"] = compute_regime_momentum_signed_3d(df)
       df = compute_fracdiff_d05_close(df)  # KEPT in dispatch; dropped from V3_FEATURE_COLUMNS_TOP_N
       df = compute_cross_asset_divergence_norm(df)
       df = compute_vol_normalized_ret_5d(df)
       return df
   ```
   Per `feedback_v3_axis_selection_quant_discipline.md` rule 4, this PIVOT supersedes the
   orchestrator's LDO-removal pick. EDA backing committed at SHA `290f37b` (/051 EDA) and
   SHA `0a10581` (/052 LDO supersession EDA). Section 10 QR Audit Trail documents the
   supersession.

2. **`src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N`** — SWAP 15th element
   ```python
   V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
       "max_dd_window_50",
       "ema_spread_atr_20",
       "ret_kurt_50",
       "ret_skew_200",
       "range_realized_vol_50",
       "hurst_diff_100_50",
       "ret_kurt_200",
       "hurst_100",
       "btc_ret_14d",
       "ret_skew_50",
       "vwap_dev_20",
       "ret_autocorr_lag1_50",
       "sym_vs_btc_ret_7d",
       "regime_momentum_signed_5d",
       # iter-v3/052: SWAP — regime_momentum_signed_3d REPLACES fracdiff_d05_close as 15th element.
       # PIVOT from orchestrator-mandated LDO removal axis (pre-falsified by /052 EDA SHA 0a10581).
       # QR-EDA-backed per /051 EDA RANKED #2 queued for /052 (SHA 290f37b synthesis.md §c3).
       # Mechanism: ret_3d × sign(hurst_100 - 0.5). Orthogonal time-scale variant of
       # regime_momentum_signed_5d (iter-v3/028 baseline edge ingredient; multi-seed validated).
       # Compute function reactivated from dead code (engineered_v3.py:330-376).
       # fracdiff_d05_close PARKED per /051 closeout (LEARNED ranks 11-13/15 but no IS lift);
       # compute_fracdiff_d05_close retained in dispatch as inert column (zero revert cost).
       # 5 adversarial tests in tests/features_v3/test_fracdiff_d05_universal.py RETAINED.
       "regime_momentum_signed_3d",
   )
   """Top-15 feature subset (as of iter-v3/052): SWAP — fracdiff_d05_close DROPPED;
   regime_momentum_signed_3d ADDED as 15th element. PIVOT from orchestrator's LDO-removal
   axis (pre-falsified by /052 EDA SHA 0a10581) to QR-EDA-backed NEW universal engineered
   feature axis (/051 EDA SHA 290f37b synthesis.md §c3 RANKED #2)."""
   ```

3. **`run_baseline_v3.py:V3_MODELS`** — UNCHANGED from /051 head
   ```python
   V3_MODELS: tuple[tuple[str, str], ...] = (
       ("BCHUSDT", "8h"),
       ("LDOUSDT", "8h"),
       ("TRXUSDT", "8h"),
       # iter-v3/051 system-level REVERT to /028 baseline 3-sym universe (UNCHANGED at /052).
       # LDO REMOVAL axis PRE-FALSIFIED by /052 EDA SHA 0a10581 (IS Δ -0.16 BREAKS gate;
       # IS-OOS daily ratio 3.58 OUT-OF-BAND = PATH C-suspicious anti-pattern).
   )
   ```

4. **`src/crypto_trade/strategies/ml/validation_v3.py:REQUIRED_GAP`** — UNCHANGED from /051
   ```python
   REQUIRED_GAP = 66  # = (timeout_candles=21+1) × n_symbols=3 — UNCHANGED at /052
   ```

5. **REGENERATE feature parquets for 4 symbols** (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT — ALGO reserved-for-future re-inclusion):
   ```bash
   uv run crypto-trade features --track v3 --interval 8h \
     --symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT \
     --format parquet --workers 4
   ```
   Estimated runtime: ~5-10 min. Generates `regime_momentum_signed_3d` column in all 4 symbol parquets.

6. **`run_baseline_v3.py:_verify_feature_columns`** — UPDATE assertions
   - `n != 15` (UNCHANGED count from /051)
   - REMOVE assertion: `fracdiff_d05_close` MUST be present (was at /051 setup)
   - ADD assertion: `fracdiff_d05_close` MUST NOT be in V3_FEATURE_COLUMNS_TOP_N
   - ADD assertion: `regime_momentum_signed_3d` MUST be present
   - Keep all other assertions (regime_momentum_signed_5d preservation, sym_vs_btc_ret_7d, ret_skew_50)

7. **`run_baseline_v3.py:_verify_v3_models`** — UNCHANGED from /051 (3-sym universe assertion)

8. **`run_baseline_v3.py:_verify_required_gap`** — UNCHANGED from /051 (REQUIRED_GAP == 66)

9. **`run_baseline_v3.py:ITERATION_LABEL`** = `"v3-052"`

10. **`run_baseline_v3.py`** — Update banner comment block describing iter-v3/052 SWAP axis

### 3.2 — Tests

- `tests/features_v3/test_fracdiff_d05_universal.py` (5 adversarial tests from /051): RETAIN unchanged. They serve as dead-code regression coverage; fracdiff_d05_close still computed in dispatch but DROPPED from V3_FEATURE_COLUMNS_TOP_N.
- ADD `tests/features_v3/test_regime_momentum_signed_3d_universal.py` (5 NEW adversarial tests):
  - test_regime_momentum_signed_3d_in_universal_feature_list
  - test_regime_momentum_signed_3d_present_in_all_4_symbol_parquets (BCH/LDO/TRX/ALGO)
  - test_regime_momentum_signed_3d_stationary_per_symbol (ADF p<0.05 across all 4 syms)
  - test_regime_momentum_signed_3d_no_lookahead (uses past-only data; shift(1) + shift(4) verified)
  - test_v3_feature_columns_top_n_swap_fracdiff_to_3d_at_iter_v3_052
- The 5d sister feature (`regime_momentum_signed_5d`) test coverage is UNCHANGED (no test file needed for sister; preserved from /028 baseline).

### 3.3 — Carry-forward state (UNCHANGED from /051 head)

- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED; LDO removal axis pre-falsified)
- REQUIRED_GAP = 66 (UNCHANGED; universe unchanged)
- regime_momentum_signed_5d PRESERVED in V3_FEATURE_COLUMNS_TOP_N (iter-v3/028 edge ingredient; rank 12-15/15 at /051 but mandate per `feedback_v3_engineered_features_proven.md`)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty per /051 REVERT)
- block_long_for = () (empty per /051 REVERT)
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- adx_threshold_per_symbol = {} (empty)
- BTC trend filter: lookback=42, threshold=15.0% (UNCHANGED)
- OOD z-score gate: zscore_threshold=2.0, **15-D space (UNCHANGED count; dimensionality preserved by SWAP)**
- ADX gate: threshold=20.0 global (UNCHANGED)
- Regime gate: DISABLED (CLOSED per /022)
- Per-symbol cap: DISABLED (CLOSED per /020)

### 3.4 — Setup commit checklist

- [ ] V3_MODELS UNCHANGED — (BCH, LDO, TRX) 3 elements
- [ ] V3_FEATURE_COLUMNS_TOP_N = 15 elements (regime_momentum_signed_3d as 15th; NO fracdiff_d05_close)
- [ ] REQUIRED_GAP UNCHANGED — 66 in validation_v3.py
- [ ] ITERATION_LABEL = "v3-052"
- [ ] `compute_regime_momentum_signed_3d` ACTIVATED in `add_engineered_v3_features` (engineered_v3.py)
- [ ] Feature parquets REGENERATED for BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT (verify `regime_momentum_signed_3d` column present)
- [ ] All 4 audit functions pass: `_verify_v3_models`, `_verify_feature_columns`, `_verify_required_gap`, `_verify_iteration_label`
- [ ] tests/features_v3/test_fracdiff_d05_universal.py UNCHANGED (5 tests PASS — dead-code coverage)
- [ ] tests/features_v3/test_regime_momentum_signed_3d_universal.py CREATED (5 new tests PASS)
- [ ] `uv run pytest tests/features_v3/` ALL PASS
- [ ] `uv run ruff check . && uv run ruff format .` ALL CLEAN
- [ ] `compute_fracdiff_d05_close` in engineered_v3.py PRESERVED as dispatched-but-unused compute (column dropped from V3_FEATURE_COLUMNS_TOP_N; zero revert cost)
- [ ] phase5p5_gate.md document PASS state (all 12 mandatory sections in this brief)

### 3.5 — Run command (LOCKED)

```bash
uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

- EXPLORATION single-seed=42
- ENSEMBLE_SIZE=5 (auto inner ensemble)
- n_trials=35 (EXPLORATION default per `feedback_v3_exploration_n_trials_35.md`)
- 5 inner × 35 trials × **3 symbols = 525 total Optuna trials** (SAME as /051; universe unchanged)
- `--clean-oof` guardrail RETAINED (SHA `6a216b5`)

### 3.6 — Estimated wall-clock

- Setup commit (dispatch activation + V3_FEATURE_COLUMNS_TOP_N SWAP + parquet regen + audits + 5 tests): 35-50 min (longer than /051 due to feature regen step ~5-10 min)
- Phase 5.5 gate: 5-10 min
- Backtest (3-sym + 15 features + n_trials=35 single-seed): 25-35 min (same scale as /051)
- Phase 6/7 reports + Phase 7.5 Critic: 30-40 min
- **TOTAL: ≤1.75h** (within 2h EXPLORATION cap)

---

## Section 4 — Expected OOS Impact

### 4.1 — Quantitative predicted bands (single-seed n_trials=35 EXPLORATION-spec)

| Metric | iter-v3/028 baseline (multi-seed) | iter-v3/051 (1-seed) | **iter-v3/052 PREDICTED (1-seed)** | Δ vs /028 anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.5101 | +0.4506 | **+0.58 ± 0.18** (band [+0.40, +0.75]) | **Δ −0.10 to +0.25** |
| OOS monthly Sharpe | +0.5053 | +0.5891 | **+0.55 ± 0.30** (band [+0.25, +0.85]) | **Δ −0.25 to +0.35** |
| IS-OOS daily Sharpe ratio | 0.99 | 1.15 | **1.05 ± 0.45** (band [0.60, 1.50]) | IN-BAND [0.5, 2.0] |
| IS Trades | 156 (mean) | 178 | **155-200** (Δ -13% to +12%) | comparable |
| OOS Trades | 95 (mean) | 96 | **75-115** (Δ -22% to +20%) | comparable |
| IS MaxDD | 41.43% | 37.37% | **35-45%** (BCH dominant; UNCHANGED universe) | comparable |
| OOS MaxDD | 23.53% | 32.75% | **25-37%** (3-sym LDO still in universe) | comparable |
| OOS Calmar | 0.92 | 0.53 | **0.50-1.20** (single-seed lottery range) | comparable |
| OOS Top concentration | 76.47% (TRX) | 67.65% (BCH) | **65-80%** (LDO still in 3-sym mix) | comparable |
| regime_momentum_signed_3d importance rank | n/a | n/a | **top-10 in ≥1 of 3 syms** (per 5d sister precedent; rank 11-14/15 multi-seed but ESSENTIAL) | informational |
| DSR | 0.0 (structural) | 0.0 (structural) | **0.0** (structural at n_trials=525) | structural EXPLORATION-INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md` |
| PBO | 0.1243 | 0.1168 | **0.10 ± 0.05** | comparable |
| PSR | 1.0 (saturation) | 1.0 | **1.0** | saturation |
| n_trials (Optuna total) | 1050 | 525 | **525** | EXPLORATION 3-sym (UNCHANGED) |
| n_eff | 19 | 19 | **18-22** | within range |

### 4.2 — Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Mandatory per `feedback_v3_axis_saturation_predictor.md`** — explicit prediction of how many IS trades will change:

- **IS trade count change**: predicted **−13% to +12%** (band [155, 200] from /051's 178; mean ~178 — i.e., neutral). Mechanism: SWAP of one feature for another at the 15th slot does not directly drop/add trades; the change comes from Optuna re-tune learning to use 3d's stronger univariate signal for split decisions, potentially tightening (fewer marginal trades) OR loosening (more discriminative entries) the model's threshold. Direction uncertain at single-seed n_trials=35.
  **Falsifier (axis saturation)**: if observed IS trade count change is within ±5% AND 3d importance rank ≥ 14/15 in ALL 3 symbols, axis is SATURATED-INERT (the model isn't learning the feature; analogous to PROMISING-INERT but for ADD axes per `feedback_v3_axis_saturation_predictor.md`). Action: PARK 3d at /052 closeout; pivot to next NEW universal feature at /053.

- **OOS trade count change**: predicted **−22% to +20%** (band [75, 115] from /051's 96). Similar mechanism to IS; the SWAP at the 15th feature slot drives Optuna re-tuning rather than direct trade-roster shifts.
  **Falsifier**: same saturation diagnostic (< ±5% AND rank ≥ 14/15 ALL syms).

- **BCH/LDO/TRX IS attribution share**: UNCHANGED universe means relative attribution will shift only via the Optuna re-tune learning to use 3d. /051 attribution was BCH +24.60 / LDO +11.155 / TRX -5.43 wpnl. Predicted /052 directional shifts:
  - BCH: predicted ±10% shift (BCH has highest baseline trade volume; 3d's strongest univariate signal at TRX could shift cross-symbol balance)
  - LDO: predicted ±15% shift (LDO has lowest IC redundancy with 3d sister 5d, 0.4271 — most independent signal channel)
  - TRX: predicted ±20% shift (TRX has strongest 3d univariate ρ -0.068 — most direct response expected)

- **regime_momentum_signed_3d importance rank prediction**: predicted top-10 in at least 1 of 3 symbols (TRX most likely given strongest univariate ρ -0.068; followed by ALGO at -0.058 but ALGO not in V3_MODELS at /052). Per iter-v3/028 precedent, regime_momentum_signed_5d ranks 12-15/15 at multi-seed but is ESSENTIAL (proven mandate per `feedback_v3_engineered_features_proven.md`) — analogous low-rank-but-essential pattern expected for 3d.

### 4.3 — Most likely classification

Per §7 pre-registration and §2 EDA evidence, **PATH B (PROMISING-INERT) is most likely (~30%)** — the SWAP at single-seed n_trials=35 may not produce decisive IS+OOS shift if Optuna does not learn to use the feature for splits (analogous to fracdiff at /051 ranks 11-13/15 with no decisive lift). Secondary path: **PATH A (PROMISING-clean) at ~25%** — if Optuna does learn the stronger univariate signal of 3d (mean ρ -0.057 vs fracdiff -0.044) and translates it to IS Sharpe lift while preserving in-band IS-OOS daily ratio. Tertiary: **PATH C-clean (NEGATIVE-clean) at ~20%** — if 3d/5d stacking distorts colsample picks (despite IC at 0.43-0.47 being below 0.50 threshold, Optuna at n_trials=35 may not select 3d optimally). PATH D (NULL-RESULT) at ~15%. PATH C-suspicious at only ~10% (the EDA does not predict the OOS-only artifact that the LDO removal axis would have triggered).

### 4.4 — Falsifier band (axis-saturation)

| Metric | Predicted range | Falsifier trigger |
|---|---|---|
| IS trade count change | -13% to +12% | < ±5% AND 3d rank ≥ 14/15 ALL syms (saturation-INERT) |
| OOS trade count change | -22% to +20% | < ±5% AND 3d rank ≥ 14/15 ALL syms (saturation-INERT) |
| 3d importance rank | top-10 in ≥1 sym | rank ≥ 14/15 ALL 3 syms = PROMISING-INERT |
| IS Sharpe Δ vs /028 anchor | -0.10 to +0.25 | < -0.10 = PATH C-clean (axis CLOSED) |
| OOS Sharpe Δ vs /028 anchor | -0.25 to +0.35 | < -0.30 = PATH C-clean (axis CLOSED) |
| IS-OOS daily Sharpe ratio | 0.60 to 1.50 | outside [0.5, 2.0] = PATH C-suspicious |

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md` (R1-R5 framework adapted for v3 risk-gate architecture).

### 5.1 — R1 — Cool-downs

- 2-candle post-trade cooldown per (model, symbol) — UNCHANGED (engine-level seeded via `cooldown_<model>_<sym>` engine_state keys)
- R1 cooldowns rebuilt from DB on engine startup (via `_rebuild_risk_state()`)

### 5.2 — R2 — Drawdown-triggered position scaling

- Engine-level drawdown brake DISABLED in v3 (per `feedback_v3_concentration_is_signal.md`)
- Per-symbol drawdown brake DISABLED (per `feedback_v3_concentration_is_signal.md` rejecting iter-v3/020 per-symbol PnL cap)
- Vol scaling (RiskV2Wrapper) ACTIVE — per-trade weight_factor in [0.33, 1.0] band; primary risk scaling

### 5.3 — R3 — OOD detection

- **OOD z-score gate ACTIVE** at zscore_threshold=2.0 (UNCHANGED from /051)
- Dimensionality: **15-D feature space** (UNCHANGED count at /052 — SWAP preserves dimensionality)
- Mahalanobis distance computed on 15 features from V3_FEATURE_COLUMNS_TOP_N (now includes regime_momentum_signed_3d instead of fracdiff_d05_close)
- Cutoff = 95th percentile of training-window distances (per RiskV2 implementation)
- Embedded in per-symbol RiskV2Wrapper at predict time

### 5.4 — R4 — Vol kill-switch

- **BTC trend filter ACTIVE** at lookback=42, threshold=15.0% (UNCHANGED from /051)
- Mechanism: if |BTC 14-day return| > 15%, kill ALL trades (weight_factor=0)
- /051 observed: 32 OOS trades killed (~25% of candidates); similar % expected at /052

### 5.5 — R5 — Concentration caps

- Per-symbol PnL share caps DISABLED (CLOSED per `feedback_v3_concentration_is_signal.md` iter-v3/020 verdict)
- Top-symbol concentration gate INFORMATIONAL ONLY (≤ 30% aspirational, not enforced as kill switch)
- Expected /052 OOS top concentration: 65-80% (BCH or TRX dominant in 3-sym universe; unchanged from /051's 67.65% baseline)

### 5.6 — Risk gate stack (v3 7-primitive)

| Primitive | Parameter | iter-v3/052 state | Behavior |
|---|---|---|---|
| BTC trend kill | lookback=42, threshold=15% | ACTIVE | Kill all trades if |BTC 14d ret| > 15% |
| Vol scaling | weight_factor ∈ [0.33, 1.0] | ACTIVE | Per-trade scaling by vol estimate |
| ADX gate | threshold=20.0 global | ACTIVE | Filter low-trend regimes |
| Hurst regime | embedded in features | ACTIVE (informational) | hurst_100, hurst_diff_100_50 are features |
| z-score OOD | zscore_threshold=2.0, 14-D | ACTIVE | Reject OOD candles; 14-D after fracdiff drop |
| Low-vol filter | embedded | ACTIVE | Skip extremely low-vol candles |
| Hit-rate gate | DISABLED | OFF | Per `feedback_v3_strict_10_to_1_cadence.md` discipline |
| Primitive 10 — BCH LONG block | block_long_for=() | INFRASTRUCTURE-ONLY | Wired off per /051 REVERT; code path preserved |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | Per /020 CLOSED-mechanism |
| Regime gate | enable_regime_gate=False | DISABLED | Per /022 PARTIALLY-EFFECTIVE-CLOSED |

### 5.7 — IS-calibrated thresholds + simulated effect

- BTC trend filter at 15%: calibrated at /050 EDA (32 OOS trades killed; consistent across /045-/051)
- Vol scaling: per-trade weight_factor in [0.33, 1.0]; calibrated at /028 multi-seed (no change since)
- OOD z-score 2.0: calibrated at /011 (tightened from default 2.5 to 2.0 to surface more OOD)

No risk-gate thresholds change at iter-v3/052. The axis under test is a NEW universal engineered feature SWAP (regime_momentum_signed_3d replaces fracdiff_d05_close in V3_FEATURE_COLUMNS_TOP_N); risk-gate calibration is held constant.

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

(Same as §5.6 — repeated here for adversarial-review structure)

| # | Primitive | Mechanism | iter-v3/052 state | Audit |
|---|---|---|---|---|
| 1 | BTC trend kill switch | If |BTC 14d return| > 15%, weight_factor = 0 | ACTIVE | `_build_v3_model` BTC_TREND_CONFIG |
| 2 | Vol scaling (RiskV2Wrapper) | Per-trade scaling by symbol-vol estimate; bounded [0.33, 1.0] | ACTIVE | RiskV2Wrapper at strategy level |
| 3 | ADX gate | Filter low-trend regimes at threshold=20.0 | ACTIVE | RiskV2Config.adx_threshold=20.0 |
| 4 | Hurst regime | hurst_100, hurst_diff_100_50 features inform model | ACTIVE (informational) | features_v3 regime group |
| 5 | z-score OOD (Mahalanobis) | Reject OOD candles at 2.0 cutoff in 15-D feature space (UNCHANGED from /051) | ACTIVE | RiskV2Config.zscore_threshold=2.0 |
| 6 | Low-vol filter | Skip extremely low-vol candles | ACTIVE | RiskV2Wrapper embedded |
| 7 | Hit-rate gate | Per-symbol hit-rate feedback | DISABLED | Per `feedback_v3_strict_10_to_1_cadence.md` |
| 8 | Per-symbol cap | Per-symbol PnL share cap (e.g., 0.40) | DISABLED | Per `feedback_v3_concentration_is_signal.md` /020 |
| 9 | Regime gate | TRX/2022-Q4 regime block | DISABLED | Per `feedback_v3_promising_mechanical_subtype.md` /022 |
| 10 | Direction-asymmetric kill switch | block_long_for=("BCHUSDT",) or symmetric block_short_for | INFRASTRUCTURE-ONLY (wired off per /051 REVERT) | run_baseline_v3.py:_build_v3_model |

Primitive 10 is preserved as code infrastructure (mechanism + 7 adversarial tests + GateStats counter) but wired-off at /051 REVERT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10. iter-v3/052 inherits this REVERT (no per-symbol customization wiring change). The EDA finding that LDO OOS drag is direction-asymmetric (in §2.8 audit appendix) does NOT trigger a new primitive 10 wiring — that would be per-symbol customization, REJECTED at system level.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Single most likely failure mode** (per §2 EDA finding): PATH B (PROMISING-INERT) — regime_momentum_signed_3d at single-seed n_trials=35 may not be learned decisively by Optuna (sister 5d feature also ranks 12-15/15 at multi-seed despite being ESSENTIAL). Mechanism: stacking with 5d sister at IC 0.43-0.47 may distort colsample picks at low Optuna budget; Optuna prefers existing 14 features for splits, leaving 3d at rank 14-15/15 with limited importance.

Secondary failure mode: PATH C-clean — 3d/5d stacking causes IS Sharpe regression (Δ < -0.10) if Optuna can't disentangle the two regime-momentum time-scales. This is the iter-v3/026/027 anti-pattern (engineered features don't stack at single-seed) applied to sister features; mitigated by:
- IC 0.43-0.47 is BELOW the 0.50 stacking-risk threshold from iter-v3/026
- The two features differ in time-scale (1-day vs 5-day at 8h cadence), not in composition

Tertiary failure mode: PATH C-suspicious — IS-OOS daily Sharpe ratio exits [0.5, 2.0] band. UNLIKELY because the EDA shows symmetric univariate signal across IS+OOS (no OOS-only artifact in counterfactual).

If PATH B fires: PARK 3d at /052 closeout; pivot to next NEW universal engineered feature at /053 (candidates: hurst_drift_50_200 per /051 EDA synthesis.md §c2).

### 7.1 — Predicted failure-mode taxonomy (5 paths per Critic FINAL `32cc46f` rec #3)

| Path | Probability | Trigger | Action if fires |
|---|---:|---|---|
| PATH A (PROMISING-clean) | 25% | IS Δ ≥ +0.05 AND OOS Δ ≥ +0.30 AND IS-OOS ratio in band | Carry 3d to /053 stacking test (with adjacent universal feature); CLOSE fracdiff-d05 per /051 PARKED status |
| PATH B (PROMISING-INERT) | **30%** | 3d importance rank ≥ 14/15 ALL 3 syms AND \|IS Δ\| ≤ 0.10 | PARK 3d (zero revert cost); pivot to next NEW universal feature at /053 (hurst_drift_50_200) |
| PATH C-clean | 20% | IS Δ < -0.10 OR OOS Δ < -0.30 with ratio in band | CLOSE 3d UNIVERSAL axis; document NEGATIVE; pivot to /053 |
| PATH C-suspicious | 10% | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | CLOSE 3d UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP |
| PATH D (NULL-RESULT) | 15% | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis effect LEARNED (trade count change ≥10%) | PARK 3d; retest at multi-seed CONFIRMATION as bundle ingredient |

### 7.2 — Additional sanity-check failure modes

- **Optuna trial-count saturation**: 525 trials at 5 inner × 35 × 3 sym; n_eff predicted 18-22 (UNCHANGED from /051). DSR likely 0.0 (structural at n_trials=525; EXPLORATION-INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md`).
- **PBO at 3-sym universe**: predicted 0.10 ± 0.05 (UNCHANGED from /051's 0.1168 and /028's 0.1243). REQUIRED_GAP=66 unchanged.
- **Stacking risk** (sister features 3d + 5d): IC 0.43-0.47 BELOW 0.50 stacking-risk threshold. Mitigation: monitor 3d AND 5d importance ranks at engineering report. If 5d importance drops materially at /052 vs /051 (e.g., from rank 14 to rank 15 or 16), document as sister-stacking effect.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**LOCKED at brief commit; mechanical evaluation post-backtest; NO post-hoc renegotiation per `feedback_no_cheating.md` discipline.**

### 8.1 — 5 LOCKED paths (per Critic FINAL `32cc46f` rec #3 PATH D addition)

| Path | All conditions must fire (AND) | Decision |
|---|---|---|
| **PATH A (PROMISING-clean)** | IS Δ ≥ +0.05 vs /028 anchor (+0.5101) AND OOS Δ ≥ -0.20 vs /028 anchor (+0.5053) AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0] AND regime_momentum_signed_3d importance rank ≤ 10/15 in ≥1 of 3 syms | PROMISING for cycle 4 #2; carry 3d to /053 stacking test (with adjacent NEW universal feature) |
| **PATH B (PROMISING-INERT)** | regime_momentum_signed_3d importance rank ≥ 14/15 in ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | PARK 3d (zero revert cost; compute function + tests retained); pivot to next NEW universal feature at /053 |
| **PATH C-clean (NEGATIVE-clean)** | IS Δ < -0.10 OR OOS Δ < -0.30 (with IS-OOS daily ratio ∈ [0.5, 2.0]) | CLOSE 3d UNIVERSAL axis for cycle 4; document NEGATIVE; pivot to /053 axis |
| **PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)** | IS-OOS daily Sharpe ratio outside [0.5, 2.0] band | CLOSE 3d UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP; pivot to /053 axis |
| **PATH D (EXPLORATION-NULL-RESULT)** | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis effect LEARNED (3d importance rank ≤ 13/15 in ≥1 sym AND trade count change ≥10% OR IS+OOS Sharpe Δ both ≤ ±0.10 with rank ≤ 13/15) | NULL-RESULT; PARK 3d (retain code at zero revert cost); retest at multi-seed CONFIRMATION as bundle ingredient |

### 8.2 — Numerical thresholds

| Threshold | Value | Source |
|---|---|---|
| IS Sharpe anchor (/028 baseline) | +0.5101 | BASELINE_V3.md |
| OOS Sharpe anchor (/028 baseline) | +0.5053 | BASELINE_V3.md |
| PATH A IS Δ floor | +0.05 | EXPLORATION PROMISING band |
| PATH A OOS Δ floor | -0.20 | EXPLORATION PROMISING band (allows neutral-OOS PROMISING when IS lifts; per `feedback_v3_engineered_features_proven.md` precedent at iter-v3/025 which had IS lift dominant over OOS) |
| PATH A IS-OOS ratio band | [0.5, 2.0] | `feedback_v3_engineered_features_dont_stack.md` |
| PATH A importance rank floor | ≤ 10/15 in ≥1 sym | Per `feedback_v3_engineered_features_proven.md` (engineered feature must rank meaningfully in at least one sym) |
| PATH B \|IS Δ\| range | ≤ 0.10 | INERT band |
| PATH B \|OOS Δ\| range | ≤ 0.30 | INERT band (wider than IS to accommodate single-seed OOS noise) |
| PATH B INERT criterion | rank ≥ 14/15 ALL 3 syms | Per `feedback_v3_inert_features_at_higher_budget.md` |
| PATH C-clean IS Δ ceiling | -0.10 | NEGATIVE band |
| PATH C-clean OOS Δ ceiling | -0.30 | NEGATIVE band |
| PATH C-suspicious ratio band | [0.5, 2.0] | `feedback_v3_engineered_features_dont_stack.md` |
| PATH D IS Δ range | (-0.10, +0.05) | NULL-RESULT no-man's-land (per Critic FINAL `32cc46f` rec #3) |
| PATH D OOS Δ range | (-0.20, +0.20) | NULL-RESULT no-man's-land |
| PATH D learned criterion | rank ≤ 13/15 in ≥1 sym AND (trade count change ≥10% OR Sharpe Δ both ≤ ±0.10) | LEARNED with no decisive effect |

### 8.3 — BOTH-must-improve gate (advisory, NOT MERGE-blocking at EXPLORATION-spec)

Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates require BOTH IS AND OOS Sharpe improvement vs prior baseline. This gate is **CONFIRMATION-only** (not applied at EXPLORATION). However, the gate's spirit informs PATH A criteria: a clean PROMISING for engineered features prefers IS lift over OOS lift (since IS is more reliably attributable to the feature, OOS being noisier at single-seed).

At iter-v3/052 EXPLORATION-spec: if PATH A fires, the axis is candidate for cycle 4 #3 stacking. If PATH B fires (most likely), the axis is parked and we pivot to the next NEW universal feature candidate.

### 8.4 — DSR / PBO / PSR INFORMATIONAL at EXPLORATION-spec

Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is structural artifact at n_trials=525 (E[max_SR] formula returns ~2.0 required; observed annualized ≈1.0-1.5 → DSR=0). Not a MERGE gate at EXPLORATION-spec.

- DSR > 0.95 gate: ENFORCED at CONFIRMATION only
- PBO < 0.4 gate: ENFORCED at both EXPLORATION and CONFIRMATION
- PSR > 0.95 gate: ENFORCED at both
- IC < 0.7 gate: ENFORCED at both (regime_momentum_signed_3d PASSES at max |IC| 0.6192 — see §2.2)

### 8.5 — Catalog row pre-commits (one per outcome)

(See §11 below for full row format)

---

## Section 9 — Library Stack Declaration

Pinned via `pyproject.toml` (UNCHANGED from /051):

```
lightgbm == 4.6.0
optuna == 4.8.0
numpy == 2.2.6
pandas == 3.0.0
scikit-learn == 1.8.0
scipy == 1.17.0
statsmodels == 0.14.6
pyarrow == 23.0.1
mlfinlab == 1.4 (fallback: mlfinpy)
pypbo
fracdiff >= 0.10
```

No new dependencies introduced at iter-v3/052. fracdiff package remains available (compute_fracdiff_d05_close uses it as numerical primitive); only V3_FEATURE_COLUMNS_TOP_N drops the column dispatch.

Python version: 3.13+.

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**PIVOT: Orchestrator pick SUPERSEDED by QR EDA per `feedback_v3_axis_selection_quant_discipline.md` rule 4.**

### 10.1 — Setup commit SHA backfill

(To be backfilled at setup commit time; matches the Engineer's setup commit that implements §3 changes — activate `compute_regime_momentum_signed_3d` dispatch + V3_FEATURE_COLUMNS_TOP_N SWAP + 5 adversarial tests + parquet regen. Until backfill: PENDING.)

### 10.2 — EDA commit SHAs (TWO EDA scripts inform this brief)

**Primary EDA (axis backing):** SHA `290f37b` — analysis(iter-v3/051): cycle 4 #1 EDA + 4-axis ranking

Located at `analysis/iteration_v3-051/`:
- `axis_c_regime_3d_compute.py` — on-the-fly compute + IC + ADF + univariate Spearman for regime_momentum_signed_3d
- `axis_c_regime_3d_ic.csv` — per-symbol IC matrix (max |IC| 0.6192 < 0.70 strict gate)
- `axis_c_regime_3d_adf.csv` — ADF p=0 across all 4 symbols
- `axis_c_regime_3d_univariate.csv` — Spearman ρ -0.044 to -0.068 significant all 4 syms
- `synthesis.md` §c3 + `candidate_axes_ranking.md` §Candidate 2 — explicit RANKED #2 designation for /052
- `regime_momentum_importance.csv` — sister 5d feature importance precedent at /028 + /050

**Secondary EDA (orchestrator-supersession backing):** SHA `0a10581` — analysis(iter-v3/052): LDO removal EDA — INVERTS orchestrator premise

Located at `analysis/iteration_v3-052/`:
- `ldo_removal_eda.py` + 7 CSVs + `synthesis.md` — pre-falsifies the orchestrator's LDO-removal mandate

### 10.3 — Orchestrator pick PRE-FALSIFIED by /052 EDA

**The orchestrator's original brief mandate (committed at SHA `87e070b`) stated:**
- LDO IS PnL share = −14.96% at /051 (drag at IS too)
- LDO OOS weighted_pnl = −17.44 (drag at OOS)
- Cycle 4 #2 axis = LDO removal + fracdiff drop (TWO-VARIABLE bundle)

**The /052 QR EDA (SHA `0a10581`) revealed the premise is FALSE:**
- LDO IS PnL share = **+36.78% weighted_pnl share** (CONTRIBUTOR, not drag) — premise misread `per_symbol.csv:net_pnl_pct` (sums per-trade raw % returns; IGNORES weight_factor) instead of `weighted_pnl` (the Sharpe-relevant metric).
- LDO OOS weighted_pnl = −17.44 wpnl (drag at OOS — CONFIRMED).
- **2-sym counterfactual at /051 trade roster**: IS Sharpe Δ **−0.16** (BREAKS IS), OOS Sharpe Δ **+1.01** (lifts OOS), IS-OOS daily Sharpe ratio **3.58 (OUT-OF-BAND of [0.5, 2.0])**.
- The LDO-removal axis would trigger PATH C-suspicious by construction — structurally identical to per-symbol customization anti-pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) applied at universe-composition level. This pattern was CLOSED at system level after 2-cycle confirmation (iter-v3/039 + /050).

### 10.4 — QR EDA SUPERSEDES orchestrator pick (per `feedback_v3_axis_selection_quant_discipline.md` rule 4)

The memory rule explicitly states:

> Rule 2: The QR makes the axis call, not the orchestrator. The orchestrator may suggest candidates but cannot commit a setup commit until QR has produced EDA backing the axis choice. **If the orchestrator commits a setup commit ad-hoc, QR must REWRITE the brief and REVERT the setup commit when EDA fails to support it.**
>
> Rule 4: A new Section 10 ("QR Audit Trail") is added to the brief template when the orchestrator's original axis pick is superseded. Section 10 cites the EDA SHA, the orchestrator's original pick, the QR-driven replacement, and the setup commit SHA of the rewrite.

The /052 QR EDA at SHA `0a10581` produced numerical evidence that the LDO-removal axis would fire PATH C-suspicious BY CONSTRUCTION (counterfactual deltas robust to single-seed Optuna noise per axis_2_counterfactual_2sym.csv methodology). The orchestrator pick is PRE-FALSIFIED — running the test would consume a cycle 4 EXPLORATION slot to mechanically re-confirm an anti-pattern at the universe-composition level.

**PIVOT decision (this brief):** The /052 axis SWAPS to `regime_momentum_signed_3d` UNIVERSAL — the /051 EDA RANKED #2 queued explicitly for /052 per `analysis/iteration_v3-051/synthesis.md` §c3 and `candidate_axes_ranking.md` §Candidate 2.

### 10.5 — Pivoted axis: regime_momentum_signed_3d UNIVERSAL

**Mechanism:** `ret_3d × sign(hurst_100 − 0.5)` — orthogonal 3-bar time-scale variant of regime_momentum_signed_5d (iter-v3/028 baseline edge ingredient; multi-seed CONFIRMATION-MERGE).

**EDA backing (cite from /051 SHA `290f37b`):**
- ADF stationary p=0 ALL 4 syms (axis_c_regime_3d_adf.csv) — `regime_momentum_signed_3d` is structurally stationary by construction (bounded sign factor × stationary ret_3d).
- Max |IC| = 0.6192 < 0.70 strict gate, NO carve-out needed (axis_c_regime_3d_ic.csv) — CLEANER than fracdiff which required Category-2 carve-out at LDO 0.7381.
- Univariate ρ significant at ALL 4 syms (mean -0.057, range -0.044 to -0.068; axis_c_regime_3d_univariate.csv) — STRONGER signal than fracdiff (mean -0.044).
- IC with sister 5d feature 0.43-0.47 (moderate; BELOW 0.50 stacking-risk threshold from iter-v3/026 anti-pattern).
- iter-v3/044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+/052 (3-sym BCH+LDO+TRX). The /044 falsification does NOT apply to cycle 4 starting baseline.
- compute function exists as dead code at `engineered_v3.py:330-376` (zero new code; 1-line dispatch reactivation + parquet regen).
- Same proven family as iter-v3/028 baseline edge ingredient regime_momentum_signed_5d (composed engineered feature; multi-seed validated).

### 10.6 — Setup change: SINGLE-AXIS SWAP (not TWO-VARIABLE bundle)

The PIVOTED axis is a SINGLE feature SWAP (not the original TWO-VARIABLE LDO+fracdiff bundle):
- DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15th element) — PARKED per /051 closeout
- ADD regime_momentum_signed_3d as 15th element — NEW universal engineered feature axis

V3_FEATURE_COLUMNS_TOP_N net count: **15 UNCHANGED**. V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX). REQUIRED_GAP UNCHANGED (66). All other state UNCHANGED from /051 head. Single-axis discipline per `feedback_v3_axis_selection_quant_discipline.md` rule 5 (single-axis EXPLORATIONs preferred).

### 10.7 — Difference from iter-v3/041 pattern (NOT a "proceed with locked mandate" case)

This is NOT analogous to iter-v3/041 (universal feature pruning where QR raised concerns and orchestrator's mandate proceeded). In iter-v3/041, the QR concerns were qualitative ("BCH may be affected") without numerical pre-falsification. At iter-v3/052, the QR EDA at SHA `0a10581` produced a NUMERICAL counterfactual (IS Δ -0.16; OOS Δ +1.01; IS-OOS ratio 3.58 OUT-OF-BAND) that triggers PATH C-suspicious by construction.

Per `feedback_v3_axis_selection_quant_discipline.md` rule 2 (sentence 3): "If the orchestrator commits a setup commit ad-hoc, QR must REWRITE the brief and REVERT the setup commit when EDA fails to support it." This rule fires here. The PIVOT is mandated, not optional.

The orchestrator's recommendation to pivot (delivered in the PIVOT-task prompt) is consistent with this rule — the orchestrator acknowledged the EDA backing the supersession and instructed the QR to execute the pivot.

### 10.8 — Critic FINAL `32cc46f` recommendation alignment (PIVOTED)

| Critic FINAL `32cc46f` Recommendation | iter-v3/052 brief addressed? |
|---|---|
| Rec #1: iter-v3/052 axis = LDO removal investigation (HIGH-priority cycle 4 #2) | **PRE-FALSIFIED by /052 EDA SHA `0a10581`**; axis QUEUED for multi-seed CONFIRMATION re-evaluation. Replaced by /051 EDA RANKED #2 (regime_momentum_signed_3d UNIVERSAL) per `feedback_v3_axis_selection_quant_discipline.md` rule 4. |
| Rec #2: Drop fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N at /052 setup. PARKED, not CLOSED. Retain compute function + tests. | YES — §3.1 setup commit: SWAP 15th element (DROP fracdiff_d05_close; ADD regime_momentum_signed_3d). compute_fracdiff_d05_close + 5 tests retained as dispatched-but-unused (zero revert cost). |
| Rec #3: Brief pre-registration tightening — add PATH D (EXPLORATION-NULL-RESULT) covering IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.30, +0.20) | YES — §8.1 PATH D added with band [-0.20, +0.20] OOS (aligned with `feedback_v3_axis_saturation_predictor.md` symmetric band convention; LEARNED criterion adapted to engineered-feature-axis: rank ≤ 13/15 in ≥1 sym OR trade count change ≥10%). |

### 10.9 — Catalog catalog entry update at /053 EDA reference

The /053 EDA (next cycle 4 EXPLORATION; whichever axis chosen there) must reference SHA `0a10581` (LDO supersession EDA) and this brief (§10) as the basis for the LDO removal axis CLOSED status at cycle 4 EXPLORATION. The axis remains AVAILABLE for retest at multi-seed CONFIRMATION (iter-v3/061+), where single-seed lottery artifacts dissolve.

---

## Section 11 — References

### Catalog row pre-commits (one per outcome path)

Per `briefs-v3/exploration_catalog.md` format. ONE row added to catalog at diary write per the firing path.

**PATH A (PROMISING-clean) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL (V3_MODELS UNCHANGED 3-sym BCH+LDO+TRX); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof. PIVOT from orchestrator LDO-removal axis (pre-falsified by /052 EDA SHA 0a10581) to QR-EDA-backed /051 RANKED #2 (SHA 290f37b) | [+IS_Δ ≥ +0.05] (vs iter-v3/028 baseline +0.5101; PROMISING-clean) | [+OOS_Δ ≥ -0.20] (vs iter-v3/028 baseline +0.5053; IS-OOS daily ratio [X] in [0.5, 2.0] band; 3d importance rank ≤ 10 in ≥1 sym) | EXPLORATION-PROMISING-clean | YES — regime_momentum_signed_3d at universal scope lifts IS Sharpe. Carry to /053 stacking test or expand axis. NEW universal engineered feature family validated. |
```

**PATH B (PROMISING-INERT) catalog row — MOST LIKELY (~30%):**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL; PIVOT from orchestrator LDO-removal axis (pre-falsified) | [|IS_Δ| ≤ 0.10] (vs +0.5101) | [|OOS_Δ| ≤ 0.30] (vs +0.5053; 3d importance rank ≥ 14/15 ALL syms = INERT) | EXPLORATION-PROMISING-INERT | NO — 3d not learned at single-seed n_trials=35. PARK 3d (compute function + tests retained at zero revert cost). Pivot to /053 next NEW universal feature (hurst_drift_50_200 candidate). |
```

**PATH C-clean (NEGATIVE-clean) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL; PIVOT from orchestrator LDO-removal axis (pre-falsified) | [IS_Δ < -0.10] OR [OOS_Δ < -0.30] (vs /028 anchor; IS-OOS ratio in [0.5, 2.0]) | NEGATIVE-clean falsifier fired | EXPLORATION-NEGATIVE-clean | NO — 3d at universal scope regresses bundle (likely stacking-with-5d interaction at single-seed). CLOSE 3d UNIVERSAL axis for cycle 4. Pivot to /053. |
```

**PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL; PIVOT from orchestrator LDO-removal axis (pre-falsified) | [IS_Δ vs +0.5101] | [OOS_Δ vs +0.5053; IS-OOS daily ratio OUT-OF-BAND of [0.5, 2.0]] | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS (engineered feature single-seed lottery artifact) | NO — 3d SWAP triggers PATH C-suspicious anti-pattern at single-seed. CLOSE 3d UNIVERSAL axis for cycle 4. |
```

**PATH D (EXPLORATION-NULL-RESULT) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL; PIVOT from orchestrator LDO-removal axis (pre-falsified) | [IS_Δ in (-0.10, +0.05)] (vs +0.5101) | [OOS_Δ in (-0.20, +0.20)] (vs +0.5053; 3d LEARNED with rank ≤ 13 in ≥1 sym AND/OR trade count change ≥10%) | EXPLORATION-NULL-RESULT (per Critic FINAL `32cc46f` rec #3) | NO — 3d axis PARKED (not CLOSED). Retain code at zero revert cost. Retest at multi-seed CONFIRMATION as bundle ingredient. |
```

### 11.2 — File references

**Primary EDA (axis backing) — `analysis/iteration_v3-051/` SHA `290f37b`:**
- `axis_c_regime_3d_compute.py` — on-the-fly compute + IC + ADF + univariate for regime_momentum_signed_3d
- `axis_c_regime_3d_ic.csv` — full per-symbol IC matrix
- `axis_c_regime_3d_adf.csv` — ADF stationarity
- `axis_c_regime_3d_univariate.csv` — Spearman ρ vs forward 1-bar return
- `synthesis.md` §c3 — explicit RANKED #2 designation queued for /052
- `candidate_axes_ranking.md` §Candidate 2 — sister doc

**Secondary EDA (orchestrator-supersession backing) — `analysis/iteration_v3-052/` SHA `0a10581`:**
- `ldo_removal_eda.py` — 7-axis EDA
- `axis1_ldo_contribution_at_051.csv` — LDO weighted_pnl share (premise correction)
- `axis2_counterfactual_2sym.csv` — 2-sym BCH+TRX counterfactual (CRITICAL TABLE)
- `axis3_050_vs_051_supersession.csv` — premise correction
- `axis4_cross_iteration_ldo.csv` — LDO pattern across /028/045/047/049/050/051
- `axis5_data_extent.csv` — LDO 30 months vs BCH/TRX 62 months
- `axis6_ldo_directional_asymmetry.csv` — LDO LONG vs SHORT at /051
- `axis7_ldo_monthly_pnl.csv` — LDO 2025-Q3 OOS regression concentration
- `synthesis.md` — full LDO supersession analysis + pivot rationale

### 11.3 — Memory rules consulted

- `feedback_v3_axis_selection_quant_discipline.md` — QR EDA-driven axis selection; Section 10 audit trail when orchestrator overrides
- `feedback_v3_strict_both_is_oos_baseline.md` — BOTH-must-improve gate (CONFIRMATION-only; advisory at EXPLORATION)
- `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — per-symbol customization anti-pattern (LDO removal triggers same at universe-composition level)
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 4 #2 of 10; do NOT collapse 10th EXPLORATION into CONFIRMATION
- `feedback_v3_exploration_n_trials_35.md` — n_trials=35 EXPLORATION default
- `feedback_v3_single_seed_frozen_baseline.md` — single-seed=42 lottery caveat (esp. for OOS interpretation)
- `feedback_v3_dsr_mode_artifact.md` — DSR/PSR EXPLORATION-INFORMATIONAL at n_trials=350
- `feedback_v3_engineered_features_dont_stack.md` — IS-OOS daily Sharpe ratio falsifier [0.5, 2.0]
- `feedback_v3_axis_saturation_predictor.md` — Section 4 behavioral-effect predictor mandate
- `feedback_v3_engineered_feature_pivot.md` — Category 2 carve-out (N/A at /052 since fracdiff dropped)
- `feedback_v3_baseline_update_policy.md` — STRICTLY-BETTER-than-prior-baseline (CONFIRMATION-only)
- `feedback_v3_concentration_is_signal.md` — per-symbol cap CLOSED (informs §5.5)
- `feedback_no_cheating.md` — no post-hoc renegotiation of pre-registered §7-§8

### 11.4 — Critic FINAL artifacts

- `briefs-v3/iteration_v3-051/review.md` SHA `32cc46f` — recommendations #1 + #2 + #3 + #4 (Rec #1 PRE-FALSIFIED by /052 EDA; Rec #2 + #3 implemented in this brief)
- `briefs-v3/iteration_v3-051/engineering_report.md` SHA `13a6ec5` — critical finding originally cited by orchestrator (LDO IS net_pnl_pct -14.96%; pre-falsified by /052 EDA showing weighted_pnl interpretation correction)
- `diary-v3/iteration_v3-051.md` — /051 closeout setting up cycle 4 #2 candidate axes
- `diary-v3/iteration_v3-050.md` — /050 closeout setting up cycle 4 priorities

### 11.5 — Baseline anchor

- `BASELINE_V3.md` (UNCHANGED at iter-v3/028; +0.5101 IS / +0.5053 OOS multi-seed mean; SHA `b0576df`)

---

## Section 12 — Brief Validation Checklist (Pre-Phase-5.5)

| # | Requirement | Status |
|---|---|---|
| 1 | Data split declaration (§0) | DONE |
| 2 | Iteration type declaration with spec (§0.5) | DONE — EXPLORATION cycle 4 #2; --seeds 1 --n-trials 35 --clean-oof; SINGLE-AXIS SWAP (PIVOTED from TWO-VARIABLE bundle) |
| 3 | Hypothesis (§1) | DONE — regime_momentum_signed_3d UNIVERSAL SWAP |
| 4 | IS-only numerical evidence with committed analysis script (§2) | DONE — Primary SHA `290f37b` (/051 EDA RANKED #2 axis backing); Secondary SHA `0a10581` (/052 LDO supersession EDA) |
| 5 | Proposed changes (§3) | DONE — SINGLE-AXIS SWAP: V3_FEATURE_COLUMNS_TOP_N 15th element SWAP (fracdiff_d05_close → regime_momentum_signed_3d); compute dispatch activation; feature parquet regen |
| 6 | Expected OOS impact with predicted bands + behavioral-effect predictor (§4) | DONE — §4.1 quantitative bands; §4.2 importance rank + trade-count predictor |
| 7 | Risk Mitigation R1-R5 with IS-calibrated thresholds (§5) | DONE |
| 8 | Risk Management Design 10-primitive gate table (§6) | DONE |
| 9 | Pre-registered failure-mode prediction (§7) | DONE — PATH B (PROMISING-INERT) 30% most likely |
| 10 | Pre-registered MERGE/NO-MERGE numerical criteria LOCKED (§8) | DONE — 5 paths incl. PATH D per Critic `32cc46f` rec #3 |
| 11 | Library stack declaration (§9) | DONE — UNCHANGED from /051 |
| 12 | Section 10 QR audit trail | DONE — orchestrator pick SUPERSEDED by QR EDA per `feedback_v3_axis_selection_quant_discipline.md` rule 4; PIVOT documented in §10.3-10.9 |
| 13 | Section 11 catalog row pre-commits | DONE — 5 rows (one per path) for PIVOTED axis |
| 14 | Setup commit SHA backfill placeholder (§10.1) | PENDING (Engineer backfills at setup-commit time) |
| 15 | All 12 mandatory sections present | DONE |

**Brief PIVOTED at commit. Pre-Phase-5.5 gate criteria satisfied for the new axis. Ready for QE Phase 5.5 review.**

---

**End of iteration v3-052 research brief (PIVOTED — regime_momentum_signed_3d UNIVERSAL SWAP).**
