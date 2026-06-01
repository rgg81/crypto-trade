# LightGBM Master Advisor — iter-v1/024 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/024`. HEAD `669994a`. Cycle-3 EXPLORATION #9/10. First multi-model architecture in v1.
- **Anchor**: BASELINE_V1.md portfolio IS +0.2829 / OOS +0.6637.
- **/023 outcome**: LEARNED-NEGATIVE (OOS Δ -0.20); funding gain share 5.40% > 2.38% uniform parity; ORACLE +78.55% extreme-tail concentration could NOT be harvested at pool depth 3-5.
- **/024 design**: 2 sub-models per cohort partitioned by `|funding_z30| > 1.5`; STATELESS regime gate at inference.

## 1. DOT 8-IS-trade overfit risk — DROP DOT from regime-conditional dispatch

DOT extreme partition has **8 IS trades**, of which **3 are shorts**. Per-cohort walk-forward × 24 monthly cells → DOT extreme sub-model gets per-cell n_eff of 0.33 trades — DEGENERATE. The direction reversal (longs +0.64% / shorts -1.70%) is statistically indistinguishable from noise at n=3 shorts; sub-model will lock onto whichever direction first month's basin happens to favor and propagate across OOS.

**Recommend**: DOT stays on baseline single-model dispatch. The 7 other sub-models (Pool A × 2 + LINK × 2 + LTC × 2 + DOT × 1) form the architecture. Structural mitigation, not knob — preserves the strongest 3 signals (Pool A 40 trades, LINK 17 with WR 85.7%, LTC 17 with shorts edge).

REJECTED alternative: pooling DOT-extreme bars into LINK/LTC extreme — violates cohort isolation.

## 2. Verdict-prior recalibration — RECOMMEND 12/7/48/20/10/3

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING | 15% | **12%** | /023 LEARNED-NEGATIVE means signal IS present; partition mechanism is sound. But 2× sub-models compound basin relocation. |
| PROMISING-INERT-FAV | 8% | **7%** | 2× sub-model parameter space doubles lottery surface AND doubles dilution cost; net wash. |
| **INERT (modal)** | 42% | **48%** | Multi-model failure mode: both sub-models at single-seed n_trials=18 land in pool-baseline-like basins (thin extreme subsets at MID Optuna budget are under-fit twin of high-budget INERT). +6pp toward modal. |
| NEGATIVE clean | 18% | **20%** | DOT overfit risk preserved even if mitigated; LTC normal-regime counter-direction (NORMAL D -4.01% sum) means normal sub-model may underperform pool. |
| NEGATIVE-CATASTROPHIC | 12% | **10%** | 2× sub-models means errors can OFFSET (averaging effect); reduces CAT tail vs single-axis catastrophes /020/022. |
| PROMISING-METHODOLOGY | 5% | **3%** | model-arch axis NOT primarily methodology. |

**Modal INERT 42% → 48%**. PROMISING tail 23% → 19%. Key recalibration: 2 sub-models × n_trials=18 × ENSEMBLE_SIZE=3 = 6 effective tree-build paths per cohort per month vs baseline's 3. Compute doubled but variance NOT halved because each sub-model sees half the data.

## 3. F-AXIS-MECHANISM strengthening

**#1 Dispatch**: WITH DOT mitigation, **7 sub-models** not 8. Engineering report MUST emit `per_cohort_per_regime_breakdown.csv` with 7 rows.

**#2 Trade-count floor** (NEW LOAD-BEARING): per-cohort EXTREME sub-model emits ≥ 5 IS trades AND ≥ 3 OOS trades. Otherwise sub-model is degenerate (Row 9 trigger). DOT excluded from this floor.

**#3 Regime-gate fire-rate** (TIGHTEN): per-cohort IS [10%, 18%] AND OOS [8%, 22%]. Per Section 2.3 persistence 0.15-0.18, fire rate is structurally bounded by funding distribution — no Optuna-knob moves it. Wider OOS band for legitimate regime-drift.

**#4 n_eff_per_cell**: EXTREME [2, 8] (lower bound 2 not 3; Pool A ext 66 bars/month × 5x5 CV = 13/fold; LINK/LTC ext even tighter). NORMAL [5, 10] unchanged.

**ADD: gain-share recurrence check (CRITICAL — load-bearing from /023)**: per-sub-model funding-z30 + z90 family gain share must be reported. **Extreme sub-model's funding gain share MUST exceed normal sub-model's** — if not, partition is not specializing (Mode A INERT diagnostic strengthened).

## 4. Implementation risks

**(a) Look-ahead in regime gate**: USE RegimeRoutedStrategy wrapper at signal-time, NOT in-strategy callback at prediction time. The callback inside `_train_for_month()` is for training-row partition; the wrapper at `get_signal()` is for inference-routing. Conflating them risks wrapper firing on bar t with z30(t) that includes bar t's own funding-rate. Verify in Phase 5.5.

**(b) Label-mixing**: each sub-model's labeling uses past-only sigma. Extreme sub-model's label distribution will be skewed (more violent moves → more triple-barrier hits at barriers). Expect extreme sub-model `binary_logloss` 5-15% higher; may confuse EDA-band predictor.

**(c) Sub-model month-skipping under thin partition**: pre-commit policy — if extreme sub-model skip-month, route ALL of that month's bars (both regimes) through normal sub-model. NOT in brief Section 10.3; flag for QR.

## 5. /027 bundle composition if /024 PROMISING — target +1.30 to +1.55

3-component bundle:
- Pool baseline OOS +0.66
- LINK specialist /018 +0.50 estimate
- ETH+gate /019 +0.30 estimate
- Regime-conditional /024 **+0.15 estimate** (modest because partition mechanism shared across cohorts → correlated with LINK funding-extreme exposure)

Nominal Σ = +1.61 OOS Sharpe. Realistic with correlation drag (regime-conditional × LINK ρ ≈ 0.45 both ride funding-z30 extreme): **+1.30 to +1.55**.

**Cross-correlation pre-validation MANDATORY at /027**: Pearson(monthly_returns_regime_conditional, monthly_returns_LINK_specialist) < 0.50; else regime-conditional alpha is largely redundant.

## 6. Most important point

**The biggest risk is NOT the architecture — it is the DOT extreme sub-model trained on 8 trades; recommend hard-mitigation NOW (DOT stays on baseline single-model) rather than relying on Mode E post-hoc diagnostic, because if DOT extreme lands a contrarian basin at single-seed it pollutes portfolio aggregate enough to convert modal-INERT into NEGATIVE-clean misread.**

## 7. /025 verdict-conditional staging — REFINE

- **PROMISING (12%)** → /025 = /027 prep + `cross_correlation_check_alpha_components.py` (monthly returns Pearson/Spearman between LINK, ETH+gate, regime-conditional). If ρ > 0.50 between any pair, /027 must reweight.

- **PROMISING-INERT-FAV (7%)** → /025 = open-interest delta family (NEW non-OHLCV per `feedback_v3_cross_asset_ohlcv_closed.md` carve-out). Primitive: `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Importance target: rank ≤14/43 on ≥2 cohorts + gain share ≥4.0%.

- **INERT (48% MODAL)** → /025 = **open-interest delta family** (PRIMARY) — NOT per-cohort drawdown brake (STATEFUL deadlock risk per iter-v3/054; per `feedback_v3_concentration_is_signal.md` per-cohort dampening primitives CLOSED in v3 — transfer prior). Drawdown brake demoted to /026.

- **NEGATIVE clean (20%)** → /025 = OI delta family at single-seed.

- **NEGATIVE-CATASTROPHIC (10%)** → 3rd cycle-3 >1σ HIGH-RISK NEG-CAT trips mandatory multi-seed at /025. /027 then 2-component (pool + LINK + ETH+gate; regime-conditional CLOSED for v1).

## Closing

**MEDIUM-HIGH confidence three calls**:
1. **DOT extreme sub-model is single largest implementation risk** — drop before Phase 6.
2. **Modal INERT shifts 42% → 48%** with multi-model 2× basin-relocation surface.
3. **Cross-correlation pre-validation at /025/027** between LINK specialist and regime-conditional is load-bearing for bundle composition.

**Critic Phase 7.5 priority items**:
1. DOT mitigation present in implementation (7 sub-models not 8)
2. RegimeRoutedStrategy wrapper at signal-time (no look-ahead)
3. Gain-share recurrence check across regimes per cohort
4. Cross-correlation analysis present for /027 bundle pre-validation

---

# LightGBM Master Advisor — iter-v1/024 — Phase 7.4 (Post-Mortem DIAGNOSTIC)

## Context
- comparison.csv BIT-IDENTICAL to /023 (Sharpe +0.4121/+0.4606, 694/257 trades, all metrics)
- ALL 3 extreme sub-models produced empty `_models` (skip rate 100%)
- Wrapper architecture correct; data partition layer broken

## 1. Why extreme sub-models trained nothing — STRUCTURAL DEFECT, NOT THINNESS

ROOT CAUSE: **column-resolution bug** in `make_extreme_filter`, NOT partition thinness.

Logs show repeated "0 rows after filter" for ALL 240 month×cohort training cells. EDA Section 2.1 had 1573/709/802 extreme bars — those rows physically exist. So extreme returning literal **0** means the column is MISSING, not the bars.

**Smoking gun** at `src/crypto_trade/strategies/regime_gate_v1.py:181-185`:
```python
def _filter(df):
    if z30_column not in df.columns:
        return np.zeros(len(df), dtype=bool)  # all-False fallback
```
Complementary normal filter at line 207-210 returns **all-True** when column missing. Asymmetric fallback → extreme empty (skip) + normal full (= /023 baseline = bit-identical comparison.csv).

`self._master` passed to `_train_for_month` at `lgbm.py:525` does NOT contain `funding_rate_zscore_30`. Even though V1_FEATURE_COLUMNS_PRUNED includes it, the column lands in feature-cache view but not `self._master` that filter callback receives.

**Pre-launch miss (mine)**: Phase 4.5 §4(a) flagged look-ahead risk in wrapper but didn't recommend `len(extreme_filter(sample))>0` precondition assertion. 3-line unit test would have caught this in seconds.

## 2. Bit-identity to /023 — MECHANISM BYPASS

Every Optuna call landed on the NORMAL partition only. Normal filter returns all-True when column missing → trained on FULL window = /023 baseline. Same seed=42 + same n_trials=18 + same ENSEMBLE_SIZE=3 + same hyperparameter bounds + same training rows → identical best_params → identical trade roster.

This is NOT basin invariance. It is **mechanism bypass at the data-loading layer**. The wrapper did its job (`regime_gate_v1.py:319-344` dispatches via skip-month fallback to normal because `_is_extreme_model_trained_for_month()` always returns False). Training-data partition is where the bug lives.

## 3. F-AXIS #1 Dispatch Correctness BLOCK

Brief Section 4.2 pre-registered: "7 unique model_name values". Observed: **4** (3 normal + DOT baseline). 3 extreme feature_importance CSVs absent at `reports-v1/iteration_v1-024/in_sample/`.

Section 5 mass-shifting trigger #2: "IF EXTREME sub-model trade count < 5 IS for ≥1 cohort → Row 9 n_eff degenerate." All 3 cohorts violate (0 trades each).

## 4. Architectural lesson — BOLD direction for /025

Reject options A/B/C/E (each insufficient or wrong). **Recommend BLOCK-PENDING-FIX with 3-line patch**:

1. Replace silent zero-mask fallback at `regime_gate_v1.py:181-185` with hard `raise ValueError("Required column missing")`
2. Trace runner master-construction to ensure funding_rate_zscore_30 propagates
3. Add 3-line unit test: `make_extreme_filter('funding_rate_zscore_30', 1.5)(master_sample)` returns mask with ≥1 True

Re-run /024-A same config (seed=42, n_trials=18, ENSEMBLE_SIZE=3). Mechanism gets a fair test.

## 5. Verdict cell assignment — Row 9 BLOCK-PENDING-FIX

Per pre-registered Section 8 Row 9: "F-AXIS #1 dispatch fail → BLOCK-PENDING-FIX". F1 OOS Δ -0.2031 is MEANINGLESS as signal evaluator because mechanism under test was bypassed. Treating as Row 6 NEGATIVE-clean would conflate mechanism bypass with learned-negative outcome.

**Critic Phase 7.5 verdict: BLOCK-PENDING-FIX** with required action: fix `regime_gate_v1.py:181-185` + trace runner master-construction + 3-line unit test + re-run /024-A.

## 6. Most important point

**The /024 outcome is not a refutation of regime-conditional architecture — it is a 3-line column-resolution defect masquerading as a null-result. Bit-identity to /023 IS the diagnostic that mechanism was bypassed at data layer rather than producing INERT signal. Closing the model-arch axis on this evidence would be the wrong call.**

## 7. Calibration miss

My Phase 4.5 priors 12/7/48/20/10/3 are UNDERDETERMINED. The verdict (Row 9 BLOCK-PENDING-FIX) was not in my prior distribution. **Lesson**: future Phase 4.5 advisories on data-pipeline axes MUST include "column-presence assertion in filter callback" as Implementation Risk item with explicit unit test specification.

Prior recommendations that materialized correctly: DOT mitigation (§1), wrapper-at-signal-time no-look-ahead (§4a), skip-month fallback design (§4c).

Prior that missed: F-AXIS #5 gain-share recurrence (cannot evaluate because extreme sub-models didn't exist — needs precondition assertion).
