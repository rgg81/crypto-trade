# LightGBM Master Advisor — iter-v1/022 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/022`. HEAD `a8166d8`. Cycle-3 EXPLORATION #7 of 10. Fourth single-cohort iter after LINK (/018 PROMISING-INERT), ETH+gate (/019 PROMISING +0.65 OOS Δ), BTC (/020 NEGATIVE-CATASTROPHIC -0.86 OOS Δ).
- **Anchor**: BASELINE_V1.md portfolio (IS +0.2829 / OOS +0.6637); LTC-in-pool per-trade Sharpe IS +0.0038 / OOS **-0.2670** (worst-in-portfolio).
- **LTC prior class**: ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT — IS half-split sign reversal + 89% of OOS catastrophe in LONG direction + 64% in 2025-12 + 2026-01 BTC correction phase.
- **Mechanism**: `longsuppress_btc_trend_gate@4%` — ASYMMETRIC one-sided variant of /019 ETH primitive; ORACLE EDA IS Δ +10.79% / OOS Δ +12.45%.
- **Track record entering /022**: H1 directional 0.5/4, methodology 2/2, alternative-branch utility 1/1.

## 1. /021 H2 REFUTATION binding compliance — SATISFACTORY with caveat

QR's framing at Section 1 is structurally compliant: (a) joint-loss substrate LTC-only post-isolation, (b) drag class direction-asymmetric (89% longs), (c) gate operates as exogenous trade-stream filter.

**Caveat**: Section 1's H2 INFORMATIONAL hypothesis ("Cohort isolation may amplify the H2 negative half (basin lands in regime LTC OOS lives in)") edges toward feature-level reasoning. QR should ensure Phase 7.4 verdict assignment cites **BASIN VECTOR EVIDENCE** (Optuna best_params shift via params_persist_path infrastructure from /021), NOT feature_importance rank-shift evidence. /021 instrumentation defect (pool FI all-zeros) does NOT block /022 (single-symbol Model D' — pool aggregation defect cannot recur). **PASS framing check.**

## 2. ORACLE EDA validity carve-out — CONFIRMED for STATELESS gate

Per `feedback_v3_oracle_eda_validity.md`: `longsuppress_btc_trend_gate@4%` is fully stateless. STATELESS carve-out applies; ORACLE EDA on baseline LTC trades is VALID.

**Critical caveat**: IS Δ +10.79% / OOS Δ +12.45% are post-hoc projections on the BASELINE Model D LTC roster (pool-trained, 124 IS / 34 OOS). /022 Model D'-LTC-only retrains in single-cohort isolation — actual roster will differ. Per /019 §3 empirical pattern: gate efficacy compressed at retraining (EDA projected +0.30 OOS Sharpe; observed +0.6990 — actually MORE not less, but Jaccard 0.04 confirms near-zero overlap → mechanism wasn't roster-locked). For LTC, basin-relocation risk is real and BIDIRECTIONAL.

**QR should NOT cite ORACLE EDA Δ as predicted /022 outcome** — only as mechanism validation evidence.

## 3. Verdict-class priors — RECOMMEND adjust to 8/12/40/20/10/10

QR's 15/10/45/12/8/10 split underweights the negative tail. Three reasons:

1. **ASYMMETRIC threshold tuning IS harder than symmetric**. /019 ETH at ±8% worked because BOTH directions had counter-trend drag at large magnitudes; LTC longs-only @ -4% targets narrower band. Tighter threshold (4% vs 8%) is more sensitive to BTC regime changes.

2. **/020 BTC precedent**: ASYMMETRIC_ROTATION cohort went catastrophic. LTC is IS-MARGINAL/OOS-CAT — STRUCTURALLY DIFFERENT class — but basin-relocation mechanism that broke /020 applies equally to LTC single-cohort isolation.

3. **PROMISING tail at 25%** requires basin to land favorably AND gate efficacy to exceed EDA upper bound by ~10× — that's not 25%, that's 8-15%.

**Recalibrated**: PROMISING **8%** / PROMISING-INERT **12%** / INERT **40%** (still modal) / NEGATIVE **20%** / NEGATIVE-INTRINSIC **10%** / NEGATIVE-CATASTROPHIC **10%**. Modal INERT decreases (gate is causally targeted, so pure null less likely than /020 BTC). **PROMISING+PROMISING-INERT total 20%, NEGATIVE total 40%.**

## 4. F-AXIS-MECHANISM #1-3 pre-registration

- **F-AXIS #1 (dispatch correctness)**: PASS criterion `df['symbol'].unique() == ['LTCUSDT']`. Approved.
- **F-AXIS #2 (trade count; LOAD-BEARING)**: LTC-in-pool baseline = 124 IS / 34 OOS. /022 LTC-only at ENSEMBLE_SIZE=3 + 25.8% IS kill rate ORACLE → predicted IS ~93 (post-gate ORACLE roster). But basin relocation expands/contracts by 20-40%. **Predicted /022 LTC IS band [70, 160] modal 100; OOS band [18, 50] modal 28.** QR's [80, 180] / [20, 60] wider on lower bound — ACCEPT as safety margin but Phase 7.4 measures exact roster.
- **F-AXIS #3 (gate fire-rate on LONG trades)**: ORACLE EDA IS 25.81% / OOS 14.71%. **Predicted band [15%, 40%] IS / [5%, 30%] OOS — APPROVED**, but watch for OOS fire rate <5% (indicates LTC-only basin avoided BTC-bear regime trades entirely → cohort-isolation already removed drag → gate effectively off → NEGATIVE-UNDER-FIRE).

## 5. n_eff_per_cell prediction

Per /019 §5: n_eff derived from training row count. **Predicted n_eff_per_cell point estimate 8, band [6, 10].** QR's 7-modal / [4, 9] too pessimistic on lower bound. ACCEPT QR's 7-modal but widen upper to 10.

## 6. Jaccard prediction

Per /018 LINK = 0.04 / /019 ETH = 0.04 / /020 BTC = 0.084 empirical history: single-cohort retraining produces ~95% NEW roster regardless of cohort prior class at single-seed=42 n_trials=18 ENSEMBLE_SIZE=3 budget.

**Predicted LTC /022 vs baseline LTC-in-pool Jaccard: 0.04-0.10, modal 0.06.** PROMISING-MECHANICAL classification (Jaccard ≥ 0.80) is NEAR-ZERO probability. /022 will be either NEW SIGNAL SOURCE (compoundable) or NEGATIVE. QR's pre-registered band [0.05, 0.35] correct lower bound but wider than empirical — **recommend narrow to [0.03, 0.20]**.

## 7. /023+ verdict-conditional pre-staging

- **PROMISING (8%)** → /023 = DOT-only specialization (LAST single-cohort untested).
- **PROMISING-INERT (12%)** → /023 = DOT-only (cohort-coverage closure has scientific value).
- **INERT (40% modal)** → /023 = DOT-only.
- **NEGATIVE (20%) or NEGATIVE-INTRINSIC (10%)** → /023 = NEW-family axis (funding-rate or per-cohort drawdown brake).
- **NEGATIVE-CATASTROPHIC (10%)** → /023 = NEW-family axis (NOT closeout + jump to /027). DO NOT collapse cadence.

## 8. Most important point

**/022's verdict is dominated by whether single-cohort retraining at LTC-only single-seed=42 lands in a basin where 89% direction-asymmetric OOS drag persists at retrained roster (gate fires within band → modal INERT/PROMISING-INERT 52%) OR whether basin relocates to a roster where direction asymmetry dissolves (gate underfires <5% OOS → NEGATIVE-UNDER-FIRE 15%) OR whether basin relocates to a structurally worse roster than /020 BTC catastrophic (NEGATIVE-CATASTROPHIC 10%) — F-AXIS #3 fire-rate empirical observation is the load-bearing diagnostic, not F1 magnitude alone.**

## 9. /027 bundle composition update at PROMISING

If LTC PROMISING (8%) or PROMISING-INERT (12%):
- 3-specialist bundle on FULL POOL preserved (Option β extended)
- LINK-only specialist (+0.80 anchor at multi-seed)
- ETH-only + symmetric gate (+0.50 anchor at multi-seed)
- **LTC-only + asymmetric long-suppress gate (NEW)**: single-seed Δ TBD; multi-seed target **+0.30**
- Nominal Σ_independent: +2.26
- Realistic with correlation drag: **+1.20 to +1.50 OOS Sharpe** (raises ceiling vs 2-specialist /021 §7 estimate of +1.10-1.30)
- Multi-seed CONFIRMATION mandatory cross-correlation pre-validation: LTC+gate paths vs LINK paths AND vs ETH+gate paths — both < 0.40 required

## Closing Notes

**MEDIUM-HIGH confidence in three calls** (calibrated against post-/021 H1 0.5/1 directional credit):

1. **Verdict priors: PROMISING tail 20% (vs QR's 25%); NEGATIVE tail 40% (vs QR's 30%)** — ASYMMETRIC threshold harder; basin-relocation downside underweighted.
2. **F-AXIS #3 is LOAD-BEARING disambiguator**, not F1 magnitude — anchor at extreme negative reduces F1 diagnostic power around INERT/NEGATIVE boundary.
3. **Jaccard band narrow to [0.03, 0.20]** vs QR's [0.05, 0.35]; empirical history strongly suggests ~0.06 modal regardless of cohort.

**Single most important point for QR**: brief Section 1 H2 INFORMATIONAL framing edges close to feature-level reasoning. Phase 7.4 verdict assignment MUST cite Optuna best_params shifts (basin vector) as mechanism evidence, NOT feature_importance rank-shifts. Without this, /021 H2 REFUTATION binding is at risk of soft-rebinding through linguistic slippage.

**Critic Phase 7.5 priority items**:
1. F-AXIS #3 fire-rate against pre-registered [15%, 40%] IS / [5%, 30%] OOS — LOAD-BEARING.
2. Layer C single-cohort feature_importance defect check.
3. Basin relocation evidence (Optuna best_params shift) — BASIN-VECTOR not feature-importance.
4. Jaccard against baseline LTC-in-pool — empirical [0.03, 0.20].
