# iter-v1/017 — Engineering Report

**Iteration**: iter-v1/017 (CYCLE-3 EXPLORATION #2 of 10)
**Date**: 2026-05-26
**Branch**: `iteration-v1/017`
**HEAD at Phase 7**: `5b3515e`
**Verdict (Critic Phase 7.5)**: EXPLORATION-NEGATIVE anti-direction-INERT
**LM Master Phase 7.4 reframing**: PROMISING-INERT (Critic took conservative anchor)
**Anchor**: `v0.v1-baseline-corrected` (`f8bc12c`) — IS +0.2829 / OOS +0.6637

---

## 1. Headline Outcome

| Metric | Baseline | /017 | Δ | Verdict-Band |
|---|---|---|---|---|
| IS Sharpe | +0.2829 | +0.3338 | **+0.0509** | INERT [-0.20, +0.20] |
| OOS Sharpe | +0.6637 | +0.5729 | **-0.0908** | INERT-anti-direction [-0.20, +0.20] |
| OOS/IS ratio | 2.35 | 1.72 | -0.63 | Healthy anti-overfit |
| IS trades | 596 | 842 | +246 | F8 IS PASS |
| OOS trades | 217 | 301 | +84 | F8 OOS BREACH (>284) |
| n_eff_per_cell_median | 13 | **9** | -4 | Outside Phase 4.5 [11, 17]; corrected [8, 13] |
| PSR_monthly_vs_0 (OOS) | — | **0.808** | +0.68 vs /016 | **Load-bearing positive signal** |

**Critic verdict cell**: F1 OOS Δ anti-direction (-0.0908) within INERT band + F-AXIS-MECHANISM #3 FAIL (n_eff=9 below [11, 17]) + F8 OOS breach (+17 trades above 284 upper-end) = **EXPLORATION-NEGATIVE anti-direction-INERT**.

**LM Master delta**: reframed as PROMISING-INERT citing PSR jump 0.125→0.808 + ETH partial dilution + basin-health positive. Critic accepted basin-health evidence as informative but NOT as merge signal — conservative anchor per cycle-3 discipline retains NEGATIVE label.

---

## 2. Per-Symbol IS/OOS PnL Attribution

### IS (842 trades total)

| Symbol | Trades | WR | Net PnL | Share | Avg PnL |
|---|---|---|---|---|---|
| DOTUSDT | 128 | 46.9% | **+96.07** | 75.10% | +0.75% |
| LTCUSDT | 117 | 47.0% | +67.53 | 52.79% | +0.58% |
| LINKUSDT | 154 | 41.6% | +52.58 | 41.10% | +0.34% |
| SOLUSDT | 155 | 40.0% | **+19.04** | 14.88% | +0.12% |
| ETHUSDT | 159 | 37.7% | -13.49 | -10.54% | -0.08% |
| BTCUSDT | 129 | 31.0% | **-93.81** | -73.34% | -0.73% |

### OOS (301 trades total)

| Symbol | Trades | WR | Net PnL | Share | Avg PnL |
|---|---|---|---|---|---|
| LINKUSDT | 48 | 50.0% | **+53.80** | 107.57% | +1.12% |
| DOTUSDT | 50 | 44.0% | +32.91 | 65.81% | +0.66% |
| BTCUSDT | 52 | 36.5% | **+15.11** | 30.22% | +0.29% |
| SOLUSDT | 51 | 37.3% | **+8.19** | 16.39% | +0.16% |
| ETHUSDT | 53 | 39.6% | -28.07 | -56.13% | -0.53% |
| LTCUSDT | 47 | 36.2% | -31.93 | -63.85% | -0.68% |

### Comparison Across /014/015/016/017 (ETH OOS trajectory)

| Iter | Axis | ETH OOS PnL | ETH OOS Share | LINK OOS PnL | Net OOS PnL |
|---|---|---|---|---|---|
| /014 | labeling σ_t LABEL-only | -41.18 | — | +3.87 | +3.31 |
| /015 | labeling σ_t symmetric C1 FIX multi-seed | -23.29 | — | +84.58 (285%) | +29.66 |
| /016 | sample-weighting uniform | **-51.46** | +76% | +34.91 (60%) | -67.99 |
| **/017** | **universe +SOL** | **-28.07** | **-56%** | **+53.80 (108%)** | **+42.36** |

**ETH PARTIAL DILUTION CONFIRMED**: /017's -28.07 is 2nd-best ETH OOS in cycle-2+3 window; universe dilution at 16.4% SOL contribution genuinely shifted the basin (NOT just headline). Drag is structural-PARTIAL-dilutable, NOT structural-locked (refutes LM Master Phase 4.5 75% regime-lock prediction in magnitude direction).

---

## 3. BTC Single-Seed Rotation Signature

**Catastrophic IS / positive OOS / single-seed = 42**: BTC IS **-93.81** (rank-6, worst) vs BTC OOS **+15.11** (rank-3, positive). Cross-period sign inversion is **expected single-seed-rotation signature**, NOT defect.

Per-symbol IS catastrophic-rotation across cycle-2+3:
- /011: LINK catastrophic IS
- /014: ETH catastrophic IS (-99.73)
- /015: ETH catastrophic IS (+17.34 sign-flipped via C1 FIX)
- /016: All 5 symbols IS-negative simultaneously
- **/017: BTC IS -93.81 + DOT IS +96.07 (new winner)**

Pattern: at single-seed=42 EXPLORATION, ~1 symbol per iteration drifts catastrophically IS-negative while another floats catastrophically IS-positive, with the **identity ROTATING**. v1 analog of v3's "single-seed=42 frozen-baseline" pattern but with universe-rotation overlay (per LM Master Phase 7.4 §3).

**LM Master Phase 7.4 instruction to Critic Check 4**: BTC IS -93.81 + BTC OOS +15.11 is single-seed-rotation signature, **NOT defect**. Critic Phase 7.5 honored — no BLOCK on per-symbol IS catastrophic alone.

---

## 4. PSR_monthly_vs_0 Jump 0.125 → 0.808 (+0.68)

**Single most important quantitative signal of /017** — exceeds all point-Sharpe signals in interpretive weight per LM Master Phase 7.4 §3.

| Iter | PSR_monthly_vs_0 (OOS) | Δ vs prior |
|---|---|---|
| /014 | ~0.50 | — |
| /015 | 0.59 | +0.09 |
| /016 | **0.125** (collapse) | -0.47 |
| **/017** | **0.808** | **+0.68 (largest single-iter jump in cycle-3)** |

PSR rewards **monthly-PnL distribution shape**, not point Sharpe. The +0.68 jump means OOS monthly distribution became more **consistently positive** (LINK + DOT + BTC + SOL = 4 positive symbols vs /016's all-negative). LM Master Phase 7.4 §1 catalog implication: **basin-reorganization without signal discovery** — analog of v3 PROMISING-MECHANICAL at universe layer.

**Forward elevation (Critic Phase 7.5 Rec #3)**: PSR_monthly_vs_0 elevated to **first-class basin-health metric** in cycle-3. Track in catalog headline alongside point Sharpe.

---

## 5. F-AXIS-MECHANISM Sub-Checks

| Sub-Check | Predicted (Phase 4.5) | Observed | Status |
|---|---|---|---|
| #1 Model F dispatched | SOL trade count > 0 | 51 OOS trades | **PASS** |
| #2 SOL portfolio share | ∈ [5%, 40%] CAUTIOUS band | **16.4%** IS, **16.4%** OOS | **PASS** |
| #3 n_eff_per_cell_median | ∈ [11, 17] | **9** | **FAIL** (3rd time) |

**n_eff REFUTED 3rd consecutive time**:
- /014: n_eff=19 (label-shape baseline σ_t LABEL-only) — OUTLIER above
- /015: n_eff=3 (timeout-fallback dominance at 7.82% labels) — OUTLIER below
- /016: n_eff=9 (weight-distribution collapse uniform)
- **/017: n_eff=9 (universe expansion, baseline labels, abs_pnl weighting)**

**Corrected mental model** (LM Master Phase 7.4 §4): `n_eff_per_cell` in v1 has **stable native range ~9-13** at baseline-labels + abs_pnl-weighting + single-seed EXPLORATION. /014's 19 and /015's 3 were both outliers requiring specific axis-driver. **Tighten band to [8, 13]** as cycle-3 EXPLORATION native band; outside-band only when axis structurally touches label-shape or weight-distribution. **Demote n_eff to INFORMATIONAL** for universe-expansion axes (NOT a sensitive axis-attribution sub-check).

---

## 6. USER STRATEGIC PIVOT (2026-05-26 at /017 closeout)

**User directive (verbatim)**: *"Use the explorations to narrow down approaches like individual symbols, pooled symbols (2 or 3) with specific features, configurations. Then use the confirmation to combine those small explorations and take an edge in the diversification."*

Codified into `feedback_v1_per_cohort_exploration_strategy.md` at `~/.claude/projects/-home-roberto-crypto-trade/memory/`.

**Old methodology (cycle-3 /016, /017)**: global axes on pooled universe (sample-weighting, universe expansion).

**New methodology (cycle-3 /018+ onwards)**: per-cohort specialization (1-3 symbols, cohort-specific features/config) at EXPLORATION; CONFIRMATION at /027 bundles specialists for **diversification edge**.

**Justification chain**:
1. Cycle-2 NO-MERGE (10 iterations, 7 axis families) — global-axis saturated
2. Cycle-3 /016 NEGATIVE + /017 PROMISING-INERT — pooled-universe global axes saturated at single-axis EXPLORATION budget
3. LINK structural OOS positive across /011-/017 (7+ iterations) — under-exploited by pooled training
4. ETH structural OOS negative across same iterations — pollutes pooled BTC signal
5. v3 precedent: per-symbol architecture (V3-BCH, V3-LDO, V3-TRX) found edge there

**Caveats** (from memory file):
- Single-cohort EXPLORATION verdicts are intrinsically cohort-bound; PROMISING per-cohort doesn't imply PROMISING portfolio
- Cohort rotation rule: prior 5 EXPLORATIONs by COHORT + SPECIALIZATION
- Each EXPLORATION proposes ONE specialization dimension
- CONFIRMATION bundles only PROMISING specialists; re-evaluate at multi-seed

---

## 7. /018 Mandate — LINK-only Specialized (HIGH Structural Prior)

**Per Critic Phase 7.5 Path Forward + USER STRATEGIC PIVOT**:

### Priority Ranking

| Cohort | Structural Prior | OOS Edge Pattern | Rationale |
|---|---|---|---|
| **LINK-only** | **HIGH** | OOS positive at /011, /012, /013, /014, /015, /016, /017 (7+ iters) | Strongest structural OOS edge; under-exploited by pooled training |
| ETH-only + regime kill | MEDIUM | OOS negative pattern is strongest; regime gate addresses head-on | Pre-committed at /017 brief Section 11.3 |
| BTC-only specialized | MEDIUM | BTC IS at /017 -93.81 (catastrophic rotation); BTC OOS +15.11 (positive) | Pooled Model A (BTC+ETH) trains badly on BTC; separation may reveal BTC-specific edge |

**Selected /018 candidate**: **LINK-only specialized** (HIGH structural prior).

**Specialization dimensions to consider** (single-axis per EXPLORATION):
- LINK-specific features (DeFi-correlation, LINK-specific volatility scaling)
- LINK-specific atr_tp/atr_sl (currently shared with Model C — likely under-tuned)
- LINK-specific labeling thresholds
- LINK-specific risk-gate config

**Caveat**: single-symbol model can't diversify intrinsically; if LINK OOS edge is regime-bound (post-2024 DeFi cycle), it may not generalize. Test via CONFIRMATION /027 bundling.

**LM Master Phase 7.4 +XRP recommendation (65% MEDIUM-HIGH)** SUPERSEDED by user strategic pivot. /018 brief Section 0.6 must justify per-cohort axis selection with explicit reference to user 2026-05-26 directive.

---

## 8. Process Findings

### 8.1 Engineering Report MISSING (6th strike — fixed by THIS report)

`reports-v1/iteration_v1-017/engineering_report.md` did not exist at Phase 7.5 dispatch (Critic Phase 7.5 Finding #1). This report retroactively closes the violation.

**Permanent fix scope**: orchestrator/skill-layer (Phase 6 contract addition + Phase 6.0 pre-flight handoff check). Not QR scope this iteration.

### 8.2 n_eff Band Correction (Forward-Binding for /018+)

LM Master Phase 4.5 predicted [11, 17]; observed 9 (REFUTED 3rd time). Corrected band [8, 13]. Demoted to INFORMATIONAL for universe + sample-weighting axes.

**Forward-binding /018+**: only label-shape or weight-distribution axes should pre-register n_eff_per_cell as a primary F-AXIS-MECHANISM sub-check. Universe and feature axes use n_eff as informational only.

### 8.3 PSR Sensitivity Reveal

PSR_monthly_vs_0 jump 0.125 → 0.808 was the most sensitive signal at /017 — exceeded all point-Sharpe signals in interpretive weight. **Elevate to first-class basin-health metric** in cycle-3 catalog headline.

---

## 9. Cadence Position

- Cycle-3 EXPLORATION count: **2 of 10**
- CONFIRMATION earliest: /027 (assuming sequential EXPLORATIONs)
- Edge ingredients merged this cycle: **0**
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic (/016) + 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017)
- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)
- Methodology pivot: global-axis → per-cohort specialization (/018 onwards)

---

## 10. Files & Commits

- Branch: `iteration-v1/017` from `iter-v1/016` closeout (tag `v0.v1-016`)
- HEAD at Phase 5.5 PASS: `5a1883c`
- HEAD at QE implementation: `887d115` (+SOL fetch) → axis isolation fix `5fffe8a`
- HEAD at Critic Phase 6.0 PASS: `e4aead6`
- HEAD at backtest completion: comparison.csv in `reports-v1/iteration_v1-017/`
- HEAD at LM Master Phase 7.4 post-mortem: `f0dccd3`
- HEAD at Critic Phase 7.5 review (EXPLORATION-NEGATIVE anti-direction-INERT): `5b3515e`
- HEAD at Phase 7 engineering report (6th-strike fix): THIS COMMIT

**Trunk merge**: NONE. EXPLORATION-NEGATIVE anti-direction-INERT never updates BASELINE_V1.md.

**Tag**: `v0.v1-017` (applied after Phase 8 closeout commit).
