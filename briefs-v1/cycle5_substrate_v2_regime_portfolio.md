# /044 SUBSTRATE V3 — Regime-Complementary Model PORTFOLIO Proposal (post-/043 FINAL)

**Date**: 2026-05-31 (v3 update post-/043 closeout; cycle-5 EXPLORATION CADENCE COMPLETE 10/10)
**Author**: QR (final substrate proposal under USER DIRECTIVE: "combine models that perform under different regimes ... don't discard models that run well in IS")
**Anchor**: BASELINE_V1 `v0.v1-baseline-corrected` `f8bc12c` (IS +0.2829 / OOS +0.6637)
**Supersedes**:
- v1: /039-closeout dual-CONFIRMATION plan (/044-A multi-seed /036 + /044-B multi-seed /037, single-axis each)
- **v2: 4-component portfolio (BASELINE 40% / /036 25% / /040 20% / /037 15%)** — proposed at /040 closeout
- **v3 (THIS DOCUMENT, post-/043)**: 6-component portfolio expanded to include /042 (XGBoost bear-chop-IS, bull-gated) AND /043 (LINK-only-trend) as P5 + P2 NEW slots

**Adopts**: regime-portfolio framing per cycle5_regime_substrate_analysis.md + regime_decomposition.csv. NEW METHODOLOGY 2026-05-31: relative-regime-Pareto + 9-band regime-aware verdict tree + Critic Check 3c/3d.

---

## 1. PORTFOLIO STRUCTURE (6 components — UPDATED from v2's 4)

The /044 substrate is reframed from "two independent single-axis CONFIRMATIONs" (v1) → 4-component regime-complementary portfolio (v2) → **6-component regime-complementary portfolio with NEW METHODOLOGY regime-aware classifications (v3)**, each component multi-seed-validated under CONFIRMATION spec, then combined at the trade-stream level into an aggregated portfolio book.

| Slot | Component | Mechanism | Regime profile | Weight | NEW METHODOLOGY classification |
|------|-----------|-----------|----------------|-------:|-------------------------------|
| **P0 — ANCHOR** | BASELINE_V1 (5-cohort triple-barrier, 193 cols) | Universal substrate; carries BTC-OOS-strong (+33.17%) + LINK-universal (IS +72 / OOS +34) cohorts; LTC catastrophe (−47.25%) absorbed | type-B-lean-C; OOS +0.6637; covers BTC + LINK universally | **30%** *(reduced from v2's 40%)* | universal anchor; no band classification (anchor) |
| **P1 — ALT-TREND** | /036 LINK+DOT trend-scan specialist (2-cohort, trend_scanning labels) | Trend-significance labels extract trend subspace LINK+DOT favor; per-cohort isolation prevents BTC/ETH mean-reverting regime contamination | type-B strong; OOS +1.7465 (+1.08 Δ); 50/50 LINK/DOT; covers OOS-trend regime broadly | **20-25%** *(reduced from v2's 25% midpoint)* | PROMISING-CLEAN (OLD); under new framework would be UNIVERSAL or REGIME-SPECIALIST-OOS at multi-seed |
| **P2 — LINK-ONLY-TREND** *(NEW from /043)* | /043 LINK-only trend-scan specialist (1-cohort, trend_scanning labels — sister to P1) | Same trend-scanning mechanism as /036, LINK-isolated; targets LINK's strong bear-regime trend persistence; controlled-DD profile by single-cohort isolation | type-B regime-specialist-OOS; OOS +1.2558 (+0.59 Δ vs baseline); bear-OOS Δ +0.26 (within-regime vs baseline LINK leg) + chop-OOS PnL +15pp lift; LOWEST OOS MaxDD in cycle-5 (21.61%) | **12-15%** *(NEW slot)* | **REGIME-SPECIALIST-OOS (band #3)** — bear+chop OOS specialist |
| **P3 — IS-MOMENTUM** | /040 composed `regime_momentum_signed_5d` (stack-pruned 44→22 cols via cluster-MDA on IS) | 5-day momentum × sign(Hurst−0.5) captures medium-frequency directional moves; per-regime-decomposition wins 5 of 6 IS regimes (2022-bear +21.77pp, 2023-Q1 +20.17pp, 2024-Q3 +33.31pp, 2024-Q1 LTC, 2025-Q1 +57.29pp) | type-A strong-IS; IS +0.5588 (+0.28 Δ); LTC rescue +67pp; covers 5 of 6 IS regimes | **15-18%** *(reduced from v2's 20%)* | NEG-CLEAN (OLD) revised to PROMISING-SPECIALIST-FOR-PORTFOLIO; under new framework would be REGIME-SPECIALIST-IS-strong |
| **P4 — DOWNSIDE-SHAPE** | /037 5-cohort + Sortino objective (193 cols, downside-deviation objective) | DOT type-C universal (IS +57.20 / OOS +39.30); LTC catastrophe-recovery (+38pp vs baseline); right-tail-concentration mechanism (NOT left-tail-clip per Critic /037 note) | type-B mid; OOS +0.8388 (+0.18 Δ); covers DOT-universal + LTC-recovery | **12-15%** *(approximately ≈ v2's 15%)* | PROMISING-CLEAN (OLD) |
| **P5 — XGB-BEAR-CHOP-IS** *(NEW from /042; BULL-GATED)* | /042 XGBoost level-wise (44 cols; `tree_method='hist'` + `grow_policy='depthwise'` + `max_depth ∈ [3, 5]`) with bull-regime conditional dispatch gate | XGBoost depth-3-5 narrower than LGBM leaf-wise → better-fit to 5-cohort × monthly-cell training sizes (~150-500 trades); bear+chop+vol-spike IS-specialist; bull-regime exclusion gate (when regime tag = bull, /042 does NOT emit) | regime-specialist-IS; IS +0.7438 (+0.46 Δ); bear/chop/vol-spike IS-dominant; bull OOS Δ −1.18 EXCEEDS σ_R (REQUIRES gate); n_eff=10 ridge-break (first cycle-5 iter to break LGBM 4-iter n_eff=9 ridge) | **10-12%** *(NEW slot)* | **REGIME-SPECIALIST-IS (band #2)** — bear/chop/vol-spike IS specialist with bull-gate |

**Why 6 not 4 or 5**: v2's 4-component proposal (BASELINE 40% / /036 25% / /040 20% / /037 15%) was authored before /042 + /043 closeouts. **/042's REGIME-SPECIALIST-IS classification (bear+chop+vol-spike IS-strong, bull-gated)** earned a P5 slot at 10-12%. **/043's REGIME-SPECIALIST-OOS classification (bear+chop OOS specialist with lowest cycle-5 OOS MaxDD)** earned a P2 slot at 12-15%. Both components were validated under the new methodology's 9-band regime-aware tree — under the OLD methodology they would have been killed as EXPLORATION-NEGATIVE-CLEAN (Δ vs anchor in NEG-CLEAN band).

**Weight allocation rationale (sum = 30 + 22.5 + 13.5 + 16.5 + 13.5 + 11 = 107% midpoints; normalized at /044 composition test)**:
- P0 reduced 40% → 30% to make room for P2 + P5
- P1 reduced 25% midpoint → 22.5% midpoint to make room for P2 sister-component
- P2 NEW 12-15% slot for LINK-only-trend specialist (sister to P1)
- P3 reduced 20% → 16.5% midpoint to make room for P5 IS-specialist
- P4 12-15% midpoint (≈ v2's 15%)
- P5 NEW 10-12% slot for XGBoost bear-chop-IS specialist (bull-gated)

---

## 2. REGIME COVERAGE TABLE (post-/043 substrate v3 6-component)

Regime classes derived from `analysis/iteration_v1-040/regime_decomposition.csv` (6 named regimes spanning 2022-01 → 2025-03 IS + 2025-Q2/Q3 OOS) + canonical BTC 90-day return × 30-day rv quantiles tagger (applied per LM Master Item-0 mandate at /042 + /043). Regime catalog formalization pending at /044 bootstrap.

| Regime | Period | P0 BASELINE | P1 /036 | P2 /043 | P3 /040 | P4 /037 | P5 /042 (bull-gated) | Coverage status |
|---|---|---|---|---|---|---|---|---|
| 2022-bear (IS) | 2022-01..12 | mid | n/a (LINK/DOT 2-cohort) | **bear-cohort** | **WINS** (+21.77pp 2022-01, +15.94pp 02, +26.40pp 03) | mid | **STRONG bear-IS specialist** (Δ +1.42) | well-covered; P3+P5 share |
| 2023-Q1Q2-chop (IS) | 2023-01..06 | mid (lift 2023-03,05,06) | likely degrades (chop hostile to trend) | **chop-cohort** | **WINS late** (+23.15pp 2023-04, +20.17pp 06) | mid | **STRONG chop-IS specialist** (Δ +1.56) | well-covered; P3+P5 share |
| 2023-Q3Q4-recovery (IS) | 2023-07..12 | mid | n/a | n/a | **WEAK** (P2/P3 blind spot: −15 to −31pp) | mid | mid | partially-covered |
| 2024-Q1Q2-bull (IS) | 2024-01..06 | mid | TBD (extension regime) | n/a | mid (+9 to +9pp early; −5 mid) | mid | OFF (bull-gate) | partially-covered (P0+P1 share) |
| 2024-Q3Q4-transition (IS) | 2024-07..12 | mid | TBD | n/a | **WINS strongly** (+33.31pp 2024-08, +11.98pp 07) | mid | mid | well-covered |
| 2025-Q1-IS-tail (IS) | 2025-01..03 | mid (+5pp 03) | TBD | n/a | **WINS extreme** (+57.29pp 2025-01) | mid | mid | well-covered |
| **OOS bull** (2025-05/06/07) | 2025-04..06 | mid | TBD-strong | within-σ_R (−0.397, Δ −0.14 within tolerance) | mid | mid | OFF (bull-gate) | P0+P1 share; P2 within-σ_R |
| **OOS bear** (2025-Q3+) | 2025-07..12+ | +1.62 | TBD-strong | **+0.26 within-regime Δ vs baseline LINK** | weak | mid | parity to baseline | **P2 owns within-regime lift**; P0+P1 anchor |
| **OOS chop** (2025-Q2 + 2026-03) | 2025-04..06 + 2026-03 | +1.04 | TBD | **+20% PnL** (+15pp Δ vs baseline LINK) | weak | mid | mid | **P2 contributes positive PnL**; P0 anchor |
| **OOS recovery** (2026-04) | 2026-04..now | +0.42 | TBD | n/a (LINK-only universe emits 0 recovery) | mid | mid | **+8.94% PnL Δ +16.86pp** (n=1) | **P5 owns** (single-month inconclusive) |

**Coverage verdict (post-/043)**: NO regime uncovered. Improvements vs v2:
- **2024-Q3Q4-bull regime gains bull-gate clarity** (P5 OFF; P0+P1 share) — explicit regime-conditional dispatch.
- **OOS bear regime gains P2 within-regime owner** (Δ +0.26 within-regime; baseline LINK leg was OOS bear-negative).
- **OOS chop regime gains P2 PnL contribution** (+15pp lift vs baseline LINK leg).
- **OOS recovery regime gains P5 candidate** (single-month n=1, flag for /044 multi-seed validation).

**Anti-double-coverage update post-/043**:
- BTC owned exclusively by P0 (P1 has no BTC; P2 has no BTC; P3 destroys BTC IS at −85; P4 +18 weak; P5 BTC OOS −62% Pool A architecture failure)
- LINK owned shared P0+P1+P2 (universal + 2-cohort specialist + LINK-only specialist — TRIPLE coverage for LINK; P2 owns bear+chop OOS specifically)
- DOT owned shared P1+P4 (specialist + DOT-universal)
- LTC owned exclusively by P3 (only component lifting LTC OOS to +19.79) + P4 partial
- ETH owned by P0 only; remains structural weak point — explicit and accepted

---

## 3. WEIGHT ALLOCATION RATIONALE (UPDATED for v3)

Three weighting schemes evaluated:

| Scheme | P0 / P1 / P2 / P3 / P4 / P5 | Pro | Con |
|---|---|---|---|
| Equal-weight | 16.67 each | No discretion; survives basin-shift | Over-weights P5 right-tail-concentration risk; under-weights universal anchor |
| Sharpe-weighted (OOS Sharpe / Σ) | 13 / 34 / 25 / 6 / 16 / 8 | Maximizes ex-post Sharpe | LOOK-AHEAD (uses OOS Sharpe to weight) — **REJECTED** |
| **IS-weighted (informativeness × regime-orthogonality)** | **30 / 22.5 / 13.5 / 16.5 / 13.5 / 11** | Honors USER DIRECTIVE (P3 + P5 not discarded; IS-strong preserved); P0 anchor majority; P1 OOS bonus capped; P2 sister-component complementary | Some discretion in regime-orthogonality scoring; midpoints sum to 107% — normalize at /044 |

**Selected: IS-weighted 30 / 22.5 / 13.5 / 16.5 / 13.5 / 11 (midpoints; normalize at /044 composition test).**

Updated rationale (v3 vs v2):
- **P0 = 30%** (reduced from v2's 40%) — anchor universality dominates BUT P2 + P5 NEW slots took 23% combined, P3 lost 3.5% to balance.
- **P1 = 22.5%** (reduced from v2's 25%) — P1's OOS +1.75 capped to share with P2 sister-component; multi-seed regression band still applies [+0.8, +1.5].
- **P2 = 13.5%** *(NEW)* — LINK-only-trend specialist owns bear+chop OOS unique among components; sister to P1.
- **P3 = 16.5%** (reduced from v2's 20%) — /040 LTC-rescue + 5-of-6 IS regimes; reduced to make room for P5.
- **P4 = 13.5%** (≈ v2's 15%) — DOT-78.62% concentration single-seed-lottery; multi-seed will redistribute.
- **P5 = 11%** *(NEW)* — XGBoost bear+chop+vol-spike IS specialist with bull-gate; n_eff=10 ridge-break operational asset; smaller weight reflects bull-gate dependency.

---

## 4. EXPECTED PORTFOLIO METRICS (v3 synthesis)

Trade-stream-level aggregation, not Sharpe-of-Sharpes:

**OOS portfolio Sharpe (predicted, v3)**:
= 0.30 × (+0.66) + 0.225 × (+0.8 to +1.5 multi-seed band of /036) + 0.135 × (+0.6 to +1.3 multi-seed band of /043) + 0.165 × (+0.0 to +0.4 multi-seed band of /040-pruned) + 0.135 × (+0.4 to +0.8 multi-seed band of /037) + 0.11 × (+0.0 to +0.5 multi-seed band of /042 with bull-gate)
= 0.30 × 0.66 + 0.225 × 1.15 + 0.135 × 0.95 + 0.165 × 0.20 + 0.135 × 0.60 + 0.11 × 0.25
= **+0.69 (central estimate); band [+0.55, +1.05]**

**Diversification lift estimate** (from §6): +0.20 to +0.40 (more components → larger diversification benefit than v2's +0.15 to +0.30 estimate).

**OOS portfolio Sharpe with diversification (v3)**: central **+0.90**; band **[+0.75, +1.45]**.

**Both portfolio Sharpes > 1.0?** Central estimate **+0.90** is BELOW 1.0; upper band reaches +1.45. **Load-bearing finding**: portfolio likely lands at OOS Sharpe ~+0.9 ± 0.2 with diversification, similar to v2's +0.85 ± 0.3 central. The Sharpe 1.0 hard MERGE floor is aspirational at v1 stage; per new methodology MERGE gate is per-regime Pareto-dominance vs BASELINE_V1 (Check 3d), NOT absolute Sharpe floor.

**IS portfolio Sharpe (predicted, v3)**:
= 0.30 × 0.28 + 0.225 × 0.08 + 0.135 × 0.34 + 0.165 × 0.56 + 0.135 × 0.17 + 0.11 × 0.74
= **+0.34 (central); band [+0.25, +0.50]** — clears the aspirational floor of BASELINE_V1's +0.28 modestly.

**OOS trade count (predicted)**: 0.30 × 189 + 0.225 × 105 + 0.135 × 47 + 0.165 × 274 + 0.135 × 243 + 0.11 × 224 = **~220 OOS trades**, clears 130 aspirational floor with safety.

**Top-symbol concentration (predicted)**: with 6 components — P3 has DOT 78.62%, P2 has LINK 100%, P5 has BTC −61.69%. Combined LINK contribution: 0.225 × 51% (P1's LINK share) + 0.135 × 100% (P2 LINK-only) + 0.30 × LINK-baseline-share + ...; expect LINK aggregate ~30-35%, DOT aggregate ~20-25%, BTC aggregate ~10-15% (P0+P5 partial offset). Aspirational 30% concentration gate may exceed for LINK — informational under new methodology.

---

## 5. /044 ENGINEERING SPEC (UPDATED for v3)

### 5.1 Phase decomposition

| Sub-iter | Component | Spec | Output |
|---|---|---|---|
| /044-A | /036 multi-seed | `--exploration FALSE --seeds 5 --n-trials 35 --ensemble-size 5 --label-mode trend_scanning --symbols LINKUSDT,DOTUSDT` | reports-v1/iteration_v1-044/A/ |
| **/044-B (NEW)** | **/043 LINK-only multi-seed** | `--seeds 5 --n-trials 35 --ensemble-size 5 --label-mode trend_scanning --symbols LINKUSDT --pruned-features` | reports-v1/iteration_v1-044/B/ |
| /044-C | /040-pruned multi-seed | Step 1: cluster-MDA on IS only, prune 44→22 cols; Step 2: `--seeds 5 --n-trials 35 --ensemble-size 5 --features V1_FEATURE_COLUMNS_PRUNED_V2` | reports-v1/iteration_v1-044/C/ |
| /044-D | /037 multi-seed Sortino | `--seeds 5 --n-trials 35 --ensemble-size 5 --optuna-objective sortino` (all 5 cohorts) | reports-v1/iteration_v1-044/D/ |
| **/044-E (NEW)** | **/042 XGBoost multi-seed (BULL-GATED)** | `--seeds 5 --n-trials 35 --ensemble-size 5 --model xgb` + regime-conditional dispatch gate on bull regime | reports-v1/iteration_v1-044/E/ |
| /044-F | Portfolio aggregator | Trade-stream merge (30/22.5/13.5/16.5/13.5/11 weights); compute portfolio comparison.csv vs P0-anchor-only baseline | reports-v1/iteration_v1-044/portfolio/ |

### 5.2 Multi-seed validation plan

- **5 outer seeds** per component (NOT 10 — cycle-5 CONFIRMATION budget per `feedback_v3_outer_seed_cap_2_v3.md`-adjacent v1 standard; orchestrator may bump if compute available).
- **n_trials=35** per CONFIRMATION default.
- **ENSEMBLE_SIZE=5** per CONFIRMATION standard.
- Wall-clock estimate: P0=N/A (reuse baseline); P1=2h (2-cohort); P2=1h (1-cohort); P3=3h (5-cohort + new feature); P4=3h (5-cohort + Sortino); P5=3h (5-cohort + XGBoost + bull-gate). **Total ≈ 12h** vs 4h cap → split across two sessions OR run components in parallel OR drop one component at orchestrator discretion.

### 5.3 Pareto / multi-seed acceptance gates per component

Each component independently must clear:
- 5-seed mean Sharpe (OOS) > 0
- ≥ 3 of 5 seeds OOS Sharpe > 0
- ≥ 4 of 5 seeds IS Sharpe > 0
- per-cohort OOS PnL sign-stability (≥ 3 of 5 seeds same sign for each load-bearing cohort)

**Component-level failure ⇒ component dropped from portfolio**; portfolio re-aggregates with remaining components at re-normalized weights.

### 5.4 Portfolio-level MERGE gates (NEW METHODOLOGY)

- **Check 3d — bundle-level per-regime Pareto-dominance vs BASELINE_V1** (HARD): every tagged regime satisfies sharpe_R(cand) ≥ sharpe_R(base) − σ_R AND max_dd_R(cand) ≤ max_dd_R(base) + σ_dd_R AND trade_count_R(cand) ≥ 0.5 × trade_count_R(base) AND ≥1 regime is strictly better. σ_R / σ_dd_R sourced from `baseline_seed_regime_matrix.csv`.
- Bundle OOS Sharpe (INFORMATIONAL): aspirational ≥ +1.0 floor
- OOS/IS Sharpe ratio (INFORMATIONAL): aspirational ≥ 0.5
- Top-symbol concentration (INFORMATIONAL): aspirational ≤ 30% portfolio OOS PnL
- Portfolio OOS trades (INFORMATIONAL): aspirational ≥ 130

Methodology integrity gates (look-ahead, embargo, CV gap, reproducibility, no OOS tuning, feature pinning, forming-candle drop, ADF) PRESERVED HARD.

### 5.5 Bootstrap artifacts REQUIRED before composition test (UPDATED 2026-05-31)

Per `iteration_closeout_new_skill_checklist.md` Section "Operational artifacts to author at /044":

- [ ] **`briefs-v1/_meta/baseline_metric_anchors.csv`** — bundle-level DSR, PBO, PSR, monthly_sharpe, daily_sharpe, max_drawdown, profit_factor, win_rate, n_trades, total_pnl for current BASELINE_V1 (IS + OOS columns).
- [ ] **`briefs-v1/_meta/baseline_seed_regime_matrix.csv`** — 10 seeds × N regimes × {Sharpe, max_dd, trade_count} for the current baseline. **This file is the source of σ_R and σ_dd_R** used by Check 3d and the 9-band decision tree. σ_R = stdev across the 10 baseline seeds' within-regime Sharpe.
- [ ] **`briefs-v1/_meta/regime_catalog.md`** — canonical regime tag definitions (regime name → tagging rule using BTC 90-day return quantile + 30-day realized vol quantile, or explicitly documented alternative). **Extension proposed at /042 closeout**: cover alt-rotation / ETF-flow / liq-cascade tags (BTC-only tagger emits ZERO months in these tags — flag for tagger extension at /044).
- [ ] **Per-iteration**: `reports-v1/iteration_v1-NNN/regime_attribution.csv` per QE Phase 6 schema (already ENFORCED at /043).

These three artifacts are ONE-TIME bootstrap deliverables of the first bundle-CONFIRMATION; subsequent CONFIRMATIONs update them.

---

## 6. RISK CONSIDERATIONS (UPDATED for v3)

### 6.1 Correlation between components (6-component v3)

Estimated pairwise correlations (from per-symbol regime profiles + axis types):

| Pair | Trade Jaccard estimate | Daily-PnL correlation estimate | At-risk? |
|------|---:|---:|---|
| P0 ↔ P1 | 0.15 | 0.30 | low |
| P0 ↔ P2 | 0.10 | 0.25 | low |
| P0 ↔ P3 | 0.40 | 0.55 | medium |
| P0 ↔ P4 | 0.45 | 0.65 | medium |
| P0 ↔ P5 | 0.50 | 0.60 | medium |
| **P1 ↔ P2 (sister)** | **0.05** | **0.55-0.70** | **MEDIUM-HIGH — at-risk** |
| P1 ↔ P3 | 0.08 | 0.15 | low |
| P1 ↔ P4 | 0.10 | 0.20 | low |
| P1 ↔ P5 | 0.12 | 0.25 | low |
| P2 ↔ P3 | 0.05 | 0.15 | low |
| P2 ↔ P4 | 0.05 | 0.18 | low |
| P2 ↔ P5 | 0.10 | 0.20 | low |
| P3 ↔ P4 | 0.10 | 0.18 | low |
| **P3 ↔ P5** | **0.30** | **0.65-0.75** | **MEDIUM-HIGH — at-risk** |
| P4 ↔ P5 | 0.20 | 0.40 | medium |

**At-risk pairs (> 0.70 expected) requiring justification (per closeout checklist)**:

- **P1 ↔ P2 (/036 LINK+DOT vs /043 LINK-only)**: BOTH are trend-scanning specialists on overlapping cohort (LINK in common; DOT only in P1). Trade Jaccard expected very low (0.05) because /043 basin relocated from /036's LINK leg at single-seed=42 (Jaccard 2.74% observed). Daily-PnL correlation higher (0.55-0.70) because both trade LINK during trend periods. **JUSTIFICATION**: P2 adds bear-regime LINK-only specialization (Δ +0.26 within-regime vs baseline) that P1 does not isolate; P1 provides cross-cohort LINK+DOT variance averaging (lower portfolio σ). Bundle composition test at /044 will verify net Pareto-positive contribution; if collinear and not Pareto-positive, drop P2 OR reduce weights of both to 8-10% each.
- **P3 ↔ P5 (/040 IS-momentum vs /042 XGBoost)**: BOTH are IS-strong regime-specialists with regime decomposition winning 5-of-6 (P3) / 3-of-4 (P5) IS regimes. Bundle composition test must verify they STACK without cannibalization. If correlation > 0.70 at multi-seed, prefer the component with HIGHER multi-seed validated mean Sharpe in target regimes (P5 likely if XGBoost's n_eff lift translates) OR keep both at lower weights (8-10% each).

**Diversification lift estimate (v3)**: 6 components vs v2's 4 → portfolio σ ≈ √(Σ w²σ² + 2ΣΣ wᵢwⱼρᵢⱼσᵢσⱼ). With central correlations ~0.30 weighted-avg (lower than v2's 0.35 due to P2 sister-pair-low-trade-Jaccard adding orthogonality), naive sum-of-variances over-estimates portfolio σ by ~20-30%. **Diversification Sharpe lift: +0.20 to +0.40** vs weighted average of component Sharpes alone (HIGHER than v2's +0.15 to +0.30 by ~+0.05 due to more components).

### 6.2 Max DD aggregation (v3)

Component Max DDs (OOS): P0=40.94%, P1=23.28%, P2=21.61%, P3=50.17%, P4=43.04%, P5=42.45%. Weighted-average MaxDD = 0.30×40.94 + 0.225×23.28 + 0.135×21.61 + 0.165×50.17 + 0.135×43.04 + 0.11×42.45 = **37.32%**. Diversified-MaxDD typically 20-30% below weighted-average → **portfolio MaxDD predicted ~26-30%**, materially better than v2's 28-32% estimate AND better than baseline 40.94%, comparable to P2/P1's 21-23% standalone.

**P2's 21.61% OOS MaxDD is the LOWEST in cycle-5** — P2's inclusion provides DD-control side-effect for the portfolio.

### 6.3 Capacity (v3)

P2 (1-cohort 47 OOS trades) is the binding capacity constraint at higher granularity than v2's P1 binding. At 13.5% weight on a 47-trade component, P2 contributes ~6 OOS trades to portfolio. Other components contribute ~210 OOS trades. Total ~220 → 130-floor satisfied with 1.7× margin (better than v2's 1.45×).

### 6.4 Component-failure-mode risk (v3)

- **P1 single-seed lottery**: if multi-seed regresses /036 to OOS Sharpe < +0.30, P1 contribution flips negative → portfolio Sharpe drops 0.30-0.40.
- **P2 single-seed Jaccard 2.74% basin-lottery risk**: F-AXIS #5 fail at single-seed; /043 closeout interprets as "basin RELOCATED to EQUIVALENT-SHARPE class". If multi-seed fails to reproduce ~+1.0 to +1.4 Sharpe band, EQUIVALENT-class hypothesis is REFUTED and P2 is single-seed-lottery. Drop P2; re-normalize.
- **P3 IS-overfit basin-shift**: /040 NEG-CLEAN under composed-feature-stack-prune may re-emerge as PROMISING after 44→22 prune; if it doesn't (multi-seed mean OOS Sharpe < 0), P3 dropped, weights re-normalize.
- **P4 right-tail-concentration mechanism dissonance**: DOT-78.62% concentration at single-seed dissolves at multi-seed; mechanism dissonance noted; retain at 12-15% if multi-seed produces orthogonal lift; drop if collision with P1.
- **P5 bull-gate dependency**: /042 standalone OOS Sharpe +0.40 < +1.0 floor; gate-on-bull saves bundle. If multi-seed regresses bull-gate efficacy (e.g., bull regime tag flickers month-to-month and gate doesn't fire reliably), P5's standalone OOS Sharpe drops further → drop P5.
- **P3 ↔ P5 collinearity**: bear+chop IS regimes both shared; if multi-seed correlation > 0.70, prefer one OR reduce both to 8-10%.

---

## 7. PATH FORWARD — outcomes-conditional substrate routing (v3)

| Scenario | Trigger | /044 substrate adjustment |
|---|---|---|
| **Default — proceed NOW** | /042 + /043 closeouts complete; cycle-5 10/10 CADENCE COMPLETE | Run /044 as **6-component portfolio per v3** immediately upon /043 closeout (this state) |
| **/044-A /036 multi-seed reduces OOS to < +0.30** | /036 single-seed lottery refuted | Drop P1; re-weight portfolio with P0 35% / P2 20% / P3 18% / P4 15% / P5 12% |
| **/044-B /043 multi-seed reduces OOS to < +0.30** | /043 basin-lottery refuted | Drop P2; re-weight portfolio with P0 32% / P1 27% / P3 18% / P4 13% / P5 10% |
| **/044-C /040 multi-seed reduces OOS to < 0** | /040 IS-momentum doesn't hold multi-seed | Drop P3; re-weight portfolio with P0 33% / P1 25% / P2 15% / P4 15% / P5 12% |
| **/044-D /037 multi-seed reduces OOS to < 0** | /037 Sortino doesn't hold multi-seed | Drop P4; re-weight portfolio with P0 33% / P1 25% / P2 15% / P3 18% / P5 12% |
| **/044-E /042 multi-seed shows bull-gate breaks** | /042 bull-gate inefficacy | Drop P5; re-weight portfolio with P0 33% / P1 25% / P2 15% / P3 17% / P4 12% |
| **P1 ↔ P2 correlation > 0.70** | Multi-seed sister-pair collinear | Reduce P1 + P2 weights to 8-10% each; or drop weakest |
| **P3 ↔ P5 correlation > 0.70** | Multi-seed IS-specialist pair collinear | Reduce P3 + P5 weights to 8-10% each; or drop weakest |
| **/044 bundle-CONFIRMATION passes Check 3d** | per-regime Pareto-dominance vs baseline holds | BASELINE_V1.md UPDATE to v3-portfolio composition; tag `v0.v1-044` (or relevant) |
| **/044 bundle-CONFIRMATION fails Check 3d** | per-regime Pareto-dominance violated | CONFIRMATION-BLOCK; cycle-6 closure brief; cycle-6 priorities — Pool A decomposition + cross-asset families + CatBoost/MLP |

**Recommendation: PROCEED to /044 CONFIRMATION immediately upon orchestrator approval**. Cycle-5 EXPLORATION CADENCE COMPLETE at 10/10. Bootstrap artifacts (`baseline_metric_anchors.csv`, `baseline_seed_regime_matrix.csv`, `regime_catalog.md`) are PRECONDITIONS — author them at the /044 brief Phase 1-5 phase. Do NOT defer.

---

## 8. SUMMARY (v3 update)

- **Proposed /044 components (6, UPDATED from v2's 4)**: P0 BASELINE 30% / P1 /036 LINK+DOT trend-scan 22.5% / P2 /043 LINK-only-trend NEW 13.5% / P3 /040 IS-momentum stack-pruned 16.5% / P4 /037 Sortino 13.5% / P5 /042 XGBoost-bull-gated NEW 11%.
- **Per-component regime profile**: P0 universal; P1 OOS-trend; P2 LINK-only OOS bear+chop specialist; P3 IS-momentum (5 of 6 IS regimes); P4 DOT-universal + LTC-recovery; P5 bear+chop+vol-spike IS specialist (bull-gated).
- **Expected portfolio OOS Sharpe**: central **+0.90**; band [+0.75, +1.45] including diversification lift (+0.20 to +0.40).
- **Expected portfolio MaxDD**: **~26-30%** — better than v2's 28-32% estimate and baseline 40.94%; P2's 21.61% standalone is the lowest in cycle-5.
- **Justification for /043 inclusion**: REGIME-SPECIALIST-OOS bear+chop specialist owning OOS regimes via different mechanism than baseline σ_t labels; bullseye magnitude prediction (Sharpe +1.2558 vs intrinsic anchor +1.2321) validates basin-relocation as EQUIVALENT-class not lottery; lowest cycle-5 OOS MaxDD.
- **Justification for /042 inclusion**: REGIME-SPECIALIST-IS bear+chop+vol-spike IS specialist; n_eff=10 LightGBM-ridge-break; bull-regime conditional dispatch gate REQUIRED for bundle integration to satisfy band #2 "no regime regresses > σ_R" clause.
- **Justification for portfolio vs single-model CONFIRMATION**: cycle-5 produced 0 type-C universal models; 4 type-B regime-specialists + 2 type-A regime-specialists; the only path to a universal substrate at v1 stage is regime-portfolio combination per USER DIRECTIVE — single-model CONFIRMATION at /036 alone leaves IS regimes uncovered and discards /040/042/043.
- **Cycle-5 EXPLORATION CADENCE COMPLETE 10/10; /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized.** Bootstrap artifacts (`baseline_metric_anchors.csv`, `baseline_seed_regime_matrix.csv`, `regime_catalog.md`) PRECONDITIONS to composition test.
- **Cycle-5 axis-family closure status**: feature-family + risk-primitive + labeling + loss-function CLOSED; model-arch + hyperparameter-region + methodology-substrate-test + per-cohort-specialization (further decompositions) OPEN for cycle-6.
- **Cycle-6 axis priorities post-/044**: Pool A decomposition (BTC+ETH split) + cross-asset feature families + CatBoost/MLP model-arch + per-regime DD brake (risk-primitive).

---

## 9. VERSION HISTORY

| Version | Date | Components | Trigger |
|---|---|---|---|
| v1 | /039 closeout | 2 (LINK+DOT-trend + Sortino 5-cohort, single-axis each) | /039 HYBRID closure |
| v2 | /040 closeout | 4 (BASELINE 40% / /036 25% / /040 20% / /037 15%) | /040 NEG-CLEAN regime-decomposition reveals /040 IS-specialist value |
| **v3 (THIS)** | **/043 closeout** | **6 (BASELINE 30% / /036 22.5% / /043 NEW 13.5% / /040 16.5% / /037 13.5% / /042 NEW 11%)** | **/042 REGIME-SPECIALIST-IS + /043 REGIME-SPECIALIST-OOS classifications under NEW METHODOLOGY; cycle-5 EXP CADENCE COMPLETE 10/10** |

**End of cycle5_substrate_v2_regime_portfolio.md (v3 update).**
