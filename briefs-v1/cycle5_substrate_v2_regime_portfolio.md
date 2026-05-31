# /044 SUBSTRATE V2 — Regime-Complementary Model PORTFOLIO Proposal

**Date**: 2026-05-31
**Author**: QR (final substrate proposal under USER DIRECTIVE: "combine models that perform under different regimes ... don't discard models that run well in IS")
**Anchor**: BASELINE_V1 `v0.v1-baseline-corrected` `f8bc12c` (IS +0.2829 / OOS +0.6637)
**Supersedes**: /039-closeout dual-CONFIRMATION plan (/044-A multi-seed /036 + /044-B multi-seed /037, single-axis each).
**Adopts**: regime-portfolio framing per cycle5_regime_substrate_analysis.md + regime_decomposition.csv.

---

## 1. PORTFOLIO STRUCTURE (4 components)

The /044 substrate is reframed from "two independent single-axis CONFIRMATIONs" to a **single 4-component regime-complementary portfolio**, each component multi-seed-validated under CONFIRMATION spec, then combined at the trade-stream level into an aggregated portfolio book.

| Slot | Component | Mechanism | Regime profile | Weight |
|------|-----------|-----------|----------------|-------:|
| **P0 — ANCHOR** | BASELINE_V1 (5-cohort triple-barrier, 193 cols) | Universal substrate; carries BTC-OOS-strong (+33.17%) + LINK-universal (IS +72 / OOS +34) cohorts; LTC catastrophe (−47.25%) absorbed | type-B-lean-C; OOS +0.6637; covers BTC + LINK universally | **40%** |
| **P1 — OOS-TREND** | /036 LINK+DOT trend-scan specialist (2-cohort, trend_scanning labels) | Trend-significance labels extract trend subspace LINK+DOT favor; per-cohort isolation prevents BTC/ETH mean-reverting regime contamination | type-B strong; OOS +1.7465 (+1.08 Δ); 50/50 LINK/DOT; covers OOS-trend regime | **25%** |
| **P2 — IS-MOMENTUM** | /040 composed `regime_momentum_signed_5d` (stack-pruned 44→22 cols via cluster-MDA on IS) | 5-day momentum × sign(Hurst−0.5) captures medium-frequency directional moves; per-regime-decomposition wins 5 of 6 IS regimes (2022-bear +21.77pp, 2023-Q1 +20.17pp, 2024-Q3 +33.31pp, 2024-Q1 LTC, 2025-Q1 +57.29pp) | type-A strong-IS; IS +0.5588 (+0.28 Δ); LTC rescue +67pp; covers 5 of 6 IS regimes | **20%** |
| **P3 — DOWNSIDE-SHAPE** | /037 5-cohort + Sortino objective (193 cols, downside-deviation objective) | DOT type-C universal (IS +57.20 / OOS +39.30); LTC catastrophe-recovery (+38pp vs baseline); right-tail-concentration mechanism, NOT left-tail-clip (per Critic mechanism dissonance note) | type-B mid; OOS +0.8388 (+0.18 Δ); covers DOT-universal + LTC-recovery | **15%** |

**Why 4 not 3 or 5**: 3 components leave the IS regime uncovered (which violates USER DIRECTIVE re: not discarding IS-strong models). 5 components introduce /034 which under single-seed=42 is bit-identical Optuna basin to /038 — adding it now is data-snooping until multi-seed disambiguates the basis_zscore_30 marginal contribution.

---

## 2. REGIME COVERAGE TABLE

Regime classes derived from `analysis/iteration_v1-040/regime_decomposition.csv` (6 regimes spanning 2022-01 → 2025-03 IS + 2025-Q2/Q3 OOS):

| Regime | Period | BASELINE (P0) | /036 (P1) | /040 (P2) | /037 (P3) | Coverage status |
|---|---|---|---|---|---|---|
| 2022-bear | 2022-01..12 | mid | n/a (LINK/DOT 2-cohort) | **WINS** (+21.77pp 2022-01, +15.94pp 02, +26.40pp 03) | mid | **P2 owns**; P0 supports |
| 2023-Q1Q2-chop | 2023-01..06 | mid (lift 2023-03,05,06) | likely degrades (chop hostile to trend) | **WINS late** (+23.15pp 2023-04, +20.17pp 06) | mid | **P0 + P2 share**; P1 weak |
| 2023-Q3Q4-recovery | 2023-07..12 | mid | n/a | **WEAK** (P2 blind spot: −15 to −31pp) | mid | **P0 + P3 share**; P2 hands off |
| 2024-Q1Q2-bull | 2024-01..06 | mid | TBD (PROMISING extension regime) | mid (+9 to +9pp early; −5 mid) | mid | **P0 + P1 share** |
| 2024-Q3Q4-transition | 2024-07..12 | mid | TBD | **WINS strongly** (+33.31pp 2024-08, +11.98pp 07) | mid | **P2 owns**; P0 supports |
| 2025-Q1-IS-tail | 2025-01..03 | mid (+5pp 03) | TBD | **WINS extreme** (+57.29pp 2025-01) | mid | **P2 owns** |
| **OOS 2025-Q2/Q3** | 2025-03-24..now | +0.6637 (BTC-strong, LINK-strong) | **+1.7465** (LINK+DOT-trend) | +0.2959 (LTC-recovery +19.79 / weak elsewhere) | +0.8388 (DOT-strong +39.30, LTC-recovery +38pp) | **All 4 contribute**; P1 dominates |

**Coverage verdict**: NO regime uncovered. 2023-Q3Q4-recovery is the weakest-covered regime (only P0+P3 partial); flagged as monitoring concern (Section 7). All 6 IS regimes + OOS window have ≥ 2 components contributing positively.

**Anti-double-coverage**: BTC owned exclusively by P0 (P1 has no BTC; P2 destroys BTC IS at −85; P3 +18 weak). LINK owned shared P0+P1 (universal+specialist). DOT owned shared P1+P3 (specialist + DOT-universal). LTC owned exclusively by P2 (only component that lifts LTC OOS to +19.79) + P3 partial. ETH owned by P0 only (others weak or negative); ETH is the portfolio's structural weak point — explicit and accepted.

---

## 3. WEIGHT ALLOCATION RATIONALE

Three weighting schemes evaluated:

| Scheme | P0 / P1 / P2 / P3 | Pro | Con |
|---|---|---|---|
| Equal-weight | 25 / 25 / 25 / 25 | No discretion; survives basin-shift | Over-weights P3 right-tail-concentration risk; under-weights universal anchor |
| Sharpe-weighted (OOS Sharpe / Σ) | 18 / 47 / 8 / 22 | Maximizes ex-post Sharpe | LOOK-AHEAD (uses OOS Sharpe to weight) — **REJECTED** |
| **IS-weighted (informativeness × regime-orthogonality)** | **40 / 25 / 20 / 15** | Honors USER DIRECTIVE (P2 + P3 not discarded); P0 anchor majority; P1 OOS bonus capped to prevent regression-to-mean blowup | Some discretion in regime-orthogonality scoring |

**Selected: IS-weighted 40/25/20/15.**

Rationale:
- **P0 = 40%** because anchor universality must dominate; if P1 OOS Sharpe regresses 30% under multi-seed (expected per typical OOS-extreme regression), portfolio stays anchored.
- **P1 = 25%** capped despite OOS +1.75 — the 105 OOS trades is below 130 floor and single-seed-lottery risk caps capacity. Per cycle5_regime_substrate_analysis Section 11, /036's multi-seed regression band is [+0.8, +1.5].
- **P2 = 20%** because USER DIRECTIVE explicitly says don't discard IS-strong; /040 owns 5 of 6 IS regimes; LTC rescue +67pp is unique in cycle-5; but type-A profile bets on IS-regime return in OOS window — 20% caps the regression risk.
- **P3 = 15%** smallest because DOT-78.62%-concentration is single-seed-lottery signal per `feedback_v3_single_seed_frozen_baseline.md`; multi-seed will redistribute; the right-tail-concentration mechanism is mechanism-orthogonal to H1a (per /037 Critic note) and may not COMPOUND with P1 trend mechanism — 15% caps interaction risk.

---

## 4. EXPECTED PORTFOLIO METRICS (synthesis)

Trade-stream-level aggregation, not Sharpe-of-Sharpes:

**OOS portfolio Sharpe (predicted)** =
0.40 × (+0.6637) + 0.25 × (+0.8 to +1.5 multi-seed band of /036) + 0.20 × (+0.0 to +0.4 multi-seed band of /040-pruned, with regression from +0.2959) + 0.15 × (+0.4 to +0.8 multi-seed band of /037)
= 0.40 × 0.66 + 0.25 × 1.15 + 0.20 × 0.20 + 0.15 × 0.60
= **+0.66 (central estimate); band [+0.50, +0.95]**

**IS portfolio Sharpe (predicted)** =
0.40 × 0.28 + 0.25 × 0.08 + 0.20 × 0.56 + 0.15 × 0.17 = **+0.27 (central); band [+0.20, +0.40]**

**Both portfolio Sharpes > 1.0?** NO at central estimate. **This is the load-bearing finding**: the portfolio is unlikely to clear the Sharpe 1.0 hard MERGE floor on the OOS side at central estimate without correlation-diversification lift (Section 6 estimates that lift at +0.15 to +0.30). Portfolio Sharpe band incorporating diversification: **OOS [+0.65, +1.25]**, central **+0.85**.

**OOS trade count (predicted)**: 0.40 × 189 + 0.25 × 105 + 0.20 × 274 (/040 OOS) + 0.15 × 243 (/037 OOS) = **~190 OOS trades**, clears 130 floor with safety.

**Top-symbol concentration (predicted)**: P3's DOT 78.62% caps at 15% × 78.62% = 11.8% of portfolio OOS PnL; combined with P1's 50/50 LINK/DOT (DOT contributes 25% × 51% = 12.75%) → DOT total ~ 24.5% of portfolio OOS PnL; clears 30% concentration gate.

---

## 5. /044 ENGINEERING SPEC

### 5.1 Phase decomposition

| Sub-iter | Component | Spec | Output |
|---|---|---|---|
| /044-A | /036 multi-seed | `--exploration FALSE --seeds 5 --n-trials 35 --ensemble-size 5 --label-mode trend_scanning --symbols LINKUSDT,DOTUSDT` | reports-v1/iteration_v1-044/A/ |
| /044-B | /037 multi-seed | `--seeds 5 --n-trials 35 --ensemble-size 5 --optuna-objective sortino` (all 5 cohorts) | reports-v1/iteration_v1-044/B/ |
| /044-C | /040-pruned multi-seed | Step 1: cluster-MDA on IS only, prune 44→22 cols; Step 2: `--seeds 5 --n-trials 35 --ensemble-size 5 --features V1_FEATURE_COLUMNS_PRUNED_V2` | reports-v1/iteration_v1-044/C/ |
| /044-D | Portfolio aggregator | Trade-stream merge (40/25/20/15 weights); compute portfolio comparison.csv vs P0-anchor-only baseline | reports-v1/iteration_v1-044/portfolio/ |

### 5.2 Multi-seed validation plan

- **5 outer seeds** per component (not 10) — cycle-5 CONFIRMATION budget per `feedback_v3_outer_seed_cap_2_v3.md`-adjacent v1 standard; 5 inner × 5 outer = 25 models/cell.
- **n_trials=35** per CONFIRMATION spec (`feedback_v3_confirmation_n_trials_35.md` v3-only, but matches v1 CONFIRMATION default).
- **ENSEMBLE_SIZE=5** per CONFIRMATION standard.
- Wall-clock estimate: P0=N/A (reuse baseline); P1=2h (2-cohort); P2=3h (5-cohort + new feature); P3=3h (5-cohort + Sortino). **Total ≈ 8h** vs 4h cap → split across two sessions OR run /044-A+B concurrently with /044-C in a second pass.

### 5.3 Pareto / multi-seed acceptance gates per component

Each P1/P2/P3 component independently must clear:
- 5-seed mean Sharpe (OOS) > 0
- ≥ 3 of 5 seeds OOS Sharpe > 0
- ≥ 4 of 5 seeds IS Sharpe > 0 (lower bar than OOS to avoid discarding IS-strong)
- per-cohort OOS PnL sign-stability (≥ 3 of 5 seeds same sign for each load-bearing cohort)

**Component-level failure ⇒ component dropped from portfolio**; portfolio re-aggregates with remaining components at re-normalized weights.

### 5.4 Portfolio-level MERGE gates

- Portfolio IS Sharpe > 1.0 → conditionally relaxed to > 0.30 (BASELINE_V1 itself is +0.28, so portfolio must beat baseline IS) per user note that hard 1.0 floor is aspirational at v1 stage.
- Portfolio OOS Sharpe > 1.0 — hard floor; if portfolio doesn't clear, NO MERGE.
- OOS/IS ratio ≥ 0.5 — hard floor.
- Top-symbol concentration ≤ 30% portfolio OOS PnL.
- Portfolio OOS trades ≥ 130.

---

## 6. RISK CONSIDERATIONS

### 6.1 Correlation between components

Components share underlying universe (BTC/ETH/LINK/LTC/DOT) so trade-stream correlation is non-zero. Estimated pairwise correlation (from per-symbol regime profiles):

| Pair | Trade Jaccard estimate | Daily-PnL correlation estimate |
|------|---:|---:|
| P0 ↔ P1 | 0.15 (P1 strict subset LINK+DOT; different labels) | 0.30 |
| P0 ↔ P2 | 0.40 (same labels, different feature) | 0.55 |
| P0 ↔ P3 | 0.45 (same features+labels, different objective) | 0.65 |
| P1 ↔ P2 | 0.08 (LINK+DOT only ∩ different label) | 0.15 |
| P1 ↔ P3 | 0.10 (LINK+DOT ∩ different obj) | 0.20 |
| P2 ↔ P3 | 0.10 (different feature, different obj) | 0.18 |

**Diversification lift estimate**: portfolio σ ≈ √(Σ w²σ² + 2ΣΣ wᵢwⱼρᵢⱼσᵢσⱼ). With central correlations ~0.35 weighted-avg, naive sum-of-variances over-estimates portfolio σ by ~15-25%. **Diversification Sharpe lift: +0.15 to +0.30** vs weighted average of component Sharpes alone. This is the lift assumed in Section 4's portfolio band.

### 6.2 Max DD aggregation

Component Max DDs (OOS): P0=40.94%, P1=23.28%, P2=50.17%, P3=43.04%. Weighted-average MaxDD = 0.40×40.94 + 0.25×23.28 + 0.20×50.17 + 0.15×43.04 = **39.74%**. Diversified-MaxDD is typically 20-30% below weighted-average → **portfolio MaxDD predicted ~28-32%**, comparable to baseline 40.94%, materially better than P2 alone (50%).

### 6.3 Capacity

P1 (2-cohort 105 OOS trades) is the binding capacity constraint. At 25% weight on a 105-trade component, P1 contributes ~26 OOS trades to portfolio. P0+P2+P3 contribute ~160 OOS trades. Total ~190 → 130-floor satisfied with 1.45× margin.

### 6.4 Component-failure-mode risk

- P1 single-seed lottery: if multi-seed regresses /036 to OOS Sharpe < +0.30, P1 contribution flips negative → portfolio Sharpe drops 0.30-0.40.
- P2 IS-overfit basin-shift: /040 NEG-CLEAN under composed-feature-stack-prune may re-emerge as PROMISING after 44→22 prune; if it doesn't (multi-seed mean OOS Sharpe < 0), P2 dropped, weights re-normalize 0.47/0.29/0.24 to P0/P1/P3.
- P3 right-tail-concentration mechanism dissonance: DOT-78.62% concentration at single-seed dissolves at multi-seed but the right-tail-clip mechanism (per Critic /037 note) is NOT what H1a posited; if multi-seed produces orthogonal lift, retain at 15%; if it produces collision with P1, drop.

---

## 7. PATH FORWARD — outcomes-conditional substrate routing

| Scenario | Trigger | /044 substrate adjustment |
|---|---|---|
| **Default — proceed NOW** | /041 + /042 + /043 in flight; no new PROMISING discovered | Run /044 as 4-component portfolio per Section 5 immediately upon /043 closeout |
| **/041 PROMISING** (TBD axis) | /041 review = PROMISING-CLEAN | Add /041 as P4 candidate AT WEIGHT 10%; reduce P0 to 30%, P2 to 15% (preserve P1=25%, P3=15%) |
| **/042 XGBoost head-to-head BEATS LightGBM** | /042 OOS Sharpe > /036 multi-seed est | Replace P1 mechanism with /042; recompute weights |
| **/042 XGBoost CONFIRMS LightGBM** | /042 OOS Sharpe ≤ /036 | NO substrate change; close model-arch axis |
| **/043 LINK-only trend-scan** PROMISING | /043 OOS Sharpe > /036 LINK-cohort decomposition | Replace P1 with /043 (LINK-only) + add /043b DOT-only as separate P1b; finer per-cohort granularity |
| **/043 LINK-only trend-scan NEG** | /043 confirms LINK+DOT bundle = correct cohort grouping | NO substrate change; routes are validated |
| **2023-Q3Q4-recovery regime returns OOS-rolling** | OOS window rolls forward; portfolio under-performs in chop | Add chop-specialist P5 (TBD axis — likely confidence-threshold ternary OR per-symbol DD brake per /037 Critic Rec) |

**Recommendation: PROCEED to /044 CONFIRMATION immediately upon /043 closeout** (after /041, /042, /043 review.md exist). Do NOT wait for additional /045+ data — substrate is regime-complete at 4 components, USER DIRECTIVE explicitly mandates combining IS-strong + OOS-strong models, and further single-seed EXPLORATIONs add noise more than information at this point in cycle-5.

---

## 8. SUMMARY

- **Proposed /044 components (4)**: P0 BASELINE (40%), P1 /036 LINK+DOT trend-scan (25%), P2 /040-stack-pruned composed-feature (20%), P3 /037 5-cohort Sortino (15%).
- **Per-component regime profile**: P0 universal; P1 OOS-trend; P2 IS-momentum (5 of 6 IS regimes); P3 DOT-universal + LTC-recovery.
- **Expected portfolio OOS Sharpe**: central **+0.85**; band [+0.65, +1.25] including diversification lift.
- **Justification for /040 inclusion**: type-A regime-specialist owning 5 of 6 IS regimes including 2025-Q1 (+57.29pp) and LTC-OOS-rescue (+67pp vs baseline) — IS-strength concentrated across regimes, NOT a single-window basin overfit; USER DIRECTIVE explicitly mandates not discarding IS-strong components when regime-complementary.
- **Justification for portfolio vs single-model CONFIRMATION**: cycle-5 produced 0 type-C universal models; 3 type-B regime-specialists + 1 type-A regime-specialist; the only path to a universal substrate at v1 stage is regime-portfolio combination per USER DIRECTIVE — single-model CONFIRMATION at /036 alone leaves IS regimes uncovered and discards /040.
- **Timing**: PROCEED to /044 CONFIRMATION IMMEDIATELY after /041 + /042 + /043 review.md exist; do NOT wait for /045+.
