# iter-v1/018 — Phase 7 Engineering Report

**Iteration**: iter-v1/018 (cycle-3 EXPLORATION #3 of 10; FIRST per-cohort EXPLORATION under USER STRATEGIC PIVOT)
**Branch**: `iteration-v1/018`
**HEAD**: `04e544c` (Critic Phase 7.5 review at `1ad1892`)
**Wall-clock**: ~25 min (well inside 2h cap)
**Verdict**: **EXPLORATION-PROMISING favorable-INERT side** — LINK-only specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate as load-bearing component.
**Reports**: `reports-v1/iteration_v1-018/{in_sample,out_of_sample}/`
**Critic review**: `briefs-v1/iteration_v1-018/review.md` (HEAD `1ad1892`)
**LM Master pre/post**: `briefs-v1/iteration_v1-018/lgbm_advisor.md` (Phase 4.5 advisory + Phase 7.4 post-mortem)

---

## 1. Headline Metrics

| Metric | IS | OOS | OOS / IS Ratio |
|---|---|---|---|
| **Sharpe** | **+0.3407** | **+0.9789** | **2.8730** |
| Sortino | +0.2671 | +0.6738 | 2.52 |
| Win rate | 41.6% | **50.0%** | 1.20 |
| Profit factor | 1.140 | 1.493 | 1.31 |
| Max drawdown | 43.37% | 24.21% | 0.56 |
| Trades | 154 | 48 | 0.31 |
| Total Net PnL % | +36.99 | +39.42 | 1.07 |
| Calmar ratio | 0.85 | 1.63 | 1.91 |
| **PSR_monthly_vs_0** | 0.757 | **0.885** | 1.17 |
| **PSR_monthly_vs_1** | 0.151 | **0.553** | 3.67 |
| PSR_daily_vs_0 | 0.732 | 0.858 | 1.17 |
| DSR | -67.99 | -12.52 | informational only (EXPLORATION-mode) |
| n_eff (global PCA) | 9 | 9 | — |
| n_eff_per_cell_median | 9 | 9 | in [4, 9] band (single-cohort native) |
| r5_fire_rate | 0.0 | 0.0 | R5 disabled |

**LINK-in-pool anchor (per `feedback_v1_per_cohort_exploration_strategy.md`)**: IS Sharpe +0.3724 / OOS Sharpe +0.8184.

- **F1 OOS Δ vs LINK-in-pool**: +0.9789 − 0.8184 = **+0.1605** → INERT band (just below +0.20 PROMISING boundary)
- **F3 IS Δ vs LINK-in-pool**: +0.3407 − 0.3724 = **−0.0317** → INERT band

→ **PROMISING-INERT favorable-direction** verdict-cell.

## 2. Per-Symbol PnL Attribution

### In-Sample (Model C — LINK-only dispatch)

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total IS PnL |
|---|---|---|---|---|---|---|
| **LINKUSDT** | **154** | **64** | **41.6%** | **+52.58** | **+0.34%** | **100.00%** |

### Out-of-Sample (Model C — LINK-only dispatch)

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total OOS PnL |
|---|---|---|---|---|---|---|
| **LINKUSDT** | **48** | **24** | **50.0%** | **+53.80** | **+1.12%** | **100.00%** |

**F-AXIS-MECHANISM #1 binary PASS**: per_symbol.csv contains 100% LINKUSDT both IS and OOS — single-cohort dispatch through Model C (R1 + R3, ATR×3.5 TP / ATR×1.75 SL, V1_FEATURE_COLUMNS_PRUNED) clean. Zero spillover from other symbols' dispatch branches.

## 3. Critic + LM Master Convergent Verdict

Both Critic Phase 7.5 (`review.md`) and LM Master Phase 7.4 (`lgbm_advisor.md`) converge on **PROMISING-INERT favorable**:

| Item | Critic | LM Master |
|---|---|---|
| Verdict cell | PROMISING-INERT favorable-direction | PROMISING-INERT (modal call CONFIRMED at 45% prior) |
| F1 anchor | LINK-in-pool +0.8184 (cell determination) | LINK-in-pool +0.8184 |
| /027 carry-forward | LINK-only specialist CONDITIONALLY CARRIED to substrate | LOAD-BEARING bundle component, anchor +0.80 |
| WR 50% identical | informational only | **same signal, cleaner Optuna trajectory** — PROMISING-FEATURE-MECHANICAL adjacent |
| OOS/IS 2.87 | not flagged as suspicious | regime-driven + capacity-driven (LINK IS bear-cycle drag; OOS single DeFi regime); 8/8 cross-arch prior > CSCV |
| PSR_monthly_vs_0 = 0.885 | informational only (small-sample 14 OOS months); do NOT cite as "near aspirational 0.95" | well above 0.40 PROMISING-INERT floor; approaches 0.95 aspirational but small-sample wide CI |
| /019 axis | ETH-only with stateless BTC-trend regime gate — single-axis isolation, deadlock-impossibility proof required | ETH-only with BTC-trend regime gate — diversifies cohort coverage, builds /027 portfolio-of-specialists |

**Track records updated:**
- **Critic**: 14 of 14 checks PASS (Check 6 N/A single-seed; Check 3 INFORMATIONAL single-cohort).
- **LM Master**: 2/16 directional (was 1/15 — Phase 4.5 modal INERT 45% confirmed at PROMISING-INERT cell) + 8/16 mechanism-level (was 7/15 — WR identical → same signal cleaner trajectory mechanism pre-registered for next cohort isolation).

## 4. LINK 9/9 Structural Prior — Updated

LINK OOS PnL trajectory across baseline + /011-/018:

| Anchor | LINK OOS PnL % |
|---|---|
| baseline | +52 |
| /011 | +85 |
| /012 | +53 |
| /013 | +47 |
| /014 | +4 |
| /015 | +85 |
| /016 | +35 |
| /017 | +54 |
| **/018 (LINK-only)** | **+54** |

**CV ≈ 0.51, mean +51, all 9 positive sign, range [+4, +85].**

Cross-architecture stability:
- 3 different universes (5-sym, 6-sym, 1-sym)
- 4 different feature stacks
- 2 different labeling regimes (/014 σ_t LABEL-only; /015 σ_t symmetric)
- 2 different sample-weight modes (`abs_pnl` and `uniform`)
- 3 different methodology substrates

This is the **most stable per-symbol structural pattern in v1 catalog**. Multi-seed CV at /027 will REGRESS toward the cross-arch mean (~+0.82) NOT extend beyond /018's +0.98 — the LINK OOS +0.98 at /018 contains single-seed=42 basin-lottery overshoot (band [+0.30, +1.20] from variance alone).

## 5. /027 Bundle Composition Preview

Per LM Master Phase 7.4 §7:

| Specialist | Status after /018 | Predicted multi-seed Sharpe contribution |
|---|---|---|
| **LINK-only specialist** | **VALIDATED — LOAD-BEARING** | +0.80 anchor |
| ETH-only + BTC-trend regime gate | TBD at /019 | +0.50–0.70 (conditional on /019 verdict) |
| BTC-only specialized | TBD at /021 | +0.40–0.70 (conditional on labeling diagnostic at /020) |
| DOT-only specialized | TBD at /022 | TBD |
| SOL-only specialized | TBD at /023 (note: SOL was added at /017 universe expansion; specialization vs in-pool TBD) | TBD |
| 2-3 sym pooled cohorts | TBD at /024-/026 | TBD |

**/027 bundle target**: ≥+0.70 multi-seed mean OOS Sharpe (else portfolio-of-specialists methodology DOES NOT beat naive pooling). Each specialist anchored at ≤30% bundle weight via concentration cap; cross-specialist correlation matrix computed from /018-/026 monthly OOS to guide weights.

**Critical risk**: if LINK-only specialist anchors below +0.60 multi-seed mean (rather than +0.80), /027 bundle Sharpe degrades by ~0.20 — the 9/9 single-seed OOS-positive pattern argues against this but is sample-of-1 at each seed=42 architecture.

## 6. USER STRATEGIC PIVOT — Empirical Validation

The user directive 2026-05-26 verbatim at /017 closeout: *"Use the explorations to narrow down approaches like individual symbols, pooled symbols (2 or 3) with specific features, configurations. Then use the confirmation to combine those small explorations and take an edge in the diversification."*

Codified at `feedback_v1_per_cohort_exploration_strategy.md`.

**/018 is the FIRST per-cohort EXPLORATION** under this methodology — and produced the first cycle-3 edge candidate (PROMISING-INERT favorable). Compare:

- Cycle-3 #1 (/016 sample-weighting `uniform` on pooled universe): EXPLORATION-NEGATIVE catastrophic (OOS Δ −1.67)
- Cycle-3 #2 (/017 universe +SOL on pooled): EXPLORATION-NEGATIVE anti-direction-INERT (OOS Δ −0.09)
- **Cycle-3 #3 (/018 LINK-only per-cohort): EXPLORATION-PROMISING favorable-INERT** (OOS Δ +0.16)

The pivot from global-pooled axes to per-cohort specialization **directly produced the first cycle-3 edge candidate** — empirical validation of the methodology shift. This is sample-of-1 (single iteration), but the structural prior (LINK 9/9 OOS-positive) is sample-of-9 — strongest in v1 catalog.

## 7. Phase 7 Closeout — Items for Phase 8

1. **Diary** (`diary-v1/iteration_v1-018.md`): frontmatter verdict `EXPLORATION-PROMISING-INERT favorable`, axis family `per-cohort-specialization-LINK` (NEW 9th catalog family), cohort identifier LINK, specialization dimension NONE (Option E LINK-in-isolation; no additional knob).

2. **Catalog row append** at `briefs-v1/exploration_catalog.md` Ledger.

3. **Tag** `v0.v1-018` after Phase 8 closeout commit.

4. **/019 axis advances per Critic + LM Master convergent recommendation**: ETH-only with stateless BTC-trend regime gate. NEW axis family `per-cohort-specialization-ETH` (10th).

5. **Five LESSONS** to codify in diary (see Phase 8 dispatch).

## 8. Files & Commits on Branch

- Branch: `iteration-v1/018` from `iter-v1/017` closeout
- HEAD at LM Master Phase 4.5: `004d1d1`
- HEAD at brief Section 3.4 LM Master responses: `d4a5717`
- HEAD at QE LINK-only dispatch implementation: `4813f1e`
- HEAD at Critic Phase 6.0 PASS: `7508dd4`
- HEAD at LM Master Phase 7.4 post-mortem: `04e544c`
- HEAD at Critic Phase 7.5 review (PROMISING-INERT favorable): `1ad1892`
- HEAD at Phase 7 evaluation + engineering report (THIS COMMIT): TBD
- HEAD at Phase 8 closeout (next commit): TBD
- Reports artifacts in `reports-v1/iteration_v1-018/`

**Trunk merge**: NONE. EXPLORATION-PROMISING-INERT does NOT update BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1 — strictly-better policy not triggered: F1 IS Δ −0.03 and F3 OOS Δ +0.16 do not BOTH strictly beat the cross-arch LINK-in-pool anchor). LINK-only specialist carries forward as **structural-cell ingredient** for /027 CONFIRMATION substrate, NOT as merge candidate to BASELINE_V1.md.

**Tag**: `v0.v1-018` to be applied after Phase 8 diary commit.
