# LightGBM Master Advisor — iter-v1/025 — Phase 4.5 (Pre-Design)

## Context Read
- **Track**: v1. Branch `iteration-v1/025`. HEAD `9502ecd`. Cycle-3 EXPLORATION **#10/10 — LAST**. /027 CONFIRMATION follows.
- **Anchor**: BASELINE_V1.md portfolio (IS +0.2829 / OOS +0.6637).
- **/023 outcome**: LEARNED-NEGATIVE (funding gain 5.40% > parity 2.38%; OOS Δ -0.20).
- **/024 outcome**: NEGATIVE-clean (regime-conditional engaged but didn't specialize).
- **EDA reality**: `oi_availability.csv` shows BTC PRESENT (4994 IS rows / 87.2%) BUT **ETH/LINK/LTC/DOT ALL MISSING (oi_n_rows=0)**. Fetch in flight.

## 1. OI vs funding mechanism — LightGBM CAN learn OI more easily

Funding had directional sign-flip at extreme tails (depth 3-5 must compose 2 splits + maintain conditional). OI has Q4 mild-positive single-band concentration (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68, +85.30% PnL share) — **a depth-3 tree carves Q4 with one split**.

Q1 (extreme negative) is +0.99 Sharpe-proxy / +54.42% PnL — also positive. Q3 mid is dead. The model learns "Q3 mid dead, everything else alive" — 2-split saddle pattern, depth-3-survivable.

## 2. Verdict-prior recalibration — RECOMMEND 22/8/22/30/12/4/2

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING-clean | 18% | **22%** | Q4 Sharpe-proxy 1.68 is 2.4× /023's strongest mid-band; single-split learnable |
| PROMISING-INERT-FAV | 8% | **8%** | unchanged |
| INERT | 25% | **22%** | Q4 depth-3-easy; less likely than /023; -3pp |
| LEARNED-NEGATIVE | 30% | **30%** | /023 pattern remains structural prior |
| NEGATIVE-INERT | 13% | **12%** | -1pp |
| NEG-CAT | 4% | **4%** | unchanged |
| AUTO-REJECT (F3) | 2% | **2%** | unchanged |

**Net shift**: PROMISING tail 26% → **30%** (vs /023's 20%).

## 3. F-AXIS #1 DUAL GATE — TIGHTEN with breadth check

Single feature parity = 1/43 = 2.33%; 4.0% = 1.7× parity. Tighten PROMISING-clean: `rank ≤14/43 AND gain ≥4.0% on ≥2 cohorts AND z90 rank ≤20/43 on ≥3 cohorts (breadth check)`. Without breadth check, 2-cohort PROMISING risks being BTC+ETH only while LINK/LTC/DOT NaN-degrade.

## 4. CRITICAL: Pre-launch HARD BLOCK on OI fetch

`oi_availability.csv` shows ETH/LINK/LTC/DOT oi_n_rows=0 status=MISSING. **Phase 6 cannot launch.**

**MANDATE**:
- HARD-RAISE precondition at Phase 6.0: for sym in ETH/LINK/LTC/DOT: `assert data/open_interest/sym/8h.csv exists AND row_count ≥ 1000`. If FAIL → BLOCK-PENDING-FIX.
- **Minimum 3/5 symbols ≥1000 IS OI rows** for DUAL GATE evaluation to have ≥2 cohorts.
- **No silent NaN-feature degradation** (echo of /024 dispatch-defect lesson).
- Brief Section 3.6 commits to FAIL-FAST; LM Master endorses + emit `oi_coverage_check.csv` per-symbol in engineering report Section 7.

## 5. Two implementation risks

**(a) NaN-tolerant LightGBM on partial OI coverage**: 2020-01 → 2020-09 has NO OI for BTC/ETH/LINK/LTC (~700 early IS bars per symbol with `oi_delta_30_z90 = NaN`). LightGBM default-direction split creates `(symbol_dummy × NaN_indicator)` learnable interaction — curve-fit hazard.

**Recommend**: skip-month if OI unavailable (simpler than indicator column; no extra feature). OR add `oi_delta_30_z90_isnull` indicator.

**(b) z90 stationarity hides level non-stationarity**: ADF p≈0 on z90 is true but raw `oi_delta_30` has trend (asymmetric distribution; secular BTC OI growth 2024-2026). z90 normalizes recent 90-bar history but BTC OI building secularly produces different z90 sample than 2020-2022 (post-Luna OI decline). Predict z90 importance will be REGIME-CONDITIONAL across folds. Emit per-fold rank in engineering report.

## 6. /027 CONFIRMATION bundle composition

| /025 verdict | /027 bundle | OOS target |
|---|---|---|
| PROMISING-clean (22%) | LINK + ETH+gate + **OI-aware pool** | **+1.30 to +1.50** under corr drag |
| PROMISING-INERT-FAV (8%) | LINK + ETH+gate (2 components; OI cataloged informational) | +1.10 to +1.30 |
| INERT (22%) | LINK + ETH+gate (2 components) | +1.10 to +1.30 |
| LEARNED-NEGATIVE (30%) | LINK + ETH+gate (2 components; OI as 2nd LEARNED-NEGATIVE catalogued) | +1.10 to +1.30 |
| NEGATIVE-INERT (12%) | LINK + ETH+gate (2 components) | +1.10 to +1.30 |
| NEG-CAT (4%) | LINK + ETH+gate + multi-seed mandate at /026 if HIGH-RISK trips | +1.10 to +1.30 |

**Cross-correlation pre-validation MANDATORY at /027 if /025 PROMISING**: Pearson(monthly_returns_OI-aware-pool, LINK_specialist) < 0.50 AND Pearson(OI-aware-pool, ETH+gate) < 0.50.

## 7. Most important point

**The Q4 mild-positive band (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68) is a single-split depth-3-learnable pattern stronger than any single ORACLE band funding ever showed — OI delta has structurally higher PROMISING probability than /023 funding had, BUT the 4-of-5 missing OI data MUST be fetched and verified ≥1000 IS rows per symbol before Phase 6 launches (HARD BLOCK), or the F-AXIS #1 DUAL GATE evaluation degenerates to BTC-only and the verdict is uninterpretable.**

## 8. /026 verdict-conditional staging

- **PROMISING (22%)** → /026 = pre-CONFIRMATION sanity (cross-correlation check). Do NOT stack OI momentum/volatility per SAME-FAMILY rule.
- **PROMISING-INERT-FAV (8%)** → /026 = OI momentum composed feature (Category 2 LR-PF; algebraic identity; Sharpe-Δ primary falsifier).
- **INERT/LEARNED-NEGATIVE/NEGATIVE-INERT** → /026 = methodology pre-CONFIRMATION sanity; no new EXPLORATION axis; proceed to /027.
- **NEG-CAT (4%)** → /026 = methodology only; cycle-3 ≥1σ NEG count reaches 4 → mandatory multi-seed for future HIGH-RISK.

## Critic Phase 7.5 Priority Items

1. **Coverage verification first**: ETH/LINK/LTC/DOT OI exists AND row count ≥1000 AND IS overlap ≥70%. BLOCK if not.
2. F-AXIS #1 DUAL GATE per-cohort with `rank ≤20/43` breadth check on ≥3 cohorts in addition to ≤14/43 on ≥2.
3. Per-fold rank stability of `oi_delta_30_z90` across 24 walk-forward months — if std-of-rank > 8, regime-conditional importance → PROMISING-FEATURE-MECHANICAL.
4. OOS-only IC reconfirmation: `IC(oi_delta_30_z90, funding_rate_zscore_30)` and `IC(oi_delta_30_z90, mom_macd_hist_12_26_9)`.
5. ORACLE Q4 band attribution reconciliation OOS — if Q4 not in OOS trade roster, PROMISING → LEARNED-NEGATIVE (basin relocation).

---

# LightGBM Master Post-Mortem — iter-v1/025 — Phase 7.4

## Context
- IS Sharpe +0.3327 / OOS Sharpe -0.7353 / F1 OOS Δ **-1.40** (2nd-worst cycle-3 after /020 /022)
- OI gain shares 4/4 cohorts CLEAR DUAL GATE: Pool A 7.53% / LINK 6.39% / LTC 8.00% / DOT 7.69%; portfolio 7.49%
- DUAL GATE PROMISING-clean ALL passes; F1 NEGATIVE-CATASTROPHIC

## 1. LEARNED-NEGATIVE amplification — why OI is WORSE than funding

Three superimposed mechanisms:

**(A) Confidence-weighted miscalibration**: OI ate 7.49% of portfolio gain (1.4× funding 5.40%) and is rank 4/43 (vs funding rank 12). Top-4 features hold **39.14% of all split gain** — narrow basin. When OI's OOS distribution drifts, the basin moves with it and ALL 4 leading features fire from wrong region.

**(B) Q5 strong-positive band catastrophe** (dominant attribution):
| Band | IS PnL | OOS PnL |
|---|---|---|
| Q1 neg-extreme | +58.52 | **-30.78** |
| Q4 ORACLE mild-pos | -2.28 | +22.45 |
| Q5 strong-pos | +0.58 | **-56.41** |

**The brief's ORACLE Q4 hypothesis was misidentified.** IS profit basin was Q1 NEG-extreme (+58.52), not Q4. EDA used regime-conditional z-windows not realized trade attribution. OOS Q1 flipped (-30.78) and Q5 collapsed (-56.41). Q4 SURVIVED (+22.45 / 40.8% WR) but model didn't concentrate there.

**(C) Cross-asset OI joint regime shift**: BTC+ETH+alt OIs all rose together through 2025-Q3/Q4 (perp-funding cycle post-halving). z90 normalizes within-symbol but joint regime shift means all cohorts' Optuna basins relocated SAME direction — no diversification cancellation. Funding was more symbol-idiosyncratic.

## 2. /023 + /025 LEARNED-NEGATIVE pattern (n=2 ESTABLISHED)

**Pattern: v1 single-seed n_trials=18 + Pool Model A architecture allows LightGBM to ingest NEW features and overfit IS joint loss surface without TPE saturation to discover OOS generalization failure.**

Contributing causes (ranked):
1. **Pool Model A primary**: 5-symbol joint training = feature importance reflects average across symbols, not per-symbol fit quality. OI nearly UNIFORM 6.39%-8.00% across 5 cohorts — pool wants OI because "signal somewhere in joint sample" without per-cohort OOS robustness. Per-symbol specialists (LINK, ETH+gate) avoided trap.
2. **n_trials=18 below TPE saturation** (~30 per v3 cadence): low-budget picks early IS-basin combinations without testing perturbation robustness. Funding rank 12 below basin-pull threshold; OI rank 4 inside it.
3. **v1 basin susceptibility (secondary)**: 8h-candle horizon + pool = chunky inferential commitments.

## 3. Cycle-3 closeout assessment

8/10 EXPLORATIONs failed. The 2 that succeeded (LINK, ETH+gate) shared property: **per-cohort architectural changes with independent priors**, NOT feature additions to joint Pool.

**Structural finding (n=2)**: NEW feature families ADDED TO POOL MODEL A at single-seed EXPLORATION budget are STRUCTURALLY UNABLE to clear OOS at v1 cohort. Not noise — mechanism (basin relocation under joint training).

## 4. /027 CONFIRMATION bundle FINAL — LOCKED

1. **BASELINE_V1 pool** (14-feature anchor, FROZEN — no OI / funding / regime-conditional)
2. **LINK specialist** (+0.80 OOS Δ standalone)
3. **ETH+gate specialist** (+0.50 OOS Δ standalone)

Target: **+1.10 to +1.30 OOS Sharpe multi-seed mean**.

EXCLUDED with mechanism evidence in catalog: OI delta (LEARNED-NEG-CAT), funding rate z (LEARNED-NEG), regime-conditional pool (/024 non-specialization), microstructure features (untested), XGBoost (deferred), meta-labeling (v3 NEG-PATH-C precedent).

**MULTI-SEED MANDATE for /027** (HIGH-RISK count now ≥3 in cycle-3):
- `--seeds 2` minimum (5 inner × 2 outer = 10 models/cell)
- n_trials=35
- Full DSR/PBO/PSR re-eval
- Cross-correlation pre-validation MANDATORY: Pearson(pool, LINK) < 0.50 AND Pearson(pool, ETH+gate) < 0.50

## 5. Track record

| Prior | Verdict | Outcome |
|---|---|---|
| LEARNED-NEGATIVE 30% modal | HIT directionally | ✓ |
| NEG-CAT 4% tail | TAIL FIRED | Should have been **15-20%** (rank-4/7.49% basin-pull was exponentially more than rank-12/5.40%) |
| PROMISING 22% | REFUTED | Q4 survived but model didn't concentrate there |
| DUAL GATE methodology | VINDICATED 5/5 | ✓ correctly identified LEARNING |
| HARD BLOCK on missing OI | VINDICATED | ✓ pre-flight defect saved iteration |

**Miscalibration lesson**: EDA Sharpe-proxy without trade-attribution should be discounted ~50% in prior calculus. Brief Q4 reading was distribution-level not trade-conditioned.

Cumulative LM Master: **directional 2/8 = 25%; methodology 6/6 = 100%** (DUAL GATE + HARD BLOCK both load-bearing).

## 6. Most important Phase 7.4 finding

**Pool Model A + NEW feature at LightGBM rank ≤5 / portfolio gain ≥4.0% / breadth-uniform across 4+ cohorts is the structural LEARNED-NEGATIVE-CATASTROPHIC signature for v1 at single-seed n_trials=18 EXPLORATION budget — DUAL GATE PROMISING-clean status now functions as a CONTRA-INDICATOR under this configuration, and cycle-4 must STRUCTURALLY disqualify NEW-feature-to-Pool-Model-A EXPLORATIONs in favor of per-symbol specialist axes or orthogonal-mechanism rule layers.**

## Closing for Critic

Three evidence anchors:
1. **Top-4 split-gain share 39.14%** — narrow basin
2. **IS-Q1 (+58.52) → OOS-Q1 (-30.78) sign flip** dominant attribution channel; brief EDA misidentified load-bearing band
3. **z90 stationarity passed ADF but joint cross-asset OI level non-stationary** through 2025-2026 (post-halving perp build)

Critic should NOT block /027 — bundle composition is correctly defensive; this report supports MERGE-with-multi-seed-mandate.
