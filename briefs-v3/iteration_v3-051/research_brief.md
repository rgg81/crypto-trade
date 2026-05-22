# Iteration v3-051 — Research Brief (NEW universal engineered feature: fracdiff_d05_close UNIVERSAL + system-level REVERT to /028 architecture)

**Type**: EXPLORATION (Cycle 4 #1 of 10)
**Track**: v3 (rigor arm) — fifty-first iteration
**Branch**: `iteration-v3/051` (off iter-v3/050 head at SHA `0b2ad36`)
**Date**: 2026-05-11
**Author**: QR (autopilot)

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

Sacred constants UNCHANGED. The QR sees iter-v3/051 OOS metrics for the FIRST time in
Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #1 of 10 (FIRST EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)

System-level REVERT to iter-v3/028 architecture (mandated by
`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 with second-cycle
confirmation; SYSTEM-LEVEL CONSTRAINT — NOT axis under test):
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (REVERT — drop ALGO from /050 head)
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (REVERT — clear ALGO+LDO custom multipliers)
  - block_long_for = () (REVERT — clear primitive 10 BCH LONG block)
  - REQUIRED_GAP = 66 = (21+1)*3 (REVERT from 88 due to 3-sym universe)

Single new axis under test:
  ADD `fracdiff_d05_close` to V3_FEATURE_COLUMNS_TOP_N (14 → 15) at universal scope
  (broadcast to all 3 symbols in V3_MODELS).

Carry-forward state (UNCHANGED from iter-v3/028 baseline architecture):
  - V3_FEATURE_COLUMNS_TOP_N = 14 → 15 (ADD fracdiff_d05_close as 15th element)
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
  - V3_FEATURES_PER_SYMBOL = {} (empty)
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
  - adx_threshold_per_symbol = {} (empty)
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)

Predicted classification: PROMISING-clean (35%), PROMISING-INERT (20%), NEGATIVE-clean
  (30%), NEGATIVE-SUSPICIOUS-OOS (15%).
```

**Context**: iter-v3/050 SECOND CONFIRMATION = NO MERGE per Critic FINAL `b6339c5`.
Multi-seed mean +0.32 IS / +0.74 OOS vs iter-v3/028 anchor +0.5101 IS / +0.5053 OOS;
IS regression -0.19 fails BOTH-must-improve rule. SYSTEM-LEVEL CONFIRMATION across 2
cycles of per-symbol-customization anti-pattern (iter-v3/039 cycle 2 + iter-v3/050
cycle 3). Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10
to system-level constraint.

iter-v3/051 = cycle 4 #1 of 10 EXPLORATIONs (per `feedback_v3_strict_10_to_1_cadence.md`).
iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first; do NOT
collapse the 10th EXPLORATION into CONFIRMATION).

The QR EDA (3 scripts at `analysis/iteration_v3-051/` SHA `290f37b`) ranked 4 candidate
axes per Critic FINAL `b6339c5` recommendations #2 + #3 + #5 of iter-v3/050 closeout:
- (a)/(b1) LDO removal alone: REJECTED on EDA IS axis FAIL (-0.015 IS regression)
- (b2/b3/b4) per-symbol customization REVERT: INCORPORATED as system-level mandate
- (c1) fracdiff_d05_close UNIVERSAL: ADVANCED (cycle 4 axis #1 — this brief)
- (c3) regime_momentum_signed_3d UNIVERSAL: QUEUED for /052
- (c2) hurst_drift_50_200: DEFERRED (>2h cap)
- (d) 3-sym universe restoration WITHOUT ALGO: INCORPORATED into setup REVERT

Cycle 4 starting baseline (post-system-level REVERT) = iter-v3/028 architecture exactly.
Single axis under test = fracdiff_d05_close addition.

---

## Section 1 — Hypothesis

Adding `fracdiff_d05_close` to `V3_FEATURE_COLUMNS_TOP_N` at universal scope (14 → 15;
broadcast to all 3 symbols BCH/LDO/TRX) — alongside the SYSTEM-LEVEL REVERT of per-symbol
customizations to iter-v3/028 architecture (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL
= {}; block_long_for = ()) — provides a NEW universal stationary engineered feature with
mean-reversion signal (univariate Spearman ρ ∈ [-0.068, -0.038] significant at p<0.05
across all 4 symbols). Expected effect: bundle IS Sharpe lift +0.05 to +0.30 vs iter-v3/028
baseline reference +0.5101 (single-seed n_trials=35 EXPLORATION-spec); bundle OOS Sharpe Δ
within [-0.20, +0.30] vs /028 anchor +0.5053 (Optuna response uncertain at single-seed but
EDA-evidenced effect signal-positive).

The mechanism: `fracdiff_d05_close` = López de Prado AFML Chapter 5 Fixed-Width Window
Fractional Differentiation at d=0.5 applied to close price. Theoretically: preserves
long-memory property of price series while achieving stationarity (avoids the standard
differencing trade-off between memory loss and unit-root removal). The d=0.5 setting was
chosen by LdP as the empirical sweet spot between memory preservation and stationarity
(d→0 = no diff = non-stationary; d→1 = standard diff = memory loss). The feature is
ALREADY present in all 4 symbol parquets (no feature regeneration required); the iter-v3/035
BCH-only PROMISING precedent (+37.98 OOS swing for BCH at single-seed) suggests the feature
CAN learn signal in the v3 architecture.

The cycle 4 starting hypothesis (iter-v3/050 diary §Cadence): "lift IS Sharpe to ≥ +0.5101
(BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL
axes (per-symbol customizations rejected at bundle level)." This iteration tests whether
fracdiff_d05_close at universal scope can lift IS Sharpe above +0.5101 without sacrificing
OOS edge.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Cycle 4 starting baseline reference (post-system-level REVERT)

The cycle 4 starting baseline = iter-v3/028 architecture exactly (3-sym BCH+LDO+TRX;
default ATR; no primitive 10; 14-feature stack including regime_momentum_signed_5d). The
reference metrics are the iter-v3/028 multi-seed CONFIRMATION-MERGE numbers:

| Metric | iter-v3/028 multi-seed | Source |
|--------|----:|---|
| IS monthly Sharpe | +0.5101 | BASELINE_V3.md (multi-seed mean across 2 outer seeds) |
| OOS monthly Sharpe | +0.5053 | BASELINE_V3.md |
| OOS/IS Sharpe ratio | 0.99 | BASELINE_V3.md |
| IS Trades | 156 (mean per seed) | reports-v3/iteration_v3-028/in_sample/per_symbol.csv |
| OOS Trades | 95 (mean per seed) | reports-v3/iteration_v3-028/out_of_sample/per_symbol.csv |
| IS MaxDD | 41.43% | BASELINE_V3.md |
| OOS MaxDD | 23.53% | BASELINE_V3.md |
| Top OOS concentration | 76.47% (TRX dominant) | BASELINE_V3.md |

Single-seed EXPLORATION reference (NOT directly available; estimated from base rate of
single-seed deviation vs multi-seed mean per cycle 3 EXPLORATION evidence):
- IS Sharpe single-seed band: [+0.40, +0.65] (±0.10 from multi-seed mean +0.51)
- OOS Sharpe single-seed band: [+0.30, +0.80] (±0.20 from multi-seed mean +0.51)

### 2.2 — Candidate axis EDA evidence: fracdiff_d05_close at universal scope

**ADF stationarity (IS subset, full sample) — `axis_c_fracdiff_adf.csv`**:

| symbol | n_is_obs | adf_p_value | stationary_at_p005 |
|---|---:|---:|---|
| BCHUSDT | 5528 | 0.000000 | True |
| LDOUSDT | 2542 | 0.000000 | True |
| TRXUSDT | 5470 | 0.000008 | True |
| ALGOUSDT | 5026 | 0.000086 | True |

**ALL 4 SYMBOLS STATIONARY at p<0.05.** The d=0.5 FFD is empirically achieving stationarity
as theoretically predicted by LdP. (ALGO included in EDA but NOT in iter-v3/051 V3_MODELS.)

Source: `analysis/iteration_v3-051/axis_c_fracdiff_adf.csv`.

**IC matrix — top 5 |IC| pairs across all symbols (carve-out evaluation) —
`axis_c_fracdiff_per_sym_ic.csv`**:

| symbol | candidate | existing_feature | abs_ic | is_source_primitive |
|---|---|---|---:|---|
| LDOUSDT | fracdiff_d05_close | vwap_dev_20 | 0.7381 | YES |
| LDOUSDT | fracdiff_d05_close | regime_momentum_signed_5d | 0.6721 | NO |
| BCHUSDT | fracdiff_d05_close | vwap_dev_20 | 0.6597 | YES |
| BCHUSDT | fracdiff_d05_close | regime_momentum_signed_5d | 0.6402 | NO |
| LDOUSDT | fracdiff_d05_close | ema_spread_atr_20 | 0.5985 | YES |

**The only IC violations (≥ 0.70) are with `vwap_dev_20`** at LDO (0.7381). Both are
close-derived primitives (vwap_dev_20 = (close - vwap)/vwap; fracdiff_d05_close =
FFD(close, d=0.5)). Per `feedback_v3_engineered_feature_pivot.md` Category 2 carve-out:
composed features get IC carve-out vs source primitives. **CARVE-OUT PASSES.**

Post-carve-out max |IC| = 0.6721 with `regime_momentum_signed_5d` at LDO, which is
**BELOW the strict 0.70 gate.** No additional carve-out needed.

Per-symbol max |IC| with existing 14:
- BCHUSDT: 0.6597 (with vwap_dev_20 source) → post-carve-out 0.6402
- LDOUSDT: 0.7381 (with vwap_dev_20 source) → post-carve-out 0.6721
- TRXUSDT: 0.5238 (with vwap_dev_20 source) → post-carve-out ~0.45
- ALGOUSDT: 0.5881 (with vwap_dev_20 source) → post-carve-out ~0.50

**Univariate Spearman ρ vs forward 1-bar return (mean-reversion signal test) —
`axis_c_fracdiff_univariate.csv`**:

| symbol | candidate | n_obs | spearman_rho | spearman_p | significant_at_p005 |
|---|---|---:|---:|---:|---|
| BCHUSDT | fracdiff_d05_close | 5527 | -0.03753 | 0.00526 | True |
| LDOUSDT | fracdiff_d05_close | 2541 | -0.05119 | 0.00985 | True |
| TRXUSDT | fracdiff_d05_close | 5469 | -0.05016 | 0.00021 | True |
| ALGOUSDT | fracdiff_d05_close | 5025 | -0.03849 | 0.00636 | True |

**ALL 4 SYMBOLS SIGNIFICANT at p<0.05** with negative correlation (mean-reversion: when
fracdiff_d05_close is HIGH, next 1-bar return tends to be NEGATIVE). Effect size small
(|ρ| = 0.038 to 0.051) but consistent.

NOTE per `feedback_v3_axis_selection_quant_discipline.md`: univariate Spearman is the
WEAKEST evidence type (warning from iter-v3/070 failure mode); used here as a sanity
check, NOT as primary justification. The primary justification is (1) stationarity,
(2) IC carve-out PASS, (3) presence in parquets, (4) cycle 4 axis #1 priority.

### 2.3 — Why fracdiff_d05_close at universal scope (not per-symbol)?

The system-level constraint from `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (UPDATED
2026-05-10 with second-cycle confirmation across iter-v3/039 + iter-v3/050) BANS per-symbol
customization stacking AT CONFIRMATION. iter-v3/035 used fracdiff_d05_close per-symbol
BCH-only and the iter-v3/039 CONFIRMATION-NO-MERGE rejected the per-symbol bundle (per
`feedback_v3_per_symbol_lifts_oos_breaks_is.md`).

**Universal scope is structurally distinct from per-symbol scope.** The universal scope
adds the feature to V3_FEATURE_COLUMNS_TOP_N (broadcast to all 3 symbols' models); each
symbol's per-symbol model trains on its own data with the new column added. This is NOT
a "per-symbol customization" — it is a uniform global feature addition that respects the
system-level constraint.

The iter-v3/050 diary §Cycle 4 Priorities axis #1 explicitly recommends:
> "fracdiff_d05_close for ALL 4 symbols (universal scope; iter-v3/035 used BCH-only —
> universal scope unstested at multi-seed)"

iter-v3/051 implements this universal-scope retest at the cycle 4 starting baseline (3-sym
BCH+LDO+TRX; ALGO REVERTED per system-level mandate). The test is whether fracdiff_d05_close
at universal scope can lift IS Sharpe above +0.5101 baseline without OOS regression.

### 2.4 — Why fracdiff_d05_close ranked #1 vs regime_momentum_signed_3d?

Both candidates are NEW universal engineered features with similar EDA evidence:

| Criterion | fracdiff_d05_close | regime_momentum_signed_3d |
|---|---:|---:|
| ADF stationarity | All 4 syms p<0.05 | All 4 syms p<0.05 (cleaner: p=0 for all) |
| Max |IC| with existing 14 | 0.7381 (with vwap_dev_20 source) | 0.6192 (with vwap_dev_20 NOT source) |
| IC carve-out needed? | YES (vwap_dev_20 source primitive) | NO (passes strict gate) |
| Univariate Spearman (mean abs) | 0.044 | 0.057 |
| Already in parquets? | YES | NO (dead code in engineered_v3.py:330) |
| Implementation cost | 30-45 min (no feature regen) | 60-80 min (feature regen + dead-code activation) |
| Prior precedent | iter-v3/035 BCH-only PROMISING (+37.98 OOS swing for BCH) | iter-v3/044 EDA-FALSIFIED at ALGO LONG bottleneck (REVERTED before backtest) |
| Stacking risk vs regime_momentum_signed_5d | Moderate (IC 0.67 at LDO) | High (IC 0.47 at BCH; same family) |

**fracdiff_d05_close ranks #1 because**:
1. Lower implementation cost (no feature regen).
2. Empirical PROMISING precedent at iter-v3/035 (BCH-only); universal-scope retest is the
   cycle 4 priority axis.
3. Structurally distinct from regime_momentum_signed_5d (linear FFD transform vs sign-flip
   composed); reduces stacking risk per `feedback_v3_engineered_features_dont_stack.md`.

regime_momentum_signed_3d is QUEUED for iter-v3/052 EXPLORATION as cycle 4 #2 axis
(stronger univariate signal AND cleaner IC pass; would test if /051 is NEGATIVE or to
explore alternative if /051 is PROMISING).

### 2.5 — Other candidate axes EDA-falsified or deferred

| # | Candidate | EDA Status | Rationale |
|---|---|---|---|
| (a)/(b1) | LDO removal alone | REJECTED-IS-FAIL | LDO IS PnL contribution near-zero (+0.85 wpnl at /050); removing LDO from /050 daily PnL gives IS Δ -0.015 (+0.49 → +0.49) BUT OOS Δ +1.51 (+1.17 → +2.02). **FAILS BOTH-must-improve on IS axis.** Per `feedback_v3_strict_both_is_oos_baseline.md`, EDA-rejected. (`axis_a_ldo_attribution.csv`, `axis_b_subaxis_ranking.csv`) |
| (b2) | per-sym ATR REVERT alone | NOT SIMULABLE | Trade rosters from iter-v3/045 vs counterfactual /045-no-ATR differ by Optuna re-tune. No precise EDA evidence. Queued for /053+. |
| (b3) | Primitive 10 REVERT alone | ELIMINATED-LOTTERY | iter-v3/045 single-seed (proxy for primitive 10 OFF) was the lottery winner that compressed -57.3% IS / -79.0% OOS at multi-seed CONFIRMATION (per /050 retrospective). Standalone REVERT at single-seed risks repeating lottery artifact. Queued for /054+. |
| (b4) | Full per-symbol REVERT | INCORPORATED | INCORPORATED into iter-v3/051 setup as system-level mandate; full REVERT IS the cycle 4 starting baseline. NOT an axis under test. |
| (c2) | hurst_drift_50_200 | DEFERRED | New feature code required (~1.5h+ implementation; tight against 2h cap). Queued for /055+. |
| (c3) | regime_momentum_signed_3d UNIVERSAL | QUEUED-#2 | Eligible; cleaner IC pass; stronger univariate; HIGHER implementation cost (~60-80 min). Queued for /052 if /051 NEGATIVE OR fallback if /051 PROMISING with room for compounding. |
| (d) | 3-sym universe restoration WITHOUT ALGO | EQUIVALENT-TO-(b4) | INCORPORATED into iter-v3/051 setup REVERT. Empirically equivalent to b4 (full REVERT) at multi-seed since multi-seed Optuna at 3-sym/default-ATR/no-primitive-10 = iter-v3/028 baseline. |

### 2.6 — IC-gate consideration (Category 2 carve-out applies)

This iteration adds a NEW universal feature column to V3_FEATURE_COLUMNS_TOP_N. IC gate
applies. fracdiff_d05_close has max |IC| = 0.7381 with `vwap_dev_20` (source primitive
— both close-derived). Per `feedback_v3_engineered_feature_pivot.md` Category 2 composed
feature carve-out: composed features get IC carve-out vs their source primitives. Both
fracdiff_d05_close and vwap_dev_20 are linear close-derived — fracdiff_d05_close is
explicitly an FFD transform of close; vwap_dev_20 is (close - vwap)/vwap = (close - rolling
mean of close × volume / rolling sum of volume)/vwap. Both reduce to functions of the same
underlying price series. **CARVE-OUT APPLIES; STRICT GATE BYPASSED.**

Post-carve-out max |IC| = 0.6721 with `regime_momentum_signed_5d` at LDO, which is
BELOW the strict 0.70 gate. NO additional carve-out needed.

Phase 5.5 gate documentation will explicitly justify the carve-out per
`feedback_v3_engineered_feature_pivot.md`.

### 2.7 — Predicted Behavioral Effect (per `feedback_axis_saturation_predictor.md`)

Predicted bundle metrics vs iter-v3/028 baseline reference (single-seed; cycle 4 starting
baseline = iter-v3/028 architecture; ADD fracdiff_d05_close at universal scope):

- **fracdiff_d05_close importance rank**: predicted top-10 in at least 1 of 3 symbols
  (per iter-v3/035 BCH 50%+ split-importance precedent at single-seed n_trials=10). At
  n_trials=35 the search space is wider so top-rank may be diluted; expected top-12 in
  at least 1 of 3 symbols.
- **Bundle IS trade count**: predicted 130-200 (reference: iter-v3/028 IS = 156). The new
  feature may cause Optuna to pick slightly different threshold; expected ±20% drift.
- **Bundle OOS trade count**: predicted 70-110 (reference: iter-v3/028 OOS = 95).
- **Bundle IS Sharpe Δ vs iter-v3/028 baseline reference +0.5101**: predicted **[+0.05,
  +0.30]** (lift; small to moderate). Rationale: stationary feature with significant
  univariate signal across 4 symbols; tree models can use it for split decisions in regions
  where existing 14 features have flat importance distributions (TRX especially).
- **Bundle OOS Sharpe Δ vs iter-v3/028 baseline reference +0.5053**: predicted **[-0.20,
  +0.30]** (uncertain; Optuna response uncertainty at single-seed n_trials=35).
- **IS-OOS daily Sharpe ratio**: predicted ∈ [0.7, 1.5] (clean lift, not suspicious — per
  `feedback_v3_engineered_features_dont_stack.md` falsifier band).

**Falsifier (saturation predictor)**:
- If observed IS Sharpe Δ < -0.10 vs iter-v3/028 baseline reference: NEGATIVE-clean (axis
  CLOSED at /051; pivot to regime_momentum_signed_3d at /052).
- If observed OOS Sharpe Δ < -0.30 vs iter-v3/028 baseline reference: NEGATIVE-clean.
- If fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols: PROMISING-INERT (the
  feature was not learned by the model; INERT-OVERFIT pattern per
  `feedback_v3_inert_features_at_higher_budget.md`).
- If IS-OOS daily Sharpe ratio outside [0.5, 2.0]: NEGATIVE-SUSPICIOUS-OOS (the
  iter-v3/026/027 anti-pattern).
- If IS trade count change > 30% relative vs iter-v3/028 reference: cascade effect;
  investigate.

**Per-symbol Optuna independence prediction**: BCH, LDO, TRX models train independently
with the new feature added to their input matrix. Since fracdiff_d05_close is universal
(broadcast), all 3 symbols see the same column added to their respective parquets. The
expected per-symbol importance distribution will reflect each symbol's underlying signal
strength in the feature.

### Analysis Scripts

3 EDA scripts committed at SHA `290f37b`:
- `analysis/iteration_v3-051/multi_axis_eda.py` — main EDA covering 4 candidate axes
  (a/b/c/d) + regime_momentum importance investigation. 5 CSV outputs.
- `analysis/iteration_v3-051/axis_c_fracdiff_deep_dive.py` — fracdiff_d05_close per-symbol
  IC + ADF + univariate (the SELECTED axis). 3 CSV outputs.
- `analysis/iteration_v3-051/axis_c_regime_3d_compute.py` — regime_momentum_signed_3d
  on-the-fly EDA (the QUEUED-#2 axis). 3 CSV outputs.

Plus 2 markdown synthesis files (`synthesis.md` + `candidate_axes_ranking.md`). Full
audit chain documented.

---

## Section 3 — Proposed Changes

### Sub-fix 1: REVERT V3_MODELS to 3-symbol BCH+LDO+TRX (system-level mandate)

In `run_baseline_v3.py:V3_MODELS` (around line 117), REVERT to 3-sym universe:

```python
# iter-v3/051: REVERT V3_MODELS to 3-symbol BCH+LDO+TRX per system-level rule
# `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
# confirmation of per-symbol-customization anti-pattern at multi-seed CONFIRMATION).
# Cycle 4 starting baseline = iter-v3/028 architecture exactly. ALGO REVERTED.
# Per `analysis/iteration_v3-051/synthesis.md` SHA `290f37b` (cycle 4 #1 EDA).
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)
```

### Sub-fix 2: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL to empty (system-level mandate)

In `run_baseline_v3.py:V3_ATR_MULTIPLIERS_PER_SYMBOL` (around line 578), REVERT to empty:

```python
# iter-v3/051: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL to {} (clear per-symbol custom ATR
# multipliers ALGOUSDT and LDOUSDT) per system-level rule
# `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. All 3 symbols use DEFAULT_ATR_MULTIPLIERS
# = (2.0, 1.0). Per `analysis/iteration_v3-051/synthesis.md` SHA `290f37b`.
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {}
```

### Sub-fix 3: REVERT block_long_for to empty (system-level mandate)

In `run_baseline_v3.py:_build_v3_model` RiskV2Config initialization (around line 1304),
REVERT primitive 10:

```python
risk_cfg = RiskV2Config(
    zscore_threshold=2.0,
    adx_threshold=20.0,  # GLOBAL (universal across all 3 symbols at iter-v3/051)
    adx_threshold_per_symbol={},  # empty (UNCHANGED from iter-v3/050)
    # iter-v3/051: REVERT primitive 10 BCH LONG block per system-level rule
    # `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. block_long_for cleared.
    # Per `analysis/iteration_v3-051/synthesis.md` SHA `290f37b`.
    block_long_for=(),  # REVERT (was ("BCHUSDT",) at iter-v3/050)
    block_short_for=(),  # UNCHANGED
    # ... other fields unchanged ...
)
```

### Sub-fix 4: UPDATE REQUIRED_GAP for 3-symbol universe

In `run_baseline_v3.py:CPCV_EMBARGO` block (around line 140), UPDATE REQUIRED_GAP comment
and value:

```python
# iter-v3/051: REVERT REQUIRED_GAP from 88 → 66 = (21+1)*3 due to V3_MODELS contraction
# 4 → 3 symbols (drop ALGO). Per system-level rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.
# DO NOT use min(REQUIRED_GAP, n_trades//20) — that is the iter-v3/001 bug.
```

(REQUIRED_GAP is computed dynamically from V3_MODELS length in `_build_v3_model` — verify
the runner uses the correct value at runtime.)

### Sub-fix 5: ADD fracdiff_d05_close to V3_FEATURE_COLUMNS_TOP_N (single axis under test)

In `src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N` (around line 235),
ADD `fracdiff_d05_close` as the 15th element (after `regime_momentum_signed_5d`):

```python
    "regime_momentum_signed_5d",
    # iter-v3/051: fracdiff_d05_close ADDED at universal scope (14 → 15) — cycle 4 #1
    # EXPLORATION axis. NEW universal engineered feature axis re-opened for cycle 4 per
    # iter-v3/050 diary §Cycle 4 Priorities axis #1.
    # fracdiff_d05_close = LdP AFML Ch. 5 Fixed-Width Window Fractional Differentiation
    # at d=0.5 applied to close. Theoretically: preserves long-memory while achieving
    # stationarity (LdP empirical sweet-spot d=0.5).
    # Already implemented (compute_fracdiff_d05_close in fracdiff_v3.py); already in all
    # 4 symbol parquets (BCH/LDO/TRX/ALGO; ALGO available for future re-inclusion).
    # iter-v3/035 BCH-only PROMISING precedent (+37.98 OOS swing for BCH); universal scope
    # UNTESTED at multi-seed per /050 diary recommendation.
    # EDA evidence (`analysis/iteration_v3-051/axis_c_fracdiff_*.csv` SHA `290f37b`):
    # - ADF stationary at p<0.05 across all 4 symbols (BCH/LDO/TRX/ALGO p≈0)
    # - IC carve-out PASS: max |IC| = 0.7381 with vwap_dev_20 (source close-derived
    #   primitive); post-carve-out max |IC| = 0.6721 < 0.70 strict gate
    # - Univariate Spearman significant at all 4 symbols (mean ρ = -0.044 negative
    #   mean-reversion signal)
    # Per `feedback_v3_engineered_feature_pivot.md` Category 2 carve-out applies.
    # Per `feedback_v3_engineered_features_proven.md` (iter-v3/025 regime_momentum
    # PROMISING precedent + iter-v3/028 multi-seed CONFIRMATION-MERGE): composed
    # engineered features CAN work at universal scope.
    "fracdiff_d05_close",
)
```

(Update the docstring on the tuple to "Top-15 feature subset (as of iter-v3/051)" plus
the iter-v3/051 history block.)

### Sub-fix 6: UPDATE `_verify_feature_columns` assertions

In `run_baseline_v3.py:_verify_feature_columns` (around line 193):

1. UPDATE the docstring for iter-v3/051 (REVERT + ADD axis description).
2. UPDATE `n != 14` → `n != 15`.
3. ADD assertion that `fracdiff_d05_close` MUST BE PRESENT in V3_FEATURE_COLUMNS_TOP_N:

```python
if "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N:
    raise RuntimeError(
        "fracdiff_d05_close NOT in V3_FEATURE_COLUMNS_TOP_N — iter-v3/051 axis ADD missing. "
        "Add 'fracdiff_d05_close' as 15th element of V3_FEATURE_COLUMNS_TOP_N in "
        "src/crypto_trade/features_v3/__init__.py."
    )
print("  fracdiff_d05_close PRESENT in V3_FEATURE_COLUMNS_TOP_N (iter-v3/051 axis)  PASS")
```

4. UPDATE assertions for V3_MODELS (3-sym), V3_ATR_MULTIPLIERS_PER_SYMBOL (empty),
   block_long_for (empty); these were all REVERTed.

5. REMOVE assertions referencing iter-v3/049/050 specific state:
   - DELETE assertion that V3_ATR_MULTIPLIERS_PER_SYMBOL has 2 entries
   - DELETE assertion that block_long_for == ("BCHUSDT",)
   - DELETE assertion that adx_threshold_per_symbol == {} (still keep this, since the
     field is empty by default)

### Sub-fix 7: ADD adversarial tests `tests/features_v3/test_fracdiff_d05_universal.py`

5 mandatory tests (all PASS at setup commit):

1. `test_fracdiff_d05_close_in_universal_feature_list` — `fracdiff_d05_close` MUST be in
   `V3_FEATURE_COLUMNS_TOP_N`; verify it is the 15th element (n=15 total).
2. `test_fracdiff_d05_close_present_in_all_4_symbol_parquets` — all 4 symbol parquets
   (BCH/LDO/TRX/ALGO; ALGO reserved-for-future even though not in /051 V3_MODELS) must
   have `fracdiff_d05_close` column.
3. `test_fracdiff_d05_close_stationary_per_symbol` — ADF p<0.05 for fracdiff_d05_close
   in IS subset of each symbol's parquet (smoke test).
4. `test_fracdiff_d05_close_no_lookahead` — verify the FFD computation uses past-only
   data (the `compute_fracdiff_d05_close` function in fracdiff_v3.py uses Fixed-Width
   Window FFD which is past-only by construction; verify the convention).
5. `test_v3_models_is_3_symbol_at_iter_v3_051` — V3_MODELS must be (BCH, LDO, TRX) at
   iter-v3/051 (regression test against accidental ALGO re-add).

### Sub-fix 8: UPDATE ITERATION_LABEL

In `run_baseline_v3.py`, change `ITERATION_LABEL = "v3-050"` to
`ITERATION_LABEL = "v3-051"`.

### Sub-fix 9: NO feature regeneration required

The `fracdiff_d05_close` column is already present in all 4 symbol parquets at
`data/features_v3/{SYMBOL}_8h_features.parquet`. No `uv run crypto-trade features --track
v3` invocation needed. (Saves 5-10 min vs feature-add iterations.)

### Sub-fix 10: USE --clean-oof guardrail

The iter-v3/051 backtest invocation should use the `--clean-oof` flag (introduced at SHA
`6a216b5` to prevent OOF parquet contamination):

```bash
uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

### Bundle state verification (what `_verify_feature_columns` must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 15 features (ADD fracdiff_d05_close — iter-v3/051 axis)        PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                           PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries (REVERT — system-level mandate)                  PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                            PASS
features_for_symbol("BCHUSDT") == 15 features (TOP_N fallback)                            PASS
features_for_symbol("LDOUSDT") == 15 features (TOP_N fallback)                            PASS
features_for_symbol("TRXUSDT") == 15 features (TOP_N fallback)                            PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)                 PASS
"fracdiff_d05_close" IN V3_FEATURE_COLUMNS_TOP_N (NEW iter-v3/051)                        PASS
"vol_normalized_ret_5d" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/049)             PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (queued iter-v3/052)          PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/043)               PASS
V3_MODELS = (BCH, LDO, TRX) — 3 symbols (REVERT — system-level mandate)                   PASS
ALGOUSDT NOT IN V3_MODELS (REVERT)                                                        PASS
REQUIRED_GAP = 66 = (21+1) x 3 (REVERT)                                                   PASS
Primitive 10: BCH model risk_cfg.block_long_for == () (REVERT — system-level mandate)     PASS
Primitive 10: BCH model risk_cfg.block_short_for == () (UNCHANGED)                        PASS
Per-symbol ADX: risk_cfg.adx_threshold_per_symbol == {} (UNCHANGED)                       PASS
ITERATION_LABEL == "v3-051" (UPDATED)                                                     PASS
```

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted Bands (single-seed, vs iter-v3/028 baseline reference)

**IS Sharpe prediction (single-seed, vs iter-v3/028 multi-seed mean +0.5101)**:
- Predicted band: **[+0.55, +0.85]** vs iter-v3/028 anchor +0.5101 (lift +0.05 to +0.30)
- More conservative point estimate: +0.55 to +0.65 (lift +0.05 to +0.15) given single-seed
  EXPLORATION variability and Optuna response uncertainty
- Rationale: stationary feature with significant univariate signal across 4 symbols (mean
  ρ = -0.044 negative mean-reversion); tree models can use it for split decisions in
  regions where existing 14 features have flat importance distributions (TRX especially).
  iter-v3/035 BCH-only PROMISING precedent (+37.98 OOS swing for BCH at single-seed) shows
  the feature CAN learn signal in the v3 architecture.

**OOS Sharpe prediction (single-seed, vs iter-v3/028 multi-seed mean +0.5053)**:
- Predicted band: **[+0.30, +0.85]** vs iter-v3/028 anchor +0.5053 (regression up to -0.20
  OR lift up to +0.30)
- More conservative point estimate: +0.40 to +0.55 (slight regression to slight lift)
- Rationale: NEW universal feature at single-seed n_trials=35 carries the iter-v3/026/027
  pattern risk (NEGATIVE-SUSPICIOUS-OOS at IS-OOS daily ratio outside [0.5, 2.0]). The
  single-seed Optuna lottery may pick suboptimal hyperparameters that show different OOS
  vs IS responses.

### 4.2 Behavioral-Effect Predictor (per `feedback_v3_axis_saturation_predictor.md`)

**fracdiff_d05_close importance rank predictions**:
- BCH: predicted top-10 in 15 (per /035 BCH-only 50%+ split-importance precedent)
- LDO: predicted top-12 in 15 (univariate ρ=-0.051 strongest of 3 syms)
- TRX: predicted top-12 in 15 (univariate ρ=-0.050; TRX has flat importance distribution
  so a new feature with signal should rank reasonably)

If fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols: PROMISING-INERT.
If fracdiff_d05_close importance rank > 13/15 in EXACTLY 2 of 3 symbols (e.g., LDO + TRX
inert; BCH learns it): PROMISING-mixed (axis under qualified discussion in /052+).

**Trade count predictions**:
- Bundle IS trade count: 130-200 (reference: iter-v3/028 IS = 156)
- Bundle OOS trade count: 70-110 (reference: iter-v3/028 OOS = 95)
- Per-symbol IS trade count change: predicted ±20% per symbol vs iter-v3/028 reference
  - BCH: 70-100 (was 86 at /028)
  - LDO: 9-13 (was 11 at /028; small sample so wide variability)
  - TRX: 70-100 (was 85 at /028)

**Behavioral-effect bands (cycle 4 #1 EXPLORATION)**:
- If observed IS Sharpe Δ falls outside [+0.05, +0.30] but inside [-0.10, +0.05]:
  PROMISING-INERT. The naive +0.10 IS Sharpe lift didn't materialize; Optuna response
  neutralizes the new feature.
- If observed OOS Sharpe Δ < -0.30: NEGATIVE-clean. Pivot to regime_momentum_signed_3d
  at /052.
- If observed IS trade count change > 30% relative: cascade effect; investigate.
- If IS-OOS daily Sharpe ratio outside [0.5, 2.0]: NEGATIVE-SUSPICIOUS-OOS.

### 4.3 OOS falsifier (pre-registered)

- If fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols: PROMISING-INERT (the
  EDA finding doesn't generalize; 3 syms predicted top-12 in at least 1 sym).
- If observed bundle IS trade count change > 30% relative vs iter-v3/028 reference (156):
  investigate cascade effects.
- If IS-OOS daily Sharpe ratio outside [0.5, 2.0] band: NEGATIVE-SUSPICIOUS-OOS (per
  `feedback_v3_engineered_features_dont_stack.md`).

**Pathway-A trigger (PROMISING-clean)**:
- Bundle IS Sharpe Δ ≥ +0.05 vs iter-v3/028 anchor +0.5101 (i.e. IS Sharpe ≥ +0.56) AND
- Bundle OOS Sharpe Δ ≥ -0.20 vs iter-v3/028 anchor +0.5053 (i.e. OOS Sharpe ≥ +0.31) AND
- fracdiff_d05_close importance rank ≤ 12/15 in at least 1 of 3 symbols AND
- IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]

**Pathway-B trigger (PROMISING-INERT)**:
- fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols (gate not firing as expected)
- AND Bundle IS Sharpe Δ ∈ [-0.10, +0.05]

**Pathway-C trigger (NEGATIVE-clean)**:
- Bundle IS Sharpe Δ < -0.10 OR
- Bundle OOS Sharpe Δ < -0.30

**Pathway-C-suspicious trigger (NEGATIVE-SUSPICIOUS-OOS)**:
- IS-OOS daily Sharpe ratio outside [0.5, 2.0] band

**Action on PATH C-clean**: fracdiff_d05_close UNIVERSAL axis CLOSED for cycle 4. Pivot to
regime_momentum_signed_3d UNIVERSAL at iter-v3/052 (cycle 4 #2 axis).

**Action on PATH C-suspicious**: NEGATIVE-SUSPICIOUS-OOS (cannot be cited as evidence per
`feedback_v3_engineered_features_dont_stack.md`). Pivot to regime_momentum_signed_3d at
iter-v3/052.

**Action on PATH B (PROMISING-INERT)**: Drop fracdiff_d05_close at iter-v3/052 setup;
restore 14-feature stack. Pivot to alternative axis at /052.

**Action on PATH A (PROMISING-clean)**: fracdiff_d05_close UNIVERSAL carries forward to
iter-v3/052+ as cycle 4 PROMISING bundle ingredient. iter-v3/052 tests
regime_momentum_signed_3d UNIVERSAL on top of the verified fracdiff_d05_close UNIVERSAL
baseline (or alternative axis if 3d univariate signal is too redundant with 5d).

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace EXPANDED from
14-D to 15-D (fracdiff_d05_close added). Mahalanobis distance gate operates on the new
15-D subspace; expected OOD fire rate within ±5% of /028 baseline (the new feature is
stationary so distribution shift expected to be minimal).

**Primitive 10 (BCH LONG block)**: REVERTED — `block_long_for=()` per system-level mandate.

**Per-symbol ATR (V3_ATR_MULTIPLIERS_PER_SYMBOL)**: REVERTED — empty per system-level mandate.

**Per-symbol ADX (adx_threshold_per_symbol)**: empty (UNCHANGED from /049 closeout).

**Primitive 9 (regime gate)**: unchanged. `enable_regime_gate=False` (NOT enabled this
iteration; regime-conditional axis was EDA-falsified at iter-v3/048 + iter-v3/049).

**NEW: fracdiff_d05_close at universal scope (iter-v3/051 axis)**: feature added to all
3 symbols' input matrix. No feature regeneration required (already in parquets).

**Cross-symbol contagion risk**: The feature is BROADCAST to all 3 symbols' models. Each
per-symbol model trains independently with the same column added; no cross-symbol
contamination at the feature-engineering layer. The `--clean-oof` guardrail prevents OOF
parquet contamination at the prediction layer.

**Universe contraction risk (4 → 3 syms)**: ALGO REVERTED per system-level mandate. The
3-sym universe (BCH, LDO, TRX) is the iter-v3/028 baseline universe — 24 months of
multi-seed CONFIRMATION-MERGE evidence (+0.5101 IS / +0.5053 OOS) confirms the universe
is structurally viable. REQUIRED_GAP correctly recomputed to 66 = (21+1)*3.

**Risk-budget redistribution risk**: REVERT of per-symbol customizations means the bundle
returns to /028 risk-gate composition (7 primitives: BTC trend kill, vol scaling, ADX
threshold 20.0 global, Hurst regime check, z-score OOD, low-vol filter, hit-rate disabled).
NO new risk gate added. The new feature only changes the model input matrix; risk gates
operate downstream.

**IS trade-rate stability**: Bundle IS trades expected within ±20% of iter-v3/028
reference (156 → 130-200). If portfolio total deviates > 30% relative, investigate
feature-pipeline consistency.

**Adversarial-tests regression risk**: The 5 fracdiff_d05_universal tests + the 5
per_symbol_adx_threshold tests + the 7 primitive 10 tests + the 5 per_symbol_atr tests
+ existing primitive 9 + per_symbol_cap tests all PASS at the setup commit. If any
regress in CI before backtest runs, the iteration is BLOCKED.

**Multi-run-stochasticity risk** (per iter-v3/048 forensic correction): single-process
invocation discipline applies. The `--clean-oof` guardrail at SHA `6a216b5` PREVENTS
the OOF parquet duplication observed during iter-v3/047/048 attribution forensics.
Single-process invocation: run the iter-v3/051 backtest ONCE and record the result;
do NOT re-run for cleaner numbers (peeking-at-OOS violation per
`feedback_no_cheating.md`).

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

All 10 risk gates carried forward from iter-v3/050 with REVERTs to /028 baseline state.
NO new GATES added.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | RiskV2Config | threshold=20.0 GLOBAL; per-symbol={} | None (per-symbol REVERT carried forward from /050 closeout) |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, **15-D space** | UP from 14-D (fracdiff_d05_close ADDED) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |
| 8 — Per-symbol cap | RiskV2Config | enable_per_symbol_cap=False | None (CLOSED at /020) |
| 9 — Regime gate | RiskV2Config | enable_regime_gate=False | None (CLOSED at /022) |
| 10 — Direction block | RiskV2Config | block_long_for=(); block_short_for=() | **REVERT — system-level mandate** |

**Predicted OOD fire rate (Gate 6)**: within ±5% of iter-v3/028 baseline. The 15-D feature
subspace adds a stationary mean-reverting feature; covariance shift expected to be minimal.
Mahalanobis distance computation on 15-D subspace is mathematically well-defined (still
positive-definite if all 15 features have non-zero variance, which they do per ADF tests).

**Predicted ADX gate fire rate**: unchanged from /028 baseline (ADX threshold 20.0 global;
per-symbol overrides empty).

**Predicted primitive 10 fire rate**: 0 (block_long_for empty); the gate exists in code
but does not fire for any symbol at iter-v3/051.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-clean — clean lift; 35% probability)**:
fracdiff_d05_close shows importance rank ≤ 12/15 in at least 1 of 3 symbols (most likely
BCH per /035 precedent or LDO per strongest univariate ρ=-0.051). Bundle IS Sharpe lift
+0.05 to +0.30 vs iter-v3/028 anchor; OOS Sharpe Δ within [-0.20, +0.30] (clean range).
IS-OOS daily Sharpe ratio ∈ [0.7, 1.5] (clean lift, not suspicious). Classification:
PROMISING-clean. Compoundable at iter-v3/052+ as fracdiff_d05_close UNIVERSAL ingredient.
**Probability: 35%.**

**Second plausible failure mode (NEGATIVE-clean — IS or OOS regression at single-seed; 30%
probability)**:
Single-seed Optuna lottery produces different per-symbol picks at the modified feature
matrix (15-D vs 14-D). Could be lower-quality picks at TRX (which has flat importance
distribution) or LDO (which has small sample). Bundle IS Sharpe Δ < -0.10 OR Bundle OOS
Sharpe Δ < -0.30. Classification: NEGATIVE-clean. fracdiff_d05_close UNIVERSAL axis CLOSED
for cycle 4; pivot to regime_momentum_signed_3d UNIVERSAL at iter-v3/052. **Probability:
30%.**

**Third plausible failure mode (PROMISING-INERT — Optuna doesn't learn; 20% probability)**:
fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols (the model ignores the new
feature; Optuna picks heavily-correlated existing features instead). Bundle IS Sharpe Δ
∈ [-0.10, +0.05]. Classification: PROMISING-INERT per
`feedback_v3_inert_features_at_higher_budget.md`. Action: drop fracdiff_d05_close at
iter-v3/052 setup; pivot to regime_momentum_signed_3d UNIVERSAL. **Probability: 20%.**

**Fourth plausible failure mode (NEGATIVE-SUSPICIOUS-OOS — iter-v3/026/027 anti-pattern;
15% probability)**:
IS Sharpe collapses (Δ < -0.10) AND OOS Sharpe spikes implausibly (Δ > +1.0). IS-OOS
daily Sharpe ratio outside [0.5, 2.0] band. Per
`feedback_v3_engineered_features_dont_stack.md`, this is the iter-v3/026/027 pattern
applied to NEW universal features (not stacking but single-feature addition). The
fracdiff_d05_close has IC 0.67 with regime_momentum_signed_5d at LDO — moderate
correlation with the existing iter-v3/028 edge ingredient. Stacking risk could fire
at single-seed n_trials=35 single-seed lottery. Classification: NEGATIVE-SUSPICIOUS-OOS
(rejected as single-seed lottery; cannot be cited as evidence). Action: pivot to
regime_momentum_signed_3d at iter-v3/052. **Probability: 15%.**

**What the gates should catch**:
- Sub-fix 6 assertion: `fracdiff_d05_close` MUST BE PRESENT in V3_FEATURE_COLUMNS_TOP_N.
  If wrong, runner BLOCKS at startup.
- Sub-fix 7 tests: 5 adversarial tests catch implementation bugs (universal-list semantics,
  parquet presence, ADF stationarity smoke test, no-lookahead convention, V3_MODELS 3-sym).
- Gate 6 (OOD): Mahalanobis distance computation on 15-D space; if singular covariance
  matrix or numerical issues, runner reports diagnostic.
- Per-symbol importance assertions: check that `model_importance_last_month_*.csv` files
  contain `fracdiff_d05_close` row (validates the feature reached the model).
- Bundle IS trade count: predicted 130-200. Larger drift signals risk-gate cascade or
  feature-pipeline issue.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  Bundle IS Sharpe Δ ≥ +0.05 vs iter-v3/028 anchor +0.5101 (i.e. IS Sharpe ≥ +0.56)
  AND Bundle OOS Sharpe Δ ≥ -0.20 vs iter-v3/028 anchor +0.5053 (i.e. OOS Sharpe ≥ +0.31)
  AND fracdiff_d05_close importance rank ≤ 12/15 in at least 1 of 3 symbols
  AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]
  Classification: PROMISING-clean. fracdiff_d05_close UNIVERSAL contributes positive lift.
  Catalog entry: candidate for iter-v3/052+ EXPLORATION as compoundable bundle ingredient.

**PATH B — PROMISING-INERT**:
  fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols (gate not firing — Optuna
  does not learn the feature)
  AND Bundle IS Sharpe Δ ∈ [-0.10, +0.05]
  AND Bundle OOS Sharpe Δ ∈ [-0.30, +0.30]
  Classification: PROMISING-INERT per
  `feedback_v3_inert_features_at_higher_budget.md`. Action: drop fracdiff_d05_close at
  iter-v3/052 setup; pivot to regime_momentum_signed_3d UNIVERSAL.

**PATH C-clean — NEGATIVE-clean**:
  Bundle IS Sharpe Δ < -0.10 (IS regression dominates) OR
  Bundle OOS Sharpe Δ < -0.30 (OOS regression dominates)
  Classification: NEGATIVE-clean. fracdiff_d05_close UNIVERSAL axis CLOSED for cycle 4.
  Action: pivot to regime_momentum_signed_3d UNIVERSAL at iter-v3/052.

**PATH C-suspicious — NEGATIVE-SUSPICIOUS-OOS**:
  IS-OOS daily Sharpe ratio outside [0.5, 2.0] band per
  `feedback_v3_engineered_features_dont_stack.md`. The iter-v3/026/027 anti-pattern
  applied to NEW universal feature addition.
  Classification: NEGATIVE-SUSPICIOUS-OOS. Cannot be cited as evidence.
  Action: pivot to regime_momentum_signed_3d UNIVERSAL at iter-v3/052.

**Pre-registered classification thresholds (LOCKED before backtest)**:
- PATH A: IS Sharpe Δ ≥ +0.05 vs /028 AND OOS Sharpe Δ ≥ -0.20 vs /028 AND
  fracdiff_d05_close importance rank ≤ 12/15 in ≥1 of 3 symbols AND IS-OOS daily ratio ∈ [0.5, 2.0]
- PATH B: fracdiff_d05_close importance rank > 13/15 in ALL 3 symbols AND
  IS Sharpe Δ ∈ [-0.10, +0.05] AND OOS Sharpe Δ ∈ [-0.30, +0.30]
- PATH C-clean: IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30
- PATH C-suspicious: IS-OOS daily Sharpe ratio outside [0.5, 2.0]

These thresholds are LOCKED and CANNOT be post-hoc renegotiated per cycle 4 discipline
inherited from cycle 3.

**Note on PATH A IS-Δ threshold**: The +0.05 threshold (vs the standard +0.10) reflects
the EDA-evidenced effect being modest (~+0.10 to +0.30 IS Sharpe lift max). A +0.10
threshold would require the upper-band prediction to materialize. The +0.05 threshold is
more honest about the expected effect size at single-seed. Pre-registered.

**Saturation rule**: If iter-v3/051 produces PATH C-clean OR PATH C-suspicious, the
fracdiff_d05_close UNIVERSAL axis is CLOSED for cycle 4. Combined with cycle 3 closures
(per-symbol cap /020, BTC regime gate /022, primitive 10 BCH /047, vol_normalized_ret_5d
/048, per-symbol ADX /049), this would be the 6th universal axis closure in v3 history.
iter-v3/052 pivots to regime_momentum_signed_3d UNIVERSAL (cycle 4 #2 axis).

If iter-v3/051 produces PATH B (PROMISING-INERT), fracdiff_d05_close is dropped from
V3_FEATURE_COLUMNS_TOP_N at iter-v3/052 setup and the alternative axis is tested.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/045/046/047/048/049/050 reproducibility stamp. No new
libraries introduced. The `fracdiff_d05_close` column is already present in all 4 symbol
parquets (no feature regeneration); `compute_fracdiff_d05_close` in `fracdiff_v3.py` uses
only numpy + pandas + scipy.

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels for all
statistical tests (ADF, PBO, DSR, PSR). The `compute_fracdiff_d05_close` function is a
pure numpy/pandas implementation of the LdP AFML Ch. 5 Fixed-Width Window FFD algorithm
(NO external library needed).

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA basis**: 3 EDA scripts at `analysis/iteration_v3-051/` committed at SHA `290f37b`:
- `multi_axis_eda.py` — main EDA covering 4 candidate axes (a/b/c/d) + regime_momentum
  importance investigation. 5 CSV outputs.
- `axis_c_fracdiff_deep_dive.py` — fracdiff_d05_close per-symbol IC + ADF + univariate
  (the SELECTED axis). 3 CSV outputs.
- `axis_c_regime_3d_compute.py` — regime_momentum_signed_3d on-the-fly EDA (the QUEUED-#2
  axis). 3 CSV outputs.

Plus 9 CSV outputs and 2 markdown synthesis files (`synthesis.md` +
`candidate_axes_ranking.md`).

Establishes:
- Cycle 4 #1 EXPLORATION: 4 candidate axes ranked by quantitative basis.
- 3 of 4 candidates ELIMINATED, REJECTED, or DEFERRED at EDA stage:
  - (a)/(b1) LDO removal alone: REJECTED-IS-FAIL (-0.015 IS regression at /050; FAILS
    BOTH-must-improve on IS axis)
  - (b2) per-sym ATR REVERT alone: NOT PRECISELY SIMULABLE; queued for /053+
  - (b3) primitive 10 REVERT alone: ELIMINATED-LOTTERY (single-seed compression precedent)
  - (b4) full per-symbol REVERT: INCORPORATED into iter-v3/051 setup as system-level
    mandate (NOT axis under test)
  - (c2) hurst_drift_50_200: DEFERRED (>2h cap; new feature code required)
  - (d) 3-sym universe restoration WITHOUT ALGO: INCORPORATED into iter-v3/051 setup
    (empirically equivalent to b4)
- (c1) fracdiff_d05_close UNIVERSAL: ADVANCED (cycle 4 #1 — this brief)
- (c3) regime_momentum_signed_3d UNIVERSAL: QUEUED for /052 as cycle 4 #2 axis

**Critical methodological correction (EDA discipline)**: The system-level rule from
`feedback_v3_per_symbol_lifts_oos_breaks_is.md` (UPDATED 2026-05-10 with second-cycle
confirmation across iter-v3/039 + iter-v3/050) MANDATES the per-symbol customization REVERT
as the cycle 4 starting baseline. This is NOT an axis under test — it is the new structural
baseline. The single axis under test (fracdiff_d05_close UNIVERSAL) is added ON TOP of the
REVERTed baseline.

**Original orchestrator pick**: orchestrator did NOT pre-commit a NEW axis (per
`feedback_v3_axis_selection_quant_discipline.md` discipline since iter-v3/044). The
orchestrator delegates axis selection to QR via committed EDA. The 4 SEED CANDIDATES
listed in iter-v3/050 diary §Cycle 4 Priorities (LDO removal, per-symbol REVERT, NEW
universal engineered features, 3-sym universe restoration) are SEED IDEAS only — the QR
scored these via EDA-driven quantitative basis.

**QR-driven selection**: fracdiff_d05_close at universal scope (Candidate (c1) in
`analysis/iteration_v3-051/candidate_axes_ranking.md`). EDA evidence:

1. **Cycle 4 HIGH-priority axis #1** per Critic FINAL `b6339c5` recommendation #5 of
   iter-v3/050 closeout (explicitly cited in /050 diary §Cycle 4 Priorities axis #1).

2. **EDA-validated quantitative basis**: ADF stationary at p<0.05 across all 4 symbols;
   IC carve-out PASS (max |IC| = 0.7381 with vwap_dev_20 source primitive; post-carve-out
   max |IC| = 0.6721 < 0.70 strict gate); univariate Spearman significant at p<0.05 across
   all 4 symbols.

3. **Categorically distinct from prior closed cycle 3 axes**: cycle 3 NEW universal
   engineered feature axis CLOSED at iter-v3/048 (5 attempts) — cycle 4 RE-OPENS the axis
   per /050 diary recommendation. fracdiff_d05_close at universal scope is the FIRST
   cycle 4 attempt.

4. **Per `feedback_v3_structural_over_knob_exploration.md`**: NEW universal feature family
   axis (highest priority).

5. **Per `feedback_v3_engineered_features_proven.md`**: composed engineered features CAN
   work at universal scope (iter-v3/025/028 regime_momentum precedent).

6. **iter-v3/035 BCH-only PROMISING precedent**: fracdiff_d05_close already showed +37.98
   OOS swing for BCH at single-seed; universal-scope retest is the cycle 4 priority axis
   per /050 diary recommendation.

7. **Implementation feasible within 2h cap**: 30-45 min setup + 25-35 min backtest =
   ≤1.5h. NO feature regeneration required (already in parquets).

8. **System-level constraint compliance**: per-symbol customizations REVERTED as part of
   the new cycle 4 starting baseline. The single axis under test (fracdiff_d05_close
   UNIVERSAL) is a UNIVERSAL addition, NOT a per-symbol customization. Respects the
   `feedback_v3_per_symbol_lifts_oos_breaks_is.md` system-level rule.

9. **Single-seed lottery risk acknowledged**: per
   `feedback_v3_engineered_features_dont_stack.md`, any new engineered feature at
   single-seed n_trials=35 carries the iter-v3/026/027 NEGATIVE-SUSPICIOUS-OOS pattern
   risk. Pre-registered Falsifier (PATH C-suspicious): IS-OOS daily Sharpe ratio outside
   [0.5, 2.0] band.

**Cross-validation against alternative axis (regime_momentum_signed_3d)**:
- Both candidates have similar EDA evidence (stationarity, IC, univariate signal)
- regime_momentum_signed_3d has CLEANER IC pass (max |IC| = 0.6192 < 0.70 strict gate;
  no carve-out needed)
- regime_momentum_signed_3d has STRONGER univariate signal (mean ρ = -0.057 vs -0.044)
- BUT: regime_momentum_signed_3d requires feature regeneration (~5-10 min) + dead-code
  activation (~3 LOC change in engineered_v3.py); higher implementation cost (60-80 min
  vs 30-45 min)
- AND: regime_momentum_signed_3d was EDA-FALSIFIED at iter-v3/044 by QR EDA at the
  bottleneck symbol (ALGO LONG WR 22.2%/13.3%); the falsification may not apply at
  iter-v3/051 (ALGO REVERTED) but creates additional risk
- AND: stacking risk with regime_momentum_signed_5d (IC 0.47 at BCH) is HIGHER than
  fracdiff_d05_close (IC 0.67 at LDO) per `feedback_v3_engineered_features_dont_stack.md`
- DECISION: fracdiff_d05_close ranked #1; regime_momentum_signed_3d QUEUED for /052

**Adversarial review preparation (anticipating Critic challenges)**:
- Q: "Why not test the per-symbol REVERT alone first as a sanity check?"
  A: The full REVERT is identity to iter-v3/028 baseline (already at multi-seed
  +0.5101 IS / +0.5053 OOS). Standalone REVERT test would consume an EXPLORATION slot
  to re-confirm baseline. The cycle 4 #1 ADD axis incorporates the REVERT in the setup.
- Q: "Why not test LDO removal alone — the structural drag is the strongest empirical
  signal?"
  A: LDO removal FAILS BOTH-must-improve on IS axis at EDA stage (-0.015 IS regression
  vs +1.51 OOS lift). Per `feedback_v3_strict_both_is_oos_baseline.md`, EDA-rejected.
  Queued for /052+ as universe-contraction axis (structurally distinct from feature axis).
- Q: "iter-v3/048 closed cycle 3 NEW universal engineered feature axis with 5 attempts
  failure. Why try again?"
  A: Cycle 4 RE-OPENS the axis per /050 diary §Cycle 4 Priorities axis #1. Cycle 3
  closure is per-cycle, not permanent. fracdiff_d05_close at universal scope is the
  FIRST cycle 4 attempt; saturation predictor starts fresh at attempt #1.
- Q: "What if fracdiff_d05_close is INERT (rank 14/15 across all 3 syms)?"
  A: PATH B classification (PROMISING-INERT). Drop the feature at /052 setup; pivot to
  regime_momentum_signed_3d UNIVERSAL.

---

## Section 11 — References

### Memory rules invoked
- `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (UPDATED 2026-05-10; SYSTEM-LEVEL CONFIRMED)
- `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve rule)
- `feedback_v3_strict_10_to_1_cadence.md` (cycle 4 begins iter-v3/051)
- `feedback_v3_axis_selection_quant_discipline.md` (QR EDA-driven axis selection)
- `feedback_v3_engineered_feature_pivot.md` (Category 2 IC carve-out)
- `feedback_v3_engineered_features_proven.md` (composed engineered features work)
- `feedback_v3_engineered_features_dont_stack.md` (single-seed lottery falsifier band)
- `feedback_v3_inert_features_at_higher_budget.md` (PROMISING-INERT classification)
- `feedback_v3_structural_over_knob_exploration.md` (NEW feature family priority)
- `feedback_v3_dsr_mode_artifact.md` (EXPLORATION-mode DSR informational only)
- `feedback_v3_exploration_n_trials_35.md` (n_trials=35 EXPLORATION default)
- `feedback_v3_axis_saturation_predictor.md` (behavioral-effect predictor)

### Prior iterations cited
- iter-v3/028 BASELINE_V3.md (multi-seed +0.5101 IS / +0.5053 OOS; cycle 4 anchor)
- iter-v3/035 (fracdiff_d05_close BCH-only PROMISING precedent at single-seed)
- iter-v3/039 (cycle 2 CONFIRMATION-NO-MERGE; first system-level rule firing)
- iter-v3/044 (regime_momentum_signed_3d EDA-FALSIFIED at ALGO LONG bottleneck; reverted)
- iter-v3/045 (cycle 3 STRONGEST PROMISING; LDO ATR (2.0, 1.5))
- iter-v3/047 (primitive 10 BCH LONG block; carry-forward)
- iter-v3/048 (cycle 3 NEW universal engineered feature axis CLOSED; vol_normalized_ret_5d
  INERT)
- iter-v3/049 (cycle 3 LAST EXPLORATION; per-symbol ADX TRX 21; closed)
- iter-v3/050 (SECOND v3 CONFIRMATION; NO MERGE; cycle 4 priorities established)

### Implementation files
- `src/crypto_trade/features_v3/__init__.py` — V3_FEATURE_COLUMNS_TOP_N (UPDATE)
- `src/crypto_trade/features_v3/fracdiff_v3.py` — compute_fracdiff_d05_close (UNCHANGED)
- `run_baseline_v3.py:V3_MODELS` — REVERT to 3-sym
- `run_baseline_v3.py:V3_ATR_MULTIPLIERS_PER_SYMBOL` — REVERT to {}
- `run_baseline_v3.py:_build_v3_model` RiskV2Config — REVERT block_long_for to ()
- `run_baseline_v3.py:_verify_feature_columns` — UPDATE assertions
- `run_baseline_v3.py:ITERATION_LABEL` — UPDATE to "v3-051"
- `tests/features_v3/test_fracdiff_d05_universal.py` — NEW file (5 adversarial tests)

### Run command (LOCKED)

```bash
uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

### Estimated wall-clock

- Setup commit (REVERT + ADD + tests): 30-45 min
- Phase 5.5 gate: 5-10 min
- Backtest (3-sym + 15 features at n_trials=35 single-seed): 25-35 min
- Phase 6/7 reports: 10-15 min
- TOTAL: ≤1.5h (well within 2h EXPLORATION cap)

---

## Section 12 — Brief Validation Checklist (Pre-Phase-5.5)

Before Phase 5.5 gate runs, the QR confirms:

- [x] Section 0 — Data split declaration with sacred constants (OOS_CUTOFF, training_months,
      ENSEMBLE_SIZE, n_trials, colsample_bytree, OOS_CUTOFF_MS)
- [x] Section 0.5 — Iteration type declaration (EXPLORATION; cycle 4 #1; spec; carry-forward
      state; predicted classification probabilities)
- [x] Section 1 — Hypothesis (single sentence; what changes; what is expected)
- [x] Section 2 — IS-only numerical evidence (committed analysis script SHA `290f37b`;
      tables with quantitative basis; explicit citations to CSV files)
- [x] Section 3 — Proposed changes (detailed sub-fixes with line numbers; bundle state
      verification)
- [x] Section 4 — Expected OOS impact (predicted bands; behavioral-effect predictor;
      pre-registered falsifier; pathway-A/B/C triggers)
- [x] Section 5 — Risk Mitigation (R1/R2/R3; primitive 9/10; per-symbol ATR; per-symbol ADX;
      cross-symbol contagion; universe contraction; risk-budget redistribution; trade-rate
      stability; adversarial tests; multi-run-stochasticity)
- [x] Section 6 — Risk Management Design (10-primitive gate table; predicted fire rates)
- [x] Section 7 — Pre-registered Failure-Mode Prediction (4 failure modes with probability;
      what gates should catch)
- [x] Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED; non-renegotiable
      post-hoc; PATH A/B/C-clean/C-suspicious; saturation rule)
- [x] Section 9 — Library Stack Declaration (versions pinned)
- [x] Section 10 — QR Audit Trail (EDA basis; 4 candidates evaluated; QR-driven selection
      rationale; cross-validation; adversarial review preparation)
- [x] Section 11 — References (memory rules; prior iterations; implementation files; run
      command; estimated wall-clock)
- [x] Section 12 — Brief Validation Checklist (this section)

**Brief written WITHOUT viewing iter-v3/051 OOS data.** First QR exposure to iter-v3/051
OOS metrics is in Phase 7.

**EDA artifacts committed at SHA `290f37b`** before brief write per
`feedback_v3_axis_selection_quant_discipline.md` discipline.

**Pre-registered Section 8 thresholds LOCKED** before backtest runs; non-renegotiable
post-hoc per cycle 4 discipline inherited from cycle 3.

End of brief.
