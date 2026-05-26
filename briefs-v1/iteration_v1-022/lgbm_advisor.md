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

---

# LightGBM Master Post-Mortem — iter-v1/022 — Phase 7.4

## Context Read

- IS Sharpe **-0.0046** / OOS Sharpe **-1.4407**. F1 OOS Sharpe Δ = **-1.17** (NEGATIVE-CATASTROPHIC; ~10× the -0.55 floor). 117 IS / 48 OOS trades (both inside QR band).
- F-AXIS #3 gate fire-rate: IS 17.95% / OOS 29.17% — **inside pre-registered [15%, 40%] / [5%, 30%] bands**. Gate operated as designed.
- Brief Section 1 hypothesis REFUTED catastrophically.

## 1. Phase 4.5 vs Phase 7.4 prediction reality

LM Master priors 8/12/40/20/10/10. Observed: **NEGATIVE-CATASTROPHIC** — 10% tail materialized.

| Prediction | Observed | Verdict |
|---|---|---|
| F-AXIS #2 IS [70,160], OOS [18,50] | 117 / 48 | **HIT** |
| F-AXIS #3 IS [15%,40%], OOS [5%,30%] | 17.95% / 29.17% | **HIT** |
| n_eff [6,10] | 8 | **HIT** |
| Jaccard [0.03, 0.20] modal 0.06 | IS 0.10 / OOS 0.093 | **HIT** |
| F1 OOS Δ (NEG-CAT 10% tail) | -1.17 | **HIT NEG-CAT** |
| Closing call: "F-AXIS #3 LOAD-BEARING, not F1 magnitude" | F-AXIS #3 PASSED yet F1 collapsed | **VINDICATED** |

**All 4 F-axes PASSED yet iteration is catastrophic.** Mechanism ≠ outcome.

## 2. Jaccard computation

| Window | Intersection | Union | **Jaccard** |
|---|---|---|---|
| IS (vs baseline 124 trades) | 22 | 219 | **0.1005** |
| OOS (vs baseline 34 trades) | 7 | 75 | **0.0933** |

~90% NEW roster on both windows. Confirms /020-precedent basin relocation. The asymmetric gate's ORACLE EDA Δ +12.45% was projected on a 34-trade baseline roster; only 7 of those appear in /022 OOS — EDA descriptively true but operationally irrelevant.

## 3. Gate-fired-but-didn't-work analysis

**Baseline OOS LTC drag direction**: longs -45.44% / total -47.25% → **96% LONG-direction**.

**/022 retrained OOS LTC drag direction**: longs -26.54% / total -34.88% → **76% LONG-direction**. Shorts now contribute -8.34% (vs -1.81% baseline — short drag grew **4.6×**).

The asymmetric long-suppress gate is OPERATING ON THE WRONG SUBSET. Even at OOS fire-rate 29.17% (heavy engagement), it cannot touch the short-side -8.34% drag because by design it only blocks longs.

**Worse**: /022 IS PnL distribution shows the basin is FUNDAMENTALLY DIFFERENT — IS longs +44.54% / shorts +23.00% (both POSITIVE). The 89% IS direction-asymmetric pattern that justified the brief is GONE in the retrained basin. OOS roster expressed regime-rotation drag from BOTH directions; gate blocked only one side.

**Verdict**: /021 H2 binding holds. Mechanism (asymmetric gate at -4% BTC ret_42) is causally targeted at a phenomenon (89% long-drag-in-BTC-bear) that is a property of the BASELINE LTC-in-pool basin. When basin relocated (~90% new trades), the targeted phenomenon evaporated, and the gate continued firing on an unrelated 29% slice.

## 4. Per-cohort axis SATURATED — rule update

| Cohort | Prior class | Mechanism | Outcome |
|---|---|---|---|
| LINK | POSITIVE_EVERYWHERE | pure isolation | **PROMISING +0.80** ✓ |
| ETH | counter-trend OOS drag (symmetric) | ±8% symmetric gate | **PROMISING +0.50** ✓ |
| BTC (/020) | ASYMMETRIC_ROTATION | pure isolation | **NEG-CAT -0.86** ✗ |
| LTC (/022) | ASYMMETRIC_ROTATION-INVERSE | asymmetric long-suppress gate | **NEG-CAT -1.17** ✗ |

**Rule (post-/022)**: Any cohort classified as `ASYMMETRIC_ROTATION_*` is INVIABLE for single-cohort isolation regardless of gate symmetry. Dominant failure mode: BASIN RELOCATION dissolves the asymmetry on which the gate's targeting depends. **Per-cohort isolation axis SATURATED.**

**DOT pre-classification mandatory for /023**: If DOT class = POSITIVE_EVERYWHERE or MILD_PROMISING, isolation may be viable. If DOT class = ASYMMETRIC_ROTATION, **predict NEG-CAT a third time**. Do NOT default /023 to DOT-only.

## 5. /023 routing — NEW-family axis MANDATORY

Per Phase 4.5 §7: NEGATIVE-CATASTROPHIC (10%) → /023 = NEW-family axis (NOT closeout-jump-to-/027).

Consecutive-CATASTROPHIC tracker: /020 + /022 = **2 in cycle-3** (separated by /021 PROMISING-METHODOLOGY). Forward-binding mandate at 3; not triggered, but second catastrophe on SAME AXIS-TYPE is decisive evidence axis-type is saturated.

NEW-family candidates not used in last 5 EXPLORATIONs:

| Candidate | Family | Justification |
|---|---|---|
| **Funding-rate feature family** | NEW feature family (non-OHLCV) | Cycle-3 has NOT tested. NEW signal source, stateless, production-proven. STRONGEST recommendation. |
| Per-cohort drawdown brake (R2-like) | NEW risk-primitive | Addresses /020 + /022 symptomatically. STATEFUL — requires deadlock-impossibility proof. |
| Microstructure z-score features | NEW feature family | Available at 8h cadence. Risk: iter-v3/015 microstructure went INERT at n_trials=10. |

**Strongest recommendation: funding-rate feature family**: (a) NEW signal source, (b) stateless, (c) production-proven, (d) v1 LightGBM never had access, (e) sidesteps cohort-isolation axis trap.

## 6. /027 bundle composition update

| Slot | Source | Status | Multi-seed Δ |
|---|---|---|---|
| LINK-only specialist | /018 | ✓ Confirmed PROMISING | **+0.80** |
| ETH-only + symmetric gate | /019 | ✓ Confirmed PROMISING | **+0.50** |
| BTC | /020 NEG-CAT | ✗ specialist eliminated; **stays IN POOL** | baseline-only |
| LTC | /022 NEG-CAT | ✗ specialist eliminated; **stays IN POOL** | baseline-only |
| DOT | /023+ TBD | TBD pending NEW-family axis routing | TBD |

Bundle Δ target at /027 multi-seed: **+1.10 to +1.30 OOS Sharpe** (2 specialists) + DOT TBD + funding-rate axis pending. Catastrophic outcomes /020 + /022 SUBTRACTED candidate specialists but did NOT poison pool.

## 7. Track record update

LM Master priors at /022: 8% / 12% / 40% / 20% / 10% / 10%. Observed: **NEGATIVE-CATASTROPHIC (10% tail).**

- F-axis micro-mechanics: 4/4 hit (F2 IS, F2 OOS, F3 IS, F3 OOS) + Jaccard inside band + n_eff inside band.
- Verdict-class probability: NEG-CAT was 10% (third-rarest tail); materialized. Directional CREDIT for raising NEG total to 40% vs QR's 30%.
- Most important prediction VINDICATED: "F-AXIS #3 LOAD-BEARING disambiguator, not F1 magnitude — anchor at extreme negative reduces F1 diagnostic power."

Cumulative LM Master track record after /022: H1 directional 1/2 on catastrophes (correctly flagged /020-type risk for /022), methodology 2/2, asymmetric-gate downside flagged correctly. **Verdict probability skew earned credit.**

## 8. Most important Phase 7.4 finding

**The asymmetric long-suppress gate operated within pre-registered fire-rate bands AND fired at the wrong trades — confirming the /021 H2 REFUTATION binding empirically: gate-targeting mechanisms operate at TRADE-ROSTER LEVEL, but basin relocation at single-seed cohort isolation produces ~90% NEW rosters where the targeted phenomenon (89% long-direction drag in BTC-bear) has dissolved, leaving the gate firing on an unrelated 29% slice. Per-cohort isolation is now structurally SATURATED for any cohort classified ASYMMETRIC_ROTATION, regardless of gate symmetry.**
